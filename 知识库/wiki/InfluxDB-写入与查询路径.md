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

![Architecture Diagram](../diagram/influxdb-read-write-path.svg)
## 一、写入路径对比

### v1/v2 写入路径 (Go)

```svg

![InfluxDB-写入与查询路径 - 图1](../diagram/InfluxDB-写入与查询路径-fig1.svg)



```

**关键细节**：
- **WAL 和 Cache 同时写入**：WAL 确保持久性（与 [[事务模型深度调研]] 中 WAL 机制同源），Cache 确保立即可查
- **WAL 分段压缩**：每个 batch 用 Snappy 压缩后 append 到 WAL 文件
- **Cache Flush 触发条件**：Cache 大小超过阈值 (25MB) 或定时触发 (10min)
- **Compaction 层级**：每级文件大小递增，类似 [[LSM-Tree]] 的 Leveling 策略

**写放大问题**：同一条数据被反复读写——WAL(1x) → Cache → TSM L0(flush) → L0→L1(compact) → L1→L2...

### v3 写入路径 (Rust)

```svg

![InfluxDB-写入与查询路径 - 图2](../diagram/InfluxDB-写入与查询路径-fig2.svg)



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

![InfluxDB-写入与查询路径 - 图3](../diagram/InfluxDB-写入与查询路径-fig3.svg)



```

**Iterator 模型的核心缺陷**：
- **O(N) per Series**：每个 Series 一个独立 Iterator，N 个 Series = N 个 Iterator
- **无向量化**：逐点处理，无 SIMD 加速
- **TSM Block 解码**：每次查询都需解码 TSM Block
- **单线程执行**：v1/v2 查询引擎为单线程模型

### v3 查询路径 — DataFusion 向量化

```svg

![InfluxDB-写入与查询路径 - 图4](../diagram/InfluxDB-写入与查询路径-fig4.svg)

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
