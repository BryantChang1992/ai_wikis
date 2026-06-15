---
type: analysis
title: "Fluss 客户端与计算集成分析"
sources:
  - "https://github.com/BryantChang1992/ai_memory_chang_ai_team/blob/master/tech_research/fluss/05-客户端与计算集成.html"
tags:
  - "Fluss"
  - "客户端"
  - "Flink"
  - "Connector"
  - "源码分析"
created: 2026-06-15
updated: 2026-06-15
status: draft
related:
  - "[[Fluss-整体架构]]"
  - "[[Fluss-存储引擎]]"
  - "[[Fluss-Lake层与湖仓融合]]"
  - "[[Fluss-KV存储-RocksDB]]"
diagram: "diagram/fluss-architecture.svg"

---

# Fluss 客户端与计算集成分析

## 概述

Fluss 客户端 API 在 Kafka Producer/Consumer 范式上做了根本性的扩展——从"一个 Producer + 一个 Consumer"变为**Writer / Scanner / Lookuper 三种角色**，对应不同的数据访问模式。同时原生集成了 Flink/Spark 计算引擎，提供 Catalog/Source/Sink/Lookup Join/Tiering 全链路。

## 客户端架构

<svg viewBox="0 0 780 520" xmlns="http://www.w3.org/2000/svg" style="max-width:100%;height:auto">
  <defs>
    <marker id="a1" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <path d="M0,0 L8,3 L0,6 Z" fill="currentColor"/>
    </marker>
  </defs>
  <style>
    text { font-family: sans-serif; font-size: 13px; fill: currentColor; dominant-baseline: middle; text-anchor: middle; }
  </style>

  <!-- Root -->
  <rect x="280" y="10" width="200" height="36" rx="4" fill="transparent" stroke="currentColor" stroke-width="2"/>
  <text x="380" y="28" font-weight="bold" font-size="14">FlussTable</text>
  <text x="380" y="43" font-size="11">（统一表访问入口）</text>

  <!-- Vertical trunk -->
  <line x1="380" y1="46" x2="380" y2="70" stroke="currentColor" stroke-width="1.5" marker-end="url(#a1)"/>

  <!-- Horizontal trunk -->
  <line x1="380" y1="75" x2="380" y2="80" stroke="currentColor" stroke-width="1.5"/>
  <line x1="380" y1="80" x2="680" y2="80" stroke="currentColor" stroke-width="1.5"/>
  <line x1="380" y1="80" x2="100" y2="80" stroke="currentColor" stroke-width="1.5"/>

  <!-- Branch to Writer -->
  <line x1="100" y1="80" x2="100" y2="95" stroke="currentColor" stroke-width="1.5" marker-end="url(#a1)"/>
  <rect x="25" y="100" width="150" height="30" rx="4" fill="transparent" stroke="currentColor" stroke-width="1.5"/>
  <text x="100" y="120" font-weight="bold">Writer 层</text>

  <line x1="100" y1="130" x2="100" y2="145" stroke="currentColor" stroke-width="1.5" marker-end="url(#a1)"/>
  <rect x="10" y="150" width="180" height="24" rx="3" fill="transparent" stroke="currentColor"/>
  <text x="100" y="167" font-size="12">AppendWriter → 追加写入</text>
  <text x="100" y="182" font-size="10" opacity="0.7">（≈ KafkaProducer.send）</text>

  <line x1="100" y1="190" x2="100" y2="200" stroke="currentColor" stroke-width="1" stroke-dasharray="2,2"/>
  <rect x="10" y="205" width="180" height="24" rx="3" fill="transparent" stroke="currentColor"/>
  <text x="100" y="222" font-size="12">UpsertWriter → 写入/更新</text>
  <text x="100" y="237" font-size="10" opacity="0.7">（PK 表专用）</text>

  <line x1="100" y1="245" x2="100" y2="255" stroke="currentColor" stroke-width="1" stroke-dasharray="2,2"/>
  <rect x="10" y="260" width="180" height="24" rx="3" fill="transparent" stroke="currentColor"/>
  <text x="100" y="277" font-size="12">TableWriter&lt;T&gt; → 类型化写入器</text>

  <!-- Branch to Scanner -->
  <line x1="380" y1="80" x2="380" y2="95" stroke="currentColor" stroke-width="1.5" marker-end="url(#a1)"/>
  <rect x="305" y="100" width="150" height="30" rx="4" fill="transparent" stroke="currentColor" stroke-width="1.5"/>
  <text x="380" y="120" font-weight="bold">Scanner 层</text>

  <line x1="380" y1="130" x2="380" y2="145" stroke="currentColor" stroke-width="1.5" marker-end="url(#a1)"/>
  <rect x="290" y="150" width="180" height="24" rx="3" fill="transparent" stroke="currentColor"/>
  <text x="380" y="167" font-size="12">LogScanner → 顺序日志扫描</text>

  <line x1="380" y1="174" x2="380" y2="187" stroke="currentColor" stroke-width="1" stroke-dasharray="2,2"/>
  <rect x="290" y="192" width="180" height="24" rx="3" fill="transparent" stroke="currentColor"/>
  <text x="380" y="209" font-size="12">BatchScanner → 批量扫描</text>
  <text x="380" y="224" font-size="10" opacity="0.7">（快照 + 日志合并）</text>

  <line x1="380" y1="232" x2="380" y2="244" stroke="currentColor" stroke-width="1"/>
  <line x1="380" y1="244" x2="250" y2="244" stroke="currentColor" stroke-width="1"/>
  <line x1="250" y1="244" x2="250" y2="258" stroke="currentColor" stroke-width="1" marker-end="url(#a1)"/>
  <text x="250" y="275" font-size="11">KvBatchScanner</text>
  <text x="250" y="290" font-size="11">KvSnapshotBatchScanner</text>
  <text x="250" y="305" font-size="11">LimitBatchScanner</text>
  <text x="250" y="320" font-size="11">CompositeBatchScanner</text>

  <line x1="380" y1="244" x2="510" y2="244" stroke="currentColor" stroke-width="1"/>
  <line x1="510" y1="244" x2="510" y2="258" stroke="currentColor" stroke-width="1" marker-end="url(#a1)"/>
  <text x="510" y="275" font-size="11">RemoteLogDownloader</text>
  <text x="510" y="290" font-size="11">→ 远程日志透明下载</text>

  <!-- Branch to Lookuper -->
  <line x1="680" y1="80" x2="680" y2="95" stroke="currentColor" stroke-width="1.5" marker-end="url(#a1)"/>
  <rect x="605" y="100" width="150" height="30" rx="4" fill="transparent" stroke="currentColor" stroke-width="1.5"/>
  <text x="680" y="120" font-weight="bold">Lookuper 层</text>

  <line x1="680" y1="130" x2="680" y2="145" stroke="currentColor" stroke-width="1.5" marker-end="url(#a1)"/>
  <rect x="590" y="150" width="180" height="24" rx="3" fill="transparent" stroke="currentColor"/>
  <text x="680" y="167" font-size="12">PrimaryKeyLookuper → PK 精确查找</text>

  <line x1="680" y1="174" x2="680" y2="187" stroke="currentColor" stroke-width="1" stroke-dasharray="2,2"/>
  <rect x="590" y="192" width="180" height="24" rx="3" fill="transparent" stroke="currentColor"/>
  <text x="680" y="209" font-size="12">PrefixKeyLookuper → 前缀查找</text>
