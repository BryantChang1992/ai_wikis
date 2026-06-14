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
| `papers/` | 论文原文（PDF）+ 附属子文档 | 论文精读、调研中引用的论文 |
| `web/` | 网页存档 | 技术调研周报中的参考链接 |
| `notes/` | 原始笔记 | 会议记录、随手笔记、外部资料 |

## 论文目录结构

```
sources/papers/
├── 论文原文.pdf              ← 论文英文原文，只读
├── 论文简称/                 ← 附属子文档目录
│   ├── 精读分析.md           ← AI 或人类写的精读分析
│   └── 全文翻译.md           ← 中文全文翻译（可选）
```

## 入库规则

1. 论文原文（PDF）直接放在 `sources/papers/` 下
2. 精读分析、翻译等附属文档放在以论文简称命名的子目录中
3. Agent 读取时优先用精读分析作为 ingest 源材料，PDF 作为溯源
4. 源文件 SHA256 去重——相同内容不重复处理

## 当前源文件列表

### papers/
- [Event-Horizon-CIDR2026.pdf](papers/Event-Horizon-CIDR2026.pdf) — CIDR 2026，TU Delft，非对称依赖降低跨地域延迟（原文 PDF，1.6MB）
  - [Event-Horizon/精读分析.md](papers/Event-Horizon/精读分析.md) — 精读分析稿
  - [Event-Horizon/全文翻译.md](papers/Event-Horizon/全文翻译.md) — 中文全文翻译
- [LSM-Survey-VLDBJ2019.pdf](papers/LSM-Survey-VLDBJ2019.pdf) — VLDB Journal 2019，UC Irvine，LSM-tree 综述（原文 PDF，879KB）
  - [LSM-Survey/精读分析.md](papers/LSM-Survey/精读分析.md) — 精读分析稿
  - [LSM-Survey/全文翻译.md](papers/LSM-Survey/全文翻译.md) — 中文全文翻译
- [RaaS-SIGMOD2026.pdf](papers/RaaS-SIGMOD2026.pdf) — SIGMOD 2026，Purdue，存储计算分离 Tail Latency 消除（原文 PDF，3.2MB）
  - [RaaS/精读分析.md](papers/RaaS/精读分析.md) — 精读分析稿
  - [RaaS/全文翻译.md](papers/RaaS/全文翻译.md) — 中文全文翻译

### web/
*(待入库)*

### notes/
*(待入库)*

---

*由 CHANG_AI_TEAM Agent 维护，最后更新: 2026-06-14*
