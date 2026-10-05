---
title: '🏗️ 面向 AI 的数据平台建设 · 周报 #4（2026-06-11）'
blog_url: https://bryantchang1992.github.io/ai_memory_chang_ai_team/posts/tech-research/week-04/data-for-ai/
blog_source: _posts/2026-06-11-data-for-ai-week-04.md
blog_source_commit: f83970fa7e6ad32d626cc6ca3ba7428c90a638a5
blog_body_sha256: acf1224c2bbaee44750b7aeb771ab977ee4baf440a3a48afd4c75272933d99e1
synced_at: '2026-10-05'
type: survey
created: '2026-06-11'
tags:
- 数据平台
- Lakehouse
issue: 4
issue_date: '2026-06-11'
---

## 📌 本周综述

> **📌** **本期要点：**Apache Hudi 1.2 正式发布——原生 VECTOR / BLOB / VARIANT 类型 + Lance 格式集成，将 Lakehouse 推入多模态 AI 时代；Databricks Unity Catalog 全面 GA Iceberg v3 + 跨引擎 ABAC 治理；Apache Iceberg 1.11.0 引入服务端扫描规划与表级加密；Gravitino 1.2.1 持续强化多 Catalog 联邦。

本周是 2026 年第 24 周（6 月第二周），数据平台建设方向迎来了密集的重大发布。Apache Hudi 1.2 在 6 月 7 日正式发布，这是 **Lakehouse 领域首个将多模态数据存储（VECTOR、BLOB、VARIANT）作为一等公民的正式版本**。同时，Databricks 宣布 Unity Catalog 上 Managed Iceberg、Iceberg v3、Foreign Iceberg 全部 GA，并推出跨引擎 ABAC（Beta）——标志着企业级的开放 Lakehouse 治理体系已经成型。

Lakehouse 正在完成从 **"分析平台"到"AI 原生数据平台"** 的关键升级。

---

## 🪶 Apache Hudi 1.2 发布：Lakehouse 正式拥抱 AI 多模态数据

`🚀 重大版本` `6月7日发布` `多模态`

