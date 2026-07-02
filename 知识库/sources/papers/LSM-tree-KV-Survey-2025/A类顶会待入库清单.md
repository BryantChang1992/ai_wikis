# Top 10 CCF-A 核心论文选入清单

> LSM-tree KV Survey 参考文献筛选，排除已有卡片覆盖的（Monkey/Dostoevsky/TRIAD/NoveLSM/ElasticBF）和工业系统描述类。

| # | Ref | 论文 | 会议 | 年 | 入选理由 |
|---|-----|------|------|-----|---------|
| 1 | [91] | **PebblesDB**: Fragmented LSM Trees | SOSP | 2017 | SOSP — 碎片化 Level 的里程碑，用 Guard 概念约束 SSTable key range 重叠，避免全量 merge |
| 2 | [94] | **Lethe**: A Tunable Delete-Aware LSM Engine | SIGMOD | 2020 | 唯一针对隐私删除的 LSM 引擎，tombstone 传播 + 阈值驱动强制 compaction |
| 3 | [32] | **Bourbon**: A Learned Index for LSM Trees | OSDI | 2020 | OSDI — ML 加速 LSM 查询的开创性工作，learned index + KV 分离 |
| 4 | [18] | **Hailstorm**: Disaggregated Compute/Storage | ASPLOS | 2020 | ASPLOS — 存算分离 LSM KV 的首批系统，compaction offload + 负载均衡无需 resharding |
| 5 | [50] | **Nova-LSM**: Distributed Component-based LSM | SIGMOD | 2021 | RDMA 存算分离 + 共享存储池，动态 compaction 调度 |
| 6 | [72] | **ElasticBF**: Elastic Bloom Filter | ATC | 2019 | 已有卡片提及但浅，应独立成卡：数据访问热度驱动的细粒度异构 BF |
| 7 | [114] | **Pacman**: Efficient Compaction on PM | ATC | 2022 | 持久内存 Compaction 加速的代表：tagged pointer + 元数据 DRAM 化 + 冷热分离 |
| 8 | [140] | **CaaS-LSM**: Compaction-as-a-Service | SIGMOD | 2024 | 最新 Compaction 架构范式：将 compaction 解耦为无状态 FaaS 服务 |
| 9 | [151] | **REMIX**: Efficient Range Query | FAST | 2021 | 全局排序索引的标准方案，跨 SSTable 构建内存中的全局二分查找结构 |
| 10 | [101] | **gLSM**: GPU Accelerated Compactions | ToS | 2024 | GPU 加速 Compaction 的代表，利用 GPU 大规模并行性处理归并排序 |

## Top 10 方向覆盖

| 方向 | 代表论文 | 篇数 |
|------|---------|------|
| Compaction 策略/架构 | PebblesDB (SOSP) | 1 |
| 隐私/删除语义 | Lethe (SIGMOD) | 1 |
| ML + Learned Index | Bourbon (OSDI) | 1 |
| 存算分离/分布式 | Hailstorm (ASPLOS) + Nova-LSM (SIGMOD) | 2 |
| Bloom Filter 优化 | ElasticBF (ATC) | 1 |
| 持久内存 | Pacman (ATC) | 1 |
| Compaction 新范式 | CaaS-LSM (SIGMOD) | 1 |
| 范围查询优化 | REMIX (FAST) | 1 |
| 硬件加速 | gLSM (ToS) | 1 |

## 第二梯队备选（如果有多余精力）

| Ref | 论文 | 会议 | 年 | 主题 |
|-----|------|------|-----|------|
| [16] | SILK: Preventing Latency Spikes | ATC | 2019 | 动态带宽分配 |
| [139] | ADOC: Harmonizing Dataflow | FAST | 2023 | 自适应调参 |
| [150] | Disco: Compact Index for LSM | SIGMOD | 2025 | 全索引查询加速 |
| [112] | GRF: Global Range Filter | SIGMOD | 2024 | 范围过滤 |
| [147] | ChameleonDB for Optane PM | EuroSys | 2021 | PM 混合架构 |
| [65] | WALTZ: Zone Append for ZNS SSD | VLDB | 2023 | ZNS 适配 |
| [90] | PrismDB: Compactions Between Tiers | ASPLOS | 2023 | 多存储层 |
| [143] | DEPART: Replica Decoupling | FAST | 2022 | 副本解耦 |
