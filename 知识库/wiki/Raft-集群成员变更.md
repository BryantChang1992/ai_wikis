---
type: concept
title: "Raft 集群成员变更"
sources:
  - "sources/papers/Raft-Dissertation/精读分析.md"
tags:
  - 分布式系统
  - 共识算法
  - Raft
  - 集群管理
  - 动态配置
created: 2026-06-16
updated: 2026-06-16
status: stable
related:
  - "[[Raft-共识算法协议核心]]"
---

# Raft 集群成员变更

![[diagram/raft-joint-consensus.svg]]

## 定义

Raft **集群成员变更（Cluster Membership Changes）** 是 Ongaro 博士论文中 Raft 的三大差异化创新之一。它通过 **Joint Consensus（联合共识）** 机制，在集群配置变更期间**避免脑裂**，同时**保持集群可用性**——在不停止服务的情况下安全地添加或移除节点。

## 核心问题

### 为什么成员变更容易导致脑裂？

在分布式共识系统中，集群配置（哪些节点参与投票）本身需要在所有节点间达成一致。但配置变更发生在系统运行期间，导致一个根本性困境：

> **配置本身也是需要共识的数据，但共识的过程依赖于当前的配置定义"多数"**。

朴素方案是让旧配置 Cold 中的 Leader 选择一个时间点，将配置切换为新配置 Cnew。但这存在致命风险：

```
时间线：Cold = {S1, S2, S3}, Cnew = {S3, S4, S5}

t1: S1, S2 获知新配置，认为多数 = 2/3 (Cnew)
t2: S3, S4 尚未获知新配置，认为多数 = 2/3 (Cold)
t3: 两个"多数派"独立选出 Leader → 脑裂！
```

核心矛盾：Cold 和 Cnew 的多数派可能**不相交**（disjoint），导致两个 Leader 都在各自的"多数"定义下认为自己合法。

### 形式化表述

设 Cold 的多数为 ⌊|Cold|/2⌋ + 1，Cnew 的多数为 ⌊|Cnew|/2⌋ + 1。在最坏情况下（如从 3 节点变为 5 节点，且只需替换 Leader），存在两条决策路径各自满足多数条件，导致 **Safety 违反**。

## 解法：Joint Consensus

### 核心思想

Ongaro 的方案是**不直接切换**，而是引入一个中间过渡阶段，让新旧配置的多数派**强制相交**：

```
Cold  →  Cold,new（Joint Consensus 阶段）  →  Cnew
```

在 Joint Consensus 阶段，任何一个决策（选举或提交）需要**同时获得 Cold 和 Cnew 两个多数派的支持**。这保证了：

> **任何两个 Leader 都不会同时在两个不同的配置下被选出，因为 Joint Consensus 阶段的两个多数派必然重叠。**

### 协议流程

Raft 使用特殊的日志条目来管理配置变更。配置作为日志条目的一部分被复制和提交。

#### 阶段 1：Leader 发起 Cold,new

1. Leader 接收管理员请求（如 `AddServer` 或 `RemoveServer`）
2. Leader 构造一个包含 **Cold,new** 的日志条目（联合配置条目）
3. 此条目被复制到 Cold ∪ Cnew 中的所有节点
4. 此后所有的决策（AppendEntries 等）都需要 Cold 和 Cnew **双方**的多数确认

#### 阶段 2：Joint Consensus 期间的行为

| 操作 | 规则 |
|------|------|
| **日志复制** | 条目必须被复制到 Cold ∪ Cnew 的**全部**节点 |
| **Commit** | 条目需要 **Cold 的多数** AND **Cnew 的多数** 都确认 |
| **Leader Election** | Candidate 需要从 **Cold** 和 **Cnew** 各获得多数投票 |
| **新节点追赶** | 新节点在加入前作为 non-voting learner 追赶日志 |

#### 阶段 3：进入 Cnew

1. Cold,new 条目被提交后，集群确认联合配置已生效
2. Leader 构造包含 **Cnew** 的日志条目
3. 此时 Cnew 条目只需在 Cnew 的多数节点上复制即可提交
4. Cnew 提交后，不属于 Cnew 的旧节点可以安全下线

### 为什么 Joint Consensus 安全？

Joint Consensus 的核心安全性质：

- **Leader 唯一性**：任何两个可能被选出的 Leader（一个在 Cold，一个在 Cold,new）都**必须重叠**于 Cold 和 Cnew 的多数派交集
- **日志一致性**：已提交的 Cold,new 条目不会丢失，因为任何后续 Leader 的日志中必然包含它（Election Restriction 保证）

用 Ongaro 的话概括：

> "In Raft, the cluster first switches to a transitional configuration, which we call *joint consensus*; once the joint consensus has been committed, the system then transitions to the new configuration."

## Single-server Changes

### 动机

Joint Consensus 要求两阶段的日志复制，在大规模集群中操作开销较高。对于**一次只变更一个节点**的场景，Ongaro 提供了更简单的优化。

### 原理

当一次只添加或移除一个节点时，Cold 和 Cnew 的多数派**必然重叠**（因为 |Cold| 和 |Cnew| 只差 1），可以直接进行单阶段切换：

```
从 3 节点变为 4 节点：
Cold 多数 = 2/3
Cnew 多数 = 3/4
重叠 ≥ 1 → 安全，可跳过 Joint Consensus
```

