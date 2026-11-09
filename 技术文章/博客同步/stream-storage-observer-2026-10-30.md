---
type: survey
title: 第 4 期：提交边界、协议写入与恢复前缀
sources:
- https://github.com/apache/kafka/pull/23943
- https://github.com/apache/fluss/pull/4286
- https://github.com/AutoMQ/automq/pull/3700
tags:
- 流存储
- 社区观察
created: '2026-11-09'
updated: '2026-11-09'
status: draft
publication_status: github_archive
source_checked: '2026-10-30'
related:
- '[[知识库/sources/web/stream-storage-observer-20261030/README]]'
publication_scope: 仅 GitHub 正文归档；GitHub Pages、知识卡及双库同步暂缓。
report_date: '2026-10-30'
source_check_scope: 原报告公开 PR、讨论、提案和发行资料，核读范围与限制见正文；本次归档未重新更新技术状态。
---

# 流存储技术观察 · 2026-10-30

## 第 4 期：提交边界、协议写入与恢复前缀

> 归档范围：本页保存 2026-10-30 报告正文及公开引用，供 GitHub 阅读。GitHub Pages 页面、知识卡与双库同步暂缓；所在目录不表示博客同步已完成。技术状态和原文中的历史交付说明按原观察窗口保留，不代表归档日的最新进展。本次归档未重新核验全部外部链接。

[公开来源索引](../../知识库/sources/web/stream-storage-observer-20261030/README.md)

观察区间：2026 年 10 月 23 日 12:00 至 10 月 30 日 12:00 UTC，即北京时间 10 月 23 日 20:00 至 10 月 30 日 20:00。下文事件日期使用 UTC；检索在本次执行期间完成，12:00 之后的事件不计入本期。

本周值得关注的共同问题是：**系统什么时候才有资格推进下一步**。Kafka 的事务协调器不能因为本地日志存在就执行尚未提交的事务状态；Fluss 的 Kafka 兼容实现已经从握手走到真实写入，但认证、内存回收和过载控制仍必须逐条验证；AutoMQ 则修正把请求响应当作底层写入完成的 epoch 竞态，并明确恢复失败后保留哪个全局前缀。

这些变化不能只用“功能已支持”来概括。Kafka 的新补丁大多只是进入 trunk；Fluss 本周新增能力不属于此前发布的 1.0.0；AutoMQ 的 1.7.5-rc2 有候选版发行证据，仍不能改称正式稳定版。本期沿着具体失败路径解释方案和代价，并把实际合并代码、仍在评审的设计与作者测试分别标明。

| 项目 | 本周核心进展 | 截止时必须保留的边界 |
|---|---|---|
| Kafka | 事务状态加载等待提交边界；Streams 内存背压推进；异步任务批次归属继续评审 | trunk 合并不等于发布包已含；性能提案仍有未完成部分 |
| Fluss | Kafka Produce、JSON/rescue、SASL/PLAIN 和稳定 MetadataView 合并；内部 RPC 独立调度 | 无 Kafka TLS、事务、幂等和消费者完整兼容承诺；过载接线仍有 open PR |
| AutoMQ | append 完成与 epoch 推进重新绑定；恢复按全局 WAL 前缀截断；Archive 游标修复 | 有损恢复不是零丢失；新 failover 停滞仍未闭环；rc2 不是稳定版 |

