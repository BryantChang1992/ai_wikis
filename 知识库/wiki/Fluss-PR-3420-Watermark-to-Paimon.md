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
related:
  - "[[Fluss-Lake层与湖仓融合]]"
  - "[[Fluss-Tiering分层架构]]"
  - "[[Fluss-整体架构]]"
  - "[[Fluss-分布式协调]]"
  - "[[流处理乱序数据管理]]"
---

# Fluss PR #3420 — Watermark → Paimon Snapshot

PR #3420 让 Fluss 在 Lake Tiering 时将 watermark 报告给 Paimon snapshot。**核心价值**：打通流处理 watermark → 湖仓 snapshot 的链路，下游批量作业可通过 Paimon snapshot 的 watermark 确定分区数据"就绪"——这是实现批流一体 Lakehouse 的关键基础设施。

## 架构变更路径

### 新增接口层（fluss-common）

| 接口 | 变更 | 说明 |
|------|------|------|
| `WatermarkExtractor` | 新增 | 从 rows 提取 watermark |
| `LakeWriteResult` | 扩展 | 支持可选 watermark 字段 |
| `LakeWriter` | 泛型升级 | 约束到 `LakeWriteResult` |
| `LakeTieringFactory` | 泛型升级 | 同上 |
| `LakeCommitter` | 泛型升级 | 同上 |

### Paimon 实现（fluss-lake-paimon）

```
PaimonLakeWriter
  └── 写入期间提取/聚合每个 writer 的最大 watermark
        ↓
PaimonLakeCommitter
  └── 聚合 watermark → 传入 committable 创建
        ↓
PaimonWriteResult (携带 watermark)
  └── PaimonWriteResultSerializer (v0 → v1 序列化升级)
```

### Flink Connector 适配（fluss-flink-common）

- **`TieringSplitReader`**：创建 watermark extractor，传递给 lake writer
- **`TieringCommitOperator`**：聚合多 bucket watermark，传入 lake committer
- **`SimpleWatermarkExtractor`**：解析简单 watermark 定义

### 其他 Lake 实现兼容

**Iceberg / Lance**：默认 watermark = null，API 兼容性更新（向后兼容）。

## 影响范围

| 维度 | 详情 |
|------|------|
| 文件变更数 | 49 个 |
| 影响路径 | common → Paimon/Iceberg/Lance → Flink connector |
| 序列化格式 | v0 → v1（nullable watermark，向后兼容） |
| 破坏性 | 无 |

## 与 [[Fluss-Lake层与湖仓融合]] 的关系

PR #3420 是 Lake Tiering 向**生产级能力**演进的关键补丁。没有 watermark → snapshot 链路时：
- 下游批量作业不知道"流数据什么时候算一段，可以开始读了"
- 只能等固定时间间隔或手动触发

有了这个链路后：
- Paimon snapshot 携带 watermark → 下游知道"这个 snapshot 覆盖到时间戳 T 为止的数据"
- 批处理作业可以按 watermark 确定性触发——真正的批流一体

## 与 [[流处理乱序数据管理]] 的关联

Watermark 在流处理中用于处理乱序数据——它是"我们不会再看到比 T 更早的数据了"的声明。PR #3420 把这个声明从 Flink 运行时扩展到了 Paimon snapshot 元数据层——**乱序管理的边界从运行时延伸到湖仓持久化层**。

## 架构意义

```
┌──────────┐    watermark(rows)    ┌──────────────┐
│  Fluss   │ ────────────────────→ │ Paimon       │
│ Tablet   │                       │ Snapshot     │
│ Server   │                       │ (带 watermark)│
└──────────┘                       └──────┬───────┘
                                          │
                                    ┌─────▼──────┐
                                    │ 下游批作业  │
                                    │ "读到 T 为止"│
                                    └────────────┘
```

这是 **Fluss 从"流存储"到"批流一体 Lakehouse 基础架构"演进的关键一步**。Watermark 是流和批之间的时间契约——一旦这个契约在 Paimon snapshot 中可查询，批处理就可以按时间确定性消费流数据。
