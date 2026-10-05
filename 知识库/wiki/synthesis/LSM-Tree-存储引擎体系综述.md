---
type: synthesis
title: 技术综述：LSM-Tree 存储引擎体系综述
sources:
- '[[知识库/wiki/LSM-Tree]]'
- '[[知识库/wiki/LSM-Tree-写放大]]'
- '[[知识库/wiki/LSM-Tree-合并优化]]'
- '[[知识库/wiki/LSM-Tree-硬件适配]]'
- '[[知识库/wiki/LSM-Tree-自动调参]]'
- '[[知识库/wiki/LSM-Tree-二级索引]]'
- '[[知识库/wiki/LSM-Tree-RUM猜想]]'
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
- '[[知识库/wiki/InfluxDB深度调研]]'
- '[[知识库/wiki/Doris-深度调研]]'
- '[[知识库/wiki/Doris-Compaction-策略]]'
- '[[知识库/wiki/Doris-Segment-v2-存储格式]]'
- '[[知识库/wiki/事务模型深度调研]]'
confidence: 0.8
confidence_rationale: 类型=synthesis; 来源×0; 21天前更新
synced_at: '2026-10-05'
blog_url: https://bryantchang1992.github.io/ai_memory_chang_ai_team/posts/wiki-synthesis-lsm-tree/
blog_source: _posts/2026-06-14-wiki-synthesis-lsm-tree.md
blog_source_commit: f83970fa7e6ad32d626cc6ca3ba7428c90a638a5
blog_body_sha256: e2b10a04ada5e463d7c7a218994a9f41ba8e702f0cc24e920f501f6eeead83fb
---

