---
type: concept
title: "ByteHouse 统一表引擎 — 两阶段写入与多模态存储"
sources:
  - "sources/papers/ByteHouse/ByteHouse-SIGMOD2026.pdf"
  - "sources/papers/ByteHouse/精读分析.md"
tags:
  - ByteHouse
  - 存储引擎
  - 统一表引擎
  - Sniffer
  - CrossCache
  - NexusFS
  - MVCC
  - Compaction
created: 2026-06-15
updated: 2026-06-15
status: draft
related:
  - "[[ByteHouse-架构与设计]]"
  - "[[ByteHouse-多模态查询优化]]"
  - "[[Log-as-the-Database-模式]]"
  - "[[LSM-Tree]]"
  - "[[Doris-Compaction-策略]]"
diagram: "diagram/bytehouse-architecture.svg"
---

# ByteHouse 统一表引擎

## 定义

ByteHouse 的 Unified Table Engine 将结构化 OLAP、增量刷新、多模态检索统一到同一个存储引擎中，提供一致的表模型、统一元数据和事务可见性。

## 逻辑表设计 — Document/Chunk 两级抽象

![[diagram/bytehouse-doc-chunk.svg]]

- 复合主键: `(document_id, chunk_id)`
- 同一个表中既有结构化列（数值/字符串）又有向量列（embedding）
- 排序键：范围裁剪（扫描） + 低延迟点查（向量检索）

## 物理表设计 — Stable + Delta Segment

| 段类型 | 内容 | 特点 |
|--------|------|------|
| Stable Segment | 不可变列式数据 | 扫描优化，定期更新 |
| Delta Segment | 最近写入/更新/特征刷新 | 增量追加，频繁操作 |

**MVCC 版本控制**：
- 查询读一致性快照，不受后台刷新干扰
- 后台异步 Compaction 将 delta 合并到 stable
- Adaptive Compaction Controller：公式控制压缩强度

## 自适应 Compaction 控制

```
α = min(1, max(0, k · (N_Δ / N* - 1)))

- N_Δ: 活跃 delta segment 数量
- N*: 平衡状态阈值
- k: 灵敏度系数
- α: 压缩强度 [0,1] → 决定触发频率、批次大小、调度优先级
```

α 低 (N_Δ ≈ N*) → 保守压缩，避免 write amplification
α 高 (N_Δ >> N*) → 激进压缩，恢复扫描局部性
线性单调控制 → 平滑过渡，防止振荡

## 两阶段写入流水线

```
写入 → staging (ByteKV, row-oriented) → flush → columnar storage
  1. 暂存到分布式 KV                            2. 达到阈值/时间后转列存
```

- Staging 阶段：WAL 保证持久化 + 原子性
- Flush 阶段：schema evolution + 版本可见性保留
- 与 [[Log-as-the-Database-模式]] 思路一致：先写 WAL 再物化

## Sniffer 自描述文件格式

- 数据、索引（Min-Max/Bloom）、元数据 **colocate 在同一文件中**
- 消除外部元数据依赖（对比 Iceberg manifest/Snowflake FDN）
- **关键优势**：点查路径单次 I/O 完成 data+index+metadata 读取

## CrossCache — SSD 集群缓存

- 独立扩缩容的 SSD 缓存层
- Chunk 粒度分片，一致性哈希路由
- Prefetching + 异步刷写
- 闭合存算分离 vs. 数据局部性的性能差距

## NexusFS — 虚拟文件系统

统一访问三种存储后端：
- 本地 SSD（最佳延迟）
- CrossCache 节点（中等延迟，共享缓存）
- TOS/HDFS 对象存储（最大容量）

Alignment-aware region management + buffer 编排。

## 与 LSM-Tree 和 Doris Compaction 的比较

| 维度 | ByteHouse | Doris (MOB) | LSM-Tree |
|------|-----------|-------------|----------|
| 写路径 | staging KV → flush | 内存 MemTable → flush | MemTable → SST |
| 读路径 | stable segments 直接读 | base + delta 合并读 | 多层 SST 合并 |
| Compaction | 自适应 α 控制 | 调度触发 | 层级/通用合并 |
| 唯一性 | 多模态统一表 | 数据模型 (D/A/U) | 纯 KV |
