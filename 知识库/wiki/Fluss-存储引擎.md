---
type: analysis
title: "Fluss 存储引擎模块分析"
sources:
  - "https://github.com/BryantChang1992/ai_memory_chang_ai_team/blob/master/tech_research/fluss/02-存储引擎模块.html"
tags:
  - "Fluss"
  - "存储引擎"
  - "RocksDB"
  - "Log Segment"
  - "源码分析"
created: 2026-06-15
updated: 2026-06-15
status: draft
related:
  - "[[Fluss-整体架构]]"
  - "[[Fluss-KV存储-RocksDB]]"
  - "[[Fluss-Arrow列式记录格式]]"
  - "[[LSM-Tree]]"
---

# Fluss 存储引擎模块分析

## 概述

Fluss 存储引擎采用**三层存储模型**，与 Kafka 单层本地 Log 有根本差异。在 TabletServer 内部，ReplicaManager 统一调度三个子系统：LogManager（本地 Log）、KvManager（RocksDB KV）、RemoteLogManager（远程分层）。

```
ReplicaManager
  ├── LogManager  → LogTablet → LocalLog → LogSegments → LogSegment
  ├── KvManager   → KvTablet  → RocksDBKv + WalBuilder + SnapshotManager + RowMerger
  └── RemoteLogManager → S3/HDFS/OSS
```

## 三层存储 vs Kafka 单层

| 层 | Fluss | Kafka 2.7.2 |
|----|-------|-------------|
| **L1: 本地 Log** | `LocalLog` (LogSegments) — 基于 Kafka Log 改造 | `Log` (LogSegments) — 文件系统 Segment |
| **L2: KV Store** | `KvTablet` (RocksDB) — **Fluss 独有** | 无 |
| **L3: 远程分层** | `RemoteLogManager` (S3/HDFS) — **原生支持** | 无（KIP-405 后引入） |

## Log 子系统

Fluss 的 Log 子系统高度复用 Kafka，但有关键差异：

| 特性 | Fluss LogTablet/LocalLog | Kafka Log |
|------|------------------------|-----------|
| 文件结构 | `.log` Segment（同 Kafka） | `.log` + `.index` + `.timeindex` |
| 索引 | 内存 NavigableMap（无独立 `.index` 文件） | 稀疏索引 `.index` |
| 时间索引 | 无 `.timeindex` | 时间索引 `.timeindex` |
| 恢复点 | `OffsetCheckpointFile`（同 Kafka） | `recovery-point-offset-checkpoint` |
| 记录格式 | Arrow 列式（带 schema id），三种 LogFormat | Key/Value 行式字节流 |
| 远程日志 | 内建 `remoteLogStartOffset/remoteLogEndOffset` | 无 |
| Lake 日志 | 内建 `lakeLogStartOffset/lakeLogEndOffset` | 无 |
| ChangeLog | `isChangelog` 标志 + `minRetainOffset` 保护 KV 快照依赖 | 无 |

LogFormat 枚举：`ARROW` / `COMPACTED` / `INDEXED`。其中 `COMPACTED` 和 `INDEXED` 为 PK 表的 changelog 优化格式。

## KV 存储子系统（Fluss 最大差异化模块）

详见 [[Fluss-KV存储-RocksDB]]。核心架构：

```
KvManager → KvTablet → RocksDBKv
              ├── WalBuilder（Arrow/Compacted/IndexWalBuilder）
              ├── SnapshotManager（PeriodicSnapshot → RocksIncrementalSnapshot → Uploader → Committer）
              ├── RowMerger（Default/FirstRow/Versioned/Aggregate）
              ├── PartialUpdater
              ├── AutoIncrementManager
              └── KvPreWriteBuffer
```

**关键设计决策**：Fluss KV 的 WAL 不是额外文件——它**直接复用 changelog LogTablet 的 segment**。这意味着 KV 恢复时不是读 WAL 文件，而是**重放 changelog LogTablet**。这实现了 Write-Once Read-Multiple 的架构模式。

## Tablet 抽象 vs Kafka Partition

| 维度 | Fluss Tablet | Kafka Partition |
|------|-------------|----------------|
| 物理实体 | LogTablet（仅日志）或 KvTablet（日志+KV） | Partition（仅日志） |
| 存储层 | 本地 Log + 可选 KV + 可选远程 | 仅本地 Log |
| 恢复方式 | Log replay 或 Snapshot restore | 仅 Log replay |
| 合并策略 | RowMerger（UPSERT/AGGREGATE/PARTIAL_UPDATE） | 无 |
| 删除语义 | 真正的 DELETE（从 KV 中删除） | Tombstone（追加标记） |
| 索引 | RocksDB（PK 索引） | OffsetIndex + TimeIndex |

Tablet 不是简单的 Partition 重命名——它是**物理存储代理单元**，封装了日志、KV、远程三层存储的统一生命周期。

## Replica 机制

Fluss 的 ReplicaManager 在 Kafka 基础上扩展了两个新的写入/读取路径：

| 路径 | Fluss | Kafka |
|------|-------|-------|
| 写入 | `appendRecords()` + `putKv()` | `appendRecords()` |
| 读取 | `fetchLogRecords()` + `fetchKvRecords()` + `lookup()` | `fetchMessages()` |

ISR 协议一致，延时操作框架（DelayedWrite/DelayedFetchLog）完全复用 Kafka DelayedOperation。Fetcher 线程（ReplicaFetcherThread）也继承 Kafka 设计。

---

> **关键洞察**：Fluss 存储引擎的核心创新不是 Log 的实现（这部分大量复用 Kafka），而是**在 Log 之上加了一层 KV Store**，使系统从"append-only 消息流"进化为"可更新、可删除、可索引的结构化存储"。这使得 Fluss 的应用场景从消息队列扩展到实时分析型数据库。