</svg>

## 写入路径

与 Kafka Producer 架构相似但有重要扩展：

<svg viewBox="0 0 700 50" xmlns="http://www.w3.org/2000/svg" style="max-width:100%;height:auto">
  <defs>
    <marker id="a2" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <path d="M0,0 L8,3 L0,6 Z" fill="currentColor"/>
    </marker>
  </defs>
  <style>
    text { font-family: sans-serif; font-size: 13px; fill: currentColor; dominant-baseline: middle; text-anchor: middle; }
  </style>
  <rect x="10" y="8" width="110" height="30" rx="4" fill="transparent" stroke="currentColor"/>
  <text x="65" y="23" font-size="12">AppendWriter</text>
  <line x1="120" y1="23" x2="145" y2="23" stroke="currentColor" stroke-width="1.5" marker-end="url(#a2)"/>
  <rect x="150" y="8" width="130" height="30" rx="4" fill="transparent" stroke="currentColor"/>
  <text x="215" y="23" font-size="12">RecordAccumulator</text>
  <line x1="280" y1="23" x2="305" y2="23" stroke="currentColor" stroke-width="1.5" marker-end="url(#a2)"/>
  <rect x="310" y="8" width="110" height="30" rx="4" fill="transparent" stroke="currentColor"/>
  <text x="365" y="23" font-size="12">BucketAssigner</text>
  <line x1="420" y1="23" x2="445" y2="23" stroke="currentColor" stroke-width="1.5" marker-end="url(#a2)"/>
  <rect x="450" y="8" width="75" height="30" rx="4" fill="transparent" stroke="currentColor"/>
  <text x="487" y="23" font-size="12">Sender</text>
  <line x1="525" y1="23" x2="550" y2="23" stroke="currentColor" stroke-width="1.5" marker-end="url(#a2)"/>
  <rect x="555" y="8" width="110" height="30" rx="4" fill="transparent" stroke="currentColor"/>
  <text x="610" y="23" font-size="12">TabletServer</text>
