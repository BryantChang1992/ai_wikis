---
title: 技术调研周报 — Week 09 (2026-07-02)
blog_url: https://bryantchang1992.github.io/ai_memory_chang_ai_team/posts/tech-research/week-09/
blog_source: _posts/2026-07-02-tech-research-week-09.md
blog_source_commit: f83970fa7e6ad32d626cc6ca3ba7428c90a638a5
blog_body_sha256: 11c90501cabd729d7a1083c57632aa2f1f51c56e7bb842fa9e635eb108f894f3
synced_at: '2026-10-05'
type: survey
created: '2026-07-12'
tags:
- AI Infra
- Agent Harness
- Hermes Agent
- Qwen 3.6
- Flink 2.3.0
- Fluss
- Kafka
- AutoMQ
- Delta Lake
- Doris
- LSM-Tree
- CockroachDB
- CXL
- 湖仓
- 时序数据库
issue: 9
issue_date: '2026-07-02'
---

> 覆盖周期：2026-06-26 ~ 2026-07-02 | Week 09（2026-07-12 修订）

---

## 🧠 AI Infra · Agent 基础设施

→ [子调研详情](https://bryantchang1992.github.io/ai_memory_chang_ai_team/tech_research/ai_harness/week_09_2026-07-02.html)

### 🔥 Hermes Agent：自进化 Agent 登顶 OpenRouter #1

本周 AI Agent 领域最大的事件是 Nous Research 的 Hermes Agent 达到 **140,000+ GitHub Stars** 并被 OpenRouter 列为全球使用量最高的 Agent 应用。Nvidia 官方博客发文推荐，将 Hermes 与 RTX 硬件生态绑定推广。

**四个核心差异化能力**：

| 能力 | 描述 |
|------|------|
| **Self-Evolving Skills** | 遇到复杂任务或收到反馈后，自动将经验保存为可复用 Skill。基于 ICLR 2026 Oral 论文的 DSPy + GEPA 框架实现 skill 自进化（MIT licensed） |
| **Contained Sub-Agents** | 子 Agent 作为短生命周期隔离 Worker，专注子任务，减少主 Agent 混乱，适配本地小模型 |
| **Reliability by Design** | Nous Research 对每个内置 skill/tool/plugin 进行压力测试，30B 参数级模型即可稳定运行 |
| **Active Orchestration Layer** | 不是薄 wrapper，而是主动编排层。同一模型在不同框架下，Hermes 表现一致更强 |

**技术栈与生态**：
- Provider-agnostic（Anthropic / OpenAI / Google / DeepSeek + 本地 Ollama）
- 16+ 消息平台集成，持久化 Memory 跨 session 累积、Cron 定时任务
- **Nvidia 推荐 DGX Spark**（128GB 统一内存）作为"always-on agentic computer"
- 搭配 **Qwen 3.6 27B/35B** 本地部署，性能超越其前代 120B/400B 级模型

**Insight**：Hermes 的成功标志着 Agent 框架从"胶水代码时代"正式进入"编排引擎时代"。自进化 Skill + 隔离子 Agent 的设计与 Microsoft CodeAct 的"模型写代码替代逐轮 tool call"思路形成互补——前者降低框架复杂度，后者降低推理开销。

### Qwen 3.6 发布

Alibaba Qwen 3.6 系列核心看点：
- **Qwen 3.6 27B**：密集模型，匹配前代 400B 模型精度但仅 1/16 参数
- **Qwen 3.6 35B**：~20GB 内存可运行，超越 120B 级前代模型
- 作为 Hermes Agent 的理想运行底座

### Agent 框架 2026 全景对比

JetBrains 官方博客发布 <em>Top Agentic Frameworks for Building Applications 2026</em>，系统对比 LangGraph、CrewAI、AutoGen、Semantic Kernel、Hermes Agent 五大框架。核心结论：2026 年关键决策不再是"要不要用 Agent"，而是"需要多少自主性、控制力和治理能力"。

### HPE Discover 2026：企业 Agent 战略

HPE 在 Las Vegas Discover 2026 宣布面向 GreenLake 和 Morpheus 的 Agent AI 扩展，将 Agent 能力绑定到混合云和自动化堆栈——传统企业基础设施厂商正式入场 Agent 编排。

### 内部：Agent Harness 知识图谱修复

本周内部完成 Agent Harness 系列 wikilink 图谱修复（434c840, 6/29）：综述 + 8 张子卡片的双向引用全部补全，README 索引完整，网状引用密度从 ~60% → 100%。

---

## ⚡ Kafka / AutoMQ / Fluss 社区动态

→ [子调研详情](https://bryantchang1992.github.io/ai_memory_chang_ai_team/tech_research/kafka_research/week_09_2026-07-02.html)

### 🐘 Apache Kafka — 4.4.0 预热

社区将 Kafka 4.4.0 预计发布日期调至 2026 年 9 月，KIP freeze 截止 7/8。

**活跃 KIP**：

| 编号 | 标题 | 状态 |
|------|------|------|
| **KIP-1314** | Broker-side consumer group rebalance callback — 允许 broker 在 rebalance 时触发自定义回调 | 🔵 PR 活跃 |
| **KIP-1320** | Deprecate Utils behind internal implementation | 🟡 PoC（7/5） |

**本周 PR 亮点**（6/26-7/2）：
- **KAFKA-20769** — ListDeserializer 截断输入时静默反序列化损坏条目修复（🔴 安全关键）
- **KAFKA-20538** — RocksDBTimeOrderedKeyValueBuffer 增加 headers 感知能力
- **KAFKA-20197** — Headers-aware StreamPartitioner，允许基于消息 header 的路由分区
- **KAFKA-10025** — RocksDBMetricsRecorder store close 时 value provider 读取保护
- **KAFKA-13009** — 全局 state store 不再加入 per-task subtopologies

**趋势**：Kafka 4.x 进入成熟期，本周 PR 聚焦**稳定性修复 + Streams 能力扩展**。

### ⚡ AutoMQ 1.7.1 发布（6/23）

1.7.0 发布仅 19 天后即推出补丁版，13 个修复：

| 类别 | 修复 |
|------|------|
| **API Key 鉴权** | AutoMQ API Key 授权机制修复 — 补齐 1.7.0 安全短板 |
| **Failover 加速** | 延迟优化 + Retry Storm Backoff，双重降低故障恢复延迟 |
| **S3 WAL 可靠性** | 批量 Object ID 优化 + NoSuchUploadException 兜底 + 写入前校验 |

**1.7.1 后活跃 PR**：
- S3Stream 跨 bucket multipart copy（#3450/#3452），解锁跨区域 S3 迁移
- Parallelize list offset handling（#3445），加速 failover offset 恢复
- TableTopic Debezium key 派生 identifier（#3449），增强 CDC 集成
- Runtime monitor 新增（#3420/#3438），生产可观测性提升

### 🌊 Apache Fluss — 湖仓集成深化

**本周 PR 动态**（6/26-7/2）：

| PR | 描述 | 方向 |
|----|------|------|
| **#3523** | 支持自定义 Paimon lake table path | 🏛 湖仓集成 |
| **#3537** | KV rebalance 并发度可配置 | ⚙️ 运维 |
| **#3554** | Tiering 逻辑从 Flink 模块解耦，为多引擎支持铺路 | 🔧 架构 |
| **#3463** | RocksDB L0 协同背压机制 | ⚡ 性能 |
| **#3469** | Lake tiering pendingRecordLag 监控指标 | 📊 可观测 |

**持续活跃**：
- **#3393** ✅ DROP COLUMN schema evolution 已合并
- **#3047** ✅ SASL/PLAIN 认证用户管理已合并
- **#3222** 本地 segment TTL 自动清理

**趋势**：Fluss 从「核心功能开发」进入「运维可观测 + 生态连接」阶段。Hudi+Paimon 双湖格式 + Tiering 解耦，流-湖连接器定位愈发清晰。

---

## 🌊 流处理

→ [子调研详情](https://bryantchang1992.github.io/ai_memory_chang_ai_team/tech_research/doris/week_09_2026-07-02.html#flink)

### 🔥 Apache Flink 2.3.0 发布（6/25）

实现 15 个 FLIP 的核心功能，关键增强：

| 特性 | 描述 |
|------|------|
| **FROM_CHANGELOG / TO_CHANGELOG** | append-only ↔ changelog 双向转换 SQL 算子，首次在 SQL 层面将 retract/upsert → append-only |
| **Materialized Table DDL/ALTER** | 显式列定义（含 watermark/PK）、ADD/MODIFY/DROP/RENAME，消除"物化表二等公民"状态 |
| **Adaptive Partition Selection** | 自适应 partition 选择，优化背压处理 |
| **Native S3 FS（Experimental）** | FLIP-555，AWS SDK v2，完全脱离 Hadoop/Presto 依赖 |
| **SinkUpsertMaterializer 重构** | ON CONFLICT（DO NOTHING / DO ERROR / DO DEDUPLICATE）解决无界状态增长 |

Flink 2.1.3 补丁版同周期发布（5 个 bug 修复）。

### 🏠 内部：Fluss 客户端写入流程深度分析

**产出**（a3a59fd ~ 53b4f65, 6/30-7/1）：
- 497 行 Markdown 深度分析：ConnectionFactory → AppendWriter → RpcClient 全链路
- 架构 SVG：3 轮迭代（正交箭头、三列对齐、7 处箭头穿越修复）
- 至此 Fluss 源码分析 8 个模块（01-07 + 05b）**全部完成**

**关键发现**：Connection（重量级全局单例）→ Table（轻量级 per-thread）→ AppendWriter（异步 flush）三层约定明确；MetadataUpdater 后台拉取 schema/bucket/format；WriterClient 管理多 bucket 路由 + 重试/背压。

---

## 🐘 分布式数据库

→ [子调研详情](https://bryantchang1992.github.io/ai_memory_chang_ai_team/tech_research/doris/week_09_2026-07-02.html#distdb)

### CockroachDB vs TiDB 2026 架构对比

多家独立评测机构发布年度对比：CockroachDB 紧耦合多层架构（"像运行一台跨越 DC 的 PostgreSQL"），TiDB 存算分离（SQL + TiKV + TiFlash 三组件）。地理分布式事务 → CRDB 更自然；弹性扩缩 OLTP+OLAP → TiDB 存算分离优势明显。

### CXL 3.0 2026 产品化

CXL 3.0（PCIe 6.0 基础）预计 2026 年产品化，有望改变内存数据库的扩展模式——从 scale-out 分片走向 scale-up 弹性内存池。EDBT 2026 已有论文探讨动态 CXL 内存池分配。

---

## 💾 存储引擎

→ [子调研详情](https://bryantchang1992.github.io/ai_memory_chang_ai_team/tech_research/doris/week_09_2026-07-02.html#storage)

### LSM-tree KV Store 综述（ArXiv 2507.09642）

最新综述论文从 flush/compaction 优化 + 基础操作改进两个维度系统梳理 LSM-tree 研究全景，并覆盖多租户 Serverless 场景。与 SIGMOD 2026 的 LSM Serverless 论文形成呼应。

---

## 🏛 湖仓

→ [子调研详情](https://bryantchang1992.github.io/ai_memory_chang_ai_team/tech_research/data_for_ai/week_09_2026-07-02.html)

### 🔥 Delta Lake 4.3.0 发布（6/18）

本周湖仓方向最大事件：

| 特性 | 描述 |
|------|------|
| **UC Delta REST API** | Spark 原生支持 Unity Catalog Delta API，服务端 commit validation + server-advertised table features。为 Flink/Trino 等多引擎统一访问奠定基础 |
| **replaceOn / replaceUsing** | DataFrame 选择性数据替换 API，细粒度数据修正不再需要全表重写 |
| **UniForm 原子+增量 Iceberg** | Iceberg metadata 与 Delta commit 原子写入，仅增量转换变更日志，大幅降低兼容开销 |
| **Delta Sharing Streaming + CDF** | Trigger.AvailableNow 支持 shared tables，Parquet→Delta streaming 自动转换 |

**4.3.1 补丁**（7/8）：OAuth case-sensitivity 修复、S3A fast listing 兼容、UC metadata 持久化修复。

### 湖仓格式竞争格局 — 2026 Mid-Year

| 格式 | 最新版本 | 周期内关键事件 |
|------|----------|----------------|
| Delta Lake | 4.3.1 (7/8) | UC REST API 集成、replaceOn、UniForm 增量 Iceberg |
| Iceberg | 1.11.0 (5/20) | v3 Spec 生产就绪（删除向量、服务端扫描、表加密） |
| Hudi | 1.2.0 (5/23) / 0.14.2 (6/8) | 1.2 多模态正式版、Hudi 2.0 目标 6 月 |
| Paimon | 持续迭代 | Fluss 深度整合，实时湖仓链路推进 |

**趋势洞察**：Delta UC REST API 标志着 Catalog 战争升级——Databricks 将 Catalog 变成控制平面。UniForm 双向兼容使 Delta 性能 + Iceberg 兼容不再互斥。Hudi 2.0 是关键变量。Fluss+Paimon 的「Kafka→Fluss→Paimon→Flink」全链路可能成为实时湖仓事实标准。

### Fluss + Paimon 实时湖仓推进

Fluss 湖仓集成继续深化：Paimon 自定义路径、Hudi tiering 文档、Tiering 逻辑从 Flink 解耦。LakeStream 在已有湖仓表上启用流式读写的核心能力持续迭代。

---

## 📊 时序 & 分析型数据库

→ [子调研详情](https://bryantchang1992.github.io/ai_memory_chang_ai_team/tech_research/data_for_ai/week_09_2026-07-02.html#doris)

### Apache Doris 4.0.7 发布（7/12）

4.0 系列最新 patch release，4.1 系列（4.1.2 发布于 6/17）持续迭代。4.1.x 的 AI 统一存储能力（HNSW+IVF+IVF_ON_DISK 向量索引、BM25 全文搜索、单行 100MB JSON）吸引社区持续关注。存算分离模式已部署 2000+ 企业。

### 时序数据库趋势

- **InfluxDB 3.x** — Pacha-Tree 存储引擎 Beta 测试推进，LSM-tree + 时间分区混合架构
- **TimescaleDB** — 列存加速 + Hypertable 压缩比持续优化
- **趋势** — 时序 DB 与 OLAP DB 边界模糊化：Doris 时序能力增强 vs InfluxDB SQL 兼容性提升，两者在「时序分析」场景形成正面竞争

---

## 📊 统计

| 方向 | 动态数 | 亮点 |
|------|--------|------|
| AI Infra · Agent 基础设施 | 5 | Hermes Agent 140k⭐、Qwen 3.6、Agent 框架对比 2026、内部图谱修复 |
| Kafka / AutoMQ / Fluss | 12 | Kafka KIP-1314/1320、AutoMQ 1.7.1、Fluss 湖仓集成 + Paimon/Hudi |
| 流处理 | 3 | Flink 2.3.0（FROM_CHANGELOG/TO_CHANGELOG）、Fluss 客户端深度分析 |
| 分布式数据库 | 2 | CockroachDB vs TiDB 2026、CXL 3.0 产品化 |
| 存储引擎 | 1 | LSM-tree KV Store 综述（ArXiv） |
| 湖仓 | 6 | Delta Lake 4.3.0 UC REST API、四大格式竞争格局、Fluss+Paimon |
| 时序 & 分析型 | 3 | Doris 4.0.7、InfluxDB Pacha-Tree、TSDB vs OLAP 融合趋势 |

**合计 32 条动态 | 7 方向全覆盖**

---

> ⚡ **下期预告**：Week 10 关注 Kafka 4.4.0 KIP freeze 结果、Flink 2.3.0 FROM_CHANGELOG 落地、Delta Lake UC REST API 多引擎支持进展、VLDB 2026 论文列表。
>
> 📎 子调研详情详见各方向页面。
