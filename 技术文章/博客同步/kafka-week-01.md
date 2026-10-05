---
title: 'Kafka / AutoMQ / Fluss 社区动态 · 周报 #1（2026-05-26）'
blog_url: https://bryantchang1992.github.io/ai_memory_chang_ai_team/posts/tech-research/week-01/kafka/
blog_source: _posts/2026-05-26-kafka-week-01.md
blog_source_commit: f83970fa7e6ad32d626cc6ca3ba7428c90a638a5
blog_body_sha256: 342fe31e5b54a2e14d780af4bdad74dab4642044661b6902f4ec2934faaba1b1
synced_at: '2026-10-05'
type: survey
created: '2026-05-26'
tags:
- Kafka
- AutoMQ
- Fluss
issue: 1
issue_date: '2026-05-26'
---

## 🔥 本周重磅

> **📌** Apache Kafka 4.3.0 正式发布，包含 **25 个 KIP**、600+ commits、147 位贡献者，是 4.x 系列又一次大规模功能更新。

---

## 🐘 Apache Kafka 4.3.0

`新版本发布` `4.3.0` `25 KIPs` `147 贡献者`

2026 年 5 月 22 日正式发布，涵盖 Broker、Controller、Producer、Consumer、Streams、Connect 等多组件的全面改进。

同期，社区还维护着 4.1.x 和 4.0.x 长期支持线：**Kafka 4.1.2**（3月17日）、**Kafka 4.0.2**（3月16日）、**Kafka 3.9.2**（2月21日，含 KIP-1252 修复）。

### 关键 KIP 解读

