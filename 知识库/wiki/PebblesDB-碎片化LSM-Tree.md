---
type: concept
title: "PebblesDB: 碎片化 LSM-Tree (FLSM)"
sources:
  - "http://www.cs.utexas.edu/~vijay/papers/sosp17-pebblesdb.pdf"
  - "https://github.com/utsaslab/pebblesdb"
  - "https://github.com/utsaslab/pebblesdb/blob/master/benchmark.md"
tags:
  - 存储引擎
  - LSM-Tree
  - 写放大
  - 碎片化
  - Guards
  - FLSM
  - 合并优化
  - Tiering
  - SOSP2017
created: 2026-07-02
updated: 2026-07-02
status: draft
related:
  - "[[LSM-Tree]]"
  - "[[LSM-Tree-写放大]]"
  - "[[LSM-Tree-合并优化]]"
  - "[[LSM-Tree-RUM猜想]]"
  - "[[LSM-tree-KV-Survey-综述]]"
---
confidence: 0.75
confidence_rationale: "类型=concept; 来源×0; 4天前更新"


# PebblesDB: 碎片化 LSM-Tree (FLSM)

> **论文**: *PebblesDB: Building Key-Value Stores using Fragmented Log-Structured Merge Trees*, Pandian Raju, Rohan Kadekodi, Vijay Chidambaram, Ittai Abraham. SOSP 2017, ACM.
>
> **开源**: <https://github.com/utsaslab/pebblesdb>（基于 HyperLevelDB 修改，API 兼容 LevelDB/RocksDB，可作为 drop-in replacement）

## 一句话摘要

PebblesDB 提出 **FLSM (Fragmented Log-Structured Merge Trees)** 数据结构——通过引入 **Guards（哨兵）** 使用概率分布将每层的 key 空间划分为不相交区间（每个 guard 内允许多个 SSTable 有重叠 key range），将 compaction 从"全部重写下层数据"变为"按 guard 边界切分 + 追加"，从而将写放大降至 RocksDB 的 1/2~1/3（减少约 50% 的写 IO），同时通过 SSTable-level Bloom Filter 和并行 Seek 将读性能拉回到与传统 LSM 持平甚至反超。

## 核心创新：Guards 与碎片化 Level

### 问题根源：LSM-tree 的 Key-Range Disjointness 不变式

标准 Leveling LSM-tree（LevelDB/RocksDB）在每层维护核心不变式：**同一层内所有 SSTable 的 key range 互不重叠**（每个 key 在每层只存在于唯一一个 SSTable 中）。这确保了点查每层只需读 1 个 SSTable，但也带来了巨大的写放大——当 L_i 的 SSTable 需要 compact 到 L_{i+1} 时，只要 key range 与 L_{i+1} 的 SSTable 有交集，**下层所有相交的 SSTable 都必须被读取、merge-sort、重写成一个整块**。

### FLSM 的解法：打破不变式 + Guards 组织

FLSM **放弃**了"每层 SSTable key range 不重叠"的不变式。取而代之：

- **Guards（哨兵）**：每层用 guards 将 key 空间划分为**不相交的连续区间**。每个 guard G_i 关联一个 key (K_i)，G_i 负责 key range [K_i, K_{i+1}) 内的所有 SSTable。
- 同一 guard 内允许多个 SSTable **有重叠 key range**，但不同 guard 间 key range 不重叠。
- Guards 的密度随层级递增（低层 guards 少、区间粗；高层 guards 多、区间细），类似 Skip List 的方向指针结构。

### Guards 选择机制

- **概率选择**：每个插入的 key 经 MurmurHash 计算哈希值，取最低几位（LSB）判断是否成为该层的 guard。
- **层级传播**：若一个 key 在 Level i 被选为 guard，则对 Level i+1 ~ Level_max 它也是 guard（子集/超集关系——高层 guards 是低层 guards 的超集）。
- **异步插入**：新选出的 guard 先加入 `uncommitted guards` 集合，直到下一次 compaction 触发时才正式生效。
- **可调参数**：`top_level_bits`（决定最高层的 guard 密度）和 `bit_decrement`（逐层放宽位数），默认可支持 1 亿+ key 的规模。

