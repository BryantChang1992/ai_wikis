---
type: concept
title: "Doris Compaction 策略"
sources:
  - "技术文章/Doris调研/02-存储引擎.md"
tags:
  - 数据库
  - OLAP
  - Doris
  - 存储引擎
  - Compaction
  - LSM-Tree
  - Merge-on-Write
created: 2026-06-14
updated: 2026-06-14
status: draft
related:
  - "[[Doris-深度调研]]"
  - "[[Doris-Segment-v2-存储格式]]"
  - "[[Doris-数据模型]]"
  - "[[LSM-Tree-合并优化]]"
  - "[[LSM-Tree-RUM猜想]]"
---

# Doris Compaction 策略

## 概述

Doris Compaction 负责将多个小 Rowset 合并为大 Rowset，减少碎片、加速查询、物理回收 DELETE_BITMAP 空间。每个 Replica 独立执行 Compaction，不依赖跨副本一致性。

## 四种 Compaction 类型

### 1. Cumulative Compaction

| 项目 | 说明 |
|------|------|
| 触发条件 | Cumulate Point 之前的 Rowset 数量超过阈值 |
| 作用 | 合并大量小 Rowset 为较大的 Rowset |
| 频率 | 高频（数据写入密集时持续触发） |
| 优先级 | 低（不影响在线服务） |

**典型场景**：Routine Load 持续写入产生大量小 Rowset，通过 Cumulative Compaction 逐步合并。

---

### 2. Base Compaction

| 项目 | 说明 |
|------|------|
| 触发条件 | Base Rowset 版本过期，或累积到一定条件 |
| 作用 | 合并所有 Rowset 为单一 Base Rowset |
| 频率 | 低频（仅当数据不再频繁写入时） |
| 优先级 | 低 |

**典型场景**：历史分区数据不再写入，触发 Base Compaction 将全部增量 Rowset 合并为一个，释放空间、提升查询效率。

---

### 3. Quick Compaction

| 项目 | 说明 |
|------|------|
| 触发条件 | MoW 表 Segment 数超过阈值（由 DELETE_BITMAP 过多导致） |
| 作用 | 局部合并 DELETE_BITMAP 过多的小 Segment |
| 频率 | 中频 |
| 优先级 | 中 |

**核心价值**：DELETE_BITMAP 过多会显著拖慢查询（每个查询需加载大量位图）。Quick Compaction 快速回收被标记删除的空间，降低查询开销。

---

### 4. Vertical Compaction

| 项目 | 说明 |
|------|------|
| 触发条件 | 宽表（Column 数 > 阈值） |
| 作用 | 按列组合并，将大宽表拆分为多次合并 |
| 频率 | 低频（仅宽表触发） |
| 优先级 | 低 |

**核心价值**：传统 Rowset 合并需同时加载所有列到内存，宽表（数千列）可能 OOM。Vertical Compaction 按列组分批合并，降低内存峰值。

## Compaction 执行流程

```
1. BE Compaction 线程池定期扫描 Tablet 状态
2. 选取待合并 Rowset 列表
3. 读取源 Rowset 所有 Segment，按 Sort Key 归并排序
4. MoW 表：同时合并 DELETE_BITMAP，物理删除标记行
5. 写入新 Rowset 到磁盘
6. 原子替换旧 Rowset 元数据
```

## 一致性保证

| 阶段 | 保证 |
|------|------|
| 选择 Rowset | 仅选已 Publish 版本 |
| 合并执行 | 读取源 → 合并 → 写新文件（**不修改源文件**） |
| 原子替换 | CAS 替换元数据指针 |
| 并发安全 | 每 Tablet 同时最多 1 个 Compaction |
| 失败处理 | 新 Rowset 作废，下次重试 |

## 与 LSM-Tree Compaction 的对比

Doris Compaction 与经典 [[LSM-Tree-合并优化|LSM-Tree 合并优化]] 的核心差异：

| 维度 | 经典 LSM (RocksDB) | Doris Compaction |
|------|---------------------|-------------------|
| 合并层级 | 固定层级 (L0→L1→...→Ln) | 无固定层级（Rowset 版本链） |
| 触发策略 | 层级大小超限 | Rowset 数量/版本过期 |
| 列式优化 | 无 | Vertical Compaction 按列分批 |
| MoW 适配 | 无内建支持 | Quick Compaction 回收 DELETE_BITMAP |
| 并发模型 | 单线程或多线程 Level | 各 Tablet 独立并发 |

## 性能影响

- Cumulative/Base Compaction：IO 和 CPU 开销较大，通过优先级控制避免影响在线查询
- Quick Compaction：轻量级，快速回收过期 DELETE_BITMAP 空间
- 过度 Compaction 会导致 [[LSM-Tree-RUM猜想|写放大]]，需监控 Compaction Score
