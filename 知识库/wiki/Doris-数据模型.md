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

```
写入 → 追加新行（无去重，无聚合）
查询 → 直接读取原始行
```

- **特点**：无聚合开销，写入吞吐最高
- **适用场景**：原始日志、事件流、无需去重的明细表
- **关键参数**：Sort Key（用于前缀索引，加速范围查询）

---

### 2. Aggregate 模型

**定位**：预聚合指标场景。

```
写入 → 同 Key 行按聚合函数合并（SUM/MAX/MIN/REPLACE）
查询 → 读取聚合结果
```

- **特点**：写入时有聚合开销、查询无需聚合，查询极快
- **适用场景**：多维分析报表、漏斗分析、UV/PV 统计
- **聚合类型**：SUM、MAX、MIN、REPLACE（覆盖）、HLL_UNION（近似去重）、BITMAP_UNION（精准去重）
- **注意**：不能直接查询明细行，仅查询聚合结果

---

### 3. Unique 模型

**定位**：主键更新场景（宽表、CDC 同步、实时 UPSERT）。

Doris 提供两种实现方式，核心差异在于"何时合并去重"：

#### 3.1 Merge-on-Write (MoW) — Doris 2.1+ 默认

```
写入时：
  1. 按 Sort Key 排序内存 Batch
  2. 逐 Key 查询 Tablet 内是否存在
     ├── 不存在 → 写入 Segment 新数据行
     └── 存在 → 标记旧行 DELETE_BITMAP + 写入新数据行
  3. Segment 写满（默认 256MB）后封存
  4. Rowset 提交（可见）

查询时：
  直接读最新版本 → 无合并开销
```

| 维度 | 表现 |
|------|------|
| 写入延迟 | 略高（需 Key 去重查询） |
| 查询延迟 | **最低**（无需多版本合并） |
| 存储空间 | 仅最新版本 |
| 适用 | 实时报表、CDC 同步、频繁更新 |

---

#### 3.2 Merge-on-Read (MoR) — 传统实现

```
写入时：
  不验证 Key 是否存在 → 直接追加新版本行

查询时：
  读取同一 Key 的多版本行 → 合并取最新值
```

| 维度 | 表现 |
|------|------|
| 写入延迟 | 低（无去重开销） |
| 查询延迟 | **较高**（需合并多版本） |
| 存储空间 | 多版本历史 |
| 适用 | 大量追加、偶尔查询 |

---

## 模型选择指南

```
                     写入模式是 Append-only？
                         ├── Yes → 需要聚合？
                         │          ├── Yes → Aggregate 模型
                         │          └── No  → Duplicate 模型
                         └── No  → 需要 UPSERT 主键更新？
                                    ├── 查询延迟敏感 → Unique MoW
                                    └── 写入吞吐优先 → Unique MoR
```

## 与 LSM-Tree 的关系

Doris Unique MoW 的 DELETE_BITMAP 机制本质上借鉴了 [[LSM-Tree]] 的"写入时标记删除"策略，但不同于典型 LSM 的多层级合并——Doris 通过 Compaction 周期性地物理删除被标记的行，符合 [[LSM-Tree-RUM猜想]] 中"以写入开销换取查询性能"的 trade-off。

## 关键权衡

- **Duplicate**：极致写吞吐，但无去重/聚合能力
- **Aggregate**：极致查询速度，但丢失明细、写入有成本
- **Unique MoW**：查询最优，写入需 Key 查重
- **Unique MoR**：写入最快，查询需版本合并
