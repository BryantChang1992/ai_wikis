---
type: synthesis
title: "InfluxDB 时序数据库体系综述"
sources:
  - "[[InfluxDB深度调研]]"
  - "[[InfluxDB-数据模型]]"
  - "[[InfluxDB-TSM存储引擎]]"
  - "[[InfluxDB-3-列存引擎]]"
  - "[[InfluxDB-写入与查询路径]]"
  - "[[InfluxDB-指标设计与基数管理]]"
  - "[[InfluxDB-多副本与高可用]]"
  - "[[InfluxDB-Catalog元数据]]"
tags:
  - InfluxDB
  - 时序数据库
  - TSDB
  - 综述
  - 存储引擎
  - 列存
  - Parquet
created: 2026-06-14
updated: 2026-06-14
status: draft
related:
  - "[[synthesis/LSM-Tree-存储引擎体系综述]]"
  - "[[synthesis/Apache-Doris-OLAP-数据库体系综述]]"
  - "[[事务模型深度调研]]"
---

# InfluxDB 时序数据库体系综述

> 本综述基于 InfluxDB 深度调研形成的 8 张 wiki 卡片，以 v1/v2 到 v3.0 的架构革命为主线，系统梳理数据模型、存储引擎、读写路径、指标设计、高可用和元数据管理。

---

## 领域定义

**InfluxDB** 是时序数据库（TSDB）领域最具代表性的系统，由 InfluxData 开发。经历了从 v1/v2 自研 TSM 引擎到 v3.0 基于 Apache Parquet/Arrow/DataFusion 列存引擎的架构革命。其演进历程是理解时序存储从单体到云原生架构变迁的最佳案例。

---

## 概念关系图