### FLSM Compaction：从 Rewrite 到 Partition + Append

```
标准 Leveling LSM compaction：
  L_i 的 SSTable ∩ L_{i+1} 的相交 SSTable
  → merge-sort → 重写为一个新的合并 SSTable
  → 数据被重复读写多次（同一条记录在不同的 compaction round 中反复参与 merge）

FLSM compaction：
  Guard G 管辖的 SSTable → merge-sort →
  按 L_{i+1} 的 guard 边界做 partition（切分） →
  每个 partition 作为一个新的 SSTable 片段 append 到对应的 child guard
  → 数据在到达最底层之前，只需被写入一层一次！
```

**关键结果**：在 L1~L_{n-1} 层，数据不再被反复重写——compaction 从"重写一整层所有相交 SSTable"变为"切分 + 追加到下一层的对应 guard"。只有最底层（没有更下层可追加）需要真正重写。这是 FLSM 写放大极低的根本原因。

### 与 Tiering 的区别

| | FLSM (PebblesDB) | Tiering (RocksDB Universal) |
|---|---|---|
| 分组/分片方式 | Guards 按概率 hash 切分 key space（不相交） | 整层或垂直分组 |
| Compaction 方式 | Partition + Append（碎片化） | 多个 SSTable merge 成一个 |
| Key range 重叠 | Guard 间不重叠，Guard 内允许重叠 | 层内 SSTable 间允许重叠 |
| 读路径 | 查 1 个 guard/层，但 guard 内有 N 个 SSTable | 查层内**所有** SSTable |
| 范围查询效率 | 优于 Tiering（只查 1 个 guard 区间） | 需查整层全部 SSTable |

FLSM 本质上是 Leveling 和 Tiering 之间的一种折中——既不完全 Leveling（允许 guard 内重叠），也不完全 Tiering（guard 间严格不重叠），用 guards 做空间划分来约束读路径的搜索范围。

## PebblesDB 的读写优化

FLSM 的数据结构本身**牺牲了部分读性能换写吞吐**（每个 guard 内有多个 SSTable 可能都需要检查）。PebblesDB 通过以下关键优化将读性能拉回到持平甚至超越标准 LSM 的水平：

### 读优化

| 优化 | 原理 | 效果 |
|------|------|------|
| **SSTable-level Bloom Filter** | 每个 SSTable 附带 Bloom Filter，点查时先查 BF，跳过不含 key 的 SSTable。相比 HyperLevelDB 的 block-level BF，避免了 guard 内多次读盘 | 在每个 level 实际只需读 1 个 SSTable（概率性） |
| **并行 Seek** | 多线程并发执行 guard 内多个 SSTable 的 seek()，利用 SSD 内部并行性 | seek 延迟接近 LSM（数据远大于 RAM 时有效） |
| **Seek-based 强制 Compaction** | 连续 N 次 seek 定位到同一 guard 后，强制合并该 guard 内的多个 SSTable | 热点 guard 自动降碎片化，以少量写 IO 换 seek 性能 |
| **更大的 SSTable 文件** | FLSM compaction 产生的 SSTable 更大更少，索引块更容易在内存中缓存命中 | 读性能可比传统 LSM 反超（benchmark 中 +27% vs RocksDB） |
| **激进 Compaction 触发** | 若 L_i 大小达到 L_{i+1} 的 25%，立即触发 compaction，防止层级堆积 | 减少点查所需搜索的层数 |

### 调参旋钮

`kMaxFilesPerGuardSentinel`（`max_sstables_per_guard`）：**控制每个 guard 允许追加的最大 SSTable 数**。这是 FLSM 在读写之间权衡的**唯一核心参数**：

