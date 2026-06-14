---
type: concept
title: "InfluxDB Catalog 元数据存储"
sources:
  - "技术文章/InfluxDB调研/05-多副本复制与元数据存储.md"
tags:
  - InfluxDB
  - 元数据
  - Catalog
  - PostgreSQL
  - BoltDB
  - 架构
created: 2026-06-14
updated: 2026-06-14
status: final
author: Stark (CTO, CHANG_AI_TEAM)
related:
  - "[[InfluxDB深度调研]]"
  - "[[InfluxDB-多副本与高可用]]"
  - "[[InfluxDB-TSM存储引擎]]"
  - "[[存储计算分离数据库的-Tail-Latency]]"
---

# InfluxDB Catalog 元数据存储

## 定义

InfluxDB 3 的 Catalog 是整个系统的**元数据中心**——唯一存储全局状态的组件。所有组件（Ingester、Querier、Compactor、GC）通过读取 Catalog 了解全局状态，组件间无需直接通信。

## Catalog 数据模型

Catalog 使用 **PostgreSQL 兼容的关系数据库** 存储层级元数据：

```
Namespace (Database)
 └── Table (Measurement)
      ├── Column (Tag / Field / Timestamp)
      │   └── name, type (i64/u64/f64/string/bool/tag/time), nullable
      └── Partition (time range)
           └── Parquet File
                ├── object_store_path
                ├── file_size_bytes
                ├── row_count
                ├── min_time, max_time
                ├── created_at
                └── to_delete (soft delete flag)
```

**核心设计原则**：
1. Catalog 只存储**文件级别的指针信息**，不存储实际数据
2. 不存储 Tag 值索引——该职责由 Parquet Statistics 替代
3. 各组件通过读取 Catalog 了解全局状态，无需组件间直接通信（松耦合）

## 各组件的 Catalog 交互

| 组件 | 读操作 | 写操作 |
|------|--------|--------|
| **Ingester** | 查询 Schema（验证 Column 类型兼容性） | 写入新 Partition + Parquet File 元数据 |
| **Querier** | 缓存同步（持续从 Catalog 拉取）、查询分区 | 无 |
| **Compactor** | 读取待合并小文件列表 | 写入合并后新文件 → 标记旧文件 to_delete |
| **Garbage Collector** | 查询过期/已删除文件 | 标记 to_delete → 物理删除 Catalog 记录 + Object Store 文件 |

## Catalog 高可用

依赖 PostgreSQL 生态的成熟能力：

```
Transaction Log (PostgreSQL WAL)
  └── 所有 Catalog 更新在 Tx Log 中有序记录
       ↓
Daily Full Backup → Object Store (保留 ≥ 100 天, 3 AZ 存储)
  └── 灾难恢复: 最近 Daily Backup + 重放 Tx Log → 恢复至 crash 时刻
       ↓
PostgreSQL Streaming Replication (Primary + Standby)
  └── Auto Failover · Connection Pooling · Read Replicas
```

**RPO 分析**：
- 正常故障（Primary Crash）→ Auto Failover to Standby → **秒级 RPO**
- 全集群故障 → Daily Backup + Tx Log 重放 → **<24h RPO**（取决于 backup 间隔）

## v1/v2 vs v3 元数据存储对比

| 维度 | InfluxDB v1/v2 | InfluxDB 3 |
|------|---------------|------------|
| 存储引擎 | BoltDB / etcd (嵌入式 KV) | PostgreSQL-Compatible RDBMS (独立服务) |
| 元数据类型 | Database/RP/Shard 映射 + Series File | Namespace/Table/Column/Partition/File |
| 索引 | TSI 倒排索引 (嵌入 Metastore) | Parquet Statistics (与元数据分离) |
| 高可用 | etcd 集群 (Enterprise) 或单文件 (OSS) | PostgreSQL 原生 Streaming Replication |
| 备份 | 手动 / Enterprise 工具 | Daily Auto Backup + Tx Log |
| 耦合度 | 元数据 + 索引耦合在单文件中 | 存算分离，松耦合架构 |
| 弹性 | 单机 BoltDB，线性扩展受限 | 独立 RDBMS 可按需伸缩 |

## 架构意义

Catalog 独立化为独立 PostgreSQL 服务是 InfluxDB 3 架构分离的关键一步：

1. **元数据与索引解耦** — TSI 索引曾是 v1/v2 的致命瓶颈，v3 将其职责拆分给 Parquet Statistics（索引）+ Catalog（元数据）
2. **存算分离的基础** — 所有组件通过 Catalog 知道数据在哪，无需 peer-to-peer 通信。这与 [[存储计算分离数据库的-Tail-Latency]] 中讨论的存算分离架构有相似的设计理念
3. **运维可依赖** — 利用 PostgreSQL 几十年的运维工具链（备份、主从、监控），相比自研 BoltDB 运维成熟度大幅提升

---

*参考: InfluxData 官方文档 "InfluxDB 3 Storage Engine Internals"*
