---
type: meta
title: "源文件索引"
tags: ["meta", "sources"]
created: 2026-06-14
updated: 2026-06-14
---

# 源文件索引 (Raw Sources)

> `sources/` 是三层架构中的 **Raw Sources 层**。这里的文件是只读的原始资料——Agent 读取但绝不修改。

## 子目录

| 目录 | 内容 | 来源 |
|------|------|------|
| `papers/` | 论文原文（PDF）+ 精读分析 + 翻译 | 论文精读、调研中引用的论文 |
| `web/` | 网页存档 | 技术调研周报中的参考链接 |
| `notes/` | 原始笔记 | 会议记录、随手笔记、外部资料 |

## 论文目录结构

每篇论文一个父目录，内含英文原文 PDF + 精读分析 + 全文翻译：

```
sources/papers/
├── Event-Horizon/
│   ├── Event-Horizon-CIDR2026.pdf    ← 英文原文
│   ├── 精读分析.md                    ← 精读分析
│   └── 全文翻译.md                    ← 中文全文翻译
├── LSM-Survey/
│   ├── LSM-Survey-VLDBJ2019.pdf
│   ├── 精读分析.md
│   └── 全文翻译.md
└── RaaS/
    ├── RaaS-SIGMOD2026.pdf
    ├── 精读分析.md
    └── 全文翻译.md
```

## 入库规则

1. 每篇论文建一个以论文简称命名的父目录
2. 父目录下放：英文原文 PDF、精读分析.md、全文翻译.md
3. Agent 读取时优先用精读分析作为 ingest 源材料，PDF 作为溯源
4. 源文件 SHA256 去重——相同内容不重复处理

## 当前源文件列表

### papers/
- [Event-Horizon/](papers/Event-Horizon/) — CIDR 2026，TU Delft，非对称依赖降低跨地域延迟
  - Event-Horizon-CIDR2026.pdf（原文，1.6MB）
  - 精读分析.md / 全文翻译.md
- [LSM-Survey/](papers/LSM-Survey/) — VLDB Journal 2019，UC Irvine，LSM-tree 综述
  - LSM-Survey-VLDBJ2019.pdf（原文，879KB）
  - 精读分析.md / 全文翻译.md
- [RaaS/](papers/RaaS/) — SIGMOD 2026，Purdue，存储计算分离 Tail Latency 消除
  - RaaS-SIGMOD2026.pdf（原文，3.2MB）
  - 精读分析.md / 全文翻译.md

### web/
*(待入库)*

### notes/
*(待入库)*

---

*由 CHANG_AI_TEAM Agent 维护，最后更新: 2026-06-14*
