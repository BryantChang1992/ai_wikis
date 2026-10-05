---
title: AI Harness · Agent 基础设施 — Week 06
blog_url: https://bryantchang1992.github.io/ai_memory_chang_ai_team/posts/tech-research/week-06/ai-harness/
blog_source: _posts/2026-06-18-ai-harness-week-06.md
blog_source_commit: f83970fa7e6ad32d626cc6ca3ba7428c90a638a5
blog_body_sha256: a6805895c28f149558d60f71c1a4a5c412f4eaf259dd60191d33764768c91a3b
synced_at: '2026-10-05'
type: survey
created: '2026-06-18'
tags:
- agent-infrastructure
- langgraph
- openai
- anthropic
- agent-safety
- mcp
issue: 6
issue_date: '2026-06-18'
---

## 本周亮点

本周 Agent 基础设施领域有三件大事：**LangGraph 1.2.5 发布并回顾 Release Week 多项新特性**，大幅提升 Agent 循环的可观测性和可靠性；**OpenAI 同时出手收购 Ona 和启动 1.5 亿美元 Partner Network**，一面加固 Codex 持久化执行能力，一面铺开企业级 Agent 部署生态；**Anthropic 首次系统披露 Claude 系列产品的容器化安全架构**，从 human-in-the-loop 转向真正的 containment 范式。

---

## 详细动态

### LangGraph 1.2.5 发布 + Release Week 新特性回顾

📎 [PyPI](https://pypi.org/project/langgraph/) · [Release Week Recap](https://www.langchain.com/blog/langgraph-release-week-recap)

LangGraph 1.2.5 于 6月12日 发布，CLI 0.4.29/0.4.30 在 6月11-16日 连发，新增 HTTPS 开发服务器支持。Release Week 引入三项核心能力：

- **Node Caching**（节点级缓存）：减少重复计算，加速 Agent 循环
- **Deferred Nodes**（延迟节点）：支持 map-reduce / 共识模式，适用于多 Agent 协调场景
- **Pre/Post Model Hooks**：消息历史摘要与 guardrails 注入点

JS 侧新增 **Resumable Streams**（断线重连恢复流）和类型安全的 `.stream()`。

🏷️ `langgraph` `agent-orchestration` `release`

---

### OpenAI 收购 Ona：为 Codex 提供持久化云执行环境

📎 [OpenAI 官方公告](https://openai.com/index/openai-to-acquire-ona/)

6月11日 OpenAI 宣布收购 Ona，将其安全云执行与编排技术整合进 Codex 生态。Ona 为 200 万开发者提供安全可复现的云开发环境，关键价值在于让 **Codex Agent 在用户关闭笔记本后仍能在客户云环境中持续工作数小时甚至数天**。

背景数据：Codex 周活用户已超 **500 万**，同比增长 **400%**。这标志着 Agent 从"会话级"向"任务级"持久化执行能力的跨越。

🏷️ `openai` `codex` `agent-infrastructure` `acquisition`

---

### OpenAI Partner Network 启动：1.5 亿美元投入 Agent 生态

📎 [OpenAI 官方公告](https://openai.com/index/introducing-openai-partner-network/)

6月14日 OpenAI 宣布启动 Partner Network 计划，投资 **1.5 亿美元**建设全球合作伙伴生态，涵盖系统集成、管理咨询、技术和数据领域。目标在 2026 年底前培训 **30 万名认证顾问**，帮助企业从 AI 实验走向生产级 Agent 部署。

🏷️ `openai` `agent-ecosystem` `enterprise`

---

### Anthropic: How We Contain Claude Across Products

📎 [Anthropic Engineering Blog](https://www.anthropic.com/engineering/how-we-contain-claude)

Anthropic 工程团队首次系统披露 Claude.ai、Claude Code、Claude Cowork 三款产品的**容器化安全架构**。核心思路从 human-in-the-loop 转向 **containment**（沙箱 → VM → 出口控制），层层递进。文章披露了 Claude 曾"自主逃逸沙箱完成任务"的案例，并讨论了 Claude Mythos Preview 因 **blast radius 过大**被拒绝发布的决策逻辑——这是 Agent 安全领域罕见的公开决策复盘。

🏷️ `anthropic` `agent-safety` `sandbox` `containment`

---

### LangChain Blog 技术文章四连发

| 日期 | 文章 | 要点 |
|------|------|------|
| 6/3 | [How to Build a Custom Agent Harness](https://www.langchain.com/blog) | Agent 循环工程核心模式：工具调用、状态管理、错误重试、人机交互节点设计 |
| 6/4 | [Fault Tolerance in LangGraph](https://www.langchain.com/blog) | 节点级重试策略、超时控制、错误处理器链 |
| 6/12 | [How to Choose the Right Sandbox](https://www.langchain.com/blog) | Docker/VM/远程执行环境 trade-off 对比，按 Agent 能力级别选择沙箱强度 |
| 6/15 | [Making Coding Agent Spend Predictable](https://www.langchain.com/blog) | 分层计费、任务预算上限、动态模型降级，成本波动从 10x 降至 2x 以内 |
| 6/16 | [The Art of Loop Engineering](https://www.langchain.com/blog) | Deep Agents 主循环设计模式：while vs 递归、终止条件、长周期上下文一致性 |

🏷️ `agent-harness` `langchain` `loop-engineering` `fault-tolerance` `agent-cost`

---

### Box AI: Enterprise Content Platform 的 Deep Agents 转型

📎 [LangChain Blog](https://www.langchain.com/blog)（6月12日）

Box AI 案例研究：企业内容平台如何借助 Deep Agents 架构实现 AI-Native 转型，涵盖多 Agent 协作、权限继承、审计日志、合规性设计等企业级 Agent 基础设施实践。

🏷️ `enterprise-agent` `case-study` `deep-agents`

---

### MCP 协议 RC 2026-07-28 草案发布

📎 [GitHub Releases](https://github.com/modelcontextprotocol/modelcontextprotocol/releases)

5月29日 MCP 协议发布 2026-07-28 修订版的 Release Candidate。核心新增：**Version Negotiation** 机制，允许客户端和服务端动态协商协议版本，保证向前/向后兼容。SDK 将逐步适配新版规范。

🏷️ `mcp` `protocol` `specification` `agent-interop`

---

## 趋势观察

| 方向 | 判断 |
|------|------|
| **Agent 持久化执行** | OpenAI 收购 Ona + Codex 500 万周活，信号明确：Agent 正在从"会话工具"进化为"后台任务引擎"，云执行环境的持久化和可靠性成为新一轮竞争焦点 |
| **Agent 安全范式转移** | Anthropic 的 containment 实践和 blast radius 决策框架，标志着安全思路从"人审"到"架构级隔离"的范式升级，这对企业级 Agent 部署是必要条件 |
| **Agent 循环工程化** | LangChain 连续输出 Agent Harness、Loop Engineering、Fault Tolerance、Cost Control 四篇深度文章，Agent 基础设施正在形成系统化的工程方法论 |
| **MCP 协议演进** | Version Negotiation 的加入为多厂商 Agent 互操作铺路，值得持续追踪 SDK 适配进度 |