- Set to **1** → FLSM 退化为标准 Leveling LSM（每 guard 只有 1 个 SSTable）
- Set to **高值** → 降低 compaction 频率，提升写吞吐，但增加每个 guard 内的 SSTable 数 → 拉高读/seek 延迟
- **默认值：2**（论文实验中的最佳平衡点）

## 实验数据摘要

### Micro-benchmarks（db_bench, 单线程, 50M KV 对, 1KB value）

| 指标 | vs HyperLevelDB | vs RocksDB |
|------|-----------------|-----------|
| 随机写吞吐 | **2.7×** | **6.7×** |
| 读吞吐 | +20% | +27% |
| 写 IO（写放大） | -60% | -58%~67%（约 2.4-3× 降低） |
| Compaction 速度 | **2.5×** 更快 | — |
| Seek（全压实后最差场景） | -30% | — |
| 顺序写 | **退步**至 1/3（因 LSM 机械搬 SSTable 零 IO，FLSM 仍需 partition） | — |

### 多线程 (4 线程) & YCSB

| 场景 | PebblesDB 表现 |
|------|---------------|
| **随机写**（YCSB Load A/E） | 吞吐 1.5-2×，写 IO 减半 |
| **纯读**（YCSB Workload C） | 反超（更大的 SSTable → 更少的 table_cache 缺失） |
| **读写混合**（YCSB Workload A） | 写完得更快，Level 0 压力早解除，整体吞吐更高 |
| **范围查询**（YCSB Workload E） | 仅 ~6% 开销（5% 持续写入阻止了全压实，next() 操作摊平了 seek 开销） |
| **Read-Modify-Write**（YCSB Workload F） | 持平（每次写前必先读，无法发挥 FLSM 写吞吐优势） |
| **小缓存数据集** | 设置 max_sstables_per_guard=1 后性能恢复到与传统 LSM 相当 |

### 真实应用验证

| 应用 | 效果 |
|------|------|
| **MongoDB**（替换 RocksDB 存储引擎） | 同等吞吐 + IO 减少 37-40%，写放大低于 WiredTiger |
| **HyperDex**（替换默认的 HyperLevelDB） | 吞吐提升 18-59%，大 value（16KB）时几何平均提升 105% |

> **注意**：应用层自身的网络/序列化延迟 + "写前必读"模式（HyperDex 每个 put 前先 get 检查）会部分摊平 FLSM 的写优势，论文建议应用层需要改造才能最大化发挥 FLSM。

## 架构要点

### 存储布局

```
Level 0 (无 Guard)    [SSTable, SSTable, ...]       ← MemTable flush，可重叠
Level 1 (少量 Guard)   Sentinel [<K1]  G1 [K1~K2)  G2 [K2~K3)  ...
                       1 个 guard 内: [*.sst, *.sst, ...]
Level 2 (更多 Guard)   Sentinel  G1  G2  G3  G4  G5  ...
                       guard 密度是上层的 2 倍（bit_decrement=1）
...
Level_max (最多 Guard) ⋯  compact 到此层需要重写（无下层可追加）
```

### 实现细节

- **代码量**：在 HyperLevelDB 上新增/修改约 9,100 行 C++
- **Crash Recovery**：利用 LevelDB 的 MANIFEST + WAL 机制，额外持久化 guard 元数据
- **多线程 Compaction**：类似 RocksDB，背景线程按层选取 compaction 任务
- **Guard 删除**：论文中未实现（空 guard 对性能影响可忽略）
- **Guard 并行 Compaction**：论文中设计了 guard 间可并行 compaction，但未在开源代码中实现（提升空间存在）

## 局限性

