---
type: concept
title: "Rosé — 分区数据库异步复制协议"
tags:
  - 异步复制
  - 主备复制
  - 单调前缀一致性
  - 分区数据库
  - 故障恢复
  - CIDR-2026
related:
  - "[[Rosé-Coordinated-Apply-协调应用]]"
  - "[[事务模型深度调研]]"
  - "[[synthesis/分布式数据系统一致性体系]]"
sources:
  - "sources/papers/Rose/Rose-CIDR2026.pdf"
status: draft
created: 2026-06-15
updated: 2026-06-15

---

# Rosé — 分区数据库异步复制协议

![[diagram/rose-async-replication.svg]]

## 一句话总结

Rosé 是一个面向分区式数据库的**异步主备复制协议**，利用数据库已有的全局快照机制（epoch/HLC）将单调前缀一致性扩展到分区场景，通过三件套（回压限制 lag + 协调应用 + 全局快照边界）解决异步复制的三个核心痛点。

## 三件套设计

### 1. 全局快照 → 单调前缀一致性

**问题**：分区数据库中每个 partition 独立复制。跨分区事务的写入可能部分到达部分未到达备份 → 备份整体处于未定义状态。

**解法**：
- 备份集群跟踪每个 partition 的完整应用 epoch：e₁, e₂, ..., eₙ
- **对外暴露的快照 epoch = min(eᵢ)**
- 只有所有 partition 都到达 epoch e 的事务，才在备份集群上可见
- snapshot epoch 单调递增 → 备份在任何时刻暴露的都是一个一致的全局快照

**关键**：这不需要引入新的一致机制——现代数据库已有的全局快照支持（HLC/epoch/TrueTime）就是基础设施。

### 2. 回压限制复制 Lag

**复制 lag** = e_primary,i − e_backup,i（该 partition 最多落后多少 epoch）

**系统级 lag** = min(lag_i) —— 只要有一个掉队 partition，整个备份集群的快照 epoch 无法推进。

**回压机制**：
- 每个 partition 维护一个有界发送队列（size = L）
- 队列满 → **仅对该 partition 限流**（straggler isolation）
- L 是关键调参：太大 = 新鲜度保证差，太小 = 容易限流

**可用性**：Rosé 的可用性不低于同步复制（已证明）。如果备份区域完全不可达，管理员可手动解除回压。

### 3. Coordinated Apply（协调应用）

分离 WAL 复制和 KV 存储应用。详见 [[Rosé-Coordinated-Apply-协调应用]]。

## 关键对比

| | 同步共识复制 | 原生异步主备 | Yugabyte xCluster | Rosé |
|---|---|---|---|---|
| **写延迟** | 高（多数派） | 低 | 低 | 低 |
| **备份一致性** | 强 | 未定义 | 单调前缀 | 单调前缀 |
| **复制 lag** | 无 | 无限制 | 无限制 | 有界 |
| **故障恢复时间** | 即时 | 慢+修复 | 即时 | 即时 |
| **恢复后性能** | 满 | 满（修复后） | **退化** | **满** |

## 局限
- 回压参数 L 需人工调优，未自动化
- 备份区域长期不可达时需人工解除回压
- 仅对比 Yugabyte，未与 Spanner/CockroachDB 等对比
- CIDR 短文（7页），缺少形式化验证和完备的安全证明

## 与知识库的关联
- **[[事务模型深度调研]]**：全局快照是 MVCC 的副产品，Rosé 将其用于复制语义
- **[[LSM-Tree]]**：Yugabyte 的恢复后性能退化根源在 LSM 树——旧版本数据分布在多个 SST 文件中，mark keep_ts 后 compaction 负担巨大。Rosé 通过 WAL/KV 分离避免了这个问题
- **[[synthesis/分布式数据系统一致性体系]]**：Rosé 填补了"异步复制 + 强语义"象限
