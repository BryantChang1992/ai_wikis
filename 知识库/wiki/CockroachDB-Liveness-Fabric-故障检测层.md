---
type: concept
title: "Liveness Fabric — 去中心化集群故障检测层"
tags:
  - CockroachDB
  - 故障检测
  - 心跳机制
  - 大规模共识
  - Liveness-Fabric
related:
  - "[[CockroachDB-Leader-Lease-整体设计]]"
  - "[[CockroachDB-Leader-Fortification]]"
  - "[[事务模型深度调研]]"
sources:
  - "sources/papers/CockroachDB-Leader-Leases/Scalable-Leader-Leases-SIGMOD2026.pdf"
status: draft
created: 2026-06-15
updated: 2026-06-15

---

# Liveness Fabric — 去中心化集群故障检测层

![[diagram/cockroachdb-leader-lease-3-layer.svg]]

## 一句话总结

Liveness Fabric 是一个**去中心化、心跳驱动的集群级故障检测层**，通过节点间有向边的 (epoch, expiration) support 关系，将故障检测从 per-Raft-group 的 O(N_groups) 降到 O(N_nodes²)，是 Leader Leases 的根基。

## 为什么需要？

在多共识组架构中，每个 group 独立维护 Raft 心跳（leader → follower）来检测故障。当 group 数量达到数万时，这个成本巨大——即使 90% 的 group 长时间只有读活动，心跳仍然照发不误。

Liveness Fabric 将故障检测**从 Raft 中抽离出来**，作为一个共享的基座服务——所有 Raft group 共享同一个故障检测层，不再各自发送 Raft 心跳。

## 核心设计

### 有向 support 关系

Liveness Fabric 的核心是节点间的有向边：**n₁ → n₂** 维护一个 support 关系。

- n₁ **请求** n₂ 支持自己到时间戳 t
- n₂ **承诺** 在时间戳 t 之前持续支持 n₁，期间不会撤销 support
- 每对节点间双向、独立运行

### 数据结构

每个节点维护：
- `max_epoch`：epoch 计数器（重启或失去 support 时递增）
- `support_from[n']`：(epoch, expiration) —— **我收到的 support**（非持久化）
- `support_for[n']`：(epoch, expiration) —— **我给出的 support**（**持久化**——重启不能背弃承诺）
- `max_requested`：**持久化**——防止在旧 epoch support 未到期时请求新 epoch
- `max_withdrawn`：**持久化**——防止为已撤销 epoch 重新提供 support

### 两个核心性质

**1. Support Durability（支持持久性）**

如果 n₁ 从 n₂ 收到 (epoch=e, exp=t) 的 support，那么直到 n₂ 的时钟超过 t 之前，n₂ **不能**撤销这个 epoch 的 support。

关键实现安全保证：**epoch 递增是单向的**。一旦某个 epoch 的 support 被撤销，**该 epoch 永不复原**。

**2. Support Disjointness（支持不相交性）**

如果 n₁ 从 n₂ 收到 epoch=e、到期时间 t 的 support，那么 n₁ 不会在时钟 < t 时请求/收到 epoch=e'（e'>e）的 support。

通俗来说：**同一 epoch 的两段 support 在时间上不能重叠**。上一个 epoch 的 support 必须完全过期，才能开始下一个 epoch 的 support。这为 Lease Disjointness 奠定了拓扑基础。

### 心跳周期

- 每 **1 秒** 向所有节点发送心跳
- lease 时长设 **3 秒**（允许连续丢失 2 次心跳）
- 避免瞬时抖动误触发故障切换

### Store 级别 vs Node 级别

CockroachDB 在实际实现中，每个**store（磁盘）** 运行一个独立的 Liveness Fabric 实例。优势：
- 磁盘故障的爆炸半径限制在单个 store，而非整节点
- 代价是增加心跳总数（通过批量化优化缓解）

## 与 Disk Stall 的协同工作

Liveness Fabric 要求心跳请求/响应发出前先完成**同步磁盘写**。好处：
- 磁盘 stall → 无法心跳 → support 自动到期 → 触发 leadership 变更
- 全局唯一故障检测路径——不再有"看似存活实则僵死"的情况

## 算子（Algorithms）

### 发送心跳 & 接收响应
```
Send { epoch: support_from[n'], exp: now + 3s }
Receive { epoch: e, exp: t }
if e > max_epoch: max_epoch = e
if support_from[n'].epoch == e:
    support_from[n'].exp = max(support_from[n'].exp, t)
elif support_from[n'].epoch < e:
    support_from[n'] = (e, t)
```

### 接收心跳 & 发送响应
```
Receive { epoch: e, exp: t }
if support_for[n'].epoch == e:
    support_for[n'].exp = max(support_for[n'].exp, t)
elif support_for[n'].epoch < e:
    support_for[n'] = (e, t)
Send { epoch: support_for[n'].epoch, exp: support_for[n'].exp }
```

### 撤销 support
```
if now > support_for[n'].exp:
    support_for[n'].epoch++
    support_for[n'].exp = 0
```

## 形式化验证

Liveness Fabric 的 Support Durability 和 Support Disjointness 两个性质均使用 **TLA+** 形式化验证。

## 可扩展性

- 150 节点 × 12 stores = 1800 stores → 仅消耗 0.225 cores (~2.8% of 8 vCPU)
- 线性增长
