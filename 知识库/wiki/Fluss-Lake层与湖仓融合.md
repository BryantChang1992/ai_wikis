---
type: analysis
title: "Fluss Lake 层与湖仓融合 — 实时存储 + 数据湖一体化"
sources:
  - "sources/web/fluss/06-Lake层与湖仓融合.md"
tags:
  - Fluss
  - Lakehouse
  - Iceberg
  - Paimon
  - 数据湖
  - Lake Storage
created: 2026-06-15
updated: 2026-06-15
status: draft
related:
  - "[[Fluss-整体架构]]"
  - "[[Fluss-客户端与计算集成]]"
  - "[[Fluss-Tiering分层架构]]"
diagram: "diagram/fluss-lake-backends.svg"

---

# Fluss Lake 层与湖仓融合 — 实时存储 + 数据湖一体化

> **Key Insight**：Fluss 的 Lake 层不只是"把数据存到 S3"——它是 **Streaming Table → Lakehouse Table 的一体化转换引擎**。通过 Tiering 作业将本地 Log/KV 数据实时转换为 Parquet/Arrow 格式写入 Iceberg/Paimon/Hudi/Lance，实现毫秒级写入 + 分钟级数据分析的统一架构。与 Kafka KIP-405 的根本区别在于：KIP-405 是"磁盘空间卸载"，Fluss Lake 是"语义级别数据湖融合"。

---

## 1. Lake 存储插件架构

<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 700 200" width="700" height="200">
  <defs>
    <marker id="arrow-fl1" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <path d="M0,0 L8,3 L0,6 Z" fill="currentColor"/>
    </marker>
  </defs>
  <rect x="10" y="5" width="200" height="26" rx="5" fill="transparent" stroke="currentColor" stroke-width="1.2"/>
  <text x="110" y="18" font-family="sans-serif" font-size="12" fill="currentColor" text-anchor="middle" dominant-baseline="middle">LakeStoragePlugin (SPI)</text>
  <line x1="110" y1="31" x2="110" y2="45" stroke="currentColor" stroke-width="1.2"/>
  <text x="130" y="45" font-family="sans-serif" font-size="11" fill="currentColor" text-anchor="start" dominant-baseline="middle">→ LakeStorage.createLakeStorage()</text>
  <line x1="130" y1="55" x2="130" y2="68" stroke="currentColor" stroke-width="1.2"/>
  <text x="130" y="68" font-family="sans-serif" font-size="11" fill="currentColor" text-anchor="start" dominant-baseline="middle">→ LakeCatalog (createTable/dropTable/listTables/alterTable)</text>
  <line x1="130" y1="78" x2="130" y2="90" stroke="currentColor" stroke-width="1.2"/>
  <text x="130" y="90" font-family="sans-serif" font-size="11" fill="currentColor" text-anchor="start" dominant-baseline="middle">→ LakeTable</text>
  <line x1="130" y1="100" x2="130" y2="115" stroke="currentColor" stroke-width="1.2"/>
  <text x="150" y="115" font-family="sans-serif" font-size="11" fill="currentColor" text-anchor="start" dominant-baseline="middle">→ LakeTableRead (谓词下推读取)</text>
  <text x="150" y="135" font-family="sans-serif" font-size="11" fill="currentColor" text-anchor="start" dominant-baseline="middle">→ LakeTableAppend (追加写)</text>
  <text x="150" y="155" font-family="sans-serif" font-size="11" fill="currentColor" text-anchor="start" dominant-baseline="middle">→ LakeTableDelta (Delta 写：Upsert/Delete)</text>
</svg>

### 四种 Lake 后端

| 后端 | 模块 | 文件数 | 完整度 |
|------|------|--------|--------|
| **Iceberg** | `fluss-lake-iceberg` | ~35 | ★★★★★ 完整 |
| **Paimon** | `fluss-lake-paimon` | ~30 | ★★★★★ 完整 |
| **Hudi** | `fluss-lake-hudi` | ~7 | ★★☆☆☆ 基础 |
| **Lance** | `fluss-lake-lance` | ~12 | ★★★☆☆ 部分 |

---

## 2. Iceberg 集成全链路

