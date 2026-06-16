---
type: concept
title: "Raft 日志压缩"
sources:
  - "sources/papers/Raft-Dissertation/精读分析.md"
tags:
  - 分布式系统
  - 共识算法
  - Raft
  - 日志压缩
  - 快照
created: 2026-06-16
updated: 2026-06-16
status: stable
related:
  - "[[Raft-共识算法协议核心]]"
  - "[[LSM-Tree-合并优化]]"
---

# Raft 日志压缩

## 定义

**Raft 日志压缩（Log Compaction）** 是 Raft 共识协议处理日志无限增长的机制——通过将状态机快照（Snapshot）替代前缀日志，使日志大小收敛到有限范围内，保证系统长期运行而不会因日志膨胀耗尽存储。这是 Ongaro 博士论文 Ch 9 的核心内容，也是将 Raft 从"协议层正确"推向"工程层可用"的关键组件。

## 问题：日志无限制增长

Raft 的正常运行依赖 **Log Replication**——Leader 接收客户端命令并作为日志条目追加到本地日志，而后通过 AppendEntries RPC 复制到 Followers。在长期运行的系统中，这产生两个致命问题：

### 1. 存储膨胀

- 每个日志条目都需持久化到磁盘，日志文件随时间线性增长
- 一个长运行集群可能积累 GB-TB 级别的历史日志
- 日志重放恢复（replay）的耗时与日志长度成正比——重启或新节点加入时，需要重放全部历史日志到达当前状态

### 2. 新节点启动不可行

新 Follower 启动时需要接收并重放全部历史日志。对于运行数年的集群，重放整条日志可能需要数小时甚至数天——在此期间新节点无法提供服务，甚至可能永远追不上 Leader 的写入速度。

> 没有日志压缩的 Raft，本质上不支持无限期连续运行，也不支持节点动态加入。

## Snapshot 机制：用状态机快照替代前缀日志

Raft 的日志压缩核心方案是 **Snapshot**：对状态机的当前状态做一次完整快照，然后用该快照替代所有已应用的前缀日志。

### 核心思想

```
Before Snapshot（日志累积累积）:
日志条目:  [1] [2] [3] ... [1000] [1001] [1002] [1003]
状态机:    S0 → S1 → S2 ... S1000 → S1001 → S1002 → S1003

After Snapshot（快照替代前缀）:
快照 (index=1002, term=7): [S1002 完整状态]
日志条目:                            [1003]
状态机:                              S1002 → S1003
```

快照覆盖到 `lastIncludedIndex`，包含 `lastIncludedTerm`，其后的日志条目从 `lastIncludedIndex + 1` 继续编号。日志元数据连续，但快照之前的存储空间已被回收。

### 快照的内容

| 内容 | 说明 |
|------|------|
| **状态机状态** | 当前状态机的完整序列化表示（如 Key-Value store 的全部数据） |
| **Last Included Index** | 快照覆盖的最后一个日志条目的 index |
| **Last Included Term** | 快照覆盖的最后一个日志条目的 term |
| **集群配置** | 快照对应时刻的集群成员配置（可选，但强烈建议包含） |

### 谁负责创建快照？

> **每个服务器独立创建自己的快照**——不是 Leader 统一生成再分发。

每个节点（包括 Leader 和 Followers）在已应用的日志前缀达到一定大小或条目数时，自行触发快照创建。原因：

- 解耦快照与 Leader 角色——Leader 不做中心化瓶颈
- 允许不同节点根据磁盘压力独立决策
- 简化设计：快照是纯本地操作，不涉及共识

## InstallSnapshot RPC：向落后节点传输快照

### 动机

当 Leader 需要向某个 Follower 复制日志，但对应前缀日志已被 Leader 自己的快照替代时，AppendEntries RPC 失效——Leader 的磁盘上已经不存在这些日志条目。此时 Leader 通过 **InstallSnapshot RPC** 将快照发送给落后的 Follower。

### RPC 协议定义

InstallSnapshot 是一个分块传输协议，支持快照内容的流式发送：

| 参数 | 说明 |
|------|------|
| `term` | Leader 的当前 term |
| `leaderId` | Leader 的标识，供 Follower 重定向客户请求 |
| `lastIncludedIndex` | 快照覆盖的最后一个日志条目的 index |
| `lastIncludedTerm` | 快照覆盖的最后一个日志条目的 term |
| `offset` | 本次传输块在快照文件中的字节偏移量 |
| `data[]` | 本次传输的快照数据块 |
| `done` | 如果为 true，表示这是最后一块 |

