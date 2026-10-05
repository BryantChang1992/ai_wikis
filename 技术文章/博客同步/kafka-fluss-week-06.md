---
title: Kafka / AutoMQ / Fluss 社区动态 — Week 06
blog_url: https://bryantchang1992.github.io/ai_memory_chang_ai_team/posts/tech-research/week-06/kafka-fluss/
blog_source: _posts/2026-06-18-kafka-fluss-week-06.md
blog_source_commit: f83970fa7e6ad32d626cc6ca3ba7428c90a638a5
blog_body_sha256: f63875530481af6367b4107e306a3a3b68e2950f6c83cb327dc71f151e98d791
synced_at: '2026-10-05'
type: survey
created: '2026-06-18'
tags:
- Kafka
- AutoMQ
- Fluss
- kip
- kraft
- stream-processing
- lake-storage
issue: 6
issue_date: '2026-06-18'
---

> 采集时间：2026-06-18 14:15 CST

---

## Apache Kafka

### KIP-1359: Improve usability of resetting group offsets

📎 [KIP-1359](https://cwiki.apache.org/confluence/display/KAFKA/KIP-1359)

Andrew Schofield 提出的改进 consumer group offset 重置可用性的提案，6/18 仍在活跃讨论。

🏷️ `KIP` `Consumer Group` `Usability`

---

### KIP-1358: Gradual and gated preferred-leader election in the KRaft controller

📎 [KIP-1358](https://cwiki.apache.org/confluence/display/KAFKA/KIP-1358)

Haifeng Chen 提出的 KRaft controller 渐进式 preferred leader 选举方案，6/18 活跃讨论。意在降低大规模集群中 leader 切换的风险和影响面。

🏷️ `KIP` `KRaft` `Leader Election`

---

### KIP-1357: Add broker side custom assignors for "streams" groups

📎 [KIP 页面](https://cwiki.apache.org/confluence/pages/viewpage.action?pageId=430408758)

Gabriella Fu 提出的为 Streams group 添加 broker 侧自定义 assignor 的 KIP，6/17 活跃讨论。

🏷️ `KIP` `Kafka Streams` `Consumer Group`

---

### KIP-1356: Introduce IQv2 for headers-aware state stores

📎 [KIP-1356](https://cwiki.apache.org/confluence/display/KAFKA/KIP-1356)

Jess Jin 提出的为 headers-aware state stores（KIP-1271）引入 Interactive Query v2 支持，6/18 活跃讨论。进一步推动 Kafka Streams 的状态查询能力升级。

🏷️ `KIP` `Kafka Streams` `State Store` `Interactive Query`

---

### Kafka 4.3.0 发布后续：Gravitee 深度解读

📎 [Gravitee Blog](https://www.gravitee.io/blog/apache-kafka-news-2026_whats-next)

Gravitee 6/15 发布 Kafka 2026 全景分析，涵盖 4.x 系列关键决策点：

- **KRaft 迁移**：ZooKeeper 在 4.x 中已完全消除（非 deprecated），3.x 集群必须完成 KRaft 迁移后才能升级
- **KIP-932 Share Groups**：替代传统消息队列的关键特性
- **Tiered Storage** 成熟度评估

面向 CTO/平台负责人的决策参考，建议尽早规划 KRaft 迁移路径。

🏷️ `KRaft Migration` `KIP-932` `Tiered Storage` `Platform Decision`

---

### Kafka-Nated Espresso May 2026：Current Summit + 社区动态

📎 [Substack](https://getkafkanated.substack.com/p/get-kafka-nated-espresso-may-2026)

Hugh Evans 的 5 月 Kafka 月报亮点：

- **Current Summit** 在伦敦 ExCeL 举办
- **Sean Quah** 被宣布为新的 Apache Kafka Committer
- **KIP-1276**（CIDR-based ACL）和 **KIP-1306**（ConsumerRebalanceListener 扩展）投票通过
- **KIP-1279**（Cluster Mirroring）仍在活跃讨论中，预计进入 4.4
- 特别提及 **Fluss** 在 Fresha 团队的 EKS 生产实践

🏷️ `Community` `Current Summit` `KIP-1276` `KIP-1279` `Committer`

---

### Red Hat Kafka Monthly Digest: May 2026（第100期）

📎 [Red Hat Developer Blog](https://developers.redhat.com/blog/2026/06/02/kafka-monthly-digest-may-2026)

Red Hat 发布 Kafka 月报第 **100 期**里程碑，回顾 2026 年 5 月 Apache Kafka 社区动态。

🏷️ `Monthly Digest` `Red Hat` `Milestone`

---

## AutoMQ

### AutoMQ 1.7.0 正式发布 🚀

📎 [GitHub Releases](https://github.com/AutoMQ/automq/releases/tag/1.7.0)

对比 1.6.5 包含 **40+ PR**，本周最大事件。关键特性：

| 特性 | 说明 |
|------|------|
| **Namespace 支持** | 为 KV Store 和 devkit 添加多实例隔离的 namespace 能力 |
| **Cluster Events Framework** | 基于 Protobuf 的集群事件发布框架 |
| **Autoscaling 指标** | 暴露 broker 资源统计信息用于自动扩缩容 |
| **Fetch Listener Callbacks** | 支持异步 inter-broker 请求和 fetch 回调 |
| **QuorumControllerExtension 生命周期** | 添加 activate/deactivate 钩子 |
| **Maven Snapshot 发布** | 首次发布 Maven snapshot 包 |

**Bug 修复**：修复 S3 并发写入异常（OCI）、LogCache 双重释放竞争、DataBlockIndex int overflow 导致 compaction 数据丢失等关键问题。E2E 稳定性方面，1.7 系列 MirrorMaker、Connect、Streams 的 E2E 测试全面加固。

🏷️ `Release` `1.7.0` `Namespace` `Autoscaling` `Cluster Events`

---

## Apache Fluss (Incubating)

### FLUSS-3483: Validate lake snapshot offsets before commit

📎 [PR #3494](https://github.com/apache/fluss/pull/3494)

Jackeyzhe 6/18 提交：修复表 drop 后重建导致的 stale V2 lake snapshot commit 竞争条件。新表可能指向旧 tableId 的 offsets metadata，导致 lake tiering 反复失败。PR 在 commit 前校验 tableId、offsets 可读性和 TableBucket 一致性。

🏷️ `PR` `Lake Storage` `Bug Fix` `Coordinator`

---

### Server/Client: Cooperative KV backpressure based on RocksDB L0

📎 [PR #3463](https://github.com/apache/fluss/pull/3463)

6/10 创建，6/17 仍在活跃讨论。为 KV 存储引入基于 RocksDB L0 文件数的协同背压机制，防止写入过快导致 compaction 积压。

🏷️ `PR` `KV Store` `RocksDB` `Backpressure`

---

### Security: Redact sensitive config values in startup logs

📎 [PR #3486](https://github.com/apache/fluss/pull/3486)

6/15 创建，6/17 更新。安全增强：在启动日志中对敏感配置值（如密码、密钥）进行脱敏处理。

🏷️ `PR` `Security` `Configuration`

---

### FIP-37: Add bitmap scalar functions

📎 [PR #3492](https://github.com/apache/fluss/pull/3492)

6/16 创建。实现 FIP-37 提案：添加 bitmap 标量函数并通过 FlussCatalog 注册，增强 Fluss 的 bitemporal 分析能力。

🏷️ `PR` `FIP-37` `Bitmap` `Flink`

---

### Lake/Tiering: Support reporting watermark to Paimon snapshot

📎 [PR #3420](https://github.com/apache/fluss/pull/3420)

6/2 创建，6/17 仍在活跃更新。为 lake tiering 添加向 Paimon snapshot 上报 watermark 的能力，改善端到端数据新鲜度追踪。

🏷️ `PR` `Lake Storage` `Paimon` `Watermark`

---

## 趋势观察

| 项目 | 趋势 |
|------|------|
| **Kafka** | KIP 讨论活跃，偏向 Streams 改进（headers-aware state stores、custom assignors、IQv2）和 KRaft 运维优化。社区关注 KRaft 迁移实操和 4.x 治理层挑战。 |
| **AutoMQ** | 1.7.0 发布是本周最大事件，功能密度高（namespace、事件框架、autoscaling），体现了对多租户和企业级生产就绪的投入。 |
| **Fluss** | 持续高频迭代，焦点在 lake storage 正确性（snapshot 校验、watermark）、KV 存储稳定性（RocksDB 背压）和安全加固。仍在 incubating 阶段但 PR 质量和数量均在线。 |