<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 720 180" width="720" height="180">
  <defs>
    <marker id="arrow-fl2" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <path d="M0,0 L8,3 L0,6 Z" fill="currentColor"/>
    </marker>
  </defs>
  <rect x="10" y="5" width="170" height="28" rx="5" fill="transparent" stroke="currentColor" stroke-width="1.2"/>
  <text x="95" y="19" font-family="sans-serif" font-size="12" fill="currentColor" text-anchor="middle" dominant-baseline="middle">IcebergLakeStorage</text>
  <line x1="95" y1="33" x2="95" y2="48" stroke="currentColor" stroke-width="1.2"/>
  <line x1="35" y1="48" x2="680" y2="48" stroke="currentColor" stroke-width="1.2"/>
  <line x1="35" y1="48" x2="35" y2="65" stroke="currentColor" stroke-width="1.2"/>
  <line x1="180" y1="48" x2="180" y2="65" stroke="currentColor" stroke-width="1.2"/>
  <line x1="340" y1="48" x2="340" y2="65" stroke="currentColor" stroke-width="1.2"/>
  <line x1="500" y1="48" x2="500" y2="65" stroke="currentColor" stroke-width="1.2"/>
  <line x1="660" y1="48" x2="660" y2="65" stroke="currentColor" stroke-width="1.2"/>
  <!-- Row 1 -->
  <text x="12" y="83" font-family="sans-serif" font-size="11" fill="currentColor" text-anchor="start" dominant-baseline="middle">├ IcebergLakeCatalog</text>
  <text x="12" y="100" font-family="sans-serif" font-size="10" fill="currentColor" text-anchor="start" dominant-baseline="middle" font-style="italic">　　（建表、管理 Namespace）</text>
  <text x="157" y="83" font-family="sans-serif" font-size="11" fill="currentColor" text-anchor="start" dominant-baseline="middle">├ IcebergLakeWriter</text>
  <text x="157" y="100" font-family="sans-serif" font-size="10" fill="currentColor" text-anchor="start" dominant-baseline="middle" font-style="italic">　　─ AppendOnlyTaskWriter</text>
  <text x="157" y="115" font-family="sans-serif" font-size="10" fill="currentColor" text-anchor="start" dominant-baseline="middle" font-style="italic">　　─ DeltaTaskWriter</text>
  <text x="317" y="83" font-family="sans-serif" font-size="11" fill="currentColor" text-anchor="start" dominant-baseline="middle">├ IcebergLakeCommitter</text>
  <text x="317" y="100" font-family="sans-serif" font-size="10" fill="currentColor" text-anchor="start" dominant-baseline="middle" font-style="italic">　　（收集 WriteResult →</text>
  <text x="317" y="115" font-family="sans-serif" font-size="10" fill="currentColor" text-anchor="start" dominant-baseline="middle" font-style="italic">　　提交 Snapshot → 过期清理）</text>
  <text x="477" y="83" font-family="sans-serif" font-size="11" fill="currentColor" text-anchor="start" dominant-baseline="middle">├ IcebergLakeSource</text>
  <text x="477" y="100" font-family="sans-serif" font-size="10" fill="currentColor" text-anchor="start" dominant-baseline="middle" font-style="italic">　　（Split 规划 +</text>
  <text x="477" y="115" font-family="sans-serif" font-size="10" fill="currentColor" text-anchor="start" dominant-baseline="middle" font-style="italic">　　Parquet → InternalRow）</text>
  <text x="637" y="83" font-family="sans-serif" font-size="11" fill="currentColor" text-anchor="start" dominant-baseline="middle">└ IcebergRewriteDataFiles</text>
  <text x="637" y="100" font-family="sans-serif" font-size="10" fill="currentColor" text-anchor="start" dominant-baseline="middle" font-style="italic">　　（Compaction：</text>
  <text x="637" y="115" font-family="sans-serif" font-size="10" fill="currentColor" text-anchor="start" dominant-baseline="middle" font-style="italic">　　合并小文件 +</text>
  <text x="637" y="130" font-family="sans-serif" font-size="10" fill="currentColor" text-anchor="start" dominant-baseline="middle" font-style="italic">　　清理 Delete Files）</text>
</svg>

### 写入模式

| 表类型 | Writer | Iceberg 操作 |
|--------|--------|-------------|
| 普通表 (Log Table) | `AppendOnlyTaskWriter` | `AppendFiles` |
| PK 表 (KV Table) | `DeltaTaskWriter` + `GenericRecordDeltaWriter` | `RowDelta` |
| Merge-Engine 表 | `DeltaTaskWriter` (aggregate mode) | `RowDelta` + rewrite |

读取路径支持三级谓词下推：Partition filter（目录级）→ Row group filter（Parquet 统计信息）→ Arrow 统计信息 filter（列 min/max/null-count）。

---

## 3. Paimon 集成 — MergeTree 写入

Paimon 集成的一个关键亮点是 `MergeTreeWriter`——直接写入 Paimon 的 LSM 格式，支持 PK 表和 Merge Engine。此外还支持：

- **DV (Deletion Vector) 表**：Paimon 0.9+ 增量删除机制
- **SortedRecordReader**：按 PK 排序读取，支持 Merge-on-Read
- **AppendOnlyWriter**：Arrow 原生列式零拷贝写入

---

## 4. Lance — Arrow-Native 零拷贝

Lance 是新兴的 Arrow-native 列式存储格式。Fluss 集成它的核心优势：

