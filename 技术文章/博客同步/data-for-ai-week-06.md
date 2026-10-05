---
title: 面向 AI 的数据平台建设 — Week 06
blog_url: https://bryantchang1992.github.io/ai_memory_chang_ai_team/posts/tech-research/week-06/data-for-ai/
blog_source: _posts/2026-06-18-data-for-ai-week-06.md
blog_source_commit: f83970fa7e6ad32d626cc6ca3ba7428c90a638a5
blog_body_sha256: 096c5b2c59f7ed0980e335ed7ce5ec2caaf656f1b5c8b37227f0f7eb4435e7f0
synced_at: '2026-10-05'
type: survey
created: '2026-06-18'
tags:
- Iceberg
- Hudi
- Delta Lake
- Catalog
- Lakehouse
issue: 6
issue_date: '2026-06-18'
---

> 采集时间：2026-06-18 | 范围：Apache Iceberg / Delta Lake / Apache Hudi / Catalog 生态

---

## Apache Iceberg

### 1. Apache Iceberg 1.11.0 正式发布（2026-05-19）

- **链接**：[https://iceberg.apache.org/blog/category/release/](https://iceberg.apache.org/blog/category/release/)
- **摘要**：1.11.0 是一次里程碑发布。核心变化：

  - **REST Catalog 成熟化**：服务端扫描规划（Remote Scan Planning）、ETag 缓存实现 freshness-aware 表加载、幂等键（Idempotency-Key）支持提交重试安全；
  - **引擎升级**：Spark 4.1 + Flink 2.1 成为默认构建目标，MERGE INTO 支持自动 Schema Evolution；
  - **查询加速**：LIMIT 下推、向量化读取覆盖更多 Parquet 编码；
  - **安全**：内置表加密（Envelope Encryption + Google KMS）；
  - **v4 Table Spec 基础**：DynamicIcebergSink 实验性多表路由写入。

- **标签**：`Iceberg` `1.11` `REST Catalog` `Spark 4.1` `release`

### 2. Iceberg v4 Spec 讨论持续升温（2026-06-09）

- **链接**：[https://dev.to/alexmercedcoder/apache-iceberg-v4-the-current-state-the-proposals-and-why-they-matter-3e07](https://dev.to/alexmercedcoder/apache-iceberg-v4-the-current-state-the-proposals-and-why-they-matter-3e07)
- **摘要**：Iceberg v4 尚未定稿，正处于 IEP（Iceberg Enhancement Proposal）阶段。当前讨论的焦点包括：为流式写入和 AI 工作负载优化的新存储布局、更细粒度的读限制（Finer Grained Read Restrictions）已在 Apache 邮件列表活跃讨论（2026-06-09），以及社区正着手 1.12 版本规划。Snowflake 的技术博客指出 v4 将"面向流式和 AI 场景优化数据管道"。
- **标签**：`Iceberg` `v4 Spec` `IEP` `流式` `AI优化`

---

## Delta Lake

### 3. Delta Lake 4.2.0 发布（2026-04-17），Flink + Kernel 生态扩展

- **链接**：[https://delta.io/blog/2026-04-17-delta-4-2-released/](https://delta.io/blog/2026-04-17-delta-4-2-released/)
- **摘要**：4.2.0 两大进展：

  - **Delta Kernel 新的 Flink Connector**：替代已弃用的旧版连接器，原生支持 Catalog-Managed Table，提供事务性精确一次语义（Sink Writer + Committer）；
  - **数据类型扩展**：Kernel 新增地理空间、排序规则（collation）、VARIANT 类型支持；
  - **Catalog-Managed Table 成熟化**：原子操作、SQL Schema Evolution、同步 UniForm；
  - 流式改进。Databricks 在 Data + AI Summit 2026（6/15-18 正在进行）设置 Delta Lake 专题轨道。

- **标签**：`Delta Lake` `4.2` `Kernel` `Flink` `Catalog-Managed`

### 4. Databricks 宣布 Unity Catalog + Iceberg v3 GA（2026-05-28）

- **链接**：[https://www.databricks.com/blog/unity-catalog-and-next-era-apache-icebergtm](https://www.databricks.com/blog/unity-catalog-and-next-era-apache-icebergtm)
- **摘要**：Databricks 在 Data + AI Summit 前夕宣布 Iceberg v3 GA，核心能力：

  - **Managed Iceberg GA**：在 Unity Catalog 中直接创建/读写/优化/治理 Iceberg 表，支持 Predictive Optimization 和 Liquid Clustering；
  - **Iceberg v3 GA**：删除向量（Deletion Vectors）、行追踪、VARIANT 类型原生支持；
  - **Foreign Iceberg GA**：注册并安全查询外部 Catalog 管理的 Iceberg 表；
  - **Cross-engine ABAC Beta**：通过 REST Catalog Scan API 对外部 Iceberg 引擎实施细粒度访问控制；
  - **External Sharing 到 Iceberg 客户端 GA**——数据共享生态扩展至任何 Iceberg REST 兼容客户端。

- **标签**：`Delta Lake` `Unity Catalog` `Iceberg v3` `GA` `治理` `Data+AI Summit`

---

## Apache Hudi

### 5. Apache Hudi 1.2.0 发布：面向 AI 和多模态数据的开放 Lakehouse（2026-06-07）

- **链接**：[https://hudi.apache.org/blog/2026/06/10/stateless-global-upserts-for-flink-streaming-in-apache-hudi-1-2-0/](https://hudi.apache.org/blog/2026/06/10/stateless-global-upserts-for-flink-streaming-in-apache-hudi-1-2-0/)
- **摘要**：Hudi 1.2.0 是本周最大亮点，标志着 Lakehouse 正式进入 AI/多模态时代：

  - **多模态数据支持**：embeddings、图像、视频现在可以和结构化数据共存于同一张表中（Hudi 官方博客："Ship multimodal support. Embeddings, images, and video now sit in the same tables as your structured data"）；
  - **Flink 无状态全局 Upsert**：首次通过 Record Level Index (RLI) 为 Flink Writer 提供可扩展的全局 Upsert，Index 存储在 Metadata Table 而非 Flink State 中，解决了大型表的 checkpoint/recovery 瓶颈；
  - 路线图显示 Hudi 2.0.0 目标 2026 年 6 月，加速向 AI 原生 Lakehouse 平台演进。

- **标签**：`Hudi` `1.2` `多模态` `AI` `Flink` `RLI` `release`

---

## 数据湖仓 / Catalog 生态

### 6. Apache Gravitino 1.2.0：从元数据 Catalog 到运营平台（2026-03-13）

- **链接**：[https://datastrato.ai/blog/gravitino-1-2-0-introduction/](https://datastrato.ai/blog/gravitino-1-2-0-introduction/)
- **摘要**：Gravitino 1.2 实现从被动元数据目录到主动运营层的转变。三大新能力：

  - **Table Maintenance Service**：分区级表健康主动管理——针对小文件积累和删除债务的精准优化，而非全表级别的昂贵 COMPACT；
  - **UDF 管理**：将转换逻辑变为受治理的 Catalog 资产；
  - **服务端扫描规划**：轻量级 AI 查询可通过 Python 直接运行，无需全量查询引擎。1.2.1 补丁版于 5 月 12 日发布，聚焦稳定性和性能。

- **标签**：`Gravitino` `1.2` `Catalog` `运维` `UDF` `Table Maintenance`

### 7. Apache Polaris 毕业为 TLP + Lance 集成推动多模态 Lakehouse（2026-02/01）

- **链接**：[https://polaris.apache.org/blog/2026/01/06/apache-polaris-and-lance-bringing-ai-native-storage-to-the-open-multimodal-lakehouse/](https://polaris.apache.org/blog/2026/01/06/apache-polaris-and-lance-bringing-ai-native-storage-to-the-open-multimodal-lakehouse/)
- **摘要**：Apache Polaris 于 2026 年 2 月 19 日正式从 Incubator 毕业为 Apache 顶级项目，成为 Iceberg REST Catalog 生态中最具独立性的开源 Catalog 实现。今年 1 月宣布与 Lance（AI 原生列存储格式）集成，推动开放多模态 Lakehouse 架构——Lance 提供面向 AI 的列存储格式和表格式，Polaris 提供统一 Catalog/治理层。近期 GitHub PR（2026-06-02）仍在活跃维护 Polaris + Lance 集成文档和配置。
- **标签**：`Polaris` `TLP` `Lance` `多模态` `AI-Native` `Catalog`

---

## 本周关键趋势总结

| 趋势 | 关键信号 |
|------|----------|
| **Lakehouse 全面拥抱多模态 AI** | Hudi 1.2 直接内建 embeddings/图像/视频支持；Lance + Polaris 推动 AI Native 存储 |
| **Catalog 成为竞争主战场** | Iceberg REST Catalog 成熟化、Databricks Unity Catalog 开放 interoperability、Polaris 毕业 TLP |
| **Flink 流批一体加速** | Iceberg 1.11 Flink 2.1 支持 + DynamicIcebergSink；Hudi 1.2 Flink RLI 全局 Upsert；Delta 4.2 Kernel Flink Connector |
| **Iceberg v4 预热** | v4 Spec 设计讨论活跃，社区对齐流式 + AI 场景优化方向；1.12 版本已在规划 |
| **运维自动化向内建** | Gravitino Table Maintenance Service、Unity Catalog Predictive Optimization——从被动治理到主动运维 |

---

## 数据来源

- Apache Iceberg 官方博客 & GitHub
- Delta Lake 官方博客 (delta.io)
- Apache Hudi 官方博客
- Databricks Blog / Unity Catalog 公告
- Snowflake Engineering Blog
- Apache Gravitino / Polaris 官方博客
- DEV Community (Alex Merced 技术分析)
- Onehouse Blog
- Data + AI Summit 2026 议程
