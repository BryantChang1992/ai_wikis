---
type: concept
title: 'Bourbon: LSM-Tree 学习索引'
sources:
- https://www.usenix.org/conference/osdi20/presentation/dai
- https://arxiv.org/abs/2005.14213
- '[[知识库/sources/papers/LSM-tree-KV-Survey-2025/精读分析]]'
tags:
- 存储引擎
- LSM-Tree
- 学习索引
- Learned Index
- 点查优化
- WiscKey
- OSDI 2020
created: 2026-07-02
updated: 2026-07-02
status: draft
related:
- '[[知识库/wiki/LSM-Tree]]'
- '[[知识库/wiki/LSM-Tree-自动调参]]'
- '[[知识库/wiki/LSM-tree-KV-Survey-综述]]'
- '[[知识库/wiki/LSM-Tree-合并优化]]'
confidence: 0.8
confidence_rationale: 类型=concept; 来源×1; 4天前更新
synced_at: '2026-10-05'
blog_url: https://bryantchang1992.github.io/ai_memory_chang_ai_team/knowledge/Bourbon-Learned-Index-LSM/
blog_source: _posts/2026-07-02-knowledge-644c614109.md
---

# Bourbon: LSM-Tree 学习索引

> **论文**: Yifan Dai, Yien Xu, Aishwarya Ganesan, Ramnatthan Alagappan, Brian Kroth, Andrea Arpaci-Dusseau, Remzi Arpaci-Dusseau. *From WiscKey to Bourbon: A Learned Index for Log-Structured Merge Trees*. OSDI 2020, pp. 155–171.

## 一句话摘要

Bourbon 是将 **Learned Index（学习索引）** 引入 LSM-tree 的首个系统——基于 WiscKey 的 KV 分离架构，用 Greedy PLR（分段线性回归）模型预测 key 在 SSTable 文件内的偏移量，替代传统二分查找索引，并通过 Cost-Benefit Analyzer 动态决定是否学习某个文件，实现 1.23x-1.78x 的点查加速。

---

## 核心创新点

### 1. Learned Index 替代传统索引结构做点查加速

传统 LSM-tree 点查路径（以 WiscKey/LevelDB 为例）包含多个索引步骤：

```
FindFiles → LoadIB+FB → SearchIB(二分查找) → SearchFB(Bloom Filter) → ReadValue
```

Bourbon 的核心思路：用 PLR 模型预测 key 对应的 SSTable 内偏移量，将 O(log n) 的二分查找降为 O(log s)（s 为线段数，s << n）：

```
FindFiles → LoadIB+FB → Model Lookup(PLR 预测偏移) → SearchFB → LoadChunk → LocateKey → ReadValue
```

**加速的本质**：索引步骤（FindFiles + SearchIB + SearchDB）在总延迟中占比随存储设备提速而上升——在内存缓存场景下占 ~50%，在 Optane SSD 上占 ~44%。Bourbon 针对性地压缩了这一部分开销。

### 2. 从 WiscKey 继承 KV 分离架构

Bourbon 直接基于 WiscKey（~20K 行代码，Bourbon 新增 ~5K 行），继承了其 KV 分离设计：

```
LSM-tree 只存 (key, value_pointer) → Value Log 存实际 value
```

KV 分离对学习索引至关重要——key 和 pointer 大小固定，PLR 模型只需预测记录在 SSTable 中的偏移，乘以固定记录大小即可得到精确字节偏移。若 value 内联存储（经典 LSM），value 大小可变将使偏移预测极其困难。

### 3. Cost-Benefit Analyzer（开销-收益分析器）

并非所有 SSTable 文件都值得学习。Bourbon 引入了动态决策机制：

| 组件 | 设计 |
|------|------|
| **等待策略 (Wait Before Learning)** | 新文件创建后等待 T_wait=50ms（保守设置，覆盖最慢的模型构建时间），过滤掉寿命极短的临时文件 |
| **开销估算 C_model** | 假设学习线程干扰前台任务，C_model = T_build（构建 PLR 的时间，与数据点数量呈线性关系） |
| **收益估算 B_model** | B_model = (T_baseline - T_model) × N_lookups，其中 N 分 negative/positive 两类分别统计，基于**同层级其他文件的历史数据**进行估算 |
| **调度策略** | 所有待学习文件按 B_model - C_model 排序放入**最大优先级队列**，收益最高的优先学习 |

