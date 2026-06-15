---
type: synthesis
title: "LSM-Tree 存储引擎体系综述"
sources:
  - "[[LSM-Tree]]"
  - "[[LSM-Tree-写放大]]"
  - "[[LSM-Tree-合并优化]]"
  - "[[LSM-Tree-硬件适配]]"
  - "[[LSM-Tree-自动调参]]"
  - "[[LSM-Tree-二级索引]]"
  - "[[LSM-Tree-RUM猜想]]"
tags:
  - 存储引擎
  - LSM-Tree
  - 综述
  - 数据库
  - 写优化
created: 2026-06-14
updated: 2026-06-15
status: draft
related:
  - "[[InfluxDB深度调研]]"
  - "[[Doris-深度调研]]"
  - "[[Doris-Compaction-策略]]"
  - "[[Doris-Segment-v2-存储格式]]"
  - "[[事务模型深度调研]]"
---

# LSM-Tree 存储引擎体系综述

> 本综述基于 VLDB Journal 2019 Survey 形成的 7 张 wiki 卡片，以 RUM 猜想为统一理论框架，串联 LSM-tree 的写放大、合并优化、硬件适配、自动调参、二级索引等子领域。

---

## 领域定义

**LSM-Tree** (Log-Structured Merge-Tree) 是一种**写优化**的持久化存储结构，通过将随机写转化为顺序写，后台合并维护读性能。它是现代存储系统（RocksDB、LevelDB、HBase、Cassandra、Doris TSM、InfluxDB TSM）的基础引擎设计范式。

---

## 概念关系图

```
                        ┌─────────────────────────────────┐
                        │     RUM 猜想 (理论框架)          │
                        │  Read-Update-Memory Trade-off   │
                        └──────────────┬──────────────────┘
                                       │ 约束所有优化空间
           ┌───────────────────────────┼───────────────────────────┐
           │                           │                           │
           ▼                           ▼                           ▼
   ┌───────────────┐          ┌───────────────┐          ┌───────────────┐
   │   写放大       │          │   合并优化     │          │   硬件适配     │
   │  (瓶颈中心)    │◄────────►│  (节奏控制)    │◄────────►│  (环境适配)    │
   └───────┬───────┘          └───────┬───────┘          └───────┬───────┘
           │                          │                          │
           │  Leveling vs Tiering     │  LSbM / bLSM             │  WiscKey / HashKV
           │  Merge Skipping          │  流水线合并              │  NoveLSM / cLSM
           │  TRIAD                   │  写入停顿                │  LDS / LOCS
           │                          │                          │
           └──────────────────────────┼──────────────────────────┘
                                      │ 统一调参入口
                                      ▼
                           ┌───────────────────────┐
                           │     自动调参          │
                           │  Monkey / Dostoevsky  │
                           │  ElasticBF / Mutant   │
                           └───────────┬───────────┘
                                       │ 从 KV 走向数据库
                                       ▼
                           ┌───────────────────────┐
                           │     二级索引          │
                           │  走向完整数据库引擎    │
                           │  Diff-Index / LSII    │
                           └───────────────────────┘
```

**关系说明**：RUM 猜想是理论顶层——写放大、合并、硬件适配三者互相关联，自动调参在三者之上提供自适应控制，二级索引在所有基础上使 LSM-tree 从 KV-store 走向完整数据库引擎。

---

## 子主题展开

### 1. 核心架构 — [[LSM-Tree]]

LSM-Tree 通过 MemTable → Immutable MemTable → L0 SSTable → … → L_max 的层级结构，将写入缓冲在内存、以顺序写方式刷盘，后台 Compaction 逐层合并。关键组件包括 WAL（持久化）、Bloom Filter（加速点查）、SSTable（不可变数据文件）。

### 2. 核心瓶颈 — [[LSM-Tree-写放大]]

写放大是 LSM-tree 最核心的性能瓶颈，源自 Compaction 过程中数据被反复读写。Leveling 策略下 WA = O(T·L/B)，Tiering 下 WA = O(L/B)。三类降 WA 方案：Tiering 及其变体（低写放大但高空间放大）、Merge Skipping、数据倾斜利用（TRIAD）。

### 3. 节奏控制 — [[LSM-Tree-合并优化]]

合并是 LSM-tree 的心脏。三大优化方向：
- **合并性能**：VT-tree Stitching（指针拼接）和流水线合并
- **缓冲区管理**：LSbM-tree 延迟删除，利用 OS buffer cache
- **写入停顿**：bLSM Spring-and-Gear 调度器，唯一系统性地解决写入停顿的工作（但远不完善）

### 4. 环境适配 — [[LSM-Tree-硬件适配]]

随着硬件演进（大内存、多核、SSD/NVM、云存储），LSM-tree 需要针对性适配：
- **大内存**：Accordion 多级内存，减少磁盘 I/O
- **多核**：cLSM 并发 Compaction
- **KV 分离**：WiscKey / HashKV 将 value 从 merge 中剥离，写放大极低但范围查询显著退化
- **NVM**：NoveLSM 利用持久化内存降低延迟

### 5. 自适应控制 — [[LSM-Tree-自动调参]]

手工调参脆弱且无法适应负载变化。三大方向：
- **参数调优**：Monkey 非均匀 Bloom Filter 分配（无损优化点查）、Dostoevsky Lazy-Leveling（低层 tiering + 最底层 leveling 混合策略）
- **BF 动态调整**：ElasticBF 按 SSTable 热度激活/停用子 BF
- **数据放置**：Mutant 云存储分层

