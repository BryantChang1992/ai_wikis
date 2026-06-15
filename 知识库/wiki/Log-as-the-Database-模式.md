---
type: concept
title: "Log-as-the-Database 模式"
sources:
  - "sources/papers/RaaS/RaaS-SIGMOD2026.pdf"
  - "sources/papers/RaaS/精读分析.md"
  - "sources/papers/RaaS/全文翻译.md"
tags:
  - Log-as-the-Database
  - 存储计算分离
  - redo-log
  - WAL
  - 数据库架构
  - LSN
created: 2026-06-14
updated: 2026-06-14
status: draft
related:
  - "[[存储计算分离数据库的-Tail-Latency]]"
  - "[[RaaS-Replay-as-a-Service]]"
  - "[[事务模型深度调研]]"
---

# Log-as-the-Database 模式

> **来源**：*Reducing Tail Latency in Storage-Disaggregated Database Systems* — SIGMOD 2026，Purdue University  
> **一句话**：存储计算分离数据库只通过网络传输 redo log，不传数据页——这是架构的核心优势，也是 [[存储计算分离数据库的-Tail-Latency|tail latency]] 的结构性根因。

---

![[diagram/log-as-the-database.svg]]
## 1. 什么是 Log-as-the-Database？

在传统单机数据库中，WAL（Write-Ahead Log）只是持久化的第一站——数据页最终会被刷入磁盘。WAL 是"保险"，不是"真相来源"。

在存储计算分离架构（Aurora、Socrates、AlloyDB、Neon）中，**redo log 上升为唯一的数据传输载体**：

![[diagram/Log-as-the-Database-模式-fig.svg]]


### 核心差异

| 维度 | 传统单机 | Log-as-the-Database |
|------|---------|---------------------|
| 网络传输内容 | 脏页 + WAL | **仅 redo log** |
| 数据页谁产生 | Compute Node 写入 | **Storage Node 异步回放生成** |
| 读请求路径 | 从 buffer pool / disk 读 | 从存储节点读 → 若页未物化 → on-the-fly replay |
| 网络开销 | 高（传完整页） | 低（只传日志，10-100× 更小） |

---

## 2. 为什么这样设计？——优势

### 2.1 网络效率

redo log 比完整数据页小 1-2 个数量级。在云环境中跨 AZ 传输，带宽成本显著降低。

### 2.2 弹性扩缩

计算节点无需关心数据页的物理位置和持久化状态——只需发 log。这使得：
- 计算节点可以快速添加/移除（无状态或轻状态）
- 存储节点独立管理数据生命周期（compaction、garbage collection）

### 2.3 快速恢复

Crash recovery 时只需从最后一个 checkpoint 开始回放 log，无需传输大量数据页。

---

## 3. 代价：不可预测的读延迟

### 3.1 回放链长度差异

存储节点异步回放日志来物化数据页。不同页的回放积压量不同：

| 页状态 | 读延迟 | 原因 |
|--------|--------|------|
| 刚物化完成 | ~1ms | 直接从内存/SSD 读取 |
| 积压 25 条 log | ~50ms | on-the-fly replay 25 条 |
| 积压 272 条 log | ~86ms | replay 272 条 |
| **积压 380 条 log** | **~145ms (tail)** | replay 380 条，且与前台争抢 CPU |

### 3.2 回放与查询的 CPU 冲突

存储节点同时承担两个角色：
1. **前台**：响应读请求（GetPage@LSN），需要 on-the-fly replay
2. **后台**：持续回放积压日志，物化数据页

当 workload burst 时，后台回放吃掉 43% CPU，前台查询只剩 49.4%（参见 [[存储计算分离数据库的-Tail-Latency]]），直接导致 tail latency 暴涨。

---

## 4. 解法思路

### 4.1 在存储层内部优化（效果有限）

| 方案 | 效果 | 问题 |
|------|------|------|
| 提高回放频率 | P99 仅改善 3% | 频繁 cancel + 依然抢 CPU |
| 并行回放（多线程） | **恶化**：P99 +38.3% | 更多线程抢同一颗 CPU |

### 4.2 解耦回放任务（RaaS 方案）

[[RaaS-Replay-as-a-Service|RaaS]] 的核心思路：**承认 log-as-the-database 的 CPU 争抢是结构性的，通过解耦来解决**——把回放任务搬到集群空闲实例上执行。

参见 [[RaaS-Replay-as-a-Service|RaaS 完整方案]]。

---

## 5. 类比：流存储中的 Log-as-the-Database

这个模式在流存储系统中同样存在：

| 概念 | 存储分离数据库 | 分离式 Kafka |
|------|---------------|-------------|
| "log" | redo/WAL log | Kafka log segment |
| "物化" | 回放 log → data page | log → consumer offset state |
| "后台任务" | log replay / compaction | log compaction / segment merge |
| "tail latency 来源" | 回放链长度 + CPU 争抢 | consumer lag spike |

Kafka 的 log compaction 同样是 CPU 密集型的后台任务，在分离式部署中也会与前台 I/O 争抢资源——RaaS 的卸载模式对这类场景有直接参考价值。

---

## 6. Key Takeaways

1. **Log-as-the-database 是存储计算分离的基石**——牺牲读延迟确定性，换取弹性和网络效率
2. **结构性代价不可消除，但可转移**：RaaS 证明，只要把 CPU 密集型回放从热路径上移走，代价就可以大幅降低
3. **这是一个通用模式**：任何"后台物化 + 前台查询"的系统（数据库、流存储、搜索引擎）都可能面临相同问题
4. **设计启示**：架构设计时需明确区分"数据面"和"控制面"——log 是控制面（轻量），data page 物化是数据面（重量），后者应该可以独立调度
