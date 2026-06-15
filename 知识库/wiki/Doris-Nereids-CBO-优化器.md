---
type: concept
title: "Doris Nereids CBO 优化器"
sources:
  - "技术文章/Doris调研/03-查询流程.md"
tags:
  - 数据库
  - OLAP
  - Doris
  - 查询优化
  - CBO
  - Nereids
  - Runtime Filter
  - Join Reorder
created: 2026-06-14
updated: 2026-06-14
status: draft
related:
  - "[[Doris-深度调研]]"
  - "[[Doris-MPP-向量化查询引擎]]"
diagram: "diagram/doris-architecture.svg"

---

# Doris Nereids CBO 优化器

## 概述

Nereids 是 Doris 第二代查询优化器，基于 **CBO (Cost-Based Optimization)** 模型，通过统计信息驱动查询计划选择。于 v2.1 实验性引入，v3.0 成为默认优化器，替代了早期手工 RBO 规则。

## 优化器演进

| 阶段 | 优化器 | 特点 |
|------|--------|------|
| v0.x~v1.x | 无优化器 | 手工 SQL Rewrite 规则 |
| v1.x~v2.x | RBO (Rule-Based) | 固定规则重写，无成本模型 |
| v2.1+ | Nereids CBO (实验) | 基于成本，统计信息驱动 |
| v3.0+ | Nereids CBO (稳定) | 默认优化器，Join Reorder、CTE 重用 |
| v4.0 (计划) | Nereids + Falcon | 新执行引擎，Runtime Filter 增强 |

## Nereids CBO 核心能力

### 1. Join Reorder

基于表统计信息（RowCount/NDV）动态调整 Join 顺序，避免大表 × 大表的笛卡尔积式连接。传统 RBO 固定从左到右 Join 顺序，CBO 可根据数据量级选出最优 Join 树。

```
RBO:     A ⋈ B ⋈ C        （固定顺序）
CBO:     min(A, B, C) 作为 Build 侧   （自适应）
```

### 2. CTE 物化

公共表表达式（Common Table Expression）物化重用，避免重复计算。如果一个 CTE 在查询中被多次引用，Nereids 会将其结果物化，后续引用直接读取缓存。

```sql
WITH user_stats AS (
  SELECT user_id, COUNT(*) FROM orders GROUP BY user_id
)
SELECT * FROM user_stats WHERE cnt > 100
UNION ALL
SELECT * FROM user_stats WHERE cnt > 500;
-- Nereids: user_stats 仅计算一次，物化后两次引用共用
```

### 3. Runtime Filter

Join 的 Build 侧（小表）生成 Bloom Filter，**提前下推到 Scan 侧**过滤无效数据：

<svg viewBox="0 0 680 140" xmlns="http://www.w3.org/2000/svg" style="max-width:100%">
  <defs>
    <marker id="arrow-rf" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <path d="M0,0 L8,3 L0,6 Z" fill="currentColor"/>
    </marker>
  </defs>
  <!-- Step 1 -->
  <rect x="10" y="8" width="200" height="34" rx="6" fill="transparent" stroke="currentColor" stroke-width="2"/>
  <text x="110" y="27" font-family="sans-serif" font-size="12" fill="currentColor" text-anchor="middle" dominant-baseline="middle">小表 Build Hash Table</text>
  <line x1="210" y1="25" x2="240" y2="25" stroke="currentColor" stroke-width="2" marker-end="url(#arrow-rf)"/>
  <rect x="244" y="8" width="160" height="34" rx="6" fill="transparent" stroke="currentColor" stroke-width="2"/>
  <text x="324" y="27" font-family="sans-serif" font-size="12" fill="currentColor" text-anchor="middle" dominant-baseline="middle">同时生成 Bloom Filter</text>
  <!-- Label Step 1 -->
  <text x="10" y="50" font-family="sans-serif" font-size="11" fill="currentColor" stroke="currentColor" font-weight="bold">Step 1</text>

  <!-- Step 2 arrow -->
  <line x1="324" y1="42" x2="324" y2="62" stroke="currentColor" stroke-width="2" marker-end="url(#arrow-rf)"/>

  <!-- Step 2 -->
  <rect x="140" y="65" width="180" height="34" rx="6" fill="transparent" stroke="currentColor" stroke-width="2"/>
  <text x="230" y="84" font-family="sans-serif" font-size="12" fill="currentColor" text-anchor="middle" dominant-baseline="middle">Bloom Filter 广播到左表 Scan Node</text>
  <!-- Label Step 2 -->
  <text x="10" y="84" font-family="sans-serif" font-size="11" fill="currentColor" stroke="currentColor" font-weight="bold">Step 2</text>

  <!-- Step 3 arrow -->
  <line x1="230" y1="99" x2="230" y2="112" stroke="currentColor" stroke-width="2" marker-end="url(#arrow-rf)"/>

  <!-- Step 3 -->
  <rect x="20" y="115" width="420" height="34" rx="6" fill="transparent" stroke="currentColor" stroke-width="2"/>
  <text x="230" y="134" font-family="sans-serif" font-size="12" fill="currentColor" text-anchor="middle" dominant-baseline="middle">Scan Node 利用 Bloom Filter 提前过滤 → 大幅减少 Shuffle 数据量</text>
  <!-- Label Step 3 -->
  <text x="10" y="134" font-family="sans-serif" font-size="11" fill="currentColor" stroke="currentColor" font-weight="bold">Step 3</text>
</svg>


**效果**：大表 Join 小表场景，可过滤 50%~99% 的无效行。

### 4. Derived Column Rewrite

派生列改写，消除不必要的列计算。例如 `SELECT a+b FROM t WHERE a+b>10` → 复用已计算的表达式，避免重复计算。

---

## 与传统 RBO 的对比

| 维度 | RBO (v1.x~v2.x) | Nereids CBO (v3.0+) |
|------|-----------------|---------------------|
| 优化依据 | 固定规则 | 统计信息 + 成本模型 |
| Join 顺序 | 固定（SQL 书写顺序） | 动态（基于数据量级） |
| CTE 处理 | 内联展开（可能重复计算） | 物化复用 |
| Runtime Filter | 部分支持 | 深度集成 |
| 统计信息 | 无 | Table/Column/Partition 三级统计 |
| 扩展性 | 新规则需修改核心代码 | 插件式 Rule |

---

## 统计信息

Nereids CBO 依赖以下统计信息：

| 统计项 | 粒度 | 说明 |
|--------|------|------|
| RowCount | Table/Partition | 行数 |
| NDV (Number of Distinct Values) | Column | 基数估计 |
| NullCount | Column | 空值数 |
| Max/Min | Column | 值域范围 |
| Histogram | Column (可选) | 数据分布直方图 |

统计信息通过 `ANALYZE TABLE` 命令收集，支持自动和手动两种模式。

---

## 关键影响

- **Join 性能**：CBO Join Reorder 可将多表 Join 延迟降低 2-10x
- **Runtime Filter 整合**：优化器自动识别适合 Runtime Filter 的 Join，无需人工 Hint
- **生态兼容**：与 Lakehouse Catalog 联动，联邦查询也能利用 CBO 统计信息