三种策略对比（实验）：

| 策略 | 前台查询加速 | 学习开销 | 综合效果 |
|------|------------|---------|---------|
| **offline**（永不重学） | 差，写后查询迅速退化到基线路径 | 0 | 1% 写比例就失效 |
| **always**（总是学习） | 最好 | 巨大（50% 写比例时学习时间 134s） | 写多时总开销反超基线 |
| **cba**（开销-收益分析） | 接近 always | 可控（50% 写时仅 13.9s） | **最优综合效果** |

---

## 架构设计要点

### 五条设计准则（从 WiscKey 实验推导）

Bourbon 的设计并非凭空而来，而是通过对 WiscKey 的深入实验分析总结了五条 guidelines：

1. **Favor learning files at lower levels**：低层 SSTable 寿命远长于高层（L4 均值 >> L1 均值），模型复用时间长
2. **Wait before learning a file**：即使是低层也有 ~2% 的文件寿命 < 1s（因级联 compaction），等待阈值可过滤掉它们
3. **Do not neglect files at higher levels**：高层文件处理大量 negative lookup（即便 Bloom Filter 拦截后仍需查 index block），学习索引依然受益
4. **Be workload- and data-aware**：数据加载顺序（顺序 vs 随机）、访问分布（uniform vs zipfian）深刻影响各层查到的查询量分布
5. **Do not learn levels for write-heavy workloads**：层级学习的平稳窗口在 50% 写比例下仅 ~25s，频繁重学抵消收益

### File Learning vs Level Learning

| 粒度 | 寿命特点 | 适用场景 | Bourbon 选择 |
|------|---------|---------|-------------|
| **File Learning** | 文件一旦创建不可变，寿命较长 | 所有混合读写负载 | ✅ 默认选择 |
| **Level Learning** | 任何新文件创建或旧文件删除都导致重学，寿命 ≤ 单个文件 | 仅只读负载（此时比 file 快 ~10%） | 静态配置，不支持运行时切换 |

### Greedy-PLR 模型

选择 PLR 而非神经网络/RMI 的理由：

| 要求 | PLR 满足情况 |
|------|------------|
| 训练速度快 | O(n) 线性时间（Greedy-PLR 单次扫描） |
| 推理速度快 | O(log s) 二分查找线段 + O(1) 计算偏移 |
| 空间开销小 | 每段几十字节，总计为数据集的 0%~2% |
| 支持误差边界 | 用户可配置 δ，δ=8 为实验最优值 |

## 与传统 Bloom Filter 方案的对比

Bourbon 和 Bloom Filter 优化的是 LSM-tree 点查路径上的**不同步骤**，两者是**互补而非替代**关系：

| 维度 | Bloom Filter（如 Monkey） | Bourbon Learned Index |
|------|--------------------------|----------------------|
| **优化目标** | 减少不必要的数据块 I/O（false positive → 零结果查询不必读 block） | 加速索引步骤（FindFiles → SearchIB → SearchDB） |
| **查询路径位置** | SearchFB 步骤 | 替代 SearchIB（二分查找 index block） |
| **适用条件** | 数据在慢速存储设备上，I/O 是瓶颈 | 数据在内存/快速存储上，CPU 索引遍历是瓶颈 |
| **存储设备影响** | 设备越慢收益越大 | 设备越快收益越大（Optane SSD > SATA SSD） |
| **内存限制** | 受益明显（减少 I/O） | 内存仅 25% 数据量 + SATA SSD 时仅 1.04x 加速（数据访问主导延迟） |
| **组合使用** | Bourbon 仍保留 Bloom Filter（SearchFB 步骤不变） | ✅ 两者在同一查询路径中共存 |

