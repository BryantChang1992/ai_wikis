---
type: concept
title: "Doris 数据模型：Duplicate / Aggregate / Unique"
sources:
  - "技术文章/Doris调研/01-概述与核心概念.md"
  - "技术文章/Doris调研/02-存储引擎.md"
tags:
  - 数据库
  - OLAP
  - Doris
  - 数据模型
  - Unique Key
  - Merge-on-Write
  - UPSERT
created: 2026-06-14
updated: 2026-06-14
status: draft
related:
  - "[[Doris-深度调研]]"
  - "[[Doris-Segment-v2-存储格式]]"
  - "[[Doris-Compaction-策略]]"
  - "[[LSM-Tree-RUM猜想]]"
---

# Doris 数据模型：Duplicate / Aggregate / Unique

## 概述

Apache Doris 提供四种表模型（实际为三种基础模型 + Unique 的两种实现），针对不同 OLAP 场景优化。模型选择直接影响写入性能、查询性能和存储成本。

## 模型详解

### 1. Duplicate 模型

**定位**：明细数据、日志类 Append-only 场景。

<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 500 40" width="500" height="40">
  <defs>
    <marker id="arrow-dor1" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <path d="M0,0 L8,3 L0,6 Z" fill="currentColor"/>
    </marker>
  </defs>
  <rect x="10" y="5" width="100" height="28" rx="5" fill="transparent" stroke="currentColor" stroke-width="1.2"/>
  <text x="60" y="19" font-family="sans-serif" font-size="12" fill="currentColor" text-anchor="middle" dominant-baseline="middle">写入</text>
  <line x1="110" y1="19" x2="150" y2="19" stroke="currentColor" stroke-width="1.2" marker-end="url(#arrow-dor1)"/>
  <text x="155" y="19" font-family="sans-serif" font-size="11" fill="currentColor" text-anchor="start" dominant-baseline="middle">追加新行（无去重，无聚合）</text>
  <text x="10" y="38" font-family="sans-serif" font-size="11" fill="currentColor" text-anchor="start" dominant-baseline="middle">查询 → 直接读取原始行</text>
</svg>

- **特点**：无聚合开销，写入吞吐最高
- **适用场景**：原始日志、事件流、无需去重的明细表
- **关键参数**：Sort Key（用于前缀索引，加速范围查询）

---

### 2. Aggregate 模型

**定位**：预聚合指标场景。

<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 530 40" width="530" height="40">
  <defs>
    <marker id="arrow-dor2" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <path d="M0,0 L8,3 L0,6 Z" fill="currentColor"/>
    </marker>
  </defs>
  <rect x="10" y="5" width="100" height="28" rx="5" fill="transparent" stroke="currentColor" stroke-width="1.2"/>
  <text x="60" y="19" font-family="sans-serif" font-size="12" fill="currentColor" text-anchor="middle" dominant-baseline="middle">写入</text>
  <line x1="110" y1="19" x2="150" y2="19" stroke="currentColor" stroke-width="1.2" marker-end="url(#arrow-dor2)"/>
  <text x="155" y="19" font-family="sans-serif" font-size="11" fill="currentColor" text-anchor="start" dominant-baseline="middle">同 Key 行按聚合函数合并（SUM / MAX / MIN / REPLACE）</text>
  <text x="10" y="38" font-family="sans-serif" font-size="11" fill="currentColor" text-anchor="start" dominant-baseline="middle">查询 → 读取聚合结果</text>
</svg>

- **特点**：写入时有聚合开销、查询无需聚合，查询极快
- **适用场景**：多维分析报表、漏斗分析、UV/PV 统计
- **聚合类型**：SUM、MAX、MIN、REPLACE（覆盖）、HLL_UNION（近似去重）、BITMAP_UNION（精准去重）
- **注意**：不能直接查询明细行，仅查询聚合结果

---

### 3. Unique 模型

**定位**：主键更新场景（宽表、CDC 同步、实时 UPSERT）。

Doris 提供两种实现方式，核心差异在于"何时合并去重"：

#### 3.1 Merge-on-Write (MoW) — Doris 2.1+ 默认

