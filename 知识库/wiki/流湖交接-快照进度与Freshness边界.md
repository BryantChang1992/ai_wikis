---
type: concept
title: 流湖交接：快照进度与 freshness 边界
sources:
- '[[知识库/sources/web/fluss-streamhouse-lakestream-20261005/来源记录]]'
- '[[技术文章/博客同步/tech-research-week-14]]'
- https://fluss.apache.org/blog/streamhouse-lakestream-fluss/
- https://fluss.apache.org/blog/fluss-tiering-service-deep-dive-part1/
- https://fluss.apache.org/blog/fluss-tiering-service-deep-dive-part2/
tags:
- 流处理
- Fluss
- 数据湖
created: '2026-10-11'
updated: '2026-10-11'
status: draft
report_as_of: '2026-10-11'
review_scope: 基于本期已核验公开报告与来源记录提炼；不增加独立证据数，不声称复现实验或完成额外源码审计。
related:
- '[[知识库/wiki/Fluss-Tiering分层架构]]'
- '[[知识库/wiki/Fluss-Lake层与湖仓融合]]'
- '[[知识库/wiki/synthesis/读路径优化的四种边界]]'
---

# 流湖交接：快照进度与 freshness 边界

## 问题

流层与湖层共享逻辑表后，何时可以把湖快照与后续流变化接起来？

## 机制

先固定各 bucket 的本轮停止 offset，再将文件与对应进度提交成湖快照，之后把湖进度登记回 Fluss。联合读者必须按每个 bucket 的交接位置衔接；主键更新和删除不能用直接拼接两边行集替代。新尝试 epoch 还用于拒绝旧完成通知。

## 取舍

共享表减少重复搭建的机会，但读引擎、受管理写入口、落湖提交和共享元数据必须协调；仅支持读取开放格式文件不等于支持联合读写。

## 适用边界

freshness 是轮次调度参数，不是最大数据陈旧时间。轮次处理、排队、截止位置及主键表首轮快照都会影响湖可见延迟。这里只采用作者机制文章；未固定 release/源码做审计，也没有新性能实验。

## 与已有知识的区别

[[知识库/wiki/Fluss-Tiering分层架构]] 已解释先提交快照、再报告进度；[[知识库/wiki/Fluss-Lake层与湖仓融合]] 覆盖插件和转换职责。本卡不重复架构总览，补充固定的逐 bucket 交接位置、拒绝旧完成消息的 epoch，以及 freshness 轮次等待和主键首轮快照的例外。它们分别约束联合读正确性与可见延迟，不能被配置值或概览图替代。

既有页面：[[知识库/wiki/Fluss-Lake层与湖仓融合]]。

## 来源

- [[知识库/sources/web/fluss-streamhouse-lakestream-20261005/来源记录|来源与阅读范围]]
- [[技术文章/博客同步/tech-research-week-14|本期完整报告及实验条件]]
- 发表时间：本周文章 2026-10-05；机制/调优补读分别为2026-06-04、2026-06-09。
- 原文定位：10/5正文读写责任与元数据协调；6/4完整tiering轮次；6/9 freshness knob 与主键首轮边界。
