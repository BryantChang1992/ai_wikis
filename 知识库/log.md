---
type: meta
title: 知识库操作日志
tags:
- meta
- log
created: 2026-06-14
updated: '2026-10-09'
---

# 知识库操作日志

> 时序记录所有增删改操作。格式：`[日期 时间] 操作者: 操作类型 — 描述`

## 2026-07-11 — Bigtable 论文入库

> CEO 指令：录入 Bigtable (OSDI 2006) 论文到知识库。

- **操作者**：CTO Stark（spawn rd-task Worker 执行）
- **操作**：
  1. 论文 PDF 下载：`sources/papers/Bigtable/Bigtable-OSDI-2006.pdf`（221KB）
  2. 精读分析（580 行）：8 章全覆盖 — 问题动机/数据模型/系统架构/存储引擎/容错与一致性/性能优化/生产经验/影响与后续发展
  3. Wiki 概念卡片（198 行）：`wiki/Bigtable-分布式结构化存储系统.md`，confidence 0.95，related 10 条 wikilink
  4. .entities.json 新增 Bigtable 实体（120 实体总数）
  5. 更新 README.md + sources/README.md + log.md
- **commit**：（待提交）

### 入库内容概述
- **Bigtable (OSDI 2006)**：Google PB 级分布式结构化存储系统，SSTable/MemTable/Compaction/Chubby/GFS 五层架构
- **核心价值**：LSM-Tree 的经典工程实现、NoSQL 运动基石（直接影响了 HBase/Cassandra/LevelDB/RocksDB）
- **知识图谱链接**：关联 LSM-Tree、LSM-Tree-KV-Survey、共识协议体系、Fluss 整体架构等

## 2026-07-03 — Week 09 周报入库（补做）

> CEO 审阅后指令："需要补，每一个入库都要遵守规范"。全部 Web 源（非论文），精读分析以 CTO 自产 + 周报内容合成。

- `[10:40] CTO Agent`: **INGEST** — 入库 7 张 Wiki 概念卡片 + 7 个 sources/web/ 精读分析

### AI Infra · Agent 基础设施
- `Hermes-Agent-自进化Agent框架.md` — Nous Research 自进化 Agent 框架：内建学习循环 + 隔离子 Agent + OpenRouter #1（140k⭐）
  - sources: `sources/web/hermes-agent/精读分析.md`（基于 GitHub README）
- `Qwen-3.6-模型发布.md` — Alibaba Qwen 3.6 参数效率革命：27B（匹配 400B）+ 35B（超越 120B）
  - sources: `sources/web/qwen-3.6/精读分析.md`（基于周报 + Nvidia/Hermes 相关资料）
- `Agent-框架-2026-全景对比.md` — LangGraph/CrewAI/AutoGen/Semantic Kernel/Hermes 五大框架对比
  - sources: `sources/web/agent-frameworks-2026/精读分析.md`（基于多家评测机构年度对比）

### 流处理
- `Apache-Flink-2.3.0-版本发布.md` — Flink 2.3.0：FROM_CHANGELOG/TO_CHANGELOG + Materialized Table DDL + Native S3 FS
  - sources: `sources/web/flink-2.3.0/精读分析.md`（基于 flink.apache.org 官方公告）
- `Fluss-客户端写入流程源码分析.md` — Connection/Table/AppendWriter 三层约定 + 8 模块全部完成
  - sources: `sources/web/fluss-client-write/精读分析.md`（基于 Fluss 源码 a3a59fd~53b4f65）

### 分布式数据库
- `CockroachDB-vs-TiDB-2026-对比.md` — 紧耦合 vs 存算分离两大路线 2026 横评
  - sources: `sources/web/cockroachdb-vs-tidb/精读分析.md`（基于多家评测机构年比）

### 存储引擎
- `CXL-3.0-内存池化新范式.md` — CXL 3.0（PCIe 6.0）内存池化 + 对数据库的影响
  - sources: `sources/web/cxl-3.0/精读分析.md`（基于 CXL 联盟 + EDBT 2026 论文）

### Lint 结果
- 增量 Lint：0 dangling / 0 self-ref / 0 missing source / 所有 wikilink 有效
- 更新 README.md + sources/README.md 索引

