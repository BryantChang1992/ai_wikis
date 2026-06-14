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
