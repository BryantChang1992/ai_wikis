---
type: analysis
title: 🏛 湖仓 / Data for AI — Week 08 (2026-06-25)
blog_url: https://bryantchang1992.github.io/ai_memory_chang_ai_team/tech_research/data_for_ai/week_08_2026-06-25.html
blog_source: tech_research/data_for_ai/week_08_2026-06-25.html
blog_source_commit: f83970fa7e6ad32d626cc6ca3ba7428c90a638a5
synced_at: '2026-10-05'
tags:
- 博客同步
---

# 🏛 湖仓 / Data for AI — Week 08 (2026-06-25)

覆盖周期：2026-06-19 ~ 2026-06-25

## 1. Apache Iceberg v3 Public Preview on Databricks

🔥 2026-04-09 发布。开放表格式进入新时代。

### 三大核心特性

#### 1.1 Row Lineage + Deletion Vectors = Native CDC

每行携带**永久 row ID + 序列号**，精确识别变更。Deletion Vectors 使逻辑删除无需重写 Parquet 文件，数据操作性能最高 **10x 提升**。

Geodis（全球物流）正在利用这一能力集中 Iceberg 数据资产，同时保持引擎选择自由：*"Now that Deletion Vectors have come to Iceberg, we can centralize our Iceberg data estate in Unity Catalog, while leveraging the engine of our choice and maintaining best-in-class performance."* — Delio Amato, Chief Architect & Data Officer, Geodis

#### 1.2 VARIANT 类型

原生半结构化数据列类型，**不需要 flatten、不需要外部存储、不需要 ETL normalization**。与关系列共处一表，新字段出现即可查询（无需 schema migration）。

Panther 安全公司利用 VARIANT 实现百万级安全日志接入和分析：*"Unity Catalog and Iceberg v3 unlock the power of semi-structured data through VARIANT."* — Russell Leighton, Chief Architect, Panther

通过 **Shredding** 优化，VARIANT 数据可达到列存级别性能，支持低延迟 BI 和告警。

#### 1.3 Delta-Iceberg 互通里程碑

Iceberg v3 原生采纳 **Deletion Vectors、Row Lineage、VARIANT**，与 Delta Lake 功能对齐。Delta UniForm 允许多引擎读取同一份 Delta 数据（Snowflake、BigQuery、Redshift、Athena、Trino）。

历史性的 trade-off 被消除：顾客不再需要在「Delta 的性能」和「Iceberg 的兼容性」之间二选一。

来源：[databricks.com/blog — Iceberg v3 Public Preview](https://www.databricks.com/blog/next-era-open-lakehouse-apache-icebergtm-v3-public-preview-databricks)

## 2. 湖仓格式竞争格局（2026）

| 格式 | 核心生态 | 2026 差异化 | 最新版本 |
| --- | --- | --- | --- |
| **Iceberg** | 最广泛引擎支持 | v3 打破性能-兼容 trade-off；Databricks + Snowflake 双引擎战略 | v3 (Public Preview) |
| **Delta Lake** | Spark / Databricks | UniForm 实现 Iceberg 兼容读写；Lakehouse 一体化平台 | 4.2.x |
| **Hudi** | Uber / AWS | 1.2 多模态 Lakehouse；2.0 目标 2026-06 | 1.2.0 |
| **Paimon** | Flink / 阿里巴巴 | Fluss 配合实现实时 Lakehouse；原生流批一体 | - |

## 3. Fluss + Paimon 实时湖仓链路

Fluss 定位为 **"real-time data layer on top of Lakehouse"**，配合 Paimon 实现：

```
Kafka/Event Source → Fluss (Streaming Storage)
                         ↓ LakeStream
                    Paimon (Lakehouse Table)
                         ↓
              Flink / Trino / Spark 查询
```

核心能力：**在已有湖仓表上直接启用流式读写**（LakeStream），不需要新建 streaming 表。这是阿里巴巴流批一体战略的关键技术拼图。

来源：[github.com/apache/fluss — 1.0 Roadmap](https://github.com/apache/fluss/discussions/2684), [CMU DB Group — Future Data: Fluss](https://db.cs.cmu.edu/events/future-data-apache-fluss-a-streaming-storage-for-real-time-lakehouse/)

## 4. Iceberg vs Delta Lake 产业分析

2026 年多篇对比分析文章共识：

- 两种格式的核心 lakehouse 能力（ACID、Time Travel、Schema Evolution）已基本对齐
- 差异转移到了**实现细节和运维体验**：catalog 管理、引擎兼容性、性能优化策略
- Databricks 的 Unity Catalog 通过对 Delta 数据暴露 Iceberg 接口，本质上在推动 **"一份数据，多引擎读取"**的架构收敛
- "单表格式胜利"不再重要，**"多格式互通 + 统一治理"**成为 2026 年主流叙事

来源：[Dremio — Iceberg vs Delta Lake (2026-02)](https://www.dremio.com/blog/apache-iceberg-vs-delta-lake/), [Big Data Boutique (2026-03)](https://bigdataboutique.com/blog/apache-iceberg-vs-delta-lake-choosing-the-right-table-format)

## 小结

湖仓方向 2026 年的核心矛盾已从「选哪个格式」转变为「如何统一治理」。Iceberg v3 和 Delta UniForm 从两个方向推动互通：一个在格式层增强，一个在接口层桥接。Fluss + Paimon 则代表第三条路：用流式存储层统一 streaming 和 lakehouse 两层。
