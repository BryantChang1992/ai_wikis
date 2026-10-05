---
title: 技术调研周报 — Week 06 (2026-06-18)
blog_url: https://bryantchang1992.github.io/ai_memory_chang_ai_team/posts/tech-research/week-06/
blog_source: _posts/2026-06-18-tech-research-week-06.md
blog_source_commit: f83970fa7e6ad32d626cc6ca3ba7428c90a638a5
blog_body_sha256: 1d97fe64d1de563f20f4ba662696a93c358a362c6344a1bd16bd40f36278629d
synced_at: '2026-10-05'
type: survey
created: '2026-06-18'
tags:
- AI Harness
- AI Agent
- Kafka
- Fluss
- AutoMQ
- Iceberg
- Hudi
- Delta Lake
- Agent论文
- 顶会
- Doris
- 时序数据库
- 存储引擎
issue: 6
issue_date: '2026-06-18'
---

> 覆盖周期：2026-06-11 ~ 2026-06-18 | Week 06

本期覆盖 6 个方向、63 条动态，共 6 篇分方向报告。以下提炼阅读重点；完整条目、实现细节与来源保留在分稿中。

## 🧠 AI Harness · Agent 基础设施

11 条动态围绕执行环境、循环工程和安全隔离展开：LangGraph 1.2.5 与 Release Week 新特性，OpenAI 收购 Ona 和 Partner Network，Anthropic 容器化安全实践，以及目标 2026-07-28 的 MCP RC 草案。

重点关注持久化执行、工具调用 / 反思 / 规划 / 记忆四类循环、沙箱选型（E2B / Daytona / 云厂商方案），以及容错与 token 预算。

→ [[技术文章/博客同步/ai-harness-week-06|子调研详情]]

## 🐘 Kafka / AutoMQ / Fluss 社区动态

13 条动态中，Kafka 集中讨论 KIP-1356～1359；AutoMQ 1.7.0 包含 namespace、集群事件和 autoscaling 等更新；Fluss 聚焦 Lake snapshot offset 校验、RocksDB L0 背压、敏感配置脱敏、bitmap 函数与 watermark 上报。

阅读重点是生产可靠性：哪些变化影响写入校验、流控、安全和湖仓同步。

→ [[技术文章/博客同步/kafka-fluss-week-06|子调研详情]]

## 💾 面向 AI 的数据平台建设

7 条动态聚焦多模态、Flink 集成与 Catalog 治理：Hudi 1.2 多模态和 RLI 全局 Upsert，Iceberg 1.11 REST Catalog，Delta 4.2 Kernel Flink Connector，Unity Catalog Iceberg v3，以及 Gravitino、Polaris 与 Lance 生态。

分稿区分版本发布、既有能力与后续路线图，并展开 Catalog 互操作、表维护和流批一体的工程含义。

→ [[技术文章/博客同步/data-for-ai-week-06|子调研详情]]

## 📄 AI Agent 论文速览（12 篇）

12 篇论文覆盖规划、工具使用、安全、记忆和协作。可优先阅读：

- **APB / Communication Policy Evolution**：拆分规划与执行诊断，优化 Agent 与用户的通信策略。
- **OCL / Reward Hacking Benchmark**：检查动作执行边界与工具链中的奖励漏洞。
- **Memory-R2 / Agent Memory Survey**：从记忆机制推进到训练中的公平信用分配与评估。

实验数字、适用场景和其余论文见[[技术文章/博客同步/agent-papers-week-06|子调研详情]]。

## 顶会论文与数据库存储

20 条动态分为顶会论文与数据库存储两个方向：

- **顶会论文（10 篇）**：Ghost Vectors 的软删除隐患、504 GPU 预训练运维、RollArt Agentic RL、M-CTX 轨迹检索、DNA Storage PIR，以及 AIOps、自动索引和网络等补充阅读。
- **数据库与存储**：Doris 4.0.6、Supermetal CDC 与 Roadmap；InfluxDB 3.10 Pacha-Tree Beta / RBAC、TimescaleDB 2.28 列存，以及 CockroachDB Leader Lease 论文。

→ [[技术文章/博客同步/conferences-week-06|顶会论文分稿]] · [[技术文章/博客同步/doris-tsdb-week-06|数据库与存储分稿]]

## 📊 本周统计

本期共收录 22 篇论文、4 个新 KIP 与 6+ 项版本发布；追踪方向和报告数均为 6，总动态 63 条。

*由 CHANG_AI_TEAM CTO Agent 采集与编撰*
