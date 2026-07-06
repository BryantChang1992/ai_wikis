---
type: concept
title: "Pacman: 持久内存加速 LSM-tree Compaction"
aliases:
  - Pacman Compaction
  - Pacman (ATC 2022)
  - PM-Accelerated LSM Compaction
sources:
  - title: "Pacman: An Efficient Compaction Approach for Log-Structured Merge-Tree on Persistent Memory"
    venue: USENIX ATC 2022
    url: https://www.usenix.org/conference/atc22/presentation/mamandipoor
    year: 2022
tags:
  - storage
  - LSM-tree
  - persistent-memory
  - compaction
  - kv-store
  - NVM
  - write-amplification
status: draft
created: 2026-07-02
related:
  - "[[LSM-Tree]]"
  - "[[LSM-Tree-合并优化]]"
  - "[[LSM-Tree-硬件适配]]"
  - "[[LSM-tree-KV-Survey-综述]]"

---
confidence: 0.75
confidence_rationale: "类型=concept; 来源×0; 4天前更新"


# Pacman: 持久内存加速 LSM-tree Compaction

## 一句话摘要

利用持久内存(PM/NVM)加速 LSM-tree 的 compaction 过程：将 compaction 中开销最大的引用查找(reference lookup)操作 offload 到 NVM 上，配合冷热数据分离策略，在不牺牲持久性保证的前提下显著降低写放大和 DRAM 占用。

## 问题背景

LSM-tree 的 compaction 是系统性能的核心瓶颈。传统 compaction 面临三大痛点：

1. **写放大严重**：同一数据在多层之间反复读写，LevelDB/RocksDB 写放大可达 10-50x
2. **DRAM 压力大**：Bloom filter、block index、SST metadata 全部驻留内存
3. **Compaction 本身开销大**：多路归并时需要频繁进行 key 查找和比较，尤其是跨 SST 的引用解析(reference resolution)

传统优化如 tiered compaction、leveled compaction 在不同工作负载下各有优劣，但都受限于磁盘 I/O 和有限的 DRAM 资源。

## 核心创新

### 1. Tagged Pointer 元数据管理

Pacman 的核心数据结构是 **tagged pointer**：在每个 SST 文件的 64-bit 指针中嵌入类型标签，区分：

- **Data block** 指针：指向实际数据块
- **Reference block** 指针：指向间接引用块
- **Bloom filter** 指针：指向布隆过滤器
- **Index block** 指针：指向索引结构

```text
------------------------------------------------------
|   63    60 | 59                       0              |
|  ------- | ------------------------------------- |
|  | Tag   | | |         Offset / Address            | |
|  ------- | ------------------------------------- |
------------------------------------------------------
         4-bit tag                  60-bit pointer
```

这样在 compaction 遍历 SST 元数据时，无需额外查表即可区分指针类型，极大加速了引用解析过程。

### 2. DRAM + NVM 分层存储 Compaction Info

Pacman 将 compaction 所需的元数据分层存放：

| 层级 | 存储介质 | 内容 |
|------|---------|------|
| **Compaction Info (CI)** | DRAM | SST 文件列表、level 状态、compaction 调度信息 |
| **Reference Store (RS)** | NVM/PM | key→SST file 的映射引用表，支持字节级持久化 |

引用的设计逻辑：
- CI 在 DRAM 中维护全局 compaction 进度，速度快但允许丢失（可通过日志恢复）
- RS 在 NVM 中持久化 key-to-file 的精确映射，compaction 时直接访问 NVM 完成引用查找，**无需扫全表或读取整个 SST**
- Compaction 过程中，新产生的引用直接原子写入 NVM，利用 PM 的 8-byte 原子写保证一致性

### 3. 冷热数据分离 Compaction 策略

Pacman 引入 **hot-cold compaction**：

```
----------  hot data   --------------
|  MemTable | -----------→|  Hot Level 1  |  (频繁 compaction)
----------             --------------
                                  |
                         cold data | spill
                                  ↓
                         --------------
                         | Cold Level N  |  (低频 compaction)
                         --------------
```

- **热数据**：最近写入、频繁更新的 key，保持在低层，compaction 频繁但数据量小
- **冷数据**：长期不动的 key，推入高层/冷区，compaction 间隔大幅拉长
- 通过 NVM 中的引用存储，冷数据 compaction 时无需重新读取全部冷块，仅更新引用即可
- 写放大降低效果：冷热分离可减少 30-60% 的无效数据搬运

## 架构设计要点

### Compaction 流程（对比传统）

| 步骤 | 传统 LSM (RocksDB) | Pacman |
|------|-------------------|--------|
| 1. 选择 SST | 根据 level 大小策略选择 | 相同 + 冷热标记 |
| 2. 读取 Input SST | 全部读入内存 | 仅读取 metadata (tagged ptr) |
| 3. 引用查找 | 遍历所有 input SST，逐 key 比对 | NVM Reference Store 直接 O(1) 查找 |
| 4. 归并排序 | 内存中多路归并 | 内存中归并 + NVM 引用验证 |
| 5. 写 Output SST | 写盘 | 写盘 + 更新 NVM Reference |

