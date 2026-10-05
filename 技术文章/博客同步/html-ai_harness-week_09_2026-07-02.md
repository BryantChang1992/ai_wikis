---
type: analysis
title: 🧠 Week 09 · AI Infra & Agent 基础设施
blog_url: https://bryantchang1992.github.io/ai_memory_chang_ai_team/tech_research/ai_harness/week_09_2026-07-02.html
blog_source: tech_research/ai_harness/week_09_2026-07-02.html
blog_source_commit: f83970fa7e6ad32d626cc6ca3ba7428c90a638a5
synced_at: '2026-10-05'
tags:
- 博客同步
---

# 🧠 Week 09 · AI Infra & Agent 基础设施

2026-07-02 · 覆盖周期 2026-06-26 ~ 2026-07-02

## 🔥 Hermes Agent：自进化 Agent 登顶 OpenRouter #1

本周 AI Agent 领域的最大事件是 Nous Research 的 Hermes Agent 达到 **140,000+ GitHub Stars** 并被 OpenRouter 列为全球使用量最高的 Agent 应用。Nvidia 官方博客发文推荐，将 Hermes 与其 RTX 硬件生态绑定推广。

### 四个核心差异化能力

| 能力 | 描述 |
| --- | --- |
| **Self-Evolving Skills** | 遇到复杂任务或收到反馈后，自动将经验保存为可复用 Skill。基于 **ICLR 2026 Oral** 论文的 DSPy + GEPA 框架实现 skill 自进化（MIT licensed）。 |
| **Contained Sub-Agents** | 子 Agent 作为短生命周期隔离 Worker，专注子任务，聚焦上下文 + 工具集。减少主 Agent 混乱，适配本地小模型。 |
| **Reliability by Design** | Nous Research 对每个内置 skill/tool/plugin 进行压力测试，30B 参数级模型即可稳定运行，"just works"。 |
| **Active Orchestration Layer** | 不是薄 wrapper，而是主动编排层。同一模型在不同框架下，Hermes 表现一致更强。 |

### 技术栈与生态

- Provider-agnostic（支持 Anthropic/OpenAI/Google/DeepSeek + 本地 Ollama），模型中立设计
- 16+ 消息平台集成（包括 Discord、Telegram、Signal 等）
- 持久化 Memory 跨 session 累积、Cron 定时任务调度
- Nvidia 推荐 DGX Spark（128GB 统一内存）作为"always-on agentic computer"
- 搭配 Qwen 3.6 27B/35B 本地部署，性能超越其前代 120B/400B 级模型

**Insight**：Hermes 的成功标志着 Agent 框架从"胶水代码时代"正式进入"编排引擎时代"。自进化 Skill + 隔离子 Agent 的设计与 Microsoft CodeAct 的"模型写代码替代逐轮 tool call"思路形成互补——前者降低框架复杂度，后者降低推理开销。

## 🧰 JetBrains：2026 AI Agent 框架全景对比

JetBrains 官方博客于 6 月底发布 *Top Agentic Frameworks for Building Applications 2026*，从开发者视角系统对比了当前主流 Agent 框架：

- **LangGraph**：有向循环图编排，适合复杂多步工作流
- **CrewAI**：角色扮演式多 Agent 协作，入门友好
- **AutoGen**：Microsoft 的对话式多 Agent 框架，深度 Azure 集成
- **Semantic Kernel**：Microsoft 的 .NET/C#/Python/Java SDK，企业级编排
- **Hermes Agent**：自进化开源 Agent，本地优先

核心结论：**2026 年 Agent 框架已从实验工具演变为基础设施应用**。关键决策不再是"要不要用 Agent"，而是"需要多少自主性、控制力和治理能力"。

## 🏢 HPE Discover 2026：企业 Agent 战略

HPE 在 Las Vegas Discover 2026 大会上宣布了面向 GreenLake 和 Morpheus 的 Agent AI 扩展，将 Agent 能力绑定到混合云和自动化堆栈中。标志着传统企业基础设施厂商正式进入 Agent 编排市场。

## 🏠 内部产出：Agent Harness 知识图谱修复

本周内部完成了 Agent Harness 系列的 wikilink 图谱修复（Commit `434c840`，2026-06-29）。

- Agent Harness Engineering Survey 综述卡片补全 9 条 wikilink 双向引用
- 8 张子卡片（执行环境、工具接口、上下文管理、编排、可观测性、评估、治理、沙箱）补全 related 字段
- README 索引补全 8 条卡片入口

修复后 Agent Harness 集群的网状引用密度从 ~60% 提升到 100%，为后续 Synthesis Review 打下基础。

📎 相关卡片：
[综述](https://github.com/BryantChang1992/ai_wikis/blob/master/知识库/wiki/Agent-Harness-Engineering-Survey综述.md) ·
[执行环境](https://github.com/BryantChang1992/ai_wikis/blob/master/知识库/wiki/Agent-Harness-Execution-Environment执行环境.md) ·
[工具接口](https://github.com/BryantChang1992/ai_wikis/blob/master/知识库/wiki/Agent-Harness-Tool-Interface工具接口.md) ·
[上下文管理](https://github.com/BryantChang1992/ai_wikis/blob/master/知识库/wiki/Agent-Harness-Context-Memory上下文管理.md) ·
[编排](https://github.com/BryantChang1992/ai_wikis/blob/master/知识库/wiki/Agent-Harness-Lifecycle-Orchestration编排.md) ·
[可观测性](https://github.com/BryantChang1992/ai_wikis/blob/master/知识库/wiki/Agent-Harness-Observability可观测性.md) ·
[评估](https://github.com/BryantChang1992/ai_wikis/blob/master/知识库/wiki/Agent-Harness-Verification-Evaluation评估.md) ·
[治理](https://github.com/BryantChang1992/ai_wikis/blob/master/知识库/wiki/Agent-Harness-Governance治理.md)

## 🤖 Qwen 3.6：支持本地 Agent 部署的新一代模型

Alibaba 发布 Qwen 3.6 系列，核心亮点：

- Qwen 3.6 27B：密集模型，匹配前代 400B 模型精度但仅需 1/16 参数
- Qwen 3.6 35B：~20GB 内存即可运行，超越 120B 级前代模型
- 作为 Hermes Agent 的理想运行底座，Nvidia RTX/DGX Spark 加速推理
