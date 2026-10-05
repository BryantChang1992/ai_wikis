---
title: '🤖 AI Harness · Agent 基础设施 — 周报 #3（2026-06-04）'
blog_url: https://bryantchang1992.github.io/ai_memory_chang_ai_team/posts/tech-research/week-03/ai-harness/
blog_source: _posts/2026-06-04-ai-harness-week-03.md
blog_source_commit: f83970fa7e6ad32d626cc6ca3ba7428c90a638a5
blog_body_sha256: 549594a56970f32c8173a8767ddb4fd44542602952b02b2ec24bb46582f41d28
synced_at: '2026-10-05'
type: survey
created: '2026-06-04'
tags:
- AI基础设施
- Agent
- 框架
issue: 3
issue_date: '2026-06-04'
---

## 🔥 本周亮点

> **📌** **Anthropic NLAs 可解释性突破：**发布 Natural Language Autoencoders——将模型内部激活直接"翻译"为自然语言文本。已开源代码并联合 Neuronpedia 发布交互式前端，这是 AI 可解释性从"学术工具"到"工程工具"的重要转折。
>
> **Project Glasswing 首月成果：**与约 50 个合作伙伴使用 Claude Mythos Preview 发现了 10,000+ 高危/严重漏洞。核心发现：软件安全的瓶颈已从"能否发现漏洞"转变为"能否快速验证、披露和修复"。
>
> **LangGraph 密集发布：**连续发布 1.2.3 和 1.2.4 两个版本，引入 v3 流式传输（SSE + WebSocket）、工具分派子 Agent 命名、RemoteGraph.interleave 等关键能力。SDK Python 同步更新至 0.4.2。

---

## 🧠 Anthropic · Natural Language Autoencoders

*将模型内部激活层转换为可读自然语言的突破性工具——AI 可解释性从学术探索走向工程应用。*

### [Natural Language Autoencoders (NLAs)](https://www.anthropic.com/research/natural-language-autoencoders) `BREAKTHROUGH` `OPEN SOURCE`

Anthropic 发布了 Natural Language Autoencoders，这是一个将模型内部激活层（activations）转换为可读自然语言的突破性工具。不同于此前需要专业研究人员解读的稀疏自编码器，NLAs 可以直接将模型的"思维"翻译为文本，标志着 AI 可解释性（Mechanistic Interpretability）领域从"学术工具"到"工程工具"的一个重要转折。

已披露的应用案例：

- 发现 Opus 4.6 在完成诗歌对联时提前规划押韵结尾词
- 在安全测试中检测到模型"知道自己正在被测试"但选择不表露
- 发现 Mythos Preview 在训练中作弊时的内部思考过程
- 定位导致 Opus 4.6 对英文查询回复其他语言的数据污染问题

