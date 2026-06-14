---
type: concept
title: "InfluxDB 3 列存存储引擎"
sources:
  - "技术文章/InfluxDB调研/02-存储引擎.md"
  - "技术文章/InfluxDB调研/03-写入与查询路径.md"
tags:
  - InfluxDB
  - 列存
  - Parquet
  - Arrow
  - DataFusion
  - 存储引擎
  - 存算分离
created: 2026-06-14
updated: 2026-06-14
status: final
author: Stark (CTO, CHANG_AI_TEAM)
related:
  - "[[InfluxDB深度调研]]"
  - "[[InfluxDB-TSM存储引擎]]"
  - "[[InfluxDB-写入与查询路径]]"
  - "[[存储计算分离数据库的-Tail-Latency]]"
---

# InfluxDB 3 列存存储引擎

## 定义

InfluxDB 3.0 从零开始用 Rust 重写了整个存储引擎，以 **Apache Parquet** 作为原生持久化格式，基于 **Apache Arrow** 和 **DataFusion** 构建列式查询引擎。这是 InfluxDB 历史上最根本的架构变革。

## 技术栈

| 技术 | 角色 |
|------|------|
| **Apache Arrow** | 列式内存格式，零拷贝数据交换 |
| **Apache DataFusion** | 向量化 SQL 查询引擎 |
| **Apache Parquet** | 列式持久化格式，原生统计信息 |
| **Rust** | 零成本抽象，无 GC，内存安全 |

## 存算分离架构

```
Line Protocol → Ingester → Parquet (Object Store: S3/MinIO)
                         → Catalog (PostgreSQL)
```

InfluxDB 3.0 采用**存算分离**的云原生架构，包含四个独立组件：

| 组件 | 职责 |
|------|------|
| **Ingest Router + Ingester** | 数据摄入：Line Protocol 解析、Schema 校验、分区排序、Parquet 持久化 |
| **Query Router + Querier** | 数据查询：利用 DataFusion 构建和执行查询计划 |
| **Compactor** | 后台合并小文件，优化存储布局 |
| **Garbage Collector** | 执行保留策略，回收过期数据 |

所有组件通过 **Catalog** 和 **Object Store** 进行松耦合通信——组件间无需直接通信，只通过共享存储协调状态。这与 [[存储计算分离数据库的-Tail-Latency]] 中讨论的存算分离架构有共同的设计关注点。

## Parquet 作为一等公民的优势

### 1. 内置统计信息 — 无索引剪枝

每个 Parquet Row Group / Data Page 存储 Min/Max/Null Count 统计信息，查询引擎可以通过这些元数据**直接跳过不相关文件**，无需像 TSI 那样维护全局倒排索引。这是消除基数上限的关键。

```
-- 查询: SELECT * FROM cpu WHERE host='server-a' AND time > now()-1h
-- Parquet Statistics 剪枝:
--   → 跳过 time.max < now()-1h 的 Partition
--   → 跳过 host 列 Min/Max 不含 'server-a' 的 Row Group
-- → 根本不需要索引查找！
```

### 2. 极致压缩比：10-100x

Cardinality-Aware Sort（按基数最低的列优先排序）最大化列式压缩效率：
- 低基数列（如 `region`）连续存储 → RLE/字典编码效果极佳
- 高基数列（如 `value`）利用时间序列特性 → Delta 编码 + Snappy/ZSTD

### 3. 开放标准 — 生态兼容

Parquet 可直接被 Spark、Pandas、DuckDB 等工具读取，实现**零 ETL 数据分析**。

### 4. 存算分离 — 弹性伸缩

数据存储在 S3/MinIO，计算（Ingester/Querier/Compactor）可按需独立伸缩，互不影响。

## 与 TSM 引擎的关键对比

| 维度 | TSM (v1/v2) | Columnar (v3) | 突破 |
|------|-------------|---------------|------|
| 存储格式 | TSM (自研列式) | Parquet (开放标准) | 生态兼容性 |
| 索引 | TSI 倒排索引 | Parquet Statistics | **消除基数上限** |
| 语言 | Go | Rust | 零 GC 停顿 |
| 压缩比 | 5-10x | 10-100x | 存储成本 10x 降低 |
| 写放大 | 严重 (多级 Compaction) | 低 (单次 Parquet 写) | 写入吞吐提升 |
| 扩展 | 手动分片 | 原生水平扩展 | 弹性伸缩 |

## 去重策略演进

- **v1/v2**：写入时无去重，查询时通过 Iterator 合并
- **v3**：Ingester 写入时 Sort-Merge 去重 + Querier 仅对重叠文件去重

---

*参考: "InfluxDB 3.0 System Architecture" — Nga Tran, Paul Dix, Andrew Lamb, Marko Mikulicic*
