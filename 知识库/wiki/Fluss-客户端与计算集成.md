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
---

# Fluss 客户端与计算集成分析

## 概述

Fluss 客户端 API 在 Kafka Producer/Consumer 范式上做了根本性的扩展——从"一个 Producer + 一个 Consumer"变为**Writer / Scanner / Lookuper 三种角色**，对应不同的数据访问模式。同时原生集成了 Flink/Spark 计算引擎，提供 Catalog/Source/Sink/Lookup Join/Tiering 全链路。

## 客户端架构

```
FlussTable（统一表访问入口）
  ├── Writer 层
  │   ├── AppendWriter    → 追加写入（≈ KafkaProducer.send）
  │   ├── UpsertWriter    → 写入/更新（PK 表专用）
  │   └── TableWriter<T>  → 类型化写入器
  ├── Scanner 层
  │   ├── LogScanner      → 顺序日志扫描
  │   ├── BatchScanner    → 批量扫描（快照 + 日志合并）
  │   │   ├── KvBatchScanner        → KV 快照过滤扫描
  │   │   ├── KvSnapshotBatchScanner → 纯快照扫描
  │   │   ├── LimitBatchScanner     → Limit 扫描
  │   │   └── CompositeBatchScanner → 多源组合扫描
  │   └── RemoteLogDownloader       → 远程日志透明下载
  └── Lookuper 层
      ├── PrimaryKeyLookuper  → PK 精确查找
      └── PrefixKeyLookuper   → 前缀查找
```

## 写入路径

与 Kafka Producer 架构相似但有重要扩展：

```
AppendWriter → RecordAccumulator → BucketAssigner → Sender → TabletServer
```

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

```
INSERT INTO fluss_table SELECT ...
  → FlussSink → SinkWriter (pre-commit → commit cycle)
    → RecordAccumulator (batch buffer)
    → AppendWriter / UpsertWriter
      → TabletServer (ProduceLog / PutKv)
```

### Source 读取模型

```
SELECT * FROM fluss_table
  → FlussSource → FlussSourceEnumerator (split discovery)
    → LogSplit / KvSnapshotSplit / LakeSplit
  → FlussSourceReader → FlussSplitReader
    → LogScanner (log split)
    → KvBatchScanner (snapshot split)
    → IcebergLakeSource / PaimonLakeSource (lake split)
```

Flink Source 能同时从三种 Split 类型读取数据——这是"流批一体"在 Source 层的具体实现。

## 数据转换层

Fluss 的类型系统通过 `FlussRowToFlinkRowConverter` 实现 Arrow ↔ Flink RowData 的双向转换。关键路径：Arrow Vector → InternalRow → Flink RowData（零列拷贝，仅指针偏移）。

---

> **关键洞察**：Fluss 客户端 API 的设计暗含了一个重要的产品定位——**不只是消息队列，更是实时特征存储**。Lookup Join（维表关联）和 PrefixLookup（前缀索引）的功能说明 Fluss 的 PK 表可以充当 Flink 作业中的在线特征存储，这是 Kafka 做不到的。而多 Split 类型的 Source 支持（Log/KvSnapshot/Lake）意味着 Fluss 在"流批一体"的数据访问层已经做了架构准备。
