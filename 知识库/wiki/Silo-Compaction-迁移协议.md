---
type: concept
title: HATS：副本选择与 Compaction 配额
tags:
- LSM-Tree
- Compaction
- 调度
- 迁移协议
- WAF
- FAST-2026
related:
- '[[知识库/wiki/Silo-分布式LSM-Compaction调度]]'
- '[[知识库/wiki/LSM-Tree-合并优化]]'
sources:
- '[[知识库/sources/papers/LSM-Scheduling/精读分析]]'
- '[[知识库/sources/papers/LSM-Scheduling/LSM-Scheduling-FAST2026.pdf]]'
status: draft
created: 2026-06-15
updated: '2026-10-05'
synced_at: '2026-10-05'
blog_url: https://bryantchang1992.github.io/ai_memory_chang_ai_team/knowledge/Silo-Compaction-迁移协议/
blog_source: _posts/2026-06-15-knowledge-7f06276984.md
source_check_scope: 本地HATS PDF 第6–8页，§4.2–5、算法1。
source_checked: '2026-10-05'
diagram_format: mermaid
---

# HATS：副本选择与 Compaction 配额

> **历史误命名**：旧文件称“Silo Compaction 迁移协议”，其 Anti-hog、Pro-hog、CrossZone、远程读SST写回协议没有在所引PDF中出现。本文按实际HATS原文纠正，保留路径供旧链接访问。

## 粗粒度算法怎么走（§4.2、算法1）

记 L 为 epoch 长度，T_i 为节点平均读延迟，C[i,j] 为 range i 第j副本收到的请求数。节点余量 Δ_i=`L/T_i − 本轮读请求总数`。负数表示超载，正数表示余量。

在一个复制组内，依次从超载副本给空闲副本转移 `min(超载量, 空闲量, 原分配请求量)`。转移后的 E 通过 Gossip 分发，客户端按副本期望请求占比选 coordinator。算法保持每个range的总请求数，而不是把数据移动到新节点。

教学例：A超载200、B余量120、该range在A有800次请求，则搬移120次期望读，A保留680，B增加120。剩余超载仍需寻找其他副本；这个例子不是论文的benchmark数值。

```mermaid
flowchart LR
  C[当前状态 C 与平均延迟] --> D[计算每节点余量]
  D --> Pair[同组选择超载与空闲副本]
  Pair --> Min[取三项最小值作为转移读数]
  Min --> E[更新 E 与双方余量]
  E --> Publish[Gossip 发布 term 与 epoch]
  Publish --> Client[客户端按 E 选择 coordinator]
```

## 细粒度协调（§4.3）

即时延迟 t[i,j] 包含coordinator到副本的网络和服务时间，使用EWMA（实现权重.5）。令Q为该节点在E中的期望总读数，score=`L/t[i,j] − Q`；选择score最高的合法副本。单纯追逐最快副本容易使大家同时涌向它，这里加入全局已分配负载作为约束。

## 压实配额与防饥饿（§4.4–5）

不同range副本分成独立LSM-tree，在一个节点的允许压实预算内，按其期望读比例分配。论文默认总预算64MiB/s、epoch60s。靠近新flush的最低层压实不受该限速，以免新SST积压；其他层限速。

读冷写热的range不能长期得到零进展。§5给出防饥饿阈值与回退Cassandra FCFS执行的规则。因此调度的目标同时包括读性能与后台工作可推进，不是永远牺牲所有冷副本。

## 不变量与故障范围

1. 数据仍在原副本，本地压实必须保持相同可见结果。
2. 只在拥有目标range并满足一致性要求的副本中选路由。
3. expected state按term、epoch更新，拒绝旧决策倒退。
4. scheduler故障由seed间Raft重新选举；数据副本故障仍交Cassandra处理。

这是一套调度协议，不是新的事务提交或SST跨节点安装协议。故障恢复的详细持久化规则不能从本文的调度机制推导成“任意系统可直接套用”。

定位：本地PDF第6–8页；算法1、§4.2.1、§4.3、§4.4、§5。完整条件与评估见[[知识库/sources/papers/LSM-Scheduling/精读分析|HATS精读]]；概览见[[Silo-分布式LSM-Compaction调度|HATS协同调度]]。
