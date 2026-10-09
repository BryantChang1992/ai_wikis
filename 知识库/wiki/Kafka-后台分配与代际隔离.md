---
type: concept
title: Kafka 后台分配：日志回滚后的代际隔离
sources:
- '[[技术文章/博客同步/stream-storage-observer-2026-10-09]]'
- https://github.com/apache/kafka/pull/23688
tags:
- 消息系统
- Kafka
- 分布式协调
created: '2026-10-09'
updated: '2026-10-09'
status: draft
confidence: 0.7
confidence_rationale: 从已发布调研报告提炼；本轮未重新审读全部上游原文或独立复现实验，报告与卡片不算独立证据。
report_as_of: '2026-10-09'
related:
- '[[知识库/wiki/synthesis/异步存储任务的安全边界]]'
- '[[知识库/wiki/流处理弹性与重配置]]'
---

# Kafka 后台分配：日志回滚后的代际隔离

## 问题

把 assignor 计算移出 heartbeat 前台后，日志写入失败可能回滚 group epoch，而旧后台结果仍会迟到；数值相同的 epoch 可能属于不同运行。

## 机制

#23688 提案为 in-flight run 跟踪 epoch，在 group epoch 增长到该值或更低值时取消旧 run，并让后续 heartbeat 接收有效结果。核心约束是：结果的任务生命周期必须与当前日志状态匹配。

## 取舍

前台阻塞减少，但取消、组删除清理、目标 epoch 校验和迟到结果处理变复杂。

## 边界与项目阶段

截止 2026-10-09 报告窗口仍为 open PR；默认开启仅是补丁提议。该卡提炼正确性问题，不声称已部署、已发布或有确定性能倍数。

> Confidence: 0.70。证据日期截至 2026-10-09；本轮为报告提炼，未进行新的完整源码审计。

## 来源与关联

- [[技术文章/博客同步/stream-storage-observer-2026-10-09|完整报告与逐项出处]]
- [上游原始资料](https://github.com/apache/kafka/pull/23688)
- [[知识库/wiki/流处理弹性与重配置]]
