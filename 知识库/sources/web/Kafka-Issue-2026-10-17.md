---
type: analysis
title: Kafka Issue 2026-10-17 来源索引
sources:
- https://issues.apache.org/jira/projects/KAFKA/summary
- https://github.com/apache/kafka
tags:
- Kafka
- 来源索引
created: '2026-11-09'
updated: '2026-11-09'
status: draft
related:
- '[[技术文章/博客同步/kafka-issues-2026-10-17]]'
publication_status: github_archive
publication_scope: 仅 GitHub 公开引用索引；不发布 GitHub Pages 或研究执行附件。
report_date: '2026-10-17'
source_checked: '2026-10-17'
source_check_scope: 沿用原报告 2026-10-17 的官方 JIRA、PR、最终提交及发行记录核读；正文检索与附录后续复核时间分别保留，未独立复现。
---

# Kafka Issue 2026-10-17 来源索引

[返回报告正文](../../../技术文章/博客同步/kafka-issues-2026-10-17.md)

> 本索引沿用 2026-10-17 的历史核读范围，不代表归档时重新核验。仅归档正文和公开引用，不包含原研究 JSON/CSV、请求记录或原文响应；文中这些记录名仅说明原研究方法，不表示此仓库提供附件。

此页为原报告的核读范围及公开链接索引，不是完整网页原文存档。

## 来源索引

统计截止：2026-10-17 12:00 UTC；本次复核：2026-10-17 14:52 UTC 起。以下链接全部指向公开官方来源。

## 官方渠道

