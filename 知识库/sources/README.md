---
type: meta
title: 源文件索引
tags:
- meta
- sources
created: 2026-06-14
updated: '2026-10-11'
---

# 源文件索引 (Raw Sources)

> 本目录同时保留原始资料和历史派生阅读材料。已取得的原始 PDF、真实网页快照及原始笔记不可改写；精读分析、译述和来源索引允许基于证据纠错并保留 Git 历史。`web/` 当前主要是阅读分析，不能冒称完整网页存档。详见 [[知识库/schema]]。

## 子目录

| 目录 | 内容 | 来源 |
|------|------|------|
| `papers/` | 论文原文（PDF）+ 精读分析 + 翻译 | 论文精读、调研中引用的论文 |
| `web/` | 网页存档 | 技术调研周报中的参考链接 |
| `notes/` | 原始笔记 | 会议记录、随手笔记、外部资料 |

## 论文目录结构

每篇论文一个父目录；原文、精读分析和译文分别记录取得状态。文件名“全文翻译”可能为兼容旧链接保留，实际覆盖以正文声明为准：

```
sources/papers/
├── Event-Horizon/
│   ├── Event-Horizon-CIDR2026.pdf    ← 英文原文
│   ├── 精读分析.md                    ← 精读分析
│   └── 全文翻译.md                    ← 译文（明确全文/节译/译述范围）
├── LSM-Survey/
│   ├── LSM-Survey-VLDBJ2019.pdf
│   ├── 精读分析.md
│   └── 全文翻译.md
└── RaaS/
    ├── RaaS-SIGMOD2026.pdf
    ├── 精读分析.md
    └── 全文翻译.md
```

## 入库规则

1. 每篇论文建一个以论文简称命名的父目录
2. 按实际取得与授权情况放原文、精读分析和明确覆盖范围的译文；不强制 PDF 或全文翻译齐备。
3. 先用精读分析定位，再回到原文核对关键断言；分析稿不是独立的一手来源。
4. 源文件 SHA256 去重——相同内容不重复处理

## 当前源文件列表

### papers/
- [Event-Horizon/](papers/Event-Horizon/) — CIDR 2026，TU Delft，非对称依赖降低跨地域延迟
  - Event-Horizon-CIDR2026.pdf（原文，1.6MB）
  - 精读分析.md / 全文翻译.md
- [LSM-Survey/](papers/LSM-Survey/) — VLDB Journal 2019，UC Irvine，LSM-tree 综述
  - LSM-Survey-VLDBJ2019.pdf（原文，879KB）
  - 精读分析.md / 全文翻译.md
- [RaaS/](papers/RaaS/) — SIGMOD 2026，Purdue，存储计算分离 Tail Latency 消除
  - RaaS-SIGMOD2026.pdf（原文，3.2MB）
  - 精读分析.md / 全文翻译.md
- [CockroachDB-Leader-Leases/](papers/CockroachDB-Leader-Leases/) — SIGMOD 2026，CockroachDB，多 Raft 组 Leader Lease 扩展
  - Scalable-Leader-Leases-SIGMOD2026.pdf（原文，1.2MB）
  - 精读分析.md / 全文翻译.md ✅
  - → wiki: CockroachDB-Leader-Lease-整体设计.md, CockroachDB-Liveness-Fabric-故障检测层.md, CockroachDB-Leader-Fortification.md
- [Rose/](papers/Rose/) — CIDR 2026，Columbia，分区数据库的灵活复制
  - Rose-CIDR2026.pdf（原文，536KB）
  - 精读分析.md / 全文翻译.md ✅
  - → wiki: Rosé-异步复制协议设计.md, Rosé-Coordinated-Apply-协调应用.md
- [Agent-First-Data/](papers/Agent-First-Data/) — CIDR 2026，Berkeley，Agent-First 数据系统
  - Agent-First-Data-CIDR2026.pdf（原文，849KB）
  - 精读分析.md / 全文翻译.md ✅
  - → wiki: Agent-First-Data-Systems.md, Agentic-Memory-语义缓存.md, Agent-First-Branch-Transactions-分支事务.md
