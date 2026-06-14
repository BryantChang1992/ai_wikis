---
type: concept
title: "RaaS (Replay-as-a-Service)：存储计算分离数据库的 Tail Latency 消除方案"
sources:
  - "sources/papers/RaaS/RaaS-SIGMOD2026.pdf"
  - "sources/papers/RaaS/精读分析.md"
  - "sources/papers/RaaS/全文翻译.md"
tags:
  - RaaS
  - 存储计算分离
  - Tail-Latency
  - 数据库
  - 后台回放
  - SIGMOD-2026
  - 性能优化
  - 云数据库
created: 2026-06-14
updated: 2026-06-14
status: draft
related:
  - "[[存储计算分离数据库的 Tail Latency]]"
  - "[[Log-as-the-Database 模式]]"
  - "[[事务模型深度调研]]"
---

# RaaS（Replay-as-a-Service）

> **论文**：*Reducing Tail Latency in Storage-Disaggregated Database Systems* — SIGMOD 2026，Purdue University  
> **核心思路**：把数据库后台日志回放从存储引擎中解耦为独立服务，跑在集群空闲实例上，消除 CPU 争抢和 tail latency。

---

## 1. 一句话定义

**RaaS 是一种架构模式**：将 [[存储计算分离数据库的 Tail Latency|存储计算分离数据库]] 中 CPU 密集的后台日志回放（log replay）任务，从存储节点剥离为独立的无状态微服务，调度到集群空闲实例上执行。**核心效果来自"让空闲资源干活"而非"加机器"。**

---

## 2. 架构

```
Compute Layer ──redo log──► Log Store ──redo log──► Storage Layer
                                                         │
                                                   ① offload task
                                                         ▼
                                                Control Coordinator
                                                   │  Monitor
                                                   │  Scheduler
                                                   │  Dispatcher
                                                   ▼
                                         RSA (Replay Service Agent)
                                         on idle storage/compute nodes
                                                   │
                                               ② fetch/write
                                                   ▼
                                               AWS S3
```

### 两个新组件

| 组件 | 职责 | 特点 |
|------|------|------|
| **RSA** (Replay Service Agent) | 执行回放任务，从 S3 拉日志数据、写回物化结果 | 无状态、可任意扩缩 |
| **Control Coordinator** | 接收卸载请求 → 监控集群资源 → 调度到最优 RSA | 有状态（维护任务状态），单节点即可 |

### 关键设计：S3 作为数据总线

- Storage Node 只发 **18KB metadata**（KeySpace + LsnRange + page→log mapping + location index）给 Coordinator
- RSA 自己去 S3 拉数据 / 写结果
- → **网络开销降低 93.9%**（49GB → 3GB）

---

## 3. 四大技术挑战与解法

| # | 挑战 | 解法 |
|---|------|------|
| **C1** | 回放逻辑与前台 GetPage@LSN 代码强耦合 | 识别最小元数据边界（KeySpace + LsnRange + page→log mapping + location index），**只解耦 compute-intensive 的 page materialization step** |
| **C2** | 回放数据量巨大，存储节点 CPU 有限 | S3 中转：只发 metadata，RSA 自己去 S3 拉数据/写结果 → 网络开销降低 93.9% |
| **C3** | 原来单线程回放浪费 RSA 的多核资源 | 并行 MergeSort 按 page 分组日志 + 多线程并行 apply → Avg 延迟 -17.3%，P95 -23.7% |
| **C4** | 任务调度策略 | 优先级 = 任务量 × 等待时间；选 RSA：① 过滤 CPU>75% ② 过滤资源不足 ③ 优先上次服务过的（缓存亲和） ④ 选资源最多的 |

---

## 4. 任务卸载流程

1. Storage Node 检测到 CPU 不足 → 提取元数据
2. 发 metadata → Control Coordinator（**不传数据文件**）
3. Coordinator 选 RSA → 派发任务
4. RSA 从 S3 拉文件 → 执行 `remote_compact_tiered()` → 结果写回 S3
5. RSA 通知 Coordinator → Coordinator 通知 Storage Node 结果位置
6. Storage Node 更新本地索引

**关键行为**：如果 Storage Node 有空闲资源，任务在本地执行，不触发卸载。RaaS 只在资源争抢时才介入。

---