| 变更方向 | Cold 多数 | Cnew 多数 | 必重叠？ | 是否安全直接切换 |
|---------|----------|----------|---------|---------------|
| 3→4 加节点 | 2 | 3 | ✅ (交集≥1) | ✅ 安全 |
| 4→3 减节点 | 3 | 2 | ✅ (交集≥2) | ✅ 安全 |
| 3→5 加两个 | 2 | 3 | ❌ (可能为0) | ❌ 需要 Joint Consensus |

### 协议简化

Single-server 变更只需一个日志条目，直接包含 Cnew。该条目以 Cold 的规则复制和提交；一旦提交，配置立即切换到 Cnew。

> Ongaro 论文中明确推荐：**实践中应尽量使用 single-server changes**，因为它简单且安全。批量变更时才回退到 Joint Consensus。

## 成员变更期间的可用性保证

### 集群持续服务

Raft 的成员变更设计保证集群在变更期间**可持续服务**：

| 阶段 | 读请求 | 写请求 | Leader Election |
|------|--------|--------|----------------|
| 变更前 (Cold) | ✅ 正常 | ✅ 正常 | Cold 规则 |
| Joint Consensus (Cold,new) | ✅ 正常 | ✅ 正常（需双重多数确认） | Cold + Cnew 双重投票 |
| 变更后 (Cnew) | ✅ 正常 | ✅ 正常 | Cnew 规则 |

### 关键保证

1. **无服务中断**：任何阶段都不需要停止集群
2. **渐进式过渡**：配置变更作为正常的日志条目流转，复用已有 Raft 机制
3. **非对称节点安全**：落后节点在追赶期间不参与投票，但配置变更日志会被复制到它们
4. **回退安全**：如果 Leader 在变更中途崩溃，新 Leader 继续推进未完成的配置变更

### 新节点的追赶机制

新加入的节点在成为 voting member 之前作为 **non-voting learner**：

```
1. 管理员添加节点 → 集群记录新节点为 non-voter
2. Leader 持续向新节点发送 AppendEntries 追赶日志
3. 当日志差距足够小时，发起配置变更将其转为 voter
```

这避免了新节点因日志落后而阻塞整个提交流水线。

## Leader 在变更期间的特殊角色

### 变更的发起者与协调者

Leader 是整个配置变更流程的**唯一驱动者**，承担以下特殊职责：

1. **唯一入口**：只有当前 Leader 可以发起配置变更。管理员请求被转发给 Leader
2. **两阶段提交管理**：Leader 跟踪 Cold,new 和 Cnew 两个阶段的提交状态
3. **连续性保证**：Leader 必须在 Cold ∩ Cnew 中才能推进变更

### Leader 崩溃的场景处理

| 崩溃时机 | 后果 | 新 Leader 行为 |
|---------|------|--------------|
| Cold,new 日志未提交 | 变更未生效 | 配置回退到 Cold，变更丢失 |
| Cold,new 已提交 | 联合配置已生效 | 新 Leader 继续提交 Cnew，完成变更 |
| Cnew 日志已发出 | 新 Leader 继续推进 | 根据已复制程度决定提交或回退到 Cold,new |

### 配置变更与 Leader Election 的交互

Raft 的 **Election Restriction**（Ch 7）在成员变更期间被扩展：在 Joint Consensus 阶段，Candidate 必须从 Cold 和 Cnew **各获得多数投票**才能当选。这进一步保证了：

- 新 Leader 的日志中一定包含已提交的 Cold,new 条目
- 不会出现一个 Leader 认为配置是 Cold、另一个认为配置是 Cold,new 的分裂

### 实现约束

Ongaro 论文对实现者提出了几个硬性约束：

- **一次只能有一个未完成的配置变更**：在上一个变更提交之前，不允许发起新的变更
- **Leader 不能移除自己直到 Cnew 提交**：避免变更被阻塞
- **新 Leader 就任后应立即检查并推进未完成的配置变更**

## 与 Paxos 方案的对比

Paxos 原论文**完全没有定义成员变更机制**，导致各实现各自为政。Raft 的 Joint Consensus 是对共识工程化的一个重要贡献：

| 维度 | Raft Joint Consensus | Paxos 实现（如 ZAB/Multi-Paxos） |
|------|---------------------|-------------------------------|
| 标准性 | 论文明确定义 | 无标准，每实现一套方案 |
| 安全性 | Joint Consensus 形式化保证 | 取决于具体实现 |
| 复杂度 | 两阶段 + single-server 简化 | 通常需要外部协调器 |
| 可用性 | 变更期间持续服务 | 部分实现需要短暂停服务 |

## 工程实践影响

Raft 的成员变更设计直接影响了其生态系统中所有主流实现：

- **etcd**（Kubernetes 核心组件）：使用 Joint Consensus 实现动态集群扩缩容
- **CockroachDB**：在 Multi-Raft 架构中的每个 Range 使用 Raft 成员变更
- **TiKV**：基于 Raft 成员变更实现 Region 的动态分裂和合并
- **Consul**：集群节点加入/离开通过 Raft 成员变更完成

> 成员变更是可组合共识的核心能力——没有安全变更，共识系统的运维价值大打折扣。

## 关键引用

> "Raft's membership changes use a new *joint consensus* approach, in which the majorities of both the old and new configurations overlap during the transition."

—— Ongaro, 博士论文 Abstract
