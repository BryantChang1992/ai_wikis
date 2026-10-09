---
title: 第 1 期：分配、重试与恢复的边界
type: survey
created: '2026-10-09'
tags:
- Kafka
- Fluss
- AutoMQ
- 流存储
blog_url: https://bryantchang1992.github.io/ai_memory_chang_ai_team/stream-storage-observer/2026-10-09/
blog_source: stream-storage-observer/2026-10-09.md
blog_source_commit: 82b0a7d1e406ce27735469a5822b5a1af9355e96
blog_body_sha256: 3c1a6b187fa0c159fe9277456458d3f7857a15da1dce55f2703322673f2ef000
synced_at: '2026-10-09'
issue_date: '2026-10-09'
observer_number: 1
related:
- '[[知识库/wiki/Kafka-后台分配与代际隔离]]'
- '[[知识库/wiki/Fluss-分区桶数路由契约]]'
- '[[知识库/wiki/Fluss-灾难恢复的三种保证]]'
- '[[知识库/wiki/AutoMQ-有界投机重试与资源生命周期]]'
- '[[知识库/wiki/配置演进-新写入校验与历史回放分离]]'
---

[← 流存储技术观察](https://bryantchang1992.github.io/ai_memory_chang_ai_team/stream-storage-observer/)

观察窗口：2026 年 10 月 2 日 19:56 至 10 月 9 日 19:56（北京时间，UTC+8）。本期为独立专题首期，资料于 10 月 9 日核验。下文具体事件时间统一使用 UTC，避免邮件归档和 GitHub 日期混用。

本周三个社区都在处理一个相似的问题：把工作放到后台、把请求发得更并行、把状态放到远端之后，怎样继续维持原先的正确性承诺。Kafka 的分配计算要防止过期结果在回滚后生效；Fluss 的客户端并发与远端恢复需要清楚的失败边界；AutoMQ 的投机重试和多桶写入，则必须控制请求放大、完成顺序与数据清理。

这些方向的成熟度并不相同。下面先给出状态地图，再解释问题、机制和取舍。表中的“合并”只表示进入所列分支，不代表正式版本已经发布。

| 项目与核心线索 | 本周事件 | 截止阶段 |
|---|---|---|
| Kafka 协调器后台分配、uniform2 | 10/3、10/6 新 PR；10/7 评审 | 开发/评审中，均未合并 |
| Kafka share cold snapshot | 10/8 新 PR | 修复提议，未合并 |
| Fluss 分区路由、共享 lookup | 10/3、10/4 合并 | main 已合并，正式版归属未确认 |
| Fluss TLS 基础组件 | 10/6 合并 | 仅基础组件，运行时接线未完成 |
| Fluss 全盘丢失恢复 | 10/8 问题与新 PR | 评审中，未合并 |
| AutoMQ 有界排队快速重试 | 10/8 合并 #3641 | 1.7 分支已合并，未据此确认正式发行 |
| AutoMQ IPv6 配置兼容、多桶 RouterChannel | 10/7 讨论收敛、10/9 新 PR | 均未合并 |

表中各项原始来源与精确阶段见下文。文章中的工程观察来自所述机制推导；上游自报的测试与性能动机不作为本刊独立验证结果。

## Kafka：让协调器计算更轻，也让分配结果更合理

### 先减少无收益的 rack 计算

**本周事件：10 月 5 日 09:46:23。** Lucas Brutschy 对 KIP-1379 给出具体评审，追问 broker-wide 配置是否该下放到 group、开关翻转是否引发兼容影响，以及向已有 topic 返回空 rack 集合会不会改变接口契约。发起邮件是 10 月 2 日，具体时区未在取得的引文中标注，因此正文以 10 月 5 日评审作为确定的本周事件。[评审原文](https://www.mail-archive.com/dev%40kafka.apache.org/msg158908.html)

KIP 的动机很实际：只有消费者使用 follower fetch，且分区副本没有覆盖所有 rack 时，rack-aware assignment 才能改变读取位置。当前 metadata hash 却会为每组读取副本 rack，leader/ISR 变化也可能触发重算。方案用默认 false 的 broker 配置显式开启；关闭时从 hash 和 assignor 输入移除 rack。减少计算的代价是引入运维选择，并需处理滚动升级重算及自定义 assignor 的兼容。状态仍是 Under Discussion。[KIP-1379](https://cwiki.apache.org/confluence/spaces/KAFKA/pages/451979127/KIP-1379%2BMake%2Bserver-side%2Brack-aware%2Bassignment%2Bopt-in)

### 再将耗时分配移出前台，但必须防止旧结果“复活”

**本周事件：10 月 3 日 17:28:45 创建 PR #23688；10 月 7 日进入人工逐行评审。** 这个 KAFKA-20292 系列补丁把 consumer assignor 放到 coordinator 后台线程，提议配置默认开启。因此，触发计算的 heartbeat 不一定立即拿到新 assignment，需要后续 heartbeat 接收结果。[PR #23688](https://github.com/apache/kafka/pull/23688)

真正的难点是日志回滚：某次 group epoch 增长触发了后台计算，随后写入失败、epoch 回滚；后台任务却继续运行。下一次增长可能再次用到同一个 epoch，仅比较数字就无法区分旧任务结果。补丁跟踪每个 in-flight run 的 epoch，在 group epoch 增长到该值或更低值时取消旧 run。这里用更复杂的生命周期管理换取前台响应能力，不能只概括成“多加一个线程”。10 月 7 日评审仍在问数据结构维护规则、removeGroup 清理与 targetAssignmentEpoch 校验。截止时 PR open、merged_at=null，尚不能视为已落地主干或已发布。[epoch 评审](https://github.com/apache/kafka/pull/23688#discussion_r4206725017)；[状态清理评审](https://github.com/apache/kafka/pull/23688#discussion_r4206674806)

### 最后改变“均衡”的定义：总分区数相等，不代表热点被分摊

**本周事件：10 月 6 日 08:32:18，PR #23723 提出 uniform2 主体。** 老 uniform 分配器关注每个 member 的总 partition 数，可能让某个 topic 几乎全部落到同一个 member。若 topic 间流量不同，扩容成员也不一定分散热负载。[PR #23723](https://github.com/apache/kafka/pull/23723)

uniform2 优先保证每个 partition 恰好分配给一个订阅者，再使同一 topic 在其订阅者之间只差至多一个 partition，并确保额外分区不能再转给总分配数至少少两个的同主题订阅者；满足这些约束后，才尽量保留现有 ownership，且结果只依赖输入内容。其流程拆为 keep、hand out、balance 和具体 partition placement。取舍是把逐 topic 公平性放到总数与粘性之前，增加算法复杂度；它不是基于实测字节流量的动态负载调度器。当前补丁明确不处理 rack，且仅与旧 uniform 并存开发，未注册为内置 assignor。截止时仍 open，现有默认分配器未因此改变。[同一原始 PR 的设计与阶段说明](https://github.com/apache/kafka/pull/23723)

三条线索对应不同层面：KIP-1379 降低无效计算，offload 降低计算对前台的阻塞，uniform2 改善计算结果。它们一起显示，server-side rebalance 的下一步是既让 coordinator 扛得住，又确保扩容确实改善业务负载。这是本刊综合判断，不是性能数据；目前没有足够一手 benchmark 支持一个统一加速倍数。

### Share group：空闲分区也会拖住日志清理

**本周事件之一：10 月 5 日 17:39:27，KIP-1349 获得 Sushant Mahajan 的 +1。** 这不是新提案：邮件引文显示投票最早于 8 月 19 日发起，核心方向是由记录数改为字节数控制 share-group 快照频率。本周这条 +1 本身不足以确认投票通过，也没有证明代码合并。[本周投票原文](https://www.mail-archive.com/dev%40kafka.apache.org/msg158919.html)

**本周事件之二：10 月 8 日 19:05:55，PR #23750 提出 cold snapshot 修复。** 现有定时器用创建和写入时间推断“最后一个 snapshot 来自 cold job”，但 ShareUpdate 不改变这两个时间戳。若所有分区都做过 cold snapshot，此后即使来了新 update，任务也可能继续被跳过。[PR #23750](https://github.com/apache/kafka/pull/23750)

补丁的第一层修复是：只有所有分区均处于 cold-snapshot 状态且没有 pending update，才跳过整轮；第二层是在每个 ShareSnapshot 时重置更新计数，使计数真正代表尚未被 snapshot 包含的更新。一个反直觉点是，没有新更新的闲分区仍需适时重拍，因为日志可裁剪边界由所有 share partition 最新快照 offset 的最小值决定。只优化活跃分区，会让闲分区卡住全局清理。此项仍为 open PR，没有已合并或已发布证据。

字节阈值解决“做一次快照之前积攒多少状态”，cold snapshot 解决“谁在拖住全局回收边界”。二者处于同一成本模型，却是两件不同工作；这次正确性补丁并不意味着 KIP-1349 已实现完成。

### Diskless 与版本进度：讨论仍在继续

10 月 5 日的开发邮件索引出现 KIP-1165 对象整理（Object Consolidation）的讨论。当前草案将混合 partition 的摄入 WAL 后台整理成普通分区日志，再通过 KIP-405 分层存储承接历史读取；只有远端日志、索引及 producer snapshot 连续可读后，才回收相应 WAL 坐标。这个设计试图同时解决摄入攒批、落后消费者读取和逐分区过期删除，代价是后台 I/O 与跨层进度管理。它仍为 Under Discussion (Re-Opened)。本次取得了邮件索引与当前草案，但单封邮件正文未成功取回，因此这些规则只作为当前方案背景，不宣称都在本周首次提出。[讨论索引](https://www.mail-archive.com/dev%40kafka.apache.org/maillist.html) · [讨论条目](https://www.mail-archive.com/dev%40kafka.apache.org/msg158917.html) · [KIP-1165](https://cwiki.apache.org/confluence/spaces/KAFKA/pages/350783996/KIP-1165%2BObject%2BConsolidation%2Bfor%2BDiskless)

Kafka 4.4.0 本周推进至 RC4 的测试与投票阶段。10 月 7 日的投票邮件将截止设为 10 月 12 日 09:00 PT；10 月 8 日的验证反馈确认此前制品签名问题解决，并指出文档仍需从最终 tag 生成。这是候选版本验证进展，尚不能写作正式发布。[RC4 投票](https://www.mail-archive.com/users%40kafka.apache.org/msg44062.html) · [验证反馈](https://www.mail-archive.com/dev%40kafka.apache.org/msg158967.html)

## Fluss：补齐客户端、安全与灾难恢复的运行边界

### 多语言客户端补齐路由与并发语义

分区表修改 bucket.num 后，旧分区仍保留原来的桶数；因此不能用表级桶数统一计算全部分区的路由。9 月 29 日提出的 [issue #4525](https://github.com/apache/fluss/issues/4525) 指出，Rust 核心仍按表级 num_buckets 路由，也没有发送 routing_bucket_count。结果是在 1.0 服务端上出现 lookup/list offsets 错误、flush 卡住和扫描无结果。Python、C++、Elixir 使用同一核心，因此这并非单一语言的边角问题。该问题的提出日期在本周之前，本周新增的是修复合并。

[#4527](https://github.com/apache/fluss/pull/4527) 于 10 月 3 日 16:37:55 合并到 main。实现缓存分区桶数及表级 bucket-count epoch，并在写入、读取、lookup、统计等请求中携带 routing_bucket_count；epoch 为 0 时才使用旧的表级回退。写入未知分区先使用临时桶数，在真正发出前解析；服务端继续拒绝使用过期桶数的批次，避免静默错路由。

这项补齐仍有明确边界：修改桶数前创建的 writer，第一次向新分区发送有 key 的批次可能失败，随后用同一 writer 重试才能成功。Rust 对发送后的路由拒绝采取“批次失败并重新读取桶数”，而非直接使整个 writer 失效。这是以显式重试保护路由正确性，不能解读成修改桶数对应用完全无感。

同一条线上的另一部分是 lookup 并发。9 月 28 日创建的 [#4500](https://github.com/apache/fluss/pull/4500) 于 10 月 4 日 01:37:34 合并：Rust Lookuper 从独占可变引用改为共享引用，编码器的 mutex 在 await 前释放，Python 绑定移除外围 mutex。这样才能让同一个 lookuper 的多个查询同时进入 batching。随后 [#4541](https://github.com/apache/fluss/pull/4541) 于 10 月 4 日 08:35:07 合并，C++ 桥接改用共享引用、接口改为 const，并以编译期 Sync 检查支持跨线程共享。

但“跨线程共享”尚不等于“单线程异步流水化”。10 月 6 日创建的 [#4559](https://github.com/apache/fluss/pull/4559) 仍为 open：它提出 PendingLookup/PendingPrefixLookup 句柄，使启动查询立即返回，再通过 Wait 收取结果；带超时的 Wait 保留仍在执行的查询，销毁句柄则放弃查询。10 月 7 日创建的 [#4563](https://github.com/apache/fluss/pull/4563) 也尚未合并，针对单个不可用 TabletServer 拖住整个客户端的队头阻塞：重试填满 batch 时仍接纳新查询，请求异步发送，且不再重试调用者已放弃的查询。关联 [#4562](https://github.com/apache/fluss/issues/4562) 给出了单台不可用服务器导致其余健康服务器查询也超时的场景。

这组变化的价值在于将 Java、Rust 及其语言绑定的运行契约拉近，而不只是增加 API。已合并的路由和共享对象能力，应与尚待评审的非阻塞句柄及故障隔离分开追踪；本期没有证据表明它们已进入新的正式发布包。

### TLS 基础组件合并，运行时加密尚未接通

FIP-29 在本周之前已形成设计。它针对的是 Fluss RPC 的原生 TLS/mTLS：客户端会根据元数据直连持有相应 bucket 的服务器，单一入口的 TLS 终止并不能自然覆盖这种连接拓扑，也不能直接把客户端证书身份交给 Fluss 的授权体系。[FIP-29 原文](https://cwiki.apache.org/confluence/spaces/FLUSS/pages/406620533/FIP-29+m+TLS+Support) 将传输加密与认证插件区分开，计划在 Netty pipeline 最前端加入 SslHandler，再让既有应用层协议运行在加密连接内。

7 月 30 日创建的 [#3813](https://github.com/apache/fluss/pull/3813) 于 10 月 6 日 15:45:49 合并。它增加服务端 security.ssl.*、客户端 client.security.ssl.* 配置、SslConfig 解析校验，以及构造 Netty SslContext/SslHandler 的工厂，支持客户端主机名校验及服务端按 listener 决定是否要求客户端证书。

本周评审也有实质落点：10 月 6 日作者回复，已修正旧 JDK 不支持默认 TLS 协议时的校验问题；同日补上 truststore 加载时的可信证书检查，避免 PKCS12 未正确解密却构造出空信任库，直到握手才失败。并保留无密码 JKS 的合法用法，而不是一刀切要求密码。对应证据为 [协议默认值修正](https://github.com/apache/fluss/pull/3813#discussion_r4195348637) 和 [空 truststore 检查](https://github.com/apache/fluss/pull/3813#discussion_r4195506685)。问题最初在 10 月 1 日提出，修复回复及合并发生于本周，二者不能混写为本周新发现。

FIP 原设计指出，基于 SslHandler 的加密要求文件内容经过 JVM 缓冲区，因此日志读取不能继续直接走 sendfile 的零拷贝路径；每个 listener 是否开启 TLS，需要在威胁模型与读取吞吐开销之间做明确选择。这属于设计背景，不是本周新增性能测试结论。FIP 也没有包办 ZooKeeper 连接、远端存储或磁盘静态加密。

#3813 明确说明没有接入生产 pipeline，不改变运行时行为；[服务端接线 #3792](https://github.com/apache/fluss/issues/3792) 与 [客户端接线 #3797](https://github.com/apache/fluss/issues/3797) 仍 open。因此，目前合并的范围是 TLS 基础配置与工厂，运行时接线及整个 FIP 尚未交付。

### 全量本地盘丢失：恢复能力取决于远端覆盖边界

远端存在 KV snapshot 和 WAL，并不自动意味着本地状态清空后能正常启动。10 月 8 日 09:38:22 新建的 [#4566](https://github.com/apache/fluss/issues/4566) 报告：所有 TabletServer 本地数据丢失、但 ZooKeeper 及远端快照/WAL 保留时，空本地日志从 offset 0 开始，而快照可能对应更高 offset。若不先恢复日志边界，KV replay 会访问不存在的本地位置；首次失败遗留的 tablet 注册状态还会让后续重试报重复目录错误，掩盖真正原因。

同日 09:40:03 创建的 [#4567](https://github.com/apache/fluss/pull/4567) 提议先从耐久快照和已提交远端 WAL 恢复空日志的 offset、高水位、leader end-offset snapshot，以及用于重复写入检测的 writer state，再恢复 KV。对于必须读取却缺失或被截断的 WAL 区间，应明确失败，而非静默构造缺数据的状态；失败的部分初始化也应清理干净以允许重试。恢复后若快照已超前于旧远端 WAL，tiering 需要在显式保留缺口的前提下继续运行。

该 PR 不承诺恢复全部已确认写入。若某次写入只存在于已经全部丢失的本地副本，且尚未被远端快照/WAL 覆盖，它仍可能丢失；历史 changelog 的每个 offset 也不保证继续可读。观察上应把“恢复出一致的 KV 状态”“保住全部已确认写入”“保留连续可重放日志”作为三个不同保证。这不是文字细节，而是应用能否在故障后继续增量消费、是否需要重新建立基线的边界。

#4567 为新提交且 open、merged=false。灾难恢复修复仍在评审。对依赖本地多副本来兜底的数据平台，这个案例提示测试应覆盖所有本地副本同时丢失，并核对远端数据实际覆盖到哪个一致边界；这是基于问题和方案作出的工程观察，并非社区发布的运维保证。

### 其他实质讨论

- Kafka Basic Produce：10 月 4 日作者在 [#4185 的评论](https://github.com/apache/fluss/issues/4185#issuecomment-5979636805) 表示基础代码和部分性能测试已有，但尚未合并；10 月 6 日另一贡献者 [回复](https://github.com/apache/fluss/issues/4185#issuecomment-6012953509) 已向作者 fork 提交初步修正。该里程碑强调 Fluss DDL 先建表，再用 Kafka producer 写入；Kafka consumer/Fetch、幂等与事务 Produce 不在当前范围。本周协作推进的是这一有限范围，全协议兼容尚未落地。
- 存储侧保留最近 N 项：10 月 8 日深夜提出的 [#4569](https://github.com/apache/fluss/issues/4569) 与 [#4570](https://github.com/apache/fluss/pull/4570) 为 ARRAY 聚合增加 last_n，将输入数组追加后保留最后 N 个元素，减少应用重复维护 per-key 历史状态。代价是每次更新重写数组；FULL changelog 同时记录旧、新数组，故适合较小 N。PR 尚未合并，也不是按事件时间排序的窗口机制。
- 表内均衡：旧 PR [#3917](https://github.com/apache/fluss/pull/3917) 在 10 月 9 日 07:03 获得 [LGTM +1](https://github.com/apache/fluss/pull/3917#pullrequestreview-5466908193)，但仍 open。它试图修正“集群总数均衡、单张热表仍集中”的盲区，增加按表的 replica/leader 目标，并优先转移 leadership、必要时才迁移副本。评审通过意见不等于已合并。

## AutoMQ：对象存储路径的尾延迟、兼容性与多桶扩展

### S3 快速重试：从抢占名额转向有界排队

对象存储偶发慢请求会传导到流存储的尾延迟。现有 PutObject 快速重试在请求超过按大小统计的 P99 延迟后尝试申请重试名额，但五个名额全部被占用时，本次重试机会直接丢失。这样，稍慢的请求可能先占满资源，真正长尾的请求反而得不到第二次尝试。合并范围读取此前也没有对应的投机重试能力。[PR #3641](https://github.com/AutoMQ/automq/pull/3641)

本周首先出现的开发线索是 10 月 7 日 11:55:59 创建的 #3640：作者希望给 leader 读取代理 RouterChannel 的路径加入快速重试，并通过负载测试观察 P99 尖峰是否收敛。这是明确的问题假设和待验证目标，原帖没有给出已改善的生产性能数据。[PR #3640](https://github.com/AutoMQ/automq/pull/3640)

10 月 8 日 09:36:06 创建的 #3641 对读写快速重试做了更系统的改造：超过 P99 时，仅将仍未完成的原始请求放入 FIFO 队列，EventLoop 在执行前再次检查原始请求是否已经完成；每个重试管理器最多运行一个投机请求。代码分别创建读、写管理器，因此这里的“一个”不是集群级总上限。队列最终使用容量为 4096 的 ArrayBlockingQueue，满时直接丢弃该次投机机会并释放其资源，原请求及正常重试路径继续运行。[PR #3641](https://github.com/AutoMQ/automq/pull/3641)；[作者确认队列上限](https://github.com/AutoMQ/automq/pull/3641#discussion_r4217787312)

读取采用第一个成功结果完成最终 future，晚到的重复成功结果释放对应缓冲区；投机请求失败不会夺走原请求正常重试路径的控制权。未知长度的读到末尾请求和 API 检查模式跳过读快速重试。另一个容易被忽略的修正是延迟直方图恰好命中大小桶边界时，不再由插值返回零，避免触发阈值失真。[合并提交 75b11ff](https://github.com/AutoMQ/automq/commit/75b11ff660c62ba5fa3b0d93ad9b6caca967b90f)

这里的工程取舍很清楚：牺牲部分重试并发，保留真正仍在等待的请求的重试机会，用有界队列控制资源占用。本文判断是，这更适合吸收少量 S3 延迟离群点，不能据此推导为普遍性 S3 降速时的吞吐提升。队列容量限制的是任务数，不能直接等同于缓冲区字节上限。

社区讨论也没有把“先返回成功”与“底层请求结束”混为一谈。#3640 的评审在 10 月 7 日指出，投机读取获胜后，如果原始 GET 尚未结束但名额已经释放，实际在途 GET 可能超出预算；作者在 10 月 8 日回复讨论取消原始请求，并把读写路径的相关完善列为后续工作。这是仍公开存在的资源生命周期讨论，不能把 #3641 的合并解释为 #3640 所有问题已经被关闭。[评审问题](https://github.com/AutoMQ/automq/pull/3640#discussion_r4212442069)；[作者回复](https://github.com/AutoMQ/automq/pull/3640#discussion_r4215072636)

#3641 在 10 月 8 日 12:06:17 获得 Gezi-lzq 的 APPROVED review，12:13:16 合入 1.7，合并提交为 75b11ff660c62ba5fa3b0d93ad9b6caca967b90f。作者报告完成 s3stream 测试和相关 S3UnitTest 等验证，同时披露其环境中 RAT 被禁用、规定的 spotlessJavaCheck 不可用；本观察没有自行重跑测试，也没有发现可支撑性能收益百分比的公开测量。[批准记录](https://github.com/AutoMQ/automq/pull/3641#pullrequestreview-5456287386)；[PR 与验证说明](https://github.com/AutoMQ/automq/pull/3641)

#3640 截止时仍 open；两者目标分支不同：#3640 指向 main，#3641 合入 1.7。

### IPv6 Zone 路由：新配置严格，旧状态兼容

10 月 5 日 18:59:47，社区报告在 IPv6-only EKS 环境启用 Zone Router 后，不带 automq_az 提示的客户端 METADATA 请求抛出 NumberFormatException；连没有配置 CIDR 的情况也受影响。原因是旧匹配器按点分 IPv4 字符串转 long，遇到 IPv6 地址即失败。报告涉及 1.7.4，并说明在 1.7.5-rc1 和其他环境复现；这些是报告者的复现范围，不是本观察重新认证的版本矩阵。[Issue #3638](https://github.com/AutoMQ/automq/issues/3638)

10 月 6 日 14:30:00 提交的 #3639 改为按地址字节、掩码及前缀长度匹配，支持同一区域配置 IPv4/IPv6，地址只匹配同地址族，采用最长前缀；没有地址、没有配置或无匹配时返回没有 zone，而不是让请求异常。它不改变 wire protocol、存储格式或配置键。[PR #3639](https://github.com/AutoMQ/automq/pull/3639)

讨论很快超出了 IPv6 本身。KRaft 持久化的 broker 配置在回放时也会先调用 validateReconfiguration；若把验证器直接改严格，即使 reconfigure 打算宽容处理旧值，也可能根本走不到应用阶段，并导致整批配置无法应用。旧 CIDR 值还可能挡住无关的 exclude.zones 更新。[Issue 中的兼容性讨论](https://github.com/AutoMQ/automq/issues/3638#issuecomment-6002032683)

随后 10 月 6 日的评审又指出反方向的问题：如果所有验证一律宽容，新 Admin 写入同样可能把不合法值持久化，再静默跳过。10 月 7 日 13:16:22，作者提交说明把严格校验放到 controller 的配置变更入口，只检查此次真正改变且不同于已持久化值的 CIDR；旧状态回放及应用保留兼容行为，删除、重发未变值和修改无关键继续工作。[10 月 6 日评审](https://github.com/AutoMQ/automq/pull/3639#issuecomment-6022269302)；[10 月 7 日调整说明](https://github.com/AutoMQ/automq/pull/3639#issuecomment-6038753240)

取舍不是简单地“宽容解析”。能保持原含义的遗留值保留并告警；旧解析器接受但没有有效 CIDR 含义的条目跳过并告警；新的非法写入拒绝。跳过条目也可能改变实际 zone 选择，因此作者补充了路由语义变化说明，以及 cluster-default→broker override→删除 override 后回落的回归测试。本文判断是，这个案例体现了配置演进中两个不同契约：读取历史状态需要兼容，写入新状态需要收紧，不能共用一个无上下文的严格开关。

10 月 7 日 14:52:44，参与评审的 BackendArchitectX 表示其提出的问题已经解决、没有阻塞意见，并留下一个非阻塞的错误诊断完整性问题。这是参与者的评论，尚不能等同于维护者批准或合并。截止时 #3639 仍 open，merged_at=null。[评审结论](https://github.com/AutoMQ/automq/pull/3639#issuecomment-6040577114)

PR 的升级说明特别要求：所有 broker 都运行包含该变更的版本后，才配置 IPv6 CIDR；回退旧版本前先移除 IPv6 CIDR。controller 无法自动保证这种滚动升级顺序。因修复尚未合并，这里是在报告拟议行为及升级约束，并非推荐当前生产环境直接启用该能力。[升级说明](https://github.com/AutoMQ/automq/pull/3639)

### 多桶 RouterChannel：扩展吞吐之前，先保住顺序与清理

10 月 9 日 11:35:31，superhx 提交 #3642 到 1.7 分支，距离本期截止只有约二十分钟。其背景是 RouterChannel 虽接受多个对象存储 bucket URI，但默认 provider 只打开第一个 bucket，路由 WAL 流量因而集中在单桶。该 PR 尝试让全部 mode=rw bucket 参与写入，同时保留 mode=r bucket 读取已有 offset 的能力。[PR #3642](https://github.com/AutoMQ/automq/pull/3642)

方案不是把每条记录随意分流：RouterChannel 先统一组 batch，按在途请求数选择可写 bucket，再整批提交并显式 flush；offset 中保留 bucket ID，读取据此找回对应 WAL。因为不同桶会乱序完成，外部可见的完成结果通过按 order hint 分组的队列排序；epoch 清理则只推进已完成 append 的区间，再按每桶记录的 offset trim。对象 WAL 增加 manualMode 和 flush，使 RouterChannel 统一掌握批处理，避免两层批处理策略相互干扰。[PR 的设计及代码](https://github.com/AutoMQ/automq/pull/3642)

本文判断是，这把容量扩展问题转化为更明确的跨桶顺序、缓冲区归属和回收一致性问题；bucket ID 必须在仍有 offset 引用期间保持稳定，第一桶的 batch 参数还成为统一策略来源，运维配置不再只是一个可任意重排的 bucket 列表。其收益目前是设计动机，尚不能声称已经消除生产瓶颈或给出扩展倍数。

截止时该 PR open、未合并，只有一项提交和自动评审意见，设计与并发边界仍待进一步人工验证。

## 下周值得继续追踪的证据

- Kafka：后台分配的 epoch 回滚与 group 清理评审能否收敛；uniform2 何时进入可配置入口，而不仅是算法主体；cold snapshot 是否合并并进入目标版本。
- Fluss：非阻塞 lookup 与单台故障隔离是否合并；TLS 是否真正接入客户端、服务端 pipeline；全盘丢失测试是否同时验证 KV 一致性、已确认写入和 changelog 连续性。
- AutoMQ：快速重试能否以公开负载结果证明长尾收益，并同时报告 API 与内存成本；IPv6 修复何时进入可部署版本；多桶写入的乱序完成及清理测试是否通过评审。

## 来源范围与版本边界

本期以 Apache Kafka、Apache Fluss、AutoMQ 官方仓库的 Issue、PR、逐行评审，以及 Apache 开发邮件公开归档和 KIP/FIP 原文为依据。只把实际创建、讨论、评审或合并发生于观察窗口内的事件计为本周进展，页面 updated_at 仅用于发现候选。原始链接随相关论断提供；所述实现机制来自原始补丁及作者解释，本期没有独立运行这些上游代码或复现实验。

Kafka 已核验本周开发邮件及重点 PR。Fluss 的 Apache 邮件列表入口取回受限，公开镜像日期索引所见停留在 9 月，故本周判断主要基于 GitHub 的讨论与评审，不能据此说邮件列表没有活动。AutoMQ 官方仓库未启用可访问的 Discussions，本期覆盖公开 Issue 和 PR，不声称覆盖私有仓库、Slack 或其他非公开交流。

版本方面，Fluss 1.0.0 的[发布公告](https://www.mail-archive.com/dev@fluss.apache.org/msg01449.html)在 9 月 21 日；AutoMQ [1.7.5-rc1](https://github.com/AutoMQ/automq/releases/tag/1.7.5-rc1) 发布于 9 月 24 日，均为本期之前的背景。AutoMQ nightly 条目的滚动更新也不作为新正式版本。本期已明确区分“方案讨论”“开发中”“合并至分支”与“正式发布”，不把兼容性宣传或设计目标当作已测得效果。

---

[返回本专题目录](https://bryantchang1992.github.io/ai_memory_chang_ai_team/stream-storage-observer/) · [技术调研周报：顶会论文与技术博客](https://bryantchang1992.github.io/ai_memory_chang_ai_team/weekly/)
