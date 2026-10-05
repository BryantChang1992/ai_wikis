---
title: '🏗️ 面向 AI 的数据平台建设 · 周报 #2（2026-05-28）'
blog_url: https://bryantchang1992.github.io/ai_memory_chang_ai_team/posts/tech-research/week-02/data-for-ai/
blog_source: _posts/2026-05-28-data-for-ai-week-02.md
blog_source_commit: f83970fa7e6ad32d626cc6ca3ba7428c90a638a5
blog_body_sha256: a56faa85b51ef5c738abe33f6ce85c00f80a001e11617487c8e586a8333a0e8d
synced_at: '2026-10-05'
type: survey
created: '2026-05-28'
tags:
- 数据平台
- Lakehouse
issue: 2
issue_date: '2026-05-28'
---

## 🔥 本周重磅：Iceberg 1.11.0 正式发布

`BREAKING` `NEW`

2026年5月19日-20日，**Apache Iceberg 1.11.0** 正式发布。这是 Iceberg 项目在 2026 年的第一个大版本，也是确立其 Lakehouse 格式领导地位的重要更新。本次发布涉及多平台适配、Spark 4.0/4.1 支持、多项特性废除以及 REST 协议扩展，标志着 Iceberg 进入全面成熟期。

### 核心变更速览

| 类别 | 变更项 | 影响范围 |
|------|--------|---------|
| `BREAKING` | 终止支持 Position Delete Files with Row Data（#14045） | 所有使用 v1 delete file 的用户 |
| `DEPRECATED` | 移除 Java 11 支持（#14400） | 仍运行在 Java 11 的集群 |
| `DEPRECATED` | 废弃 Spark 3.4 支持（#14099） | Spark 3.4 集群（建议升级至 3.5+） |
| `DEPRECATED` | 移除 Flink 1.19 支持（#13714） | Flink 1.19 集群（建议升级至 1.20+） |
| `NEW` | 扩展 REST Client Header 支持（#12194） | 所有使用 REST Catalog 的部署 |
| `NEW` | Spark 4.0 PartitionStatistic 支持 | Spark 4.0 用户 |
| `NEW` | 新增 Spark 4.1 Runtime Jar | Spark 4.1 用户 |

### 支持的平台版本

| 平台 | 支持版本 |
|------|---------|
| **Spark** | 4.1、4.0、3.5（Scala 2.12 + 2.13） |
| **Flink** | 2.1、2.0、1.20 |
| **Cloud Bundles** | AWS、GCP、Azure |

值得注意的是，Java 11 被彻底移除、Flink 1.19 和 Spark 3.4 被废弃的背后，反映的是社区对 **"向前看"策略的坚定执行**——不再为过时的运行时背负技术债务，集中资源在新一代计算引擎上。

> **📌** **💡 关键洞察：**Iceberg 1.11.0 的版本策略传递了明确信号——Java 17 是最低基线，Spark 3.5+ 和 Flink 1.20+ 是推荐配置。如果你的数据平台还跑在更老的版本上，现在是升级的黄金窗口期。

---

## 🧊 Apache Iceberg 1.11.0 深度拆解

从**工程决策**和**架构演进**的视角深入拆解每个关键变更。

### 1. 废止 Position Delete Files with Row Data（#14045）

Position Delete Files 允许在文件级别记录需要删除的行，而 "with Row Data" 变体在 delete 文件中同时存储了实际行数据。这种双负载设计在工程实践中增加了 I/O 路径的复杂度和存储开销。**社区决定转向更纯粹的 delete 文件语义**，将行数据回填的需求交给上层应用逻辑处理。这本质上是一次「职责分离」重构——delete 文件只负责标记删除，不再承担数据承载的角色。

### 2. Java 运行时基线提升（Java 11 → Java 17+）

移除 Java 11 支持（#14400）是一个必然但痛苦的决定。Java 17（LTS）已经发布了 5 年，提供了显著的性能改进。Iceberg 社区引用了一个常见的工程权衡：**维护过时的运行时兼容性，其成本已经超过了仍在使用 Java 11 的用户的迁移成本**。

### 3. REST Catalog 协议增强（#12194）

扩展 REST Client Header 支持是一个看似微小但意义重大的改动。它允许在 REST Catalog 的 HTTP 通信中传递自定义 Header，解决了几个关键场景：

- **认证链传递**：在微服务/多租户架构中透传鉴权信息
- **链路追踪**：注入分布式追踪的 trace-id 等上下文
- **流量标识**：标记请求来源（batch / interactive / AI workload）

这标志着 **REST Catalog API 正在从"能通"走向"可运维"**，对构建企业级数据平台至关重要。

