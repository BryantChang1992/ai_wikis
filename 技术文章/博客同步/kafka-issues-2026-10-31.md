---
type: survey
title: Kafka Issue 周报：恢复状态、成员所有权与修复交付
sources:
- https://issues.apache.org/jira/projects/KAFKA/issues
- https://issues.apache.org/jira/browse/KAFKA-21402
created: '2026-10-31'
updated: '2026-11-09'
status: draft
tags:
- Kafka
- issue
- 社区观察
related:
- '[[知识库/sources/web/Kafka-Issue-2026-10-31]]'
publication_status: github_archive
source_checked: '2026-10-31'
source_check_scope: 公开 JIRA 生命周期与重点原文和 PR、回移、发行；未运行复现。
publication_scope: 仅 GitHub 正文归档；GitHub Pages、知识卡及双库同步暂缓。
report_date: '2026-10-31'
---

# Kafka Issue 周报：恢复状态、成员所有权与修复交付

> 归档范围：本页保存 2026-10-31 报告正文及公开引用，仅供 GitHub 阅读。GitHub Pages 页面、知识卡更新与双库同步暂缓。目录沿用报告的既定路径，不代表已完成博客同步。技术状态按原观察窗口保留，不代表归档日的最新进展。

[公开来源索引](../../知识库/sources/web/Kafka-Issue-2026-10-31.md)

观察区间：**2026-10-24 12:00（含）至 2026-10-31 12:00（不含）UTC**，即北京时间两个周六的 20:00。接续上期固定截点，不因上期未发布而跳过一周。本期实际检索截止 2026-10-31 12:07:45 UTC；正文事件日期统一使用 UTC，截点后的事件不倒填为本周成果。



## 本周结论

本周重点是几类不会因普通重试而自动消失的问题：事务加载失败后的部分缓存可能把错误重新写回日志；Streams 的旧成员仍能访问事务协调器时，空 offset 提交未必能证明任务所有权；恢复 checkpoint 的旧快照和配额中永远放不下的 batch，则分别威胁恢复正确性与消费前进。与此同时，TLS 关闭处理和磁盘 cordon 已有实际合并，必须继续核对它们进入哪一条维护分支、哪一个真正发行包。

官方 JIRA 公开可见查询中，本期新增 **54 项**：21 Bug、18 Sub-task、13 Improvement、2 Task；截至截点其中 11 项已解决、43 项未解决。**28 项出现设置 resolution 的事件**，均仍保持解决状态，类型为 **25 Fixed、1 Won't Fix、1 Won't Do、1 Not A Problem**，未发现窗口内重开事件。新增与解决集合重叠 11 项，合并去重为 **71 项**，不能相加说成 82 个独立问题，也不能把 28 个关闭全部称为修复。

这组数字是公开问题工作流的统计，不是生产事故数或已发版修复数。Fixed 内也有测试、改进与子任务；影响版本字段不是完整实测范围。下文把新增问题、JIRA 解决、PR 合并、回移和正式发布分别呈现，附录保留可复核清单。

### 与其他专题的分工

