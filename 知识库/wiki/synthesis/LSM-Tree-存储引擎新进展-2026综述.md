---
type: synthesis
tags:
  - synthesis
  - LSM-Tree
  - Compaction
  - storage-engines
  - scheduling
  - distributed-storage
related:
  - "[[Silo-分布式LSM-Compaction调度]]"
  - "[[Silo-Compaction-迁移协议]]"
  - "[[LSM-Tree]]"
  - "[[LSM-Tree-写放大]]"
  - "[[LSM-Tree-合并优化]]"
  - "[[LSM-Tree-自动调参]]"
  - "[[LSM-Tree-RUM猜想]]"
  - "[[LSM-Tree-硬件适配]]"
  - "[[LSM-Tree-二级索引]]"
  - "[[Fluss-KV存储-RocksDB]]"
  - "[[Fluss-存储引擎]]"
created: 2026-06-15
---

# LSM-Tree 存储引擎新进展：从单机到分布式 Compaction

> 基于 Silo (FAST 2026) 的分布式 LSM compaction 调度 + Fluss 的 RocksDB 存储引擎实践，综合 10 张 LSM-Tree wiki 卡片。

## 一、LSM-Tree 为什么需要新突破？

LSM-Tree 是写入优化存储引擎的事实标准——RocksDB、LevelDB、Apache Cassandra、HBase、TiKV 都建立在它的基础之上。Fluss 也选用 RocksDB 作为本地存储引擎。

但 LSM 有一个系统性问题：**写放大（Write Amplification, WA）和空间放大（Space Amplification, SA）之间的 tradeoff**——这是 LSM-Tree 的 RUM 猜想的物理极限——Read amplification、Update amplification、Memory amplification 三者不可同时最优。

过去 15 年，学术界和工业界的优化主要围绕：
- **Compaction 策略**：Leveled vs Tiered vs Hybrid (SILK, Dostoevsky, RocksDB 的动态选择)
- **索引结构**：Bloom filter, partition index, data block index
- **自动调参**：Monkey, RocksDB autotuner

但这些优化有一个共同假设：**compaction 调度是每个节点独立进行的，不跨节点协调**。

Silo (FAST 2026) 改变了这个假设。

---

## 二、Silo：分布式 LSM Compaction 的全局调度

### 核心问题

在分布式 KV 存储里（如 TiKV、HBase、Cassandra），每个节点独立决定自己的 compaction 时机和策略。这导致：

1. **负载倾斜**：热点 Range 的 compaction 可能同时触发多个 SST files 的 merge → 瞬时 I/O 打满 → 前台请求受影响
2. **冗余 compaction**：相邻 Range 可能互相 compact 大量重叠的数据（特别是 range split/merge 后）
3. **不可预知**：无法在全局层面规划 compaction 窗口和优先级

### Silo 的两阶段方法

**全局调度层**：中心化的 Scheduler 全局监控所有 store 的 compaction 队列深度、I/O 负载、pending SST file count，做出**全局最优**的调度决策——哪些 Range 现在 compact、哪些延后、哪个 store 承接 compaction 负载。

**本地执行层**：每个 store 执行分配到的 compaction 任务。Silo 对 RocksDB compaction 线程池进行了修改，允许外部注入优先级。

### 关键机制

1. **Anti-hog（反霸占）**：防止某个热点 Range 的 compaction 霸占全部 I/O 带宽。调度器限制每个 Range 同时 active compaction 的数量
2. **Pro-hog（优先霸占）**：当检测到某个 Range 的 write stall 风险（L0 文件数接近上限）时，调度器给予该 Range 最高优先级
3. **Compaction 迁移**：如果某个 store 已过载，调度器可以将该 store 的某些 Range 的 compaction 任务**迁移到其他空闲 store 执行**——这是一个根本性的范式变化：compaction 不一定要在数据所在的节点执行

### 迁移协议的挑战

Compaction 迁移需要解决几个关键问题：
- **读取一致性**：被迁移的 compaction 产出的新 SST files 需要以原子方式取代旧 files
- **WAL 协调**：迁移期间的写入需要同步到迁移目标节点
- **网络开销**：大 SST files 跨节点传输的成本

Silo 的 Anti-hog + Pro-hog 策略使得迁移协议是**按需触发**的（只有在过载时才迁移），而非缺省启用的——避免了不必要的网络开销。

---

## 三、Fluss 的 LSM 实践

Fluss 对 RocksDB 的使用是"教科书式"的 LSM 应用，但有两个值得关注的实践：

**Tiering 与 LSM compaction 的协同**：
- 热数据在 RocksDB 的各级 SST files 中
- 当 SST files 到达最深层级（bottommost level），且数据时间戳超过 TTL，直接迁移到 Iceberg Lake Storage——**compaction 和 tiering 合并为一个流程**
- 效果：warm/cold tier 的 LSM compaction 开销几乎为零——数据直接出 LSM 树，进入列式湖仓

**Arrow columnar format 的副产品**：
- Fluss 在 RocksDB 的 value 中存储 Arrow RecordBatch
- 当 compaction merge 多个 SST files 时，Arrow 的列式格式允许**列级合并**（而非行级）→ compaction I/O 减少
- 读路径上的投影裁剪：如果 Flink 只需要 2 列，Fluss 可以从 Arrow 格式中只读取这 2 列——减少了 LSM 的 read amplification

---

## 四、LSM-Tree 的技术路线图

```
LSM-Tree 单机优化 (2010-2020)
  ├── Leveled vs Tiered compaction
  ├── Bloom filter + partition index
  ├── Automatic tuning (Monkey, Dostoevsky)
  └── Hardware adaptation (PMem, ZNS SSD)

LSM-Tree 分布式调度 (2026+)
  └── Silo: Global compaction scheduling + task migration

LSM-Tree 湖仓融合 (2026+)
  └── Fluss: Compaction → tiering → Iceberg lakehouse
```

三个方向不是互斥的——可以组合：
- **Silo 的全局调度** + **Fluss 的 tiering** = 全局最优的 compaction + 冷数据零 compaction 成本
- **Silo 的迁移协议** + **多租户 RocksDB** = 跨租户的 compaction 负载均衡

---

## 五、知识库 LSM 卡片体系

| 卡片 | 层级 | 主题 |
|------|------|------|
| [[LSM-Tree]] | 概念 | LSM-Tree 基础理论 |
| [[LSM-Tree-写放大]] | 概念 | WA / SA / RA tradeoff |
| [[LSM-Tree-合并优化]] | 概念 | Leveled vs Tiered compaction |
| [[LSM-Tree-自动调参]] | 概念 | Monkey, autotuner |
| [[LSM-Tree-硬件适配]] | 概念 | PMem, ZNS SSD, SMR |
| [[LSM-Tree-二级索引]] | 概念 | Secondary index on LSM |
| [[Silo-分布式LSM-Compaction调度]] | 概念 | 全局 compaction 调度（新） |
| [[Silo-Compaction-迁移协议]] | 概念 | Compaction 跨节点迁移（新） |
| [[Fluss-KV存储-RocksDB]] | 概念 | Fluss 中 RocksDB 的应用（新） |
| [[Fluss-存储引擎]] | 概念 | Fluss 存储层总览（新） |

---

*合成日期：2026-06-15 | 基于 Silo (FAST 2026) + Fluss 源码分析 + 既有 LSM 知识卡片体系*