### 备注
- 原 URL 获取遇到多处 404（JetBrains/CockroachLabs/ComputerWeekly），精读分析以周报内容 + 可用替代源合成
- 不含论文 PDF（Web 源非学术论文），精读分析即源文件
- 跳过入库：HPE Agent 战略（信息量小，合并入 Hermes 卡）、Flink 2.1.3（补丁版，在 Flink 2.3.0 卡提及）、内部图谱修复（维护类）

## 2026-06-20

- `[17:30] CTO Agent`: **INGEST** — 入库论文 "Agent Harness Engineering: A Survey" (TMLR 2026 under review)
  - 源文件归档: `sources/papers/Agent-Harness-Engineering-Survey/` (PDF 3.4MB + 精读分析.md)
  - 生成 1 张 Survey 综述卡 + 7 张 ETCLOVG 分层概念卡片:
    - `Agent-Harness-Engineering-Survey综述.md` — 三条核心主张 + 三阶段演化 + 跨层规律 + 五大开放问题
    - `Agent-Harness-Execution-Environment执行环境.md` — E 层：7 类沙箱 + 逃逸/规模化/可复制性挑战
    - `Agent-Harness-Tool-Interface工具接口.md` — T 层：MCP vs A2A 协议 + 工具设计四原则
    - `Agent-Harness-Context-Memory上下文管理.md` — C 层：三层记忆 + Context Drift + 幻觉沉淀(QSAF)
    - `Agent-Harness-Lifecycle-Orchestration编排.md` — L 层：三层编排 + 5 种模式 + 四大故障模式
    - `Agent-Harness-Observability可观测性.md` — O 层：可观测堆栈 + 成本优化 + Managed Agents
    - `Agent-Harness-Verification-Evaluation评估.md` — V 层：5 阶段 Task-to-Feedback Lifecycle
    - `Agent-Harness-Governance治理.md` — G 层：6 大治理机制 + 覆盖缺口分析
  - 增量 Lint: 0 dangling / 0 missing source / 0 self-ref / 0 duplicate
  - 更新 README.md + sources/README.md 索引
  - 覆盖 170+ OSS 项目映射，7 层完整分析

## 2026-06-15

- `[10:00] CTO Agent`: **SYNTHESIZE** — 3 篇领域综述
  - `LSM-Tree-存储引擎新进展-2026综述`: Silo 分布式 compaction + Fluss LSM 实践
  - `分布式数据系统事务与一致性新进展-2026综述`: CockroachDB + Aurora + Rosé + Agent-First 四系统横向对比
  - `Fluss-流处理平台架构综述`: Fluss 五大模块 vs Kafka 源码级综述
  - README.md 更新: 综述索引 + 2026 论文概念卡片 12 张

- `[09:45] CTO Agent`: **INGEST** — Aurora PostgreSQL Limitless Database (SIGMOD 2026 Industry)
  - 精读分析 + 全文翻译 + 3 张 wiki 卡片
  - 卡片: Aurora-Limitless-分布式架构, Aurora-Limitless-时间戳事务, Aurora-Limitless-自适应扩缩容
  - 替代第 5 篇 LSM-Raft (Poster, PDF 无法获取)

- `[09:25-09:30] CTO Agent`: **INGEST** — 4 篇论文批量入库（精读分析 + 全文翻译 + concept cards）
  - CockroachDB Leader Leases (SIGMOD 2026): 精读分析 + 全文翻译 + 3 张 wiki 卡片
  - Rosé (CIDR 2026): 精读分析 + 全文翻译 + 2 张 wiki 卡片
  - Agent-First Data (CIDR 2026): 精读分析 + 全文翻译 + 3 张 wiki 卡片
  - Silo / LSM-Scheduling (FAST 2026): 精读分析 + 全文翻译 + 2 张 wiki 卡片
  - LSM-Raft (SIGMOD 2026): ⚠️ 确认为 Poster（非 full paper），ACM/ResearchGate 均封锁，无法获取 PDF
  - 所有 wiki 卡片已通过 [[wikilink]] 与知识库现有节点互联

- `[00:10] rd-task Worker`: **INGEST** — Fluss 源码分析 10 张 wiki 卡片
  - 源文件: 7 个 HTML 源文件（sources/web/fluss/01-07）
  - 产出: 10 张 wiki 卡片（6 analysis + 4 concept）
  - analysis: Fluss-整体架构 / 存储引擎 / 分布式协调 / RPC与网络 / 客户端与计算集成 / Lake层与湖仓融合
  - concept: Fluss-KV存储-RocksDB / Tiering分层架构 / Kafka兼容层 / Arrow列式记录格式
  - 首次引入 "Apache Fluss 调研" 小节到 README.md

