---
type: analysis
title: "Agent Cost Control — Gateway 成本控制"
sources:
  - "sources/web/langchain/coding-agent-spend-精读.md"
  - "https://www.langchain.com/blog/how-we-made-coding-agent-spend-predictable"
tags:
  - "agent-infra"
  - "cost-control"
  - "llm-gateway"
  - "observability"
created: 2026-06-19
updated: 2026-06-19
status: draft
related: []
---

# Agent Cost Control — Gateway 成本控制

## 动机

LangChain 的 AI 支出从可控到失控的三重驱动：
1. 少数团队 → 全公司使用 AI
2. 最好模型越来越贵
3. Agent 可在单任务中触发数十次模型调用

一个重度使用 coding agent 的开发者**周消费可达数千美元**，没有实时可见性。

## LLM Gateway 方案

| 预算维度 | 时间窗口 |
|----------|----------|
| 组织 / 工作空间 / 用户 / API Key | 月 / 周 / 天 / 小时 |

所有 coding agent 调用（Claude Code / Codex / Deep Agents）集中通过 Gateway 路由 → 工程领导获得**按分钟的消费视图**。

成本数据关联到 agent、trace、故障模式，而非仅为月末账单。

## Dogfood 三教训

1. **模型计价比静态表复杂**：caching、token 分级、频繁调价 → 定价需系统化维护
2. **不是所有客户端都能路由**：Cursor 只暴露 base-url swap（Chat only），Claude Desktop 需 managed config → 需测量 Gateway 覆盖差量
3. **硬限制离不开工作流**：工程师要求提前预警 + 快速、可审计的提额流程

## 关键 Insight

> 成本可观测性需**分钟级**，不是月末看账单。预算控制保护业务而不阻断工作，才是好的成本治理。
