---
type: concept
title: "Dataflow 模型"
sources:
  - "sources/papers/SP-Survey/SP-Survey-arXiv2020.pdf"
  - "sources/papers/SP-Survey/精读分析.md"
tags:
  - 流处理
  - Dataflow
  - Google
  - 批流统一
  - Watermark
  - 窗口计算
created: 2026-06-15
updated: 2026-06-15
status: stable
related:
  - "[[流处理乱序数据管理]]"
  - "[[流处理状态管理]]"
  - "[[Stream-Processing-System-Generations]]"
---

# Dataflow 模型

![Architecture Diagram](../diagram/dataflow-model.svg)
## 定义

**Google Dataflow Model**（Akidau et al., VLDB 2015）是首个**批流统一处理模型**，将批处理定义为流处理的特殊情形（有界数据流）。它用四条核心抽象统一了过去分散在多个系统中的乱序处理、进度追踪、触发和修正机制。

论文的评价：Dataflow Model 是**2nd Gen 流处理系统的里程碑**——它把 Punctuation、Low-Watermark、Revision Processing 等 1st Gen 的概念重新组合，形成通用框架。

## 批流统一的基础


<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 580 130" width="580" height="130">
  <rect x="30" y="5" width="520" height="120" rx="8" fill="transparent" stroke="currentColor" stroke-width="1.5"/>
  <text x="290" y="28" font-family="sans-serif" font-size="13" fill="currentColor" text-anchor="middle" dominant-baseline="middle" font-weight="bold">Dataflow Model</text>
  <line x1="60" y1="38" x2="520" y2="38" stroke="currentColor" stroke-width="0.8"/>
  <text x="290" y="60" font-family="sans-serif" font-size="12" fill="currentColor" text-anchor="middle" dominant-baseline="middle">批处理 = 有界数据流 + 全局聚合</text>
  <text x="290" y="82" font-family="sans-serif" font-size="12" fill="currentColor" text-anchor="middle" dominant-baseline="middle">流处理 = 无界数据流 + 窗口聚合</text>
  <line x1="60" y1="98" x2="520" y2="98" stroke="currentColor" stroke-width="0.8"/>
  <text x="290" y="115" font-family="sans-serif" font-size="12" fill="currentColor" text-anchor="middle" dominant-baseline="middle">同一模型、同一 API 处理批和流</text>
</svg>

> 这直接催生了 Apache Beam 项目，并成为 Flink、Spark Structured Streaming 等系统的语义基础。

## 四条核心抽象

### 1. 时间域的三维分离

| 时间域 | 定义 | 使用场景 |
|--------|------|---------|
| **Event Time** | 事件发生的真实时间（数据自带的元数据） | **正确性计算**：按事件真实时间聚合 |
| **Processing Time** | 系统观察到事件的墙上时钟时间 | **低延迟近似**：不考虑乱序 |
| **Ingestion Time** | 事件进入系统的时间 | 折中：保证同一批次的一致性 |

> 分离的意义：允许系统按 Event Time 做正确计算，同时按 Processing Time 做低延迟近似。这是 Watermark 机制成立的前提。

### 2. Watermark — 事件时间进度估计

- 系统声明："在时间戳 T 之前的所有事件，我相信都已收到"
- **完美 Watermark 不存在** —— 它是启发式估计
- Watermark 延迟 = **结果正确性 vs 结果延迟**的权衡：
  - 激进 Watermark → 低延迟但可能缺少迟到数据
  - 保守 Watermark → 高正确性但高延迟

### 3. Trigger — 何时物化窗口结果

触发条件决定"何时将窗口的中间/最终结果发布出去"：

| 触发类型 | 条件 | 适用场景 |
|----------|------|---------|
| **Watermark 触发** | Watermark 越过窗口边界 | 期望完整结果的批处理 |
| **Processing Time 触发** | 墙上时钟到达某时刻 | 低延迟仪表盘 |
| **计数触发** | N 个元组到达 | 实时告警（每 X 个事件触发一次） |
| **复合触发** | 上述的组合（AND/OR） | 复杂事件处理 |
| **用户自定义** | 任意自定义逻辑 | 业务特定需求 |

### 4. Refinement — 如何修正早期结果

当迟到数据到达时，已发布的早期结果需要修正：

| 策略 | 行为 | 适用场景 |
|------|------|---------|
| **Accumulating** | 新结果覆盖旧结果 | 最终一致性场景（如最终计数） |
| **Discarding** | 新结果独立存在，不合并 | 仅关心增量（如增量异常检测） |
| **Accumulating & Retracting** | 收回旧结果 + 发布新结果 | 严格正确性场景（如金融结算） |

> StreamInsight 的**补偿（Compensation）**机制是最早的 Retraction 实现之一。

## 与 1st Gen 概念的血缘关系

Dataflow Model 并非凭空创造——它重新组合了 1st Gen 的多项技术：

| Dataflow 概念 | 1st Gen 前身 | 前身系统 |
|--------------|-------------|---------|
| Watermark | Low-Watermark + Heartbeat | STREAMS, Naiad |
| Watermark 传播 | Punctuation | Aurora, Naiad |
| Trigger | Revision Processing (Store & Revise) | CEDR, Borealis |
| Refinement (Retract) | Dynamic Revision (delta messages) | Borealis |
| 事件/处理时间分离 | Slack（用户配置的延迟上界） | Aurora |

## What / Where / When / How 四问

Dataflow Model 的核心贡献是将所有窗口计算统一到四个问题：

| 问题 | 含义 | Dataflow 抽象 |
|------|------|-------------|
| **What** | 做什么计算？ | ParDo, GroupByKey, Combine, Flatten 等 |
| **Where** | 在哪个时间窗口？ | Fixed / Sliding / Session Windows |
| **When** | 何时物化结果？ | Trigger（Watermark/P-Time/Count/Composite） |
| **How** | 如何修正？ | Refinement（Accumulating/Discarding/Retracting） |

## 影响与现状

- 直接催生了 **Apache Beam** 项目（Google Dataflow SDK 开源版）
- Flink 的 DataStream API 采用相同语义模型
- Spark Structured Streaming 也与之对齐
- 成为 2nd Gen 流处理系统的**事实标准语义层**

## 相关

- [[流处理乱序数据管理]] — Watermark/Punctuation 机制的完整分析
- [[Stream-Processing-System-Generations]] — Dataflow Model 在代际演化中的位置
- [[流处理状态管理]] — 批流统一对状态管理的影响

---

*参考论文: Fragkoulis et al., "A Survey on the Evolution of Stream Processing Systems", arXiv:2008.00842v2, 2023*
*核心参考: Akidau et al., "The Dataflow Model: A Practical Approach to Balancing Correctness, Latency, and Cost in Massive-Scale, Unbounded, Out-of-Order Data Processing", VLDB 2015*
