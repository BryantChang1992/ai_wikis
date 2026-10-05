---
title: 'Kafka / AutoMQ / Fluss 社区动态 · 周报 #3（2026-06-04）'
blog_url: https://bryantchang1992.github.io/ai_memory_chang_ai_team/posts/tech-research/week-03/kafka/
blog_source: _posts/2026-06-04-kafka-week-03.md
blog_source_commit: f83970fa7e6ad32d626cc6ca3ba7428c90a638a5
blog_body_sha256: 3fdd5be20fa619f1b42141f3ae7d5155c439943f5ff28ef0eca80d1fa065a4e3
synced_at: '2026-10-05'
type: survey
created: '2026-06-04'
tags:
- Kafka
- AutoMQ
- Fluss
issue: 3
issue_date: '2026-06-04'
---

## 🔥 本周综述

> **📌** **本期定位：**数据最丰富的一期——AutoMQ 1.7.0 发布、Fluss 63 个活跃 PR、Kafka 9 个新 KIP 提案进入讨论。

本周是开源流存储领域极其活跃的一周。AutoMQ 在 6 月 4 日发布了里程碑式的 1.7.0 版本，带来命名空间隔离、集群事件框架、Maven 发布等核心特性；Fluss 社区以 63 个活跃 PR 创下近期单周活跃度新高，Hudi LakeCatalog 成功合并、FIP-40 多语言 SDK 合仓推进中；Kafka 社区进入新一轮 KIP 讨论热潮，包括原生集群镜像（KIP-1279）、延迟消息（KIP-1277）、机架感知 min ISR（KIP-1290）等重磅提案。

---

## 🐘 Apache Kafka — 4.2.1 发布 & 新一轮 KIP 提案

`Bugfix Release` `5月30日` `45 Contributors` `9 新 KIP`

### Kafka 4.2.1 Bugfix 发布（5月30日）

Apache Kafka 4.2.1 正式发布，由 **45 位贡献者**参与开发，涵盖 Consumer、Streams、Connect 等多组件稳定性修复。建议所有 4.2.x 用户尽快升级。

### 🔥 新一轮 KIP 提案（讨论中）

在 4.3.0 发布后，Kafka 社区迅速启动新一轮 KIP 提案讨论：

