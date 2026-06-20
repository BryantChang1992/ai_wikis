---
type: concept
title: "Agent Harness: Lifecycle & Orchestration (L)"
sources:
  - "sources/papers/Agent-Harness-Engineering-Survey/Agent-Harness-Engineering-Survey-OpenReview2026.pdf"
  - "sources/papers/Agent-Harness-Engineering-Survey/精读分析.md"
tags:
  - "Agent-Harness"
  - "Agent基础设施"
  - "Agent编排"
  - "多Agent"
created: 2026-06-20
updated: 2026-06-20
status: draft
related:
  - "[[Agent-Harness-Engineering-Survey综述]]"
  - "[[Loop-Engineering-多层Agent循环架构]]"
  - "[[Custom-Agent-Harness-Middleware架构]]"
  - "[[Agent-Fault-Tolerance-容错设计]]"
---

# Agent Harness: Lifecycle & Orchestration (L)

> ETCLOVG 第四层：Agent 如何跨多轮推理、工具调用、失败恢复和交付物交接来完成任务——从单一循环到完整工程流水线。

---

## 1. 层级定位

Lifecycle & Orchestration 结合了两个在早期框架中经常分离的关注点：
1. **Agent 的执行流**——如何从一个状态转移到下一个
2. **操作状态**——执行流读取和写入的持久状态

长期任务中，可靠性不取决于模型能否生成"好的下一步"，而取决于 Harness 能否**记住已发生的事、决定下一步、从错误中恢复、协调子任务、在完成时停止**。

---

## 2. 三层编排架构

### 2.1 Level 1: Single-Agent Inner Loop（单 Agent 内循环）

| 维度 | 详情 |
|------|------|
| 核心模式 | 观察 → 决策 → 行动 → 反馈，遵循 ReAct 范式（Yao et al., 2023） |
| 执行模型两种 | **Stateless Replay** vs. **Hybrid（Stateful+Replay）** |

**Stateless vs. Stateful 之争**：

| 模型 | 代表系统 | 机制 | 优点 | 缺点 |
|------|----------|------|------|------|
| **Stateless Replay** | Codex CLI (OpenAI, 82k ⭐) | 从交互历史重建执行 | 可复制、可审计 | 轨迹长时重建成本高 |
| **Hybrid** | Claude Code (123k ⭐), OpenCode (159k ⭐), Aider (45k ⭐), Gemini CLI (104k ⭐) | 可重播历史 + 持久化工件 | 连续性 + 审计性 | 一致性和调试挑战 |

**代表系统能力对比**：

| 系统 | GitHub Stars (k) | 主要特点 |
|------|-----------------|----------|
| OpenCode | 159 | 开源最大，多模型支持 |
| Claude Code | 123 | Anthropic 生态，强架构感知 |
| Gemini CLI | 104 | Google 生态，多模态 |
| Codex CLI | 82 | OpenAI 生态，纯无状态设计 |
| Aider | 45 | AI 结对编程，Git 原生集成 |
| SWE-agent | 19 | 学术代码修复，AID 接口设计 |

### 2.2 Level 2: Multi-Agent Orchestration（多 Agent 编排）

**五种编排模式**：

| 模式 | 核心机制 | 代表系统（Stars k） | 何时使用 |
|------|----------|---------------------|----------|
| **Hierarchical** | 高级控制器分配任务，Agent 作为执行者 | AutoGen (58), OpenAI Agents SDK (26), DeerFlow (67), DeepAgents (23) | 任务可清晰分解为子任务 |
| **Team** | 具名角色的专业化 Agent 协作 | oh-my-claudecode (34) | 需要明确的角色分工（规划者/编码者/审查者） |
| **Workflow** | Agent/工具组成显式阶段 | Semantic Kernel (28) | 业务流程/流水线式的任务 |
| **Fan-out** | 多 Agent 并行探索 | Emdash (4) | 需要多样性（代码生成、创意任务） |
| **Graph Composition** | Agent/工具/状态为节点的交互图 | LangGraph (32), Hive (10) | 复杂的、条件分支多的任务 |

