---
type: survey
title: 第 5 期：失败分类、文件回收与升级边界
sources:
- https://github.com/apache/kafka/pull/24072
- https://github.com/apache/fluss/pull/5064
- https://github.com/AutoMQ/automq/pull/3717
tags:
- 流存储
- 社区观察
- Kafka
- Fluss
- AutoMQ
created: '2026-11-09'
updated: '2026-11-09'
status: draft
publication_status: github_archive
source_checked: '2026-11-06'
source_check_scope: 本期所列官方 PR、关键讨论、提案和发行记录；范围与限制见正文。
related:
- '[[知识库/sources/web/stream-storage-observer-20261106/README]]'
publication_scope: 仅 GitHub 正文归档；GitHub Pages、知识卡及双库同步暂缓。
report_date: '2026-11-06'
---

# 流存储技术观察 · 2026-11-06

## 第 5 期：失败分类、文件回收与升级边界

> 归档范围：本页保存 2026 年 11 月 6 日报告正文及公开引用，供 GitHub 阅读。GitHub Pages 页面、知识卡更新与双库同步暂缓。目录沿用报告的既定路径，不代表已完成博客同步。技术状态按原观察窗口保留，不代表归档日的最新进展。

[公开来源索引](../../知识库/sources/web/stream-storage-observer-20261106/README.md)

观察区间：2026 年 10 月 30 日 12:00 至 11 月 6 日 12:00 UTC，即北京时间 10 月 30 日 20:00 至 11 月 6 日 20:00。下文日期均按 UTC；仅以窗口内发生的事件计入本周进展，检索时看到的窗口后活动不向前归入。

本周最需要分清的是失败后的下一步。Kafka 的日志压缩必须正确界定 aborted transaction 的扫描区间，否则已提交的删除也会失效；Fluss 的湖层不能因为没收到提交结果就删除新文件；AutoMQ 则把某些状态冲突交回上层重新获取上下文，同时继续争论WAL 失败点之后的数据应如何处理。它们都涉及正确性，但失败模型和保证并不相同。

另一个共同变化是，兼容性与发布状态成为方案的一部分。Fluss 的压缩批使用新 magic 让旧 reader 明确拒绝，Kafka mirroring 将源集群边界收敛到 3.0 及以上，AutoMQ 的读取重试修复则明确没有进入 1.7 回移。判断能否采用，不能只看 PR 已合并。

| 项目 | 本周重点 | 截止时的交付边界 |
|---|---|---|
| Kafka | 压缩日志墓碑与时间戳查询修复；3.9.3 发布筹备；mirroring 基础设施继续落地 | 修复进入 trunk 不等于已发版；3.9.3 尚未发布；KRaft 升级保护仍待审 |
| Fluss | Iceberg 提交未知结果保护、COMPACTED 压缩、客户端韧性；全局二级索引实测继续 | 本周未核实到新正式发行；GSI、Bulk Load 与 remote tiering 提交保护仍有开放项 |
| AutoMQ | 1.7.5-rc3 候选发布；WAL 重试分类、snapshot Fetch 与恢复修复合并 | rc3 不是 GA；11 月 3 日后的修复不自动属于 11 月 2 日 rc3；保留坏点后 WAL 的提案未合并 |

本期沿着失败路径说明机制、证据和取舍。正文引用的性能及故障数字均来自上游贡献者的公开测试，未独立复现。上期已经合并的补丁，只有在本周出现新的发行、回移、评审或反转时才作为增量讨论。

## Kafka：正确性修复与升级支持边界

本节观察窗口为 **2026 年 10 月 30 日 12:00 至 11 月 6 日 12:00 UTC**。本周最重要的变化不是又一个大版本发布，而是事务压缩和时间戳查找的正确性修复、3.9.3 发布筹备，以及 Cluster Mirroring 实现与兼容性边界的同步调整。下文明确区分已合并到 trunk、待审补丁、讨论中的 KIP 和发布计划；合并到 trunk 不代表已有可下载的正式修复版本。

### 1. 两项存储正确性修复落地：已删除键复活，以及时间戳查询漏掉有效数据

**事务 tombstone 被错误忽略的问题已合并。** KAFKA-21410 / PR #24072 于 11 月 2 日提出，11 月 5 日 00:19 UTC 合并到 trunk。触发场景涉及事务生产者写入的 compacted topic：一轮清理填满 offset map 后，下一轮从 segment 中部继续；此前 aborted-transaction 查询的下界却仍取 log-start offset，错误带入本轮起点之前已经结束的 aborted transaction。下一轮可能不会再遇到其 ABORT marker，因而把同一 producer 后续已经提交的事务批次也视为 aborted。若被忽略的是已提交 tombstone，旧值会保留；待 tombstone 的删除期限过去，已经删除的键就会重新出现。[PR #24072](https://github.com/apache/kafka/pull/24072)

