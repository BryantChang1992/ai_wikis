---
title: '🏗️ 面向 AI 的数据平台建设 · 周报 #3（2026-06-04）'
blog_url: https://bryantchang1992.github.io/ai_memory_chang_ai_team/posts/tech-research/week-03/data-for-ai/
blog_source: _posts/2026-06-04-data-for-ai-week-03.md
blog_source_commit: f83970fa7e6ad32d626cc6ca3ba7428c90a638a5
blog_body_sha256: cb49da4aead6396671ccf173c8d5f186fa0a6c7593925d9d5a6add18129fae9e
synced_at: '2026-10-05'
type: survey
created: '2026-06-04'
tags:
- 数据平台
- Lakehouse
issue: 3
issue_date: '2026-06-04'
---

## 📌 本周综述

> **📌** **本期要点：**Delta Lake 4.2.0 发布——Flink connector、Geospatial/Variant GA、安全加固；Hudi RFC-100（非结构化数据存储）合并——Lakehouse 架构向多模态数据迈出关键一步。

本周是 2026 年第 23 周（6 月第一周），数据平台建设方向迎来多个重要更新。Delta Lake 发布了 4.2.0 版本，在流处理集成（Flink connector）和多模态数据类型（Geospatial/Variant GA）方面有重大突破，同时进行了全面的安全加固。Apache Hudi 社区则发起了里程碑式的 RFC-100 提案，正式将非结构化数据存储纳入 Lakehouse 架构的视野，标志着**Lakehouse 从"结构化数据湖"向"多模态数据平台"的关键转型**。

结合 Fluss 社区的 Lakehouse Tiering 深度推进（Arrow 列存、Lance 集成），本周的信号非常清晰：**面向 AI 的数据平台正在进入多模态、流批一体、安全优先的新阶段**。

---

## 🔺 Delta Lake 4.2.0 — Flink Connector + Geospatial GA

`MAJOR` `5月末发布`

