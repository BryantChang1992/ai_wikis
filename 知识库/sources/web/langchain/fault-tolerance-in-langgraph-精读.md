# Retries, Timeouts and Error Handlers: Fault Tolerance in LangGraph — 精读分析

- **URL**: https://www.langchain.com/blog/fault-tolerance-in-langgraph
- **来源**: LangChain Blog
- **发布日期**: 2026-06 (约)
- **精读日期**: 2026-06-19

---

## 1. 问题定义

> "写 happy path 很容易。让它在生产中活下来的错误处理样板代码（重试/超时/回退）常比业务逻辑本身更长。"

生产 Agent 面临的三类故障：
- **瞬态故障**：LLM 5xx、向量库连接重置、HTTP 服务短暂不可用 → "等几秒再说，应该就好了"
- **超时**：卡住的 HTTP 调用或冻结子进程会无限期挂起图执行
- **不可恢复错误**：所有重试耗尽后仍需运行的补偿逻辑

---

## 2. 三大原语

### 2.1 RetryPolicy

```python
RetryPolicy(
    initial_interval=0.5,   # 初始等待
    backoff_factor=2.0,     # 指数退避因子
    max_interval=128.0,     # 退避上限
    max_attempts=3,         # 最大重试次数
    jitter=True,            # 退避时间添加随机
    retry_on=(ConnectionError, TimeoutError),
)
```

**默认策略**（故意保守）：
- 重试：ConnectionError、5xx 来自 httpx/requests、少数通用瞬态类别
- 不重试：ValueError、TypeError、RuntimeError——这些几乎总是程序 bug，不是瞬态故障

`retry_on` 可以是：
1. 异常类型集合（简单）
2. 可调用函数——检查运行时的错误特征以判断是否匹配重试条件

### 2.2 TimeoutPolicy

```python
TimeoutPolicy(
    run_timeout=30.0,         # 硬墙钟时间上限
    idle_timeout=5.0,         # 无进度信号的最大等待时间
    refresh_on="auto"         # 或 "heartbeat" 模式
)
```

**两种超时**：
- `run_timeout`：硬上限。不关心是否还有进展——超时就停
- `idle_timeout`：智能。每个"进展"信号会重置——channel writes、streaming chunks（LangChain LLM 模型自动 emit）、子任务事件、回调事件。**长时间运行但活跃流出的工作不会触发**，但真正卡住的会

**Heartbeat 模式**：如果自己控制工作并想 emit 自己的进展信号→切换为 `refresh_on="heartbeat"` → 显式调用 `runtime.heartbeat()`

### 2.3 Error Handler

```python
def on_call_llm_failed(state: State, error: NodeError) -> State:
    log.error("call_llm failed after retries: %s", error.error)
    return {"status": "llm_unavailable"}

.add_node(
    "call_llm",
    call_llm,
    retry_policy=RetryPolicy(max_attempts=4),
    error_handler=on_call_llm_failed,
)
```

**关键设计特性**：
1. **仅重试耗尽后触发**——这是让功能真正有用的属性。若想每次异常都运行→直接 try/except
2. **失败上下文注入**：handler 通过 `NodeError` 参数获取失败节点名 + 异常
3. **原子转换**：节点失败时，ERROR 写入提交到 checkpoint，handler 作为 **新任务在同一 step 中**调度。宿主进程在 handler 中途崩溃→下次恢复时**重新调度 handler**，非原始失败节点
4. **Handler 不允许再设 error handler**：防止无限递归

---

## 3. SAGA 模式：航班预订案例

### 3.1 问题

```
reserve_seat → process_payment → issue_ticket
     ✓              ✗（重试耗尽）
```

naive 方案（整个流程重试）在第一第二步骤完成后失效——座位已预定，付款失败后座位卡在中间状态。需要每步独立重试，且重试耗尽后**仅回滚已完成步骤**。

### 3.2 SAGA 模式实现

核心思想：补偿操作（undo）仅针对实际完成的步骤，按**逆序**执行。

```python
def compensate(state) -> Command:
    if "issue_ticket" in state["completed"]:
        void_ticket(state)
    if "process_payment" in state["completed"]:
        refund_payment(state)
    if "reserve_seat" in state["completed"]:
        release_seat(state)
    return Command(goto=END)
```

**架构**：
```
所有步骤共享同一 RetryPolicy + error_handler:
  .set_node_defaults(retry_policy=RETRYABLE, error_handler=to_compensate)
  → "reserve_seat" → "process_payment" → "issue_ticket"
  → 任一步重试耗尽 → 原子转换到 compensate
```

**收益**：
- 每步独立 backoff 重试
- 重试耗尽后**原子转换**到 compensate
- 持久状态追踪哪些步骤已完成，compensate 仅回滚需要的

---

## 4. 与 Agent 自主性的关系

Agent 正在承担更多自主权→执行高后果、难以逆转的动作（预订航班、生成票据、执行付款、调用内部服务）→ 可靠性要求从"demo 的 1% 故障率可接受"变为"生产 Agent 几十步→后果叠加→不可接受"。

### 4.1 故障容错层级

| 层级 | 原语 | Agent 类型需求 |
|------|------|--------------|
| 瞬态 → 自动恢复 | RetryPolicy + TimeoutPolicy | 所有生产 Agent 需要 |
| 超过重试上限 → 有序降级 | Error Handler + 补偿逻辑 | 有副作用的工作流 |
| 资源耗尽 → 主动回滚 | SAGA 补偿 | 分布式事务 Agent |

---

## 5. 与 CHANG_AI_TEAM 的关系

- **[[Agent-Fault-Tolerance-容错设计]]**：本文是 Wiki 卡片的主要 source
- **[[Custom-Agent-Harness-Middleware架构]]**：ToolRetryMiddleware / ModelRetryMiddleware 是 Harness 层面实现重试的位置
  - LangGraph 的重试在**图节点层面**（node retry）——更底层
  - LangChain Middleware 的重试在**loop 钩子层面**（before/after model/tool）——更高层
  - 两者互补：节点层的重试适用于瞬态网络故障；loop 层的 fallback 适用于模型不可用

---

## 6. 工程启示

1. **重试的"默认保守"规则是好设计**：瞬态故障重试，代码 bug 不重试。这避免了深层架构错误被重试层层放大
2. **Timeout ≠ 简单超时**：`idle_timeout` + 进展信号是更智能的超时形式——长运行但活跃的进程不应被杀死
3. **Error Handler 的原子性支持是关键**：崩溃恢复时重调度 handler（而非原始节点）保证了补偿逻辑的一致性
4. **SAGA 模式在 Agent 工作流中是普遍需求**：任何分步执行且步骤有副作用的 Agent 都需要 SAGA——不是特例