**Anthropic 的 Planner-Generator-Evaluator 三 Agent 架构**（GAN 启发）：

```
Planner ──→ Generator ──→ Evaluator
   ↑            ↑              │
   └──────── Sprint Contract ───┘
              (重规划)
```

关键发现：升级到 Opus 4.6 后，**移除** sprint 构造和 context resets，成本 $200 → $125，质量不变——证明 Harness 复杂度和模型能力负相关。

### 2.3 Level 3: Full Lifecycle Pipeline（完整生命周期）

| 维度 | 详情 |
|------|------|
| 核心抽象 | **Task Runner** — 管理调度、状态持久化、重试、验证、迭代 |
| 代表系统 | Symphony (OpenAI, 24k), Vibe Kanban (26k), GitHub Agentic Workflows (5k) |
| 典型工作流 | Issue/Task → 规划 → 代码/工件生成 → 测试验证 → Review → PR 接受 |
| 人类角色 | **Steering（指导）而非 Executing（执行）** |

**Symphony（OpenAI 2026）的设计原则**：
- Issue Tracker 作为控制平面
- Repository 作为任务状态的持久化锚点
- Agent 围绕 Git 工作流组织，而非替代它

---

## 3. 生命周期状态管理

论文**严格区分**三类状态：

| 状态类型 | 层次 | 示例 | 维护者 |
|----------|------|------|--------|
| **Context/Memory** (§5) | 推理级 | 对话历史、检索文档、记忆 | 上下文层 |
| **Lifecycle State** (§6) | 操作级 | 待处理子任务、检查点、重试计数、共享工件、执行状态 | 编排层 |
| **Observability** (§7) | 监控级 | Trace、Span、Token 计数、延迟、成本 | 可观测层 |

**Lifecycle State 是 Harness 自身用来继续执行的操作状态**——它独立于"Agent 推理时看到什么"和"外部观察到什么"。

---

## 4. Anthropic 长期 Agent 的四大故障模式

从 Anthropic (2025d, 2026c) 的生产经验中提炼：

| 故障模式 | 表现 | Harness 级解决方案 |
|----------|------|-------------------|
| **One-Shot 尝试** | Agent 试图一次性完成整个任务 | Initializer Agent 拆解任务为特性列表 |
| **过早宣布完成** | Agent 声称完成但实际未完成 | Separated Evaluator（独立的评估 Agent） |
| **Session 间环境破碎** | 新 Session 开始时环境不可用 | Clean Handoff State（干净的交接状态）+ git repo checks |
| **标记完成但无测试** | 声称实现但未运行测试 | 自动化测试作为 Agent 流程的硬性门禁 |

---

## 5. 多 Agent 系统中的故障传播

**AgentErrorTaxonomy**（Zhu et al., 2025）的核心发现：
- **错误传播（Error Propagation）是核心可靠性瓶颈**
- 失败按模块分解：记忆错误 → 反思错误 → 规划错误 → 行动错误 → 系统错误 → 级联
- AgentDebug 框架：隔离根因而非治疗表面症状，相对任务成功率提升 26%

**MAST**（Cemri et al., 2025）：14 种多 Agent 故障模式（κ=0.88），聚类为三类：
1. 系统设计问题
2. Agent 间不对齐
3. 任务验证问题

---

## 6. 设计原则

1. **编排可靠性 = 状态管理 + 恢复机制**——不仅仅靠"好的提示词"
2. **Human-in-the-loop 位置应在关键决策点，而非每一步**
3. **Harness 复杂度应随模型能力自适应**——模型变强时主动移除不必要的脚手架
4. **Durable Progress Artifacts**：确保 Agent 的进展以可恢复的工件形式持久化（Git repo、进度文件、初始化脚本）
5. **Clean Handoff**：Agent 在 Session 间交接时应留下"干净的状态"，让下一 Session 的 Agent 可以无摩擦继续