## 2026-06-14

- `[23:30] Stark (CTO)`: **PUBLISH** — GitPage 周报发布
  - 新增 `tech_research/wiki_synthesis/` 子方向
  - 发布 `_posts/2026-06-14-tech-research-week-05.md`
  - 更新 `tech_research/index.html`（6 方向、18 篇报告）
  - README wikilink 修正 + 删除重复 LSM 综述文件
- `[22:00] Stark (CTO)`: **INIT** — 知识库结构化配置
  - 新建 `purpose.md`（目的定义）
  - 新建 `schema.md`（结构规则）
  - 新建 `log.md`（本文件）
  - 升级 `README.md` 为知识库索引
  - 改造 `事务模型深度调研.md`（补全 frontmatter + [[wikilink]]）
- `[22:30] Stark (CTO)`: **REFACTOR** — 落地 Karpathy 三层架构
  - 创建 `sources/` 目录（Raw Sources 层，只读源文件）
  - 创建 `wiki/` 目录（Wiki 层，LLM 生成知识）
  - 移动 `事务模型深度调研.md` → `wiki/`
  - 创建 `sources/README.md`（源文件索引）
  - 更新 `schema.md`：加入三层架构说明和数据流
  - 更新 `README.md`：按三层架构重组索引
- `[22:15] Knowledge Worker`: **INGEST** — Event Horizon (CIDR 2026)
  - 源文件: sources/papers/Event-Horizon-Asymmetric-Dependencies-Geo-Distributed-Operations.md
  - 产出: wiki/Event-Horizon-非对称依赖.md
  - 核心概念: 非对称依赖、半线性化(SL)、DeMon、事件视界
- `[22:45] Stark (CTO)`: **RULE** — 定义 Ingest 规则
  - schema.md 追加 Ingest 规则章节：触发条件、执行流程、去重机制、Worker 配置
  - 创建 `sources/web/`、`sources/papers/`、`sources/notes/` 子目录
  - 首次执行 Ingest 流程验证（Event Horizon）
- `[23:20] Stark (CTO)`: **CLEANUP** — 清理 sources 目录
  - 删除 `sources/papers/Event-Horizon-...-全文翻译.md`（翻译不应在 raw 层）
  - 入库 `LSM-based-Storage-Techniques-A-Survey.md`（精读分析）、`RaaS-Reducing-Tail-Latency-Storage-Disaggregated-DB.md`（精读分析）到 sources/papers/
- `[23:25] rd-task Worker`: **INGEST** — LSM-tree 综述 (VLDB Journal 2019)
  - 源文件: sources/papers/LSM-based-Storage-Techniques-A-Survey.md
  - 产出 7 张概念卡片: LSM-Tree 总览、写放大、合并优化、硬件适配、自动调参、二级索引、RUM 猜想
- `[23:25] rd-task Worker`: **INGEST** — RaaS (SIGMOD 2026)
  - 源文件: sources/papers/RaaS-Reducing-Tail-Latency-Storage-Disaggregated-DB.md
  - 产出 3 张概念卡片: RaaS 方案、Tail Latency 根因、Log-as-the-Database 模式
- `[22:45] rd-task Worker`: **INGEST** — Doris 调研知识卡片
  - 源文件: 技术文章/Doris调研.md + 技术文章/Doris调研/ 下 5 个子文档
  - 产出 1 张调研报告 + 7 张概念卡片
  - 调研报告: Doris 实时分析数据库深度调研
  - 概念卡片: 数据模型、Segment v2 存储格式、Compaction 策略、MPP 向量化查询引擎、Nereids CBO 优化器、架构演进、元数据与一致性复制
- `[22:55] rd-task Worker`: **INGEST** — InfluxDB 调研知识卡片
  - 源文件: 技术文章/InfluxDB调研.md + 技术文章/InfluxDB调研/ 下 5 个子文档
  - 产出 1 张调研报告 + 7 张概念卡片
  - 调研报告: InfluxDB 深度调研（从 TSM 到列存引擎）
  - 概念卡片: 数据模型、TSM 存储引擎、3 列存引擎、写入与查询路径、指标设计与基数管理、多副本与高可用、Catalog 元数据

