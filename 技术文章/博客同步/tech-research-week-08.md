---
title: 技术调研周报 — Week 08 (2026-06-25)
blog_url: https://bryantchang1992.github.io/ai_memory_chang_ai_team/posts/tech-research/week-08/
blog_source: _posts/2026-06-25-tech-research-week-08.md
blog_source_commit: f83970fa7e6ad32d626cc6ca3ba7428c90a638a5
blog_body_sha256: 52c0531a710e18d2041ffe1ea46db5b1ace266e5e6556c56a819f4e83c5150c4
synced_at: '2026-10-05'
type: survey
created: '2026-06-25'
tags:
- AI Infra
- Agent Harness
- CodeAct
- Hyperlight
- CockroachDB
- Leader Leases
- Flink
- Fluss
- Doris
- Iceberg
- LSM-Tree
- PASV
- 湖仓
- CXL
issue: 8
issue_date: '2026-06-25'
---

> 覆盖周期：2026-06-19 ~ 2026-06-25 | Week 08（补调研）

---

## 🧠 AI Infra · Agent 基础设施

→ [子调研详情](https://bryantchang1992.github.io/ai_memory_chang_ai_team/tech_research/ai_harness/week_08_2026-06-25.html)

本周 AI Infra 领域最大的事件是 **Microsoft BUILD 2026 Agent Framework 三大发布**，另有 Harness Engineering 理论化进展和模型架构演进信号。

### 🔥 Microsoft Agent Framework at BUILD 2026

Microsoft 在 BUILD 2026 上一口气发布了 Agent Harness / Hosted Agents / CodeAct 三大组件，标志着 Agent 基础设施从"拼凑式胶水代码"进入"平台化工程"阶段。

| 组件 | 核心价值 | 状态 |
|------|----------|------|
| **Agent Harness** | 生产级 Agent 运行环境，内建 context compaction、文件内存、TODO 管理、技能发现、子 Agent 调度、OpenTelemetry 追踪、工具审批 | GA（含在 MAF 1.0 中） |
| **Hosted Agents (Foundry)** | 一键部署到 Azure，scale-to-zero、VM 隔离沙箱、持久化 session 状态、自动可观测 | GA |
| **CodeAct + Hyperlight** | 模型写 Python 一次性调用多个工具，在 Hyperlight micro-VM 中沙箱执行，52% 延迟降低 + 64% token 节省 | Alpha |

**CodeAct 的技术深度**是本周最值得关注的。传统 Agent 每次工具调用都是一个独立推理轮次：选工具 → 等结果 → 继续推理，多步任务产生大量串行延迟和 token 消耗。CodeAct 将模式改为：模型用 Python 写一段代码，通过 `call_tool()` 一次性执行多个工具调用，在 Hyperlight 微虚拟机中沙箱运行，返回合并结果。基准测试数据：传统方式 27.81s / 6,890 tokens → CodeAct 13.23s / 2,489 tokens。

**Hyperlight 沙箱的设计值得细看**：基于 Hyperlight micro-VM（用 KVM/macOS Hypervisor.framework 抽象），每次 CodeAct 调用启动一个全新的轻量 VM，执行完毕后销毁，隔离性达到硬件级别但启动时间极短。这是 Agent 安全执行的一大步。

### Harness Engineering 理论化

Faros AI 将其系统化为 AI 工程成熟度三阶段：Prompt Engineering (2022-23) → Context Engineering (2024-25) → Harness Engineering (2026)。核心公式：**Agent = Model + Harness**。

LangChain 团队的实战案例尤为有力：仅通过优化 Agent Harness 层面（不改模型），将编码 Agent 从 Terminal Bench 2.0 第 30 位提升到第 5 位。

Anthropic 研究识别了三个 Harness 级才能解决的模型原生缺陷：Victory Declaration Bias（不验证就标记完成）、Context Anxiety（上下文快满时焦虑加速）、One-shotting Overreach（一次尝试整个任务导致混乱）。

### 模型架构演进信号

Sebastian Raschka 发布的 2026 H1 论文列表揭示了几个趋势：
- **Hybrid Architecture 主流化**：Nemotron 3 Super（Attention + Mamba-2 交替层）、Qwen 3.6（Attention + Gated DeltaNet 交替层）
- **SSM 持续进化**：Mamba-3、Gated DeltaNet-2（解耦 Erase/Write 操作）
- **MoE 容量分配重思考**：Scaling Embeddings Outperforms Scaling Experts 论文挑战传统 MoE 设计
- **Diffusion LLM 兴起**：被列为独立研究方向，值得关注

---

## 🐘 分布式数据库

→ [子调研详情](https://bryantchang1992.github.io/ai_memory_chang_ai_team/tech_research/doris/week_08_2026-06-25.html#distdb)

### 🔥 CockroachDB Leader Leases — SIGMOD 2026

本周分布式数据库方向最重要的技术产出。论文由 Cockroach Labs 团队（Ibrahim Kettaneh、Rebecca Taft 等）在 SIGMOD 2026 发表，解决了一个长期存在的扩展瓶颈。

**问题本质**：CockroachDB 数据被分成数百万个小 Range，每个需要指定一个 leaseholder 来高效服务读请求。历史上有两种方案：
- **Expiration-based Leases**：每个 Range 独立续租，可靠但产生大量 Raft 写入（per-Range 心跳），集群规模大时 CPU 开销巨大
- **Centralized Leases**：所有 lease 依赖单一 Range 的节点健康状态，便宜但引入单点故障

**Leader Leases 方案**：通过三层设计统一两者优势：
1. **Liveness Fabric**：去中心化的节点间健康检查层，替代 per-Range 检查
2. **Leader Fortification**：Raft 协议修改，防止 leader 意外失去领导权，确保 leaseholder 始终是 Raft leader
3. **Leader Leases**：合并 leader + leaseholder 角色，消除冗余协调，缩短故障恢复窗口

**实验效果**：Lease 维护 CPU 降低最高 **85%**，在 Range 数量增长时吞吐稳定，节点崩溃/网络分区/磁盘停滞等故障场景下秒级恢复。Liveness Fabric 安全性经 TLA+ 形式化验证。

A. Jesse Jiryu Davis 的技术解读（emptysqua.re）指出了一个有趣的实际工程细节：Store Liveness 的 heartbeat 本身**需要一次磁盘写入**才能发出——这意味着磁盘停滞的节点无法请求支持，从而被自动踢出。他将 CockroachDB 的演进称为"现实世界系统的英勇修补"。

### CXL 与数据库

CXL（Compute Express Link）内存与数据库系统的交叉研究在 2026 年持续升温：
- **EDBT 2026**：Dynamic Memory Allocation of CXL Memory Pools in Enterprise Databases 论文（openproceedings.org/2026/conf/edbt/paper-280.pdf）探讨 CXL 内存池在事务型数据库中的弹性分配
- **VLDB 2025**：An Examination of CXL Memory Use Cases for In-Memory DBMS 发现 CXL 内存对 OLAP 工作负载吞吐退化 < 8%（PCIe Gen5）
- **清华大学**：CXL-Powered Database System（ICDE 论文），系统化阐述 CXL 数据库的机会与挑战
- 趋势：CXL 3.0（PCIe 6.0 基础）预计 2026 年产品化，有望改变内存数据库的扩展模式——从 scale-out 分片回归 scale-up 弹性内存池

---

## 🌊 流处理

→ [子调研详情](https://bryantchang1992.github.io/ai_memory_chang_ai_team/tech_research/kafka_research/week_08_2026-06-25.html)

### Flink 2.0 生态成型

Apache Flink 2.0 正式发布后，生态组件快速跟进：
- **Flink 2.0.2**（2026-05-11）：34 个 bug 修复和安全补丁，推荐所有用户升级
- **Flink Connector Parent 2.0.0**：所有官方 connector 完成 Flink 2.0 兼容适配
- **Flink Connector AWS 6.0**：Flink 2.0 兼容 + AWS Glue Schema Registry 增强
- **Flink Kubernetes Operator 1.14.0**：Shopify 团队贡献 FlinkBlueGreenDeployment 修复
- **Flink 2.2.0** 已成为最新 stable release（官网状态）

关键 FLIP 进展：
- **FLIP-555**（Accepted）：Flink Native S3 FileSystem，直接用 AWS SDK V2，完全脱离 Hadoop/Presto 依赖
- **FLIP-566**（讨论中）：IMMUTABLE 列约束，对增量处理和 CDC 语义至关重要
- Flink CDC V3.6 即将发布，Fluss 0.9 配合实现生产级 schema evolution

### Fluss 1.0 路线图

Fluss 路线图讨论（GitHub #2684）已明确：
- **Feature Freeze: 2026-06-01**
- **Release: 2026-06-15**
- 核心目标：Enable LakeStream on existing lake table（在已有湖仓表上启用流式读写）

Fluss 已定位为"table-first columnar streaming storage"，通过 union reads 打通 streaming 和 lakehouse 两层。Apache Flink Agents 0.2.0 也已发布（新增 Embedding Models、Vector Stores、MCP Server、异步执行），标志着 Flink 生态向 AI/Agent 领域延伸。

### RisingWave 2.x

RisingWave 2.x 系列已发布至 v2.8.0（2026-03-02），新增跨数据库查询支持。品牌定位已从此前的"流处理数据库"转向"Event Streaming Platform for Agentic AI"，强调 Postgres wire-compatible + Rust 实现的安全性能优势。

---

## 💾 存储引擎

→ [子调研详情](https://bryantchang1992.github.io/ai_memory_chang_ai_team/tech_research/doris/week_08_2026-06-25.html#storage)

### PASV 入选 ACM Transactions on Storage

PASV（Passive Data Persistence Scheme）最初发表于 FAST '22，**2026 年 5 月入选 ACM Transactions on Storage**（DOI: 10.1145/3813114），标志着这项技术获得学术界的最终认可。

**核心问题**：LSM-tree 数据库存在 double-logging 问题——数据既要写 WAL（Write-Ahead Log），又要在 compaction 时写入 SST 文件。两份写操作对应同一份数据，造成 I/O 放大。

**PASV 方案**：完全移除 WAL，利用 SST 文件的构建过程本身作为持久化手段。Compaction 过程中新生成的 SST 文件本身就构成数据的持久化副本，无需单独维护 WAL。

ACM TOS 版本扩展为"Passive and Hybrid Data Persistence Scheme"，增加了 hybrid 模式支持。论文历程：Submitted 2025-09-17 → Revised 2026-01-28 → Accepted 2026-04-16 → Published 2026-05-05。

### SIGMOD 2026 存储引擎相关论文

根据 SIGMOD 2026 accepted papers 列表，存储引擎方向另有：
- **Making LSM-Tree-based Key-Value Store Practical and Efficient for Multi-Tenant Serverless Cloud Databases**：多租户 Serverless 场景下 LSM KV 存储的实用化改进
- **Tree Search using GPUs**：GPU 加速树搜索

---

## ⏱ 时序 & 分析型数据库

→ [子调研详情](https://bryantchang1992.github.io/ai_memory_chang_ai_team/tech_research/doris/week_08_2026-06-25.html)

### 🔥 Apache Doris 4.1：AI 统一存储与检索

2026 年 4 月发布，是 Doris 向 AI 基础设施转型的标志性版本。

**AI & Search 能力全面升级**：

| 能力 | 4.0 状态 | 4.1 增强 |
|------|----------|----------|
| 向量索引类型 | HNSW | HNSW + **IVF + IVF_ON_DISK** |
| 向量规模 | 千万级 | 十亿~万亿级（磁盘索引） |
| 向量量化 | 基础 | INT8/INT4/PQ 三种压缩 |
| 全文搜索 | search() 基础 | **BM25 评分 + ES 兼容语法 + NESTED 搜索** |
| 向量查询性能 | 基线 | **4x 提升**（Ann Index Only Scan） |

**长上下文 AI 存储**：原生支持单行 100MB JSON 文档，覆盖多轮对话、Agent 执行轨迹、RAG 上下文等场景，不需要外部对象存储。

**OLAP 性能**：TPC-H +22.6%、TPC-DS +19.1%、SSB +14.3%，ClickBench 冷查询排名第一。

**湖仓集成**：完整 Apache Iceberg V2/V3 读写支持 + Apache Paimon DDL 管理。

**Adoption**：存算分离模式已部署 2000+ 家企业。

### Doris 2026 Roadmap

GitHub Issue #60036 明确的 2026 路线图：
- UNNEST 功能、递归 CTE、ASOF JOIN
- AI & Hybrid Search 持续深耕
- 查询性能、存储效率、数据湖集成优化
- 社区已进入 4.x 快速迭代周期

---

## 🏛 湖仓

→ [子调研详情](https://bryantchang1992.github.io/ai_memory_chang_ai_team/tech_research/data_for_ai/week_08_2026-06-25.html)

### 🔥 Iceberg v3 Public Preview on Databricks

2026 年 4 月 9 日 Databricks 发布 Iceberg v3 Public Preview，开放表格式进入新纪元。

**三大核心特性**：

1. **Row Lineage**：每行携带永久 row ID + 序列号，可精确识别变更行，告别全表扫描和外部 CDC
2. **Deletion Vectors**：逻辑删除无需重写整个 Parquet 文件，数据操作性能最高 **10x 提升**
3. **VARIANT 类型**：原生半结构化数据列类型，无需 flatten 或外部存储，与关系列共处一表

**Interoperability 里程碑**：Delta Lake UniForm 使 Delta 和 Iceberg 正式互通——写 Delta、读 Iceberg。Iceberg v3 原生采纳 Deletion Vectors、Row Lineage、VARIANT，消除了 Delta 性能和 Iceberg 兼容之间的历史 trade-off。

Geodis、Panther 等企业已在实际生产中使用 Iceberg v3。Panther 利用 VARIANT 实现百万级安全日志的接入和分析。

### 湖仓格式竞争格局

2026 年四大格式的差异化逐渐清晰：

| 格式 | 生态绑定 | 差异化 |
|------|----------|--------|
| Iceberg | 最广泛的引擎支持 | v3 打破性能-兼容 trade-off，Databricks + Snowflake 双引擎 |
| Delta Lake | Spark/Databricks 生态 | UniForm 实现 Iceberg 兼容，Lakehouse 一体化 |
| Hudi | Uber/AWS 生态 | 1.2 多模态，2.0 目标 2026 年 6 月 |
| Paimon | Flink/阿里 生态 | Fluss 配合实现实时 Lakehouse，流批一体 |

### Fluss + Paimon 实时湖仓

Fluss（已进入 Apache 孵化器）定位为"real-time data layer on top of Lakehouse"，与 Apache Paimon 深度整合，通过 LakeStream 功能在现有湖仓表上直接启用流式读写。这一架构打通了"Kafka → Fluss → Paimon → Flink 查询"的实时链路，是阿里巴巴流批一体战略的核心拼图。

---

## 📊 统计

| 方向 | 动态数 | 亮点 |
|------|--------|------|
| AI Infra · Agent 基础设施 | 8 | Microsoft Agent Harness/CodeAct/Hosted Agents、Harness Engineering 理论化 |
| 分布式数据库 | 4 | CockroachDB Leader Leases (SIGMOD)、CXL 数据库研究 |
| 流处理 | 7 | Flink 2.0.2/2.2.0、Fluss 1.0 路线图、RisingWave 2.x |
| 存储引擎 | 3 | PASV 入 ACM TOS、LSM Serverless、GPU Tree Search |
| 时序 & 分析型 | 5 | Doris 4.1 (AI 统一存储)、Doris Roadmap 2026 |
| 湖仓 | 5 | Iceberg v3、Delta UniForm 互通、Fluss + Paimon 实时湖仓 |

**合计 32 条动态 | 6 方向全覆盖**

---

> ⚡ **下期预告**：Week 09 按常规节奏进行调研（非补调研），重点关注 Fluss 1.0 发布结果、ACM TOS PASV 论文精读、以及即将举行的 VLDB 2026 论文 list。
>
> 📎 子调研详情详见各方向页面。
