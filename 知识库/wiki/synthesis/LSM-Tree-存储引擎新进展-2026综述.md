---
type: synthesis
title: LSM 近期进展：调度、卸载和存储接口
created: 2026-06-16
updated: '2026-10-05'
status: draft
sources:
- '[[知识库/wiki/Silo-分布式LSM-Compaction调度]]'
- '[[知识库/wiki/Silo-Compaction-迁移协议]]'
- '[[知识库/wiki/LSM-Tree]]'
- '[[知识库/wiki/LSM-Tree-写放大]]'
- '[[知识库/wiki/LSM-Tree-合并优化]]'
- '[[知识库/wiki/LSM-Tree-自动调参]]'
- '[[知识库/wiki/LSM-Tree-RUM猜想]]'
- '[[知识库/wiki/LSM-Tree-硬件适配]]'
tags:
- LSM-Tree
- Compaction
- storage-engines
- scheduling
- distributed-storage
- synthesis
related:
- '[[知识库/wiki/Silo-分布式LSM-Compaction调度]]'
- '[[知识库/wiki/Silo-Compaction-迁移协议]]'
- '[[知识库/wiki/LSM-Tree]]'
- '[[知识库/wiki/LSM-Tree-写放大]]'
- '[[知识库/wiki/LSM-Tree-合并优化]]'
- '[[知识库/wiki/LSM-Tree-自动调参]]'
- '[[知识库/wiki/LSM-Tree-RUM猜想]]'
- '[[知识库/wiki/LSM-Tree-硬件适配]]'
- '[[知识库/wiki/LSM-Tree-二级索引]]'
- '[[知识库/wiki/Fluss-KV存储-RocksDB]]'
- '[[知识库/wiki/Fluss-存储引擎]]'
- '[[知识库/wiki/PebblesDB-碎片化LSM-Tree]]'
- '[[知识库/wiki/Pacman-持久内存Compaction]]'
- '[[知识库/wiki/gLSM-GPU加速Compaction]]'
- '[[知识库/wiki/ElasticBF-弹性BloomFilter]]'
- '[[知识库/wiki/Lethe-删除感知LSM引擎]]'
- '[[知识库/wiki/Bourbon-Learned-Index-LSM]]'
- '[[知识库/wiki/REMIX-全局排序索引]]'
- '[[知识库/wiki/Nova-LSM-分布式组件化LSM]]'
- '[[知识库/wiki/CaaS-LSM-Compaction即服务]]'
- '[[知识库/wiki/Hailstorm-存算分离LSM数据库]]'
- '[[知识库/wiki/LSM-tree-KV-Survey-综述]]'
- '[[知识库/wiki/Bigtable-分布式结构化存储系统]]'
synced_at: '2026-10-05'
blog_url: https://bryantchang1992.github.io/ai_memory_chang_ai_team/knowledge/LSM-Tree-存储引擎新进展-2026综述/
blog_source: _posts/2026-06-16-knowledge-aa56613e6a.md
reviewed: '2026-10-05'
review_scope: 关键机制、证据范围、图示与跨页一致性
diagram_format: mermaid
---

# LSM 近期进展：调度、卸载和存储接口

本次原文核对发现，旧笔记以“Silo 分布式 Compaction”命名的内容不对应所附论文。实际 PDF 是 FAST 2026 的 HATS。旧 WAF 调度、任务迁移协议及 62% / 57% 结果已撤回；保留旧路径仅为兼容链接，显示名称改为 HATS。

## HATS 在协调什么

压实干扰使不同副本的读取代价随时间变化；只均匀分发读请求无法消除延迟差异，一直推迟压实又会累积读放大。HATS 将合法副本间的读路由与各副本本地 compaction 预算放进同一反馈过程。

```mermaid
flowchart TD
  O[读负载与延迟观测] --> S[调度器计算期望分布]
  S --> R[读请求选择合法副本]
  S --> B[本地 LSM 分配 compaction rate]
  R --> F[性能反馈]
  B --> F
  F --> O
```

Raft 在这项设计中选出 scheduler，不替代 Cassandra 的用户数据复制协议。数据也不会随每次读调度迁移。因此它不能被画成远端 compaction 服务。

## 实驗支持哪些结论

论文以 Cassandra 5.0 为基础，默认 10 个四核/16GiB/SATA SSD 节点、10Gbps 网络、R=3、读响应数 1、写响应数 3，使用 YCSB、100M 记录及多轮运行。read-dominant 负载中，作者报告相对 C3/DEPART 的 P99 与吞吐改善；具体数值和图表位置见 [[知识库/sources/papers/LSM-Scheduling/精读分析]]。这些结果不是通用 SLO 达标率，也没有验证所有强一致读取配置或千节点规模。

## 与其他路线比较

| 路线 | 调整的对象 | 应验证的额外代价 |
|---|---|---|
| [[Silo-分布式LSM-Compaction调度|HATS 读与压实协同]] | 路由与本地预算 | 状态过期、调度震荡、写密集负载 |
| [[CaaS-LSM-Compaction即服务]] | 压实计算的位置 | 网络、任务一致性、失败清理 |
| [[Hailstorm-存算分离LSM数据库]] | 计算、存储池与卸载 | 原文实验仍待独立精读 |
| [[Fluss-KV存储-RocksDB]] | 流日志与 PK 状态接口 | 快照和日志的恢复边界 |

下一步实证问题是：同一硬件与一致性目标下，调度与卸载是否可组合、何时竞争同一网络预算，而不是仅比较不同论文摘要中的最大倍数。基础成本模型见 [[LSM-Tree-存储引擎体系综述]]。
