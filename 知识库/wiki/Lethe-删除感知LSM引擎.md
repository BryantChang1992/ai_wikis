---
type: concept
title: "Lethe: 删除感知 LSM 引擎"
sources:
  - "https://arxiv.org/abs/2006.04777"
  - "https://cs-people.bu.edu/mathan/publications/sigmod20-sarkar.pdf"
  - "https://disc-projects.bu.edu/lethe/"
tags:
  - LSM-Tree
  - 删除
  - Tombstone
  - Compaction
  - 隐私
  - 存储引擎
  - KV-store
created: 2026-07-02
updated: 2026-07-02
status: draft
related:
  - "[[LSM-Tree]]"
  - "[[LSM-Tree-合并优化]]"
  - "[[LSM-Tree-写放大]]"
  - "[[LSM-tree-KV-Survey-综述]]"
  - "[[LSM-Tree-RUM猜想]]"
---

# Lethe：一种可调优的删除感知 LSM 引擎

> Sarkar, Papon, Staratzis, Athanassoulis (Boston University)
> SIGMOD 2020, pp. 893–908 · arXiv: 2006.04777

## 一句话摘要

Lethe 是第一个将删除作为一等公民对待的 LSM 引擎，通过**删除感知的强制 Compaction 策略（FADE）**和**编织排序的物理存储布局（KiWi）**，首次实现对删除持久化延迟的可调保证，并支持高效的次级键范围删除。

---

## 1. 核心问题：LSM-tree 中删除是"二等公民"

### 标准 LSM-tree 的删除语义

在标准 LSM-tree 中，删除操作**不是物理删除**，而是写入一个特殊标记——**Tombstone**（墓碑，value 通常为 1 字节）：

```
DELETE key=foo  →  INSERT (key=foo, value=TOMBSTONE)  // 一条新写入
```

逻辑删除**立即生效**（后续查询不再返回该 key），但物理删除的发生时延完全不可控：

```
Tombstone 传播路径：
MemTable → L0 SST → L1 → L2 → ... → Ln（最终层）
                                            ↑
                                    到达 Ln 才物理删除 + 回收空间
```

这个传播延迟取决于四个不可控因素：
1. Compaction 的**文件选取策略**
2. 数据**写入速率**
3. LSM-tree 的**层间大小比**（size ratio）
4. 树的**总层数**

### 三类关键场景被忽视

| 场景 | 痛点 |
|------|------|
| **流处理窗口数据** | 过期数据无法及时清理，浪费带宽和存储 |
| **隐私合规（GDPR 被遗忘权）** | Tombstone 到达 Ln 前，被删除数据可被磁盘取证恢复 |
| **大规模云部署** | 存储成本敏感，无效数据占据大量空间 |

此外，标准的 LSM 引擎**只支持按排序键删除**。要按其他属性（如 timestamp）批量删除，商业系统通常每 7/15/30 天做一次**全树 Compaction**——极其昂贵的操作。

---

## 2. 两大利器：FADE + KiWi

Lethe 由两个正交组件构成：

### 2.1 FADE：删除感知的强制 Compaction 策略

**核心思想**：引入**删除持久化阈值**（Delete Persistence Threshold），为每层分配 TTL，墓碑超时即触发强制 Compaction。

```
用户设定阈值 Δ（如 10 分钟）

Lethe 为每层计算 Level-TTL：
  TTL(L1) < TTL(L2) < ... < TTL(Ln) ≤ Δ

当某 SSTable 中最老 Tombstone 的年龄 > 该层的 TTL 时：
  → 强制发起 Compaction（与饱和度触发完全正交）
  → 将该 SSTable 优先推向下一层
  → 直到 Tombstone 到达 Ln，完成物理删除
```

**关键设计要点**：

| 设计要素 | 说明 |
|----------|------|
| 额外元数据 | 每个文件记录**最老 Tombstone 的时间戳**和估计的**每墓碑无效条目数**——开销极小 |
| 触发正交性 | FADE 触发与传统的饱和度触发完全独立，不需要改动现有 Compaction 策略核心 |
| 阈值可调 | 用户/应用可设定任意删除持久化延迟目标——从秒级到小时级 |
| 精确性维持 | 即使在倾斜写入负载下，FADE 也能通过在更早阶段设定更紧的 deadline 来保证阈值遵守 |

