---
type: concept
title: "Silo — 分布式 LSM-Tree Compaction 全局调度"
tags:
  - LSM-Tree
  - Compaction
  - 调度
  - WAF
  - 写放大
  - 分布式存储
  - SLO
  - FAST-2026
related:
  - "[[LSM-Tree]]"
  - "[[LSM-Tree-合并优化]]"
  - "[[Silo-Compaction-迁移协议]]"
sources:
  - "sources/papers/LSM-Scheduling/LSM-Scheduling-FAST2026.pdf"
created: 2026-06-15
updated: 2026-06-15
---

# Silo — 分布式 LSM-Tree Compaction 全局调度

## 一句话总结

第一个将 LSM-Tree compaction 调度从**单节点提升到集群层面**的框架：用 WAF（写放大因子）作为跨节点可比较的健康度量信号，通过四种迁移策略（anti-hog/pro-hog/cross-zone/延迟判断）消除 tail node 的 compaction 瓶颈，将 SLO 满足率提升 +57%，P99 读延迟降低 -62%。

## 为什么需要 Silo

### 现有 LSM 优化的盲区

| 方案 | 优化目标 | 作用域 | 遗留问题 |
|------|---------|--------|----------|
| Monkey | 读放大 | 单节点 | 不解决节点间差异 |
| Dostoevsky | 写/读/空间放大 | 单节点 | 不解决节点间差异 |
| PiSDF | compaction 后抖动 | 单节点 | 不解决节点间差异 |
| Q-LSM | compaction 负载建模 | 单节点 | 不解决节点间差异 |
| **Silo** | **集群 SLO** | **集群** | — |

### 现实数据

阿里 AtlasFS（9 节点）trace 分析：
- **compaction_workdist per-node 差异高达 1.9×**
- 一个 tail node 在 compaction 上挣扎 → 即使其他 8 个节点正常，P99 读延迟也是那 1 个 tail node 决定的

## WAF 为什么是好的调度信号

| 候选指标 | 优点 | 缺点 |
|----------|------|------|
| CPU_util | 易获取 | compaction 可能是 I/O-bound → CPU30% 但磁盘100% |
| QPS | 反映负载 | 不直接反映 compaction 压力 |
| 读延迟 | 反映用户感知 | 波动大，不适合做调度阈值 |
| **WAF** | ✅ 准确反映 compaction 量<br>✅ 跨节点可直接比较<br>✅ RocksDB 内置可查询<br>✅ 稳定（不剧烈抖动） | — |

## 调度流程

```
Global Scheduler: 收集 (WAF_i, CPU_i, IO_i, QPS_i, P99_i)
  → 计算健康分数: Score_i = 0.5·WAF + 0.3·CPU + 0.2·IO
    → 识别 hog (Score > μ + 1.5σ) + target (Score 最低)
      → 选择 WAF 贡献最大的 compaction job
        → 迁移指令发送给 hog + target
          → Target 远程读 SST → 执行 compaction → 写回原节点
```

## 关键效果

| 指标 | 无调度 | Silo | 改善 |
|------|--------|------|------|
| SLO 满足率 (YCSB-A) | 62% | 97% | **+57%** |
| P99 读延迟 (YCSB-E) | 4.2ms | 1.6ms | **-62%** |
| WAF 差异 (节点间) | 2.9× | 1.2× | 均衡 |
| 吞吐 | 基准 | ±2% | 0 退化 |

## 局限

- ⚠️ 仅 9 节点评估 → 数百节点规模未知
- ⚠️ 迁移依赖远程读（需要快速网络）→ CrossZone/DC 延迟高
- ⚠️ 与 replication（Raft）的交互未讨论
- ⚠️ Workload 突变时的收敛时间未分析
- ⚠️ 异构集群（不同硬件）的调度未解决

## 与知识库关联

- [[LSM-Tree]]：Sil 的基础理解需要
- [[LSM-Tree-合并优化]]：Silo 是这些单节点优化的**集群级补充**
- [[Silo-Compaction-迁移协议]]：迁移协议的详细设计
