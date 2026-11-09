---
type: analysis
title: Kafka Issue 2026-10-31 来源索引
sources:
- https://issues.apache.org/jira/projects/KAFKA/issues
created: '2026-10-31'
updated: '2026-11-09'
status: draft
tags:
- Kafka
- 来源索引
related:
- '[[技术文章/博客同步/kafka-issues-2026-10-31]]'
publication_status: github_archive
publication_scope: 仅 GitHub 公开引用索引；不发布 GitHub Pages 或研究执行附件。
report_date: '2026-10-31'
source_checked: '2026-10-31'
source_check_scope: 公开 JIRA 生命周期与重点原文和 PR、回移、发行；未运行复现。
---

# Kafka Issue 2026-10-31 来源索引

[返回报告正文](../../../技术文章/博客同步/kafka-issues-2026-10-31.md)

> 本索引沿用 2026-10-31 的历史核读范围，不代表归档时重新核验。仅归档正文和公开引用，不包含原研究 JSON/CSV、请求记录或原文响应；文中这些记录名仅说明原研究方法，不表示此仓库提供附件。

此页是实际查询与原文核读的索引，不是完整网页原文存档。附录统计覆盖与重点深读范围不同，未逐项深读所有 71 个问题的所有关联代码。

# Kafka Issue 2026-10-31：覆盖范围与可核查口径

## 时间与官方渠道

固定事件窗口为 **2026-10-24 12:00:00 UTC（含）至 2026-10-31 12:00:00 UTC（不含）**，接续上期，不因上期未发布而重新取七天。此 census 实际采集记录为 2026-10-31 **12:02:32–12:05:39 UTC**。文章其他来源可有更晚检索时间，不能倒计入事件窗口。

本次直接读取 Apache JIRA KAFKA 项目匿名只读 REST API。查询日期字面量不含时区，因此先覆盖 **10 月 23 日至 11 月 1 日** 的宽候选窗口，再按带时区 created、resolutiondate、changelog.created 精确过滤到固定 UTC 窗口。不是将日期查询结果直接当作精确计数。

