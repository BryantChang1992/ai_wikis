---
type: concept
title: 'CaaS-LSM: Compaction-as-a-Service'
aliases:
- CaaS-LSM
- Compaction即服务
sources:
- https://doi.org/10.1145/3654927
tags:
- LSM-Tree
- compaction
- disaggregated-storage
- FaaS
- serverless
- KV-store
- storage-disaggregation
- RocksDB
status: draft
related:
- '[[知识库/wiki/LSM-Tree]]'
- '[[知识库/wiki/LSM-Tree-合并优化]]'
- '[[知识库/wiki/Silo-Compaction-迁移协议]]'
- '[[知识库/wiki/LSM-tree-KV-Survey-综述]]'
created: &id001 2026-07-02
confidence: 0.75
confidence_rationale: 类型=concept; 更新于4天前
updated: *id001
source_citations:
- 'title: CaaS-LSM: Compaction-as-a-Service for LSM-based Key-Value Stores in Storage Disaggregated Infrastructure;
  authors: [''Qiaolin Yu'', ''Chang Guo'', ''Jay Zhuang'', ''Viraj Thakkar'', ''Jianguo Wang'', ''Zhichao Cao''];
  venue: SIGMOD 2024 (Proc. ACM Manag. Data, Vol. 2, No. 3); doi: 10.1145/3654927; year: 2024'
synced_at: '2026-10-05'
blog_url: https://bryantchang1992.github.io/ai_memory_chang_ai_team/knowledge/CaaS-LSM-Compaction即服务/
blog_source: _posts/2026-07-02-knowledge-935f738bf5.md
---

# CaaS-LSM: Compaction-as-a-Service

## 一句话摘要

将 LSM-tree 的 Compaction 从存储引擎中完全解耦为无状态的 FaaS（Function-as-a-Service）弹性服务，运行于存储侧节点，由自适应控制面统一调度管理。

## 背景与动机

在存算分离（Storage Disaggregation）架构下，传统 LSM-KVS 的 Compaction 是一个核心瓶颈：SST 文件在 Compute Node (CN) 和 Disaggregated Storage (DS) 之间反复搬移，产生大量网络 I/O，与前台读写争抢 CPU 和带宽资源。现有方案（如 Disaggregated-RocksDB、Nova-LSM）虽然将 Compaction 卸载到 DS 节点，但存在以下未解决的问题：

1. **紧耦合依赖**：offloaded compaction 与 LSM-KVS 实例强绑定，缺乏独立弹性
2. **负载不均**：compaction 任务无法跨节点动态调度
3. **协调开销**：compaction 与 LSM-KVS 的状态同步、Manifest 更新引入额外开销
4. **错误处理脆弱**：网络抖动、节点故障等瞬态错误缺乏系统化容错

CaaS-LSM 提出 **Compaction-as-a-Service** 范式，将 Compaction 从"嵌入式后台线程"彻底转变为"独立的无状态云服务"。

## 核心创新

### 1. Compaction-as-a-Service 范式

Compaction 不再作为 LSM-KVS 的内嵌组件，而是以 FaaS 任务的形式提交到存储侧执行。每个 compaction 任务完全无状态——输入为待合并的 SST 文件列表，输出为新 SST 文件和更新的 Manifest。任务完成后即释放资源，天然支持弹性伸缩。

### 2. 无状态 Compaction 执行

- Compaction 任务与 LSM-KVS 实例的生命周期解耦
- 任务可在任意存储节点或空闲计算节点上运行（基于 HDFS 共享存储）
- 无需与 LSM-KVS 进行复杂的状态协调，避免分布式锁和两阶段提交
- 通过原子化的 Manifest 更新保证正确性

### 3. 自适应控制面 (Adaptive Control Plane)

CaaS-LSM 引入了一个性能与资源优化的控制面，负责：

- **运行时调度**：根据 compaction 任务的紧急程度、数据局部性、节点负载动态分配
- **资源管理**：监控各节点 CPU/内存/网络利用率，避免 compaction 干扰前台请求
- **自适应策略**：根据写入压力自动调整 compaction 并发度和优先级
- **弹性扩缩**：利用 FaaS 平台的自动伸缩能力，按需分配 compaction 算力

### 4. 分层错误处理

针对不同级别的错误设计了差异化容错逻辑：

- **瞬态错误**（网络抖动、临时资源不足）：重试 + 指数退避，不中断服务
- **执行错误**（任务超时、节点故障）：任务重新调度到健康节点
- **致命错误**（数据损坏、Manifest 冲突）：安全回滚，保持 LSM-KVS 一致性

## 架构设计要点

```
-------------------------------------------------
|                  Compute Node (CN)               |
|  -----------  ----------  --------------  |
|  | Foreground |  | Memtable |  | Block Cache  |  |
|  |   Writes   |  |  Manager |  |              |  |
|  -----------  ----------  --------------  |
|  ------------------------------------------   |
|  |         Compaction Service Client        |   |
|  |   (提交任务、接收结果、更新 Manifest)      |   |
|  ------------------------------------------   |
-------------------------------------------------
                       |  Compaction Request
                       ▼
-------------------------------------------------
|            Control Plane (控制面)                |
|  ------------ ----------- -------------  |
|  | Scheduler  | | Resource  | |   Error     |  |
|  |  (调度器)   | |  Monitor  | |  Handler    |  |
|  ------------ ----------- -------------  |
-------------------------------------------------
                       |  Dispatch Tasks
                       ▼
-------------------------------------------------
|         Compaction Workers (FaaS Tasks)          |
|  ----------  ----------  ----------      |
|  | Worker 1 |  | Worker 2 |  | Worker N | ...  |
|  |(stateless)| |(stateless)| |(stateless)|      |
|  ----------  ----------  ----------      |
|              Shared Storage (HDFS)               |
|         SST Files  |  Manifest  |  WAL           |
-------------------------------------------------
```