### 交互流程

```
Leader                               Follower
  |                                      |
  |-- InstallSnapshot RPC (chunk 0) ---->| 1. 检查 term；创建临时文件
  |-- InstallSnapshot RPC (chunk 1) ---->| 2. 追加写入临时文件
  |-- ...                                |
  |-- InstallSnapshot RPC (last chunk) ->| 3. done=true → 应用快照
  |                                      |      - 丢弃 ≤ lastIncludedIndex 的前缀日志
  |                                      |      - 保存快照文件
  |                                      |      - 状态机重置为快照状态
  |<---- Response -----------------------| 4. 返回最后一条快照数据的 offset
```

### Follower 端处理

当 Follower 收到 InstallSnapshot 请求时：

1. **Term 检查**：如果 `term < currentTerm`，立即拒绝
2. **快照覆盖检查**：如果 `lastIncludedIndex ≤ commitIndex`，快照冗余——忽略
3. **接收数据块**：将 data 写入临时文件，按 offset 偏移量
4. **完成**（`done == true`）：
   - 原子替换旧快照文件（如果存在）
   - **丢弃所有 ≤ lastIncludedIndex 的前缀日志条目**
   - 使用快照重置状态机
   - 使用快照中的集群配置（如果包含）
   - 保留 > lastIncludedIndex 的后缀日志继续用于正常复制

### 为什么保留了后续日志？

```text
Follower 状态（收到快照前）:
日志:  [1...500] ← 与 Leader 一致
快照: 无

Follower 状态（收到快照 lastIncludedIndex=500 后）:
快照:  [1...500 状态]
日志:  []         ← 丢弃，已被快照替代

另一种场景——Follower 日志比快照多：
Follower 状态（收到快照前）:
日志:  [1...500] [501] [502] ← 501-502 未被 Commit
快照:  无

Follower 状态（收到快照 lastIncludedIndex=500 后）:
快照:  [1...500 状态]
日志:  [501] [502]           ← 保留，因为 > lastIncludedIndex
```

后续的 AppendEntries RPC 在快照基础上继续复制，一致性由 Log Matching Property 保证。

## 增量快照 vs 全量快照的权衡

Ongaro 在论文 Ch 9 中讨论了两种快照策略，最终在标准 Raft 中采用**全量快照**，但为增量方式预留了设计接口。

### 全量快照（Full Snapshot）

| 优点 | 缺点 |
|------|------|
| ✅ 实现简单，无依赖链 | ❌ 每次传输整个状态，状态大时开销高 |
| ✅ 无版本兼容性问题 | ❌ 存储空间需求与状态大小成正比 |
| ✅ 快照独立，可任意删除旧快照 | ❌ 传输大快照阻塞新节点启动 |
| ✅ 故障恢复简单——只需加载最近的快照 | ❌ 频繁快照产生写放大 |

**适用场景**：状态机状态相对紧凑（几 MB 到几百 MB）、写入密集度适中。

### 增量快照（Incremental Snapshot）

| 优点 | 缺点 |
|------|------|
| ✅ 每次只传输变化部分 | ❌ 实现复杂——需要 diff 算法和 delta 格式 |
| ✅ 传输和存储开销小 | ❌ 存在依赖链——恢复时需要从 base 逐次应用 delta |
| ✅ 支持高频快照 | ❌ delta 累积过多时也需要 merge（类似 Compaction） |
| | ❌ 版本兼容性挑战——不同节点可能处于不同的 delta 链 |

**论文中的定位**：Ongaro 明确预留了增量接口（`offset` 参数的分块设计天生支持增量传输），但指出全量快照"已经足够实用"。实际生产系统中，CockroachDB 的 Range Snapshot 采用了类似增量的分层方案。

### 工程选择建议

| 状态规模 | 推荐策略 |
|----------|----------|
| < 100 MB | 全量快照，直接传输 |
| 100 MB - 1 GB | 全量快照 + 压缩传输 |
| > 1 GB | 增量快照 或 外部 Snapshot 机制（如 CockroachDB 的 SST-based） |
| > 10 GB | 必须增量 + 分层快照 + 外部存储介质 |

## 快照对性能的影响和工程实践

### 性能影响分析

#### 1. 快照创建期间的资源竞争

快照创建是一个**计算密集型 + IO 密集型**的操作：

| 资源 | 影响 |
|------|------|
| **CPU** | 状态机序列化（如 KV store 的遍历 + 编码） |
| **内存** | 快照缓冲（Copy-on-Write 技术的 fork 开销） |
| **磁盘 IO** | 快照文件写入（可能几十 MB 到几 GB） |
| **写入延迟** | 快照期间的 AppendEntries 处理必须继续，可能产生竞争 |

