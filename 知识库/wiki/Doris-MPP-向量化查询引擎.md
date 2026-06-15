---
type: concept
title: "Doris MPP 向量化查询引擎"
sources:
  - "技术文章/Doris调研/03-查询流程.md"
tags:
  - 数据库
  - OLAP
  - Doris
  - 查询引擎
  - MPP
  - 向量化
  - SIMD
  - Runtime Filter
  - Colocate Join
created: 2026-06-14
updated: 2026-06-14
status: draft
related:
  - "[[Doris-深度调研]]"
  - "[[Doris-Nereids-CBO-优化器]]"
diagram: "diagram/doris-architecture.svg"

---

# Doris MPP 向量化查询引擎

## 概述

Doris 查询引擎基于自研 C++ 向量化执行引擎，支持标准 SQL 和 MPP 分布式执行，是其高性能查询的核心。查询从 FE（Java 优化器+协调器）到 BE（C++ 执行器）分 Stage 流水线执行。

## 查询架构

<svg viewBox="0 0 680 200" xmlns="http://www.w3.org/2000/svg" style="max-width:100%">
  <defs>
    <marker id="arrow-down" markerWidth="6" markerHeight="8" refX="3" refY="8" orient="auto">
      <path d="M0,0 L3,8 L6,0 Z" fill="currentColor"/>
    </marker>
    <marker id="arrow-right5" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <path d="M0,0 L8,3 L0,6 Z" fill="currentColor"/>
    </marker>
  </defs>
  <!-- Client -->
  <rect x="200" y="5" width="280" height="30" rx="6" fill="transparent" stroke="currentColor" stroke-width="2"/>
  <text x="340" y="24" font-family="sans-serif" font-size="12" fill="currentColor" text-anchor="middle" dominant-baseline="middle">Client (MySQL Protocol / HTTP / Arrow Flight)</text>
  <!-- Arrow down -->
  <line x1="340" y1="35" x2="340" y2="50" stroke="currentColor" stroke-width="2" marker-end="url(#arrow-down)"/>
  <!-- FE row -->
  <rect x="110" y="52" width="80" height="28" rx="6" fill="transparent" stroke="currentColor" stroke-width="2"/>
  <text x="150" y="68" font-family="sans-serif" font-size="12" fill="currentColor" text-anchor="middle" dominant-baseline="middle">SQL Parser</text>
  <line x1="190" y1="66" x2="205" y2="66" stroke="currentColor" stroke-width="1.8" marker-end="url(#arrow-right5)"/>
  <rect x="208" y="52" width="80" height="28" rx="6" fill="transparent" stroke="currentColor" stroke-width="2"/>
  <text x="248" y="68" font-family="sans-serif" font-size="12" fill="currentColor" text-anchor="middle" dominant-baseline="middle">Analyzer</text>
  <line x1="288" y1="66" x2="303" y2="66" stroke="currentColor" stroke-width="1.8" marker-end="url(#arrow-right5)"/>
  <rect x="306" y="52" width="78" height="28" rx="6" fill="transparent" stroke="currentColor" stroke-width="2"/>
  <text x="345" y="68" font-family="sans-serif" font-size="12" fill="currentColor" text-anchor="middle" dominant-baseline="middle">Optimizer</text>
  <line x1="384" y1="66" x2="399" y2="66" stroke="currentColor" stroke-width="1.8" marker-end="url(#arrow-right5)"/>
  <rect x="402" y="52" width="88" height="28" rx="6" fill="transparent" stroke="currentColor" stroke-width="2"/>
  <text x="446" y="68" font-family="sans-serif" font-size="12" fill="currentColor" text-anchor="middle" dominant-baseline="middle">Coordinator</text>
  <line x1="490" y1="66" x2="505" y2="66" stroke="currentColor" stroke-width="1.8" marker-end="url(#arrow-right5)"/>
  <rect x="508" y="52" width="88" height="28" rx="6" fill="transparent" stroke="currentColor" stroke-width="2"/>
  <text x="552" y="68" font-family="sans-serif" font-size="12" fill="currentColor" text-anchor="middle" dominant-baseline="middle">Result Merger</text>
  <!-- Label: FE -->
  <text x="60" y="68" font-family="sans-serif" font-size="12" fill="currentColor" text-anchor="end" dominant-baseline="middle" font-weight="bold">FE (Java):</text>
  <!-- Arrow down Plan Fragments -->
  <line x1="340" y1="80" x2="340" y2="100" stroke="currentColor" stroke-width="2" marker-end="url(#arrow-down)"/>
  <text x="348" y="93" font-family="sans-serif" font-size="10" fill="currentColor">Plan Fragments</text>
  <!-- BE row -->
  <rect x="50" y="105" width="70" height="28" rx="6" fill="transparent" stroke="currentColor" stroke-width="2"/>
  <text x="85" y="121" font-family="sans-serif" font-size="12" fill="currentColor" text-anchor="middle" dominant-baseline="middle">Scan</text>
  <line x1="120" y1="119" x2="135" y2="119" stroke="currentColor" stroke-width="1.8" marker-end="url(#arrow-right5)"/>
  <rect x="138" y="105" width="70" height="28" rx="6" fill="transparent" stroke="currentColor" stroke-width="2"/>
  <text x="173" y="121" font-family="sans-serif" font-size="12" fill="currentColor" text-anchor="middle" dominant-baseline="middle">Filter</text>
  <line x1="208" y1="119" x2="223" y2="119" stroke="currentColor" stroke-width="1.8" marker-end="url(#arrow-right5)"/>
  <rect x="226" y="105" width="65" height="28" rx="6" fill="transparent" stroke="currentColor" stroke-width="2"/>
  <text x="258" y="121" font-family="sans-serif" font-size="12" fill="currentColor" text-anchor="middle" dominant-baseline="middle">Join</text>
  <line x1="291" y1="119" x2="306" y2="119" stroke="currentColor" stroke-width="1.8" marker-end="url(#arrow-right5)"/>
  <rect x="309" y="105" width="65" height="28" rx="6" fill="transparent" stroke="currentColor" stroke-width="2"/>
  <text x="341" y="121" font-family="sans-serif" font-size="12" fill="currentColor" text-anchor="middle" dominant-baseline="middle">Agg</text>
  <line x1="374" y1="119" x2="389" y2="119" stroke="currentColor" stroke-width="1.8" marker-end="url(#arrow-right5)"/>
  <rect x="392" y="105" width="65" height="28" rx="6" fill="transparent" stroke="currentColor" stroke-width="2"/>
  <text x="424" y="121" font-family="sans-serif" font-size="12" fill="currentColor" text-anchor="middle" dominant-baseline="middle">Sort</text>
  <line x1="457" y1="119" x2="472" y2="119" stroke="currentColor" stroke-width="1.8" marker-end="url(#arrow-right5)"/>
  <rect x="475" y="105" width="65" height="28" rx="6" fill="transparent" stroke="currentColor" stroke-width="2"/>
  <text x="507" y="121" font-family="sans-serif" font-size="12" fill="currentColor" text-anchor="middle" dominant-baseline="middle">Sink</text>
  <!-- Label: BE -->
  <text x="40" y="121" font-family="sans-serif" font-size="12" fill="currentColor" text-anchor="end" dominant-baseline="middle" font-weight="bold">BE (C++):</text>
  <!-- Arrow up for vectorized engine -->
  <line x1="340" y1="138" x2="340" y2="152" stroke="currentColor" stroke-width="1.5" marker-end="url(#arrow-down)"/>
  <rect x="230" y="155" width="220" height="24" rx="4" fill="transparent" stroke="currentColor" stroke-width="1.5"/>
  <text x="340" y="169" font-family="sans-serif" font-size="11" fill="currentColor" text-anchor="middle" dominant-baseline="middle">向量化引擎 (4096行/Batch, SIMD)</text>
