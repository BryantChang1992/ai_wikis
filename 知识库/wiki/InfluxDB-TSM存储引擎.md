---
type: concept
title: "InfluxDB TSM 存储引擎"
sources:
  - "技术文章/InfluxDB调研/02-存储引擎.md"
tags:
  - InfluxDB
  - 存储引擎
  - TSM
  - TSI
  - 倒排索引
  - Compaction
created: 2026-06-14
updated: 2026-06-14
status: final
author: Stark (CTO, CHANG_AI_TEAM)
related:
  - "[[InfluxDB深度调研]]"
  - "[[InfluxDB-3-列存引擎]]"
  - "[[LSM-Tree]]"
  - "[[LSM-Tree-写放大]]"
diagram: "diagram/influxdb-architecture.svg"

---

# InfluxDB TSM 存储引擎

## 定义

TSM (Time-Structured Merge Tree) 是 InfluxDB v1/v2 自研的列式存储格式，设计理念源自 [[LSM-Tree]]。与 [[LSM-Tree]] 的 SSTable 类似，TSM 采用不可变文件 + 后台 Compaction 的架构，但针对时序数据做了专门优化。

## 存储结构

<svg viewBox="0 0 500 70" xmlns="http://www.w3.org/2000/svg" style="max-width:100%">
  <text x="10" y="16" font-family="sans-serif" font-size="13" fill="currentColor">db/rp/ShardID/</text>
  <line x1="10" y1="26" x2="30" y2="26" stroke="currentColor" stroke-width="1.5"/>
  <line x1="30" y1="26" x2="30" y2="54" stroke="currentColor" stroke-width="1.5"/>
  <line x1="30" y1="36" x2="50" y2="36" stroke="currentColor" stroke-width="1.5"/>
  <text x="55" y="39" font-family="sans-serif" font-size="12" fill="currentColor" dominant-baseline="middle">TSM0001.tsm</text>
  <text x="215" y="39" font-family="sans-serif" font-size="11" fill="currentColor" dominant-baseline="middle" font-style="italic"># 数据文件（不可变）</text>
  <line x1="30" y1="46" x2="50" y2="46" stroke="currentColor" stroke-width="1.5"/>
  <text x="55" y="50" font-family="sans-serif" font-size="12" fill="currentColor" dominant-baseline="middle">TSM0002.tsm</text>
  <line x1="10" y1="56" x2="30" y2="56" stroke="currentColor" stroke-width="1.5"/>
  <line x1="30" y1="56" x2="50" y2="56" stroke="currentColor" stroke-width="1.5"/>
  <text x="55" y="60" font-family="sans-serif" font-size="12" fill="currentColor" dominant-baseline="middle">...</text>
</svg>


**TSM 文件内部布局**：
- **Header**: 文件魔数 + 版本
- **Blocks**: 每个 Block 存储一个 Series 在一个时间段内的 Field 值
- **Index**: Block 的偏移量和时间范围索引
- **Footer**: 文件尾，指向 Index 起始位置

## 关键特性

### 列式存储
同一 Series 同一 Field 的值连续存储，压缩效果极佳（Snappy 压缩，~5-10x 压缩比）。

### 不可变文件
TSM 文件一经写入不可修改——这是 LSM 类引擎的通用设计原则。写入只能通过 Compaction 合并，删除通过 Tombstone 标记。

### 多级 Compaction
```
L0 (Cache Flush) → L1 → L2 → L3 → ...
   小文件            中等文件         大文件
```

类似 [[LSM-Tree]] 的 Leveling 策略，每级文件大小递增。L0 为 Cache Flush 产生的小文件，通过逐级合并提高查询效率。

**Compaction 的写放大**：同一条数据被反复读写多次——WAL (1x) → Cache → TSM L0 (flush) → L0→L1 (compact) → L1→L2 ... 这直接导致了 [[LSM-Tree-写放大]] 中描述的相同根因。

## TSI (Time Series Index) 倒排索引

TSI 是基于倒排索引的元数据索引系统：

- **索引内容**：`Measurement → Tag Key → Tag Value → Series ID` 的映射关系
- **存储形式**：内存中的 LogFile + 磁盘上的 IndexFile
- **分层设计**：热数据在内存，冷数据在磁盘

### TSI 的致命缺陷

当 Series Cardinality > 百万时：
1. 索引膨胀 → 内存炸裂
2. TSI LogFile 急剧增长 → 写放大加剧
3. 查询时遍历大量 Series ID → 延迟线性增长
4. 最终 → OOM Kill 或查询超时

这是 InfluxData 决定在 v3 放弃 TSI、转向 Parquet Statistics 的根本原因。

## 引擎局限

| 瓶颈 | 根因 | 后果 |
|------|------|------|
| 高基数性能退化 | TSI 索引膨胀 | 内存爆炸、OOM |
| Compaction 写放大 | 多级合并反复 I/O | 写入吞吐被限制 |
| 单机瓶颈 | 本地磁盘 + 单机 BoltDB | 无法水平扩展 |
| WAL 重放慢 | 崩溃后需全量重放 | 启动时间长 |

## 与 [[LSM-Tree]] 的关系

TSM 引擎本质是 LSM-Tree 在时序场景的具体实现：
- MemTable ↔ In-Memory Cache
- SSTable ↔ TSM File
- Compaction (Leveling) ↔ 多级 TSM Compaction
- Bloom Filter ↔ TSI Index（但 TSI 是倒排索引，功能上更对标）
- WAL ↔ WAL (Snappy compressed)

**核心差异**：标准 LSM-Tree 面向通用 KV，而 TSM 针对时序数据做了列式 Block 组织、时间范围索引、和 Snappy 列压缩优化。

---

*参考: InfluxData 官方文档 "InfluxDB Storage Engine Internals"*
