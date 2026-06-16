---
type: concept
title: "Raft 客户端交互 — 线性一致性与请求路由"
tags:
  - 分布式系统
  - 共识算法
  - Raft
  - 线性一致性
  - 客户端
  - Read-Index
  - Lease-Read
  - 幂等
related:
  - "[[Raft-共识算法协议核心]]"
  - "[[分布式数据系统一致性体系]]"
status: stable
created: 2026-06-16
updated: 2026-06-16
sources:
  - "sources/papers/Raft-Dissertation/精读分析.md"
---

# Raft 客户端交互 — 线性一致性与请求路由

## 一句话总结

Raft 通过**写请求全链路（提交 → 共识 → 状态机 → 响应）、客户端序列号去重、Leader 租约 + Read Index 优化读路径、以及 Follow Redirect 路由机制**，为上层应用提供可证明的线性一致性（Linearizability）保证。

## 写请求全链路

Raft 中一条客户端写请求从发出到响应，经过五个关键阶段：

```
Client → Leader (Append RPC)
    → Leader 追加到本地日志
    → Leader 广播 AppendEntries 到 Followers
    → 收到多数派确认 → commitIndex 推进
    → Leader 状态机 apply → 返回结果给客户端
```

| 阶段 | 动作 | 关键约束 |
|------|------|----------|
| 1. 路由 | 客户端找到 Leader | 非 Leader 返回 `NotLeader` 重定向 |
| 2. 追加 | Leader 写入本地 log[] | 每条日志含 `(term, index)` 唯一标识 |
| 3. 复制 | AppendEntries 广播 | 需要**多数派**确认（含 Leader 自己） |
| 4. 提交 | commitIndex 推进 | 仅提交当前 Term 的日志 → 隐式提交前任 Term 日志 |
| 5. 执行 | Leader 状态机 apply | apply 后返回结果给客户端 |

### 线性一致性写保证

线性一致性写的关键在于：**写操作在 Leader 收到多数派确认、commitIndex 推进的时间点生效**，该时间点在所有副本视角一致。

- 对客户端而言：请求发出和响应之间的某个原子时间点
- 对读请求而言：读到的总是 commitIndex 最新的状态

这种保证来自两大约束：
1. **Election Restriction**：Candidate 日志必须不比多数节点旧，否则无法赢得选举 → 已 commit 的日志不会丢失
2. **Log Matching Property**：相同 index + term 的日志在两个节点上 → 之前所有日志相同 → 状态机确定性地抵达相同状态

## 线性一致性读：Read Index / Lease Read

### 基础方案：Read Index

传统 Raft 中，Leader 无法确定自己还是不是 Leader，因此需要通过共识确认后再读：

```
Read Index 流程：
1. Leader 记录当前 commitIndex
2. Leader 发送心跳/AppendEntries 给多数派，确认自己仍是 Leader
3. 等待状态机 apply 到至少记录的 commitIndex
4. 在此时刻读取状态机
```

**代价**：每次读请求需要一轮多数派通信（1 RTT），读吞吐受网络延迟限制。

### 优化方案：Lease Read（租约读）

Leader 在心跳周期内可以假设自己仍是 Leader——这就是 **Leader 租约（Lease）** 的思路：

> 如果 Leader 在 election timeout 内发送心跳并获得多数派确认，那么它在接下来的一段时间内（通常是 election timeout）不可能被替换。在此期间，Leader 可以直接服务读请求，无需额外的共识回合。

| 机制 | 读一致性级别 | 读延迟 | 适用场景 |
|------|------------|--------|----------|
| Read Index | 严格线性一致 | 1 RTT（最低） | 跨地域、时钟不可靠 |
| Lease Read | 线性一致 | < 1ms（本地） | 单地域、低延迟优先 |

### 时钟约束

Lease Read 依赖于**时钟漂移有界**的假设：
- Leader 租约有效期 = election timeout - 最大时钟偏移
- 如果时钟偏差超过此值，Leader 可能在租约到期前被替换 → 读可能返回过期数据

因此生产系统（如 etcd）通常提供两种读模式：
- `SerializableRead`：任意节点直接读，不保证线性一致
- `LinearizableRead`：通过 Read Index 机制保证线性一致

## 幂等操作：客户端序列号 + 服务端去重

Raft 的状态机命令是**应用层任意操作**——可能包含非幂等命令（如 `SET x = x + 1`）。如果客户端超时重试但命令已被执行，重复执行会破坏状态。因此 Raft 在协议栈中内置幂等去重。

### 客户端序列号

每个客户端分配唯一 ID，并为每条命令分配单调递增的序列号：

```
struct ClientCommand {
    client_id;      // 客户端唯一标识
    sequence_num;   // 单调递增序列号
    command;        // 实际命令体
}
```

### 服务端去重表

Leader 维护每个客户端最近一次执行的结果缓存：

| 字段 | 含义 |
|------|------|
| `client_id` | 客户端标识 |
| `latest_seq` | 该客户端已执行的最高序列号 |
| `latest_response` | 对应执行结果 |

去重逻辑：
1. 新命令到达，检查 `sequence_num`
2. 如果 `sequence_num <= latest_seq`：直接返回缓存的 `latest_response`（幂等重放）
3. 如果 `sequence_num > latest_seq`：正常执行，更新 latest_seq 和 latest_response

