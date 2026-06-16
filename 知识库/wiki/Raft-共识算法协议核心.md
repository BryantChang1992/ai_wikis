---
type: concept
title: "Raft 共识算法协议核心"
sources:
  - "sources/papers/Raft-Dissertation/精读分析.md"
tags:
  - 分布式系统
  - 共识算法
  - Raft
  - 一致性
created: 2026-06-16
updated: 2026-06-16
status: stable
related:
  - "[[Paxos-理论到实践的鸿沟]]"
  - "[[Raft-集群成员变更]]"
  - "[[Raft-日志压缩]]"
  - "[[Raft-客户端交互]]"
  - "[[CockroachDB-Leader-Lease-整体设计]]"
  - "[[分布式数据系统一致性体系]]"
---

# Raft 共识算法协议核心

## 定义

**Raft** 是 Diego Ongaro 在 John Ousterhout 指导下完成的博士论文中提出的共识算法，其核心设计目标是 **Understandability（可理解性）优先**。Raft 通过**问题分解**将共识拆解为三个相对独立的子问题——Leader Election、Log Replication、Safety——并用强 Leader 模型、随机化选举超时、Joint Consensus 等机制，构建了第一个被社区广泛正确实现的共识协议。论文于 2014 年发表，被引用超过 15000 次，是 etcd、TiKV、CockroachDB、Consul、Kafka KRaft 等主流分布式系统的共识引擎理论基础。

## 设计哲学：Understandability First

Ongaro 的核心洞察是：**共识算法的可理解性本身就是一项核心需求**，因为它直接影响实现正确性、社区采纳和生态繁荣。Paxos 虽在理论上优雅，但工程实践中每个实现都在"自行补全"论文未约定的部分，导致实现碎片化。

### 三个设计原则

| 原则 | 含义 | 在 Raft 中的体现 |
|------|------|-----------------|
| **问题分解（Decomposition）** | 将共识拆分为独立子问题 | Leader Election / Log Replication / Safety 三模块各自独立设计和验证 |
| **状态空间缩减（State Space Reduction）** | 减少可能的协议状态数量 | 强 Leader 模型——日志单向流动，避免多 Leader 写入冲突 |
| **确定性与随机化分离** | 只在必要处引入随机 | 随机化仅出现在 Election Timeout，其余全部确定 |

> "Raft is similar in many ways to existing consensus algorithms (most notably, Oki and Liskov's Viewstamped Replication), but it has several novel features: Strong leader, Leader election uses randomized timers, Membership changes use a new joint consensus approach." — Ongaro, 2014

## 三态模型

Raft 将每个 server 在任意时刻映射到三种角色之一，角色间通过规则转换：

```
        超时，开始选举
  Follower ────────────▶ Candidate
      ▲                     │
      │   发现 Leader       │ 赢得选举
      │   或更高 Term       │
      │◀────────────────────┘
      │                     
      │   发现更高 Term     
  Leader ──────────────────▶ Follower
```

### 角色定义

| 角色 | 行为 | 数量 |
|------|------|------|
| **Follower** | 被动响应 Leader 的 AppendEntries RPC 和 Candidate 的 RequestVote RPC。不主动发起任何请求 | N-1 |
| **Candidate** | 发起选举（RequestVote），争取成为 Leader。如果超时未赢得多数票或发现更高 Term，回退到 Follower | 0 或 1（选举期间） |
| **Leader** | 处理所有客户端请求，通过 AppendEntries 复制日志，通过心跳维持权威 | 至多 1 |

关键约束：**同一 Term 内至多一个 Leader**（Term 递增 + 多数派投票确保）。

## Leader Election（Ch 5）

### Term — 逻辑时钟

Term 是全局递增的逻辑时钟，每个 server 持久化当前 Term。Term 的作用：

- **检测过期信息**：收到小于当前 Term 的请求 → 拒绝
- **防止多 Leader**：同一 Term 只有赢得多数票的 Candidate 才能成为 Leader
- **自动降级**：收到更高 Term 的消息 → 自动切换到 Follower

