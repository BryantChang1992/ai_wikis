---
type: concept
title: "Agent Harness: Context Management & Memory (C)"
sources:
  - "sources/papers/Agent-Harness-Engineering-Survey/Agent-Harness-Engineering-Survey-OpenReview2026.pdf"
  - "sources/papers/Agent-Harness-Engineering-Survey/精读分析.md"
tags:
  - "Agent-Harness"
  - "Agent基础设施"
  - "上下文管理"
  - "Agent记忆"
created: 2026-06-20
updated: 2026-06-20
status: draft
related:
  - "[[Agent-Harness-Engineering-Survey综述]]"
  - "[[Agent-Memory-Survey-2026综述]]"
  - "[[Agentic-Memory-语义缓存]]"
---

# Agent Harness: Context Management & Memory (C)

> ETCLOVG 第三层：Agent 如何在短期、中期和长期跨度上维护状态——Context Drift 是长期 Agent 的顶级威胁。

---

## 1. 层级定位

Context Management 关心的是**提供给模型用于推理的信息**——这不同于 Lifecycle 的操作状态（§6）和 Observability 的监控状态（§7）。

核心挑战：Agent 不是无状态函数，而是**有状态的、跨时间运行的过程**。上下文漂移（Context Drift）是这一层的最根本问题。

---

## 2. 三层记忆架构

### 2.1 Short-Term Memory（短期记忆）

| 维度 | 详情 |
|------|------|
| 跨度 | 单次推理（一个 Context Window） |
| 存储方式 | Prompt Assembly + System Messages + Tool Results |
| 代表技术 | Structured Prompt Templates, Anthropic 的 Context Assembly |
| 核心风险 | Token 消耗随对话增长线性上升 |
| 优化手段 | Prompt-cache-aware ordering, 工具结果截断, 早段消息摘要化 |

### 2.2 Mid-Term Memory（中期记忆）

| 维度 | 详情 |
|------|------|
| 跨度 | 多轮对话（同一 Session） |
| 存储方式 | Vector Store + RAG + 对话摘要 |
| 代表技术 | Mem0（用户级记忆）, Memobase（结构化记忆）, Letta（可编程记忆 Agent） |
| 核心风险 | 检索精度——错误的检索可能召回无关或误导性的记忆 |
| 优化手段 | 时间衰减权重、相关性排序、记忆合并去重 |

### 2.3 Long-Term Memory（长期记忆）

| 维度 | 详情 |
|------|------|
| 跨度 | 跨 Session（数天/数周/数月） |
| 存储方式 | 结构化数据库 + 配置文件 + 外部持久化 |
| 代表技术 | Zep（会话记忆+知识图谱）, cognee（图 RAG 记忆）, SuperMemory（第二大脑） |
| 核心风险 | **Context Drift** — Agent 状态逐渐偏离真实任务状态 |
| 优化手段 | 不确定性感知摘要、事实溯源（Provenance）、矛盾处理、显式过期标记 |

---

## 3. Context Drift（上下文漂移）——深度分析

### 3.1 定义

Context Drift 是指 Agent 在长时间运行中，其内部状态逐渐偏离真实任务状态的**不可逆过程**。这不是偶尔发生的边角案例——它是长期 Agent 的**系统性属性**。

### 3.2 四大漂移来源

| 来源 | 机制 | 后果 | 缓解 |
|------|------|------|------|
| **Compaction** | 每步压缩删除信息 | 关键约束被抹去 | 约束标记机制——不能被压缩的关键信息显式标记 |
| **Retrieval** | 漂移中的 Agent 不知道该检索什么 | 错误的检索加深漂移 | 被动触发式重检索（当置信度下降时） |
| **Sub-agent Isolation** | 子 Agent 上下文不污染编排器 | 编排器自身积累漂移 | 定期状态对账——编排器与子 Agent 结果交叉校验 |
| **幻觉沉淀** | 幻觉输出存入持久记忆 | 跨 Session 的自强化退化 | QSAF 检测——识别和标记可疑记忆 |

### 3.3 幻觉沉淀（Hallucination Sedimentation）——QSAF 框架

QSAF（Atta et al., 2025）将认知退化形式化为六阶段生命周期，验证在 5 个 LLM 平台上：
1. Agent 产生幻觉输出
2. 幻觉被存入持久记忆存储
3. 未来 Session 中 RAG 召回该幻觉
4. Agent 将幻觉视为事实
5. 基于"事实"做出错误决策
6. 错误决策产生的新信息再次存入记忆——**自强化循环**

### 3.4 为什么当前技术不足

| 技术 | 能解决的问题 | 不能解决的问题 |
|------|-------------|---------------|
| Compaction | Token 数量 | 压缩是否保留了所有关键约束？ |
| Retrieval | 相关信息的表面匹配 | 漂移中的 Agent 不知道需要检索什么 |
| Sub-agent Isolation | 子任务上下文污染 | 编排器自身的上下文漂移 |

Bowne-Anderson & Huber (2026) 的**边界论**：Context Engineering 本身永远无法解决长期可靠性——需要完整的 Harness 层（验证循环 + 检查点 + 异常检测）。

---

## 4. 记忆的写–管–读循环

论文和 Zhang et al. (2025) / Du (2026) 将 Agent 记忆形式化为三阶段循环：

```
Write（写入）  →  新信息纳入记忆系统
   ↓
Manage（管理） →  去重、合并、过期、冲突解决、策略学习
   ↓
Read（读取）   →  RAG 检索、结构化查询、上下文注入
   ↓__________________________________
        (新的交互产生新信息 → 回到 Write)
```

**策略学习的记忆管理**（Policy-Learned Management）是新兴机制——动态学习哪些信息应保留、哪些应遗忘。

---

## 5. 关键基准测试

| 基准 | 作者 | 核心测量 | 发现 |
|------|------|----------|------|
| **MemoryArena** | He et al. (2026) | 相互依赖的多 Session 任务 | Context Drift 最具破坏性的场景 |
| **MemBench** | Tan et al. (2025) | 跨 Session 时序推理、知识更新、聚合 | 记忆质量在时序推理中退化最快 |
| **增量多轮评估** | Hu et al. (2025b) | 隔离记忆质量与生成质量 | 记忆系统是独立于模型生成能力的瓶颈 |

这些基准的局限性：它们证明漂移发生，但尚未提供**防止漂移的机制性理解**。

---

## 6. 设计原则

1. **将上下文管理重新定义为状态估计**：量化每次压缩/检索/遗忘的信息损失
2. **不确定性感知摘要**：摘要应附带置信度标记——哪些信息是确定的，哪些是推测的
3. **事实溯源（Provenance）**：每条记忆应可追溯到其来源——"这条信息来自哪个 Session 的哪次工具调用"
4. **显式过期标记**：不依赖 Agent 自己判断信息是否过时——由系统标记
5. **恢复程序**：Agent 应能从**外部工件**（Git 记录、文件、日志）重建状态，而非信任自己的压缩历史
6. **记忆与评估绑定**：记忆质量不应仅靠召回准确性——最终评判标准是下游行动错误率

---

## 7. 未来方向

- **不确定性感知的压缩算法**：在压缩上下文中，标记哪些信息是确定的、哪些可能不准确
- **矛盾检测与协调**：当新信息与旧记忆冲突时，主动触发协调而非静默覆盖
- **记忆预算**：像 Token 预算一样管理记忆预算——不同优先级的记忆获得不同的保留时长
