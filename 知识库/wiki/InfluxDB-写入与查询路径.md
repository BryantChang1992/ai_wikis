---
type: concept
title: "InfluxDB 写入与查询路径"
sources:
  - "技术文章/InfluxDB调研/03-写入与查询路径.md"
tags:
  - InfluxDB
  - 写入路径
  - 查询路径
  - WAL
  - DataFusion
  - 向量化
  - Compaction
created: 2026-06-14
updated: 2026-06-14
status: final
author: Stark (CTO, CHANG_AI_TEAM)
related:
  - "[[InfluxDB深度调研]]"
  - "[[InfluxDB-TSM存储引擎]]"
  - "[[InfluxDB-3-列存引擎]]"
  - "[[事务模型深度调研]]"
  - "[[LSM-Tree]]"
---

# InfluxDB 写入与查询路径

## 一、写入路径对比

### v1/v2 写入路径 (Go)

```svg
<svg viewBox="0 0 680 120" xmlns="http://www.w3.org/2000/svg">
<text x="10" y="14" font-family="sans-serif" font-size="11" fill="currentColor" text-anchor="start" dominant-baseline="middle">InfluxDB v1/v2 写入路径:</text>
<rect x="10" y="24" width="200" height="28" rx="4" fill="transparent" stroke="currentColor" stroke-width="1.2"/><text x="110" y="38" font-family="sans-serif" font-size="10" fill="currentColor" text-anchor="middle" dominant-baseline="middle">HTTP /write (Line Protocol)</text>
<line x1="210" y1="38" x2="240" y2="38" stroke="currentColor" stroke-width="1.5"/>
<text x="245" y="38" font-family="sans-serif" font-size="10" fill="currentColor" text-anchor="start" dominant-baseline="middle">├── ① WAL (Snappy Compressed, fsync to disk)</text>
<line x1="245" y1="52" x2="245" y2="68" stroke="currentColor" stroke-width="1"/>
<text x="245" y="82" font-family="sans-serif" font-size="10" fill="currentColor" text-anchor="start" dominant-baseline="middle">├── ② In-Memory Cache (Series → Time-Sorted Fields Map)</text>
<line x1="245" y1="96" x2="245" y2="110" stroke="currentColor" stroke-width="1"/>
<text x="245" y="112" font-family="sans-serif" font-size="10" fill="currentColor" text-anchor="start" dominant-baseline="middle">└── ③ TSM 文件 (Compaction × 合并为更大 TSM 文件)</text>
</svg>

```

**关键细节**：
- **WAL 和 Cache 同时写入**：WAL 确保持久性（与 [[事务模型深度调研]] 中 WAL 机制同源），Cache 确保立即可查
- **WAL 分段压缩**：每个 batch 用 Snappy 压缩后 append 到 WAL 文件
- **Cache Flush 触发条件**：Cache 大小超过阈值 (25MB) 或定时触发 (10min)
- **Compaction 层级**：每级文件大小递增，类似 [[LSM-Tree]] 的 Leveling 策略

**写放大问题**：同一条数据被反复读写——WAL(1x) → Cache → TSM L0(flush) → L0→L1(compact) → L1→L2...

### v3 写入路径 (Rust)

