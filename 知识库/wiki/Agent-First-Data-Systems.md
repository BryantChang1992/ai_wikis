---
type: concept
title: "Agent-First Data Systems — Agent 优先的数据系统架构"
tags:
  - LLM-Agent
  - 数据系统架构
  - Agentic-Speculation
  - 查询优化
  - CIDR-2026
related:
  - "[[Agent-First-Branch-Transactions-分支事务]]"
  - "[[Agentic-Memory-语义缓存]]"
sources:
  - "sources/papers/Agent-First-Data/Agent-First-Data-CIDR2026.pdf"
status: draft
created: 2026-06-15
updated: 2026-06-15
diagram: "diagram/agent-first-data-systems.svg"

---

# Agent-First Data Systems — Agent 优先的数据系统架构

## 一句话总结

UC Berkeley 的愿景论文：传统数据系统是为人机交互的**被动查询-结果模型**设计的（低并发、精确答案、独立查询），必须重构为 **Probe-Brief 的主动引导模型**（高并发、satisficing、冗余共享、可转向）才能适应 LLM Agent 成为主要 workload 的未来。

## Agentic Speculation 四特性

| 特性 | 含义 | 优化机会 |
|------|------|----------|
| **Scale（规模）** | 每秒上千请求 | Satisficing 而非全量执行 |
| **Heterogeneity（异质性）** | 粗探索→精确验证混合 | Phase-based 近似度控制 |
| **Redundancy（冗余）** | 不同探针高度重叠 | MQO + 缓存共享 |
| **Steerability（可引导性）** | Agent 可被引导向更优方向 | Sleeper Agent 提供辅助反馈 |

### 实证（BIRD + 多后端 Case Study）

- 并行 50 次尝试 → 成功率提升 14-70%
- Distinct sub-plan 仅 10-20%（冗余巨大）
- 给 hints → SQL 查询减少 18%，部分查询减少 37%

## 三层架构

<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 540 120" width="540" height="120">
  <rect x="20" y="5" width="500" height="32" rx="6" fill="transparent" stroke="currentColor" stroke-width="1.5"/>
  <text x="270" y="21" font-family="sans-serif" font-size="12" fill="currentColor" text-anchor="middle" dominant-baseline="middle">Query Interfaces: Probe + Brief + Sleeper Agent</text>
  <line x1="20" y1="37" x2="520" y2="37" stroke="currentColor" stroke-width="1"/>
  <rect x="20" y="40" width="500" height="32" rx="6" fill="transparent" stroke="currentColor" stroke-width="1.5"/>
  <text x="270" y="56" font-family="sans-serif" font-size="12" fill="currentColor" text-anchor="middle" dominant-baseline="middle">Probe Optimizer: Satisficing / MQO / AQP</text>
  <line x1="20" y1="72" x2="520" y2="72" stroke="currentColor" stroke-width="1"/>
  <rect x="20" y="75" width="500" height="32" rx="6" fill="transparent" stroke="currentColor" stroke-width="1.5"/>
  <text x="270" y="91" font-family="sans-serif" font-size="12" fill="currentColor" text-anchor="middle" dominant-baseline="middle">Storage: Agentic Memory + Branch Transactions</text>
</svg>

### Layer 1: Probe > Query

- Probe = SQL + **brief**（NL goals, phase, 近似需求, 优先级）
- 支持语义相似搜索（"找跟 electronics 相关的表"）——SQL 无法表达
- 支持终止条件函数（eval on partial results → 提前结束）

### Layer 2: Satisficing 不是 Optimizing

- 旧目标：max 吞吐（等所有查询完整结果）
- 新目标：min 总交互时间（刚好够让 agent 决策下一步）
- Intra-probe：语义剪枝 + phase-based 近似度 + MQO 共享
- Inter-probe：去重 + 预物化 + Exploration vs Exploitation

### Layer 3: Agentic Memory + Branch TX

详见 [[Agentic-Memory-语义缓存]] 和 [[Agent-First-Branch-Transactions-分支事务]]

## 核心优势

1. ✅ 不要求 agent 写更好的 SQL — 而是数据库"主动理解" agent
2. ✅ Satisficing 将成本从"绝对算术"转为"省总时间"——更符合 agent 多轮交互的本质
3. ✅ 四个特性的抽象有实验数据支持（不是拍脑袋）
4. ✅ Sleeper agent 本质上是把人类 DBA/分析师的知识自动化

## 局限

- ⚠️ 纯 Vision Paper，无实现，无系统验证
- ⚠️ Sleeper agent 成本/延迟/精度权衡未讨论
- ⚠️ Satisficing 如果太激进可能导致更多轮次——无理论界
- ⚠️ 隐私/安全问题仅被提及无解决方案
- ⚠️ 未讨论与具体数据库引擎（PostgreSQL/Spark/DuckDB）的结合

## 与知识库的关联

- [[事务模型深度调研]]：分支事务是 MVCC 在 agent 方向的自然延伸
- [[Agentic-Memory-语义缓存]]：Agentic Memory 需要向量索引 + 结构化查询双重能力