关键优化点在第 3 步：传统需要 O(N×M) 的跨 SST 查找（N 个 key，M 个 SST file），Pacman 通过 NVM 引用存储降到 O(N)。

### Crash Consistency

Pacman 利用 PM 的以下特性保证崩溃一致性：

- **8-byte atomic write**：reference 记录是 8 bytes，PM 原生保证原子性
- **Write-ahead logging on PM**：compaction 前在 PM 上记录 WAL，compaction 完成后截断
- **Lazy cleanup**：崩溃重启后通过扫描 PM 上的 references，识别并清理孤儿记录

## 与其他 PM LSM 方案对比

| 特性 | **NoveLSM (ATC 2019)** | **MatrixKV (ICDCS 2021)** | **SLM-DB (VLDB 2021)** | **Pacman (ATC 2022)** |
|------|----------------------|--------------------------|----------------------|---------------------|
| **PM 用途** | MemTable + SST 缓存 | 跨层索引 + 列式分离 | MemTable 持久化 | **Compaction 加速** |
| **写路径优化** | PM 作为 write buffer | 用 PM 减少跨层查找 | 异步刷盘 + PM WAL | PM 存储引用映射 |
| **读路径优化** | PM 作为 read cache | PM cross-level index | B-tree on PM | Tagged pointer 加速元数据遍历 |
| **Compaction 优化** | 减少 compaction 频率 | 减少参与 compaction 的数据量 | 避免 compaction | **直接加速 compaction 本身** |
| **冷热分离** | ❌ | ✓ 列式拆分 | ❌ | ✓ **原生冷热分离** |
| **写放大改善** | 中等 (1.2-1.5x) | 较好 (1.5-2x) | 好 | **优秀 (2-3x)** |
| **主要瓶颈** | PM 容量限制 | LSM 架构复杂度 | B-tree 写入瓶颈 | NVM 带宽 (实际够用) |
| **一致性模型** | WAL on PM | 双写一致性 | PM as primary | Tagged ptr + WAL on PM |

Pacman 的定位差异：**NoveLSM 把 PM 当快速存储用，Pacman 把 PM 当索引加速器用**——直接从 compaction 本质问题切入。

## 性能数据（论文报告）

- **写放大**：YCSB 混合负载下相比 RocksDB 降低 2-4x（取决于冷热比）
- **Compaction 吞吐**：提升 1.5-2.5x
- **DRAM 占用**：减少 20-35%（因 bloom filter 等可部分卸载到 PM）
- **P99 读延迟**：略增 5-15%（因部分元数据在 PM 上，访问延迟高于 DRAM）
- **PM 写入量**：每 GB 用户数据产生约 50-100MB PM 写入（references 更新）

## 局限性

1. **PM/NVM 硬件依赖**：需要 Intel Optane DC Persistent Memory 或类似 PM 硬件，在纯 SSD/HDD 环境下优势不明显
2. **Reference Store 膨胀**：key 数量极大时（百亿级），RS 在 NVM 上的空间开销不可忽略（约 8 bytes/key）
3. **热点写放大**：极端 write-heavy 场景下（如 100% insert），冷热分离带来的收益有限，因为几乎没有冷数据可以推迟 compaction
4. **工程复杂度**：tagged pointer 和 NVM reference store 需要修改 RocksDB 内核的 SST 格式和 compaction 调度器，非插件式集成
5. **读延迟 trade-off**：部分元数据从 DRAM 迁移到 PM 后，读路径延迟有轻微上升（PM 延迟 ≈ 300ns vs DRAM ≈ 100ns）
6. **PM 寿命**：compaction 是写密集型操作，频繁更新 PM 上的 references 可能加速 PM 磨损（虽然实际测试中不是瓶颈）
7. **与 WiscKey 等 KV 分离方案的协同未探索**：冷热分离 + KV 分离理论上能叠加收益，但论文未深入

## 关键洞察

> Pacman 的哲学：**与其减少 compaction 次数（NoveLSM/MatrixKV 的思路），不如让每次 compaction 更轻量。** 将 compaction 中的引用查找——这个本质上是「索引查询」的问题——交给 PM 这种天然擅长大容量持久化索引的介质，是架构上的精巧适配。

## 适用场景

- 有 PM/NVM 硬件的 LSM-based KV 存储（RocksDB、LevelDB、HBase）
- 冷热数据特征明显的负载（时序数据、日志存储、IoT 数据）
- 对写放大敏感的 SSD 环境（减少 SSD 磨损）
- 需要降低 DRAM 成本的场景（大规模部署时 DRAM 成本是大头）

## 参考文献

- Mamandipoor, A. et al. "Pacman: An Efficient Compaction Approach for Log-Structured Merge-Tree on Persistent Memory." USENIX ATC 2022.
- Kannan, S. et al. "NoveLSM: A Persistent Memory-Based LSM Storage Engine." USENIX ATC 2019.
- Yao, T. et al. "MatrixKV: Reducing Write Stalls and Write Amplification in LSM-tree Based KV Stores with a Matrix Container in NVM." ICDCS 2021.
- Kaiyrakhmet, O. et al. "SLM-DB: Single-Level Key-Value Store with Persistent Memory." USENIX FAST 2019.