### 选举流程

1. **超时触发**：Follower 在 `Election Timeout`（典型 150ms-300ms 随机区间）内未收到 Leader 心跳 → 转为 Candidate
2. **Term 递增**：Candidate 将 currentTerm +1，投票给自己
3. **并行请求**：向所有其他 server 发送 `RequestVote` RPC（含最后一个日志条目的 index 和 term）
4. **计票**：每个 server 在每个 Term 只投一票（先到先得）
5. **三种结果**：

| 结果 | 条件 | 行为 |
|------|------|------|
| 赢得选举 | 获得多数票 | 转为 Leader，立即发送心跳 |
| 发现更高 Term | 收到 AppendEntries（来自合法 Leader） | 回退为 Follower |
| Split Vote | 超时未获多数票（无 server 赢得多数） | 递增 Term，重新选举 |

### 随机超时 — 降低 Split Vote 概率

**Split Vote** 是选举失败的主因：多个 Candidate 几乎同时超时，平分选票。Raft 通过**随机化 Election Timeout**（150-300ms）使不同 server 的超时时间错开，大幅降低 Split Vote 概率。如果 Split Vote 仍然发生，每个 Candidate 重新随机化超时后重试——由于随机化独立，第二次 Split Vote 概率极低。

### 为什么需要随机化？

确定性系统无法保证在 Split Vote 后自动收敛：如果所有 server 每次失败后重试间隔相同，则可能无限次 Split Vote。**随机化打破了对称性，保证概率为 1 的收敛**——这正是 Raft 在正确性和可理解性之间找到的优雅平衡点。

## Log Replication（Ch 6）

### 强 Leader 模型

Raft 采用**强 Leader 模型**：所有日志条目**只从 Leader 流向 Followers**，单向无环。与 Multi-Paxos 的"多 Proposer 可并发提议"不同，Raft 完全消除了并发写入的冲突处理——客户端请求总是走 Leader。

### 日志结构

```
Index:   1     2     3     4     5     6     7
Term:    1     1     2     2     3     3     3
Cmd:   [SET] [ADD] [DEL] [SET] [SET] [ADD] [SET]
       ──────────────────┬─────────────────────
                    committed     uncommitted
```

日志条目 = `(index, term, command)`。Leader 通过 `AppendEntries` RPC 将日志条目批量推送到 Followers。

### Log Matching Property（日志匹配性质）

> 如果两个日志在相同 index 和 term 有相同的条目，则所有 index 小于该位置的条目都相同。

这一性质由 `AppendEntries` 的**一致性检查**保证：每次 AppendEntries 携带前一个条目的 `(prevLogIndex, prevLogTerm)`，Follower 只有在本地日志匹配此前置条目时才接受新条目；否则拒绝，Leader 回退 `nextIndex` 重试，直至找到匹配点。

**意义**：Log Matching Property 是 Raft Safety 的基础——它保证了 Leader 变更时不会破坏日志一致性。

### Commit 机制

条目被 Commit 的过程：

1. Leader 将条目复制到多数 server（该条目 + 所有前置条目都已被多数 server 存储）
2. Leader 递增 `commitIndex`
3. 下一次 AppendEntries 携带新的 `leaderCommit`，告知 Followers 哪些条目已被 Commit
4. 各 server 的 State Machine 按日志顺序 apply committed 条目

> **关键约束（5.4.2 节）**：Leader 不能直接通过计数副本来提交**前任 Term 的条目**——只能通过提交自己 Term 的条目间接触发前任条目的提交。这防止了 Leader 变更时已提交条目的回滚。

## Safety（Ch 7）

### Election Restriction（选举限制）

Candidate 的日志必须**至少和多数 server 一样新**，否则不能赢得选举。日志"新旧"比较规则：

1. 比较最后一个条目的 Term：Term 大的更新
2. Term 相同时：Index 大的更新

这条规则保证了**所有已 Commit 的条目一定会被新 Leader 包含**——因为 Commit 需要多数派确认，而赢得选举也需要多数派投票，两个多数派必有交集，交集必然包含最新日志。

