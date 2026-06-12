# Apache Doris 实时分析数据库深度调研报告

> **作者**: Stark (CTO, CHANG_AI_TEAM)
> **日期**: 2026-06-12
> **版本**: v1.1
> **摘要**: 涵盖 Apache Doris 核心概念、存储引擎（Segment/Page/Compaction）、查询流程（MPP 向量化）、元数据存储与一致性复制、以及关键架构演进（Palo → Doris 0.x → 1.x → 2.x → 3.0 存算分离）的全面技术调研。

---

## 目录

1. [概述与核心概念](#1-概述与核心概念)
2. [存储引擎](#2-存储引擎)
3. [查询流程](#3-查询流程)
4. [架构演进](#4-架构演进)
5. [元数据存储与一致性复制](#5-元数据存储与一致性复制)
6. [总结与选型建议](#6-总结与选型建议)

---

## 1. 概述与核心概念

![[01-概述与核心概念]]

---

## 2. 存储引擎

![[02-存储引擎]]

---

## 3. 查询流程

![[03-查询流程]]

---

## 4. 架构演进

![[04-架构演进]]

---

## 5. 元数据存储与一致性复制

![[05-元数据存储与一致性复制]]

---

## 6. 总结与选型建议

### 6.1 关键差异总结

| 维度 | Doris 2.x (Shared-Nothing) | Doris 3.x (存算分离) |
|------|---------------------------|---------------------|
| 架构模式 | Shared-Nothing MPP | Compute-Storage Separation |
| 存储层 | 本地 SSD/HDD | Object Store (S3/HDFS/MinIO) |
| 弹性扩缩 | 数据重分布，小时级 | 计算节点秒级弹性 |
| 成本 | 高 (计算+存储绑定) | 低 (按需弹性，存储下沉) |
| 写路径 | MoW 本地写入 | MoW + 远程 Compaction |
| 读路径 | 本地 Segment 读取 | File Cache + 远程拉取 |
| 高可用 | Multi-Replica | Multi-Replica + 远程副本 |
| 成熟度 | 7年+，稳定 | 1年+，快速发展中 |

### 6.2 关键能力总结

| 能力 | 描述 |
|------|------|
| 数据模型 | Duplicate / Aggregate / Unique (MoW/MoR) |
| 存储格式 | Segment v2 (自研列式) → 未来 Parquet |
| 索引 | 前缀索引 + Bloom Filter + Bitmap + Inverted Index |
| 查询引擎 | 自研 C++ 向量化引擎 → 4.0 Nereids + Falcon |
| 湖仓一体 | 原生 Catalog 联邦查询 (Hive/Iceberg/Paimon/Hudi) |
| 半结构化 | 原生 Variant 类型、倒排索引 (ES 级搜索) |
| 并发扩展 | 3.0 Workload Group + 读写分离 Compute Group |

### 6.3 选型建议

| 场景 | 推荐方案 | 原因 |
|------|----------|------|
| **实时报表 / 多维分析** | Doris 3.x | 极致查询性能，标准 SQL，亚秒级响应 |
| **广告归因 / 用户行为分析** | Doris 3.x Unique MoW | 高效 Upsert，QPS 万级 |
| **日志分析 + 全文搜索** | Doris 3.x + Inverted Index | 倒排索引性能接近 Elasticsearch 2~5x |
| **数据湖查询加速** | Doris 3.x Lakehouse | 原生 Iceberg/Paimon/Hudi 联邦查询 |
| **IoT 时序 / 监控指标** | 考虑 InfluxDB 3 或 ClickHouse | Doris 非专为高基数时序优化 |
| **ETL 宽表加工** | Doris 2.x / Doris 3.x | 支持增量 Upsert，CDC 实时导入 |

### 6.4 我们的建议

对于 CHANG_AI_TEAM 的可观测性平台项目，Apache Doris 作为分析层而非热存储层：

1. **定位为分析层**：Doris 擅长大规模数据多维聚合分析，适合查询层、报表层
2. **不替代时序存储**：热指标数据仍用 InfluxDB，Doris 聚焦聚合结果和用户行为分析
3. **Lakehouse 补充**：使用 Doris Iceberg Catalog 对接数据湖，实现分析查询加速
4. **关注 3.x 存算分离**：降低成本、提升弹性，适配云原生部署策略
5. **Nereids + Falcon 值得关注**：全新优化器 + 执行引擎，预计 4.x 主推

---

## 参考资料

- [Apache Doris 官方文档](https://doris.apache.org/docs/)
- [Doris 3.0 Release Notes](https://github.com/apache/doris/issues/37502)
- [Compute-Storage Decoupled Architecture](https://www.velodb.io/blog/slash-your-cost-90-apache-doris-compute)
- [Unique Key & Merge-on-Write](https://doris.apache.org/docs/dev/key-features/unique-key/)
- [Doris Roadmap 2025](https://github.com/apache/doris/issues/47948)
- [Doris Compaction Principles](https://doris.apache.org/docs/dev/admin-manual/trouble-shooting/compaction-principles/)
- [Data Update Overview (MoW vs MoR)](https://doris.apache.org/docs/3.x/data-operate/update/update-overview/)

## 附录：图表清单

| 图 | 文件 | 内容 |
|----|------|------|
| 01 | `Doris调研/diagram/01-architecture-overview.svg` | Apache Doris 整体架构 |
| 02 | `Doris调研/diagram/02-storage-engine.svg` | 存储引擎 Segment/Page 体系 |
| 03 | `Doris调研/diagram/03-write-path-mow.svg` | Merge-on-Write 写入路径 |
| 04 | `Doris调研/diagram/04-query-execution.svg` | MPP 向量化查询执行 |
| 05 | `Doris调研/diagram/05-architecture-evolution.svg` | Palo → Doris 3.0 架构演进 |
| 06 | `Doris调研/diagram/06-metadata-store.svg` | Meta Service 元数据存储三层模型 |
| 07 | `Doris调研/diagram/07-write-consistency.svg` | 写入路径 2PC 事务一致性流程 |

---

> **修订历史**:
> - 2026-06-12 v1.1: 新增第 5 章「元数据存储与一致性复制」，含 2 张新增技术图（06、07）
> - 2026-06-12 v1.0: 初始版本，含 5 张技术图、4 个子文档
