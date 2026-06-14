---
type: concept
title: "LSM-Tree 二级索引 (Secondary Indexing)"
sources:
  - "sources/papers/LSM-Survey/LSM-Survey-VLDBJ2019.pdf"
  - "sources/papers/LSM-Survey/精读分析.md"
  - "sources/papers/LSM-Survey/全文翻译.md"
tags:
  - 存储引擎
  - LSM-Tree
  - 二级索引
  - 数据库
  - 索引维护
created: 2026-06-14
updated: 2026-06-14
status: draft
related:
  - "[[LSM-Tree]]"
  - "[[LSM-Tree-合并优化]]"
  - "[[事务模型深度调研]]"
---

# LSM-Tree 二级索引 (Secondary Indexing)

## 定义

**二级索引** 是指基于非主键列建立的索引，用于加速非主键查询。在 LSM-tree 中维护二级索引是一个核心挑战——因为 LSM-tree 的合并操作会不断重写数据，索引需要随之更新。

## 为什么是核心挑战

LSM-tree 从 KV-store 走向完整数据库存储引擎，二级索引是必须跨越的门槛。核心难点：

1. **合并导致数据位置变化**：compaction 后 key 的物理位置改变，索引指向失效
2. **更新传播延迟**：LSM-tree 的写入是异步合并的，索引可能滞后
3. **多索引一致性**：主键索引和多个二级索引必须在合并后保持一致

## 四个研究方向

### 1. 索引结构 (Index Structures)

| 结构 | 特点 | 适用场景 |
|------|------|---------|
| **LSII** (LSM-based Secondary Index) | LSM-tree 本身就作为二级索引 | 通用 |
| **Filters** | 每个组件记录 filter key 的 min/max 范围 | 时间相关数据特别有效 |
| **R-tree** | 空间索引，适配多维范围查询 | 地理空间数据 |

**Filters 的关键洞察**：如果数据有自然的时间或序列顺序，在 SSTable 的 filter key 上记录 min/max 范围可以快速排除不相关的 SSTable，而不需要完整的 Bloom Filter。

### 2. 索引维护 (Index Maintenance)

这是二级索引最核心的研究方向。**Diff-Index** 提出了四种维护方案的分类：

#### Diff-Index 分类体系

```
维护开销: sync-full > sync-insert > async-simple > async-session
查询性能: sync-full > sync-insert > async-simple > async-session
```

| 方案 | 维护时机 | 维护开销 | 查询开销 | 一致性 |
|------|---------|---------|---------|--------|
| **sync-full** | 每次写入同步更新所有索引 | 最高 | 最低（即时可见） | 强一致 |
| **sync-insert** | 同步追加索引条目（不验证） | 高 | 低 | 最终一致 |
| **async-simple** | 异步批量更新索引 | 中 | 中 | 最终一致 |
| **async-session** | 按会话/批次异步更新 | 最低 | 最高（可能过期） | 最终一致 |

**Trade-off 本质**：维护开销 vs 查询性能的连续取舍——需要根据工作负载（读多写少 vs 写多读少）选择合适方案。

#### Luo & Carey (PVLDB 2019) — Primary Key Index 方案

**被 Survey 认为是最优雅的解法**（Survey 作者本人的后续工作）。

**核心思想**：
- 维护一个 **Primary Key Index**：只存 `key → timestamp`（而非全记录）
- 验证和清理二级索引时，只需查询 primary key index（小），**避免访问全记录**（大）

```
传统方案:
  验证二级索引 → 查询主记录（大 I/O） → 验证一致性

Luo & Carey 方案:
  验证二级索引 → 查询 Primary Key Index（小 I/O） → 验证一致性
                          ↑
              只存 key+timestamp，体积远小于主记录
```

**效果**：
- 二级索引的验证和清理 I/O 大幅降低
- 特别适合写多读少的场景（索引需要频繁验证）
- 主索引体积小，可以常驻内存

#### 其他维护方案

| 方案 | 特点 |
|------|------|
| **DELI** | 延迟清理无效索引条目（类似 Cassandra 本地二级索引），清理滞后 |
| **Diff-Index** | 差分索引——只记录变更部分，定期合并到主索引 |

### 3. 统计信息 (Statistics)

**Absalyamov 轻量统计**：在合并过程中顺便收集统计信息（基数估计、值分布等），用于查询优化器。

**挑战**：统计信息本身也会因合并而过时，需要额外的维护策略。

### 4. 分布式二级索引

| 类型 | 特点 | 挑战 |
|------|------|------|
| **全局二级索引** | 跨所有分片统一索引 | 写入需跨分片协调（类似 2PC） |
| **本地二级索引** | 每个分片独立索引 | 查询需 scatter-gather 所有分片 |

**与分布式事务的关系**：全局二级索引维护在分布式环境下类似分布式事务（参见 [[事务模型深度调研]]），需要两阶段提交或类似机制保证一致性。

## 与其他 LSM 优化的关联

| 优化方向 | 关联 |
|----------|------|
| [[LSM-Tree-合并优化]] | 关联合并（correlated merge）需要同步所有二级索引 |
| [[LSM-Tree-硬件适配]] | 多核并行合并可以并行维护多个二级索引 |
| [[LSM-Tree-自动调参]] | 索引维护策略选择应该根据负载自动决定 |

## 未来方向

1. **自适应索引维护**：根据查询模式动态选择 sync/async 策略
2. **LSM-aware 查询优化器**：利用 LSM-tree 的多层结构特性优化查询计划
3. **多索引场景下的合并优化**：多个二级索引同时维护的协调和优化

---

*参考论文: Luo & Carey, "LSM-based Storage Techniques: A Survey", VLDB Journal 2019*
