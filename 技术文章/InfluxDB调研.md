# InfluxDB 时序数据库深度调研报告

> **作者**: Stark (CTO, CHANG_AI_TEAM)
> **日期**: 2026-06-12
> **版本**: v1.0
> **摘要**: 涵盖 InfluxDB 核心概念、存储引擎演进（TSM/TSI → InfluxDB 3 列存引擎）、写入路径、查询路径、指标设计最佳实践、多副本复制与高可用、以及元数据存储（Catalog）的全面技术调研。

---

## 目录

1. [概述与核心概念](#1-概述与核心概念)
2. [存储引擎](#2-存储引擎)
3. [写入与查询路径](#3-写入与查询路径)
4. [指标设计最佳实践](#4-指标设计最佳实践)
5. [多副本复制与元数据存储](#5-多副本复制与元数据存储)
6. [总结与选型建议](#6-总结与选型建议)

---

## 1. 概述与核心概念

![[01-概述与核心概念]]

---

## 2. 存储引擎

![[02-存储引擎]]

---

## 3. 写入与查询路径

![[03-写入与查询路径]]

---

## 4. 指标设计最佳实践

![[04-指标设计最佳实践]]

---

## 5. 多副本复制与元数据存储

![[05-多副本复制与元数据存储]]

---

## 6. 总结与选型建议

### 6.1 关键差异总结

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
| 成熟度 | 10年+，稳定 | 3年，快速发展中 |

### 6.2 选型建议

| 场景 | 推荐版本 | 原因 |
|------|----------|------|
| **新项目 · 中等规模** | InfluxDB 3 Edge (OSS) | 未来方向，Parquet 生态，低成本 |
| **新项目 · 大规模/高基数** | InfluxDB 3 Clustered | 无基数限制，存算分离，弹性伸缩 |
| **存量 v1/v2 · 稳定运行** | 暂不迁移 | v1/v2 维护模式，待 v3 Community 成熟 |
| **IoT 边缘计算** | InfluxDB 3 Edge | 单进程轻量，嵌入式 VM，离线运行 |
| **数据分析 · 需要 SQL** | InfluxDB 3 | 原生 SQL (FlightSQL)，与现有工具兼容 |
| **仅需简单监控 · 低基数** | 考虑 VictoriaMetrics/Prometheus | 更轻量，生态更匹配 |

### 6.3 我们的建议

对于 CHANG_AI_TEAM 的可观测性平台项目，建议关注 InfluxDB 3 生态：

1. **先评估 v3 Edge** 作为单机方案的可行性（即将开源，MIT/Apache2 许可）
2. **关键优势**：Parquet 格式可直接用 DuckDB/Polars 做离线分析，无需额外 ETL
3. **劣势关注**：v3 生态系统仍在建设中，部分 v1/v2 功能（如 Flux Tasks）不可用，需评估迁移成本
4. **长期策略**：以 Parquet 为数据湖格式中心，选择支持 Parquet 原生的存储方案（InfluxDB 3 / ClickHouse / DuckDB）

---

## 参考资料

- [InfluxDB 3.0 System Architecture](https://www.influxdata.com/blog/influxdb-3-0-system-architecture/) — Nga Tran, Paul Dix, Andrew Lamb, Marko Mikulicic
- [InfluxDB 3 Storage Engine Internals](https://docs.influxdata.com/influxdb3/cloud-dedicated/reference/internals/storage-engine/) — InfluxData Official Docs
- [InfluxDB Internals 101: Data Model & Write Path](https://www.influxdata.com/blog/influxdb-internals-101-part-one/) — Ryan Betts
- [Data Layout and Schema Design Best Practices](https://www.influxdata.com/blog/data-layout-and-schema-design-best-practices-for-influxdb/) — Anais Dotis-Georgiou
- [The Plan for InfluxDB 3 Open Source](https://www.influxdata.com/blog/the-plan-for-influxdb-3-0-open-source/) — Paul Dix

## 附录：图表清单

| 图 | 文件 | 内容 |
|----|------|------|
| 01 | `InfluxDB调研/diagram/01-architecture-overview.svg` | InfluxDB 3.0 整体架构 |
| 02 | `InfluxDB调研/diagram/02-storage-engine.svg` | 存储引擎演进对比 |
| 03 | `InfluxDB调研/diagram/03-write-path.svg` | 写入路径全流程对比 |
| 04 | `InfluxDB调研/diagram/04-query-path.svg` | DataFusion 向量化查询 |
| 05 | `InfluxDB调研/diagram/05-schema-best-practices.svg` | Tag/Field 决策 + 基数管理 |
| 06 | `InfluxDB调研/diagram/06-replication-ha.svg` | 多副本复制与高可用 |
| 07 | `InfluxDB调研/diagram/07-catalog-metadata.svg` | Catalog 元数据存储 |

---

> **修订历史**:
> - 2026-06-12 v1.0: 初始版本，含 7 张技术图、5 个子文档
