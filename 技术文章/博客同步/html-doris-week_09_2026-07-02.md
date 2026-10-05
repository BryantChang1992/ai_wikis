---
type: analysis
title: 🌊 Week 09 · 流处理 / 存储引擎 / 湖仓
blog_url: https://bryantchang1992.github.io/ai_memory_chang_ai_team/tech_research/doris/week_09_2026-07-02.html
blog_source: tech_research/doris/week_09_2026-07-02.html
blog_source_commit: f83970fa7e6ad32d626cc6ca3ba7428c90a638a5
synced_at: '2026-10-05'
tags:
- 博客同步
---

# 🌊 Week 09 · 流处理 / 存储引擎 / 湖仓

2026-07-02 · 覆盖周期 2026-06-26 ~ 2026-07-02

## 🔥 Apache Flink 2.3.0 发布

Apache Flink PMC 于 **2026-06-25** 发布 Flink 2.3.0，实现 15 个 FLIP 的核心功能，多项关键增强。

### 核心特性

| 特性 | 描述 |
| --- | --- |
| **FROM\_CHANGELOG / TO\_CHANGELOG** | 两个新的 Process Table Function，实现 append-only 流与动态 changelog 表之间的双向转换。FROM\_CHANGELOG 支持自定义 op\_mapping 适配不同 CDC 格式；TO\_CHANGELOG 首次在 SQL 层面将 retract/upsert 流物化为 append-only 输出。 |
| **Materialized Table 进化** | CREATE MATERIALIZED TABLE 支持显式列定义（含 watermark/PK）；ALTER 支持 ADD/MODIFY/DROP 元数据和计算列 + RENAME TO。新增 START\_MODE 子句精确控制 query 变更后的重处理起点。 |
| **Adaptive Partition Selection** | 基于自适应分析的 partition 选择，优化背压（backpressure）处理。 |
| **Native S3 Filesystem（Experimental）** | 完全重构的 S3 文件系统（FLIP-555），基于 AWS SDK v2，完全脱离 Hadoop/Presto 依赖。 |
| **SinkUpsertMaterializer 重构** | 新增 ON CONFLICT 子句（DO NOTHING / DO ERROR / DO DEDUPLICATE），解决 upsert key ≠ primary key 时的无界状态增长问题。 |

同周期还有 Flink 2.1.3 补丁版（6/14），5 个 bug 修复。

**Insight**：Flink 2.3.0 在 SQL 层面补上了 changelog 互转的最后一块拼图。TO\_CHANGELOG 尤其重要——它为 CDC 管道、审计归档、append-only sink 提供了标准 SQL 入口，不再需要回退到 DataStream API。Materialized Table 的 DDL/ALTER 能力对齐也消除了此前"物化表二等公民"的状态。

## 🏠 内部产出：Fluss 客户端写入流程深度分析

本周内部完成 Fluss 客户端写入全链路源码分析（Commit `a3a59fd` ~ `53b4f65`，2026-06-30 ~ 07-01）。

### 产出清单

- **05b 文档**：497 行 Markdown，覆盖 ConnectionFactory → AppendWriter → RpcClient 完整管线
- **架构 SVG**：Fluss 客户端写入引擎核心组件架构图（3 轮迭代优化：正交箭头路径、三列对齐排版、7 处箭头穿越修复）
- **README 更新**：模块分析进度表新增 05b 条目

### 关键发现

- **三个关键约定**：`Connection`（重量级全局单例，内含 RpcClient/MetadataUpdater/WriterClient）→ `Table`（轻量级 per-thread，AutoCloseable）→ `AppendWriter`（异步写入，flush() 阻塞等待全部 ack）
- **写入管线**：Row → Arrow RecordBatch → KV Index batch → Log Segment → Remote Storage，多层编码转换
- **MetadataUpdater**：通过后台线程定期/按需拉取 schema、bucket 分配、列格式元数据
- **WriterClient**：管理多 bucket 写入路由，处理重试和背压信号

