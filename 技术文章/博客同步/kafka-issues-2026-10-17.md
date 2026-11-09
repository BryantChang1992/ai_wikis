---
type: survey
title: Kafka Issue 周报 第 1 期：恢复进度、迁移快照与修复证据
sources:
- https://issues.apache.org/jira/projects/KAFKA/summary
- https://github.com/apache/kafka
tags:
- Kafka
- issue
- 社区观察
created: '2026-11-09'
updated: '2026-11-09'
status: draft
source_checked: '2026-10-17'
source_check_scope: 沿用原报告 2026-10-17 的官方 JIRA、PR、最终提交及发行记录核读；正文检索与附录后续复核时间分别保留，未独立复现。
related:
- '[[知识库/sources/web/Kafka-Issue-2026-10-17]]'
publication_scope: 公开技术报告及引用；知识卡和独立专题不因本文同步而扩大发布范围。在线状态以实际部署验收为准。
report_date: '2026-10-17'
---

# Kafka Issue 周报 第 1 期

> 阅读时间说明：本文保留 2026-10-17 报告的观察窗口、原文核验时间和技术限制。正文中的“本周”、版本阶段及历史交付说明均按原观察时点理解，不代表本次页面整理时的最新状态。本次仅适配发布格式，未重新核读全部外部来源或独立复现实验。

[公开来源索引](../../知识库/sources/web/Kafka-Issue-2026-10-17.md)

## 恢复进度、迁移快照与修复证据

说明：正文依据 2026-10-17 12:15 UTC 前的检索；附录注明后续复核时间，观察截止仍为 12:00 UTC，不计入此后发生的事件。



观察窗口：2026-10-10 12:00 至 2026-10-17 12:00 UTC，左闭右开；对应北京时间 10 月 10 日 20:00 至 10 月 17 日 20:00。本文以 Apache Kafka 官方 JIRA 为 issue 来源，结合完整讨论、GitHub PR 与最终提交核验落地状态。检索截止：2026-10-17 12:15 UTC；测试结果来自上游报告，本文未独立运行复现。

本周最值得追踪的是两种相反的恢复进度失真：旧 offset 被带进重建后的状态库，制造“假超前”并跳过恢复；空 changelog 已经追平，却仍上报 offset=0，制造“假落后”并触发无尽 rebalance。两项修复均已合入并回移，但目标版本尚未正式发行。与此同时，新报告继续暴露任务重建、快照回滚和 standby 预取边界上的缺口。

## 先把“解决”数清楚

| 口径 | 数量 | 应如何理解 |
|---|---:|---|
| 本周新建 | 45 | 其中 22 Bug、12 Improvement、6 Sub-task、3 Test、2 Task |
| 本周设置 resolution、进入 Resolved | 24 | 两种查询的 issue 集合一致 |
| resolution=Fixed | 20 | 包括改进和子任务，不能都称为 bug 修复 |
| resolution=Duplicate | 2 | 旧问题归并，不是两个独立新修复 |
| resolution=Done / Resolved | 各 1 | Cluster Mirroring 的配置子任务 |
| 本周迁移至 Closed / Reopened | 0 / 0 | 状态迁移数，不是当前存量 |

