---
type: concept
title: Bourbon：LSM 学习索引的证据与选型
sources:
- '[[知识库/sources/papers/LSM-tree-KV-Survey-2025/精读分析]]'
- '[[知识库/sources/papers/LSM-tree-KV-Survey-2025/LSM-tree-KV-Survey-2025.pdf]]'
tags:
- 存储引擎
- LSM-Tree
- 学习索引
- Learned Index
- 点查优化
- WiscKey
- OSDI 2020
created: 2026-07-02
updated: '2026-10-05'
status: draft
related:
- '[[知识库/wiki/LSM-Tree]]'
- '[[知识库/wiki/LSM-Tree-自动调参]]'
- '[[知识库/wiki/LSM-tree-KV-Survey-综述]]'
- '[[知识库/wiki/LSM-Tree-合并优化]]'
synced_at: '2026-10-05'
blog_url: https://bryantchang1992.github.io/ai_memory_chang_ai_team/knowledge/Bourbon-Learned-Index-LSM/
blog_source: _posts/2026-07-02-knowledge-644c614109.md
source_check_scope: 综述级核验：页19的点查优化段、参考文献[32]（页30）；未取得/核验独立原文，撤除未确认量化与协议细节。
source_checked: '2026-10-05'
diagram_format: mermaid
---

# Bourbon：LSM 学习索引的证据与选型

> **来源层级**：本次只核验本地2025 LSM综述的页19的点查优化段、参考文献[32]（页30）。这是二级来源概念卡，不是Bourbon独立原论文精读；原有`draft`审核状态不升级。

## 综述明确支持的结论

2025综述把Bourbon归为通过机器学习加快LSM点查的研究；参考文献给出Dai等OSDI 2020论文 *From WiscKey to Bourbon: A Learned Index for Log-Structured Merge Trees*。

## 为什么这条路线与 Bloom Filter 不同

Bloom filter先回答“可能存在吗”，减少无效数据访问；学习索引利用键与位置的相关性缩小查找范围。两者优化不同环节。若总耗时由随机I/O主导，减少CPU索引比较未必带来明显端到端收益；若数据在缓存或快速设备中，索引CPU可能成为更值得优化的部分。这是性能分解推论，不是本次重跑Bourbon的结果。

```mermaid
flowchart LR
  Key[待查Key] --> Locate[候选文件与索引定位]
  Locate --> Model[学习模型辅助缩小查找范围]
  Model --> Verify[精确比较和版本可见性检查]
  Verify --> Value[返回正确Value或不存在]
```

图是学习索引的一般职责分解，不声称为Bourbon原论文每个函数的执行顺序。预测不是数据存在性证明，也不应取代精确验证。

## 走通示例与不变量（工程推论）

假设一个不可变有序文件有100万keys，模型预测key k在位置50000附近。最终仍须在合法查找区间比较实际key；compaction生成新文件后，旧文件模型不能未经重建/验证就用于新布局。必须明确模型失效、回退和文件生命周期绑定，否则“预测很快”会变成返回错误记录。

## 实验应问的问题

分别计文件定位、过滤器、数据block访问、模型推理/训练成本；控制缓存命中、设备、读写比及key分布。应把训练和重建开销摊入混合工作负载，而不是只测静态只读查询。

旧稿的44%/50%CPU占比、134s/13.9s训练、1.04×/1.25×与模型0–2%空间等具体数字，未由本地综述验证，已撤出结论。Greedy-PLR、file/level learning及cost-benefit实现细节需独立原文后再恢复为事实，不用推测填补。

相关：[[LSM-Tree-自动调参]]、[[ElasticBF-弹性BloomFilter]]、[[LSM-tree-KV-Survey-综述]]。