<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 700 250" width="700" height="250">
  <defs>
    <marker id="arrow-dor3" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <path d="M0,0 L8,3 L0,6 Z" fill="currentColor"/>
    </marker>
  </defs>
  <text x="10" y="18" font-family="sans-serif" font-size="13" fill="currentColor" text-anchor="start" dominant-baseline="middle" font-weight="bold">写入时：</text>
  <rect x="10" y="30" width="210" height="26" rx="5" fill="transparent" stroke="currentColor" stroke-width="1"/>
  <text x="115" y="43" font-family="sans-serif" font-size="11" fill="currentColor" text-anchor="middle" dominant-baseline="middle">1. 按 Sort Key 排序内存 Batch</text>
  <line x1="220" y1="43" x2="255" y2="43" stroke="currentColor" stroke-width="1.2" marker-end="url(#arrow-dor3)"/>
  <rect x="258" y="30" width="210" height="26" rx="5" fill="transparent" stroke="currentColor" stroke-width="1"/>
  <text x="363" y="43" font-family="sans-serif" font-size="11" fill="currentColor" text-anchor="middle" dominant-baseline="middle">2. 逐 Key 查询 Tablet 内是否存在</text>
  <line x1="363" y1="56" x2="363" y2="72" stroke="currentColor" stroke-width="1.2"/>
  <line x1="200" y1="72" x2="526" y2="72" stroke="currentColor" stroke-width="1.2"/>
  <line x1="200" y1="72" x2="200" y2="90" stroke="currentColor" stroke-width="1.2"/>
  <line x1="526" y1="72" x2="526" y2="90" stroke="currentColor" stroke-width="1.2"/>
  <rect x="110" y="90" width="180" height="26" rx="5" fill="transparent" stroke="currentColor" stroke-width="1" stroke-dasharray="4,2"/>
  <text x="200" y="103" font-family="sans-serif" font-size="11" fill="currentColor" text-anchor="middle" dominant-baseline="middle">├ 不存在 → 写入 Segment 新数据行</text>
  <rect x="370" y="90" width="310" height="26" rx="5" fill="transparent" stroke="currentColor" stroke-width="1" stroke-dasharray="4,2"/>
  <text x="525" y="103" font-family="sans-serif" font-size="11" fill="currentColor" text-anchor="middle" dominant-baseline="middle">└ 存在 → 标记旧行 DELETE_BITMAP + 写入新数据行</text>
  <line x1="200" y1="116" x2="200" y2="140" stroke="currentColor" stroke-width="1.2"/>
  <line x1="200" y1="140" x2="375" y2="140" stroke="currentColor" stroke-width="1.2"/>
  <line x1="375" y1="140" x2="375" y2="160" stroke="currentColor" stroke-width="1.2"/>
  <rect x="210" y="140" width="330" height="26" rx="5" fill="transparent" stroke="currentColor" stroke-width="1"/>
  <text x="375" y="153" font-family="sans-serif" font-size="11" fill="currentColor" text-anchor="middle" dominant-baseline="middle">3. Segment 写满（默认 256MB）后封存</text>
  <line x1="375" y1="166" x2="375" y2="185" stroke="currentColor" stroke-width="1.2" marker-end="url(#arrow-dor3)"/>
  <rect x="260" y="185" width="230" height="26" rx="5" fill="transparent" stroke="currentColor" stroke-width="1"/>
  <text x="375" y="198" font-family="sans-serif" font-size="11" fill="currentColor" text-anchor="middle" dominant-baseline="middle">4. Rowset 提交（可见）</text>
  <text x="10" y="228" font-family="sans-serif" font-size="13" fill="currentColor" text-anchor="start" dominant-baseline="middle" font-weight="bold">查询时：</text>
  <text x="115" y="228" font-family="sans-serif" font-size="11" fill="currentColor" text-anchor="start" dominant-baseline="middle">直接读最新版本 → 无合并开销</text>
</svg>

| 维度 | 表现 |
|------|------|
| 写入延迟 | 略高（需 Key 去重查询） |
| 查询延迟 | **最低**（无需多版本合并） |
| 存储空间 | 仅最新版本 |
| 适用 | 实时报表、CDC 同步、频繁更新 |

---

#### 3.2 Merge-on-Read (MoR) — 传统实现

<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 55" width="600" height="55">
  <defs>
    <marker id="arrow-dor4" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <path d="M0,0 L8,3 L0,6 Z" fill="currentColor"/>
    </marker>
  </defs>
  <text x="10" y="18" font-family="sans-serif" font-size="13" fill="currentColor" text-anchor="start" dominant-baseline="middle" font-weight="bold">写入时：</text>
  <text x="115" y="18" font-family="sans-serif" font-size="11" fill="currentColor" text-anchor="start" dominant-baseline="middle">不验证 Key 是否存在 → 直接追加新版本行</text>
  <text x="10" y="42" font-family="sans-serif" font-size="13" fill="currentColor" text-anchor="start" dominant-baseline="middle" font-weight="bold">查询时：</text>
  <text x="115" y="42" font-family="sans-serif" font-size="11" fill="currentColor" text-anchor="start" dominant-baseline="middle">读取同一 Key 的多版本行 → 合并取最新值</text>
</svg>

| 维度 | 表现 |
|------|------|
| 写入延迟 | 低（无去重开销） |
| 查询延迟 | **较高**（需合并多版本） |
| 存储空间 | 多版本历史 |
| 适用 | 大量追加、偶尔查询 |

---

