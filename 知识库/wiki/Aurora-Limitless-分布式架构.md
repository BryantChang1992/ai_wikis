---
type: concept
tags:
  - distributed-database
  - aurora
  - architecture
  - sharding
  - postgresql
related:
  - "[[存储计算分离数据库的-Tail-Latency]]"
  - "[[Aurora-Limitless-时间戳事务]]"
  - "[[Aurora-Limitless-自适应扩缩容]]"
  - "[[事务模型深度调研]]"
status: draft
sources:
  - "sources/papers/Aurora-Limitless/精读分析.md"
created: 2026-06-15
source: Aurora PostgreSQL Limitless Database (SIGMOD 2026)
diagram: "diagram/aurora-limitless-architecture.svg"

---

# Aurora Limitless 分布式架构

## 概述

Aurora Limitless Database 是 Amazon Aurora PostgreSQL 的水平扩展方案，通过 **Router/Shard 解耦架构** 实现透明分布式扩展，应用无需修改分片逻辑。系统已在 AWS 生产环境运行超过一年。

## 三层架构

<svg viewBox="0 0 680 100" xmlns="http://www.w3.org/2000/svg" style="max-width:100%">
  <defs>
    <marker id="arrow-al" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <path d="M0,0 L8,3 L0,6 Z" fill="currentColor"/>
    </marker>
  </defs>
  <!-- Client -->
  <rect x="10" y="15" width="55" height="28" rx="5" fill="transparent" stroke="currentColor" stroke-width="1.8"/>
  <text x="37" y="31" font-family="sans-serif" font-size="12" fill="currentColor" text-anchor="middle" dominant-baseline="middle">Client</text>
  <line x1="65" y1="29" x2="80" y2="29" stroke="currentColor" stroke-width="1.8" marker-end="url(#arrow-al)"/>
  
  <!-- DNS LB -->
  <rect x="83" y="15" width="70" height="28" rx="5" fill="transparent" stroke="currentColor" stroke-width="1.8"/>
  <text x="118" y="31" font-family="sans-serif" font-size="12" fill="currentColor" text-anchor="middle" dominant-baseline="middle">DNS LB</text>
  <line x1="153" y1="29" x2="168" y2="29" stroke="currentColor" stroke-width="1.8" marker-end="url(#arrow-al)"/>
  
  <!-- Routers -->
  <rect x="171" y="15" width="100" height="28" rx="5" fill="transparent" stroke="currentColor" stroke-width="1.8"/>
  <text x="221" y="31" font-family="sans-serif" font-size="12" fill="currentColor" text-anchor="middle" dominant-baseline="middle">Routers (无状态)</text>
  <line x1="271" y1="29" x2="286" y2="29" stroke="currentColor" stroke-width="1.8" marker-end="url(#arrow-al)"/>
  
  <!-- Shards -->
  <rect x="289" y="15" width="100" height="28" rx="5" fill="transparent" stroke="currentColor" stroke-width="1.8"/>
  <text x="339" y="31" font-family="sans-serif" font-size="12" fill="currentColor" text-anchor="middle" dominant-baseline="middle">Shards (有状态)</text>
  <line x1="389" y1="29" x2="404" y2="29" stroke="currentColor" stroke-width="1.8" marker-end="url(#arrow-al)"/>
  
  <!-- Aurora Storage -->
  <rect x="407" y="15" width="160" height="28" rx="5" fill="transparent" stroke="currentColor" stroke-width="1.8"/>
  <text x="487" y="31" font-family="sans-serif" font-size="12" fill="currentColor" text-anchor="middle" dominant-baseline="middle">Aurora Storage (3-AZ, 6副本)</text>
  
  <!-- Control Plane up/down arrow -->
  <line x1="221" y1="43" x2="221" y2="60" stroke="currentColor" stroke-width="1.8"/>
  <line x1="209" y1="60" x2="233" y2="60" stroke="currentColor" stroke-width="1.8"/>
  <text x="228" y="68" font-family="sans-serif" font-size="12" fill="currentColor">↕</text>
  <rect x="155" y="78" width="130" height="24" rx="5" fill="transparent" stroke="currentColor" stroke-width="1.8"/>
  <text x="220" y="92" font-family="sans-serif" font-size="12" fill="currentColor" text-anchor="middle" dominant-baseline="middle">Control Plane</text>
</svg>


- **Router**：服务应用流量，持有 schema + topology + shard mapping 元数据。无 standby（通过 DNS LB 实现高可用），每个连接绑定至一个 Router
- **Shard**：拥有数据分片。每个 Shard 是独立 Aurora PostgreSQL 集群。支持 0-2 个 standby（跨 AZ）
- **Control Plane**：集群管理、监控、热管理、备份恢复
- **Aurora Storage**：跨 3 AZ 6 副本，自动段修复，弹性容量。Aurora Limitless 利用其 quorum writes 避免了额外的 Paxos/Raft 共识层

## 三种表类型

| 类型 | 分布策略 | 声明方式 | 典型场景 |
|------|---------|---------|---------|
| **Sharded** | Hash(shard_key) 水平分区 | `limitless_create_table_mode = 'sharded'` | 大表（customers, orders） |
| **Reference** | 全量复制到每个 shard | `limitless_create_table_mode = 'reference'` | 小表常 JOIN（tax_rates） |
| **Standard** | 单 shard 存放 | `limitless_create_table_mode = 'standard'` | 不便分片 / 导入过渡 |

**Co-location**：相同 shard key 的表通过 `limitless_create_table_collocate_with` 声明共置，使 co-located join 可在单个 shard 内完成。

## 查询执行模型

### 单 Shard 查询（核心路径）
Router 利用 PostgreSQL partition pruning 识别所有数据在同一 shard 的查询，**直推到底**——单次往返。

### 跨 Shard 查询
1. Router 将 sharded table 表示为 PG **partitioned table** + **foreign table (FDW)**
2. 生成子计划下推到各 shard，**异步并行执行**（Async Foreign Scan）
3. 结果返回 Router 后 post-processing（排序、聚合）

**优化技术**：
- Predicate pushdown（IMMUTABLE 函数 + 内置操作）
- Co-located join pushdown（shard 本地 join，Router 仅 append）
- Reference table join pushdown（支持内连接 + outer join with ref as null-padded side）
- Partial aggregate/sorting pushdown
- Function 分发（声明 shard key 参数，执行推至对应 shard）

## 连接复用

Router 连接管理器以**事务粒度**在 shard 连接上复用客户端会话。事务完成后，其 shard 连接可被其他事务使用。Session 状态（认证、角色、变量）通过 session-context 传递跨事务保持。

## 与知识库关联
- [[存储计算分离数据库的-Tail-Latency]]：完全复用 Aurora 的 storage-compute separation
- [[Aurora-Limitless-时间戳事务]]：分布式事务协议
- [[Aurora-Limitless-自适应扩缩容]]：垂直+水平二维扩缩容机制
