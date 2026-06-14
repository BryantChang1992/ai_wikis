---
type: meta
title: "源文件索引"
tags: ["meta", "sources"]
created: 2026-06-14
---

# 源文件索引 (Raw Sources)

> `sources/` 是三层架构中的 **Raw Sources 层**。这里的文件是只读的原始资料——Agent 读取但绝不修改。
> 新的源文件通过 Agent 自动 ingest 入库，或手动放入此目录。

## 当前源文件

*(待入库)*

## 入库规则

1. 源文件放入 `sources/` 后，Agent 读取、分析、生成 wiki 页面到 `wiki/`
2. 每个 wiki 页面必须在 frontmatter 的 `sources:` 字段中引用对应的源文件
3. 源文件 SHA256 去重——相同内容不重复处理
4. 源文件命名保留原始名称，避免重命名便于溯源

---

*由 CHANG_AI_TEAM Agent 维护*
