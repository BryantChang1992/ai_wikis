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
related:
  - "[[Loop-Engineering-多层Agent循环架构]]"
  - "[[Agent-Fault-Tolerance-容错设计]]"
  - "[[Agent-Cost-Control-Gateway成本控制]]"
  - "[[Model-Neutrality-模型中立与反锁定]]"
  - "[[Agentic-Memory-语义缓存]]"
  - "[[Agent-Sandbox-安全沙箱选型]]"
  - "[[AI-Infra-Agent基础设施体系综述]]"
---

# Custom Agent Harness — Middleware 架构

LangChain 的 `create_agent` 设计理念：**`agent = model + harness`**。Harness 的职责不是在模型层面做优化，而是**在每一步为模型提供正确的上下文**。Middleware 是实现 harness 可组合性的核心机制。

## 核心 Agent Loop

```
startup → [before_model → model_call → after_model → before_tool → tool_call → after_tool] × N → teardown
               └────────────────── Middleware hook points ───────────────────────┘
```

`create_agent` 是最小化核心 Loop，所有逻辑通过 middleware hook 注入。

## Middleware 四杠杆

| 杠杆 | 用途 | 典型场景 |
|------|------|----------|
| **Deterministic Logic** | 商业规则、策略执行、动态模型切换 | post-compaction 消息历史更新、合规检查 |
| **Tools** | 工具全生命周期管理（注册/初始化/清理），独立于 agent 定义 | 运行时工具注入、环境依赖初始化 |
| **Custom State** | 跨 hook 共享状态（计数器、标志位） | 工具调用次数计数器、故障模式追踪 |
| **Stream Handlers** | 拦截/转换输出流，分发给 UI/审计/监控 | 实时 token 计数、敏感词过滤 |

## 能力 → Middleware 映射

这是一个完整的能力到 Middleware 的 1:1 映射，每个能力有独立 middleware：

| 能力域 | Middleware | 对应知识库概念 |
|--------|-----------|---------------|
| 防上下文溢出 | `SummarizationMiddleware`, `ContextEditingMiddleware` | [[Loop-Engineering-多层Agent循环架构]] |
| 记忆存取 | `FilesystemMiddleware`, `MemoryMiddleware`, `SkillsMiddleware` | [[Agentic-Memory-语义缓存]] |
| 环境执行 | `ShellToolMiddleware`, `CodeInterpreterMiddleware` | [[Agent-Sandbox-安全沙箱选型]] |
| 子任务委托 | `SubAgentMiddleware`, `TodoListMiddleware` | [[Agent-First-Data-Systems]] |
| 容错 | `ToolRetryMiddleware`, `ModelRetryMiddleware`, `ModelFallbackMiddleware` | [[Agent-Fault-Tolerance-容错设计]] |
| 策略执行 | `PIIMiddleware`, `HumanInTheLoopMiddleware` | [[Anthropic-Agent安全容器化实践]] |
| 成本控制 | `ModelCallLimitMiddleware`, `ToolCallLimitMiddleware`, `PromptCachingMiddleware` | [[Agent-Cost-Control-Gateway成本控制]] |

## 设计哲学

**最好的 Agent 不是用最强模型构建的，而是用最贴合任务的 harness 构建的。**

Middleware 的价值在于**可组合性**：
- 每个 middleware 是独立、可复用、可测试的策略单元
- 组合多个 middleware 不增加耦合，因为 hook 是顺序执行
- 新增能力 = 新增一个 middleware，不需要改 agent core

## 与 [[Model-Neutrality-模型中立与反锁定]] 的关联

Middleware 架构是模型中立的天然载体。`ModelFallbackMiddleware` + `DynamicModelSwitching` 在 middleware 层实现模型路由，而不是在 Agent 代码中硬编码模型品牌。这使得从模型 A 切换到模型 B 是配置变更而非代码变更。

## 与 [[Loop-Engineering-多层Agent循环架构]] 的区别

| 维度 | Loop Engineering | Middleware Harness |
|------|-----------------|-------------------|
| 关注点 | 循环层级怎么设计（外循环/内循环/子循环） | 每一步执行前后注入什么逻辑 |
| 抽象层次 | 架构结构 | 执行策略 |
| 关系 | 循环定义结构 | Middleware 在结构上注入行为 |

两者是正交互补关系——Loop 定义 Agent 的骨骼，Middleware 定义 Agent 的肌肉。

## 系统关系全景

```
                     Agent Core Loop
                          │
    ┌─────────────────────┼─────────────────────┐
    │                     │                     │
    ▼                     ▼                     ▼
 容错层                 记忆层                安全层
 (retry/timeout)     (memory/cache)        (sandbox/approval)
 [[Agent-Fault-Tol...]] [[Agentic-Memory...]] [[Agent-Sandbox...]]
    │                     │                     │
    └─────────────────────┼─────────────────────┘
                          ▼
                    成本控制层
                    (limit/cache/meter)
               [[Agent-Cost-Control-Gateway...]]
                          │
                          ▼
                    模型路由层
                    (fallback/switch)
               [[Model-Neutrality...]]
```