[Delta Lake 4.2.0](https://github.com/delta-io/delta/releases/tag/v4.2.0) 基于 Apache Spark 4.1.0/4.0.1，包含多项重大更新。这是 Delta Lake 在流处理和 AI 数据场景下的重要版本。

### 核心变更速览

| 类别 | 变更项 | 状态 | 影响范围 |
|------|--------|------|---------|
| `流处理` | Kernel-based Flink Connector | 实验性 | Flink 用户可直接读写 Delta 表并与 Catalog 集成 |
| `流处理` | Delta Spark V2 Connector 流式读取增强 | 实验性 | 支持 startingTimestamp、skipChangeCommits 等选项 |
| `多模态` | Kernel Geospatial + Variant GA + Collations | GA | geometry/geography 类型读写，Variant 类型正式 GA |
| `治理` | Unity Catalog Managed Table 增强 | 实验性 | REPLACE TABLE/RTAS、Dynamic Partition Overwrite |
| `安全` | 全表面安全加固 | — | 更严格的验证和依赖安全扫描 |

### 1. Kernel-based Flink Connector

全新的基于 **Delta Kernel** 的 Flink connector，让 Flink 可以直接读写 Delta 表并与 Catalog 集成。这是 Delta 在**流处理生态的重大扩展**——在此之前，Flink 生态中读写 Delta 表主要依赖社区的非官方 connector 或通过 Spark 桥接。Delta Kernel 作为核心抽象层，使得跨引擎的读写一致性得到了原生保证。

这对 AI 数据平台的意义在于：**实时特征工程管线可以直接在 Flink 上操作 Delta 表**，无需数据格式转换或引擎切换。

### 2. Geospatial + Variant GA

Delta Kernel 现在可以读写 `geometry`/`geography` 类型的表（带 bounding-box data skipping），**Variant 类型正式 GA**，支持 collated string 类型。Variant 类型对 AI 场景尤其关键——当数据来源多样（JSON、Protobuf、非结构化）且 Schema 不确定时，Variant 提供了一种灵活的半结构化存储方式，同时保留了 Delta 的事务和查询优化能力。

### 3. 安全加固

Delta 项目在多个表面区域进行了大规模安全加固，包括更严格的输入验证和依赖安全扫描，以主动降低供应链风险。这标志着**安全从"功能"升级为版本发布的基础要求**。

> **📌** **💡 关键洞察：**Delta Lake 4.2.0 最值得关注的是 Flink connector 的引入——它标志着 Delta 正在从 "Spark-first" 转向 "multi-engine"。结合 Variant GA 和多模态类型的支持，Delta 正在为 AI 工作负载的多引擎、多模态需求做准备。

---

## 🪶 Apache Hudi RFC-100：非结构化数据存储

`里程碑` `多模态`

Hudi 的核心贡献者 vinothchandar 提交了 [RFC-100：Unstructured Data Storage in Hudi](https://github.com/apache/hudi/pull/13924)，这是 Lakehouse 架构向多模态数据演变的关键里程碑。

### 为什么重要？

传统的 Hudi 以及其他 Lakehouse 格式（Iceberg、Delta）主要是为**结构化数据**设计的——行和列、固定 Schema、Parquet 存储。但在 AI 时代，数据平台的输入越来越多样化：

- **图像/视频帧**：用于计算机视觉模型训练
- **文本语料**：LLM 预训练和微调
- **JSON Blob / 日志**：半结构化诊断数据
- **向量嵌入**：RAG 服务的知识库数据
- **音频/时序**：多模态模型输入

### 两种技术方案

| 方案 | 核心思路 | 优点 | 缺点 |
|------|---------|------|------|
| **方案 A：Column Group + Column Family** | 在现有 File Group 上增加 Column Group 维度，将宽表列按 Column Group 拆分存储 | 独立 compaction 和查询；与现有 Hudi 架构兼容性好 | 增加了元数据管理复杂度 |
| **方案 B：Virtual Tables** | 将 Column Group 视为共享 Timeline 的独立虚拟表 | 独立管理生命周期，隔离性好 | 查询需要 UNION 操作，跨表查询效率可能下降 |

### Lance 集成可能性

提案还讨论了与 **Lance 格式**的集成——利用 Lance 的高效列式存储来管理非结构化数据，同时保留 Hudi 的事务和增量处理能力。Lance 是专为 AI/ML 设计的列式格式，对图像嵌入、向量等数据类型有原生优化。这种集成思路与 **Fluss 社区在 Lakehouse Tiering 中集成 Lance** 的方向不谋而合。

> **🏆 判断：**RFC-100 尚未完成设计，但它的出现标志着 Lakehouse 社区的一个共识——**"非结构化数据也是 Lakehouse 的一等公民"**。对 CHANG_AI_TEAM 而言，当前不需要在技术方案上做选择，但需要关注 Hudi 的选择将如何影响 AI 训练管线的数据访问模式。

---

## 📊 Lakehouse 生态趋势：多模态 × 流批一体 × 安全

`趋势` `综合`

本周 Delta Lake 4.2.0 发布、Hudi RFC-100 提案、以及 Fluss 社区的 Lakehouse Tiering 深度推进，共同勾勒出 Lakehouse 生态三个明确的演进方向：

### 🔷 方向一：多模态数据存储成为新方向

三大 Lakehouse 项目都在向 "不仅存结构化数据" 的方向演进——这些不是巧合，而是对 AI 工作负载的集体响应：

- **Delta Lake**：Variant 类型 GA、Geospatial 类型支持——让半结构化和空间数据成为湖的一等公民
- **Apache Hudi**：RFC-100 正式将非结构化数据纳入架构讨论——Column Group + Lance 集成
- **Apache Fluss**：Lakehouse Tiering 中集成 Lance 和 Arrow 列存——流式写入 + 列存读取的多模态流水线

### 🔷 方向二：流批一体加速

Delta 推出 Flink connector、Fluss 强化 Flink 集成——Lakehouse 和流处理的边界正在消失，"流式写入 + 批式查询"正在成为标配：

| 项目 | 流式写入 | 批式查询 | 流式消费 | 多引擎支持 |
|------|---------|---------|---------|-----------|
| **Delta Lake** | ✅ Spark Structured Streaming | ✅ Spark / Trino / Presto | ✅ Flink (new!) | Spark / Flink / Trino |
| **Apache Fluss** | ✅ Flink / Native | ✅ Flink / Spark | ✅ Flink Native | Flink / Spark / Rust |
| **Apache Iceberg** | ✅ Flink / Spark | ✅ Spark / Trino / Snowflake | ✅ Flink | Spark / Flink / Trino / Snowflake |

### 🔷 方向三：安全性从功能变为基建

Delta Lake 4.2.0 的安全加固、Fluss 的 SASL 限制和 S3 Token 脱敏——安全不再是一个 Feature，而是版本发布的基础要求。数据平台承载的组织数据越重要，安全就越不能是可选的附加功能。

> **📌** **🎯 对 CHANG_AI_TEAM 的关键启示：**
> - **多模态是刚需而非噱头**：如果 AI 平台只存结构化数据，将无法支撑图像、文本、向量等现代 ML 工作负载
> - **Flink connector 标志 Delta 的生态开放**：Delta 不再只是 Spark 生态的一部分，这对多引擎架构至关重要
> - **关注 Lance 格式**：多个项目（Hudi、Fluss）都在向 Lance 靠拢，它可能成为 AI 数据列式存储的事实标准
> - **安全需要基建先行**：在新平台建设中，安全架构应该从设计阶段就纳入，而非后期补丁

---

## 🔗 信息来源

### 官方发布

- [Delta Lake 4.2.0 GitHub Release](https://github.com/delta-io/delta/releases/tag/v4.2.0)
- [Hudi RFC-100 · Unstructured Data Storage](https://github.com/apache/hudi/pull/13924)

### 生态参考

- [Apache Hudi GitHub](https://github.com/apache/hudi)
- [Delta Lake GitHub](https://github.com/delta-io/delta)
- [Apache Fluss GitHub](https://github.com/apache/fluss)
- [Fluss Tiering Service Deep Dive Part 1](https://fluss.apache.org/blog/fluss-tiering-service-deep-dive-part1/)

---

*CHANG_AI_TEAM · 面向 AI 的数据平台建设 · 周报 #3 · 2026年6月4日*