</svg>


---

## MPP 分布式执行三阶段

### Phase 1: Plan Fragment 分发

FE 将 SQL Plan 拆分为多个 Fragment，每个 Fragment 由 BE 上一个 Instance 执行：

<svg viewBox="0 0 650 100" xmlns="http://www.w3.org/2000/svg" style="max-width:100%">
  <defs>
    <marker id="arrow-f" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <path d="M0,0 L8,3 L0,6 Z" fill="currentColor"/>
    </marker>
    <marker id="arrow-b" markerWidth="8" markerHeight="6" refX="0" refY="3" orient="auto">
      <path d="M8,0 L0,3 L8,6 Z" fill="currentColor"/>
    </marker>
  </defs>
  
  <!-- Fragment 0 -->
  <rect x="10" y="10" width="175" height="24" rx="5" fill="transparent" stroke="currentColor" stroke-width="1.8"/>
  <text x="97" y="24" font-family="sans-serif" font-size="11" fill="currentColor" text-anchor="middle" dominant-baseline="middle">Fragment 0 (Coordinator)</text>
  <line x1="185" y1="22" x2="215" y2="22" stroke="currentColor" stroke-width="1.8" marker-end="url(#arrow-f)"/>
  <text x="210" y="15" font-family="sans-serif" font-size="10" fill="currentColor">Result Sink</text>
  <line x1="220" y1="22" x2="250" y2="22" stroke="currentColor" stroke-width="1.8" marker-end="url(#arrow-f)"/>
  <text x="240" y="15" font-family="sans-serif" font-size="10" fill="currentColor">Merge</text>
  <line x1="255" y1="22" x2="280" y2="22" stroke="currentColor" stroke-width="1.8" marker-end="url(#arrow-f)"/>
  <text x="270" y="15" font-family="sans-serif" font-size="10" fill="currentColor">Client</text>
  
  <!-- Fragment 1 -->
  <rect x="10" y="40" width="175" height="24" rx="5" fill="transparent" stroke="currentColor" stroke-width="1.8"/>
  <text x="97" y="54" font-family="sans-serif" font-size="11" fill="currentColor" text-anchor="middle" dominant-baseline="middle">Fragment 1 (Agg BE)</text>
  <line x1="185" y1="52" x2="215" y2="52" stroke="currentColor" stroke-width="1.8"/>
  <text x="210" y="45" font-family="sans-serif" font-size="10" fill="currentColor">Final Agg</text>
  <line x1="220" y1="52" x2="250" y2="52" stroke="currentColor" stroke-width="1.8" marker-end="url(#arrow-b)"/>
  <rect x="260" y="42" width="85" height="20" rx="3" fill="transparent" stroke="currentColor" stroke-width="1" stroke-dasharray="3,2"/>
  <text x="302" y="54" font-family="sans-serif" font-size="10" fill="currentColor" text-anchor="middle" dominant-baseline="middle">EXCHANGE</text>
  
  <!-- Fragment 2 -->
  <rect x="10" y="70" width="175" height="24" rx="5" fill="transparent" stroke="currentColor" stroke-width="1.8"/>
  <text x="97" y="84" font-family="sans-serif" font-size="11" fill="currentColor" text-anchor="middle" dominant-baseline="middle">Fragment 2 (Scan BE)</text>
  <line x1="185" y1="82" x2="215" y2="82" stroke="currentColor" stroke-width="1.8" marker-end="url(#arrow-f)"/>
  <text x="210" y="75" font-family="sans-serif" font-size="10" fill="currentColor">Pre Agg</text>
  <line x1="220" y1="82" x2="250" y2="82" stroke="currentColor" stroke-width="1.8" marker-end="url(#arrow-f)"/>
  <rect x="260" y="72" width="85" height="20" rx="3" fill="transparent" stroke="currentColor" stroke-width="1" stroke-dasharray="3,2"/>
  <text x="302" y="84" font-family="sans-serif" font-size="10" fill="currentColor" text-anchor="middle" dominant-baseline="middle">EXCHANGE</text>