- [LSM-Scheduling/](papers/LSM-Scheduling/) — FAST 2026，HATS：分布式 LSM 读流量与本地 Compaction 配额协同调度（旧目录名保留兼容）
  - LSM-Scheduling-FAST2026.pdf（原文，3.2MB）
  - 精读分析.md / 全文翻译.md ✅
  - → wiki: Silo-分布式LSM-Compaction调度.md, Silo-Compaction-迁移协议.md
- [LSM-Raft/](papers/LSM-Raft/) — ⚠️ 原文未取得；既有 PDF 是拦截页，题名与机制待核验
  - SIGMOD Poster 仅有摘要公开，ACM Cloudflare 封锁，ResearchGate IP 被封
  - 目录已预留，后续若能获取 PDF 再补充 Ingest
- [ByteHouse/](papers/ByteHouse/) — SIGMOD 2026 Companion，ByteDance，云原生多模态数仓
  - ByteHouse-SIGMOD2026.pdf（原文，2.8MB）
  - 精读分析.md ✅
  - → wiki: ByteHouse-架构与设计.md, ByteHouse-统一表引擎.md, ByteHouse-多模态查询优化.md
- [Aurora-Limitless/](papers/Aurora-Limitless/) — SIGMOD 2026 Industry，AWS，Aurora PostgreSQL 水平扩展
  - Aurora-Limitless-SIGMOD2026.pdf（原文，1.7MB）
  - 精读分析.md / 全文翻译.md ✅
  - → wiki: Aurora-Limitless-分布式架构.md, Aurora-Limitless-时间戳事务.md, Aurora-Limitless-自适应扩缩容.md
- [Chandy-Lamport-Snapshot/](papers/Chandy-Lamport-Snapshot/) — TOCS 1985，Chandy & Lamport，分布式快照算法开山之作（SIGOPS Hall of Fame 2013）
  - Chandy-Lamport-Snapshot-TOCS1985.pdf（原文，969KB）
  - 精读分析.md ✅
  - → wiki: Chandy-Lamport-分布式快照算法.md
- [Raft-Dissertation/](papers/Raft-Dissertation/) — Stanford 2014，Ongaro，Raft 共识算法博士论文（被引 15000+）
  - Ongaro-Raft-Dissertation-Stanford2014.pdf（原文，5.1MB）
  - 精读分析.md ✅
  - → wiki: Raft-共识算法协议核心.md, Raft-集群成员变更.md, Raft-日志压缩.md, Raft-客户端交互.md, Paxos-理论到实践的鸿沟.md
  - → synthesis: 共识协议体系综述.md
