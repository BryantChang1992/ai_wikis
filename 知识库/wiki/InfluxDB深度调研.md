---
type: survey
title: "InfluxDB 深度调研：从 TSM 到列存引擎"
sources:
  - "技术文章/InfluxDB调研/01-概述与核心概念.md"
  - "技术文章/InfluxDB调研/02-存储引擎.md"
  - "技术文章/InfluxDB调研/03-写入与查询路径.md"
  - "技术文章/InfluxDB调研/04-指标设计最佳实践.md"
  - "技术文章/InfluxDB调研/05-多副本复制与元数据存储.md"
  - "技术文章/InfluxDB调研.md"
tags:
  - InfluxDB
  - 时序数据库
  - TSDB
  - 存储引擎
  - 列存
  - Parquet
  - 可观测性
created: 2026-06-14
updated: 2026-06-14
status: final
author: Stark (CTO, CHANG_AI_TEAM)
related:
  - "[[InfluxDB-数据模型]]"
  - "[[InfluxDB-TSM存储引擎]]"
  - "[[InfluxDB-3-列存引擎]]"
  - "[[InfluxDB-写入与查询路径]]"
  - "[[InfluxDB-指标设计与基数管理]]"
  - "[[InfluxDB-多副本与高可用]]"
  - "[[InfluxDB-Catalog元数据]]"
  - "[[LSM-Tree]]"
  - "[[事务模型深度调研]]"
---

# InfluxDB 深度调研：从 TSM 到列存引擎

> **作者**: Stark (CTO, CHANG_AI_TEAM)
> **日期**: 2026-06-14
> **摘要**: 系统性研究 InfluxDB 的核心架构与演进。从 v1/v2 的 TSM 引擎到 v3.0 的 Columnar 引擎，涵盖数据模型、存储引擎、写入/查询路径、指标设计最佳实践、多副本复制与高可用、以及 Catalog 元数据架构。为可观测性平台技术选型提供决策依据。

---

## 为何调研 InfluxDB

CHANG_AI_TEAM 正在建设 Agent 基础设施可观测性平台，时序数据库（TSDB）是核心选型组件。InfluxDB 作为最成熟的时序数据库之一，经历了从 v1.x 到 v3.0 的架构革命——从自研 TSM 引擎到基于 Apache Parquet/Arrow/DataFusion 的列存引擎。理解这次架构跃迁的技术动因，对任何时序存储选型都有参考价值。

## 版本演进全景

| 版本 | 状态 | 存储引擎 | 查询语言 | 关键特点 |
|------|------|----------|----------|----------|
| v1.x | 维护模式 | TSM + TSI | InfluxQL | 经典架构，生态成熟 |
| v2.x | 维护模式 | TSM + TSI | InfluxQL + Flux | Flux 引入，新增 Tasks |
| v3.0 Edge | 开源 (MIT) | Columnar (Parquet) | SQL + InfluxQL | Rust 重写，存算分离 |
| v3.0 Clustered | 商业版 | Columnar (全功能) | SQL + InfluxQL | 分布式集群，水平扩展 |

**核心转折点**：InfluxDB 3.0 用 Rust 重写了整个存储引擎，以 Apache Parquet 作为原生存储格式，基于 Apache Arrow 和 DataFusion 构建列式查询引擎，从架构层面解决了 v1/v2 的高基数性能瓶颈。

## 关键差异速查

| 维度 | InfluxDB v1/v2 (TSM) | InfluxDB 3.0 (Columnar) |
|------|---------------------|------------------------|
| 存储格式 | TSM (自研列式) | Apache Parquet (开放标准) |
| 索引方式 | TSI 倒排索引 | Parquet Statistics 剪枝 |
| 基数上限 | ≤ 百万级 | 理论上无上限 |
| 查询引擎 | Iterator (Go) | DataFusion 向量化 (Rust) |
| 压缩比 | ~5-10x | 10-100x |
| 写放大 | 严重 (WAL+Flush+Compaction) | 低 (单次 Parquet 写入) |
| 存储位置 | 本地磁盘 | Object Store (S3/MinIO) |
| 扩展方式 | 手动分片 (Enterprise) | 原生水平扩展 |
| 元数据 | BoltDB 嵌入式 KV | PostgreSQL 兼容 RDBMS |