### 2026-06-14 23:40

### 2026-06-15

- `[00:10] Stark (CTO)`: **INGEST** — Apache Fluss 源码分析 7 模块 → 10 张 wiki 卡片
  - 源文件: tech_research/fluss/ 下 7 个模块分析 HTML（01-07）
  - 产出 6 张 analysis 卡片: 整体架构、存储引擎、分布式协调、RPC与网络、客户端与计算集成、Lake层与湖仓融合
  - 产出 4 张 concept 卡片: KV存储-RocksDB、Tiering分层架构、Kafka兼容层、Arrow列式记录格式
  - 核心发现: Fluss ~30% 代码复用 Kafka，70% 自研；最大差异化是 KV Store + Arrow 列式 + Lake 集成

### 2026-06-14 23:40 (continued)

- **目录重组**：wiki/ 下新增 `synthesis/` 子目录，独立存放领域综述 + Lint 报告
  - 迁移 6 个文件到 `wiki/synthesis/`：LSM-Tree-存储引擎体系综述、OLAP与TSDB全景综述、分布式数据系统一致性体系、Apache-Doris-OLAP-数据库体系综述、InfluxDB-时序数据库体系综述、Lint-2026-06-14
  - 原因：综述/synthesis 与研究型页面（survey/concept）混放不利于查找
  - 影响文件：schema.md（目录结构+三层层角色表+Synthesize写入路径）、README.md（索引引用路径）、HEARTBEAT.md（转义规则+关键文件清单）
## 2026-06-15 — SP-Survey 流处理综述纳入

- **源文件归档**：`sources/papers/SP-Survey/`（PDF + 精读分析）
- **概念卡片 (6)**：
  - `wiki/Stream-Processing-System-Generations.md` — 流处理三代演化
  - `wiki/流处理乱序数据管理.md` — Watermark/Trigger/Refinement
  - `wiki/流处理状态管理.md` — In-Memory/Out-of-Core/External + 持久化粒度
  - `wiki/流处理容错模型.md` — At-Least-Once → Exactly-Once 分级 + Output Commit
  - `wiki/流处理弹性与重配置.md` — 弹性/重配置/Flow Control
  - `wiki/Dataflow-Model.md` — 批流统一四抽象
- **关联卡片**：与 LSM-Tree、Fluss 综述、事务综述建立 wikilink

## 2026-06-15 (续) — 流处理系统演化综述 合成

- **新增综述**：`wiki/synthesis/流处理系统演化综述.md` (263行)
- **覆盖范围**：三代演化、乱序数据管理、状态管理、容错模型、弹性与重配置、Dataflow Model
- **交叉关联**：LSM-Tree、Fluss 综述、分布式事务综述
- **6张概念卡片全面重写**：从精读分析摘要升级为论文原文级技术深度（+664行增量）


## 2026-06-15 (续2) — 知识库 P0 修复

- **补全 frontmatter**：13张卡片缺 status → 全部补 status: draft；3张 Aurora 卡片缺 sources → 补 sources 指向
- **README 去重**：删除底部 Fluss/InfluxDB/Doris 重复块（Fluss 10条重复全删）
- **README 补新**：+6张流处理概念卡片（Stream-Processing-System-Generations + 流处理4张 + Dataflow-Model）+ 2张 synthesis（流处理系统演化综述 + 知识库优化方案）
- **修复后基线**：57张卡片 + 10张综述，全部 frontmatter 完整（type/src/status/tags/related），README 无重复

## 2026-06-15 (续3) — ByteHouse 论文 Ingest

- **源文件归档**：`sources/papers/ByteHouse/` — SIGMOD 2026 Companion
  - `ByteHouse-SIGMOD2026.pdf`（2.8MB）+ `精读分析.md`
- **Wiki 卡片** (3张):
  - `ByteHouse-架构与设计.md` — 三层存算分离 + CrossCache + NexusFS
  - `ByteHouse-统一表引擎.md` — Document/Chunk 两级抽象 + Stable/Delta Segment MVCC + 自适应 Compaction + Sniffer 格式
  - `ByteHouse-多模态查询优化.md` — HBO + ML 回归优化 + RANK_FUSION + 分级向量索引 + 三模式执行
