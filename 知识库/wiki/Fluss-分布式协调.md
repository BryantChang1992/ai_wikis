---
type: analysis
title: "Fluss 分布式协调层分析"
sources:
  - "https://github.com/BryantChang1992/ai_memory_chang_ai_team/blob/master/tech_research/fluss/03-分布式协调.html"
tags:
  - "Fluss"
  - "分布式协调"
  - "Coordinator"
  - "状态机"
  - "重平衡"
  - "源码分析"
created: 2026-06-15
updated: 2026-06-15
status: draft
related:
  - "[[Fluss-整体架构]]"
  - "[[Fluss-RPC与网络]]"

---

# Fluss 分布式协调层分析

## 概述

Fluss 的分布式协调层采用 **CoordinatorServer（独立进程）** 架构，对标 Kafka Controller 但进行了现代化重构：Java 实现、事件驱动、更丰富的管理职责。核心差异在于 CoordinatorServer 不仅是"分区管理员"，还是"集群调度器"——内建重平衡、自动分区、Lake 分层管理。

## Coordinator vs Kafka Controller

| 维度 | Fluss Coordinator | Kafka 2.7.2 Controller |
|------|-------------------|------------------------|
| 语言 | Java | Scala |
| 事件模型 | 16 种 `CoordinatorEvent` 类型 | `ControllerEvent` switch-case |
| 状态机 | 双状态机（Replica + TableBucket） | 双状态机（Replica + Partition） |
| Leader 选举 | Curator `LeaderLatch` | ZK 临时节点 `/controller` 竞争 |
| 通道管理 | Protobuf RPC | Kafka 二进制协议 |
| 独有能力 | AutoPartitionManager / RebalanceManager / LakeTableTieringManager / LeaseManager | 无 |

## 事件驱动架构

CoordinatorEventProcessor 是核心事件分发循环，处理 16 种事件类型：

| 事件 | 触发场景 | Kafka 对应 |
|------|---------|-----------|
| `NewCoordinatorEvent` | 当选 Coordinator | `BecomeLeader` |
| `FencedCoordinatorEvent` | Coordinator Epoch 过期 | `ControllerMovedException` |
| `NewTabletServerEvent` | TabletServer 注册 | `BrokerChange` |
| `DeadTabletServerEvent` | TabletServer 失联 | `BrokerChange` |
| `CreateTableEvent` / `DropTableEvent` | 创建/删除表 | `CreateTopics` / `DeleteTopics` |
| `CreatePartitionEvent` / `DropPartitionEvent` | 创建/删除分区 | `CreatePartitions` |
| `AdjustIsrReceivedEvent` | TabletServer 上报 ISR 变更 | `AlterIsr` |
| `NotifyLeaderAndIsrResponseReceivedEvent` | Leader/ISR 通知确认 | `LeaderAndIsrResponseReceived` |
| `RebalanceEvent` / `RebalanceTaskTimeoutEvent` | 集群重平衡 | （Kafka 用 Cruise Control 外挂） |
| `SchemaChangeEvent` | Schema 变更 | 无 |
| `CommitKvSnapshotEvent` | KV 快照提交 | 无 |
| `ControlledShutdownEvent` | 优雅关闭 | 同名事件 |

事件流：ZK Watcher → `EventManager.put()` → 事件队列 → `CoordinatorEventProcessor.process()` → 状态机迁移 → `CoordinatorRequestBatch` 批量发送 RPC。

## 双状态机模型

### ReplicaStateMachine（6 种状态）

![Fluss-分布式协调 - 图1](../diagram/Fluss-分布式协调-fig1.svg)




### TableBucketStateMachine（5 种状态）

![Fluss-分布式协调 - 图2](../diagram/Fluss-分布式协调-fig2.svg)

Leader 选举策略：`DefaultLeaderElection` 在 AR（Assigned Replicas）中选取第一个 ISR 内的副本。

## 重平衡（RebalanceManager + GoalOptimizer）

Fluss 内建重平衡系统，通过 Goal 优化器实现自动化调度——这是 Kafka 依赖外部 Cruise Control 完成的功能：

- **BalancedCapacityGoal**：均衡各 TabletServer 的存储容量
- **ReplicaCountGoal**：均衡副本数量分布
- **RackAwareGoal**：确保副本跨机架分布
- **GoalOptimizer**：组合多个 Goal，按优先级顺序优化

## 租约管理（KvSnapshotLeaseManager）

协调器管理 KV 快照的生命周期租约：`AcquireKvSnapshotLease` → 使用 → `ReleaseKvSnapshotLease` → 过期 → `DropKvSnapshotLease`。租约防止 TabletServer 迁移时读取正在被清理的快照。

## ZK 数据结构

```
/fluss/databases/[database]
/fluss/database/[database]/tables/[table]/partitions/[part]
/fluss/tablet_servers/[serverId]
/fluss/coordinator/leader
/fluss/table_assignments/...
/fluss/kv_snapshot_leases/...
```

vs Kafka 的 `/brokers/topics/[topic]/partitions/[partitionId]/state` —— Fluss 引入了 Database 层级。

## 元数据管理

- **CoordinatorMetadataCache**：协调器内存缓存，从 ZK 加载 database/table/schema 信息
- **ServerMetadataCache**：TabletServer 信息缓存
- **ServerSchemaCache**：Schema 缓存（schema id → schema 定义）
- **MetadataManager**：元数据持久化到 ZK

---

> **关键洞察**：Fluss Coordinator 的设计哲学是"更重的中央控制 + 更智能的调度"。Kafka Controller 是轻量级的（只管分区状态），Fluss Coordinator 是重量级的（管重平衡、自动分区、Lake 分层、Schema、ACL）。这反映了两种架构哲学：Kafka 把复杂度推向外部工具（Cruise Control、Schema Registry），Fluss 把复杂度集成到内核。
