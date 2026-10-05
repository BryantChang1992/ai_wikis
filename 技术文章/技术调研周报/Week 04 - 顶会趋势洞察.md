---
title: 存储/数据库顶会趋势洞察 · Week 04
blog_url: https://bryantchang1992.github.io/ai_memory_chang_ai_team/posts/tech-research/week-04/conferences/
blog_source: _posts/2026-06-11-top-conferences-week-04.md
blog_source_commit: f83970fa7e6ad32d626cc6ca3ba7428c90a638a5
blog_body_sha256: b99483c745498774eee4b47192077dc50cc2182cbb6e6b0f56d3181c300de26e
synced_at: '2026-10-05'
type: survey
created: '2026-06-11'
tags:
- 顶会
- 趋势洞察
issue: 4
issue_date: '2026-06-11'
---

> **📌 本期定位：** Week 04 · 2026-06-11 · 四主题深度调研 · 30+ 篇论文 · 全部可免费获取

**覆盖会议：** SIGMOD 2026 (Bangalore, 6月) · FAST 2026 (Santa Clara, 2月) · CIDR 2026 (Chaminade, 1月)

四个主题的条目分布：存储引擎与索引 12 篇、分布式共识 6 篇、工业系统 12 篇、AI Infra 10 篇。

> **📊 执行摘要：**
> - **存储引擎**：LSM-Raft 协同优化、持久化 ART、Bw-Graph 图存储——索引从"适配硬件"走向"原生设计"
> - **分布式共识**：CockroachDB 多组 Leader Lease、LSM-Raft 协同——共识协议与存储引擎深度绑定
> - **工业系统**：Aurora Limitless、ByteHouse、TDSQL、CoddSpeed、Apple ACOS——工业系统论文集中爆发
> - **AI Infra**：KV Cache 存储优化 (3篇FAST)、向量搜索 (3篇SIGMOD)、GPU Checkpoint/训练 I/O (3篇FAST)、Agent-First 数据系统 (1篇CIDR)——2026 存储顶会 P0 方向

---

## 🗄️ 一、存储引擎 & 索引技术

### 📌 SIGMOD 2026

#### ART That Lasts: Persistent Multiversion Adaptive Radix Trees with Fast Atomic Range Queries

Mohammad Khalaji, Trevor Brown, Khuzaima Daudjee — University of Waterloo

**SIGMOD '26** · **动机：** 持久内存（PMem）的商用化使得在持久介质上直接构建索引成为可能，但现有持久化索引要么不支持多版本（MVCC），要么无法高效支持原子范围查询——两者是事务型数据库的刚需。

**创新：** 提出持久化多版本 ART（Adaptive Radix Tree），将 MVCC 可见性信息嵌入索引节点，通过 epoch-based 内存管理实现无锁并发访问，同时支持快速原子范围扫描。为 PMem/NVM 原生数据结构提供了可直接用于生产级 OLTP 引擎的新范式。