### 4. Spark 版本矩阵重整

本次发布对 Spark 的支持形成了清晰的三个梯队：**尖端（4.1）、主流（4.0）、稳定（3.5）**。与 2023-2024 年混乱的 Spark 2.x/3.x 双线维护相比，当前策略更加聚焦。

> **📌** **🏗️ 架构影响评估：**对于典型的四层数据架构（Ingestion → Storage → Compute → Serving），Iceberg 1.11.0 的影响主要集中在 *Compute* 和 *Serving* 层。REST Catalog 的增强将推动 Catalog 层向标准化方向发展。

---

## 🏛️ Lakehouse 格式格局 2026：战争终结

`趋势` `分析`

持续多年的 "Table Format Wars"——Apache Iceberg vs. Delta Lake vs. Apache Hudi——在 2026 年被多位分析师认定为**实质上已见分晓**。但这并非简单的「赢家通吃」，而是进入了**差异化分工**的新阶段。

### 🥇 Apache Iceberg

已成为开放表格式的**事实标准**。跨引擎互操作性最强，REST Catalog 生态最活跃。被 Snowflake、AWS、Google Cloud 等多云厂商采用为原生格式。Snowflake 的 Polaris、AWS 的 S3 Tables、Dremio 的 Nessie 均以 Iceberg 为核心。

`领导者` `开放标准`

### 🥈 Delta Lake

在 **Databricks 生态内保持强势**。Unity Catalog 提供了端到端治理体验。Delta 3.0+ 逐步向开源靠拢（Delta Kernel 等），但社区多元性仍不及 Iceberg。适合深度绑定 Databricks 的组织。

`生态绑定` `全栈体验`

### 🥉 Apache Hudi

在**流式处理和 CDC 场景**中找到差异化定位。Hudi 的增量查询和 Upsert 能力在实时数仓场景中仍有独特价值。社区规模较小但聚焦，主要被 Uber（原创者）、Amazon 等用于实时数据同步。

`利基市场` `流式/CDC`

> **🏆 结论：**格式战争已从「三强混战」演变为清晰的格局——**Iceberg 作为通用开放标准**，Delta Lake 作为 Databricks 生态的深度整合方案，Hudi 作为流式场景的专业选手。对于建设面向 AI 的数据平台，**Iceberg 是最安全、最具未来兼容性的选择**。

### 对数据平台选型的启示

- **不绑定单一厂商**：选择 Iceberg 意味着你可以自由切换计算引擎（Spark / Flink / Trino / Snowflake / BigQuery）
- **REST Catalog 是关键**：Iceberg 的开放 Catalog API 使得元数据治理可以实现跨引擎统一
- **Delta Lake 不是"错误"选择**：如果你的组织已经是 Databricks Heavy User，继续使用 Delta Lake 是完全合理的
- **Hudi 关注但不必须**：除非有大规模 CDC 入湖场景，否则 Hudi 不是选型的首要考量

---

## 📋 统一 Catalog 演进：Polaris、Unity 与开放 API

`NEW` `趋势`

如果说 Table Format 决定了数据如何存储，那么 **Catalog 决定了数据如何被发现、治理和共享**。2026年5月，Catalog 层面的演进同样精彩。

### Polaris "Generic Tables" — 打破格式壁垒