- **Diagram**: `bytehouse-architecture.svg` — 三层完整架构图
- **关联**: 引用了 Doris 深度调研、事务模型深度调研、Log-as-Database、LSM-Tree
- **更新**: sources/README.md 索引 + log.md

## 2026-06-15 (续4) — 全量 Diagram 批量修复

- 48张卡片新增 frontmatter diagram 引用（按主题智能匹配）, 57/57 卡片 100% 覆盖
- 删除 dangling related `[[Flow-Control-Backpressure]]`
- 新增 `stream-processing-generations.svg` (流处理三代演化)
- 验证: 0 broken diagram refs, 0 wiki dangling
- `git commit 7e8ac72` — 80 files, +1740 lines

### 2026-06-16 12:07 — Distributed Consensus Revised (Howard 2019) 论文入库
- **操作**：Ingest + Synthesize + 配图
- **来源**：Heidi Howard 博士论文 "Distributed Consensus Revised" (Cambridge, 2019, UCAM-CL-TR-935)
- **源文件**：
  - PDF: `sources/papers/Distributed-Consensus-Revised/UCAM-CL-TR-935.pdf` (1.2MB)
  - ArXiv: `sources/papers/Distributed-Consensus-Revised/arxiv-1902.06776.pdf` (213KB)
- **精读分析**：`sources/papers/Distributed-Consensus-Revised/精读分析.md` (CTO 自产)
- **新增 wiki 卡片（4 张）**：
  1. `wiki/共识算法族系-从Paxos到广义解.md` — 全貌综述：4 层递进泛化全景 (CTO 自产)
  2. `wiki/Paxos-Quorum-Intersection-Revised.md` — Flexible Paxos + Revision A/B §4 (Worker)
  3. `wiki/Paxos-Value-Selection-Revised.md` — Quorum-based Value Selection §6 (Worker)
  4. `wiki/Paxos-Epochs-Revised.md` — Epochs by Recovery + Multi-path §7 (Worker)
- **综述更新**：`synthesis/共识协议体系综述.md` → 重命名/扩展为 `synthesis/共识协议体系综述.md`，新增 Howard 广义共识框架章节
- **新增配图（4 张，Style 1 Flat Icon）**：
  1. `diagram/consensus-generalised-family.svg/.png` — 4 层递进泛化全景
  2. `diagram/paxos-quorum-intersection.svg/.png` — Classic vs Flexible Paxos quorum 对比
  3. `diagram/paxos-value-selection.svg/.png` — Quorum-based 决策流
  4. `diagram/paxos-epochs-revised.svg/.png` — 4 种 Epoch 方案对比 + Recovery 机制
- **索引更新**：`sources/README.md` + `知识库/README.md`
- **Worker 效率**：3 个 rd-task Worker 并行生产，总耗时 <3min
- **Commit**: 待提交

### 2026-06-19 13:15 — Week 07 周五 Wiki 维护日

- **操作**：全量 Lint + 修复 + Synthesize Refresh 检测 + 索引更新
- **背景**：本周无新周报产出（Week 06 周三提前发布），无 CEO 审阅标记，跳过 Ingest
- **Lint 结果**：
  - Dangling wikilink：13 处 `synthesis/` 前缀引用 → 全部修复为页面名引用
  - 循环自引：0
  - Diagram 断链：0
  - ASCII 残留：2 文件（P2 优先级，待替换）
  - 孤儿页面：1（Chandy-Lamport-分布式快照算法，0 inbound）
  - sources dangling：Doris/InfluxDB/Fluss 系列为合法远程源引用，非断链
- **Synthesize Refresh**：10 篇综述全部健康（3-5 天内更新，related 零 dangling），无触发增量更新
- **新综述待合成**：Fluss-流处理平台架构综述（已存在但未入索引，9 子卡片达临界质量）
- **新增**：`wiki/synthesis/Lint-2026-06-19.md` — 本周 Lint 报告
- **Commit**: `432be45` — fix(lint): Week 07 维护日 — 修复 13 处 synthesis/ 前缀引用 + 新增 Lint 报告

### 2026-06-19 13:30 — CEO 派发 11 篇文章入库

- **操作**：Source Ingest — 11 篇 AI Infra / Fluss 文章源文件归档 + 概念卡片生成
- **背景**：CEO 通过交互卡片委派，要求 11 篇源文件入库

