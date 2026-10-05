---
type: synthesis
title: LSM-Tree 存储引擎体系：成本模型到部署决策
sources:
- '[[知识库/wiki/LSM-Tree]]'
- '[[知识库/wiki/LSM-Tree-写放大]]'
- '[[知识库/wiki/LSM-Tree-合并优化]]'
- '[[知识库/wiki/LSM-Tree-硬件适配]]'
- '[[知识库/wiki/LSM-Tree-自动调参]]'
- '[[知识库/wiki/LSM-Tree-二级索引]]'
- '[[知识库/wiki/LSM-Tree-RUM猜想]]'
tags:
- 存储引擎
- LSM-Tree
- 综述
- 数据库
- 写优化
created: 2026-06-14
updated: '2026-10-05'
status: draft
related:
- '[[知识库/wiki/InfluxDB深度调研]]'
- '[[知识库/wiki/Doris-深度调研]]'
- '[[知识库/wiki/Doris-Compaction-策略]]'
- '[[知识库/wiki/Doris-Segment-v2-存储格式]]'
- '[[知识库/wiki/事务模型深度调研]]'
synced_at: '2026-10-05'
blog_url: https://bryantchang1992.github.io/ai_memory_chang_ai_team/posts/wiki-synthesis-lsm-tree/
blog_source: _posts/2026-06-14-wiki-synthesis-lsm-tree.md
blog_source_commit: f83970fa7e6ad32d626cc6ca3ba7428c90a638a5
blog_body_sha256: e2b10a04ada5e463d7c7a218994a9f41ba8e702f0cc24e920f501f6eeead83fb
reviewed: '2026-10-05'
review_scope: 关键机制、证据范围、图示与跨页一致性
diagram_format: mermaid
---

# LSM-Tree 存储引擎体系：成本模型到部署决策

LSM 用内存缓冲、不可变有序文件和后台合并重组读写成本。WAL、过滤器、缓存、合并调度、并发控制分别承担不同职责；“有追加日志”不足以把一个系统归类为 LSM。

```mermaid
flowchart TD
  W[写入] --> M[内存缓冲]
  W --> L[按耐久性协议写 WAL]
  M --> S[刷盘生成有序文件]
  S --> C[Compaction]
  C --> S
  Q[查询] --> M
  Q --> F[索引、Bloom Filter 与缓存]
  F --> S
  T[成本模型与自动调参] --> C
  T --> F
  H[硬件与负载] --> T
```

## 六个主题应怎样连起来

| 主题 | 解决的问题 | 不可忽略的代价 |
|---|---|---|
| [[LSM-Tree-写放大]] | 同一逻辑数据反复重写 | 降低写放大可能增加读与空间成本 |
| [[LSM-Tree-合并优化]] | 如何选文件、安排资源与控制积压 | 前台 P99、后台债务和崩溃恢复 |
| [[LSM-Tree-硬件适配]] | DRAM、SSD、持久内存、网络的成本差异 | 并发、带宽、耐久性与故障域 |
| [[LSM-Tree-自动调参]] | 过滤器、层级、冷热数据的资源分配 | 模型假设、观测延迟和在线调整代价 |
| [[LSM-Tree-二级索引]] | 主键外的定位与索引维护 | 原子性、过期条目验证、恢复 |
| [[LSM-Tree-RUM猜想]] | 讨论读、更新与内存/空间之间的取舍 | 不能当作禁止任何局部改进的无条件定理 |

## 容易误读的优化

Monkey 的非均匀 Bloom filter 分配，在相应模型中让靠近内存的较小层分得更多 bits/key；越往容量大的层，允许的误判率越高。不是“最大层每 key 分最多位”。层的总位数和每 key 位数也要区分。

Dostoevsky 的 Lazy Leveling 避免把所有层的合并政策锁成同一种：非底层保留更多 run，底层控制空间。它的成本结论依赖模型和查询组合，不是所有硬件上都最优。ElasticBF 动态启用过滤器的精度配置，不是任意停用覆盖某些键的唯一过滤器。

KV 分离减少 value 参与反复合并，却引入 value log 管理、垃圾回收和范围读取代价；不能仅看写入吞吐。bLSM 的调度是相关研究之一，旧稿“唯一解决停顿”“此后十年无人研究”没有综述范围外的充分依据，已撤回。

## 度量口径与复现实验

写放大应写清分母是用户字节、记录还是块 I/O，分子是否包含 WAL、flush、compaction、复制及设备内部写入。渐近更新 I/O 成本公式里的 block size 不能不加说明地当作字节写放大系数。

一个最小比较应固定数据总量、value 大小、读写比、偏斜、缓存预算、磁盘与线程，先灌入稳态数据，再观察足够长时间的合并。记录吞吐、P50/P99、读写放大、空间、stall 时长与恢复时间。只跑短期空库写入容易隐藏 compaction 债务。

## 系统关系和证据层级

Doris rowset/compaction 与 InfluxDB TSM 借鉴相近思想，却不是标准 RocksDB 层级的简单改名。FASTER 采用 hash index + hybrid log，也不应被列作 LSM 变体。HATS 在 Cassandra 上协调读与本地压实，CaaS/Hailstorm 等方向讨论卸载，二者需要区分。

本综述依赖两篇已核对的 LSM 综述和知识卡片；其中转述的每个子系统并非全部取得独立原文。继续阅读 [[LSM-Tree-存储引擎新进展-2026综述]]、[[Hailstorm-存算分离LSM数据库]] 与 [[CXL-3.0-内存池化新范式]] 时，应保留这条证据边界。
