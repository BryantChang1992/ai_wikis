---
type: concept
title: Fluss 分区桶数：路由与旧批次的契约
sources:
- '[[技术文章/博客同步/stream-storage-observer-2026-10-09]]'
- https://github.com/apache/fluss/pull/4527
tags:
- 流处理
- Fluss
- 客户端
created: '2026-10-09'
updated: '2026-10-09'
status: draft
confidence: 0.7
confidence_rationale: 从已发布调研报告提炼；本轮未重新审读全部上游原文或独立复现实验，报告与卡片不算独立证据。
report_as_of: '2026-10-09'
related:
- '[[知识库/wiki/Fluss-客户端与计算集成]]'
- '[[知识库/wiki/Fluss-客户端写入流程源码分析]]'
---

# Fluss 分区桶数：路由与旧批次的契约

## 问题

修改表级 bucket.num 后，历史分区与新分区桶数不同。拿表的最新值统一路由，会把 key 发到错误位置。

## 机制

缓存分区实际桶数与表级 bucket-count epoch，请求携带 routing_bucket_count；未知分区可先形成临时批次，但真正发送前必须解析布局。服务端拒绝过期布局后，刷新元数据并显式处理批次失败。

## 取舍

缓存和校验增加元数据管理成本；显式失败要求应用重试，却保护了键分组与幂等序号的正确性。已按错误桶数组成的有 key 批次不能仅换标签继续发送。

## 边界与项目阶段

#4527 已合入 main（2026-10-03 16:37:55 UTC，即北京时间 10 月 4 日），正式发行归属未确认。修改桶数前创建的 writer 首次写新分区可能失败，同 writer 重试才成功；不承诺无感扩桶。

> Confidence: 0.70。证据日期截至 2026-10-09；本轮为报告提炼，未进行新的完整源码审计。

## 来源与关联

- [[技术文章/博客同步/stream-storage-observer-2026-10-09|完整报告与逐项出处]]
- [上游原始资料](https://github.com/apache/fluss/pull/4527)
- [[知识库/wiki/Fluss-客户端与计算集成]]
- [[知识库/wiki/Fluss-客户端写入流程源码分析]]
