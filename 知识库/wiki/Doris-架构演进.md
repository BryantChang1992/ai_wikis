---
type: concept
title: "Doris 架构演进：Palo → 3.0 存算分离"
sources:
  - "技术文章/Doris调研/04-架构演进.md"
tags:
  - 数据库
  - OLAP
  - Doris
  - 架构演进
  - 存算分离
  - Shared-Nothing
  - MPP
  - 技术决策
created: 2026-06-14
updated: 2026-06-14
status: draft
related:
  - "[[Doris-深度调研]]"
  - "[[Doris-MPP-向量化查询引擎]]"
  - "[[Doris-元数据与一致性复制]]"
---

# Doris 架构演进：Palo → 3.0 存算分离

## 概述

Apache Doris 经历了从百度内部 OLAP 引擎到 Apache 顶级项目的十多年演进，核心架构从 Shared-Nothing MPP 逐步演进到 3.0 的存算分离。

## 演进全景

### Phase 1: Palo (2013~2017) — 百度内部时代

| 维度 | 特征 |
|------|------|
| 背景 | 百度广告报表，MySQL 单机无法满足 |
| 架构 | Shared-Nothing MPP，单 FE + 多 BE |
| 存储 | Segment v1，基础列式，无 Page 级索引 |
| 查询 | C++ 解释执行，无向量化 |
| 数据模型 | 仅 Aggregate 模型 |
| 成就 | 验证 MPP + 列存方案可行性 |

### Phase 2: Doris 0.x (2017~2021) — 开源孵化期

| 维度 | 特征 |
|------|------|
| 架构 | FE 多 Master (BDB-JE replication) |
| 存储 | **Segment v2**：Page 级索引、ZoneMap、Bloom Filter |
| 查询 | **向量化引擎** (SIMD)，性能 5-10x 提升 |
| 数据模型 | 新增 Duplicate、Unique (MoR) |
| 生态 | Routine Load (Kafka)、Broker Load (HDFS/S3)、Colocate Join |

### Phase 3: Doris 1.x~2.x (2022~2024) — 功能爆发期

| 维度 | 特征 |
|------|------|
| 架构 | Shared-Nothing 成熟，FE HA，BE 横向扩展 |
| 存储 | Segment v2 完善，**DELETE_BITMAP** 支持 |
| 数据模型 | **Unique MoW 成为默认** |
| 索引 | **Inverted Index** (全文搜索)、N-Gram Bloom Filter |
| 查询 | **Nereids CBO** (实验→稳定) |
| 湖仓 | Multi-Catalog (Hive/Iceberg/Hudi) |
| 半结构化 | Variant 类型 |
| 运维 | Workload Group、Auto Partition、Arrow Flight SQL |

### Phase 4: Doris 3.0+ (2024~至今) — 存算分离

核心变革：**Compute-Storage Separation**

```
传统 Shared-Nothing                存算分离 3.0
┌──────────────────┐              ┌──────────────────┐
│  FE (BDB-JE)     │              │  FE              │
│  ┌──────┬──────┐ │              │  └→ Meta Service  │ ← 独立元数据层
│  │ BE1  │ BE2  │ │              │                   │
│  │ SSD  │ SSD  │ │              │  Compute Group    │
│  └──────┴──────┘ │              │  ┌──────┬──────┐  │
│  BE3 with SSD    │              │  │ BE1  │ BE2  │  │ ← 弹性扩缩
└──────────────────┘              │  │Cache │Cache │  │
                                  │  └──────┴──────┘  │
                                  │       ↓↓          │
                                  │  Object Store     │ ← S3/HDFS/MinIO
                                  │  (持久数据)       │
                                  └──────────────────┘
```

| 新能力 | 说明 |
|--------|------|
| Remote Storage | S3/HDFS/MinIO 作为持久层 |
| Compute Group | 计算集群弹性扩缩，秒级 |
| File Cache | 本地 SSD 缓存热数据，保证查询延迟不退化 |
| Meta Service | 集中式元数据，替代 BDB-JE 单机瓶颈 |
| 读写分离 | Read/Write Compute Group 独立 |
| 远程 Compaction | 存算分离专用 Compaction |

### Phase 5: 4.x+ Roadmap (2025+)

| 方向 | 说明 |
|------|------|
| **Falcon 执行引擎** | 全新 C++ 向量化引擎 |
| **Parquet 原生存储** | Segment v2 → Parquet，与数据湖生态打通 |
| **Streaming SQL** | 流批一体 |
| **Multi-Warehouse** | 多计算集群共享数据 |
| **AI/ML 集成** | 内置 ML 推理算子、Python UDF |

## 关键架构决策

| 时间 | 决策 | 影响 |
|------|------|------|
| 2013 | C++ 实现 BE | 极致性能基础，无 GC 开销 |
| 2017 | 开源 + Apache 捐赠 | 生态增长 |
| 2021 | Segment v2 + 向量化 | 性能超越 Impala/Kylin |
| 2022 | Unique Key MoW | 实时 Upsert 能力突破 |
| 2023 | Nereids CBO | Join 优化重大提升 |
| 2023 | Multi-Catalog 湖仓 | 联邦查询扩展 |
| 2024 | 存算分离 3.0 | 成本优化 + 弹性扩展 |
| 2025 | 倒排索引 2.0 | 日志搜索直接竞争 ES |

## Shared-Nothing vs 存算分离

| 维度 | 2.x (Shared-Nothing) | 3.x (存算分离) |
|------|---------------------|---------------|
| 存储层 | 本地 SSD/HDD | Object Store (S3/HDFS/MinIO) |
| 弹性扩缩 | 数据重分布，小时级 | 计算秒级弹性 |
| 成本 | 高 (计算+存储绑定) | 低 (按需弹性) |
| 写路径 | MoW 本地 | MoW + 远程 Compaction |
| 读路径 | 本地 Segment | File Cache + 远程拉取 |
| 高可用 | Multi-Replica | Multi-Replica + 远程副本 |
| 成熟度 | 7年+ | 1年+，快速发展 |

## 竞品定位

```
实时分析 OLAP 生态：
┌────────────┬──────────┬──────────┬──────────┐
│ 维度        │ Doris    │ ClickHouse│ StarRocks│
├────────────┼──────────┼──────────┼──────────┤
│ Upsert      │ ★★★★★   │ ★★       │ ★★★★    │
│ 高并发      │ ★★★★    │ ★★       │ ★★★★    │
│ 实时导入    │ ★★★★★   │ ★★★      │ ★★★★    │
│ 湖仓一体    │ ★★★★    │ ★★★      │ ★★★★    │
│ 存算分离    │ ★★★★    │ ★★★★★   │ ★★★★    │
└────────────┴──────────┴──────────┴──────────┘
```

> **核心差异化**：Doris 在 Upsert (MoW) + 高并发查询 + 实时导入三个维度形成独特优势组合。