</svg>

### 写入批次类型

| 批次类 | LogFormat | 适用表类型 |
|--------|-----------|-----------|
| `ArrowLogWriteBatch` | ARROW | 所有类型 |
| `CompactedLogWriteBatch` | COMPACTED | PK 表 |
| `IndexedLogWriteBatch` | INDEXED | PK 表（点查优化） |
| `KvWriteBatch` | — | PK 表（RocksDB 写入） |

### BucketAssigner 五种策略

| 策略 | 类 | 说明 |
|------|-----|------|
| **Hash** | `HashBucketAssigner` | 基于 key hash 路由（默认） |
| **RoundRobin** | `RoundRobinBucketAssigner` | 轮询 |
| **Static** | `StaticBucketAssigner` | 固定映射 |
| **Sticky** | `StickyBucketAssigner` | 粘性分配，同 writer 尽量同 bucket |
| **Dynamic** | `DynamicBucketAssigner` | 动态路由 + 自动分区创建 |

### IdempotenceManager

基于 `writerId + sequenceNumber + bucket-based tracking` 保证同一 Writer 的同一 offset 只写入一次。与 Kafka 幂等生产者类似但无事务支持。

## 读取路径

### 与 KafkaConsumer 关键差异

| 特性 | Fluss Scanner | Kafka 2.7.2 Consumer |
|------|--------------|---------------------|
| API | `scanner.poll() → Iterator<ScanRecord>` | `consumer.poll() → ConsumerRecords` |
| 读取语义 | Log scan / Batch scan (snapshot+log) / Lookup | Log scan only |
| 点查 | ✅ `Lookuper.lookup(key)` / `prefixLookup(prefix)` | ❌ |
| 范围扫描 | ✅ `LimitBatchScanner.limitScan()` | ❌ 需 seek + poll 模拟 |
| 谓词下推 | ✅ Arrow 列裁剪 + 统计信息 | ❌ |
| 远程数据 | ✅ `RemoteLogDownloader` 透明下载 | ❌ |
| 快照读取 | ✅ 从 Lake snapshot 直接读 Parquet | ❌ |
| Offset 管理 | 用户自行管理 | Consumer Group 协议自动管理 |

### BatchScanner：快照+日志合并

`CompositeBatchScanner` 的核心逻辑：
1. 获取 KV 快照列表（GetLatestKvSnapshots）
2. 下载快照文件（从远程存储 S3/HDFS）
3. 读取快照 + 合并后续 changelog（增量）
4. 对用户呈现一致视图

这是"快照 + changelog"模式的典型实现——类似数据库的 checkpoint + WAL replay。

## Flink Connector 集成

### 模块结构（215 个 Java 文件）

```
fluss-flink/
├── fluss-flink-1.18/     → Flink 1.18 适配
├── fluss-flink-1.19/     → Flink 1.19 适配
├── fluss-flink-1.20/     → Flink 1.20 适配（DummyClass 仅占位）
├── fluss-flink-2.2/      → Flink 2.2 适配
├── fluss-flink-common/   → 共享逻辑
└── fluss-flink-tiering/  → Lake Tiering 独立入口
```

### 核心能力矩阵

