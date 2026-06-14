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
- `[22:45] Stark (CTO)`: **RULE** — 定义 Ingest 规则
  - schema.md 追加 Ingest 规则章节：触发条件、执行流程、去重机制、Worker 配置
  - 创建 `sources/web/`、`sources/papers/`、`sources/notes/` 子目录
  - 首次执行 Ingest 流程验证（见下方）
