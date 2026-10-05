---
title: '🤖 AI Harness · Agent 基础设施 — 周报 #4（2026-06-11）'
blog_url: https://bryantchang1992.github.io/ai_memory_chang_ai_team/posts/tech-research/week-04/ai-harness/
blog_source: _posts/2026-06-11-ai-harness-week-04.md
blog_source_commit: f83970fa7e6ad32d626cc6ca3ba7428c90a638a5
blog_body_sha256: 2131464e8e7fccc284f4fa06b48242ecb38223f6c43eae25a24af9d8fc8c1072
synced_at: '2026-10-05'
type: survey
created: '2026-06-11'
tags:
- AI基础设施
- Agent
- 框架
issue: 4
issue_date: '2026-06-11'
---

## 🔥 本周亮点

> **📌** **Anthropic 发布 Claude Fable 5 / Mythos 5（6月9日）：**Fable 5 是 Anthropic 迄今最强大的广泛发布模型，Mythos 5 面向 Glasswing 安全合作伙伴。两大模型标配 1M token 上下文窗口、128K 最大输出、always-on 自适应思考——这是 Anthropic 首次不再支持传统 extended thinking 模式，标志着"自适应思考"成为唯一推理范式。
>
> **OpenAI Assistants API 正式宣布退役（2026年8月26日）：**一个时代的终结。开发者必须迁移至 Agents SDK + Responses API。整个 Agent 基础设施栈的重心正在从"API-first 托管"转向"SDK-first 自主构建"。
>
> **Anthropic 发布 Tool Search Tool / Programmatic Tool Calling / Tool Use Examples：**三项功能将 Agent 工具调用带入新范式——按需发现工具、用代码替代自然语言循环、用示例替代 Schema 描述。在内部评测中，Opus 4 的 MCP 评测准确率从 49% 跃升至 74%。
>
> **Anthropic 发布 Agent 容器化安全工程指南：**详细披露了 Claude 三大产品的容器化安全架构、三层防御体系及实战经验——blast radius 的工程化约束已成为 Agent 部署的关键课题。

---

## 🧠 Claude Fable 5 & Mythos 5

*2026年6月9日，Anthropic 发布 Fable 5（广泛可用）和 Mythos 5（Glasswing 合作伙伴限定），这是自 Opus 4.8 以来的最大模型升级。*

### [Claude Fable 5 (claude-fable-5)](https://platform.claude.com/docs/en/about-claude/models/introducing-claude-fable-5-and-claude-mythos-5) `BREAKTHROUGH` `NEW MODEL`

Anthropic 史上最强大的广泛发布模型，与 Opus 4.7 共享 tokenizer（同一文本多约 30% token），关键规格：

| 特性 | Fable 5 / Mythos 5 |
|------|---------------------|
| 上下文窗口 | 1M tokens（默认） |
| 最大输出 | 128K tokens |
| 推理模式 | Adaptive Thinking only（always-on） |
| Extended Thinking | ❌ 不支持（返回 400） |
| Temperature/top_p/top_k | ❌ 不可修改 |
| 安全分类器 | ✓ 新增 reasoning_extraction 类别 |
| 数据留存 | 强制 30 天（不支持 ZDR） |
| 计费 | Refusal 无输出时不收费 |

核心变化：Adaptive Thinking 成为唯一推理模式——Anthropic 首次完全移除传统 extended thinking，模型自主决定何时需要深度思考。thinking.display 默认 "omitted"，安全思考链不暴露给用户。