<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 50" width="600" height="50">
  <defs>
    <marker id="arrow-fl3" markerWidth="10" markerHeight="7" refX="10" refY="3.5" orient="auto">
      <path d="M0,0 L10,3.5 L0,7 Z" fill="currentColor"/>
    </marker>
  </defs>
  <rect x="10" y="8" width="200" height="26" rx="5" fill="transparent" stroke="currentColor" stroke-width="1.2"/>
  <text x="110" y="21" font-family="sans-serif" font-size="12" fill="currentColor" text-anchor="middle" dominant-baseline="middle">Fluss Arrow batch</text>
  <line x1="210" y1="21" x2="260" y2="21" stroke="currentColor" stroke-width="1.5" marker-end="url(#arrow-fl3)"/>
  <rect x="263" y="8" width="200" height="26" rx="5" fill="transparent" stroke="currentColor" stroke-width="1.2"/>
  <text x="363" y="21" font-family="sans-serif" font-size="12" fill="currentColor" text-anchor="middle" dominant-baseline="middle">ShadedArrowBatchWriter</text>
  <line x1="463" y1="21" x2="510" y2="21" stroke="currentColor" stroke-width="1.5" marker-end="url(#arrow-fl3)"/>
  <text x="520" y="21" font-family="sans-serif" font-size="12" fill="currentColor" text-anchor="start" dominant-baseline="middle">Lance 文件（零拷贝）</text>
</svg>

这是四种后端中与 Fluss Arrow 内部格式最天然契合的方案。

---

## 5. 与 Kafka KIP-405 的本质区别

| 维度 | Fluss Lake | Kafka KIP-405 (2.8+) |
|------|-----------|----------------------|
| **目标** | 写入数据湖，支持分析查询 | 将日志卸载到 S3，释放本地磁盘 |
| **存储格式** | Parquet / Arrow / Paimon format | 原始 `.log` segment（二进制相同） |
| **可查询性** | ✅ Trino/Spark/Flink 可直接查询 | ❌ 仅内部读取 |
| **格式转换** | ✅ 实时 Arrow → Parquet 转换 | ❌ 不转换 |
| **Schema 管理** | ✅ Lake Catalog + schema evolution | ❌ 无 schema |
| **Delete/Update** | ✅ RowDelta / Position Delete | ❌ 不支持 |
| **Compaction** | ✅ RewriteDataFile | ❌ 仅 log compaction |

### 设计哲学

<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 380 130" width="380" height="130">
  <defs>
    <marker id="arrow-fl4" markerWidth="10" markerHeight="7" refX="10" refY="3.5" orient="auto">
      <path d="M0,0 L10,3.5 L0,7 Z" fill="currentColor"/>
    </marker>
  </defs>
  <text x="10" y="18" font-family="sans-serif" font-size="13" fill="currentColor" text-anchor="start" dominant-baseline="middle" font-weight="bold">Fluss = Streaming Storage + Lakehouse Integration</text>

  <rect x="110" y="32" width="150" height="26" rx="6" fill="transparent" stroke="currentColor" stroke-width="1.2"/>
  <text x="185" y="45" font-family="sans-serif" font-size="12" fill="currentColor" text-anchor="middle" dominant-baseline="middle">实时写入 (ms 级)</text>

  <line x1="185" y1="58" x2="185" y2="72" stroke="currentColor" stroke-width="1.5" marker-end="url(#arrow-fl4)"/>

  <rect x="85" y="75" width="200" height="26" rx="6" fill="transparent" stroke="currentColor" stroke-width="1.2"/>
  <text x="185" y="88" font-family="sans-serif" font-size="12" fill="currentColor" text-anchor="middle" dominant-baseline="middle">Fluss Tablet (oltp level)</text>

  <line x1="185" y1="101" x2="185" y2="112" stroke="currentColor" stroke-width="1" stroke-dasharray="4,3"/>
  <text x="185" y="115" font-family="sans-serif" font-size="10" fill="currentColor" text-anchor="middle" dominant-baseline="middle" font-style="italic">async tiering (minute-level)</text>
  <line x1="185" y1="118" x2="185" y2="128" stroke="currentColor" stroke-width="1.5" marker-end="url(#arrow-fl4)"/>

  <rect x="80" y="130" width="210" height="26" rx="6" fill="transparent" stroke="currentColor" stroke-width="1.2"/>
  <text x="185" y="143" font-family="sans-serif" font-size="12" fill="currentColor" text-anchor="middle" dominant-baseline="middle">Lakehouse (olap level)</text>
</svg>

这不是"存储分层"，而是 **"实时存储 + 数据湖"的融合架构**——与 Kafka 的"消息队列 + 外部 ETL"是完全不同的范式。

---

*源文件: Fluss 源码分析 06，CHANG_AI_TEAM CTO，2026-06-10*
