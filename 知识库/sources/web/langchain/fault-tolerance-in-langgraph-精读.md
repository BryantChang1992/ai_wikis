# Fault Tolerance in LangGraph: Retries, Timeouts and Error Handlers

- **URL**: https://www.langchain.com/blog/fault-tolerance-in-langgraph
- **来源**: LangChain Blog
- **日期**: 2026-06 (约)

## 核心主题

Agent 在实际运行中遭遇的错误（网络、工具调用失败、LLM 限流），LangGraph 提供了三个容错原语。

### 三个原语

| 原语 | 作用 | 配置 |
|------|------|------|
| **RetryPolicy** | 自动重试 + exponential backoff + jitter | `max_attempts`, `backoff_factor`, `retry_on` (callable/tuple) |
| **TimeoutPolicy** | 硬超时 / 空闲超时 | `run_timeout`, `idle_timeout` (基于 heartbeat) |
| **error_handler** | 重试耗尽后的补偿逻辑（清理/告警/降级） | 接收 `(state, NodeError)` → 返回新 state |

### 重试耗尽后的错误处理特征

- **仅在重试全部失败后触发**（不拦截每次异常）
- **失败上下文注入**（`error.node` / `error.error`）
- **原子性过渡**：原节点 ERROR write 已 checkpoint，handler 在同 superstep 调度
- Handler 不可叠加（防止无限递归）

### SAGA 模式

以航班预订为例展示了补偿逻辑：
- reserve_seat → process_payment → issue_ticket
- 任一步骤重试耗尽 → compensate undo 已执行的副作用
- 通过 `completed` 列表追踪，反向回滚

## 关键 Insight

错误处理的真正价值不在重试，而在**重试耗尽后的补偿逻辑**——这才是生产级 Agent 与原型分道扬镳的地方。
