---
type: concept
title: "Fluss KV 存储（RocksDB）"
sources:
  - "https://github.com/BryantChang1992/ai_memory_chang_ai_team/blob/master/tech_research/fluss/02-存储引擎模块.html"
tags:
  - "Fluss"
  - "RocksDB"
  - "KV Store"
  - "存储引擎"
  - "WAL"
  - "Snapshot"
created: 2026-06-15
updated: 2026-06-15
status: draft
related:
  - "[[Fluss-存储引擎]]"
  - "[[Fluss-整体架构]]"
  - "[[LSM-Tree]]"
---

# Fluss KV 存储（RocksDB）

## 定义

Fluss KV 存储是为 **Primary Key 表** 提供类数据库 Upsert/Delete 语义的本地存储层。底层引擎为 RocksDB（LSM-tree），但 Fluss 对 RocksDB 的使用方式有一个关键设计创新——**WAL 不是额外文件，而是直接复用 changelog LogTablet 的 segment**。

## 核心组件

<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 700 180" width="700" height="180">
  <defs>
    <marker id="arrow-fkv1" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <path d="M0,0 L8,3 L0,6 Z" fill="currentColor"/>
    </marker>
  </defs>
  <rect x="10" y="5" width="150" height="26" rx="5" fill="transparent" stroke="currentColor" stroke-width="1.2"/>
  <text x="85" y="18" font-family="sans-serif" font-size="12" fill="currentColor" text-anchor="middle" dominant-baseline="middle" font-weight="bold">KvManager（全局入口）</text>
  <line x1="85" y1="31" x2="85" y2="45" stroke="currentColor" stroke-width="1.2"/>
  <text x="105" y="45" font-family="sans-serif" font-size="11" fill="currentColor" text-anchor="start" dominant-baseline="middle">→ KvTablet（单 bucket 的 KV 管理单元）</text>
  <line x1="105" y1="55" x2="105" y2="70" stroke="currentColor" stroke-width="1.2"/>
  <!-- Sub items -->
  <line x1="50" y1="70" x2="680" y2="70" stroke="currentColor" stroke-width="1"/>
  <line x1="50" y1="70" x2="50" y2="82" stroke="currentColor" stroke-width="1"/>
  <line x1="140" y1="70" x2="140" y2="82" stroke="currentColor" stroke-width="1"/>
  <line x1="300" y1="70" x2="300" y2="82" stroke="currentColor" stroke-width="1"/>
  <line x1="430" y1="70" x2="430" y2="82" stroke="currentColor" stroke-width="1"/>
  <line x1="550" y1="70" x2="550" y2="82" stroke="currentColor" stroke-width="1"/>
  <line x1="640" y1="70" x2="640" y2="82" stroke="currentColor" stroke-width="1"/>
  <text x="12" y="97" font-family="sans-serif" font-size="11" fill="currentColor" text-anchor="start" dominant-baseline="middle">├ RocksDBKv</text>
  <text x="12" y="112" font-family="sans-serif" font-size="9" fill="currentColor" text-anchor="start" dominant-baseline="middle" font-style="italic">　　→ RocksDB 实例</text>
  <text x="102" y="97" font-family="sans-serif" font-size="11" fill="currentColor" text-anchor="start" dominant-baseline="middle">├ WalBuilder</text>
  <text x="102" y="112" font-family="sans-serif" font-size="9" fill="currentColor" text-anchor="start" dominant-baseline="middle" font-style="italic">　　（三种格式）</text>
  <text x="210" y="97" font-family="sans-serif" font-size="11" fill="currentColor" text-anchor="start" dominant-baseline="middle">├ PeriodicSnapshotManager</text>
  <text x="210" y="112" font-family="sans-serif" font-size="9" fill="currentColor" text-anchor="start" dominant-baseline="middle" font-style="italic">　　（定时快照触发）</text>
  <text x="380" y="97" font-family="sans-serif" font-size="11" fill="currentColor" text-anchor="start" dominant-baseline="middle">├ RowMerger</text>
  <text x="380" y="112" font-family="sans-serif" font-size="9" fill="currentColor" text-anchor="start" dominant-baseline="middle" font-style="italic">　　（四种实现）</text>
  <text x="480" y="97" font-family="sans-serif" font-size="11" fill="currentColor" text-anchor="start" dominant-baseline="middle">├ PartialUpdater</text>
  <text x="480" y="112" font-family="sans-serif" font-size="9" fill="currentColor" text-anchor="start" dominant-baseline="middle" font-style="italic">　　（部分列更新）</text>
  <text x="560" y="97" font-family="sans-serif" font-size="11" fill="currentColor" text-anchor="start" dominant-baseline="middle">├ AutoIncrementManager</text>
  <text x="560" y="112" font-family="sans-serif" font-size="9" fill="currentColor" text-anchor="start" dominant-baseline="middle" font-style="italic">　　（自增 ID）</text>
  <text x="620" y="97" font-family="sans-serif" font-size="11" fill="currentColor" text-anchor="start" dominant-baseline="middle">└ KvPreWriteBuffer</text>
  <text x="620" y="112" font-family="sans-serif" font-size="9" fill="currentColor" text-anchor="start" dominant-baseline="middle" font-style="italic">　　（预写缓冲）</text>
