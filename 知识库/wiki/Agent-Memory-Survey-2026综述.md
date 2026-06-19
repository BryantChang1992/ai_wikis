---
type: survey
title: "Agent Memory 综述 2026"
sources:
  - "sources/papers/Agent-Memory-Survey/arxiv-2603.07670-精读.md"
  - "https://arxiv.org/abs/2603.07670"
tags:
  - "agent-infra"
  - "agent-memory"
  - "survey"
  - "llm-agents"
created: 2026-06-19
updated: 2026-06-19
status: draft
related: []
---

# Agent Memory 综述 2026

## 概述

LLM Agent 面临的核心约束：单一上下文窗口远不足以承载跨交互的历史、学习和避错信息。**Memory 是将无状态文本生成器转变为自适应 Agent 的关键**。

本文系统化梳理了 2022-2026 年初的 Agent Memory 研究。

## 形式化定义

Agent Memory = **write → manage → read** 循环，与 perception 和 action 紧密耦合：
- **Write**：从交互中提取并用结构化形式存储信息
- **Manage**：整合（consolidation）、遗忘、矛盾消解
- **Read**：在决策点选择性召回最相关信息

## 三维分类法

| 维度 | 含义 |
|------|------|
| **Temporal Scope** | 记忆的时效范围（working/episodic/semantic） |
| **Representational Substrate** | 存储形式（自然语言/向量/结构化/symbolic） |
| **Control Policy** | 何时写入、读取、遗忘的决策策略 |

## 五大机制家族

1. **Context-resident compression**：压缩当前上下文，而非持久化外部存储
2. **Retrieval-augmented stores**：向量/结构化检索增强记忆
3. **Reflective self-improvement**：反思性自我修正，从错误中提取教训
4. **Hierarchical virtual context**：多层虚拟上下文管理
5. **Policy-learned management**：强化学习训练 memory 管理策略

## 评估演进

从静态 recall benchmark → **多会话 agentic 测试**，后者交织记忆与决策，暴露了当前系统的顽固短板。

## 工程挑战

- Write-path filtering（写入时过滤噪声）
- Contradiction handling（矛盾处理）
- Latency budgets（检索延迟预算）
- Privacy governance（隐私治理）

## 开放挑战

**持续整合**（continual consolidation）、**因果驱动检索**、**可信反思**、**学习性遗忘**、**多模态具身记忆**。

## 关键 Insight

> Agent 记忆不是单一功能，而是横跨写入、管理、读取的**系统架构问题**。当前最大瓶颈不是存储容量，而是选择性遗忘和因果准确检索。