上期 10 月 23 日稿件已文件交付但尚未上线，本期以该稿件的观察截点去重。可访问的专题历史文章仍为 [10 月 16 日期](https://bryantchang1992.github.io/ai_memory_chang_ai_team/stream-storage-observer/2026-10-16/)。全文不把旧提案的背景重新计作本周新增，也不以“关闭 PR”代替“已合并”。

## Kafka：提交边界与背压不能只看成功路径

### 1. 事务协调器不能先相信日志尾部，异步任务也不能认错自己的批次

上期的问题是旧 coordinator 不能只凭缓存把路由错误判成致命事务错误；本期更底层的一处修复则要求新 coordinator 在行动之前，先证明它加载的事务状态不会被正常选主截断。10 月 27 日合并的 [#23943](https://github.com/apache/kafka/pull/23943) 指出，新 leader 原来读取 `__transaction_state` 到 log end offset，但其中可能包含尚未进入 high watermark 的记录。若据此向部分数据分区发送 COMMIT marker，随后领导权再次转移，下一任 leader 看不到那条 PREPARE_COMMIT，便可能超时 abort；同一事务因此可能在不同分区得到相反结果。补丁针对的是即使 clean election 也存在的窗口，不是用来修补 unclean election 已丢失的已提交记录。

简单地只读当前 HW 也不够：刚选出的 leader 的 HW 可能暂时落后，直接加载会漏掉实际已提交状态。方案因此把加载开始时的 LEO 当作固定目标，等 HW 追上再加载。加载期间请求得到 `COORDINATOR_LOAD_IN_PROGRESS`，协调器不应追加新事务记录；通常付出一次 follower fetch 往返的等待，若 ISR 中有失联副本，则可能等到其按 `replica.lag.time.max.ms` 被移除。代价是恢复稍慢，收益是把发送 marker 之前的状态可信边界讲清楚。[完整方案与测试](https://github.com/apache/kafka/pull/23943)；[HW 推进机制的评审答复](https://github.com/apache/kafka/pull/23943#discussion_r4391867753)

实现上两个容易被忽略的细节决定这个等待是否可靠：注册 PartitionListener 后再检查一次 HW，避免错过注册间隙的推进；加载中的分区跳过过期 transactional ID 清理，避免上一 epoch 尚存的缓存产生 tombstone，把本应固定的 LEO 又向前推。分区变 follower、下线或删除时放弃等待；回调需要调度出去，因为 listener 触发时持有 partition lock。这是本周已合入 trunk 的修复，不代表已进入本周发布的版本。[评审对过期清理旁路的确认](https://github.com/apache/kafka/pull/23943#discussion_r4393659779)

另一方面，上期仍开放的 [#23923](https://github.com/apache/kafka/pull/23923) 本周暴露了“延迟任务直到 batch written”方案的更深限制：操作在生成 records 时已经登记 task，随后 append 因新 records 放不下而先 flush 旧 batch，旧 batch 的成功回调是否会过早提交这个属于新操作的 task？10 月 25 日作者确认这是 KAFKA-20912 的一部分，直接修改 timeline structure 的非 replay 操作也受影响；候选修法包括取消这种大批次触发的先行 flush，或每次 append 后创建 snapshot，尚未决定。[反例](https://github.com/apache/kafka/pull/23923#discussion_r4369998732)；[作者确认](https://github.com/apache/kafka/pull/23923#discussion_r4371941197)

因此本周不能把上期草案写成已经保证副作用与状态一致。`batch written` 不是 HW，且先要证明 task 归属的是哪一批。timer 的 [#23913](https://github.com/apache/kafka/pull/23913) 也仍是 draft：作者提出把立即 timer 与依赖写入成功的可回滚 timer 分开，评审则倾向让原有失败补偿随统一回滚消失，并接受写失败时撤销一次 session 延长，以减少接口复杂度；这仍是设计取舍，不是最终契约。[10 月 25 日语义分类](https://github.com/apache/kafka/pull/23913#discussion_r4369854996)；[10 月 26 日回复](https://github.com/apache/kafka/pull/23913#discussion_r4378971691)

### 2. Streams：内存上限不只是“提前 commit”，还必须关住所有继续写入的路径

事务 state store 把未提交写入保留在 RocksDB native WriteBatch 中，这部分不受普通 block cache / write buffer 上限约束。原先达到 `statestore.uncommitted.max.bytes` 就请求提前 commit，但长时间 rebalance 可以跳过 commit，处理循环却继续写，所谓上限便失去约束。10 月 27 日合并的 [#23728](https://github.com/apache/kafka/pull/23728) 改为超限且提交未能消退压力时暂停处理与 punctuator；仍继续 poll 和尝试 commit，让 rebalance 能结束，成功提交或 revoke flush 后恢复。它明确牺牲长 rebalance 时的吞吐，而不是让 native memory 无界增长。

评审中又发现背压本身会制造永久停顿。第一种是 `Processor.init()` 已写入超限数据，task 却尚未 commit-eligible；暂停的恰好是原本会把它推进到可提交状态的处理路径。作者在 topology 初始化后发现事务缓冲非空时立即设置 `commitNeeded`。第二种是极小合法上限低于空 WriteBatch 的固定头部大小：即使 commit 成功，空缓冲仍“超限”，永远无法恢复。最终计量只在 WriteBatch 真正包含 records 后计算其大小，同时避免空初始化被误判为需要提交。这里的教训不是再加一个 if，而是背压要证明“有一条不依赖被暂停工作、并能把计量降到阈值下的排空路径”。[初始化死锁及修复](https://github.com/apache/kafka/pull/23728#discussion_r4381118264)；[空批次基线修复](https://github.com/apache/kafka/pull/23728#discussion_r4386743512)

10 月 29 日合并的 [#23984](https://github.com/apache/kafka/pull/23984) 随后覆盖独立 processing threads：只暂停 StreamThread 主循环不能阻止 executor 继续处理和 punctuate。补丁把每个 StreamThread 的 pause 标志传入调度层，停止分派新 task，也让正在执行的 task 停止推进并按既有路径释放；恢复时唤醒 executor。不能把标志放进所有 StreamThread 共享的 `TaskExecutionMetadata`。评审还补了 group-not-ready 的提前返回路径，否则 `ASSIGNMENT_DELAYED` 等状态回复留下 active tasks 时，executor 仍可越过字节检查。[提前返回漏洞](https://github.com/apache/kafka/pull/23984#discussion_r4393758443)

这两项已经合入 trunk，维护者分别报告回补到 4.4 分支，但不等于已经随 4.4.0 发布。下一步开放中的 [#23999](https://github.com/apache/kafka/pull/23999) 要减少正常运行的重复占用：先只在 heap 暂存写入，commit 时再在写锁之外构建 native WriteBatch、锁内 flush。重复更新同一个 key 的计量扣除旧条目，避免把历史累计写入当成仍驻留数据。代价是 commit 时仍要临时出现 native copy，因此阈值判断预留“全部未提交字节加最大 store 未提交字节”；stores 逐个提交，使额外峰值按最大 store 而非全部 stores 相加。作者的 JMH 模型中覆盖写入收益显著，但无覆盖、1000 字节 value 的 commit 最坏慢约 28%；这是模型报告，不是 Kafka 总吞吐结论。该 PR 截止仍未合并，也尚无评审意见。

### 3. Share-group DLQ：既要隔离慢工作，也必须承认持久化失败时的交付取舍

10 月 28 日合并的 [#23964](https://github.com/apache/kafka/pull/23964) 处理 DLQ 对 share-group 控制面的拖累：persister 线程不仅完成所有 share partitions 的写响应，还同步读取待复制到死信队列的源 records；每次请求重建 LogConfig，并扫描超出目标 offset 的文件批次，又叠加不必要的 CPU 与磁盘工作。补丁直接读取需要的配置键，把源读取搬至独立 fetch executor，且对 V2 batch 按 baseOffset 提前排除不相关批次。

这不是“异步化后问题消失”。评审追问 executor 的所属组件、线程数、ReplicaManager 依赖和停机顺序，尤其指出直接 `shutdownNow()` 会把已排队未执行任务遗弃，使其 futures 永远不完成；作者改用 shutdown 加 awaitTermination。最终实现由 DLQ manager 持有线程池，internal thread-count 默认 2。这里不是无限等待排空：超时后未完成读取留在 daemon thread，不阻塞停机；也刻意避免中断 FileChannel 操作，以免关闭其他用户仍共享的 segment channel。独立执行资源的价值在于缩小 persister 的阻塞面，但生命周期结束时仍必须明确取舍。[关闭队列任务的评审](https://github.com/apache/kafka/pull/23964#discussion_r4393140595)；[作者选择](https://github.com/apache/kafka/pull/23964#discussion_r4394006763)

本周另一项 [#23995](https://github.com/apache/kafka/pull/23995) 则说明 DLQ 不是所有失败路径的无条件保证。作者发现，在状态持久化失败、acquisition lock 已过期且 delivery count 达到限制时，回滚路径直接进入 ARCHIVED，而不是正常 DLQ 流程的 ARCHIVING，于是提议修成后者。维护者解释，这个差异是刻意保留的：persister 已经经过五次指数退避重试仍失败，转 ARCHIVING 的第一步仍需写同一 partition key、很可能还是同一故障 broker；执意再走 DLQ 会把 in-flight 队列卡住。[维护者解释](https://github.com/apache/kafka/pull/23995#issuecomment-6477981433)

作者在 10 月 29 日接受解释并关闭 PR，表示可另做这一路径的 metric/log，未提交新的状态迁移保证。这是本周应该呈现的结论：此处选择的是故障时队列能继续前进，而不是保证每条达到次数上限的记录都进入 DLQ；可观测性仍是待办方向。不能只读 PR 开头，就把“绕过 DLQ”写成已经合入的修复。[关闭说明](https://github.com/apache/kafka/pull/23995#issuecomment-6486791868)

### 简讯与上期闭环

- **本地留存时间的锚点。** 本周发起讨论的 [KIP-1385](https://cwiki.apache.org/confluence/spaces/KAFKA/pages/451979130/KIP-1385+Measure+local.retention.ms+from+remote+upload+time+instead+of+record+timestamps) 拟改从远端上传完成计 `local.retention.ms`，避免旧时间戳回填刚上传就删本地、未来时间戳又阻塞删除。复用 COPY_SEGMENT_FINISHED 的既有 eventTimestamp，要求插件准确返回完成时间；重启后未读到前先不按本地时间删除。代价是回填占盘可能增加；全局 retention 和字节限制仍有效，不能承诺绝对本地保留窗口。缺少元数据时回退记录时间并告警。截止仍 Under Discussion，未确认实现/投票；原始讨论邮件抓取失败，勿称已有共识。
- **TLS 已知文件错误不再重读分类。** 上期开放的 [#23928](https://github.com/apache/kafka/pull/23928) 于 10 月 28 日 16:54:50 合并。新增的本周设计变化是取消独立 scheduler 上报/限流路径，已知 FileReadException 直接 inline 报告，日志目录仅首次下线时记录 ERROR；PLAINTEXT 不确定错误仍重读，ClosedChannelException 不算介质故障，KRaft snapshots 仍未覆盖。[简化建议](https://github.com/apache/kafka/pull/23928#discussion_r4364794578)；[采纳](https://github.com/apache/kafka/pull/23928#discussion_r4368128930)
- **uniform2 总装合并而非默认启用。** [#23723](https://github.com/apache/kafka/pull/23723) 于 10 月 28 日合并；仍未注册 built-in，仍无 rack awareness。不能把该合并写成用户已能直接启用完整替代方案。
- **EOS offset-reset 仍在修复评审。** 本周 [#24002](https://github.com/apache/kafka/pull/24002) 处理 commit timeout 后 revived task 尚未初始化就被 assignment 关闭，pending reset 丢失的路径；跨 task replacement 保留 reset，只交给当前仍由 consumer 持有的输入分区。它与上期 [#23848](https://github.com/apache/kafka/pull/23848) 的部分 revoke/abort 场景相近但不相同，两者均仍 open。不能因系统测试报告通过或自动 review 推荐批准而称修复已发布。
- **发布与安全。** 本周核实了 [4.4.0 正式发布公告](https://kafka.apache.org/blog/2026/10/22/apache-kafka-4.4.0-release-announcement/)，官网标注的发布日期是 10 月 22 日，因此不是本期窗口内的新发行；[4.3.2 官方博客](https://kafka.apache.org/blog/2026/10/23/apache-kafka-4.3.2-release-announcement/) 与下载页标注 10 月 23 日，dev 索引正式邮件为 10 月 27 日。应写“本周核实发布闭环/公告补齐”，勿把邮件日期当二进制首次发布日。10 月 28 日官方集中披露协议分配、解压、认证、Connect 等安全问题，各自修复版本不同，例如 issuer/audience 默认校验条目仍覆盖到 4.3.2，而非一句“4.3.2 已修所有 CVE”。[官方安全列表](https://kafka.apache.org/community/cve-list/)；3.9 分支的数组/tagged-field 资源限制回补 [#24018](https://github.com/apache/kafka/pull/24018) 已于 10 月 30 日 07:05:22 合并，但这不是 3.9.3 已发布的证据。

## Fluss：写入链路接通之后，资源与指标仍要重新界定

### 1. Kafka 从“表可发现”走到可认证、可转换的实际写入；生产语义仍有边界

上期截点只有 ApiVersions 与 Metadata 进入生产入口，本周不再只是协议骨架：[Produce handler #4284](https://github.com/apache/fluss/pull/4284) 10 月 24 日合并，[native append #4286](https://github.com/apache/fluss/pull/4286) 10 月 25 日接通非幂等 Produce v3–v11，随后同一天合并 [SASL/PLAIN #4861](https://github.com/apache/fluss/pull/4861) 和 [JSON/rescue #4682](https://github.com/apache/fluss/pull/4682)。这一批已经能把标准 Kafka producer 的请求写进预建 Fluss Arrow log table，再由 native Fluss readback 验证；不是仍待落地的目标合同。但它仍是 DDL-first：无主键、非分区表、显式 table.kafka.enabled=true，不提供自动建表、CreateTopics/DeleteTopics。consumer/Fetch、幂等与事务仍在范围之外，[总任务 #4185](https://github.com/apache/fluss/issues/4185) 仍 open。

真正的工程变化是把协议、schema 与原生存储寿命接起来。#4286 让 metadata 查询、分区转换和本地 append 提交留在已有 RPC worker，ack 异步完成；借用的输入在同步处理阶段消费，pooled Arrow 输出在本地 append 返回时即可回收，不必一直保留到复制 ack。partition 错误隔离、别名、null/empty value、native offset/ack 映射都有集成测试。生产模块共用 conversion memory，shutdown 要等 worker 停止再释放资源。测试证明了特定回归场景，不是完整客户端版本矩阵或吞吐基准。[native append 实现与验证边界](https://github.com/apache/fluss/pull/4286)；[21 个生命周期/并发测试场景 #4299](https://github.com/apache/fluss/pull/4299)。

JSON/rescue 则把“宽容 schema”变成实际读写行为：声明 _kafka_rescue STRING 后，未知字段及不可转换值递归进入 rescue，相应 nullable 值置 null，合法兄弟字段保留，支持 ROW/ARRAY/MAP。没有 rescue 时转换错误返回 INVALID_RECORD；拒绝的 partition batch 不追加部分前缀。nested 的业务字段允许叫 _kafka_key，它与外层系统 key 是不同位置，不能套用 flat 的系统名冲突规则。[评审纠正布局边界](https://github.com/apache/fluss/pull/4682#discussion_r4370905032)。

这次设计刻意先保留 Jackson readTree 中间树，把 coercion/rescue 放在 converters 中，decoder 随 write plan 缓存并并发复用；不是已经完成 streaming JSON。普通 decimal 精度由 BigDecimal 保持，但 signed zero 被归一化、极端 exponent 可能拒绝或丢失数值保真，rescue 也不保证原 token 文本。后续 [#4906](https://github.com/apache/fluss/pull/4906) 才提出 schema-compiled streaming converter，截止仍 open。作者 JMH 数字不能写成现有 main 的收益。[简化树路径的评审](https://github.com/apache/fluss/pull/4682#discussion_r4371036796)。

还有一处必须按最终代码纠正：PR 正文仍说 unpaired Unicode escapes fatal；最后批准评审明确移除了全树 Unicode 扫描，严格 UTF-8 字节检查仍保留，但未配对 surrogate escape 遵从 Jackson 和 Fluss 默认字符串编码。不得把 PR 正文旧说法当最终保证。[批准说明](https://github.com/apache/fluss/pull/4682#pullrequestreview-5644162544)；[合并提交 decoder](https://github.com/apache/fluss/blob/0e4fce7c916bf3edde99de8533de535a2faca8ed/fluss-kafka/src/main/java/org/apache/fluss/kafka/format/json/JsonKafkaFieldDecoder.java)。

SASL 合并的意义在于身份贯穿：每连接认证状态、SaslHandshake v0–v1 / SaslAuthenticate v0–v2、认证前请求 gate，再把 principal 送到 backend session 与 native append UserContext，用 Fluss ACL 授权，而非“只校验一个密码”。但这是 SASL_PLAINTEXT，**不加密凭据或数据**；Kafka TLS、SCRAM、重新认证不在本次实现，动态凭据变更只影响新认证，已建立连接保留原身份。不能从上期 native server TLS 推出 Kafka listener 已有 TLS。[固定版安全说明](https://github.com/apache/fluss/blob/f96bc2fa9268be7eacb3ce1f119d380086c4955b/website/docs/kafka-compatibility.md)。

上期 #4807 指出的 Metadata ZK 扫描和全请求失败也在本周闭环：[10 月 26 日 #4825](https://github.com/apache/fluss/pull/4825) 将每表 Kafka-enabled 布尔值与 routing 在同一 metadata lock 下捕获为稳定 MetadataView，修改 bucket map 时复制，防止旧 view 跟着变化；cache-aside ZK 回填须防 concurrent ALTER/DROP 的旧值复活。发现不再每次枚举 ZK/逐表重读 schema，坏 topic 不应拖垮健康 topic 和 broker 信息。但这仍沿用异步 metadata propagation，是一致的本地视图，不是跨集群线性一致目录，也不是“系统不再访问 ZooKeeper”。[MetadataView 固定提交](https://github.com/apache/fluss/blob/c07dcc6072255d04e4003062041664a422c6260e/fluss-server/src/main/java/org/apache/fluss/server/metadata/MetadataView.java)。

最后，ack 被尊重不等于 exactly-once。当前要求 enable.idempotence=false；重试可能重复，多个 in-flight request 下重试可能改变分区内顺序。说明这些边界的 [文档 PR #4899](https://github.com/apache/fluss/pull/4899) 仍 open。不要复述其“retries=0 就没有重复”的宽泛口号——更准确说法是停止自动重试消除了这一自动重试来源，但会在暂态失败下放弃重试，不能保证业务端没有重放。新能力已经可写，但 bounded admission、消费者协议和更强交付语义仍未闭合。

### 2. 复制不应为慢客户端买单：独立 listener 终于成为独立 RPC 调度域

此前单独配置 internal listener 并不等于资源隔离：它与客户端仍共享 Netty network threads、request processors、queue/backpressure。慢外部请求占住 worker、队列进入背压时，replication 连接也可能一起停读，进而拖慢 high watermark 与 acks=all。**10 月 30 日 06:59 UTC 合并的 [#4857](https://github.com/apache/fluss/pull/4857)** 按既有 listener 拓扑自动分组：有独立 internal 且也有 external 时建两套 network/worker/queue 资源；所有 external 共用一组；单端点或只有一类 listener 仍为一组，不增加隔离开关。

代价不是免费的：三个 Netty capacity 配置现在是 **每资源组**，默认 3 network + 8 worker 在双组部署变为合计 6 + 16。评审特别指出默认 Helm INTERNAL/CLIENT 拓扑升级也会遇到这一变化，作者补齐配置描述。max-queued-requests=500 是分配到 worker 的背压阈值，不是硬队列上限，队列仍无界。[容量评审与落实](https://github.com/apache/fluss/pull/4857#issuecomment-6515024959)；[固定提交配置文档](https://github.com/apache/fluss/blob/7392085a98ea632ac06ea71d36938c968dddc68f/website/docs/maintenance/configuration.md#netty)。

资源拆分也提出 shutdown 所有权问题：两个组共享 handler，不能一个 worker pool 退出就关闭 handler，另一个还在用。最终由 NettyServer 统一持有，等两个组都停止后只 close 一次，重复 closeAsync 返回同一 future；加入阻塞两组请求、分别释放的测试。[问题](https://github.com/apache/fluss/pull/4857#issuecomment-6471840043)；[修复回应](https://github.com/apache/fluss/pull/4857#issuecomment-6493226725)。现有 request histogram 仍共享，外部 processor 索引保持，内部追加，总 queue gauge 汇总两组；这不是通过改变指标口径伪造隔离效果。

未解决边界很实在：隔离的是 RPC 排队/网络执行，不是 CPU、磁盘、业务锁或异步 executor 的物理隔离。Kafka 的流控接线也还没闭环：[open #4897](https://github.com/apache/fluss/pull/4897) 指出 KafkaCommandDecoder 未登记 RequestChannel，现有 pause/resume 看不到这些连接，过载时排队 Produce 会继续保留大 buffer；[open #4898](https://github.com/apache/fluss/pull/4898) 则处理新连接在背压已激活时未立即暂停的漏洞。两项截至截点均未合并，且即使合并也不等同字节级有界 admission。不要将 #4857 写成“Kafka 已获得完整过载保护”。

与此呼应，[10 月 26 日 #3412](https://github.com/apache/fluss/pull/3412) 在 append 释放 replica lock 且登记 delayed write 后，立即检查成功 bucket 的 delayed fetch，使等待旧 log end 的 follower 及时收到新增记录；consumer fetch 仍必须等 high watermark。每 bucket 的 completion exception 被隔离，不能反向破坏已经登记的 Produce 或其他 bucket。它修的是复制推进时机，不改变 ack 的持久性等级。

### 3. RocksDB 共享统计节约固定内存，但告警含义必须随之迁移；读错误修复又被回滚

**10 月 30 日 10:29 UTC 的 [#4948](https://github.com/apache/fluss/pull/4948)** 把每 bucket 一个 native RocksDB Statistics 改为同一 TabletServer 内按 table ID 共享。背景不是 block-cache 容量，而是 Statistics 的 CPU-local ticker/histogram 数组本身在大量 bucket/partition 下重复占用 native memory；大小受 CPU 数与 RocksDB build 影响，不能给出未经测试的通用节省百分比。

机制是 ref-counted lease：打开/恢复 DB 取得引用，失败打开也归还，最后一个 DB 关闭之后才释放 native Statistics。采集共享统计时按 identity 去重，并在选中 DB 的 resource lease 内读；只有成功采集才标记 collected，这样被选中 DB 恰好关闭时可由其他活 DB 补采。DB property 与 memory 仍逐实例汇总。关闭某个 bucket 不会抹去它在共享统计中的历史样本，只要还有同表实例活着；最后关闭后再开才得到新统计。[registry 实现](https://github.com/apache/fluss/blob/1992f3940498342db3093fa80b2d3b070f559bf2/fluss-server/src/main/java/org/apache/fluss/server/kv/rocksdb/RocksDBStatisticsRegistry.java)。

取舍是最容易被漏写的重点：原来的“最大 bucket P99”变成“该 TS 上该表所有样本的 P99”，低流量慢 bucket 可能被高流量快 bucket 掩盖；stall 是累计总和，并发 stall 的时间可以重叠。评审要求新名 ...P99、...Total，历史四个 ...Max 名作为 deprecated alias 保留至 1.x、计划 2.0 移除。**保留名字不保留旧语义**，现有 alert threshold 需要重审；跨 TS 的 P99 不能 max/average 得到全表 P99。这是 merged main 中以 1.1 为目标的迁移说明，不代表 1.1 已发布。[评审](https://github.com/apache/fluss/pull/4948#issuecomment-6516995098)；[合并版监控说明](https://github.com/apache/fluss/blob/1992f3940498342db3093fa80b2d3b070f559bf2/website/docs/maintenance/observability/monitor-metrics.md)。

后续 TS-level cache/read-cost 观测 [#4855](https://github.com/apache/fluss/pull/4855) 仍 open，作者承诺适配共享 Statistics 后的 collection cursor 和引用计数，避免重复注册计数、首个 bucket 关闭后停止采样；不能将其新增 12 series 当作已发布指标。上期普通 MultiGet 锁外执行 [#4768](https://github.com/apache/fluss/pull/4768) 仍 open，本周不要重复当作新落地。

另一个必须记录的反转是 [#4488](https://github.com/apache/fluss/pull/4488)：10 月 29 日曾合并通过 Get 复查每个 null 的办法，区分 MultiGet 真正 missing 与 JNI 被吞掉的 read error；但 genuine miss 会多一次 point lookup。10 月 30 日评审建议改在 RocksDB JNI 层解决，并计划纳入后续 Fluss RocksDB release，[#4951](https://github.com/apache/fluss/pull/4951) 07:46 UTC 已回滚。故截止时不能宣布 MultiGet 错误处理已修好；具体回滚 patch 还撤回 limitScan 的 iterator status 改造和相关测试，不能只说回滚“性能 workaround”却保留全部正确性修复。[撤回理由](https://github.com/apache/fluss/pull/4488#issuecomment-6513477128)；[实际回滚](https://github.com/apache/fluss/commit/e3a5c2a7d395dee8fce82207b993f482178aeed2)。上游修复是否已进入新的 Fluss RocksDB 版本本次未单独核实，不作已交付判断。


## AutoMQ：真正完成、可恢复前缀与清理器协作

### 1. 恢复要等待真正的存储完成；失败后的继续前进也必须说清丢弃范围

上期在修 WAL 解码后的预算和 byte accounting，本周则推进到更关键的生命周期界线。[#3700](https://github.com/AutoMQ/automq/pull/3700) 指出：ZeroZone 中 linked local write 原先没有纳入 committed RouterChannel epoch 核算，remote write 又在 Produce response 完成时释放注册；若响应只是超时而底层 append 还在进行，epoch 已经前进，随后 ConfirmWAL commit 可能漏掉迟到的 link，导致其引用的 RouterChannel 数据被提前 trim。这里“请求结束”与“数据不再可能进入这个 epoch”不是同一事件。

修复把 fencing 检查与请求注册相对 epoch advancement 原子化；每个 partition append 的 context 穿过 transaction-verification handoff，到真正 storage append 边界捕获 future。先等所有 partition responses 才读取这些 futures，避免事务验证推迟实际 append 注册；之后等全部 append futures 终止才释放一次 epoch registration。客户端响应仍按既有超时返回，不必为这套内部生命周期额外延长响应；但 buffer 要保留到 response 与 storage 都完成。DIRECT local write 没有 RouterChannel link，仍不纳入 epoch 核算，无协议、持久化格式或配置改变。[实现与回归测试](https://github.com/AutoMQ/automq/pull/3700/files)

同日另一项 [#3701](https://github.com/AutoMQ/automq/pull/3701) 必须与预防性修复区分：link metadata parsing 或 decode 失败不再使整个 WAL recovery 直接中止，而是保留失败前的成功全局 WAL 前缀，丢弃失败记录及之后所有 streams 的 WAL 后缀。**这是明确有损的恢复策略，不是“自动修复所有损坏数据”**。成功恢复随后允许 WAL reset，因此不是仅暂时跳过该记录、留待下次找回，也不是仅丢弃出错 stream 的后续记录。[PR 的 lossy fallback 声明](https://github.com/AutoMQ/automq/pull/3701)

实现先过滤已 committed、已关闭 stream、非连续记录，再有界批量并发 decode；检查顺序按 WAL position 而非 future 完成先后，保证最早失败决定截断点。每批（包括未填满的批）先上传，再继续预取；只有被保留记录推进实际 recovered stream ends，预取扫描使用私有 offsets。decoder 的输入改为明确借用：caller 在 decode 成功或失败后释放，返回记录单独归 caller 所有，避免 double release 用 IllegalReferenceCountException 掩盖原始故障。新增测试覆盖跨 stream 截断、乱序完成、sizing 错误、上传失败清理及已解码后缀释放。源码以 [RECOVERY_TRUNCATED] 日志标明失效 WAL position、stream ID、base offset。[恢复实现](https://github.com/AutoMQ/automq/blob/eb5ff4484b/s3stream/src/main/java/com/automq/stream/s3/WALRecovery.java)

两项分别于 10 月 27 日 11:04:01 / 11:03:36 UTC 合入 main；当日 [#3704](https://github.com/AutoMQ/automq/pull/3704) 回移 1.7、[#3703](https://github.com/AutoMQ/automq/pull/3703) 回移 1.8。10 月 28 日 03:33:22 发布的 [1.7.5-rc2](https://github.com/AutoMQ/automq/releases/tag/1.7.5-rc2) changelog 明列 #3704，所以这里可说“已经进入已发布 RC”；不能写成 1.7.5 正式版发布。GitHub release 的 prerelease 布尔值虽为 false，版本名仍明确是 rc2，编辑应按版本名表达。

#### 本周未闭环：重试本身不能修复过期的恢复快照

[#3711](https://github.com/AutoMQ/automq/issues/3711) 报告在 1.7.5-rc2、S3 WAL、Strimzi combined controller/broker 改 controller-only 时，failover 先取得 opening-stream 快照，旧 owner 随后关闭其中一个 time-index stream。恢复构造的多 stream object 提交被 STREAM_NOT_OPENED 整体拒绝；内层每十秒重复同一请求，不会重新取得 stream 集合，导致作者报告 128 个 partitions（含 42/50 offsets partitions）停在 OPENING 约 54 分钟，后续 failover 也排队。作者报告重启 failover target 后，重新列出 streams 的另一 target 两秒完成；这是一例现场 workaround，不应改写成所有环境的无风险操作建议。

10 月 30 日提出的 [#3717](https://github.com/AutoMQ/automq/pull/3717) 截止仍 **open、未合并**。方案将 STREAM_NOT_OPENED、STREAM_FENCED、OFFSET_NOT_MATCHED、STREAM_INNER_ERROR 从无限重试的默认分支改为抛出对应异常：恢复中退出当前 commit，在 WAL reset 之前失败，交由外层 failover retry 重新获取 opening streams；正常 WAL upload 则进入既有 storage-failure 路径，而不是在被拒绝提交后继续运行。它没有取消 controller 校验，也不是直接丢掉闭合 stream 后强行提交。已核对既有 [recover0](https://github.com/AutoMQ/automq/blob/67145c42d0/s3stream/src/main/java/com/automq/stream/s3/S3Storage.java) 的 upload/commit 在 reset 前，以及 [FailoverListener](https://github.com/AutoMQ/automq/blob/67145c42d0/core/src/main/java/kafka/automq/failover/FailoverListener.java) 的外层 retry。PR 当前仅六行分类变更、无附带测试或评论；不能称现场回归已通过。旧 owner 为何尚在 controlled shutdown 就被判失败、是否支持不重启 target 的 reset/cancel，公开 issue 尚无完整回答。

可提炼的设计启示：可重试错误必须按“重发是否改变成功条件”分类。网络瞬断可以重发；ownership/offset 状态冲突通常需要返回上层重建上下文，原请求无限重放只把不一致固化成不可用。

### 2. Archive 与 compaction 不只是游标问题：两个合法清理器也会互相等住

[#3709](https://github.com/AutoMQ/automq/pull/3709) 修正一个一行状态错误：fully drained Archive 跳到后续 online object boundary 时，AdvanceEmptyCursor 推进了其他 offsets，却留下旧 archiveMetadataEndOffset，metadata cleanup 去找已不存在的位置，归档进度停滞。新方案在同一 Archive record 中把 metadata cursor 一起推进；并非重新归档中间已跳过的数据。

评审继续问“旧 expired object 还在 online index 会怎样”，促成 [#3716](https://github.com/AutoMQ/automq/pull/3716)。维护者用明确 offset 例子说明循环：expired X=[0,50)，living Y=[50,150)，stream start=100；empty cursor 到 50 后，Y 被 archive/publish，metadata cursor M=50，prepared end P=150。Controller cleanup 遇到排在最前的 X，其 start=0 不等于 M，停下。随后 retention 到 150，X/Y 都过期，broker 把二者作为一批删除；但 Y 仍落在 Archive 保护区 [M,P)，Controller 拒绝整批，X 于是继续挡住 metadata cleanup，M 无法前进，Y 又继续受保护。作者明确说这是代码路径示例，**不是运行中完整生命周期已复现的声称**。[完整 bug flow 与验证](https://github.com/AutoMQ/automq/pull/3716#issuecomment-6518366227)

最终合并的解法不是放松 Controller 的保护，而是在 broker 每轮 compaction 刷新 Archive state，去重后、区分 expired/living 之前过滤所有与 [archiveMetadataEndOffset, archivePreparedEndOffset) 相交的 objects。该区间同时涵盖已发布但 online metadata 尚待清理、以及已 prepared 但尚未 publish 的对象。这样 X 可单独删，Y 留给 Archive cleanup。过滤应用于全部六种 compaction modes，包括 expired deletion、physical/Composite merge、dirty Composite cleanup；已有连续性检查不允许跨过滤掉的 gap 合并。恰好接触区间边界的对象仍可处理；空保护区不过滤；Archive state 读取失败就终止本轮，不做无保护 fallback；Archive 禁用时不读取状态。Controller 保留最终冲突检查，应对 broker 取样后状态已变化的竞态。[代码与测试](https://github.com/AutoMQ/automq/pull/3716/files)

代价是每轮读取归档状态、可合并候选减少，收益是避免明知会被拒的重写及把合法过期对象绑在受保护对象的失败批次里。作者报告 focused 49 tests；main 全套 metadata 152、core 1368（52 skipped）、s3stream 530（1 skipped）无失败。报告为作者测试，不是本次调研复跑，也不是端到端线上收敛保证。

#3709 于 10 月 30 日 05:12:47、#3716 于 09:45:13 合 main；[#3718](https://github.com/AutoMQ/automq/pull/3718) 10:11:49 把两项合入 1.8。旧 [#3710](https://github.com/AutoMQ/automq/pull/3710) 的“controller cleanup 过滤 metadata cursor 前对象”备选 backport **closed 未合并**，不要把其候选过滤当作最终上线实现。#3718 focused tests 已完成，广泛测试与格式检查被用户要求停止，评论仅委托 CI，不能沿用 main 的全套结果冒充 backport 全部验证通过。[回移验证边界](https://github.com/AutoMQ/automq/pull/3718#issuecomment-6520005028)

尚未解决的是 MetadataCleanup.schedule() 只挑第一个 pending stream，一个停滞 stream 可能饿死其他有工作 stream；维护者明确说 fairness 可单独跟踪、不必阻塞本次 cursor fix。[评审原文](https://github.com/AutoMQ/automq/pull/3709#issuecomment-6514619500) 截点前没有公平性补丁。三项合并均在 10/30 上午，晚于已核实 nightly 10/29 20:05:03 的更新时间，也不在 10/28 rc2 内；只能称已合 main/1.8，未证实进入可下载新构建。

### 3. 重启性能从组合数字走向单项因果：唤醒旧 snapshot Fetch 的验证补齐，但 PR 仍未合

上期 [#3669](https://github.com/AutoMQ/automq/issues/3669) 的多个 coordination/scheduling/balancing 改动捆绑测量，维护者要求逐项证明。本周 10/27 再次明确希望第一张子 issue 选证据最强的一项，区分历史 1.7 与 main；10/29 的 [#3712](https://github.com/AutoMQ/automq/issues/3712) 真正提供了这样的新证据，不应只复述上期组合 p99。

实验固定 main commit 6bba2b768594c0f674789e2a02ee37e0fbb1e071，与只加 [#3670](https://github.com/AutoMQ/automq/pull/3670) 的构建比较。作者核对 runtime 仅 ElasticReplicaManager 一个 compiled class 不同，dependency jars 与其他运行文件一致。问题是 snapshot replica 的删除或替换绕过普通 partition-stop 路径，没有重新检查 delayed Fetch；旧 replica 已不能服务，旧请求仍等 long-poll 超时。方案先发布新 mapping，再在 ConcurrentHashMap.compute 外检查 delayed Fetch/Produce，防止引入 map/purgatory 锁序反转；unchanged mapping 不唤醒，既有完成条件决定数据或错误。

六 broker、三个逻辑 racks、每 rack 两 broker、单 partition 持续写与按 rack 独立 reader，Fetch v13/maxWait 5s/minBytes 1。重启日志显示，从 snapshot removal 到 NOT_LEADER_OR_FOLLOWER，baseline 约 4747–4854 ms（5 个观测），补丁后 3–9 ms（6 个观测）。另用 exclude.zones 确定性删除 replica，验证新 marker 已在真实 leader 确认，五秒和一秒超时设置均显示 baseline 等待随 timeout 变化、补丁及时返回。[机制验证](https://github.com/AutoMQ/automq/issues/3712)

六次 fresh-data 试验顺序 baseline→fixed→fixed→baseline→baseline→fixed：20 records/s、1024-byte、75 秒流量、第 25 秒 graceful restart，关闭 optional AutoBalancer，WAL/router batching 250ms。读可见性从提交到 Fetch 收到，以 probe monotonic clock 测量，覆盖全运行区间；每次 p99 合并三个同样本量 reader、nearest-rank。三组 main read p99 为 4.268/4.290/3.100s，fix 为 0.732/0.934/0.734s；max main 5.348–5.391s，fix 1.072–1.412s。write ack maxima main 1.089–1.131s，fix 1.062–1.396s，**不支持写延迟改善**。这不是 broker readiness 改善的替代指标，而是单一请求生命周期缺口的测量。

作者报告 9000 已确认 records、三个 reader 共 27000 deliveries 全部 exact offset 与 payload-byte 校验，无失败 produce、漏数据、重复 offset；两个 snapshot transition 回归在 unpatched main 失败、patched 通过，广泛测试 1984 passed/53 skipped。限制同样明确：单机 Docker synthetic 单分区、无模拟跨 AZ 延迟，p99 是这些本地运行而非 fleet 估计；历史 1.7 应用 query-visible 数据另列，不能与 main Fetch 指标混比；一次 retained-storage 同时换 image 的预试遇到 WAL fencing startup failure，被排除，最终试验用 fresh storage。

本周进展是“独立 main 对照与完整性证据补齐”，而不是“恢复优化系列已落地”。#3712 open、0 comments；#3670 截止仍 open/未合，公开 PR timeline 只有此前 CLA comment，其他 #3669 系列不能从这一项读改善推导整体收益。


## 下一周最值得核验的证据

- Kafka：coordinator task 是否能与正确 batch 原子绑定；Streams 延迟 native WriteBatch 是否合并、峰值和 commit 代价如何验收；DLQ 故障绕过路径是否增加明确指标。
- Fluss：Kafka channel 是否真正接入现有背压；新旧连接能否在过载时一致暂停；统计共享后的告警迁移是否有运维说明；被回滚的 MultiGet 读错是否由底层 JNI 修复承接。
- AutoMQ：failover 的状态冲突分类是否合并并复现原场景；有损恢复是否能清楚提示被丢弃范围；Archive cleanup 公平性是否有独立修复；snapshot Fetch 的单项对照是否通过维护者评审。

这些问题各有具体状态转换、回归条件或发行证据，不应靠更多 closed/merged 数量替代。

## 来源覆盖与验证边界

Kafka 核查了窗口内新建与合并 PR 的官方查询结果，并完整读取主要 PR 的正文、diff 与关键讨论；KIP-1385 读到提案正文，但其邮件讨论未能完整取得，因此只报告提议，不称已有共识。Kafka 发布日期以官网与正式公告分别标明，安全条目以官方 CVE 列表为准，不外推所有版本的修复范围。

Fluss 完整检索 updated 日期范围的 155 项 PR，再按实际事件日期筛选；重点读取 12 项 PR 的完整返回评论，以及 JSON、SASL、资源配置、监控说明的固定合并文件和 MultiGet 回滚 patch。邮件公开索引可见日期滞后，未取得本周完整邮件集，不能据此断言无新 FIP 讨论或投票结果。

AutoMQ 检索官方组织窗口内 9 项 issue、30 项 PR 活动，深入核读 17 项 PR、7 项 issue 及关键生产补丁，并检查最近 10 条发行记录。检索数包含旧 PR 更新，不是本周新功能数；本期没有覆盖所有官网博客、视频或私下交流。各项目的自动评审意见不作为独立正确性证明，关键变化以维护者回复和最终补丁相互校验。

检索截止：2026-10-30 12:10 UTC；事件截点仍为 12:00 UTC，窗口后活动不计本期。本研究未独立部署三套系统、未复跑其产品测试或性能实验。文中测试数量、延迟与故障结果均保留作者场景限制，局部改善不代表生产集群的通用收益。本文只使用公开技术来源，没有归档整篇第三方原文或开展全文翻译。
