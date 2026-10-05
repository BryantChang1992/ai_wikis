---
type: analysis
title: 🧠 AI Infra · Agent 基础设施 — Week 08 (2026-06-25)
blog_url: https://bryantchang1992.github.io/ai_memory_chang_ai_team/tech_research/ai_harness/week_08_2026-06-25.html
blog_source: tech_research/ai_harness/week_08_2026-06-25.html
blog_source_commit: f83970fa7e6ad32d626cc6ca3ba7428c90a638a5
synced_at: '2026-10-05'
tags:
- 博客同步
---

# 🧠 AI Infra · Agent 基础设施 — Week 08 (2026-06-25)

覆盖周期：2026-06-19 ~ 2026-06-25

## 1. Microsoft Agent Framework at BUILD 2026

🔥 本周最重要的发布。MAF 1.0 于 4 月 GA，BUILD 2026 一次性发布三大组件。

### 1.1 Agent Harness

将 **Model + Harness = Agent** 公式产品化。内建能力：

- **Automatic Context Compaction**：token 用量监控 + 对话历史自动压缩，防止长 tool-calling 链 context overflow
- **FileMemoryProvider**：session 级文件内存，agent 可跨轮次持久化笔记
- **TodoProvider**：多步任务管理（add/complete/remove/list）
- **AgentModeProvider**：plan vs execute 模式切换
- **AgentSkillsProvider**：文件系统驱动的技能发现和执行
- **BackgroundAgentsProvider**：子 Agent 并行调度（fan-out）
- **OpenTelemetryAgent**：自动 OTEL SemConv 追踪
- **ToolApprovalAgent**：「不再询问」审批规则

来源：[devblogs.microsoft.com/agent-framework](https://devblogs.microsoft.com/agent-framework/microsoft-agent-framework-at-build-2026-announce/), 2026-06-03

### 1.2 Hosted Agents (Foundry)

从本地开发到生产部署的完整路径：容器化 → Foundry 托管 → 自动扩缩 + 持久化状态 + 可观测性。

- Scale to zero（空闲零成本）
- VM 隔离沙箱 + session 持久化（跨 scale-to-zero）
- OpenTelemetry 自动对接 Application Insights
- .NET 3 行代码 / Python 2 行代码上线

来源：同上

### 1.3 CodeAct + Hyperlight

消除多步工具调用的串行推理瓶颈：模型生成 Python 代码 → `call_tool()` 批量执行 → Hyperlight micro-VM 沙箱。

| 指标 | 传统方式 | CodeAct | 改进 |
| --- | --- | --- | --- |
| 耗时 | 27.81s | 13.23s | **52.4%** ↓ |
| Token | 6,890 | 2,489 | **63.9%** ↓ |

Hyperlight micro-VM 基于 KVM/macOS Hypervisor.framework，每次调用启动全新轻量 VM，执行后销毁。隔离级别 = 硬件级，启动时间极短。

来源：同上 / [github.com/hyperlight-dev/hyperlight](https://github.com/hyperlight-dev/hyperlight)

## 2. Harness Engineering 理论化

Faros AI 系统化阐述 AI 工程三阶段：

| 阶段 | 时期 | 核心学科 | 产出 |
| --- | --- | --- | --- |
| 1. Prompt Engineering | 2022-2023 | 语言 | 代码片段 / 自动补全 |
| 2. Context Engineering | 2024-2025 | 信息 | 上下文感知文件更新 |
| 3. Harness Engineering | 2026 | 环境 | 端到端任务执行 + 验证 |

Mitchell Hashimoto 的核心理念：*「每当 Agent 犯错，不要修改 prompt，要改造 harness——让同一个错误永不再犯。」*

LangChain 实战案例：不改模型，仅优化 harness → Terminal Bench 2.0 排名从第 30 位跃升至第 5 位。

Anthropic 识别的三类模型原生缺陷：

- **Victory Declaration Bias**：不验证就标记完成
- **Context Anxiety**：context window 快满时急于完成，跳过关键步骤
- **One-shotting Overreach**：一次处理全部任务，产生不可审查的大范围变更

来源：[faros.ai/blog/harness-engineering](https://www.faros.ai/blog/harness-engineering), [anthropic.com/engineering/harness-design-long-running-apps](https://www.anthropic.com/engineering/harness-design-long-running-apps)

## 3. 模型架构 2026 H1 趋势

Sebastian Raschka 的论文列表揭示：

- **Hybrid Architecture 主流化**：Nemotron 3 Super (Attention + Mamba-2)、Qwen 3.6 (Attention + Gated DeltaNet)
- **SSM 进化**：Mamba-3（Improved Sequence Modeling）、Gated DeltaNet-2（解耦 Erase/Write）
- **MoE 反思**：Scaling Embeddings Outperforms Scaling Experts — 挑战传统 MoE 容量假设
- **Diffusion LLM**：升格为独立研究方向（被列为第 9 大分类）
- **Agent Harness & Tool Use**：首次被列为独立研究分类（第 6 大分类）

关键论文：

- Nemotron 3 Super (2026-04-13)：120B-A12B MoE，Hybrid Mamba-Transformer，生产环境部署
- Step 3.5 Flash (2026-02-11)：11B 活跃参数达 frontier 级性能
- Scaling Embeddings Outperforms Scaling Experts (2026-01-29)：重思 MoE 设计
- GLM-5 (2026-02-17)：From Vibe Coding to Agentic Engineering

来源：[sebastianraschka.com — LLM Research Papers 2026 Part 1](https://magazine.sebastianraschka.com/p/llm-research-papers-2026-part1)

## 小结

Agent 基础设施从 2025 年的「框架百花齐放」进入 2026 年的「平台化收敛」。Microsoft 三件套确立了 Harness → Execution → Deployment 的完整链路。Harness Engineering 理论化标志着这个领域正在形成自己的工程方法论。
