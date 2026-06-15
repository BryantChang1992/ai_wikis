---
type: analysis
title: "Fluss 整体架构与 Kafka 2.7.2 对照"
sources:
  - "https://github.com/BryantChang1992/ai_memory_chang_ai_team/blob/master/tech_research/fluss/01-整体架构对比.html"
  - "https://github.com/BryantChang1992/ai_memory_chang_ai_team/blob/master/tech_research/fluss/07-模块对应关系总表.html"
tags:
  - "Fluss"
  - "Kafka"
  - "架构"
  - "源码分析"
  - "流存储"
created: 2026-06-15
updated: 2026-06-15
status: draft
related:
  - "[[Fluss-存储引擎]]"
  - "[[Fluss-分布式协调]]"
  - "[[Fluss-RPC与网络]]"
  - "[[Fluss-客户端与计算集成]]"
  - "[[Fluss-Lake层与湖仓融合]]"
---

# Fluss 整体架构与 Kafka 2.7.2 对照

![[diagram/fluss-vs-kafka-architecture.svg]]
## 概述

Apache Fluss (Incubating) 是新一代流存储系统，从 Kafka 生态演化而来但在架构上有根本性设计差异。核心发现：**Fluss 约 30% 代码复用 Kafka（Log Segment 管理 + Replica 复制框架），70% 自研（KV 存储、Arrow 列式、Lake 集成、RPC 框架）**。

Fluss 不是在 Kafka 上做增量改进，而是**重构了存储模型**——从 Topic（无 schema 字节流）升级为 Table（强 schema、支持 PK、支持 KV 索引），从单一本地 Log 扩展为三层存储（本地 Log + KV Store + Remote/Lake）。

## 核心概念映射

| Fluss | Kafka 2.7.2 | 说明 |
|-------|-------------|------|
| **Database** | （无） | Fluss 引入 Database 作为 Table 的命名空间容器 |
| **Table** | Topic | 基本数据组织单元 |
| **Partition** | Partition | 逻辑分区（语义一致） |
| **TableBucket** | Partition (Replica) | 物理存储单元，Fluss 的 bucket 即 Kafka 的 partition replica |
| **Tablet** | Partition（逻辑） | Fluss 中 Tablet 是表级管理单元 |
| **TabletServer** | Broker | 数据服务节点 |
| **CoordinatorServer** | Controller | 集群管理节点，独立进程可独立高可用 |
| **LogTablet** | Log (Partition Log) | 物理日志实体 |
| **KV Store** | （无） | PK 表的 RocksDB 存储——**Fluss 最大差异化能力** |
| **Lake Table** | （无） | 湖表，数据以 Parquet/Arrow 格式写入 Lakehouse |
| **Row / InternalRow** | Record (Key+Value bytes) | Fluss 用 Arrow 列式（schema-aware），Kafka 用字节流 |

## 八大核心差异

| 维度 | Fluss | Kafka 2.7.2 |
|------|-------|-------------|
| **架构** | 存算分离（TabletServer 专注存储，CoordinatorServer 独立） | 存算耦合（Broker 同时服务读写+复制） |
| **数据模型** | Table（有 schema，支持 PK）+ Database 命名空间 | Topic（无 schema，key/value bytes） |
| **存储层** | 三层：本地 Log + KV Store (RocksDB) + Remote/Lake Storage | 单层：本地 Log Segment 文件 |
| **记录格式** | Arrow 列式（列裁剪 + 谓词下推 + 向量化） | 行式字节流（无 schema 感知） |
| **一致性** | ISR 协议（同 Kafka） | ISR 协议 |
| **协调** | CoordinatorServer（职责多于 Controller：重平衡/自动分区/Lake 分层） | Controller（仅管理分区/副本状态） |
| **计算引擎** | 原生 Flink/Spark Source/Sink/Catalog/Lookup Join | Connect Framework + 外部连接器 |
| **分层存储** | 原生 Remote Log + Lake Table（KIP-405 后才有的能力） | 无（KIP-405 在 2.8+ 引入） |

## 代码复用分析

### 已确认复用（标注 `This file is based on source code of Apache Kafka Project`）

| Fluss | Kafka 来源 | 复用程度 |
|-------|-----------|---------|
| `LocalLog.java` | `kafka.log.Log.scala` | 高度复用 Log Segment 管理逻辑 |
| `LogTablet.java` | `kafka.log.Log.scala` | 复用追加、读取、分段逻辑 |
| `LogManager.java` | `kafka.log.LogManager.scala` | 复用日志目录管理 |
| `LogSegment.java` | `kafka.log.LogSegment.scala` | 高度复用 |
| `ReplicaManager.java` | `kafka.server.ReplicaManager.scala` | 复用副本管理框架 |
| `ReplicaFetcherThread.java` | `kafka.server.AbstractFetcherThread.scala` | 复用 Follower 拉取逻辑 |
| `DelayedOperation.java` | `kafka.server.DelayedOperation.scala` | 复用延时操作框架 |

### 完全自研的模块

- **KV 子系统**（KvManager/KvTablet/RocksDBKv/RowMerger/Snapshot 全链路）：近 30 个类
- **Arrow 列式记录**（ArrowLogWriteBatch/ArrowLogFetchCollector/ArrowWalBuilder）
- **Lake 集成**（Iceberg/Paimon/Hudi/Lance 四种后端，各 7-35 个类）
- **RPC 框架**（Netty + Protobuf + GatewayClientProxy 动态代理）
- **Kafka 协议兼容层**（KafkaProtocolPlugin，骨架状态）
- **Flink Connector**（215 个 Java 文件，Source/Sink/Catalog/Lookup/Tiering）
- **Coordinator 增强**（AutoPartitionManager/RebalanceManager/LakeTableTieringManager）

## Fluss 独有的 8 个核心能力（Kafka 2.7.2 无对应）

1. **KV Store (RocksDB)**：PK 表提供点查/更新/删除，Kafka 本质是 append-only log
2. **Arrow 列式记录**：列裁剪、谓词下推、向量化计算
3. **Lake Table**：数据直接以 Parquet/Arrow 格式写入数据湖
4. **Remote Log**：本地仅保留 N 个 segment，老数据自动 tier 到远程存储
5. **Merge Engine**：行级聚合（SUM/MAX/MIN/COUNT）、部分更新、去重
6. **Primary Key 表**：Upsert/Delete，自动生成 Changelog
7. **Schema 管理**：内建 schema evolution（通过 schema id）
8. **存算分离**：TabletServer 可独立扩缩，CoordinatorServer 可独立高可用

## Kafka 2.7.2 独有（Fluss 无对应）

1. **Connect Framework**：标准化数据源/目标连接器生态
2. **Streams DSL**：内建流处理库（但可被 Flink/Spark 替代）
3. **KRaft**：KIP-500 去 ZK 化
4. **事务生产者**：完整的分布式事务语义（Fluss 当前无）
5. **幂等生产者**：Producer ID + Sequence Number
6. **Log Compaction**：基于 key 的日志压缩

---

> **关键洞察**：Fluss 与 Kafka 的根本分歧在于**数据模型哲学**。Kafka 走"通用字节流"路线（最大兼容性），Fluss 走"结构化数据"路线（Table + Schema + PK + 类型安全），加上了原生 Lakehouse 集成。两者的竞争不是"谁更快"，而是"流处理平台应该对数据有多少理解"。
