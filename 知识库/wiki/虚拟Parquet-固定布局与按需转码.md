---
type: concept
title: 虚拟 Parquet：固定布局与按需转码的兼容边界
sources:
- '[[知识库/sources/papers/Active-Data-Lakes/来源记录]]'
- '[[技术文章/博客同步/tech-research-week-14]]'
- https://www.vldb.org/pvldb/vol19/p1372-ginter.pdf
- https://www.vldb.org/pvldb/vol19/FrontMatterVol19No6.pdf
tags:
- 数据湖
- Parquet
- 存储引擎
created: '2026-10-11'
updated: '2026-10-11'
status: draft
report_as_of: '2026-10-11'
review_scope: 基于本期已核验公开报告与来源记录提炼；不增加独立证据数，不声称复现实验或完成额外源码审计。
related:
- '[[知识库/wiki/数据湖-提交结果不确定性与有界重试]]'
- '[[知识库/wiki/synthesis/读路径优化的四种边界]]'
---

# 虚拟 Parquet：固定布局与按需转码的兼容边界

## 问题

底层采用新编码后，如何让只支持 Parquet 的旧查询引擎继续进行 footer 和 range 读取？

## 机制

在存储与读者之间提供主动转换服务，内部保留 BtrBlocks，按需生成虚拟 Parquet。为了让 footer 中的偏移在转码前就可计算，原型选择大小可预测的编码，放弃通用压缩及多种编码；不是先完整生成另一份 Parquet 副本。

## 取舍

兼容旧读者的收益由转码 CPU、网络传输和新增服务复杂度支付。格式兼容不等于压缩率、扫描吞吐和并发可用性都得到改善。

## 适用边界

论文 §4.3/图5 的证据是 DuckDB 1.2.1 单线程、TPC-H lineitem SF10、同可用区两台 c5n.9xlarge。冷数据和服务端内存数据的差距不同，不能外推任意查询。Iceberg/Paimon 没有因此自动拥有该架构；本轮不复现实验。

## 与已有知识的区别

这解决“旧读者能否解释新的物理存储”的问题。已有提交重试卡讨论的是结果不确定时是否可以再写；读格式的兼容性不能替代提交幂等与快照正确性。

既有页面：[[知识库/wiki/数据湖-提交结果不确定性与有界重试]]。

## 来源

- [[知识库/sources/papers/Active-Data-Lakes/来源记录|来源与阅读范围]]
- [[技术文章/博客同步/tech-research-week-14|本期完整报告及实验条件]]
- 发表时间：PVLDB 19(6)，2026-02；本周为补读，不是新发表。
- 原文定位：正式论文 §3–4、§4.2、§4.3 图5、§8.4；刊期由官方 front matter 核验。
