---
type: analysis
title: "Parallax — Agent 安全架构"
sources:
  - "sources/papers/Parallax/arxiv-2604.12986-精读.md"
  - "https://arxiv.org/abs/2604.12986"
tags:
  - "agent-infra"
  - "agent-security"
  - "prompt-injection"
  - "sandbox"
created: 2026-06-19
updated: 2026-06-19
status: draft
related: []
---

# Parallax — Agent 安全架构

## 问题

Prompt-level guardrails 对具备执行能力的 Agent 是**架构性不足**——安全策略与威胁在同一抽象层运行。预测 2026 年底 80% 企业应用将嵌入 AI Copilot，该缺口愈加紧迫。

## Parallax 四原则

| 原则 | 机制 |
|------|------|
| **Cognitive-Executive Separation** | 结构性阻止推理系统执行动作——think 和 act 在不同进程中 |
| **Adversarial Validation with Graduated Determinism** | 推理与执行之间插入独立的多层验证器 |
| **Information Flow Control** | 数据敏感性标签在 Agent 工作流中传播，检测上下文依赖的威胁 |
| **Reversible Execution** | 捕获预破坏状态，验证失败时回滚 |

开源实现：[OpenParallax](https://github.com/openparallax/openparallax) (Go)

## 实验数据

- 280 对抗性测试用例 × 9 攻击类别
- 默认配置：**98.9% 阻断，零误报**
- 最高安全配置：**100% 阻断**
- **Prompt guardrails 在推理系统被攻破时零保护**（两者共存于同一被攻破系统内）

## 关键 Insight

> 让同一个可能被入侵的"大脑"监督自己的行为是安全架构的根本缺陷。**思考与执行必须在架构层面分离**，这是 Agent 安全的第一性原理。
