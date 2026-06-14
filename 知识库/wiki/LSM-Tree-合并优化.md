---
type: concept
title: "LSM-Tree 合并优化 (Merge Optimization)"
sources:
  - "sources/papers/LSM-Survey/LSM-Survey-VLDBJ2019.pdf"
  - "sources/papers/LSM-Survey/精读分析.md"
  - "sources/papers/LSM-Survey/全文翻译.md"
tags:
  - 存储引擎
  - LSM-Tree
  - 合并
  - Compaction
  - 性能优化
created: 2026-06-14
updated: 2026-06-14
status: draft
related:
  - "[[LSM-Tree]]"
  - "[[LSM-Tree-写放大]]"
  - "[[LSM-Tree-自动调参]]"
  - "[[LSM-Tree-RUM猜想]]"
---

# LSM-Tree 合并优化 (Merge Optimization)

## 定义

LSM-tree 的合并（compaction/merge）是将一个或多个 SSTable 按 key 排序合并为新的 SSTable 的过程。合并是 LSM-tree 的核心操作——它既决定了写放大，也决定了查询性能和空间利用率。优化合并过程主要有三个维度：**合并性能**、**缓冲区管理**、**写入停顿控制**。

## 三大优化方向

### 1. 合并性能优化 (Merge Performance)

#### VT-tree Stitching（指针拼接）

**原理**：当两个参与合并的 SSTable 的某些 page 在 key 范围上完全不重叠时，不拷贝数据，而是通过指针直接引用旧 SSTable 的 page。

| 优点 | 缺点 |
|------|------|
| 减少数据拷贝，提高合并速度 | 导致文件碎片化 |
| 内存开销降低 | **与 Bloom Filter 不兼容**（BF 依赖 SSTable 完整性） |
| | 需要额外索引管理 stitched pages |

**适用场景**：数据不重叠较多的场景（如时间分区数据），但由于碎片化和 BF 不兼容，实际应用受限。

#### 流水线合并 (Pipelined Merge)

**原理**：将合并操作拆分为多个流水线阶段（读 → 排序 → 写），各阶段并行执行，隐藏 I/O 延迟。

**效果**：提升合并吞吐量，但不改变合并的总 I/O 量。

### 2. 缓冲区管理 (Buffer Cache)

#### LSbM-tree（延迟删除缓冲区）

**核心思想**：合并完成后**不立即删除**旧 SSTable，而是将其附加到目标层的缓冲区中。利用操作系统的 buffer cache 访问频率信息，逐步清理访问最少的旧文件。

```
Merge(SST_old_Li, SST_Li+1) → SST_new_Li+1 + SST_old_kept_in_buffer
                                    ↑
                         buffer cache 根据访问频率逐步驱逐旧 SSTable
```

| 优点 | 缺点 |
|------|------|
| 热数据主动留在 cache，查询受益 | 冷数据场景有额外空间开销 |
| 利用 OS buffer cache 的成熟 LRU 机制 | 增加合并操作的复杂度 |
| 减少因过早删除导致的 cache miss | |

**适用场景**：有明显热数据的工作负载。

### 3. 写入停顿控制 (Write Stalls)

#### 问题描述

当 L0 文件数达到阈值或合并速度跟不上写入速度时，LSM-tree 必须停顿（stall）写入来等待合并完成。这导致**写入延迟尖刺（latency spike）**，严重影响 P99 延迟。

#### bLSM — Spring-and-Gear 调度器

**唯一尝试系统性地解决写入停顿的工作**（SIGMOD 2012）。

**核心机制**：
1. **Spring**：弹性调度——合并线程根据写入负载动态调整工作速率
2. **Gear**：多级调度——在不同层使用不同的合并速率阈值

| 已解决 | 未解决 |
|--------|--------|
| Bounded 了写入内存组件的延迟 | 未解决排队延迟 |
| 提供可预测的写入延迟 | 端到端延迟方差仍是盲区 |
| | 只考虑了内存到磁盘的阶段 |

**现状**：bLSM 之后，写入停顿问题没有获得更多系统性的关注，尽管大量生产系统（RocksDB、HBase）实际受到写入停顿的困扰。

## 与其他优化的关系

| 优化类别 | 关联概念 |
|----------|---------|
| 合并频率控制 | [[LSM-Tree-写放大]] — Tiering 降低合并频次 |
| 合并策略选择 | [[LSM-Tree-自动调参]] — Dostoevsky lazy-leveling 混合合并策略 |
| 合并与硬件 | [[LSM-Tree-硬件适配]] — 多核并行合并（cLSM）、NVM 持久化内存组件 |
| 二级索引合并 | [[LSM-Tree-二级索引]] — 关联合并同步多个索引 |

## 未来方向

1. **写入停顿的系统性解决**：bLSM 之后近十年，端到端延迟方差仍是盲区
2. **流水线合并与多核**：将现代多核架构与流水线合并结合的潜力未充分挖掘
3. **合并策略与负载自适应**：根据实时负载特征动态切换合并策略

---

*参考论文: Luo & Carey, "LSM-based Storage Techniques: A Survey", VLDB Journal 2019*
