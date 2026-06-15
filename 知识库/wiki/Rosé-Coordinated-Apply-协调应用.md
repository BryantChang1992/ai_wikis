---
type: concept
title: "Rosé Coordinated Apply — WAL/KV 解耦的协调应用机制"
tags:
  - 异步复制
  - WAL
  - KV存储
  - 故障恢复
  - Rosé
related:
  - "[[Rosé-异步复制协议设计]]"
  - "[[LSM-Tree]]"
  - "[[LSM-Tree-合并优化]]"
sources:
  - "sources/papers/Rose/Rose-CIDR2026.pdf"
status: draft
created: 2026-06-15
updated: 2026-06-15
diagram: "diagram/rose-async-replication.svg"

---

# Rosé Coordinated Apply — WAL/KV 解耦的协调应用机制

## 一句话总结

Rosé 将写操作的**WAL 复制**和**KV 存储应用**解耦：WAL 条目自由复制到备份，但只在所有 partition 的一致 epoch 内统一 apply——使故障恢复仅需秒级 trim WAL，且 KV 存储中始终干净，恢复后无性能退化。

## 问题：异步复制中"不必要"的数据

在异步复制中，不同 partition 的备份可能处于不同 epoch。假设：
- P₁ 已复制到 epoch 10
- P₂ 仅复制到 epoch 8
- 全局 snapshot epoch = 8

那么 P₁ 备份中 epoch 9-10 的数据在故障时**不可用**——因为它对应的 P₂ 中 epoch 9-10 的数据还没到达。故障恢复时需要将这些"超额"数据清理掉。

## Yugabyte 的做法（及代价）

Yugabyte 的 RocksDB 每个 SST 文件有一个 metadata block，记录该文件中的 max_ts。故障恢复策略：
- 遍历所有 SST 文件
- 如果 file.max_ts > desired_snapshot_ts → 在 metadata block 写入 keep_ts
- 读操作需检查 keep_ts 并跳过超过此时间戳的数据
- 后台 compaction 逐步清理

**结果**：即时恢复做到，但读路径上有大量"无效数据"过滤开销：
- **吞吐下降 22%**
- **P99 延迟上升 15%**

## Rosé 的做法：Coordinated Apply

### 原理

大多数数据库的两阶段写入路径：
1. **WAL**：顺序写，保证持久性，格式适合快速 trim
2. **KV Store**：结构化组织，适合快速读取

Rosé 观察到：**WAL 是天然适合协调的层**——数据按插入顺序排列，trim 到指定偏移量是 O(1) 操作。

### 协议

1. 备份集群持续跟踪 min(replicated_epoch) — 全局 snapshot epoch
2. 当且仅当所有 partition 都到达某个 epoch，才通知各 partition 将该 epoch 之前的数据从 WAL apply 到 KV store
3. 备份 partition 的 WAL 可能已经包含未来 epoch 的数据（复制快），但**KV store 中永远不会超过 snapshot epoch**
4. 故障恢复时：
   - Trim WAL 到 snapshot epoch（极快）
   - KV store 无需清理——因为原本就没有超出一致点的数据
   - 恢复后立即满性能

### Dead Time 分析

不同 partition 的写入速度不同（hot partition → 复制时间长，cold partition → 复制时间短）。Coordinated apply 意味着快的 partition 要等待慢的完成才能 apply。

**dead_timeᵢ = max(RTⱼ) − RTᵢ**

其中 RT = 复制时间 = (write_bandwidth × epoch_duration) / network_bandwidth

**缓解**：
- Rosé 使用**毫秒级 epoch** → dead time 量级极低
- 在没有极端 hot partition 的场景下，dead time ≈ 0
- snapshot epoch 推进不受影响——快 partition 虽延迟开始 apply，但应当在慢 partition 传输完成前完成（因为传输才是瓶颈，不是 apply）

## 效果

| | Yugabyte xCluster | Rosé Coordinated Apply |
|---|---|---|
| **故障切换时间** | <2s | <2s |
| **恢复后吞吐** | 退化 22% | **不退化** |
| **恢复后 P99 延迟** | 退化 15% | **不退化** |
| **KV 存储状态** | 含脏数据，需后台清理 | **始终干净** |
| **清理方式** | 后台 compaction | trim WAL（极快） |

## 通用性

这个思路可以推广到任何使用"WAL + 结构化存储"架构的系统：
- 只要 WAL 格式支持快速 trim
- 只要 KV store 支持批量 apply
- 只要副本有全局一致性的 notion of time（epoch/snapshot/HLC）

**前提**：需要回压机制配合——如果没有 lag 限制，掉队 partition 会使所有 partition 的 apply 卡住（见 [[Rosé-异步复制协议设计]]）。
