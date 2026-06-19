---
type: meta
title: "知识库操作日志"
tags: ["meta", "log"]
created: 2026-06-14
updated: 2026-06-15
---

# 知识库操作日志

> 时序记录所有增删改操作。格式：`[日期 时间] 操作者: 操作类型 — 描述`

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
- 新卡片全部 `status: draft`，related 字段暂空（留待 Synthesize 建立内链）
- 增量 Lint：11 卡 sources 引用全部有效，0 dangling
- **索引更新**：`sources/README.md` + `知识库/README.md` 新增 AI Infra + Fluss 实践 section
- **Commit**: `6121932` — feat(ingest): CEO 派发 11 篇文章入库 — AI Infra + Fluss 实践

