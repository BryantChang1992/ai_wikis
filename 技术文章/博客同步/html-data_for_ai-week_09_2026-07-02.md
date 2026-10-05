---
type: analysis
title: 🏛 Week 09 · 湖仓 & 时序数据库
blog_url: https://bryantchang1992.github.io/ai_memory_chang_ai_team/tech_research/data_for_ai/week_09_2026-07-02.html
blog_source: tech_research/data_for_ai/week_09_2026-07-02.html
blog_source_commit: f83970fa7e6ad32d626cc6ca3ba7428c90a638a5
synced_at: '2026-10-05'
tags:
- 博客同步
---

# 🏛 Week 09 · 湖仓 & 时序数据库

2026-07-02 · 覆盖周期 2026-06-26 ~ 2026-07-02

## 🔥 Delta Lake 4.3.0 发布（6/18）

本周湖仓方向最大事件，Delta Lake 4.3.0 带来多项架构级更新：

### 核心特性

| 特性 | 描述 |
| --- | --- |
| **Unity Catalog Delta REST API** | Spark 原生支持 UC Delta API，以 Unity Catalog 为 managed Delta table 的单一事实源。服务端 commit validation + server-advertised table features + intent-based metadata update。为后续 Flink/Trino 等多引擎统一访问奠定基础 |
| **replaceOn / replaceUsing API** | DataFrame 新增选择性数据替换：`replaceUsing` 按匹配列替换、`replaceOn` 按自定义条件替换，细粒度数据修正不再需要全表重写 |
| **UniForm 原子+增量 Iceberg 转换** | UniForm 将 Iceberg metadata 与 Delta commit 原子写入，仅增量转换变更日志范围，显著降低 Iceberg 兼容的写入开销 |
| **Delta Sharing Streaming + CDF** | Streaming CDF 支持增强：自动 Delta response 解析、Parquet→Delta streaming 转换、Trigger.AvailableNow 支持 |

### 4.3.1 补丁（7/8）

- OAuth case-sensitivity bug 修复（Delta REST Catalog 认证）
- S3A fast listing 兼容性修复（FilterFileSystem wrapper）
- UC managed-table metadata 持久化问题修复

### Insight

Delta 4.3.0 的 UC Delta REST API 是 Catalog 竞争格局的关键一步。Databricks 的策略是「让 UC 成为所有 Delta 表的源头」，通过 server-side validation 和 intent-based metadata 来防止并发写入冲突，本质上是把 Git-like 的乐观并发控制升级为服务端的中心化协调。

## 📊 Apache Doris

### Doris 4.0.7 发布（7/12）

Doris 4.0 系列最新的 patch release，主要包含 bug 修复和稳定性增强。4.1 系列（4.1.0 发布于 4/16，4.1.2 发布于 6/17）持续迭代中。

### 本周 Doris 方向更新

- Doris 4.0.7 紧随 4.0.6（6/8）发布，4.0 系列维护节奏保持高频
- 4.1.x 系列的 AI 统一存储能力（向量索引 HNSW+IVF+IVF\_ON\_DISK、全文搜索 BM25、单行 100MB JSON）持续吸引社区关注
- 存算分离模式已部署 2000+ 企业

## ⏱ 时序数据库

### 本周动态

- **InfluxDB 3.x** — Pacha-Tree 存储引擎 Beta 测试持续推进，融合 LSM-tree 与时间分区优化的混合存储架构
- **TimescaleDB** — 列存加速能力持续优化，Hypertable 压缩比进一步提升
- **趋势** — 时序数据库与 OLAP 数据库的边界持续模糊化：Doris 4.1 的时序能力增强、InfluxDB 3.x 的 SQL 兼容性提升，两者在「时序分析」场景形成正面竞争

## 🗺 湖仓格式竞争格局（2026 Mid-Year）

| 格式 | 最新版本 | 周期内关键事件 | 定位 |
| --- | --- | --- | --- |
| **Delta Lake** | 4.3.1 (7/8) | UC REST API 集成、replaceOn/replaceUsing、UniForm 增量 Iceberg | Databricks 生态核心，Catalog-first 战略 |
| **Iceberg** | 1.11.0 (5/20) | v3 Spec 生产就绪（删除向量、服务端扫描规划、表加密） | 最广泛引擎支持，v3 打破性能-兼容 trade-off |
| **Hudi** | 1.2.0 (5/23) / 0.14.2 (6/8) | 1.2 多模态（VECTOR+BLOB+VARIANT）、Hudi 2.0 目标 6 月 | 多模态 Lakehouse 先行者，Uber/AWS 生态 |
| **Paimon** | 持续迭代 | Fluss 深度整合，实时湖仓链路：Kafka→Fluss→Paimon→Flink | Flink/阿里生态，流批一体 |

### 竞争格局洞察

1. **Delta Lake UC REST API 标志着 Catalog 战争升级**：Databricks 不再满足于「Delta 是一种格式」，而是通过 UC 将 Catalog 变成控制平面
2. **UniForm 的双向兼容正在改变格局**：写 Delta、读 Iceberg 成为现实，Delta 性能和 Iceberg 兼容不再互斥
3. **Hudi 2.0 是关键变量**：如果 6 月目标达成，多模态 Lakehouse + Flink 流批一体的组合将对 Delta 形成差异化竞争
4. **Fluss+Paimon 实时湖仓链路值得关注**：阿里巴巴内部已验证的「Kafka→Fluss→Paimon→Flink 查询」全链路，可能成为实时湖仓的事实标准
