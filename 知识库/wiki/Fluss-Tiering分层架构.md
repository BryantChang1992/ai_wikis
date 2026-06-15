---
type: concept
title: "Fluss Tiering 分层架构"
sources:
  - "https://github.com/BryantChang1992/ai_memory_chang_ai_team/blob/master/tech_research/fluss/06-Lake层与湖仓融合.html"
  - "https://github.com/BryantChang1992/ai_memory_chang_ai_team/blob/master/tech_research/fluss/05-客户端与计算集成.html"
tags:
  - "Fluss"
  - "Tiering"
  - "Lakehouse"
  - "数据湖"
  - "Flink"
created: 2026-06-15
updated: 2026-06-15
status: draft
related:
  - "[[Fluss-Lake层与湖仓融合]]"
  - "[[Fluss-存储引擎]]"
  - "[[Fluss-KV存储-RocksDB]]"
diagram: "diagram/fluss-tiering-architecture.svg"

---

# Fluss Tiering 分层架构

## 定义

Tiering 是 Fluss 将本地 Tablet 数据**异步、持续**写入 Lakehouse（数据湖）的机制。它不是一个简单的后台任务——它是一个**独立的 Flink 流处理作业**（`FlussLakeTiering`），具有完整的 Source → Transform → Sink → Commit 流水线。

## 架构位置

<svg viewBox="0 0 680 160" xmlns="http://www.w3.org/2000/svg" style="max-width:100%">
  <defs>
    <marker id="arrow-tier" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <path d="M0,0 L8,3 L0,6 Z" fill="currentColor"/>
    </marker>
  </defs>
  <text x="10" y="18" font-family="sans-serif" font-size="13" fill="currentColor" font-weight="bold">Fluss 数据生命周期:</text>
  
  <!-- Layer 1 -->
  <rect x="20" y="28" width="200" height="30" rx="6" fill="transparent" stroke="currentColor" stroke-width="2"/>
  <text x="120" y="45" font-family="sans-serif" font-size="12" fill="currentColor" text-anchor="middle" dominant-baseline="middle">实时写入 (ms 级)</text>
  
  <!-- Arrow -->
  <line x1="220" y1="43" x2="245" y2="43" stroke="currentColor" stroke-width="2" marker-end="url(#arrow-tier)"/>
  
  <!-- Layer 2 -->
  <rect x="250" y="20" width="260" height="35" rx="6" fill="transparent" stroke="currentColor" stroke-width="2"/>
  <text x="380" y="30" font-family="sans-serif" font-size="11" fill="currentColor" text-anchor="middle" dominant-baseline="middle">Fluss Tablet</text>
  <text x="380" y="46" font-family="sans-serif" font-size="10" fill="currentColor" text-anchor="middle" dominant-baseline="middle">(本地 Log + KV, 毫秒级读写, OLTP 级别)</text>
  
  <!-- Arrow downward to next line -->
  <line x1="120" y1="58" x2="120" y2="75" stroke="currentColor" stroke-width="2" marker-end="url(#arrow-tier)"/>
  
  <!-- Layer 3 -->
  <rect x="20" y="80" width="280" height="30" rx="6" fill="transparent" stroke="currentColor" stroke-width="2"/>
  <text x="160" y="97" font-family="sans-serif" font-size="12" fill="currentColor" text-anchor="middle" dominant-baseline="middle">Tiering 作业（分钟级异步分层）</text>
  
  <!-- Arrow -->
  <line x1="300" y1="95" x2="325" y2="95" stroke="currentColor" stroke-width="2" marker-end="url(#arrow-tier)"/>
  
  <!-- Layer 4 -->
  <rect x="330" y="76" width="230" height="38" rx="6" fill="transparent" stroke="currentColor" stroke-width="2"/>
  <text x="445" y="88" font-family="sans-serif" font-size="11" fill="currentColor" text-anchor="middle" dominant-baseline="middle">Lakehouse</text>
  <text x="445" y="104" font-family="sans-serif" font-size="10" fill="currentColor" text-anchor="middle" dominant-baseline="middle">(Parquet/Arrow, 分钟级物化, OLAP 级别)</text>
  
  <!-- Arrow -->
  <line x1="380" y1="114" x2="380" y2="130" stroke="currentColor" stroke-width="2" marker-end="url(#arrow-tier)"/>
  
  <!-- Layer 5 -->
  <rect x="200" y="135" width="260" height="24" rx="6" fill="transparent" stroke="currentColor" stroke-width="1.5"/>
  <text x="330" y="149" font-family="sans-serif" font-size="11" fill="currentColor" text-anchor="middle" dominant-baseline="middle">本地 segment 可被 GC（释放磁盘空间）</text>
