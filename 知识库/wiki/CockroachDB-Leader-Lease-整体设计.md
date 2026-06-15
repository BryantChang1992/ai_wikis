---
type: concept
title: "CockroachDB Leader-Lease — 可扩展多组租约方案"
tags:
  - CockroachDB
  - Raft
  - Leader-Lease
  - 分布式一致性
  - 故障检测
  - 大规模共识
related:
  - "[[事务模型深度调研]]"
  - "[[synthesis/分布式数据系统一致性体系]]"
  - "[[CockroachDB-Liveness-Fabric-故障检测层]]"
  - "[[CockroachDB-Leader-Fortification]]"
sources:
  - "sources/papers/CockroachDB-Leader-Leases/Scalable-Leader-Leases-SIGMOD2026.pdf"
status: draft
created: 2026-06-15
updated: 2026-06-15
---

# CockroachDB Leader-Lease — 可扩展多组租约方案

## 一句话总结

CockroachDB 通过 **Liveness Fabric（共享故障检测层）+ Leader Fortification（增强 Raft 领导保证）** 将 lease 维护成本从 O(N_groups) 降到 O(N_nodes²)，**CPU 节省 85%+**，同时消除了集中化 lease 在部分网络分区下的永久不可用问题。

## 核心问题

分布式数据库为强一致读引入 **Lease（租约）** 机制——持有 lease 的副本可以在不进行共识通信的情况下服务读请求。但当数据被分割为数十万个 consensus group 时，每个 group 独立维护自己的 lease 成为 CPU 和网络瓶颈。

CockroachDB 原有的两种方案都有硬伤：
- **Expiration Lease**：每个 Range 通过 Raft 日志周期性续约 → 10 万 Range 消耗 90%+ CPU
- **Centralized Lease**：通过集中式 liveness Range 管理 node 级 epoch → CPU 极低，但 partial partition 时 leaseholder 能续约却不能写 → **永久不可用**

## 解法：Leader Leases

### 三层架构
<svg viewBox="0 0 660 100" xmlns="http://www.w3.org/2000/svg" style="max-width:100%">
  <defs>
    <marker id="arrow-up3" markerWidth="6" markerHeight="8" refX="3" refY="0" orient="auto">
      <path d="M0,8 L3,0 L6,8 Z" fill="currentColor"/>
    </marker>
  </defs>
  <!-- Layer 1: Leader Lease -->
  <rect x="160" y="8" width="110" height="26" rx="5" fill="transparent" stroke="currentColor" stroke-width="2"/>
  <text x="215" y="23" font-family="sans-serif" font-size="13" fill="currentColor" text-anchor="middle" dominant-baseline="middle" font-weight="bold">Leader Lease</text>
  <line x1="270" y1="21" x2="295" y2="21" stroke="currentColor" stroke-width="2" marker-end="url(#arrow-up3)"/>
  <text x="380" y="23" font-family="sans-serif" font-size="12" fill="currentColor" text-anchor="middle" dominant-baseline="middle">极薄包装：lease = fortified leader 的 [now, LSU)</text>
  
  <!-- Layer 2 -->
  <rect x="160" y="42" width="110" height="26" rx="5" fill="transparent" stroke="currentColor" stroke-width="1.8"/>
  <text x="215" y="57" font-family="sans-serif" font-size="12" fill="currentColor" text-anchor="middle" dominant-baseline="middle">Raft (修改版)</text>
  <line x1="270" y1="55" x2="295" y2="55" stroke="currentColor" stroke-width="2" marker-end="url(#arrow-up3)"/>
  <text x="410" y="57" font-family="sans-serif" font-size="12" fill="currentColor" text-anchor="middle" dominant-baseline="middle">Fortification / LSU 计算 / 关闭心跳</text>
  
  <!-- Layer 3 -->
  <rect x="155" y="76" width="120" height="26" rx="5" fill="transparent" stroke="currentColor" stroke-width="1.8"/>
  <text x="215" y="91" font-family="sans-serif" font-size="12" fill="currentColor" text-anchor="middle" dominant-baseline="middle">Liveness Fabric</text>
  <line x1="275" y1="89" x2="300" y2="89" stroke="currentColor" stroke-width="2" marker-end="url(#arrow-up3)"/>
  <text x="430" y="91" font-family="sans-serif" font-size="12" fill="currentColor" text-anchor="middle" dominant-baseline="middle">集群 mesh：每对 store 间双向 support</text>
</svg>


### 关键机制

**1. Liveness Fabric（共享故障检测层）**
- 节点 n₁ → n₂ 有向边维护 support 关系：(epoch, expiration)
- support 语义：n₂ 承诺在 expiration 前不会撤销对 n₁ 的支持
- 一旦 support 被撤销（epoch 递增），**永不复原**
- 允许关闭 Raft 心跳，故障检测完全由 Liveness Fabric 代理

**2. Leader Fortification（增强 Raft）**
- leader 通过 `MsgFortifyLeader` 请求 follower 承诺在时间戳 X 前不投票给他人
- 收到多数派（含自己）成功响应 = fortified
- 允许完全关闭 per-group Raft 心跳

**3. LeadSupportUntil (LSU)**
- LSU = max_{Quorums} min_{r in Q} τ_r
- 即：所有多数派中，每个多数派的最小 support 到期时间的最大值
- LSU 是 lease 有效期的直接来源
- leader 可以保证在 LSU 之前不会被替换

### 为什么要统一 leader 和 leaseholder？

历史上 CockroachDB 分离 leader 和 leaseholder。统一后：
- 消除了 partial partition 永久不可用：如果 leaseholder 无法与多数派通信 → Liveness Fabric 失去 support → lease 失效
- 架构更简单：不再需要协调 leader 和 leaseholder 两个角色

### Disk Stall 的处理

要求 Liveness Fabric 心跳前做同步磁盘写：
- 磁盘 stall → 无法发心跳 → 失去 fortification → 自动触发 leadership 变更
- 爆炸半径限制在单个 store（心跳 per-store 而非 per-node）

---

## 评估亮点

| 维度 | Expiration | Centralized | Leader |
|------|-----------|-------------|--------|
| **CPU @ 100K Range** | 90%+ | ~5% | ~15% |
| **Partial partition** | ✅ | ❌ 永久不可用 | ✅ |
| **Disk stall** | ❌ | ❌ | ✅ |
| **恢复延迟(P50)** | 3.0-3.9s | 3.0-3.9s | 4.0-4.7s |
| **TPC-C 吞吐** | 随 scale 下降 20% | 平稳 | 平稳 |

**核心权衡**：故障恢复慢 1-2 秒（因为 lease 到期才能竞选），但换来了可扩展性和 partial partition 下的可靠性。

**Liveness Fabric 可扩展性**：
- 150 node × 12 stores = 1800 stores → 仅 0.225 cores (2.8% of 8 vCPU)
- 线性增长

## 对工程实践的启示

1. **共享故障检测层的设计模式**：任何管理大量共识组的系统都可以借鉴
2. **"多数派承诺"比"心跳超时随机性"更可靠**：Fortification 提供确定性保证
3. **紧耦合 leader 和 leaseholder 消除一整类故障模式**
4. **Disk stall 检测必须与故障检测紧密集成**，否则可能"死了却装死不了"

## 局限性

- 故障恢复延迟略高（1-2s）——对 ultra-low-latency failover 场景可能不够
- Leader replica 不能 quiesce——论文承认计划 future work
- 配置变更约束增加变更成本