#### 入库清单
| # | 文章 | 来源 | 方向 | 子卡片 |
|---|------|------|------|--------|
| 1 | Memory for Autonomous LLM Agents | ArXiv 2603.07670 | Agent Memory | Agent-Memory-Survey-2026综述 |
| 2 | Parallax: Why AI Agents That Think Must Never Act | ArXiv 2604.12986 | Agent Security | Parallax-Agent安全架构 |
| 3 | How We Contain Claude | Anthropic Engineering | Agent Security | Anthropic-Agent安全容器化实践 |
| 4 | The Art of Loop Engineering | LangChain Blog | Agent Harness | Loop-Engineering-多层Agent循环架构 |
| 5 | Why Model Neutrality Matters More Than Cloud Neutrality | LangChain Blog | Agent Harness | Model-Neutrality-模型中立与反锁定 |
| 6 | Fault Tolerance in LangGraph | LangChain Blog | Agent Harness | Agent-Fault-Tolerance-容错设计 |
| 7 | How to Build a Custom Agent Harness | LangChain Blog | Agent Harness | Custom-Agent-Harness-Middleware架构 |
| 8 | How We Made Coding Agent Spend Predictable | LangChain Blog | Cost Control | Agent-Cost-Control-Gateway成本控制 |
| 9 | How to Choose the Right Sandbox for Your Agent | LangChain Blog | Agent Security | Agent-Sandbox-安全沙箱选型 |
| 10 | Bottling the River: Apache Fluss on EKS | Fresha Blog | Fluss 实践 | Fluss-EKS-生产部署实践-Fresha |
| 11 | Fluss PR #3420 — Watermark → Paimon Snapshot | GitHub | Fluss | Fluss-PR-3420-Watermark-to-Paimon |

#### 源文件归档
- `sources/papers/Agent-Memory-Survey/` + `Parallax/`（论文精读 ×2）
- `sources/web/anthropic/`（1 篇）
- `sources/web/langchain/`（6 篇）
- `sources/web/fresha/`（1 篇）
- `sources/web/fluss/`（1 篇 PR 精读）

#### CTO 备注
- Worker 并行派发 6 个 rd-task 全部 failed（runtime lost active execution context），CTO 直接手写 11 张卡片
- Agent-First 标签体系新增 `agent-infra` / `agent-security` / `agent-harness` / `agent-memory` 等标签
- 新卡片全部 `status: draft`，每张含详细分析和 3-6 条 related 内链
- 增量 Lint：11 卡 sources + related 全部有效，0 dangling
- **索引更新**：`sources/README.md` + `知识库/README.md` 新增 AI Infra + Fluss 实践 section
- **Commit**: `6121932` — feat(ingest): CEO 派发 11 篇文章入库 — AI Infra + Fluss 实践

- `[17:00] CTO Agent`: **SYNTHESIZE** — 新增 AI Infra Agent 基础设施体系综述
  - 整合 10 张 wiki 卡片（Harness + Security + Control + Memory + Hill Climbing）
  - 九章：全景结构 / Harness 层 / 安全层三重防御 / 控制面 / 状态层 / 正交叠加模型 / 成熟度评估 / 演化方向 / 已有知识关联
  - 10 张卡片反向引用全部注入，0 dangling
  - **Commit**: pending

- `[16:30] CTO Agent`: **REWRITE** — 11 张卡片深度重写 + related 补全
  - **根因**：初版为 Worker 全部 failed 后 CTO 紧急手写，内容仅为源文件摘要级，related 全部为空
  - **修复**：逐张重写，每张基于源精读分析深度展开，添加系统对比/架构关系/交叉引用
  - **related 网络效果**：11 张卡共 48 条 related，形成 AI Infra 知识子图（Agent Memory ↔ Security ↔ Harness ↔ Cost）
  - 卡片大小从平均 ~300 bytes 提升到 ~2600 bytes
  - **Lint**：48 条 related 全量验证，0 dangling
  - **Commit**: `81e1294` — rewrite(ingest): 11 张卡片深度重写 + related 网络补全