</svg>


### Phase 2: Data Shuffle

BE 间通过 BRPC 进行数据交换，四种策略：

| 策略 | 触发条件 | 说明 | 开销 |
|------|----------|------|------|
| **Broadcast** | 右表 < broadcast_row_limit | 全量广播到所有 Scan Node | 网络 × N |
| **Hash Shuffle** | Join Key 或 Agg Key | 按 Key Hash 重分布 | 网络全量 |
| **Bucket Shuffle** | Join Key = 分桶键 | 直接按 Bucket 映射 | **零 Shuffle** |
| **Colocate Join** | 两张表同 Colocation Group | 本地 Join | **零 Shuffle，最优** |

> **Bucket Shuffle** 和 **Colocate Join** 是 Doris 独有的 Shuffle 优化——利用分区/分桶信息消除数据重分布，是高频 Join 查询的核心优化。

### Phase 3: Vectorized Execution

BE 内部以 **4096 行**为一个 Columnar Batch 流水线处理：

<svg viewBox="0 0 650 60" xmlns="http://www.w3.org/2000/svg" style="max-width:100%">
  <defs>
    <marker id="arrow-vec" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <path d="M0,0 L8,3 L0,6 Z" fill="currentColor"/>
    </marker>
  </defs>
  <!-- Operator chain -->
  <rect x="10" y="8" width="55" height="26" rx="4" fill="transparent" stroke="currentColor" stroke-width="1.5"/>
  <text x="37" y="23" font-family="sans-serif" font-size="12" fill="currentColor" text-anchor="middle" dominant-baseline="middle">Scan</text>
  <line x1="65" y1="21" x2="78" y2="21" stroke="currentColor" stroke-width="1.8" marker-end="url(#arrow-vec)"/>
  <rect x="80" y="8" width="55" height="26" rx="4" fill="transparent" stroke="currentColor" stroke-width="1.5"/>
  <text x="107" y="23" font-family="sans-serif" font-size="12" fill="currentColor" text-anchor="middle" dominant-baseline="middle">Filter</text>
  <line x1="135" y1="21" x2="148" y2="21" stroke="currentColor" stroke-width="1.8" marker-end="url(#arrow-vec)"/>
  <rect x="150" y="8" width="60" height="26" rx="4" fill="transparent" stroke="currentColor" stroke-width="1.5"/>
  <text x="180" y="23" font-family="sans-serif" font-size="12" fill="currentColor" text-anchor="middle" dominant-baseline="middle">Project</text>
  <line x1="210" y1="21" x2="223" y2="21" stroke="currentColor" stroke-width="1.8" marker-end="url(#arrow-vec)"/>
  <rect x="225" y="8" width="55" height="26" rx="4" fill="transparent" stroke="currentColor" stroke-width="1.5"/>
  <text x="252" y="23" font-family="sans-serif" font-size="12" fill="currentColor" text-anchor="middle" dominant-baseline="middle">Join</text>
  <line x1="280" y1="21" x2="293" y2="21" stroke="currentColor" stroke-width="1.8" marker-end="url(#arrow-vec)"/>
  <rect x="295" y="8" width="50" height="26" rx="4" fill="transparent" stroke="currentColor" stroke-width="1.5"/>
  <text x="320" y="23" font-family="sans-serif" font-size="12" fill="currentColor" text-anchor="middle" dominant-baseline="middle">Agg</text>
  <line x1="345" y1="21" x2="358" y2="21" stroke="currentColor" stroke-width="1.8" marker-end="url(#arrow-vec)"/>
  <rect x="360" y="8" width="50" height="26" rx="4" fill="transparent" stroke="currentColor" stroke-width="1.5"/>
  <text x="385" y="23" font-family="sans-serif" font-size="12" fill="currentColor" text-anchor="middle" dominant-baseline="middle">Sort</text>
  <line x1="410" y1="21" x2="423" y2="21" stroke="currentColor" stroke-width="1.8" marker-end="url(#arrow-vec)"/>
  <rect x="425" y="8" width="55" height="26" rx="4" fill="transparent" stroke="currentColor" stroke-width="1.5"/>
  <text x="452" y="23" font-family="sans-serif" font-size="12" fill="currentColor" text-anchor="middle" dominant-baseline="middle">Sink</text>
  
  <!-- Upward labels -->
  <text x="107" y="48" font-family="sans-serif" font-size="10" fill="currentColor" text-anchor="middle">SIMD (SSE/AVX2)</text>
  <line x1="107" y1="34" x2="107" y2="42" stroke="currentColor" stroke-width="1.2" marker-end="url(#arrow-vec)"/>
  <text x="450" y="48" font-family="sans-serif" font-size="10" fill="currentColor" text-anchor="middle">内存池管理（避免碎片）</text>
  <line x1="340" y1="34" x2="340" y2="42" stroke="currentColor" stroke-width="1.2" marker-end="url(#arrow-vec)"/>