**核心洞察**：Bourbon 的论文实验展示了一个重要趋势——随着存储硬件从 SATA SSD → NVMe SSD → Optane SSD 进化，**索引步骤（CPU 开销）在总延迟中的占比从 ~20% 上升到 ~44%**。这意味着未来存储越快，学习索引的价值越大，与 Bloom Filter 形成时间维度上的互补。

---

## 实验亮点

### 测试环境
- 20-core Intel Xeon E5-2660, 160 GB RAM, 480 GB SATA SSD
- 16B integer keys, 64B values, δ=8（误差边界）
- 64M KV pairs（合成数据集）+ Amazon Reviews / NYC OpenStreetMaps（真实数据集）

### 关键结果
- 内存缓存：索引时间减少 + 加载字节范围缩小（PLR 精确定位），综合加速 **1.5x-1.78x**
- Zipfian 负载 + 25% 缓存：加速 **1.25x**（热点数据索引开销仍主导）
- 范围查询：短范围（<10 keys）加速明显，长范围退化为接近基线（索引开销占比下降）
- 混合读写：BOURBON-cba 在学习开销仅 13.9s（vs always 的 134s）的同时，保持接近 always 的前台性能
- Learned Index 模型额外空间开销仅为数据集大小的 **0%~2%**

---

## 局限性

1. **仅支持定长 key**：不直接支持字符串 key，作者建议将字符串视为 base-64 整数转换，但大 key（>64-bit）需高效大整数运算，未实现
2. **Level/File 学习不支持运行时切换**：目前只能静态配置，无法根据负载动态切换粒度
3. **慢存储 + 小内存场景收益有限**：SATA SSD + 25% 缓存下仅 1.04x，数据访问主导延迟时学习索引无法发挥优势
4. **写密集型负载收益递减**：写比例升高 → 文件寿命缩短 + 查询次数减少 → 学习收益下降 + 学习开销占比上升
5. **范围查询大区间时效果递减**：PLR 优化的是首 key 定位（索引步骤），后续 key 的顺序扫描与基线相同
6. **模型选择单一**：仅评估了 Greedy-PLR，未对比 RMI、PGM-Index、splines 等替代模型，论文承认未来可采用更优模型
7. **未讨论 WiscKey 自身的局限性**：继承了 KV 分离后 Value Log 的 GC 问题、崩溃一致性复杂度

---

## 在 LSM-tree 优化谱系中的位置

```
LSM 点查优化路线图：

  bLSM (SIGMOD'12)       → 首次用 Bloom Filter 优化点查
  Monkey (SIGMOD'17)      → BF bits 非均匀分配，理论最优
  ElasticBF (ATC'19)      → 动态异构 BF，按热度激活
  Bourbon (OSDI'20)  ★   → Learned Index 替代二分查找索引，CPU 路径加速
  REMIX (FAST'21)         → 全局排序索引，内存中二分查找
  GRF (SIGMOD'24)         → 全局 Range Filter，单次探测替代多次
  Disco (SIGMOD'25)       → 跨所有 run 的全局索引，达到 B+-tree 级查询效率
```

Bourbon 在其中的独特地位：**第一个将 ML 引入 LSM-tree 查询路径的系统**，证明了 SSTable 不可变特性与学习索引天然契合，且存储硬件越快，学习索引价值越大。

---

## 与 [[LSM-tree-KV-Survey-综述]] 的关联

该综述（Lv et al., 2025）将 Bourbon 列为 LSM-tree 点查优化的关键里程碑之一，与 Monkey、ElasticBF 并列。综述指出的趋势——多租户、Serverless、硬件加速 compaction——与 Bourbon 暗示的方向一致：**未来 LSM-tree 控制面的智能化**。Cost-Benefit Analyzer 的决策逻辑可以视为 LSM-tree "自适应控制面"的雏形，与 [[LSM-Tree-自动调参]] 中讨论的在线自适应调参方向直接相关。

---

*论文: Dai et al., "From WiscKey to Bourbon: A Learned Index for Log-Structured Merge Trees", OSDI 2020.*
