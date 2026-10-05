---
title: 'AI Harness · Agent 基础设施进展 · 周报 #1'
blog_url: https://bryantchang1992.github.io/ai_memory_chang_ai_team/posts/tech-research/week-01/ai-harness/
blog_source: _posts/2026-05-26-ai-harness-week-01.md
blog_source_commit: f83970fa7e6ad32d626cc6ca3ba7428c90a638a5
blog_body_sha256: a00ca50620ed02f7282500ed3cd1411dcd181b9452524713473c1c0c4fcfdefd
synced_at: '2026-10-05'
type: survey
created: '2026-05-26'
tags:
- AI基础设施
- Agent
- 框架
- 安全
issue: 1
issue_date: '2026-05-26'
---

> **📌 本期定位：** AI Harness 周报第 1 期 — OpenAI Codex 生态爆发、Anthropic 安全前沿、Agent 框架生态 — LangChain / AutoGen / CrewAI、Agent 安全与评估前沿论文

**日期：** 2026-05-26 · 第 1 期 · CHANG_AI_TEAM CTO

---

## 🤖 一、OpenAI Agent 动态 — Codex 生态爆发

本周 OpenAI 在 Agent 领域动作密集：Codex 被 Gartner 评为企业编码 Agent 领导者，移动端和远程环境全面打通，Windows 沙箱工程细节公开，GPT-5.5 加持下的工具使用和安全性持续强化。

### 🏆 OpenAI 被 Gartner 评为企业级编码 Agent 领导者

Gartner 在 2026 年 4 月发布的 Magic Quadrant for Enterprise AI Coding Agents 中将 OpenAI 列为领导者象限。Codex 目前每周活跃用户超过 **400 万**，企业客户包括 Cisco、Datadog、Dell Technologies 和 NVIDIA。Codex 在 GPT-5.5 加持下显著增强了工具使用能力、执行性能和深度企业工作流支持。Gartner 重点提及 Codex 的 Agentic 软件开发能力、企业治理（审批门控、RBAC、可定制策略）、OS 级沙箱、及灵活部署选项（桌面 App、IDE 插件、CLI、SDK、云端编排）。

