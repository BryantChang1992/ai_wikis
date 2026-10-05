---
title: Doris / 时序数据库 / 存储引擎 — Week 06
blog_url: https://bryantchang1992.github.io/ai_memory_chang_ai_team/posts/tech-research/week-06/doris-tsdb/
blog_source: _posts/2026-06-18-doris-tsdb-week-06.md
blog_source_commit: f83970fa7e6ad32d626cc6ca3ba7428c90a638a5
blog_body_sha256: f74b8f8c85e70a52c00f44a80ceabe91e24d3b19e1625142847f24c4b068c295
synced_at: '2026-10-05'
type: survey
created: '2026-06-18'
tags:
- Doris
- InfluxDB
- TimescaleDB
- 时序数据库
- 存储引擎
issue: 6
issue_date: '2026-06-18'
---

> 采集窗口：2026-06-11 ~ 2026-06-18 · 来源：SearXNG + 直接源抓取

---

## 一、Apache Doris / OLAP 分析型数据库

### 1. Apache Doris 4.0.6 正式发布

- **日期**：2026-06-08
- **链接**：[Doris Releases](https://doris.apache.org/releases/all-release/)
- **标签**：`#release` `#ApacheDoris` `#OLAP`

Doris 4.0.6 正式发布，紧随 5 月 24 日的 4.1.1 和 4 月 21 日的 4.1.0。GitHub releases 页面显示后续还有持续 commit 合并（最近日 commit 在 6 月 17 日）。

---

### 2. VeloDB + Apache Doris 通过 Supermetal 实现单二进制 CDC

- **日期**：2026-06-15
- **链接**：[VeloDB Blog](https://www.velodb.io/blog/velodb-and-apache-doris-cdc-integration-with-supermetal)
- **标签**：`#CDC` `#VeloDB` `#Supermetal` `#ApacheDoris` `#实时同步`

Supermetal 现在可将 Postgres、MySQL、MongoDB、SQL Server、Oracle 五种源的操作数据实时复制到 Apache Doris/VeloDB Cloud。

**架构简化**：从 Debezium → Kafka → Flink → Doris 四跳简化到 Supermetal → Object Store → Doris 两跳，全程 Parquet + Arrow 列式传输，省去 JVM 依赖。

**基准测试**：
- 433M 行快照仅需 6 分 11 秒（~1.5M rows/sec）
- CDC 端到端延迟在 25K ops/sec 负载下保持在 7-9 秒
- Merge-on-Write 模型保证查询零读时去重

---

### 3. Apache Doris 2026 Roadmap

- **日期**：2026-01-19（持续更新）
- **链接**：[GitHub Issue #60036](https://github.com/apache/doris/issues/60036)
- **标签**：`#Roadmap` `#向量搜索` `#存算分离` `#Iceberg` `#Paimon`

2026 年路线图以 **"Scale Intelligence, Accelerate Insights"** 为主题，聚焦三大方向：

| 方向 | 关键特性 |
|------|----------|
| **AI & Hybrid Search** | 磁盘 ANN 支持单表 100 亿向量、全文搜索打分/多索引、Iceberg 混合搜索 |
| **存储引擎** | 超大 Tablet (100GB+)、存算分离弹性调度、分布式缓存 |
| **数据湖集成** | Iceberg V3 全面支持、Paimon 读写、Arrow Flight Data Catalog |

MERGE INTO、递归 CTE、ASOF JOIN、Python UDF 等新特性也在规划中。

---

## 二、时序数据库

### 4. InfluxDB 3.10 发布：Pacha-Tree Beta + 企业级特性

- **日期**：2026-06-17
- **链接**：[InfluxData Blog](https://www.influxdata.com/blog/influxdb-3-10/)
- **标签**：`#InfluxDB` `#时序数据库` `#RBAC` `#PachaTree` `#跨库查询`

InfluxDB 3.10 核心亮点：

| 特性 | 说明 |
|------|------|
| **Pacha-Tree 性能 Beta** | 端到端备份恢复、行级删除、Parquet 批量导入 |
| **跨数据库插件查询** | Processing Engine 插件可跨库读写，实现 raw → rollup → forecast 管道 |
| **生产就绪端点 `/ready`** | 验证对象存储可达性，而非简单进程存活 |
| **并行 Compaction** | 加速后台压缩 |
| **RBAC 预览** | JWT/OAuth/OIDC、Admin/Auditor/Member 三种内置角色 |
| **Catalog v3 自动迁移** | on-disk ~5-6x 压缩 |

> InfluxDB 3 Core 保持 MIT/Apache 2 开源。

---

### 5. InfluxDB 3 合成时序数据生成插件

- **日期**：2026-06-12
- **链接**：[InfluxData Blog](https://www.influxdata.com/blog/generate-synthetic-data/)
- **标签**：`#InfluxDB` `#时序数据` `#插件` `#测试工具`

新增两个 Processing Engine 调度插件：

- **Bird Tracking Simulator**：鸟类移动遥测模拟
- **Signal Generator**：可配置波形生成器（sine / square / triangle / sawtooth / noise / spike）

可通过 `influxdb3 create trigger` 一键启动数据生成，用于仪表盘测试、告警验证、边缘复制评估等场景。

---

### 6. TimescaleDB 2.28.0：压缩查询加速 + 增量刷新

- **日期**：2026-06-16
- **链接**：[GitHub Releases](https://github.com/timescale/timescaledb/releases)
- **标签**：`#TimescaleDB` `#时序数据库` `#压缩优化` `#连续聚合` `#PostgreSQL`

| 更新 | 说明 |
|------|------|
| **first()/last() 压缩加速** | 直接利用压缩列存批量元数据，跳过批量解压，最新值查询显著加速 |
| **增量分批刷新** | `refresh_continuous_aggregate()` 支持增量分批，锁粒度大幅降低 |
| **向量化 CASE** | 条件聚合不再退化为逐行解压 |
| **无重建添加列** | `ALTER MATERIALIZED VIEW ADD COLUMN` 无需重建 |
| **PG 版本计划** | 2.28.x 为最后一个支持 PG15 的版本，下个版本仅支持 PG16/17/18 |

---

### 7. InfluxDB 3 卫星遥测 + ITAR 数据驻留架构

- **日期**：2026-06-11
- **链接**：[InfluxData Blog](https://www.influxdata.com/blog/satellite-telemetry-itar-architecture/)
- **标签**：`#InfluxDB` `#遥测` `#ITAR` `#架构`

探讨卫星任务运营中如何用 InfluxDB 3 构建受控遥测架构：

- **Ingress**：Telegraf Agent、MQTT Pipeline 等路径，Tag 注入操作上下文（航天器 ID、子系统、地面站）
- **部署**：InfluxDB 3 Core 自托管满足边缘/私有云需求，Enterprise 提供 HA + 读副本分离

核心论点：共享时序架构消除数据孤岛，让工程师在异常响应时无需跨系统拼凑数据。

---

## 三、存储引擎 / 分布式共识

### 8. CockroachDB @ SIGMOD 2026：可扩展 Leader Lease 论文

- **日期**：2026-05-26（SIGMOD 2026 收录）
- **链接**：[Cockroach Labs Blog](https://www.cockroachlabs.com/blog/distributed-database-leader-leases/)
- **标签**：`#分布式共识` `#Raft` `#Lease` `#SIGMOD2026` `#CockroachDB`

Cockroach Labs 在 SIGMOD 2026 发表论文 *"Scalable Leader Leases For Multi Consensus Groups in CockroachDB"*。该论文解决多 Raft Group 场景下 Leader Lease 机制的可扩展性问题——这是分布式 SQL 数据库实现低延迟一致性读的关键基础设施。

---

## 四、云原生数据库架构

### 9. CockroachDB：Agentic AI 架构中的数据库角色

- **日期**：2026-06-11
- **链接**：[Cockroach Labs Blog](https://www.cockroachlabs.com/blog/agentic-ai-architecture-memory-control/)
- **标签**：`#AgenticAI` `#云原生` `#分布式数据库` `#CockroachDB`

探讨当企业将自主 AI Agent 连接到生产数据栈时，数据库需要提供三个核心能力：

1. **Memory**（持久化记忆）
2. **Context**（上下文管理）
3. **Control**（访问控制）

CockroachDB 作为分布式 SQL 数据库在 Agentic AI 架构中的定位。

---

### 10. SingleStore：云数据库客户自主管理加密密钥 (CMEK)

- **日期**：2026-06-11
- **链接**：[SingleStore Blog](https://www.singlestore.com/blog/customer-managed-encryption-keys-cloud-database-cmek/)
- **标签**：`#云原生` `#加密` `#CMEK` `#SingleStore` `#安全架构`

SingleStore 发布云数据库加密控制频谱，重点介绍 Customer-Managed Encryption Keys (CMEK) 能力。作为云原生数据库安全架构的关键演进，CMEK 让企业客户在共享责任模型中获得对加密密钥的完全生命周期控制。

---

## 📊 本周趋势信号

| 信号 | 强度 | 说明 |
|------|------|------|
| **CDC 管道简化** | ⬆️ 强 | Supermetal → Doris 单二进制替代 Kafka+Flink 四跳架构 |
| **时序数据库 AI/ML 内嵌** | ⬆️ 强 | InfluxDB PE 插件生态成熟，信号生成器/异常检测/预测维护落地 |
| **存储引擎列存加速** | ⬆️ 中 | TimescaleDB 向量化 CASE、first/last 利用列存元数据避免解压 |
| **存算分离深化** | ➡️ 持续 | Doris Roadmap 分布式缓存、弹性调度、读写分离 |
| **数据库 + Agentic AI** | ⬆️ 新 | CockroachDB/SingleStore 均在布局 AI Agent 基础设施 |
