---
type: concept
title: KV 缓存：路由索引缺口与有限重放
sources:
- '[[技术文章/博客同步/tech-research-week-12-13]]'
- https://github.com/sgl-project/sglang/pull/42275
tags:
- AI Infra
- KV Cache
created: '2026-10-09'
updated: '2026-10-09'
status: draft
confidence: 0.7
confidence_rationale: 从已发布调研报告提炼；本轮未重新审读全部上游原文或独立复现实验，报告与卡片不算独立证据。
report_as_of: '2026-10-04'
related:
- '[[知识库/wiki/synthesis/异步存储任务的安全边界]]'
- '[[知识库/wiki/Agent-Harness-Context-Memory上下文管理]]'
---

# KV 缓存：路由索引缺口与有限重放

## 问题

缓存删除事件丢失后，路由器可能持续相信已淘汰的缓存仍可命中；预测归属也可能被误当成实际复用。

## 机制

Dynamo 的 Mooncake 共享索引在序号缺口或流失败时保守清空。SGLang 实验路由按 worker/rank 追踪序号，先请求缺失批次再处理实时批次；事件历史和等待时间都有上限。路由预测与确认事件分开保存。

## 取舍

清空会降低命中率，有限重放增加延迟和状态管理复杂度；两者都应优先避免继续依赖陈旧状态。

## 边界与项目阶段

SGLang 默认只留最近 10,000 批事件、单次补账最多等 2 秒，历史不足仍会丢失；其重放与预测功能为实验路径主干合并、发行归属未核验。不能据此声称 Dynamo 已具重放。验收分别记录索引命中、实际加载/复用及 TTFT。

> Confidence: 0.70。证据日期截至 2026-10-04；本轮为报告提炼，未进行新的完整源码审计。

## 来源与关联

- [[技术文章/博客同步/tech-research-week-12-13|完整报告与逐项出处]]
- [上游原始资料](https://github.com/sgl-project/sglang/pull/42275)
- [[知识库/wiki/Agent-Harness-Context-Memory上下文管理]]