</svg>


这不是"冷热分层"（把冷数据搬到廉价存储），而是**数据模型的语义升级**——从 append-only log 变为可查询的 Lakehouse Table。

## Tiering 工作流

<svg viewBox="0 0 680 200" xmlns="http://www.w3.org/2000/svg" style="max-width:100%">
  <defs>
    <marker id="arrow-tw" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <path d="M0,0 L8,3 L0,6 Z" fill="currentColor"/>
    </marker>
  </defs>
  
  <text x="10" y="18" font-family="sans-serif" font-size="13" fill="currentColor" font-weight="bold">Tiering 工作流:</text>
  
  <!-- Step 1 -->
  <rect x="30" y="28" width="350" height="24" rx="5" fill="transparent" stroke="currentColor" stroke-width="1.8"/>
  <text x="205" y="42" font-family="sans-serif" font-size="12" fill="currentColor" text-anchor="middle" dominant-baseline="middle">CoordinatorServer</text>
  <line x1="380" y1="40" x2="395" y2="40" stroke="currentColor" stroke-width="2" marker-end="url(#arrow-tw)"/>
  
  <!-- Step 2 -->
  <rect x="30" y="58" width="350" height="24" rx="5" fill="transparent" stroke="currentColor" stroke-width="1.8"/>
  <text x="205" y="72" font-family="sans-serif" font-size="12" fill="currentColor" text-anchor="middle" dominant-baseline="middle">LakeTableTieringManager 调度 tiering 任务</text>
  <line x1="380" y1="70" x2="395" y2="70" stroke="currentColor" stroke-width="2" marker-end="url(#arrow-tw)"/>
  
  <!-- Step 3 -->
  <rect x="30" y="88" width="350" height="24" rx="5" fill="transparent" stroke="currentColor" stroke-width="1.8"/>
  <text x="205" y="102" font-family="sans-serif" font-size="12" fill="currentColor" text-anchor="middle" dominant-baseline="middle">TieringSource（Flink Source，从 TabletServer 读本地数据）</text>
  <line x1="380" y1="100" x2="395" y2="100" stroke="currentColor" stroke-width="2" marker-end="url(#arrow-tw)"/>
  
  <!-- Step 4 -->
  <rect x="30" y="118" width="350" height="24" rx="5" fill="transparent" stroke="currentColor" stroke-width="1.8"/>
  <text x="205" y="132" font-family="sans-serif" font-size="12" fill="currentColor" text-anchor="middle" dominant-baseline="middle">LakeWriter（写入 Lake Storage: Iceberg/Paimon/Hudi/Lance）</text>
  <line x1="380" y1="130" x2="395" y2="130" stroke="currentColor" stroke-width="2" marker-end="url(#arrow-tw)"/>
  
  <!-- Step 5 -->
  <rect x="30" y="148" width="350" height="24" rx="5" fill="transparent" stroke="currentColor" stroke-width="1.8"/>
  <text x="205" y="162" font-family="sans-serif" font-size="12" fill="currentColor" text-anchor="middle" dominant-baseline="middle">TieringCommitter（提交 Snapshot）</text>
  <line x1="380" y1="160" x2="395" y2="160" stroke="currentColor" stroke-width="2" marker-end="url(#arrow-tw)"/>
  
  <!-- Step 6 -->
  <rect x="30" y="178" width="350" height="24" rx="5" fill="transparent" stroke="currentColor" stroke-width="1.8"/>
  <text x="205" y="192" font-family="sans-serif" font-size="12" fill="currentColor" text-anchor="middle" dominant-baseline="middle">Coordinator.commitLakeTableSnapshot（通知协调器）</text>
