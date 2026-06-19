# Fluss PR #3420: [lake/tiering] Support Reporting Watermark to Paimon Snapshot

- **URL**: https://github.com/apache/fluss/pull/3420
- **来源**: GitHub apache/fluss, by Shawn-Hx
- **日期**: 2026-06 (opened ~2 weeks ago)

## 核心变更

让 Fluss 在 Lake Tiering 时将 watermark 报告给 Paimon snapshot。

### 架构变更路径

**新增接口层**（fluss-common）：
- `WatermarkExtractor` — 从 rows 提取 watermark
- `LakeWriteResult` — 接口扩展，支持可选 watermark
- `LakeWriter` / `LakeTieringFactory` / `LakeCommitter` — 泛型约束升级到 LakeWriteResult

**Paimon 实现**（fluss-lake-paimon）：
- `PaimonLakeWriter`：写入期间提取/聚合每个 writer 的最大 watermark
- `PaimonLakeCommitter`：将聚合后的 watermark 传入 committable 创建
- `PaimonWriteResult`：实现 LakeWriteResult，携带 watermark
- `PaimonWriteResultSerializer`：序列化版本升级，编码 nullable watermark

**Flink Connector 适配**（fluss-flink-common）：
- `TieringSplitReader` → 创建 watermark extractor，传递给 lake writer
- `TieringCommitOperator` → 聚合多 bucket watermark，传入 lake committer
- `SimpleWatermarkExtractor` → 新增，解析简单 watermark 定义

**其他 Lake 实现适配**（Iceberg / Lance）：默认 watermark = null，API 兼容性更新。

### 影响范围

- 49 个文件变更
- 影响全 lake tiering 路径：common → Paimon/Iceberg/Lance → Flink connector
- 序列化格式升级（向后兼容 v0 → v1）

## 关键 Insight

Fluss 的 Lake Tiering 在向生产级能力演进：watermark 到 snapshot 的链路打通后，下游批量作业可以通过 Paimon snapshot 的 watermark 确定分区数据"就绪"，这是实现批流一体 Lakehouse 的关键基础设施。
