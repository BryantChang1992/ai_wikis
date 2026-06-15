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
diagram: "diagram/fluss-storage-engine-3-layer.svg"

---

# Fluss 存储引擎模块分析

## 概述

Fluss 存储引擎采用**三层存储模型**，与 Kafka 单层本地 Log 有根本差异。在 TabletServer 内部，ReplicaManager 统一调度三个子系统：LogManager（本地 Log）、KvManager（RocksDB KV）、RemoteLogManager（远程分层）。

<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 700 160" width="700" height="160">
  <defs>
    <marker id="arrow-fse1" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <path d="M0,0 L8,3 L0,6 Z" fill="currentColor"/>
    </marker>
  </defs>
  <!-- ReplicaManager -->
  <rect x="20" y="10" width="140" height="34" rx="6" fill="transparent" stroke="currentColor" stroke-width="1.5"/>
  <text x="90" y="27" font-family="sans-serif" font-size="13" fill="currentColor" text-anchor="middle" dominant-baseline="middle" font-weight="bold">ReplicaManager</text>

  <!-- Line down from ReplicaManager -->
  <line x1="90" y1="44" x2="90" y2="60" stroke="currentColor" stroke-width="1.5"/>

  <!-- Branch lines -->
  <line x1="90" y1="60" x2="90" y2="62" stroke="currentColor" stroke-width="1.5"/>
  <line x1="90" y1="60" x2="34" y2="60" stroke="currentColor" stroke-width="1.5"/>
  <line x1="34" y1="60" x2="34" y2="80" stroke="currentColor" stroke-width="1.5"/>
  <line x1="90" y1="60" x2="90" y2="80" stroke="currentColor" stroke-width="1.5"/>
  <line x1="90" y1="60" x2="146" y2="60" stroke="currentColor" stroke-width="1.5"/>
  <line x1="146" y1="60" x2="146" y2="80" stroke="currentColor" stroke-width="1.5"/>

  <!-- LogManager -->
  <rect x="80" y="80" width="125" height="28" rx="5" fill="transparent" stroke="currentColor" stroke-width="1.2"/>
  <text x="142" y="94" font-family="sans-serif" font-size="12" fill="currentColor" text-anchor="middle" dominant-baseline="middle">LogManager</text>

  <!-- KvManager -->
  <rect x="4" y="80" width="125" height="28" rx="5" fill="transparent" stroke="currentColor" stroke-width="1.2"/>
  <text x="66" y="94" font-family="sans-serif" font-size="12" fill="currentColor" text-anchor="middle" dominant-baseline="middle">KvManager</text>

  <!-- RemoteLogManager -->
  <rect x="8" y="120" width="125" height="28" rx="5" fill="transparent" stroke="currentColor" stroke-width="1.2"/>
  <text x="70" y="134" font-family="sans-serif" font-size="12" fill="currentColor" text-anchor="middle" dominant-baseline="middle">RemoteLogManager</text>

  <!-- Arrows from LogManager -->
  <line x1="205" y1="88" x2="260" y2="88" stroke="currentColor" stroke-width="1.2" marker-end="url(#arrow-fse1)"/>
  <text x="230" y="81" font-family="sans-serif" font-size="10" fill="currentColor" text-anchor="middle" dominant-baseline="middle">→</text>
  <rect x="262" y="76" width="100" height="24" rx="4" fill="transparent" stroke="currentColor" stroke-width="1" stroke-dasharray="2,2"/>
  <text x="312" y="88" font-family="sans-serif" font-size="11" fill="currentColor" text-anchor="middle" dominant-baseline="middle">LogTablet</text>

  <line x1="362" y1="84" x2="390" y2="84" stroke="currentColor" stroke-width="1" marker-end="url(#arrow-fse1)"/>
  <rect x="392" y="74" width="95" height="22" rx="4" fill="transparent" stroke="currentColor" stroke-width="1" stroke-dasharray="2,2"/>
  <text x="440" y="85" font-family="sans-serif" font-size="10" fill="currentColor" text-anchor="middle" dominant-baseline="middle">LocalLog</text>

  <line x1="487" y1="80" x2="525" y2="80" stroke="currentColor" stroke-width="1" marker-end="url(#arrow-fse1)"/>
  <rect x="527" y="72" width="105" height="20" rx="4" fill="transparent" stroke="currentColor" stroke-width="1" stroke-dasharray="2,2"/>
  <text x="580" y="82" font-family="sans-serif" font-size="10" fill="currentColor" text-anchor="middle" dominant-baseline="middle">LogSegments</text>

  <line x1="632" y1="77" x2="655" y2="77" stroke="currentColor" stroke-width="1" marker-end="url(#arrow-fse1)"/>
  <rect x="630" y="65" width="70" height="20" rx="4" fill="transparent" stroke="currentColor" stroke-width="1" stroke-dasharray="2,2"/>
  <text x="665" y="75" font-family="sans-serif" font-size="10" fill="currentColor" text-anchor="middle" dominant-baseline="middle">LogSegment</text>

  <!-- KvManager details -->
  <line x1="129" y1="93" x2="200" y2="93" stroke="currentColor" stroke-width="1" marker-end="url(#arrow-fse1)"/>
  <rect x="202" y="80" width="110" height="24" rx="4" fill="transparent" stroke="currentColor" stroke-width="1" stroke-dasharray="2,2"/>
  <text x="257" y="92" font-family="sans-serif" font-size="11" fill="currentColor" text-anchor="middle" dominant-baseline="middle">KvTablet</text>

  <line x1="312" y1="88" x2="345" y2="88" stroke="currentColor" stroke-width="1" marker-end="url(#arrow-fse1)"/>
  <rect x="347" y="78" width="120" height="22" rx="4" fill="transparent" stroke="currentColor" stroke-width="1" stroke-dasharray="2,2"/>
  <text x="407" y="89" font-family="sans-serif" font-size="10" fill="currentColor" text-anchor="middle" dominant-baseline="middle">RocksDBKv</text>

  <!-- RemoteLogManager detail -->
  <line x1="133" y1="128" x2="170" y2="128" stroke="currentColor" stroke-width="1.2" marker-end="url(#arrow-fse1)"/>
  <text x="178" y="128" font-family="sans-serif" font-size="10" fill="currentColor" text-anchor="start" dominant-baseline="middle">→ S3 / HDFS / OSS</text>
