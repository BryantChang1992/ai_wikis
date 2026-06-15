---
type: concept
title: "InfluxDB 指标设计与基数管理"
sources:
  - "技术文章/InfluxDB调研/04-指标设计最佳实践.md"
tags:
  - InfluxDB
  - 指标设计
  - 基数管理
  - Schema 设计
  - 下采样
  - 反模式
created: 2026-06-14
updated: 2026-06-14
status: final
author: Stark (CTO, CHANG_AI_TEAM)
related:
  - "[[InfluxDB深度调研]]"
  - "[[InfluxDB-数据模型]]"
diagram: "diagram/influxdb-architecture.svg"

---

# InfluxDB 指标设计与基数管理

## 核心公式

```
Series Cardinality = |tag₁| × |tag₂| × ... × |tagₙ| × |fields|
```

每个 Tag Key 的取值数量相乘，再乘以 Field Key 数量，得到 Series 总数。这是评估 Schema 是否合理的**唯一量化标准**。

## Tag vs Field 决策框架

### 决策流程

<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 700 210" width="700" height="210">
  <defs>
    <marker id="arrow-idb1" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <path d="M0,0 L8,3 L0,6 Z" fill="currentColor"/>
    </marker>
  </defs>
  <!-- Start: 需要 WHERE 过滤? -->
  <rect x="10" y="10" width="170" height="32" rx="16" fill="transparent" stroke="currentColor" stroke-width="1.5"/>
  <text x="95" y="26" font-family="sans-serif" font-size="13" fill="currentColor" text-anchor="middle" dominant-baseline="middle">需要 WHERE 过滤?</text>

  <!-- YES branch -->
  <line x1="180" y1="26" x2="290" y2="26" stroke="currentColor" stroke-width="1.5" marker-end="url(#arrow-idb1)"/>
  <text x="235" y="20" font-family="sans-serif" font-size="11" fill="currentColor" text-anchor="middle" dominant-baseline="middle" fill-opacity="0.7">YES</text>

  <rect x="293" y="10" width="180" height="32" rx="16" fill="transparent" stroke="currentColor" stroke-width="1.5"/>
  <text x="383" y="26" font-family="sans-serif" font-size="13" fill="currentColor" text-anchor="middle" dominant-baseline="middle">仍需检查基数</text>

  <line x1="473" y1="26" x2="560" y2="26" stroke="currentColor" stroke-width="1.5" marker-end="url(#arrow-idb1)"/>

  <!-- Branch lines from 检查基数 -->
  <line x1="560" y1="26" x2="560" y2="50" stroke="currentColor" stroke-width="1.5"/>
  <line x1="500" y1="50" x2="620" y2="50" stroke="currentColor" stroke-width="1.5"/>
  <line x1="500" y1="50" x2="500" y2="70" stroke="currentColor" stroke-width="1.5"/>
  <line x1="560" y1="50" x2="560" y2="70" stroke="currentColor" stroke-width="1.5"/>
  <line x1="620" y1="50" x2="620" y2="70" stroke="currentColor" stroke-width="1.5"/>

  <!-- LOW -->
  <rect x="430" y="70" width="140" height="30" rx="6" fill="transparent" stroke="currentColor" stroke-width="1.2"/>
  <text x="500" y="85" font-family="sans-serif" font-size="12" fill="currentColor" text-anchor="middle" dominant-baseline="middle">LOW (&lt;10K)</text>
  <line x1="570" y1="85" x2="615" y2="85" stroke="currentColor" stroke-width="1.2" marker-end="url(#arrow-idb1)"/>
  <text x="615" y="85" font-family="sans-serif" font-size="12" fill="currentColor" text-anchor="start" dominant-baseline="middle">✅ 作为 Tag</text>

  <!-- MED -->
  <rect x="490" y="106" width="140" height="30" rx="6" fill="transparent" stroke="currentColor" stroke-width="1.2"/>
  <text x="560" y="121" font-family="sans-serif" font-size="12" fill="currentColor" text-anchor="middle" dominant-baseline="middle">MED (10K-100K)</text>
  <line x1="630" y1="121" x2="670" y2="121" stroke="currentColor" stroke-width="1.2" marker-end="url(#arrow-idb1)"/>
  <text x="670" y="121" font-family="sans-serif" font-size="12" fill="currentColor" text-anchor="start" dominant-baseline="middle">⚠ 谨慎 Tag</text>

  <!-- HIGH -->
  <rect x="490" y="142" width="140" height="30" rx="6" fill="transparent" stroke="currentColor" stroke-width="1.2"/>
  <text x="560" y="157" font-family="sans-serif" font-size="12" fill="currentColor" text-anchor="middle" dominant-baseline="middle">HIGH (&gt;100K)</text>
  <line x1="630" y1="157" x2="670" y2="157" stroke="currentColor" stroke-width="1.2" marker-end="url(#arrow-idb1)"/>
  <text x="670" y="157" font-family="sans-serif" font-size="12" fill="currentColor" text-anchor="start" dominant-baseline="middle">❌ 绝不能 Tag</text>

  <!-- NO branch flows downward -->
  <line x1="95" y1="42" x2="95" y2="85" stroke="currentColor" stroke-width="1.5"/>
  <line x1="10" y1="85" x2="95" y2="85" stroke="currentColor" stroke-width="1.5"/>
  <line x1="10" y1="85" x2="10" y2="105" stroke="currentColor" stroke-width="1.5"/>
  <text x="48" y="100" font-family="sans-serif" font-size="11" fill="currentColor" text-anchor="middle" dominant-baseline="middle" fill-opacity="0.7">NO</text>

  <!-- 需要 GROUP BY? -->
  <rect x="5" y="105" width="170" height="32" rx="16" fill="transparent" stroke="currentColor" stroke-width="1.5"/>
  <text x="90" y="121" font-family="sans-serif" font-size="13" fill="currentColor" text-anchor="middle" dominant-baseline="middle">需要 GROUP BY?</text>

  <!-- GROUP BY YES -->
  <line x1="175" y1="121" x2="255" y2="121" stroke="currentColor" stroke-width="1.5" marker-end="url(#arrow-idb1)"/>
  <text x="215" y="115" font-family="sans-serif" font-size="11" fill="currentColor" text-anchor="middle" dominant-baseline="middle" fill-opacity="0.7">YES</text>
  <rect x="258" y="108" width="120" height="28" rx="6" fill="transparent" stroke="currentColor" stroke-width="1.2"/>
  <text x="318" y="122" font-family="sans-serif" font-size="12" fill="currentColor" text-anchor="middle" dominant-baseline="middle">必须 Tag</text>

  <!-- GROUP BY NO -->
  <line x1="90" y1="137" x2="90" y2="165" stroke="currentColor" stroke-width="1.5"/>
  <line x1="10" y1="165" x2="90" y2="165" stroke="currentColor" stroke-width="1.5"/>
  <line x1="10" y1="165" x2="10" y2="180" stroke="currentColor" stroke-width="1.5"/>
  <text x="50" y="177" font-family="sans-serif" font-size="11" fill="currentColor" text-anchor="middle" dominant-baseline="middle" fill-opacity="0.7">NO</text>

  <rect x="8" y="180" width="150" height="28" rx="6" fill="transparent" stroke="currentColor" stroke-width="1.2"/>
  <text x="83" y="194" font-family="sans-serif" font-size="12" fill="currentColor" text-anchor="middle" dominant-baseline="middle">✅ 作为 Field 存储</text>
