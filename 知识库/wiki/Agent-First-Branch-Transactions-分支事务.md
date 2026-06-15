---
type: concept
title: "Agent-First Branch Transactions — Agent 优先的分支事务"
tags:
  - LLM-Agent
  - 事务处理
  - MVCC
  - 分支
  - CIDR-2026
  - 快照隔离
related:
  - "[[Agent-First-Data-Systems]]"
  - "[[事务模型深度调研]]"
sources:
  - "sources/papers/Agent-First-Data/Agent-First-Data-CIDR2026.pdf"
status: draft
created: 2026-06-15
updated: 2026-06-15
diagram: "diagram/agent-first-data-systems.svg"

---

# Agent-First Branch Transactions — Agent 优先的分支事务

## 一句话总结

Agent 在探索数据时创建大量"what-if"分支——Neon 观察 agent 创建 20× 更多分支、50× 更多 rollback。分支事务需要支持 **Multi-World Isolation**（逻辑隔离 + 物理共享，即 "MVCC on steroids"），以实现上千近似快照的并行探索 + 超快速 rollback。

## 问题

传统事务模型假设：
- 单个执行线程 → ACID 隔离
- Rollback 是异常情况（罕见）

Agent 的现实：
- **多分支并行探索**：同一个 "如果重组机组" 任务可能有数十个假设性事务流
- **Rollback 是常态**：大部分分支最终被丢弃，只保留一个最优方案
- **分支高度相似**：同一 schema，90% 相同数据
- **分支需要互相 reconcile**：不仅是与 mainline，还包括 branch vs branch

## 核心概念: Multi-World Isolation (MWI)

| | 传统 ACID | MWI (Agent-First) |
|---|---|---|
| 隔离模式 | 线性隔离 | 逻辑隔离 + 物理共享 |
| Rollback 频率 | 罕见 | 常态（超轻量） |
| 分支数量 | 个位数 | 成千上万 |
| 分支相似度 | 各异 | 高度相似（90%+） |
| Reconciliation | 与 mainline | 与 mainline + 其他分支 |

## 技术启发

### 学术先行者
- **Bayou**：弱一致性下的分支操作，最终 reconciliation
- **Tardis**：branch-and-merge 弱一致性模型
- **ORPHEUSDB**：关系型数据库上的 bolt-on 版本管理
- **Dynamo**：弱一致性版本解决

### 工业界
- **Neon (Serverless Postgres)**：CoW 分支，agent 已在使用
- **Aurora**：CoW 克隆
- **Bauplan**：proof-carrying agent 分支

## 新挑战

1. **"MVCC on steroids"**：MVCC 管理数百版本——分支事务需管理数千相似快照
2. **Ultra-fast rollback**：不是偶尔回滚，而是绝大部分分支都需要快速 abort
3. **相似分支间的计算共享**：两个分支修改不同列但基于同一快照 → 可以从同一物理页派生，但逻辑隔离不交叉污染
4. **Agent 间分支 reconciliation**：两个 agent 在同一段时间做了不同探索，需要 merge 方案

## 与知识库的关联

- [[事务模型深度调研]] 中 MVCC/Snapshot Isolation 是 MWI 的基础
- CockroachDB 的 [[CockroachDB-Leader-Lease-整体设计]] 中的 epoch 机制可以为分支事务提供 snapshot establishment
- Rosé 的 [[Rosé-Coordinated-Apply-协调应用]] 中 WAL/KV 分离思想 → 分支事务可以将分支变更留在 WAL 中而不触及共享 KV store

## 局限

- 纯愿景，无实现
- 多分支 reconcile 的语义未定义
- 只说"借鉴 MVCC"但未给出设计细节
