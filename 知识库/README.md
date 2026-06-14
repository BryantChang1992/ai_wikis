---
type: meta
title: "CHANG_AI_TEAM 知识库"
tags: ["meta", "知识库"]
created: 2026-06-14
updated: 2026-06-14T22:45
---

# CHANG_AI_TEAM 知识库

这是 CHANG_AI_TEAM 的核心知识底座。基于 Karpathy LLM Wiki 三层架构：

```
sources/  →  wiki/  →  Schema
 (只读)      (AI维护)   (规则)
```

## 目录

- [[purpose]] — 为什么存在、研究什么
- [[schema]] — 怎么组织、怎么写
- [[log]] — 谁做了什么

---

## 第1层: Raw Sources (`sources/`)

> 原始资料，只读。Agent 从这里读取，但绝不修改。

参见 [[sources/README]]

---

## 第2层: Wiki (`wiki/`)

> LLM 生成的结构化知识，是知识库的核心产出。

### 调研报告
- [[wiki/事务模型深度调研]] — 从 ACID 到全球分布式事务（MVCC/2PC/3PC/TCC/SAGA/Percolator/Spanner/Calvin）
- [[wiki/Doris-深度调研]] — Apache Doris 实时分析数据库全面调研：5 大模块（核心概念/存储引擎/查询流程/架构演进/元数据与一致性）

### 概念卡片
- [[wiki/LSM-Tree]] — LSM-Tree 总览：定义、历史、架构、Leveling/Tiering、经典优化、代表系统
- [[wiki/LSM-Tree-写放大]] — 写放大根因、Leveling vs Tiering 对比、Tiering 变体、Merge Skipping、TRIAD
- [[wiki/LSM-Tree-合并优化]] — VT-tree stitching、LSbM-tree、bLSM 写停顿调度
- [[wiki/LSM-Tree-硬件适配]] — 大内存/多核/NVMe SSD/NVM 下的 LSM-tree 优化
- [[wiki/LSM-Tree-自动调参]] — Monkey/Dostoevsky/ElasticBF 的自动调参策略
- [[wiki/LSM-Tree-二级索引]] — Diff-Index 体系、主键索引方案
- [[wiki/LSM-Tree-RUM猜想]] — 读-写-空间三选二理论框架及 RUM 定位
- [[wiki/RaaS-Replay-as-a-Service]] — RaaS (SIGMOD 2026): Replay-as-a-Service 消除存储计算分离 Tail Latency
- [[wiki/存储计算分离数据库的-Tail-Latency]] — 问题根因(日志链长度差异+CPU争抢)、传统解法为何无效
- [[wiki/Log-as-the-Database-模式]] — Log-as-Database 设计原理、结构性代价、Kafka 类比
- [[wiki/Event-Horizon-非对称依赖]] — Event Horizon (CIDR 2026): 半线性化与非对称依赖，降低跨地域协调延迟
- [[wiki/Doris-数据模型]] — Doris 四种表模型：Duplicate/Aggregate/Unique MoW/Unique MoR 的设计与权衡
- [[wiki/Doris-Segment-v2-存储格式]] — Doris 自研 Segment v2 列式存储：Page 体系、索引层级、DELETE_BITMAP、与 Parquet 对比
- [[wiki/Doris-Compaction-策略]] — Cumulative/Base/Quick/Vertical 四种 Compaction 的触发条件与一致性保证
- [[wiki/Doris-MPP-向量化查询引擎]] — MPP 分布式查询三阶段、四种 Shuffle 策略、向量化执行、Lakehouse 联邦查询
- [[wiki/Doris-Nereids-CBO-优化器]] — Nereids CBO 优化器：Join Reorder、CTE 物化、Runtime Filter、统计信息
- [[wiki/Doris-架构演进]] — Palo → Doris 3.0 存算分离的十年演进、关键架构决策、竞品定位
- [[wiki/Doris-元数据与一致性复制]] — BDB-JE → Meta Service 元数据演进、TabletScheduler 多副本复制、2PC 事务与故障恢复

---

## 第3层: Schema

> 规则与配置，定义知识库如何运作。

| 文件 | 说明 |
|------|------|
| [[purpose]] | 知识库的目标、研究方向 |
| [[schema]] | 分类体系、模板、[[wikilink]] 规范 |
| [[log]] | 操作日志 |

---

*由 CHANG_AI_TEAM Agent 维护，最后更新: 2026-06-14 22:45*