[apache/kafka 仓库 API](https://api.github.com/repos/apache/kafka)本次返回 **has_issues=false**；GitHub PR 用于补充讨论和代码/回移/发行证据，不作为另一套 GitHub issue 数与 JIRA相加。open_issues_count 本身不能证明仓库启用了独立 issue。另已保存公开 .asf.yaml 配置响应用于交叉核对。官方问题报告入口需与[开发指南](https://kafka.apache.org/community/developer/)一同理解。

## 六类候选查询及分页

完整 JQL、各页 startAt/maxResults/total/实际条数保存在 query_coverage.json。查询均排序后获取到 API total，结果数不超过100的不是任意截取100项。

| 查询 | API total | 分页实际返回 | 用途 |
|---|---:|---|---|
| created >= 2026-10-23 AND created < 2026-11-01 | 69 | 0:69/100 | 精确过滤得到新增54 |
| resolutiondate 同宽窗口 | 31 | 0:31/100 | 当前解决日期交叉核对 |
| resolution CHANGED DURING 同宽窗口 | 31 | 0:31/100 | 防止遗漏解决后重开 |
| status CHANGED TO Reopened DURING 同宽窗口 | 0 | 0:0/100 | 重开交叉核对 |
| status CHANGED TO/FROM Resolved 或 Closed DURING 同宽窗口 | 31 | 0:31/100 | 与 resolution 事件交叉核对 |
| updated 同宽窗口 | 183 | 0:100/100，100:83/100 | 活动范围审计，不是新增/解决计数 |

这里“完整”只限于采集时官方 API 返回的匿名可见查询集合。不包括权限受限、删除、未入索引的票据；没有将未查到写成不存在。updated 的183项未逐一深读全部历史，也没有冒充183项新增或修复。

## 86 个候选的完整 changelog

created、resolutiondate、resolution-change、resolved/closed-status-change 候选并集为86项。逐项请求 /rest/api/2/issue/{key}?expand=changelog，核对 startAt=0、histories 条数等于 total。**86/86完整**，不是假设 expand 永远不截断。history_coverage.json 保留逐项总数与判定；该批响应没有遗留历史分页。

16 次 history 请求出现 HTTP503，均通过一次后续只读重试补齐。主查询无失败。请求/重试网址、采集时间及结果保存在 all_requests_manifest.json；无必需候选遗留失败。不把暂时性503写成权限拒绝。

事件按历史中 resolution 从空变为非空定义；清空 resolution 则记重开。非空类型之间变更保留 transitions，不把它误算第二次解决。状态与 resolution 按截止后的历史倒推至截止时；本批实际未发现截止后变更，因此截止快照与采集时一致。

## 最终统计

- 新增54：Bug21、Sub-task18、Improvement13、Task2。
- 截止状态：Open36、Patch Available6、In Progress1、Resolved11。新增43项尚未解决。
- 解决事件28，涉及28个不同 issue，截止仍解决28。类别：Fixed25、Won’t Fix1、Won’t Do1、Not A Problem1。**不能把28一概称为28个漏洞修复**，Fixed也包含改进、子任务和文档。
- 本周重开0；不等于历史从未重开。上期重开的 KAFKA-21255 在本期重新解决，应写成回移工作的闭环，不是本周首次引入主线修复。
- 新增与解决交集11；并集71。没有重复算成82个独立问题。
- 三个非 Fixed 分别为 KAFKA-20820（Won’t Fix）、KAFKA-21385（Won’t Do）、KAFKA-21390（Not A Problem），原因见 nonfixed-closures.md。

## 精简交付清单与重要限制

issues/new_issues/resolved_issues/reopened_issues 的 JSON/CSV 只保留标题、类型、优先级、状态、时间、影响/目标版本、事件标记及原始链接，不含整段票据或全部评论复制。events/transitions 保存可核查历史ID和时间。Fix Version 字段是目标/票据元数据，**不是已发布证明**。

对21363、21402、21397、21367、21255、20820、21385、21390共8个重点票据，额外读取评论端点。分别6、1、1、0、3、1、1、0条，startAt=0/maxResults=100，返回数均等于total；comments_manifest.json保留记录。本文不宣称71项都逐一读了全部评论。相关PR/源码/发布证据由正文研究另行核验。

原始响应只保留作研究复核，不应随精简公开交付包整页复制。GitHub合并状态不能替代JIRA解决状态，例如21349本次仍Open，而其关联PR此前已合并；反向也不能只凭JIRA Fixed断言发行包已包含代码。公开数据持续变化，清单只对本次窗口与可见范围负责。

### GitHub PR 检索的独立覆盖限制

本次关闭 PR 搜索返回 79 项且 incomplete_results=false，但结果未包含独立读取确认在 10 月 29 日关闭的 #23995。因此本文不把 79 当作完整的 PR 关闭总数，也不将其并入 JIRA 统计。正文按 JIRA 关联、上期未闭环清单和逐项 PR 原文交叉核对；查询成功标志不能代替完整性证明。

## 原始链接

- https://api.github.com/repos/apache/kafka
- https://bryantchang1992.github.io/ai_memory_chang_ai_team/stream-storage-observer/
- https://github.com/BryantChang1992/ai_wikis/blob/master/知识库/专题跟踪/KIP-1150/2026-10-30-迁移控制链合并与读路径安全.md
- https://github.com/apache/kafka/commit/04071f2a527dc750c0b2a22d171587f861966268
- https://github.com/apache/kafka/commit/0acc8008cb81397cb17664a0399f0b7b305258db
- https://github.com/apache/kafka/commit/14ee92ca1ecf469eb8f006abf7b75453513cac49
- https://github.com/apache/kafka/commit/2379fdd3727a4ad04a95142091b2dcffb8b846d3
- https://github.com/apache/kafka/commit/330318de73c169f526069e33803fdc9f28af5a9c
- https://github.com/apache/kafka/commit/365f6651db30d3cc53482b2bceffe29946b48faf
- https://github.com/apache/kafka/commit/40cd922dbd405118110da6b11cf219aeccbf3ab2
- https://github.com/apache/kafka/commit/682fe10b28a35be295c20304073f107884a72c07
- https://github.com/apache/kafka/commit/6cbcf527493c7f688487bbf3fe2b3271081dda3d
- https://github.com/apache/kafka/commit/72de69ccdcd72ac59ef1db2b1848179b8c1ac5c6
- https://github.com/apache/kafka/commit/7d07ebf69794895a9cbf8ae1750a8bb469ab59d8
- https://github.com/apache/kafka/commit/7dbea6cf86a9a5b31f3449c0850d001149887aa5
- https://github.com/apache/kafka/commit/8b83b92fd1c06bcedbb6f658dad33e35f9f16820
- https://github.com/apache/kafka/commit/a2b91b7694762e886be25d9a31591321c0d8313c
- https://github.com/apache/kafka/commit/b1093f64c085d82c08fd6462b26a190e2eb3cb83
- https://github.com/apache/kafka/commit/b1ddd4eb555b84347d03ef9ddf75f63c3ba9a347
- https://github.com/apache/kafka/pull/23241
- https://github.com/apache/kafka/pull/23241#issuecomment-6495634446
- https://github.com/apache/kafka/pull/23728
- https://github.com/apache/kafka/pull/23728#issuecomment-6448002057
- https://github.com/apache/kafka/pull/23900
- https://github.com/apache/kafka/pull/23901
- https://github.com/apache/kafka/pull/23902
- https://github.com/apache/kafka/pull/23903
- https://github.com/apache/kafka/pull/23916
- https://github.com/apache/kafka/pull/23933
- https://github.com/apache/kafka/pull/23938
- https://github.com/apache/kafka/pull/23939
- https://github.com/apache/kafka/pull/23940
- https://github.com/apache/kafka/pull/23941
- https://github.com/apache/kafka/pull/23943
- https://github.com/apache/kafka/pull/23970
- https://github.com/apache/kafka/pull/23975
- https://github.com/apache/kafka/pull/23984
- https://github.com/apache/kafka/pull/23984#issuecomment-6507110226
- https://github.com/apache/kafka/pull/23995
- https://github.com/apache/kafka/pull/23995#issuecomment-6477981433
- https://github.com/apache/kafka/pull/23995#issuecomment-6486791868
- https://github.com/apache/kafka/pull/24017
- https://github.com/apache/kafka/pull/24017#discussion_r4414302125
- https://github.com/apache/kafka/pull/24017#discussion_r4415025892
- https://github.com/apache/kafka/pull/24018
- https://issues.apache.org/jira/browse/KAFKA-18574
- https://issues.apache.org/jira/browse/KAFKA-20125
- https://issues.apache.org/jira/browse/KAFKA-20820
- https://issues.apache.org/jira/browse/KAFKA-20866
- https://issues.apache.org/jira/browse/KAFKA-20901
- https://issues.apache.org/jira/browse/KAFKA-20981
- https://issues.apache.org/jira/browse/KAFKA-21099
- https://issues.apache.org/jira/browse/KAFKA-21214
- https://issues.apache.org/jira/browse/KAFKA-21230
- https://issues.apache.org/jira/browse/KAFKA-21251
- https://issues.apache.org/jira/browse/KAFKA-21255
- https://issues.apache.org/jira/browse/KAFKA-21292
- https://issues.apache.org/jira/browse/KAFKA-21297
- https://issues.apache.org/jira/browse/KAFKA-21324
- https://issues.apache.org/jira/browse/KAFKA-21341
- https://issues.apache.org/jira/browse/KAFKA-21344
- https://issues.apache.org/jira/browse/KAFKA-21349
- https://issues.apache.org/jira/browse/KAFKA-21353
- https://issues.apache.org/jira/browse/KAFKA-21354
- https://issues.apache.org/jira/browse/KAFKA-21355
- https://issues.apache.org/jira/browse/KAFKA-21356
- https://issues.apache.org/jira/browse/KAFKA-21357
- https://issues.apache.org/jira/browse/KAFKA-21358
- https://issues.apache.org/jira/browse/KAFKA-21359
- https://issues.apache.org/jira/browse/KAFKA-21360
- https://issues.apache.org/jira/browse/KAFKA-21361
- https://issues.apache.org/jira/browse/KAFKA-21362
- https://issues.apache.org/jira/browse/KAFKA-21363
- https://issues.apache.org/jira/browse/KAFKA-21363?focusedCommentId=18132618&page=com.atlassian.jira.plugin.system.issuetabpanels:comment-tabpanel#comment-18132618
- https://issues.apache.org/jira/browse/KAFKA-21364
- https://issues.apache.org/jira/browse/KAFKA-21365
- https://issues.apache.org/jira/browse/KAFKA-21366
- https://issues.apache.org/jira/browse/KAFKA-21367
- https://issues.apache.org/jira/browse/KAFKA-21368
- https://issues.apache.org/jira/browse/KAFKA-21369
- https://issues.apache.org/jira/browse/KAFKA-21370
- https://issues.apache.org/jira/browse/KAFKA-21371
- https://issues.apache.org/jira/browse/KAFKA-21372
- https://issues.apache.org/jira/browse/KAFKA-21373
- https://issues.apache.org/jira/browse/KAFKA-21374
- https://issues.apache.org/jira/browse/KAFKA-21375
- https://issues.apache.org/jira/browse/KAFKA-21376
- https://issues.apache.org/jira/browse/KAFKA-21377
- https://issues.apache.org/jira/browse/KAFKA-21378
- https://issues.apache.org/jira/browse/KAFKA-21379
- https://issues.apache.org/jira/browse/KAFKA-21380
- https://issues.apache.org/jira/browse/KAFKA-21381
- https://issues.apache.org/jira/browse/KAFKA-21382
- https://issues.apache.org/jira/browse/KAFKA-21383
- https://issues.apache.org/jira/browse/KAFKA-21384
- https://issues.apache.org/jira/browse/KAFKA-21385
- https://issues.apache.org/jira/browse/KAFKA-21386
- https://issues.apache.org/jira/browse/KAFKA-21387
- https://issues.apache.org/jira/browse/KAFKA-21388
- https://issues.apache.org/jira/browse/KAFKA-21389
- https://issues.apache.org/jira/browse/KAFKA-21390
- https://issues.apache.org/jira/browse/KAFKA-21391
- https://issues.apache.org/jira/browse/KAFKA-21392
- https://issues.apache.org/jira/browse/KAFKA-21393
- https://issues.apache.org/jira/browse/KAFKA-21394
- https://issues.apache.org/jira/browse/KAFKA-21395
- https://issues.apache.org/jira/browse/KAFKA-21396
- https://issues.apache.org/jira/browse/KAFKA-21397
- https://issues.apache.org/jira/browse/KAFKA-21397?focusedCommentId=18134533&page=com.atlassian.jira.plugin.system.issuetabpanels:comment-tabpanel#comment-18134533
- https://issues.apache.org/jira/browse/KAFKA-21398
- https://issues.apache.org/jira/browse/KAFKA-21399
- https://issues.apache.org/jira/browse/KAFKA-21400
- https://issues.apache.org/jira/browse/KAFKA-21401
- https://issues.apache.org/jira/browse/KAFKA-21402
- https://issues.apache.org/jira/browse/KAFKA-21402?focusedCommentId=18135401&page=com.atlassian.jira.plugin.system.issuetabpanels:comment-tabpanel#comment-18135401
- https://issues.apache.org/jira/browse/KAFKA-21403
- https://issues.apache.org/jira/browse/KAFKA-21404
- https://issues.apache.org/jira/browse/KAFKA-21405
- https://issues.apache.org/jira/browse/KAFKA-21406
- https://issues.apache.org/jira/browse/KAFKA-21407
- https://kafka.apache.org/blog/2026/09/29/apache-kafka-4.2.2-release-announcement/
- https://kafka.apache.org/blog/2026/10/22/apache-kafka-4.4.0-release-announcement/
- https://kafka.apache.org/blog/2026/10/23/apache-kafka-4.3.2-release-announcement/
- https://kafka.apache.org/community/cve-list/
- https://kafka.apache.org/community/developer/


## 原报告其他公开引用

- https://issues.apache.org/jira/projects/KAFKA/issues