<svg viewBox="0 0 800 460" xmlns="http://www.w3.org/2000/svg" font-family="sans-serif" font-size="13px">
  <defs>
    <marker id="arrow-i1" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto"><path d="M0,0 L8,3 L0,6 Z" fill="currentColor"/></marker>
    <marker id="arrow-i2" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto"><path d="M0,0 L8,3 L0,6 Z" fill="currentColor"/></marker>
  </defs>
  <!-- Top box -->
  <rect x="270" y="10" width="260" height="50" rx="6" fill="transparent" stroke="currentColor" stroke-width="1.5"/>
  <text x="400" y="30" text-anchor="middle" dominant-baseline="middle" fill="currentColor">InfluxDB 深度调研</text>
  <text x="400" y="48" text-anchor="middle" dominant-baseline="middle" fill="currentColor" font-size="12px">(总览 · 选型建议)</text>
  
  <line x1="400" y1="60" x2="400" y2="90" stroke="currentColor" stroke-width="1.5" marker-end="url(#arrow-i1)"/>
  
  <line x1="140" y1="90" x2="660" y2="90" stroke="currentColor" stroke-width="1.5"/>
  <line x1="140" y1="90" x2="140" y2="115" stroke="currentColor" stroke-width="1.5" marker-end="url(#arrow-i1)"/>
  <line x1="400" y1="90" x2="400" y2="115" stroke="currentColor" stroke-width="1.5" marker-end="url(#arrow-i1)"/>
  <line x1="660" y1="90" x2="660" y2="115" stroke="currentColor" stroke-width="1.5" marker-end="url(#arrow-i1)"/>
  
  <!-- Three top boxes -->
  <rect x="50" y="115" width="180" height="80" rx="4" fill="transparent" stroke="currentColor" stroke-width="1.5"/>
  <text x="140" y="137" text-anchor="middle" dominant-baseline="middle" fill="currentColor" font-weight="bold">数据模型</text>
  <text x="140" y="157" text-anchor="middle" dominant-baseline="middle" fill="currentColor" font-size="12px">Measurement</text>
  <text x="140" y="175" text-anchor="middle" dominant-baseline="middle" fill="currentColor" font-size="12px">Tag / Field</text>
  <text x="140" y="191" text-anchor="middle" dominant-baseline="middle" fill="currentColor" font-size="12px">Series / Card</text>
  
  <rect x="310" y="115" width="180" height="80" rx="4" fill="transparent" stroke="currentColor" stroke-width="1.5"/>
  <text x="400" y="137" text-anchor="middle" dominant-baseline="middle" fill="currentColor" font-weight="bold">存储引擎</text>
  <text x="400" y="157" text-anchor="middle" dominant-baseline="middle" fill="currentColor" font-size="12px">TSM / Columnar</text>
  <text x="400" y="175" text-anchor="middle" dominant-baseline="middle" fill="currentColor" font-size="12px">Compaction</text>
  
  <rect x="570" y="115" width="180" height="80" rx="4" fill="transparent" stroke="currentColor" stroke-width="1.5"/>
  <text x="660" y="137" text-anchor="middle" dominant-baseline="middle" fill="currentColor" font-weight="bold">写入与查询</text>
  <text x="660" y="157" text-anchor="middle" dominant-baseline="middle" fill="currentColor" font-size="12px">Iterator /</text>
  <text x="660" y="175" text-anchor="middle" dominant-baseline="middle" fill="currentColor" font-size="12px">DataFusion</text>
  
  <!-- Bidirectional arrows between top three -->
  <line x1="230" y1="140" x2="308" y2="150" stroke="currentColor" stroke-width="1" marker-end="url(#arrow-i2)"/>
  <line x1="308" y1="170" x2="230" y2="175" stroke="currentColor" stroke-width="1" marker-end="url(#arrow-i2)"/>
  <line x1="490" y1="140" x2="568" y2="150" stroke="currentColor" stroke-width="1" marker-end="url(#arrow-i2)"/>
  <line x1="568" y1="170" x2="490" y2="175" stroke="currentColor" stroke-width="1" marker-end="url(#arrow-i2)"/>
  
  <!-- Vertical down -->
  <line x1="140" y1="195" x2="140" y2="230" stroke="currentColor" stroke-width="1.5" marker-end="url(#arrow-i1)"/>
  <line x1="400" y1="195" x2="400" y2="230" stroke="currentColor" stroke-width="1.5" marker-end="url(#arrow-i1)"/>
  <line x1="660" y1="195" x2="660" y2="230" stroke="currentColor" stroke-width="1.5" marker-end="url(#arrow-i1)"/>
  
  <!-- Three bottom boxes -->
  <rect x="50" y="230" width="180" height="80" rx="4" fill="transparent" stroke="currentColor" stroke-width="1.5"/>
  <text x="140" y="252" text-anchor="middle" dominant-baseline="middle" fill="currentColor" font-weight="bold">指标设计 · 基数</text>
  <text x="140" y="272" text-anchor="middle" dominant-baseline="middle" fill="currentColor" font-size="12px">管理</text>
  <text x="140" y="290" text-anchor="middle" dominant-baseline="middle" fill="currentColor" font-size="12px">Tag/Field 决策</text>
  <text x="140" y="306" text-anchor="middle" dominant-baseline="middle" fill="currentColor" font-size="12px">五大最佳实践</text>
  
  <rect x="310" y="230" width="180" height="80" rx="4" fill="transparent" stroke="currentColor" stroke-width="1.5"/>
  <text x="400" y="252" text-anchor="middle" dominant-baseline="middle" fill="currentColor" font-weight="bold">多副本 · 高可用</text>
  <text x="400" y="272" text-anchor="middle" dominant-baseline="middle" fill="currentColor" font-size="12px">Router 双副本</text>
  <text x="400" y="290" text-anchor="middle" dominant-baseline="middle" fill="currentColor" font-size="12px">WAL 恢复</text>
  <text x="400" y="306" text-anchor="middle" dominant-baseline="middle" fill="currentColor" font-size="12px">Object Store</text>
  
  <rect x="570" y="230" width="180" height="80" rx="4" fill="transparent" stroke="currentColor" stroke-width="1.5"/>
  <text x="660" y="252" text-anchor="middle" dominant-baseline="middle" fill="currentColor" font-weight="bold">Catalog 元数据</text>
  <text x="660" y="272" text-anchor="middle" dominant-baseline="middle" fill="currentColor" font-size="12px">PostgreSQL</text>
  <text x="660" y="290" text-anchor="middle" dominant-baseline="middle" fill="currentColor" font-size="12px">BoltDB → RDBMS</text>

  <!-- Timeline at bottom -->
  <line x1="60" y1="430" x2="740" y2="430" stroke="currentColor" stroke-width="2"/>
  
  <!-- Arrow heads for timeline -->
  <polygon points="740,430 730,425 730,435" fill="currentColor"/>
  
  <!-- v1.x -->
  <line x1="100" y1="430" x2="100" y2="418" stroke="currentColor" stroke-width="1.5"/>
  <text x="100" y="410" text-anchor="middle" dominant-baseline="middle" fill="currentColor" font-size="12px" font-weight="bold">v1.x</text>
  <text x="100" y="450" text-anchor="middle" dominant-baseline="middle" fill="currentColor" font-size="12px">TSM+TSI</text>
  <text x="100" y="466" text-anchor="middle" dominant-baseline="middle" fill="currentColor" font-size="11px">Go | 单机</text>
  
  <!-- v2.x -->
  <line x1="350" y1="430" x2="350" y2="418" stroke="currentColor" stroke-width="1.5"/>
  <text x="350" y="410" text-anchor="middle" dominant-baseline="middle" fill="currentColor" font-size="12px" font-weight="bold">v2.x</text>
  <text x="350" y="450" text-anchor="middle" dominant-baseline="middle" fill="currentColor" font-size="12px">+Flux/Tasks</text>
  <text x="350" y="466" text-anchor="middle" dominant-baseline="middle" fill="currentColor" font-size="11px">Go | 单机</text>
  
  <!-- v3.0 -->
  <line x1="640" y1="430" x2="640" y2="418" stroke="currentColor" stroke-width="1.5"/>
  <text x="640" y="410" text-anchor="middle" dominant-baseline="middle" fill="currentColor" font-size="12px" font-weight="bold">v3.0 Edge / Clustered</text>
  <text x="640" y="450" text-anchor="middle" dominant-baseline="middle" fill="currentColor" font-size="12px">Parquet+Arrow+DataFusion</text>
  <text x="640" y="466" text-anchor="middle" dominant-baseline="middle" fill="currentColor" font-size="11px">Rust | 存算分离</text>