**工作流程示意**：

```
          阈值 Δ = 10min
          ─────────────────────────────>
          L1 TTL=2min   L2 TTL=5min   Ln TTL=10min
          
Tombstone 年龄:
  t=0  →  写入 MemTable
  t=2  →  超过 L1-TTL，强制 Compaction 到 L2
  t=5  →  超过 L2-TTL，强制 Compaction 到 Ln
  t=5  →  到达 Ln，完成物理删除 ✓（远在 Δ 过期前）
```

### 2.2 KiWi：编织排序的物理存储布局

**核心思想**：在磁盘上按**排序键（S）**与**删除键（D）**的编织顺序组织数据，使次级范围删除只需丢弃整页。

```
传统 LSM 布局（纯按 S 排序）:
  S=1 S=5 S=8 S=12 ...    ← 要删 D<66 的条目 → 必须扫描全树

KiWi 布局（S-D 编织排序）:
  文件 → Delete Tile → Page
          ↑ 新增层
  Tile 内部按 D 分区，Page 内部按 S 重排序：
  
  ┌─────────────────────────────────┐
  │  Delete Tile (D-range: 1-100)   │
  │  ┌──────────┐ ┌──────────┐      │
  │  │ Page 1   │ │ Page 2   │ ...  │  ← 每页内按 S 排序（保留二分查找能力）
  │  │ D in     │ │ D in     │      │
  │  │ [1,50]   │ │ [51,100] │      │
  │  └──────────┘ └──────────┘      │
  └─────────────────────────────────┘
  
  执行 DELETE WHERE D < 66：
  → 定位受影响 Tile → 整页丢弃 Page 1 → O(1) 完成
```

**KiWi 的三层结构**（新增 Delete Tile 层）：

| 层级 | 排序维度 | 作用 |
|------|----------|------|
| 文件内 Tile 间 | 按 D 分区 | 将同一删除键范围的条目聚集 |
| Tile 内 Page 间 | 按 D 分段 | 进一步缩小删除影响面 |
| Page 内条目间 | 按 S 排序 | 保留点查的二分查找能力 |

**设计权衡**：

- **Delete Tile 粒度**：粒度越大（单 Tile 覆盖更多 D 范围）→ 点查退化为全文件扫描 → 读性能下降；粒度越小（更多 Tile）→ 元数据开销增大 → 写性能下降
- **可导航的连续布局空间**：KiWi 形成一个从"纯 S 排序"到"纯 D 排序"的连续谱系，Lethe 可根据 workload 动态选择最优布局点

---

## 3. 实验结果

实验配置：1GB 数据（平均条目 1KB），内存 buffer 1MB，size ratio = 10。

| 指标 | Lethe vs RocksDB | 关键条件 |
|------|-----------------|----------|
| **读吞吐** | **1.17–1.4×** | 及时清除无效条目 → 降低 Bloom Filter 误判率 |
| **空间放大** | **降低 2.1–9.8×** | Tombstone 及无效数据被准时物理删除 |
| **写放大** | **增加 4%–25%** | FADE 强制 Compaction 的额外 I/O 代价——阈值的直接代价 |
| **删除持久化** | **按时完成** | 在不同阈值（16.67%/25%/50% 运行时间）下均严格遵守 |

**KiWi 单独评估**：

- 更大的 Delete Tile 粒度 → 更多**整页丢弃**→ 更少 I/O（单次次级删除操作）
- 不同 workload 的最优粒度不同 → Lethe 可在连续布局空间中自动选择

---

## 4. 与标准 LSM-tree 删除语义对比

