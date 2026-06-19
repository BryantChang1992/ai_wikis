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
related:
  - "[[Loop-Engineering-多层Agent循环架构]]"
  - "[[Custom-Agent-Harness-Middleware架构]]"
  - "[[Agent-Cost-Control-Gateway成本控制]]"
  - "[[Agent-First-Data-Systems]]"
  - "[[流处理容错模型]]"
  - "[[AI-Infra-Agent基础设施体系综述]]"
---

# Agent Fault Tolerance — 容错设计

LangGraph 的容错体系围绕三个原语构建：**RetryPolicy**、**TimeoutPolicy**、**error_handler**。核心理念：**错误处理的价值不在重试本身，而在重试耗尽后的补偿逻辑**——这是生产级 Agent 与原型的分水岭。

## 三个容错原语

### RetryPolicy — 自动重试

| 参数 | 说明 |
|------|------|
| `max_attempts` | 最大重试次数 |
| `backoff_factor` | 指数退避乘数 |
| `retry_on` | 可调用 / 异常元组，决定哪些异常触发重试 |

内置 jitter 机制避免重试风暴。重试间隔 = `backoff_factor * 2^attempt + random(0, 1)`。

### TimeoutPolicy — 超时控制

两维度：
- **`run_timeout`**：硬超时——节点执行超过 N 秒即终止
- **`idle_timeout`**：空闲超时——基于 heartbeat，无活动超过 N 秒即触发

两者可同时使用，任一先触发即中断。

### error_handler — 补偿逻辑

**关键行为**：
- **仅在重试全部失败后触发**（不拦截每次异常，只拦截"重试耗尽"这个事件）
- **失败上下文注入**：`error.node`（哪个节点失败）+ `error.error`（原始异常对象），handler 可基于此做细粒度补偿
- **原子性过渡**：原节点 ERROR write 已 checkpoint，handler 在同一 superstep 调度
- **不可叠加**：handler 中再抛异常不会触发新 handler（防无限递归）

## SAGA 模式

以航班预订为例展示了完整的补偿工作流：

```
reserve_seat → process_payment → issue_ticket
        ↓ 重试耗尽
    compensate：
        undo process_payment（退款）
        undo reserve_seat（释放座位）
```

实现方式：维护 `completed` 列表追踪已执行步骤 → 反向回滚。这是 **分布式事务 SAGA 模式在 Agent 工作流中的直接映射**。

## 与相关领域交叉

### 与 [[Loop-Engineering-多层Agent循环架构]] 的关系

容错是循环工程的安全网。多层 Agent 循环中，每一层都需要独立的容错策略——外层循环的 Timeout 应大于内层所有节点超时之和，否则会出现"外层先超时杀死了一个正在重试的内层节点"的竞态。

### 与 [[流处理容错模型]] 的类比

Agent 容错的 SAGA 补偿模式与流处理中的 exactly-once 语义本质上是同一类问题：**部分成功 → 需要补偿 or 幂等重放**。区别在于 Agent 的副作用不限于数据（可能发过消息、改过配置），补偿逻辑更复杂。

### 在 [[Custom-Agent-Harness-Middleware架构]] 中的位置

容错原语是 Harness Middleware 中最关键的一层——在模型调用和工具调用之间插入 retry/timeout/compensate 逻辑。LangGraph 的原语设计可以直接作为 Middleware 层的容错模块参考。

### 与 [[Agent-Cost-Control-Gateway成本控制]] 的联动

重试是成本放大的倍增器——每次 retry 都产生新的 token 消耗。Gateway 层需要在成本控制中审计重试开销，区分"有效重试"与"注定失败的浪费调用"。

## 生产实践要点

1. **重试策略必须可审计**：每次 retry 的 attempt 序号、间隔、结果都要打入 trace
2. **idle_timeout 是发现挂死的关键**：Agent 最常见故障不是报错而是静默挂起
3. **error_handler 的测试成本很高**：需要构造"重试全部耗尽"的场景，建议用 fault-inject 工具
4. **SAGA 补偿的幂等性**：undo 操作要设计成可重复执行而不产生副作用的

## 系统关系

- **上游**：Agent 循环（[[Loop-Engineering-多层Agent循环架构]]）中的节点执行
- **控制面**：Harness Middleware（[[Custom-Agent-Harness-Middleware架构]]）的容错层
- **旁路**：成本控制（[[Agent-Cost-Control-Gateway成本控制]]）审计重试开销
- **理论基础**：SAGA 补偿模式 ← [[流处理容错模型]] 的 exactly-once 思路