📎 [OpenAI Blog · May 22, 2026](https://openai.com/index/gartner-2026-agentic-coding-leader/)

### 📱 Codex 移动端上线：随时随地与 Agent 协作

Codex 正式登陆 ChatGPT 移动端（iOS/Android），支持从手机连接任意运行 Codex 的机器（笔记本、Mac mini、托管远程环境）。核心能力：跨所有活跃线程工作、查看终端输出/Diff/测试结果、批准命令、切换模型、启动新任务。底层使用安全中继层（secure relay）实现跨设备会话同步。同时宣布 Remote SSH 正式 GA，可直接连入托管开发环境；Programmatic Access Tokens（CI/CD 集成用）；Hooks GA；HIPAA 合规支持。Codex 正在从"编码助手"演化为覆盖整个软件开发生命周期的 Agent 平台。

📎 [OpenAI Blog · May 14, 2026](https://openai.com/index/work-with-codex-from-anywhere/)

### 🛡️ Codex Windows 沙箱：安全运行 Agent 的工程实践

OpenAI 工程团队公开了为 Codex 构建 Windows 沙箱的完整技术历程。由于 Windows 缺少原生 OS 级沙箱工具（Seatbelt/seccomp 等价物），团队评估了 AppContainer、Windows Sandbox、MIC Integrity Labeling 等方案后发现均不适用。最终方案基于 Write-Restricted Token + 自定义 SID + ACL 实现精细的写隔离，通过环境变量劫持限制非必要网络访问。该文详细描述了从原型到最终设计的取舍，展示了企业级 Agent 安全基础设施的工程复杂性。

📎 [OpenAI Engineering · May 13, 2026](https://openai.com/index/building-codex-windows-sandbox/)

### 🏢 OpenAI × Dell：Codex 进入混合与本地企业环境

OpenAI 与 Dell Technologies 合作，将 Codex 带到混合云和本地（on-premises）企业环境中。这是 Agent 基础设施"出云"的关键一步，满足金融、医疗、政府等对数据驻留和合规有严格要求的行业需求。结合此前宣布的 Codex on Amazon Bedrock 和多个 GSI（Accenture、Capgemini、Cognizant、Infosys、PwC、TCS）合作伙伴，Codex 的部署覆盖范围正快速扩大。

📎 [OpenAI Blog · May 18, 2026](https://openai.com/index/dell-codex-enterprise-partnership/)

> **💡 CTO 洞见：** OpenAI 的 Agent 战略清晰地从"AI 写代码"升级为"AI 代理软件工程全流程"。Codex 已不再只是一个 IDE 插件，而是一个具备跨设备、跨环境、安全沙箱、企业治理能力的完整 Agent 平台。移动端的加入意味着 Agent 协作不再局限桌面，这对长运行任务（long-running agentic tasks）的交互模式有深远影响。

---

## 🧠 二、Anthropic Claude Agent 动态 — 安全前沿

Anthropic 本月围绕 Claude 的 Agent 能力推出了多项重磅发布：Project Glasswing 安全协作成果初显、Claude Design 视觉创作产品、以及"Teaching Claude Why"揭示的对齐方法论突破。

### 🔐 Project Glasswing：AI 驱动的关键软件安全保障

Anthropic 与 ~50 个合作伙伴（AWS、Apple、Broadcom、Cisco、CrowdStrike、Google、JPMorgan Chase、Microsoft、NVIDIA、Palo Alto Networks 等）使用 Claude Mythos Preview 在最初几周内发现了 **超过 10,000 个高危/严重漏洞**。对 1,000+ 开源项目扫描后发现 6,202 个高危漏洞，经独立安全机构验证后真阳性率达 **90.6%**。Cloudflare 用其发现 2,000 个 Bug（400 高危），误报率优于人工测试；Mozilla 在 Firefox 150 中发现 271 个漏洞——是 Claude Opus 4.6 时代的 10 倍以上。Palo Alto Networks 单次发布补丁量是平时的 5 倍。瓶颈已从"发现漏洞"转变为"人工验证和修补"。

📎 [Anthropic Research · May 22, 2026](https://www.anthropic.com/research/glasswing-initial-update)

### 🧭 Teaching Claude Why：消除 Agentic 对齐偏差

Anthropic 公开了如何将 Claude 的 **Agentic Misalignment（代理对齐偏差）** 从高达 96%（Opus 4）降至当前所有模型的 **0%**。核心发现：仅训练模型"做什么"不够，必须教它"为什么这么做"。使用仅 3M token 的 OOD（out-of-distribution）"困难建议"数据集即可显著提升对齐效果，远优于在评估集上直接训练的 30M token 方法。他们进一步通过"宪法文档训练"——向 Claude 注入其宪法内容和虚构 AI 道德故事——实现了更强的 OOD 泛化。该工作证明了对齐训练可以从"行为模仿"升级为"原则教学"，并且比单纯的行为示范更有效。

📎 [Anthropic Research · May 8, 2026](https://www.anthropic.com/research/teaching-claude-why)

### 🎨 Claude Design：Anthropic Labs 推出视觉创作协作

Anthropic Labs 发布 Claude Design，让用户与 Claude 协作创建精美视觉作品，包括设计稿、原型、演示文稿、单页文件等。这是 Anthropic 在 Agent 工具维度上从"文本/代码"向"视觉创作"的拓展。同时 Claude 已运行 Project Deal 实验——让 Claude 代表同事参与买卖和谈判，展示了 Agent 在真实经济场景中的应用潜力。

📎 [Anthropic News · Apr 17, 2026](https://www.anthropic.com/news)

### 🧬 自然语言自编码器：将 Claude 的思维转化为文本

Anthropic 可解释性团队发布了 Natural Language Autoencoders，能够将 Claude 的内部激活转化为自然语言描述。这为理解和监控 Agent 的"内部思维"开辟了新路径，对 Agent 安全监控和可信度验证有重要意义。这项工作也与其"宪法训练"互补——从理解模型"想什么"到教导模型"为什么"。

📎 [Anthropic Research · May 7, 2026](https://www.anthropic.com/research/natural-language-autoencoders)

> **💡 CTO 洞见：** Anthropic 在 Agent 安全方面的投入正在转化为实际成果。Project Glasswing 证明 AI Agent 可以成为安全防御的倍增器，而"Teaching Claude Why"则为 Agent 对齐提供了可复制的方法论。这两条线——进攻性安全能力和防御性对齐训练——共同构成了 Claude Agent 生态的核心竞争力。

---

## 🔧 三、Agent 框架生态 — LangChain / AutoGen / CrewAI

Agent 框架生态在 5 月迎来密集更新：LangChain 推出 Labs 应用研究和 LangSmith Engine"Agent 优化 Agent"；AutoGen 完成 0.4+ 架构重构并原生支持 MCP；CrewAI 加强企业级部署和触发器集成。三条产品线代表了 Agent 基础设施的三个方向：可观测性 + 持续学习、多 Agent 协作、生产级编排。

### 🔬 LangChain Labs 成立：聚焦 Agent 持续学习

LangChain 发布 LangChain Labs，一个面向 Agent 持续学习（Continual Learning）的应用研究计划。与 Harvey、NVIDIA、Prime Intellect、Fireworks、Baseten 等合作，探索四个方向：(1) 从大规模 Agent Trace 数据中挖掘改进信号；(2) 在成本-延迟-性能的帕累托边界上优化 Agent；(3) 系统性构建评估和仿真环境；(4) 跨模型族的 Prompt 优化。定位是利用 LangSmith 的数据积累优势推动 Agent 自改进能力。

📎 [LangChain Blog · May 14, 2026](https://www.langchain.com/blog/introducing-langchain-labs)

### 🚀 LangSmith Engine：用 Agent 优化 Agent

LangSmith Engine 正式发布，这是一个"用 Agent 改进 Agent"的元系统。配合 SmithDB（Agent 可观测性的专用数据层）、LangSmith Sandboxes GA、Context Hub 等功能，LangChain 正在构建覆盖整个 Agent 开发周期的平台。同期发布的还有 The Agent Development Lifecycle (ADLC) 框架、Deep Agents v0.6（支持 Delta Channels 用于长时间运行 Agent 的流式通信）、以及 Managed Deep Agents 托管服务。"From Token Streams to Agent Streams" 一文提出了从 Token 级流式到 Agent 级流式的范式升级。

📎 [LangChain Blog · Interrupt 2026, May 13-21](https://www.langchain.com/blog)

### 🔄 AutoGen 0.4+：事件驱动多 Agent 架构 + MCP 原生集成

Microsoft AutoGen 已演进至 0.4+ 版本，采用三层架构：**Core**（事件驱动编程框架，支持分布式 Agent）、**AgentChat**（对话式单/多 Agent 应用）、**Extensions**（与外部服务集成）。关键更新：(1) 原生内置 **McpWorkbench**，直接对接 MCP 服务器生态；(2) AutoGen Studio 提供无代码 Agent 原型设计 Web UI；(3) 支持 DockerCommandLineCodeExecutor 的安全代码执行；(4) GrpcWorkerAgentRuntime 支持分布式 Agent 部署。标志着 AutoGen 从实验框架走向生产级多 Agent 系统。

📎 [AutoGen Docs · 2026](https://microsoft.github.io/autogen/stable/)

### 🚢 CrewAI：面向生产的多 Agent 编排系统

CrewAI 持续强化企业级多 Agent 系统能力：支持 **Agents + Tasks + Flows + Crews** 的多层抽象，提供 Sequential/Hierarchical/Hybrid 多种编排模式。新增 Enterprise 功能：(1) Automation Triggers——支持 Gmail、Slack、Salesforce、HubSpot 等外部触发；(2) RBAC 团队管理和访问控制；(3) 集成工具包可调用已有 CrewAI Automation 或 Amazon Bedrock Agents；(4) Memory、Knowledge、Guardrails 内置支持。定位为"从第一天就面向生产"的多 Agent 框架。

📎 [CrewAI Docs · 2026](https://docs.crewai.com/)

> **💡 CTO 洞见：** Agent 框架生态正在从"能跑就行"进化到"生产可用"。三条主线值得关注：LangChain 的 Data→Trace→Improvement 闭环、AutoGen 的事件驱动 + 分布式架构、CrewAI 的企业编排能力。对于 CHANG_AI_TEAM 而言，LangSmith 的可观测性和 Deep Agents 的长时间运行能力是最值得深入评估的方向。

---

## 🛡️ 四、Agent 安全与评估 — 前沿论文与框架

学术和工业界对 AI Agent 安全性的关注度急剧上升。近期 arXiv 涌现大量 Agent 安全相关论文，涵盖攻击面分析、动态红队测试、可信代码 Agent、渗透测试对比等。

### 📄 SoK: The Attack Surface of Agentic AI — Tools, and Autonomy

Dehghantanha & Homayoun 系统化了 Agentic AI 的攻击面，将现代 AI Agent 系统（LLM + 工具 + RAG + 自主多步能力）的安全威胁分类为工具滥用、知识投毒、自主权限滥用和链式攻击。该 SoK（Systematization of Knowledge）是 Agent 安全研究领域的重要参考框架。

📎 [arXiv · March 2026](https://arxiv.org/search/?query=SoK+Attack+Surface+Agentic+AI&searchtype=all)

### 📄 DREAM: Dynamic Red-teaming across Environments for AI Models

Lu 等人提出 DREAM 框架，针对 Agent 系统中的动态多阶段安全挑战进行红队测试。传统基准测试多为静态单轮评估，无法捕捉 Agent 在长链路攻击中的漏洞。DREAM 支持跨环境自适应红队测试，填补了 Agent 安全评估的关键空白。

📎 [arXiv · Feb 2026 (updated)](https://arxiv.org/search/?query=DREAM+Dynamic+Red-teaming+AI+Models&searchtype=all)

### 📄 Reflection-Driven Control for Trustworthy Code Agents

Wang 等人提出 Reflection-Driven Control，一种可热插拔的控制模块，可无缝集成到通用 LLM Agent 中。该模块通过反射(Reflection)机制实时审查 Agent 行为，防止不可预测或有害的输出。在 Code Agent 场景中，该模块不需要修改底层模型即可提供安全护栏。

📎 [arXiv · Dec 2025](https://arxiv.org/search/?query=Reflection-Driven+Control+Trustworthy+Code+Agents&searchtype=all)

### 📄 BashArena: A Control Setting for Highly Privileged AI Agents

Kaufman 等人提出 BashArena，一个评估高权限 AI Agent（如可直接执行 Shell 命令的编码 Agent）安全性的控制实验平台。面对未来 AI 系统可能获得更高系统权限的趋势，BashArena 提供了衡量 Agent 在真实系统环境中安全风险的方法论。

📎 [arXiv · Dec 2025](https://arxiv.org/search/?query=BashArena+Control+Setting+AI+Agents&searchtype=all)

### 📄 Penetration Testing of Agentic AI: Comparative Security Analysis

Nguyen & Husain 对不同模型和框架下的 Agentic AI 系统进行了渗透测试对比分析，评估了主流 LLM Agent 在面对 Prompt 注入、越狱和权限提升攻击时的安全表现差异。

📎 [arXiv · Dec 2025](https://arxiv.org/search/?query=Penetration+Testing+Agentic+AI+Comparative&searchtype=all)

### 🔬 ExploitBench & ExploitGym：AI Agent 漏洞利用能力基准

两个新发布的学术基准——[ExploitBench](https://exploitbench.ai/) 和 [ExploitGym](https://arxiv.org/abs/2605.11086)——专门评估 AI 模型的漏洞利用开发能力。Claude Mythos Preview 在两个基准上均是最强表现者。这标志着 Agent 安全评估从"单轮对话安全"向"多步攻击能力"的范式转变。

📎 [ExploitBench](https://exploitbench.ai/) · [ExploitGym (arXiv)](https://arxiv.org/abs/2605.11086) · May 2026

> **💡 CTO 洞见：** Agent 安全正从"事后补救"走向"设计即安全"（Security by Design）。关键趋势：(1) 动态红队测试取代静态评估；(2) 反射/审计模块成为 Agent 标准组件；(3) 漏洞利用基准成为模型能力新标尺。对于计划部署 Agent 的团队，建议从第一天就建立 Sandbox + Audit Log + Reflection Control 的三层安全防线。

---

## 📚 术语速查

- **Agentic Misalignment**：AI Agent 在追求给定目标时采取与人类价值观/预期不符的行为
- **ADLC (Agent Development Lifecycle)**：LangChain 提出的 Agent 开发全生命周期框架
- **Delta Channels**：LangGraph 中用于长时间运行 Agent 的增量流式通信通道
- **McpWorkbench**：AutoGen 中对接 MCP（Model Context Protocol）服务器的原生工具
- **OOD (Out-of-Distribution)**：训练数据分布之外的场景，衡量模型泛化能力
- **Write-Restricted Token**：Windows 安全原语，用于限制进程的文件写入权限

---

## 🔗 参考链接

- [Gartner 2026: OpenAI Codex 被评为 Agentic Coding 领导者](https://openai.com/index/gartner-2026-agentic-coding-leader/)
- [Codex 移动端上线 + Remote SSH GA](https://openai.com/index/work-with-codex-from-anywhere/)
- [Codex Windows 沙箱工程实践](https://openai.com/index/building-codex-windows-sandbox/)
- [Dell × Codex 企业混合云部署](https://openai.com/index/dell-codex-enterprise-partnership/)
- [Project Glasswing: 发现 10,000+ 高危漏洞](https://www.anthropic.com/research/glasswing-initial-update)
- [Teaching Claude Why: misalignment 降至 0%](https://www.anthropic.com/research/teaching-claude-why)
- [Anthropic 官方新闻](https://www.anthropic.com/news)
- [LangChain Labs 持续学习](https://www.langchain.com/blog/introducing-langchain-labs)
- [AutoGen 0.4+ 官方文档](https://microsoft.github.io/autogen/stable/)
- [CrewAI 企业编排文档](https://docs.crewai.com/)

---

*CHANG_AI_TEAM · AI Harness 技术调研周报 · 第 1 期 · 2026-05-26*
