---
type: concept
title: "流处理系统代际演化"
tags: [stream-processing, architecture, history]
status: stable
sources:
  - sources/papers/SP-Survey/精读分析.md
related:
  - 流处理乱序数据管理
  - 流处理状态管理
  - 流处理容错模型
  - Dataflow-Model
created: 2026-06-15
---

# 流处理系统代际演化

## 定义

流处理系统经历了三个代际的演化，每代有不同的架构哲学、处理模型和能力边界。

## 三代分类

| 代际 | 时间 | 代表系统 | 核心特征 |
|------|------|---------|----------|
| 1st Gen (DSMS) | 2000–2010 | STREAM, Aurora/Borealis, TelegraphCQ, Gigascope | Scale-up 单机架构，有序处理，关系型流模型（CQL），流是演变的关系 |
| 2nd Gen (Dataflow) | 2011–2022 | Storm, Flink, Spark Streaming, Beam, Kafka Streams | Scale-out 分布式 Shared-Nothing 架构，数据流模型，原生无序处理，System-Managed State |
| 3rd Gen (Emerging) | 2022– | Ray, Stateful Functions, Neptune, Ambrosia | 事件驱动架构，定点计算，硬件加速，微服务集成 |

## 关键分野

- **1st → 2nd 的跳跃**：从"流即关系"到"流即事件"，状态管理从系统内部 Synopsis 变为用户定义+系统管理，容错从 Best-Effort 到 Exactly-Once on State
- **2nd → 3rd 的跳跃**：从数据流 Job/DAG 到事件驱动微服务，从流处理引擎到通用计算框架集成

## 相关

- [[Stream Processing]] / [[Dataflow-Model]] / [[流处理状态管理]] / [[流处理容错模型]]