```svg
<svg viewBox="0 0 700 200" xmlns="http://www.w3.org/2000/svg">
<defs><marker id="v3w1" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto"><path d="M0,0 L8,3 L0,6 Z" fill="currentColor"/></marker></defs>
<text x="10" y="14" font-family="sans-serif" font-size="11" fill="currentColor" text-anchor="start" dominant-baseline="middle">InfluxDB v3 写入路径:</text>
<rect x="10" y="24" width="200" height="28" rx="4" fill="transparent" stroke="currentColor" stroke-width="1.2"/><text x="110" y="38" font-family="sans-serif" font-size="10" fill="currentColor" text-anchor="middle" dominant-baseline="middle">HTTP /write (Line Protocol)</text>
<line x1="210" y1="38" x2="240" y2="38" stroke="currentColor" stroke-width="1.5" marker-end="url(#v3w1)"/>
<rect x="245" y="24" width="200" height="28" rx="4" fill="transparent" stroke="currentColor" stroke-width="1.2"/><text x="345" y="38" font-family="sans-serif" font-size="10" fill="currentColor" text-anchor="middle" dominant-baseline="middle">Ingest Router</text>
<line x1="445" y1="38" x2="475" y2="38" stroke="currentColor" stroke-width="1.5" marker-end="url(#v3w1)"/>
<rect x="480" y="24" width="200" height="28" rx="4" fill="transparent" stroke="currentColor" stroke-width="1.2"/><text x="580" y="38" font-family="sans-serif" font-size="10" fill="currentColor" text-anchor="middle" dominant-baseline="middle">Ingester</text>
<text x="10" y="72" font-family="sans-serif" font-size="10" fill="currentColor" text-anchor="start" dominant-baseline="middle">Ingest Router: Line Protocol Parser → Consistent Hash → Ingester</text>
<text x="10" y="94" font-family="sans-serif" font-size="10" fill="currentColor" text-anchor="start" dominant-baseline="middle">Ingester Processing:</text>
<text x="25" y="112" font-family="sans-serif" font-size="10" fill="currentColor" text-anchor="start" dominant-baseline="middle">① 写入 Object Store (Parquet - Write-Optimized + Recent Write Buffer)</text>
<text x="25" y="132" font-family="sans-serif" font-size="10" fill="currentColor" text-anchor="start" dominant-baseline="middle">② 更新 Catalog (PostgreSQL/SQLite: Partition + Parquet File + Tombstone Meta)</text>
<text x="25" y="152" font-family="sans-serif" font-size="10" fill="currentColor" text-anchor="start" dominant-baseline="middle">③ 异步 Writ Buffer Flush → Compaction into Read-Optimized Parquet</text>
<text x="25" y="172" font-family="sans-serif" font-size="10" fill="currentColor" text-anchor="start" dominant-baseline="middle">④ WAL 优化: 批量写入 Object Store，非逐条 fsync</text>
</svg>

```

**关键优化**：
1. **Cardinality-Aware Sort**：按基数最低的列优先排序，最大化 Parquet 压缩效率
2. **单次写入**：数据直接写成 Parquet，无多级 Compaction 写放大
3. **毫秒级延迟**：不等待 Compaction，写入 Object Store + Catalog Update 后立即可查
4. **WAL 语义简化**：仅用于 crash recovery，不参与查询路径

### 写入路径总览

```
v1/v2: HTTP → WAL + Cache → TSI → Cache Flush → TSM L0 → Compaction L1→L2 (多次 I/O)
v3:    HTTP → Ingest Router → Ingester (校验/分区/排序/去重) → Parquet (单次写入)
```

## 二、查询路径对比

### v1/v2 查询路径 — Iterator 模型

```svg
<svg viewBox="0 0 700 120" xmlns="http://www.w3.org/2000/svg">
<text x="10" y="14" font-family="sans-serif" font-size="11" fill="currentColor" text-anchor="start" dominant-baseline="middle">InfluxDB v1/v2 查询路径:</text>
<rect x="10" y="24" width="200" height="28" rx="4" fill="transparent" stroke="currentColor" stroke-width="1.2"/><text x="110" y="38" font-family="sans-serif" font-size="10" fill="currentColor" text-anchor="middle" dominant-baseline="middle">InfluxQL / Flux Query</text>
<line x1="210" y1="38" x2="240" y2="38" stroke="currentColor" stroke-width="1.5"/>
<text x="245" y="38" font-family="sans-serif" font-size="10" fill="currentColor" text-anchor="start" dominant-baseline="middle">├── Parse & Validate → AST</text>
<line x1="245" y1="52" x2="245" y2="68" stroke="currentColor" stroke-width="1"/>
<text x="245" y="68" font-family="sans-serif" font-size="10" fill="currentColor" text-anchor="start" dominant-baseline="middle">├── TSI Index Lookup: Measurement+Tag → Series IDs → Shards</text>
<line x1="245" y1="82" x2="245" y2="96" stroke="currentColor" stroke-width="1"/>
<text x="245" y="98" font-family="sans-serif" font-size="10" fill="currentColor" text-anchor="start" dominant-baseline="middle">└── TSM File Scan (Merge from Cache + WAL + TSM Files)</text>
</svg>

```

