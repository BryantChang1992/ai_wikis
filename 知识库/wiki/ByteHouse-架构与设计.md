---
type: concept
title: ByteHouse 整体架构 — 三层存算分离
sources:
- '[[知识库/sources/papers/ByteHouse/精读分析]]'
- '[[知识库/sources/papers/ByteHouse/ByteHouse-SIGMOD2026.pdf]]'
tags:
- ByteHouse
- OLAP
- 云原生
- 存算分离
- Multi-modal
- SIGMOD-2026
- ByteDance
created: 2026-06-15
updated: '2026-10-05'
status: draft
related:
- '[[知识库/wiki/ByteHouse-统一表引擎]]'
- '[[知识库/wiki/ByteHouse-多模态查询优化]]'
- '[[知识库/wiki/Doris-深度调研]]'
- '[[知识库/wiki/事务模型深度调研]]'
synced_at: '2026-10-05'
blog_url: https://bryantchang1992.github.io/ai_memory_chang_ai_team/knowledge/ByteHouse-架构与设计/
blog_source: _posts/2026-06-15-knowledge-8189f15178.md
source_check_scope: 本地PDF §2–7，页2–12，图2–10；修正索引媒介、实验条件与跨产品断言。
source_checked: '2026-10-05'
diagram_format: mermaid
---

# ByteHouse 整体架构 — 三层存算分离

## 定义

ByteHouse 是 ByteDance 自研的云原生分析数据仓库，采用 **控制、计算、存储分层** 的 shared-storage 架构，同时支持结构化 OLAP 和非结构化向量检索。已服务 400+ 内部业务。

## 三层架构

```mermaid
flowchart TB
  Control[控制：规划、目录、事务] --> Compute[计算：APM / SBM / IPM]
  Compute --> Table[统一表与MVCC]
  Table --> Nexus[NexusFS]
  Nexus --> Cache[本地和CrossCache缓存]
  Nexus --> Store[远端持久存储]
```

### Control Layer

| 组件 | 职责 |
|------|------|
| Server | SQL 解析、语义分析、HBO 优化、分布式调度 |
| Catalog Manager | 版本化元数据存储 (ByteKV)，快照一致的 schema/分区/索引 |
| Global Transaction Manager | 论文§2称其支持serializable事务和一致快照读；详细并发控制证明未展开 |
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

## 对比边界

本卡描述论文版本的ByteHouse。删除未逐一验证的当前竞品能力矩阵；比较Doris、ClickHouse或Snowflake应固定版本、部署模式和相同工作负载。


## 证据与适用条件

核验本地PDF：§2–3（页2–6）架构与存储，§4–6（页6–10）执行和优化，§7（页10–12）实验。ClickBench 43查询各跑5次取最快，较ClickHouse总延迟降低25.4%；向量实验为99%召回、1%标量过滤；CrossCache对照含无缓存、100%/50%本地命中。不同实验不能混为统一收益。细节见[[知识库/sources/papers/ByteHouse/精读分析|精读分析]]。