</svg>

**关系说明**：数据模型是根基——Tag/Field 决策直接影响存储引擎的索引和行为（基数）。存储引擎经历了从 TSM（LSM 衍生）到 Columnar（Parquet 原生）的架构跃迁。读写路径从 Iterator 模型到 DataFusion 向量化体现查询引擎的根本性变革。指标设计需要理解模型才能做好——基数管理是 v1/v2 的生存问题。多副本和 Catalog 共同构成分布式基础设施层。

---

## 子主题展开

### 1. 数据模型 — [[InfluxDB-数据模型]]

Measurement + Tag Set + Field Set + Timestamp 构成 Point，Point 的笛卡尔积形成 Series。Series Cardinality = |tag₁| × … × |tagₙ| × |fields| 是 InfluxDB 最核心的性能度量。v1/v2 上限百万级（TSI 索引膨胀），v3 理论上无上限（Parquet Statistics 取代 TSI）。

### 2. 存储引擎演进 — [[InfluxDB-TSM存储引擎]] → [[InfluxDB-3-列存引擎]]

**TSM 时代** (v1/v2)：自研列式格式，借鉴 LSM-tree 设计，不可变 TSM 文件 + 多级 Compaction。TSI 倒排索引提供元数据查找。致命缺陷：高基数时 TSI 膨胀 → 内存爆炸 → OOM。

**Columnar 时代** (v3.0)：全面拥抱 Apache 生态——Parquet 持久化格式、Arrow 内存格式、DataFusion 查询引擎。核心突破：
- Parquet Statistics 实现**无索引剪枝**，消除基数上限
- 单次写入（无多级 Compaction），写放大显著降低
- Cardinality-Aware Sort 最大化压缩效率（10-100x）
- 存算分离架构：Ingester / Querier / Compactor / GC 四组件独立伸缩

### 3. 读写路径演进 — [[InfluxDB-写入与查询路径]]

**写入**：v1/v2 经过 WAL → Cache → TSI → L0 Flush → 多级 Compaction，每条数据被反复 I/O。v3 通过 Ingest Router 路由 → Ingester 校验/分区/排序/去重 → Parquet 单次写入 Object Store。

**查询**：v1/v2 Iterator 模型 O(N) per Series，逐点处理，无向量化。v3 DataFusion 向量化引擎：4096 行 Batch、SIMD 加速、Parquet Statistics 剪枝、Predicate Pushdown、Column Pruning，延迟不再随 Series 基数线性增长。

### 4. 指标设计最佳实践 — [[InfluxDB-指标设计与基数管理]]

核心决策框架：需要 WHERE 过滤 → 检查基数 → <10K 做 Tag / 10K-100K 谨慎 / >100K 绝不能 Tag。Field 存高基数 + 需要聚合的值。五大反模式：编码数据到 Measurement、高基数 Tag、过量 Tag Key、无下采样、无 RP/Granularity。