论文特别指出：**Log Compaction 与正常操作的资源竞争是 Raft 设计中未充分解决的问题**。后续 Etcd 通过 Copy-on-Write + 异步写盘缓解了此问题。

#### 2. InstallSnapshot 的网络冲击

- 大快照（GB 级）传输会占用大量网络带宽
- 可能拖慢正常的 AppendEntries RPC（心跳和日志复制）
- 同时向多个落后节点发送快照时出现**广播风暴**

#### 3. 快照的写放大

频繁创建快照会导致：
- 状态机内容被反复序列化写入磁盘（写放大）
- 如果快照未被使用（没有落后节点需要），则纯属浪费

### 工程最佳实践

| 实践 | 说明 | 参考实现 |
|------|------|---------|
| **阈值触发** | 日志条目数或日志字节数超过阈值才触发，而非周期性全量 | etcd `--snapshot-count`（默认 100000 条） |
| **异步快照** | 快照创建在后台线程执行，不影响 Raft 帧框主循环 | Etcd / TiKV |
| **Copy-on-Write** | 利用 fork + COW 避免快照期间锁住状态机 | Etcd（Linux fork 语义） |
| **压缩传输** | InstallSnapshot 数据块经 gzip/lz4/snappy 压缩 | TiKV（lz4） |
| **流控与限速** | Leader 限制并发 InstallSnapshot 数量和每个快照的传输带宽 | CockroachDB（snapshot rate limiter） |
| **外部快照存储** | 快照文件存储到对象存储（S3/GCS），减少本地磁盘压力 | TiKV（BR/TiFlash） |
| **分层快照** | 先传输 base 快照，再追加 delta，类似 LSM Compaction | CockroachDB Range Snapshot |
| **定期清理旧快照** | 保留最近 N 个快照，清理无用快照 | etcd（自动 GC） |

### 典型实现对比

| 系统 | 快照策略 | 触发条件 | 传输方式 |
|------|----------|----------|----------|
| **etcd** | 全量 + COW | `snapshot-count` 条日志 | HTTP Range GET 分块 |
| **TiKV** | 全量（RocksDB snapshot） | log gap > threshold | gRPC 流式 + lz4 压缩 |
| **CockroachDB** | 分层增量（SST-based） | Range 大小超限 | gRPC 流式 + 速率限制 |
| **Consul** | 全量（raft-boltdb） | snapshot-interval | TCP 流式 |
| **NATS JetStream** | 全量 | 文件大小阈值 | 内建 RPC |

## 与 LSM-Tree Compaction 的概念类比

Raft Log Compaction 和 LSM-Tree Compaction 虽运行在完全不同的层级（共识 vs 存储引擎），但设计思想有相似之处：

| 维度 | Raft Log Compaction | LSM-Tree Compaction |
|------|---------------------|---------------------|
| **核心目标** | 回收前缀日志空间、加速恢复 | 回收 SST 文件空间、加速查询 |
| **压缩对象** | 日志条目 → 状态机快照 | 多层 SST → 单层大 SST |
| **触发策略** | 日志大小/条目数阈值 | 层级大小超限 |
| **增量方案** | delta snapshot（论文预留） | Leveled / Tiered Compaction |
| **写放大** | 频繁快照产生写放大 | 写放大是 LSM 的核心取舍 |
| **恢复加速** | 快照减少重放长度 | Compaction 减少读放大 |

> Raft 的 Snapshot 本质上是将日志的"增量表示"转换为状态机的"全量表示"，这与 LSM 将多个小 SST 合并为单一大 SST 的逻辑一致。两者都是**用一次性计算开销换取长期存储和恢复效率**。

## 总结

| 维度 | 要点 |
|------|------|
| **为什么需要** | 日志无限增长 → 存储耗尽、新节点启动不可行 |
| **怎么做** | 状态机快照替代前缀日志，每个节点独立执行 |
| **如何同步** | InstallSnapshot RPC 分块传输快照到落后 Follower |
| **全量 vs 增量** | Raft 原生用全量；增量是为大状态预留的优化方向 |
| **工程要点** | 异步创建、COW、压缩传输、流控限速、外部存储 |

---

*核心来源: Ongaro, D. (2014). CONSENSUS: BRIDGING THEORY AND PRACTICE — Chapter 9: Log Compaction. Stanford University Ph.D. Dissertation.*
