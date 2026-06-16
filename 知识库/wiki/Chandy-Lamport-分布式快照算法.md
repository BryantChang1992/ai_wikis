---
type: concept
title: "Chandy-Lamport 分布式快照算法"
sources:
  - "sources/papers/Chandy-Lamport-Snapshot/精读分析.md"
tags:
  - 流处理
  - 分布式系统
  - 快照
  - 一致性
  - 容错
  - Flink
created: 2026-06-16
updated: 2026-06-16
status: stable
related:
  - "[[流处理容错模型]]"
  - "[[流处理状态管理]]"
  - "[[Dataflow-Model]]"
---

# Chandy-Lamport 分布式快照算法

## 定义

**Chandy-Lamport 算法**（1985）是分布式快照问题的开山之作——在无全局时钟的分布式系统中，通过进程状态 + 通道状态的协同记录，在不停止系统运行的情况下捕获一个**一致的全局状态**（consistent global state）。2013 年获 ACM SIGOPS Hall of Fame Award，被引用超过 5000 次，是 Flink Checkpoint 机制的理论基石。

## 问题背景

分布式系统面临一个根本性困难：**没有全局时钟**，各进程无法在同一个时间点"同时"记录自己的状态。朴素做法（各自同时拍照）产生的快照无法保证一致性。

### 什么算"一致"的快照？

> 快照对应一个**一致性切割**（Consistent Cut）：对于任意进程 p 和 q，如果 p 在快照中记录了收到来自 q 的消息 m，则 q 在快照中**也记录了发送 m 的事件**。

通俗理解：快照不能出现"消息已收到但还没发出"的因果倒置——那对应一个实际不可能发生的系统状态。

### 稳定属性检测

论文的核心动机之一是**稳定属性**（Stable Property）检测——一旦为真就永远保持真的属性，例如：
- 系统是否死锁？
- 计算是否终止？
- 是否存在资源泄漏？

如果能捕获一个一致快照，就可以在快照上安全地检测这些属性：如果快照中某稳定属性为真，则分布式系统在某个历史时刻确实进入了该状态。

## 算法模型

### 系统形式化

- 分布式系统建模为有向图 `G = (V, E)`
- `V` = 进程集合，每个进程有自己的本地状态
- `E` = 单向 FIFO 通道集合，每条通道上有一列正在传输的消息序列
- **全局状态** = `Σ(所有进程状态)` + `Σ(所有通道状态)`

### 关键假设

| 假设 | 说明 |
|------|------|
| **FIFO 通道** | 消息在通道上按发送顺序到达（原始算法依赖此假设） |
| **强连通** | 进程图是强连通的（任意两进程间存在有向路径） |
| **通道无限缓冲** | 通道不会丢消息（传输可靠） |
| **进程无故障** | 快照期间进程不会崩溃（后续工作扩展了容错支持） |

## 算法步骤：Marker 传播机制

算法的核心创新是 **marker（标记）消息**——它充当逻辑时钟，将全局状态切割点传播到所有进程。算法分两个阶段：

### Phase 1：启动（Initiator）

任意进程 p 启动快照：

1. **记录本地状态**：p 立即记录自己的当前状态
2. **发送 marker**：p 在记录完本地状态后，向每个**出边通道**发送一个 marker 消息
3. **开始监听入边通道**：p 开始记录每个**入边通道**上到达的消息（作为通道状态）

### Phase 2：传播（Non-Initiator）

进程 q 的行为分为两种情况：

**情况 A — 首次从通道 c 收到 marker（进入切割边界）：**

1. **记录本地状态**：q 立即记录自己的当前状态
2. **通道 c 的状态设为空**：因为 marker 是 c 上记录的第一条消息，说明 c 在 q 快照之前没有 in-flight 消息
3. **传播 marker**：q 向每个**出边通道**发送 marker
4. **开始监听其他入边通道**：q 开始记录所有**其他入边通道**上到达的消息（等待对应 marker 到来）

**情况 B — 后续从通道 c' 收到 marker：**

- **停止记录通道 c'**：q 停止记录 c'，将期间收到的消息序列作为 c' 的通道状态

### 算法终止

当所有进程都记录了本地状态，且所有通道的状态都已记录，快照完成。

### 直观理解

```
时刻线：  进程A -------●--------------
                      | (marker)
进程B ---------------●--------------

● = 快照切割点
marker 将切割线"传染"到其他进程
通道状态 = 切割点之间已经发出但尚未收到的 in-flight 消息
```

## 核心定理

> "The global state recorded by the algorithm is a possible global state of the system during the computation."
> — Chandy & Lamport, 1985

这一定理证明了两点：

1. **存在性**：算法总能产出某个合法全局状态——不是虚构的
2. **可达性**：存在某个合法的系统执行序列，使系统确实经过该状态

换句话说，Chandy-Lamport 快照不是"近似"或"估计"，而是严格的**一致性切割**：快照所展示的全局状态，是系统在某个历史时刻的真实现照（虽然具体是哪个墙上时钟时刻我们无法定义）。

