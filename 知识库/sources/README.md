---
type: meta
title: "源文件索引"
tags: ["meta", "sources"]
created: 2026-06-14
updated: 2026-06-16
---

# 源文件索引 (Raw Sources)

> `sources/` 是三层架构中的 **Raw Sources 层**。这里的文件是只读的原始资料——Agent 读取但绝不修改。

## 子目录

| 目录 | 内容 | 来源 |
|------|------|------|
| `papers/` | 论文原文（PDF）+ 精读分析 + 翻译 | 论文精读、调研中引用的论文 |
| `web/` | 网页存档 | 技术调研周报中的参考链接 |
| `notes/` | 原始笔记 | 会议记录、随手笔记、外部资料 |

## 论文目录结构

每篇论文一个父目录，内含英文原文 PDF + 精读分析 + 全文翻译：

```
sources/papers/
├── Event-Horizon/
│   ├── Event-Horizon-CIDR2026.pdf    ← 英文原文
│   ├── 精读分析.md                    ← 精读分析
│   └── 全文翻译.md                    ← 中文全文翻译
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
2. 父目录下放：英文原文 PDF、精读分析.md、全文翻译.md
3. Agent 读取时优先用精读分析作为 ingest 源材料，PDF 作为溯源
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
- [LSM-Scheduling/](papers/LSM-Scheduling/) — FAST 2026，UC Riverside，分布式 LSM Compaction 全局调度
  - LSM-Scheduling-FAST2026.pdf（原文，3.2MB）
  - 精读分析.md / 全文翻译.md ✅
  - → wiki: Silo-分布式LSM-Compaction调度.md, Silo-Compaction-迁移协议.md
- [LSM-Raft/](papers/LSM-Raft/) — SIGMOD 2026 Poster，Tsinghua，LSM-tree 与 Raft 协同优化（⚠️ 无法获取）
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
  - UCAM-CL-TR-935.pdf（原文，1.2MB）+ arxiv-1902.06776.pdf
  - 精读分析.md ✅
  - → wiki: 共识算法族系-从Paxos到广义解.md, Paxos-Quorum-Intersection-Revised.md, Paxos-Value-Selection-Revised.md, Paxos-Epochs-Revised.md
- [Distributed-Consensus-Revised/](papers/Distributed-Consensus-Revised/) — Cambridge 2019，Heidi Howard，分布式共识博士论文（Cited 100+）
  - UCAM-CL-TR-935.pdf（原文，1.2MB）+ arxiv-1902.06776.pdf
  - 精读分析.md ✅
  - → wiki: 共识算法族系-从Paxos到广义解.md, Paxos-Quorum-Intersection-Revised.md, Paxos-Value-Selection-Revised.md, Paxos-Epochs-Revised.md
  - → synthesis: 将整合入共识协议体系综述（待更新）

### web/
- [Fluss 源码分析](web/fluss/) — Fluss trunk vs Kafka 2.7.2 源码级对比分析（2026-06-10）
  - 01-整体架构对比.md（已入库）
  - 02~07 待补（原文件: tech_research/fluss/*.html，需从 HTML 转换为 md）

### notes/
*(待入库)*

---

*由 CHANG_AI_TEAM Agent 维护，最后更新: 2026-06-16*

## 2026-06-16 新增

| 文件 | 类型 | 来源 |
|------|------|------|
| `papers/Chandy-Lamport-Snapshot/` | 经典论文 + 精读分析 | ACM TOCS 1985 |
| `papers/Chandy-Lamport-Snapshot/Chandy-Lamport-Snapshot-TOCS1985.pdf` | PDF 原文 | lamport.azurewebsites.net |
| `papers/Chandy-Lamport-Snapshot/精读分析.md` | 精读分析 | CTO 自产 |
| `papers/Raft-Dissertation/` | 博士论文 + 精读分析 | Stanford University 2014 |
| `papers/Raft-Dissertation/Ongaro-Raft-Dissertation-Stanford2014.pdf` | PDF 原文 | GitHub ongardie/dissertation |
| `papers/Raft-Dissertation/精读分析.md` | 精读分析 | CTO 自产 |
| `papers/Distributed-Consensus-Revised/` | 博士论文 + 精读分析 | Cambridge 2019 |
| `papers/Distributed-Consensus-Revised/UCAM-CL-TR-935.pdf` | PDF 原文 | cl.cam.ac.uk |
| `papers/Distributed-Consensus-Revised/精读分析.md` | 精读分析 | CTO 自产 |
| `papers/Distributed-Consensus-Revised/` | 博士论文 + 精读分析 | Cambridge 2019 |
| `papers/Distributed-Consensus-Revised/UCAM-CL-TR-935.pdf` | PDF 原文 | cl.cam.ac.uk |
| `papers/Distributed-Consensus-Revised/arxiv-1902.06776.pdf` | ArXiv 版本 | arxiv.org |
| `papers/Distributed-Consensus-Revised/精读分析.md` | 精读分析 | CTO 自产 |

## 2026-06-15 新增

| 文件 | 类型 | 来源 |
|------|------|------|
| `papers/SP-Survey/` | Survey 论文 + 精读分析 | arXiv:2008.00842 |
| `papers/SP-Survey/SP-Survey.pdf` | PDF 原文 | arXiv |
| `papers/SP-Survey/精读分析.md` | 精读分析 | CTO 自产 |
