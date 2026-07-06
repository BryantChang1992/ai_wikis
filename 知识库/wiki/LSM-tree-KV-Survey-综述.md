---
type: concept
title: "LSM-tree KV Store 综述（2020-2025）"
sources:
  - "sources/papers/LSM-tree-KV-Survey-2025/LSM-tree-KV-Survey-2025.pdf"
  - "sources/papers/LSM-tree-KV-Survey-2025/精读分析.md"
tags:
  - LSM-tree
  - KV-store
  - survey
  - compaction
  - multi-tenant
  - storage-engine
created: 2026-07-02
status: draft
related:
  - "[[LSM-Tree]]"
  - "[[LSM-Tree-RUM猜想]]"
  - "[[LSM-Tree-合并优化]]"
  - "[[LSM-Tree-写放大]]"
  - "[[LSM-Tree-自动调参]]"
  - "[[Silo-Compaction-迁移协议]]"
---
confidence: 0.85
confidence_rationale: "类型=concept; 来源×2; 4天前更新"


## 一句话摘要

2025 年由 MBZUAI + OceanBase（蚂蚁集团）+ 厦门大学联合发表的 LSM-tree KV 存储综述，系统梳理了 2020–2025 年间 100+ 篇优化论文，从 Compaction 优化、基础操作优化和新兴架构三大维度全面审视 LSM-tree 技术演进。

## 核心贡献

1. **建立了统一的 LSM-tree 优化分类框架**：将 100+ 篇论文按 Compaction 优化（资源分配、优先级调度、策略精化）、基础操作优化（Point Lookup、Range Query、隐私删除）和新兴架构（存算分离、Serverless、新硬件、应用定制）三大维度进行系统分类，为研究者提供清晰的导航图。

2. **首次系统梳理 Write Stall 问题的四个环节**：前台-后台资源竞争、Compaction 策略-数据选择-数据量-数据布局的全链路瓶颈分析，揭示了 LSM-tree 性能抖动根因的完整图景。

3. **将存算分离、多租户 Serverless、新硬件适配等现代云原生方向纳入 LSM-tree 研究版图**：相比 Luo & Carey (2020) 综述，新增了 Disaggregated Compaction、DPU offload、CXL 内存池化等前沿领域的系统梳理。

4. **提出了 AI-driven 自动调参、异构存储分层、Workload-Adaptive 架构等未来方向**：为 LSM-tree 从静态配置走向智能自适应指明了路径。

## 关键研究方向

### 1. Compaction 资源与调度优化
Compaction 是 LSM-tree 最核心的后台操作，也是 Write Stall 的主要根源。研究方向包括：如何合理分配 CPU/IO 带宽给前台读写和后台合并（资源分配），如何决定合并任务的执行顺序和时机（优先级调度），以及如何选择触发时机、参与合并的 SST 文件、合并数据量和数据布局（策略精化）。

### 2. 基础操作加速
在 Compaction 之外，直接优化 Point Lookup（点查）、Range Query（范围查询）和隐私删除（GDPR 合规下的安全删除）三大基础操作。典型技术包括 Bloom Filter 增强、索引加速、批量删除优化等。

### 3. 读写放大与 RUM 猜想权衡
Write Amplification（写放大）、Read Amplification（读放大）、Space Amplification（空间放大）三者之间遵循 RUM 猜想的内在约束。该方向探索如何在特定工作负载下找到最优的折中点，以及通过新数据结构打破传统权衡边界的可能性。

### 4. 隐私合规删除
面向 GDPR 等数据保护法规的删除需求，LSM-tree 的追加写特性使得"真正删除"变得困难。研究方向包括高效逻辑删除机制、SST 文件级别的物理删除策略、以及 Lazy Deletion 的安全语义保障。

## 新兴架构

### 存算分离 LSM-KVS
将 Compaction 计算与存储层解耦，实现弹性调度。Compaction 不再是单体引擎内部的后台线程，而可以独立扩展为分布式 Compaction Service，支持单独扩缩容。

### 多租户 Serverless
面向万级到百万级用户，不同租户的负载特征差异巨大（热点、冷热比、读写比）。关键挑战是：如何在共享引擎实例中实现租户间的性能隔离，阻止"吵闹邻居"效应，同时让每个租户获得接近独占实例的体验。

### 新硬件适配
- **NVM/PM (Persistent Memory)**：替代或增强传统 WAL，降低写延迟
- **DPU Offload**：将 Compaction 密集计算 offload 到 DPU/智能网卡，释放 CPU
- **CXL 内存池化**：通过 CXL 总线共享大容量内存池，扩展 MemTable 容量、减少 Compaction 频率

### 异构存储分层
利用不同性能/成本特征的存储介质（如 Optane SSD + QLC SSD + HDD + 云对象存储），根据数据冷热度自动跨层迁移，兼顾性能和总拥有成本（TCO）。

## 与现有知识的关联

- **[[LSM-Tree]]**：本文综述的基础数据结构，所有优化均围绕 LSM-tree 的追加写 + 分层合并模型展开
- **[[LSM-Tree-RUM猜想]]**：读写空间放大三大指标的权衡关系，是理解 Compaction 优化的理论基础
- **[[LSM-Tree-合并优化]]**：本文重点展开的核心方向之一，涵盖策略精化的四个子维度
- **[[LSM-Tree-写放大]]**：Write Stall 和写放大的根因分析，是资源调度优化的动机
- **[[LSM-Tree-自动调参]]**：AI-driven tuning 方向的已有知识基础，本文将其定位为未来关键方向
- **[[Silo-Compaction-迁移协议]]**：与存算分离架构下的独立 Compaction Service 设计理念有天然关联

## 潜在应用场景

1. **LLM 训练数据预处理引擎**：大模型训练数据集具有极端的 write-heavy 特征（海量文本数据的 Tokenize、去重、索引），LSM-tree 的高写入吞吐 + 存算分离架构非常适合此类场景
2. **Serverless KV 云服务**：为 AWS DynamoDB / 阿里云 Tablestore 等产品提供 Compaction 优化的理论指导，支撑百万级租户的差异化 SLA
3. **GDPR 合规存储**：隐私删除方向的研究成果可直接应用于欧洲市场的用户数据删除合规需求
4. **AI-driven 数据库自动运维**：RL 自动调参技术可嵌入数据库内核，减少 DBA 人工介入，降低运维成本
5. **边缘计算存储引擎**：异构存储分层 + 新硬件适配的组合，适合在资源受限的边缘节点上运行高效 KV 引擎