</svg>

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

<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 700 190" width="700" height="190">
  <defs>
    <marker id="arrow-fse2" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <path d="M0,0 L8,3 L0,6 Z" fill="currentColor"/>
    </marker>
  </defs>
  <!-- Chain: KvManager → KvTablet → RocksDBKv -->
  <rect x="10" y="8" width="100" height="28" rx="5" fill="transparent" stroke="currentColor" stroke-width="1.2"/>
  <text x="60" y="22" font-family="sans-serif" font-size="12" fill="currentColor" text-anchor="middle" dominant-baseline="middle">KvManager</text>

  <line x1="110" y1="22" x2="145" y2="22" stroke="currentColor" stroke-width="1.2" marker-end="url(#arrow-fse2)"/>

  <rect x="148" y="8" width="90" height="28" rx="5" fill="transparent" stroke="currentColor" stroke-width="1.2"/>
  <text x="193" y="22" font-family="sans-serif" font-size="12" fill="currentColor" text-anchor="middle" dominant-baseline="middle">KvTablet</text>

  <line x1="238" y1="22" x2="278" y2="22" stroke="currentColor" stroke-width="1.2" marker-end="url(#arrow-fse2)"/>

  <rect x="281" y="8" width="110" height="28" rx="5" fill="transparent" stroke="currentColor" stroke-width="1.2"/>
  <text x="336" y="22" font-family="sans-serif" font-size="12" fill="currentColor" text-anchor="middle" dominant-baseline="middle" font-weight="bold">RocksDBKv</text>

  <!-- Down line from RocksDBKv -->
  <line x1="336" y1="36" x2="336" y2="50" stroke="currentColor" stroke-width="1.2"/>
  <!-- Branch to top sub-items -->
  <line x1="100" y1="50" x2="500" y2="50" stroke="currentColor" stroke-width="1.2"/>
  <line x1="336" y1="50" x2="336" y2="55" stroke="currentColor" stroke-width="1.2"/>

  <line x1="100" y1="50" x2="100" y2="65" stroke="currentColor" stroke-width="1.2"/>
  <line x1="220" y1="50" x2="220" y2="65" stroke="currentColor" stroke-width="1.2"/>
  <line x1="340" y1="50" x2="340" y2="65" stroke="currentColor" stroke-width="1.2"/>
  <line x1="460" y1="50" x2="460" y2="65" stroke="currentColor" stroke-width="1.2"/>

  <!-- Sub-item boxes (row 1) -->
  <text x="108" y="80" font-family="sans-serif" font-size="11" fill="currentColor" text-anchor="start" dominant-baseline="middle">├── WalBuilder</text>
  <text x="108" y="100" font-family="sans-serif" font-size="10" fill="currentColor" text-anchor="start" dominant-baseline="middle" font-style="italic">　　（Arrow / Compacted / IndexWalBuilder）</text>

  <text x="228" y="80" font-family="sans-serif" font-size="11" fill="currentColor" text-anchor="start" dominant-baseline="middle">├── SnapshotManager</text>
  <text x="228" y="100" font-family="sans-serif" font-size="10" fill="currentColor" text-anchor="start" dominant-baseline="middle" font-style="italic">　　（PeriodicSnapshot → </text>
  <text x="228" y="115" font-family="sans-serif" font-size="10" fill="currentColor" text-anchor="start" dominant-baseline="middle" font-style="italic">　　　RocksIncrementalSnapshot → </text>
  <text x="228" y="130" font-family="sans-serif" font-size="10" fill="currentColor" text-anchor="start" dominant-baseline="middle" font-style="italic">　　　Uploader → Committer）</text>

  <text x="348" y="80" font-family="sans-serif" font-size="11" fill="currentColor" text-anchor="start" dominant-baseline="middle">├── RowMerger</text>
  <text x="348" y="100" font-family="sans-serif" font-size="10" fill="currentColor" text-anchor="start" dominant-baseline="middle" font-style="italic">　　（Default / FirstRow / </text>
  <text x="348" y="115" font-family="sans-serif" font-size="10" fill="currentColor" text-anchor="start" dominant-baseline="middle" font-style="italic">　　　Versioned / Aggregate）</text>

  <text x="468" y="80" font-family="sans-serif" font-size="11" fill="currentColor" text-anchor="start" dominant-baseline="middle">├── PartialUpdater</text>
  <text x="468" y="105" font-family="sans-serif" font-size="11" fill="currentColor" text-anchor="start" dominant-baseline="middle">├── AutoIncrementManager</text>
  <text x="468" y="130" font-family="sans-serif" font-size="11" fill="currentColor" text-anchor="start" dominant-baseline="middle">└── KvPreWriteBuffer</text>
</svg>

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
