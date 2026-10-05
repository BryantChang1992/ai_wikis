---
type: analysis
title: 🌊 Kafka / Flink / Fluss 社区动态 — Week 08 (2026-06-25)
blog_url: https://bryantchang1992.github.io/ai_memory_chang_ai_team/tech_research/kafka_research/week_08_2026-06-25.html
blog_source: tech_research/kafka_research/week_08_2026-06-25.html
blog_source_commit: f83970fa7e6ad32d626cc6ca3ba7428c90a638a5
synced_at: '2026-10-05'
tags:
- 博客同步
---

# 🌊 Kafka / Flink / Fluss 社区动态 — Week 08 (2026-06-25)

覆盖周期：2026-06-19 ~ 2026-06-25

## 1. Apache Flink 2.0 生态成型

### 版本发布时间线

| 版本 | 日期 | 内容 |
| --- | --- | --- |
| Flink 2.0 | 2026 Q1 | 统一流批处理、动态分区裁剪、Runtime Filter、自适应并行度 |
| Flink 2.0.2 | 2026-05-11 | 34 bug 修复 + 安全补丁，推荐所有 2.0 用户升级 |
| Flink 2.2.0 | Latest Stable | 当前稳定版（官网上下载页最新） |

### 生态组件更新

- **Flink Connector Parent 2.0.0**：全部官方 connector 完成 Flink 2 兼容适配 + 许可证检查
- **Flink Connector AWS 6.0**：Flink 2 + AWS Glue Schema Registry 增强
- **Flink Kubernetes Operator 1.14.0**：Shopify 团队贡献 FlinkBlueGreenDeployment 修复

### 关键 FLIP

| FLIP | 状态 | 内容 |
| --- | --- | --- |
| FLIP-555 | Accepted — 实现中 | Flink Native S3 FileSystem，直接用 AWS SDK V2，脱离 Hadoop/Presto 依赖 |
| FLIP-566 | 讨论中 | IMMUTABLE 列约束，对增量 / CDC 语义重要 |

### 技术改进要点

- Watermark 对齐优化 — SamplingWatermarkRingBuffer 缓冲 watermark
- Checkpoint 恢复改进 — 首次 checkpoint barrier 到达前暂停 Source，加快恢复
- VARIANT 类型支持 — 与 Iceberg v3 对齐
- Flink SQL GA（Confluent 平台）

来源：[flink.apache.org — March 2026 Update](https://flink.apache.org/2026/03/01/flink-community-update-for-march-2026/), [flink.apache.org — 2.0.2](https://flink.apache.org/2026/05/11/apache-flink-2.0.2-release-announcement/), [nightlies.apache.org — Flink 2.0 RN](https://nightlies.apache.org/flink/flink-docs-stable/release-notes/flink-2.0/)

## 2. Apache Fluss 1.0 路线图

🔥 即将发布

| 里程碑 | 日期 |
| --- | --- |
| Feature Freeze | 2026-06-01 |
| Release | 2026-06-15 |

核心目标：**Enable LakeStream on existing lake table** — 在已有湖仓表上直接启用流式读写。

Fluss 定位为 "table-first columnar streaming storage"，通过 union reads 实现 streaming 和 lakehouse 两层的数据统一视图。已进入 Apache 孵化器。

2026 年 4 月 CMU DB Group 举办的 Future Data 活动中，Fluss 被特别介绍为 "a lakehouse-native streaming storage system"。

来源：[github.com/apache/fluss — 1.0 Roadmap](https://github.com/apache/fluss/discussions/2684), [fluss.apache.org/learn/talks](https://fluss.apache.org/learn/talks/)

## 3. Apache Flink Agents 0.2.0

Flink 生态向 AI/Agent 领域延伸的重要信号：

- 新增 Embedding Models 支持
- 新增 Vector Stores 集成
- 新增 MCP Server 支持
- 新增 Java 异步执行能力

来源：[flink.apache.org — Agents 0.2.0](https://flink.apache.org/2026/02/06/apache-flink-agents-0.2.0-release-announcement/)

## 4. RisingWave 2.x

RisingWave 持续迭代至 v2.8.0（2026-03-02），新增跨数据库查询。

品牌重新定位：从 "Streaming Database" → **"Event Streaming Platform for Agentic AI"**，强调 Postgres wire-compatible + Rust 实现。

来源：[risingwave.com — Streaming Database Landscape 2026](https://risingwave.com/blog/streaming-database-landscape-2026-complete-guide/), [docs.risingwave.com — Release Notes](https://docs.risingwave.com/changelog/release-notes)

## 5. Flink CDC V3.6 + Fluss 0.9 联动

LinkedIn 预告（Hongshun Wang）：Fluss 0.9 + Flink CDC V3.6 组合将实现 production-level schema evolution，补齐实时湖仓场景下最棘手的 schema 变更处理。

来源：LinkedIn — Hongshun Wang post

## 小结

流处理生态在 2026 年进入平台化成熟期：Flink 2.0 站稳、Fluss 1.0 即将发布、RisingWave 2.x 转向 Agentic AI。最大的结构性变化是 **Fluss + Paimon 的实时湖仓链路**——直接 LakeStream 读写湖仓表，模糊了 streaming 和 lakehouse 的传统边界。