| 功能 | 实现 | Kafka 对应 |
|------|------|-----------|
| **Catalog** | `FlinkCatalog` / `FlinkCatalogFactory` | 无标准 Catalog |
| **Source** | `FlussSource → FlussSourceReader → FlussSplitReader` | `FlinkKafkaConsumer` |
| **Sink** | `FlussSink → SinkWriter → PreWriteBuffer` | `FlinkKafkaProducer` |
| **Lookup Join** | `FlussLookupFunction`（点查维表关联） | 无（需借助 HBase/JDBC） |
| **Changelog Stream** | `FlussChangelogSource`（CDC 流，区分 INSERT/UPDATE/DELETE） | `FlinkKafkaConsumer`（无 CHANGE 类型） |
| **Tiering** | `TieringCommitOperator` / `TieringCommitter` | 无 |
| **谓词下推** | `PushdownUtils → PredicateConverter` | 不支持下推 |
| **Arrow 转换** | `FlussRowToFlinkRowConverter ↔ Arrow ↔ RowData` | 无 Arrow |
| **RoaringBitmap** | `RbBuildAggFunction` / `RbAndAggFunction` / `RbOrAggFunction` | 无 |

### Sink 写入模型

<svg viewBox="0 0 780 130" xmlns="http://www.w3.org/2000/svg" style="max-width:100%;height:auto">
  <defs>
    <marker id="a3" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <path d="M0,0 L8,3 L0,6 Z" fill="currentColor"/>
    </marker>
  </defs>
  <style>
    text { font-family: sans-serif; font-size: 13px; fill: currentColor; dominant-baseline: middle; text-anchor: middle; }
  </style>
  <text x="10" y="15" font-size="12" text-anchor="start">INSERT INTO fluss_table SELECT ...</text>

  <rect x="10" y="35" width="110" height="30" rx="4" fill="transparent" stroke="currentColor"/>
  <text x="65" y="55" font-size="12">FlussSink</text>

  <line x1="120" y1="50" x2="145" y2="50" stroke="currentColor" stroke-width="1.5" marker-end="url(#a3)"/>

  <rect x="150" y="30" width="160" height="40" rx="4" fill="transparent" stroke="currentColor"/>
  <text x="230" y="45" font-size="12">SinkWriter</text>
  <text x="230" y="62" font-size="11">(pre-commit → commit cycle)</text>

  <line x1="310" y1="50" x2="335" y2="50" stroke="currentColor" stroke-width="1.5" marker-end="url(#a3)"/>

  <rect x="340" y="35" width="140" height="30" rx="4" fill="transparent" stroke="currentColor"/>
  <text x="410" y="55" font-size="12">RecordAccumulator</text>
  <text x="410" y="70" font-size="10" opacity="0.7">(batch buffer)</text>

  <line x1="480" y1="50" x2="505" y2="50" stroke="currentColor" stroke-width="1.5" marker-end="url(#a3)"/>

  <rect x="510" y="25" width="130" height="45" rx="4" fill="transparent" stroke="currentColor"/>
  <text x="575" y="40" font-size="12">AppendWriter</text>
  <text x="575" y="55" font-size="12">/ UpsertWriter</text>

  <line x1="640" y1="50" x2="665" y2="50" stroke="currentColor" stroke-width="1.5" marker-end="url(#a3)"/>

  <rect x="670" y="35" width="100" height="30" rx="4" fill="transparent" stroke="currentColor"/>
  <text x="720" y="55" font-size="12">TabletServer</text>
  <text x="720" y="72" font-size="10" opacity="0.7">(ProduceLog / PutKv)</text>
</svg>

### Source 读取模型