| 维度 | 标准 LSM（RocksDB/LevelDB） | Lethe |
|------|---------------------------|-------|
| 删除方式 | 逻辑删除（Tombstone） | 逻辑删除 + 强制传播 |
| 物理删除时延 | **不可控**（取决于写入速率、层数、Compaction 策略等） | **用户可设定阈值**（Δ） |
| 删除触发 | 仅靠饱和度驱动 Compaction 被动传播 | FADE 超时驱动 + 饱和度驱动，双正交触发 |
| 次级键删除 | **全树 Compaction**（极其昂贵，商用系统每 7–30 天一次） | **KiWi 整页丢弃**（无需全树重写） |
| 空间放大 | 高（无效条目 + Tombstone 长期滞留在各层） | 低（准时清理） |
| 读性能 | 受 Tombstone 污染 BF → 误判率上升 | BF 更干净 → 误判率更低 |
| 写放大 | 低（标准 Compaction 不急于传播 Tombstone） | 略高（+4%–25%，强制传播的代价） |
| 隐私合规 | **不满足**：Tombstone 到达 Ln 前数据可被取证恢复 | **满足**：按设定 Δ 保证物理删除 |

---

## 5. 架构设计要点

### 5.1 元数据开销

FADE 额外维护的元数据极其轻量：
- 每个 SSTable：`oldest_tombstone_timestamp` + `estimated_invalid_entries_per_tombstone`
- 无需额外索引结构

### 5.2 与现有 Compaction 的兼容性

FADE 的触发逻辑与饱和度触发**完全正交**——可以作为独立模块叠加到任何 LSM 引擎上，无需修改现有 Compaction 策略（Leveled、Tiered、Lazy-leveling 等）。

### 5.3 KiWi 的读性能保证

尽管 KiWi 在 Tile 间按 D 排序，但每个 Page 内部仍按 S 排序。这意味着：
- **点查**：仍可在 Page 内做二分查找（O(log N_page)），不受 D 排序影响
- **范围查（按 S）**：需要跨 Tile 扫描，代价随 Tile 粒度增大而上升——这是可调的

---

## 6. 局限性

1. **写放大增加不可避免**：FADE 强制 Compaction 的本质是以额外的写 I/O 换取删除持久化保证和更低的空间放大。这是 RUM 猜想在删除维度的直接体现
2. **KiWi 的读惩罚可调但不可消除**：跨 Tile 的范围扫描始终比纯 S 排序布局慢——只能在读性能与次级删除效率之间取舍
3. **仅支持两类删除键**：FADE 处理主排序键删除，KiWi 处理单一次级删除键——不支持任意属性的多删除键场景
4. **未解决 Update 传播**：论文聚焦于 Delete，未涉及 Update（实际上 Update 在 LSM-tree 中也是插入一条新记录）
5. **阈值设定依赖应用经验**：Δ 的选择直接影响写放大 vs 空间放大/隐私的平衡，没有自动化建议机制
6. **无分布式考量**：Lethe 设计面向单机 LSM 引擎，未涉及分布式 KV Store 的副本一致性与删除传播问题
7. **评测规模有限**：1GB 数据集的实验难以反映 TB 级生产环境下的行为

---

## 7. 在知识库中的位置

| 概念 | 关系 |
|------|------|
| [[LSM-Tree]] | Lethe 是对 LSM-tree 删除路径的专项增强 |
| [[LSM-Tree-合并优化]] | FADE 为 Compaction 引入了一个新触发维度——**删除时延驱动**（与传统的饱和度驱动正交） |
| [[LSM-Tree-写放大]] | FADE 的强制 Compaction 增加了写放大——这是删除保证的显式代价 |
| [[LSM-Tree-RUM猜想]] | 读放大、写放大、空间放大在删除维度的新平衡点 |
| [[LSM-tree-KV-Survey-综述]] | 综述中唯一专门讨论隐私删除的独立引擎 |
| [[Doris-Compaction-策略]] | ClickHouse/Doris 的 Compaction 同样面临删除传播延迟问题 |

---

## 参考文献

1. Sarkar, S., Papon, T. I., Staratzis, D., & Athanassoulis, M. (2020). *Lethe: A Tunable Delete-Aware LSM Engine.* In Proceedings of the 2020 ACM SIGMOD International Conference on Management of Data (pp. 893–908). [DOI: 10.1145/3318464.3389757](https://doi.org/10.1145/3318464.3389757)
2. Lv, Y., Li, Q., Xu, Q., Gao, C., Yang, C., Wang, X., & Xue, C. J. (2025). *Rethinking LSM-tree based Key-Value Stores: A Survey.* arXiv:2507.09642.（Section 3.2 — 删除与隐私部分）