</svg>

<svg viewBox="0 0 680 60" xmlns="http://www.w3.org/2000/svg" style="max-width:100%">
  <defs>
    <marker id="arrow-tw2" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <path d="M0,0 L8,3 L0,6 Z" fill="currentColor"/>
    </marker>
  </defs>
  <rect x="30" y="8" width="350" height="24" rx="5" fill="transparent" stroke="currentColor" stroke-width="1.8"/>
  <text x="205" y="22" font-family="sans-serif" font-size="12" fill="currentColor" text-anchor="middle" dominant-baseline="middle">TabletServer.notifyLakeTableOffset（更新本地 lake offset）</text>
  <line x1="380" y1="20" x2="395" y2="20" stroke="currentColor" stroke-width="2" marker-end="url(#arrow-tw2)"/>
  
  <rect x="30" y="38" width="350" height="24" rx="5" fill="transparent" stroke="currentColor" stroke-width="1.8"/>
  <text x="205" y="52" font-family="sans-serif" font-size="12" fill="currentColor" text-anchor="middle" dominant-baseline="middle">本地 LogManager 删除已被 tiered 的 segment</text>
</svg>


### 组件清单

| 组件 | 类 | 功能 |
|------|-----|------|
| 入口 | `FlussLakeTiering` / `FlussLakeTieringEntrypoint` | Tiering 作业启动 |
| Source | `TieringSource` → `TieringSplitReader` | 从 TabletServer 读取数据 |
| Writer | `LakeWriter` 接口 | 写入 Lake Storage |
| Committer | `TieringCommitOperator` / `TieringCommitter` | 提交 Lake Snapshot |
| Event | `TieringReachMaxDurationEvent` / `FinishedTieringEvent` / `FailedTieringEvent` | 事件驱动 |
| Metrics | `TieringMetrics` | 指标收集 |
| Split | `TieringLogSplit` / `TieringSnapshotSplit` | 分层 Split 定义 |
| Result | `TableBucketWriteResult` / `TableBucketWriteResultEmitter` | 结果回传 |

## Coordinator 端管理

| 类 | 功能 |
|-----|------|
| `LakeTableTieringManager` | 管理 Lake 表的 Tiering 进度与调度 |
| `LakeCatalogDynamicLoader` | 动态加载 Lake Catalog（支持运行时切换后端） |
| `CommitLakeTableSnapshot` event | 处理 Tiering 提交的快照信息 |
| `NotifyLakeTableOffset` | 通知 TabletServer 更新本地 Lake offset |

## 心跳驱动

TabletServer 通过 `lakeTieringHeartbeat` RPC 向 Coordinator 汇报 bucket 的本地日志进度。Coordinator 根据 `lakeLogStartOffset` vs `logEndOffset` 的差距决定是否需要触发 Tiering。

## 设计哲学

Fluss Tiering 的设计原则是：

1. **异步**：Tiering 不阻塞实时写入路径。Writer 写入本地 Log 后立即返回，Tiering 在后台异步进行
2. **独立作业**：Tiering 是独立的 Flink 作业，有自己的并行度、容错、Backpressure 机制
3. **组件化**：Source/Writer/Committer 都是可插拔接口，支持不同 Lake 后端
4. **事件驱动**：通过 `TieringReachMaxDurationEvent` 控制单次 Tiering 的最大时长，防止长尾

---

> **关键洞察**：Fluss Tiering 是"流批一体"在存储层的具体实现。传统架构中，"把 Kafka 数据写入数据湖"是一个独立的 ETL 管道（如 Kafka Connect + Hudi DeltaStreamer），而 Fluss 将其内建为系统的一部分。这意味着用户不需要部署和维护额外的 ETL 管道——Flink Tiering 作业本身就是 Fluss 集群的一部分。但这也有代价：Tiering 作业的稳定性和性能直接关系到数据的"可分析性"，如果 Tiering 延迟过高，分析师看到的数据就是过时的。