- **⭐ [KIP-1279 · 原生集群镜像（Cluster Mirroring）](https://cwiki.apache.org/confluence/display/KAFKA/KIP-1279%3A+Cluster+Mirroring)** — 将跨集群复制能力原生集成到 Broker 中，替代 MirrorMaker 2。目前讨论中影响面最广的提案——如果落地，将彻底改变 Kafka 多集群架构的运维模式。
- **[KIP-1277 · 原生延迟消息](https://cwiki.apache.org/confluence/display/KAFKA/KIP-1277%3A+Support+Delayed+Message+in+Kafka)** — Producer 可设置未来投递时间戳，Broker 在指定时间后才对 Consumer 可见。
- **[KIP-1290 · 机架感知 min ISR](https://cwiki.apache.org/confluence/display/KAFKA/KIP-1290%3A+Rack-Aware+Minimum+In-Sync+Replicas)** — 确保 ISR 确认跨越足够数量的不同 AZ，提供真正的跨 AZ 持久性保证。
- **[KIP-1297 · Role-Aware Metric Tags（KRaft）](https://cwiki.apache.org/confluence/display/KAFKA/KIP-1297%3A+Role-Aware+Metric+Tags)** — 为 KRaft 模式指标添加 role 标签，解决 controller-only 节点上指标重复/误导问题。
- **[KIP-1289 · Share Group 事务性确认](https://cwiki.apache.org/confluence/display/KAFKA/KIP-1289+Support+Transactional+Acknowledgments+for+Share+Groups)** — 确保处理副作用写入和确认操作原子提交。
- **[KIP-1288 · 客户端 SSL 热加载](https://cwiki.apache.org/confluence/display/KAFKA/KIP-1288%3A+SSL+Hot+Reload+for+Kafka+Clients)** — 监听 keystore/truststore 变更自动重载 SSLContext。
- **[KIP-1282 · 分区扩展防数据丢失](https://cwiki.apache.org/confluence/display/KAFKA/KIP-1282%3A+Prevent+data+loss+during+partition+expansion)** — 引入新的 `partition-start` 策略，仅对新发现的分区从起始读取。
- **[KIP-1272 · Compacted Topic 分层存储](https://cwiki.apache.org/confluence/display/KAFKA/KIP-1272%3A+Support+compacted+topic+in+tiered+storage)** — 分层存储能力扩展到 compacted topic。
- **[KIP-1266 · RemoteLogMetadata Topic 改为 Compacted](https://cwiki.apache.org/confluence/display/KAFKA/KIP-1266%3A+Bounding+The+Number+Of+RemoteLogMetadata+Messages)** — 避免无界增长和慢启动。

---

## ⚡ AutoMQ 1.7.0 — 重大版本发布

`Major Release` `6月4日发布` `30 PRs` `Kafka 3.9.1 基线`

> **📌** **版本亮点：**AutoMQ 1.7.0 合并了 Apache Kafka 3.9.1 作为上游基线，引入命名空间隔离、集群事件框架、Maven Snapshot 包发布、Broker 自伸缩指标等核心特性。

### 🏗️ 架构与核心特性

- **集群事件框架（#3312）：**引入基于 Protobuf 的集群事件发布框架，为集群状态变更通知和未来 Operator 自动运维打下基础。
- **命名空间隔离（#3298, #3306）：**DevKit 和 KV 存储均增加命名空间支持，实现多实例/多租户隔离。
- **Broker 自伸缩指标（#3367）：**暴露 Broker 资源使用统计指标，为自动扩缩容提供数据支撑。
- **ZeroZone 异步分区快照（#3344）：**新增异步分区快照长轮询机制。
- **QuorumController 扩展钩子（#3337）：**为 QuorumController 插件增加激活/停用生命周期钩子。
- **RouterChannel 纪元查询（#3342）：**新增纪元查询 API，便于诊断路由通道状态。

### 📦 构建与发布

- **Maven Snapshot 包发布（#3330）：**首次支持 Maven Snapshot 包发布，方便开发者以依赖方式集成。
- **开源依赖版本统一（#3275）**
- **Strimzi 兼容性提升（#3309）：**用 gRPC ManagedChannel 替换 OkHttp 发送器。

### 🐛 关键 Bug 修复

- **🔴 DataBlockIndex int 溢出修复（#3336）：**endOffsetDelta 在 compaction 过程中 int 溢出可能导致数据丢失，已紧急修复。**所有 1.6.x 用户应尽快升级。**
- **LogCache tryMerge 双重释放（#3307）**
- **OCI S3 并发写入异常（#3314）**
- **S3 对象删除重试（#3392）**

### ⚡ 性能优化

- **带宽限制器 CPU 优化（#3377）：**大幅降低 AsyncNetworkBandwidthLimiter 在网络流量达上限时的 CPU 开销，解决了自 2024 年 10 月开放的历史性能问题（#2052）。

---

## 🌊 Apache Fluss — 社区最活跃的一周

`63 Active PRs` `8 Merged` `2 Tech Blogs` `Lakehouse Tiering`

### 📝 两篇重磅技术博客

- **[Tiering Service Deep Dive Part 1: The Mental Model](https://fluss.apache.org/blog/fluss-tiering-service-deep-dive-part1/)**（6月4日）— 三篇系列开篇，从零构建 Lake Tiering 心智模型。通过完整 Tiering Round 讲解四个角色的职责划分。
- **[The Storage Hierarchy: Hot, Remote, and Lake](https://fluss.apache.org/blog/fluss-storage-hierarchy/)**（6月2日）— 深度剖析 Fluss 三层存储架构（本地 RocksDB → S3 远程对象存储 → Lakehouse），Primary-Key Table 的三种内部结构，Tablet Server 故障恢复两阶段流程。

### 🏷️ 里程碑级 PR

| # | 标题 | 作者 | 状态 | 说明 |
|---|------|------|------|------|
| [#3401](https://github.com/apache/fluss/pull/3401) | 🔥 **FIP-40: merge fluss-rust** | fresh-borzoni | Open | Rust/Python/C++/Elixir 多语言 SDK 合仓，210+ commits |
| [#3395](https://github.com/apache/fluss/pull/3395) | 🎉 **Hudi LakeCatalog 引入** | fhan688 | ✅ Merged | FIP-24 Hudi 支持的里程碑 |
| [#3257](https://github.com/apache/fluss/pull/3257) | Standby Replica ALTER TABLE | swuferhong | ✅ Merged | 🔴 blocker 修复 |
| [#3400](https://github.com/apache/fluss/pull/3400) | Cluster Health API | swuferhong | Open | 🔴 blocker：集群健康检查 API |
| [#3430](https://github.com/apache/fluss/pull/3430) | Arrow 列存 Paimon 写入 | luoyuxia | Open | 替代 #3418，大幅提升 Lakehouse Tiering 写入效率 |

### 🔗 Flink 集成增强

- **Union Read 支持（#3432）：**允许同时从多个表读取数据
- **KVScan Flink 集成（#3383）：**支持主键点查场景
- **Log-Only Source 恢复模式（#3355）：**已合并
- **Batch Virtual Log Table 快速失败（#3402）**

### 🛠️ 运维与稳定性

- **RebalanceManager 超时保护（#3429）：**per-task 超时机制
- **FlushedLogOffset 单调性修复（#3427）**
- **S3 孤文件清理（#3404）：**🔴 blocker

### 🔐 安全

- **SASL JAAS 限制（#3425）：**限制为 PlainLoginModule
- **安全更新页面（#3408）：**网站新增 Security Updates
- **S3 Token 日志脱敏（#3421）**

---

## 📊 趋势观察

### 一、流存储进入"多模态"时代

Fluss 的 Lakehouse Tiering 深度推进、Arrow 列存优化、Hudi LakeCatalog 合并——三个信号共同指向：**下一代流存储基础设施必须是多模态的。**传统数据平台为结构化数据设计，而 AI 工作负载需要处理文本、图像、向量嵌入等多样化数据形态。

### 二、Kafka 和 AutoMQ 的版本节奏对比

| 维度 | Apache Kafka | AutoMQ |
|------|-------------|--------|
| 最新版本 | 4.3.0 (5月22日) | 1.7.0 (6月4日) |
| 上游基线 | — | Kafka 3.9.1 |
| 版本差距 | — | 落后社区 3 个大版本 |
| 核心竞争力 | 生态完整性、社区规模 | 云原生架构、S3-backed 存算分离 |

> **核心判断：**AutoMQ 1.7.0 是一次高质量发布，但追踪的是 Kafka 3.9.1 基线。KIP-1279（原生集群镜像）如果落地，将成为关键变量——如果 AutoMQ 能率先提供更优雅的方案，可能成为差异化优势。

### 三、Fluss 的成长曲线

63 个活跃 PR 创下新高：
- **多语言 SDK 合仓（FIP-40）：**降低 AI/ML 场景接入门槛
- **Hudi 支持首合（#3395）：**Fluss 正在成为"跨 Lake Format 的 Streaming Layer"
- **技术博客定位：**非营销博客，而是帮助用户理解架构的必要文档

---

## 📎 参考链接

### Apache Kafka

- [Kafka 4.2.1 Release Announcement](https://kafka.apache.org/blog/2026/05/30/apache-kafka-4.2.1-release-announcement/)
- [KIP-1279 · 原生集群镜像](https://cwiki.apache.org/confluence/display/KAFKA/KIP-1279%3A+Cluster+Mirroring)
- [KIP-1277 · 原生延迟消息](https://cwiki.apache.org/confluence/display/KAFKA/KIP-1277%3A+Support+Delayed+Message+in+Kafka)
- [KIP-1290 · 机架感知 min ISR](https://cwiki.apache.org/confluence/display/KAFKA/KIP-1290%3A+Rack-Aware+Minimum+In-Sync+Replicas)

### AutoMQ

- [AutoMQ 1.7.0 Release Notes](https://github.com/AutoMQ/automq/releases/tag/1.7.0)
- [#3336 · DataBlockIndex int 溢出修复](https://github.com/AutoMQ/automq/pull/3336)
- [#3377 · 带宽限制器 CPU 优化](https://github.com/AutoMQ/automq/pull/3377)

### Apache Fluss

- [Storage Hierarchy 博客](https://fluss.apache.org/blog/fluss-storage-hierarchy/)
- [Tiering Service Deep Dive Part 1](https://fluss.apache.org/blog/fluss-tiering-service-deep-dive-part1/)
- [#3401 · FIP-40 fluss-rust 合仓](https://github.com/apache/fluss/pull/3401)
- [#3395 · Hudi LakeCatalog 合并](https://github.com/apache/fluss/pull/3395)

---

*CHANG_AI_TEAM · Kafka/AutoMQ/Fluss 社区动态 · 周报 #3 · 2026年6月4日*