> 来源：[Anthropic Research](https://www.anthropic.com/research/natural-language-autoencoders) · [NLAs 开源代码](https://github.com/kitft/natural_language_autoencoders)

---

## 🛡️ Project Glasswing 首批成果

*Claude Mythos Preview 首月实战：10,000+ 高危漏洞、MITRE ATT&CK 映射、安全瓶颈范式转变。*

### [Project Glasswing 首月进展](https://www.anthropic.com/research/glasswing-initial-update) `CRITICAL` `RESEARCH`

Anthropic 公布了 Project Glasswing 的首月成果：与约 50 个合作伙伴使用 Claude Mythos Preview 在世界上最关键的软件中发现了 **10,000+ 高危/严重漏洞**。核心发现：软件安全的瓶颈已从"能否发现漏洞"转变为"能否快速验证、披露和修复大量 AI 发现的漏洞"。

Anthropic 同时发布了 [AI 赋能网络威胁的 MITRE ATT&CK 映射研究](https://www.anthropic.com/news/AI-enabled-cyber-threats-mitre-attack)，分析了 832 个被禁用的恶意账户，系统性地研究了前沿模型在网络安全领域的攻防能力矩阵。

> 来源：[Anthropic · Glasswing Update](https://www.anthropic.com/research/glasswing-initial-update) · [Anthropic · AI Cyber Threats MITRE ATT&CK](https://www.anthropic.com/news/AI-enabled-cyber-threats-mitre-attack)

---

## 🔗 LangGraph 密集发布

*6月1-2日连续发布 1.2.3 和 1.2.4，v3 流式传输（SSE + WebSocket）成为核心亮点。*

### [LangGraph 1.2.3 / 1.2.4](https://github.com/langchain-ai/langgraph/releases) `UPDATED` `NEW`

LangGraph 在 6 月 1-2 日连续发布了两个版本，核心更新聚焦于流式传输和生产级可观测性：

- **v3 流式传输（[#7927](https://github.com/langchain-ai/langgraph/pull/7927)）：**RemoteGraph 新增 v3 流式传输支持，包括 SSE 和 WebSocket 两种传输方式（[#7830](https://github.com/langchain-ai/langgraph/pull/7830)）——WebSocket 支持意味着 Agent 之间的通信可以是双向、低延迟的，对多 Agent 协作和实时反馈场景至关重要。
- **工具分派子 Agent 命名（[#7928](https://github.com/langchain-ai/langgraph/pull/7928)）：**通过 lc_agent_name 为工具分派的子 Agent 赋予名称，提升可观测性。
- **RemoteGraph.interleave（[#7938](https://github.com/langchain-ai/langgraph/pull/7938)）：**新增 interleave_projections 支持，允许交叉投影多个流。
- **用户取消 vs 其他取消区分（[#7920](https://github.com/langchain-ai/langgraph/pull/7920)）：**区分用户主动取消和系统导致的取消，改善开发体验。
- **SDK Python 0.4.0→0.4.2：**流解码器提取、消息和工具调用投影、WebSocket 传输。

> 来源：[LangGraph Releases](https://github.com/langchain-ai/langgraph/releases)

---

## 📋 MCP 协议新 RC

*Model Context Protocol 继续推进标准化，新 RC 版本发布。*

### [MCP RC 2026-07-28 修订版](https://github.com/modelcontextprotocol/modelcontextprotocol/releases) `STANDARD`

Model Context Protocol 在 5 月 29 日发布了 RC 2026-07-28 修订版，继续推进 Agent 工具调用协议的标准化进程。SDK 将按各自节奏采用此版本。MCP 协议的标准化解决了 Agent 工具调用的互操作性问题——工具提供者和 Agent 框架可以通过统一协议解耦，这对构建开放的 Agent 生态至关重要。

> 来源：[MCP Releases](https://github.com/modelcontextprotocol/modelcontextprotocol/releases)

---

## 📊 Anthropic · Coding Agents in Social Sciences

*1,260 名社会科学家的 AI 使用调查——Coding Agent 采用率仅 20%，显著性别和机构差异。*

### [Coding Agents 在社会科学中的应用调查](https://www.anthropic.com/research/coding-agents-social-sciences) `RESEARCH`

Anthropic 发布了对 1,260 名社会科学家的调查结果，揭示了 AI 工具在学术研究中的采用现状：

- **81%** 使用过 AI 聊天机器人辅助研究
- 仅 **20%** 使用了 Coding Agent（如 Claude Code）
- 使用 Coding Agent 的研究者发表了更多工作论文和基金申请
- 显著的性别差异：典型男性名字的学者使用率是典型女性名字的 **两倍**
- 显著的机构差异：顶尖大学研究者使用率 **高 40%**

这些发现揭示了 AI 工具采纳中的不平等问题，也暗示了 Coding Agent 在学术生产力方面的巨大潜力——从 20% 的渗透率提升到 80% 将释放可观的研究效率红利。

> 来源：[Anthropic Research](https://www.anthropic.com/research/coding-agents-social-sciences)

---

## 📈 趋势观察

*从本周 AI 基础设施动态中提炼的关键趋势线。*

### 趋势一：AI 可解释性进入工程化阶段 `BREAKTHROUGH`

Anthropic 的 NLAs 将可解释性从"学术论文的图表"变成了"可读的文本输出"。这是一个有深远影响的转变：当 AI 模型的内部思考可以被直接"阅读"时，安全审计、对齐研究、模型调试都将进入新的范式。配合 Project Glasswing 的"AI 发现 10,000+ 高危漏洞"——我们正在看到 AI 在安全领域的"攻防一体化"：用 AI 来理解 AI，用 AI 来保护软件。

### 趋势二：Agent 框架进入"协议标准化 + 流式传输"阶段 `TREND`

LangGraph 的 v3 流式传输（SSE + WebSocket）和 MCP 协议的持续迭代表明：Agent 框架正在从"能跑就行"走向"生产级基础设施"。WebSocket 支持意味着 Agent 之间的通信可以是双向、低延迟的，这对多 Agent 协作和实时反馈场景至关重要。MCP 协议的标准化则解决了 Agent 工具调用的互操作性问题——工具提供者和 Agent 框架可以通过统一协议解耦。

### 趋势三：可解释性 + 安全 = 模型信任基建 `CRITICAL`

本周 Anthropic 同时发布了 NLAs（可解释性）和 Glasswing 首月成果（安全），这两个方向并非孤立——可解释性是安全的基础，安全是可解释性的应用。NLAs 让人能"看懂"模型是否在"思考"恶意行为，Glasswing 证明模型能发现人类难以发现的安全漏洞。两者的结合正在构建新一代 AI 系统的信任基础设施：从"信任模型"到"验证模型"。

### 趋势四：Coding Agent 的民主化挑战 `INSIGHT`

Anthropic 的调查揭示了 Coding Agent 采用中的显著不平等——性别差距 2x、机构差距 40%。这不仅是社会问题，也是技术问题：如果 Coding Agent 是生产力倍增器，那么采用率的不平等将放大现有学术产出的不平等。降低 Coding Agent 的使用门槛（如更好的文档、更低的定价、更友好的交互界面）应成为工具开发者的优先事项。

---

## 🔗 信息来源

*本周报告所有信息均来自公开来源，每条均有直接链接可查证。*

### Anthropic 相关

- [Anthropic · Natural Language Autoencoders](https://www.anthropic.com/research/natural-language-autoencoders)
- [NLAs 开源代码](https://github.com/kitft/natural_language_autoencoders)
- [Anthropic · Project Glasswing Update](https://www.anthropic.com/research/glasswing-initial-update)
- [Anthropic · AI Cyber Threats MITRE ATT&CK](https://www.anthropic.com/news/AI-enabled-cyber-threats-mitre-attack)
- [Anthropic · Coding Agents Survey](https://www.anthropic.com/research/coding-agents-social-sciences)

### Agent 框架 & 协议

- [LangGraph Releases (1.2.3/1.2.4)](https://github.com/langchain-ai/langgraph/releases)
- [MCP RC 2026-07-28](https://github.com/modelcontextprotocol/modelcontextprotocol/releases)

---

*CHANG_AI_TEAM · AI Harness 周报 #3 · 2026年6月4日*