Snowflake 开源的 [Apache Polaris](https://github.com/apache/polaris)（Incubating）在最近的更新中引入了 "Generic Tables" 概念——这是一个**关键信号**：Polaris 不再只是 Iceberg 的 Catalog，而开始管理非 Iceberg 格式的表。这意味着：

- 一个 Catalog 可以同时管理 Delta Lake 表、Iceberg 表、甚至传统 Hive 表
- 企业可以在统一治理层下逐步迁移格式，避免「大爆炸式」迁移
- Data Lakehouse Weekly 提到，下一版本中 Generic Tables 将获得更多打磨

### 三大 Catalog 体系对比

| Catalog | 维护方 | 核心格式 | 开放性 | 关键特性 |
|---------|--------|---------|--------|---------|
| **Apache Polaris** | Snowflake / Apache | Iceberg（主）→ Generic Tables | ⭐⭐⭐⭐⭐ | Apache Incubating，100% 开源，REST API |
| **Unity Catalog** | Databricks | Delta Lake（原生） | ⭐⭐⭐ | 开源版功能受限，商业版全功能 |
| **AWS Glue Catalog** | AWS | S3 Tables (Iceberg-native) | ⭐⭐ | AWS 生态深度集成，跨云能力弱 |

> **📌** **🔮 展望：**Catalog 层正在成为数据平台的**新控制面（Control Plane）**。在 AI 时代，模型训练管线需要访问分散在多个系统中的数据，统一 Catalog 将决定数据发现效率的下限。Polaris 的 Generic Tables 方向值得持续跟踪。

---

## 🤖 AI + 数据平台融合趋势

`热点` `融合`

随着 LLM/ML 工作负载在数据平台中的占比不断提升，2026 年 5 月的讨论焦点已从「能否在数据平台上跑 AI」转向「**如何让数据平台原生支持 AI 工作负载**」。

### 1. Iceberg — AI 数据访问的通用接口

传统 ML 训练的数据访问链路涉及多个阶段的数据复制（Data Lake → Feature Store → Training Storage），每个环节都引入延迟和一致性风险。Iceberg 的**快照隔离（Snapshot Isolation）**和**时间旅行（Time Travel）**能力，使得训练流程可以直接在 Lakehouse 中访问一致的数据快照，无需额外的数据拷贝。

- **模型可复现性**：通过 Iceberg Snapshot ID 精确锁定训练所用的数据版本
- **增量训练**：基于 Snapshot Diff 获取增量数据，避免全量重读
- **特征工程统一**：特征计算可以下沉到 Iceberg 表，使用 Spark/Flink 等引擎统一处理

### 2. 向量数据库 × Lakehouse — RAG 的新基础设施

RAG（Retrieval-Augmented Generation）架构正在推动**向量数据库与 Lakehouse 的融合**：

| 向量数据库 | 与 Lakehouse 的集成方式 | 适用场景 |
|-----------|------------------------|---------|
| **Milvus** | Bulk Insert 直接读取 Parquet/Iceberg 文件 | 大规模向量检索（亿级+） |
| **Qdrant** | 通过 Spark Connector 从 Lakehouse 同步 | 轻量级 RAG、边缘部署 |
| **Weaviate** | 原生 S3/Iceberg Backend 支持（实验性） | 多模态 RAG、混合搜索 |

核心逻辑是：**Lakehouse 作为「唯一真相源」（Source of Truth）**，向量数据库作为面向低延迟检索的「读优化视图」。embedding 生成和索引构建在 Lakehouse 侧完成，检索服务由向量数据库提供。

### 3. 数据平台架构演进路线图

| 阶段 | 关键词 | 核心能力 | 当前状态 |
|------|--------|---------|---------|
| **L1：基础 Lakehouse** | Iceberg + Catalog | ACID 事务、时间旅行、Schema 演化、多引擎访问 | ✅ 已成熟 |
| **L2：AI-Ready 数据层** | Snapshot + 特征工程 | 训练数据版本化、增量数据发现、特征计算下沉 | 🔄 推进中 |
| **L3：Lakehouse-Native RAG** | 向量索引 + 检索 | Lakehouse 原生向量索引、混合搜索 | 🔬 探索中 |
| **L4：自主学习数据平台** | Agentic Data Ops | AI Agent 自主治理/优化数据管道 | 💡 概念阶段 |

> **📌** **🎯 对 CHANG_AI_TEAM 的建议：**当前应聚焦 L1→L2 的过渡——基于 Iceberg 建立 AI-Ready 数据层，特别是训练数据版本化和增量数据发现能力。RAG 集成可以先从 Milvus + Iceberg Bulk Insert 的方案起步，避免过早引入复杂的原生向量索引。

---

## 🔗 信息来源

### 官方发布

- [Apache Iceberg Official Releases](https://iceberg.apache.org/releases/)
- [Apache Iceberg 1.11.0 GitHub Release](https://github.com/apache/iceberg/releases/tag/apache-iceberg-1.11.0)
- [Apache Polaris GitHub](https://github.com/apache/polaris)

### 行业分析

- [James M Blog: Iceberg vs Delta vs Hudi 2026](https://jamesm.blog/data-engineering/iceberg-vs-delta-vs-hudi-2026/)
- [Algoscale: Lakehouse Format Comparison 2026](https://algoscale.com/go/blog/iceberg-vs-delta-vs-hudi-2026/)
- [Reintech: Table Format Comparison 2026](https://reintech.io/blog/apache-iceberg-vs-delta-lake-vs-apache-hudi-2026-table-format-comparison)
- [Data Lakehouse Weekly (May 13-20, 2026)](https://dev.to/alexmercedcoder/apache-data-lakehouse-weekly-may-13-20-2026-17a4)

### 技术参考

- [Milvus Bulk Insert Documentation](https://milvus.io/docs/bulk_load.md)

---

*CHANG_AI_TEAM · 面向 AI 的数据平台建设 · 周报 #2 · 2026年5月28日*
