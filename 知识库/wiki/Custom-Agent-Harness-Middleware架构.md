---
type: concept
title: "Custom Agent Harness — Middleware 架构"
sources:
  - "sources/web/langchain/custom-agent-harness-精读.md"
  - "https://www.langchain.com/blog/how-to-build-a-custom-agent-harness"
tags:
  - "agent-infra"
  - "agent-harness"
  - "middleware"
  - "langchain"
created: 2026-06-19
updated: 2026-06-19
status: draft
related: []
---

# Custom Agent Harness — Middleware 架构

## 核心公式

> **agent = model + harness**

Harness 的职责是在每一步为模型提供正确的上下文。

## create_agent 哲学

最小化 Agent Loop（类比 [Pi.dev](https://pi.dev/) 的配置驱动编码 Agent Harness），只实现核心循环，通过 **Middleware** 暴露扩展点。

## Middleware 四杠杆

| 杠杆 | 注入点 | 用途 |
|------|--------|------|
| **Deterministic Logic** | before/after model, before/after tool | 策略执行、动态模型切换、compaction 后消息更新 |
| **Tools** | 全生命周期（init → register → teardown） | 工具管理独立于 agent 定义 |
| **Custom State** | 跨 hook 持久化 | 计数器、标志位等跨步状态 |
| **Stream Handlers** | 输出流拦截/转换 | UI 消费 token、审计日志、监控 |

## Harness 能力 → Middleware 映射

| 能力 | Middleware |
|------|-----------|
| 防上下文溢出 | `SummarizationMiddleware`, `ContextEditingMiddleware` |
| 记忆存取 | `FilesystemMiddleware`, `MemoryMiddleware`, `SkillsMiddleware` |
| 环境执行 | `ShellToolMiddleware`, `CodeInterpreterMiddleware` |
| 子任务委托 | `SubAgentMiddleware`, `TodoListMiddleware` |
| 容错兜底 | `ToolRetryMiddleware`, `ModelRetryMiddleware`, `ModelFallbackMiddleware` |
| 策略执行 | `PIIMiddleware`, `HumanInTheLoopMiddleware` |
| 成本控制 | `ModelCallLimitMiddleware`, `PromptCachingMiddleware` |

## 关键 Insight

> 最好的 Agent 不是用最强模型构建的，而是用**最贴合任务的 harness** 构建的。Middleware 让可组合、可复用的策略单元成为可能。
