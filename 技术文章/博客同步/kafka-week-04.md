---
title: 'Kafka / AutoMQ / Fluss 社区动态 · 周报 #4（2026-06-11）'
blog_url: https://bryantchang1992.github.io/ai_memory_chang_ai_team/posts/tech-research/week-04/kafka/
blog_source: _posts/2026-06-11-kafka-week-04.md
blog_source_commit: f83970fa7e6ad32d626cc6ca3ba7428c90a638a5
blog_body_sha256: 9a11c1fd0112e4ef41318b71ab36592a55f8ff061c4095bf9c677e41c17886ad
synced_at: '2026-10-05'
type: survey
created: '2026-06-11'
tags:
- Kafka
- AutoMQ
- Fluss
- 流处理
issue: 4
issue_date: '2026-06-11'
---

## 🔥 本周综述

> **📌 本期定位：**本周是三个项目各自进入不同节奏的一周——Kafka 进入修复密集期（37 个 PR 合并），AutoMQ 在 1.7.0 发布后密集修复 + 性能优化，Fluss 持续推进 Hudi 生态和 Tiering 文档体系建设。

本周没有重大版本发布，但三个项目的代码活跃度都维持在较高水平。Kafka 社区进行了 4.1/4.2/4.3 三条线的 bug 修复回传，其中 KIP-932（Share Groups）的 SharePartition 初始化修复尤其重要；AutoMQ 1.7.0 发布后的首个完整工作周，新增了 ETag 条件写入、Failover 性能优化、Retry Storm Backoff 等特性；Fluss 社区发布了 Tiering Service Deep Dive 系列第二篇，并持续推进 Hudi 生态的 source split planner 和 aggregation column 支持。

核心看点：

- **Kafka 37 个 PR 合并**——KIP-932 SharePartition 初始化修复、Group Coordinator 日志修复三线回传
- **AutoMQ 1.7.0 发布后首周**——API Key 鉴权修复、Failover 性能双倍优化、Retry Storm Backoff、ETag 条件写入
- **Fluss Tiering Deep Dive Part 2**——深入 Buckets/Splits 并行模型、Log vs PK 表差异、Freshness 配置调优
- **Fluss Hudi 生态加深**——Source Split Planner 引入、Aggregation Column 支持、Auto-Partition 配置变更

---

## 🐘 Apache Kafka — 37 个 PR 合并 · 修复密集期

> **📊 本周数据：**本周 Kafka 社区以 bug 修复为主，37 个 PR 合并，覆盖 4.1/4.2/4.3/trunk 四条线。没有新版本发布，没有新增 KIP 提案。目前社区仍在上期 9 个 KIP 的讨论周期中。

### 🔧 关键 Bug 修复

