---
type: concept
title: CockroachDB vs TiDB 2026 架构对比
sources:
- '[[知识库/sources/web/cockroachdb-vs-tidb/精读分析]]'
tags:
- 分布式数据库
- CockroachDB
- TiDB
- 架构对比
created: 2026-07-03
updated: 2026-07-03
status: draft
related:
- '[[知识库/wiki/synthesis/分布式数据系统事务与一致性新进展-2026综述]]'
- '[[知识库/wiki/CockroachDB-Leader-Lease-整体设计]]'
- '[[知识库/wiki/CockroachDB-Liveness-Fabric-故障检测层]]'
- '[[知识库/wiki/事务模型深度调研]]'
confidence: 0.8
confidence_rationale: 类型=concept; 来源×1; 3天前更新
synced_at: '2026-10-05'
blog_url: https://bryantchang1992.github.io/ai_memory_chang_ai_team/knowledge/CockroachDB-vs-TiDB-2026-对比/
blog_source: _posts/2026-07-03-knowledge-dec25a48e3.md
---

# CockroachDB vs TiDB 2026 架构对比

## 一句话

CockroachDB 紧耦合 vs TiDB 存算分离——2026 年两条路线各自证明了有效性，核心差异不在"哪个更好"而在"解决什么问题"。

## 架构对比

### CockroachDB：紧耦合、"像运行一台跨越 DC 的 PostgreSQL"

- 自研 SQL 引擎 + KV 存储一体
- PostgreSQL wire-compatible
- 事务协调器与数据天然共址
- 扩充 = 加入更多全功能节点

### TiDB：存算分离、三组件协同

- SQL 层（TiDB Server）+ 存储层（TiKV）+ 列存（TiFlash）+ 调度（PD）
- MySQL wire-compatible
- 各层独立扩缩
- TiFlash 通过 Raft Learner 同步列存副本

## 关键对比

| 维度 | CockroachDB | TiDB | 优势 |
|------|------------|------|------|
| 地理分布式事务 | 紧耦合 → 事务协调自然 | Placement Rules → 三层跨越 | **CRDB** |
| 弹性扩缩 OLTP | 加节点 = 全功能节点 | 只扩 SQL 层 / 只扩存储层 | **TiDB** |
| OLTP+OLAP 混合 | 内置列存 | TiFlash 独立列存 | **TiDB** |
| SQL 兼容 | PostgreSQL | MySQL | 取决于生态 |
| 开源许可 | BSL | Apache 2.0 | **TiDB** |
| 单集群简洁性 | 一个二进制 | 多组件运维 | **CRDB** |

## 2026 演进

### CockroachDB 方向

SIGMOD 2026 的 Leader Leases 重新设计标志着 CRDB 在分布式协调层的持续投资。[[CockroachDB-Leader-Lease-整体设计]] 和 [[CockroachDB-Liveness-Fabric-故障检测层]] 解决了 Leader 选举的关键性能瓶颈。

### TiDB 方向

TiKV 和 TiFlash 持续演进，存算分离架构的灵活性在 cloud-native 环境中优势明显。CNCF 毕业项目地位带来了更广泛的社区支持。

## 选型指南

| 场景 | 推荐 | 理由 |
|------|------|------|
| PG 生态用户 | CockroachDB | 原生兼容 |
| MySQL 生态用户 | TiDB | Wire-compatible |
| 地理分布式 OLTP | CockroachDB | 紧耦合事务更自然 |
| 多云弹性 OLTP+OLAP | TiDB | 存算分离 + TiFlash |
| 简单运维 | CockroachDB | 单一二进制 |
| 开源合规 | TiDB | Apache 2.0 |

## 与知识库中 CRDB 研究的关联

本对比聚焦于两个系统的架构差异。[[CockroachDB-Leader-Lease-整体设计]] 提供了 CRDB 在分布式协调层的深度分析，[[分布式数据系统事务与一致性新进展-2026综述]] 将 CRDB 和 Aurora/Rosé/Agent-First 等系统进行了横向事务模型对比。
