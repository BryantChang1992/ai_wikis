---
type: concept
title: "InfluxDB 数据模型与核心概念"
sources:
  - "技术文章/InfluxDB调研/01-概述与核心概念.md"
tags:
  - InfluxDB
  - 时序数据库
  - 数据模型
  - 基数管理
created: 2026-06-14
updated: 2026-06-14
status: final
author: Stark (CTO, CHANG_AI_TEAM)
related:
  - "[[InfluxDB深度调研]]"
  - "[[InfluxDB-指标设计与基数管理]]"
diagram: "diagram/influxdb-architecture.svg"

---

# InfluxDB 数据模型与核心概念

## 数据模型

InfluxDB 的数据模型围绕 **Point（数据点）** 构建，每个 Point 包含四个组件：

<svg viewBox="0 0 720 100" xmlns="http://www.w3.org/2000/svg" style="max-width:100%">
  <!-- The actual Line Protocol line as code-like text -->
  <text x="10" y="18" font-family="monospace, sans-serif" font-size="11" fill="currentColor">cpu,host=server-a,region=us-west usage_user=64.5,usage_sys=12.3 1718200000000000000</text>
  
  <!-- Measurement bracket -->
  <line x1="10" y1="28" x2="10" y2="40" stroke="currentColor" stroke-width="2"/>
  <line x1="10" y1="40" x2="40" y2="40" stroke="currentColor" stroke-width="2"/>
  <text x="12" y="55" font-family="sans-serif" font-size="12" fill="currentColor">Measurement</text>
  
  <!-- Tag set bracket -->
  <line x1="47" y1="28" x2="47" y2="40" stroke="currentColor" stroke-width="2"/>
  <line x1="47" y1="40" x2="205" y2="40" stroke="currentColor" stroke-width="2"/>
  <line x1="205" y1="28" x2="205" y2="40" stroke="currentColor" stroke-width="2"/>
  <text x="126" y="55" font-family="sans-serif" font-size="12" fill="currentColor" text-anchor="middle">Tag Set</text>
  
  <!-- Field set bracket -->
  <line x1="213" y1="28" x2="213" y2="40" stroke="currentColor" stroke-width="2"/>
  <line x1="213" y1="40" x2="342" y2="40" stroke="currentColor" stroke-width="2"/>
  <line x1="342" y1="28" x2="342" y2="40" stroke="currentColor" stroke-width="2"/>
  <text x="278" y="55" font-family="sans-serif" font-size="12" fill="currentColor" text-anchor="middle">Field Set</text>
  
  <!-- Timestamp bracket -->
  <line x1="350" y1="28" x2="350" y2="40" stroke="currentColor" stroke-width="2"/>
  <line x1="350" y1="40" x2="490" y2="40" stroke="currentColor" stroke-width="2"/>
  <line x1="490" y1="28" x2="490" y2="40" stroke="currentColor" stroke-width="2"/>
  <text x="420" y="55" font-family="sans-serif" font-size="12" fill="currentColor" text-anchor="middle">Timestamp</text>
</svg>


| 组件 | 说明 | 类型 | 是否索引 |
|------|------|------|----------|
| **Measurement** | 逻辑分组（类似表名） | String | 是 |
| **Tag Set** | 元数据键值对 | `key=value` (String only) | 是 |
| **Field Set** | 实际度量值 | String / Float / Integer / Boolean | 否 |
| **Timestamp** | 纳秒级 Unix 时间戳 | int64 | 是 |

## Series（系列）

**Series** 是 InfluxDB 最核心的概念：

```
Series = Measurement + Tag Set + Field Key
```

一个 Series 是一组共享相同 Measurement、Tag Set 和 Field Key 的数据点的集合。

**Series Cardinality（系列基数）** 是影响 InfluxDB 性能最关键的因素：

```
Series Cardinality = |tag₁| × |tag₂| × ... × |tagₙ| × |fields|
```

- **v1/v2 建议上限**：百万级 Series（超过此数 TSI 索引膨胀，性能退化）
- **InfluxDB 3 理论上限**：无硬限制（Parquet Statistics 替代 TSI 索引）

具体的基数计算示例和风险管理见 [[InfluxDB-指标设计与基数管理]]。

## Bucket / Database / Retention Policy

| 概念 | v1/v2 | v3 |
|------|-------|-----|
| 顶层容器 | Database + Retention Policy | Database (namespace) |
| 数据组织 | Bucket (v2) | Table (自动发现) |
| 保留策略 | RP (v1) / Bucket RP (v2) | GC Job 定期执行 |
| 分片粒度 | Shard Group Duration | Partition (默认按天) |

## Line Protocol — 统一写入格式

InfluxDB 所有版本的写入 API 均使用 Line Protocol 格式：

```
<measurement>[,<tag_key>=<tag_value>...] <field_key>=<field_value>[,<field_key>=<field_value>] [<timestamp>]
```

这是 InfluxDB 写入路径的统一入口，所有版本通用，是生态兼容性的基石。

## 版本演进

```
v1.x (2013~)        v2.x (2019~)         v3.0 (2023~)
TSM + TSI            TSM + TSI            Columnar (Parquet)
InfluxQL             InfluxQL + Flux       SQL + InfluxQL
单机优先            单机 + Tasks         存算分离
Go                   Go                   Rust (Arrow/DataFusion)
```

**v1/v2 的设计制约**：TSI 索引在 Series Cardinality > 百万时索引膨胀→内存爆炸→全链路退化。
**v3 的根本性突破**：以 Parquet 为"一等公民"格式，利用 Parquet Statistics 实现无索引剪枝，消除基数上限。

---

*参考: InfluxData 官方文档 "InfluxDB Internals 101" (Ryan Betts)*
