---
type: synthesis
title: "Apache Doris OLAP 数据库体系综述"
sources:
  - "[[Doris-深度调研]]"
  - "[[Doris-数据模型]]"
  - "[[Doris-Segment-v2-存储格式]]"
  - "[[Doris-Compaction-策略]]"
  - "[[Doris-MPP-向量化查询引擎]]"
  - "[[Doris-Nereids-CBO-优化器]]"
  - "[[Doris-架构演进]]"
  - "[[Doris-元数据与一致性复制]]"
tags:
  - 数据库
  - OLAP
  - Doris
  - 综述
  - MPP
  - 列式存储
  - 实时分析
  - 存算分离
created: 2026-06-14
updated: 2026-06-14
status: draft
related:
  - "[[LSM-Tree-存储引擎体系综述]]"
  - "[[InfluxDB-时序数据库体系综述]]"
  - "[[事务模型深度调研]]"
---

# Apache Doris OLAP 数据库体系综述

> 本综述基于 Doris 深度调研形成的 8 张 wiki 卡片，以数据模型 → 存储引擎 → 查询引擎 → 架构演进为主线，系统梳理 Doris 的技术体系。

---

## 领域定义

**Apache Doris** 是百度开源、Apache 毕业的 MPP 架构实时分析数据库，专为 OLAP 高并发低延迟多维分析设计。C++ BE（计算+存储）和 Java FE（元数据+查询规划）。在 **Upsert (MoW) + 高并发查询 + 实时导入** 三个维度形成独特优势组合。

---

## 概念关系图

```
                        ┌──────────────────────────────┐
                        │     Doris 深度调研            │
                        │     (总览 · 选型 · 历史)      │
                        └──────────────┬───────────────┘
                                       │
        ┌──────────────────────────────┼──────────────────────────────┐
        │                              │                              │
        ▼                              ▼                              ▼
┌───────────────┐              ┌───────────────┐              ┌───────────────┐
│   数据模型     │              │   存储引擎     │              │   查询引擎     │
│ Duplicate     │──────────────►│ Segment v2    │──────────────►│ MPP 向量化    │
│ Aggregate     │  DELETE_BITMAP│ Compaction    │  索引+裁剪     │ Nereids CBO   │
│ Unique MoW/MoR│              │ 四种策略      │              │ Runtime Filter│
└───────┬───────┘              └───────┬───────┘              └───────┬───────┘
        │                              │                              │
        └──────────────────────────────┼──────────────────────────────┘
                                       │
                                       ▼
                        ┌──────────────────────────────┐
                        │        架构演进               │
                        │  Shared-Nothing → 存算分离    │
                        │  Palo → 1.x → 2.x → 3.0      │
                        └──────────────┬───────────────┘
                                       │
                        ┌──────────────┴──────────────┐
                        │                             │
                        ▼                             ▼
                ┌───────────────┐             ┌───────────────┐
                │ 元数据 · 复制  │             │   生态整合     │
                │ BDB-JE → Meta │             │ Lakehouse     │
                │ Service       │             │ Catalog联邦   │
                │ Doris 3.0 一致性│             │ 查询          │
                └───────────────┘             └───────────────┘
```

**关系说明**：数据模型决定写入语义（Duplicate/Aggregate/Unique），存储引擎 Segment v2 和 Compaction 策略实现这些语义（特别是 DELETE_BITMAP 实现 MoW）。查询引擎利用存储层的索引（前缀索引/ZoneMap/Bloom Filter）进行过滤剪枝，Nereids CBO 生成最优查询计划，MPP 向量化引擎执行。架构从 Shared-Nothing 演进到存算分离，元数据从 BDB-JE 演进到独立 Meta Service。

---

## 子主题展开

### 1. 数据模型 — [[Doris-数据模型]]

四种模型覆盖 OLAP 全场景：
- **Duplicate**：Append-only 明细/日志，写入吞吐最高
- **Aggregate**：预聚合指标，查询极快但丢失明细
- **Unique MoW** (Doris 2.1+ 默认)：写入时 UPSERT，DELETE_BITMAP 标记旧行，查询最优
- **Unique MoR**：追加写入，查询时合并多版本，写入快查询慢

模型选择框架：先判断写入是否 Append-only（是→选聚合模型，否→走 Unique 路线），再判断查询延迟是否敏感（敏感→MoW，不敏感→MoR）。

### 2. 存储引擎 — [[Doris-Segment-v2-存储格式]]

自研 Segment v2 列式格式，以 Page (1MB) 为 I/O 最小单元。五层索引体系：前缀索引（粗粒度）→ ZoneMap（Min/Max/NullCount）→ Bloom Filter（判不存在）→ Bitmap/Inverted Index（低基数/全文搜索）。DELETE_BITMAP 是 Unique MoW 的核心创新：在现有 Segment 中标记被删除行，不重写文件。与 Parquet 的关键差异：Doris 牺牲极端压缩率换低延迟写入。

### 3. Compaction 策略 — [[Doris-Compaction-策略]]

四种 Compaction 类型：
- **Cumulative**：合并小 Rowset，高频低频优先级
- **Base**：合并全部 Rowset 为单一文件，用于冷数据分区
- **Quick Compaction**：回收 DELETE_BITMAP 过多的 Segment，降低查询开销
- **Vertical Compaction**：宽表按列组分批合并，避免 OOM

与经典 LSM Compaction 的核心差异：Doris 无固定层级（Rowset 版本链），每个 Tablet 独立并发 Compaction，Vertical Compaction 是列式数据库特有的优化维度。

