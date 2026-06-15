---
type: concept
title: "Doris Segment v2 存储格式"
sources:
  - "技术文章/Doris调研/02-存储引擎.md"
tags:
  - 数据库
  - OLAP
  - Doris
  - 存储引擎
  - 列式存储
  - Segment v2
  - Parquet
  - DELETE_BITMAP
created: 2026-06-14
updated: 2026-06-14
status: draft
related:
  - "[[Doris-深度调研]]"
  - "[[Doris-数据模型]]"
  - "[[Doris-Compaction-策略]]"
  - "[[LSM-Tree]]"
  - "[[synthesis/LSM-Tree-存储引擎体系综述]]"
diagram: "diagram/doris-architecture.svg"

---

# Doris Segment v2 存储格式

## 概述

Segment v2 是 Apache Doris 自研的列式存储格式，专为 OLAP 低延迟写入和高性能查询优化。它以 Page 为最小 I/O 单元，结合 LSM-tree 写入思想和高效 Compaction 策略。

## 存储层级结构

<svg viewBox="0 0 600 460" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <marker id="ar4" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <path d="M0,0 L8,3 L0,6 Z" fill="currentColor"/>
    </marker>
  </defs>
  <style>
    text { font-family: sans-serif; font-size: 12px; fill: currentColor; dominant-baseline: middle; text-anchor: middle; }
    line { stroke: currentColor; stroke-width: 1.5; }
    rect { fill: transparent; stroke: currentColor; stroke-width: 1.5; rx: 4; }
  </style>

  <!-- Table -->
  <rect x="240" y="10" width="120" height="28"/>
  <text x="300" y="24">Table</text>

  <line x1="300" y1="38" x2="300" y2="55" marker-end="url(#ar4)"/>

  <!-- Partition -->
  <rect x="210" y="59" width="180" height="28"/>
  <text x="300" y="73">Partition (Range 分区)</text>

  <line x1="300" y1="87" x2="300" y2="104" marker-end="url(#ar4)"/>

  <!-- Bucket -->
  <rect x="220" y="108" width="160" height="28"/>
  <text x="300" y="122">Bucket (Hash 分桶)</text>

  <line x1="300" y1="136" x2="300" y2="153" marker-end="url(#ar4)"/>

  <!-- Tablet -->
  <rect x="200" y="157" width="200" height="28"/>
  <text x="300" y="171">Tablet (最小数据分发单元)</text>

  <line x1="300" y1="185" x2="300" y2="202"/>
  <!-- horizontal branch line for Rowsets -->
  <line x1="140" y1="202" x2="460" y2="202"/>
  <line x1="140" y1="202" x2="140" y2="218"/>
  <line x1="300" y1="202" x2="300" y2="218"/>
  <line x1="460" y1="202" x2="460" y2="218"/>

  <!-- Rowset 0 -->
  <rect x="80" y="222" width="120" height="28"/>
  <text x="140" y="236">Rowset 0 (当前写入)</text>

  <!-- Rowset 1 -->
  <rect x="240" y="222" width="120" height="28"/>
  <text x="300" y="236">Rowset 1 (已封存)</text>

  <!-- Rowset N -->
  <rect x="400" y="222" width="120" height="28"/>
  <text x="460" y="236">Rowset N</text>

  <line x1="460" y1="250" x2="460" y2="267" marker-end="url(#ar4)"/>

  <!-- Segment(s) -->
  <rect x="390" y="271" width="140" height="28"/>
  <text x="460" y="285">Segment(s) (列式数据文件)</text>

  <line x1="460" y1="299" x2="460" y2="316"/>
  <!-- branch for Segment children -->
  <line x1="180" y1="316" x2="460" y2="316"/>
  <line x1="180" y1="316" x2="180" y2="332"/>
  <line x1="273" y1="316" x2="273" y2="332"/>
  <line x1="366" y1="316" x2="366" y2="332"/>
  <line x1="460" y1="316" x2="460" y2="332"/>

  <!-- Segment children -->
  <rect x="115" y="336" width="130" height="28"/>
  <text x="180" y="350" font-size="11px">Column 0: Data Pages</text>

  <rect x="115" y="372" width="130" height="28"/>
  <text x="180" y="386" font-size="11px">Column 1: Data Pages</text>

  <rect x="205" y="336" width="136" height="28"/>
  <text x="273" y="350" font-size="11px">Short Key Index (稀疏索引)</text>

  <rect x="205" y="372" width="136" height="28"/>
  <text x="273" y="386" font-size="11px">ZoneMap Index (per Segment)</text>

  <rect x="300" y="336" width="132" height="28"/>
  <text x="366" y="350" font-size="11px">Bloom Filter (optional)</text>

  <rect x="380" y="336" width="160" height="64"/>
  <text x="460" y="358" font-size="11px">Footer (元数据)</text>
</svg>

## Segment 核心设计

### 数据组织
- **Page** 为最小 I/O 单元（默认 1MB）
- 每个 Column 的数据按 Page 组织，同一 Column 的 Page **物理连续**
- Column Page 内部采用 **RLE (Run-Length Encoding)** + **Bit-Packing** 压缩

### 元数据布局
- **Footer**：Segment 层级元数据（版本号、Column 数量、索引偏移量）
- **Short Key Index**：稀疏索引，每 N 行记录一个 Key，快速定位
- **ZoneMap Index**：每 Segment 每列的 Min/Max/NullCount，用于读取剪枝

### 索引体系

| 索引类型 | 层级 | 位置 | 过滤效果 |
|----------|------|------|----------|
| 前缀索引 | Tablet 级 | 稀疏索引，内存 | 粗粒度过滤（前 36 字节） |
| ZoneMap | Segment 级 | Footer | Min/Max/HasNull 统计过滤 |
| Bloom Filter | Block 级 | Segment 内 | 快速判不存在 HASH 值 |
| Bitmap Index | 列级 | 独立索引文件 | 低基数列精准过滤 |
| Inverted Index | 列级 | 独立索引文件 | 全文搜索、Token 匹配 |

## DELETE_BITMAP 机制

Unique MoW 表的核心创新——在现有 Segment 中标记被删除行，无需重写文件：

```
写入流程（MoW）：
  1. 逐 Key 查询 Tablet 内是否存在
  2. 若存在 → 在现有 Segment 中标记旧行为 DELETE_BITMAP
  3. 写入新数据行到新 Segment
查询流程：
  4. 先加载 DELETE_BITMAP
  5. 跳过被标记行
Compaction 清理：
  6. Quick Compaction 时物理清除被标记行，释放空间
```

## 与 Apache Parquet 对比

| 维度 | Doris Segment v2 | Apache Parquet |
|------|-----------------|----------------|
| 设计哲学 | OLAP 写入优化，低延迟 | 数据湖通用，压缩优先 |
| Page 大小 | 1MB（可配置） | ~1MB (Row Group) |
| 索引粒度 | Segment + Page 级 | Row Group + Page 级 |
| 编码方式 | RLE + BitPacking + LZ4/ZSTD | Dictionary + RLE + Delta |
| 主键支持 | **原生 Prefix Sort Key** | 无 |
| 更新支持 | **MoW DELETE_BITMAP** | 不可变 |
| 场景 | 实时写入+高并发查询 | 批量写入+大扫描 |

## 关键设计考量

- **写入优化**：Segment 不追求极端压缩率，优先保证写入低延迟
- **LSM 思想**：小 Rowset 频繁写入，大 Rowset 通过 Compaction 异步合并
- **未来演进**：4.x 计划支持 Parquet 原生格式，与数据湖生态深度打通