本期不重复 10 月 30 日《流存储技术观察》的 Kafka 主干机制长篇背景，只补后续 issue、生命周期、回移与发行证据。站内历史入口为[流存储技术观察](https://bryantchang1992.github.io/ai_memory_chang_ai_team/stream-storage-observer/)。[KIP-1150 最新独立周记](https://github.com/BryantChang1992/ai_wikis/blob/master/知识库/专题跟踪/KIP-1150/2026-10-30-迁移控制链合并与读路径安全.md)已经归档；本期没有把普通事务、恢复或网络 bug 强行归为该 KIP 的实现。

## 本周新增问题：正确性边界没有被“正常重试”覆盖

### 事务加载：读到正确位置，还必须证明整个加载成功

10 月 30 日 12:44 UTC 新建的 [KAFKA-21402](https://issues.apache.org/jira/browse/KAFKA-21402) 是本期相对于前一天《流存储技术观察》的重要增量：TransactionStateManager 读 `__transaction_state` 中途失败后，捕获异常、记录日志，却仍返回已经构建的部分 map；调用方随后把它安装成完整缓存并结束加载。报告给出的 TV2 事件是 OOM 之后缓存仍持有很久以前的 ONGOING/epoch，协调器据此超时 abort，写入新的 PREPARE_ABORT；数据分区已见过更高 producer epoch，拒绝 marker。由于错误状态已经重新写回事务日志，换 coordinator、重新加载也未必能自愈，InitProducerId 可能持续返回 CONCURRENT_TRANSACTIONS。这是报告中的观测案例，本期未复现。

它与 [KAFKA-21349 / PR #23943](https://github.com/apache/kafka/pull/23943) 相关但不同：后者等待 HW 追上加载起点 LEO，解决“加载尚未提交的状态”；21402 则问“读取在中途失败，还能否承认缓存完整”。#23943 已在 10 月 27 日合入 trunk，但 JIRA 21349 截止仍 Open、无 fix version，不能为了让表格好看就把它算成已解决。21402 也仍 Open、没有已核实的修复 PR；其 affects version 标了 0.11.0.0，这不是全部后续版本均经实测的证明。10 月 30 日的[维护者回复](https://issues.apache.org/jira/browse/KAFKA-21402?focusedCommentId=18135401&page=com.atlassian.jira.plugin.system.issuetabpanels:comment-tabpanel#comment-18135401) 补充，目前缺少事务分区加载失败指标，新增指标需要 KIP；这是未来设计程序的要求，不能写成已有某个 KIP 已解决问题。

### Streams EOS：没有输入 offset 的事务，也可能需要证明成员仍有所有权

10 月 26 日新建的 [KAFKA-21363](https://issues.apache.org/jira/browse/KAFKA-21363) 报告了一个容易被“EOS 已开启”掩盖的网络隔离窗口。作者使用 4.4.0 client、4.3.0 broker、classic group protocol，只切断旧实例到 group coordinator 的路径，保留 transaction coordinator 和数据分区可达。旧实例仍持有 active task，wall-clock punctuator 继续改 store 并提交事务；新实例又已取得同一任务。punctuator-only commit 没有输入 offset，空 map 不触发 sendOffsetsToTransaction 的成员检查，两者使用不同 transactional ID，也不会互相 producer fencing。作者两次受控复现还显示，旧实例干净关闭保留 checkpoint 后重启，会跳过 checkpoint 之前由另一实例写入的 changelog，导致本地 store 与全量恢复结果不一致。

讨论尚未形成最终补丁。[维护者指出](https://issues.apache.org/jira/browse/KAFKA-21363?focusedCommentId=18132618&page=com.atlassian.jira.plugin.system.issuetabpanels:comment-tabpanel#comment-18132618)，只在客户端超时后丢弃 assignment 仍有竞态，可能只是缩短窗口；把真实 offset 放进事务，才可能强制验证组成员身份。但不能直接提交 consumer position，那会把已拉取、未处理记录也越过去；空 offset map 在 producer 和 broker 两侧又都有短路，兼容旧 broker 的方案仍需推敲。截止无 fix version、未核实修复 PR。报告明确没有测试 KIP-1071 的 streams group protocol，不能把 classic 场景的证据扩展到新协议；这属于既有 EOS 行为缺陷，未核实专属修复 KIP。

### 日志恢复：文件写入串行，不等于 checkpoint 快照不会倒退

10 月 27 日新增的 [KAFKA-21367](https://issues.apache.org/jira/browse/KAFKA-21367) 给出的竞态很具体：定期 checkpoint 先采样 recoveryPoint=10，然后暂停；另一个线程把日志截断到 0，并写入 checkpoint=0；旧任务恢复后又把 10 覆盖回去。现有文件写锁只保护落盘，不保护采样和落盘这个整体，因此“每次写入完整”并不能保证时间顺序。下一次非干净启动可能从过高的恢复点挑选 segment，跳过更早损坏的 batch。

作者在固定 trunk 上用受控 CRC 损坏、segment roll 和未完成异步 flush 验证恢复后果，明确不是实际断电实验，也不是该竞态自行破坏 record 字节。候选 [PR #23975](https://github.com/apache/kafka/pull/23975) 用同一 per-directory checkpoint 对象串行化采样与写入，保持文件格式不变；截止仍在评审，未核实发布版本。需要观察的不是再加一层文件锁，而是两种截断路径、定期任务和目录级并发是否都落入同一顺序边界。未发现直接关联 KIP，按普通恢复正确性修复跟踪。

### 消费配额：永远放不下的一批，等待再久也不会变小

10 月 30 日新建的 [KAFKA-21397](https://issues.apache.org/jira/browse/KAFKA-21397) 指向 consumer fetch 与 share fetch 的活性问题：fetchMaxBytes 被限制到 quota window 容量，但首个非空 batch 为保证前进可以突破该值；响应计费发现超额后又撤销计费、返回空响应。若单个不可拆 batch 比整个允许突发窗口还大，客户端等待后重试同一 offset，仍得到同样的空响应，不会靠时间流逝自然解除。

[帖内方案](https://issues.apache.org/jira/browse/KAFKA-21397?focusedCommentId=18134533&page=com.atlassian.jira.plugin.system.issuetabpanels:comment-tabpanel#comment-18134533) 是让这种永远放不下的响应先发送，保留计费，再通过后续 throttle 偿还带宽，兼顾平均配额与不可拆分 batch 的前进；请求时间配额不应因此被无条件绕过。该回复明确包含 AI 建议代码，尚无合并或回归测试结论，不能描述成维护者已经接受的最终实现。截止 issue Open，影响版本、fix version、关联 KIP 均未核实。

### Streams 静态成员：process 级集合不能表示同进程的两个所有者

同在 10 月 30 日新增的 [KAFKA-21401](https://issues.apache.org/jira/browse/KAFKA-21401) 则揭示所有权索引的表示能力问题。静态成员保留 instance ID、改用新 process ID 重入时，继承旧 standby assignment 可能让同一进程的两个成员暂时持有相同任务；索引只存 Set<processId>，其中一个成员完成 revoke 就删除该进程，另一成员仍持有的 standby 因而变得不可见。后续分配 active role 时便可能不再等待它释放，违反同进程任务排他和协作式交接约束。

作者提出在 process ID 改变时按新成员处理、先移除旧成员记录再重算 assignment，但目前只是候选思路；截止 Open、无 fix version，未核实相应修复 PR。不要将“静态身份相同”混同“持有状态的进程相同”。该问题发生在 Streams group 实现中，本文不凭组件名称强行指认某 KIP 为既定修复方案。

## 本周解决闭环：重新关闭、回移和真正发布要分别看

### TLS close_notify：已经合并，但不是所有受影响版本都已拿到补丁

[KAFKA-21341](https://issues.apache.org/jira/browse/KAFKA-21341) 于 10 月 30 日 14:54 UTC 记为 Fixed，关联 [#23933](https://github.com/apache/kafka/pull/23933) 于当天 12:29 合入 trunk，晚于《流存储技术观察》的截点。问题不是一般的 TCP 断连：TLS close_notify 与应用数据同次读取，读取先返回数据，buffered 标志被清掉；如果对端合法地保持 TCP 开放、不发送 FIN，Selector 不会再读取来报告 EOF，飞行中的请求要等超时。补丁保留后续 buffered read，先交付已解密字节，再报告关闭，避免吞掉最后一段有效响应；muted channel 则等 unmute 后处理。

JIRA 标了大量 affects versions，当前 fix version 只有未发布的 4.5.0。本文只认定 trunk 修复及测试已合并，不把其受影响版本列表误写成“对应分支全部已修”，也不宣称现有 4.4.0/4.3.2 已包含它。未核实直接关联 KIP，按网络层普通缺陷修复分类。

### cordon 配置：接受字符串不等于控制器收到真实目录身份

[KAFKA-20901](https://issues.apache.org/jira/browse/KAFKA-20901) 10 月 29 日转 Fixed，[#23241](https://github.com/apache/kafka/pull/23241) 同日 11:37 合入 trunk。报告环境为 Kafka 4.3.1 KRaft：log.dirs 使用相对路径时，cordoned.log.dirs 填绝对路径会因字符串不相等被拒；填相对路径虽能保存，却匹配不到 LogManager 内部按绝对路径索引的 directory ID，因此控制器仍可向该磁盘放置新副本。修复把校验、动态配置和 heartbeat 传播统一到绝对路径。

这改变的是运维动作能否实际生效，不是新添另一种 cordon 策略；配置写成功、DescribeConfigs 能回读都不足以证明磁盘已经退出新分配。当前 JIRA fix version 为未发布 4.5.0，本期未核实已发布版本或其他回移，不能把测试通过写成线上版本已修复。未在该票与 PR 核实专属 KIP 关联。

### 非修复关闭要留下原因，而不是计入“修好了”

- [KAFKA-20820](https://issues.apache.org/jira/browse/KAFKA-20820) 关于 symlink log.dirs 无法格式化/启动，最终为 Won't Fix。10 月 27 日回复认为底层 JDK 修复已回移到 OpenJDK 17.0.14，应更新 JDK，无须 Kafka 再加 workaround；不能算作 Kafka 本周代码修复。
- [KAFKA-21385](https://issues.apache.org/jira/browse/KAFKA-21385) 的 CVE-2026-110952 回移请求为 Won't Do：回复说明默认 issuer/audience 检查属于 4.4 的兼容性破坏型安全强化，不回移 3.9.3。这是“不做该分支回移”，不是漏洞不存在。
- [KAFKA-21390](https://issues.apache.org/jira/browse/KAFKA-21390) 的 CVE-2026-110985 回移请求为 Not A Problem，原文理由是 3.9 不受影响；与上项理由不同。安全公告中的 affected/fixed 版本应逐条读取，不能因为都有 CVE 标签就合并解释。

### 两个反例：PR 状态不能代替 issue 状态

| 对象 | JIRA 截止状态 | 代码状态 | 本期如何计数 |
|---|---|---|---|
| [KAFKA-21349](https://issues.apache.org/jira/browse/KAFKA-21349) | Open，无 fix version | [#23943](https://github.com/apache/kafka/pull/23943) 10 月 27 日合入 trunk，[b1093f64](https://github.com/apache/kafka/commit/b1093f64c085d82c08fd6462b26a190e2eb3cb83) | 有合并证据，不增加 JIRA resolved 数 |
| [KAFKA-21380](https://issues.apache.org/jira/browse/KAFKA-21380) | Open，无 fix version | [#23995](https://github.com/apache/kafka/pull/23995) 10 月 29 日关闭、未合并 | 有方案被撤回，不增加 Fixed 数 |

21380 涉及 KIP-1191 的 DLQ 失败路径，但[维护者解释](https://github.com/apache/kafka/pull/23995#issuecomment-6477981433)该直接 ARCHIVED 转移是为避免 persister 多次失败后再以相同 partition key 写 ARCHIVING，导致队列继续卡住。作者[接受并关闭 PR](https://github.com/apache/kafka/pull/23995#issuecomment-6486791868)，明确保留 JIRA，可能另做 metric/log。本期只补生命周期证据，不重复前一天观察稿中的完整 DLQ 机制；既不能把提议当最终修复，也不能把 open issue 当所有原始指控都已获认可。

实现复核链接：[TLS 合并提交](https://github.com/apache/kafka/commit/330318de73c169f526069e33803fdc9f28af5a9c)；[cordon 合并提交](https://github.com/apache/kafka/commit/a2b91b7694762e886be25d9a31591321c0d8313c)。两项 PR 未返回行内评审评论，本次依据完整 PR 正文与已合并元数据描述实现；进一步读取 changed-files 补丁返回 HTTP 403，未完成逐行补丁复核；cordon 的[合并后评论](https://github.com/apache/kafka/pull/23241#issuecomment-6495634446)只是提出后续删除非绝对路径 getter，不是本期已完成事项。

安全版本交叉核验以 [Kafka 官方 CVE 列表](https://kafka.apache.org/community/cve-list/)为准：CVE-2026-110952 与 CVE-2026-110985 的受影响范围、默认配置条件和修复版本不同。前者列出的 fixed version 为 4.4.0，后者列出 4.2.2、4.3.1、4.4.0。上述关闭分类不应被简化成同一种“安全补丁回移完成”。

## 回移闭环：合入维护分支仍不是进入已发布补丁版

本期窗口从 10 月 24 日开始。按官网公告页日期，已发布的 [4.4.0（10 月 22 日）](https://kafka.apache.org/blog/2026/10/22/apache-kafka-4.4.0-release-announcement/)、[4.3.2（10 月 23 日）](https://kafka.apache.org/blog/2026/10/23/apache-kafka-4.3.2-release-announcement/) 和 [4.2.2（9 月 29 日）](https://kafka.apache.org/blog/2026/09/29/apache-kafka-4.2.2-release-announcement/) 都早于本期。下表记录的 10 月 25–30 日回移，不能反向算入这些既有发行包。JIRA 4.4.0 版本元数据的 releaseDate 则为 10 月 26 日，与官网公告页日期不同，本文不将两者默认为同一事件；无论采用哪个日期，都不能仅靠版本名称断言包含某次回移。判断发行包含关系仍需具体提交或发行说明证据。本次没有核实到包含它们的新补丁发行版；JIRA 的 fixVersion 是目标，不是发布证明。

KAFKA-21255 的重要闭环是上期因旧分支回移需要而重开的 ticket，本期重新解决，并落下 4.3 的独立回移 PR。它修复丢失 Streams heartbeat 响应后，重试仍不携带完整 assignment 的问题，属于已有 Streams 协议实现缺陷，不是本周重新实现一个 KIP。4.3 的适配明确保留该分支既有 endpoint cache 和 epoch 更新条件，不能简单把 trunk diff 原样复制。

KAFKA-21230 则是 KIP-892 已有实现的内存边界修复：两个 trunk PR 分别覆盖普通处理循环和独立 executor，维护者分别明确报告 cherry-pick 至 4.4；本次补查分支提交列表遇到 HTTP 403，因此 4.4 的独立提交 SHA 没有再次核到，下表保留“维护者确认”的证据等级，不把 trunk SHA 冒充回移 SHA。

| 问题 / PR | 实际目标分支 | 合并时间 UTC | 合并提交 | 截止时结论 |
|---|---|---|---|---|
| [KAFKA-21255 / #23970](https://github.com/apache/kafka/pull/23970) | 4.3 | 2026-10-28 16:01:22 | [682fe10b28](https://github.com/apache/kafka/commit/682fe10b28a35be295c20304073f107884a72c07) | 已合并；未核实新发行包含 |
| [KAFKA-21230 / #23728](https://github.com/apache/kafka/pull/23728) | trunk | 2026-10-27 16:15:09 | [0acc8008cb](https://github.com/apache/kafka/commit/0acc8008cb81397cb17664a0399f0b7b305258db) | 已合并；未核实新发行包含 |
| [KAFKA-21230 / #23984](https://github.com/apache/kafka/pull/23984) | trunk | 2026-10-29 19:42:24 | [14ee92ca1e](https://github.com/apache/kafka/commit/14ee92ca1ecf469eb8f006abf7b75453513cac49) | 已合并；未核实新发行包含 |
| [KAFKA-21234 / #23938](https://github.com/apache/kafka/pull/23938) | 4.4 | 2026-10-25 13:34:00 | [72de69ccdc](https://github.com/apache/kafka/commit/72de69ccdcd72ac59ef1db2b1848179b8c1ac5c6) | 已合并；未核实新发行包含 |
| [KAFKA-21234 / #23939](https://github.com/apache/kafka/pull/23939) | 4.3 | 2026-10-25 13:34:14 | [40cd922dbd](https://github.com/apache/kafka/commit/40cd922dbd405118110da6b11cf219aeccbf3ab2) | 已合并；未核实新发行包含 |
| [KAFKA-21234 / #23940](https://github.com/apache/kafka/pull/23940) | 4.2 | 2026-10-25 13:35:30 | [365f6651db](https://github.com/apache/kafka/commit/365f6651db30d3cc53482b2bceffe29946b48faf) | 已合并；未核实新发行包含 |
| [KAFKA-21234 / #23941](https://github.com/apache/kafka/pull/23941) | 3.9 | 2026-10-25 13:35:22 | [7d07ebf697](https://github.com/apache/kafka/commit/7d07ebf69794895a9cbf8ae1750a8bb469ab59d8) | 已合并；未核实新发行包含 |
| [KAFKA-21324 / #23900](https://github.com/apache/kafka/pull/23900) | 4.3 | 2026-10-28 04:33:44 | [2379fdd372](https://github.com/apache/kafka/commit/2379fdd3727a4ad04a95142091b2dcffb8b846d3) | 已合并；未核实新发行包含 |
| [KAFKA-21324 / #23901](https://github.com/apache/kafka/pull/23901) | 4.2 | 2026-10-28 04:34:24 | [04071f2a52](https://github.com/apache/kafka/commit/04071f2a527dc750c0b2a22d171587f861966268) | 已合并；未核实新发行包含 |
| [KAFKA-21324 / #23902](https://github.com/apache/kafka/pull/23902) | 4.1 | 2026-10-28 04:34:15 | [6cbcf52749](https://github.com/apache/kafka/commit/6cbcf527493c7f688487bbf3fe2b3271081dda3d) | 已合并；未核实新发行包含 |
| [KAFKA-21324 / #23903](https://github.com/apache/kafka/pull/23903) | 4.0 | 2026-10-28 04:34:02 | [b1ddd4eb55](https://github.com/apache/kafka/commit/b1ddd4eb555b84347d03ef9ddf75f63c3ba9a347) | 已合并；未核实新发行包含 |
| [KAFKA-21324 / #23916](https://github.com/apache/kafka/pull/23916) | 3.9 | 2026-10-28 04:33:25 | [7dbea6cf86](https://github.com/apache/kafka/commit/7dbea6cf86a9a5b31f3449c0850d001149887aa5) | 已合并；未核实新发行包含 |
| [Bound array and tagged-field allocation in generated message readers / #24018](https://github.com/apache/kafka/pull/24018) | 3.9 | 2026-10-30 07:05:22 | [8b83b92fd1](https://github.com/apache/kafka/commit/8b83b92fd1c06bcedbb6f658dad33e35f9f16820) | 已合并；未核实新发行包含 |
| [OAuth issuer/audience 回移 / #24017](https://github.com/apache/kafka/pull/24017) | 3.9 | 未合并；2026-10-29T17:10:19Z 关闭 | — | 因破坏兼容性不回移，非 Fixed |

KAFKA-21230 的 4.4 回移声明分别见 [10 月 27 日维护者回复](https://github.com/apache/kafka/pull/23728#issuecomment-6448002057) 和 [10 月 29 日维护者回复](https://github.com/apache/kafka/pull/23984#issuecomment-6507110226)。KAFKA-21234 修复已在上期介绍，本期新增是四个维护分支的实际合并；KAFKA-21324 的 WindowKeyQuery 时间参数顺序问题在 trunk 已随 KAFKA-20705 修正，本周是五个旧分支回移，不能重复统计为五个独立缺陷。

安全问题也不能一概写成“回移已完成”。[#24018](https://github.com/apache/kafka/pull/24018) 把协议数组与 tagged-field 分配限制带入 3.9 分支；[#24017](https://github.com/apache/kafka/pull/24017) 则关闭而未合并。后者会改变 OAuth 校验的默认启动行为，维护者认为 3.9.3 的补丁兼容承诺不适合这种硬化，作者明确标记 3.9 不做。[兼容性异议](https://github.com/apache/kafka/pull/24017#discussion_r4414302125) · [决定与作者接受](https://github.com/apache/kafka/pull/24017#discussion_r4415025892)。应结合具体 CVE 的受影响范围与配置要求核验，不能用“最新补丁”替代逐条判断。

## 下一步需要什么证据

- KAFKA-21402 需要失败加载不得安装部分缓存的实际补丁、错误出口回归测试和清晰的加载失败信号，而不是只重试 coordinator。
- KAFKA-21363 需要验证 punctuator-only 事务的成员所有权检查及旧 broker 兼容，不能把缩短心跳超时当成消除竞态的证明。
- KAFKA-21367 与 KAFKA-21397 分别需要覆盖两类截断、并发 checkpoint，以及不可拆 batch 与请求/带宽配额交互的测试。
- 已合入主干的 TLS、cordon、加载屏障等应继续按具体回移提交和发行记录核验。JIRA fixVersions、分支已有代码、发行包已含修复是三种不同证据。

本文未独立运行 Kafka 复现或性能测试。作者报告、评审判断与本文分析已分别标出；没有以模型运行生成性能数值或社区共识。对 KIP 的关联只采用原文明确证据；未来需要 KIP，不等于已有 KIP 获批。

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

## 附录：逐项可核查清单

官方标题原样保留。版本字段见随包 CSV，只表示 JIRA 标签，不证明正式发行。每项按 issue 去重，新增与解决可同时出现；未出现 Duplicate、Invalid、Cannot Reproduce 或重开，不代表这些类别在历史上不存在。

| Issue | 官方标题 | 本期事件 | 截点状态 / resolution |
|---|---|---|---|
| [KAFKA-18574](https://issues.apache.org/jira/browse/KAFKA-18574) | Quarantined test list should be sorted | 2026-10-25 Fixed | Resolved / Fixed |
| [KAFKA-20125](https://issues.apache.org/jira/browse/KAFKA-20125) | Improve the docs of dynamic-only configurations | 2026-10-29 Fixed | Resolved / Fixed |
| [KAFKA-20820](https://issues.apache.org/jira/browse/KAFKA-20820) | Broker fails to start when log.dirs is a symbolic link | 2026-10-27 Won't Fix | Resolved / Won't Fix |
| [KAFKA-20866](https://issues.apache.org/jira/browse/KAFKA-20866) | Remove incremental-only fields from RecordAppendResult | 2026-10-28 Fixed | Resolved / Fixed |
| [KAFKA-20901](https://issues.apache.org/jira/browse/KAFKA-20901) | [KRaft] cordoned.log.dirs is accepted but not enforced when log.dirs uses a relative path | 2026-10-29 Fixed | Resolved / Fixed |
| [KAFKA-20981](https://issues.apache.org/jira/browse/KAFKA-20981) | Kafka Streams should handle unknown status code pro-actively | 2026-10-30 Fixed | Resolved / Fixed |
| [KAFKA-21099](https://issues.apache.org/jira/browse/KAFKA-21099) | CVE-2026-90559 snappy-java vulnerability | 2026-10-29 Fixed | Resolved / Fixed |
| [KAFKA-21214](https://issues.apache.org/jira/browse/KAFKA-21214) | Spread every topic over its subscribers, without rack awareness | 2026-10-28 Fixed | Resolved / Fixed |
| [KAFKA-21230](https://issues.apache.org/jira/browse/KAFKA-21230) | Long rebalances can cause OOM errors with transactional state stores enabled | 2026-10-27 Fixed | Resolved / Fixed |
| [KAFKA-21251](https://issues.apache.org/jira/browse/KAFKA-21251) | kafka-streams-groups.sh --describe --topology: global store sub-topology label can collide with a real subtopology id | 2026-10-26 Fixed | Resolved / Fixed |
| [KAFKA-21255](https://issues.apache.org/jira/browse/KAFKA-21255) | Streams heartbeat retry responses can omit assignments after response loss | 2026-10-27 Fixed | Resolved / Fixed |
| [KAFKA-21292](https://issues.apache.org/jira/browse/KAFKA-21292) | Update docs of MockConsumer to use RebalanceListener | 2026-10-26 Fixed | Resolved / Fixed |
| [KAFKA-21297](https://issues.apache.org/jira/browse/KAFKA-21297) | Refactor the maybeUpdateLimitOffsetsForStandbyChangelogs | 2026-10-27 Fixed | Resolved / Fixed |
| [KAFKA-21324](https://issues.apache.org/jira/browse/KAFKA-21324) | Wrong parameter order in private ctor of WindowKeyQuery | 2026-10-28 Fixed | Resolved / Fixed |
| [KAFKA-21341](https://issues.apache.org/jira/browse/KAFKA-21341) | SslTransportLayer does not report a disconnect when the peer sends close_notify without a TCP FIN | 2026-10-30 Fixed | Resolved / Fixed |
| [KAFKA-21344](https://issues.apache.org/jira/browse/KAFKA-21344) | Handle partition rotate for share fetches in session | 2026-10-26 Fixed | Resolved / Fixed |
| [KAFKA-21353](https://issues.apache.org/jira/browse/KAFKA-21353) | The incorrect parameter in internal-api-checker.md breaks the site build | 2026-10-25 Fixed | Resolved / Fixed |
| [KAFKA-21354](https://issues.apache.org/jira/browse/KAFKA-21354) | kafka-metadata-quorum remove-controller output contains an extra space before "KRaft" | 新增 2026-10-26 | Open / 未解决 |
| [KAFKA-21355](https://issues.apache.org/jira/browse/KAFKA-21355) | Add a fuzzer for the uniform2 assignor | 新增 2026-10-26 | Open / 未解决 |
| [KAFKA-21356](https://issues.apache.org/jira/browse/KAFKA-21356) | Performance issue in share fetch with share group DLQ enabled. | 新增 2026-10-26 | Open / 未解决 |
| [KAFKA-21357](https://issues.apache.org/jira/browse/KAFKA-21357) | Topology optimization fails with "Found a null keyChangingChild node" on nested merges | 新增 2026-10-26 | Open / 未解决 |
| [KAFKA-21358](https://issues.apache.org/jira/browse/KAFKA-21358) | Integrate RebalanceListener/Consumer for Kafka Streams | 新增 2026-10-26 | Open / 未解决 |
| [KAFKA-21359](https://issues.apache.org/jira/browse/KAFKA-21359) | Remove ConsumerRebalanceListener/Consumer subscribe methods | 新增 2026-10-26 | Open / 未解决 |
| [KAFKA-21360](https://issues.apache.org/jira/browse/KAFKA-21360) | Heterogeneous simple share assignor keeps partitions of topics that no member subscribes to | 新增 2026-10-26 | Open / 未解决 |
| [KAFKA-21361](https://issues.apache.org/jira/browse/KAFKA-21361) | Distribution snapshots for Kafka client metrics | 新增 2026-10-26 | Open / 未解决 |
| [KAFKA-21362](https://issues.apache.org/jira/browse/KAFKA-21362) | Classic group waits for the rebalance timeout after a member is rejected with GROUP_MAX_SIZE_REACHED | 新增 2026-10-26 | Open / 未解决 |
| [KAFKA-21363](https://issues.apache.org/jira/browse/KAFKA-21363) | Streams EOS: member cut off from the group coordinator keeps committing punctuator writes unfenced, and its store diverges from the changelog after a clean restart | 新增 2026-10-26 | Open / 未解决 |
| [KAFKA-21364](https://issues.apache.org/jira/browse/KAFKA-21364) | Streams EOS: input records skipped after a commit timeout, the offset reset of the revived task is lost when the enforced rebalance closes it | 新增 2026-10-26 | Patch Available / 未解决 |
| [KAFKA-21365](https://issues.apache.org/jira/browse/KAFKA-21365) | Add separate test file to ensure the three deprecated subscribe methods are covered | 新增 2026-10-26 | Open / 未解决 |
| [KAFKA-21366](https://issues.apache.org/jira/browse/KAFKA-21366) | KIP-1388: Add a committed-offsets filter to ListGroups | 新增 2026-10-26 | Open / 未解决 |
| [KAFKA-21367](https://issues.apache.org/jira/browse/KAFKA-21367) | Stale recovery checkpoint can overwrite truncation checkpoint and skip log recovery | 新增 2026-10-27 | Open / 未解决 |
| [KAFKA-21368](https://issues.apache.org/jira/browse/KAFKA-21368) | Missing InterfaceAudience.Public annotations | 新增 2026-10-27；2026-10-30 Fixed | Resolved / Fixed |
| [KAFKA-21369](https://issues.apache.org/jira/browse/KAFKA-21369) | KafkaAdminClient calls MetricsReporter.close() twice during a single shutdown | 新增 2026-10-27 | Open / 未解决 |
| [KAFKA-21370](https://issues.apache.org/jira/browse/KAFKA-21370) | Return STREAMS_INVALID_TOPOLOGY_EPOCH instead of INVALID_REQUEST for topology epoch mismatches in streams groups | 新增 2026-10-27；2026-10-30 Fixed | Resolved / Fixed |
| [KAFKA-21371](https://issues.apache.org/jira/browse/KAFKA-21371) | The docs of partitioner.rack.aware should mention partitioner.ignore.keys and client.rack | 新增 2026-10-27 | Open / 未解决 |
| [KAFKA-21372](https://issues.apache.org/jira/browse/KAFKA-21372) | PartitionGroup#readyToProcess formats log messages on every call, and most of these messages are discarded | 新增 2026-10-27 | Open / 未解决 |
| [KAFKA-21373](https://issues.apache.org/jira/browse/KAFKA-21373) | Remove the sasl infra from UserQuotaTest | 新增 2026-10-27 | Open / 未解决 |
| [KAFKA-21374](https://issues.apache.org/jira/browse/KAFKA-21374) | Streams: reads of a global store pass the headers of the global thread's last record to the value deserializer | 新增 2026-10-27 | Open / 未解决 |
| [KAFKA-21375](https://issues.apache.org/jira/browse/KAFKA-21375) | Add per-topic metrics for bytes sent to brokers outside client.rack | 新增 2026-10-27 | Open / 未解决 |
| [KAFKA-21376](https://issues.apache.org/jira/browse/KAFKA-21376) | Move AdminUtils#fetchOrWaitForLeader to clients test fixtures and consolidate it with ClusterInstance#getLeaderBrokerId | 新增 2026-10-27 | Open / 未解决 |
| [KAFKA-21377](https://issues.apache.org/jira/browse/KAFKA-21377) | kafka-topics --under-min-isr-partitions / --at-min-isr-partitions use the raw min.insync.replicas instead of the effective value used by the broker and controller | 新增 2026-10-28 | Open / 未解决 |
| [KAFKA-21378](https://issues.apache.org/jira/browse/KAFKA-21378) | Add "leaderEpoch" field in PartitionChangeRecord | 新增 2026-10-28 | Open / 未解决 |
| [KAFKA-21379](https://issues.apache.org/jira/browse/KAFKA-21379) | Add mirror coordinator record schemas and serde | 新增 2026-10-28；2026-10-30 Fixed | Resolved / Fixed |
| [KAFKA-21380](https://issues.apache.org/jira/browse/KAFKA-21380) | Failed state-transition rollback bypasses DLQ when delivery count limit is reached | 新增 2026-10-28 | Open / 未解决 |
| [KAFKA-21381](https://issues.apache.org/jira/browse/KAFKA-21381) | Backport CVE fixes to 3.9 | 新增 2026-10-29 | In Progress / 未解决 |
| [KAFKA-21382](https://issues.apache.org/jira/browse/KAFKA-21382) | Backport fix for CVE-2026-83525 | 新增 2026-10-29；2026-10-30 Fixed | Resolved / Fixed |
| [KAFKA-21383](https://issues.apache.org/jira/browse/KAFKA-21383) | Backport fix for CVE-2026-111496 | 新增 2026-10-29；2026-10-30 Fixed | Resolved / Fixed |
| [KAFKA-21384](https://issues.apache.org/jira/browse/KAFKA-21384) | Backport fix for CVE-2026-115644 | 新增 2026-10-29 | Patch Available / 未解决 |
| [KAFKA-21385](https://issues.apache.org/jira/browse/KAFKA-21385) | Backport fix for CVE-2026-110952 | 新增 2026-10-29；2026-10-29 Won't Do | Resolved / Won't Do |
| [KAFKA-21386](https://issues.apache.org/jira/browse/KAFKA-21386) | Backport fix for CVE-2026-111073 | 新增 2026-10-29；2026-10-29 Fixed | Resolved / Fixed |
| [KAFKA-21387](https://issues.apache.org/jira/browse/KAFKA-21387) | Backport fix for CVE-2026-116593 | 新增 2026-10-29 | Patch Available / 未解决 |
| [KAFKA-21388](https://issues.apache.org/jira/browse/KAFKA-21388) | Doc doesn't have upgrading steps | 新增 2026-10-29 | Patch Available / 未解决 |
| [KAFKA-21389](https://issues.apache.org/jira/browse/KAFKA-21389) | ASSIGNMENT_DELAYED stops processing of tasks a streams member already owns | 新增 2026-10-29 | Patch Available / 未解决 |
| [KAFKA-21390](https://issues.apache.org/jira/browse/KAFKA-21390) | Backport fix for CVE-2026-110985 | 新增 2026-10-29；2026-10-29 Not A Problem | Resolved / Not A Problem |
| [KAFKA-21391](https://issues.apache.org/jira/browse/KAFKA-21391) | Improve standby stickiness of rack-aware standby placement in the sticky task assignor | 新增 2026-10-29 | Open / 未解决 |
| [KAFKA-21392](https://issues.apache.org/jira/browse/KAFKA-21392) | Backport fix for CVE-2026-111108 | 新增 2026-10-29；2026-10-30 Fixed | Resolved / Fixed |
| [KAFKA-21393](https://issues.apache.org/jira/browse/KAFKA-21393) | KIP-919 supports for `alterClientQuotas` | 新增 2026-10-29 | Open / 未解决 |
| [KAFKA-21394](https://issues.apache.org/jira/browse/KAFKA-21394) | KIP-919 supports for `electLeaders` | 新增 2026-10-29 | Open / 未解决 |
| [KAFKA-21395](https://issues.apache.org/jira/browse/KAFKA-21395) | Backport fix for CVE-2026-111115 | 新增 2026-10-29；2026-10-30 Fixed | Resolved / Fixed |
| [KAFKA-21396](https://issues.apache.org/jira/browse/KAFKA-21396) | Kafka Streams should report active task lag when restore status changes | 新增 2026-10-29 | Patch Available / 未解决 |
| [KAFKA-21397](https://issues.apache.org/jira/browse/KAFKA-21397) | a single large batch bigger than the quota's allowed burst can stall consumers indefinitely | 新增 2026-10-30 | Open / 未解决 |
| [KAFKA-21398](https://issues.apache.org/jira/browse/KAFKA-21398) | Fix the docs of UUIDSerializer | 新增 2026-10-30；2026-10-30 Fixed | Resolved / Fixed |
| [KAFKA-21399](https://issues.apache.org/jira/browse/KAFKA-21399) | Consider adding SerializerConfigs to expose the serialization configs | 新增 2026-10-30 | Open / 未解决 |
| [KAFKA-21400](https://issues.apache.org/jira/browse/KAFKA-21400) | Consider removing copartition request normalization once client ordering is guaranteed by version compatibility requirements | 新增 2026-10-30 | Open / 未解决 |
| [KAFKA-21401](https://issues.apache.org/jira/browse/KAFKA-21401) | Streams static member rejoin with a changed process ID loses task ownership tracking and permits premature assignment | 新增 2026-10-30 | Open / 未解决 |
| [KAFKA-21402](https://issues.apache.org/jira/browse/KAFKA-21402) | Transaction coordinator installs partially loaded transaction state when loading __transaction_state fails | 新增 2026-10-30 | Open / 未解决 |
| [KAFKA-21403](https://issues.apache.org/jira/browse/KAFKA-21403) | Add --mirror-state-decoder support to kafka-dump-log.sh | 新增 2026-10-30 | Open / 未解决 |
| [KAFKA-21404](https://issues.apache.org/jira/browse/KAFKA-21404) | Add MirrorStateMessageFormatter | 新增 2026-10-30 | Open / 未解决 |
| [KAFKA-21405](https://issues.apache.org/jira/browse/KAFKA-21405) | Lift non-public config key strings into public (MirrorClientConfig) | 新增 2026-10-30 | Open / 未解决 |
| [KAFKA-21406](https://issues.apache.org/jira/browse/KAFKA-21406) | Document controller_mutation_rate metrics | 新增 2026-10-30 | Open / 未解决 |
| [KAFKA-21407](https://issues.apache.org/jira/browse/KAFKA-21407) | StreamTask spams "not ready for processing" at INFO every 2 minutes for every idle task | 新增 2026-10-30 | Open / 未解决 |
