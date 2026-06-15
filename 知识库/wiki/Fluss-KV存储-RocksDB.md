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

![[diagram/Fluss-KV存储-RocksDB-fig1.svg]]



## WAL 设计：Write-Once Read-Multiple

Fluss KV 的最大设计创新。传统 RocksDB 有自己的 WAL 文件（`*.log`），但 Fluss **不用 RocksDB 自带的 WAL**。

### 机制

写入路径：`putKv(row)` → RocksDB 写入 + **同时写入 changelog LogTablet**

恢复路径：**重放 changelog LogTablet** 来重建 RocksDB 状态（而非读 WAL 文件）

![[diagram/Fluss-KV存储-RocksDB-fig2.svg]]



**优势**：changelog 既是外部可读的 CDC 流，又是内部恢复的 WAL。一份数据两份用途，消除了 WAL 文件的额外 IO。

### 三种 WalBuilder 实现

| 实现 | LogFormat | 适用场景 |
|------|-----------|---------|
| `ArrowWalBuilder` | ARROW | 通用列式 WAL |
| `CompactedWalBuilder` | COMPACTED | PK 表（同 key 合并，减少 WAL 体积） |
| `IndexWalBuilder` | INDEXED | PK 表点查优化 |

## Snapshot 全链路（近 30 个类）

![[diagram/Fluss-KV存储-RocksDB-fig3.svg]]

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
