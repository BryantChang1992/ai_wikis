# InfluxDB 时序数据库深度调研报告（总览）

> **作者**: Stark (CTO, CHANG_AI_TEAM)
> **日期**: 2026-06-12
> **版本**: v1.0

---

## 子文档索引

本调研报告拆分为以下子文档，按阅读顺序排列：

| # | 文档 | 内容 |
|---|------|------|
| 1 | [01-概述与核心概念](InfluxDB调研-01-概述与核心概念.md) | 版本演进路线、数据模型（Point/Tag/Field/Series）、Line Protocol |
| 2 | [02-存储引擎](InfluxDB调研-02-存储引擎.md) | TSM/TSI vs Columnar (Parquet+DataFusion) 引擎演进对比 |
| 3 | [03-写入与查询路径](InfluxDB调研-03-写入与查询路径.md) | v1/v2 vs v3 写入全流程 + DataFusion 向量化查询 |
| 4 | [04-指标设计最佳实践](InfluxDB调研-04-指标设计最佳实践.md) | Tag/Field 决策框架、五大实践、四种反模式、下采样策略 |
| 5 | [05-多副本复制与元数据存储](InfluxDB调研-05-多副本复制与元数据存储.md) | 三层数据持久化、Catalog 元数据模型、HA 与故障恢复 |

## 附录

| 图 ID | 文件 | 内容 |
|-------|------|------|
| 01 | `diagram/influxdb-research/01-architecture-overview.svg` | InfluxDB 3.0 整体架构 |
| 02 | `diagram/influxdb-research/02-storage-engine.svg` | TSM/TSI → Columnar 存储引擎演进对比 |
| 03 | `diagram/influxdb-research/03-write-path.svg` | 写入路径全流程对比 |
| 04 | `diagram/influxdb-research/04-query-path.svg` | DataFusion 向量化查询引擎详解 |
| 05 | `diagram/influxdb-research/05-schema-best-practices.svg` | Tag/Field 决策框架 + 基数管理 |
| 06 | `diagram/influxdb-research/06-replication-ha.svg` | 多副本复制与高可用 |
| 07 | `diagram/influxdb-research/07-catalog-metadata.svg` | Catalog 元数据存储详解 |

---

> **修订历史**:
> - 2026-06-12 v1.0: 初始版本，含 7 张技术图、5 个子文档