## 5. 实验效果

### 核心指标（SysBench 86GB，mixed read/write，8 实例）

| 指标 | Without RaaS | With RaaS | 改善 |
|------|-------------|-----------|------|
| **Avg Throughput** | 1351 TPS | **2376 TPS** | **+75.9%** |
| **P95 Latency** | 68.28 ms | **40.9 ms** | **-40.1%** |
| **P99 Latency** | 106.75 ms | **62.19 ms** | **-41.7%** |
| 请求 >100ms 占比 | 1.33% | 0.06% | **-95.5%** |
| <10ms 完成占比 | 32.5% | 53.3% | +20.8% |

### TPC-C 验证

| 指标 | Without RaaS | With RaaS | 改善 |
|------|-------------|-----------|------|
| P95 | 225.49 ms | 129.08 ms | **-42.76%** |
| P99 | 300.43 ms | 189.84 ms | **-36.81%** |

### CPU 利用率变化

- **Without RaaS**：storage node 后台回放期间 CPU 打到 400%（满核），前台查询饿死
- **With RaaS**：workload 期间 CPU 200-320%，后台回放在 idle interval 由 RSA 执行
- Storage node 空闲率：48% → 18%，**资源利用率大幅提升**

---

## 6. 容错设计

| 故障场景 | 系统行为 |
|----------|----------|
| S3 上传失败 | RSA 自动重试，对 storage node 透明 |
| 单个 RSA 崩溃 | Coordinator 检测心跳 → 剔除 → 重调度到其他 RSA（延迟约 +200ms，无性能影响） |
| 全部 RSA 不可用 | Coordinator 拒绝任务 → storage node 跳过本次回放 → 下次重新触发 |
| Coordinator 崩溃 | Storage node **回退到本地回放模式** → 无数据丢失 / 无宕机风险 |

---

## 7. 边界与局限

| 场景 | 表现 |
|------|------|
| Read-only workload | RaaS 无影响（无日志积压，任务在触发前取消） |
| Non-bursty（全集群持续高负载） | co-located RSA 无改善（预期内）；dedicated RSA 部署可提升至 2151 TPS（+71.6%） |
| 本地并行回放（不卸载） | **反而恶化**：P99 +38.3%（资源争抢加剧） |
| 提高本地回放频率 | 效果有限：P99 仅改善 3%（频繁 cancel + 资源争抢） |

---

## 8. 对分离式 Kafka / 流存储的启发

RaaS 的思路可直接迁移到分离式流存储系统（如 AutoMQ、Confluent Cloud）：

| 场景 | RaaS 模式映射 |
|------|--------------|
| **Log Compaction 卸载** | Kafka compaction 是 CPU 密集型操作，可卸载到空闲 broker |
| **Tiered Storage 回放** | 从 S3 拉 cold segment 回放时，借鉴 S3 中转减少 broker 网络开销 |
| **调度框架** | Coordinator 的 Monitor/Scheduler/Dispatcher 模式可直接复用 |

---

## 9. 论文评价

### 亮点
- 首次系统性分析存储分离 OLTP 数据库 tail latency 根因
- 思路简洁有效：解耦后台回放——本质是"让存储层回归存储"
- 实现务实：基于 OpenAurora 真实系统，**不改读写路径**
- 评估扎实：SysBench + TPC-C，覆盖容错、边界、non-bursty 场景
- 开源：[purduedb/OpenAurora/tree/RaaS](https://github.com/purduedb/OpenAurora/tree/RaaS)

### 局限
- COTS 数据库（Aurora/Socrates）验证依赖封闭系统，主要实验在 OpenAurora
- Non-bursty 场景 co-located 部署无增益，需 dedicated RSA 节点
- 未涉及多租户环境 tail latency 分析（论文列为 future work）
- Memory-disaggregated 数据库（RDMA/CXL 场景）待探索

---

## 10. Key Takeaways

1. **解耦是解法**：把 CPU 密集的后台任务从资源受限的存储层剥离
2. **S3 作为数据总线**：metadata 通过控制面，data 通过 S3 对象存储——减少 93.9% 网络开销
3. **资源利用率 > 资源扩容**：RaaS 核心效果来自利用空闲资源，而非加机器
4. **渐进式容错**：RSA 不可用时自动回退本地模式，保证可用性