</svg>

## WAL 设计：Write-Once Read-Multiple

Fluss KV 的最大设计创新。传统 RocksDB 有自己的 WAL 文件（`*.log`），但 Fluss **不用 RocksDB 自带的 WAL**。

### 机制

写入路径：`putKv(row)` → RocksDB 写入 + **同时写入 changelog LogTablet**

恢复路径：**重放 changelog LogTablet** 来重建 RocksDB 状态（而非读 WAL 文件）

<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 65" width="600" height="65">
  <defs>
    <marker id="arrow-fkv2" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <path d="M0,0 L8,3 L0,6 Z" fill="currentColor"/>
    </marker>
  </defs>
  <text x="10" y="16" font-family="sans-serif" font-size="12" fill="currentColor" text-anchor="start" dominant-baseline="middle" font-weight="bold">传统方案：</text>
  <text x="100" y="16" font-family="sans-serif" font-size="11" fill="currentColor" text-anchor="start" dominant-baseline="middle">写 → RocksDB WAL + RocksDB SST → 恢复时读 WAL</text>
  <text x="10" y="40" font-family="sans-serif" font-size="12" fill="currentColor" text-anchor="start" dominant-baseline="middle" font-weight="bold">Fluss 方案：</text>
  <text x="100" y="40" font-family="sans-serif" font-size="11" fill="currentColor" text-anchor="start" dominant-baseline="middle">写 → RocksDB SST + changelog LogTablet → 恢复时重放 LogTablet</text>
</svg>

**优势**：changelog 既是外部可读的 CDC 流，又是内部恢复的 WAL。一份数据两份用途，消除了 WAL 文件的额外 IO。

### 三种 WalBuilder 实现

| 实现 | LogFormat | 适用场景 |
|------|-----------|---------|
| `ArrowWalBuilder` | ARROW | 通用列式 WAL |
| `CompactedWalBuilder` | COMPACTED | PK 表（同 key 合并，减少 WAL 体积） |
| `IndexWalBuilder` | INDEXED | PK 表点查优化 |

## Snapshot 全链路（近 30 个类）

