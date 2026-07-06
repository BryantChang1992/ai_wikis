---
type: concept
title: "Hailstorm: 存算分离 LSM-tree KV 数据库"
aliases: ["Hailstorm", "存算分离LSM"]
sources:
  - "ASPLOS 2020"
  - "Hailstorm: Disaggregated Compute and Storage for LSM-tree Stores"
tags:
  - lsm-tree
  - disaggregated-storage
  - compaction
  - kv-store
  - cloud-native
  - architecture
status: draft
created: 2026-07-02
related:
  - "[[LSM-Tree]]"
  - "[[LSM-Tree-合并优化]]"
  - "[[LSM-tree-KV-Survey-综述]]"
confidence: 0.75
confidence_rationale: "类型=concept; 更新于4天前"
---

## 一句话摘要

Hailstorm（ASPLOS 2020）提出将 LSM-tree 的 compaction 从计算节点 offload 到远端存储节点，在存算分离架构下实现无 resharding 的负载均衡，显著提升云原生 KV 存储的性能与弹性。

## 核心创新

传统 LSM-tree KV 存储（如 LevelDB、RocksDB）在计算节点本地执行 compaction，该过程消耗大量 CPU 和磁盘 I/O，成为系统瓶颈。Hailstorm 的核心创新在于：

1. **Compaction Offloading**：将 compaction 操作从计算节点卸载到远端存储节点，计算节点仅负责前台的读写请求，存储节点承担后台的 compaction 与数据管理
2. **无需 Resharding 的负载均衡**：由于数据以文件粒度在存储层管理，计算节点可以灵活访问任意 SST 文件，当某个计算节点负载过高时，可直接由其他节点接手，无需进行传统的 resharding 操作
3. **存算完全分离**：计算资源与存储资源独立弹性伸缩，各自按需扩展

## 架构设计

### 整体架构

Hailstorm 采用三层架构：**计算层 → 文件系统层(FUSE) → 存储层**

```
-------------------------------------
|          Compute Nodes              |
|  ---------  ---------          |
|  | Read/   |  | Read/   |  ...     |
|  | Write   |  | Write   |          |
|  | Service |  | Service |          |
|  ---------  ---------          |
|       |            |                |
|       ------------                |
|             |                       |
-------------------------------------
              | FUSE File System
-------------------------------------
|             v                        |
|          Storage Layer              |
|  -----------------------------   |
|  |   Storage Nodes              |   |
|  |  ----------- ---------- |   |
|  |  | Compaction| | File     | |   |
|  |  | Offloading| | Serving  | |   |
|  |  ----------- ---------- |   |
|  |   Shared File System (SST)  |   |
|  -----------------------------   |
-------------------------------------
```

### FUSE 文件系统层

- Hailstorm 通过 FUSE（Filesystem in Userspace）在计算节点和存储节点之间建立统一的文件访问层
- 计算节点通过 FUSE 挂载远端存储的文件系统，以 POSIX 接口透明地读写 SST 文件
- 存储节点内部维护文件元数据和数据块的实际存储位置
- FUSE 层解耦了计算与存储，使得计算节点无需感知数据的具体物理布局

### Compaction Offloading 机制

- **传统方式**：Compaction 由计算节点本地执行 → CPU 争抢 + I/O 抖动 → 影响前台查询延迟
- **Hailstorm 方式**：
  1. 计算节点将新写入的 MemTable 刷写为 SST 文件，写入共享存储
  2. 存储节点检测到新的 SST 文件后，异步触发 compaction
  3. Compaction 在存储节点本地完成（数据就近处理，减少网络传输）
  4. 合并后的新 SST 文件更新到共享文件系统
  5. 计算节点通过 FUSE 感知文件变更，更新元数据缓存

### 数据一致性

- MemTable 刷写采用 WAL（Write-Ahead Log）保证持久性
- SST 文件以不可变（immutable）方式写入，compaction 产生新文件而非原地修改
- 存储节点 compaction 完成后通过原子文件操作通知计算节点

## 实验结果

基于 YCSB 基准测试，与传统 LSM-tree KV 存储（如 RocksDB）对比：

| 场景 | 提升幅度 | 说明 |
|------|---------|------|
| YCSB Skewed Workload | **~2.3x** 吞吐 | Zipfian 分布下，compaction offload 使计算节点资源集中在读写 |
| Scan 操作 | **~22x** 提升 | 大范围扫描受益于存储节点近数据处理和并行 I/O |
| 负载均衡 | 无需 resharding | 计算节点无状态，可水平扩展接管任意 SST 文件 |
| 弹性伸缩 | 计算/存储独立扩展 | 存算分离后各自按需扩缩容 |

## 局限性

1. **FUSE 开销**：FUSE 用户态文件系统引入额外的上下文切换开销（user↔kernel），对小 I/O 场景可能成为瓶颈
2. **元数据一致性延迟**：compaction 完成到计算节点感知文件变更之间存在窗口期，需仔细设计缓存失效策略
3. **网络依赖**：存算分离意味着所有读 I/O 都经过网络，对网络带宽和延迟敏感
4. **复杂性增加**：整体架构相比单体 LSM 存储复杂得多，运维和故障排查难度上升
5. **单点瓶颈**：FUSE 文件系统层可能成为系统瓶颈，需要缓存和预取优化
6. **冷启动问题**：新计算节点需要从远端加载 SST 文件元数据，启动较慢

## 相关概念

- [[LSM-Tree]]：Log-Structured Merge-Tree 基础数据结构
- [[LSM-Tree-合并优化]]：Compaction 策略与优化技术（Tiered/Leveled/Universal）
- [[LSM-tree-KV-Survey-综述]]：LSM-tree KV 存储系统综述

## 延伸阅读

- 论文原始出处：ASPLOS 2020 Proceedings
- 相关系统：Pegasus（ASPLOS 2021, disaggregated storage）、Socrates（AWS, 存算分离数据库架构）
- 对比方向：与 Aurora（shared-storage）、Snowflake（shared-data）等存算分离架构的异同
