# How to Build a Custom Agent Harness — 精读分析

- **URL**: https://www.langchain.com/blog/how-to-build-a-custom-agent-harness
- **作者**: Sydney Runkle, LangChain
- **发布日期**: 2026-06-03
- **精读日期**: 2026-06-19

---

## 1. 核心公式

```
agent = model + harness
```

Harness 的职责：**在每一步为模型提供正确的上下文**。不是给模型好的 system prompt——是确保到达模型的上下文是准确、完整、良好的。

---

## 2. create_agent 的设计哲学

**最小化的核心 Agent Loop**，不是全栈框架。对标 Pi（高度可配置的 coding agent harness）。

### 2.1 与其他 harness 的对比

| Harness | 设计理念 | 优点 | 局限 |
|------|----------|------|------|
| Deep Agents | 预组装 opinionated middleware 栈 | 开箱即用，快速上生产 | 定制有上限 |
| Claude Agent SDK | Anthropic 原生集成，sandbox 深度整合 | 模型层优化，安全强 | 锁定 Anthropic 生态 |
| **create_agent** | 仅 core agent loop + middleware 原语 | 最大可定制性 | 需自行组装 middleware |

### 2.2 Middleware 六钩子

```
startup → before_model → after_model → before_tool → after_tool → teardown
```

每个 middleware 在每个钩子上处理一个关注点，自由组合：

```python
agent = create_agent(
    model="anthropic:claude-sonnet-4-6",
    tools=tools,
    system_prompt="you are a helpful assistant...",
    middleware=[...]  # 栈式组合
)
```

---

## 3. Middleware 四杠杆

### 3.1 Deterministic Logic（确定性逻辑）

- 业务逻辑、策略执行、动态 agent 控制
- **动态模型切换**：根据任务复杂度选模型
- **Prompt 调整**、**compaction 后的消息历史更新**
- 适合理由：不能（或不应该）放在 prompt 中的逻辑

### 3.2 Tools（工具生命周期管理）

不是直接在 agent 上注册工具——middleware 处理完整生命周期：
- **Setup**：初始化/依赖注入/配置
- **Teardown**：运行结束时干净清理
- **注册**：交给 agent 干净工具集

**为什么重要**：工具配置靠近治理逻辑，而非散落在 agent 定义各处。

### 3.3 Custom State（自定义状态）

Middleware 可扩展 agent 状态，跨钩子追踪：计数器、标记、跨运行持久化值。在钩子间共享数据。

### 3.4 Stream Handlers（流处理器）

拦截和转换 agent 输出流——过滤事件、注入元数据、路由不同事件类型到不同消费者：
- UI 消费 token delta
- 审计日志捕获 tool call
- 监控系统追踪延迟

---

## 4. Harness Capability → Middleware 映射

| 能力 | Middleware | 关键设计考量 |
|------|-----------|------------|
| 防上下文溢出 | SummarizationMiddleware, ContextEditingMiddleware | 摘要漂移风险：低频关键信息在多轮摘要后消失 |
| 内存管理 | FilesystemMiddleware, MemoryMiddleware, SkillsMiddleware | 启动时加载相关知识，结束时写回→从真实使用中逐步改进 |
| 环境动作 | ShellToolMiddleware, FilesystemMiddleware, CodeInterpreterMiddleware | 工具集过大增加安全面；过小限制创造力 |
| 任务委托 | SubAgentMiddleware, AsyncSubAgentMiddleware, TodoListMiddleware | Sub-agent 有干净上下文窗口→处理复杂子任务 |
| 故障恢复 | ToolRetryMiddleware, ModelRetryMiddleware, ModelFallbackMiddleware | Backoff + fallback 是生产底线，非可选 |
| 策略执行 | PIIMiddleware, HumanInTheLoopMiddleware | 每通 call 必须触发，不管模型做什么——不能放 prompt |
| 行为控制 | HumanInTheLoopMiddleware | 对高风险动作（金融交易/DB 操作）暂停等批准 |
| 成本控制 | ModelCallLimitMiddleware, ToolCallLimitMiddleware, PromptCachingMiddleware | Call 限制从源头防止 runaway 成本 |

---

## 5. Task-Harness Fit

核心论点：**最好的 Agent 不是用最强模型构建的，而是用最贴合任务需求的 harness 构建的。**

### 5.1 不同场景的不同 middleware 栈

| 场景 | 核心需求 | Middleware 组合 |
|------|---------|----------------|
| 客服 Agent | 合规、低延迟、策略一致性 | PIIMiddleware + HumanInTheLoopMiddleware + PromptCachingMiddleware |
| Coding Agent | 文件系统、Shell、长时运行 | FilesystemMiddleware + ShellToolMiddleware + SubAgentMiddleware + SummarizationMiddleware |
| GTM Agent | API 集成、数据查询、HR 集成 | 自定义 middleware（SDK 查询 + CRM 集成） |
| Async Coding Agent | 完全自主、长时间运行、需求可能模糊 | AsyncSubAgentMiddleware + TodoListMiddleware + ModelFallbackMiddleware |

**LangChain 团队自身全部基于 create_agent + 定制 middleware 栈构建**。

---

## 6. Middleware 架构的工程意义

### 6.1 组织维度

同一 middleware 可跨组织所有 agent 复用：
- 新 agent 继承经过实战验证的行为（无需重建）
- 更新 middleware 一次→全公司所有 agent 同时受益

### 6.2 架构判断

Middleware 模式是**关注点分离在 Agent 时代的形态**：
- 传统 microservice：每个服务独立部署，关注点分离在部署边界
- Agent middleware：每个关注点独立打包（代码/配置/状态/流处理），运行时编织到 Agent Loop

**关键优势**：无需重新部署 Agent 即可更新安全策略、成本限制、工具集成——只更新 middleware 栈。

### 6.3 与 Parallax 验证 pipeline 的映射

Parallax 的 cognitive-executive separation 可以映射为一个 middleware：

```python
SecurityMiddleware:
  after_model hook:
    → extract intent
    → L1 rule engine (whitelist check)
    → L2 classifier (anomaly detection)  
    → L3 LLM validator (semantic safety)
    → allow/deny/human-in-loop
```

这正是模型中立 harness 的价值——同一 middleware 栈可保护任何后端模型。

---

## 7. 工程启示

1. **最小化核心 + 丰富 middleware > 大一统框架**：LangChain 从 LangChain Expression Language (LCEL) → create_agent 的演进说明越简单越可组合
2. **工具生命周期管理不应在 Prompt 中**：tools 的依赖初始化、清理、注册应作为 middleware 的一部分
3. **审核+日志+延迟的分离是 Agent 需求**：不像传统服务可依赖框架层日志，Agent 的 stream handler 需要原生支持路由到不同消费者
4. **组织级 middleware 复用是关键**：一次投资→全公司受益，这是 Agent 时代的 Code Reuse 形态