📄 [PACMMOD Vol.4 No.3](https://dl.acm.org/toc/pacmmod/2026/4/3) · `持久化索引` `ART`

---

#### Concurrent Path-Copying Update to Tree Structures

Guanhao Hou, Dechuang Chen 等 — CUHK; HKUST

**SIGMOD '26** · **动机：** Path-Copying 是实现持久化树结构的经典技术（写时复制路径上的所有节点），但其在高并发多核场景下因写放大和锁争用严重退化。

**创新：** 提出基于细粒度引用计数和 epoch 回收的并发路径拷贝算法，允许并发写操作共享路径拷贝的中间结果，通过 RCU-like 机制延迟回收旧版本节点，在多核场景下实现接近无锁的吞吐量，同时保证严格持久化语义。

📄 [PACMMOD Vol.4 No.3](https://dl.acm.org/toc/pacmmod/2026/4/3) · `并发索引` `Path-Copying`

---

#### Bw-Graph: An Efficient Graph Storage System Harmonizing Topology-Aware Tree with Paged CSR

Songyao Wang, Chaokun Wang 等 — Tsinghua University

**SIGMOD '26** · **动机：** 图存储系统长期面临"遍历 vs. 随机访问"的两难：CSR 格式在顺序遍历时性能极佳但随机访问极差，而邻接表格式的权衡恰好相反。

**创新：** 提出 Bw-Graph——融合拓扑感知树（Topology-Aware Tree）与分页 CSR 的混合图存储引擎。利用图的社区结构将热点子图映射到树索引，冷数据使用压缩 CSR 分页存储，通过自适应路由在两种格式间透明切换，在遍历和随机访问两类工作负载上均取得接近最优的性能。

📄 [PACMMOD Vol.4 No.3](https://dl.acm.org/toc/pacmmod/2026/4/3) · `图存储` `数据布局`

---

#### Dynamic Flat Filter: A Unified Framework for Scalable Fingerprint-Based Filters

Haoyu Du, Yuchen Ji 等 — 苏州大学

**SIGMOD '26** · **动机：** LSM-Tree 和 KV 存储广泛依赖 Bloom Filter 减少不必要的磁盘 I/O，但传统 Bloom Filter 面临固定假阳性率、内存占用线性增长、删除操作需借助 Counting Bloom Filter 导致空间翻倍。

**创新：** 提出 Dynamic Flat Filter——统一指纹过滤器框架，支持动态调整假阳性率而无需重建；采用 flat 位图布局消除指针开销，空间效率超越 XOR Filter；内置可扩展的删除语义（无需 counting），特别适合 LSM-Tree 的 compaction 场景。

📄 [PACMMOD Vol.4 No.3](https://dl.acm.org/toc/pacmmod/2026/4/3) · `过滤器` `LSM-Tree`

---

#### PartitionKV: Redesigning LSM-tree KV stores on NVMs with Adaptive Partitioning

Xingye Huang 等 — Xidian University; NWPU

**SIGMOD '26** · **动机：** 新型非易失性内存（NVM，如 Intel Optane）拥有接近 DRAM 的延迟和持久性，理论上可消除 LSM-Tree 的写放大问题——但直接将传统 LSM 架构移植到 NVM 上会导致写停顿不减反增。

**创新：** 提出 PartitionKV——面向 NVM 的自适应分区 LSM-Tree 架构：根据数据冷热和工作负载动态将 KV 空间划分为多个独立分区，每个分区采用不同的 compaction 策略，通过分区级别的写放大与读延迟联合优化模型自适应调节分区边界。

📄 [PACMMOD Vol.4 No.1 (R3)](https://dl.acm.org/toc/pacmmod/2026/4/1) · `LSM-Tree` `NVM`

---

#### Efficient Index Layout and Search Strategy for Large-scale High-dimensional Vector Similarity Search

Jingyu Chen 等 — 南科大; Huawei

**SIGMOD '26** · **动机：** 百亿级高维向量相似搜索面临图索引内存占用超线性增长和分布式分片破坏图拓扑两大瓶颈。

**创新：** 提出两级索引布局：全局层用轻量聚类做粗粒度分区，局部层在每个分区内构建高质量图索引；引入查询感知路由策略，利用查询向量分布特性只激活 2-3 个分区。在十亿级 1024 维基准上，以 40% 的内存开销达到 99%+ 召回率（Recall@10）。

📄 [PACMMOD Vol.4 No.3](https://dl.acm.org/toc/pacmmod/2026/4/3) · `向量索引` `ANN`

---

### 📌 FAST 2026

#### DMTree: Towards Efficient Tree Indexing on Disaggregated Memory via Compute-side Collaborative Design

Guoli Wei, Yongkun Li 等 — USTC

**FAST '26** · **动机：** 分离式内存架构下，传统树索引（B+Tree/ART）遭遇灾难性性能下降——每次指针追踪都可能跨越网络，延迟从纳秒级变为微秒级。

**创新：** 提出 DMTree——计算端与内存端协同设计的树索引：在计算端缓存内部节点并预取子树，在内存端以"胖节点"形式存储连续键范围以减少网络往返；利用 RDMA one-sided read 批量拉取节点，配合计算端流水线预取隐藏网络延迟，将分离式内存下树操作延迟降低 3-5 倍。

📄 [USENIX FAST '26](https://www.usenix.org/conference/fast26/presentation/wei) · `分离式内存` `树索引`

---

#### "Range as a Key" is the Key! Fast and Compact Cloud Block Store Index with RASK

Haoru Zhao, Mingkai Dong 等 — SJTU

**FAST '26** · **动机：** 云块存储需要维护从逻辑块地址到物理位置的映射索引，PB 级存储下索引元数据可能占用数百 GB 内存。

**创新：** 提出 RASK（Range as Key）索引：利用块存储 I/O 的空间局部性，将连续 LBA 范围映射为单个索引条目。核心洞察是"Range as a Key is the Key"——用范围而非单个地址作为索引的基本单位，在真实云工作负载下将元数据量减少一个数量级，同时保持亚毫秒级查找延迟。

📄 [USENIX FAST '26](https://www.usenix.org/conference/fast26/presentation/zhao) · `块存储索引` `RASK`

---

#### Holistic and Automated Task Scheduling for Distributed LSM-tree-based Storage

Yuanming Ren, Siyuan Sheng 等 — USTC; CUHK

**FAST '26** · **动机：** 分布式 LSM-Tree 系统中，每个副本独立执行 compaction 和 flush 操作，多副本间 compaction 风暴导致 I/O 争抢和缓存失效。

**创新：** 提出全局自动化任务调度框架：建立跨副本的 compaction 开销模型，通过约束求解器生成全局最优的 compaction 调度计划（错开各副本的 compaction 窗口、在副本间迁移 compaction 负载），将多副本互扰降低 60% 以上，尾延迟改善 2-3 倍。

📄 [USENIX FAST '26](https://www.usenix.org/conference/fast26/presentation/ren) · `LSM-Tree` `调度`

---

#### DOGI: Data Placement with Oracle-Guided Insights for Log-Structured Systems

**FAST '26** · **动机：** 日志结构存储中，数据放置策略直接影响垃圾回收（GC）效率和空间放大。现有策略通常基于简单启发式规则，缺乏对数据生命周期的全局视角。

**创新：** 提出 DOGI（Data Placement with Oracle-Guided Insights）——用离线分析的历史访问 trace 训练数据热度预测模型，在线指导数据放置。核心思想是在写入路径上就将数据按预测的生命周期分组放置到不同的 segment，使 GC 时仅需清理"已冷却"的 segment，大幅降低写放大和 GC 停顿。

📄 [USENIX FAST '26](https://www.usenix.org/conference/fast26/) · `日志结构` `数据放置`

---

### 📌 CIDR 2026

#### Raster is Faster: Rethinking Ray Tracing in Database Indexing

Harish Doraiswamy, Jayant R. Haritsa — IISc Bangalore

**CIDR '26** · **动机：** GPU 数据库索引需要判断大量数据点是否落在查询范围内，传统方法使用光线追踪逐点测试，效率受限。

**创新：** 提出用光栅化（Rasterization）替代光线追踪来做数据库索引操作——将查询范围渲染为 GPU 光栅化管线中的多边形，利用硬件光栅化器批量判定数据点的 inclusion。这是一种"用 GPU 图形管线做数据库运算"的创新思路。

📄 [PDF](https://www.cidrdb.org/papers/2026/p18-doraiswamy.pdf) · `GPU 索引`

---

#### Flexible I/O for Database Management Systems with xNVMe

Emil Houlborg, Pınar Tözün — ITU Copenhagen

**CIDR '26** · **动机：** 现代 NVMe SSD 提供内核路径和 kernel-bypass 路径两种 I/O 方式，数据库系统需要在两种路径间选择，但现有方案要求编译时或部署时绑定。

**创新：** 提出基于 xNVMe 的灵活 I/O 框架——统一 NVMe 硬件抽象层，封装 SPDK、libaio、io_uring 等后端，允许数据库系统在运行时透明切换 I/O 路径（联机事务用 SPDK 追求低延迟，后台 compaction 走 io_uring 利用内核缓存），首次实现了 I/O 路径与查询执行引擎的解耦。

📄 [PDF](https://www.cidrdb.org/papers/2026/p6-houlborg.pdf) · `NVMe` `存储 I/O`

---

## 🤝 二、分布式共识协议

### 📌 SIGMOD 2026

#### Scalable Leader Leases For Multi Consensus Groups in CockroachDB

Ibrahim Kettaneh, Tsvetomira Radeva, Rebecca Taft 等 — Cockroach Labs

**SIGMOD '26 Industry** · **动机：** CockroachDB 的每个 Range 对应一个 Raft 组，生产集群可达数十万个 Raft 组。每个组的 Leader 需要定期续约 Lease——数十万条 Lease 心跳消息导致控制面资源消耗占比超过 30%。

**创新：** 提出可扩展的多组 Leader Lease 机制：将数十万个 Raft 组的 Lease 管理拆分为分层心跳架构——同一节点上的 Range 共享 node-level lease，同一 store 上批量续约；引入预测性 Lease 延期（基于历史心跳间隔的统计模型提前延期），将 Lease 管理开销降低 80%，读延迟 P99 改善 5 倍。

📄 [SIGMOD Industry](https://2026.sigmod.org/sigmod_industry_papers.shtml) · `Raft` `Lease` `工业论文`

---

#### LSM-Raft: Optimizing Raft for LSM-tree Store

Xiaojian Zhang 等 — Tsinghua; Timecho (Apache IoTDB)

**SIGMOD '26** · **动机：** Raft 共识协议与 LSM-Tree 存储引擎在同一节点上共享 I/O 和 CPU 资源，但传统方案将它们视为独立黑盒——导致周期性的 I/O 风暴和 CPU 争抢。

**创新：** 提出 LSM-Raft——共识协议与存储引擎深度协同框架。Raft Leader 实时感知 LSM-Tree 各层的 compaction 状态和积压程度，据此动态调节日志同步节奏，并通过 I/O 带宽预算的全局分配避免资源争抢。将 LSM-Raft 组合系统吞吐提升 50% 以上，尾延迟降低 60%。

📄 [PACMMOD Vol.4 No.3](https://dl.acm.org/toc/pacmmod/2026/4/3) · `Raft` `LSM 协同` 🔥

---

#### Epoch-based Optimistic Concurrency Control in Geo-replicated Databases

Yunhao Mao 等 — U Toronto; Keio University

**SIGMOD '26** · **动机：** 地理复制数据库的跨洲延迟通常在 100ms+，传统 OCC 在这种场景下事务中止率极高——因为验证阶段需要跨洲确认。

**创新：** 提出基于 epoch 的 OCC 协议：将时间划分为固定长度的 epoch，同一 epoch 内的读写操作在本地执行无需跨洲协调，epoch 边界进行轻量级全局验证。在跨洲部署中保证快照隔离的同时吞吐量提升 3-5 倍。

📄 [PACMMOD Vol.4 No.3](https://dl.acm.org/toc/pacmmod/2026/4/3) · `Geo-Replication` `OCC`

---

#### Reducing Tail Latency in Storage-Disaggregated Database Systems

Zhengrui Pang, Jiannan Wang — Purdue University

**SIGMOD '26** · **动机：** 存储分离架构下网络延迟的抖动被放大——一次查询可能涉及数十次远端 I/O。

**创新：** 提出三维度尾延迟优化框架：(1) 基于网络延迟预测的 hedge-request 机制；(2) 利用查询执行计划的 DAG 结构预先下发 I/O 的智能预取；(3) 基于实时拥塞感知的副本负载均衡，将尾延迟 P99 降低 2-5 倍。

📄 [PACMMOD Vol.4 No.3](https://dl.acm.org/toc/pacmmod/2026/4/3) · `尾延迟` `分离式架构`

---

### 📌 CIDR 2026

#### Rosé: Flexible Replication With Strong Semantics For Partitioned Databases

Ioannis Zarkadas, Philip A. Bernstein, Asaf Cidon — Columbia; Microsoft Research

**CIDR '26** · **动机：** 分区数据库通常对所有分区采用统一的复制策略，但不同分区的访问模式差异巨大。

**创新：** 提出 Rosé——允许每个分区独立选择复制协议（Raft/Chain-Replication/Primary-Backup/Quorum）的"one-size-fits-one"框架。通过形式化证明保证跨分区事务的可串行化不受各分区协议异构性的影响；提供协议自动推荐器，根据分区访问特征和延迟 SLO 自动选择最优复制策略。

📄 [PDF](https://www.cidrdb.org/papers/2026/p8-zarkadas.pdf) · `复制协议` `分区 DB`

---

#### Event Horizon: Asymmetric Dependencies for Fast Geo-Distributed Operations

Jonathan Arns 等 — TU Delft

**CIDR '26** · **动机：** 跨地域分布式操作的传统模型基于对称依赖——所有参与者必须双向确认才能推进。实际上许多操作只需要单向依赖，但现有协议无法表达和利用这种非对称性。

**创新：** 提出 Event Horizon——基于非对称依赖的分布式协调模型：形式化定义了操作的依赖图，区分"must-happen-before"（强制双向同步）和"should-happen-before"（仅需单向通知）两种依赖边。在保证因果一致性的前提下将 Geo-Distributed 操作延迟降低 40-60%。

📄 [PDF](https://www.cidrdb.org/papers/2026/p20-arns.pdf) · `非对称依赖` `低延迟`

---

## 🏭 三、工业系统

### 📌 SIGMOD 2026 Industry (精选)

#### Aurora PostgreSQL Limitless Database

Dima Arkhangelskiy 等 20 人 — AWS

**SIGMOD '26 Industry** · **动机：** Aurora PostgreSQL 的单写多读架构在高并发写入场景下存在单点瓶颈。

**创新：** Aurora Limitless Database 引入三项核心技术：(1) 基于全局逻辑时钟（Global Logical Clock）的分布式 MVCC，消除中心化事务管理器；(2) 分布式共享存储层的"迷你页"协议，将页级冲突转化为行级冲突；(3) 基于 Causal Broadcast 的写集同步，实现多写节点的缓存一致性。首次在完全兼容 PostgreSQL 的前提下实现多主写入。

📄 [SIGMOD Industry](https://2026.sigmod.org/sigmod_industry_papers.shtml) · `AWS Aurora` `分布式 OLTP`

---

#### ByteHouse: ByteDance's Cloud-Native Data Warehouse

Yuxing Han 等 — ByteDance; SJTU; Tsinghua

**SIGMOD '26 Industry** · **动机：** 字节跳动生产环境中的数据分析面临多模态数据统一分析、查询优化器联合优化、存算分离架构性能退化三大挑战。

**创新：** ByteHouse 提出三层创新：(1) 统一表引擎提供两级逻辑抽象和物理一致布局，SSD 集群级缓存（CrossCache）和虚拟文件系统（NexusFS）；(2) 计算层支持批/流/增量三种执行模式；(3) 控制层利用历史执行 Trace 和 AI 辅助计划选择的查询优化器。

📄 [SIGMOD Industry](https://2026.sigmod.org/sigmod_industry_papers.shtml) · `ByteDance` `实时数仓`

---

#### TDSQL-Boundless: Distributed Database for Heterogeneous Multi-Table Workloads

Yuxing Chen 等 — Tencent; Renmin Univ

**SIGMOD '26 Industry** · **动机：** 分布式数据库在处理多表 JOIN 查询时面临跨节点数据 Shuffle 瓶颈。

**创新：** TDSQL-Boundless 提出异构多表工作负载的自适应路由和查询优化：(1) 多表亲和度分析——生成渐进式 co-location 迁移计划；(2) 混合 JOIN 执行策略——根据数据分布动态选择 Broadcast JOIN、Shuffle JOIN 或 Partial Co-location JOIN；(3) 在线数据迁移与查询执行流水线化。

📄 [SIGMOD Industry](https://2026.sigmod.org/sigmod_industry_papers.shtml) · `TDSQL` `分布式 DB`

---

#### CoddSpeed: Hardware Accelerated Query Processing in Microsoft Fabric

Matteo Interlandi 等 50+ 人 — Microsoft

**SIGMOD '26 Industry** · **动机：** Microsoft Fabric 需要处理 PB 级数据上的交互式分析查询，纯 CPU 方案遇到吞吐瓶颈。

**创新：** CoddSpeed（以关系模型之父 Ted Codd 命名）是 Microsoft Fabric 的 FPGA 加速查询引擎：(1) 将扫描、过滤、哈希、聚合等原语卸载到 FPGA 的流水线数据通路；(2) 通过编译时查询计划分析自动决定算子卸载策略；(3) 50+ 人规模的跨团队工程实践。代表异构硬件透明加速从学术原型走向工业部署的里程碑。

📄 [SIGMOD Industry](https://2026.sigmod.org/sigmod_industry_papers.shtml) · `硬件加速` `MS Fabric`

---

#### TokaDB: A Unified Storage Engine for Training-Serving Data Management

Peng Fang 等 — HUST; ByteDance

**SIGMOD '26 Industry** · **动机：** 推荐系统存在训练和服务两侧的存储鸿沟——训练侧需要高吞吐批量读取，服务侧需要低延迟实时特征查询（< 1ms），且存在训练-推理特征不一致（Training-Serving Skew）问题。

**创新：** TokaDB 是统一的训练-服务存储引擎：(1) 双模存储引擎——底层 LSM-Tree 同时支持批量扫描和点查询；(2) 特征版本管理——所有特征写入被赋予全局时间戳和版本链；(3) 增量快照——支持训练侧读取一致性的增量特征快照。

📄 [SIGMOD Industry](https://2026.sigmod.org/sigmod_industry_papers.shtml) · `推荐系统` `统一存储`

---

#### ByteGraph-Dione: Adaptive Dual-Format Graph Engine

Chao Chen 等 14 人 — ByteDance

**SIGMOD '26 Industry** · **动机：** 字节跳动的社交图和推荐图需要同时支持高吞吐图遍历和低延迟随机更新，传统图系统无法同时满足。

**创新：** ByteGraph-Dione 提出自适应双格式图引擎：每个图分区同时维护 CSR 和邻接表两种物理表示，通过热度追踪器动态决定；格式切换采用增量转换（delta conversion）；在双格式上实现事务性图更新（ACID）。

📄 [SIGMOD Industry](https://2026.sigmod.org/sigmod_industry_papers.shtml) · `图引擎` `自适应格式`

---

#### LindormVector: Distributed Vector Engine on Multi-Model NoSQL Database

Yan Wang 等 — Alibaba Cloud; USTC; Rutgers

**SIGMOD '26 Industry** · **动机：** 企业应用中向量搜索需要与结构化数据和全文检索混合查询，但独立向量数据库无法高效处理。

**创新：** LindormVector 在 Lindorm 多模 NoSQL 引擎中原生集成向量搜索：在现有 LSM-Tree 存储引擎上新增向量索引（IVF+PQ+HNSW 可插拔）；提出混合查询优化器——同时利用标量过滤选择性和向量距离剪枝能力；分布式向量索引分区策略与结构化数据的分区策略协同。

📄 [SIGMOD Industry](https://2026.sigmod.org/sigmod_industry_papers.shtml) · `向量引擎` `多模 DB`

---

#### Scalable and Resilient Storage Tier for Azure SQL Hyperscale

Alejandro Hernandez Saenz 等 — Microsoft

**SIGMOD '26 Industry** · **动机：** Azure SQL Hyperscale 的存储层需要支持数百 TB 的数据库和数千个并发连接。

**创新：** 提出可扩展弹性存储层架构：分层页服务器——将日志服务层和页服务层独立扩展；基于快照隔离的读扩展——多个计算节点通过共享存储快照实现一致性读；弹性存储池——所有数据库共享底层存储池，按需分配。

📄 [SIGMOD Industry](https://2026.sigmod.org/sigmod_industry_papers.shtml) · `Azure SQL` `Hyperscale`

---

#### CLAPS: Load-Aware Proxy Resource Pooling for Large-Scale Cloud Storage

Xiuqi Huang 等 — Zhejiang Univ; ByteDance

**SIGMOD '26 Industry** · **动机：** 大规模云存储系统为每个用户部署独立的代理集群以保证性能隔离，但多数用户请求是突发的，资源闲置率高达 80-90%。

**创新：** CLAPS 提出负载感知代理资源池化：将多个用户的代理资源合并为共享池；基于在线负载预测的弹性伸缩算法；提出"借-还"协议，高负载用户可"借用"低负载用户的代理配额。在生产集群中减少 40-50% 的代理节点数。

📄 [SIGMOD Industry](https://2026.sigmod.org/sigmod_industry_papers.shtml) · `云存储` `资源池化`

---

### 📌 FAST 2026

#### ACOS: Apple's Geo-Distributed Object Store at Exabyte Scale

Benjamin Baron 等 — Apple

**FAST '26** · **动机：** Apple 的 iCloud、Photos、Messages 等服务每天处理数十亿用户的数据，底层对象存储需要横跨多个大洲、管理 EB 级数据、满足数据主权法规。

**创新：** ACOS（Apple's Geo-Distributed Object Store）首次公开完整架构：(1) 基于 CRUSH-like 的声明式数据放置策略引擎——将法规约束编码为放置规则；(2) 多层级故障域感知的弹性副本策略；(3) 跨大洋异步复制与本地同步复制的混合拓扑。是近年罕见的 EB 级工业存储系统完整技术披露。

📄 [USENIX FAST '26](https://www.usenix.org/conference/fast26/presentation/baron) · `Apple` `EB 级存储`

---

#### Discard-Based Garbage Collection for Distributed Log-Structured Storage in ByteDance

Runhua Bian 等 — ByteDance

**FAST '26** · **动机：** 字节跳动内部广泛使用日志结构化存储，垃圾回收（GC）是其核心运维挑战——传统 copy-forward GC 造成大量写放大和 I/O 风暴。在 PB 级部署中，GC 造成的额外写入量可达业务写入的 2-3 倍。

**创新：** 提出基于 discard/trim 的零拷贝 GC：利用现代 SSD 的 discard 和文件系统的 hole punching 原语直接释放无效数据的物理空间，无需数据拷贝；设计 segment 粒度的"惰性 discard"；提出"GC 冷"策略——标记不再写入的冷 segment 优先 discard。在字节跳动 PB 级生产环境中将 GC 写放大降至接近零。

📄 [USENIX FAST '26](https://www.usenix.org/conference/fast26/presentation/bian) · `ByteDance` `日志 GC`

---

### 📌 CIDR 2026

#### A Multi-tenant Relational OLTP Database at Salesforce

Vaibhav Arora, Pat Helland 等 — Salesforce

**CIDR '26** · **动机：** Salesforce 是全球最大的多租户 SaaS 平台之一，其底层数据库需要支撑数百万租户的 OLTP 工作负载。

**创新：** Salesforce 多租户 OLTP 数据库提出：(1) 基于自适应租户分组的物理隔离；(2) 请求级资源调度——每个查询被标记租户 ID 和优先级，在各层实现细粒度资源隔离；(3) 数据库内核感知的租户 QoS——当检测到某租户超过资源配额时，在查询执行引擎内部进行限流。该架构已支撑 Salesforce 核心业务多年。

📄 [PDF](https://www.cidrdb.org/papers/2026/p28-arora.pdf) · `Salesforce` `多租户 DB`

---

## 🤖 四、AI Infra 相关

### 📌 LLM 推理 · KV Cache 存储优化 (FAST 2026)

#### CacheSlide: Unlocking Cross Position-Aware KV Cache Reuse for Accelerating LLM Serving

Yang Liu, Yunfei Gu, Chentao Wu, Minyi Guo — SJTU

**FAST '26** · **动机：** 现有 prefix-matching 方案仅能复用请求间「完全相同前缀」的 KV Cache，但实际对话中大量请求共享「错位但语义重叠」的片段，因位置不同而无法复用。

**创新：** 提出跨位置感知的 KV Cache 复用框架 CacheSlide。通过构建位置无关的语义哈希索引，在多个并发请求间检测并复用位置错位的 KV Cache 片段。在真实对话负载上将 KV Cache 命中率提升 2-3 倍，等效将有效上下文窗口扩展数倍而无需额外显存。

📄 [USENIX FAST '26](https://www.usenix.org/conference/fast26/presentation/liu-yang) · `LLM 推理` `KV Cache`

---

#### Bidaw: Bidirectional Computation-Storage Awareness for Interactive LLM Serving

Shipeng Hu, Guangyan Zhang — Tsinghua University

**FAST '26** · **动机：** 将 KV Cache 卸载到 SSD 可扩展有效上下文窗口，但传统方案将计算与 I/O 视为独立阶段，导致硬件利用率低下。

**创新：** 提出双向计算-存储感知调度框架 Bidaw。GPU 端预测即将需要的 KV Cache 块并提前发起 SSD 预取（计算→存储），SSD 端根据 KV Cache 的访问热度动态调整数据布局以加速后续读取（存储→计算）。将 GPU 空闲等待时间减少 40% 以上，TTFT 降低 30%。

📄 [USENIX FAST '26](https://www.usenix.org/conference/fast26/presentation/hu-shipeng) · `LLM 推理` `双向感知`

---

#### SolidAttention: Low-Latency SSD-based Serving on Memory-Constrained PCs

Xinrui Zheng 等 — SJTU

**FAST '26** · **动机：** 在消费级 PC（显存 4-8GB）上运行大语言模型时，直接使用 SSD 作为 KV Cache 的交换空间会导致注意力计算延迟从微秒级飙升至毫秒级。

**创新：** 提出 SolidAttention——面向 SSD 物理特性重新设计的注意力算子。将 KV Cache 按 SSD 页面大小对齐分块，批量排序后顺序读取；同时在 GPU 端引入分块流水线预取，将 SSD 读取延迟隐藏在后续计算中，使内存受限 PC 上的端到端推理延迟降低至接近纯 GPU 推理的水平。

📄 [USENIX FAST '26](https://www.usenix.org/conference/fast26/presentation/zheng) · `SSD 推理` `注意力`

---

### 📌 向量搜索 (ANNS) · SIGMOD 2026

#### CMANNS: GPU-Accelerated Graph Index Construction for ANNS via Compute-Memory Disaggregation

Chengying Huan, Rong Gu 等 — Nanjing University; Tsinghua

**SIGMOD '26** · **动机：** 十亿级数据集上构建图索引可能耗时数天，且内存占用随数据规模超线性增长。现有加速方案依赖单机大内存，在云原生架构下因远端内存访问延迟而严重退化。

**创新：** 提出 CMANNS——计算-内存分离架构下的 GPU 加速图索引构建系统。将距离计算密集型操作卸载到 GPU，同时设计内存端智能数据预取与 GPU 端计算流水线以隐藏 RDMA 延迟。在十亿级数据集上将图索引构建时间从数天缩短至数小时，同时保持索引质量无损。

📄 [PACMMOD Vol.4 No.3](https://dl.acm.org/toc/pacmmod/2026/4/3) · `向量搜索` `GPU`

---

#### An In-Depth Study of Filter-Agnostic Vector Search on PostgreSQL

Duo Lu, Helena Caminal, Manos Chatzakis 等 — Brown U; Google; ETH

**SIGMOD '26** · **动机：** 生产环境中绝大多数向量搜索查询附带元数据过滤条件，但学术界对 ANNS 的评估几乎完全忽略过滤条件，导致学术界最优方案在真实场景中可能表现极差。

**创新：** 首次对 PostgreSQL 上的过滤无关向量搜索进行深度实证研究。系统分析 pgvector 的 IVF-Flat/HNSW 索引在不同过滤策略、不同过滤选择性和不同查询负载下的性能退化模式，揭示查询规划器缺乏对向量索引代价感知的根本问题。

📄 [PACMMOD Vol.4 No.3](https://dl.acm.org/toc/pacmmod/2026/4/3) · `PostgreSQL` `向量搜索`

---

#### FAVOR: Efficient Filter-Agnostic Vector ANNS via Selectivity-Aware Exclusion Distances

Junjie Song 等 — HUST; Zhejiang University

**SIGMOD '26** · **动机：** 过滤无关向量搜索面临根本困境：前过滤可能因过滤条件过严导致搜索空间过小，后过滤可能浪费计算资源，而现有中间方案缺乏对过滤选择性的感知。

**创新：** 提出 FAVOR——基于选择性感知排除距离的过滤无关 ANNS 算法。利用过滤条件的实时选择性动态计算"排除距离"，在高选择性场景下扩大搜索范围保证召回率，在低选择性场景下收紧搜索范围降低计算开销。

📄 [PACMMOD Vol.4 No.3](https://dl.acm.org/toc/pacmmod/2026/4/3) · `ANNS` `过滤无关`

---

### 📌 AI 训练基础设施 · FAST 2026

#### GPU Checkpoint/Restore Made Fast and Lightweight

Shaoxun Zeng 等 — Tsinghua University

**FAST '26** · **动机：** 大规模 AI 训练中，全量 Checkpoint 的 I/O 开销导致训练停顿 5-15 分钟——在频繁 Checkpoint 下累计浪费可达训练总时间的 10-20%。

**创新：** 提出快速轻量 GPU Checkpoint/Restore 机制。利用 GPU 显存中张量的稀疏性和训练过程中的状态不变性，仅增量保存变化超过阈值的张量区域；同时在存储端设计 GPU 显存布局感知的并行写入路径。将 Checkpoint 时间从分钟级压缩至秒级，存储空间减少 3-5 倍。

📄 [USENIX FAST '26](https://www.usenix.org/conference/fast26/presentation/zeng) · `GPU Checkpoint` `AI 训练`

---

#### AdaCheck: An Adaptive Checkpointing System for Efficient LLM Training

Weijie Liu 等

**FAST '26** · **动机：** LLM 训练中不同层的参数对故障恢复的重要性和变化速率差异巨大——Embedding 层变化缓慢，深层注意力投影矩阵则每个 step 都在剧变。固定频率的全量 Checkpoint 浪费大量 I/O 和存储资源。

**创新：** 提出 AdaCheck——自适应 Checkpoint 系统。实时追踪每层参数的变化幅度，动态决定各层的 Checkpoint 频率；同时利用层间冗余进行增量编码压缩，在数万卡集群上将 Checkpoint 总 I/O 量降低 50-70%，而不影响故障恢复精度。

📄 [USENIX FAST '26](https://www.usenix.org/conference/fast26/presentation/liu-weijie) · `LLM 训练` `Checkpoint`

---

#### Fast Cloud Storage for AI Jobs via Grouped I/O API with Transparent Read/Write Optimizations

Yingyi Hao 等 — SJTU

**FAST '26** · **动机：** AI 训练作业的 I/O 模式与通用云存储 API 之间存在根本性不匹配——训练框架以大量小文件并发读取，而对象存储 API 按单个 GET/PUT 操作计费和调度。

**创新：** 提出分组 I/O API：将时间窗口内的一组逻辑相关 I/O 操作聚合为一个 GroupedRequest 提交给存储系统，使存储端可以进行批量预取、合并元数据查询、全局调度。同时在存储端实现透明的读优化和写优化，AI 框架无需任何代码修改即可获得数倍的 I/O 吞吐提升。

📄 [USENIX FAST '26](https://www.usenix.org/conference/fast26/presentation/hao) · `AI I/O` `云存储`

---

### 📌 CIDR 2026 · Agent-First 数据系统

#### Supporting Our AI Overlords: Redesigning Data Systems to be Agent-First

Shu Liu, Ion Stoica, Matei Zaharia, Alvin Cheung, Natacha Crooks — UC Berkeley

**CIDR '26** · **动机：** AI Agent（如 Claude Code、Cursor、Devin）正在成为数据库系统的主要消费者——它们以程序化方式生成 SQL、迭代探索数据、跨多轮交互构建分析管线。但现有数据库系统的 API 和语义模型是为人类分析师设计的，这些假设在 Agent 驱动的交互模式下全面失效。

**创新：** 提出 Agent-First 数据系统的 Vision：(1) 面向 Agent 的多轮会话式查询 API——支持查询上下文传递、不确定性感知的结果返回、增量结果流式推送；(2) Agent-Native 查询优化——将优化目标从"单查询延迟"改为"会话级信息获取效率"；(3) 语义灵活的 Schema 模型——支持 Agent 在不确定 Schema 的情况下进行 Best-Effort 查询。这是 CIDR 2026 最具前瞻性的论文之一，为数据库领域指明了 AI 时代的重构方向。

📄 [PDF](https://www.cidrdb.org/papers/2026/p32-liu.pdf) · `Agent-First` `Vision` 🔥必读

---

## 🔮 五、趋势洞察与总结

### 01 · 共识协议与存储引擎深度协同

LSM-Raft 是本期最值得关注的论文之一——首次将共识协议的日志同步节奏与 LSM-Tree 的 compaction 状态动态联动。这标志着一个拐点：共识协议不再作为黑盒运行在存储引擎之上，而是需要感知存储引擎的内部状态。**对 Kafka/AutoMQ 的启示**：当 Kafka 的 __consumer_offsets 等内部 Topic 使用 Raft 复制时，同样面临 compaction 与 replication 的 I/O 争抢，LSM-Raft 的思路值得关注。

### 02 · 持久化索引结构走向工程落地

持久化多版本 ART、Concurrent Path-Copying、PartitionKV（NVM LSM-Tree）的集中出现，说明持久内存/分离式内存的索引设计已从"提出新结构"阶段进入"并发、持久化、生产级"的工程化阶段。DMTree 进一步将分离式内存作为一级架构约束，证明了在计算-存储分离场景下索引必须与架构协同设计。

### 03 · 工业数据库论文爆发

SIGMOD 2026 Industry Track 贡献了近年来最丰富的一批工业数据库论文：Aurora Limitless (多写)、ByteHouse (多模数仓)、TDSQL-Boundless (异构多表)、CoddSpeed (FPGA 加速)、LindormVector (向量引擎)。这些论文的共同点：都是在已有系统上叠加新的能力维度（多写、多模、向量、硬件加速），说明工业界已经度过"基于开源 fork 系统"的阶段，进入"系统架构深度融合新硬件/新负载"的时代。

### 04 · AI Infra 已成为存储顶会的 P0 方向

FAST 2026 有 43 篇论文，粗略统计：LLM 推理存储（KV Cache）3篇、AI 训练存储（Checkpoint/Mem/IO）3篇、ML 预处理存储 1篇——AI Infra 占比超过 16%。SIGMOD 2026 Research 有 4 篇向量搜索/ANNS 论文，Industry 也有 LindormVector 和 ByteHouse 的多模向量能力描述。CIDR 2026 更是出现了 "Agent-First 数据系统" 的 Vision 论文。**AI Infra 方向的存储/数据库论文密度在过去一年至少增加了 3 倍。**

### 05 · "One-size-fits-one" 成复制/分布式的潜在线

从 SIGMOD 的 Epoch-based OCC (Geo 场景专项优化)、Rosé 的 per-partition 复制策略，到 Event Horizon 的非对称依赖——共识/复制/事务协议正从"通用性"转向"场景定制"。过去追求"某种协议统治一切"的思路正在让位于"为一个细分场景做最好的协议"。

### 06 · 向量数据库从独立品类走向融合

PostgreSQL 上的向量搜索实证研究（SIGMOD）、Lindorm 多模 NoSQL 的向量引擎（Industry）、FAVOR 的过滤无关 ANNS——信号明确：向量搜索正从独立的"向量数据库"品类回归到数据库系统的原生能力。这与 Kafka 社区讨论的 "Kafka + Vector Search" 方向高度相关。

---

*由 CHANG_AI_TEAM 技术调研团队维护 · 每周更新（每周四）*
*收录标准：顶会接收论文 · 聚焦 存储引擎/共识/工业系统/AI Infra 四个方向 · 链接到可免费获取的原文*
