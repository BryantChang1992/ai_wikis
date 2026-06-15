---
type: concept
title: "Silo Compaction 迁移协议 — Anti-hog 与 Pro-hog 设计"
tags:
  - LSM-Tree
  - Compaction
  - 调度
  - 迁移协议
  - WAF
  - FAST-2026
related:
  - "[[Silo-分布式LSM-Compaction调度]]"
  - "[[LSM-Tree-合并优化]]"
sources:
  - "sources/papers/LSM-Scheduling/LSM-Scheduling-FAST2026.pdf"
status: draft
created: 2026-06-15
updated: 2026-06-15

---

# Silo Compaction 迁移协议 — Anti-hog 与 Pro-hog 设计

![[diagram/silo-compaction-scheduling.svg]]

## 一句话总结

Silo 实现 Compaction 任务的跨节点迁移：hog node 暂停 compaction（不放弃 metadata）→ target node 远程读 SST 文件 → 在 target 执行 merge-sort compaction → 写回原节点 → 两边更新元数据。三种迁移模式分别针对不同场景。

## 三策略总览

| 策略 | 触发条件 | 含义 | 场景 |
|------|----------|------|------|
| **Anti-hog** | Score > μ + 1.5σ 且存在轻载节点 | 被动响应，已 overload 才迁移 | 日常 tail node 处理 |
| **Pro-hog** | 预测即将 overload | 主动预防，在成为瓶颈前迁移 | 可预见的负载尖峰 |
| **CrossZone** | 本 Zone 内无轻载节点 | 跨 AZ/DC 利用远端空闲资源 | 本 Zone 整体高负载 |

## Anti-hog 协议详细流程

### Phase 1: Global Scheduler Decision

```
1. 每 1s 收集 per-node metrics
2. 计算 health score: Score = 0.5·WAF + 0.3·CPU + 0.2·IO
3. 统计集群分数分布（μ, σ）
4. Hog = nodes where Score > μ + 1.5σ
5. Target = node with min Score (需要 CPU < 70%, IO < 70%)
6. 从 hog 的 pending compaction queue 选择 WAF 贡献最大的 job
7. 发送迁移指令给 hog + target
```

### Phase 2: Migration Execution

![Silo-Compaction-迁移协议 - 图1](../diagram/Silo-Compaction-迁移协议-fig.svg)

### 为什么写回原节点而不是留在 target？

- 数据必须保持本地——Silo 不改变数据分布，只是把 compaction 的计算和 I/O 迁移到轻载节点

## Pro-hog 的区别

- Pro-hog 在 hog detection 中使用**趋势预测**而非瞬时阈值
- 算法：跟踪 Score 的短期滑动平均（5s window）
- 触发条件：Score_trend > threshold_rate（快速增长）

目的：避免"compaction 开始做才 overload"的情况——在任务 big 之前迁移。

## 失败处理

- 迁移期间 target 节点故障 → hog Silocal 超时重试（3 次）→ 回退到本地 compaction
- 迁移期间 hog 节点故障 → 无影响（旧 SST 文件保留）
- WAF 在 Raft 重放时的冲突 → 论文未处理（未来工作）

## 迁移成本分析

| 成本项 | 数量级 | 影响 |
|--------|--------|------|
| **远程读** | SST 大小 × 1（32-64MB chunks stream） | 0.2-1s 网络传输 |
| **远程 compaction** | 迁移的 compaction CPU+IO | Target 节点负担 |
| **写回** | 新 SST 文件写回原节点 | 0.3-1s 网络传输 |
| **元数据更新** | Protobuf metadata RPC | <1ms |
| **总迁移时间** | **0.5-2s**（SST 5-100MB） | 在 compaction 等待时间内 |

## 局限

- 同 AZ 内 1-5ms RTT 可行，跨 DC（20-50ms RTT）网络开销显著
- 数 GB 的 SST 文件迁移成本高 → 需要判断"迁移是否值得"
- 迁移期间该 key range 的 compaction 暂停 → 影响读放大

## 与知识库关联

- [[LSM-Tree-合并优化]]：Silo 的 compaction 迁移是与 Monkey/Dostoevsky 等单节点优化正交的改进
- [[Silo-分布式LSM-Compaction调度]]：调度框架的总览
