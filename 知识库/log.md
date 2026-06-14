---
type: meta
title: "知识库操作日志"
tags: ["meta", "log"]
created: 2026-06-14
updated: 2026-06-14
---

# 知识库操作日志

> 时序记录所有增删改操作。格式：`[日期 时间] 操作者: 操作类型 — 描述`

## 2026-06-14

- `[23:30] Stark (CTO)`: **PUBLISH** — GitPage 周报发布
  - 新增 `tech_research/wiki_synthesis/` 子方向
  - 发布 `_posts/2026-06-14-tech-research-week-05.md`
  - 更新 `tech_research/index.html`（6 方向、18 篇报告）
  - README wikilink 修正 + 删除重复 LSM 综述文件
- `[22:00] Stark (CTO)`: **INIT** — 知识库结构化配置
  - 新建 `purpose.md`（目的定义）
  - 新建 `schema.md`（结构规则）
  - 新建 `log.md`（本文件）
  - 升级 `README.md` 为知识库索引
  - 改造 `事务模型深度调研.md`（补全 frontmatter + [[wikilink]]）
- `[22:30] Stark (CTO)`: **REFACTOR** — 落地 Karpathy 三层架构
  - 创建 `sources/` 目录（Raw Sources 层，只读源文件）
  - 创建 `wiki/` 目录（Wiki 层，LLM 生成知识）
  - 移动 `事务模型深度调研.md` → `wiki/`
  - 创建 `sources/README.md`（源文件索引）
  - 更新 `schema.md`：加入三层架构说明和数据流
  - 更新 `README.md`：按三层架构重组索引
- `[22:15] Knowledge Worker`: **INGEST** — Event Horizon (CIDR 2026)
  - 源文件: sources/papers/Event-Horizon-Asymmetric-Dependencies-Geo-Distributed-Operations.md
  - 产出: wiki/Event-Horizon-非对称依赖.md
  - 核心概念: 非对称依赖、半线性化(SL)、DeMon、事件视界
- `[22:45] Stark (CTO)`: **RULE** — 定义 Ingest 规则
  - schema.md 追加 Ingest 规则章节：触发条件、执行流程、去重机制、Worker 配置
  - 创建 `sources/web/`、`sources/papers/`、`sources/notes/` 子目录
  - 首次执行 Ingest 流程验证（Event Horizon）
- `[23:20] Stark (CTO)`: **CLEANUP** — 清理 sources 目录
  - 删除 `sources/papers/Event-Horizon-...-全文翻译.md`（翻译不应在 raw 层）
  - 入库 `LSM-based-Storage-Techniques-A-Survey.md`（精读分析）、`RaaS-Reducing-Tail-Latency-Storage-Disaggregated-DB.md`（精读分析）到 sources/papers/
- `[23:25] rd-task Worker`: **INGEST** — LSM-tree 综述 (VLDB Journal 2019)
  - 源文件: sources/papers/LSM-based-Storage-Techniques-A-Survey.md
  - 产出 7 张概念卡片: LSM-Tree 总览、写放大、合并优化、硬件适配、自动调参、二级索引、RUM 猜想
- `[23:25] rd-task Worker`: **INGEST** — RaaS (SIGMOD 2026)
  - 源文件: sources/papers/RaaS-Reducing-Tail-Latency-Storage-Disaggregated-DB.md
  - 产出 3 张概念卡片: RaaS 方案、Tail Latency 根因、Log-as-the-Database 模式
- `[22:45] rd-task Worker`: **INGEST** — Doris 调研知识卡片
  - 源文件: 技术文章/Doris调研.md + 技术文章/Doris调研/ 下 5 个子文档
  - 产出 1 张调研报告 + 7 张概念卡片
  - 调研报告: Doris 实时分析数据库深度调研
  - 概念卡片: 数据模型、Segment v2 存储格式、Compaction 策略、MPP 向量化查询引擎、Nereids CBO 优化器、架构演进、元数据与一致性复制
- `[22:55] rd-task Worker`: **INGEST** — InfluxDB 调研知识卡片
  - 源文件: 技术文章/InfluxDB调研.md + 技术文章/InfluxDB调研/ 下 5 个子文档
  - 产出 1 张调研报告 + 7 张概念卡片
  - 调研报告: InfluxDB 深度调研（从 TSM 到列存引擎）
  - 概念卡片: 数据模型、TSM 存储引擎、3 列存引擎、写入与查询路径、指标设计与基数管理、多副本与高可用、Catalog 元数据

### 2026-06-14 23:40

- **目录重组**：wiki/ 下新增 `synthesis/` 子目录，独立存放领域综述 + Lint 报告
  - 迁移 6 个文件到 `wiki/synthesis/`：LSM-Tree-存储引擎体系综述、OLAP与TSDB全景综述、分布式数据系统一致性体系、Apache-Doris-OLAP-数据库体系综述、InfluxDB-时序数据库体系综述、Lint-2026-06-14
  - 原因：综述/synthesis 与研究型页面（survey/concept）混放不利于查找
  - 影响文件：schema.md（目录结构+三层层角色表+Synthesize写入路径）、README.md（索引引用路径）、HEARTBEAT.md（转义规则+关键文件清单）
