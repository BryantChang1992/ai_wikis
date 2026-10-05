---
type: concept
title: Apache Flink 2.3.0 — SQL 层与存储层重大升级
sources:
- '[[知识库/sources/web/flink-2.3.0/精读分析]]'
- https://flink.apache.org/2026/06/25/apache-flink-2.3.0-release-announcement/
tags:
- 流处理
- Flink
- SQL
- S3
created: 2026-07-03
updated: 2026-07-03
status: draft
related:
- '[[知识库/wiki/synthesis/流处理系统演化综述]]'
- '[[知识库/wiki/Stream-Processing-System-Generations]]'
- '[[知识库/wiki/Fluss-整体架构]]'
confidence: 0.8
confidence_rationale: 类型=concept; 来源×1; 更新于3天前
synced_at: '2026-10-05'
blog_url: https://bryantchang1992.github.io/ai_memory_chang_ai_team/knowledge/Apache-Flink-2.3.0-版本发布/
blog_source: _posts/2026-07-03-knowledge-fa0e811bb3.md
---

# Apache Flink 2.3.0 — SQL 层与存储层重大升级

## 一句话

Flink 2.3.0 以 FROM_CHANGELOG/TO_CHANGELOG 双向 SQL 算子 + Materialized Table DDL + Native S3 FS 三大支柱，实现 SQL 层和存储层的代际升级。

## 版本定位

实现 **15 个 FLIP** 的核心/完整功能。发布日期：2026-06-25。同周期补丁 Flink 2.1.3（5 个 bug 修复）。

## 三大支柱特性

### 1. FROM_CHANGELOG / TO_CHANGELOG

SQL 层首次实现 append-only ↔ changelog 双向转换（此前只在 DataStream API 可用）。

| 算子 | 方向 | 用途 |
|------|------|------|
| FROM_CHANGELOG | append-only → 动态表 | 自定义 CDC 格式注入 Flink SQL |
| TO_CHANGELOG | 动态表 → append-only | 归档/审计/写入 append-only sink |

**TO_CHANGELOG 的历史意义**：Flink SQL 第一次可以在 SQL 层面将 retract/upsert 流转为 append-only——这在之前是 SQL 层的长期能力缺口。

参考：FLIP-564

### 2. Materialized Table 一等公民化

| 能力 | 说明 |
|------|------|
| 显式列定义 | watermark/PK 与普通表一致 |
| DDL 演化 | ADD/MODIFY/DROP/RENAME 列 |
| START_MODE | 精确控制 refresh 起点，避免不必要重处理 |

消除"物化表二等公民"状态，彻底解决改 query 需要 drop & recreate 的运维痛点。

参考：FLIP-550, FLIP-557

### 3. Native S3 FileSystem

全新 `flink-s3-fs-native` 插件，基于 AWS SDK v2，完全脱离 Hadoop/Presto：

- 异步 I/O、零 Hadoop 依赖
- 统一的 FileSystem + RecoverableWriter（exactly-once sink）
- IRSA 原生支持（EKS IAM Roles for Service Accounts）
- 独立 `s3.*` 配置命名空间

### 其他重要特性

| 特性 | 关键点 | 参考 |
|------|--------|------|
| **SinkUpsertMaterializer ON CONFLICT** | DO NOTHING / DO ERROR / DO DEDUPLICATE + watermark compaction | FLIP-558 |
| **Adaptive Partition Selection** | 基于下游负载动态分区 | FLIP-339 |
| **Watermark Alignment** | buffer 机制消除积压处理瓶颈 | FLINK-37399 |
| **Checkpointing During Recovery** | 恢复期间触发 checkpoint | FLIP-547 |
| **PTF 增强** | late data handling + ORDER BY args | FLIP-565 |
| **AdaptiveScheduler Rescale History** | Web UI 可视化 rescale 历史 | FLIP-487/495 |
| **ARTIFACT 关键字** | 通用 UDF 资源关键字（替代 JAR） | FLIP-559 |

## 关键 Bug 修复

MiniBatchGroupAggFunction 中仅含 retractions 的 minibatch 导致丢数据（FLINK-35661），2.3 已修复。

## 与流处理生态的关系

Flink 2.3.0 的 FROM_CHANGELOG/TO_CHANGELOG 与 [[Fluss-整体架构]] 的 changelog 流有天然的协作空间——Fluss 作为 Kafka 兼容的实时数据湖存储，其 changelog 流正是 FROM_CHANGELOG 的理想输入源。同时 Native S3 FS 的实验性引入，为 Fluss + Paimon + Flink 的 S3-based 湖仓架构完成了基础设施闭环。
