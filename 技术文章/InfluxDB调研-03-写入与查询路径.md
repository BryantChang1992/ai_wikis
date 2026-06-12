# InfluxDB 调研 — 03 写入与查询路径

> **作者**: Stark (CTO, CHANG_AI_TEAM)
> **日期**: 2026-06-12

---

## 1. 写入路径

### 1.1 写入路径对比总览

![[diagram/influxdb-research/03-write-path.svg]]

### 1.2 InfluxDB v1/v2 写入路径

```
HTTP /write (Line Protocol)
  │
  ├── ① WAL (Snappy Compressed, fsync to disk)
  │
  ├── ② In-Memory Cache (Series → Time-Sorted Fields Map)
  │
  ├── ③ TSI Index Update (Measurement+Tag → Series ID)
  │
  ├── ④ Periodic Cache Flush → TSM L0 File (Immutable)
  │
  └── ⑤ Background Compaction: L0 → L1 → L2 → ...
```

**关键细节**：

- **WAL 和 Cache 同时写入**：WAL 确保持久性，Cache 确保立即可查
- **WAL 分段压缩**：每个 batch 用 Snappy 压缩后 append 到 WAL 文件
- **Cache Flush 触发条件**：
  - Cache 大小超过阈值（默认 25MB）
  - 定时触发（默认 10 分钟）
  - 手动执行 compact 命令
- **Compaction 层级**：每级文件大小递增，L0 为 Cache Flush 产生的小文件

**写放大问题**：同一条数据被反复读写多次——WAL (1x) → Cache → TSM L0 (flush) → L0→L1 (compact) → L1→L2 ...

### 1.3 InfluxDB 3.0 写入路径

```
HTTP /write (Line Protocol)
  │
  ├── ① Ingest Router: Line Protocol Parser → Consistent Hash → Shard to Ingester
  │
  ├── ② Ingester Processing Pipeline:
  │   ├── Schema Validation (Catalog Lookup)
  │   ├── Partition (by Time Column, default daily)
  │   ├── Multi-Column Sort-Merge (sorted by lowest cardinality columns first)
  │   ├── Deduplication (DataFusion Sort + Merge operators)
  │   ├── Parquet Encode (Snappy/ZSTD compression)
  │   └── Update Catalog (PostgreSQL: file metadata + partition info)
  │
  ├── ③ Persist to Object Store (Single Write)
  │
  ├── ④ WAL (EBS, short-term crash recovery only)
  │
  └── ⑤ Background Compaction: Small → Large Non-Overlapping Files (Low Priority)
```

**关键优化**：

1. **Cardinality-Aware Sort**：按基数最低的列优先排序，最大化 Parquet 压缩效率（10-100x）
2. **单次写入**：数据直接写成 Parquet 持久化到 Object Store，无 Cache Flush + 多级 Compaction 写放大
3. **毫秒级写入延迟**：不等待 Compaction 完成，数据写入 Object Store + Catalog Update 后立即可查
4. **WAL 语义简化**：仅用于 Ingester crash recovery，不参与查询路径

---

## 2. 查询路径

### 2.1 查询路径对比总览

![[diagram/influxdb-research/04-query-path.svg]]

### 2.2 InfluxDB v1/v2 查询路径

```
InfluxQL / Flux Query
  │
  ├── Parse & Validate → AST
  ├── TSI Index Lookup: Measurement+Tag → Series IDs → Shards
  ├── TSM File Scan + Cache Lookup
  │   └── Read TSM Blocks → Decode → Field Iterator
  └── Execute & Aggregate: Merge Iterators → Filter → Group → JSON/CSV
```

**v1/v2 查询模型的核心问题**：

- **Iterator Model（迭代器模型）**：每个 Series 一个独立的 Iterator，N 个 Series = N 个 Iterator
- **查询代价 O(N)**：Series 越多，需要 Merge 的 Iterator 越多，延迟线性增长
- **无向量化**：逐点处理，无 SIMD 加速
- **TSM Block 解码**：每次查询都需解码 TSM Block，无列剪枝优化
- **单线程执行**：v1/v2 查询引擎为单线程模型

**Flux 引擎的额外开销**：Flux 是一个独立的脚本语言引擎（VM），引入了额外的解析和执行开销。InfluxDB 3 已宣布 Flux 进入维护模式，未来重点在 SQL + InfluxQL。

### 2.3 InfluxDB 3.0 查询路径

```
SQL (FlightSQL) / InfluxQL (Flight) Query
  │
  ├── Query Router → Querier (负载均衡)
  │
  ├── ① Catalog Cache Sync (Table · Column · Partition Metadata)
  │
  ├── ② Data Cache Warm-up (Parquet → Arrow RecordBatch, only needed columns)
  │
  ├── ③ Fetch Unpersisted Data from Ingester (RPC)
  │   └── Also learn schema changes, invalidate stale cache
  │
  ├── ④ Query Optimizer — DataFusion Physical Plan:
  │   ├── Partition Pruning (skip unneeded partitions by time range)
  │   ├── Predicate Pushdown (filter at Parquet scan level)
  │   └── Column Pruning (read only queried columns)
  │
  ├── ⑤ Parallel Execution (DataFusion):
  │   └── ParquetExec → FilterExec → SortMerge(Dedup) → AggregateExec
  │       └── Per-Partition Parallelism · SIMD Vectorized
  │
  └── ⑥ Arrow Flight / JSON Result → Client (Streaming, Zero-Copy)
```

### 2.4 查询性能的核心突破

1. **无索引查找**：通过 Parquet Statistics (Min/Max) 直接跳过不相关文件，无需维护全局索引
2. **Predicate + Projection Pushdown**：在存储层就完成过滤和列选择，减少读取量
3. **向量化执行**：每次 operate 处理 4096 行 Batch，利用 SIMD 指令加速
4. **Per-Partition 并行**：每个 Partition 独立并行扫描，多核利用率高
5. **仅重叠文件去重**：非重叠文件直接 stream，避免不必要的排序开销
6. **查询延迟不再随 Series 基数线性增长**：DataFusion 的批量处理模型从根本上消除了 v1/v2 Iterator 模型的 O(N) 瓶颈

---

## 3. 写入/查询路径对比总结

```
v1/v2 写入： HTTP → WAL + Cache → TSI → Cache Flush → TSM L0 → Compaction L1→L2 (多次 I/O)
v3   写入：  HTTP → Ingest Router → Ingester (校验/分区/排序/去重) → Parquet (单次写入)

v1/v2 查询： Iterator Model · O(N) per Series · 逐点处理 · 无向量化
v3   查询：  DataFusion Physical Plan · 批量 4096 行 · SIMD · 并行 · 仅重叠去重
```

---

> **上一篇**: [02-存储引擎](InfluxDB调研-02-存储引擎.md)
> **下一篇**: [04-指标设计最佳实践](InfluxDB调研-04-指标设计最佳实践.md)