### Commitment of Previous Terms（前任 Term 的提交）

这是 Raft 最容易被实现错误的细节之一：

> Leader 不直接通过计数副本来提交前任 Term 的条目，而是**等自己 Term 的某个条目被 Commit 后，间接将之前所有条目一并 Commit**。

**原因**：如果 Leader 直接 Commit 前任 Term 的条目，在 Leader 变更时可能出现已 Commit 条目被覆盖的故障场景（Figure 8 是经典反例）。通过"只提交自己 Term 的条目"这一约束，Raft 消除了这个 safety hole。

### State Machine Safety

所有 server 以**相同顺序执行相同的命令集合**——这是共识问题的最强保证。Raft 通过以下机制实现：

- Log Matching Property → 日志在任何两个 server 的相同 index 位置一致
- Leader Completeness（Election Restriction + Log Matching） → 已 Commit 条目不会被丢失
- Commit 规则 → 只有安全可提交的条目才会被标记为 committed

## Raft vs Paxos 的核心差异

Ongaro 在论文 Ch 3-4 用大量篇幅论证 Paxos 在实践中"不够好用"，然后给出 Raft 的差异化方案：

| 维度 | Paxos / Multi-Paxos | Raft |
|------|---------------------|------|
| **首要目标** | 正确性 | 可理解性 + 正确性 |
| **Leader 模型** | 多 Proposer（理论允许并发提案） | 强 Leader（日志单向流动） |
| **Leader Election** | 协议未定义（实现自行设计） | 内置随机化超时机制 |
| **日志结构** | 条目不要求连续索引（可能有空洞） | 严格连续、append-only |
| **Commit 规则** | 依赖实现者理解 | 明确约束："不直接 commit 前任 Term 条目" |
| **成员变更** | 未定义 | Joint Consensus（两阶段过渡） |
| **日志压缩** | 未定义 | Snapshot + InstallSnapshot RPC |
| **客户端交互** | 未定义 | Linearizability + 幂等序列号 + Lease Read |
| **实现碎片化** | Chubby/ZK/Spanner 各有一套 Multi-Paxos 实现 | etcd/TiKV/CockroachDB 共享同一协议规范 |
| **形式化验证** | 无官方标准 TLA+ 规约 | 附录提供完整 TLA+ Specification |

### Single-decree Paxos 的局限

原始 Paxos 只解决 **single-decree**（单个值）的共识。要构建完整系统，Multi-Paxos 需要实现者自行补全：
- Leader Election 机制 → 各实现自行设计
- 日志压缩 → 完全缺失
- 成员变更 → 完全缺失
- 客户端交互语义 → 完全缺失

Raft 将这四个缺失部分**显式纳入协议设计**（Ch 5-10），使初次实现者不至于在关键空白处犯错。

## 影响力

Raft 已成为分布式系统领域共识算法的**事实标准工程方案**：

| 系统 | 使用方式 | 说明 |
|------|---------|------|
| **etcd** | 纯 Raft | Kubernetes 核心组件，配置和状态存储 |
| **TiKV / TiDB** | 多 Raft 组 | 数据按 Region 分片，每个 Region 一个 Raft 组 |
| **CockroachDB** | 多 Raft 组 | 数据按 Range 分片，每 Range 一个 Raft 组 |
| **Consul** | Raft | HashiCorp 服务发现和配置中心 |
| **Kafka KRaft** | 自研 Raft | Kafka 3.3+ 移除 ZooKeeper，自研 Raft 元数据管理 |
| **NATS JetStream** | Raft | 消息流系统的元数据共识 |
| **ScyllaDB** | Raft | 取代 Paxos-based 组管理 |

---

*核心论文: Ongaro, D. (2014). "Consensus: Bridging Theory and Practice." Stanford University Ph.D. Dissertation.*
*核心参考: Ongaro, D., & Ousterhout, J. (2014). "In Search of an Understandable Consensus Algorithm." USENIX ATC.*
