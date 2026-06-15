---
type: concept
title: "ByteHouse 多模态查询优化 — HBO + RANK_FUSION + 分级向量索引"
sources:
  - "sources/papers/ByteHouse/ByteHouse-SIGMOD2026.pdf"
  - "sources/papers/ByteHouse/精读分析.md"
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
updated: 2026-06-15
status: draft
related:
  - "[[ByteHouse-架构与设计]]"
  - "[[ByteHouse-统一表引擎]]"
  - "[[Doris-MPP-向量化查询引擎]]"
  - "[[Doris-Nereids-CBO-优化器]]"
diagram: "diagram/bytehouse-architecture.svg"
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

## 分级向量索引 (Tiered Vector Index)

为不同业务需求提供三类索引：

| 层级 | 索引类型 | 延迟 | 成本 | 适用场景 |
|------|---------|------|------|----------|
| 在线 | HNSW (内存) | <10ms | 高 | SDK/实时代码推荐 |
| 近实时 | IVF+PQ (SSD) | <100ms | 中 | 实时运营看板 |
| 经济型 | DiskANN (对象存储) | <1s | 低 | 批量分析/归档检索 |

## 三模式执行引擎

| 模式 | 全称 | 用途 | 数据交换 |
|------|------|------|----------|
| APM | Analytic Pipeline Mode | 分布式 MPP 查询 | shuffle/gather/broadcast |
| SBM | Staged Batch Mode | 长 ETL | stage 持久化 + 重试 |
| IPM | Incremental Processing Mode | 增量刷新 | lineage + versioned ops |

所有模式共享统一优化器 + runtime → 无缝切换。

## 与 Doris Nereids CBO 的对比

| 维度 | ByteHouse | Doris |
|------|-----------|-------|
| 核心优化 | HBO + ML 回归 | 规则 + CBO (Nereids) |
| 历史统计 | ✅ 执行后收集 real cardinality | ❌ 依赖 ANALYZE 统计 |
| 向量检索 | ✅ RANK_FUSION + 分级索引 | ❌ 无原生支持 |
| Join 优化 | ML 模型决策 | Join Reorder (贪心+枚举) |
| Runtime Filter | 推入向量扫描 | Bloom/Bitmap Filter |
