---
type: concept
title: "InfluxDB 多副本与高可用"
sources:
  - "技术文章/InfluxDB调研/05-多副本复制与元数据存储.md"
tags:
  - InfluxDB
  - 高可用
  - 副本
  - WAL
  - 故障恢复
  - 持久性
created: 2026-06-14
updated: 2026-06-14
status: final
author: Stark (CTO, CHANG_AI_TEAM)
related:
  - "[[InfluxDB深度调研]]"
  - "[[InfluxDB-Catalog元数据]]"
  - "[[事务模型深度调研]]"
  - "[[InfluxDB-写入与查询路径]]"
---

# InfluxDB 多副本与高可用

## 三层防护架构

InfluxDB 3 的数据持久化通过**三层防护**确保数据不丢失：

| 层级 | 机制 | 作用 |
|------|------|------|
| Layer 1 — Router | 双副本写入 (2+ Ingesters) | 写入即确认，单 Ingester 故障不影响持久化 |
| Layer 2 — Ingester | WAL (EBS/Local SSD) | Crash Recovery，Graceful Shutdown 前 flush |
| Layer 3 — Object Store | 3 AZ 冗余存储 | 跨可用区冗余，Parquet 不可变，延迟删除 |

## Router 双副本写入

<svg viewBox="0 0 650 130" xmlns="http://www.w3.org/2000/svg" style="max-width:100%">
  <defs>
    <marker id="arrow-right" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <path d="M0,0 L8,3 L0,6 Z" fill="currentColor"/>
    </marker>
    <marker id="arrow-left" markerWidth="8" markerHeight="6" refX="0" refY="3" orient="auto">
      <path d="M8,0 L0,3 L8,6 Z" fill="currentColor"/>
    </marker>
  </defs>
  <!-- Write Client -->
  <rect x="10" y="30" width="95" height="34" rx="6" fill="transparent" stroke="currentColor" stroke-width="2"/>
  <text x="57" y="49" font-family="sans-serif" font-size="12" fill="currentColor" text-anchor="middle" dominant-baseline="middle">Write Client</text>
  <!-- Arrow to Router -->
  <line x1="105" y1="47" x2="155" y2="47" stroke="currentColor" stroke-width="2" marker-end="url(#arrow-right)"/>
  <!-- Ingest Router -->
  <rect x="155" y="28" width="110" height="38" rx="6" fill="transparent" stroke="currentColor" stroke-width="2"/>
  <text x="210" y="47" font-family="sans-serif" font-size="12" fill="currentColor" text-anchor="middle" dominant-baseline="middle">Ingest Router</text>
  <text x="210" y="65" font-family="sans-serif" font-size="10" fill="currentColor" text-anchor="middle">Consistent Hash (Shard Key)</text>
  <!-- Fork point -->
  <circle cx="285" cy="47" r="4" fill="currentColor"/>
  <!-- Upper arrow to Ingester A -->
  <line x1="289" y1="43" x2="340" y2="30" stroke="currentColor" stroke-width="2" marker-end="url(#arrow-right)"/>
  <!-- Lower arrow to Ingester B -->
  <line x1="289" y1="51" x2="340" y2="64" stroke="currentColor" stroke-width="2" marker-end="url(#arrow-right)"/>
  <!-- Ingester A -->
  <rect x="345" y="12" width="150" height="34" rx="6" fill="transparent" stroke="currentColor" stroke-width="2"/>
  <text x="420" y="31" font-family="sans-serif" font-size="12" fill="currentColor" text-anchor="middle" dominant-baseline="middle">Ingester A</text>
  <text x="420" y="44" font-family="sans-serif" font-size="10" fill="currentColor" text-anchor="middle">(WAL + Process)</text>
  <!-- Ingester B -->
  <rect x="345" y="48" width="150" height="34" rx="6" fill="transparent" stroke="currentColor" stroke-width="2"/>
  <text x="420" y="67" font-family="sans-serif" font-size="12" fill="currentColor" text-anchor="middle" dominant-baseline="middle">Ingester B</text>
  <text x="420" y="80" font-family="sans-serif" font-size="10" fill="currentColor" text-anchor="middle">(WAL + Process)</text>
  <!-- Ack arrow back -->
  <line x1="345" y1="100" x2="57" y2="100" stroke="currentColor" stroke-width="2" stroke-dasharray="5,3" marker-end="url(#arrow-left)"/>
  <text x="210" y="113" font-family="sans-serif" font-size="11" fill="currentColor" text-anchor="middle">Ack (双副本确认后才返回客户端)</text>
</svg>


**关键设计**：
- Router 在**确认写入成功前**将数据复制到至少 2 个 Ingester
- 如果某一 Ingester 宕机，另一副本的 WAL 保证数据不丢失
- Consistent Hash 确保同一分区数据路由到同一组 Ingester

## Ingester WAL 生命周期

```
接收 Line Protocol → 写入 WAL (fsync) → 写入确认 (Ack back to Router)
→ 内存处理 (Sort/Dedup/Partition) → Persist Parquet (Object Store)
→ 更新 Catalog → Truncate WAL (该段已安全持久化)
```

**WAL 语义**：InfluxDB 3 的 WAL 仅用于 crash recovery，**不参与查询路径**（查询由 Object Store 上的 Parquet 文件服务）。这与 [[事务模型深度调研]] 中的 WAL 机制原理相同，但用途更窄——不像传统数据库那样支持 Point-in-Time Recovery（PITR）。

**崩溃恢复流程**：
- **Graceful Shutdown**：先 flush WAL → Parquet → 再停止
- **Unexpected Crash**：新 Ingester 启动 → 重放 WAL → 恢复未持久化数据

## Object Store 3 AZ 冗余

- Parquet 文件写入 Object Store 后，云存储提供商（S3/GCS/Azure Blob）自动在 ≥3 个可用区冗余存储
- Parquet 文件本身**不可变**（Immutable），写入后从不修改
- 删除通过 Catalog 的 Soft Delete 标记，实际文件保留约 100 天后由 GC 物理删除

## 故障恢复能力

| 故障场景 | 恢复方式 | RPO |
|----------|----------|-----|
| Ingester 进程崩溃 | 新 Ingester 重放 WAL | 毫秒级 (WAL 最后 fsync) |
| Ingester 节点宕机 | Router 路由到另一副本 Ingester | 0 (双副本已确认) |
| Object Store 单 AZ 故障 | 自动切换到另一 AZ 副本 | 0 (多 AZ 冗余) |
| Catalog 故障 | Daily Backup + Tx Log 重放 | <24h (取决于 backup 间隔) |
| 全 Region 级灾难 | Catalog Backup + Object Store 跨 Region | 分钟～小时级 |

## v1/v2 vs v3 高可用差异

| 维度 | v1/v2 | v3 |
|------|-------|-----|
| 写入持久性 | 单 WAL (本地磁盘) | 双 Ingester WAL + Object Store |
| 副本机制 | 无开箱副本 (Enterprise 版 hint-handoff) | 原生双副本写入 |
| 崩溃恢复 | 重放全部 WAL (可能很慢) | WAL 截断后重放量小 |
| 跨 AZ 冗余 | 手动备份 | 自动 3 AZ 冗余 |
| 数据不变性 | TSM 文件可变 (Compaction) | Parquet 不可变 |

---

*参考: InfluxData 官方文档 "InfluxDB 3.0 System Architecture"*