</svg>

### Tag 适用场景
- **低基数额外信息**：host, region, environment, datacenter, service, method, status_code
- **GROUP BY 维度**
- **WHERE 过滤条件**

### Field 适用场景
- **高基数值**：user_id, request_id, trace_id, session_id, ip_address
- **实际度量值**：cpu_usage, memory_bytes, latency_ms, count, throughput
- **需要聚合运算的值**：SUM, AVG, MAX, MIN, PERCENTILE

## 五大最佳实践

### P1 — 避免 Measurement 中编码数据
```
❌ cpu.server-5.us-west.usage_user
✅ cpu, host=server-5, region=us-west, field=usage_user
```
将维度信息编码到 Measurement 名称中会导致 Measurement 数量爆炸，且无法按 Tag 过滤/聚合。

### P2 — 唯一标识符作为 Field，绝不做 Tag
```
❌ user_id, order_id, request_id, trace_id 作为 Tag
✅ 以上全部作为 Field
```
这被称为 "Runaway Cardinality"——每个唯一值创建一个新 Series，直接导致索引爆炸。

### P3 — Bucket/Table 按保留策略分离
```
✅ raw_metrics (RP: 7d) → ds_hourly (RP: 90d) → ds_daily (RP: 365d)
```
不同精度的数据存放在不同 Bucket，配置不同保留策略。

### P4 — 不同采样率的指标分 Measurement
```
cpu (10s precision, measurement=cpu)
cpu_daily (1d precision, measurement=cpu_daily)
```

### P5 — Bucket/Measurement 命名简短
```
❌ my_application_production_environment_metrics_v2
✅ app_metrics
```
简短命名在百万级 Series 场景下节省显著。

## 常见反模式

### 💀 反模式 1：Runaway Cardinality
将 user_id、session_id、ip_address 等唯一值作为 Tag。
**后果**：内存爆炸 → TSI 索引膨胀 → 写入/查询全链路退化 → OOM Kill
**修复**：改为 Field；如需按 user 查询，在应用层预聚合或使用 InfluxDB 3。

### 💀 反模式 2：所有维度塞一个 Measurement
cpu、mem、disk、net 全部写入 sensor_data。
**后果**：查询必须 filter by _field → 扫描无关数据 → 无法独立配置保留策略
**修复**：按语义拆分 measurement（cpu、mem、disk、net）。