### 正确性直觉

- Marker 沿通道传播时，将各进程的"快照时刻"串成一条因果一致的切割线
- 任何越过切割线的消息（发送在切割前、接收在切割后）都会被捕获为**通道状态**
- 任何在切割线内部的消息（发送和接收都在同侧）不会被重复或遗漏

## 应用场景

### 1. 死锁检测（Deadlock Detection）

- **动机**：死锁是稳定属性——一旦死锁，直到外部干预才会解除
- **方法**：定期触发快照 → 在快照上构建等待图（Wait-For Graph）→ 检测环
- **保证**：如果快照中存在环，则系统在某个时刻确实存在死锁；如果快照中无环，则系统在快照时刻无死锁

### 2. 终止检测（Termination Detection）

- **动机**：分布式计算是否已全部完成？
- **方法**：快照中所有进程状态均为 idle + 所有通道为空 → 计算已终止
- **注意**：终止判定需要快照的全局一致视图，单独的进程无法判断

### 3. Checkpoint（检查点 / 恢复点）

- **动机**：故障后需要恢复到一致状态继续执行
- **方法**：将 Chandy-Lamport 快照作为分布式 Checkpoint
- **恢复**：所有进程回滚到快照状态，通道状态作为重放输入

### 4. 分布式调试（Distributed Debugging）

- 在一致快照上检查全局断言（global predicate）
- 回溯历史状态，定位 bug 的根因状态

### 5. 分布式垃圾回收（Distributed Garbage Collection）

- 识别不再可达的分布式对象
- 快照提供安全回收的全局视图

## 与 Flink Checkpoint 的关联

Flink 的 Checkpoint 机制本质上是 Chandy-Lamport 算法的**工程化实现**。概念映射如下：

| Chandy-Lamport | Flink Checkpoint |
|---|---|
| Marker 消息 | **Checkpoint Barrier**（通过 JobGraph 注入） |
| 进程状态快照 | **Task State Snapshot**（StateBackend：RocksDB/Heap） |
| 通道状态 | **In-flight Records**（Channel 对齐后持久化到 Checkpoint） |
| 稳定属性 | **Exactly-Once 语义**下的恢复点 |
| 多快照并发 | 分布式快照 + **Checkpoint ID** 对齐 |
| FIFO 通道假设 | Flink 默认保证通道内 Barrier 有序 |

### Flink 的工程化增强

| 维度 | 原始算法 | Flink 实现 |
|------|---------|-----------|
| **Barrier 对齐** | Marker 后停止接收 | Barrier 对齐（阻塞式/非阻塞式） |
| **状态持久化** | 未定义 | StateBackend（RocksDB 增量快照） |
| **故障恢复** | 不支持 | 进程崩溃后从最近 Checkpoint 恢复 |
| **异步快照** | 同步阻塞 | 异步状态快照（Asynchronous Barrier Snapshotting） |
| **Unaligned Checkpoint** | 不支持 | Flink 1.11+ 非对齐 Checkpoint，减少反压下的对齐延迟 |

### Barrier 对齐的经典场景

```
Source ──▶ Map(A) ──▶ KeyBy ──▶ Window(B)
            │                    │
            ▼                    ▼
         barrier              barrier

B 的入边有两个通道：来自 A 的 barrier 先到 → B 阻塞该通道，
等待另一个通道的 barrier 到达后，B 才执行快照。
在此期间阻塞通道上的数据被记录为通道状态。
```

## 局限性

| 局限 | 说明 | 解决方案 |
|------|------|---------|
| **FIFO 依赖** | 原始算法要求通道 FIFO | Lai-Yang 算法通过消息染色/日志放宽此假设 |
| **快照开销** | In-flight 消息量大时快照体积大 | 异步快照、增量快照 |
| **Marker 开销** | 大规模系统中 Marker 传播延迟不可忽略 | 分层快照、部分快照 |
| **无容错** | 不考虑进程崩溃 | "Distributed Snapshots in Spite of Failures" 扩展 |

## 影响力时间线

- **1985**：Chandy & Lamport 发表原论文（ACM TOCS Vol.3 No.1）
- **~2008-2010**：MillWheel/Storm 等 1st Gen 流处理系统采用类快照的容错机制
- **2013**：获 **ACM SIGOPS Hall of Fame Award**
- **2015**：Flink 正式基于 Chandy-Lamport 实现分布式 Checkpoint
- **2016-2020**：Flink 引入异步快照、增量快照、Unaligned Checkpoint 等工程改进
- **至今**：被 Apache Flink、Google Dataflow、Spark Structured Streaming 等主流系统采纳为容错理论基础

---

*核心论文: Chandy, K. M., & Lamport, L. (1985). Distributed snapshots: Determining global states of distributed systems. ACM TOCS, 3(1), 63-75.*
*DOI: 10.1145/214451.214456*
