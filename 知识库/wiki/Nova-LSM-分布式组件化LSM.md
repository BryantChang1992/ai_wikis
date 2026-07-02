---
type: concept
title: Nova-LSM (分布式组件化 LSM-tree KVS)
aliases: [Nova-LSM, NovaLSM]
sources:
  - title: "Nova-LSM: A Distributed, Component-based LSM-tree Key-value Store"
    authors: "Haoyu Huang, Shahram Ghandeharizadeh"
    venue: "SIGMOD 2021"
    doi: "10.1145/3448016.3457297"
    arxiv: "2104.01305"
    code: "https://github.com/HaoyuHuang/NovaLSM"
tags:
  - LSM-tree
  - 分布式存储
  - RDMA
  - 存算分离
  - KV存储
  - SIGMOD
status: draft
created: 2026-07-02
related:
  - "[[LSM-Tree]]"
  - "[[LSM-Tree-合并优化]]"
  - "[[Hailstorm-存算分离LSM数据库]]"
  - "[[LSM-tree-KV-Survey-综述]]"
---

## 一句话摘要

基于 RDMA 的组件化分布式 LSM-tree KVS：将 LSM-tree 拆解为 **LTC（计算）**、**LogC（日志）**、**StoC（存储）** 三个独立组件，通过存算分离和共享存储池实现弹性横向/纵向扩展。

---

## 核心创新

### 1. 三组件架构（LTC / LogC / StoC）

| 组件 | 全称 | 职责 |
|------|------|------|
| **LTC** | LSM-tree Component | 处理读写请求、维护 LSM-tree、执行 Compaction |
| **LogC** | Logging Component | 生成和恢复 WAL 日志，集成在 LTC 内 |
| **StoC** | Storage Component | 提供变长 Block 接口，管理持久化/内存存储 |

- 三组件通过 **RDMA**（56Gbps InfiniBand）互联
- LTC 与 StoC 之间用专用 **xchg 线程** 管理 QP 连接，最小化 QP 数量（RDMA 在大量 QP 时扩展性差）
- StoC 上的读写操作（RDMA READ/WRITE）**绕过远端 CPU**

### 2. 按 Range 分片 + Drange/Trange 双层地址空间

```
Database → ω×η Ranges → 每个 Range 含 θ 个 Drange → 每个 Drange 含 γ 个 Trange
```

- **Range**：应用可见的分片单元，可跨 η 个 LTC 迁移
- **Drange（Dynamic Range）**：LTC 内部自动构建，对应用透明。按写入负载均衡划分，使得 Level0 SSTable 互不相交，**支持并行 Compaction**
- **Trange（Tiny Range）**：更细粒度的重组织单元，通过跨 Drange 迁移实现 Minor Reorganization
- 热点 Key 对应的 Drange 可**复制多份**（如 `[0,0]` 出现在 Drange 0 和 Drange 1），分配双倍 Memtable

**效果**：
- 避免同一 Key 的多个版本分散在所有 Level0 SSTable 中（解决写停顿）
- 合并唯一 Key < 100 的 Drange → 减少 65% 写入磁盘的数据量
- Drange 是**预防性**方案（vs RocksDB Subcompaction 的检测性方案）

### 3. SSTable 跨 StoC 分片（ρ 参数 + power-of-d）

- 每个 SSTable **不散落在全部 β 个 StoC 上**，而是只散落在 **ρ 个 StoC** 上（ρ ≤ β）
- 不同的 SSTable 整体均匀散落在所有 β 个 StoC
- 选择策略使用 **power-of-d**：从 d = 2×ρ 个随机 StoC 中，选择磁盘队列最短的 ρ 个

**关键参数**：
- ρ = 1（1 个 StoC）：最简单，单盘瓶颈
- ρ = 3 + power-of-6：吞吐量≈ ρ = 10（随机选择），但写入更顺序（HDD 友好，吞吐高 17%）
- ρ 越小 → 单个 SSTable 片段越大 → 顺序写性能越好

### 4. Hybrid 可用性策略（Replication + Parity）

