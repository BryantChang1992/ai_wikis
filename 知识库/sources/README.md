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
| `web/` | 网页存档 | 技术调研周报中的参考链接 |
| `papers/` | 论文原文 | 论文精读、调研中引用的论文 |
| `notes/` | 原始笔记 | 会议记录、随手笔记、外部资料 |

## 入库规则

1. 源文件放入 `sources/` 后，Agent 读取、分析、生成 wiki 页面到 `wiki/`
2. 每个 wiki 页面必须在 frontmatter 的 `sources:` 字段中引用对应的源文件
3. 源文件 SHA256 去重——相同内容不重复处理
4. 源文件命名保留原始名称，避免重命名便于溯源

## 当前源文件列表

### papers/
- [Event-Horizon-Asymmetric-Dependencies-Geo-Distributed-Operations.md](papers/Event-Horizon-Asymmetric-Dependencies-Geo-Distributed-Operations.md) — CIDR 2026，TU Delft，非对称依赖降低跨地域延迟（精读分析）
- [LSM-based-Storage-Techniques-A-Survey.md](papers/LSM-based-Storage-Techniques-A-Survey.md) — VLDB Journal 2019，UC Irvine，LSM-tree 综述（精读分析）
- [RaaS-Reducing-Tail-Latency-Storage-Disaggregated-DB.md](papers/RaaS-Reducing-Tail-Latency-Storage-Disaggregated-DB.md) — SIGMOD 2026，Purdue，存储计算分离 Tail Latency 消除（精读分析）

### web/
*(待入库)*

### notes/
*(待入库)*

---

*由 CHANG_AI_TEAM Agent 维护，最后更新: 2026-06-14*
