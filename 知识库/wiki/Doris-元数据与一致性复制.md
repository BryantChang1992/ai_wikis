---
type: concept
title: "Doris 元数据存储与一致性复制"
sources:
  - "技术文章/Doris调研/05-元数据存储与一致性复制.md"
tags:
  - 数据库
  - OLAP
  - Doris
  - 元数据
  - 一致性
  - 2PC
  - BDB-JE
  - Meta Service
  - TabletScheduler
  - 复制
  - 事务
created: 2026-06-14
updated: 2026-06-14
status: draft
related:
  - "[[Doris-深度调研]]"
  - "[[Doris-架构演进]]"
  - "[[事务模型深度调研]]"
  - "[[Event-Horizon-非对称依赖]]"
---

# Doris 元数据存储与一致性复制

## 概述

Doris 采用 **控制面集中协调 + 数据面去中心化执行** 架构。FE 负责元数据一致性和全局调度，BE 间无中心依赖。元数据管理经历了 BDB-JE 单机 → BDB-JE Replication → Meta Service 存算分离的演进。

## 元数据存储

### 三层存储模型

| 层级 | 位置 | 内容 | 特点 |
|------|------|------|------|
| **Catalog** | FE 持久化层 (BDB-JE / Meta Service) | 元数据全集 | 持久化，版本化，支持事务 |
| **FE 内存缓存** | FE Heap | 热点元数据 | LRU 淘汰，惰性加载 |
| **BE 内存** | BE Heap | 本地 Tablet 子集 | 仅自己所管理的 Tablet |

### 元数据对象关系

```
Catalog Root
├── Internal Catalog (Doris 原生表)
│   └── Database → Table
│       ├── Column (类型/编码/压缩)
│       ├── Index (前缀/Bloom/Bitmap/Inverted)
│       └── Partition (Range/List/TTL)
│           └── Tablet → Replica (NORMAL/ALTER/CLONE)
├── Hive Catalog → ExternalTable
├── Iceberg Catalog → IcebergTable
└── ES/JDBC Catalog → ExternalTable
```

### BDB-JE 时代 (v0.x~v2.x)

Doris 0.x~2.x 使用 BDB-JE 作为 FE 元数据持久化引擎：

- **单 Leader 写入**：BDB-JE 类 Paxos 协议实现 FE 间复制
- **EditLog 机制**：每次变更生成 Entry，Follower 重放
- **Checkpoint**：定期 Snapshot，减少回放开销
- **Follower 回放**：BRPC 拉取 EditLog → 校验 CheckSum → 逐 Entry 回放到本地内存

FE 元数据文件布局：
```
fe/doris-meta/
├── bdb/           # BDB-JE Journal + Data
├── image/         # LFS 格式 Checkpoint
└── edit_log/      # 增量日志
```

### Meta Service (Doris 3.0+)

Doris 3.0 将元数据从 FE 剥离到独立集中式服务：

| 特性 | BDB-JE (v2.x) | Meta Service (v3.0) |
|------|--------------|---------------------|
| 存储引擎 | BDB-JE | FoundationDB (FDB) 或自研 Raft KV |
| 写入 | 单 Leader 顺序写 | 多 FE 并发写不同 Key 范围 |
| 恢复 | 回放完整 EditLog | 直接查询 Meta Service |
| 解耦 | FE 内嵌 | 独立服务 |

Meta Service Key 设计：
```
/meta/{cluster}/db/{db}/table/{table}         → 表层元数据
/meta/{cluster}/tablet/{tablet}                → Tablet 元数据
/meta/{cluster}/tablet/{tablet}/replica/{be}   → Replica 状态
/txn/{cluster}/db/{db}/txn/{txn}               → 事务元数据
```

---

## 多副本复制

### Shared-Nothing 复制 (v0.x~v2.x)

**写入策略**：Single-Replica Write（单副本成功即完成）→ TabletScheduler 异步 Clone 补齐。

**TabletScheduler 核心功能**：

