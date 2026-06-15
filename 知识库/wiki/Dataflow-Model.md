---
type: concept
title: "Dataflow 模型"
tags: [stream-processing, dataflow, google, batch-processing, windowing]
status: stable
sources:
  - sources/papers/SP-Survey/精读分析.md
related:
  - 流处理乱序数据管理
  - 流处理状态管理
  - Stream-Processing-System-Generations
created: 2026-06-15
---

# Dataflow 模型

## 定义

Google Dataflow Model（Akidau et al., VLDB 2015）是首个批流统一处理模型。它提出四条核心抽象，将批处理定义为流处理的特殊情形（有界数据流）。

## 四条核心抽象

### 1. 时间域分离
- **Event Time**：事件发生的真实时间
- **Processing Time**：系统观察到事件的墙上时钟时间
- **Ingestion Time**：事件进入系统的时间

分离的意义：允许按事件时间做正确计算，同时用处理时间做低延迟近似。

### 2. Watermark
- 事件时间进度的估计：系统声明"在时间戳 T 之前的所有事件，我相信都已收到"
- 完美 Watermark 不存在——是启发式估计
- Watermark 延迟 = 结果正确性 vs 结果延迟的权衡

### 3. Trigger
触发条件决定"何时物化窗口结果"：
- Watermark 触发：Watermark 越过窗口边界
- Processing Time 触发：墙上时钟到达某时刻
- 计数触发：N 个元素到达
- 复合触发：上述的组合

### 4. Refinement
修正策略决定"如何处理迟到数据对早期结果的影响"：
- **Accumulating**：新结果覆盖旧结果
- **Discarding**：新结果独立存在，不合并
- **Accumulating & Retracting**：收回旧结果，发布新结果（最完整但最重）

## 批流统一

```
批处理 = 有界数据流 + 全局聚合
流处理 = 无界数据流 + 窗口聚合
```

同一个模型、同一套 API 处理批和流——这是 Beam 和 Flink 的哲学基础。

## 影响

- 直接催生了 Apache Beam 项目
- 成为 2nd Gen 流处理系统的标准语义模型
- 用 What / Where / When / How 四问统一了所有窗口计算

## 相关

- [[流处理乱序数据管理]] / [[Stream-Processing-System-Generations]] / [[Flow-Control-Backpressure]]