</svg>


全程列式操作，利用 SIMD 指令集加速。

---

## 向量化引擎设计

| 设计元素 | 说明 |
|----------|------|
| Batch Size | 4096 行/Batch（平衡 CPU Cache 和函数调用开销） |
| SIMD | SSE/AVX2 指令集加速列运算 |
| 内存池 | 预分配内存池，避免频繁 malloc/free |
| Pipeline | 各算子间流水线执行，减少中间结果物化 |
| 表达式 JIT | 复杂表达式编译为 Native Code（Roadmap） |

---

## Runtime Filter

Doris Runtime Filter 是查询加速的核心技术：

```
1. Small Table (右表) Join Key → Build Bloom Filter
2. Broadcast Bloom Filter to Scan Node (左表)
3. Scan Node 用 Bloom Filter 过滤不需要的行
4. 大幅减少 Shuffle & Join 数据量
```

**典型收益**：大表 Join 小表场景，Runtime Filter 可过滤 50%~99% 的无效数据。

---

## Lakehouse 联邦查询

Doris 3.0 支持原生联邦查询多种数据源：

| Catalog | 引擎 | 能力 |
|---------|------|------|
| Hive | Hive Metastore | 读 Hive 表 |
| Iceberg | REST / HMS | Iceberg v2, Time Travel |
| Paimon | Filesystem / HMS | CDC 支持 |
| Hudi | HMS | MOR/COW 表 |
| JDBC | MySQL/PG/Oracle | 联邦查询 RDBMS |
| ES | Elasticsearch | 联邦查询 ES |

支持跨 Catalog 的 SQL Join：

```sql
CREATE CATALOG iceberg_catalog PROPERTIES (
    "type" = "iceberg",
    "iceberg.catalog.type" = "rest",
    "uri" = "http://iceberg-rest:8181/"
);

SELECT d.user_id, i.item_name
FROM doris_db.user_order_daily d
JOIN iceberg_catalog.item_db.items i ON d.item_id = i.item_id;
```
