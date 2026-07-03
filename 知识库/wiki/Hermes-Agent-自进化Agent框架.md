---
type: concept
title: "Hermes Agent — 自进化 Agent 框架"
sources:
  - "sources/web/hermes-agent/精读分析.md"
  - "https://github.com/NousResearch/hermes-agent"
tags:
  - "Agent-First"
  - "Agent-Harness"
  - "自进化"
  - "Skill"
created: 2026-07-03
updated: 2026-07-03
status: draft
related:
  - "[[Agent-Harness-Engineering-Survey综述]]"
  - "[[Agent-Harness-Execution-Environment执行环境]]"
  - "[[Agent-Harness-Lifecycle-Orchestration编排]]"
  - "[[Custom-Agent-Harness-Middleware架构]]"
  - "[[Qwen-3.6-模型发布]]"
  - "[[Agent-框架-2026-全景对比]]"
---

# Hermes Agent — 自进化 Agent 框架

## 一句话定义

由 Nous Research 构建的自进化 AI Agent 框架，首创内建学习循环，2026 年 7 月达到 140k+ GitHub Stars，被 OpenRouter 列为全球使用量最高的 Agent 应用。

## 核心差异化

### 1. Self-Evolving Skills（自进化 Skill）

基于 ICLR 2026 Oral 论文 DSPy + GEPA 框架，遇到复杂任务后自动将经验保存为可复用 Skill。Skills 在使用过程中自我改进，兼容 [agentskills.io](https://agentskills.io) 开放标准。

**机制链**：Agent-curated memory → periodic nudges → autonomous skill creation → self-improvement during use → FTS5 session search + LLM summarization → cross-session recall → Honcho dialectic user modeling。

与 [[Custom-Agent-Harness-Middleware架构]] 中的 Middleware 层不同，Hermes 的 Skill 不是预定义的静态工具链，而是**从经验中动态生长**的过程性记忆。

### 2. Contained Sub-Agents（隔离子 Agent）

子 Agent 在短生命周期隔离环境中运行，通过 RPC 与主 Agent 通信。支持并行 spawn 多个子 Agent，将 multi-step pipeline 压缩为近乎零上下文开销的轮次。

与 [[Agent-Harness-Lifecycle-Orchestration编排]] 的三层编排模型对比：
- Hermes 子 Agent 是 **Task-Scoped Isolated Workers**，比 L2（会话级 Orchestrator）更轻量
- RPC 通信替代了 L3（Tool-level Router）的 function call 模式

### 3. Reliability by Design（设计可靠性）

Nous Research 对每个内置 skill/tool/plugin 进行压力测试。声称 **30B 参数级模型即可稳定运行**（推荐搭配 Qwen 3.6 27B/35B 本地部署）。

### 4. Active Orchestration Layer（主动编排层）

不是薄 wrapper——主动编排层使得同一模型在不同框架下，Hermes 表现一致更强。Provider-agnostic（Anthropic / OpenAI / Google / DeepSeek / Ollama）。

## 生态与技术栈

| 维度 | 实现 |
|------|------|
| **模型供应商** | Anthropic, OpenAI, Google, DeepSeek, Nous Portal, OpenRouter, Ollama |
| **消息平台** | Telegram, Discord, Slack, WhatsApp, Signal, Email, CLI |
| **终端后端** | Local, Docker, SSH, Singularity, Modal, Daytona (serverless) |
| **记忆系统** | FTS5 + LLM summarization + Honcho dialectic user modeling |
| **任务调度** | 内建 cron scheduler + 多平台交付 |
| **安全** | Command approval, DM pairing, container isolation |
| **MCP** | 原生支持 Model Context Protocol |
| **工具生态** | 40+ tools + toolset system + agentskills.io 开放标准 |

## Nvidia 战略合作

Nvidia 官方推荐 **DGX Spark**（128GB 统一内存）作为 "always-on agentic computer"，搭配 **Qwen 3.6 27B/35B** 本地部署。将 Hermes 与 RTX 硬件生态绑定推广。

## 与 OpenClaw 的关系

Hermes 提供 `hermes claw migrate` 命令，可自动从 OpenClaw 导入配置、记忆、Skills、API keys 等。

## 行业意义

Hermes 标志着 Agent 框架从"胶水代码时代"进入"编排引擎时代"：

1. **自进化能力** → 打破"能力天花板由 prompt 决定"的瓶颈
2. **隔离子 Agent + RPC** → 与 Microsoft CodeAct 的"模型写代码替代逐轮 tool call"形成互补
3. **OpenRouter #1** → 证明自进化 Agent 在真实用户中需求远高于链式工具调用

## 待深入

- DSPy + GEPA 框架在 Hermes 中的具体实现细节
- 自进化 Skill 的质量控制与退化检测
- 子 Agent RPC 通信的安全性边界
- 30B 参数模型稳定性声称的实验验证
