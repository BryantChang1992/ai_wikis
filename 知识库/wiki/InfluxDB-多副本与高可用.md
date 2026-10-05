---
type: concept
title: InfluxDB 耐久性与高可用：确认边界和故障边界
sources:
- '[[技术文章/InfluxDB调研/05-多副本复制与元数据存储]]'
tags:
- InfluxDB
- 高可用
- 副本
- WAL
- 故障恢复
- 持久性
created: 2026-06-14
updated: '2026-10-05'
status: final
author: Stark (CTO, CHANG_AI_TEAM)
related:
- '[[知识库/wiki/InfluxDB深度调研]]'
- '[[知识库/wiki/InfluxDB-Catalog元数据]]'
- '[[知识库/wiki/事务模型深度调研]]'
- '[[知识库/wiki/InfluxDB-写入与查询路径]]'
synced_at: '2026-10-05'
blog_url: https://bryantchang1992.github.io/ai_memory_chang_ai_team/knowledge/InfluxDB-多副本与高可用/
blog_source: _posts/2026-06-14-knowledge-7bacfb6aa2.md
reviewed: '2026-10-05'
review_scope: 关键机制、证据范围、图示与跨页一致性
source_checked: '2026-10-05'
verified_sources:
- https://docs.influxdata.com/influxdb3/core/reference/internals/durability/
- https://docs.influxdata.com/influxdb3/clustered/reference/internals/durability/
- https://docs.influxdata.com/influxdb/v2/reference/internals/storage-engine/
diagram_format: mermaid
---

# InfluxDB 耐久性与高可用：确认边界和故障边界

## 三条不同的持久化路径

| 产品形态 | 确认写入依赖什么 | 查询最近数据 | 不应推断的保证 |
|---|---|---|---|
| v1/v2 TSM | 本地 WAL 持久化与 Cache 更新 | Cache 与 TSM 合并 | 单机 WAL 不等于跨节点容灾 |
| 3 Core 默认同步模式 | WAL 刷到配置的对象存储 | 内存缓冲与 Parquet | 不意味着自带多个 Ingester 副本 |
| Clustered | 多 Ingester 本地 WAL，默认复制配置见文档 | Querier 访问 Ingester 与 Parquet | 副本数不直接等于任意多故障容忍 |

```mermaid
flowchart TD
  A[收到成功响应] --> B{成功响应的持久化边界}
  B --> L[本地 WAL：检查机器与磁盘故障域]
  B --> O[对象存储 WAL：检查后端耐久性和配置]
  B --> R[多 Ingester：检查副本放置与共同故障]
  L --> T[故障注入与恢复验证]
  O --> T
  R --> T
```

Core 开启 `no_sync` 时可能在 WAL 持久化前应答，必须单独评估丢失窗口。Clustered 的近期数据尚未写成 Parquet 时仍可查询，WAL 在持久化数据安全落地前承担恢复职责。

## 不可变文件仍需要元数据与备份

TSM 与 Parquet 都通过生成新文件进行合并，不可变不等于不会误删或无需备份。对象存储的故障域与冗余策略取决于所选后端；Catalog 的备份和文件回收策略也有独立边界。旧稿所写“所有 InfluxDB 3 自动三 AZ、固定 100 天、RPO 一律为 0”没有跨产品依据。

测试至少覆盖：写入确认后进程终止、节点磁盘丢失、对象存储暂时不可用、Catalog 恢复，以及 compaction 期间故障。分别记录可用性、数据完整性和恢复耗时；不能只凭一次写入成功判断容灾达标。

关联：[[InfluxDB-Catalog元数据]]、[[InfluxDB-写入与查询路径]]。


## 核验来源

- [Core 确认与 WAL](https://docs.influxdata.com/influxdb3/core/reference/internals/durability/)
- [Clustered 副本与 WAL](https://docs.influxdata.com/influxdb3/clustered/reference/internals/durability/)
- [TSM 引擎](https://docs.influxdata.com/influxdb/v2/reference/internals/storage-engine/)
