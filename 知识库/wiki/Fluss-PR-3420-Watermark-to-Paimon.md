---
type: analysis
title: "Fluss PR #3420 — Watermark → Paimon Snapshot"
sources:
  - "sources/web/fluss/Fluss-PR-3420-Watermark-Paimon-精读.md"
  - "https://github.com/apache/fluss/pull/3420"
tags:
  - "流处理"
  - "fluss"
  - "lake-tiering"
  - "paimon"
  - "watermark"
created: 2026-06-19
updated: 2026-06-19
status: draft
related: []
---

# Fluss PR #3420 — Watermark → Paimon Snapshot

## 目标

让 Fluss Lake Tiering 将 watermark 报告给 Paimon snapshot，使下游批量作业可判断分区数据是否"就绪"。

## 架构变更

**新增接口层**（fluss-common）：
- `WatermarkExtractor` — 从 rows 提取 watermark
- `LakeWriteResult` — 接口扩展，支持可选 watermark
- `LakeWriter` / `LakeCommitter` — 泛型约束升级

**Paimon 实现链路**（fluss-lake-paimon）：
```
PaimonLakeWriter（提取/聚合 per-writer max watermark）
  → PaimonLakeCommitter（传入 committable 创建）
  → PaimonWriteResultSerializer（v0 → v1 向后兼容）
```

**Flink Connector 适配**：
- `TieringSplitReader` → 创建 extractor 传递给 lake writer
- `TieringCommitOperator` → 聚合多 bucket watermark 传入 committer

## 影响范围

- **49 个文件**变更，覆盖全 lake tiering 路径（common → Paimon/Iceberg/Lance → Flink connector）
- 序列化格式升级，向后兼容
- Iceberg / Lance 实现：默认 watermark = null（API 兼容性更新）

## 关键 Insight

> Watermark → Paimon snapshot 链路打通后，下游批量作业可确定分区"就绪"，这是批流一体 Lakehouse 的**关键基础设施**。