<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 720 200" width="720" height="200">
  <defs>
    <marker id="arrow-fkv3" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <path d="M0,0 L8,3 L0,6 Z" fill="currentColor"/>
    </marker>
  </defs>
  <rect x="15" y="5" width="170" height="26" rx="5" fill="transparent" stroke="currentColor" stroke-width="1.2"/>
  <text x="100" y="18" font-family="sans-serif" font-size="11" fill="currentColor" text-anchor="middle" dominant-baseline="middle">PeriodicSnapshotManager</text>
  <text x="200" y="18" font-family="sans-serif" font-size="9" fill="currentColor" text-anchor="start" dominant-baseline="middle" font-style="italic">（定时触发，周期可配）</text>
  <line x1="100" y1="31" x2="100" y2="45" stroke="currentColor" stroke-width="1.2"/>
  <text x="120" y="45" font-family="sans-serif" font-size="11" fill="currentColor" text-anchor="start" dominant-baseline="middle">→ KvTabletSnapshotTarget（执行快照）</text>
  <line x1="120" y1="55" x2="120" y2="70" stroke="currentColor" stroke-width="1.2"/>
  <text x="140" y="70" font-family="sans-serif" font-size="11" fill="currentColor" text-anchor="start" dominant-baseline="middle">→ RocksIncrementalSnapshot</text>
  <text x="300" y="70" font-family="sans-serif" font-size="9" fill="currentColor" text-anchor="start" dominant-baseline="middle" font-style="italic">（RocksDB Checkpoint → 仅传输变更 SST）</text>
  <line x1="140" y1="80" x2="140" y2="95" stroke="currentColor" stroke-width="1.2"/>
  <text x="160" y="95" font-family="sans-serif" font-size="11" fill="currentColor" text-anchor="start" dominant-baseline="middle">→ KvSnapshotDataUploader（上传至远程 S3/HDFS）</text>
  <line x1="160" y1="105" x2="160" y2="120" stroke="currentColor" stroke-width="1.2"/>
  <text x="180" y="120" font-family="sans-serif" font-size="11" fill="currentColor" text-anchor="start" dominant-baseline="middle">→ CompletedKvSnapshotCommitter（提交快照元数据）</text>
  <line x1="180" y1="130" x2="180" y2="145" stroke="currentColor" stroke-width="1.2"/>
  <text x="200" y="145" font-family="sans-serif" font-size="11" fill="currentColor" text-anchor="start" dominant-baseline="middle">→ ZooKeeperCompletedSnapshotHandleStore（ZK 记录）</text>
</svg>

关键组件：
- **SharedKvFileRegistry**：去重已存在于远程存储的 SST 文件，避免重复上传
- **KvSnapshotDataDownloader**：Tablet 迁移/恢复时下载快照
- **SnapshotsCleaner**：清理过期快照，基于租约管理

## RowMerger：四种行合并策略

| 实现 | 语义 | 典型场景 |
|------|------|---------|
| `DefaultRowMerger` | 覆盖写入（UPSERT） | 标准 PK 表 |
| `FirstRowRowMerger` | 保留首行（FIRST_ROW） | 去重场景 |
| `VersionedRowMerger` | 基于版本号比较 | 乐观并发控制 |
| `AggregateRowMerger` | 聚合（SUM/MAX/MIN/COUNT/ROARING_BITMAP...） | 实时指标计算 |

支持的聚合函数：SUM / MAX / MIN / PRODUCT / FIRST_VALUE / LAST_VALUE / FIRST_NON_NULL_VALUE / LAST_NON_NULL_VALUE / BOOL_AND / BOOL_OR / STRING_AGG / LISTAGG / ROARING_BITMAP_32 / ROARING_BITMAP_64

## RocksDB 资源管理

`RocksDBResourceContainer` 统一管理：
- **shared write buffer**：多 KvTablet 共享 WriteBuffer
- **shared block cache**：多 KvTablet 共享 BlockCache
- **rate limiter**：限速器防止 Compaction IO 风暴

## PartialUpdater

支持对 PK 表的部分列更新——只更新指定列，不影响其余列。通过 `PartialUpdaterCache` 缓存未写入的列值。

---

> **关键洞察**：Fluss KV 的 WAL 复用设计是"流存储 + 数据库"融合的典范。传统数据库的 WAL 是内部实现细节，外界不可见；Fluss 的 changelog LogTablet 既是恢复机制（内部），又是 CDC 流（外部）。这使得 Fluss 天然就是一个 CDC Source——无需 Debezium 之类的额外工具。