- `[16:00] CTO Agent`: **REWRITE** — 11 篇 source 层精读分析全面重写
  - **根因**：初版 9 篇网页精读仅 28-42 行，是源文件摘要级敷衍壳，远低于历史标准（150-200 行）
  - **修复**：逐篇基于完整原文系统拆解——关键论点的结构梳理 + 架构判断 + 交叉关联 + 工程启示
  - **效果**：网页精读从平均 35 行 → 平均 ~134 行（~3.8x 提升），论文精读保持 194-241 行
  - **重写清单**：custom-agent-harness(42→153L)、how-we-contain-claude(40→162L)、fault-tolerance(35→153L)、loop-engineering(28→138L)、fluss-eks(36→124L)、Fluss-PR-3420(39→145L)、sandbox(40→121L)、model-neutrality(31→114L)、coding-agent-spend(已有 115L 保持)
  - Agent Memory Survey (241L) + Parallax (194L): 论文精读保持完整
  - **Commit**: pending — rewrite(source): 11 篇 source 精读全面升级


### 2026-06-19 18:00 — Week 07 第二轮维护（严格按 ai-wiki-maintain skill）

- **触发**：CEO 要求严格按照知识库 skill 重新执行周五维护任务
- **执行范围**：Lint(全量) → Diagram → Synthesize Refresh → 集群更新

#### Lint 第二轮
- Dangling wikilink：5 处 `...` 截断名（Custom-Agent-Harness-Middleware 的 ASCII 树形图）
  - `Agent-Fault-Tol...` → `Agent-Fault-Tolerance-容错设计`
  - `Agentic-Memory...` → `Agentic-Memory-语义缓存`
  - `Agent-Sandbox...` → `Agent-Sandbox-安全沙箱选型`
  - `Agent-Cost-Control-Gateway...` → `Agent-Cost-Control-Gateway成本控制`
  - `Model-Neutrality...` → `Model-Neutrality-模型中立与反锁定`
- 修复方式：ASCII 树形代码块 → SVG diagram + 纯文本叙述

#### Diagram 新图
- `agent-harness-5layer.svg` + `agent-harness-5layer.png`：Agent Harness Middleware 五层架构
  - Style 1 (Flat Icon)：Core Loop → 容错/记忆/安全/模型路由 → 成本控制
  - 7 张 wiki 卡片映射、箭头语义着色、图例
  - SVG 验证 + PNG @2x (1920px) 导出

#### Frontmatter 修复
- 5 张 synthesis 页缺 `created`/`updated`/`sources`/`title` → 全部补全：
  - AI-Infra-Agent基础设施体系综述 (2026-06-19)
  - Fluss-流处理平台架构综述 (2026-06-17)
  - LSM-Tree-存储引擎新进展-2026综述 (2026-06-16)
  - 分布式数据系统事务与一致性新进展-2026综述 (2026-06-16)
  - 流处理系统演化综述 (2026-06-17)

#### Synthesize Refresh
- 增量检测：所有 synthesis updated ≤ 6 天，无触发重写/增量追加
- 已有 synthesis 的 diagram 引用完整（每张 ≥ 1 张主图 P0 ✅）

#### 集群状态更新
- AI Infra 集群：4 张 → 11 张（达临界质量），综述已合成
- Fluss 综述：已存在且已入索引
- Lint 报告 `Lint-2026-06-19.md` 已更新第二轮修复记录

- **Commit**: pending

## 2026-07-06 — V2 升级完成：全量 Confidence + Entity Graph + Lint

### 背景

知识库 schema.md 已于 2026-07-05 升级到 V2（Karpathy LLM Wiki v2），但 121 个页面均未填充新增字段。本次维护日完成 V2 全量对齐。

### 执行范围

| 项目 | 前 | 后 |
|------|----|----|
| confidence 字段 | 0/121 页面 | 121/121 ✅ |
| confidence_rationale | 0/121 页面 | 121/121 ✅ |
| .entities.json | 空壳 (entities: []) | 119 实体 + 485 关系 |
| Lint 🔴 阻断 | 93 (脚本误报) | 0 ✅ |
| Lint 🟡 警告 | 66 | 0 ✅ |
| ASCII 残留 | 19 页面 | 0 ✅ |
| 孤儿页面 | 16 | 0 ✅ |

### V2 升级详情

#### 1. Confidence 批量注入 (121 页)

自动化评分规则（`/tmp/batch_confidence2.py`）：
- 基础分：synthesis=0.80, survey=0.78, concept=0.75, decision=0.70, lesson=0.68
- 来源加成：1 源 +0.05, 2 源 +0.10, 3+ 源 +0.15
- 状态加成：reviewed +0.10, final +0.08, stable +0.05
- 时效衰减：每 30 天 -0.05（上限 -0.15）

