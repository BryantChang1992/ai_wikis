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
diagram: "diagram/influxdb-architecture.svg"

---

# InfluxDB Catalog 元数据存储

## 定义

InfluxDB 3 的 Catalog 是整个系统的**元数据中心**——唯一存储全局状态的组件。所有组件（Ingester、Querier、Compactor、GC）通过读取 Catalog 了解全局状态，组件间无需直接通信。

## Catalog 数据模型

Catalog 使用 **PostgreSQL 兼容的关系数据库** 存储层级元数据：

<svg viewBox="0 0 640 400" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <marker id="ar1" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <path d="M0,0 L8,3 L0,6 Z" fill="currentColor"/>
    </marker>
  </defs>
  <style>
    text { font-family: sans-serif; font-size: 12px; fill: currentColor; dominant-baseline: middle; }
    line, path { stroke: currentColor; stroke-width: 1.5; fill: none; }
    rect { fill: transparent; stroke: currentColor; stroke-width: 1.5; rx: 4; }
  </style>

  <!-- Namespace -->
  <rect x="260" y="10" width="140" height="28"/>
  <text x="330" y="24">Namespace (Database)</text>

  <!-- vertical line from Namespace down -->
  <line x1="330" y1="38" x2="330" y2="60" marker-end="url(#ar1)"/>

  <!-- Table -->
  <rect x="260" y="64" width="140" height="28"/>
  <text x="330" y="78">Table (Measurement)</text>

  <!-- horizontal branch from Table -->
  <line x1="280" y1="92" x2="280" y2="110"/>
  <line x1="280" y1="110" x2="180" y2="110"/>
  <line x1="380" y1="110" x2="380" y2="92"/>
  <line x1="180" y1="110" x2="180" y2="130"/>
  <line x1="380" y1="110" x2="380" y2="130"/>

  <!-- Column -->
  <rect x="105" y="134" width="150" height="28"/>
  <text x="180" y="148">Column</text>
  <line x1="150" y1="162" x2="150" y2="180"/>
  <rect x="75" y="184" width="210" height="50"/>
  <text x="180" y="198" font-size="11px">name, type</text>
  <text x="180" y="216" font-size="11px">(i64/u64/f64/string/bool/tag/time)</text>
  <text x="180" y="232" font-size="11px">nullable</text>

  <!-- Partition -->
  <rect x="290" y="134" width="180" height="28"/>
  <text x="380" y="148">Partition (time range)</text>
  <line x1="380" y1="162" x2="380" y2="185"/>

  <!-- Parquet File -->
  <rect x="290" y="189" width="180" height="28"/>
  <text x="380" y="203">Parquet File</text>
  <line x1="340" y1="217" x2="340" y2="238"/>

  <!-- File metadata fields -->
  <rect x="260" y="242" width="240" height="150"/>
  <text x="380" y="258" font-size="11px">object_store_path</text>
  <text x="380" y="276" font-size="11px">file_size_bytes</text>
  <text x="380" y="294" font-size="11px">row_count</text>
  <text x="380" y="312" font-size="11px">min_time, max_time</text>
  <text x="380" y="330" font-size="11px">created_at</text>
  <text x="380" y="348" font-size="11px">to_delete (soft delete flag)</text>
  <line x1="310" y1="258" x2="310" y2="258"/>
</svg>

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

<svg viewBox="0 0 700 250" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <marker id="ar2" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <path d="M0,0 L8,3 L0,6 Z" fill="currentColor"/>
    </marker>
  </defs>
  <style>
    text { font-family: sans-serif; font-size: 12px; fill: currentColor; dominant-baseline: middle; text-anchor: middle; }
    line, path { stroke: currentColor; stroke-width: 1.5; fill: none; }
    rect { fill: transparent; stroke: currentColor; stroke-width: 1.5; rx: 4; }
  </style>

  <!-- Transaction Log -->
  <rect x="220" y="10" width="260" height="28"/>
  <text x="350" y="24">Transaction Log (PostgreSQL WAL)</text>

  <line x1="350" y1="38" x2="350" y2="58" marker-end="url(#ar2)"/>

  <!-- Tx Log note -->
  <rect x="190" y="62" width="320" height="28"/>
  <text x="350" y="76">Catalog 更新在 Tx Log 中有序记录</text>

  <line x1="350" y1="90" x2="350" y2="108" marker-end="url(#ar2)"/>

  <!-- Daily Full Backup -->
  <rect x="130" y="112" width="200" height="28"/>
  <text x="230" y="126">Daily Full Backup</text>
  <line x1="330" y1="126" x2="370" y2="126" marker-end="url(#ar2)"/>
  <rect x="374" y="112" width="200" height="28"/>
  <text x="474" y="126">Object Store (≥ 100 天, 3 AZ)</text>

  <line x1="350" y1="140" x2="350" y2="158" marker-end="url(#ar2)"/>

  <!-- Disaster Recovery -->
  <rect x="150" y="162" width="400" height="28"/>
  <text x="350" y="176">Disaster Recovery: Backup + Tx Log 重放 → 恢复至 crash 时刻</text>

  <line x1="350" y1="190" x2="350" y2="208" marker-end="url(#ar2)"/>

  <!-- PostgreSQL Streaming Replication -->
  <rect x="180" y="212" width="340" height="28"/>
  <text x="350" y="226">PostgreSQL Streaming Replication (Primary + Standby)</text>
</svg>

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
