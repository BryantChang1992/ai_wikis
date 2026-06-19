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
related: []
---

# Loop Engineering — 多层 Agent 循环架构

## Loopcraft 理念

Agent 不只是 model + tool loop，而是**多层循环的叠加**。核心命题：每层循环解决一类问题，外层循环使内层更有效。

## 四层循环架构

| 层 | 作用 | 原语 |
|----|------|------|
| **L1: Agent Loop** | 模型反复调用工具直至完成 | `create_agent` |
| **L2: Verification Loop** | 输出质量校验 + 失败反馈重试 | `RubricMiddleware` |
| **L3: Event-Driven Loop** | 事件触发自动运行（cron/webhook/message） | LangSmith Deployment, Fleet |
| **L4: Hill Climbing Loop** | 分析 trace → 自动优化 harness config | LangSmith Engine |

## 递进逻辑

- L1 自动化**单个任务**
- L2 保证**质量与一致性**（代价：延迟 ↑ 成本 ↑）
- L3 连接 Agent 到**生态系统**（不再是手动调用）
- L4 产出**自我进化**：trace → 分析 → prompt/tool 改进 → 回到 L1

## L4 的特殊性

L4 的返回值**穿透到内部**，修改 L1-L3 的配置。对人类：人类判断在 L2 grading 和 L1 敏感动作审批中保留。

## 关键 Insight

> Satya Nadella 判断：早期建立学习循环的公司（人类判断 + token capital 复合），将建立难以复制的优势。Agent 的潜力不在模型，而在围绕它的循环系统。