> 本文是 **Wiki Synthesize（知识库领域提炼）** 首轮综述之一。完整报告见 [[技术文章/博客同步/tech-research-week-05|技术调研周报]] 和 [子调研详情页](https://bryantchang1992.github.io/ai_memory_chang_ai_team/tech_research/wiki_synthesis/week_01_2026-06-14.html)。

---

## 领域定义

**LSM-Tree** (Log-Structured Merge-Tree) 是一种**写优化**的持久化存储结构，通过将随机写转化为顺序写，后台合并维护读性能。它是现代存储系统的基石——RocksDB、LevelDB、HBase、Cassandra、TiKV、Doris Segment 引擎、InfluxDB TSM 引擎都直接或间接基于 LSM-tree 设计。

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

---

## 子主题展开

### 1. 核心架构

LSM-Tree 通过 `MemTable → Immutable MemTable → L0 SSTable → … → L_max` 的层级结构工作：写入先缓冲在内存（MemTable），满了就变为不可变 MemTable 然后刷盘为 SSTable；后台 Compaction 逐层合并 SSTable，维持有序性和查询性能。关键组件包括 **WAL**（写前日志，保证持久性）、**Bloom Filter**（加速点查，避免全 SSTable 遍历）、**SSTable**（不可变数据文件）。

### 2. 核心瓶颈——写放大

写放大是 LSM-tree 最核心的性能瓶颈：写入 1 字节数据，因为 Compaction 过程中数据被反复读写，实际 I/O 量可能是写入量的几十甚至上百倍。Leveling 策略下写放大 WA = O(T·L/B)，Tiering 下 WA = O(L/B)。三类降 WA 方案：

- **Tiering 及其变体**：低写放大但高空间放大，典型代表如 RocksDB 的 Universal Compaction
- **Merge Skipping**：跳过某些层的合并，减少中间 I/O
- **数据倾斜利用（TRIAD）**：热点数据减少合并、冷数据降低频率

### 3. 节奏控制——合并优化

合并是 LSM-tree 的心脏，三大优化方向：

- **合并性能**：VT-tree Stitching（指针拼接避免数据复制）、流水线合并（并发化 Compaction 各阶段）
- **缓冲区管理**：LSbM-tree 利用 OS buffer cache 延迟删除旧版本，减少点查延迟
- **写入停顿**：bLSM Spring-and-Gear 调度器是唯一系统性解决写入停顿的工作。按写入负载切换"弹簧模式"和"齿轮模式"，在持久化写和 Compaction 之间动态分配 I/O 带宽

### 4. 环境适配——硬件演进

随着硬件演进，LSM-tree 需要针对性适配：

- **大内存**：Accordion 多级内存架构，利用 DRAM 级别减少磁盘 I/O
- **多核**：cLSM 并发 Compaction，充分利用多核 CPU
- **KV 分离（WiscKey / HashKV）**：将 value 从 merge 循环中剥离，写放大极低但范围查询显著退化。这一方案的合理性取决于硬件——SSD 的随机读足够快时才可行
- **NVM**：NoveLSM 利用持久化内存降低延迟

### 5. 自适应控制——自动调参

手工调参脆弱且无法适应负载变化。三大方向：

- **参数调优**：Monkey 非均匀 Bloom Filter 分配（无损优化点查，通过数学分析找到最优 BF 位分配），Dostoevsky Lazy-Leveling（低层 tiering + 最底层 leveling 混合策略，在写放大和空间放大间提供连续谱系）
- **BF 动态调整**：ElasticBF 按 SSTable 热度激活/停用子 Bloom Filter
- **数据放置**：Mutant 云存储分层放置策略

### 6. 从 KV 到数据库——二级索引

LSM-tree 从 KV-store 走向完整数据库引擎，二级索引是核心挑战。Diff-Index 将维护策略按开销从高到低分为 sync-full / sync-insert / async-simple / async-session。关键在读写比——高写负载用 async 策略牺牲一点查询延迟换取写入吞吐。

---

## 五个跨领域洞察

### Insight 1：写放大是所有优化的最终判据

RUM 猜想定义了 Read-Update-Memory 的不可能三角——无法同时优化读、写、空间三者。LSM-tree 生态的几乎所有优化都是在 RUM 三角中寻找新的 Pareto 前沿。"无损改进"（如 Monkey 的非均匀 BF 分配）极其稀缺，绝大多数优化都是 trade-off 重分配。

### Insight 2：Dostoevsky 打破了"同质化合并策略"的假设

传统认知是 LSM-tree 所有层级统一使用 leveling 或 tiering 合并策略。Dostoevsky (2018) 证明**混合同质策略未必最优**——低层用 tiering 省写放大、最底层用 leveling 省空间，在两者间提供连续的最优谱系。这是一个被长期忽视的架构洞察。

### Insight 3：存储引擎的"最优设计"是硬件假设的函数

LSM 最初为 HDD 设计，硬件假设（顺序写快、随机 I/O 慢）已随 SSD/NVM 改变。WiscKey 证明当随机读足够快时，KV 分离可以大幅降低写放大。这意味着**没有永恒的"最优"存储引擎，只有"当前硬件下"的最优设计**。

### Insight 4：写入停顿——最大的工程盲区

bLSM (2012) 之后近十年，写入停顿的端到端延迟方差无人系统性解决。所有生产系统（RocksDB/HBase/Cassandra）实际受此困扰，但学术界和工程界对延迟 SLO 保证缺乏形式化分析。

### Insight 5：LSM-tree 是现代存储引擎的"通用语言"

LSM-tree 的影响远超自身：InfluxDB TSM 引擎是时序场景的 LSM 变体，Doris Compaction 策略全面借鉴 LSM 思想，Kafka 的 Log Compaction 也有 LSM 的影子。**理解 LSM-tree 是理解现代存储引擎的入口**。

---

## 与外部知识领域的交叉

| 交叉领域 | 说明 |
|----------|------|
| 时序数据库 | InfluxDB TSM 引擎是 LSM 在时序场景的改造 |
| OLAP 数据库 | Doris MoW DELETE_BITMAP 借鉴 LSM 标记删除 |
| 事务系统 | MVCC 多版本快照与 LSM 共享机制 |
| 存算分离 | LSM Compaction 的写放大在存算分离架构下更严重 |

---

## 待探索方向

1. **CXL 共享内存下的 LSM 架构重构**
2. **存算分离下 Compaction 的 I/O 范式转变**
3. **AI 驱动的在线自动调参（Learned Index / ML for DB）**

---

*综合自 Luo & Carey, "LSM-based Storage Techniques: A Survey", VLDB Journal 2019 · 2026-06-14 完成提炼*