**Iterator 模型的核心缺陷**：
- **O(N) per Series**：每个 Series 一个独立 Iterator，N 个 Series = N 个 Iterator
- **无向量化**：逐点处理，无 SIMD 加速
- **TSM Block 解码**：每次查询都需解码 TSM Block
- **单线程执行**：v1/v2 查询引擎为单线程模型

### v3 查询路径 — DataFusion 向量化

```svg
<svg viewBox="0 0 700 200" xmlns="http://www.w3.org/2000/svg">
<defs><marker id="v3q1" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto"><path d="M0,0 L8,3 L0,6 Z" fill="currentColor"/></marker></defs>
<text x="10" y="14" font-family="sans-serif" font-size="11" fill="currentColor" text-anchor="start" dominant-baseline="middle">InfluxDB v3 查询路径:</text>
<rect x="10" y="24" width="200" height="28" rx="4" fill="transparent" stroke="currentColor" stroke-width="1.2"/><text x="110" y="38" font-family="sans-serif" font-size="10" fill="currentColor" text-anchor="middle" dominant-baseline="middle">SQL (FlightSQL) / InfluxQL Query</text>
<line x1="210" y1="38" x2="240" y2="38" stroke="currentColor" stroke-width="1.5" marker-end="url(#v3q1)"/>
<rect x="245" y="24" width="200" height="28" rx="4" fill="transparent" stroke="currentColor" stroke-width="1.2"/><text x="345" y="38" font-family="sans-serif" font-size="10" fill="currentColor" text-anchor="middle" dominant-baseline="middle">Query Router → Querier</text>
<line x1="445" y1="38" x2="475" y2="38" stroke="currentColor" stroke-width="1.5" marker-end="url(#v3q1)"/>
<rect x="480" y="24" width="200" height="28" rx="4" fill="transparent" stroke="currentColor" stroke-width="1.2"/><text x="580" y="38" font-family="sans-serif" font-size="10" fill="currentColor" text-anchor="middle" dominant-baseline="middle">FlightSQL Server</text>
<text x="10" y="72" font-family="sans-serif" font-size="10" fill="currentColor" text-anchor="start" dominant-baseline="middle">Querier 处理步骤:</text>
<text x="25" y="92" font-family="sans-serif" font-size="10" fill="currentColor" text-anchor="start" dominant-baseline="middle">① Catalog Cache Sync (Table · Column · Partition Metadata)</text>
<text x="25" y="112" font-family="sans-serif" font-size="10" fill="currentColor" text-anchor="start" dominant-baseline="middle">② SQL Parse & Plan</text>
<text x="25" y="132" font-family="sans-serif" font-size="10" fill="currentColor" text-anchor="start" dominant-baseline="middle">③ Object Store Scan (Parquet File Pruning via Catalog + Filter Pushdown)</text>
<text x="25" y="152" font-family="sans-serif" font-size="10" fill="currentColor" text-anchor="start" dominant-baseline="middle">④ Merge Results → FlightSQL Stream Back to Client</text>
<text x="25" y="172" font-family="sans-serif" font-size="10" fill="currentColor" text-anchor="start" dominant-baseline="middle">⑤ DataFrame/Iceberg 集成读取已持久化数据</text>
</svg>

```

**核心突破**：
1. **无索引查找**：Parquet Statistics (Min/Max) 直接跳过不相关文件
2. **Predicate + Projection Pushdown**：存储层就完成过滤和列选择
3. **向量化执行**：4096 行 Batch，利用 SIMD 指令加速
4. **Per-Partition 并行**：每个 Partition 独立并行扫描
5. **仅重叠文件去重**：非重叠文件直接 stream，避免不必要排序

**关键结论**：查询延迟不再随 Series 基数线性增长——DataFusion 的批量处理模型从根本上消除了 v1/v2 Iterator 模型的 O(N) 瓶颈。

### 查询路径总览

```
v1/v2: Iterator Model · O(N) per Series · 逐点处理 · 无向量化
v3:    DataFusion Physical Plan · 批量 4096 行 · SIMD · 并行 · 仅重叠去重
```

---

*参考: "InfluxDB Internals 101: Data Model & Write Path" — Ryan Betts; InfluxData 官方文档*