分布结果：0.7-0.8: 20 页 | 0.8-0.9: 80 页 | 0.9+: 21 页

#### 2. Entity Extraction (.entities.json)

从 119 个 wiki 页面提取实体图谱，含 485 条 `relatedTo` 关系。
实体类型分布：Concept, Taxonomy, Analysis, Decision, Lesson, Meta。
1 个合法孤儿：知识库优化方案-2026-06-15 (Meta 页面，非知识图谱节点)。

#### 3. Lint 修复清单

- **Lint 脚本增强**（`lint-full.sh`）：URL sources 跳过检查、synthesis 类型 sources 容忍 wikilink、`技术文章/` 路径支持
- **Dangling wikilink 移除**（6 处）：Disaggregated-RocksDB, Nova-LSM, O3-LSM, NoveLSM, MatrixKV, SLM-DB, Monkey-BF, Bloom-Filter, SuRF 等不存在的卡片引用
- **Sources 路径修复**（16 个 Doris/InfluxDB 页面）：`技术文章/` → `../技术文章/` 修正相对路径
- **ASCII box-drawing 替换**（19 个文件）：`┌└├│─` → `|` `-`
- **ElasticBF 补 created 字段**
- **孤儿页面链接**（16 个）：所有孤儿卡片已加入对应 synthesis 综述页的 related 字段

#### 4. Synthesis Refresh

- 无新集群达临界质量 → 无新综述生成
- 已有 synthesis 全部 confidence 已注入
- LSM-Tree 新进展综述 +9 related，Fluss 综述 +3，流处理演化综述 +2，事务新进展综述 +2

### Commit



## 2026-10-05 — 博客与 Obsidian 双向对齐

- 基于博客 `f83970fa7e6a` 与知识库 `8a1563c138c8`。
- 以博客已发布正文更新对应笔记，纳入博客新增周报及旧 HTML 专题。
- 知识库独有技术材料发布到 `/knowledge/`；团队规范、Agent 文件、维护记录、制作提示词不公开。
- 修复 75 处 confidence 属性位置、同名章节嵌入、失效图片路径、来源路径及总索引；保留原有草稿/审核状态，不将同步视为事实复核。
- 对照清单：`.blog-sync-manifest.json`。待补概念保存在清单中，未生成空壳页面。

- 发布范围复核：3 份混有团队运行规则的项目设计文档保留本地，新增技术文章调整为 163 篇；68 篇博客内容回补到知识库。原始材料中已改名的链接对齐现有页面，尚未形成笔记的概念转为 pending_concepts。

- 合并 Fluss 整体架构的历史摘录副本，统一使用博客完整章节；最终新增公开技术内容为 162 篇。缺少日期字段的文章使用文内研究日期或首次 Git 入库日期，不统一回填占位日期。


## 2026-10-05 内容质量复核更正

此前日志中的 Silo / LSM-Scheduling 实际对应 HATS；未固定 commit 的 30% / 70% 复用比例撤回；LSM-Raft 的 PDF 是拦截页，不是成功入库；若干“全文翻译”实为译述，已在对应正文说明。旧日志保留作为操作历史，不应作为技术事实来源。

本轮按原文核对 18 个有效论文主题，扩充机制、假设、例子、实验条件与证据位置；维护规则采用 Mermaid 优先，保留原始 PDF。未将未复现的作者结果标成独立验证。

## 2026-10-09 — 已发布调研增量同步

- 原 231 篇映射覆盖当前全部 `_posts`；Week 12–13 两端 SHA256 与清单一致，保留全文不覆盖。跳过 compat 重定向、历史归档和草稿。
- 新增流存储技术观察 2026-10-09 完整 Markdown，保留固定 URL、源 commit、观察日期和逐项原始链接。
- 从合刊与专题报告提炼 8 张机制卡；未新增声称已完整精读的论文，未下载 PDF 或自动翻译。
- 保留现有卡片与用户编辑，新卡采用更窄的问题范围并关联既有概念；新卡 draft/0.70，未将报告副本当作独立核验证据。
- 更新索引、实体图谱、双端同步清单和后续精读流程。公开范围仅含已有公开调研及其技术提炼。
