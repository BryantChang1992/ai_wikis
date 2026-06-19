# How to Build a Custom Agent Harness

- **URL**: https://www.langchain.com/blog/how-to-build-a-custom-agent-harness
- **来源**: LangChain Blog, Sydney Runkle
- **日期**: 2026-06-03

## 核心论点

`agent = model + harness`，harness 的职责是在每一步为模型提供正确的上下文。

### Middleware 架构

`create_agent` 是最小化核心 Agent Loop，middleware 在 loop 每一步注入逻辑：

- `before_model` / `after_model`
- `before_tool` / `after_tool`
- `startup` / `teardown`

### Middleware 四杠杆

| 杠杆 | 用途 |
|------|------|
| **Deterministic Logic** | 商业逻辑、策略执行、动态模型切换、post-compaction 消息历史更新 |
| **Tools** | 工具全生命周期管理（注册/初始化/清理），独立于 agent 定义 |
| **Custom State** | 跨 hook 共享状态（计数器、标志位） |
| **Stream Handlers** | 拦截/转换输出流，分发给 UI/审计/监控 |

### Harness 能力映射

| 能力 | Middleware |
|------|-----------|
| 防上下文溢出 | `SummarizationMiddleware`, `ContextEditingMiddleware` |
| 记忆存取 | `FilesystemMiddleware`, `MemoryMiddleware`, `SkillsMiddleware` |
| 环境执行 | `ShellToolMiddleware`, `CodeInterpreterMiddleware` |
| 子任务委托 | `SubAgentMiddleware`, `TodoListMiddleware` |
| 容错 | `ToolRetryMiddleware`, `ModelRetryMiddleware`, `ModelFallbackMiddleware` |
| 策略执行 | `PIIMiddleware`, `HumanInTheLoopMiddleware` |
| 成本控制 | `ModelCallLimitMiddleware`, `ToolCallLimitMiddleware`, `PromptCachingMiddleware` |

## 关键 Insight

最好的 Agent 不是用最强模型构建的，而是用**最贴合任务的 harness** 构建的。Middleware 让可组合、可复用的策略单元成为可能。
