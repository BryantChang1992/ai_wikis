---
title: 存储/数据库顶会趋势洞察 · Week 04
blog_url: https://bryantchang1992.github.io/ai_memory_chang_ai_team/posts/tech-research/week-04/conferences/
blog_source: _posts/2026-06-11-top-conferences-week-04.md
blog_source_commit: f83970fa7e6ad32d626cc6ca3ba7428c90a638a5
blog_body_sha256: b99483c745498774eee4b47192077dc50cc2182cbb6e6b0f56d3181c300de26e
synced_at: '2026-10-05'
type: survey
created: '2026-06-11'
tags:
- 顶会
- 趋势洞察
issue: 4
issue_date: '2026-06-11'
updated: '2026-10-05'
review_scope: 已核对论文纠错，其余降为待核验题名线索
---

# Week 04 顶会线索：核验后的阅读分层

本期保留 2026-06-11 的归档时间。2026-10-05 复核发现旧稿将会议目录线索扩写成了未经原文支持的算法与实验数字，现撤回这类描述。“全部可免费获取”也不成立：LSM-Raft 的既有 PDF 实际是拦截页。

下面区分已完成精读的材料与待核验题名。待核验目录用于找原文，不代表题名、作者、会议归属和性能结论已逐项确认；历史全文可通过 Git 历史追溯。

## 已有原文精读

- [[知识库/sources/papers/LSM-Scheduling/精读分析|HATS：读与本地 Compaction 协同调度]]

- [[知识库/sources/papers/CockroachDB-Leader-Leases/精读分析|CockroachDB：Liveness Fabric 与 leader fortification]]

- [[知识库/sources/papers/RaaS/精读分析|RaaS：分离日志回放资源以缓解尾延迟]]

- [[知识库/sources/papers/Rose/精读分析|Rosé：共同 epoch 边界与协调应用]]

- [[知识库/sources/papers/Aurora-Limitless/精读分析|Aurora-Limitless 原文精读]]

- [[知识库/sources/papers/ByteHouse/精读分析|ByteHouse 原文精读]]

- [[知识库/sources/papers/Agent-First-Data/精读分析|Agent-First-Data 原文精读]]


HATS 并非旧稿描述的 compaction 迁移求解器；CockroachDB 的论文讨论支持关系和强化领导权，不是预测性心跳延长；RaaS 的核心是回放与读取资源竞争，不是旧稿的 hedge request / 预取三件套。性能数字请连同精读中的基线、负载与图表位置一起引用。

## 待核验的会议目录线索

以下仅保留旧稿的题名与入口。取得原文后再判断贡献，不能从标题推导实现。
