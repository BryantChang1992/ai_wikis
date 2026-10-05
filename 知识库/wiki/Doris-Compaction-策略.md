---
type: concept
title: Doris Compaction：选哪些文件与怎样合并
sources:
- '[[技术文章/Doris调研/02-存储引擎]]'
tags:
- 数据库
- OLAP
- Doris
- 存储引擎
- Compaction
- LSM-Tree
- Merge-on-Write
created: 2026-06-14
updated: '2026-10-05'
status: draft
related:
- '[[知识库/wiki/Doris-深度调研]]'
- '[[知识库/wiki/Doris-Segment-v2-存储格式]]'
- '[[知识库/wiki/Doris-数据模型]]'
- '[[知识库/wiki/LSM-Tree-合并优化]]'
- '[[知识库/wiki/LSM-Tree-RUM猜想]]'
- '[[知识库/wiki/synthesis/LSM-Tree-存储引擎体系综述]]'
synced_at: '2026-10-05'
blog_url: https://bryantchang1992.github.io/ai_memory_chang_ai_team/knowledge/Doris-Compaction-策略/
blog_source: _posts/2026-06-14-knowledge-1cd9b2bb17.md
reviewed: '2026-10-05'
review_scope: 关键机制、证据范围、图示与跨页一致性
source_checked: '2026-10-05'
verified_sources:
- https://doris.apache.org/docs/dev/admin-manual/trouble-shooting/compaction/
diagram_format: mermaid
---

# Doris Compaction：选哪些文件与怎样合并

不能把 Cumulative、Base、Vertical 和一次导入内的 Segment Compaction 当成四个互斥的同级策略：前两者偏向 rowset 选择与合并范围，Vertical 是执行算法，Segment Compaction 位于导入内的 segment 合并过程。

| 机制 | 主要解决的问题 | 代价或限制 |
|---|---|---|
| Cumulative | 小增量 rowset 积累 | 与导入和读取竞争资源 |
| Base / Full | 更大范围的历史 rowset 整理 | 大任务的 I/O 与运行时间 |
| Vertical | 分列组处理，降低宽表合并工作集 | 需要维护行来源顺序；收益依赖宽度与 I/O |
| Segment Compaction | 单次大批量导入产生过多 segment | 需结合导入路径与版本配置 |

```mermaid
flowchart TD
  S[扫描 tablet 与合并压力] --> L[选择连续版本的输入 rowset]
  L --> C[检查并发与资源预算]
  C --> M[按表模型合并并生成新 rowset]
  M --> V[原子切换相关元数据与可见文件集合]
  V --> G[按引用与回收规则清理旧文件]
```

新输出必须保持原来版本范围和表模型的逻辑结果。更多线程并非必然更快：当磁盘或内存已饱和，会放大前台尾延迟。观察 rowset 数、compaction score、待处理字节、写入失败和查询 P99，再结合批量大小及时间序列策略调整。

官方宽表案例中的内存和速度收益只适用于其条件，不应改写为全部表的性能保证。LSM 的写放大框架有助于分析，但 Doris 的 rowset/version 与标准 RocksDB 层级并不一一对应。

关联：[[Doris-Segment-v2-存储格式]]、[[LSM-Tree-合并优化]]。


## 核验来源

- [Compaction 原理](https://doris.apache.org/docs/4.x/admin-manual/trouble-shooting/compaction-principles/)
- [Vertical 与 Segment Compaction](https://doris.apache.org/docs/dev/admin-manual/trouble-shooting/compaction/)
