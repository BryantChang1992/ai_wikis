---
type: concept
title: "ByteHouse 云原生多模态数仓—整体架构"
sources:
  - "sources/papers/ByteHouse/ByteHouse-SIGMOD2026.pdf"
  - "sources/papers/ByteHouse/精读分析.md"
tags:
  - ByteHouse
  - OLAP
  - 云原生
  - 存算分离
  - Multi-modal
  - SIGMOD-2026
  - ByteDance
created: 2026-06-15
updated: 2026-06-15
status: draft
related:
  - "[[ByteHouse-统一表引擎]]"
  - "[[ByteHouse-多模态查询优化]]"
  - "[[Doris-深度调研]]"
  - "[[事务模型深度调研]]"
diagram: "diagram/bytehouse-architecture.svg"
---

# ByteHouse 整体架构 — 三层存算分离

## 定义

ByteHouse 是 ByteDance 自研的云原生分析数据仓库，采用 **控制-计算-存储三层完全解耦** 的 shared-storage 架构，同时支持结构化 OLAP 和非结构化向量检索。已服务 400+ 内部业务。

## 三层架构

```
Control Layer  → SQL 解析 + HBO 优化 + 元数据 + 全局事务
Compute Layer  → APM / SBM / IPM 三模式执行引擎 + 向量索引
Storage Layer  → Unified Table Engine + CrossCache + NexusFS
```

### Control Layer

| 组件 | 职责 |
|------|------|
| Server | SQL 解析、语义分析、HBO 优化、分布式调度 |
| Catalog Manager | 版本化元数据存储 (ByteKV)，快照一致的 schema/分区/索引 |
| Global Transaction Manager | 全局有序 commit timestamp → 可串行化 + 一致性快照读 |
| Daemon Manager | 后台任务编排：Compaction、Merge 调度 |

### Compute Layer

三种执行模式共享同一优化器和运行时：

- **APM (Analytic Pipeline Mode)**：分布式 MPP，shuffle/gather/broadcast
- **SBM (Staged Batch Mode)**：ETL 长任务，阶段重试 + shuffle 持久化
- **IPM (Incremental Processing Mode)**：增量执行，lineage 追踪 + 版本化算子

索引支持：Min-Max, Set, Bloom, HNSW/IVF 向量索引。Arrow 零拷贝数据交换。

### Storage Layer

详见 [[ByteHouse-统一表引擎]]。关键创新：

- **Sniffer 格式**：自描述列式，数据+索引+元数据 colocate
- **CrossCache**：独立 SSD 集群缓存，一致性哈希分片
- **NexusFS**：虚拟文件系统，统一本地 SSD + Cache + 对象存储

## 与同类系统对比

| 维度 | ByteHouse | Doris | ClickHouse | Snowflake |
|------|-----------|-------|------------|-----------|
| 架构 | 三层解耦 | 存算一体→分离 | 存算一体 | 多集群共享存储 |
| 多模态 | ✅ 原生向量索引 | ❌ | ❌ | ❌ |
| 优化器 | HBO + ML | Nereids CBO | 基于语法规则 | CBO + 结果缓存 |
| 增量执行 | IPM (lineage) | 物化视图增量 | Refreshable MV | 物化视图+Streams |
| 缓存 | CrossCache SSD 集群 | 本地磁盘 | 本地磁盘 | SSD 缓存层 |