### 6. 从 KV 到数据库 — [[LSM-Tree-二级索引]]

LSM-tree 从 KV-store 走向完整数据库存储引擎，二级索引是核心挑战。Diff-Index 将维护策略按开销从高到低分为 sync-full / sync-insert / async-simple / async-session。关键在于根据读写比选择维护开销与查询延迟的平衡点。

---

## 跨页连接的 Insight

### Insight 1：写放大是所有优化的最终判据

RUM 猜想定义了 Read-Update-Memory 的不可能三角，而 LSM-tree 生态的几乎所有优化（Tiering、KV 分离、Lazy-Leveling）都是在这个三角中寻找新的 Pareto 前沿。"无损改进"（如 Monkey、数据冗余利用）极其稀缺。

### Insight 2：Dostoevsky 打破了对同质化合并策略的假设

传统认知是"所有层统一策略"（全部 leveling 或全部 tiering），Dostoevsky 证明**同质化合并策略未必最优**——低层用 tiering 省写放大、最底层用 leveling 省空间/提查询，在两者之间提供连续谱系。

### Insight 3：LSM-tree 的硬件适配与时代强耦合

LSM 最初为 HDD 设计，硬件假设（顺序写快、随机 I/O 慢）已随 SSD/NVM 改变。WiscKey 证明当随机读足够快时，KV 分离可以大幅降低写放大。这启示我们：**存储引擎的"最优设计"是硬件假设的函数**。

### Insight 4：写入停顿是最大的工程盲区

bLSM (2012) 之后近十年，写入停顿问题几乎无系统性研究。所有生产系统（RocksDB、HBase）实际受此困扰，但学术界和工程界对端到端延迟方差缺乏关注。Store-and-forward 模型 vs I/O-bound 模型的差异需要更形式化的分析。

### Insight 5：LSM-tree 是存储引擎的"通用语言"

LSM-tree 的影响远超自身——InfluxDB TSM 引擎是其时序衍生，Doris Compaction 策略借鉴其思想，Kafka 的 log compaction 也有 LSM 的影子。理解 LSM-tree 是理解现代存储引擎的入口。

具体而言：
- **[[Doris-Compaction-策略]]** 的 Cumulative/Base/Quick Compaction 三级体系直接继承了 LSM 的层级合并理念，DELETE_BITMAP 标记删除机制与 LSM 的墓碑标记同源
- **[[Doris-Segment-v2-存储格式]]** 的 Page 体系（DataPage / IndexPage / BloomFilterPage）与 LSM SSTable 的 block-level 索引结构高度对称——都是通过分层索引 + Bloom Filter 加速随机访问
- 两者的差异在于 LSM 强调写路径优化（顺序写 + 后台合并），Doris 强调读路径优化（列式布局 + 谓词下推），但这正是 RUM 猜想在 OLAP 场景下的投影

---

## 与外部知识领域的交叉

| 交叉领域 | 关联页面 | 说明 |
|----------|---------|------|
| 时序数据库 | [[InfluxDB-TSM存储引擎]] | TSM 引擎是 LSM 在时序场景的改造 |
| OLAP 数据库 | [[Doris-Compaction-策略]]、[[Doris-Segment-v2-存储格式]]、[[Doris-数据模型]] | Doris Cumu/Base/Quick 三级 Compaction 继承 LSM 层级合并；Segment Page 体系与 LSM block 索引对称 |
| 事务系统 | [[事务模型深度调研]] | MVCC 与 LSM 多版本快照共享机制 |
| 存算分离 | [[存储计算分离数据库的-Tail-Latency]] | LSM Compaction 的写放大在存算分离下更严重 |

---

## 待探索方向

1. **Monkey × Dostoevsky 联合优化**：同时优化 Bloom Filter 分配和 merge policy，寻找联合最优解
2. **写入停顿系统性解决**：bLSM 之后十年，端到端延迟方差仍是盲区，需要端到端的延迟保证模型
3. **CXL 内存的 LSM 适配**：CXL 共享内存提供新的硬件假设，LSM 架构如何重构？
4. **存算分离下的 Compaction**：当数据在对象存储（S3）上时，Compaction 的 I/O 模式和写放大特征完全改变——这是 [[InfluxDB-3-列存引擎]] 已经面对的问题
5. **列存 LSM 的融合设计**：[[Doris-Segment-v2-存储格式]] 的 Page 体系与 LSM SSTable block 结构在索引层级上高度对称，是否存在一个统一的"列存 LSM"抽象？这可能是 OLAP 存储引擎的下一个理论突破点
6. **二级索引的 Compaction 同步**：多索引一致性是 LSM 走向数据库的关键瓶颈，异步维护 vs 同步维护的决策框架需要更系统的量化分析
7. **AI 驱动的自动调参**：LLM/ML 能否在线学习负载模式、自动选择最优参数组合？当前自动调参仍以离线分析为主

---

*综合自 Luo & Carey, "LSM-based Storage Techniques: A Survey", VLDB Journal 2019 形成的 7 张 wiki 卡片，2026-06-14 完成提炼。*

---

## 变更记录

| 日期 | 动作 | 变更说明 |
|------|------|----------|
| 2026-06-14 | 创建 | 初始版本，覆盖 LSM-Tree 7 张概念卡片 |
| 2026-06-15 | 增量更新 | 新增 Doris Compaction + Segment v2 连接；扩展 Insight 5（列存 LSM 融合）；related 增加 2 张页面；新增待探索方向 #5（列存 LSM 融合设计） |