### 关键设计决策

| 维度 | 设计选择 |
|------|----------|
| Compaction 执行位置 | 存储节点或空闲计算节点（基于 HDFS 共享存储） |
| 任务粒度 | 单个 compaction job（input SSTs → output SST） |
| 状态管理 | 完全无状态，结果通过原子 Manifest 更新写回 |
| 调度策略 | 自适应：数据局部性 + 负载均衡 + 紧急度优先 |
| 容错机制 | 分层处理：瞬态重试 / 节点级重新调度 / 致命错误回滚 |
| 底层存储 | HDFS（分布式文件系统），CN 和 Worker 共享同一命名空间 |

## 与传统嵌入式 Compaction 的对比

| 维度 | 传统嵌入式 Compaction | CaaS-LSM |
|------|----------------------|----------|
| 执行模式 | LSM-KVS 进程内后台线程 | 解耦为独立 FaaS 任务 |
| 资源分配 | 与前台共享 CPU/内存，固定线程池 | 弹性分配，按需伸缩 |
| 调度能力 | 本地 FIFO 或简单优先级 | 全局自适应调度（数据局部性 + 负载均衡） |
| 故障影响 | compaction 线程崩溃可能影响整个实例 | 任务级隔离，单任务失败不影响整体 |
| 扩展性 | 受单机 CPU 核数限制 | 横向扩展至整个 DS 集群 |
| 多租户 | 无法跨 LSM-KVS 实例共享 compaction 算力 | 多实例共享 compaction 资源池 |
| 与 LSM-KVS 耦合 | 强耦合，需理解内部状态机 | 松耦合，仅通过 SST 文件和 Manifest 交互 |
| 网络开销 | 大量 SST 数据在 CN ↔ DS 间搬移 | 数据在存储侧本地处理，CN 仅收结果 |

## 实验评估

CaaS-LSM 基于 RocksDB 实现原型，并在 Kvrocks（Redis 兼容 KV）和 Nebula（图数据库）两种分布式数据库上验证通用性。

| 指标 | 对比传统 LSM-KVS | 对比 SOTA 存算分离方案 |
|------|-----------------|----------------------|
| 吞吐量提升 | 最高 **8×** | 最高 **61%** |
| P99 延迟降低 | 最高 **98%** | 显著改善 |

## 局限性

1. **仅解决 Compaction 瓶颈**：未涉及 Memtable Flush 导致的写停顿和写放大。在 CN 内存受限时，频繁 flush 仍会导致性能下降。

2. **依赖 HDFS 共享存储**：需要所有 Compaction Worker 和 CN 共享同一 HDFS 命名空间，部署复杂度高，不适合非 HDFS 环境。

3. **冷启动延迟**：FaaS 任务的冷启动（容器初始化、数据拉取）可能增加 Compaction 延迟，对写停顿敏感的场景不友好。

4. **不利用 Disaggregated Memory (DM)**：未利用 RDMA/CXL 等远程内存技术加速数据路径，整体性能天花板受限于 DS I/O。

5. **被后续工作超越**：O3-LSM（SIGMOD 2026）在相同测试条件下实现了 3.4× 的写吞吐超越（随机写场景），说明"纯 Compaction 卸载"已不足以应对存算分离架构的全部挑战。

6. **Manifest 更新仍是串行瓶颈**：多个 compaction 任务并发完成时，Manifest 的原子更新可能成为新的竞争热点。

7. **论文未开源**：截至 2026 年，CaaS-LSM 的源码未公开，限制了社区验证和进一步研究。

## 后续演进

CaaS-LSM 开启了"数据库内核组件 FaaS 化"的方向，后续工作包括：

- **O3-LSM**（SIGMOD 2026）：在 Compaction Offloading 基础上进一步将 Memtable 和 Flush 也卸载到 Disaggregated Memory，实现三层卸载（3-Layer Offloading），写吞吐再提升 3.4×
- **Near-Data Compaction**（TPDS 2026）：将 Compaction 下沉到更接近存储的位置（SmartNIC/DPU），进一步减少数据搬移

## 相关概念

- [[LSM-Tree]] — LSM-tree 基础数据结构与原理
- [[LSM-Tree-合并优化]] — Compaction 策略优化综述（tiered vs. leveled、Write Amplification 等）
- [[Silo-Compaction-迁移协议]] — Silo 系统中 Compaction 的零停机迁移协议
- [[LSM-tree-KV-Survey-综述]] — LSM-KV 存储引擎全面综述
- Disaggregated-RocksDB（待补充专页） — Meta 的存算分离 RocksDB
- [[Nova-LSM-分布式组件化LSM]] — 基于 RDMA 的存算分离 LSM-KVS
- O3-LSM（待补充专页） — 三层卸载的存算分离 LSM-KVS（SIGMOD 2026）
