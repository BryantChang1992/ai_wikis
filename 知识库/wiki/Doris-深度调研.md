---
type: survey
title: "Apache Doris 实时分析数据库深度调研"
sources:
  - "技术文章/Doris调研.md"
  - "技术文章/Doris调研/01-概述与核心概念.md"
  - "技术文章/Doris调研/02-存储引擎.md"
  - "技术文章/Doris调研/03-查询流程.md"
  - "技术文章/Doris调研/04-架构演进.md"
  - "技术文章/Doris调研/05-元数据存储与一致性复制.md"
tags:
  - 数据库
  - OLAP
  - Doris
  - MPP
  - 实时分析
  - 列式存储
  - 存算分离
  - 调研报告
created: 2026-06-14
updated: 2026-06-14
status: final
author: Stark (CTO, CHANG_AI_TEAM)
related:
  - "[[Doris-数据模型]]"
  - "[[Doris-Segment-v2-存储格式]]"
  - "[[Doris-Compaction-策略]]"
  - "[[Doris-MPP-向量化查询引擎]]"
  - "[[Doris-Nereids-CBO-优化器]]"
  - "[[Doris-架构演进]]"
  - "[[Doris-元数据与一致性复制]]"
  - "[[事务模型深度调研]]"
  - "[[LSM-Tree]]"
  - "[[LSM-Tree-RUM猜想]]"
---

# Apache Doris 实时分析数据库深度调研

## 概述

Apache Doris 是百度于 2017 年开源、2022 年 Apache 毕业的 **MPP 架构实时分析数据库**。专为 OLAP 设计，支持高并发、低延迟多维分析和实时报表查询。C++ 实现 BE（计算+存储），Java 实现 FE（元数据+查询规划）。

## 历史沿革

| 时期 | 名称 | 关键事件 |
|------|------|----------|
| 2013~2017 | Palo (内部) | 百度广告报表驱动，C++ 实现 |
| 2017~2022 | Palo → Doris | 开源，Apache 孵化器，2022 毕业 |
| 2022~2024 | Doris 1.x~2.x | 功能爆发：Unique Key MoW、倒排索引、湖仓一体 |
| 2024.07 | Doris 3.0 | **存算分离架构**正式发布 |
| 2025+ | Doris 3.x~4.x | Nereids 优化器、Falcon 新引擎、Parquet 原生支持 |

## 核心架构 (Doris 3.0)

### Shared-Nothing 模式 (v1.x~v2.x，3.0 也支持)
- **FE (Frontend)**：Java 实现，元数据管理（BDB-JE）、查询解析、计划调度
- **BE (Backend)**：C++ 实现，Segment v2 列式存储 + 向量化查询执行
- FE 多 Master-Follower，BDB-JE 类 Paxos 复制保证一致性
- 数据多副本通过 Tablet 机制实现

### 存算分离模式 (v3.0+)
- **Compute Group**：计算集群（BE），可弹性扩缩
- **Remote Storage**：S3/HDFS/MinIO 对象存储持久层
- **File Cache**：本地 SSD 缓存，保证查询性能
- **Meta Service**：集中式元数据服务（替代 BDB-JE 单机瓶颈）

## 数据模型

| 模型 | 场景 | 写入语义 | 说明 |
|------|------|----------|------|
| **Duplicate** | 明细、日志 | Append-only | 最高吞吐 |
| **Aggregate** | 预聚合指标 | 同 Key 聚合 (SUM/MAX/MIN) | 写入有聚合开销 |
| **Unique (MoW)** | 主键更新 (CDC) | 写入时 UPSERT | 查询最优，写入有去重开销 |
| **Unique (MoR)** | 追加为主 | 追加查询时合并 | 写入快，查询慢 |

MoW (Merge-on-Write) 是 Doris 2.1+ 默认推荐策略。

## 存储引擎

自研 Segment v2 列式格式，基于 LSM-tree 写入思想。以 Page (1MB) 为 I/O 最小单元，支持 RLE + Bit-Packing 压缩。多层索引：前缀索引 → ZoneMap → Bloom Filter → Bitmap/Inverted Index。MoW 通过 DELETE_BITMAP 实现写入时去重。

## 查询引擎

自研 C++ 向量化引擎，4096 行/Batch 流水线处理，SIMD (SSE/AVX2) 加速。MPP 分布式执行：Plan Fragment 分发 + BRPC 数据交换。Shuffle 策略：Broadcast / Hash / Bucket Shuffle / Colocate Join。Nereids CBO 优化器 (v3.0 稳定) 支持 Join Reorder、CTE 物化、Runtime Filter。

## 关键差异化优势

Doris 在 **Upsert (MoW) + 高并发查询 + 实时导入** 三个维度形成独特优势组合，这是 ClickHouse/Impala 无法同时覆盖的。

| 维度 | Doris | ClickHouse | StarRocks | Impala |
|------|-------|------------|-----------|--------|
| Upsert | ★★★★★ | ★★ | ★★★★ | ★★ |
| 高并发 | ★★★★ | ★★ | ★★★★ | ★★ |
| 实时导入 | ★★★★★ | ★★★ | ★★★★ | ★★ |
| 湖仓一体 | ★★★★ | ★★★ | ★★★★ | ★★★★★ |
| 存算分离 | ★★★★ | ★★★★★ | ★★★★ | ★★ |

## 选型建议

| 场景 | 推荐 |
|------|------|
| 实时报表/多维分析 | Doris 3.x |
| 广告归因/用户行为 | Doris 3.x Unique MoW |
| 日志+全文搜索 | Doris + Inverted Index |
| 数据湖查询加速 | Doris Lakehouse |
| IoT 时序/监控 | InfluxDB 或 ClickHouse |
| ETL 宽表加工 | Doris 2.x/3.x |

## 对 CHANG_AI_TEAM 的建议

对于可观测性平台项目，Doris 定位为**分析层**而非热存储层。热指标仍用 InfluxDB，Doris 聚焦聚合结果和用户行为分析。关注 3.x 存算分离降低成本、提升弹性。
