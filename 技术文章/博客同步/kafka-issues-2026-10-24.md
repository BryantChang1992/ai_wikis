---
type: survey
title: Kafka Issue 周报：修复合并之后，交付证据仍要逐层确认
sources:
- https://issues.apache.org/jira/projects/KAFKA/issues
- https://github.com/apache/kafka/pull/23737
created: '2026-10-24'
updated: '2026-11-09'
status: draft
tags:
- Kafka
- issue
- 社区观察
related:
- '[[知识库/sources/web/Kafka-Issue-2026-10-24]]'
source_checked: '2026-10-24'
source_check_scope: 官方公开问题、变更历史和重点 PR；未运行复现。
publication_scope: 公开技术报告及引用；知识卡和独立专题不因本文同步而扩大发布范围。在线状态以实际部署验收为准。
report_date: '2026-10-24'
---

# Kafka Issue 周报：修复合并之后，交付证据仍要逐层确认

> 阅读时间说明：本文保留 2026-10-24 报告的观察窗口、原文核验时间和技术限制。正文中的“本周”、版本阶段及历史交付说明均按原观察时点理解，不代表本次页面整理时的最新状态。本次仅适配发布格式，未重新核读全部外部来源或独立复现实验。

[公开来源索引](../../知识库/sources/web/Kafka-Issue-2026-10-24.md)

观察区间：2026-10-17 12:00:00（含）至 2026-10-24 12:00:00（不含）UTC，即北京时间 10 月 17 日 20:00 至 10 月 24 日 20:00。本期接续上期既定截止，不因上期未发布而遗漏一周，也不补发或覆盖上期内容。正文事件日期统一为 UTC；检索在截止后进行，只纳入窗口内事件。数据抓取始于 12:03 UTC，检索截止 12:15 UTC；精确抓取时间见来源索引。

KIP-1150 的 10 月 23 日独立记录已存在。

## 本周结论

本周最值得关注的不是“关闭了多少票”，而是一次修复要经过多少个不同边界：从问题能否复现，到代码是否确实阻止错误；从主干合并，到回移分支；再从版本标签，到正式发行。

官方 JIRA 公开可见结果显示，窗口内新增 **53** 个 issue。**24** 个 issue 出现设置 resolution 的事件，但其中 **KAFKA-21255 随后重开**，当前仍处于已解决状态的是 **23** 个。这 23 个也不全是修复：**19 Fixed、2 Duplicate、1 Later、1 Done**。本期新增与解决集合合并去重共 **73** 个 issue，而非 77 个互不重叠的问题。Fixed 是工作流分类，不代表每项都是生产 bug，更不代表已发布。

