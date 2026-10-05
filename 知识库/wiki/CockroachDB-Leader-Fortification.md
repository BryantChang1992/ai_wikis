---
type: concept
title: Leader Fortification：强化 Raft 领导权
tags:
- Raft
- CockroachDB
- 共识协议
- Leader-Fortification
related:
- '[[知识库/wiki/CockroachDB-Leader-Lease-整体设计]]'
- '[[知识库/wiki/CockroachDB-Liveness-Fabric-故障检测层]]'
- '[[知识库/wiki/事务模型深度调研]]'
sources:
- '[[知识库/sources/papers/CockroachDB-Leader-Leases/Scalable-Leader-Leases-SIGMOD2026.pdf]]'
status: draft
created: 2026-06-15
updated: '2026-10-05'
synced_at: '2026-10-05'
blog_url: https://bryantchang1992.github.io/ai_memory_chang_ai_team/knowledge/CockroachDB-Leader-Fortification/
blog_source: _posts/2026-06-15-knowledge-7723389f4a.md
source_checked: '2026-10-05'
source_check_basis: Scalable Leader Leases For Multi Consensus Groups in CockroachDB, SIGMOD Companion 2026, 原始PDF
  §3–5 pp.4–11
diagram_format: mermaid
---

# Leader Fortification：强化 Raft 领导权

> 依据 Leader Leases 论文 §3.3、§4.2（PDF pp.4–6、9），Figures2–3。它是Raft的额外协议，不能视为基本Raft心跳天然提供的租约保证。

## 承诺与 LSU

Leader发送MsgFortifyLeader；follower核对term、没有强化另一leader、Fabric中确实支持该leader后，回复LeadEpoch。Leader收到含自身的quorum响应后建立fortification，并从本地Fabric查询每个已强化副本的有效支持截止τ。

```mermaid
flowchart TD
    R[收到 Fortify 请求] --> T{term 与领导者条件正确}
    T -->|否| N[拒绝或返回当前term]
    T -->|是| S{Fabric 支持该leader}
    S -->|否| N
    S -->|是| P[持久化 Lead / LeadEpoch 并确认]
    P --> Q[Leader 汇集合法 quorum]
    Q --> L[LSU = quorum最短支持时间的最大值]
    L --> E{支持过期或epoch改变}
    E -->|是| F[移除旧承诺，重新fortify]
```

`LSU=max_Q min_(r∈Q) τ_r` 只对有效且epoch匹配的支持计算。以自构三副本例，若可用支持到期时间分别为100、120、130，二副本quorum能给出的最大最短值为120；这里的数值是时间戳示例，不是论文配置。不能只取所有副本最大值130。

## 持久化与重配置

Follower若重启后忘记它已承诺不投票，就可能在旧lease有效期间选出新leader。因此§3.3.6新增持久字段Lead和LeadEpoch，恢复时结合Fabric检查承诺。

配置变化可能降低当前LSU，但不能让已经授出的较长授权凭空缩短。§3.3.5、Figure3引入MaxLSU，要求在提出配置变更前达到LSU=MaxLSU，先强化当前配置。成员变更不是仅重新算一个quorum公式即可。

## 退出与转移

显式MsgDefortify、观察到更高term的处理，以及经当前leader授权的leadership transfer，负责释放旧承诺并维持活性。合作lease转移暂用expiration lease，之后才把lease与新leader重新合并。未强化follower继续收到周期性Fortify请求，已强化follower可由Fabric代替常态Raft心跳。

## 安全证据和代价

§4.2的引理把Fabric的持久支持与新leader时间戳界连接起来，再由§4.3 Theorem4.7推出lease不重叠。不是依据随机选举超时猜测“应该还没有新leader”。

代价是故障时可能先等support到期再竞选。§5.1相同3秒lease配置下，相比旧类约多1–2秒；这是具体实验对照，不是协议在任意网络下的固定延迟。

前置阅读：[[Raft-客户端交互]]、[[CockroachDB-Liveness-Fabric-故障检测层]]；整体见 [[CockroachDB-Leader-Lease-整体设计]]。