新建与解决集合重叠 5 项，因此两份清单有 69 条分类记录、64 个唯一 issue。完整标题、时间、状态、目标版本及关联 PR 见[本期全量清单](#附录完整清单)。

[官方社区页](https://kafka.apache.org/community/)仍把 Project JIRA 作为开发问题入口，把 GitHub 用于 PR 工作流。本期按 created、resolutiondate 查询，使用 status CHANGED TO Resolved/Closed/Reopened 独立对账；宽日期查询再按 JSON 原始 UTC 时间筛选，避免依赖页面显示时间。首次新建宽窗分页取回 25+21 项，精筛为 45；解决宽窗完整取回 24 项。附录复核采用更宽日期范围，列出的分页数不同，但相同 UTC 窗口精筛后仍为 45 / 24。统计是对这些查询的完整枚举，以下深读则是选题，不代表每个 issue 都经过同等深度的代码审计。

## 一、已经解决：三个需要看最终代码的案例

### 1. KAFKA-21253：abort 失败后，旧 offset 不能跟着任务复活

[KAFKA-21253](https://issues.apache.org/jira/browse/KAFKA-21253) 于 10 月 9 日创建，本周 10 月 15 日 20:38 UTC 标记为 Resolved / Fixed，所以它属于“本周解决”，不属于“本周新增”。

触发链发生在 exactly-once：commitTransaction 超时后，producer 仍有未确认完成的 commit；随后 abortTransaction 抛出 IllegalStateException。旧 closeDirty 先 abort、后 close，前者失败使后者不能清空 changelog offset。任务 revive 后状态库已经擦除，collector 却保留旧位点；如果恢复未完成就再次 clean-close，过高 offset 被写入 checkpoint，下次恢复跳过缺失记录。

[PR #23791](https://github.com/apache/kafka/pull/23791) 于 10 月 15 日 20:37 UTC 合入 trunk。最终 [dfd3dcab](https://github.com/apache/kafka/commit/dfd3dcab0756a8574105db4c159ed19d500bcef7) 的做法是，在 finally 中直接 offsets.clear() 和 sendException.set(null)，同时把 TaskManager 的 unclean-close 日志改为 WARN 并带上异常。这样既清除旧恢复位点，也避免旧异步异常污染复活任务。

这是一个必须越过 PR 摘要看代码的案例：摘要还写着“把 close 放进 finally”及 ERROR 日志，最终实现已根据 review 改变。评审指出，finally 中调用会抛错的 close 可能覆盖原 abort 异常；最终没有采用那种写法。

作者报告集成测试负载复跑 20/20 通过，并补了 abort 抛错后 offset map 仍清空的单测。代码已回移到 [4.4：614efd6e](https://github.com/apache/kafka/commit/614efd6e0f14f59076468a13d5dbab09038ca2ad) 和 [4.3：05f0edf4](https://github.com/apache/kafka/commit/05f0edf48ead2bf05141d100af2ae914ef9bb91a)。回移提交也说明：故障代理仅在 trunk 存在，所以该集成测试未一起回移。不能把“已回移”写成所有分支拥有完全相同的验证覆盖。

### 2. KAFKA-14302：没有记录可应用，不代表恢复进度是零

[KAFKA-14302](https://issues.apache.org/jira/browse/KAFKA-14302) 是 2022 年的老问题，10 月 15 日 21:49 UTC 终于进入 Resolved / Fixed。窗口清理或 tombstone 会把 changelog 内容清空，但 log-end offset 仍可能很高。实例丢失本地磁盘后恢复，如果只在应用记录时更新位点，就会向分配器上报 0，制造巨大虚假 lag，反复触发 probing rebalance。

[#23298](https://github.com/apache/kafka/pull/23298) 的最终 [b2f85364](https://github.com/apache/kafka/commit/b2f85364e44abfea2bb1937d894b36edae80b968) 允许在恢复已达到可证明的结束边界时推进 offset，并保持内部 last-applied=next-fetch−1 的语义、禁止倒退。边界条件比“空 poll 后设为最新”严格得多：

- active 恢复完成时推进到 restoreEndOffset，不使用可能越过未应用 buffer 的实时 position
- standby 先确认 buffer 为空；独立 changelog 要 currentLag=0，复用 source topic 则最多推进到 active 已提交的 limit
- 一次没有返回记录的 poll，本身不能证明已经追平

修复已回移 [4.4：904491ff](https://github.com/apache/kafka/commit/904491fffb9bb3f7e17fff5863442db926191b24)。但工程闭环还多一步：10 月 16 日 21:33 UTC，后续 [#23841](https://github.com/apache/kafka/pull/23841) 修掉这条新路径中的阻塞 position()。恢复循环会检查包括 paused standby 的分区，未解析的位置可能等待 default.api.timeout.ms，拖住 state-updater。最终 [65566690](https://github.com/apache/kafka/commit/65566690ca1ddb584388c1026e2ff6673e9c6f19) 使用 Duration.ZERO，超时保留原位点、下轮重试，也已回移 [4.4：2556fc94](https://github.com/apache/kafka/commit/2556fc948fe46f09382e0126e771fe5d5602ac30)。这项后续 PR 没有新 JIRA，不能另算一个新增 issue。

### 3. KAFKA-21142：双写恢复时，缺失的 ZK state 必须真的重建

[KAFKA-21142](https://issues.apache.org/jira/browse/KAFKA-21142) 于 10 月 16 日 19:39 UTC Resolved / Fixed。[#23610](https://github.com/apache/kafka/pull/23610) 同分钟直接合入 3.9 分支，提交为 [daebfbd9](https://github.com/apache/kafka/commit/daebfbd9b37c913937d5adfc2e493fe825e3da3a)，证据链不是“先合主干再回移”。

在 ZooKeeper→KRaft 迁移的 dual-write 阶段，扩分区请求已更新 KRaft 元数据，controller leader 却在同步 ZK 完成前崩溃。新 leader 用 snapshot 修复时，对不存在的分区 /state znode 调用了 update；重试又可能被读取层合成的 placeholder state 误导，最终没有把缺失状态补上。

最终 patch 一方面将新分区写入改为 createTopicPartitions，另一方面新增 visitPartitionWithoutState 回调，把两种方向的“来源真相”区分开：ZK→KRaft 初始迁移仍可合成缺失 state，避免丢弃已有 assignment；KRaft→ZK 双写恢复则不合成，让写入端据 KRaft 状态重建。PR 描述还保留 enum 方案的旧措辞，最终采用的是 visitor 方法。

上述三项属于具体实现缺陷修复；本轮未在对应 Issue/PR 核到明示的直接 KIP 关联，因此不凭所属子系统倒推“由某 KIP 解决”。

### 合并、回移、发行是三个不同状态

| Issue | 已核验代码落点 | JIRA Fix Version | 正式发行核验 |
|---|---|---|---|
| 21253 | trunk；4.4、4.3 均有实际回移 commit | 4.5.0 / 4.4.1 / 4.3.3 | 均未发行 |
| 14302 | trunk；4.4 回移；后续 #23841 也进入两分支 | 4.5.0 / 4.4.1 | 均未发行 |
| 21142 | 直接合入 3.9 | 3.9.3 | 未发行 |

上述版本的 JIRA released 均为 false，[官方下载页](https://kafka.apache.org/community/downloads/)也尚未列出这些发行；3.9.2 仍在 Archived Releases。不能把 fixVersion 目标当作可下载版本，也不能从一个 3.9 patch 推导出整个旧系列恢复一般性维护承诺。

## 二、KIP 实现任务完成，不等于整项能力上线

[KAFKA-21222](https://issues.apache.org/jira/browse/KAFKA-21222) 与 [KAFKA-21223](https://issues.apache.org/jira/browse/KAFKA-21223) 分别在 10 月 12 日 03:22、10 月 15 日 01:23 UTC 解决；resolution 的原值分别是 Resolved 和 Done。它们对应 [KIP-1279 Cluster Mirroring](https://cwiki.apache.org/confluence/spaces/KAFKA/pages/406620973/KIP-1279%2BCluster%2BMirroring) 的 broker/topic 配置任务，PR 正文明确建立了关联。

[#23729](https://github.com/apache/kafka/pull/23729)、[#23797](https://github.com/apache/kafka/pull/23797) 与 [#23782](https://github.com/apache/kafka/pull/23782) 已合入，但新配置暂时标为 internal，等待 early access 准备好再对用户暴露。目标 4.5.0 也未发行。因此本周能确认的是配置基础落地，不能把这两个已完成子任务写成 Cluster Mirroring 全功能交付。#23797 在 issue 已 resolved 后继续补第二部分，也提醒我们 resolutiondate 不是后续实现活动的终点。

另两个非 Fixed 条目是归并：[21079](https://issues.apache.org/jira/browse/KAFKA-21079) 被判为 20721 的 Duplicate；[21080](https://issues.apache.org/jira/browse/KAFKA-21080) 的维护者评论明确指向 19960，并设置 Duplicate。本期没有 Won't Fix 条目。

## 三、四个新增问题：先看触发条件，再看修复成熟度

| 新 Issue | 创建时间 UTC | 检索时状态 | 已核实 PR | 修复版本 |
|---|---|---|---|---|
| [21298](https://issues.apache.org/jira/browse/KAFKA-21298) | 10-17 06:22 | Open | [#23848](https://github.com/apache/kafka/pull/23848)，未合并 | 未填写 |
| [21300](https://issues.apache.org/jira/browse/KAFKA-21300) | 10-17 07:38 | Open | [#23849](https://github.com/apache/kafka/pull/23849)，未合并 | 未填写 |
| [21276](https://issues.apache.org/jira/browse/KAFKA-21276) | 10-14 07:59 | Open | [#23815](https://github.com/apache/kafka/pull/23815)，评审中、未合并 | 未填写 |
| [21295](https://issues.apache.org/jira/browse/KAFKA-21295) | 10-16 13:55 | Patch Available | [#23844](https://github.com/apache/kafka/pull/23844)，未合并 | 未填写 |

### 21298：pending offset reset 不能只活在旧 task 实例中

报告描述：同一 StreamThread 的两个任务共享事务，局部 rebalance 仅撤销 A、保留 B；提交超时引起 abort，B 已处理但未提交的一段输出也被丢弃。B 应回退重放，但 reset 义务仍记在旧 task 里。若真正 reset 前再次 assignment、B 被重建，consumer position 却没有回退，新 B 会跳过那一段并提交更高 offset。后续普通重启也会从较高提交位点继续，不能自动补回漏掉的输出。

候选补丁把 reset 义务保存在 TaskManager、按 TaskId 跨重建移交，并在 replacement task 初始化前恢复。新增测试覆盖初始化重试、重复 assignment、失去任务等路径。这里是“EOS 处理结果可能遗漏”的报告，不是输入日志物理丢失；目前无 review、无明确影响版本，也没有已发布修复。

### 21300：map 能回滚，里面被原地修改的集合未必能

Streams group coordinator 的 task ownership 索引使用 TimelineHashMap，但 value 是可变 HashSet。成员分配记录写日志失败后，snapshot 能恢复 member assignment，却不能撤销集合的原地修改。结果可能残留虚假 standby owner，把本来合法的 active 分配挡在 UNRELEASED_TASKS；反向也可能漏掉真实 owner，错误允许同进程角色冲突。

拟议修复是 copy-on-write，先复制集合再 put 回 timeline map，并为 standby/warm-up 的增加、删除与回滚加测试。官方 priority 是 Minor，不能擅自写成上游标注 Critical；单任务应用停滞是报告给出的后果。持久 state directory 可能复用 process ID，因此简单重启不保证解开虚假 owner。

### 21276：standby 越过可应用上限预取，buffer 会累积

当 KTable 复用 source topic 作为 changelog 时，standby 只能应用到 active 已提交的 offset。报告指出 StoreChangelogReader 仍不断向后 fetch，把越界记录留在堆内，active 落后较多时 buffer 可无界增长。作者提供故障日志、复现程序和修复前后比较；正式 Affects Version 字段为 4.3.1，不能把作者对历史版本的追溯当成本报告独立验证。

[#23815](https://github.com/apache/kafka/pull/23815) 拟在越过 limit 的记录尚留在 buffer 时 pause 分区，limit 推进后再 resume。10 月 16 日 [review](https://github.com/apache/kafka/pull/23815#discussion_r4298052661) 特别要求确保 paused standby 的 bufferedLimitIndex 继续更新，否则防 OOM 的暂停本身可能变成永久停滞。当前只是 COMMENTED，不是批准或合并。

它与已 Accepted 的 [KIP-1325](https://cwiki.apache.org/confluence/spaces/KAFKA/pages/421957079/KIP-1325+Add+restore.buffered.records.per.partition+to+cap+Kafka+Streams+state-restore+memory) 相关，但后者讨论通用可配置 buffer 上限；本 issue 是 committed-offset 边界上的回压。两者不能互相代替完成状态。讨论中的关闭 source-topic 复用可能改变拓扑并要求重处理，暂时关闭 standby 则牺牲故障接管能力，均不应写成无代价的操作建议。

### 21295：序号回绕修好了普通发送，分拆路径仍可能遗漏

Producer 的 per-partition sequence 接近 2^31，一个跨界 batch 又被 MESSAGE_TOO_LARGE 拒绝并 split 时，普通整数加法可能给某个拆分片段分配负 base sequence。[#23844](https://github.com/apache/kafka/pull/23844) 拟复用 DefaultRecordBatch.incrementSequence，新增 MAX_INT→0 的分拆单测。

关联的 [KAFKA-7693](https://issues.apache.org/jira/browse/KAFKA-7693) 是普通发送路径的历史修复，不能据此认为所有序号路径早已覆盖。当前是 Patch Available，不是 Fixed；也不能简写成“发送超过 2^31 条必然停顿”。

## 接下来应验证什么

1. 对准备引入 21253/14302 修复的维护分支，核对实际 commit 和后续 #23841，等正式 release notes 出现后再下“已随版本交付”的结论；回移测试覆盖的差异也应保留。
2. 对 21298/21300，下一步证据是 review、merge、影响范围和 backport 决策。PR 标题或候选测试不能替代这些结论。
3. 对 21276，关注暂停后 limit 仍能更新、active 恢复与 standby 切换是否继续前进，以及缓解配置的拓扑和可用性代价。
4. 对[本周新报 21279](https://issues.apache.org/jira/browse/KAFKA-21279)，继续沿[旧问题 19023](https://issues.apache.org/jira/browse/KAFKA-19023)追踪 timer 的 snapshot 方案。维护者认为疑似重复并有人计划 PoC，但新 issue 仍 Open，不能先写成 Duplicate 或已修复。

本期的共同教训是：恢复进度必须对应当前恢复过程已经完成、可证明的边界。旧 collector 位点不能制造假超前；空压缩日志也不该制造假落后；快照、任务重建和暂停状态旁边的辅助状态，同样要保住它们的恢复义务。

## 可复核来源与限制

- [官方 JIRA 项目](https://issues.apache.org/jira/projects/KAFKA/summary)负责 issue 生命周期；[官方 GitHub 仓库](https://github.com/apache/kafka)负责代码与 PR。文章没有把两者混成同一种计数。
- created / resolutiondate 主查询分别为 project=KAFKA，字段 `>= "2026-10-10 12:00" AND < "2026-10-17 12:00"`；排序为事件时间 ASC、key ASC。历史查询使用 `status CHANGED TO Resolved/Closed/Reopened DURING (...)`，再对照原始 UTC 时间。
- 正文状态与版本按 12:15 UTC 的检索读取；当时 64 个入选 JIRA 的 updated 均未超过 12:00 截止。14:52 UTC 后复核已发现若干截点后更新，详见附录，未加入本期事件计数。没有找到 PR、影响版本或正式发行证据的地方保留未知，不用邻近 KIP 的状态填空。
- [完整清单](#附录完整清单)保留原始标题及逐项来源。重点案例已读完整 issue/评论、PR/review 与实际 patch；其余清单是元数据和关联证据核验，不宣称全部做过逐行审计。

精简查询记录、分页数量和关联依据可查 [来源索引](#来源索引)。

## 关联阅读

[流存储技术观察第 2 期](https://bryantchang1992.github.io/ai_memory_chang_ai_team/stream-storage-observer/2026-10-16/)；[KIP-1150 专项](https://github.com/BryantChang1992/ai_wikis/blob/master/知识库/专题跟踪/KIP-1150/README.md)。

## 附录：完整清单

统计窗口：2026-10-10 12:00:00 UTC ≤ 事件时间 < 2026-10-17 12:00:00 UTC。

本附录于 2026-10-17 14:52 UTC 起重新读取官方 JIRA / GitHub 核验；生成时间：2026-10-17T14:56:10.569196+00:00。事件计数仍固定于上述窗口，当前字段是复核时状态，不能把截点后更新当作本周新增事件。

## 覆盖与口径

- 新建 45 项；解决 24 项；两组重叠 5 项，共 64 个唯一 issue。
- 24 项解决中：20 Fixed、2 Duplicate、1 Done、1 Resolved。Fixed 包含改进和子任务，不等于 20 个 bug 修复。
- 独立历史查询确认：本周进入 Resolved 的同样是 24 项；进入 Closed / Reopened 均为 0。
- 新建宽日期查询分 25+25+4 页取回 54 项，按 JSON 原始 UTC 时间精筛为 45；解决宽日期查询分 25+5 页取回 30 项，精筛为 24。两者均与精确查询集合一致。
- 目标版本是 JIRA Fix Version，不自动意味着已 backport 或已正式发行。表中关联 PR 仅在有官方 remote link 等明确证据时列出；没有链接不证明没有代码。
- 本文件只列公开技术信息，不含评论全文或个人联系方式。

## 1. 新建清单（45 项）

| Issue | 原始标题 | 创建 UTC | 类型 | 状态 / resolution | 目标版本 | 关联 PR（复核时） |
|---|---|---|---|---|---|---|
| [KAFKA-21256](https://issues.apache.org/jira/browse/KAFKA-21256) | Assignment callback failure can stall reconciliation in the Streams protocol client | 2026-10-10 14:22 | Bug | In Progress / 未解决 | 未填写 | [#23773](https://github.com/apache/kafka/pull/23773) 未合并 |
| [KAFKA-21257](https://issues.apache.org/jira/browse/KAFKA-21257) | Document tokenless OAUTHBEARER login for validate-only brokers | 2026-10-11 09:09 | Improvement | Open / 未解决 | 未填写 | [#23818](https://github.com/apache/kafka/pull/23818) 未合并 |
| [KAFKA-21258](https://issues.apache.org/jira/browse/KAFKA-21258) | Move the Docker image usage guide from docker/examples/README.md to the website docs | 2026-10-11 12:49 | Improvement | Open / 未解决 | 未填写 | [#23819](https://github.com/apache/kafka/pull/23819) 未合并 |
| [KAFKA-21259](https://issues.apache.org/jira/browse/KAFKA-21259) | Document the case of OffsetOutOfRangeException for Admin#deleteRecords | 2026-10-11 13:14 | Improvement | Open / 未解决 | 未填写 | 未核实关联 PR |
| [KAFKA-21260](https://issues.apache.org/jira/browse/KAFKA-21260) | Drop the Vagrant | 2026-10-11 13:36 | Improvement | Open / 未解决 | 未填写 | 未核实关联 PR |
| [KAFKA-21261](https://issues.apache.org/jira/browse/KAFKA-21261) | Base image for system test dependencies | 2026-10-11 13:52 | Improvement | Open / 未解决 | 未填写 | 未核实关联 PR |
| [KAFKA-21262](https://issues.apache.org/jira/browse/KAFKA-21262) | Flaky share consumer benchmarks: total timeout cap and slow share group startup | 2026-10-12 02:48 | Bug | Open / 未解决 | 未填写 | [#23781](https://github.com/apache/kafka/pull/23781) 未合并 |
| [KAFKA-21263](https://issues.apache.org/jira/browse/KAFKA-21263) | Missing header-aware store variants for stream-stream outer joins | 2026-10-12 11:02 | Sub-task | Patch Available / 未解决 | 未填写 | 未核实关联 PR |
| [KAFKA-21264](https://issues.apache.org/jira/browse/KAFKA-21264) | Javadoc output language depends on the build machine's system locale | 2026-10-12 11:12 | Improvement | Resolved / Fixed | 未填写 | [#23789](https://github.com/apache/kafka/pull/23789) 已合并 |
| [KAFKA-21265](https://issues.apache.org/jira/browse/KAFKA-21265) | DescribeConfigs request fails with UNKNOWN_SERVER_ERROR on internal list config | 2026-10-12 11:31 | Bug | Resolved / Fixed | 4.5.0（未发行） | [#23785](https://github.com/apache/kafka/pull/23785) 已合并 |
| [KAFKA-21266](https://issues.apache.org/jira/browse/KAFKA-21266) | getTopicEffectiveMinIsr should take the replicas from the target partition | 2026-10-12 13:39 | Bug | Open / 未解决 | 未填写 | 未核实关联 PR |
| [KAFKA-21267](https://issues.apache.org/jira/browse/KAFKA-21267) | The empty removing/adding is omitted when calculating the assignment | 2026-10-12 15:23 | Bug | Open / 未解决 | 未填写 | 未核实关联 PR |
| [KAFKA-21268](https://issues.apache.org/jira/browse/KAFKA-21268) | Server, Shell, Storage module: replace temp file handler with JUnit 5 Temporary Directory Support | 2026-10-12 18:21 | Sub-task | Resolved / Fixed | 4.5.0（未发行） | [#23810](https://github.com/apache/kafka/pull/23810) 已合并 |
| [KAFKA-21269](https://issues.apache.org/jira/browse/KAFKA-21269) | Add tests for describing broker configs with raw string values | 2026-10-12 19:02 | Test | Open / 未解决 | 未填写 | 未核实关联 PR |
| [KAFKA-21270](https://issues.apache.org/jira/browse/KAFKA-21270) | Race condition can cause a newly created connector to use initial offsets from another request | 2026-10-12 19:49 | Bug | Open / 未解决 | 未填写 | 未核实关联 PR |
| [KAFKA-21271](https://issues.apache.org/jira/browse/KAFKA-21271) | Use RebalanceConsumer in WorkerSinkTask rebalance callbacks | 2026-10-12 22:49 | Improvement | Open / 未解决 | 4.5.0（未发行） | 未核实关联 PR |
| [KAFKA-21272](https://issues.apache.org/jira/browse/KAFKA-21272) | localLogStartOffset is not advanced when remote storage is enabled on an existing topic | 2026-10-13 16:37 | Bug | Open / 未解决 | 未填写 | 未核实关联 PR |
| [KAFKA-21273](https://issues.apache.org/jira/browse/KAFKA-21273) | Improve refiner performance | 2026-10-13 19:05 | Sub-task | In Progress / 未解决 | 未填写 | 未核实关联 PR |
| [KAFKA-21274](https://issues.apache.org/jira/browse/KAFKA-21274) | Remove unused javax jaxb-api and activation dependencies | 2026-10-13 20:31 | Task | Resolved / Fixed | 未填写 | [#23808](https://github.com/apache/kafka/pull/23808) 已合并 |
| [KAFKA-21275](https://issues.apache.org/jira/browse/KAFKA-21275) | Migrate AuthorizerIntegrationTest to Java and separate protocol-level and client API tests | 2026-10-14 04:28 | Test | Open / 未解决 | 未填写 | 未核实关联 PR |
| [KAFKA-21276](https://issues.apache.org/jira/browse/KAFKA-21276) | Standby task with source-topic changelog fetches and buffers records beyond the committed-offset limit without bound | 2026-10-14 07:59 | Bug | Open / 未解决 | 未填写 | [#23815](https://github.com/apache/kafka/pull/23815) 未合并 |
| [KAFKA-21277](https://issues.apache.org/jira/browse/KAFKA-21277) | Docker image, support KRaft dynamic quorum (KIP-853) controllers | 2026-10-14 08:07 | Improvement | Open / 未解决 | 未填写 | [#23814](https://github.com/apache/kafka/pull/23814) 未合并 |
| [KAFKA-21278](https://issues.apache.org/jira/browse/KAFKA-21278) | interactive-queries.md still states the removed methods | 2026-10-14 10:04 | Improvement | Open / 未解决 | 未填写 | [#23842](https://github.com/apache/kafka/pull/23842) 未合并 |
| [KAFKA-21279](https://issues.apache.org/jira/browse/KAFKA-21279) | Consumer and Streams group leave append failures can lose session timers and stall reassignment | 2026-10-14 13:37 | Bug | Open / 未解决 | 未填写 | 未核实关联 PR |
| [KAFKA-21280](https://issues.apache.org/jira/browse/KAFKA-21280) | SslTransportLayer.transferFrom sends stale buffer contents after a failed file read | 2026-10-14 15:12 | Bug | Open / 未解决 | 未填写 | [#23832](https://github.com/apache/kafka/pull/23832) 未合并 |
| [KAFKA-21281](https://issues.apache.org/jira/browse/KAFKA-21281) | MM2 sync can fail due to controller record limit being hit | 2026-10-14 17:29 | Bug | Open / 未解决 | 未填写 | 未核实关联 PR |
| [KAFKA-21282](https://issues.apache.org/jira/browse/KAFKA-21282) | ThreadMetadata.restoreConsumerClientId() returns the wrong client id for the restore consumer | 2026-10-14 20:34 | Bug | Open / 未解决 | 4.5.0（未发行） | 未核实关联 PR |
| [KAFKA-21283](https://issues.apache.org/jira/browse/KAFKA-21283) | Fix StreamThreadTest teardown race causing thread leaks and cascading test failures | 2026-10-15 03:31 | Test | Open / 未解决 | 未填写 | 未核实关联 PR |
| [KAFKA-21284](https://issues.apache.org/jira/browse/KAFKA-21284) | Upgrade ClassGraph version from 4 to 5 | 2026-10-15 06:57 | Task | Patch Available / 未解决 | 未填写 | [#23824](https://github.com/apache/kafka/pull/23824) 未合并 |
| [KAFKA-21285](https://issues.apache.org/jira/browse/KAFKA-21285) | Dynamic configs less than half the value in server.properties will not take effect after restart in kraft mode | 2026-10-15 07:53 | Bug | In Progress / 未解决 | 未填写 | 未核实关联 PR |
| [KAFKA-21286](https://issues.apache.org/jira/browse/KAFKA-21286) | Share consumer may delay fatal startup errors while waiting for the first heartbeat | 2026-10-15 14:01 | Bug | Open / 未解决 | 未填写 | 未核实关联 PR |
| [KAFKA-21287](https://issues.apache.org/jira/browse/KAFKA-21287) | Fix 'licenses' folder contents and 'LICENSE-binary' file references | 2026-10-15 15:03 | Bug | Patch Available / 未解决 | 未填写 | [#23826](https://github.com/apache/kafka/pull/23826) 未合并 |
| [KAFKA-21288](https://issues.apache.org/jira/browse/KAFKA-21288) | Add MirrorPartitionState | 2026-10-15 16:06 | Sub-task | Open / 未解决 | 未填写 | [#23830](https://github.com/apache/kafka/pull/23830) 未合并 |
| [KAFKA-21289](https://issues.apache.org/jira/browse/KAFKA-21289) | release.py stage-docs writes documentation to the pre-Hugo flat layout instead of the KIP-1133 Hugo layout | 2026-10-15 20:21 | Bug | Resolved / Fixed | 4.5.0（未发行） | [#23833](https://github.com/apache/kafka/pull/23833) 已合并 |
| [KAFKA-21290](https://issues.apache.org/jira/browse/KAFKA-21290) | Add ASF allowlist check to CI workflows | 2026-10-15 21:12 | Improvement | Open / 未解决 | 未填写 | 未核实关联 PR |
| [KAFKA-21291](https://issues.apache.org/jira/browse/KAFKA-21291) | Cleanup AbstractConsumerTest | 2026-10-15 23:13 | Improvement | Open / 未解决 | 未填写 | 未核实关联 PR |
| [KAFKA-21292](https://issues.apache.org/jira/browse/KAFKA-21292) | Update docs of MockConsumer to use RebalanceListener | 2026-10-16 10:26 | Sub-task | Open / 未解决 | 未填写 | 未核实关联 PR |
| [KAFKA-21293](https://issues.apache.org/jira/browse/KAFKA-21293) | SubscriptionState#unsubscribe should not reset the rebalance listener | 2026-10-16 10:43 | Sub-task | Open / 未解决 | 未填写 | [#23852](https://github.com/apache/kafka/pull/23852) 关联已核 |
| [KAFKA-21294](https://issues.apache.org/jira/browse/KAFKA-21294) | The example of "Configuring Production Kafka Brokers" does not work since the login callback is missing | 2026-10-16 11:11 | Bug | Open / 未解决 | 未填写 | [#23840](https://github.com/apache/kafka/pull/23840) 未合并；截点后有更新 |
| [KAFKA-21295](https://issues.apache.org/jira/browse/KAFKA-21295) | Kafka Producer stalls when crossing seqnum 2^31 with MESSAGE_TOO_LARGE | 2026-10-16 13:55 | Bug | Patch Available / 未解决 | 未填写 | [#23844](https://github.com/apache/kafka/pull/23844) 未合并 |
| [KAFKA-21296](https://issues.apache.org/jira/browse/KAFKA-21296) | OAuth login calls do not apply default timeouts as defined in KIP-768 | 2026-10-16 14:56 | Bug | Open / 未解决 | 未填写 | 未核实关联 PR |
| [KAFKA-21297](https://issues.apache.org/jira/browse/KAFKA-21297) | Refactor the maybeUpdateLimitOffsetsForStandbyChangelogs | 2026-10-16 18:31 | Improvement | Open / 未解决 | 未填写 | 未核实关联 PR |
| [KAFKA-21298](https://issues.apache.org/jira/browse/KAFKA-21298) | Pending offset resets are lost during task recreation, causing missing processing results under exactly-once semantics | 2026-10-17 06:22 | Bug | Open / 未解决 | 未填写 | [#23848](https://github.com/apache/kafka/pull/23848) 未合并 |
| [KAFKA-21299](https://issues.apache.org/jira/browse/KAFKA-21299) | Gradle 9.8.1 wrapper jar can’t be fetched from the release tag | 2026-10-17 07:26 | Bug | Patch Available / 未解决 | 未填写 | [#23770](https://github.com/apache/kafka/pull/23770) 未合并；截点后有更新 |
| [KAFKA-21300](https://issues.apache.org/jira/browse/KAFKA-21300) | Streams group task ownership index is not rolled back, blocking valid task assignments | 2026-10-17 07:38 | Bug | Open / 未解决 | 未填写 | [#23849](https://github.com/apache/kafka/pull/23849) 未合并 |

## 2. 解决清单（24 项）

解决时间依据 resolutiondate，非 PR 合并时间；PR 可能早于本周合并，也可能在 issue 解决后继续追加实现。

| Issue | 原始标题 | 解决 UTC | 类型 | 状态 / resolution | 目标版本 | 关联 PR（复核时） |
|---|---|---|---|---|---|---|
| [KAFKA-21110](https://issues.apache.org/jira/browse/KAFKA-21110) | Document that min.insync.replicas is bounded by the replica count | 2026-10-11 08:45 | Improvement | Resolved / Fixed | 4.5.0（未发行） | [#23529](https://github.com/apache/kafka/pull/23529) 已合并 |
| [KAFKA-21143](https://issues.apache.org/jira/browse/KAFKA-21143) | Server-only OAUTHBEARER listener with private JWKS CA triggers token login and fails broker startup | 2026-10-11 09:14 | Bug | Resolved / Fixed | 4.5.0（未发行） | [#23557](https://github.com/apache/kafka/pull/23557) 已合并 |
| [KAFKA-14333](https://issues.apache.org/jira/browse/KAFKA-14333) | Kafka Admin delete records java doc is missing information about supported cleanup.policy | 2026-10-11 13:12 | Bug | Resolved / Fixed | 4.5.0（未发行） | [#23716](https://github.com/apache/kafka/pull/23716) 已合并 |
| [KAFKA-21222](https://issues.apache.org/jira/browse/KAFKA-21222) | Add broker-level configs | 2026-10-12 03:22 | Sub-task | Resolved / Resolved | 4.5.0（未发行） | [#23729](https://github.com/apache/kafka/pull/23729) 已合并<br>[#23797](https://github.com/apache/kafka/pull/23797) 已合并 |
| [KAFKA-20278](https://issues.apache.org/jira/browse/KAFKA-20278) | Refactor and clean the code in HeadersStoreUpgradeIntegrationTest | 2026-10-12 10:41 | Sub-task | Resolved / Fixed | 未填写 | [#21754](https://github.com/apache/kafka/pull/21754) 已合并<br>[#22901](https://github.com/apache/kafka/pull/22901) 已合并<br>[#23738](https://github.com/apache/kafka/pull/23738) 已合并 |
| [KAFKA-21235](https://issues.apache.org/jira/browse/KAFKA-21235) | The docs of sleepSecsOpt should state it is in seconds | 2026-10-12 20:05 | Improvement | Resolved / Fixed | 4.5.0（未发行） | [#23787](https://github.com/apache/kafka/pull/23787) 已合并 |
| [KAFKA-21019](https://issues.apache.org/jira/browse/KAFKA-21019) | Cover consumer and share group protocols in docker sanity tests | 2026-10-12 22:04 | Sub-task | Resolved / Fixed | 4.5.0（未发行） | [#23427](https://github.com/apache/kafka/pull/23427) 已合并 |
| [KAFKA-21264](https://issues.apache.org/jira/browse/KAFKA-21264) | Javadoc output language depends on the build machine's system locale | 2026-10-13 01:19 | Improvement | Resolved / Fixed | 未填写 | [#23789](https://github.com/apache/kafka/pull/23789) 已合并 |
| [KAFKA-19804](https://issues.apache.org/jira/browse/KAFKA-19804) | Improve heartbeat request manager initial HB interval | 2026-10-13 15:50 | Task | Resolved / Fixed | 4.5.0（未发行） | [#23687](https://github.com/apache/kafka/pull/23687) 已合并 |
| [KAFKA-19979](https://issues.apache.org/jira/browse/KAFKA-19979) | Improve Kafka Streams config files | 2026-10-13 17:18 | Improvement | Resolved / Fixed | 4.5.0（未发行） | [#21308](https://github.com/apache/kafka/pull/21308) 未合并<br>[#22831](https://github.com/apache/kafka/pull/22831) 已合并 |
| [KAFKA-21151](https://issues.apache.org/jira/browse/KAFKA-21151) | Extract streams group topology description orchestration into a shared runtime abstraction | 2026-10-13 20:33 | Improvement | Resolved / Fixed | 未填写 | [#23566](https://github.com/apache/kafka/pull/23566) 已合并 |
| [KAFKA-21274](https://issues.apache.org/jira/browse/KAFKA-21274) | Remove unused javax jaxb-api and activation dependencies | 2026-10-14 09:19 | Task | Resolved / Fixed | 未填写 | [#23808](https://github.com/apache/kafka/pull/23808) 已合并 |
| [KAFKA-21265](https://issues.apache.org/jira/browse/KAFKA-21265) | DescribeConfigs request fails with UNKNOWN_SERVER_ERROR on internal list config | 2026-10-14 09:21 | Bug | Resolved / Fixed | 4.5.0（未发行） | [#23785](https://github.com/apache/kafka/pull/23785) 已合并 |
| [KAFKA-21080](https://issues.apache.org/jira/browse/KAFKA-21080) | KafkaStreams pendingTasksToInit Task Handle Leak on Unclean Shutdown | 2026-10-14 09:48 | Bug | Resolved / Duplicate | 未填写 | 未核实关联 PR |
| [KAFKA-20924](https://issues.apache.org/jira/browse/KAFKA-20924) | Introduce request header version 3 in GetTelemetrySubscriptions and PushTelemetry RPCs | 2026-10-14 09:52 | Sub-task | Resolved / Fixed | 4.5.0（未发行） | [#23544](https://github.com/apache/kafka/pull/23544) 已合并<br>[#23651](https://github.com/apache/kafka/pull/23651) 已合并 |
| [KAFKA-21223](https://issues.apache.org/jira/browse/KAFKA-21223) | Add topic-level configs | 2026-10-15 01:23 | Sub-task | Resolved / Done | 4.5.0（未发行） | [#23782](https://github.com/apache/kafka/pull/23782) 已合并 |
| [KAFKA-21153](https://issues.apache.org/jira/browse/KAFKA-21153) | ClusterInstance#waitTopicDeletion should not wait the file cleanup | 2026-10-15 07:58 | Improvement | Resolved / Fixed | 4.5.0（未发行） | [#23800](https://github.com/apache/kafka/pull/23800) 已合并<br>[#23827](https://github.com/apache/kafka/pull/23827) 已合并 |
| [KAFKA-21253](https://issues.apache.org/jira/browse/KAFKA-21253) | Failed transaction abort in RecordCollectorImpl.closeDirty() skips clearing changelog offsets, so a revived task can checkpoint a stale offset | 2026-10-15 20:38 | Bug | Resolved / Fixed | 4.5.0（未发行）、4.4.1（未发行）、4.3.3（未发行） | [#23791](https://github.com/apache/kafka/pull/23791) 已合并 |
| [KAFKA-14302](https://issues.apache.org/jira/browse/KAFKA-14302) | Infinite probing rebalance if a changelog topic got emptied | 2026-10-15 21:49 | Bug | Resolved / Fixed | 4.5.0（未发行）、4.4.1（未发行） | [#23298](https://github.com/apache/kafka/pull/23298) 已合并 |
| [KAFKA-21079](https://issues.apache.org/jira/browse/KAFKA-21079) | KafkaStreams StateUpdater Thread Death Causes StreamThread Permanent Deadlock,as a result, KafkaStreams is always in the PENDING_SHUTDOWN state. | 2026-10-15 22:50 | Bug | Resolved / Duplicate | 未填写 | 未核实关联 PR |
| [KAFKA-21268](https://issues.apache.org/jira/browse/KAFKA-21268) | Server, Shell, Storage module: replace temp file handler with JUnit 5 Temporary Directory Support | 2026-10-16 12:41 | Sub-task | Resolved / Fixed | 4.5.0（未发行） | [#23810](https://github.com/apache/kafka/pull/23810) 已合并 |
| [KAFKA-14218](https://issues.apache.org/jira/browse/KAFKA-14218) | replace temp file handler with JUnit 5 Temporary Directory Support | 2026-10-16 12:41 | Improvement | Resolved / Fixed | 4.5.0（未发行） | [#13836](https://github.com/apache/kafka/pull/13836) 关闭未合并<br>[#23280](https://github.com/apache/kafka/pull/23280) 已合并<br>[#23381](https://github.com/apache/kafka/pull/23381) 已合并<br>[#23388](https://github.com/apache/kafka/pull/23388) 已合并 |
| [KAFKA-21289](https://issues.apache.org/jira/browse/KAFKA-21289) | release.py stage-docs writes documentation to the pre-Hugo flat layout instead of the KIP-1133 Hugo layout | 2026-10-16 17:15 | Bug | Resolved / Fixed | 4.5.0（未发行） | [#23833](https://github.com/apache/kafka/pull/23833) 已合并 |
| [KAFKA-21142](https://issues.apache.org/jira/browse/KAFKA-21142) | KRaftMigrationZkWriter may fail to create TopicPartitionStateZnode during a crash fault | 2026-10-16 19:39 | Bug | Resolved / Fixed | 3.9.3（未发行） | [#23610](https://github.com/apache/kafka/pull/23610) 已合并 |

## 3. 生命周期与代码链的关键区别

- KAFKA-21253：trunk [dfd3dcab](https://github.com/apache/kafka/commit/dfd3dcab0756a8574105db4c159ed19d500bcef7)；4.4 回移 [614efd6e](https://github.com/apache/kafka/commit/614efd6e0f14f59076468a13d5dbab09038ca2ad)，4.3 回移 [05f0edf4](https://github.com/apache/kafka/commit/05f0edf48ead2bf05141d100af2ae914ef9bb91a)。目标 4.5.0/4.4.1/4.3.3 尚未发行。
- KAFKA-14302：trunk [b2f85364](https://github.com/apache/kafka/commit/b2f85364e44abfea2bb1937d894b36edae80b968)；4.4 回移 [904491ff](https://github.com/apache/kafka/commit/904491fffb9bb3f7e17fff5863442db926191b24)。还需连同后续 [#23841](https://github.com/apache/kafka/pull/23841) 的非阻塞 position() 修复看待，不能把后续 PR 另计为新增 issue。
- KAFKA-21142：[daebfbd9](https://github.com/apache/kafka/commit/daebfbd9b37c913937d5adfc2e493fe825e3da3a) 直接合入 3.9；不是先合 trunk 再回移。3.9.3 未发行。
- KAFKA-21222 / 21223 的 resolution 分别为 Resolved / Done，是 KIP-1279 的配置子任务。配置暂为 internal，不代表 Cluster Mirroring 全功能上线。
- KAFKA-21079 是 KAFKA-20721 的 Duplicate；21080 的评论明确指向 KAFKA-19960，属于归并，不能重复计算独立修复。
- KAFKA-19979 虽 Fixed，但旧 PR #21308 仍 open；已合并实现是 #22831。KAFKA-14218 的旧 #13836 关闭未合并，不能用 closed 推导 merged。
- KAFKA-21279 的维护者建议沿旧问题 19023 推进，但它仍 Open，尚不能写成正式 Duplicate。

## 4. 截点后变化与未知

本轮发现 JIRA updated 晚于截止的条目：KAFKA-21293、KAFKA-21299。

以下关联 PR 的 updated_at 晚于 12:00 截止；表格只展示复核时状态，不将其后续活动归入本周统计：

- [#23840](https://github.com/apache/kafka/pull/23840)：2026-10-17T14:36:42Z；当前 未合并。
- [#23770](https://github.com/apache/kafka/pull/23770)：2026-10-17T13:17:48Z；当前 未合并。

未填写的影响/修复版本保留未知。测试结果和复现来自上游报告，本次没有重新运行 Kafka 测试。查询与页数详见随附《来源索引》。

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