### 5. 高可用与复制 — [[InfluxDB-多副本与高可用]]

v3 Router 双副本（active-passive）+ WAL（EBS）崩溃恢复 + Object Store 3 AZ 持久化。Ingester 主动选择 Router + WAL 分段 + Catalog 双写保证。v1/v2 依赖单机文件系统 + Enterprise 手动分片。

### 6. 元数据管理 — [[InfluxDB-Catalog元数据]]

v3 从 BoltDB 迁移到 PostgreSQL 兼容 RDBMS。Catalog 负责 Table/Column/Partition/File 元数据管理，支持 Schema-aware 分区裁剪和索引加速。利用 PG 的成熟事务、索引、复制能力替代自研方案。

---

## 跨页连接的 Insight

### Insight 1：架构革命的根因是索引，不是存储

InfluxDB v3 的根本性变革不是为了换存储格式——是为了**消除索引瓶颈**。TSI 倒排索引在高基数下爆炸，而 Parquet Statistics 以"无索引剪枝"替代了"维护索引"的思维范式。这不是格式之争，是架构哲学之争。

### Insight 2：存算分离 + 不可变开放格式 = 时序存储的未来

Parquet 作为开放标准格式 + S3 对象存储 + 无状态计算组件的组合，使 InfluxDB 3 天然具备数据湖兼容性。DuckDB/Polars/Spark 可直接读取 Parquet 文件进行分析——零 ETL 是时序存储的新范式。这种"用开放格式做一等公民"的思路对可观测性平台选型有直接参考价值。

### Insight 3：基数管理的智慧跨越版本

Tag/Field 决策的框架（是否需要 WHERE/GROUP BY → 查基数 → 决定 Tag/Field）在 v1/v2 和 v3 同样有效。虽然 v3 消除了硬基数上限，但高基数 Tag 仍会降低压缩效率和查询性能——优化基数仍然是所有时序数据库的最佳实践。

### Insight 4：Rust + Arrow 生态是时序数据库的新基线

InfluxDB 3 的全 Rust 重写证明了 Rust（零 GC、内存安全）+ Arrow（零拷贝列式交换）+ DataFusion（向量化查询）的技术栈已经成为下一代数据库引擎的竞争力基线。Go 在 GC 停顿和 SIMD 方面的劣势在数据密集型场景被放大。

---

## 与外部知识领域的交叉

| 交叉领域 | 关联页面 | 说明 |
|----------|---------|------|
| LSM-Tree | [[synthesis/LSM-Tree-存储引擎体系综述]] | TSM 引擎本质是 LSM 在时序场景的衍生 |
| OLAP 数据库 | [[synthesis/Apache-Doris-OLAP-数据库体系综述]] | Parquet 列存 + Compaction + 索引策略与 Doris 高度可比 |
| 事务系统 | [[事务模型深度调研]] | WAL 机制与事务数据库同源 |
| 存算分离 | [[存储计算分离数据库的-Tail-Latency]] | v3 存算分离架构与 RaaS 论文的 tail latency 讨论直接对齐 |

---

## 待探索方向

1. **Parquet 作为可观测性数据湖基础格式**：验证 DuckDB/Polars/Spark 直接查询 InfluxDB v3 Parquet 文件的可行性，评估零 ETL 分析链路
2. **TSM → Columnar 的迁移策略**：存量 v1/v2 部署如何平滑迁移到 v3？双写 + 影子查询 + 回填历史数据的分阶段迁移方案
3. **存算分离下的查询延迟优化**：Object Store 的 I/O 延迟 vs 本地 File Cache 的命中率 trade-off，参考 [[存储计算分离数据库的-Tail-Latency]] 的 tail latency 分析
4. **Catalog 架构对比**：BoltDB → PostgreSQL 的迁移在元数据查询延迟上的量化对比，以及 PG 多 AZ 复制对可用性的影响
5. **v3 生态缺口**：Flux Tasks 的替代方案、Continuous Query 的下采样方案、Dashboards 兼容性评估
6. **与 ClickHouse/StarRocks 的交叉基准测试**：在高基数时序场景下，InfluxDB 3 Parquet 引擎 vs ClickHouse MergeTree 的写入吞吐和压缩比对比

---

*综合自 InfluxDB 深度调研形成的 8 张 wiki 卡片，2026-06-14 完成提炼。*