### 💀 反模式 3：时间戳精度问题
同一 Tag Set + 同一时间戳写入多个 Point。
**后果**：后写入覆盖先写入，数据静默丢失。
**修复**：确保同一 Series 的时间戳唯一。

### 💀 反模式 4：无下采样策略
30 天全精度 raw data，无 Continuous Query 或 Task。
**后果**：存储成本线性增长，查询扫描大量数据点。

## 下采样策略

<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 700 60" width="700" height="60">
  <defs>
    <marker id="arrow-idb2" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <path d="M0,0 L8,3 L0,6 Z" fill="currentColor"/>
    </marker>
    <marker id="arrow-idb3" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <path d="M0,0 L8,3 L0,6 Z" fill="currentColor"/>
    </marker>
    <marker id="arrow-idb4" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <path d="M0,0 L8,3 L0,6 Z" fill="currentColor"/>
    </marker>
  </defs>
  <!-- Raw -->
  <rect x="10" y="5" width="120" height="28" rx="6" fill="transparent" stroke="currentColor" stroke-width="1.2"/>
  <text x="70" y="19" font-family="sans-serif" font-size="12" fill="currentColor" text-anchor="middle" dominant-baseline="middle">Raw (10s)</text>
  <text x="70" y="30" font-family="sans-serif" font-size="10" fill="currentColor" text-anchor="middle" dominant-baseline="middle" font-style="italic">RP: 7d</text>

  <line x1="130" y1="19" x2="190" y2="19" stroke="currentColor" stroke-width="1.5" marker-end="url(#arrow-idb2)"/>
  <text x="160" y="13" font-family="sans-serif" font-size="11" fill="currentColor" text-anchor="middle" dominant-baseline="middle">Task</text>

  <!-- Hourly -->
  <rect x="193" y="5" width="150" height="28" rx="6" fill="transparent" stroke="currentColor" stroke-width="1.2"/>
  <text x="268" y="19" font-family="sans-serif" font-size="12" fill="currentColor" text-anchor="middle" dominant-baseline="middle">Hourly Agg (1h)</text>
  <text x="268" y="30" font-family="sans-serif" font-size="10" fill="currentColor" text-anchor="middle" dominant-baseline="middle" font-style="italic">RP: 90d</text>

  <line x1="343" y1="19" x2="403" y2="19" stroke="currentColor" stroke-width="1.5" marker-end="url(#arrow-idb3)"/>
  <text x="373" y="13" font-family="sans-serif" font-size="11" fill="currentColor" text-anchor="middle" dominant-baseline="middle">Task</text>

  <!-- Daily -->
  <rect x="406" y="5" width="150" height="28" rx="6" fill="transparent" stroke="currentColor" stroke-width="1.2"/>
  <text x="481" y="19" font-family="sans-serif" font-size="12" fill="currentColor" text-anchor="middle" dominant-baseline="middle">Daily Agg (1d)</text>
  <text x="481" y="30" font-family="sans-serif" font-size="10" fill="currentColor" text-anchor="middle" dominant-baseline="middle" font-style="italic">RP: 365d</text>

  <line x1="556" y1="19" x2="610" y2="19" stroke="currentColor" stroke-width="1.5" marker-end="url(#arrow-idb4)"/>

  <!-- Archive -->
  <rect x="613" y="5" width="85" height="28" rx="6" fill="transparent" stroke="currentColor" stroke-width="1.2"/>
  <text x="655" y="19" font-family="sans-serif" font-size="12" fill="currentColor" text-anchor="middle" dominant-baseline="middle">Archive</text>
  <text x="655" y="30" font-family="sans-serif" font-size="10" fill="currentColor" text-anchor="middle" dominant-baseline="middle" font-style="italic">Parquet (v3)</text>
</svg>

**关键原则**：
1. 尽早做下采样，减少高精度存储成本
2. 下采样维度与查询维度对齐
3. 聚合函数根据业务需求选择 (mean/max/min/p99)

**实现方式**：
- v1/v2：Continuous Query (v1) / Task (v2)
- v3：Embedded VM 或外部 ETL

## 基数计算示例

| 场景 | Tag 组合 | 公式 | Series 数 | 评级 |
|------|----------|------|-----------|------|
| 服务器监控 | host(100) × region(3) × env(2) × 4 fields | 100×3×2×4 | 2,400 | ✅ 安全 |
| K8s Pod 监控 | host(500) × pod(2000) × 10 fields | 500×2000×10 | 10,000,000 | ⚠ 危险 |
| IoT 设备 | device_id(100K) × sensor(5) × 3 fields | 100K×5×3 | 1,500,000 | ⚠ 危险 |
| 用户行为 | user_id(1M) × event(10) × 5 fields | 1M×10×5 | 50,000,000 | 💀 爆炸 |

---

*参考: "Data Layout and Schema Design Best Practices for InfluxDB" — Anais Dotis-Georgiou*
