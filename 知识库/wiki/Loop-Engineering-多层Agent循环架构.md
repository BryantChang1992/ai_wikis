---
type: concept
title: "Loop Engineering — 多层 Agent 循环架构"
sources:
  - "sources/web/langchain/the-art-of-loop-engineering-精读.md"
  - "https://www.langchain.com/blog/the-art-of-loop-engineering"
tags:
  - "agent-infra"
  - "agent-harness"
  - "loop-engineering"
  - "langchain"
created: 2026-06-19
updated: 2026-06-19
status: draft
related:
  - "[[Custom-Agent-Harness-Middleware架构]]"
  - "[[Agent-Fault-Tolerance-容错设计]]"
  - "[[Agent-Cost-Control-Gateway成本控制]]"
  - "[[Agent-First-Data-Systems]]"
---

# Loop Engineering — 多层 Agent 循环架构

LangChain 提出 Agent 不是模型 + tool loop 这么简单，而是**多层循环的叠加**（"loopcraft"）。Satya Nadella 的判断：**早期建立学习循环的公司（人类判断 + token capital 复合），将建立难以复制的优势**。

## 四层循环架构

| 层 | 名称 | 作用 | LangChain 原语 | 人类参与 |
|----|------|------|----------------|----------|
| **L1** | Agent Loop | 模型反复调用工具直到完成任务 | `create_agent` | 敏感操作审批 |
| **L2** | Verification Loop | 输出质量校验 + 失败反馈重试 | `RubricMiddleware`, `after_agent` hook | 人类做 grader |
| **L3** | Event-Driven Loop | 事件触发 Agent 运行 | LangSmith Deployment, Fleet | 配置触发规则 |
| **L4** | Hill Climbing Loop | 分析生产 trace → 自动优化 harness 配置 | LangSmith Engine | 审查改动的 prompt/tool 配置 |

## 层间关系

```
L4 (Hill Climbing)
  │ 分析 L1-L3 的 trace，产出优化建议
  │ 返回值箭头穿透 L3 → 修改 L1-L2 的 prompt/tool 配置
  ▼
L3 (Event-Driven)
  │ cron/webhook/消息 → 触发 L2
  ▼
L2 (Verification)
  │ 校验 L1 的输出 → 失败 → 反馈给 L1 → L1 重试
  ▼
L1 (Agent Loop)
  │ 模型 ↔ 工具循环 → 产出
```

**关键递进**：L1 自动化工作 / L2 保证质量 / L3 规模化 / L4 自我进化。

## 四层的演进逻辑

### L1 → L2：从"能跑"到"跑得对"

单 Agent Loop 能完成任务但不可靠。Verification Loop 引入质检环节——输出先过 grader（可以是 LLM as judge 或规则引擎），不合格则把 grader 的评论写回 agent prompt 让 L1 重试。

### L2 → L3：从"单次"到"持续"

单个 Agent 运行是离散的，但业务场景需要持续运作。Event-Driven Loop 通过 cron、webhook、消息队列让 Agent 从"被调用"变为"持续监听"。这是从工具到服务的跨越。

### L3 → L4：从"运维"到"进化"

生产 Agent 运行产生的 trace 数据是优化燃料。Hill Climbing Loop 分析 trace 中的成功/失败模式，自动调整 prompt 策略和 tool 配置。**L4 的返回值穿透到 L1-L3 内部——这不是简单的配置调整，而是 Agent 的自我进化**。

## 与 [[Custom-Agent-Harness-Middleware架构]] 的关系

Loop Engineering 和 Middleware Harness 是正交互补：

| 维度 | Loop Engineering | Middleware Harness |
|------|-----------------|-------------------|
| 关注点 | 循环层级怎么设计 | 每一步注入什么逻辑 |
| 抽象层次 | 架构结构（骨骼） | 执行策略（肌肉） |
| 关系 | 循环定义结构 | Middleware 在结构上注入行为 |

L1 的 Agent Loop 正是 Middleware Hook 附着的地方——`before_model` / `after_model` 等注入点都在 L1 循环内。

## 与成本控制的交叉

Agent 循环层数越深，单任务 token 消耗指数增长。[[Agent-Cost-Control-Gateway成本控制]] 需要感知循环层级——L4 的 hill climbing 本身也在消耗 token，需要纳入成本模型。

## 与容错的关系

每一层循环都需要独立的容错策略。[[Agent-Fault-Tolerance-容错设计]] 的 retry/timeout/error_handler 在每一层有不同的参数：L1 的 timeout 应小于 L2，否则 L2 可能在等待 L1 时先超时，产生竞态。
