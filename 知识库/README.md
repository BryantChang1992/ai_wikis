---
type: meta
title: "CHANG_AI_TEAM 知识库"
tags: ["meta", "知识库"]
created: 2026-06-14
updated: 2026-06-14
---

# CHANG_AI_TEAM 知识库

这是 CHANG_AI_TEAM 的核心知识底座。基于 Karpathy LLM Wiki 三层架构：

```
sources/  →  wiki/  →  Schema
 (只读)      (AI维护)   (规则)
```

## 目录

- [[purpose]] — 为什么存在、研究什么
- [[schema]] — 怎么组织、怎么写
- [[log]] — 谁做了什么

---

## 第1层: Raw Sources (`sources/`)

> 原始资料，只读。Agent 从这里读取，但绝不修改。

参见 [[sources/README]]

---

## 第2层: Wiki (`wiki/`)

> LLM 生成的结构化知识，是知识库的核心产出。

### 调研报告
- [[wiki/事务模型深度调研]] — 从 ACID 到全球分布式事务（MVCC/2PC/3PC/TCC/SAGA/Percolator/Spanner/Calvin）

---

## 第3层: Schema

> 规则与配置，定义知识库如何运作。

| 文件 | 说明 |
|------|------|
| [[purpose]] | 知识库的目标、研究方向 |
| [[schema]] | 分类体系、模板、[[wikilink]] 规范 |
| [[log]] | 操作日志 |

---

*由 CHANG_AI_TEAM Agent 维护，最后更新: 2026-06-14*
