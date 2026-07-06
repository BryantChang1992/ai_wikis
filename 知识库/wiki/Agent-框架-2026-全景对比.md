---
type: concept
title: "Agent 框架 2026 全景对比"
sources:
  - "sources/web/agent-frameworks-2026/精读分析.md"
tags:
  - "Agent-First"
  - "Agent-Harness"
  - "框架对比"
  - "技术选型"
created: 2026-07-03
updated: 2026-07-03
status: draft
related:
  - "[[Agent-Harness-Engineering-Survey综述]]"
  - "[[Hermes-Agent-自进化Agent框架]]"
  - "[[Custom-Agent-Harness-Middleware架构]]"
confidence: 0.8
confidence_rationale: "类型=concept; 来源×1; 更新于3天前"
---

# Agent 框架 2026 全景对比

## 一句话

2026 年 Agent 框架从"胶水代码时代"进入"编排引擎时代"，关键决策从"用哪个框架"转向"需要多少自主性、控制力和治理能力"。

## 五大框架横向对比

| 框架 | 定位 | 编排风格 | 核心优势 |
|------|------|----------|----------|
| **LangGraph** | 生产级工作流 | 显式状态机/DAG | 精细状态控制、持久化、Human-in-the-loop |
| **CrewAI** | 角色式多 Agent | 团队角色模拟 | 上手门槛低、快速构建 |
| **AutoGen** | 研究导向对话 | 多轮对话协商 | 学术场景成熟、复杂的 Agent 交互 |
| **Semantic Kernel** | 企业级编排 | 插件式集成 | Azure/.NET 深度集成、企业治理 |
| **Hermes Agent** | 自进化个人 Agent | 经验生长式 | 内建学习循环、OpenRouter #1、140k⭐ |

## 决策矩阵

| 需求特征 | 推荐框架 | 原因 |
|----------|----------|------|
| 需要显式状态管理、条件分支 | LangGraph | 图结构编排天生支持 |
| 快速构建多 Agent 协作原型 | CrewAI | 角色模型直观、学习曲线低 |
| 学术研究、复杂对话实验 | AutoGen | 对话式设计成熟 |
| 微软技术栈企业 | Semantic Kernel | Azure 集成 + 企业治理 |
| 个人生产力、持续运行 | Hermes Agent | 自进化、低硬件门槛 |
| 原生平台集成 | OpenAI SDK / Claude SDK | 零额外依赖 |

## 与 Agent Harness Engineering Survey 的关系

[[Agent-Harness-Engineering-Survey综述]] 提出的 ETCLOVG 七层分析框架可应用于这五个框架的比较：
- **Execution Environment（E 层）**：LangGraph 和 Hermes 提供最灵活的多后端支持
- **Tool Interface（T 层）**：Hermes 通过 MCP + RPC 双模式，LangGraph 通过 LangChain 工具生态
- **Context Memory（C 层）**：Hermes 的 Honcho user modeling 是独有设计
- **Lifecycle Orchestration（L 层）**：Hermes 的子 Agent spawn + cron 调度最完善
- **Verification（V 层）**：各框架在评估体系上均较弱，是通用短板
- **Governance（G 层）**：Semantic Kernel 和 LangGraph 在企业治理上领先

## 趋势

1. **编排风格分化**：显式 vs 角色式 vs 对话式 vs 自进化 → 不再是同质化竞争
2. **Vendor SDK 挤压通用框架**：OpenAI/Anthropic 原生 SDK 吸引了大量不想引入第三方框架的用户
3. **自进化成为新范式**：[[Hermes-Agent-自进化Agent框架]] 的经验生长式编排区别于所有传统框架