评审推动的改变不是仅在上层打补丁。Jun Rao 于 11 月 2 日建议直接纠正 `LocalLog.collectAbortedTransactions`：用本次查询的 start offset 定位起始 segment，并作为事务范围的下界。作者于 11 月 4 日采纳，同时保留 `cleanSegments` 重建 transaction index 所需的完整 segment 范围。作者报告在 macOS、Linux 和 OpenBSD 上完成复现与修复验证；完整 storage 测试第二次运行 1358 项通过，但首轮存在超时和测试 JVM 退出，不能表述为所有测试运行始终全绿。对使用事务生产者和日志压缩的团队，这是本周最值得追踪进入补丁版本的修复之一。[关键审查](https://github.com/apache/kafka/pull/24072#discussion_r4449102094) · [修改及验证记录](https://github.com/apache/kafka/pull/24072#issuecomment-6619925284)

**按时间戳查 offset 的本地和远端路径也完成修复。** KAFKA-21317 / PR #24028 于 11 月 4 日 05:12 UTC 合并到 trunk。`DeleteRecords` 可以把 log-start offset 推到某个 segment 中间，而该 segment 缓存的最大时间戳仍可能属于已逻辑删除的记录。原先的查找遇到该 segment 返回空结果便提前结束，即使后续本地或远端 segment 仍有有效匹配。修复让查询继续跨 segment 搜索。[PR #24028](https://github.com/apache/kafka/pull/24028)

关键回复还发现并解决了三个容易被标题掩盖的问题：横跨多个 leader epoch 的同一远端 segment 不应反复下载；进入本地日志后，应只扫描一次并以该结果结束；判断远端范围是否已被本地覆盖和执行本地查找时必须使用同一个 segment snapshot，否则并发 retention 删段可能让某些数据只剩远端，但查询却返回更晚的 offset 或空结果。作者报告 312 项相关测试通过。[snapshot 竞态审查](https://github.com/apache/kafka/pull/24028#discussion_r4445644055)

相关但独立的 KAFKA-21425 / PR #24027 修复 `MAX_TIMESTAMP` 仍返回 log-start offset 以下记录的问题，截止观察点仍为 open，不能与上述已合并修复合并描述为全部解决。[待审 PR #24027](https://github.com/apache/kafka/pull/24027)

### 2. 3.9.3 进入发布筹备，后续维护重点收敛到迁移可用性

11 月 6 日 **07:41 UTC**，PoAn Yang 宣布担任 Kafka 3.9.3 发布经理，计划于 **11 月 20 日 code freeze**，首个 release candidate 随后。官方计划明确日期可能调整，因此当前状态是发布筹备，不是已发布或 RC 投票完成。[发布经理邮件](https://www.mail-archive.com/dev@kafka.apache.org/msg159479.html) · [官方发布计划](https://cwiki.apache.org/confluence/spaces/KAFKA/pages/462816204/Release+Plan+3.9.3)

本周讨论同时澄清了旧分支支持的边界。11 月 2 日 Chia-Ping 表示将回补 CVE 修复并启动计划；Mickael 提醒 3.9 已不再标为受支持分支，持续维护额外版本有成本。11 月 4 日 Luke 和 Chia-Ping 形成的讨论共识是：**无 workaround、且会阻断 ZK→KRaft 迁移或造成迁移后元数据不一致的严重迁移问题，可以成为再做 3.9.4 的理由；CVE 可以随这样的版本带入，但不应单独触发新 3.9 版本。** 如果尚未找到 workaround，应先按严重问题对待。这是讨论中形成的维护原则，不宜升级表述为正式长期支持承诺。[关键往返](https://www.mail-archive.com/dev@kafka.apache.org/msg159458.html)

与之直接相关的 KAFKA-21062 / PR #23639，目标分支为 3.9，截止仍未合并。补丁处理 `/migration` 写入遇到 BADVERSION 后的恢复：对单次迁移状态更新，读回可确认先前写入是否已经成功；snapshot/delta 批量写不能靠末尾 `/migration` 状态证明整批成功，其 BADVERSION 则走冲突退位处理，使迁移 driver 进入 INACTIVE 并使 controller 退位，避免永久卡住。11 月 3 日 Omnia 的审查指出，过宽的异常捕获会把鉴权失败、会话问题、NONODE 等误判为并发写冲突，还提出旧任期事件影响新任期和退位超时导致进程退出的问题。11 月 6 日 11:02 和 11:44，作者同意保留原有异常分类，并只在 BADVERSION 的特定路径检查冲突。可见修复正在被实质审查，但尚不能写作已经解决。[PR #23639](https://github.com/apache/kafka/pull/23639) · [异常分类质疑](https://github.com/apache/kafka/pull/23639#discussion_r4455389813) · [作者对 NONODE 的回应](https://github.com/apache/kafka/pull/23639#discussion_r4492048779)

### 3. Cluster Mirroring：内部状态与排障工具落地，源集群最低版本转向 3.0+

KIP-1279 的兼容性讨论在 11 月 2–3 日发生实质收敛。原方案允许源集群版本低至 2.1，但 Kafka 已删除 `AbstractFetcherThread` 中显式调用 `OffsetForLeaderEpoch` 的截断阶段，复制路径依赖 truncation-on-fetch。Rajini 与 Mickael 不希望只为旧版 mirroring 再引入这套复杂逻辑。Federico 接受维护成本的考虑，又追问为什么不以最早引入该机制的 2.7 为界；Rajini 指出部分重要边界修复未进入 2.7，3.0.x 是更稳妥的兼容基线，随后 Federico 确认更新 KIP。[兼容性完整往返](https://www.mail-archive.com/dev@kafka.apache.org/msg159451.html)

实现方面，本周可确认合并到 trunk 的是几块基础设施：

- **10 月 30 日 15:10 UTC，#23979：** 为 `__mirror_state` 增加 `MirrorPartitionState` 与 `LastMirrorEpochs` 记录 schema、serde 和 JSON 转换；验证记录及 tombstone 经真实 broker 重启后仍能读取。[PR](https://github.com/apache/kafka/pull/23979)
- **11 月 4 日 11:10 UTC，#23843：** 增加 mirror-level configs，补全 `ClusterMirrorConfig`。[PR](https://github.com/apache/kafka/pull/23843)
- **11 月 4 日 15:30 UTC，#24078：** 为 `kafka-dump-log.sh` 增加 `--mirror-state-decoder`，便于直接检查镜像内部状态日志。[PR](https://github.com/apache/kafka/pull/24078)
- **11 月 5 日 11:46 UTC，#24077：** 增加 `MirrorStateMessageFormatter`，通过 console consumer 读取镜像内部状态。[PR](https://github.com/apache/kafka/pull/24077)

这些进展意味着内部数据格式、配置和排障能力在落地，**不意味着完整的跨集群镜像功能已经完成或可用于生产**。关键依赖仍在审查：#24034 为 `PartitionChangeRecord` 加入显式 LeaderEpoch，并引入所需的 4.5-IV1 metadata version。11 月 5 日 reviewer 警告直接相信记录中的较小 epoch 会造成倒退，破坏 fencing；11 月 6 日 11:41 作者建议在 controller 提交记录前校验，而不是回放时拒绝已经提交的记录。11 月 5 日提出的 draft #24112 则为 `mirror.version` 建立 0=禁用、1=early access 的开关，production 默认仍为 0，并依赖 #24034。两者在截止点均未合并。[epoch 关键回复](https://github.com/apache/kafka/pull/24034#discussion_r4492023392) · [feature flag 提案](https://github.com/apache/kafka/pull/24112)

### 4. KRaft 升级安全：普通 release-version 升级不应隐式改变 quorum 类型

KAFKA-21426 于 11 月 4 日报告，11 月 5 日出现 #24109 和 #24111 两个修复候选，截止均为 open。问题在于 `kafka-features.sh upgrade --release-version` 会将 `kraft.version` 与其他 feature 一起提升；当当前值为 0 时，这会把静态 controller quorum 转成动态 quorum。转换不能撤销，而节点配置可能仍使用 `controller.quorum.voters`。[PR #24109](https://github.com/apache/kafka/pull/24109) · [PR #24111](https://github.com/apache/kafka/pull/24111)

两个候选修复都试图将“升级 Kafka 功能版本”和“转换 quorum 类型”分离：当前还是静态 quorum 时保留 `kraft.version=0`，要求用户显式指定 `--feature kraft.version=1` 才转换；已经是动态 quorum 的集群仍按原方式升级。#24111 还包含帮助文本、操作文档和测试调整。当前只能记为新问题与待审防护，不能宣称正式版本已经改变升级行为。

### 5. 保留期与管理查询：KIP 正在解决操作语义，而不只是增加开关

**KIP-1385 的本周增量，是回填兼容性和启动恢复行为的讨论。** 方案把 tiered topic 的 `local.retention.ms` 从记录时间戳改为远端上传完成时间。这样可避免旧时间戳的回填数据刚上传就离开本地，也避免未来时间戳长时间阻止本地清理；已有文件 lastModified 的 fallback 又会在迁盘后重置计时。KIP 仍为 Under Discussion。[KIP 文档](https://cwiki.apache.org/confluence/spaces/KAFKA/pages/451979130/KIP-1385+Measure+local.retention.ms+from+remote+upload+time+instead+of+record+timestamps)

11 月 5 日 Chia-Ping 追问，这是否会打破运维者对回填数据上传后尽快清走的预期。作者提出两个尚待选择的方向：保持 upload-time 语义并在升级说明披露，以 `local.retention.bytes` 限制磁盘；或使用 `min(record timestamp, upload time)` 保留旧回填行为，但代价是不同数据不再具有统一的本地保留期含义。作者也澄清，metadata cache 还在初始化时，远端管理任务不会执行，上传前禁止删除的保护会阻止本地按时间删除，因此是暂停删除，而不是总会触发 fallback。[review](https://www.mail-archive.com/dev@kafka.apache.org/msg159473.html) · [作者回应](https://www.mail-archive.com/dev@kafka.apache.org/msg159471.html)

**KIP-1388 的本周增量，是 committed-offset filter 的兼容性与边界语义。** 方案在 ListGroups v6 加入 `requireCommittedOffsets`，只返回至少具有一个已提交 offset 的 group，以减少 MirrorMaker 2 和跨集群 offset 同步中无效的 OffsetFetch。11 月 2 日作者明确：旧 broker 返回 UnsupportedVersionException 时，采用该选项的 MM2 可保留其他过滤条件，只关闭新选项重试一次；修改 MM2 本身不在此 KIP 的范围内。实现只需在 committed-offset map 中判断 group 是否存在，不需要逐分区扫描。[作者答复](https://www.mail-archive.com/dev@kafka.apache.org/msg159437.html)

pending-only 的事务 offset 不计入，之后 commit 的 group 要等下一次列表查询才能发现。11 月 3 日 Rajini 表示 LGTM；11 月 5 日 Sean 又提醒，对 share groups 使用该选项会返回空，而 mixed-type 查询又不适合整体报 unsupported，建议在 rejected alternatives 解释这一取舍。截止仍为讨论，不是已实现 API。[关键回复](https://www.mail-archive.com/dev@kafka.apache.org/msg159468.html)

### 6. 安全配置提案：TLS named groups 进入投票，tokenless login 明确生产使用边界

**KIP-1376 于 11 月 2 日启动投票。** 拟新增 `ssl.named.groups`，覆盖客户端、broker/controller、Connect REST，以及 OAuth token/JWKS 的 HTTPS 连接；支持 listener 级覆盖，默认不改变现有行为，调整配置需要重启。重要限制是：named-groups API 从 Java 20 才可用，在缺少 API 的 JVM 上显式配置会启动失败；PQC named groups 本身还依赖 Java 27 或包含相应能力的厂商回补，不能把这项提案描述为所有现有 Kafka JVM 都立即获得后量子 TLS。[投票邮件](https://www.mail-archive.com/dev@kafka.apache.org/msg159431.html) · [KIP](https://cwiki.apache.org/confluence/spaces/KAFKA/pages/451974516/KIP-1376+Support+setting+TLS+named+groups)

已读取的投票线程仅见一条 non-binding +1，未见 RESULT；wiki 仍显示 In Discussion，因此准确状态是“已经发起投票，未确认通过”，不是已接受或发布。[投票回复](https://www.mail-archive.com/dev@kafka.apache.org/msg159434.html)

**KIP-1390 于 11 月 2 日启动讨论。** 它为只验证客户端 OAuth token、无需获取自身 token 的 broker 提供正式的 `OAuthBearerTokenlessLoginCallbackHandler`，避免依赖内部测试用途的 unsecured handler。它不是关闭 token 验证，也不适用于需要 token 的客户端或跨 broker/controller OAuth 连接。无新增配置项，使用现有 callback-handler 配置选择新类。[KIP](https://cwiki.apache.org/confluence/spaces/KAFKA/pages/462815912/KIP-1390+Add+a+tokenless+login+callback+handler+for+SASL+OAUTHBEARER)

评审后，作者去掉了对 `unsecuredLogin*` 的额外拒绝逻辑，改为忽略 JAAS options，并计划让旧 handler 在相关无 token 使用场景输出 WARN、提示迁移。11 月 5 日 Chia-Ping 要求在动机中明确 unsecured 类不适合生产，并考虑为新 handler 的无 token 登录增加明确日志来防止误用。截止仍为 Under Discussion。[关键评审与答复](https://www.mail-archive.com/dev@kafka.apache.org/msg159465.html)

## Fluss：湖层安全、格式兼容与客户端韧性

**观察窗口：2026-10-30 12:00 至 2026-11-06 12:00 UTC。** 本周的主线是 1.1 开发中的正确性、性能与运维完善。官方仓库按日期检索到 54 个合并 PR，扣除 10 月 30 日中午前的 6 个，窗口内为 48 个；这个数字包含修复、测试、文档等，不代表 48 项新功能。官方最新正式版本仍是 1.0.0，本周未发现新正式 release。下文的“已合并”表示开发分支代码进展，不意味着已发布或已回移到 1.0。[官方 releases](https://github.com/apache/fluss/releases) · [合并记录查询](https://api.github.com/search/issues?q=repo%3Aapache%2Ffluss+is%3Apr+merged%3A2026-10-30..2026-11-06&per_page=100)

### 1. 湖层正确性：未知提交结果不能当作失败清理，Union Read 顺序也有新风险

**Iceberg rewrite 文件误删已修复。** 11 月 5 日创建的问题 #5054 描述了 1.0.0 和 main 上的风险：lake compaction 向 Iceberg 提交后，REST catalog 超时或返回 5xx，实际提交可能已经成功，但 Fluss 会对所有异常执行新文件删除，导致表引用不存在的数据文件。报告者在 Lakekeeper 数据库死锁引发的 503 中遇到了这一情况。修复 #5064 当日 21:48 UTC 合并，遵循“明确失败才清理，结果未知则保留文件并警告”的原则，接受可能出现 orphan 文件，避免破坏已提交数据。[问题与故障场景](https://github.com/apache/fluss/issues/5054) · [合并修复](https://github.com/apache/fluss/pull/5064)

**普通 remote log tiering 还有同类问题，尚未合并修复。** Bulk Load 评审中发现，Coordinator 已持久化 manifest、但成功响应丢失时，TabletServer 上 LogTieringTask 的后续失败处理可能删除该 manifest 引用的 segment。影响范围是 Log 表及 KV 表的 WAL，不能与 KV snapshot SST 的提交和回收混为一谈。11 月 6 日 06:49 创建的 #5076 仍开放：方案为每个 bucket 保留一个未决上传，重试复用同一组不可变文件路径，以 ZooKeeper version CAS 做前驱条件发布，并根据权威后继 manifest 判断哪些文件确实可清理。它是 #4771 的独立前置修复，不承诺进程丢失等异常条件下零 orphan。[问题 #5074](https://github.com/apache/fluss/issues/5074) · [待评审修复 #5076](https://github.com/apache/fluss/pull/5076)

**Iceberg full Union Read 的桶内顺序问题刚被确认。** #5077 于 11 月 6 日 07:42 创建，报告 Fluss 1.0.0（0.9.0 也观察到）在读取同一 bucket 的湖文件时，先读新文件、再读旧文件，随后无缝切到 Fluss log。原始读取没有丢失或重复，但 event-time watermark 提前推进，会使后来的旧记录被下游当作 late data 丢弃。08:48 的维护者回复确认需要给 planner 的 lake splits 排序，并在 checkpoint restore 后保持顺序。[问题与复现](https://github.com/apache/fluss/issues/5077)

这段讨论的限制比标题更重要：外部 Iceberg compaction 可以打乱文件内部行序，split 排序无法恢复完整写入顺序；Flink restore 的 split 无序也会影响同一 bucket 分成多个 split 的 Paimon；多 bucket/partition 的读取顺序、idle timeout 和 lake 阶段 rescale 还会带来更广的 event-time 风险。因此不能写成“Paimon 完全不受影响”，也不能把一个排序修复视为完整 event-time 保证。截至观察点问题仍开放，尚无已合并修复。[维护者确认及边界](https://github.com/apache/fluss/issues/5077#issuecomment-6680962361)

另一个版本范围清晰的修复是 #5063，11 月 5 日 21:42 合并：Iceberg 1.12 插件补入 commons-io，解决 REST catalog 返回 zstd 响应时的 `NoClassDefFoundError` 和 Coordinator crash-loop。它仅影响 main/1.1-SNAPSHOT 的 1.12 插件，1.0 并无此插件，1.10 插件也不走相同压缩响应路径。[问题 #5053](https://github.com/apache/fluss/issues/5053) · [修复 #5063](https://github.com/apache/fluss/pull/5063)

### 2. 全局二级索引：大规模实测验证正确性，故障隔离和使用边界仍在打磨

FIP-38 的实现 #4820 支持单列/复合索引、独立 index bucket 数和 SYNC/ASYNC 可见性，供 Java API、Flink lookup join 使用。查询先从索引取得候选，再回主表查询并验证当前索引值。**截至 11 月 6 日仍未合并。** 本周最值得跟踪的是实测反馈推动的修改，而非将功能描述当成已交付能力。[PR #4820](https://github.com/apache/fluss/pull/4820)

11 月 3 日，社区在 Flink 2.3、3 个 TabletServer、RF3 上测试六张百万级 PK 表、每表每秒千次更新及五级 delta join，报告 600 万次索引 lookup 没有错误，savepoint 恢复和 TS 故障后的宽表结果也正确。同时发现低选择性索引值命中百万行时客户端可占约 1GB 堆、两跳请求经历两次 batch timeout，以及不可用 index bucket 对 SYNC 表可见性的连锁影响。[第一轮实测](https://github.com/apache/fluss/pull/4820#issuecomment-6600447277)

随后作者加入默认 1024 的候选上限，超限在主表请求开始前失败且不返回部分结果；完善运行时错误日志、指数退避和恢复；让失败窗口释放共享 payload budget，使健康数据源能继续争取资源；建表时检查所有在线 TS 的 `PUT_INDEX` 能力。SYNC 的等待是有意的正确性取舍：未应用索引变更前不能确认成功；ASYNC 的主表确认不等待索引，但索引新鲜度仍可能受 bounded-window 模型拖累。[可用性取舍说明](https://github.com/apache/fluss/pull/4820#issuecomment-6604679123)

**11 月 6 日 10:01 的复测是截止点前最新证据。** 600 万次 lookup 在 kill、rolling restart 和 15 分钟 freeze 后仍无错误；候选超限可在 200ms 内失败且未见客户端堆增长。不过报告者仍列出：

- SYNC snapshot discovery 需要所有 leader 可达，相关选择逻辑也影响不需要它的 lake tiering 和 Spark。
- 升级 gate 只检查建表，未覆盖后来加入的旧 TS 和新分区。
- 已删分区候选可能仍计入上限；一个 hot value 可使同 bucket 同批 lookup 一起失败；Flink 超限后可能重复重启。
- 不可用 index bucket 对 SYNC 全表的影响需更明确，故障日志和无限重试期间的 WAL 保留还需加强，测试曾填满磁盘。

这支持“正确性实测取得进展，故障恢复、资源上限和可用性边界仍待完善”的判断，不能写成已生产就绪。[最新复测与未解事项](https://github.com/apache/fluss/pull/4820#issuecomment-6682237789)

### 3. COMPACTED 压缩已合并，最终兼容策略以评审回复为准

#4814 于 **11 月 5 日 15:40 UTC 合并**，为 COMPACTED log batches 增加 LZ4_FRAME 和 ZSTD，默认关闭，只能建表时选择。压缩后若没有变小则保持原样；Log 表由客户端压缩，PK changelog 在服务端生成时压缩。[PR #4814](https://github.com/apache/fluss/pull/4814)

PR 正文保留了旧方案的兼容说明，容易误导摘要。原实现重用既有 magic，旧 reader 甚至可能把 LZ4 数据静默读成 DELETE。**11 月 4 日回复确认最终改用 magic V3，仅真正压缩的批采用新 magic；旧客户端与 TS 会明确报 `Unsupported magic value`。** 未压缩的批继续兼容原读取路径，启用新压缩表前必须先升级服务端和消费者。[最终兼容性说明](https://github.com/apache/fluss/pull/4814#issuecomment-6628791275)

11 月 5 日 reviewer 在三节点 RF3、57 列、每变体 2000 万行的测试中，观察到 COMPACTED ZSTD 的三副本磁盘占用从 37.1GB 降至 11.3GB，约 3.3 倍压缩；回读 bit-identical，PK 压缩 changelog 的重启恢复也正确。测试机器受磁盘限制，读写表现不能直接推广为普遍吞吐收益；向量浮点数据也不能套用这一压缩率。[本周性能与恢复实测](https://github.com/apache/fluss/pull/4814#issuecomment-6660004305)

### 4. Paimon PK 元数据接入落地，存量数据初始化仍等 Bulk Load

#4956 于 **11 月 4 日 07:57 UTC 合并**，扩展 `Admin.createTableFromLake`，能从受支持 Paimon PK 表创建 Fluss 元数据，映射主键、分布、merge/delete、字段聚合、sequence 与 TTL。没有已有 snapshot 的表可以启用；**已有历史 snapshot 的表仍保持 lake-disabled，历史数据初始化必须等 Bulk Load。** 因而本周完成的是主键表元数据映射，不是完整的存量主键表无缝导入。[PR #4956](https://github.com/apache/fluss/pull/4956) · [Bulk Load guard 说明](https://github.com/apache/fluss/pull/4956#issuecomment-6596676080)

评审也暴露语义边界。11 月 3 日作者讨论保留 `TIMESTAMP` TTL，但明确它受 TS 系统时区影响，可能比 Paimon 更早到期，推荐 `TIMESTAMP_LTZ`；DECIMAL SUM overflow 可能在 Fluss 为 NULL、Paimon 为 0，直到后续非空更新才重新一致；ALTER 原生 merge 相关选项的全面重验证留给后续。这些限制意味着不宜概括成对全部 Paimon merge 配置的严格等价迁移。[TTL 讨论](https://github.com/apache/fluss/pull/4956#discussion_r4450466402) · [overflow 讨论](https://github.com/apache/fluss/pull/4956#discussion_r4452603866)

可恢复 Bulk Load 服务端事务 #4771 仍在评审，通过 Coordinator 持久化 Begin/GetInProgress/Commit/Abort、验证完整 bucket 覆盖并处理 failover/restart，在安装完成前封锁目标访问。公共 SDK、Flink 集成另做。11 月 6 日 reviewer 接受先 Abort 成功再 Drop 的范围；活动事务中直接 Drop 需要额外协调，留待后续。[PR #4771](https://github.com/apache/fluss/pull/4771) · [11 月 6 日工作流共识](https://github.com/apache/fluss/pull/4771#discussion_r4490311240)

### 5. 性能优化与客户端韧性形成一组可落地改进

性能侧的合并进展有明确边界：

- **11 月 2 日，#4768：** >=16 keys 的 MultiGet 使用 RocksDB snapshot/read lease，在 KV lock 外执行，减少大查询阻塞写入和 flush；小批保留原路径以免 snapshot 开销。局部 benchmark 的锁等待改善不等于端到端集群吞吐保证。[PR](https://github.com/apache/fluss/pull/4768)
- **11 月 5 日，#5031：** Flink tiering job 中不同表可并发 commit，`lake.tiering.commit-thread-num` 默认 2，避免慢表拖住全部表；不响应中断的存储调用仍可能拖延关闭。[PR](https://github.com/apache/fluss/pull/5031)
- **11 月 5 日，Java #4883 和 Rust #4922：** remote Arrow 只解压/解码投影列。Rust 明确不减少远端下载字节数，也没有 nested-leaf pruning。[Java PR](https://github.com/apache/fluss/pull/4883) · [Rust PR](https://github.com/apache/fluss/pull/4922)
- **11 月 3 日，#4981：** prefix lookup 允许 bucket key 加连续后续 PK 列，避免 Flink lookup/delta join 先取大量无关行再过滤；旧 KV v1/Paimon encoding 仍有 client 过滤 fallback。[PR](https://github.com/apache/fluss/pull/4981)
- **11 月 6 日，#4792：** Trino 等值 bucket pruning 使用 physical partition 的实际 bucket count 和统一 BucketCalculator；范围、多值 pruning 留后续，不支持的谓词/格式仍全扫。[PR](https://github.com/apache/fluss/pull/4792)

客户端侧，11 月 1 日创建的 #4980 来自 Java/Rust 对照审查，推动了重试、关闭和元数据边界的系统整理。Java 已合并 lookup 指数退避（#4970，11 月 2 日）、无 leader bucket 退避（#4991，11 月 3 日）、writer close 完成全部 pending/retry futures（#5009，11 月 3 日）、删除重建表的 metadata 修复（#4758，11 月 4 日），以及显式 `bucket_count` 防止 partial location cache 导致错误路由（#4984，11 月 5 日）。[#4980 总览](https://github.com/apache/fluss/issues/4980) · [writer close](https://github.com/apache/fluss/pull/5009) · [显式 bucket_count](https://github.com/apache/fluss/pull/4984)

#4991 的取舍需要保留：等待 leader 的 lookup 不受原 queue-size 限制，调用方仍应限制异步并发，不能因加入 backoff 就推断内存也已得到完整约束。[无 leader 退避及限制](https://github.com/apache/fluss/pull/4991)

Rust 已合并缺失分区自动创建且隔离单分区失败（#4941，11 月 2 日）、按 UID+endpoint 缓存 RPC 连接以适应 rolling upgrade/failover（#4986，11 月 3 日），以及 lookup 指数退避并暴露给 Python/C++/Elixir（#4994，11 月 3 日）。[分区写入](https://github.com/apache/fluss/pull/4941) · [连接缓存](https://github.com/apache/fluss/pull/4986) · [lookup 退避](https://github.com/apache/fluss/pull/4994)

还有一个值得避免的误报：#5060 声称 server response 漏 bucket 会使 lookup 永不完成，但维护者要求实际生产路径后，作者承认找不到此路径，于 11 月 6 日关闭 issue。它不是已确认 P0 缺陷，也不是修复合并。[撤回说明](https://github.com/apache/fluss/issues/5060#issuecomment-6678817991)

### 6. 部署与贡献体验完善，几个大路线仍在建设中

Helm #4115 于 **11 月 3 日合并**，Coordinator readiness 区分 leader 和有效 standby，而不只检查 TCP 端口；默认仍单副本，启用 SASL 时 chart 要求 readiness credential，升级需关注渲染校验变化。异常退出后的旧 ZooKeeper session 默认约 60 秒仍有观察窗口。#4108 于 **11 月 4 日合并**，补 advertised listeners 支持 K8s 外部客户端。[HA readiness](https://github.com/apache/fluss/pull/4115) · [外部客户端访问](https://github.com/apache/fluss/pull/4108)

#3865 于 **11 月 4 日合并**，只是 SASL mechanism 可扩展性的基础，没有交付 OAuth token、JWT/JWKS、group principals 或 ACL 新机制。#3851 于 **11 月 6 日 08:22 合并**，提供 Docker Compose+just DevKit，覆盖 Core/Gateway/Paimon/Iceberg/Lance、一或三个 TS 的拓扑，挂载本地构建产物，并带 Gateway/Paimon smoke 验证。[SASL 基础](https://github.com/apache/fluss/pull/3865) · [DevKit](https://github.com/apache/fluss/pull/3851)

聚合 merge engine 的补充也已落地：#2388 于 **11 月 2 日**增加 collect/merge_map，应注意集合持续增长与写放大；#4998 于 **11 月 3 日**增加 COUNT，计非 NULL 输入、仅 BIGINT，NULL 计零，不支持 retractions 或 COUNT DISTINCT。[集合聚合](https://github.com/apache/fluss/pull/2388) · [COUNT](https://github.com/apache/fluss/pull/4998)

仍在建设中的路线需要单列阶段：

- **Delta Lake #4944：** 本周继续更新，仍 open，仅 phase 1 log-table tiering，使用 Delta Kernel 4.4.1，data 与 Fluss offsets 同次提交；PK union read 需后续 FIP，Unity Catalog 也不在当前范围。[PR](https://github.com/apache/fluss/pull/4944)
- **FIP-53 consumer offsets：** system table、protocol 和 owner discovery 已完成；server commits #4850 仍 open，consumer-group ACL 正在补齐，client commit/fetch/auto-commit、scanner/Admin 和 E2E 仍列为未完成。[任务清单](https://github.com/apache/fluss/issues/4608#issuecomment-6142592747) · [commit 实现](https://github.com/apache/fluss/pull/4850)
- **Rust FIP-48 UnionRead：** 仍按层实现，#5000 是明确“不要合并”的 Draft；PK 没有 lake baseline 时，完整当前态重建需要后续 persisted KV snapshot fallback，不能假定 retained logs 足够。streaming、稳定跨语言 ABI、retention leases、PK spilling 不在此里程碑。[范围说明](https://github.com/apache/fluss/issues/4713) · [Draft API 合约](https://github.com/apache/fluss/pull/5000)

## AutoMQ：候选版本、恢复重试与数据保留取舍

本周（2026-10-30 12:00 至 2026-11-06 12:00 UTC）的主要变化，是 1.7.5-rc3 发布和多项可靠性修复回移。需要分清三个阶段：候选版本已发布、分支代码已合并、社区方案仍在讨论；“issue 已关闭”也不等于修复已合并。

### 1. 1.7.5-rc3 已发布，后续回移尚不能算进该版本

11 月 2 日 10:38 UTC 发布的 **1.7.5-rc3**，包含关机等待上界、Jackson 与 DirectIO 修复，以及 GCS multipart range copy 回退。关机修复给 S3MetricsExporter.flush 和 ClusterEventPublisher.close 设置 5 秒上界，处理对象存储不可用时退出过程卡住的问题。对应 #3715 在 10 月 30 日 04:53 已合并，早于本次精确时间窗，但本周进入候选版本，属于发布层面的进展。虽然 GitHub 的 prerelease 字段为 false，版本名及发布准备 PR 均明确为 rc，不能称为正式 GA。[发布说明](https://github.com/AutoMQ/automq/releases/tag/1.7.5-rc3)、[关机回移](https://github.com/AutoMQ/automq/pull/3715)

GCS 修复于 11 月 2 日分别进入 1.7、1.8 和 main：允许目标对象存储声明不支持服务端 multipart range copy，改走已有的 range-read 加 UploadPart 路径，避免 GCS XML API 不支持 source-range 请求时 compaction 持续重试。开源补丁提供的是能力声明和回退机制；#3728 另外说明 Enterprise 5.5 将负责 GCS 的 opt-out 和分片存储的能力透传，不宜概括为所有开源 GCS 部署已自动修好。[1.7 修复](https://github.com/AutoMQ/automq/pull/3728)、[1.8 回移](https://github.com/AutoMQ/automq/pull/3729)、[main 修复](https://github.com/AutoMQ/automq/pull/3730)

11 月 5 日合并的 #3741、#3742 则把下一批 Controller、snapshot、router、读取恢复修复带到 1.7/1.8。这些合并发生在 rc3 发布之后，不能直接列为 rc3 已包含的内容。两次回移的维护者评论报告构建、单元测试与 SpotBugs 通过，但分支验证通过不等于已有新的发布包。[1.7 回移](https://github.com/AutoMQ/automq/pull/3741)、[1.8 回移](https://github.com/AutoMQ/automq/pull/3742)

### 2. Snapshot 读恢复已落地，Produce 交接竞态继续分项验证

11 月 3 日，#3670 合并 main：snapshot replica 被移除或替换后，重新检查已排队的 delayed Fetch/Produce，避免旧 Fetch 一直等到长轮询超时。实现先发布新映射，再在 map compute 之外检查请求，降低引入锁顺序反转的风险；未改变的副本映射不额外唤醒。该修复于 11 月 5 日回移至 1.7/1.8。[修复 PR](https://github.com/AutoMQ/automq/pull/3670)

贡献者在 #3712 提供了独立对照：单机 Docker、三逻辑 rack、单分区合成负载下，snapshot 移除到错误响应的等待由约 4,747–4,854 毫秒降至 3–9 毫秒；三组读 p99 从 3.100–4.290 秒降至 0.732–0.934 秒。这证明的是特定 Fetch 超时路径的读恢复改善，实验没有模拟跨可用区网络，也未证明写延迟改善，不能转换为生产集群的通用性能承诺。[实验与限制](https://github.com/AutoMQ/automq/issues/3712)

维护者 11 月 3 日要求后续每项方案以已合并修复为基线，分别证明增量收益。11 月 4 日新增 #3740，更新 #3671 为独立的 accepted-Produce drain：append 已被接受，但 delayed Produce 尚未注册时遇到 partition shutdown，记录可能已存储，却返回 NOT_LEADER_OR_FOLLOWER。受控实验中，基线三次均返回错误，候选三次均成功；普通重启比较没有一致的延迟收益。**#3671 仍 open，尚未合并**，其价值目前是修复受控复现的确认语义竞态，而非已证明的总体提速。[维护者要求](https://github.com/AutoMQ/automq/issues/3669#issuecomment-6602341003)、[独立问题与验证](https://github.com/AutoMQ/automq/issues/3740)、[待审 PR](https://github.com/AutoMQ/automq/pull/3671)

同期已合并的恢复小修复还包括：#3723 在 Controller 过载恢复后重新调度 stale-broker fencing；#3735 将 router 定时器绑定具体 batch，并按实际请求数计批次大小；#3738 关闭失败 reader，异步等待 10 秒后用新 reader 重试一次，第二次失败则传播异常。这些均在 11 月 5 日回移至 1.7/1.8。另 #3734 只修复 1.7 FairLimiter 把毫秒当纳秒的错误，main/1.8 已改用 FetchLimiter，不需要同一补丁。[Controller](https://github.com/AutoMQ/automq/pull/3723)、[router](https://github.com/AutoMQ/automq/pull/3735)、[新 reader 重试](https://github.com/AutoMQ/automq/pull/3738)、[1.7 limiter 范围说明](https://github.com/AutoMQ/automq/pull/3734#issuecomment-6600873540)

### 3. WAL 重试边界收紧，失败点之后的数据保留方案未获接受

对象存储暂时不可用可能被误判为 WAL fencing。#3724 报告：rangeRead 的两分钟超时包装提前使读取失败，reservation.verify 将错误映射为 false，再被解释为另一节点抢占 WAL，最终触发 broker 退出。维护者确认后，#3731 于 11 月 3 日合并，移除该包装，让可重试错误遵循原有重试策略；非重试错误仍进入既有失败处理。[故障及维护者确认](https://github.com/AutoMQ/automq/issues/3724#issuecomment-6574029416)、[修复](https://github.com/AutoMQ/automq/pull/3731)

**这个修复只确认进入 main 和 1.8，不能写成 1.7 已修复。**维护者明确指出，1.8 默认 crt-http 已处理 AWS SDK Netty 在正常 TCP 关闭时 GetObject future 可能悬挂的问题，因此本次移除超时面向 main/1.8。11 月 5 日的 #3742 包含 #3731，1.7 的 #3741 不包含它。[1.8 回移清单](https://github.com/AutoMQ/automq/pull/3742)、[1.7 回移清单](https://github.com/AutoMQ/automq/pull/3741)

另一项已落地变化是 #3717：CommitStreamSetObject 返回 STREAM_NOT_OPENED、STREAM_FENCED、OFFSET_NOT_MATCHED、STREAM_INNER_ERROR 时，不再无限重复同一请求。Failover 当前尝试在 WAL reset 前失败，交给外层重试重新取得 opening streams；正常上传则进入原有 storage failure 路径并停止 broker。#3736/#3737 于 11 月 3 日回移至 1.7/1.8。[主修复](https://github.com/AutoMQ/automq/pull/3717)、[1.7 回移](https://github.com/AutoMQ/automq/pull/3736)、[1.8 回移](https://github.com/AutoMQ/automq/pull/3737)

与此不同，#3722 提议在 link decode 失败后终止恢复并保留 WAL，避免成功截断后丢弃后缀中可能已确认的记录。作者提供了跨三个 stream 的回归验证，但维护者 11 月 2 日表示暂不保留失败点之后的数据：上层依赖 WAL 写入按顺序成功，跨越失败点恢复可能造成 metastream 与 datastream 不一致。**该 PR 已关闭、未合并**；关联 #3721 虽于 11 月 4 日标记 closed/completed，仍不能当作补丁已落地。这是需要继续关注的数据恢复语义分歧。[提案及维护者回应](https://github.com/AutoMQ/automq/pull/3722#issuecomment-6573536882)、[原始问题](https://github.com/AutoMQ/automq/issues/3721)

### 4. Jackson、DirectIO 与 EMPTY 生命周期：修复进展与验证边界

#3720 于 10 月 31 日将常规 Jackson 升级至 2.21.8，annotations 保持 2.21。#3725 于 11 月 1 日修复 DirectIO 原生内存释放：posix_memalign 分配的内存包装成无 Cleaner 的 DirectByteBuffer 后，Netty freeDirectBuffer 不会释放实际分配，改用 DirectIOLib.free，并约定只释放原 buffer 一次。两项均回移至 1.7/1.8，其中 1.7 已进入 rc3。[Jackson 修复](https://github.com/AutoMQ/automq/pull/3720)、[DirectIO 修复](https://github.com/AutoMQ/automq/pull/3725)、[1.7 回移](https://github.com/AutoMQ/automq/pull/3726)、[1.8 回移](https://github.com/AutoMQ/automq/pull/3727)

**不能据此宣布 Jackson 漏洞已全面修复。**11 月 3 日 #3733 的作者检查生成发布包的 428 个 JAR，确认 parquet-jackson:1.18.0 仍嵌入 databind 2.22.1，常规副本则为 2.21.8。FasterXML 官方 GHSA-m8xf-2cr7-77ph 明确将 2.22.0–2.22.3 列为受影响版本，2.22.4 为修复版本。因此，Parquet/Iceberg roundtrip 兼容性测试通过，不等于 shaded 副本漏洞已修复。这里能够确认的是组件版本层面的风险；实际可利用性仍取决于多态反序列化配置、可达输入路径及 classpath，不能直接断言 AutoMQ 存在已验证的可远程利用漏洞。[产物检查](https://github.com/AutoMQ/automq/pull/3733#issuecomment-6600723847)、[FasterXML 安全公告](https://github.com/FasterXML/jackson-databind/security/advisories/GHSA-m8xf-2cr7-77ph)

11 月 6 日 03:28，#3743 合并 main，处理 KVImage.EMPTY、S3ObjectsImage.EMPTY、S3StreamsMetadataImage.EMPTY 共享单例被 release 到 refCnt=0 后无法复用的问题，也覆盖同 JVM 第二个 MetadataLoader 首次 KV 更新失败。作者称生产遇到过异常，但未公开内部堆栈；公开验证来自 EMPTY 生命周期、双 loader 回归及相关测试。没有完整 broker E2E、生产 OOM 根因修复或 backport 验证的证据。[修复 PR](https://github.com/AutoMQ/automq/pull/3743)、[生产反馈及证据边界](https://github.com/AutoMQ/automq/issues/3744)

### 5. 尚未落地的安全与生态方向

Prometheus Basic Auth #3579 在 11 月 6 日得到维护者实质反馈：认可默认关闭、由部署层提供 TLS 的可选 Basic Auth 路线；要求集中模式选择和校验，分离公共 endpoint 策略与凭证检查，并把 exporter 测试和 broker 配置到 authenticator 的链路纳入 CI。维护者指出，现有 workflow 不运行 automq-metrics:test，AutoMQConfigTest 也未纳入 core:S3UnitTest。**当前仍 open，不能称已提供该功能。**[评审意见](https://github.com/AutoMQ/automq/pull/3579#issuecomment-6675874203)

11 月 4 日新建 #3739，请求在 S3 URI 中加入 serverSideEncryption 参数，以适配强制 SSE 的 bucket policy；截至观察窗末没有回复或已合并实现。Kafka 4.x 的 #2950 则在 11 月 3 日出现用户再次要求公开路线图的评论，反映 Strimzi 升级受阻，但没有新的官方 ETA。另 11 月 3 日已合并 #3708，将 DevKit 构建 JDK 前置条件从 17+ 明确为 17–22，对齐 Gradle 8.8 支持范围。[SSE 请求](https://github.com/AutoMQ/automq/issues/3739)、[Kafka 4.x 讨论](https://github.com/AutoMQ/automq/issues/2950#issuecomment-6598652429)、[DevKit 文档修正](https://github.com/AutoMQ/automq/pull/3708)

## 跨项目观察

**提交结果与清理资格必须分开。** Fluss Iceberg 的 unknown commit 不能触发新文件删除；普通 remote log tiering 的相似问题仍在另一个开放 PR 中。AutoMQ 的状态冲突应先中止当前恢复尝试，再重取 streams。两者都拒绝“收到错误就按原上下文继续”，但前者保护可能已提交的数据，后者改变重试的成功条件，不能用同一个重试参数概括。

**正确性验证需要覆盖旧状态与新状态交界。** Kafka 的 aborted transaction 在清理区间外结束，却污染区间内 tombstone；Fluss 的旧 reader 可能把新压缩标志当成记录类型；AutoMQ 的共享 EMPTY 单例则会把一次释放带来的损坏传递给后续 loader。测试除了正常读写，还要覆盖截点、重启、重用和滚动升级。

**可恢复不等于无损，可读不等于事件有序。** AutoMQ 未接受保留失败点后 WAL 的方案，是因为内部流之间的一致性约束仍未解决；Fluss Iceberg full union read 的原始读取可能不丢不重，但 event-time watermark 仍可能让下游丢弃晚到记录。报告应分别说明字节保留、状态一致性、已确认写入与业务时间语义。

## 下一周最值得核验的证据

- Kafka：#24072 和 #24028 的实际发行或回移版本；3.9.3 blocker 清单与首个 RC；#23639 的 BADVERSION 分类和任期隔离是否最终合并；静态 quorum 隐式转换的防护是否落地。
- Fluss：GSI 的全表 SYNC 依赖、snapshot discovery、升级 gate 与候选上限是否收敛；#5076 的提交未知保护是否合并并覆盖 failover；#5077 是否形成可验证的 planner/restore 顺序契约；已合并修复是否进入可下载版本。
- AutoMQ：rc3 之后的修复在哪个实际发行中交付；shaded Jackson 的版本风险及可达路径如何处理；#3671 是否在独立故障语义测试后合并；WAL 截断策略如何向运维人员明确可能的损失范围。

这些都是具体的状态、回归场景或发行证据，不应以更多 closed/merged 数量替代。

## 证据与阅读范围

事实状态以官方仓库、版本页面、提案及公开邮件为依据。PR 正文、review 与最终方案矛盾时，正文明确指出变化，不沿用已被修改的早期说明。closed issue、LGTM、分支回移、main/trunk 合并和正式发布分别记录。

Kafka 读取了关键 PR 状态、正文、评审和邮件回复。3.9.3 发布计划的动态 Jira 表未能完整展开，本文没有声称取得完整 blocker/fix 清单。4.4.0、4.3.2 及此前 CVE 公告不计成本周新发行。KAFKA-21349 本周虽被标记 resolved，其 #23943 在 10 月 27 日已经合并，也不重算本周新增。KIP 投票状态以取得的线程为准，未读到 RESULT 不等于断言任何未被索引的回复都不存在。

Fluss 枚举了官方合并列表，并查看本周 updated issues/PRs 的前 100 条及重点评论；按精确起点排除 10 月 30 日中午前合并后，窗口内为 48 个合并 PR，这只是检索到的活动量。读取了 Discussions 与路线图，未核实到窗口内新里程碑决议。Apache 邮件列表页面未取得可解析正文，限定月份的搜索没有结果，不能据此判断没有讨论或投票。

AutoMQ 读取了官方 Issues、PR、关键评审和 Releases。仓库未开启 GitHub Discussions；官网博客列表未能有效解析，不能据此声称本周没有博客或社区活动。没有读取需加入的 Slack、微信群或 Telegram，也不把组织 issue 查询无结果等同于其他仓库没有 commit。

本次研究没有部署三套系统、运行产品测试或复现性能实验。上游测试通过只支持其报告的场景，不保证所有平台、旧版本、部署拓扑或故障条件。来源索引仅保存引用和派生分析，不转载完整讨论、论文或第三方原文。
