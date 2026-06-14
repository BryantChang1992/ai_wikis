---
type: meta
title: "知识库的结构规则"
tags: ["meta", "schema"]
created: 2026-06-14
updated: 2026-06-14
---

# 知识库的结构规则

## 页面分类

| 类型 | 说明 | 示例 |
|------|------|------|
| `survey` | 调研报告 — 对技术主题的系统性研究 | 事务模型深度调研 |
| `decision` | 技术决策 — 选型理由、架构变更记录 | 为什么选择 X 而不是 Y |
| `analysis` | 架构分析 — 源码阅读、系统设计拆解 | Fluss 存储引擎设计 |
| `lesson` | 踩坑记录 — 故障复盘、教训总结 | Week 04 调研踩坑 |
| `concept` | 概念卡片 — 单一技术概念的深度解释 | MVCC、LSM-Tree |
| `meta` | 元信息 — 知识库自身的说明文件 | purpose、schema、log |

## Frontmatter 模板

```yaml
---
type: survey | decision | analysis | lesson | concept | meta
title: "标题"
sources:
  - "源文件名或URL"  # 知识来源，便于溯源
tags:
  - "标签1"
  - "标签2"
created: YYYY-MM-DD
updated: YYYY-MM-DD
status: draft | reviewed | final | deprecated
related:
  - "[[相关页面1]]"
  - "[[相关页面2]]"
---
```

### 字段说明
- **type**：必填，决定知识库如何分类和组织
- **title**：必填，人类可读的标题
- **sources**：强烈建议，记录知识来源（论文、文档、源码链接）
- **tags**：必填，至少 1 个标签
- **status**：`draft`（初稿）→ `reviewed`（已审核）→ `final`（定稿）→ `deprecated`（已过时）
- **related**：建议，[[wikilink]] 链接到相关知识页面

## 命名约定

- 文件名 = 标题（中文即可，Obsidian 友好）
- 避免特殊字符（`/` `\` `:` 等）
- 同类型文件用相同命名风格

## [[wikilink]] 规范

- **页面链接**：`[[页面名]]` — 链接到同一 vault 内的页面
- **标题链接**：`[[页面名#标题]]` — 链接到页面内具体章节
- **别名链接**：`[[页面名|显示文本]]` — 链接但显示不同文字
- 每个概念首次出现时优先用 `[[wikilink]]` 而非裸文本

## Agent 写入规则

1. **写前必读** `purpose.md` + 本文档
2. 新建页面必须包含完整的 frontmatter
3. 必须在 `[[README]]` 中更新知识条目列表
4. 必须在 `[[log]]` 中追加操作记录
5. 检查是否有可关联的已有页面，加 `[[wikilink]]`
6. 写完后 `git add -A && git commit && git push`

---

*本文件定义了知识库的"怎么做"。Agent 写入知识库时必须遵循。*