```
去重伪代码：
func (sm *StateMachine) apply(cmd ClientCommand) Response {
    if cmd.sequence_num <= sm.seqTable[cmd.client_id] {
        return sm.respTable[cmd.client_id]  // 幂等重放
    }
    resp := sm.execute(cmd.command)
    sm.seqTable[cmd.client_id] = cmd.sequence_num
    sm.respTable[cmd.client_id] = resp
    return resp
}
```

### 去重表持久化

去重表在**快照（Snapshot）**中包含——因为日志压缩后，前缀日志删除，但去重状态仍需保留：
- Snapshot 中保存 `client_id → latest_seq, latest_response` 映射
- 新 Leader 选举后从 Snapshot 恢复去重表，防止前任 Leader 已执行但未响应客户端的命令被重复执行

## 客户端与 Leader 路由：Follow Redirect

Raft 集群的动态性（Leader 可能变更）要求客户端能正确找到当前 Leader。

### 基本路由协议

```
客户端路由流程：
1. 客户端随机连接一个节点，发送请求
2. 如果节点不是 Leader → 返回 NotLeader，附带已知 Leader 地址
3. 客户端更新 Leader 缓存，重试
4. 如果缓存的 Leader 地址也过期 → 重新随机选取节点
```

### Leader 发现协议

| 策略 | 做法 | 优劣 |
|------|------|------|
| 随机探测 | 客户端任意连接一个节点 | 简单，O(1) 节点数下最多 1 次重试 |
| 缓存 Leader | 记住上次成功的 Leader 地址 | 大部分请求 0 重试，但可能过期 |
| 轮询 | 依次遍历所有节点 | O(N) 延迟，不推荐 |

Raft 论文推荐**缓存 Leader + 随机回退**：先尝试缓存地址，失败后随机选节点（从非 Leader 获取最新 Leader 信息后重试）。

### Sequential 与 Concurrent 请求

同一客户端可能并发多条请求。关键约束：

> **序列号检查必须在状态机执行点做，而不是在接收点做。**

原因：如果客户端并发发送 seq=3 和 seq=4，由于网络乱序，Leader 可能先收到 seq=4。如果在接收点就拒绝 seq=3（因为 seq=3 < latest=4），seq=3 将永远无法执行。正确做法是：两条日志都以 seq 进入 log[]，在 apply 到状态机时才按序检查并去重。

```
错误做法（在接收点去重）：
  recv(seq=4) → latest=4 → recv(seq=3) → 3 <= 4 → 拒绝  ❌

正确做法（在 apply 点去重）：
  log.append(seq=4) → log.append(seq=3)
  apply(seq=4) → latest=4 → execute
  apply(seq=3) → 3 <= 4 → 返回缓存结果（4 的结果）
```

但 seq=3 的结果不应是 seq=4 的结果——这要求客户端保证**收到 seq=3 的响应后才发送 seq=4**，或者服务端按 seq 缓存每条命令的独立结果。

### 会话管理

Raft 论文中，客户端会话是**逻辑概念**而非连接状态：
- `client_id` 在客户端首次注册时分配
- 客户端需要在请求中携带 client_id
- 新 Leader 选举后，去重表从 Snapshot 恢复，保留 client_id 映射
- 如果 client_id 从未被持久化到快照中，重新注册即可（因为这意味着该客户端从未成功提交命令）

## 与相关概念的关联

### Linearizability vs Sequential Consistency

| 维度 | Linearizability（Raft 提供） | Sequential Consistency |
|------|---------------------------|----------------------|
| 实时约束 | 操作顺序尊重全局挂钟时间 | 仅保证每个客户端的操作顺序 |
| 跨客户端 | 操作全局有序 | 不同客户端操作可交错 |
| Raft 如何保证 | Leader 串行化 + 单调 commitIndex | 不保证 |

Raft 默认提供 Linearizability（线性一致性），这是最强的单对象一致性模型。分布式数据库可以在此基础上构建更复杂的事务隔离级别。

### 与 CockroachDB Leader-Lease 的关联

CockroachDB 的 Leader-Fortification（[[CockroachDB-Leader-Fortification]]）本质上是对 Raft 客户端交互模型的工程化延伸：

- Raft Client Interaction（本章）提供的是**理论模型**：Leader 租约的时长是 election timeout 量级
- CockroachDB Leader Fortification 将其**工程化**：通过确定性承诺代替随机超时，使 lease 时长可精确计算（LSU）
- 两个设计共享同一核心思想：**向多数派确认领导权后再服务读请求**

## 设计启示

1. **序列号去重是分布式系统幂等的标准范式**——从 Raft 到 Kafka Idempotent Producer 到 Spanner 的 TrueTime，本质都是 `(client_id, seq)` 元组
2. **Read Index vs Lease Read 是延迟与复杂度的权衡**——无时钟假设时用 Read Index，时钟可假设时有 Lease Read
3. **Follow Redirect 是共识系统不可绕过的客户端复杂度**——任何基于 Leader 的共识协议都需要客户端承担路由职责
4. **并发请求的去重点必须在状态机层**——否则网络乱序会导致正确的请求被错误拒绝

## 局限性

- 单 Leader 写入模型是吞吐瓶颈（Leader 成为串行点）
- Lease Read 依赖时钟有界，跨地域或多云部署时需要谨慎
- 去重表随客户端数量线性增长，需要在客户端生命周期管理上做工程取舍
- 论文未提供客户端库的参考实现（如连接池、重试策略），留给了各实现方自行设计