- [Kafka Community](https://kafka.apache.org/community/)：Project JIRA 与 GitHub PR 工作流。
- [JIRA KAFKA 项目 REST](https://issues.apache.org/jira/rest/api/2/project/KAFKA)：项目及 Fix Version 的 released 元数据。
- [Kafka 下载与发行记录](https://kafka.apache.org/community/downloads/)：核验是否正式发行。

## 查询和完整分页

### new

JQL：project = KAFKA AND created >= "2026-10-10 12:00" AND created < "2026-10-17 12:00" ORDER BY created ASC, key ASC

总数：45；完整分页：0→25, 25→20。

- [startAt=0，返回25项](https://issues.apache.org/jira/rest/api/2/search?jql=project+%3D+KAFKA+AND+created+%3E%3D+%222026-10-10+12%3A00%22+AND+created+%3C+%222026-10-17+12%3A00%22+ORDER+BY+created+ASC%2C+key+ASC&startAt=0&maxResults=25&fields=summary%2Ccreated%2Cupdated%2Cresolutiondate%2Cstatus%2Cresolution%2Cissuetype%2Cpriority%2Ccomponents%2Cversions%2CfixVersions%2Clabels%2Cdescription%2Cissuelinks%2Cparent%2Csubtasks%2Ccomment&expand=changelog)；读取：2026-10-17T14:52:55.486589+00:00
- [startAt=25，返回20项](https://issues.apache.org/jira/rest/api/2/search?jql=project+%3D+KAFKA+AND+created+%3E%3D+%222026-10-10+12%3A00%22+AND+created+%3C+%222026-10-17+12%3A00%22+ORDER+BY+created+ASC%2C+key+ASC&startAt=25&maxResults=25&fields=summary%2Ccreated%2Cupdated%2Cresolutiondate%2Cstatus%2Cresolution%2Cissuetype%2Cpriority%2Ccomponents%2Cversions%2CfixVersions%2Clabels%2Cdescription%2Cissuelinks%2Cparent%2Csubtasks%2Ccomment&expand=changelog)；读取：2026-10-17T14:53:00.774104+00:00

### resolved

JQL：project = KAFKA AND resolutiondate >= "2026-10-10 12:00" AND resolutiondate < "2026-10-17 12:00" ORDER BY resolutiondate ASC, key ASC

总数：24；完整分页：0→24。

- [startAt=0，返回24项](https://issues.apache.org/jira/rest/api/2/search?jql=project+%3D+KAFKA+AND+resolutiondate+%3E%3D+%222026-10-10+12%3A00%22+AND+resolutiondate+%3C+%222026-10-17+12%3A00%22+ORDER+BY+resolutiondate+ASC%2C+key+ASC&startAt=0&maxResults=25&fields=summary%2Ccreated%2Cupdated%2Cresolutiondate%2Cstatus%2Cresolution%2Cissuetype%2Cpriority%2Ccomponents%2Cversions%2CfixVersions%2Clabels%2Cdescription%2Cissuelinks%2Cparent%2Csubtasks%2Ccomment&expand=changelog)；读取：2026-10-17T14:53:04.129555+00:00

### status_resolved

JQL：project = KAFKA AND status CHANGED TO Resolved DURING ("2026-10-10 12:00", "2026-10-17 12:00") ORDER BY key ASC

总数：24；完整分页：0→24。

- [startAt=0，返回24项](https://issues.apache.org/jira/rest/api/2/search?jql=project+%3D+KAFKA+AND+status+CHANGED+TO+Resolved+DURING+%28%222026-10-10+12%3A00%22%2C+%222026-10-17+12%3A00%22%29+ORDER+BY+key+ASC&startAt=0&maxResults=25&fields=summary%2Ccreated%2Cupdated%2Cresolutiondate%2Cstatus%2Cresolution%2Cissuetype%2Cpriority%2Ccomponents%2Cversions%2CfixVersions%2Clabels%2Cdescription%2Cissuelinks%2Cparent%2Csubtasks%2Ccomment&expand=changelog)；读取：2026-10-17T14:53:09.797946+00:00

### status_closed

JQL：project = KAFKA AND status CHANGED TO Closed DURING ("2026-10-10 12:00", "2026-10-17 12:00") ORDER BY key ASC

总数：0；完整分页：0→0。

- [startAt=0，返回0项](https://issues.apache.org/jira/rest/api/2/search?jql=project+%3D+KAFKA+AND+status+CHANGED+TO+Closed+DURING+%28%222026-10-10+12%3A00%22%2C+%222026-10-17+12%3A00%22%29+ORDER+BY+key+ASC&startAt=0&maxResults=25&fields=summary%2Ccreated%2Cupdated%2Cresolutiondate%2Cstatus%2Cresolution%2Cissuetype%2Cpriority%2Ccomponents%2Cversions%2CfixVersions%2Clabels%2Cdescription%2Cissuelinks%2Cparent%2Csubtasks%2Ccomment&expand=changelog)；读取：2026-10-17T14:53:13.891923+00:00

### status_reopened

JQL：project = KAFKA AND status CHANGED TO Reopened DURING ("2026-10-10 12:00", "2026-10-17 12:00") ORDER BY key ASC

总数：0；完整分页：0→0。

- [startAt=0，返回0项](https://issues.apache.org/jira/rest/api/2/search?jql=project+%3D+KAFKA+AND+status+CHANGED+TO+Reopened+DURING+%28%222026-10-10+12%3A00%22%2C+%222026-10-17+12%3A00%22%29+ORDER+BY+key+ASC&startAt=0&maxResults=25&fields=summary%2Ccreated%2Cupdated%2Cresolutiondate%2Cstatus%2Cresolution%2Cissuetype%2Cpriority%2Ccomponents%2Cversions%2CfixVersions%2Clabels%2Cdescription%2Cissuelinks%2Cparent%2Csubtasks%2Ccomment&expand=changelog)；读取：2026-10-17T14:53:16.635409+00:00

### new_utc_check

JQL：project = KAFKA AND created >= "2026-10-09" AND created < "2026-10-19" ORDER BY created ASC, key ASC

总数：54；完整分页：0→25, 25→25, 50→4。

- [startAt=0，返回25项](https://issues.apache.org/jira/rest/api/2/search?jql=project+%3D+KAFKA+AND+created+%3E%3D+%222026-10-09%22+AND+created+%3C+%222026-10-19%22+ORDER+BY+created+ASC%2C+key+ASC&startAt=0&maxResults=25&fields=summary%2Ccreated%2Cupdated%2Cresolutiondate%2Cstatus%2Cresolution%2Cissuetype%2Cpriority%2Ccomponents%2Cversions%2CfixVersions%2Clabels%2Cdescription%2Cissuelinks%2Cparent%2Csubtasks%2Ccomment&expand=changelog)；读取：2026-10-17T14:53:19.685024+00:00
- [startAt=25，返回25项](https://issues.apache.org/jira/rest/api/2/search?jql=project+%3D+KAFKA+AND+created+%3E%3D+%222026-10-09%22+AND+created+%3C+%222026-10-19%22+ORDER+BY+created+ASC%2C+key+ASC&startAt=25&maxResults=25&fields=summary%2Ccreated%2Cupdated%2Cresolutiondate%2Cstatus%2Cresolution%2Cissuetype%2Cpriority%2Ccomponents%2Cversions%2CfixVersions%2Clabels%2Cdescription%2Cissuelinks%2Cparent%2Csubtasks%2Ccomment&expand=changelog)；读取：2026-10-17T14:53:24.404379+00:00
- [startAt=50，返回4项](https://issues.apache.org/jira/rest/api/2/search?jql=project+%3D+KAFKA+AND+created+%3E%3D+%222026-10-09%22+AND+created+%3C+%222026-10-19%22+ORDER+BY+created+ASC%2C+key+ASC&startAt=50&maxResults=25&fields=summary%2Ccreated%2Cupdated%2Cresolutiondate%2Cstatus%2Cresolution%2Cissuetype%2Cpriority%2Ccomponents%2Cversions%2CfixVersions%2Clabels%2Cdescription%2Cissuelinks%2Cparent%2Csubtasks%2Ccomment&expand=changelog)；读取：2026-10-17T14:53:27.604839+00:00

### resolved_utc_check

JQL：project = KAFKA AND resolutiondate >= "2026-10-09" AND resolutiondate < "2026-10-19" ORDER BY resolutiondate ASC, key ASC

总数：30；完整分页：0→25, 25→5。

- [startAt=0，返回25项](https://issues.apache.org/jira/rest/api/2/search?jql=project+%3D+KAFKA+AND+resolutiondate+%3E%3D+%222026-10-09%22+AND+resolutiondate+%3C+%222026-10-19%22+ORDER+BY+resolutiondate+ASC%2C+key+ASC&startAt=0&maxResults=25&fields=summary%2Ccreated%2Cupdated%2Cresolutiondate%2Cstatus%2Cresolution%2Cissuetype%2Cpriority%2Ccomponents%2Cversions%2CfixVersions%2Clabels%2Cdescription%2Cissuelinks%2Cparent%2Csubtasks%2Ccomment&expand=changelog)；读取：2026-10-17T14:53:31.064388+00:00
- [startAt=25，返回5项](https://issues.apache.org/jira/rest/api/2/search?jql=project+%3D+KAFKA+AND+resolutiondate+%3E%3D+%222026-10-09%22+AND+resolutiondate+%3C+%222026-10-19%22+ORDER+BY+resolutiondate+ASC%2C+key+ASC&startAt=25&maxResults=25&fields=summary%2Ccreated%2Cupdated%2Cresolutiondate%2Cstatus%2Cresolution%2Cissuetype%2Cpriority%2Ccomponents%2Cversions%2CfixVersions%2Clabels%2Cdescription%2Cissuelinks%2Cparent%2Csubtasks%2Ccomment&expand=changelog)；读取：2026-10-17T14:53:34.974335+00:00

## 逐项详情复核方法

附录每个 issue 编号链接到官方 JIRA 原文；PR 编号链接到官方 GitHub。技术深读使用对应 issue 的 REST description/comment/changelog、remotelink 以及 GitHub PR、review、最终 commit patch。

统计使用原始 UTC 字段精筛，并对照 status transition；查询当前集合不等于永久历史快照，因此本次明确保留检索时间和截点后更新说明。本文件保留上述可重查的查询链接及完整条目表。

## 重点一手证据

- [KAFKA-21253](https://issues.apache.org/jira/browse/KAFKA-21253)、[#23791](https://github.com/apache/kafka/pull/23791)、[最终代码](https://github.com/apache/kafka/commit/dfd3dcab0756a8574105db4c159ed19d500bcef7)
- [KAFKA-14302](https://issues.apache.org/jira/browse/KAFKA-14302)、[#23298](https://github.com/apache/kafka/pull/23298)、[后续 #23841](https://github.com/apache/kafka/pull/23841)
- [KAFKA-21142](https://issues.apache.org/jira/browse/KAFKA-21142)、[#23610](https://github.com/apache/kafka/pull/23610)、[最终代码](https://github.com/apache/kafka/commit/daebfbd9b37c913937d5adfc2e493fe825e3da3a)
- [KAFKA-21222](https://issues.apache.org/jira/browse/KAFKA-21222)、[21223](https://issues.apache.org/jira/browse/KAFKA-21223)、[KIP-1279](https://cwiki.apache.org/confluence/spaces/KAFKA/pages/406620973/KIP-1279%2BCluster%2BMirroring)
- [KAFKA-21298](https://issues.apache.org/jira/browse/KAFKA-21298)、[#23848](https://github.com/apache/kafka/pull/23848)
- [KAFKA-21300](https://issues.apache.org/jira/browse/KAFKA-21300)、[#23849](https://github.com/apache/kafka/pull/23849)
- [KAFKA-21276](https://issues.apache.org/jira/browse/KAFKA-21276)、[#23815](https://github.com/apache/kafka/pull/23815)、[review 关注暂停后 limit 更新](https://github.com/apache/kafka/pull/23815#discussion_r4298052661)
- [KAFKA-21295](https://issues.apache.org/jira/browse/KAFKA-21295)、[#23844](https://github.com/apache/kafka/pull/23844)

本索引不转录评论全文、作者资料或个人联系方式。


## 原报告其他公开引用

- https://bryantchang1992.github.io/ai_memory_chang_ai_team/stream-storage-observer/2026-10-16/
- https://cwiki.apache.org/confluence/spaces/KAFKA/pages/421957079/KIP-1325+Add+restore.buffered.records.per.partition+to+cap+Kafka+Streams+state-restore+memory
- https://github.com/BryantChang1992/ai_wikis/blob/master/知识库/专题跟踪/KIP-1150/README.md
- https://github.com/apache/kafka
- https://github.com/apache/kafka/commit/05f0edf48ead2bf05141d100af2ae914ef9bb91a
- https://github.com/apache/kafka/commit/2556fc948fe46f09382e0126e771fe5d5602ac30
- https://github.com/apache/kafka/commit/614efd6e0f14f59076468a13d5dbab09038ca2ad
- https://github.com/apache/kafka/commit/65566690ca1ddb584388c1026e2ff6673e9c6f19
- https://github.com/apache/kafka/commit/904491fffb9bb3f7e17fff5863442db926191b24
- https://github.com/apache/kafka/commit/b2f85364e44abfea2bb1937d894b36edae80b968
- https://github.com/apache/kafka/pull/13836
- https://github.com/apache/kafka/pull/21308
- https://github.com/apache/kafka/pull/21754
- https://github.com/apache/kafka/pull/22831
- https://github.com/apache/kafka/pull/22901
- https://github.com/apache/kafka/pull/23280
- https://github.com/apache/kafka/pull/23381
- https://github.com/apache/kafka/pull/23388
- https://github.com/apache/kafka/pull/23427
- https://github.com/apache/kafka/pull/23529
- https://github.com/apache/kafka/pull/23544
- https://github.com/apache/kafka/pull/23557
- https://github.com/apache/kafka/pull/23566
- https://github.com/apache/kafka/pull/23651
- https://github.com/apache/kafka/pull/23687
- https://github.com/apache/kafka/pull/23716
- https://github.com/apache/kafka/pull/23729
- https://github.com/apache/kafka/pull/23738
- https://github.com/apache/kafka/pull/23770
- https://github.com/apache/kafka/pull/23773
- https://github.com/apache/kafka/pull/23781
- https://github.com/apache/kafka/pull/23782
- https://github.com/apache/kafka/pull/23785
- https://github.com/apache/kafka/pull/23787
- https://github.com/apache/kafka/pull/23789
- https://github.com/apache/kafka/pull/23797
- https://github.com/apache/kafka/pull/23800
- https://github.com/apache/kafka/pull/23808
- https://github.com/apache/kafka/pull/23810
- https://github.com/apache/kafka/pull/23814
- https://github.com/apache/kafka/pull/23818
- https://github.com/apache/kafka/pull/23819
- https://github.com/apache/kafka/pull/23824
- https://github.com/apache/kafka/pull/23826
- https://github.com/apache/kafka/pull/23827
- https://github.com/apache/kafka/pull/23830
- https://github.com/apache/kafka/pull/23832
- https://github.com/apache/kafka/pull/23833
- https://github.com/apache/kafka/pull/23840
- https://github.com/apache/kafka/pull/23842
- https://github.com/apache/kafka/pull/23852
- https://issues.apache.org/jira/browse/KAFKA-14218
- https://issues.apache.org/jira/browse/KAFKA-14333
- https://issues.apache.org/jira/browse/KAFKA-19023
- https://issues.apache.org/jira/browse/KAFKA-19804
- https://issues.apache.org/jira/browse/KAFKA-19979
- https://issues.apache.org/jira/browse/KAFKA-20278
- https://issues.apache.org/jira/browse/KAFKA-20924
- https://issues.apache.org/jira/browse/KAFKA-21019
- https://issues.apache.org/jira/browse/KAFKA-21079
- https://issues.apache.org/jira/browse/KAFKA-21080
- https://issues.apache.org/jira/browse/KAFKA-21110
- https://issues.apache.org/jira/browse/KAFKA-21143
- https://issues.apache.org/jira/browse/KAFKA-21151
- https://issues.apache.org/jira/browse/KAFKA-21153
- https://issues.apache.org/jira/browse/KAFKA-21235
- https://issues.apache.org/jira/browse/KAFKA-21256
- https://issues.apache.org/jira/browse/KAFKA-21257
- https://issues.apache.org/jira/browse/KAFKA-21258
- https://issues.apache.org/jira/browse/KAFKA-21259
- https://issues.apache.org/jira/browse/KAFKA-21260
- https://issues.apache.org/jira/browse/KAFKA-21261
- https://issues.apache.org/jira/browse/KAFKA-21262
- https://issues.apache.org/jira/browse/KAFKA-21263
- https://issues.apache.org/jira/browse/KAFKA-21264
- https://issues.apache.org/jira/browse/KAFKA-21265
- https://issues.apache.org/jira/browse/KAFKA-21266
- https://issues.apache.org/jira/browse/KAFKA-21267
- https://issues.apache.org/jira/browse/KAFKA-21268
- https://issues.apache.org/jira/browse/KAFKA-21269
- https://issues.apache.org/jira/browse/KAFKA-21270
- https://issues.apache.org/jira/browse/KAFKA-21271
- https://issues.apache.org/jira/browse/KAFKA-21272
- https://issues.apache.org/jira/browse/KAFKA-21273
- https://issues.apache.org/jira/browse/KAFKA-21274
- https://issues.apache.org/jira/browse/KAFKA-21275
- https://issues.apache.org/jira/browse/KAFKA-21277
- https://issues.apache.org/jira/browse/KAFKA-21278
- https://issues.apache.org/jira/browse/KAFKA-21279
- https://issues.apache.org/jira/browse/KAFKA-21280
- https://issues.apache.org/jira/browse/KAFKA-21281
- https://issues.apache.org/jira/browse/KAFKA-21282
- https://issues.apache.org/jira/browse/KAFKA-21283
- https://issues.apache.org/jira/browse/KAFKA-21284
- https://issues.apache.org/jira/browse/KAFKA-21285
- https://issues.apache.org/jira/browse/KAFKA-21286
- https://issues.apache.org/jira/browse/KAFKA-21287
- https://issues.apache.org/jira/browse/KAFKA-21288
- https://issues.apache.org/jira/browse/KAFKA-21289
- https://issues.apache.org/jira/browse/KAFKA-21290
- https://issues.apache.org/jira/browse/KAFKA-21291
- https://issues.apache.org/jira/browse/KAFKA-21292
- https://issues.apache.org/jira/browse/KAFKA-21293
- https://issues.apache.org/jira/browse/KAFKA-21294
- https://issues.apache.org/jira/browse/KAFKA-21296
- https://issues.apache.org/jira/browse/KAFKA-21297
- https://issues.apache.org/jira/browse/KAFKA-21299
- https://issues.apache.org/jira/browse/KAFKA-7693
- https://issues.apache.org/jira/projects/KAFKA/summary