- [Distributed-Consensus-Revised/](papers/Distributed-Consensus-Revised/) — Cambridge 2019，Heidi Howard，分布式共识博士论文
  - [Cambridge 官方原文](https://www.cl.cam.ac.uk/techreports/UCAM-CL-TR-935.pdf)；当前仓库只有精读分析，没有本地 PDF。arXiv:1902.06776 是另一篇相关论文，不是该学位论文编号。
  - 精读分析.md ✅
  - → wiki: 共识算法族系-从Paxos到广义解.md, Paxos-Quorum-Intersection-Revised.md, Paxos-Value-Selection-Revised.md, Paxos-Epochs-Revised.md
- [LSM-tree-KV-Survey-2025/](papers/LSM-tree-KV-Survey-2025/) — ArXiv 2025-07，MBZUAI + OceanBase + 厦门大学，LSM-tree KV Store 综述（2020-2025）
  - LSM-tree-KV-Survey-2025.pdf（原文，1.6MB）
  - 精读分析.md ✅
  - → wiki: LSM-tree-KV-Survey-综述.md（已有页面）
- [Agent-Memory-Survey/](papers/Agent-Memory-Survey/) — ArXiv 2026-03，Agent Memory 综述
  - 精读分析.md
  - → wiki: Agent-Memory-Survey-2026综述.md
- [Parallax/](papers/Parallax/) — ArXiv 2026-04，Agent 安全架构（Cognitive-Executive Separation）
  - 精读分析.md
  - → wiki: Parallax-Agent安全架构.md
- [Agent-Harness-Engineering-Survey/](papers/Agent-Harness-Engineering-Survey/) — TMLR 2026 (under review)，Agent Harness Engineering 综述
  - Agent-Harness-Engineering-Survey-OpenReview2026.pdf（原文，3.4MB）
  - 精读分析.md ✅
  - → wiki: Agent-Harness-Engineering-Survey综述.md + 7 张 ETCLOVG 分层卡片

### 2026-07-11 新增
- [Bigtable/](papers/Bigtable/精读分析.md) — OSDI 2006，Google，PB 级分布式结构化存储系统（NoSQL 基石）
  - Bigtable-OSDI-2006.pdf（原文，221KB）
  - 精读分析.md（CTO 自产）
  - → wiki: Bigtable-分布式结构化存储系统.md

### Week 09 入库 — 2026-07-03 🆕
- [Hermes Agent](web/hermes-agent/) — Nous Research 自进化 Agent 框架 GitHub README 精读
- [Qwen 3.6](web/qwen-3.6/) — Alibaba Qwen 3.6 模型发布精读分析
- [Agent 框架对比 2026](web/agent-frameworks-2026/) — 五大 Agent 框架 2026 全景对比精读
- [Apache Flink 2.3.0](web/flink-2.3.0/) — Apache Flink 2.3.0 官方发布公告精读
- [Fluss 客户端写入分析](web/fluss-client-write/) — Fluss 客户端写入流程源码深度分析（8 模块全完成）
- [CockroachDB vs TiDB](web/cockroachdb-vs-tidb/) — CockroachDB vs TiDB 2026 架构对比精读
- [CXL 3.0](web/cxl-3.0/) — CXL 3.0 内存池化产业趋势精读

### web/
- [Fluss 源码分析](web/fluss/) — Fluss trunk vs Kafka 2.7.2 源码级对比分析（2026-06-10）
  - 01-整体架构对比.md（已入库）
  - 完整模块分析已有 [[项目文档/Fluss源码分析/README|项目文档入口]]；不因本目录只保留部分摘录而重复转换/入库。
- [Anthropic — How We Contain Claude](web/anthropic/how-we-contain-claude-精读.md) — Anthropic Engineering Blog 2026
  - 精读分析.md
  - → wiki: Anthropic-Agent安全容器化实践.md
- [The Art of Loop Engineering](web/langchain/the-art-of-loop-engineering-精读.md) — LangChain Blog 2026-06
  - 精读分析.md
  - → wiki: Loop-Engineering-多层Agent循环架构.md
- [Why Model Neutrality Matters](web/langchain/model-neutrality-精读.md) — LangChain Blog 2026-06
  - 精读分析.md
  - → wiki: Model-Neutrality-模型中立与反锁定.md
- [Fault Tolerance in LangGraph](web/langchain/fault-tolerance-in-langgraph-精读.md) — LangChain Blog 2026-06
  - 精读分析.md
  - → wiki: Agent-Fault-Tolerance-容错设计.md
- [Custom Agent Harness](web/langchain/custom-agent-harness-精读.md) — LangChain Blog 2026-06-03
  - 精读分析.md
  - → wiki: Custom-Agent-Harness-Middleware架构.md
- [Coding Agent Spend Predictable](web/langchain/coding-agent-spend-精读.md) — LangChain Blog 2026-06-15
  - 精读分析.md
  - → wiki: Agent-Cost-Control-Gateway成本控制.md
- [Right Sandbox for Agent](web/langchain/right-sandbox-agent-精读.md) — LangChain Blog 2026-06-12
  - 精读分析.md
  - → wiki: Agent-Sandbox-安全沙箱选型.md
- [Bottling the River: Fluss on EKS](web/fresha/bottling-the-river-fluss-eks-精读.md) — Fresha Data Engineering Blog 2026-04-30
  - 精读分析.md
  - → wiki: Fluss-EKS-生产部署实践-Fresha.md
- [Fluss PR #3420](web/fluss/Fluss-PR-3420-Watermark-Paimon-精读.md) — GitHub apache/fluss 2026-06
  - 精读分析.md
  - → wiki: Fluss-PR-3420-Watermark-to-Paimon.md

### notes/
*(待入库)*

---

*由 CHANG_AI_TEAM Agent 维护；来源索引于 2026-10-09 按当前文件树复核，非所有原文重新精读。*

## 2026-06-16 新增

| 文件 | 类型 | 来源 |
|------|------|------|
| `papers/Chandy-Lamport-Snapshot/` | 经典论文 + 精读分析 | ACM TOCS 1985 |
| `papers/Chandy-Lamport-Snapshot/Chandy-Lamport-Snapshot-TOCS1985.pdf` | PDF 原文 | lamport.azurewebsites.net |
| `papers/Chandy-Lamport-Snapshot/精读分析.md` | 精读分析 | CTO 自产 |
| `papers/Raft-Dissertation/` | 博士论文 + 精读分析 | Stanford University 2014 |
| `papers/Raft-Dissertation/Ongaro-Raft-Dissertation-Stanford2014.pdf` | PDF 原文 | GitHub ongardie/dissertation |
| `papers/Raft-Dissertation/精读分析.md` | 精读分析 | CTO 自产 |
| `papers/Distributed-Consensus-Revised/` | 精读分析，原文仅外部链接 | Cambridge 2019，UCAM-CL-TR-935；未保存本地 PDF |
| `papers/Distributed-Consensus-Revised/精读分析.md` | 精读分析 | CTO 自产 |

## 2026-07-02 新增

| 文件 | 类型 | 来源 |
|------|------|------|
| `papers/LSM-tree-KV-Survey-2025/` | 综述论文 + 精读分析 | ArXiv 2025-07 |
| `papers/LSM-tree-KV-Survey-2025/LSM-tree-KV-Survey-2025.pdf` | PDF 原文 | arxiv.org (2507.09642) |
| `papers/LSM-tree-KV-Survey-2025/精读分析.md` | 精读分析 | CTO 自产 |

## 2026-06-15 新增

| 文件 | 类型 | 来源 |
|------|------|------|
| `papers/SP-Survey/` | Survey 论文 + 精读分析 | arXiv:2008.00842 |
| `papers/SP-Survey/SP-Survey-arXiv2020.pdf` | PDF 原文 | arXiv |
| `papers/SP-Survey/精读分析.md` | 精读分析 | CTO 自产 |

## 2026-10-09 已发布报告来源入口

- [[技术文章/博客同步/tech-research-week-12-13|Week 12–13 合刊]]：已有完整正文及原始论文/PR链接；本轮校验正文与清单一致，不声称再次独立精读所有引用论文。
- [[技术文章/博客同步/stream-storage-observer-2026-10-09|流存储技术观察 2026-10-09]]：公开报告完整 Markdown，原始 Issue/PR/邮件/FIP/KIP 链接随正文保存。
- [[知识库/调研与精读流程|后续原文、详细笔记、精简卡片与双端更新流程]]。本轮未新下载论文或自动翻译。

## 维护与缺口

- [[知识库/维护记录/待核验与知识缺口]]：原文未取得、来源身份纠正和待研究概念。
- [[知识库/维护记录/原始资料基线.json]]：本轮记录的原件 Git blob 标识；文件存在不等于内容有效，基线不替代原文或版权核验。

## 2026-10-11 论文与原创技术博客

- [[知识库/sources/papers/Active-Data-Lakes/来源记录|虚拟 Parquet：固定布局与按需转码的兼容边界来源记录]]：PVLDB 19(6)，2026-02；本周为补读，不是新发表。
- [[知识库/sources/web/fluss-streamhouse-lakestream-20261005/来源记录|流湖交接：快照进度与 freshness 边界来源记录]]：本周文章 2026-10-05；机制/调优补读分别为2026-06-04、2026-06-09。
- [[知识库/sources/papers/LESS-FAST2026/来源记录|纠删恢复：读取量与寻道共同优化来源记录]]：FAST26，会议2026-02-24至26；本周为旧文补读。
- [[知识库/sources/web/vllm-inference-20261007-09/来源记录|SWA 缓存：有界重算与图捕获开销来源记录]]：本周vLLM作者博客2026-10-07、2026-10-09；后者保留作局部性对照。

本期仅链接合法公开的一手材料，保留来源和阅读边界；未转载原文PDF或整篇网页、未生成全文翻译。完整报告见 [[技术文章/博客同步/tech-research-week-14]]。
