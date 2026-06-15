---
type: concept
tags:
  - distributed-database
  - aurora
  - transactions
  - snapshot-isolation
  - timestamp
  - concurrency-control
related:
  - "[[事务模型深度调研]]"
  - "[[CockroachDB-Leader-Lease-整体设计]]"
created: 2026-06-15
source: Aurora PostgreSQL Limitless Database (SIGMOD 2026)
---

# Aurora Limitless 时间戳事务

## 概述

Aurora Limitless 通过 **基于物理时钟的时间戳快照隔离**（Clock-SI + HLC）替代 PostgreSQL 传统的 xid-based snapshot，实现分布式事务的一致性和高性能。支持 Repeatable Read (SI) 和 Read Committed 隔离级别，并增强为**外部一致性**。

## 核心机制

### 时间戳替代 xid

传统 PostgreSQL 的 xid-based snapshot 需要记录 `{xmin, xmax, xip_list}`，高并发下 snapshot 计算是 CPU 瓶颈，且在分布式环境中无法跨节点感知所有活跃事务。

Aurora Limitless 的方案：
- 事务开始时 Router 取 `now().latest`（Amazon Time Sync 上界）作为 `startTs`
- 行版本可见性判定：`xmin.commitTs ≤ T.startTs < xmax.commitTs`
- Shard 维护 xid → commitTs 映射（嵌入 PG commit log）

### Amazon Time Sync

AWS 各区域部署**冗余卫星同步原子钟集群**提供微秒级时钟精度：
- `now()` 返回 `{current_time, CEB}`
- CEB（时钟误差界）典型值 < 1ms，部分区域已降至低双位微秒
- 开源 ClockBound daemon ([github.com/aws/clock-bound](https://github.com/aws/clock-bound))

### HLC（混合逻辑时钟）消除读延迟

传统 Clock-SI 的问题：shard 读请求的 snapshot timestamp 可能在 shard 本地时钟之前，需要等待时钟追上。

Aurora Limitless 使用 **混合逻辑时钟（HLC）** 消除等待：
- Shard 维护逻辑时钟 C
- 每次收到读请求 T：`C = max{C, T.startTs + 1}`
- Shard 的 prepare timestamp = `max{C, now().latest}`
- 效果：T 读取后，该 shard 后续提交的任何事务都有 commitTs > T.startTs → T 立即可读，无需等待

### Prepare 状态处理

读到 prepare 状态的行时，Shard 向事务的 Lead Shard 查询状态：
- 已提交 → 返回 commitTs 决定可见性
- 未提交 → Lead Shard 推进其 HLC ≥ `T.startTs + 1`，确保最终 commitTs > T.startTs

### COMMITTING 状态处理

事务已获得 commit time 但存储写入未完成 → 标记为 COMMITTING。读该行的 T 等待 commit/abort 完成。

## 分布式提交协议（Lead Shard 2PC）

**设计动机**：Router 无 standby（节省成本），Router 故障恢复需数分钟 → 不适合做 2PC coordinator。

**Lead Shard 2PC 流程**：
1. Router 选一个参与 shard 为 lead，向其他参与 shard 发 `PREPARE TRANSACTION`（含 lead shard ID）
2. 各 shard 计算 prepare timestamp（`max{C, now().latest}`），持久化 prepare 信息 + lead shard ID
3. Router 取所有 prepare timestamp 最大值发给 lead
4. Lead 取 `max(router_value, own_proposal)` 为 commitTs，本地持久化并提交
5. Router 通知客户端，异步向其他 shard 发 `COMMIT PREPARED`

**故障恢复**：Router 故障时，其他 shard 查询 lead shard 决定 commit/abort

**优化**：
- 只读事务直接 commit
- 单 shard 更新事务跳过 2PC，目标 shard 本地管理

## 外部一致性（External Consistency）

比 SI 更强的保证：如果 T2 在 T1（修改后）返回客户端后开始，则 `T2.startTs > T1.commitTs`。

实现：**commit wait**——lead shard 确定 commitTs 后等待 `now().earliest > commitTs` 再回复 Router。由于 commit wait 与 storage write 并行执行，且 storage write latency 通常 > CEB（<1ms），wait 很少增加延迟。

## 隔离级别对比

| 属性 | Repeatable Read (SI) | Read Committed |
|------|---------------------|----------------|
| Snapshot timestamp | 事务开始时一次 | 每个语句重新计算 |
| 写冲突检测 | ✅ 检查 | ❌ 关闭 |
| 修改行锁 | 排他锁至 commit | 排他锁至 commit |

## 与竞品对比

| 维度 | Aurora Limitless | CockroachDB | Spanner | YugabyteDB |
|------|-----------------|-------------|---------|------------|
| 时钟方案 | AWS Time Sync + HLC | HLC | TrueTime | HLC |
| 外部一致性 | ✅ (commit wait) | ❌ | ✅ | ❌ |
| Coordinator | Lead Shard (有 standby) | 无中心 (lease) | 中心式 (Paxos) | Tablet leader (Raft) |
| 隔离级别 | SI + RC | Serializable + RC | Serializable + SI | Serializable + SI |

Aurora Limitless 在保障外部一致性的同时，避免了 Spanner 的硬件时钟依赖和 CockroachDB/YugabyteDB 的保守时钟偏移等待。

## 与知识库关联
- [[事务模型深度调研]]：本文的 SI 实现（Clock-SI + HLC + external consistency）
- [[事务模型深度调研]]：时间戳替代 xid 的多版本方案
- [[事务模型深度调研]]：lead shard 2PC 变体
- [[CockroachDB-Leader-Lease-整体设计]]：CockroachDB 的 HLC-based 一致性 vs 本文的物理时钟方案
- [[事务模型深度调研]]：Clock-SI / 2PC / 3PC / Percolator 体系位置
