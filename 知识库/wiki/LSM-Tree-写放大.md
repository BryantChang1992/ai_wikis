---
type: concept
title: "LSM-Tree 写放大 (Write Amplification)"
sources:
  - "sources/papers/LSM-Survey/LSM-Survey-VLDBJ2019.pdf"
  - "sources/papers/LSM-Survey/精读分析.md"
  - "sources/papers/LSM-Survey/全文翻译.md"
tags:
  - 存储引擎
  - LSM-Tree
  - 写放大
  - 性能优化
  - Tiering
created: 2026-06-14
updated: 2026-06-14
status: draft
related:
  - "[[LSM-Tree]]"
  - "[[LSM-Tree-合并优化]]"
  - "[[LSM-Tree-RUM猜想]]"
---

# LSM-Tree 写放大 (Write Amplification)

![[diagram/lsm-write-amplification.svg]]
## 定义

**写放大 (Write Amplification, WA)** 指实际写入磁盘的数据量与应用写入数据量之比。在 LSM-tree 中，写放大主要源于合并（compaction）过程中同一数据被反复读写：一条记录从 L0 逐层合并到 L_max，在 Leveling 策略下每层都要重写一次。

## 写放大的根源

LSM-tree 的合并过程导致每次 compaction 都需要读取并重写整层的 SSTable。对于 Leveling 策略：

```
WA_leveling = O(T · L / B)
```

其中 T = size ratio（每层大小倍数），L = 层数，B = 内存缓冲区大小。Tiering 策略的写放大则为：

```
WA_tiering = O(L / B)
```

## Leveling vs Tiering 写放大对比

| 维度 | Leveling | Tiering |
|------|----------|---------|
| 写放大 | O(T·L/B) **高** | O(L/B) **低** |
| 点查 | O(L·e^(-M/N)) **低** | O(T·L·e^(-M/N)) **高** |
| 短范围查询 | O(L) **快** | O(T·L) **慢** |
| 空间放大 | O((T+1)/T) ≈ 1 **小** | O(T) **大** |

**关键洞察**：Tiering 写放大低但空间放大高、查询慢；Leveling 恰好相反。Size ratio T 是调节杠杆——T 越大，两种策略的差异越大。

## 降低写放大的三类方案

### 1. Tiering 及其变体

**原理**：在每一层保留多个 SSTable 组件（≤ T 个），只在达到阈值时才合并，大幅减少每层被重写的次数。

**变体对比**：

| 变体 | 分组方式 | 负载均衡 | 特点 |
|------|---------|---------|------|
| 传统 LevelDB tiering | 整层 | 无 | L0 使用，简单 |
| Cassandra tiering | 整层 | 无 | 每层多个 SSTable |
| Stratified tiering | 垂直分组（按层） | 动态收缩/扩展 | 每层独立管理 tiering |
| HBase | 水平分组（按键范围） | 哈希 | 大 region 用 striping 分区 |
| Probabilistic tiering | 垂直分组 | 概率 guard | 概率控制合并次数 |
| TRIAD | 热冷分离 | 无均衡 | 热键留内存 + 延迟 L0 合并 |

### 2. Merge Skipping（跳过合并）

**核心思想**：数据不逐层合并，而是跳过中间层直接写入更底层。

**代表方案 — Skip-tree**：
- 将 entry 直接推到 K 层以下的**可变缓冲区**
- 跳过中间的逐层 merge，减少重复写
- **代价**：实现复杂度显著增加，边界情况处理困难

### 3. 数据倾斜利用（TRIAD）

**核心思想**：利用工作负载的数据倾斜（skew）——热键不参与常规合并。

| 组件 | TRIAD 策略 | 效果 |
|------|-----------|------|
| 热键内存 | 热键留在内存不刷盘 | 减少热键的 merge 参与 |
| L0 合并 | 延迟 L0 到 L1 合并 | 减少频繁更新的合并开销 |
| 事务日志 | TRAN（事务日志做磁盘组件） | 利用事务日志减少写 |

## 写放大与其他维度的 Trade-off

降低写放大通常以牺牲查询性能或空间利用率为代价，这就是 [[LSM-Tree-RUM猜想]] 的核心：读(R)、写(U)、空间(M) 三者不可兼得。

具体而言：
- **Tiering** → 写 ↓，但点查 ↓、范围查询 ↓、空间 ↑
- **KV 分离** ([[LSM-Tree-硬件适配#WiscKey]]) → 写 ↓↓，但范围查询 ↓↓↓、空间 ↓↓↓（GC 开销）
- **Merge Skipping** → 写 ↓，但实现复杂度 ↑

## 未来方向

- 分区 Tiering 变体之间（垂直分组 vs 水平分组）的性能特征和 trade-off 尚不明确
- 写放大缩小的同时如何保持查询性能和空间效率仍需系统研究

---

*参考论文: Luo & Carey, "LSM-based Storage Techniques: A Survey", VLDB Journal 2019*
