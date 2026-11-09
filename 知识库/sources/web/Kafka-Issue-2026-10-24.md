---
type: analysis
title: Kafka Issue 2026-10-24 来源索引
sources:
- https://issues.apache.org/jira/projects/KAFKA/issues
created: '2026-10-24'
updated: '2026-11-09'
status: draft
tags:
- Kafka
- 来源索引
related:
- '[[技术文章/博客同步/kafka-issues-2026-10-24]]'
publication_status: github_archive
publication_scope: 仅 GitHub 公开引用索引；不发布 GitHub Pages 或研究执行附件。
report_date: '2026-10-24'
source_checked: '2026-10-24'
source_check_scope: 官方公开问题、变更历史和重点 PR；未运行复现。
---

# Kafka Issue 2026-10-24 来源索引

[返回报告正文](../../../技术文章/博客同步/kafka-issues-2026-10-24.md)

> 本索引沿用 2026-10-24 的历史核读范围，不代表归档时重新核验。仅归档正文和公开引用，不包含原研究 JSON/CSV、请求记录或原文响应；文中这些记录名仅说明原研究方法，不表示此仓库提供附件。

此页为核读范围及链接索引，不是完整原文存档。

# 覆盖范围、统计口径与审计说明

## 时间边界和来源

- 固定窗口：2026-10-17 12:00:00 UTC（含）至 2026-10-24 12:00:00 UTC（不含），不因前一期是否已发布而改变。
- 主来源为官方 Apache JIRA 的公开 KAFKA 项目，通过匿名、只读 REST API 获取。正式采集记录时间为 2026-10-24 12:03:44–12:08:38 UTC。
- 为避免 JQL 无时区日期字面量带来的边界歧义，候选查询先覆盖 10 月 16 日至 10 月 25 日，再按 API 返回的带时区 created、resolutiondate、changelog.created 严格过滤到上述 UTC 窗口。
- [Kafka 官方开发指南](https://kafka.apache.org/community/developer/)明确将问题报告导向 JIRA；[apache/kafka 官方仓库 API](https://api.github.com/repos/apache/kafka)返回 has_issues=false。GitHub 在本报告中是 PR/代码核验来源，不与 JIRA 合计为两套 issue。仓库的 open_issues_count 不应被误读成独立 GitHub issue 数量。

## 完整分页证据

所有候选查询都已取到 API 声明的 total，未仅取搜索第一页。具体请求、startAt/maxResults/total/返回数记录于 query_coverage.json，原始响应另行保留核验，不纳入精简交付清单。

| 候选查询 | API total | 分页返回数 | 用途 |
|---|---:|---|---|
| created >= 2026-10-16 且 created < 2026-10-25 | 62 | startAt=0：62/100 | UTC 过滤得到新增 53 |
| resolutiondate 同一宽窗口 | 27 | startAt=0：27/100 | 当前 resolutiondate 的交叉校验，UTC 过滤得到 23 |
| resolution CHANGED DURING 同一宽窗口 | 28 | startAt=0：28/100 | 查找解决、重开等 resolution 变化 |
| status CHANGED TO Reopened DURING 同一宽窗口 | 1 | startAt=0：1/100 | 重开交叉校验 |
| status CHANGED TO/FROM Resolved 或 Closed DURING 同一宽窗口 | 28 | startAt=0：28/100 | 避免只依赖当前 resolutiondate |
| updated 同一宽窗口 | 236 | startAt=0：100；100：100；200：36 | 活动范围审计；并非新增/解决计数 |

完整 JQL 保存在 query_coverage.json。这里的“完整”限于官方 API 当时公开、匿名可见且被查询返回的集合，不涵盖权限受限、已删除或尚未被搜索索引反映的票据。

## 83 个候选 issue 的完整 changelog

- 对 created、resolutiondate、resolution-change 和 resolved/closed-status-change 候选取去重并集，共 83 个 issue。
- 逐项使用 /rest/api/2/issue/{key}?expand=changelog 读取历史，83 项均满足 startAt=0 且 histories 的条数等于 changelog.total。即各自展开响应已经包含全部历史，没有遗留下一页或截断历史。并非假定 expand 一定完整，而是逐项核对 total。
- history_coverage.json 逐项记录 startAt、maxResults、total、retrieved 和 complete；83/83 为 true。全量 updated 查询的 236 项没有全部读取历史，也没有把这 236 项冒充为解决候选。
- 期间有 7 次 HTTP 503 暂时性读取失败，均通过一次后续只读重试补齐；没有遗留失败的必需原始数据。请求和重试记录保留于各 manifest 及 all_requests_manifest.json。

## 解决事件与重开口径

- “本周发生解决”：历史中的 resolution 从空变为非空，且该事件时间在窗口内。实际 24 个事件，涉及 24 个不同 issue，没有重复解决需额外去重的情况。
- 事件类别：Fixed 20、Duplicate 2、Later 1、Done 1。Duplicate/Later/Done 不能一概写成 bug fix。
- “截至截止仍已解决”：上述 24 项中，23 项截止时 resolution 非空，类别为 Fixed 19、Duplicate 2、Later 1、Done 1。
- 唯一重开：[KAFKA-21255](https://issues.apache.org/jira/browse/KAFKA-21255)，10 月 19 日 11:23:25 UTC 转 Fixed，18:47:45 UTC 转 Reopened 并清空 resolution。直接查询当前 resolutiondate 会漏掉它的本周解决事件。
- 后续评论将待办指向 4.3/4.2 的手工回移；关联 PR #23768 在 10 月 13 日已合并。因此既不能把它算成本周首次合并的修复，也不能单凭重开就断言 trunk 修复失效。

## 新增与精简清单

- 新增 53：Bug 23、Improvement 12、Sub-task 11、Task 6、Test 1。
- 截止时状态：Open 42、Patch Available 3、In Progress 4、Resolved 4。因此新增中尚未解决 49，已解决 4。
- 新增/本周解决事件并集去重后 73 个 issue；新增且本周已解决的交集为 4。
- issues、new_issues、resolved_issues、reopened_issues 的 JSON/CSV 已移除完整 description/comment 原文，仅保留摘要、类型、优先级、状态、时间、版本、事件标记与原始链接等字段。events 和 transitions 记录精简状态事件。
- 原始全文只用于核验，不应随正式交付包复制。GitHub PR 清单也不能冒充 JIRA 解决清单。

## 关键评论分页与五项选题

- 对 KAFKA-21349、21306、21301、21315、21317、21341、21255 共 7 项检查 JIRA /comment。每项均 startAt=0、maxResults=100，并核对返回条数等于 total。
- 五个重点新问题中，KAFKA-21315 为 2/2 条评论；KAFKA-21349、21306、21317、21341 各为 0/0。备选 KAFKA-21301 为 0/0，重开项 KAFKA-21255 为 2/2。
- 所有实际返回的关键评论都发布于截止前；没有把截止后新评论倒计入窗口。
- 重点新问题分析的修复思路和测试结论来自原报告，已明确区分作者报告与本次独立验证；JIRA 的 Fix Version 仅为计划/目标，不能证明已合并或已发布。

## 截止后观察状态的处理

- 采集发生在截止之后。状态和 resolution 的实现做了逆向历史还原：若有时间 >= 截止的变更，用 fromString 回滚至截止前。83 个候选实际没有发现截止后历史项，因此截止状态与采集时状态一致。
- PR #23943、#23873、#23933、#23880 的 open/未合并状态，是 12:07–12:08 UTC 的截止后核验观察，正文已标注，不假称其恰于 12:00 抓取。PR #23768 的 merged_at 为 10 月 13 日，明确排除在本周合并范围外。
- 评论与 PR API 分页/观察状态不替代 JIRA 事件定义。公开数据会继续变化，报告只对本次采集的指定窗口和上述可见范围负责。

## 非 Fixed 原因补充核验

在主 census 完成后，又于 12:12–12:14 UTC 核验四项非 Fixed 关闭原因。四项 JIRA 评论分页分别为 KAFKA-20642 2/2、KAFKA-15560 1/1、KAFKA-21226 0/0、KAFKA-21225 0/0；连同前述 7 项，共 11 项评论端点已完整读取。PR #23829 issue comments/reviews/review comments 分别为 1/1/0 条，响应无下一页 Link，涉及讨论均发生在截止前。具体原因和直接评论链接见 nonfixed-closures.md。特别是 Done 的 KAFKA-21225 有本周已合并 PR，不能把全部非 Fixed 项概括为“未发生代码交付”。主统计数字不因此变化。


## 正文原始链接
- https://api.github.com/repos/apache/kafka
- https://bryantchang1992.github.io/ai_memory_chang_ai_team/stream-storage-observer/
- https://downloads.apache.org/kafka/
- https://downloads.apache.org/kafka/4.3.2/
- https://downloads.apache.org/kafka/4.3.2/RELEASE_NOTES.html
- https://github.com/BryantChang1992/ai_wikis/tree/master/知识库/专题跟踪/KIP-1150
- https://github.com/apache/kafka/blob/trunk/.asf.yaml
- https://github.com/apache/kafka/commit/7ac40f4dede35c79b9c1bd27dd5a17c70e33fa6f
- https://github.com/apache/kafka/commit/ea6afaa4617b8168f060803c55e90f84230531e4
- https://github.com/apache/kafka/compare/05bf7f5f38786dc9251661fdae3a5dc4fb698d09...4.3.2
- https://github.com/apache/kafka/pull/23338
- https://github.com/apache/kafka/pull/23338#pullrequestreview-5168605731
- https://github.com/apache/kafka/pull/23445
- https://github.com/apache/kafka/pull/23737
- https://github.com/apache/kafka/pull/23737#discussion_r4329966752
- https://github.com/apache/kafka/pull/23737#issuecomment-6369066877
- https://github.com/apache/kafka/pull/23737/files
- https://github.com/apache/kafka/pull/23768
- https://github.com/apache/kafka/pull/23828
- https://github.com/apache/kafka/pull/23829#issuecomment-6260470356
- https://github.com/apache/kafka/pull/23829#pullrequestreview-5566724246
- https://github.com/apache/kafka/pull/23831
- https://github.com/apache/kafka/pull/23832
- https://github.com/apache/kafka/pull/23856
- https://github.com/apache/kafka/pull/23873
- https://github.com/apache/kafka/pull/23880
- https://github.com/apache/kafka/pull/23884
- https://github.com/apache/kafka/pull/23885
- https://github.com/apache/kafka/pull/23886
- https://github.com/apache/kafka/pull/23887
- https://github.com/apache/kafka/pull/23911
- https://github.com/apache/kafka/pull/23911#discussion_r4350717570
- https://github.com/apache/kafka/pull/23911#issuecomment-6353284161
- https://github.com/apache/kafka/pull/23911#issuecomment-6365229941
- https://github.com/apache/kafka/pull/23911#pullrequestreview-5624325594
- https://github.com/apache/kafka/pull/23911#pullrequestreview-5628481846
- https://github.com/apache/kafka/pull/23928
- https://github.com/apache/kafka/pull/23928#discussion_r4364794578
- https://github.com/apache/kafka/pull/23933
- https://github.com/apache/kafka/pull/23935
- https://github.com/apache/kafka/pull/23938
- https://github.com/apache/kafka/pull/23939
- https://github.com/apache/kafka/pull/23940
- https://github.com/apache/kafka/pull/23941
- https://github.com/apache/kafka/pull/23943
- https://issues.apache.org/jira/browse/KAFKA-12188
- https://issues.apache.org/jira/browse/KAFKA-12744
- https://issues.apache.org/jira/browse/KAFKA-15560
- https://issues.apache.org/jira/browse/KAFKA-16304
- https://issues.apache.org/jira/browse/KAFKA-17688
- https://issues.apache.org/jira/browse/KAFKA-20189
- https://issues.apache.org/jira/browse/KAFKA-20391
- https://issues.apache.org/jira/browse/KAFKA-20642
- https://issues.apache.org/jira/browse/KAFKA-20841
- https://issues.apache.org/jira/browse/KAFKA-20858
- https://issues.apache.org/jira/browse/KAFKA-21058
- https://issues.apache.org/jira/browse/KAFKA-21074
- https://issues.apache.org/jira/browse/KAFKA-21181
- https://issues.apache.org/jira/browse/KAFKA-21225
- https://issues.apache.org/jira/browse/KAFKA-21226
- https://issues.apache.org/jira/browse/KAFKA-21234
- https://issues.apache.org/jira/browse/KAFKA-21255
- https://issues.apache.org/jira/browse/KAFKA-21257
- https://issues.apache.org/jira/browse/KAFKA-21258
- https://issues.apache.org/jira/browse/KAFKA-21280
- https://issues.apache.org/jira/browse/KAFKA-21288
- https://issues.apache.org/jira/browse/KAFKA-21293
- https://issues.apache.org/jira/browse/KAFKA-21294
- https://issues.apache.org/jira/browse/KAFKA-21299
- https://issues.apache.org/jira/browse/KAFKA-21301
- https://issues.apache.org/jira/browse/KAFKA-21302
- https://issues.apache.org/jira/browse/KAFKA-21303
- https://issues.apache.org/jira/browse/KAFKA-21304
- https://issues.apache.org/jira/browse/KAFKA-21305
- https://issues.apache.org/jira/browse/KAFKA-21306
- https://issues.apache.org/jira/browse/KAFKA-21307
- https://issues.apache.org/jira/browse/KAFKA-21308
- https://issues.apache.org/jira/browse/KAFKA-21309
- https://issues.apache.org/jira/browse/KAFKA-21310
- https://issues.apache.org/jira/browse/KAFKA-21311
- https://issues.apache.org/jira/browse/KAFKA-21312
- https://issues.apache.org/jira/browse/KAFKA-21313
- https://issues.apache.org/jira/browse/KAFKA-21314
- https://issues.apache.org/jira/browse/KAFKA-21315
- https://issues.apache.org/jira/browse/KAFKA-21316
- https://issues.apache.org/jira/browse/KAFKA-21317
- https://issues.apache.org/jira/browse/KAFKA-21318
- https://issues.apache.org/jira/browse/KAFKA-21319
- https://issues.apache.org/jira/browse/KAFKA-21320
- https://issues.apache.org/jira/browse/KAFKA-21321
- https://issues.apache.org/jira/browse/KAFKA-21322
- https://issues.apache.org/jira/browse/KAFKA-21323
- https://issues.apache.org/jira/browse/KAFKA-21324
- https://issues.apache.org/jira/browse/KAFKA-21325
- https://issues.apache.org/jira/browse/KAFKA-21326
- https://issues.apache.org/jira/browse/KAFKA-21327
- https://issues.apache.org/jira/browse/KAFKA-21328
- https://issues.apache.org/jira/browse/KAFKA-21329
- https://issues.apache.org/jira/browse/KAFKA-21330
- https://issues.apache.org/jira/browse/KAFKA-21331
- https://issues.apache.org/jira/browse/KAFKA-21332
- https://issues.apache.org/jira/browse/KAFKA-21333
- https://issues.apache.org/jira/browse/KAFKA-21334
- https://issues.apache.org/jira/browse/KAFKA-21335
- https://issues.apache.org/jira/browse/KAFKA-21336
- https://issues.apache.org/jira/browse/KAFKA-21337
- https://issues.apache.org/jira/browse/KAFKA-21338
- https://issues.apache.org/jira/browse/KAFKA-21339
- https://issues.apache.org/jira/browse/KAFKA-21340
- https://issues.apache.org/jira/browse/KAFKA-21341
- https://issues.apache.org/jira/browse/KAFKA-21342
- https://issues.apache.org/jira/browse/KAFKA-21343
- https://issues.apache.org/jira/browse/KAFKA-21344
- https://issues.apache.org/jira/browse/KAFKA-21345
- https://issues.apache.org/jira/browse/KAFKA-21346
- https://issues.apache.org/jira/browse/KAFKA-21347
- https://issues.apache.org/jira/browse/KAFKA-21348
- https://issues.apache.org/jira/browse/KAFKA-21349
- https://issues.apache.org/jira/browse/KAFKA-21350
- https://issues.apache.org/jira/browse/KAFKA-21351
- https://issues.apache.org/jira/browse/KAFKA-21352
- https://issues.apache.org/jira/browse/KAFKA-21353
- https://issues.apache.org/jira/projects/KAFKA/issues
- https://kafka.apache.org/community/developer/
- https://kafka.apache.org/community/downloads/
