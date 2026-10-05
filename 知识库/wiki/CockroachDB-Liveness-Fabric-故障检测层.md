---
type: concept
title: Liveness Fabric：有向支持关系
tags:
- CockroachDB
- 故障检测
- 心跳机制
- 大规模共识
- Liveness-Fabric
related:
- '[[知识库/wiki/CockroachDB-Leader-Lease-整体设计]]'
- '[[知识库/wiki/CockroachDB-Leader-Fortification]]'
- '[[知识库/wiki/事务模型深度调研]]'
sources:
- '[[知识库/sources/papers/CockroachDB-Leader-Leases/Scalable-Leader-Leases-SIGMOD2026.pdf]]'
status: draft
created: 2026-06-15
updated: '2026-10-05'
synced_at: '2026-10-05'
blog_url: https://bryantchang1992.github.io/ai_memory_chang_ai_team/knowledge/CockroachDB-Liveness-Fabric-故障检测层/
blog_source: _posts/2026-06-15-knowledge-3f200abac6.md
source_checked: '2026-10-05'
source_check_basis: Scalable Leader Leases For Multi Consensus Groups in CockroachDB, SIGMOD Companion 2026, 原始PDF
  §3–5 pp.4–11
diagram_format: mermaid
---

# Liveness Fabric：有向支持关系

> 来源：Leader Leases 论文 §3.4、§4.1（PDF pp.6–8），Algorithms1–3、Figure4。完整分析见 [[知识库/sources/papers/CockroachDB-Leader-Leases/精读分析]]。

## 支持不是全局在线标志

A请求B支持自己的epoch e至时间戳t；B承诺在其时钟超过t前保持支持。A→B与A→C独立，B撤回支持只中断对应边，不要求C也切换epoch。生产实现以store为粒度，隔离单盘故障。

```mermaid
sequenceDiagram
    participant A as 请求者 A
    participant B as 支持者 B
    A->>B: 心跳请求 epoch e、到期 t、HLC
    B->>B: 更新并持久化 support_for[A]
    B-->>A: 当前支持 epoch、到期时间、HLC
    A->>A: 更新 support_from[B]，忽略旧响应
    Note over B: 自己时钟超过到期时间后才可撤回
    B->>B: 撤回旧 epoch，递增并把到期设为 0
    A->>B: 后续心跳
    B-->>A: 告知旧 epoch 已失效
```

## 状态与重启

| 状态 | 作用 |
|---|---|
| max_epoch | 节点epoch历史的单调计数，不代表所有边当前epoch都相同 |
| support_from | 收到的每对端支持，非持久；旧响应不可倒退epoch/时间 |
| support_for | 给其他节点的支持，持久，重启后仍须兑现 |
| max_requested | 曾请求的最大截止时间，持久；约束新epoch的建立 |
| max_withdrawn | 曾撤回支持的最大时间戳，持久；防止撤回关系复活 |

重启时递增max_epoch，使时钟越过max_requested与max_withdrawn，清空并重建收到的支持，同时恢复给出的承诺。省掉这些步骤，只有一个“发ping/等timeout”的循环，不能获得论文性质。

## 两个性质不能混淆

**Support Durability**：若A收到了B至t的支持，B仍支持A，或B时钟已超过t。**Support Disjointness**：A还在旧epoch e支持对应的时间区间内时，不会接收一个更高epoch e′的重叠支持。约束的是不同epoch，不是同epoch续约不能重叠。

协议依赖单调时钟及HLC消息的因果推进；无须紧密同步，不等于毫无时钟假设。B与A在真实时间可能先后到达同一个时间戳，因此不要将证明改写为它们在同一墙钟瞬间同时超时。

## 开销和磁盘停顿

Figure8（p.11）每节点12 stores、5–150节点，600/1200/1800 stores对应约0.073/0.15/0.225核，说明测试观测的FabricCPU增长。它不证明全mesh总消息数线性，也不证明所有集群始终低于该值。

发Fabric心跳前同步磁盘写，使磁盘stall阻止支持续期；再由 [[CockroachDB-Leader-Fortification]] 把支持过期传递到领导权。Fabric只提供底层支持，不能单独替代Raft日志安全性或数据库事务语义。