| 功能 | 说明 |
|------|------|
| 修复 | Replica 缺失/版本落后 → 创建 Clone Task |
| 均衡 | BE 间 Tablet 不均衡 → Balance Task |
| 变更 | Alter Job 触发 Tablet 重写 |
| 退役 | Decommission BE 时迁移 |

优先级：**REPAIR > BALANCE > ALTER**

**多副本一致性**：

| 阶段 | 策略 |
|------|------|
| 写入 | Single-Replica Write |
| 复制 | Asynchronous Clone (TabletScheduler) |
| 读取 | 仅选版本足够的 Replica |
| 健康 | BE 每 10s 心跳 + VersionReport |
| 修复 | 自动检测版本缺失 → 触发 Clone |

### 存算分离复制 (Doris 3.0+)

从「BE 间 Clone」变为「Object Store 为中心」：

| 维度 | Shared-Nothing | 存算分离 |
|------|---------------|----------|
| 复制目标 | BE 间 Clone | Object Store 持久数据 |
| 副本数 | 3 | 1 (Object Store 高可用) |
| 一致性 | 最终一致性 | 写后即持久 |
| 故障恢复 | TabletScheduler 克隆 | 直读 Object Store |
| 存储成本 | 3× | 1× + Object Store 副本 |

---

## 写入路径与事务模型

### 2PC 分布式事务

Doris 采用 **FE 2PC 事务协调 + BE 本地 WAL** 保证写入一致性：

```
1. BEGIN Txn → 生成事务 ID
2. PREPARE → 所有 BE 写入本地 WAL（任一失败则 ABORT）
3. COMMIT → 全部成功则提交
4. PUBLISH → 版本号递增，查询可见
5. TabletScheduler → 异步修复失败 Replica
```

### 事务类型

| 类型 | 场景 | 特点 |
|------|------|------|
| **单 Tablet 事务** | Routine Load / Small Batch | 延迟最低 |
| **2PC 分布式事务** | Broker Load / INSERT INTO SELECT | 跨 Tablet 原子性 |

### Label 幂等性

每个 Load Job 有全局唯一 Label → FE 持久化 `Label → TxnId` → 重试返回已存在 TxnId → **Exactly-Once Write**

### 失败处理

| 阶段 | 失败 | 恢复 |
|------|------|------|
| PREPARE 部分成功 | BE 写入失败 | FE 发 ABORT，BE 撤销 WAL |
| COMMIT 部分到达 | 网络分区 | BE 重启后 Gossip 同步 + TabletScheduler 修复 |
| PUBLISH 后不可见 | 部分 Replica 落后 | 查询跳过不可见 Replica，补齐后恢复 |

---

## 故障恢复

| 故障 | 检测 | 恢复 | RTO |
|------|------|------|-----|
| FE Master 宕机 | BDB-JE 心跳 | Follower 提升，重放 EditLog | ~10-30s |
| BE 宕机 (SN) | FE 心跳 10s | TabletScheduler Clone | 分钟级 |
| BE 宕机 (存算分离) | FE 心跳 | 新 Node 直读 Object Store | **秒级** |
| 磁盘故障 | BE 自检 | TabletScheduler 修复 | 分钟级 |
| 版本不一致 | VersionReport | TabletScheduler 自动补齐 | 分钟级 |
| Meta Service 宕机 | FE 检测 | RAFT 自身高可用 | 秒级 |

## 设计哲学

> 控制面集中协调 + 数据面去中心化执行。FE 负责 2PC、TabletScheduler、Load Manager；BE 独立管理 Segment、Compaction、WAL。存算分离 3.0 进一步将控制面元数据从 FE 剥离到独立 Meta Service，实现完全解耦。

与 [[事务模型深度调研]] 中 Spanner/Percolator 的对比：Doris 采用更轻量的 2PC + 异步复制策略，以最终一致性换取更高写入吞吐，适合 OLAP 场景而非 OLTP 强一致性场景。

与 [[Event-Horizon-非对称依赖]] 的关联：Doris Shared-Nothing 模式下多副本异步 Clone 本质上是最终一致性模型——数据面不要求同步多副本写入，这与 Event Horizon 的"半线性化"思路一致：**不追求全局即时一致性，而是通过非对称依赖降低协调开销**。