| PR | 标题 | 作者 | 目标分支 | 日期 |
|----|------|------|----------|------|
| [#22502](https://github.com/apache/kafka/pull/22502) | **KAFKA-20672: Retry DLQ on SharePartition init for ARCHIVING records**（KIP-932） | smjn | trunk | 6/9 |
| [#22508](https://github.com/apache/kafka/pull/22508) | KAFKA-20635: Spurious "Writing records..." errors in Group Coordinator（4.1） | dajac | 4.1 | 6/8 |
| [#22507](https://github.com/apache/kafka/pull/22507) | KAFKA-20635: Spurious "Writing records..." errors in Group Coordinator（4.2） | dajac | 4.2 | 6/8 |
| [#22506](https://github.com/apache/kafka/pull/22506) | KAFKA-20663: Fix startup state manager close to release StateDirectory task lock（4.3） | bbejeck | 4.3 | 6/8 |
| [#22525](https://github.com/apache/kafka/pull/22525) | MINOR: Update AK/KS documentation | gabriellefu | trunk | 6/9 |
| [#22500](https://github.com/apache/kafka/pull/22500) | MINOR: Truncate cluster.json when generating in ducker-ak | — | trunk | 6/8 |

> **⚡ 值得关注：**KAFKA-20635（Group Coordinator 日志错误）被三线回传（4.1/4.2/trunk），说明问题影响面较广，建议使用 4.x 的用户关注后续 patch 版本。KAFKA-20672 修复了 KIP-932 Share Groups 在 ARCHIVING 状态下的 SharePartition 初始化死信队列重试逻辑，对使用 Share Groups 的用户很重要。

### 📋 上期 9 个 KIP 持续讨论中

上期（Week 03）提出的 9 个 KIP 提案仍处于讨论阶段，暂无新投票或接受结果。重点回顾：

- **⭐ [KIP-1279 · 原生集群镜像](https://cwiki.apache.org/confluence/display/KAFKA/KIP-1279%3A+Cluster+Mirroring)** — 将跨集群复制原生集成到 Broker，替代 MirrorMaker 2
- **[KIP-1277 · 原生延迟消息](https://cwiki.apache.org/confluence/display/KAFKA/KIP-1277%3A+Support+Delayed+Message+in+Kafka)** — Producer 设置未来投递时间戳
- **[KIP-1290 · 机架感知 min ISR](https://cwiki.apache.org/confluence/display/KAFKA/KIP-1290%3A+Rack-Aware+Minimum+In-Sync+Replicas)** — 多 AZ 持久性保证
- **[KIP-1297 · KRaft Role-Aware Metrics](https://cwiki.apache.org/confluence/display/KAFKA/KIP-1297%3A+Role-Aware+Metric+Tags)**
- **[KIP-1289 · Share Group 事务确认](https://cwiki.apache.org/confluence/display/KAFKA/KIP-1289+Support+Transactional+Acknowledgments+for+Share+Groups)**
- **[KIP-1288 · 客户端 SSL 热加载](https://cwiki.apache.org/confluence/display/KAFKA/KIP-1288%3A+SSL+Hot+Reload+for+Kafka+Clients)**
- **[KIP-1282 · 分区扩展防丢数据](https://cwiki.apache.org/confluence/display/KAFKA/KIP-1282%3A+Prevent+data+loss+during+partition+expansion)**
- **[KIP-1272 · Compacted Topic 分层存储](https://cwiki.apache.org/confluence/display/KAFKA/KIP-1272%3A+Support+compacted+topic+in+tiered+storage)**
- **[KIP-1266 · RemoteLogMetadata Compacted](https://cwiki.apache.org/confluence/display/KAFKA/KIP-1266%3A+Bounding+The+Number+Of+RemoteLogMetadata+Messages)**

### 🔗 Kafka 信息来源

- [Kafka Merged PRs（本周）](https://github.com/apache/kafka/pulls?q=is%3Apr+updated%3A2026-06-04..2026-06-11+is%3Amerged)
- [KIP 索引](https://cwiki.apache.org/confluence/display/KAFKA/Kafka+Improvement+Proposals)
- [Kafka Blog](https://kafka.apache.org/blog/)

---

## ⚡ AutoMQ — 1.7.0 发布后首周 · 修复 + 性能 + 新特性

> **📊 本周数据：**AutoMQ 1.7.0 于 6 月 4 日正式发布（上期已覆盖），本周为发布后的首个完整工作周。18 个 PR 在本周有活动（3 Open + 15 Closed），主要集中在安全性修复、Failover 性能优化、S3 存储可靠性提升。

### 🔐 安全修复

- **API Key 鉴权修复（[#3411](https://github.com/AutoMQ/automq/pull/3411), [#3410](https://github.com/AutoMQ/automq/pull/3410)）：**`superhx` 提交，为 AutoMQ 自定义 API Key 增加了完整的鉴权逻辑。此前 AutoMQ 的自定义 API（如 RouterChannel、NamespaceKV 等）可能绕过标准 Kafka 鉴权链路，这是一个重要的安全加固。**建议所有 1.7.0 用户关注此修复。**

### ⚡ 性能优化

- **Failover 加速（[#3406](https://github.com/AutoMQ/automq/pull/3406)）：**`superhx` 提交了一系列 Failover 优化，显著降低 Broker 故障恢复的延迟。
- **Failover 延迟优化（[#3412](https://github.com/AutoMQ/automq/pull/3412)）** — `echooymxq` 提交，进一步降低 Failover 延迟（Open 状态，尚未合并）。
- **Retry Storm Backoff（[#3405](https://github.com/AutoMQ/automq/pull/3405)）：**`superhx` 提交，为重试风暴场景增加退避机制。当系统遇到级联失败时，避免大量客户端同时重试造成的"重试风暴"，这是分布式系统常见的稳定性增强。
- **S3WAL Upload 批量优化（[#3407](https://github.com/AutoMQ/automq/pull/3407)）：**`superhx` 提交，通过批量 objectId 的方式优化 WAL 上传准备阶段，减少 S3 API 调用次数。

### 🏗️ 新特性

- **S3 ETag 条件写入（[#3413](https://github.com/AutoMQ/automq/pull/3413)）：**`Gezi-lzq` 提交（Open），引入基于 S3 ETag 的条件对象预留写入。利用 S3 的 ETag 机制（HTTP If-Match header）做乐观并发控制，在并发写入场景下避免对象覆盖，是 S3 存储层可靠性的重要提升。
- **Proto Source Jar 依赖声明（[#3409](https://github.com/AutoMQ/automq/pull/3409), [#3408](https://github.com/AutoMQ/automq/pull/3408)）：**`Gezi-lzq` 修复 Maven 构建中 proto 源码 jar 的依赖声明问题，提升构建确定性。

> **🔔 关注点：**本周 #3411 的 API Key 鉴权修复值得重点跟踪。AutoMQ 的 1.7.0 引入了大量自定义 API（集群事件框架、命名空间 KV、RouterChannel 纪元查询等），如果这些 API 缺少鉴权，在生产环境可能构成安全风险。此外，#3405 的 Retry Storm Backoff 和 #3413 的 ETag 条件写入是两个涉及核心可靠性的 PR，建议在后续 patch 版本中关注其合入进度。

### 🔗 AutoMQ 信息来源

- [AutoMQ PRs（本周）](https://github.com/AutoMQ/automq/pulls?q=is%3Apr+updated%3A2026-06-04..2026-06-11)
- [AutoMQ 1.7.0 Release](https://github.com/AutoMQ/automq/releases/tag/1.7.0)
- [AutoMQ GitHub](https://github.com/AutoMQ/automq)

---

## 🌊 Apache Fluss — Tiering Deep Dive Part 2 · Hudi 生态深入

> **📊 本周数据：**42 个 PR 在本周范围内有活动（24 Open + 18 Closed）。Fluss 本周的核心叙事围绕 Tiering 文档体系建设和 Hudi 生态深入展开——既有一篇高质量的 Tiering Service Part 2 博客，又有 Hudi Source Split Planner 引入和 Aggregation Column 支持的代码推进。

### 📝 新博客：Tiering Service Deep Dive Part 2: Tuning（6月9日）

polyzos（PPMC）于 6 月 9 日发布了 [Tiering Service 深度剖析系列第二篇](https://fluss.apache.org/blog/fluss-tiering-service-deep-dive-part2/)，在第一篇（6月4日）建立心智模型的基础上，本篇聚焦**调优**。核心内容：

- **Buckets & Splits 并行模型：**每个 Bucket 对应一个 Split，Splits 数量 = Buckets 数量。Readers 数（Flink 并行度）多于 Buckets 时：多余 Readers 处理其他表的 Splits；少于 Buckets 时：每个 Reader 顺序处理多个 Splits。
- **Slow-Bucket 效应：**最慢的 Bucket 决定一轮 Tiering 的耗时，Splits 随机排列以摊平热点。
- **Log vs PK 表的关键差异：**PK 表的首轮 Tiering 需要复制整个 KV State（可能高达 200 GB），而后续轮次只需处理增量 Changelog。这是理解 PK 表 Tiering 成本的核心。
- **Freshness 配置的双重角色：**`table.datalake.freshness` 同时控制轮次间隔和超时强制完成，是多表场景下最容易产生困惑的配置项。
- **多表队列位置主导 Freshness：**当单个 Flink Job 处理多张表时，队列位置对实际 Freshness 的影响可能超过任何单表配置。
- **Scale-Out 决策：**从单 Job 到多 Job 的扩展决策框架。

> **💡 推荐阅读：**这篇博客是生产环境部署 Fluss Lake Tiering 的必读材料。它填补了"知道 Tiering 怎么工作"和"知道 Tiering 怎么调优"之间的空白。结合 Part 1 的架构讲解，两篇加起来是目前 Fluss 社区最好的 Tiering 实战指南。

### 🏷️ 本周关键 PR

| PR | 标题 | 作者 | 状态 | 说明 |
|----|------|------|------|------|
| [#3456](https://github.com/apache/fluss/pull/3456) | 🔥 **[lake/hudi] Introduce Hudi source split planner** | fhan688 | Open | Hudi Lake Source 的 Split Planner 实现，支持 COW/MOR 表的 split 规划，将 Fluss bucket/partition 元数据持久化到 Hudi table properties 中。这是继上期 #3395 Hudi LakeCatalog 合并后的关键下一步 |
| [#3459](https://github.com/apache/fluss/pull/3459) | **[client][server] Support adding aggregation columns** | wzx140 | Open | 支持通过 ALTER TABLE ADD COLUMN 传递聚合函数，为 aggregation merge engine 表增加聚合列能力 |
| [#3453](https://github.com/apache/fluss/pull/3453) | **[server] Support altering auto partition enabled option** | fhan688 | Open | 支持动态变更自动分区配置，提升表生命周期管理的灵活性 |
| [#3458](https://github.com/apache/fluss/pull/3458) | **[server] Allow altering datalake auto-compaction before lake enabled** | wzx140 | Open | 允许在 Lake 功能启用前配置 datalake auto-compaction，改善运维流程 |
| [#3449](https://github.com/apache/fluss/pull/3449) | **[lake] Stabilize Paimon tiering IT** | zerolbsony | Open | 稳定化 Paimon Tiering 集成测试 |
| [#3450](https://github.com/apache/fluss/pull/3450) | **[test] Fix ComponentClassLoaderTest tmpdir path handling** | litiliu | ✅ Merged | 测试修复，6月9日合并 |
| [#3448](https://github.com/apache/fluss/pull/3448) | **[metrics] Fix typo in scanner metric name** | charlesdong1991 | ✅ Merged | 指标名称拼写修复，6月9日合并 |
| [#3447](https://github.com/apache/fluss/pull/3447) | **[client] Enum conversion functionality for typed writer/reader** | VladBanar | Open | 为类型化 Writer/Reader 增加枚举转换支持，提升多语言 SDK 的类型安全性 |

### 📈 上期里程碑 PR 进展追踪

| PR | 标题 | 上期状态 | 本周状态 |
|----|------|----------|----------|
| [#3401](https://github.com/apache/fluss/pull/3401) | FIP-40: merge fluss-rust | Open | 仍 Open（持续评审中） |
| [#3430](https://github.com/apache/fluss/pull/3430) | TieringSourceReader scan arrow + write to lake | Open | 仍 Open |
| [#3400](https://github.com/apache/fluss/pull/3400) | Cluster Health API | Open（🔴 blocker） | 仍 Open |
| [#3429](https://github.com/apache/fluss/pull/3429) | RebalanceManager 超时保护 | Open | 仍 Open |

### 🔗 Fluss 信息来源

- [Tiering Service Deep Dive Part 2](https://fluss.apache.org/blog/fluss-tiering-service-deep-dive-part2/)
- [Fluss PRs（本周）](https://github.com/apache/fluss/pulls?q=updated:2026-06-04..2026-06-11)
- [Fluss GitHub](https://github.com/apache/fluss)
- [Fluss Blog](https://fluss.apache.org/blog/)

---

## 📊 趋势观察

### 一、Kafka：从"发布驱动"切换到"修复密集"模式

上期（Week 03）的叙事是"4.3.0 发布 + 9 个新 KIP"，本周则完全是修复密集期——37 个 PR 合并，且三条稳定线（4.1/4.2/4.3）同时回传修复。这反映了一个健康的社区节奏：大版本发布后，用 2-3 周集中修复回归问题，然后再进入下一个 KIP 的实现周期。KIP-932（Share Groups）的持续修复表明这个特性在生产环境的使用正在加深，暴露了更多边界情况。

### 二、AutoMQ 1.7.0 发布后的"补丁周"

1.7.0 发布后的首个完整工作周，代码活动聚焦在三个方向：（1）安全性——API Key 鉴权修复；（2）性能——Failover 加速、Retry Storm Backoff、S3WAL 批量优化；（3）可靠性——ETag 条件写入。这三个方向的优先级排序是合理的：安全 > 性能 > 新特性。特别值得关注的是 API Key 鉴权问题——如果确实存在鉴权绕过，这属于高优先级修复。

### 三、Fluss：从"广度扩张"转向"深度建设"

上期 Fluss 的特征是"广度扩张"——63 个活跃 PR、多语言 SDK 合仓、三大 Lake Format 支持全面推进。本周的数据（42 个活跃 PR）有所回落，但方向更加聚焦：

- **文档体系建设：**Tiering Service Deep Dive 系列是一个高质量的技术文档工程。三篇（Part 1 已发、Part 2 本周发布、Part 3 预告在生产环境实践）覆盖了从概念到调优再到运维的完整链路。这种深度的文档对开源项目吸引企业用户至关重要。
- **Hudi 生态深入：**从 #3395（LakeCatalog）到 #3456（Split Planner），Fluss 对 Hudi 的支持正在从"能建表"到"能读数据"演进。如果结合 Paimon（Arrow 列存写入）和 Iceberg 的已有支持，Fluss 正在成为唯一一个同时对三大 Lake Format 提供标准 Streaming Layer 的项目。
- **Aggregation 能力：**#3459 的聚合列支持表明 Fluss 在增强其作为"流式计算存储层"的能力，不再仅仅是 append-only log 或 key-value store。

### 四、本周数据对比

| 指标 | Apache Kafka | AutoMQ | Apache Fluss |
|------|-------------|--------|--------------|
| 新版本 | 无 | 无（1.7.0 已于 6/4 发） | 无 |
| 活跃 PR 数 | 37 Merged | 18（3 Open + 15 Closed） | 42（24 Open + 18 Closed） |
| 新提案/KIP | 0（上期 9 个讨论中） | — | — |
| 新博客 | 0 | 0 | 1（Tiering Deep Dive #2） |
| 社区节奏 | 修复密集期 | 版本后补丁+优化 | 文档+生态深度建设 |

### 五、下期关注点

- **Kafka：**KAFKA-20635（Group Coordinator 错误）三线回传后是否有 4.2.2/4.1.3 patch 发布；9 个 KIP 的投票进展
- **AutoMQ：**API Key 鉴权修复的 patch 版本；ETag 条件写入和 Retry Storm Backoff 的合入
- **Fluss：**Tiering Service Deep Dive Part 3（生产环境实践）的发布；FIP-40（fluss-rust 合仓）的最终合入

---

## 🔗 参考链接

### 🐘 Apache Kafka

- [Kafka Merged PRs（本周 37 个）](https://github.com/apache/kafka/pulls?q=is%3Apr+updated%3A2026-06-04..2026-06-11+is%3Amerged)
- [#22502 · KAFKA-20672 SharePartition DLQ Retry（KIP-932）](https://github.com/apache/kafka/pull/22502)
- [#22508 · KAFKA-20635 Group Coordinator Error（4.1）](https://github.com/apache/kafka/pull/22508)
- [#22507 · KAFKA-20635 Group Coordinator Error（4.2）](https://github.com/apache/kafka/pull/22507)
- [#22506 · KAFKA-20663 StateDirectory Task Lock（4.3）](https://github.com/apache/kafka/pull/22506)
- [KIP-1279 · 原生集群镜像](https://cwiki.apache.org/confluence/display/KAFKA/KIP-1279%3A+Cluster+Mirroring)
- [KIP-1277 · 原生延迟消息](https://cwiki.apache.org/confluence/display/KAFKA/KIP-1277%3A+Support+Delayed+Message+in+Kafka)
- [KIP-1290 · 机架感知 min ISR](https://cwiki.apache.org/confluence/display/KAFKA/KIP-1290%3A+Rack-Aware+Minimum+In-Sync+Replicas)
- [KIP 索引](https://cwiki.apache.org/confluence/display/KAFKA/Kafka+Improvement+Proposals)
- [Kafka Blog](https://kafka.apache.org/blog/)

### ⚡ AutoMQ

- [AutoMQ 1.7.0 Release Notes](https://github.com/AutoMQ/automq/releases/tag/1.7.0)
- [#3411 · API Key 鉴权修复](https://github.com/AutoMQ/automq/pull/3411)
- [#3413 · S3 ETag 条件写入](https://github.com/AutoMQ/automq/pull/3413)
- [#3412 · Failover 延迟优化](https://github.com/AutoMQ/automq/pull/3412)
- [#3406 · Failover 加速](https://github.com/AutoMQ/automq/pull/3406)
- [#3405 · Retry Storm Backoff](https://github.com/AutoMQ/automq/pull/3405)
- [#3407 · S3WAL Upload 批量优化](https://github.com/AutoMQ/automq/pull/3407)
- [AutoMQ PRs（本周全部）](https://github.com/AutoMQ/automq/pulls?q=is%3Apr+updated%3A2026-06-04..2026-06-11)

### 🌊 Apache Fluss

- [Tiering Service Deep Dive Part 2: Tuning](https://fluss.apache.org/blog/fluss-tiering-service-deep-dive-part2/)
- [Tiering Service Deep Dive Part 1: The Mental Model](https://fluss.apache.org/blog/fluss-tiering-service-deep-dive-part1/)
- [Storage Hierarchy: Hot, Remote, and Lake](https://fluss.apache.org/blog/fluss-storage-hierarchy/)
- [#3456 · Hudi Source Split Planner](https://github.com/apache/fluss/pull/3456)
- [#3459 · Aggregation Columns 支持](https://github.com/apache/fluss/pull/3459)
- [#3453 · Auto Partition 配置变更](https://github.com/apache/fluss/pull/3453)
- [#3401 · FIP-40 fluss-rust 合仓（追踪中）](https://github.com/apache/fluss/pull/3401)
- [#3430 · Arrow 列存 Paimon 写入](https://github.com/apache/fluss/pull/3430)
- [Fluss PRs（本周）](https://github.com/apache/fluss/pulls?q=updated:2026-06-04..2026-06-11)

---

*CHANG_AI_TEAM · 技术调研 · 调研周期：2026-06-04 ~ 2026-06-11（第 24 周 · 第 4 期）*  
*本报告基于 GitHub PR 和项目官网博客的公开信息整理。所有链接均可点击直达原文。*
