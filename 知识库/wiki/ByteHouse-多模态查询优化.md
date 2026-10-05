---
type: concept
title: ByteHouse 多模态查询优化
sources:
- '[[知识库/sources/papers/ByteHouse/精读分析]]'
- '[[知识库/sources/papers/ByteHouse/ByteHouse-SIGMOD2026.pdf]]'
tags:
- ByteHouse
- 查询优化
- HBO
- 向量检索
- RANK_FUSION
- 多模态
- AI-Assisted
- Runtime Filter
created: 2026-06-15
updated: '2026-10-05'
status: draft
related:
- '[[知识库/wiki/ByteHouse-架构与设计]]'
- '[[知识库/wiki/ByteHouse-统一表引擎]]'
- '[[知识库/wiki/Doris-MPP-向量化查询引擎]]'
- '[[知识库/wiki/Doris-Nereids-CBO-优化器]]'
synced_at: '2026-10-05'
blog_url: https://bryantchang1992.github.io/ai_memory_chang_ai_team/knowledge/ByteHouse-多模态查询优化/
blog_source: _posts/2026-06-15-knowledge-5b9838a415.md
source_check_scope: 本地PDF §2–7，页2–12，图2–10；修正索引媒介、实验条件与跨产品断言。
source_checked: '2026-10-05'
diagram_format: mermaid
---

# ByteHouse 多模态查询优化

## 定义

ByteHouse 在传统 OLAP 查询优化的基础上，引入三大增强：HBO (History-Based Optimization) + ML 回归模型辅助优化、RANK_FUSION 混合检索算子、分级 (Tiered) 向量索引。

## HBO — 基于历史的优化

**核心思想**：不依赖纯静态 CBO 统计，而是复用历史执行的真实运行时指标。

| 指标 | 来源 | 用途 |
|------|------|------|
| Cardinality | 历史执行实际行数 | 纠正估算偏差 |
| Selectivity | 历史过滤比例 | 谓词代价建模 |
| Operator Cost | 历史算子耗时 | 替代静态 cost model |

### 何时 HBO 优于 CBO

- 数据分布统计过期时（CBO 估算偏差大）
- 查询模式重复时（相同 SQL 模板复用历史精度）
- 多表 Join 顺序（HBO 知道真实中间结果大小）

## ML 增强 — 回归模型

在 HBO 离线统计基础上，训练回归模型：

```
输入特征: 查询结构特征 × 数据分布特征 × 历史行为
输出: cardinality / selectivity / operator cost 预测
```

**泛化能力**：即使查询结构未在 HBO 历史中出现，ML 模型也能推测代价。应用场景：
- **谓词下推选择**：哪些 predicate 先推下去最有收益
- **Join 侧选择**：build side / probe side 决策

**局限性**（见精读分析）：
- ⚠️ ML 模型 plan regression 未分析
- ⚠️ 过拟合训练分布可能产生比 CBO 更差的 plan

## RANK_FUSION — 混合检索算子

多模态查询的核心算子：一张表中需要同时按结构化字段过滤 + 语义相似度排序。

```
SELECT * FROM docs
WHERE category = 'tech'          ← 标量过滤
AND publish_date > '2025-01-01'  ← 范围过滤
ORDER BY RANK_FUSION(            ← 融合评分
  cosine_similarity(embedding, query_vec) * 0.7,  ← 语义 70%
  bm25_score(content, 'keyword') * 0.3             ← 关键词 30%
) DESC
LIMIT 50;
```

### Runtime Filter 推向量扫描

- 标量谓词 (category/date) 先过滤 → 缩小向量候选集
- 然后在过滤后的子集上做向量检索
- 避免全表向量扫描

## 分级向量索引（论文§6）

- 在线低延迟、高召回：HNSW + SQ。
- 近实时、强调快速可见：IVFFlat / IVFSQ / IVFPQ；原文给的较宽松延迟例是100ms–1s，而非统一小于100ms。
- 成本敏感：DiskANN 的图在SSD，routing metadata在内存；更宽松归档可选DiskIVFSQ，不是DiskANN直接只读对象存储。

```mermaid
flowchart LR
  Scalar[标量过滤与join键] --> Filter[Runtime filter]
  Filter --> Vector[向量候选]
  Filter --> Text[文本候选]
  Vector --> Fusion[归一化加权或RRF]
  Text --> Fusion
  Fusion --> Exact[Post-join精确谓词检查]
  Exact --> Top[排序并返回Top K]
```

RRF使用`sum 1/(k+rank)`融合排名，k通常60；分数加权路径先做Min–Max归一化。上面的SQL仅为教学伪代码，非官方可执行语法；runtime Bloom filter可能误报，仍需最终谓词验证。

## 三模式执行引擎

| 模式 | 全称 | 用途 | 数据交换 |
|------|------|------|----------|
| APM | Analytic Pipeline Mode | 分布式 MPP 查询 | shuffle/gather/broadcast |
| SBM | Staged Batch Mode | 长 ETL | stage 持久化 + 重试 |
| IPM | Incremental Processing Mode | 增量刷新 | lineage + versioned ops |

所有模式共享统一优化器 + runtime → 无缝切换。

## 对比边界

本卡描述论文版本的ByteHouse。删除未逐一验证的当前竞品能力矩阵；比较Doris、ClickHouse或Snowflake应固定版本、部署模式和相同工作负载。


## 证据与适用条件

核验本地PDF：§2–3（页2–6）架构与存储，§4–6（页6–10）执行和优化，§7（页10–12）实验。ClickBench 43查询各跑5次取最快，较ClickHouse总延迟降低25.4%；向量实验为99%召回、1%标量过滤；CrossCache对照含无缓存、100%/50%本地命中。不同实验不能混为统一收益。细节见[[知识库/sources/papers/ByteHouse/精读分析|精读分析]]。
