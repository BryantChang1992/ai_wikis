---
type: concept
title: Hailstorm：存算分离 LSM 的综述证据卡
aliases:
- Hailstorm
- 存算分离LSM
sources:
- '[[知识库/sources/papers/LSM-tree-KV-Survey-2025/精读分析]]'
tags:
- lsm-tree
- disaggregated-storage
- compaction
- kv-store
- cloud-native
- architecture
status: draft
created: 2026-07-02
related:
- '[[知识库/wiki/LSM-Tree]]'
- '[[知识库/wiki/LSM-Tree-合并优化]]'
- '[[知识库/wiki/LSM-tree-KV-Survey-综述]]'
updated: '2026-10-05'
source_citations:
- ASPLOS 2020
- 'Hailstorm: Disaggregated Compute and Storage for Distributed LSM-based Databases'
synced_at: '2026-10-05'
blog_url: https://bryantchang1992.github.io/ai_memory_chang_ai_team/knowledge/Hailstorm-存算分离LSM数据库/
blog_source: _posts/2026-07-02-knowledge-7d4e38d112.md
reviewed: '2026-10-05'
review_scope: 关键机制、证据范围、图示与跨页一致性
diagram_format: mermaid
---

# Hailstorm：存算分离 LSM 的综述证据卡

本卡目前依据 [[知识库/sources/papers/LSM-tree-KV-Survey-2025/精读分析]] 所对应综述的 PDF 第 15 页和参考文献 [18]，尚未完成 Hailstorm 独立原文精读。不要将此卡作为可直接复现的实验报告。

综述支持的机制包括：以分布式文件系统分离计算与存储、存储池化、把 compaction 工作卸载到远端，以及在实例间平衡工作而不要求重新分片。它们讨论的是资源分工，不意味着负载均衡没有数据移动、网络或协调成本。

```mermaid
flowchart TD
  C[LSM 计算实例] --> F[分布式文件系统与存储池]
  C --> O[远端 compaction 工作]
  O --> F
  S[资源调度] --> C
  S --> O
```

上图为本卡抽象示意，不对应原文具体组件名。旧稿的 FUSE 实现细节、2.3× / 22× 性能数字及其他系统归属没有从当前已核对材料得到支持，已撤回。后续获取原论文后，需要补充工作负载、网络条件、基线、读写放大和尾延迟，才能比较卸载收益。

文献：Laurent Bindschaedler、Ashvin Goel、Willy Zwaenepoel，*Hailstorm: Disaggregated Compute and Storage for Distributed LSM-based Databases*，ASPLOS 2020，pp.301–316，[DOI](https://doi.org/10.1145/3373376.3378504)。书目信息来自已核对综述的参考文献，DOI 不表示本次已取得原文。

关联：[[LSM-Tree-合并优化]]、[[LSM-Tree-硬件适配]]、[[存储计算分离数据库的-Tail-Latency]]。