<svg viewBox="0 0 780 180" xmlns="http://www.w3.org/2000/svg" style="max-width:100%;height:auto">
  <defs>
    <marker id="a4" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <path d="M0,0 L8,3 L0,6 Z" fill="currentColor"/>
    </marker>
  </defs>
  <style>
    text { font-family: sans-serif; font-size: 13px; fill: currentColor; dominant-baseline: middle; text-anchor: middle; }
  </style>
  <text x="10" y="18" font-size="12" text-anchor="start">SELECT * FROM fluss_table</text>

  <rect x="10" y="35" width="130" height="30" rx="4" fill="transparent" stroke="currentColor"/>
  <text x="75" y="55" font-size="12">FlussSource</text>

  <line x1="140" y1="50" x2="165" y2="50" stroke="currentColor" stroke-width="1.5" marker-end="url(#a4)"/>

  <rect x="170" y="30" width="180" height="40" rx="4" fill="transparent" stroke="currentColor"/>
  <text x="260" y="45" font-size="12">FlussSourceEnumerator</text>
  <text x="260" y="62" font-size="11">(split discovery)</text>

  <line x1="350" y1="55" x2="350" y2="80" stroke="currentColor" stroke-width="1.5"/>
  <line x1="250" y1="80" x2="450" y2="80" stroke="currentColor" stroke-width="1.5"/>

  <line x1="250" y1="80" x2="250" y2="95" stroke="currentColor" stroke-width="1.5" marker-end="url(#a4)"/>
  <rect x="180" y="100" width="140" height="24" rx="3" fill="transparent" stroke="currentColor"/>
  <text x="250" y="117" font-size="12">LogSplit</text>

  <line x1="350" y1="80" x2="350" y2="95" stroke="currentColor" stroke-width="1.5" marker-end="url(#a4)"/>
  <rect x="280" y="100" width="140" height="24" rx="3" fill="transparent" stroke="currentColor"/>
  <text x="350" y="117" font-size="12">KvSnapshotSplit</text>

  <line x1="450" y1="80" x2="450" y2="95" stroke="currentColor" stroke-width="1.5" marker-end="url(#a4)"/>
  <rect x="380" y="100" width="140" height="24" rx="3" fill="transparent" stroke="currentColor"/>
  <text x="450" y="117" font-size="12">LakeSplit</text>

  <line x1="250" y1="124" x2="250" y2="140" stroke="currentColor" stroke-width="1" stroke-dasharray="2,2"/>
  <line x1="350" y1="124" x2="350" y2="140" stroke="currentColor" stroke-width="1" stroke-dasharray="2,2"/>
  <line x1="450" y1="124" x2="450" y2="140" stroke="currentColor" stroke-width="1" stroke-dasharray="2,2"/>
  <line x1="250" y1="140" x2="450" y2="140" stroke="currentColor" stroke-width="1"/>
  <line x1="350" y1="140" x2="350" y2="155" stroke="currentColor" stroke-width="1.5" marker-end="url(#a4)"/>

  <rect x="275" y="160" width="150" height="24" rx="3" fill="transparent" stroke="currentColor"/>
  <text x="350" y="177" font-size="12">FlussSourceReader</text>
  <text x="350" y="192" font-size="11">→ FlussSplitReader</text>

  <rect x="525" y="100" width="150" height="24" rx="3" fill="transparent" stroke="currentColor"/>
  <text x="600" y="117" font-size="11">LogScanner (log split)</text>

  <rect x="525" y="130" width="150" height="24" rx="3" fill="transparent" stroke="currentColor"/>
  <text x="600" y="147" font-size="11">KvBatchScanner (snapshot split)</text>

  <rect x="525" y="160" width="170" height="24" rx="3" fill="transparent" stroke="currentColor"/>
  <text x="610" y="177" font-size="11">IcebergLakeSource / PaimonLakeSource</text>
  <text x="610" y="192" font-size="10" opacity="0.7">(lake split)</text>

  <line x1="450" y1="112" x2="520" y2="117" stroke="currentColor" stroke-width="1" stroke-dasharray="2,2" marker-end="url(#a4)"/>
  <line x1="450" y1="112" x2="520" y2="142" stroke="currentColor" stroke-width="1" stroke-dasharray="2,2" marker-end="url(#a4)"/>
  <line x1="450" y1="112" x2="530" y2="172" stroke="currentColor" stroke-width="1" stroke-dasharray="2,2" marker-end="url(#a4)"/>
</svg>

Flink Source 能同时从三种 Split 类型读取数据——这是"流批一体"在 Source 层的具体实现。

## 数据转换层

Fluss 的类型系统通过 `FlussRowToFlinkRowConverter` 实现 Arrow ↔ Flink RowData 的双向转换。关键路径：Arrow Vector → InternalRow → Flink RowData（零列拷贝，仅指针偏移）。

---

> **关键洞察**：Fluss 客户端 API 的设计暗含了一个重要的产品定位——**不只是消息队列，更是实时特征存储**。Lookup Join（维表关联）和 PrefixLookup（前缀索引）的功能说明 Fluss 的 PK 表可以充当 Flink 作业中的在线特征存储，这是 Kafka 做不到的。而多 Split 类型的 Source 支持（Log/KvSnapshot/Lake）意味着 Fluss 在"流批一体"的数据访问层已经做了架构准备。