至此 Fluss 源码分析 8 个模块（01-07 + 05b）全部完成。当前全部 1747 个源文件的模块映射关系已建立。

📎 详见：[05b-客户端写入流程深度分析](https://github.com/BryantChang1992/ai_wikis/blob/master/项目文档/Fluss源码分析/05b-客户端写入流程深度分析.md)

## 🐘 分布式数据库

### CockroachDB vs TiDB 2026 架构对比

多家独立评测机构发布 CockroachDB vs TiDB 2026 年度对比分析：

- **CockroachDB**：紧耦合多层架构，SQL 层直接在分布式 KV 存储之上，无外部依赖。优势是"像在运行一台跨越数据中心的 PostgreSQL"，牺牲的是 SQL 处理与存储无法独立扩缩。
- **TiDB**：存算分离架构，SQL frontend (Go) + TiKV 分布式存储 (Rust/RocksDB) + TiFlash 列存 (C++)。弹性扩缩能力更强，但运维复杂度更高（多组件协调）。

结论：对于地理分布式事务场景，CockroachDB 更自然；对于需要独立弹性扩缩 OLTP + OLAP 的场景，TiDB 存算分离优势明显。

### CXL 内存与数据库研究持续升温

CXL（Compute Express Link）与数据库系统的交叉研究持续活跃。关键信号：CXL 3.0（PCIe 6.0 基础）预计 2026 年产品化，有望从根本上改变内存数据库的扩展模式——从 scale-out 分片走向 scale-up 弹性内存池（EDBT 2026 论文已探讨动态 CXL 内存池分配）。

## 💾 存储引擎

### LSM-tree KV Store 综述（ArXiv 2025）

ArXiv 论文 *Rethinking LSM-tree based Key-Value Stores: A Survey* (2507.09642) 为 LSM-tree 研究提供了最新的系统性分类框架。论文从 flush/compaction 性能优化和基础 KV 操作改进两个维度梳理现有方案，并覆盖分布式场景下多租户（万级到百万级用户）的差异化需求。

虽然发在 2025 年 arxiv，但这项综述对理解当前 LSM-tree 研究全景仍有参考价值——特别是多租户 Serverless 场景下的存储引擎挑战（已在 SIGMOD 2026 有相关论文呼应）。

## 🏛 湖仓

### Fluss + Paimon 实时湖仓路线图推进

Fluss 1.0 路线图中 Feature Freeze 目标为 2026-06-01，Release 目标 2026-06-15。核心能力 LakeStream 允许在已有湖仓表上直接启用流式读写，通过 union reads 打通 streaming 和 lakehouse 两层。

Fluss 最新 commit 已涉及 Hudi Flink connector 集成（#3535），以及 Iceberg LocalTime → Fluss millis-of-day 的类型转换。Apache Fluss 社区活跃度持续攀升，已进入 Apache 孵化器的成熟阶段。

## 📊 Apache Doris 4.0.7 + 时序数据库

### Doris 4.0.7 发布（7/12）

Doris 4.0 系列最新 patch release，紧随 4.0.6（6/8）发布。4.1 系列（4.1.2 发布于 6/17）持续迭代中。4.1.x 的 AI 统一存储能力持续吸引社区关注：

- **向量索引**：HNSW + IVF + IVF\_ON\_DISK 三级索引，支持十亿~万亿级向量
- **全文搜索**：BM25 评分 + ES 兼容语法 + NESTED 搜索
- **长上下文存储**：单行 100MB JSON 文档，覆盖 Agent 执行轨迹、RAG 上下文
- **存算分离**：已部署 2000+ 企业

### 时序数据库趋势

- **InfluxDB 3.x** — Pacha-Tree 存储引擎 Beta 推进，LSM-tree + 时间分区的混合架构
- **TimescaleDB** — 列存加速 + Hypertable 压缩比持续优化
- **DB-OS 融合** — 时序 DB 与 OLAP DB 边界模糊化：Doris 增强时序能力 vs InfluxDB 提升 SQL 兼容