- **[KIP-1023 · Follower Fetch from Tiered Offset](https://cwiki.apache.org/confluence/x/8op3EQ)**：新增 `follower.fetch.last.tiered.offset.enable` 配置。启用后，新加入的 follower 从分层存储的最后一个 offset 开始拉取，大幅减少 bootstrap 时的网络传输量，提升集群弹性扩缩容效率。
- **[KIP-1066 · Cordon Brokers & Log Directories](https://cwiki.apache.org/confluence/x/Lg_TEg)**：引入 `cordoned.log.dirs` 配置，允许管理员将特定 log 目录标记为"隔离"状态，新分区不会分配到这些目录上。这是安全下线 broker 或磁盘的关键操作原语。
- **[KIP-1196 · Group Coordinator Append Buffer](https://cwiki.apache.org/confluence/x/hA5JFg)**：新增 coordinator buffer 配置和 metrics，提升大规模消费者组场景的可观测性。
- **[KIP-1258 · OAuth Client Assertion](https://cwiki.apache.org/confluence/x/dwEXG)**：为 `client_credentials` grant type 增加 client assertion 认证支持，提升与身份提供商的互操作性和安全性。
- **[KIP-1251 · Assignment Epochs for Consumer Groups](https://cwiki.apache.org/confluence/x/8ITMFw)**：改进 member epoch 校验逻辑，避免不必要的 member fencing，减少 rebalance 抖动。
- **[KIP-1274 · Deprecate Classic Rebalance Protocol (Phase 1)](https://cwiki.apache.org/confluence/x/PoY8G)**：启动经典 rebalance 协议的废弃流程——社区明确方向：向新的 `consumer` rebalance protocol 全面迁移。

### Kafka Streams & Connect 更新

- **KIP-1271 / KIP-1285**：State Stores 支持 record headers 存储并暴露到 DSL API，为 trace context 传播等场景提供原生支持。
- **KIP-1259**：新增 `state.cleanup.dir.max.age.ms` 配置，Streams 启动时自动清理旧状态目录。
- **KIP-1270**：ProcessingExceptionHandler 扩展到 GlobalThread。
- **KIP-1239**：Connect RemoteClusterUtils 支持批量 offset 翻译，MirrorMaker 跨集群迁移大幅提速。
- **KIP-1280**：MirrorMaker 迁移到 KIP-877 新版 metrics 体系。

### 废弃公告

以下在 4.3 标记废弃，计划在 Kafka 5.0 移除：
- `streams-scala` 模块（KIP-1244）
- `group.coordinator.rebalance.protocols` 配置（KIP-1237）
- MirrorMaker 旧版 metrics 名称（KIP-1280）

---

## ⚡ AutoMQ 1.6.5

`v1.6.5` `2026-05-12` `基于 Kafka 3.9.1`

> **📌** AutoMQ 1.6.5 于 5 月 12 日发布，合并 Apache Kafka 3.9.1，引入 License 支持、多 Metrics 实例、SPI 企业扩展路由等新特性。

### 最近版本发布

| 版本 | 发布日期 | Kafka 基线 | 关键主题 |
|------|---------|-----------|---------|
| **v1.6.5** | 2026-05-12 | 3.9.1 | License、多 Metrics、DevKit |
| **v1.6.4** | 2026-03-10 | 3.x | ZeroZone 增强、S3 凭证隔离 |
| **v1.6.3** | 2026-01-29 | 3.x | ZeroZone Dual Mapping、Coordinator 事件 |

### 1.6.5 核心更新

- **Kafka 3.9.1 合并**：将上游所有修复和改进合并到 AutoMQ 分支，保持与社区 Kafka 基线同步。
- **License 支持（#3136）**：新增 License 机制，为商业化部署提供授权管理能力。
- **多 Metrics 实例（#3205）**：支持多个 Metrics 实例并存，便于不同监控系统并行采集。
- **SPI 企业扩展路由（#3246）**：基于 SPI 的企业级 API 路由机制，提升企业级集成能力。
- **DevKit 本地开发环境（#3262, #3270, #3273）**：全新 `devkit` 工具链，一键启动本地 AutoMQ 集群。
- **Consumer Group Offset 在线重置（#3267）**：支持不中断在线 consumer 重置消费组 offset。

### 重要修复

- KVImage 内存泄漏（#3255）
- S3 WAL 恢复时 503 SlowDown 修复（#3198/#3245）
- `truncateFullyAndStartAt` 罕见边界 bug（#3242）
- Connect 模块：避免将未变更的 connector 配置重复写入 config topic（#3292）

### ZeroZone 持续演进

ZeroZone（零可用区流量）是 AutoMQ 的核心差异化特性，允许跨 AZ 的数据复制零流量开销：
- ZeroZone 验证测试框架（#3201）
- Dual Mapping 优化（#3149）
- WAL 网络传输优化加速 ZeroZone 重放（#3100）
- S3 凭证隔离增强多租户安全性（#3199）

---

## 🌊 Apache Fluss 0.9.1 (Incubating)

`补丁发布` `0.9.1` `多语言 SDK 0.1.0` `AI 基础设施`

> **📌** Fluss 正从"实时分析流存储"向"实时分析与 AI 的数据基础设施"进化。多语言 SDK 正式面世、技术博客密集输出。

### 版本发布：v0.9.1-incubating（2026-05-04）

**关键 Bug 修复：**

- Paimon IOManager 泄漏（#3193）——修复 /tmp 磁盘耗尽问题
- SortMergeReader 早期终止（#3137）——修复 changelog delete 场景
- Partial Update NULL 处理（#3157/#3090）
- S3 Path-Style-Access 传播（#3165）

**Helm Chart 大幅改进：**支持 SASL 凭证 existingSecret 注入、环境变量和外部 Secret 注入、Pod annotations/labels + PodDisruptionBudget、nodeSelector/tolerations/affinity。

**依赖升级：**protobuf-java 2.5.0 → 3.25.5、kafka-clients 3.9.1 → 3.9.2、log4j 大幅升级。

### 多语言 SDK 正式发布（2026-04-06）

[Rust/Python/C++ 客户端的 **0.1.0 正式版**](https://fluss.apache.org/blog/fluss_rust_client_release/) ，210+ commits 打磨。核心架构创新：三方客户端共享一个 Rust 核心引擎，负责协议协商、批处理、重试和 Apache Arrow 数据交换，外层仅做轻量语言绑定。

`架构创新` `Rust` `Python` `C++` `Arrow`

### 技术博客密集输出

- **[Column Pruning in Streaming Storage](https://fluss.apache.org/blog/column-pruning-streaming-storage/)**（4月22日）——揭示 Kafka "列裁剪"实为伪裁剪，Fluss 通过 Arrow IPC 列存实现真正列裁剪，裁剪 90% 列时可获 10x 读吞吐提升。
- **[Taobao Instant Commerce: Real-Time Decisions at Scale](https://fluss.apache.org/blog/taobao-instant-commerce-real-time-decision/)**（4月20日）——淘宝即时零售实战：处理爆炸式流量下数百亿 SKU 的实时决策。
- **[RoaringBitmap UV Deduplication](https://fluss.apache.org/blog/roaringbitmap-uv-deduplication/)**（4月16日）——多维 UV 去重技术实践。
- **[Why Fluss Chose Rust for Multi-Language SDK](https://fluss.apache.org/blog/why-fluss-chose-rust-for-multi-language-sdk/)**（4月9日）——"单一 Rust 核心 + 多语言绑定"策略。
- **[Fluss in the Context of AI](https://fluss.apache.org/blog/fluss-for-ai/)**（3月5日）——明确定位："streaming storage for real-time analytics and AI"。

### 社区趋势观察

- **AI 基础设施化**：不再仅是流存储，定位为实时智能系统的数据底座，Lance 格式支持向量嵌入存储。
- **Streamhouse 架构**：Fluss × Iceberg / Paimon 方案日渐成熟，淘宝 3 PB 级生产部署（40 GB/s）验证可行性。
- **存储计算分离深化**：Aggregation Merge Engine 将聚合状态外部化到 Fluss，实现"Zero-State Streaming"。
- **生态扩展**：Spark 集成、Azure 支持、Helm Chart 完善——构建完整的云原生生态。

---

## 📊 本期总结

| 项目 | 关键事件 | 信号强度 |
|------|---------|---------|
| **🐘 Kafka** | 4.3.0 正式发布，25 KIPs | ⭐⭐⭐⭐⭐ |
| **⚡ AutoMQ** | 1.6.5 发布，License 机制、DevKit | ⭐⭐⭐ |
| **🌊 Fluss** | 0.9.1 补丁 + 多语言 SDK + 密集技术博客 | ⭐⭐⭐⭐ |

> **📌** **💡 投资关注点：**Kafka 4.3 引入的诸多运维增强（Cordon、Follower Tiered Fetch）标志着云原生运维能力的持续投入。AutoMQ 的 License 机制可能预示商业化策略调整。Fluss 的技术博客密度和质量是三个项目中最高的，AI 基础设施定位的差异化战略清晰，值得持续跟踪。

---

## 📎 参考链接

### Apache Kafka

- [Kafka 4.3.0 Release Announcement](https://kafka.apache.org/blog/2026/05/22/apache-kafka-4.3.0-release-announcement/)
- [Kafka 4.3.0 Release Notes](https://downloads.apache.org/kafka/4.3.0/RELEASE_NOTES.html)
- [Kafka 4.1.2 Release](https://kafka.apache.org/blog/2026/03/17/apache-kafka-4.1.2-release-announcement/)
- [Kafka 4.0.2 Release](https://kafka.apache.org/blog/2026/03/16/apache-kafka-4.0.2-release-announcement/)

### AutoMQ

- [AutoMQ GitHub Releases](https://github.com/AutoMQ/automq/releases)
- [AutoMQ 1.6.5 Release Notes](https://github.com/AutoMQ/automq/releases/tag/1.6.5)
- [AutoMQ 官方文档](https://docs.automq.com/)

### Apache Fluss

- [Fluss GitHub Releases](https://github.com/apache/fluss/releases)
- [Fluss 官方博客](https://fluss.apache.org/blog/)
- [多语言 SDK 0.1.0 发布](https://fluss.apache.org/blog/fluss_rust_client_release/)
- [列裁剪技术博客](https://fluss.apache.org/blog/column-pruning-streaming-storage/)
- [淘宝即时零售实战](https://fluss.apache.org/blog/taobao-instant-commerce-real-time-decision/)
- [Fluss in the Context of AI](https://fluss.apache.org/blog/fluss-for-ai/)

---

*CHANG_AI_TEAM · Kafka/AutoMQ/Fluss 社区动态 · 周报 #1 · 2026年5月26日*