## 核心概念导图

<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 700 200" width="700" height="200">
  <!-- Root -->
  <rect x="15" y="5" width="180" height="26" rx="5" fill="transparent" stroke="currentColor" stroke-width="1.2"/>
  <text x="105" y="18" font-family="sans-serif" font-size="12" fill="currentColor" text-anchor="middle" dominant-baseline="middle" font-weight="bold">InfluxDB 概念体系</text>

  <!-- Lines from root to items -->
  <line x1="105" y1="31" x2="105" y2="45" stroke="currentColor" stroke-width="1.2"/>
  <line x1="55" y1="45" x2="680" y2="45" stroke="currentColor" stroke-width="1.2"/>

  <line x1="55" y1="45" x2="55" y2="62" stroke="currentColor" stroke-width="1.2"/>
  <line x1="160" y1="45" x2="160" y2="62" stroke="currentColor" stroke-width="1.2"/>
  <line x1="265" y1="45" x2="265" y2="62" stroke="currentColor" stroke-width="1.2"/>
  <line x1="370" y1="45" x2="370" y2="62" stroke="currentColor" stroke-width="1.2"/>
  <line x1="475" y1="45" x2="475" y2="62" stroke="currentColor" stroke-width="1.2"/>
  <line x1="560" y1="45" x2="560" y2="62" stroke="currentColor" stroke-width="1.2"/>
  <line x1="665" y1="45" x2="665" y2="62" stroke="currentColor" stroke-width="1.2"/>

  <!-- Row 1: items -->
  <text x="12" y="78" font-family="sans-serif" font-size="11" fill="currentColor" text-anchor="start" dominant-baseline="middle">├ [[InfluxDB-数据模型]]</text>
  <text x="12" y="97" font-family="sans-serif" font-size="10" fill="currentColor" text-anchor="start" dominant-baseline="middle" font-style="italic">　　Measurement / Tag / Field / </text>
  <text x="12" y="112" font-family="sans-serif" font-size="10" fill="currentColor" text-anchor="start" dominant-baseline="middle" font-style="italic">　　Timestamp / Series / Cardinality</text>

  <text x="117" y="78" font-family="sans-serif" font-size="11" fill="currentColor" text-anchor="start" dominant-baseline="middle">├ [[InfluxDB-TSM存储引擎]]</text>
  <text x="117" y="97" font-family="sans-serif" font-size="10" fill="currentColor" text-anchor="start" dominant-baseline="middle" font-style="italic">　　TSM 引擎 + TSI 倒排索引</text>

  <text x="222" y="78" font-family="sans-serif" font-size="11" fill="currentColor" text-anchor="start" dominant-baseline="middle">├ [[InfluxDB-3-列存引擎]]</text>
  <text x="222" y="97" font-family="sans-serif" font-size="10" fill="currentColor" text-anchor="start" dominant-baseline="middle" font-style="italic">　　Parquet / Arrow / </text>
  <text x="222" y="112" font-family="sans-serif" font-size="10" fill="currentColor" text-anchor="start" dominant-baseline="middle" font-style="italic">　　DataFusion / 存算分离 / </text>
  <text x="222" y="127" font-family="sans-serif" font-size="10" fill="currentColor" text-anchor="start" dominant-baseline="middle" font-style="italic">　　无索引剪枝</text>

  <text x="327" y="78" font-family="sans-serif" font-size="11" fill="currentColor" text-anchor="start" dominant-baseline="middle">├ [[InfluxDB-写入与查询路径]]</text>
  <text x="327" y="97" font-family="sans-serif" font-size="10" fill="currentColor" text-anchor="start" dominant-baseline="middle" font-style="italic">　　v1/v2 Iterator vs </text>
  <text x="327" y="112" font-family="sans-serif" font-size="10" fill="currentColor" text-anchor="start" dominant-baseline="middle" font-style="italic">　　v3 DataFusion 向量化</text>

  <text x="432" y="78" font-family="sans-serif" font-size="11" fill="currentColor" text-anchor="start" dominant-baseline="middle">├ [[InfluxDB-指标设计与基数管理]]</text>
  <text x="432" y="97" font-family="sans-serif" font-size="10" fill="currentColor" text-anchor="start" dominant-baseline="middle" font-style="italic">　　Tag/Field 决策 / </text>
  <text x="432" y="112" font-family="sans-serif" font-size="10" fill="currentColor" text-anchor="start" dominant-baseline="middle" font-style="italic">　　基数计算 / 五大实践</text>

  <text x="520" y="78" font-family="sans-serif" font-size="11" fill="currentColor" text-anchor="start" dominant-baseline="middle">├ [[InfluxDB-多副本与高可用]]</text>
  <text x="520" y="97" font-family="sans-serif" font-size="10" fill="currentColor" text-anchor="start" dominant-baseline="middle" font-style="italic">　　Router 双副本 / </text>
  <text x="520" y="112" font-family="sans-serif" font-size="10" fill="currentColor" text-anchor="start" dominant-baseline="middle" font-style="italic">　　WAL 崩溃恢复 / </text>
  <text x="520" y="127" font-family="sans-serif" font-size="10" fill="currentColor" text-anchor="start" dominant-baseline="middle" font-style="italic">　　Object Store 3 AZ</text>

  <text x="620" y="78" font-family="sans-serif" font-size="11" fill="currentColor" text-anchor="start" dominant-baseline="middle">└ [[InfluxDB-Catalog元数据]]</text>
  <text x="620" y="97" font-family="sans-serif" font-size="10" fill="currentColor" text-anchor="start" dominant-baseline="middle" font-style="italic">　　PostgreSQL RDBMS / </text>
  <text x="620" y="112" font-family="sans-serif" font-size="10" fill="currentColor" text-anchor="start" dominant-baseline="middle" font-style="italic">　　BoltDB vs 独立服务</text>
