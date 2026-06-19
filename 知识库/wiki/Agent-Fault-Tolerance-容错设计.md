---
type: concept
title: "Agent Fault Tolerance — 容错设计"
sources:
  - "sources/web/langchain/fault-tolerance-in-langgraph-精读.md"
  - "https://www.langchain.com/blog/fault-tolerance-in-langgraph"
tags:
  - "agent-infra"
  - "agent-harness"
  - "fault-tolerance"
  - "langgraph"
created: 2026-06-19
updated: 2026-06-19
status: draft
related: []
---

# Agent Fault Tolerance — 容错设计

## 问题

Agent 生产环境遭遇原型不会遇到的错误：网络失败、工具调用异常、LLM 限流。LangGraph 提供三个容错原语，绑定到节点定义旁。

## 三个原语

| 原语 | 作用 | 关键参数 |
|------|------|----------|
| **RetryPolicy** | 自动重试 + exponential backoff + jitter | `max_attempts`, `backoff_factor`, `retry_on`（异常类型/callable） |
| **TimeoutPolicy** | 硬超时（run_timeout）/ 空闲超时（idle_timeout） | `run_timeout`, `idle_timeout`, `refresh_on` |
| **error_handler** | 重试耗尽后的补偿逻辑 | 接收 `(state, NodeError)` → 返回新 state |

## error_handler 特征

- **仅在重试全部失败后触发**（不拦截每次异常）
- **失败上下文注入**：`error.node` + `error.error`
- **原子性过渡**：原节点 ERROR write 已 checkpoint，handler 在同 superstep 调度
- **不可嵌套**：handler 本身不能再设 handler

## SAGA 模式

以航班预订为例：
1. reserve_seat → 2. process_payment → 3. issue_ticket
- 通过 `completed` 列表追踪已执行步骤
- 任一步重试耗尽 → compensate 反向回滚
- 保持 **all-or-nothing** 语义

## 关键 Insight

> 错误处理的真正价值不在重试，而在**重试耗尽后的补偿逻辑**——这是生产 Agent 与原型分道扬镳的分水岭。
