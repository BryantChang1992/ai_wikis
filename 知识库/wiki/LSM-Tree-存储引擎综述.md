---
type: synthesis
title: "LSM-Tree 存储引擎综述"
sources:
  - "[[LSM-Tree]]"
  - "[[LSM-Tree-写放大]]"
  - "[[LSM-Tree-合并优化]]"
  - "[[LSM-Tree-硬件适配]]"
  - "[[LSM-Tree-自动调参]]"
  - "[[LSM-Tree-二级索引]]"
  - "[[LSM-Tree-RUM猜想]]"
tags:
  - 存储引擎
  - LSM-Tree
  - 综述
created: 2026-06-14
updated: 2026-06-14
status: draft
related:
  - "[[事务模型深度调研]]"
  - "[[InfluxDB-TSM存储引擎]]"
---

# LSM-Tree 存储引擎综述

> 本页从 7 张 LSM-Tree 概念卡片中提炼，形成对 LSM-tree 存储引擎的全局认知。

## 1. 领域定义

LSM-Tree（Log-Structured Merge-Tree）是写优化的存储结构。核心思想：将随机写转为顺序写，通过后台合并（compaction）逐步整理数据，以写放大代价换取写吞吐。已成为 RocksDB、Cassandra、HBase、TiKV 等现代 NoSQL 系统的默认存储引擎。

## 2. 概念关系图

```
                    ┌──────────────────────┐
                    │    LSM-Tree 总览     │ ← 定义、历史、架构
                    └──────┬───────────────┘
                           │
          ┌────────────────┼──────────────────┐
          ▼                ▼                  ▼
   ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
   │   写放大      │ │  合并优化     │ │ 硬件适配      │
   │ Leveling vs  │ │ VT-stitching │ │ WiscKey/KV分离│
   │ Tiering 根因 │ │ LSbM / bLSM  │ │ NVM / 多核    │
   └──────┬───────┘ └──────┬───────┘ └──────┬───────┘
          │                │                │
          └────────┬───────┴────────┬───────┘
                   ▼                ▼
          ┌──────────────┐ ┌──────────────┐
          │   RUM 猜想   │ │  二级索引    │
          │ 读-写-空间   │ │ Diff-Index   │
          │ 三选二框架   │ │ 维护策略      │
          └──────┬───────┘ └──────┬───────┘
                 │                │
                 └────────┬───────┘
                          ▼
                 ┌──────────────┐
                 │  自动调参     │
                 │ Monkey/      │
                 │ Dostoevsky/  │
                 │ ElasticBF    │
                 └──────────────┘
```

## 3. 三条主线

### 3.1 写放大——最核心的 trade-off

LSM-Tree 的根本代价。[[LSM-Tree-写放大|详见卡片]]：

| 策略 | 写放大 | 读放大 | 空间放大 |
|------|:------:|:------:|:--------:|
| Leveling | 高（每层重写） | 低（每层 1 个 sorted run） | 低 |
| Tiering | 低（只合并到新层） | 高（每层多个 sorted run） | 高 |

TRIAD 思路：热数据留内存 + 冷数据偏 tiering，打破了"所有数据同一策略"的假设。

### 3.2 合并优化——工程上最大的创新点

合并（compaction）是 LSM-tree 最复杂的组件。三个关键突破：
- **VT-tree**：stitching 技术让合并无需重写全部数据
- **LSbM-tree**：延迟删除缓冲区减少合并频率
- **bLSM**：写停顿调度算法，让合并不再阻塞写入

合并策略直接影响 [[LSM-Tree-RUM猜想|RUM 猜想]] 的三角权衡。

### 3.3 硬件适配——让 LSM-tree 跟上硬件演进

从大内存（Accordion）到多核（cLSM）到 NVMe SSD（WiscKey KV 分离）到 NVM（NoveLSM），LSM-tree 的每次重大优化几乎都跟硬件代际更替绑在一起。

## 4. 跨页连接洞察

1. **写放大 → 合并优化 → RUM 猜想 → 自动调参** 形成一条完整的优化链：理解根因 → 工程手段 → 理论框架 → 自动化
2. [[LSM-Tree-硬件适配|硬件适配]] 和 [[LSM-Tree-合并优化|合并优化]] 之间存在强烈的交叉：WiscKey 的 KV 分离本质上是硬件特性（NVMe 随机读够快）驱动的合并策略变革
3. [[LSM-Tree-二级索引|二级索引]] 是这个体系的"附加负担"——它叠加在已有的 RUM 三角上，让设计约束进一步收紧

## 5. 对外桥接

- [[事务模型深度调研]]：LSM-tree 是 TiDB/TiKV、CockroachDB 等分布式事务系统的底层存储。写放大直接影响事务吞吐
- [[InfluxDB-TSM存储引擎]]：TSM 是 LSM-tree 在时序场景的变体——保留了写优化核心，针对时序数据的 append-only + 时间分区做了专门适配

## 6. 待探索方向

- [ ] LSM-tree 在存算分离架构下的新形态（如 RocksDB Cloud、S3-backed compaction）
- [ ] 与 B+Tree 的融合方案（如 Bw-tree、LeanStore）是否正在模糊两类引擎的边界
- [ ] LSM-tree 在 AI 推理场景的应用（向量索引、KV 缓存）
