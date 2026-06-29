---
type: concept
title: "Agent Harness: Tool Interface & Protocol (T)"
sources:
  - "sources/papers/Agent-Harness-Engineering-Survey/Agent-Harness-Engineering-Survey-OpenReview2026.pdf"
  - "sources/papers/Agent-Harness-Engineering-Survey/精读分析.md"
tags:
  - "Agent-Harness"
  - "Agent基础设施"
  - "MCP"
  - "A2A"
  - "工具协议"
created: 2026-06-20
updated: 2026-06-20
status: draft
related:
  - "[[Agent-Harness-Engineering-Survey综述]]"
  - "[[Agent-Harness-Execution-Environment执行环境]]"
---

# Agent Harness: Tool Interface & Protocol (T)

> ETCLOVG 第二层：Agent 如何发现、调用和管理外部工具——定义了 Agent 的"手"。

---

## 1. 层级定位

Tool Interface 定义了 Agent 与其行动能力之间的**契约**。这层不是简单地"让 Agent 调用 API"，而是一个涉及工具发现、调用规范、错误处理和访问控制的完整接口设计问题。

核心矛盾：**更多工具 → 更广任务覆盖 → 更高的选择错误率和 Prompt Injection 面**。

---

## 2. 两大协议竞赛

### 2.1 MCP（Model Context Protocol）— Anthropic 2024

MCP 是当前最接近**事实标准**的 Agent-工具协议。

| 维度 | 详情 |
|------|------|
| 架构 | Client-Server，JSON-RPC 2.0 通信 |
| 传输层 | stdio（本地）+ SSE/Streamable HTTP（远程） |
| 核心原语 | `tools/list`（发现）、`tools/call`（执行）、`resources/read`（数据访问） |
| 三种能力 | **Resources**（数据暴露）、**Prompts**（模板复用）、**Tools**（执行操作） |
| 生态覆盖 | 文件系统、数据库（PostgreSQL/SQLite）、搜索引擎、浏览器（Playwright）、代码执行器、GitHub API、Slack、线性工具... |
| 安全模型 | Server 端不暴露机制自动安全——需在 Client 侧做权限控制和工具白名单 |
| 状态 | 已成为生态中最大共识的工具协议 |

MCP 的设计哲学是 **"给 Agent 能力而不给控制"**——Server 暴露能力，Client 控制访问。

### 2.2 A2A（Agent-to-Agent）— Google 2025

A2A 是 Agent 间通信的协议规范，定位与 MCP **互补**而非竞争。

| 维度 | 详情 |
|------|------|
| 架构 | HTTP/JSON 为基础 |
| 核心抽象 | **Task**（任务对象）—含状态机、Artifacts |
| 通信模式 | 流式、长轮询、推送通知 |
| 身份模型 | Agent Card — 自描述的 Agent 能力清单 |
| 与 MCP 关系 | MCP 连接 Agent ↔ Tool，A2A 连接 Agent ↔ Agent |

**MCP + A2A 组合**：MCP 让 Agent 调用工具，A2A 让 Agent 互相委托任务——两协议覆盖了 Agent 的所有外部交互面。

---

## 3. 工具设计的核心挑战

### 3.1 Schema 描述粒度

| 描述风格 | 优点 | 风险 |
|----------|------|------|
| 过简（如 `execute(code: str)`） | 节省上下文预算 | 模型误解工具语义、参数格式错误 |
| 过繁（JSON Schema + 示例 + 错误语义） | 模型理解更准确 | 每个工具几百 Token——50 个工具消耗数万 Token |

**最佳实践**：精确到参数级别的描述 + 包含错误反馈语义（成功/失败/部分结果的明确格式）。

### 3.2 工具选择错误（Selection Error）

论文发现：工具数量与选择准确性**不是单调关系**——过多工具时，模型的选择准确率反而下降。这就是 **Capability-Control Tradeoff** 在工具层的体现。

### 3.3 Prompt Injection 表面

每个工具都是一个攻击面：
- 恶意文档 → 文件读取工具 → 注入指令
- 恶意网页 → 浏览器工具 → 指令注入
- 恶意代码输出 → 终端工具 → 逃逸尝试

每个工具调用前后的 **Input/Output Guardrails**（§9）是必要防线。

### 3.4 信息流控制

工具间数据流动需要追踪：敏感数据是否通过工具链泄露？
- 数据库 → LLM → API → 外部系统
- 需要 taint tracking 或等价机制

---

## 4. 工具描述设计原则

1. **最小权限原则**：不给 Agent 暴露它不需要的工具。按任务按需授予权限。
2. **结构化错误反馈**：工具响应应是结构化的（成功/失败/部分结果），让 Agent 可以确定性处理。
3. **工具能力边界明确**：工具描述中应包含"这个工具**不能**做什么"——减少模型对工具能力的误判。
4. **版本化管理**：工具 Schema 需要版本化，变更需要评估对 Agent 行为的影响（Harness Coupling）。

---

## 5. 协议发展趋势

| 趋势 | 说明 |
|------|------|
| **MCP 生态扩张** | 越来越多的服务和 API 提供 MCP Server——从数据库到浏览器到企业应用 |
| **A2A 多 Agent 场景** | 复杂任务拆解到多个专业 Agent 后，标准化通信变得必要 |
| **工具市场（Tool Marketplace）** | MCP 的注册和发现机制 → 可复用工具的生态系统 |
| **动态工具发现** | Agent 按需发现和注册工具，而非静态配置——更灵活但也更不安全 |
| **跨协议互操作** | MCP ↔ A2A 的桥接——Agent 经由 MCP 调用工具，同时通过 A2A 委托其他 Agent |

---

## 6. 对我们（CHANG_AI_TEAM）的启示

1. **接入 MCP** 是当前最务实的工具策略——标准化程度最高
2. **工具列表不应膨胀**：每个工具需经过威胁评估后才暴露给 Agent
3. **A2A** 在需要多 Agent 协作的复杂场景（如代码审查 + 测试 + 部署流水线）中值得采用
4. **工具响应应结构化**——错误码、部分成功、超时等状态需明确定义，让 Agent 能正确决策

---

> 返回父页：[[Agent-Harness-Engineering-Survey综述]] · 上一级：ETCLOVG 七层体系 · T 层（Tool Interface & Protocol）