> 来源：[Claude Platform Release Notes (June 9)](https://platform.claude.com/docs/en/release-notes/overview) · [Model Introduction](https://platform.claude.com/docs/en/about-claude/models/introducing-claude-fable-5-and-claude-mythos-5)

### Claude Opus 4.1 退役公告（6月5日） `DEPRECATION`

Anthropic 宣布 Claude Opus 4.1 (claude-opus-4-1-20250805) 将于 **2026年8月5日** 退役。推荐迁移到 Claude Opus 4.8。加上 OpenAI Assistants API 8月退役，今年夏天将是 Agent 基础设施的大规模迁移窗口。

> 来源：[Anthropic · Model Deprecations](https://platform.claude.com/docs/en/about-claude/model-deprecations)

---

## 🔧 Anthropic 高级 Tool Use 平台

*Tool Search Tool（按需发现）、Programmatic Tool Calling（代码级调用）、Tool Use Examples（示例驱动）——三项功能重新定义了 Agent 工具调用范式。*

### [Tool Search Tool — 85% Token 节省，准确率大幅提升](https://www.anthropic.com/engineering/advanced-tool-use) `FEATURE` `MCP`

当 Agent 连接数十个 MCP 服务器时，工具定义本身消耗大量上下文（GitHub 35 tools ~26K tokens, Slack 11 tools ~21K tokens, Jira ~17K tokens, 合计可达 55K-134K tokens）。Tool Search Tool 通过 `defer_loading: true` 标记延迟加载工具，Agent 按需搜索并动态加载——仅需 ~8.7K tokens（vs 传统 77K tokens），节省 85%+ 上下文开销。

关键数据：

- Opus 4 在 MCP 评测中准确率从 **49% → 74%**
- Opus 4.5 从 **79.5% → 88.1%**
- 支持 Regex / BM25 / 自定义 embedding 策略
- 与 Prompt Caching 完全兼容——延迟加载的工具不影响缓存命中

> 来源：[Anthropic Engineering · Advanced Tool Use](https://www.anthropic.com/engineering/advanced-tool-use)

### [Programmatic Tool Calling — 用代码替代自然语言循环](https://www.anthropic.com/engineering/advanced-tool-use) `FEATURE`

传统 tool use 中每次工具调用都经过一次完整推理 pass，中间结果堆积在上下文中。Programmatic Tool Calling 允许 Claude 在代码执行环境中调用工具——用代码处理循环、条件判断和数据转换，仅在必要时进行推理。已应用于 [Claude for Excel](https://www.claude.com/claude-for-excel) 产品中。

> 来源：[Anthropic Engineering · Advanced Tool Use](https://www.anthropic.com/engineering/advanced-tool-use)

### Tool Use Examples — Schema 不是文档 `BEST PRACTICE`

JSON Schema 只能描述什么是结构合法的，无法表达"何时包含可选参数"、"哪些组合有意义"、"API 的使用惯例是什么"。Tool Use Examples 提供了统一的工具使用示范标准，让 Agent 从示例中学习正确用法，而非仅依赖 Schema。

> 来源：[Anthropic Engineering · Advanced Tool Use](https://www.anthropic.com/engineering/advanced-tool-use)

---

## 🚨 OpenAI Assistants API 即将退役

*OpenAI 宣布 Assistants API 将于 2026年8月26日退役——Agent 基础设施从"托管 API"到"自主 SDK"的历史转折。*

### [Assistants API Deprecation — 2026年8月26日](https://learn.microsoft.com/en-us/answers/questions/5571874/openai-assistants-api-will-be-deprecated-in-august) `BREAKING` `MIGRATION`

OpenAI Assistants API 自 2023 年推出以来，为开发者提供了托管式 Agent 构建能力（memory、tools、file handling）。但 OpenAI 明确将战略转向 **Agents SDK + Responses API**：

- Agents SDK 支持多模型（100+ LLMs provider-agnostic）
- 更强的自主性（multi-step planning、tool orchestration、state management）
- 生产级安全特性（guardrails、sandbox、execution tracing）
- 内置 Realtime Agents（语音 Agent，基于 gpt-realtime-2）

迁移关键事项：Assistants API 的 threads/messages/runs 模型需要重新映射到 SDK 的 agent/runner/session 模型。开发者有约 2.5 个月迁移时间。

> 来源：[Microsoft Learn · Assistants API Deprecation](https://learn.microsoft.com/en-us/answers/questions/5571874/openai-assistants-api-will-be-deprecated-in-august) · [OpenAI Agents SDK](https://openai.github.io/openai-agents-python/) · [Callsphere · Migration Guide](https://callsphere.ai/blog/openai-agents-sdk-vs-assistants-api-migration-2026)

### ChatGPT Memory Dreaming V3 发布 `NEW`

OpenAI 同时推出了全新 Memory 架构 Dreaming V3，从"用户主动要求记住"升级为"后台自动综合对话历史"。新增"跟随偏好与约束"和"随时间自动更新"，解决了传统 saved memories 的过时问题。Plus/Pro 用户已在美国上线。

> 来源：[OpenAI Release Notes · June 2026](https://releasebot.io/updates/openai)

---

## 🛡️ Anthropic · Agent 容器化安全工程

*Anthropic 发布深度工程博客，全面披露 Claude 三大产品的容器化安全架构——blast radius 约束成为 Agent 部署的核心课题。*

### [How We Contain Claude Across Products](https://www.anthropic.com/engineering/how-we-contain-claude) `SECURITY` `ENGINEERING`

Anthropic 系统性地披露了 agent 安全的三层防御体系和三个产品的容器化实践：

- **环境层（Environment）：**Process sandboxes、VMs、filesystem boundaries、egress controls——设置硬边界，防止 credential 泄露。Claude Code 的 [reference devcontainer](https://code.claude.com/docs/en/devcontainer) 让 Agent 无需逐次审批即可在隔离环境中自主运行。
- **模型层（Model）：**System prompts、classifiers、probes、training modifications。Claude Opus 4.7 在 Gray Swan Agent Red Teaming 基准上保持 ~0.1% 单次攻击成功率（100 次自适应尝试后 ~5-6%）。Claude Code auto mode 拦截约 83% 过度激进行为。
- **外部内容层（External Content）：**MCP servers、第三方插件、web search tools——粒度化权限限制（如只读 DB 权限）使 Agent 可广泛部署。

关键洞察：三种风险来源（用户误用、模型误行为、外部攻击者）需要三层防御重叠覆盖——环境层提供硬边界，模型层提供概率防护，外部内容层限制攻击面。Claude Mythos Preview 因 blast radius 过高而未在四月广泛发布。

> 来源：[Anthropic Engineering · How We Contain Claude](https://www.anthropic.com/engineering/how-we-contain-claude)

---

## 🔗 Agent 框架生态更新

*Google ADK 重大版本升级、LangGraph v3 流式传输进入落地期、CrewAI 密集迭代。*

### [Google ADK 2.2.0](https://github.com/google/adk-python/releases/tag/v2.2.0) `UPDATED` `BREAKING`

2026年6月4日发布，包含重要的 Breaking Changes：

- **默认模型迁移：**LlmAgent 默认从 gemini-2.5-flash → gemini-3-flash-preview（gemini-2.5-flash 将于 2026-10-16 关闭）
- **GenAI SDK v2.0.0 升级：**"turns" 术语改为 "steps"
- **OpenTelemetry 自动插桩：**新增 AutoTracingPlugin，原生 emit OTel gen_ai.client.* 指标
- **RubricBasedMultiTurnTrajectoryEvaluator：**新的评测组件，支持多轮轨迹评估
- **上下文压缩增强：**compaction summaries 现在包含思考链和工具调用
- **A2A 协议改进：**区分 input-required vs auth-required 状态，保留 A2A message metadata

> 来源：[GitHub · google/adk-python v2.2.0](https://github.com/google/adk-python/releases/tag/v2.2.0)

### [LangGraph v3 流式传输生态落地](https://github.com/langchain-ai/langgraph/releases) `ECOSYSTEM`

继上周报道的 v3 流式传输（SSE + WebSocket），本周生态正在快速吸收这些能力。SDK Python 0.4.2 的流解码器提取、interleave_projections、WebSocket 传输等能力为 Agent 间实时通信提供了坚实基础。CLI 0.4.27 增强了安全部署（pinning deploy images by digest）。

> 来源：[LangGraph Releases](https://github.com/langchain-ai/langgraph/releases)

### [CrewAI v1.14.7 alpha 系列密集迭代](https://github.com/crewAIInc/crewAI/releases) `PRE-RELEASE`

CrewAI 本周（6/3-6/9）密集发布三个 alpha 版本（a1 → a3），重点方向：

- **Flow DSL 重构：**从单一 flow.py 拆分为 DSL、Definition、Runtime 三层
- **Conversational Flows：**新增对话流追踪、handle_turn 文档、Chat API 实现
- **可插拔后端：**Memory、Knowledge、RAG、Flow 支持 default backend 切换
- **Provider 扩展：**新增 Snowflake Cortex LLM、Databricks 集成、NVIDIA Nemotron 指南
- **Crew Trained Agents：**支持 crew 级训练的 Agent 文件支持

> 来源：[GitHub · crewAI Releases](https://github.com/crewAIInc/crewAI/releases)

---

## 🔒 Agent 安全态势

*Prompt Injection 攻击激增 340%、OWASP Agentic Top 10 落地、Dual-LLM 防御模式成为共识。*

### [OWASP Top 10 for LLM & Agentic Applications 2026](https://genai.owasp.org/resources/) `CRITICAL` `STANDARD`

2026 年 Agent 安全领域的关键标准化进展：

- **OWASP Top 10 for LLM Applications 2025**：Prompt Injection 连续第三年位列 LLM01
- **OWASP Top 10 for Agentic Applications 2026**：针对自主 Agent 的新型攻击面——tool poisoning、credential theft via MCP、agent privilege escalation
- NIST 将 Prompt Injection 定性为 "生成式 AI 最大的安全缺陷"
- 超过 30 个 CVE 被披露影响主流 Coding Agent

> 来源：[OWASP Gen AI Security Project](https://genai.owasp.org/resources/) · [LLM Security Guide 2026](https://github.com/requie/LLMSecurityGuide)

### [Prompt Injection 攻击激增 340%](https://www.aimagicx.com/blog/prompt-injection-attacks-ai-agent-security-guide-2026) `ALERT`

2026年 Prompt Injection 攻击较前一年激增 340%。业界共识的防御模式包括：

- **Dual-LLM 模式：**一个 LLM 处理用户输入自动净化，另一个 LLM 执行实际任务——防止 memory poisoning
- **Canary Tokens：**在 system prompt 中嵌入隐秘密令，通过检测泄露来发现注入攻击
- **Sandboxing + Human-in-the-Loop：**将高危操作隔离在沙箱中 + 人工审批关键动作
- **RAG Poisoning 防御：**研究发现 5 份精心构造的文档即可在 90% 情况下操纵 AI 响应

> 来源：[AIMagicX · Prompt Injection 2026](https://www.aimagicx.com/blog/prompt-injection-attacks-ai-agent-security-guide-2026) · [Lushbinary · Production Playbook](https://lushbinary.com/blog/ai-agent-prompt-injection-defense-production-playbook/) · [GetMaxim · Complete Guide](https://www.getmaxim.ai/articles/prompt-injection-defense-for-production-ai-agents-a-complete-2026-guide/)

---

## 📋 MCP 生态 & 托管 Agent 更新

*MCP Tunnels 内网连接、Self-hosted Sandboxes、Managed Agents 定时部署——Claude 平台基础设施持续丰富。*

### [Claude Managed Agents 关键更新](https://platform.claude.com/docs/en/release-notes/overview) `FEATURE`

6月9日 Claude 平台同步推出多项 Managed Agents 能力：

- **Scheduled Deployments：**支持 Cron 定时调度 Agent 会话，无需自建调度器
- **Vault Environment Variables：**将密钥安全注入 Agent 沙箱，支持 CLI/SDK 认证
- **Webhook session_thread_id：**多 Agent 线程事件现在包含 session_thread_id 字段
- **MCP Tunnels（Research Preview）：**连接私有网络中的 MCP 服务器
- **Self-hosted Sandboxes：**在自有基础设施中运行 tool execution，替代 Anthropic 托管沙箱

> 来源：[Claude Platform Release Notes](https://platform.claude.com/docs/en/release-notes/overview)

### [Advisor Tool 更新 & Claude Code 扩展](https://platform.claude.com/docs/en/release-notes/overview) `TOOLING`

6月2日 Advisor Tool 新增 `max_tokens` 参数，可限制 advisor 模型的单次输出。同日起，被 refusal 的请求（未生成任何输出）不再收费。

Claude Code 方面：Auto mode 扩展至更多用户、Max plan 用户默认 fast mode on Opus 4.8、Workflows（research preview）支持定义多步 agentic plans。

> 来源：[Claude Platform Release Notes (June 2)](https://platform.claude.com/docs/en/release-notes/overview)

---

## 📈 趋势观察

*从本周 AI 基础设施动态中提炼的关键趋势线。*

### 趋势一：Agent 基础设施从"堆料"走向"提效" `PARADIGM`

Tool Search Tool（85% token 节省）、Programmatic Tool Calling（用代码替代推理循环）、自适应思考（仅在需要时触发推理）——这三项功能指向同一方向：**Agent 基础设施不再追求"塞更多东西进上下文"，而是追求"按需加载、按需推理、按需调用"**。这对成本控制和生产环境部署至关重要。从 Anthropic 的内部数据（Opus 4 从 49%→74%）来看，提效和准确率并非矛盾。

### 趋势二：Agent 运行时基础设施从"模型能力"到"平台能力" `TREND`

Claude Managed Agents 的 Scheduled Deployments、Vault、Webhooks、MCP Tunnels、Self-hosted Sandboxes——这些不是模型能力，而是 **Agent 运行时基础设施**。类比云计算的发展：早期竞争在"谁的虚拟机快"，后来竞争在"谁的管理平台好"。Agent 领域正在经历同样的转变——模型的差异化在缩小，运行时的差异化在扩大。

### 趋势三："自适应"成为推理基础设施的默认范式 `SHIFT`

Fable 5 不再支持传统 extended thinking（返回 400 错误），Adaptive Thinking 成为唯一推理模式。Claude Opus 4.8 也引入了自适应思考。这意味着 Anthropic 正在将"模型自主决定何时深度思考"作为唯一范式——开发者不能再手动控制思考预算。这对 Agent 行为的影响深远：同一 Agent 面对简单和复杂任务时的延迟和成本将呈现更大差异。

### 趋势四：Agent 安全从"可选"到"强制" `CRITICAL`

Claude Mythos Preview 因 blast radius 过高而未广泛发布、Prompt Injection 攻击 340% 激增、OWASP Agentic Top 10 落地、Assistants API 退役后开发者需自行实现安全防护——这一切指向：**Agent 安全正在成为基础设施的强制性要求，而非可选增强。**Anthropic 的三层防御模型（环境 + 模型 + 外部内容）是目前最系统的工程实践范例。

### 趋势五：OpenAI Assistants API 退役标志 Agent 基础设施进入"SDK-first"时代 `INSIGHT`

从"托管式"到"SDK 自主构建"的转变并非 OpenAI 独有。Anthropic 的 Agent SDK、LangGraph v3、Google ADK 2.2.0、CrewAI Flow DSL——所有框架都在提供更强、更灵活、更可观测的 Agent 构建原语。托管 API 适合快速原型，但生产级 Agent 需要开发者对运行时拥有深度控制权。

---

## 🔗 参考链接

*本周报告所有信息均来自公开来源，每条均有直接链接可查证。*

### Anthropic · 模型 & 平台

- [Claude Platform Release Notes (June 2-9)](https://platform.claude.com/docs/en/release-notes/overview)
- [Introducing Claude Fable 5 and Claude Mythos 5](https://platform.claude.com/docs/en/about-claude/models/introducing-claude-fable-5-and-claude-mythos-5)
- [Claude Opus 4.1 Deprecation (Aug 5, 2026)](https://platform.claude.com/docs/en/about-claude/model-deprecations)
- [Introducing Advanced Tool Use on the Claude Developer Platform](https://www.anthropic.com/engineering/advanced-tool-use)
- [How We Contain Claude Across Products](https://www.anthropic.com/engineering/how-we-contain-claude)
- [Anthropic Engineering Blog](https://www.anthropic.com/engineering)
- [Claude Agent SDK · Billing Change (June 15)](https://code.claude.com/docs/en/agent-sdk/overview)

### OpenAI

- [Assistants API Deprecation (Aug 26, 2026)](https://learn.microsoft.com/en-us/answers/questions/5571874/openai-assistants-api-will-be-deprecated-in-august)
- [OpenAI Agents SDK](https://openai.github.io/openai-agents-python/)
- [Agents SDK vs Assistants API Migration Guide](https://callsphere.ai/blog/openai-agents-sdk-vs-assistants-api-migration-2026)
- [OpenAI · ChatGPT Memory Dreaming V3](https://releasebot.io/updates/openai)
- [OpenAI · Agents API Guide](https://developers.openai.com/api/docs/guides/agents)

### Agent 框架

- [Google ADK v2.2.0](https://github.com/google/adk-python/releases/tag/v2.2.0)
- [LangGraph Releases](https://github.com/langchain-ai/langgraph/releases)
- [CrewAI Releases (v1.14.7 alpha)](https://github.com/crewAIInc/crewAI/releases)
- [OpenAI Agents SDK (GitHub)](https://github.com/openai/openai-agents-python)

### Agent 安全

- [OWASP Gen AI Security Project](https://genai.owasp.org/resources/)
- [LLM Security Guide 2026](https://github.com/requie/LLMSecurityGuide)
- [Prompt Injection Attacks 2026](https://www.aimagicx.com/blog/prompt-injection-attacks-ai-agent-security-guide-2026)
- [10-Layer Prompt Injection Defense](https://lushbinary.com/blog/ai-agent-prompt-injection-defense-production-playbook/)
- [Complete Production Defense Guide](https://www.getmaxim.ai/articles/prompt-injection-defense-for-production-ai-agents-a-complete-2026-guide/)
- [ArXiv · Prompt Injection on Coding Assistants](https://arxiv.org/html/2601.17548v1)

### MCP & 协议

- [MCP RC 2026-07-28](https://github.com/modelcontextprotocol/modelcontextprotocol/releases)
- [Claude · Tool Use Overview](https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview)
- [MCP Complete Guide 2026](https://dev.to/x4nent/complete-guide-to-mcp-model-context-protocol-in-2026-architecture-implementation-and-4a11)

---

*CHANG_AI_TEAM · AI Harness 周报 #4 · 2026年6月11日*