[Apache Hudi 1.2](https://hudi.apache.org/blog/2026/06/07/apache-hudi-release-1-2-announcement/) 于 6 月 7 日正式发布，这是本周最重量级的消息。继上周追踪到 RFC-100 提案后，该提案仅用不到两周就完成了从设计到发布的全过程——而且交付的远不止非结构化数据存储。

### 核心新特性

| 特性 | 类型 | 说明 | AI 场景意义 |
|------|------|------|------------|
| **VECTOR 类型** | `全新` | 原生嵌入向量类型，内置相似性搜索 | 直接在 Hudi 表上做向量检索，无需外部向量数据库 |
| **BLOB 类型** | `全新` | 存储二进制对象：图片、文档、视频帧 | 训练数据与元数据同表存储，消除跨系统同步 |
| **VARIANT 类型** | `全新` | 原生半结构化数据存储，无需 Schema 展平 | API 响应日志、事件流、ML Feature Store |
| **Lance 文件格式集成** | `集成` | AI 原生列式格式，对图像嵌入和向量有原生优化 | AI 训练/推理的存储层统一 |

### 为什么 Hudi 1.2 是里程碑？

Hudi 1.2 解决了 AI 时代数据平台最核心的痛点——**"同步困境"（Sync Dilemma）**：当前 AI 应用中，同一个业务实体可能同时存在于：

- 结构化元数据在 Lakehouse 表中
- Embedding 向量在 Milvus/Pinecone 等向量数据库中
- 原始文档/图片在 S3 对象存储中
- 半结构化数据在 MongoDB/Elasticsearch 中

这种碎片化导致数据一致性维护成本极高。Hudi 1.2 的答案是：**将 VECTOR、BLOB、VARIANT 全部作为原生列类型存储在同一张 Lakehouse 表中**，共享同一套事务、索引、增量处理、自动表服务和并发控制机制。

> **📌** **🎯 关键判断：**Hudi 1.2 的意义不只是一个版本发布——它重新定义了 Lakehouse 的边界。此前业界需要"Lakehouse + 向量数据库 + 对象存储"的多系统组合，Hudi 1.2 证明了一个表就能承载这一切。

### Lance 集成：AI 列式存储的事实标准正在形成

Hudi 1.2 的 Lance 格式集成与 Fluss Lakehouse Tiering 集成 Lance 方向一致。Lance 是专为 AI/ML 设计的列式格式，Hudi 的事务层 + Lance 的存储层，构成了一种新的架构范式。

### Hudi 1.2 的 Flink 增强

除 AI 多模态外，Hudi 1.2 还显著增强了 Flink 集成，包括改进的 Flink MOR 写入性能和更好的端到端一致性保证。

---

## 🧊 Apache Iceberg 1.11.0：v3 Spec 生产就绪 + 表级加密

`5月19日发布` `v3 Spec` `生产就绪`

[Apache Iceberg 1.11.0](https://github.com/apache/iceberg/releases/tag/apache-iceberg-1.11.0) 于 5 月 19 日发布，正式将 [Iceberg v3 规范](https://tuts.alexmercedcoder.dev/2026/2026-05-28-apache-iceberg-v3-upgrade/)推向生产就绪。

### v3 Spec 六大核心特性

| 特性 | v2 的问题 | v3 的解决方案 | 收益 |
|------|----------|-------------|------|
| **二进制删除向量** | Positional delete 文件随更新堆积，读时合并开销大 | 每个数据文件维护紧凑 bit map | 带 CDC 管线的表读取速度提升一个数量级 |
| **VARIANT 类型** | JSON 存为 String 列，查询时解析或展平成几百列 | 原生半结构化类型，引擎可推谓词到嵌套数据 | 事件流、API 日志、Feature Store 场景大幅简化 |
| **GEOMETRY / GEOGRAPHY** | 空间数据存为 WKT 字符串 | 一等空间类型 + 原生空间 Join | 地理位置分析场景原生支持 |
| **纳秒时间戳** | 微秒精度不满足高频金融/IoT | timestamp_ns / timestamptz_ns | 交易系统、传感器网络精准时序 |
| **默认列值** | 加列需全量数据重写或接受 NULL | ALTER TABLE ADD COLUMN 秒级完成 | TB 级表的 Schema 演化零停机 |
| **行级血缘追踪** | 无原生支持，依赖外部审计日志 | 每行记录创建/修改的 Snapshot + 操作类型 | 合规审计、数据治理原生能力 |

### 服务端扫描规划（Server-side Scan Planning）

1.11.0 在架构层面将元数据操作从引擎端转移到 REST Catalog 端——引擎提交 POST …/plan 请求，Catalog 返回优化后的 FileScanTasks。引擎不再直接访问对象存储的元数据层，实现引擎与存储的更彻底解耦。

### 表级加密

Iceberg 1.11.0 引入封套加密三级密钥体系：Table Master Key（KMS）→ Key Encryption Keys（元数据中）→ Data Encryption Keys（每文件唯一，AES-GCM）。支持 Google KMS 首批集成。

### File Format API 正式化

统一 File Format API 使添加新存储格式变得标准化，对 Lance 等新兴格式的生态扩展意义重大。

> **📌** **💡 洞察：**Iceberg v3 意味着三大 Lakehouse 格式在数据类型丰富度上已基本对齐。但 Hudi 1.2 以 VECTOR + BLOB + Lance 组合在 AI 场景暂时领先。

---

## 🏔️ Databricks Unity Catalog：Iceberg 全面 GA + 跨引擎治理

`MAJOR` `GA` `企业级`

[Databricks 宣布](https://www.databricks.com/blog/unity-catalog-and-next-era-apache-icebergtm) Unity Catalog 上的一系列 Iceberg 能力全面进入 GA 或 Public Preview。Databricks 还提出了 Iceberg v4 与 Delta 5.0 将走向**统一格式**的路线图展望。

### GA/Preview 能力一览

| 能力 | 状态 | 说明 |
|------|------|------|
| Managed Iceberg | `GA` | 在 Unity Catalog 中创建、读写、优化、治理、共享 Iceberg 表 |
| Iceberg v3 | `GA` | Deletion Vectors、Row Tracking、VARIANT 类型全支持 |
| Foreign Iceberg | `GA` | 注册、治理、安全查询外部 Catalog 中的 Iceberg 表 |
| Credential Vending | `GA` | 外部引擎通过 UC 获取凭证，无需直接授予存储权限 |
| 跨引擎 ABAC | `Beta` | 列掩码、行过滤、Tag-based policy 对外部 Iceberg REST 客户端生效 |
| External Sharing → Iceberg | `GA` | 通过 Delta Sharing 协议，任何 Iceberg REST 兼容客户端可读取共享数据 |
| Iceberg 物化视图 | `Gated Preview` | CREATE MATERIALIZED VIEW … USING ICEBERG |
| UNIQUE 约束 | `Public Preview` | Foreign Key 可引用 UNIQUE 列，RELY 启用 Join 消除 |

### 五大维度定义

Databricks 提出的评估框架定义了企业级 Lakehouse Catalog 能力：

1. **Open APIs + Credential Vending** — 任何引擎通过 Iceberg REST API 访问
2. **Catalog Federation** — 一个 UC 管理所有 Iceberg 资产的元数据
3. **跨引擎 ABAC** — 细粒度治理策略在引擎外部执行
4. **开放共享** — 通过 Delta Sharing 协议向 Iceberg 客户端共享
5. **AI 驱动优化** — Predictive Optimization 自动管理

### Roadmap：Iceberg v4 与 Delta 5.0 走向统一

Databricks 明确提到 **"Iceberg v4 and Delta 5.0 will converge on a unified open format"**——如果两大格式在下一大版本实现统一，将终结格式之争，对整个 Lakehouse 生态是核弹级别的变化。

> **🏆 判断：**Databricks 的这波发布不是零散功能更新，而是一张完整的 "开放 Lakehouse 治理蓝图"。对于需要多引擎、多团队、多治理域的企业级 AI 数据平台来说，这套方案是目前最完整的。

---

## 🌐 Apache Gravitino 1.2.1：多 Catalog 联邦治理持续完善

`补丁版本` `治理`

[Apache Gravitino 1.2.1](https://github.com/apache/gravitino/releases) 于 5 月 12 日发布，以稳定性、性能和正确性为重点：

- **Iceberg REST 合规**：修正 config endpoint prefix，修复 table scan planning SQL 生成错误
- **Authorization 性能**：优化 JCasbin 策略查找，大角色权限场景授权性能显著提升
- **Lance Catalog**：清理 GravitinoLanceTableOperations 冗余代码
- **Hive 稳定性**：修复 Hive MetaStore HttpClient 泄漏导致的 OOM
- **Trino Connector**：修复 catalog name 带 metalake 的异常
- **Kubernetes 部署**：增加 serviceAccountName 支持

> **📌** **💡 洞察：**Gravitino 作为 Apache 多 Catalog 治理项目，优势是完全开源和厂商中立。对于非 Databricks 环境的多引擎数据平台，Gravitino 仍然是最值得关注的开源选项。

---

## 📊 趋势分析：AI 数据平台的关键转型点

`趋势` `综合`

### 🔷 趋势一：Lakehouse 从"分析平台"转型为"AI 原生数据平台"

Hudi 1.2 的 VECTOR / BLOB / VARIANT + Lance 不是功能叠加，而是 Lakehouse 定位的根本性变化。此前 Lakehouse 解决的是"在数据湖上跑 SQL"，现在要解决的是"在一张表里管所有 AI 数据"。

| 格式 | 半结构化 | 向量/嵌入 | 二进制对象 | 空间数据 | AI 列式格式 |
|------|---------|----------|-----------|---------|------------|
| **Apache Hudi 1.2** | ✅ VARIANT | ✅ VECTOR + 相似搜索 | ✅ BLOB | — | ✅ Lance |
| **Apache Iceberg v3** | ✅ VARIANT | — | — | ✅ GEOMETRY | 🔜 File Format API |
| **Delta Lake 4.2.0** | ✅ Variant GA | — | — | ✅ Geospatial | — |

### 🔷 趋势二：Catalog 成为新的竞争高地

Catalog 不再只是元数据存储，而是 Lakehouse 的智能治理中心。Databricks 的跨引擎 ABAC 在 Catalog 层执行治理策略，对多引擎企业环境至关重要。

### 🔷 趋势三：Iceberg v4 + Delta 5.0 可能走向统一

如果成为现实，将终结格式之争。对 Hudi 来说构成压力——需要进一步强化差异化优势（多模态 AI 数据管理正是其最有力的差异点）。

### 🔷 趋势四：从"多系统组合"到"单表承载一切"

Hudi 1.2 的 Unified Data Foundation 愿景正在挑战现有 AI 数据架构惯例。对 Less-than-real-time 的 AI 场景，内嵌向量搜索的 Lakehouse 表可能是更简单的选择。

> **📌** **🎯 对 CHANG_AI_TEAM 的关键启示：**
> - **多模态 Lakehouse 是确定性趋势**：设计 AI 数据平台时应考虑未来多模态数据在同一存储层管理的架构
> - **Lance 格式值得重点跟踪**：Hudi、Fluss 都在集成 Lance，它可能成为 AI 列式存储的事实标准
> - **Catalog 架构需要前瞻设计**：跨引擎 ABAC、Catalog Federation、Server-side planning 是下一代 Catalog 的核心能力
> - **关注 Iceberg v4 + Delta 5.0 统一进展**：如果实现，将重塑整个 Lakehouse 生态格局
> - **向量数据库选型需要重新评估**：如果 Lakehouse 原生支持 VECTOR 类型和相似搜索，独立向量数据库的非低延迟场景必要性可能下降

---

## 🔗 信息来源

### Apache Hudi

- [Hudi 1.2 官方发布公告](https://hudi.apache.org/blog/2026/06/07/apache-hudi-release-1-2-announcement/)
- [Hudi 1.2 Release Notes](https://hudi.apache.org/releases/release-1.2)
- [Apache Hudi GitHub](https://github.com/apache/hudi)

### Apache Iceberg

- [Iceberg 1.11.0 GitHub Release](https://github.com/apache/iceberg/releases/tag/apache-iceberg-1.11.0)
- [Google Open Source Blog：Iceberg 1.11.0](https://opensource.googleblog.com/2026/05/announcing-apache-iceberg-1110.html)
- [Iceberg v3 升级指南](https://tuts.alexmercedcoder.dev/2026/2026-05-28-apache-iceberg-v3-upgrade/)
- [Iceberg 官方 Releases](https://iceberg.apache.org/releases/)

### Databricks / Unity Catalog

- [Databricks Blog：Unity Catalog & Iceberg](https://www.databricks.com/blog/unity-catalog-and-next-era-apache-icebergtm)
- [Databricks SQL Release Notes 2026](https://learn.microsoft.com/en-us/azure/databricks/sql/release-notes/2026)

### Apache Gravitino

- [Gravitino 1.2.1 GitHub Release](https://github.com/apache/gravitino/releases)
- [Apache Gravitino GitHub](https://github.com/apache/gravitino)

### 生态参考

- [Lakehouse: A New Generation (CIDR 2021)](https://www.cidrdb.org/cidr2021/papers/cidr2021_paper17.pdf)
- [2025 & 2026 Ultimate Guide to the Data Lakehouse](https://iceberglakehouse.com/posts/2025-09-2026-guide-to-data-lakehouses/)
- [Apache Iceberg in 2026: The Open Table Format That Won](https://jamesm.blog/data-engineering/apache-iceberg-2026/)

---

*CHANG_AI_TEAM · 面向 AI 的数据平台建设 · 周报 #4 · 2026年6月11日*