新增的 53 项包括 23 Bug、12 Improvement、11 Sub-task、6 Task 和 1 Test；截至窗口末 49 项仍未解决、4 项已解决。优先级由提交者和社区维护，不在这里改写成客观故障等级或受影响集群规模。官方 [JIRA KAFKA](https://issues.apache.org/jira/projects/KAFKA/issues) 是本期生命周期统计来源；[apache/kafka 仓库配置](https://github.com/apache/kafka/blob/trunk/.asf.yaml)与[仓库 API](https://api.github.com/repos/apache/kafka)确认 GitHub Issues 未启用，GitHub PR 只作为实现、评审和回移证据，不能并入“新增 issue”计数。

下文围绕逻辑读边界、共享消费请求状态、事务状态机与兼容分支组织。跨项目设计背景留给已发布的[《流存储技术观察》](https://bryantchang1992.github.io/ai_memory_chang_ai_team/stream-storage-observer/)；KIP-1150 的协议变化沿用[独立专题](https://github.com/BryantChang1992/ai_wikis/tree/master/知识库/专题跟踪/KIP-1150)。本期只补问题生命周期与修复证据，不把所有 Kafka bug 强行关联到该 KIP。

## 一、逻辑读取边界，不能由物理文件末尾代替

10 月 23 日 15:34:33 UTC，[#23737](https://github.com/apache/kafka/pull/23737) 合入 trunk，修正 FileRecords.readInto 没有遵守逻辑 slice 边界的问题。这条修复把两个看似不同的事故连起来：预分配日志中的零填充可能让 group coordinator 误报记录损坏；KRaft 则可能把 HWM 之外尚未提交的记录交给 metadata layer。共同根因不是 CRC 算法或磁盘损坏，而是“物理文件中还能读到字节”被误当成“这些字节属于当前逻辑读取”。[合并提交](https://github.com/apache/kafka/commit/7ac40f4dede35c79b9c1bd27dd5a17c70e33fa6f)

### 问题如何发展

- [KAFKA-20841](https://issues.apache.org/jira/browse/KAFKA-20841) 于 7 月 27 日建立，记录了 coordinator loader 在 log.preallocate=true 时读到 slice 之外零填充的机制。报告者在 Apache kafka-clients-4.2.0 工件上完成独立复现；生产观察来自 Confluent Platform 8.2.1，不能写成全部 Kafka 4.2 集群实测。实际逻辑记录未观察到持久损坏，问题可表现为 CorruptRecordException、coordinator shard 进入 FAILED，并被 ListGroups 空列表掩盖。Jira affects=4.2.0；没有完整版本扫描，不能把此字段当成影响范围上限。
- [KAFKA-21234](https://issues.apache.org/jira/browse/KAFKA-21234) 于 10 月 6 日建立，描述 MetadataLoader 收到未提交数据。10 月 7 日以 Duplicate 关闭并关联 KAFKA-20841，但 PR #23737 后来继续完成通用 FileRecords 修复。因此“Jira 已关闭”并不等于当时已修复；截至本次截点，20841 仍 Open、fixVersions 为空，21234 仍是 Duplicate，代码却已 merged。
- 本周关键增量是 10 月 20 日评审明确了通用 iterator 的职责边界，10 月 23 日合并并打开多个版本线回补，而不是两个问题首次被发现。

### KRaft 触发条件，必须三项同时写清

PR 明列以下三项：
1. 一次交给 listener 的 committed read 大于 8 MiB（KafkaRaftClient 的 MAX_BATCH_SIZE_BYTES）。
2. 同一 segment 在 HWM 之后还有本节点已 append、但尚未 commit 的字节。
3. snapshot generator 在 HWM 追上之前，已从受影响 metadata image 发出 snapshot。

因此不能泛化成“读超过 8 MiB 就损坏”或“所有快照都会混入未提交数据”。大 slice、物理尾部包含未提交内容、snapshot 时序共同构成这里报告的错误。预分配零填充事故则是同一缺陷的另一触发形态，不要求上述三个 KRaft 条件。

### 修复机制与评审真正保留下来的边界

最终代码以当前 FileRecords.sizeInBytes() 为上界，校验相对读取位置，设置 buffer limit 为 buffer.position() + min(buffer.remaining(), currentSize - position)，再调用底层 readFully。这把 slice 的逻辑长度下沉为 FileRecords 自身的契约，而不只在某一个 CoordinatorLoader 调用点打补丁。覆盖了非零起点 slice、slice 末尾、非法位置、预分配与非预分配文件。RecordsIterator 相应允许 firstBatchSize 为 null，处理不足完整 batch header 或 slice 尾部不足一个 batch 的情况。[最终补丁](https://github.com/apache/kafka/pull/23737/files)

评审曾尝试在 RecordsIterator 检测到不完整 batch 时抛异常，理由是当前 KRaft 调用者的 HWM、LEO、snapshot offsets 应当 batch-aligned。但 [10 月 20 日的讨论](https://github.com/apache/kafka/pull/23737#discussion_r4329966752) 最终撤回该方案：底层 FileRecords 并未保证 immutable、batch-aligned，通用 iterator 不应根据当前调用者的惯例收紧整个类型的契约。如果 raft 要强制这种约束，应该在具有明确保证的 records 类型或调用层落实。最终行为是只返回完整 batch、尾部不完整时结束迭代，并非新增“见 partial batch 就抛异常”的实现。

这也是本周最适合抽成机制卡的结论：逻辑边界修复可以下沉到通用容器；业务层的更强不变量却不应未经类型契约证明就一起下沉。二者不能混为一个“更严格更安全”的改动。

### 版本、回补与 KIP 口径

10 月 23 日 15:58，作者明确表示这不是 regression，但因会向 metadata layer 暴露未提交数据，值得回补旧版本。[回补理由](https://github.com/apache/kafka/pull/23737#issuecomment-6369066877)

当日 16:34 依次打开：[#23938 → 4.4](https://github.com/apache/kafka/pull/23938)、[#23939 → 4.3](https://github.com/apache/kafka/pull/23939)、[#23940 → 4.2](https://github.com/apache/kafka/pull/23940)、[#23941 → 3.9](https://github.com/apache/kafka/pull/23941)。截至截点四项均 Open、merged=false。准确写法是“trunk 已合并，4.4/4.3/4.2/3.9 回补待合并”，不是“这些版本已修复”。没有查到包含本次修复的正式发行证据。Jira 与 PR 未给出直接 KIP 关联；不要把它算作某个 KIP 的新功能或完成项。

## 二、Share fetch 缓存寿命修好了，公平性却留下明确新问题

10 月 23 日 12:58:43 UTC，[#23911](https://github.com/apache/kafka/pull/23911) 合入 trunk，将 fetch-offset metadata 缓存由 SharePartition 移到每个 DelayedShareFetch 请求。原缓存跨请求存在：partition 被读出但最后被 response 裁掉，或者请求失败，fetch offset 没推进，缓存却仍保留；released record 的再次获取也可能要等到 timeout。新设计让请求内 purgatory 重试仍复用缓存，但下个请求重新读取，消除了跨请求旧状态及相应 remote fetch reset。[合并提交](https://github.com/apache/kafka/commit/ea6afaa4617b8168f060803c55e90f84230531e4)

评审发现了两个不能由“测试都过了”掩盖的问题：

- 改动最初让七个 minBytes 测试从“同 segment 比较字节量”悄悄走到“旧 segment 直接完成”的分支，测试通过却不再验证 fetch.min.bytes。评审指出后已调整测试，并补了“同请求同 offset 重试不重读、新请求要读”的测试。[分支覆盖评审](https://github.com/apache/kafka/pull/23911#discussion_r4350717570) · [补测试答复](https://github.com/apache/kafka/pull/23911#issuecomment-6353284161)
- 更重要的是，[10 月 23 日 05:34 的评审](https://github.com/apache/kafka/pull/23911#pullrequestreview-5624325594) 发现一个分区饥饿场景：share session 的 LRU 顺序与 sessionEpoch % numPartitions 轮转叠加；poll()+commitSync() 每轮同时推进 ShareFetch 和 ShareAcknowledge，epoch 每次增加 2。两个分区时，一个额外 acknowledge 或空 fetch 改变奇偶性后，刚服务过的分区可能反复被转回首位，吃完 record budget，另一个分区持续饥饿。四分区也有相应遗漏情形。旧版的跨请求缓存意外改变响应顺序，曾掩盖这个组合问题；移除旧缓存后暴露了回归风险。

作者在 12:47 接受这个案例，但为不阻塞其他改动选择另开 [KAFKA-21344](https://issues.apache.org/jira/browse/KAFKA-21344)；评审者在 12:53 同意尽快另修，12:58 原 PR 合并。[作者确认并拆分](https://github.com/apache/kafka/pull/23911#issuecomment-6365229941) · [评审放行](https://github.com/apache/kafka/pull/23911#pullrequestreview-5628481846)

截至截点，KAFKA-21344 Open，没有 affects/fix versions，按票号检索仅找到上述原 PR，没有独立合并修复。最终测试包含普通 deep-backlog 公平性，不包含评审提出的 epoch parity 切换用例。准确结论是“缓存生命周期修复已合并，但已知轮转饥饿边界另案未闭环”，不能写成“公平性问题全部修复”。PR 没有直接 KIP 标记；它属于 share group 实现的后续正确性工作，而不是新 KIP 获批。

## 三、TLS/Fetch 从隐瞒磁盘错误走向明确故障处置

[KAFKA-16304](https://issues.apache.org/jira/browse/KAFKA-16304) 建于 2024-02-23，问题是 Fetch 的真正磁盘读取被推迟到 network thread 的 FileRecords.writeTo；磁盘与断连都作为 IOException 进入 Selector，后者只关连接、不让 log directory offline。[#23445](https://github.com/apache/kafka/pull/23445) 在 10 月 20 日 17:50:53 合入 trunk：失败交给存储层，在 scheduler 重读失败区间，每个 log directory 最多一个并行检查，仅再次读失败才 offline；ClosedChannelException 不按介质错误处理，网络线程不追加重读 I/O。

[KAFKA-21280](https://issues.apache.org/jira/browse/KAFKA-21280) 于 10 月 14 日发现了更靠前的 TLS 缺陷：fileChannelBuffer.clear() 后读失败/读不到字节，没有 flip；若本次调用此前已发送部分内容，异常还被吞掉，下一次 transfer 会把上一块旧 buffer 当作下一块发送。客户端 CRC 能发现错误，表现为健康副本上可读的内容从当前 leader 无法继续消费；这是同一连接的旧内容，原报告明确不是跨连接内容泄露。[#23832](https://github.com/apache/kafka/pull/23832) 于 10 月 20 日 18:10:32 合并，改为 finally flip 并立即传播 IOException，使存储故障处理真正能覆盖 TLS 路径。

两个 Jira 均于当日变成 Resolved/Fixed，fixVersion=4.5.0、released=false。16304 的已登记 affected versions 为 3.6.1/3.7.0，21280 为 2.5.0/4.3.1；这些是票据标签，不是完整受影响区间。未发现已合并的维护分支回补，也没有正式发行证据。目录 offline 可能导致仅有该目录或 metadata 目录的 broker 关闭，这是明确的故障隔离语义变化，不只是日志级别变化。

10 月 23 日新增的 [#23928](https://github.com/apache/kafka/pull/23928) 继续处理 TLS 已经知道是文件错误、却仍要重读猜测的问题，拟以 FileReadException 直接上报；PLAINTEXT sendfile 仍然无法区分文件和 socket，需要重读；KRaft snapshot 的 UnalignedFileRecords 路径仍不覆盖。截至截点该 PR Open，不能写成已实现。比前一期新增的进展是 23 日晚 Jun Rao 的评审建议：已知文件错误也许可直接 inline 上报，不必额外 scheduler/并发槽位；并建议集中封装 ClosedChannelException 的例外规则。方案细节仍在评审，不应把当前草案的 scheduler 设计当成最终定案。[23 日晚评审](https://github.com/apache/kafka/pull/23928#discussion_r4364794578)

## 四、TV2 用日志写入迫使过期协调器暴露自己

[KAFKA-21181](https://issues.apache.org/jira/browse/KAFKA-21181) 于 9 月 29 日建立，指出 ReplicaManager 先应用 leader 变更、TransactionCoordinator 稍后 resignation 的间隙，旧 coordinator 仍可从 cache 给出错误的 fatal INVALID_TXN_STATE。前一层修复 #23630 校验本地 replica 领导权；本周 [#23831](https://github.com/apache/kafka/pull/23831) 于 10 月 20 日 16:42 合入 trunk，处理连 metadata 变更都尚未应用的旧 coordinator。

TV2 在 Empty/CompleteCommit/CompleteAbort 状态收到 current-epoch Commit 时，改为提交无 partition 的空事务：epoch bump，写 PrepareCommit，无 marker 直接完成。旧 coordinator 的 acks=-1 日志写入不能复制成功，因而返回 retriable coordinator error，客户端重新查 coordinator，而不是被纯 cache 的 fatal 错误击倒。真正没有写数据的事务则只是 no-op epoch bump。TV1 不变；retry 路径不与 current-epoch 请求混淆。

回补已合入 4.3（[#23884](https://github.com/apache/kafka/pull/23884)，10 月 20 日 22:17）及 4.2/4.1/4.0（[#23885](https://github.com/apache/kafka/pull/23885)、[#23886](https://github.com/apache/kafka/pull/23886)、[#23887](https://github.com/apache/kafka/pull/23887)，21 日 16:32）。4.0–4.2 没有 KAFKA-20785，CompleteAbort+Commit+Retry 保留 INVALID_TXN_STATE，不可照搬 trunk 的 PRODUCER_FENCED。

发布口径尤其要谨慎：该 Jira 仍 In Progress，fixVersions 却列出早已发布的 4.0.0/4.1.0/4.2.0/4.3.0，字段显然不能证明本次代码已在这些发行包中。4.3.2 annotated tag 建于 10 月 20 日 12:09:55，比本次 4.3 回补早；[GitHub 比较](https://github.com/apache/kafka/compare/05bf7f5f38786dc9251661fdae3a5dc4fb698d09...4.3.2) 返回 behind 7 commits，直接证明该 4.3.2 tag 不包含本次空事务修复。写“维护分支合并”即可，不指定已交付版本。原 issue/PR 没有直接 KIP 关联，TV2 语义背景不等于本次新增 KIP。

## 短讯与升级边界

- [KAFKA-21303 / #23856](https://github.com/apache/kafka/pull/23856)：18 日建票、22 日 09:23 合入 trunk、Jira 同日 Fixed，fixVersion=4.5.0 未发布。consumer group reload 对 classic member 错用了统一 consumer-protocol timeout，可能把原本 10s 变成 45s，延迟故障检测，或把 60s 缩成 45s，提前剔除。最终从持久化 classicProtocolSessionTimeout 取值，非 classic 才回退 consumer timeout。测试明确验证混合成员的 10s/45s 分别恢复。未登记 affected version；没有直接 KIP 引用，不宜给出完整影响版本范围。
- [KAFKA-20960 / #23338](https://github.com/apache/kafka/pull/23338)：20 日 18:22 合入 3.9，不是 trunk。controller activation 在仍有 ZK-registered broker 时保持 MIGRATION，打印阻塞 broker ID，不写 POST_MIGRATION；不是抛异常中止整个 controller。票据仍 Open，affects=3.9.0/3.9.1/3.9.2，fixVersions 空。维护者已明确[可能永远不会有包含此修复的 3.9.x 正式版本](https://github.com/apache/kafka/pull/23338#pullrequestreview-5168605731)，因此合并不等于维护版本发布承诺。
- [#23935](https://github.com/apache/kafka/pull/23935) 于 23 日 16:23 合入 4.3，只修正文档：KAFKA-20464 的升级说明归属 4.3.2，而不是 4.3.0。多个 processor 经 ConnectedStoreProvider 返回同一个 StoreBuilder 时，现在归入同一 subtopology；受影响应用升级后 task IDs 改变、首启从 changelog 恢复状态。按 store name 链接不受影响。这是此前修复的版本归属与迁移成本澄清，不要当成本周新代码修复。Jira fixVersions 为 4.4.0、4.2.2、4.3.2，JIRA 中只有 4.2.2 标为 released（2026-09-29）；4.4.0/4.3.2 的 JIRA 标记仍未更新，但官方分发端已列出工件，见下一节。不能将 JIRA 标记直接当成发行事实。

## 发布证据总边界

Apache Kafka 的 GitHub releases API 本次返回空数组，这不代表没有发行。补充核读 [Apache 官方分发目录](https://downloads.apache.org/kafka/)确认 4.4.0 的目录时间为 10 月 15 日、4.3.2 为 10 月 20 日；[4.3.2 分发目录](https://downloads.apache.org/kafka/4.3.2/)实际列出源码包、二进制包、签名、校验和与 release notes。同时[项目下载页](https://kafka.apache.org/community/downloads/)仍列 4.3.1，展示了发布渠道更新不同步。分发目录证据证明官方分发端已有工件，强于仅看 git tag；这里不把目录修改时间冒充公告日期，也未下载整个发行包重编译验证。JIRA released 标记与分发状态不同步，因而不能用一个字段否定公开工件。

[4.3.2 release notes](https://downloads.apache.org/kafka/4.3.2/RELEASE_NOTES.html)明确列出 KAFKA-20464，支持前述 Streams 升级说明归属纠正。这仍然不能把本周所有维护分支合并塞进 4.3.2：前述 tag 比较明确排除了 TV2 的这次空事务回补。本文对每项修复分别陈述包含证据；未核得的具体交付版本继续写未知，而不是笼统宣称“新版本已全部修复”。检索截止补充至 2026-10-24 12:13 UTC，事件统计窗口保持不变。

## 五、重点新增：仍在等待验证与修复

统计窗口：2026-10-17 12:00:00 UTC（含）至 2026-10-24 12:00:00 UTC（不含）。以下五项在截止时均为 Open、resolution 为空。问题机制和复现结果来自票据作者的公开报告，并非本报告独立复现实验。PR 状态在 10 月 24 日 12:07–12:08 UTC 抓取，仅作截止后核验；未将其计入本周合并成果。Fix Version 是票据目标，不代表已发布。

### 1. KAFKA-21349：事务协调器可能据未提交日志行动，破坏跨分区一致性

- 新建：10 月 23 日 21:35 UTC；Major；组件 core。
- 问题与影响：事务状态加载读到 log end，而新 leader 可能持有高水位之上的未提交 PREPARE_COMMIT/PREPARE_ABORT。报告构造的连续 leader 切换场景中，部分分区先收到 COMMIT，后继 leader 丢失该未提交状态并按超时发送 ABORT，可能出现同一事务在不同分区提交/中止分裂。
- 原因分析：加载阶段把“已经复制到本机”当成“已经提交”，随后发出不可轻易撤回的事务 marker。只改成读取 HIGH_WATERMARK 也不充分，因为新 leader 的高水位可能暂时落后于真实提交位置。
- 建议方向：报告提议先记录加载起点的 log end，待高水位追上才加载；通过 PartitionListener 处理进度，并正确清理 epoch/领导权变化、注册竞态和过期事务清理路径。该方向仍待代码评审验证。
- 状态：无已确认影响版本/修复版本；[PR #23943](https://github.com/apache/kafka/pull/23943) 为 open、未合并；JIRA 评论 0 条。应作为事务原子性风险线索跟踪，而非宣称所有发行版已被独立证实受影响。
- 原始来源：[KAFKA-21349](https://issues.apache.org/jira/browse/KAFKA-21349)。

### 2. KAFKA-21306：Streams 静态成员跨进程重入，绕过任务互斥

- 新建：10 月 19 日 13:44 UTC；Critical；组件 streams；票面影响 4.4.0，修复目标 4.4.1、4.5.0。
- 问题与影响：静态成员以新的 member/process ID 重入时，会继承旧分配；若新进程中的另一线程已持有该 task 的 standby/warmup，便会让同一进程短时同时持有同一 task 的 active 和 standby。持久存储的目录锁可能让 active 停顿；无持久存储时则可能重复占用内存和执行恢复工作。不能据此直接等同于“两份 active 重复消费”。
- 原因分析：互斥检查只覆盖待分配任务，没有重新检查继承来的已分配任务；新分配虽会撤销 standby，但撤销被确认前仍有重叠窗口。
- 建议方向：进程 ID 变化时，把冲突的继承任务退回待分配，让既有 process-level exclusivity 检查重新生效。作者附有 trunk 单元测试复现；影响说明中客户端后果属于其代码分析。
- 状态：[PR #23873](https://github.com/apache/kafka/pull/23873) 为 open、未合并；JIRA 评论 0 条。票面修复目标尚不是修复落地证明。
- 原始来源：[KAFKA-21306](https://issues.apache.org/jira/browse/KAFKA-21306)。

### 3. KAFKA-21315：Share partition 确认回滚后卡在已删除 offset，持续不再投递

- 新建：10 月 20 日 09:32 UTC；Major；组件 core；票面影响 4.5.0。
- 问题与影响：ACCEPT 正在持久化时，retention/DeleteRecords 推进 log start offset；若锁过期且持久化失败，回滚会把旧 batch 恢复为 AVAILABLE，但其 offset 已低于新的起点。随后 fetch 反复 OFFSET_OUT_OF_RANGE，后面的有效消息也不能投递。
- 原因分析：archiveRecords 当初因 batch 并非 AVAILABLE 而跳过它；失败回滚没有补做起点检查，nextFetchOffset 因而反复返回过时 offset，updateCacheAndOffsets 又因起点没有再次增长而提前返回。
- 建议方向：过期锁的状态回滚应归档起点之前的记录，或让 nextFetchOffset 跳过这些 offset。票据附回归测试；10 月 20 日 09:41 UTC 有维护者表示会查看，09:49 UTC 报告者补充称需要 leader 变化或完整停掉 consumers 以重建 SharePartition 才似乎恢复。这不是已确认的通用运维方案。
- 状态：无 Fix Version、无 JIRA remote-link PR；评论分页完整，共 2 条。尚无修复完成证据。
- 原始来源：[KAFKA-21315](https://issues.apache.org/jira/browse/KAFKA-21315)。

### 4. KAFKA-21317：log start 前移后，按时间戳查询可能漏掉后续 segment 的有效 offset

- 新建：10 月 20 日 09:42 UTC；Major；组件 core。
- 问题与影响：DeleteRecords 等操作将起点推进到一个仍保留的 segment 内，过期记录的缓存最大时间戳仍令该 segment 满足初筛；实际查找因记录已在起点之前而返回空。上层直接返回空，漏查后续 segment 中的合法结果，影响按时间定位消费起点的正确性。
- 原因分析：UnifiedLog.searchOffsetInLocalLog 把“第一个候选 segment”误当成“最终结果”，没有在空结果后继续扫描。
- 建议方向：持续扫描符合条件的 segment，直到找到有效 offset，并用内存中的 segment base offset 跳过过时段。报告者称在 4.5.0-SNAPSHOT 的指定 trunk commit 上复现，补丁后回归测试通过，UnifiedLogTest/LogSegmentTest 共 243 项通过；这些是作者报告，不是本周报重跑结果。与 KAFKA-10875 的等价性尚未确定。
- 状态：票面未指定影响/修复版本；[PR #23880](https://github.com/apache/kafka/pull/23880) 为 open、未合并；JIRA 评论 0 条。
- 原始来源：[KAFKA-21317](https://issues.apache.org/jira/browse/KAFKA-21317)。

### 5. KAFKA-21341：TLS close_notify 与数据同批到达时，连接关闭可能被延迟到请求超时

- 新建：10 月 23 日 09:38 UTC；Major；组件 clients、network。
- 问题与影响：应用数据与 TLS close_notify 在同一次 socket read 中到达、对端不立即发送 TCP FIN 时，客户端可能交付已有数据，却不再识别 TLS 入站关闭。未完成请求将一直等待 request.timeout.ms，而不是及时断连重试；报告指出 TLS 终止代理的半关闭行为可触发该路径。
- 原因分析：SslTransportLayer 先返回数据，随后 updateBytesBuffered 清掉 buffered-read 标记；Selector 因而等待新的 socket 可读事件，尚未处理的 TLS CLOSED 状态被搁置。
- 建议方向：CLOSED unwrap 后保留 buffered-read 调度；明文缓冲耗尽且 inbound done 时抛出 EOF；散布读路径要保留 EOF 前已读出的字节。还需保留 muted channel 先完成响应再关闭的语义。
- 状态：JIRA 影响版本字段列出多个 3.6.x 至 4.x/4.5.0 版本，但本次没有逐发行版复现；无 Fix Version。[PR #23933](https://github.com/apache/kafka/pull/23933) 为 open、未合并；JIRA 评论 0 条。
- 原始来源：[KAFKA-21341](https://issues.apache.org/jira/browse/KAFKA-21341)。

## 计数和优先级提示

本周唯一标为 Blocker 的新票 [KAFKA-21323](https://issues.apache.org/jira/browse/KAFKA-21323) 是为 5.0.0 移除 client-metrics 匹配表达式的 legacy java.util.regex fallback，属于版本迁移清理，不应仅凭 Blocker 标签把它描绘为本周新发现的线上故障。以上选题按潜在影响与可解释的故障机制排序，而非机械地按 priority 排序。

## 重开项补充：KAFKA-21255

[KAFKA-21255](https://issues.apache.org/jira/browse/KAFKA-21255) 并非本周新建：10 月 19 日 11:23:25 UTC 从未解决转为 Fixed，18:47:45 UTC 又重开并清空 resolution。10 月 20 日维护者评论要求面向 4.3 的 PR，并说明 4.3/4.2 需要手工回移；其关联 [PR #23768](https://github.com/apache/kafka/pull/23768) 已在 10 月 13 日合并，早于本窗口。因此“本周 24 项发生解决事件”应保留它，但“截至截止仍已解决”仅 23 项；重开也不能被表述为 trunk 修复失效的证明。


## 非 Fixed 的四项解决事件

1. [KAFKA-20642](https://issues.apache.org/jira/browse/KAFKA-20642)，Duplicate，2026-10-17 14:30:26 UTC。主题是 Kafka shell glob 的字符类/字符范围支持。关闭者的两条评论明确指向重复主票 [KAFKA-20189](https://issues.apache.org/jira/browse/KAFKA-20189)，不是本票新增实现完成。

2. [KAFKA-15560](https://issues.apache.org/jira/browse/KAFKA-15560)，Duplicate，2026-10-20 08:43:17 UTC。主题是 argparse4j 升级；JIRA duplicates 关系明确指向 [KAFKA-12744](https://issues.apache.org/jira/browse/KAFKA-12744)，后者在当日 08:42:44 UTC 已转 Fixed。因此同一升级不应按这两张票重复计成两项修复。唯一旧评论讨论 2023 年的 JDK 8 兼容限制，不应误当作本次关闭理由。

3. [KAFKA-21226](https://issues.apache.org/jira/browse/KAFKA-21226)，Later，2026-10-19 06:32:22 UTC。主题是 Cluster Mirroring 的 ClusterMirrorListing、ClusterMirrorDescription 两个 Admin client 类型。JIRA 没有评论，但 [PR #23829 的 10 月 19 日 review](https://github.com/apache/kafka/pull/23829#pullrequestreview-5566724246)说明 listing/describe 实现尚未完成，建议等实现后再有意义地评审并补测试；作者随后[同意暂时关闭](https://github.com/apache/kafka/pull/23829#issuecomment-6260470356)。PR 已关闭、未合并，属于暂缓，不是取消功能，也不是实现完成。

4. [KAFKA-21225](https://issues.apache.org/jira/browse/KAFKA-21225)，Done，2026-10-23 02:39:40 UTC。主题是新增 mirror exceptions。JIRA 无 description/评论，但关联 [PR #23828](https://github.com/apache/kafka/pull/23828)确于 2026-10-23 02:39:11 UTC 合并，增加 Cluster Mirroring 所需 exceptions/protocol errors，PR 说明当前尚未将 exception 标为 public。此项是代码任务完成，不能因 resolution 不是 Fixed 就归类为“无代码关闭”。

核验范围：四项 JIRA 评论分别返回 2/2、1/1、0/0、0/0；PR #23829 issue comments 1 条、reviews 1 条、review comments 0 条，所有 GitHub 列表无下一页 Link。有关评论/review 均早于截止。补充抓取时间为 2026-10-24 12:12–12:14 UTC；合并/关闭事件的发生时间仍按 API 时间戳计算。

本次已读取的两张 JIRA 票据及关联 PR 描述没有直接提及 KIP-1150；不据“Cluster Mirroring”主题自行建立 KIP 关联。

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

## 下一观察点

1. #23737 的四条回移是否完成，并出现真正包含该提交的发行证据。
2. KAFKA-21344 的 epoch 奇偶性用例能否进入回归测试，而非仅以普通双分区公平性测试替代。
3. KAFKA-21349 的加载屏障能否同时处理高水位追赶、leader epoch 变化和监听注册竞态。
4. TV2 已合并维护分支最终落在哪些发行包；JIRA fixVersions 与实际 tag/公告必须分别核验。
5. KAFKA-21255 的手工回移是否闭环，避免将重开自动解释为原修复失败。

本报告未独立运行 Kafka 复现或性能测试。所有测试通过说法均归于公开作者/评审记录；不存在本报告生成的性能数值、版本承诺或社区共识。没有直接 KIP 证据的票据标为未确认关联，不依据题材相近自动归因。

## 附录：逐项可核查清单

标题保留官方原文；版本栏只表示 JIRA 字段，不证明发布。完整 CSV 另列组件、版本、创建与状态变化时间。下表按 issue 去重；“新增”与“解决事件”可以同时出现。

| Issue | 标题 | 本周事件 | 截止状态 / resolution |
|---|---|---|---|
| [KAFKA-12188](https://issues.apache.org/jira/browse/KAFKA-12188) | SaslAuthenticatorTest: assert the specific failure reason instead of catching any AssertionFailedError | 2026-10-20 Fixed | Resolved / Fixed |
| [KAFKA-12744](https://issues.apache.org/jira/browse/KAFKA-12744) | Dependency upgrade: "argparse4j" 0.7.0 -->> 0.9.0 | 2026-10-20 Fixed | Resolved / Fixed |
| [KAFKA-15560](https://issues.apache.org/jira/browse/KAFKA-15560) | Upgrade argparse4j to 0.9.0 | 2026-10-20 Duplicate | Resolved / Duplicate |
| [KAFKA-16304](https://issues.apache.org/jira/browse/KAFKA-16304) | Disk I/O error does not offline log directory while handling Fetch requests | 2026-10-20 Fixed | Resolved / Fixed |
| [KAFKA-17688](https://issues.apache.org/jira/browse/KAFKA-17688) | Move TransactionsTest to storage module | 2026-10-20 Fixed | Resolved / Fixed |
| [KAFKA-20391](https://issues.apache.org/jira/browse/KAFKA-20391) | Improve types returned by the Connect REST API | 2026-10-19 Fixed | Resolved / Fixed |
| [KAFKA-20642](https://issues.apache.org/jira/browse/KAFKA-20642) | Support character ranges in Kafka shell globs | 2026-10-17 Duplicate | Resolved / Duplicate |
| [KAFKA-20858](https://issues.apache.org/jira/browse/KAFKA-20858) | Refactor SubscriptionState to give cleaner separation for share groups | 2026-10-20 Fixed | Resolved / Fixed |
| [KAFKA-21058](https://issues.apache.org/jira/browse/KAFKA-21058) | Remove the dead code from jsonNodeToInt and jsonNodeToLong | 2026-10-21 Fixed | Resolved / Fixed |
| [KAFKA-21074](https://issues.apache.org/jira/browse/KAFKA-21074) | Add lightweight, client-agnostic Kafka wire-protocol fault-injection proxy for integration tests | 2026-10-23 Fixed | Resolved / Fixed |
| [KAFKA-21225](https://issues.apache.org/jira/browse/KAFKA-21225) | Add mirror exceptions | 2026-10-23 Done | Resolved / Done |
| [KAFKA-21226](https://issues.apache.org/jira/browse/KAFKA-21226) | Add Admin client types | 2026-10-19 Later | Resolved / Later |
| [KAFKA-21255](https://issues.apache.org/jira/browse/KAFKA-21255) | Streams heartbeat retry responses can omit assignments after response loss | 2026-10-19 Fixed；后重开 | Reopened / 未解决 |
| [KAFKA-21257](https://issues.apache.org/jira/browse/KAFKA-21257) | Document tokenless OAUTHBEARER login for validate-only brokers | 2026-10-18 Fixed | Resolved / Fixed |
| [KAFKA-21258](https://issues.apache.org/jira/browse/KAFKA-21258) | Move the Docker image usage guide from docker/examples/README.md to the website docs | 2026-10-20 Fixed | Resolved / Fixed |
| [KAFKA-21280](https://issues.apache.org/jira/browse/KAFKA-21280) | SslTransportLayer.transferFrom sends stale buffer contents after a failed file read | 2026-10-20 Fixed | Resolved / Fixed |
| [KAFKA-21288](https://issues.apache.org/jira/browse/KAFKA-21288) | Add MirrorPartitionState | 2026-10-20 Fixed | Resolved / Fixed |
| [KAFKA-21293](https://issues.apache.org/jira/browse/KAFKA-21293) | SubscriptionState#unsubscribe should not reset the rebalance listener | 2026-10-19 Fixed | Resolved / Fixed |
| [KAFKA-21294](https://issues.apache.org/jira/browse/KAFKA-21294) | The example of "Configuring Production Kafka Brokers" does not work since the login callback is missing | 2026-10-22 Fixed | Resolved / Fixed |
| [KAFKA-21299](https://issues.apache.org/jira/browse/KAFKA-21299) | Upgrade Gradle to 9.8.2 (security fix) and fetch the wrapper jar from a pinned commit | 2026-10-22 Fixed | Resolved / Fixed |
| [KAFKA-21301](https://issues.apache.org/jira/browse/KAFKA-21301) | Streams Group Assignment delays temporarily stop processing existing Streams tasks | 新增 2026-10-17 | Open / 未解决 |
| [KAFKA-21302](https://issues.apache.org/jira/browse/KAFKA-21302) | Streams group joins rejected due to copartition topic ordering differences | 新增 2026-10-18 | Patch Available / 未解决 |
| [KAFKA-21303](https://issues.apache.org/jira/browse/KAFKA-21303) | Incorrect session timeout applied to classic members when reloading a consumer group | 新增 2026-10-18；2026-10-22 Fixed | Resolved / Fixed |
| [KAFKA-21304](https://issues.apache.org/jira/browse/KAFKA-21304) | Add mirror.state.topic.min.isr and related configs | 新增 2026-10-19 | Open / 未解决 |
| [KAFKA-21305](https://issues.apache.org/jira/browse/KAFKA-21305) | Bump Jackson version to 2.22.4 | 新增 2026-10-19；2026-10-21 Fixed | Resolved / Fixed |
| [KAFKA-21306](https://issues.apache.org/jira/browse/KAFKA-21306) | Streams group: a static member that rejoins from a new process can put a task on that process twice | 新增 2026-10-19 | Open / 未解决 |
| [KAFKA-21307](https://issues.apache.org/jira/browse/KAFKA-21307) | Update ShareConsumeBenchSpec with addition params to support share group  DLQ | 新增 2026-10-19；2026-10-20 Fixed | Resolved / Fixed |
| [KAFKA-21308](https://issues.apache.org/jira/browse/KAFKA-21308) | StickyTaskAssignor: a full previous member hides other previous members that have room | 新增 2026-10-19 | Open / 未解决 |
| [KAFKA-21309](https://issues.apache.org/jira/browse/KAFKA-21309) | Consumer using SubscriptionPattern throws IllegalStateException on Metadata response for a deleted assigned topic" | 新增 2026-10-19 | Open / 未解决 |
| [KAFKA-21310](https://issues.apache.org/jira/browse/KAFKA-21310) | Add sugar method "join" to KafkaFuture | 新增 2026-10-19 | Open / 未解决 |
| [KAFKA-21311](https://issues.apache.org/jira/browse/KAFKA-21311) | Throw when uncompressed records need more buffer space | 新增 2026-10-19 | Open / 未解决 |
| [KAFKA-21312](https://issues.apache.org/jira/browse/KAFKA-21312) | Snapshottable tasks in the coordinator runtime | 新增 2026-10-20 | Open / 未解决 |
| [KAFKA-21313](https://issues.apache.org/jira/browse/KAFKA-21313) | Share partition acquire fails with "Existing acquisition lock timeout exists" after a log start offset move splits a batch with a pending release | 新增 2026-10-20 | Open / 未解决 |
| [KAFKA-21314](https://issues.apache.org/jira/browse/KAFKA-21314) | Share partition acquire throws "inconsistent range" at the in-flight limit on a compacted topic | 新增 2026-10-20 | Open / 未解决 |
| [KAFKA-21315](https://issues.apache.org/jira/browse/KAFKA-21315) | Share partition stops delivering records after an acknowledgement is rolled back below a moved start offset | 新增 2026-10-20 | Open / 未解决 |
| [KAFKA-21316](https://issues.apache.org/jira/browse/KAFKA-21316) | Removed entries in PartitionStates stay chained and slow down young GC on follower brokers | 新增 2026-10-20 | Open / 未解决 |
| [KAFKA-21317](https://issues.apache.org/jira/browse/KAFKA-21317) | Timestamp lookup can miss valid offsets after the log start offset advances | 新增 2026-10-20 | Open / 未解决 |
| [KAFKA-21318](https://issues.apache.org/jira/browse/KAFKA-21318) | invertedTargetAssignment invalid for share groups | 新增 2026-10-20；2026-10-23 Fixed | Resolved / Fixed |
| [KAFKA-21319](https://issues.apache.org/jira/browse/KAFKA-21319) | Share partition read_committed acquire throws "Batch record not found" when the start offset is inside an aborted transaction batch | 新增 2026-10-20 | Open / 未解决 |
| [KAFKA-21320](https://issues.apache.org/jira/browse/KAFKA-21320) | Sort copartition groups and indexes on the Streams client side | 新增 2026-10-20 | Open / 未解决 |
| [KAFKA-21321](https://issues.apache.org/jira/browse/KAFKA-21321) | Streams group: the assignment refiner does not see a member that joins in the same heartbeat | 新增 2026-10-20 | In Progress / 未解决 |
| [KAFKA-21322](https://issues.apache.org/jira/browse/KAFKA-21322) | LogConfig cleanup | 新增 2026-10-20 | Open / 未解决 |
| [KAFKA-21323](https://issues.apache.org/jira/browse/KAFKA-21323) | Remove deprecated java.util.regex fallback for client-metrics match patterns (KIP-714) | 新增 2026-10-21 | Open / 未解决 |
| [KAFKA-21324](https://issues.apache.org/jira/browse/KAFKA-21324) | Wrong parameter order in private ctor of WindowKeyQuery | 新增 2026-10-21 | Patch Available / 未解决 |
| [KAFKA-21325](https://issues.apache.org/jira/browse/KAFKA-21325) | Enable asynchronous bootstrap DNS resolution by default | 新增 2026-10-21 | In Progress / 未解决 |
| [KAFKA-21326](https://issues.apache.org/jira/browse/KAFKA-21326) | Enable Gradle configuration cache | 新增 2026-10-21 | Open / 未解决 |
| [KAFKA-21327](https://issues.apache.org/jira/browse/KAFKA-21327) | Replace JGit calls in build.gradle with the git CLI via providers.exec | 新增 2026-10-21 | In Progress / 未解决 |
| [KAFKA-21328](https://issues.apache.org/jira/browse/KAFKA-21328) | Add CI check for stale version references in docs/ | 新增 2026-10-21 | In Progress / 未解决 |
| [KAFKA-21329](https://issues.apache.org/jira/browse/KAFKA-21329) | Update outdated steps in SSL docs | 新增 2026-10-21 | Patch Available / 未解决 |
| [KAFKA-21330](https://issues.apache.org/jira/browse/KAFKA-21330) | Extract the dedicated test cases for DynamicLogConfig from DynamicBrokerConfigTest | 新增 2026-10-21 | Open / 未解决 |
| [KAFKA-21331](https://issues.apache.org/jira/browse/KAFKA-21331) | doc fix about the tested OS | 新增 2026-10-22 | Open / 未解决 |
| [KAFKA-21332](https://issues.apache.org/jira/browse/KAFKA-21332) | Clarify UpdateFeatures.max_version_level deletion semantics | 新增 2026-10-22 | Open / 未解决 |
| [KAFKA-21333](https://issues.apache.org/jira/browse/KAFKA-21333) | Test async bootstrap DNS resolution recovering after transient failure | 新增 2026-10-22 | Open / 未解决 |
| [KAFKA-21334](https://issues.apache.org/jira/browse/KAFKA-21334) | Test close() while async bootstrap DNS resolution is still pending | 新增 2026-10-22 | Open / 未解决 |
| [KAFKA-21335](https://issues.apache.org/jira/browse/KAFKA-21335) | Improve wrapper.gradle to look up the wrapper URL automatically | 新增 2026-10-22 | Open / 未解决 |
| [KAFKA-21336](https://issues.apache.org/jira/browse/KAFKA-21336) | Improve git.py to generate an accurate contributor list | 新增 2026-10-22 | Open / 未解决 |
| [KAFKA-21337](https://issues.apache.org/jira/browse/KAFKA-21337) | Integration test for async bootstrap resolution recovers after initial DNS failure | 新增 2026-10-22 | Open / 未解决 |
| [KAFKA-21338](https://issues.apache.org/jira/browse/KAFKA-21338) | Use exponential backoff with jitter for internal topic retries in InternalTopicManager | 新增 2026-10-22 | Open / 未解决 |
| [KAFKA-21339](https://issues.apache.org/jira/browse/KAFKA-21339) | Integration test for async bootstrap resolution succeeds with partially resolvable bootstrap servers | 新增 2026-10-23 | Open / 未解决 |
| [KAFKA-21340](https://issues.apache.org/jira/browse/KAFKA-21340) | Integration test when close during in-flight async bootstrap resolution shuts down cleanly | 新增 2026-10-23 | Open / 未解决 |
| [KAFKA-21341](https://issues.apache.org/jira/browse/KAFKA-21341) | SslTransportLayer does not report a disconnect when the peer sends close_notify without a TCP FIN | 新增 2026-10-23 | Open / 未解决 |
| [KAFKA-21342](https://issues.apache.org/jira/browse/KAFKA-21342) | Connection failure after successful DNS resolution must not throw BootstrapResolutionException | 新增 2026-10-23 | Open / 未解决 |
| [KAFKA-21343](https://issues.apache.org/jira/browse/KAFKA-21343) | Route bootstrap DNS resolution through the injectable HostResolver | 新增 2026-10-23 | Open / 未解决 |
| [KAFKA-21344](https://issues.apache.org/jira/browse/KAFKA-21344) | Handle partition rotate for share fetches in session | 新增 2026-10-23 | Open / 未解决 |
| [KAFKA-21345](https://issues.apache.org/jira/browse/KAFKA-21345) | Add client metrics for OAuth token endpoint requests | 新增 2026-10-23 | Open / 未解决 |
| [KAFKA-21346](https://issues.apache.org/jira/browse/KAFKA-21346) | Adding throttle metrics to the admin client | 新增 2026-10-23 | Open / 未解决 |
| [KAFKA-21347](https://issues.apache.org/jira/browse/KAFKA-21347) | Add release.py blog subcommand to generate initial blog post | 新增 2026-10-23 | Open / 未解决 |
| [KAFKA-21348](https://issues.apache.org/jira/browse/KAFKA-21348) | Smoke-test async bootstrap resolution across all client types | 新增 2026-10-23 | Open / 未解决 |
| [KAFKA-21349](https://issues.apache.org/jira/browse/KAFKA-21349) | Transaction coordinator loads uncommitted records from __transaction_state and can act on state that is later truncated | 新增 2026-10-23 | Open / 未解决 |
| [KAFKA-21350](https://issues.apache.org/jira/browse/KAFKA-21350) | Per-call record limit for Consumer poll | 新增 2026-10-23 | Open / 未解决 |
| [KAFKA-21351](https://issues.apache.org/jira/browse/KAFKA-21351) | Split KafkaConsumerTest | 新增 2026-10-23 | Open / 未解决 |
| [KAFKA-21352](https://issues.apache.org/jira/browse/KAFKA-21352) | Deprecate KafkaCSVMetricsReporter, KafkaMetricsReporterMBean, KafkaMetricsReporter and VerifiableProperties | 新增 2026-10-24 | Open / 未解决 |
| [KAFKA-21353](https://issues.apache.org/jira/browse/KAFKA-21353) | The incorrect parameter in internal-api-checker.md breaks the site build | 新增 2026-10-24 | Open / 未解决 |

机制主题：逻辑读取边界与物理文件边界。
