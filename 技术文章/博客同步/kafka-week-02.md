---
title: 'Kafka / AutoMQ / Fluss 社区动态 · 周报 #2（2026-05-28）'
blog_url: https://bryantchang1992.github.io/ai_memory_chang_ai_team/posts/tech-research/week-02/kafka/
blog_source: _posts/2026-05-28-kafka-week-02.md
blog_source_commit: f83970fa7e6ad32d626cc6ca3ba7428c90a638a5
blog_body_sha256: b503a4db4f742d955879e9e8a06fc869a5a463c8095546a4d525d2f632431d47
synced_at: '2026-10-05'
type: survey
created: '2026-05-28'
tags:
- Kafka
- AutoMQ
- Fluss
issue: 2
issue_date: '2026-05-28'
---

## 🔥 本周综述

> **📌** **本期定位：**距上期仅 2 天，本期换一个视角——不关注"发生了什么"，而是"这意味着什么"。深入解读 Kafka 4.3.0 的落地影响、剖析 Fluss 0.9.1 的架构设计意图，并追踪 Fluss 2026 路线图的战略方向。

自然时间线上没有重大新版本发布，但这正是深入分析的最佳窗口——社区在消化、解读、传播 4.3.0 的影响，Fluss 社区则继续其密集的技术产出。

本周核心看点：

- **FactorHouse 发布 Kafka 4.3.0 平台工程师指南**——面向实践者的系统化解读
- **Red Hat Kafka Monthly Digest 4 月刊**——社区视角的 4.3.0 全景覆盖
- **Fluss 0.9.1 技术深潜**——从 MergeTreeWriter IOManager 泄漏到 Netty 安全加固
- **Fluss 2026 路线图明确**——"Streaming Storage for Real-Time Analytics & AI"
- **AutoMQ 4 月 Newsletter**——简化安装、Playground、社区增长

---

## 🐘 Apache Kafka 4.3.0 深度解读

`社区解读` `FactorHouse` `Platform Engineering` `升级指南`

Kafka 4.3.0 不是"又一个大版本"，而是 4.x 系列在运维成熟度、安全标准和协议现代化三个维度上的关键锚点。

### FactorHouse 平台工程师指南