| 局限 | 详情 | 影响 |
|------|------|------|
| **小范围查询退化** | 全压实后 small range query ~30% 开销（large range query 降至 11%） | 不适合"先大量写入再纯范围查询"的负载模式 |
| **顺序写退步** | 顺序写入时标准 LSM 可直接移动 SSTable（零 IO），FLSM 仍需 partition → 写入 | 吞吐降至 HyperLevelDB 的 ~1/3 |
| **全缓存数据集降级** | 数据全部 cached 时 guards 计算开销显性：读 -7%，seek -47% | 小数据集应配置 `max_sstables_per_guard=1` |
| **CPU 开销偏高** | 中位数 CPU 使用率 171%（其他 KV 98-110%） | 因更激进的 compaction 策略 |
| **额外内存** | +~300 MB（sstable bloom filters ~150MB + 构建临时空间 ~150MB） | 相比 HyperLevelDB |
| **Guard 并行未实现** | 论文设计可并行但开源代码未实现 | 仍有性能提升空间 |
| **无 Guard 删除机制** | 不再活跃的 guard 仍占据元数据 | 长期运行可能累积无效元数据 |

## 与标准 LSM-tree 的对比总结

| 维度 | Leveling LSM (LevelDB/RocksDB) | FLSM (PebblesDB) |
|------|-------------------------------|-------------------|
| 每层 Key Range 不变式 | 不重叠（每个 key 仅在 1 个 SSTable） | **打破**——Guard 内允许多 SSTable 重叠，Guard 间不重叠 |
| Compaction 操作 | Merge-sort → 重写整个下层相交 SSTable | **Partition + Append**：切分后追加到 child guard |
| 写放大 | 高（同一条数据每层重写一次） | **低**（最底层外每条数据只写入一层一次） |
| 点查（无 BF） | 每层 1 个 SSTable | 每层 1 个 Guard × N 个 SSTable |
| 点查（有 SSTable BF） | 每层 1 个 SSTable | **≈ 1 个 SSTable**（BF 剪枝后，概率性） |
| 范围查询 | 每层 1 个 SSTable iterator | 每层 N 个 SSTable iterators（需 merge） |
| 并行 Compaction | 需精细锁（key range 相交） | **天然可并行**（不同 guard 间不干扰） |
| 配置复杂度 | size ratio, level multiplier, compaction style 等多参数 | **一个旋钮** `max_sstables_per_guard` 控制所有 trade-off |
| 工程成熟度 | 多年生产验证 | 学术原型 (SOSP'17)，生产部署案例有限 |

## FLSM 在 RUM 猜想中的位置

从 [[LSM-Tree-RUM猜想]] 的角度分析，FLSM 在 Read-Update-Memory 三角上做了重新分配：

- **Write (Update) 大幅改善** 🟢：碎片化消除多层重写（写放大 2.4-3× ↓，写吞吐 6× vs RocksDB）
- **Read 基本持平** 🟡：SSTable Bloom Filter + 并行 Seek 抹平了 guard 内多 SSTable 的开销，大面积读甚至反超
- **Memory 少量增加** 🟡：额外需要 guards 元数据 + SSTable-level Bloom Filter（~300MB）
- **Range Query 退化** 🔴：最显著的牺牲——guard 内多 SSTable 需要 iterator merge，全压实后 ~30% 退化

FLSM 本质上是一种 **弱化的 Leveling（Weakened Leveling）**：用 guards 作为空间划分边界，guard 内允许去重（读代价可控），guard 间保持不相交（保证只需查 1 个 guard/层）。相比完全 Tiering，在大范围查询上有明显优势。

## 影响力与后续工作

- PebblesDB 是 **概率化、碎片化 compaction** 方向的里程碑工作，启发了后续 Stratified Tiering（Dostoevsky, SIGMOD '20）、SCoS（ICDE '23）、Probabilistic Tiering 等方案。
- 2025 年 LSM-tree KV 综述（[[LSM-tree-KV-Survey-综述]]）将 PebblesDB 列为"Data Layout"维度下 Leveling vs Tiering 切换路径中的重要基线。
- 其"compaction 只 partition 不 rewrite"的核心思想在新型硬件（ZNS SSD、Persistent Memory）上被持续继承和扩展。
- Titan（PingCAP/TiKV 的 blob storage 层）等工业项目借鉴了 FLSM 的 partition + append 思路来减少 compaction IO。
