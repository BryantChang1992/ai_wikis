---
type: synthesis
title: 技术综述：OLAP 与时序数据库全景综述
sources:
- '[[知识库/wiki/Doris-深度调研]]'
- '[[知识库/wiki/Doris-数据模型]]'
- '[[知识库/wiki/Doris-Segment-v2-存储格式]]'
- '[[知识库/wiki/Doris-Compaction-策略]]'
- '[[知识库/wiki/Doris-MPP-向量化查询引擎]]'
- '[[知识库/wiki/Doris-Nereids-CBO-优化器]]'
- '[[知识库/wiki/Doris-架构演进]]'
- '[[知识库/wiki/Doris-元数据与一致性复制]]'
- '[[知识库/wiki/InfluxDB深度调研]]'
- '[[知识库/wiki/InfluxDB-数据模型]]'
- '[[知识库/wiki/InfluxDB-TSM存储引擎]]'
- '[[知识库/wiki/InfluxDB-3-列存引擎]]'
- '[[知识库/wiki/InfluxDB-写入与查询路径]]'
- '[[知识库/wiki/InfluxDB-指标设计与基数管理]]'
- '[[知识库/wiki/InfluxDB-多副本与高可用]]'
- '[[知识库/wiki/InfluxDB-Catalog元数据]]'
tags:
- OLAP
- 时序数据库
- 数据分析
- 综述
created: 2026-06-14
updated: 2026-06-14
status: draft
related:
- '[[知识库/wiki/synthesis/LSM-Tree-存储引擎体系综述]]'
- '[[知识库/wiki/事务模型深度调研]]'
confidence: 0.8
confidence_rationale: 类型=synthesis; 更新于22天前
synced_at: '2026-10-05'
blog_url: https://bryantchang1992.github.io/ai_memory_chang_ai_team/posts/wiki-synthesis-olap-tsdb/
blog_source: _posts/2026-06-14-wiki-synthesis-olap-tsdb.md
blog_source_commit: f83970fa7e6ad32d626cc6ca3ba7428c90a638a5
blog_body_sha256: f73ddb7ee71de83e29e9413c87ff98010ca18f5a7ec5d2577cceb70474e9fad0
---

