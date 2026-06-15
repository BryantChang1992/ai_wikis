---
type: concept
title: "Leader Fortification — Raft 增强领导保证协议"
tags:
  - Raft
  - CockroachDB
  - 共识协议
  - Leader-Fortification
related:
  - "[[CockroachDB-Leader-Lease-整体设计]]"
  - "[[CockroachDB-Liveness-Fabric-故障检测层]]"
  - "[[Raft-共识协议]]"
sources:
  - "sources/papers/CockroachDB-Leader-Leases/Scalable-Leader-Leases-SIGMOD2026.pdf"
created: 2026-06-15
updated: 2026-06-15
---

# Leader Fortification — Raft 增强领导保证协议

## 一句话总结

Leader Fortification 是对 Raft 共识协议的**修改**，通过让 leader 从 followers 获得"在某个时间戳前不会投票给他人"的**确定性承诺**，替代传统 Raft 中依赖心跳超时的随机性，从而提供更强的领导稳定性保证——Lease 层可以安全地将 leader 和 leaseholder 统一。

## 为什么标准 Raft 不够？

标准 Raft 中：
- leader 发送周期性心跳来维持自己的 leader 地位
- follower 如果在 election timeout 内没收到心跳，会发起选举
- **leader 永远无法确定自己还是 leader**，只能通过向多数派发心跳来更新状态

这带来两个问题：
1. leader 不能提供"我在时间 X 前都是 leader"这样的保证——这是 lease 的安全性基础
2. per-group 的心跳成本随 group 数线性增长

## Fortification 协议

### 新增 RPC 消息

| 消息 | 方向 | 载荷 | 语义 |
|------|------|------|------|
| `MsgFortifyLeader` | leader → follower | term + (可选时间) | "请承诺在时间戳 X 前不发起/参与选举" |
| `MsgFortifyLeaderResp` | follower → leader | term + ack + LeadEpoch | "我接受/拒绝你的 fortification" |

### Follower 接受条件

1. 消息中的 term == 自己的 current term
2. 在 Liveness Fabric 中该 follower 的节点支持 leader 的节点

### Fortified 条件

leader 收到**多数派（含自己）** 的 MsgFortifyLeaderResp(ack=true) → **fortified**。

### 记录信息

leader 记录每个 fortifying follower 的 **LeadEpoch**（Liveness Fabric 中对应的 epoch）。这允许 leader 检测 follower 是否 stop fortifying——如果 follower 的 support timestamp 过期了，或者 follower 的当前 epoch 大于记录的 LeadEpoch。

## LeadSupportUntil (LSU)

### 定义

```
LSU = max_{Q ∈ Quorums} min_{r ∈ Q} τ_r
```

其中 τ_r 是 replica r 对 leader 的 support 到期时间戳。

### 直观理解

在所有可能的多数派中，找出每个多数派的最短 support 时间，然后在这些最短时间中取最大值。

- 如果有一个多数派的所有成员都支持 leader 到 TS=20，那 LSU 至少是 20
- 如果所有多数派都至少有一个成员 support 在 TS=10 到期，那 LSU 最多 10

### 更新频率

每 **500ms**（Raft tick）重新计算一次。

### 用途

LSU 是 Leader Lease 结束时间的**直接来源**——leader 可以保证在 LSU 之前被不会被替换。

## De-fortification（撤销 Fortification）

Follower 停止 fortifying leader 的两种方式：
1. **隐式**：收到任何更高 term 的消息——说明新 leader 已被选举
2. **显式**：leader step down → 发 MsgDefortify 直到所有 follower 确认，或看到更高 term committed entry

De-fortification 对 Raft 活性至关重要——防止 follower 永远不投票导致无法选举。

## 配置变更安全

论文识别并解决了一个微妙的安全隐患：

**问题**：在 fortification 状态下连续做两次配置变更，可能构造出一个不包含任何 fortified 成员的多数派 → tlnk

**解决方案**：增加约束 **LSU == MaxLSU**（当前 LSU 等于历史上最大 LSU）才能提出新配置变更。这强制 leader 先在当前配置下 (re)fortify 一个多数派，确保任何两个连续配置之间至少有一个多数派的 fortress。

## 关闭 Raft 心跳

Fortification 协议允许完全关闭 Raft 心跳：
- 已 fortify leader 的 follower：leader 停止发送 Raft 心跳，故障检测由 Liveness Fabric 负责
- 未 fortify leader 的 follower：leader 继续发 MsgFortifyLeader 消息（这些消息充当了传统 Raft 心跳的角色）

**收益**：消除了 CockroachDB 历史中为减少心跳引入的复杂优化（heartbeat coalescence、quiescence），架构更简洁。

## 为重启安全性新增的持久化字段

标准 Raft 的 follower 不需要记住自己曾在 fortify 哪个 leader——重启后可以安全地发起选举。但在 Leader Fortification 下，如果重启的 follower 曾经承诺在 TS=X 前不投票，却在 TS < X 时重新启动并发起选举 → 赢选举 → 在旧 leader lease 有效期内服务写入 → **违反隔离语义**。

**解决方案**：持久化两个字段：
- `Lead`：重启后仍知道自己在 fortify 哪个 leader
- `LeadEpoch`：对应的 Liveness Fabric epoch

重启后，follower 检查 Liveness Fabric 是否仍在支持 leader 的节点（对于给定的 LeadEpoch）→ 如果是，继续不投票。

## 与领导权转移的交互

Leader 可以指示 follower 竞选下一 term。follower 在请求投票时附带"此次竞选由原 leader 发起"的元数据 → 其他 replica 可以安全地投票，尽管它们还在 fortify 原 leader。这相当于隐式 de-fortification。