| 方案 | 数据块 | 元数据块 (~200KB) | 空间开销 (ρ=3) | MTTF_Storage (β=10) |
|------|--------|-------------------|----------------|---------------------|
| 无保护 | 无 | 无 | 0% | 13 天 |
| 纯复制 (R=2) | Replication | Replication | 100% | 55.4 年 |
| 纯 Parity | 1 Parity / ρ 块 | 无 | 33% | 30 年 |
| **Hybrid** | 1 Parity / ρ 块 | 3 Replicas | 33% | 30 年 |

- SSTable 不可变 → 无 RAID 更新开销
- Parity 块仅在 StoC 故障时需要读取
- 理想部署：StoC 跨不同机架

---

## 规模扩展能力

### 纵向扩展（内存）

| 内存 | 配置 (α, δ) | W100 吞吐量 |
|------|-------------|------------|
| 32 MB | (1, 2) | 8,924 ops/s |
| 512 MB | (16, 32) | 53,258 ops/s |
| 4 GB | (64, 256) | 246,434 ops/s |

- 32 MB → 4 GB：**吞吐量提升 27.6x**
- 512 MB → 1 GB：吞吐量提升 4x（写停顿从 65% 降至 21%）

### 横向扩展

- **η 个 LTC**：增加计算能力，CPU 密集型工作负载受益
- **β 个 StoC**：增加磁盘带宽，I/O 密集型工作负载受益
- 支持在线增减 LTC/StoC（弹性扩缩容）
  - 加 LTC：迁移 Range 元数据 + 重放 Log Record，最快 570ms
  - 加 StoC：新 SSTable 立即使用，已有副本自动发现

---

## 与单体系统对比

### 10 GB 数据库，单节点

| 工作负载 | LevelDB(ω=1) | LevelDB*(ω=64) | Nova-LSM | 提升倍数 |
|----------|-------------|---------------|----------|---------|
| RW50 Zipfian | 1x (基准) | 5x | 34x | **34x vs LevelDB** |
| W100 Zipfian | 1x | 2x | 17x | 17x |
| SW50 Zipfian | 1x | 13x | 105x | 105x |
| RW50 Uniform | 1x | 1.1x | ~1x | 持平 |
| SW50 Uniform | 1x | 1x | 0.85x | -15%（索引开销） |

### 100 GB - 2 TB，10 节点

- Zipfian 分布：9x–22x 高于 LevelDB*/RocksDB*
- Uniform 分布：持平（页缓存耗尽，随机寻道主导）
- 延迟（RW50 Zipfian）：avg 8ms（vs LevelDB* 55ms），p99 167ms（vs 586ms）

---

## 局限性

1. **CPU 利用率更高**：维护 Lookup Index + Range Index + xchg 线程轮询 → 20-30% 性能退化（CPU 密集型、Uniform 模式）
2. **Zipfian 热 Key 瓶颈**：单个 LTC 的 CPU 成为瓶颈，需配合 Range 迁移才能扩展
3. **写入停顿仍然存在**：虽大幅减少（65%→46%→16%），Level0 大小限制下的写停顿未消除
4. **日志开销**：CPU 满负载时启用日志 → 吞吐量最多降 33%（Zipfian）
5. **StoC 负载不均**：power-of-d 下各 StoC 磁盘利用率存在 76%–93% 的差异
6. **Scan 跨 Drange 开销**：Nova-LSM 一次 Scan 最多搜索 26 个 Memtable，RocksDB* 仅 2 个

---

## 相关概念

- [[LSM-Tree]] — LSM-tree 基本原理与 Leveled Compaction
- [[LSM-Tree-合并优化]] — Compaction 策略优化综述（Dostoevsky 等）
- [[Hailstorm-存算分离LSM数据库]] — 另一种存算分离 LSM 方案（分布式文件系统路线）
- [[LSM-tree-KV-Survey-综述]] — LSM-based Storage 综述（Luo & Carey, VLDB Journal）

---

## 实现细节

- 基于 **LevelDB** 扩展，新增 20,000+ 行 C++ 代码
- 开源地址：`https://github.com/HaoyuHuang/NovaLSM`
- 线程模型：
  - LTC：512 Worker 线程（客户端请求）+ 128 Compaction 线程 + 32 xchg 线程
  - StoC：256 线程（128 用于 Compaction）
- Coordinator：基于 Lease 的 Range/StoC 管理，心跳保活
- 故障恢复：基于 MANIFEST 文件（含 Drange/Trange 元数据），LogC 用 RDMA READ 拉取日志，≤1 秒恢复 4 GB