### 4. 查询引擎 — [[Doris-MPP-向量化查询引擎]] + [[Doris-Nereids-CBO-优化器]]

**执行层**：C++ 自研向量化引擎，4096 行/Batch 流水线处理，SIMD (SSE/AVX2) 加速。MPP 分布式执行：Plan Fragment 分发 + BRPC 数据交换。四种 Shuffle 策略（Broadcast / Hash / Bucket Shuffle / Colocate Join），其中 Bucket Shuffle 和 Colocate Join 是 Doris 独有的零 Shuffle Join 优化。

**优化器层**：Nereids CBO (v3.0 稳定)，基于统计信息（RowCount/NDV/NullCount/MaxMin/Histogram）驱动的查询优化。核心能力：Join Reorder、CTE 物化重用、Runtime Filter 深度集成、Lakehouse 联邦查询。

### 5. 架构演进 — [[Doris-架构演进]]

从百度内部 Palo → Apache Doris 1.x (Shared-Nothing) → 3.0 (存算分离) → 4.0 (Falcon 新引擎)。3.0 引入 Compute Group + Object Store + File Cache + Meta Service，实现计算弹性伸缩。4.0 计划：Falcon 新执行引擎（C++→Rust?）、Parquet 原生支持（与 InfluxDB 3 的 Parquet 生态呼应）。

### 6. 元数据与一致性 — [[Doris-元数据与一致性复制]]

v1/v2 基于 BDB-JE（类 Paxos）的 FE 元数据复制 + Tablet 三副本机制。v3.0 引入独立 Meta Service（解耦元数据瓶颈）+ 存算分离下的一致性模型简化。与 [[事务模型深度调研]] 中 2PC 机制的关联：Doris 的副本一致性和跨 Tablet 事务借鉴了分布式事务的思想。

---

## 跨页连接的 Insight

### Insight 1：MoW 是 OLAP 数据库的"杀手特性"

Doris Unique MoW（写入时去重 + DELETE_BITMAP 标记）在 Upsert 场景形成对 ClickHouse 的绝对优势。ClickHouse MergeTree 本质是 Append-only + Merge-on-Read，频繁 Upsert 场景下查询延迟和存储膨胀严重。MoW 以少量写入开销换取查询最优——这是 [[LSM-Tree-RUM猜想]] 在 OLAP 领域的经典体现。

### Insight 2：Buck Shuffle / Colocate Join 是 MPP 查询的"免费午餐"

利用分区/分桶信息消除 Shuffle 数据重分布，在高频 Join 查询中将网络开销降为零。这背后是一个重要的架构原则：**物理数据布局应服务于查询模式**。建表时的 Bucket 设计（分桶键 = Join 键）直接影响查询延迟——这是 MPP 数据库独特的"Schema 即优化"哲学。

### Insight 3：Compaction 从"核心瓶颈"变成了"可管理开销"

与 LSM-Tree 的写放大问题（[[LSM-Tree-写放大]]）不同，Doris 的 Compaction 通过四种策略分级处理、各 Tablet 独立并发、宽松的实时性要求（数据导入后可延迟合并）将 Compaction 从瓶颈降级为可管理的后台开销。Quick Compaction 的 DELETE_BITMAP 回收机制尤其精巧——只合并"碎片化"的 Segment 而非整个 Rowset。

### Insight 4：存算分离是三大家（Doris/ClickHouse/StarRocks）的共同终局

Doris 3.0、ClickHouse Cloud、StarRocks 3.0 不约而同走向存算分离——共同趋势背后是对云原生弹性需求的共识。但实现路径不同：Doris 从 Shared-Nothing 渐进分离、ClickHouse 从 MergeTree 重构为 SharedMergeTree、StarRocks 从头设计存算分离。理解这三条路径的 trade-off 是 OLAP 架构判断的核心能力。

---

## 与外部知识领域的交叉

| 交叉领域 | 关联页面 | 说明 |
|----------|---------|------|
| LSM-Tree | [[LSM-Tree-存储引擎体系综述]] | Compaction 策略和 DELETE_BITMAP 借鉴 LSM 思想 |
| 时序数据库 | [[InfluxDB-时序数据库体系综述]] | Parquet 列存（Doris 4.0 计划 vs InfluxDB 3 已完成）、Compaction 策略对比 |
| 事务系统 | [[事务模型深度调研]] | 元数据一致性复制（2PC/Paxos）、MVCC 快照隔离 |
| 分布式系统 | [[Event-Horizon-非对称依赖]] | Doris 元数据一致性的非对称依赖启发 |

---

## 待探索方向

1. **Doris vs ClickHouse 存算分离深度对比**：Shared-Storage 模式下查询延迟、写入吞吐、弹性扩缩的基准测试
2. **Falcon 新引擎的技术路线**：是否走向 Rust + Arrow 生态（类似 InfluxDB 3 的技术栈选择）？
3. **Parquet 原生支持后的生态变化**：Doris 4.0 计划支持 Parquet 原生格式后，与 Iceberg/Paimon 数据湖的深度整合
4. **MoW DELETE_BITMAP 的大规模验证**：PB 级主键更新表下，Quick Compaction 的回收效率和延迟影响
5. **多租户场景下的资源隔离**：Compute Group 的 CPU/内存/IO 隔离粒度，以及 Queue 优先级调度的有效性
6. **AI/ML 工作负载的适配**：Doris 在特征存储、向量检索、模型推理数据供给等场景的适配性评估

---

*综合自 Doris 深度调研形成的 8 张 wiki 卡片，2026-06-14 完成提炼。*