> 本文是 **Wiki Synthesize（知识库领域提炼）** 首轮综述之二。基于 17 张 wiki 卡片（Doris 8 张 + InfluxDB 8 张 + 调研报告）。[[技术文章/博客同步/tech-research-week-05|完整周报]] · [子调研详情](https://bryantchang1992.github.io/ai_memory_chang_ai_team/tech_research/wiki_synthesis/week_01_2026-06-14.html)

---

## 赛道定义

| 赛道 | 代表系统 | 核心场景 | 数据特征 |
|------|---------|---------|---------|
| OLAP（在线分析处理） | Doris, ClickHouse, StarRocks | 多维聚合查询、BI 报表、实时分析 | 大批量写入、列式存储、宽表 |
| 时序数据库（TSDB） | InfluxDB, TimescaleDB, TDengine | 监控、IoT、金融行情 | 追加写入、时间有序、高压缩率 |

---

## 存储引擎对比

| 维度 | Doris | InfluxDB |
|------|-------|----------|
| 引擎类型 | Segment v2（自研列式） | TSM（时序优化 LSM）→ 3.0 列存 |
| 索引设计 | ZoneMap / BloomFilter / Bitmap / Inverted | TSI（倒排索引，Tag 维度） |
| Compaction | Cumulative / Base / Quick / Vertical 四种策略 | 自动合并 + 碎片清理 |
| 编码压缩 | RLE / BitPacking / Dict / ZSTD | 时序专用（Delta / Gorilla / Simple8b） |
| 数据模型 | 宽表 + Aggregate Key | 窄表 + Tag/Field/Timestamp |
| 与 LSM-Tree 关系 | 不直接基于 LSM | TSM 是 LSM 变体；3.0 列存脱离 LSM |

---

## 核心差异根因

两个系统的工程选择差异本质上是**场景驱动**的：

| 差异 | Doris | InfluxDB | 原因 |
|------|-------|----------|------|
| 查询模式 | 全表扫描聚合 | 时间范围 + Tag 过滤 | BI 报表 vs 实时监控 |
| 写入模式 | 批量导入 / Stream Load | 逐点写入 / 批量写入 | 定时报表 vs 实时采集 |
| 一致性需求 | 强一致（2PC + WAL） | 最终一致 / 可调 | 财务数据 vs 可容忍丢点 |
| 扩展方式 | 水平分片（Tablet）+ Scale-out | 分片/副本 + 3.0 存算分离 | 各自按场景优化 |

**关键洞察**：数据模型哲学决定了工程复杂度。Doris 的宽表 + Aggregate Key 模型 vs InfluxDB 的窄表 + Tag/Field 模型，差异来源是查询模式。OLAP 不存在 Series Cardinality 爆炸问题，而 TSDB 的基数管理是核心工程挑战——这是场景决定的，不是谁的工程水平更高。

---

## 架构趋同趋势

尽管出发点不同，两大赛道在以下方向上正在快速融合：

### 1. 存算分离

Doris 3.0 和 InfluxDB 3.0 **都走向了存算分离架构**。Doris 通过 Compute-Storage Separation 实现了弹性扩缩容，InfluxDB 3.0 则通过 Object Store + 存算分离彻底解决了 TSM 引擎的碎片化和本地存储限制。

### 2. 列式存储

InfluxDB 3.0 从 TSM（行层 + 列层混合）转向**纯列式**（Parquet + Arrow Flight），这意味着时序数据库的存储引擎正在向 OLAP 靠拢。Doris 从一开始就是自研列式引擎（Segment v2），而 InfluxDB 选择了更工业标准化的 Parquet 路径。

### 3. Lakehouse 集成

Doris 支持 Iceberg/Hudi 联邦查询（Lakehouse Catalog），InfluxDB 3.0 原生支持 Parquet 在对象存储上读写。当所有数据都以开放格式存储在对象存储上，专门的数据库还有多少存在理由？这是两大赛道共同的"存在性"问题。

### 4. 向量化执行

Doris 的 MPP 查询引擎已成熟支持 SIMD 向量化执行，InfluxDB 3.0 通过 Apache DataFusion/Arrow 获得了向量化能力。查询引擎的技术栈正在统一到 Arrow 生态。

---

## 三个关键洞察

### Insight 1：存储引擎是场景的投影

LSM-Tree 是写优化引擎，适合高速写入场景（时序数据、消息队列）。列式引擎是读优化引擎，适合扫描聚合场景（BI 报表）。InfluxDB 从 TSM（LSM 变体）转向 Parquet（列式），反映了底层数据场景正在从"纯写入"向"写读平衡"转变。

### Insight 2：元数据管理的共同演进路径

Doris 从 BDB-JE 演进到自研 Meta Service，InfluxDB 从 BoltDB 演进到 Catalog，都经历了一场"从嵌入式 KV 到独立元数据服务"的架构变革。这不是巧合——当集群规模超过单机容量后，嵌入式元数据成为瓶颈，独立高可用服务是唯一出路。

### Insight 3：湖仓一体化是终局

Iceberg + Parquet + Arrow 的组合正在同时侵蚀 OLAP 和 TSDB 的护城河。如果所有分析型工作负载都可以直接在对象存储上运行，专用数据库的差异化优势将集中在**查询优化器**和**实时写入性能**两个保留地。

---

## 待探索方向

- ClickHouse / StarRocks 与 Doris 的竞品对比
- TimescaleDB / TDengine 与 InfluxDB 的时序竞品对比
- Lakehouse 架构是否会同时取代 OLAP 和 TSDB
- AI/ML 在查询优化中的应用（Learned Index、Learned Cost Model）

---

*综合自 Doris 8 篇 + InfluxDB 8 篇 wiki 卡片 · 2026-06-14 完成提炼*
