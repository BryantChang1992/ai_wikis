---
type: synthesis
title: OLAP 与时序数据库：按工作负载阅读知识库
sources:
- '[[知识库/wiki/Doris-深度调研]]'
- '[[知识库/wiki/Doris-数据模型]]'
- '[[知识库/wiki/Doris-Segment-v2-存储格式]]'
- '[[知识库/wiki/Doris-Compaction-策略]]'
- '[[知识库/wiki/Doris-MPP-向量化查询引擎]]'
- '[[知识库/wiki/Doris-Nereids-CBO-优化器]]'
- '[[知识库/wiki/Doris-架构演进]]'
- '[[知识库/wiki/Doris-元数据与一致性复制]]'
- '[[知识库/wiki/InfluxDB深度调研]]'
- '[[知识库/wiki/InfluxDB-数据模型]]'
- '[[知识库/wiki/InfluxDB-TSM存储引擎]]'
- '[[知识库/wiki/InfluxDB-3-列存引擎]]'
- '[[知识库/wiki/InfluxDB-写入与查询路径]]'
- '[[知识库/wiki/InfluxDB-指标设计与基数管理]]'
- '[[知识库/wiki/InfluxDB-多副本与高可用]]'
- '[[知识库/wiki/InfluxDB-Catalog元数据]]'
tags:
- OLAP
- 时序数据库
- 数据分析
- 综述
created: 2026-06-14
updated: '2026-10-05'
status: draft
related:
- '[[知识库/wiki/synthesis/LSM-Tree-存储引擎体系综述]]'
- '[[知识库/wiki/事务模型深度调研]]'
synced_at: '2026-10-05'
blog_url: https://bryantchang1992.github.io/ai_memory_chang_ai_team/posts/wiki-synthesis-olap-tsdb/
blog_source: _posts/2026-06-14-wiki-synthesis-olap-tsdb.md
blog_source_commit: f83970fa7e6ad32d626cc6ca3ba7428c90a638a5
blog_body_sha256: f73ddb7ee71de83e29e9413c87ff98010ca18f5a7ec5d2577cceb70474e9fad0
reviewed: '2026-10-05'
review_scope: 关键机制、证据范围、图示与跨页一致性
diagram_format: mermaid
---

# OLAP 与时序数据库：按工作负载阅读知识库

OLAP 与 TSDB 都可使用列式编码、批量执行和分区剪枝，但需要优化的问题不同。系统选型不能由“实时”“湖仓”或某个引擎名称直接决定。

| 工作负载问题 | 优先阅读 | 测量重点 |
|---|---|---|
| 明细分析、多表 Join、主键 CDC | [[Apache-Doris-OLAP-数据库体系综述]] | Join 分布、更新可见性、并发与合并压力 |
| 指标写入、时间窗口、保留与降采样 | [[InfluxDB-时序数据库体系综述]] | 实际基数、最新数据可见性、窗口扫描与恢复 |
| 流式状态与历史湖表结合 | [[Fluss-流处理平台架构综述]] | Log/KV/Lake 三种进度和提交边界 |
| 存储底层读写成本 | [[LSM-Tree-存储引擎体系综述]] | 放大、缓存、后台债务和尾延迟 |

```mermaid
flowchart TD
  B[业务查询与更新语义] --> M[数据模型]
  M --> P[分区、索引与物理布局]
  P --> E[执行引擎与部署形态]
  E --> V[同一数据集与故障目标下验证]
  V --> C[质量、成本、延迟与可运维性]
```

读写确认、查询可见、备份可恢复是三种不同边界；列式文件、向量化执行、水平扩容也是三个不同维度。不要把 CockroachDB 的向量化等同于物理列存，或把 InfluxDB Clustered 的部署图套到 Core。

本综述是导航与比较框架，不提供未经统一测试的产品排名。各领域卡片中的版本、原文证据与待核验项优先于旧周报中的趋势判断。