</svg>

## 选型建议

| 场景 | 推荐版本 | 原因 |
|------|----------|------|
| 新项目 · 中等规模 | InfluxDB 3 Edge (OSS) | 未来方向，Parquet 生态，低成本 |
| 新项目 · 大规模/高基数 | InfluxDB 3 Clustered | 无基数限制，存算分离，弹性伸缩 |
| 存量 v1/v2 · 稳定运行 | 暂不迁移 | v1/v2 维护模式，待 v3 Community 成熟 |
| IoT 边缘计算 | InfluxDB 3 Edge | 单进程轻量，嵌入式 VM，离线运行 |
| 数据分析 · 需要 SQL | InfluxDB 3 | 原生 SQL (FlightSQL)，与现有工具兼容 |

### 对我们的建议

对于可观测性平台项目：

1. **先评估 v3 Edge** 作为单机方案的可行性
2. **关键优势**：Parquet 格式可直接用 DuckDB/Polars 做离线分析，无需额外 ETL
3. **劣势关注**：v3 生态系统仍在建设中，部分 v1/v2 功能（如 Flux Tasks）不可用
4. **长期策略**：以 Parquet 为数据湖格式中心，选择支持 Parquet 原生的存储方案（InfluxDB 3 / ClickHouse / DuckDB）

---

## 与其他调研的关系

- [[LSM-Tree]] — TSM 引擎的核心设计理念源于 [[LSM-Tree]] 的写入优化和层级合并策略。特别是 Compaction 写放大问题，在两套系统中都是核心瓶颈。
- [[事务模型深度调研]] — InfluxDB 写入路径中的 WAL 机制与事务数据库的持久性保障（WAL/Redo Log）同源。理解 WAL 的通用设计原则有助于评估时序数据库的数据可靠性。
- [[LSM-Tree-写放大]] — v1/v2 的 TSM 引擎 Compaction 产生的写放大与 LSM-Tree 的 leveling 策略有相似的根因。
- [[存储计算分离数据库的-Tail-Latency]] — InfluxDB 3.0 采用存算分离架构，其查询延迟优化策略与 RaaS 论文中讨论的 Tail Latency 问题有共同的架构关注点。

---

*调研基于 InfluxData 官方文档及技术博客，2026-06-12 完成初稿。*