FactorHouse 发布了面向平台工程师的 [Kafka 4.3.0 系统化指南](https://factorhouse.io/articles/apache-kafka-4-3-0)，从"你需要做什么"的角度出发对关键 KIP 做落地级解读：

- **[KIP-1023 · Follower Fetch from Tiered Offset](https://cwiki.apache.org/confluence/x/8op3EQ)** — *操作影响：高。* 启用后新加入的 follower 直接从分层存储最后一个 offset 开始拉取，跳过完整本地日志复制。FactorHouse 建议：启用前确保 Tiered Storage 配置正确且已在生产验证。
- **[KIP-1066 · Cordon Brokers & Log Directories](https://cwiki.apache.org/confluence/x/Lg_TEg)** — *操作影响：高。* 运维期待已久的能力——将 broker 或磁盘目录标记为"隔离"状态。典型场景：磁盘故障预警后安全下线、滚动升级前节点排水。"安全退役 broker 的缺失拼图终于补上了。"
- **[KIP-1196 · Group Coordinator Append Buffer](https://cwiki.apache.org/confluence/x/hA5JFg)** — *操作影响：中。* 限流 coordinator 内存并暴露 metrics，在 >10k 消费者组场景防止 OOM。

### Red Hat Kafka Monthly Digest（2026-04）

[Red Hat 月度综述](https://developers.redhat.com/blog/2026/05/04/kafka-monthly-digest-april-2026) 从 AMQ Streams 团队视角观察：

- **协议现代化加速：**KIP-1274（废弃经典 Rebalance）+ KIP-1251（Assignment Epochs）表明社区正全力推动新 Consumer Rebalance Protocol 成为唯一标准
- **安全性持续增强：**KIP-1258（OAuth Client Assertion）是 Kafka 从"基础 SASL"到"企业级 OAuth 集成"的关键一步
- **运维可观测性：**Coordinator buffer metrics、MirrorMaker 新版 metrics 迁移
- **4.2.1 开发中：**建议 4.2.x 用户关注

### Confluent 官方 Demo

Confluent 在 [YouTube 发布了 Kafka 4.3.0 亮点 Demo](https://www.youtube.com/watch?v=lePgrOiX11U)，通常只有重点版本才会配套官方 Demo 视频，侧面印证了 Confluent 对 4.3.0 的重视程度。

### 落地思考

- **升级紧迫性：**如果你在 4.2.x，4.3.0 值得优先考虑——KIP-1066（Cordon）和 KIP-1023（Follower Tiered Fetch）对运维效率的提升是即时的。4.0.x/4.1.x 稳定环境可等待 4.3.1 bugfix 后规划。
- **Consumer 协议迁移窗口：**KIP-1274 启动经典 Rebalance 废弃倒计时。消费者仍用经典协议的应开始迁移评估——Kafka 5.0 将彻底移除。
- **Streams Headers 支持：**KIP-1271/1285 为 State Stores 引入原生 record headers 存储。传播 trace context 有了更优雅的方案。

---

## 🌊 Apache Fluss 0.9.1 技术深潜

`v0.9.1-incubating` `2026-05-04` `补丁发布`

表面上是一个"平淡无奇"的 patch release，但其中包含的修复和架构改进信号告诉我们这个年轻项目正在快速成熟。

### 🐛 Bug 修复揭示的架构信号

#### Paimon IOManager 泄漏 — 分层存储的隐性成本

[#3193](https://github.com/apache/fluss/pull/3193) 修复了 MergeTreeWriter 中 IOManager 未释放问题，该问题会在 tiering 过程中导致 `/tmp` 磁盘持续增长直至耗尽。

**深度分析：**这反映了 Fluss 架构中的关键依赖链：**Fluss → Paimon → IOManager → 本地磁盘**。分层存储不是"把数据扔到 S3 就完了"——中间的排序/合并阶段仍然需要本地临时存储。0.9.1 的修复本质上是对这条依赖链的资源管理做了正确的生命周期绑定。

#### Partial Update 的 NULL 语义修正

[#3157](https://github.com/apache/fluss/pull/3157) 修复首次 insert 时非目标列未被置 NULL；[#3090](https://github.com/apache/fluss/pull/3090) 修复 ADD COLUMN 后 partial update/delete 的 OutOfBoundsException。

**深度分析：**这两个 bug 暴露了 Partial Update 与 Schema Evolution 交互时的语义不一致——当表结构发生变化后，新列的 NULL 默认值和旧数据的列偏移量没有正确对齐。这是典型的"流存储 + Schema Evolution"场景下的坑。

#### SortMergeReader Changelog Delete 终止

[#3137](https://github.com/apache/fluss/pull/3137) 修复 SortMergeReader 在处理 changelog delete 记录时的早期终止。在流存储中，delete 记录需要"隐藏"之前的数据但又不被物理删除，排序合并逻辑必须正确处理这种逻辑删除。

### ✨ Improvements 的架构含义

- **Lake Filter 下推（#3181）：**实现非分区扫描的 lake filter 下推——Fluss "Lakehouse-native" 设计理念的体现。利用底层 Lake Storage 的谓词下推能力，对 AI/ML 数据探索查询尤为关键。
- **Netty Max Request Size（#3108）：**引入请求大小限制——项目从"功能优先"进入"生产就绪"阶段的标志。
- **S3 凭证链 + RustFS STS（#3094/#2989）：**多组件架构（Java server、RustFS、S3）三方都需要正确凭证传递，应对多租户/多凭证场景的实际需求。

### ⛵ Helm Chart — 云原生化的信号

一个 patch 版本包含出乎意料大的 Helm Chart 升级：

- SASL 凭证 existingSecret 注入
- PodDisruptionBudget 支持
- nodeSelector / tolerations / affinity 完整调度原语
- 环境变量和外部 Secret 注入（提升 GitOps 兼容性）
- Quickstart 镜像重新引入

> 一个 patch 版本的 Helm Chart 升级到这个程度，说明 Fluss 社区在积极推动从"开发环境部署"到"生产级 Kubernetes 部署"的跨越。

---

## 🗺️ Fluss 2026 路线图

`AI Infrastructure` `Real-Time Analytics` `Streamhouse` `Columnar Storage`

> **📌** **战略定位：**Fluss 2026 的核心使命是"为实时分析与 AI 提供流式存储基础设施"——在 Kafka 占据通用消息队列的格局下，选择了更垂直、也更有技术壁垒的赛道。

### 重点一：AI 基础设施化

以 3 月发布的 [《Fluss in the Context of AI》](https://fluss.apache.org/blog/fluss-for-ai/) 为标志性宣言：

- **特征存储（Feature Store）：**列存储架构天然适合——按需读取特征列、低延迟实时特征更新、Arrow 格式与 ML 框架无缝对接
- **实时上下文注入：**RAG 和 Agent 场景需要低延迟实时上下文数据，Streaming Lakehouse 架构统一流批查询
- **向量嵌入存储：**Lance 格式原生支持向量嵌入存储和检索
- **多语言 SDK 降门槛：**Python 生态是 AI 开发的主力语言

### 重点二：Streamhouse 架构深化

- **淘宝 3 PB 级验证：**40 GB/s 吞吐，验证了架构可行性
- **Delta Join & Partial Update：**Flink 作业以近似无状态方式运行
- **Lake Filter 下推：**进一步缩小流存储和 lake 存储查询性能差距

### 重点三：Zero-State Streaming

终极目标——Flink 作业近乎无状态运行，状态全部外部化到 Fluss：
- 弹性扩缩容：近乎即时 scale up/down
- Crash Recovery：Flink 重启时直接从 Fluss 恢复
- 多作业共享状态

### 成熟度评估

| 维度 | 状态 | 评估 |
|------|------|------|
| 核心引擎 | 🟡 生产中（淘宝） | 大规模验证完成，边界仍在打磨 |
| 多语言 SDK | 🟡 0.1.0 发布 | 架构优秀，版本号偏低 |
| Kubernetes 部署 | 🟡 有 Chart，无 Operator | 缺少 Operator 级别自动运维 |
| 社区治理 | 🟡 Incubating | 毕业需要更广泛 contributor 多样性 |
| AI 能力 | 🟠 早期规划 | 向量存储、特征存储等处于规划设计阶段 |

---

## ⚡ AutoMQ 社区动态

`社区运营` `Newsletter` `开发者体验`

### 4 月 Newsletter

AutoMQ 通过 [LinkedIn](https://www.linkedin.com/pulse/automq-newsletter-april-2026-automq-bd4pc) 发布了 4 月社区通讯：

- **Playground 环境：**面向快速体验 AutoMQ 的开发者，降低"从零到运行"的摩擦
- **简化安装流程：**结合 1.6.5 引入的 DevKit，在开发者体验（DX）上持续投入

### 双轨路线

AutoMQ 正走"开源+商业"双轨路线：
- **开源侧：**DevKit 本地开发、Playground 零门槛体验、Kafka 兼容性
- **商业侧：**License 授权管理、SPI 扩展路由、多 Metrics 实例

值得关注：AutoMQ 基于 Kafka 3.9.1，与社区最新 4.3.0 存在差距——需要加快上游同步节奏。

---

## 📊 趋势观察

### 一、Kafka 4.x 进入成熟期

标志：运维原语补全、安全标准系统化提升、旧协议明确废弃路线图、第三方社区开始产出实践指南。

> **对用户：**在 4.x 上升级风险回报比有利。在 3.x 的建议在 Kafka 5.0 前完成迁移。

### 二、Fluss vs. Kafka：差异化路径

| 维度 | Kafka | Fluss |
|------|-------|-------|
| 存储格式 | 按分区、按 segment 的日志 | 按主键分区、列存储（Arrow） |
| 查询模式 | 顺序扫描 | 列裁剪、谓词下推、点查和范围查询 |
| 表模型 | 无 Schema 约束的 Topic | 有主键、有 Schema 的 Table |
| 更新能力 | 无 | Partial Update、Delete、Merge |
| Lake 集成 | Tiered Storage（冷数据归档） | Streamhouse（流批一体查询） |
| 主要场景 | 通用消息队列、事件流 | 实时分析、特征存储、AI 基础设施 |

> **核心判断：**Fluss 不是"做更好的 Kafka"，而是"做 Kafka 做不到的事"。

### 三、行业整体趋势

- **存算分离成为标配：**三个项目不约而同走向存算分离
- **AI + Streaming 深度融合：**实时数据 + AI 推理组合成为新技术范式
- **列存储成为流存储新方向：**Arrow 列存储在查询性能和 AI 兼容性上的优势推动行业重思存储格式
- **Kubernetes Native 运维：**运维云原生化是所有基础设施软件的共识方向

---

## 📎 参考链接

### Apache Kafka

- [FactorHouse · Kafka 4.3.0 Platform Engineer Guide](https://factorhouse.io/articles/apache-kafka-4-3-0)
- [Red Hat · Kafka Monthly Digest April 2026](https://developers.redhat.com/blog/2026/05/04/kafka-monthly-digest-april-2026)
- [Confluent · Kafka 4.3.0 Highlights Demo](https://www.youtube.com/watch?v=lePgrOiX11U)
- [Kafka 4.3.0 Release Announcement](https://kafka.apache.org/blog/2026/05/22/apache-kafka-4.3.0-release-announcement/)

### Apache Fluss

- [Fluss GitHub Releases · v0.9.1](https://github.com/apache/fluss/releases)
- [Fluss GitHub Discussions · 路线图](https://github.com/apache/fluss/discussions)
- [Fluss in the Context of AI](https://fluss.apache.org/blog/fluss-for-ai/)
- [淘宝即时零售 · Streamhouse 实战](https://fluss.apache.org/blog/taobao-instant-commerce-real-time-decision/)
- [Fluss 邮件列表 · 路线图讨论](https://www.mail-archive.com/issues@fluss.apache.org/msg08541.html)

### AutoMQ

- [AutoMQ Newsletter · April 2026](https://www.linkedin.com/pulse/automq-newsletter-april-2026-automq-bd4pc)
- [AutoMQ GitHub Releases](https://github.com/AutoMQ/automq/releases)

---

*CHANG_AI_TEAM · Kafka/AutoMQ/Fluss 社区动态 · 周报 #2 · 2026年5月28日*