## 模型选择指南

<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 650 180" width="650" height="180">
  <defs>
    <marker id="arrow-dor5" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <path d="M0,0 L8,3 L0,6 Z" fill="currentColor"/>
    </marker>
  </defs>
  <rect x="220" y="5" width="200" height="30" rx="15" fill="transparent" stroke="currentColor" stroke-width="1.5"/>
  <text x="320" y="20" font-family="sans-serif" font-size="12" fill="currentColor" text-anchor="middle" dominant-baseline="middle">写入模式是 Append-only？</text>
  <line x1="320" y1="35" x2="320" y2="50" stroke="currentColor" stroke-width="1.5"/>
  <line x1="180" y1="50" x2="460" y2="50" stroke="currentColor" stroke-width="1.5"/>
  <line x1="180" y1="50" x2="180" y2="65" stroke="currentColor" stroke-width="1.5"/>
  <line x1="460" y1="50" x2="460" y2="65" stroke="currentColor" stroke-width="1.5"/>
  <rect x="90" y="65" width="180" height="30" rx="15" fill="transparent" stroke="currentColor" stroke-width="1.2"/>
  <text x="180" y="80" font-family="sans-serif" font-size="12" fill="currentColor" text-anchor="middle" dominant-baseline="middle">需要聚合？</text>
  <line x1="180" y1="95" x2="180" y2="110" stroke="currentColor" stroke-width="1.2"/>
  <line x1="80" y1="110" x2="280" y2="110" stroke="currentColor" stroke-width="1.2"/>
  <line x1="80" y1="110" x2="80" y2="128" stroke="currentColor" stroke-width="1.2"/>
  <line x1="280" y1="110" x2="280" y2="128" stroke="currentColor" stroke-width="1.2"/>
  <rect x="8" y="128" width="150" height="28" rx="6" fill="transparent" stroke="currentColor" stroke-width="1"/>
  <text x="83" y="142" font-family="sans-serif" font-size="12" fill="currentColor" text-anchor="middle" dominant-baseline="middle">✅ Aggregate 模型</text>
  <rect x="200" y="128" width="150" height="28" rx="6" fill="transparent" stroke="currentColor" stroke-width="1"/>
  <text x="275" y="142" font-family="sans-serif" font-size="12" fill="currentColor" text-anchor="middle" dominant-baseline="middle">✅ Duplicate 模型</text>
  <rect x="395" y="65" width="210" height="30" rx="15" fill="transparent" stroke="currentColor" stroke-width="1.2"/>
  <text x="500" y="80" font-family="sans-serif" font-size="12" fill="currentColor" text-anchor="middle" dominant-baseline="middle">需要 UPSERT 主键更新？</text>
  <line x1="500" y1="95" x2="500" y2="110" stroke="currentColor" stroke-width="1.2"/>
  <line x1="420" y1="110" x2="580" y2="110" stroke="currentColor" stroke-width="1.2"/>
  <line x1="420" y1="110" x2="420" y2="128" stroke="currentColor" stroke-width="1.2"/>
  <line x1="580" y1="110" x2="580" y2="128" stroke="currentColor" stroke-width="1.2"/>
  <rect x="365" y="128" width="140" height="28" rx="6" fill="transparent" stroke="currentColor" stroke-width="1"/>
  <text x="435" y="142" font-family="sans-serif" font-size="11" fill="currentColor" text-anchor="middle" dominant-baseline="middle">Unique MoW</text>
  <text x="465" y="155" font-family="sans-serif" font-size="10" fill="currentColor" text-anchor="start" dominant-baseline="middle" font-style="italic">查询延迟敏感</text>
  <rect x="520" y="128" width="130" height="28" rx="6" fill="transparent" stroke="currentColor" stroke-width="1"/>
  <text x="585" y="142" font-family="sans-serif" font-size="11" fill="currentColor" text-anchor="middle" dominant-baseline="middle">Unique MoR</text>
  <text x="580" y="155" font-family="sans-serif" font-size="10" fill="currentColor" text-anchor="start" dominant-baseline="middle" font-style="italic">写入吞吐优先</text>
</svg>

## 与 LSM-Tree 的关系

Doris Unique MoW 的 DELETE_BITMAP 机制本质上借鉴了 [[LSM-Tree]] 的"写入时标记删除"策略，但不同于典型 LSM 的多层级合并——Doris 通过 Compaction 周期性地物理删除被标记的行，符合 [[LSM-Tree-RUM猜想]] 中"以写入开销换取查询性能"的 trade-off。

## 关键权衡

- **Duplicate**：极致写吞吐，但无去重/聚合能力
- **Aggregate**：极致查询速度，但丢失明细、写入有成本
- **Unique MoW**：查询最优，写入需 Key 查重
- **Unique MoR**：写入最快，查询需版本合并
