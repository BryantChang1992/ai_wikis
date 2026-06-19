---
type: meta
title: "CHANG_AI_TEAM 知识库"
tags: ["meta", "知识库"]
created: 2026-06-14
updated: 2026-06-16
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

### 领域综述（`wiki/synthesis/`）
- [[wiki/synthesis/LSM-Tree-存储引擎体系综述]] — 从 7 张 LSM 卡片提炼：三条主线（写放大/合并优化/硬件适配）+ RUM 猜想框架
- [[wiki/synthesis/LSM-Tree-存储引擎新进展-2026综述]] — 🆕 Silo 分布式 Compaction 调度 + Fluss LSM 实践
- [[wiki/synthesis/分布式数据系统事务与一致性新进展-2026综述]] — 🆕 CockroachDB + Aurora + Rosé + Agent-First 四系统事务设计横向对比
- [[wiki/synthesis/Fluss-流处理平台架构综述]] — 🆕 Fluss 五大模块综述：Kafka 兼容 + LSM 存储 + Arrow 列式 + Lake 湖仓
- [[wiki/synthesis/OLAP与TSDB全景综述]] — Doris 与 InfluxDB 横向对比：存储引擎/查询模式/架构趋同趋势
- [[wiki/synthesis/分布式数据系统一致性体系]] — 元层次提炼：事务层/副本层/会话层 + 协调代价统一框架
- [[wiki/synthesis/Apache-Doris-OLAP-数据库体系综述]] — Doris 体系综述
- [[wiki/synthesis/InfluxDB-时序数据库体系综述]] — InfluxDB 体系综述
- [[wiki/synthesis/流处理系统演化综述]] — 🆕 SP-Survey 论文驱动：三代演化、乱序/状态/容错/弹性/Dataflow 五大域、与 LSM-Tree/Fluss/事务 交叉关联
- [[wiki/synthesis/共识协议体系综述]] — 🆕 Ongaro (Stanford 2014) + Howard (Cambridge 2019) 双博士论文驱动：Raft 工程简化 + Howard 理论泛化双线并进
- [[wiki/synthesis/AI-Infra-Agent基础设施体系综述]] — 🆕 Agent Infra 四层体系（Harness/Security/Control/Memory）：10 张卡片跨层整合 + 成熟度评估
- [[wiki/synthesis/知识库优化方案-2026-06-15]] — 知识库 frontmatter/索引/tags 优化清单

### 健康检查
- [[wiki/synthesis/Lint-2026-06-14]] — 首轮 Lint 报告：3 孤儿页、4 概念缺口、3 缺失跨引用
- [[wiki/synthesis/Lint-2026-06-19]] — Week 07 维护日 Lint：0 dangling、1 孤儿页（Chandy-Lamport）、修复 13 处 synthesis/ 前缀引用

### Apache Fluss 调研（新增）

#### 架构分析
- [[wiki/Fluss-整体架构]] — Fluss 整体架构与 Kafka 2.7.2 对照：8 大核心差异、30% 代码复用分析、8 个独有能力
- [[wiki/Fluss-存储引擎]] — 三层存储模型（LocalLog/KvTablet/RemoteLog）、Log 子系统 10 项差异、Tablet vs Partition 对比
- [[wiki/Fluss-分布式协调]] — CoordinatorServer 事件驱动、双状态机、16 种事件类型、重平衡 Goal 优化器
- [[wiki/Fluss-RPC与网络]] — Netty + Protobuf 全自研、61 API Key 清单、双协议引擎、GatewayClientProxy 动态代理
- [[wiki/Fluss-客户端与计算集成]] — Writer/Scanner/Lookuper 三合一 API、Flink Connector 全链路、Lake Storage 插件架构
- [[wiki/Fluss-Lake层与湖仓融合]] — Iceberg/Paimon/Hudi/Lance 四种后端、Tiering 架构、与 Kafka KIP-405 的本质区别

#### 概念卡片
- [[wiki/Fluss-KV存储-RocksDB]] — KV 子系统全貌：WAL 复用 changelog LogTablet（Write-Once Read-Multiple）、Snapshot 全链路、RowMerger 四种实现
- [[wiki/Fluss-Tiering分层架构]] — 独立 Flink 作业的 Tiering 工作流、LakeTableTieringManager 协调
- [[wiki/Fluss-Kafka兼容层]] — Kafka 协议兼容链路（仅 API_VERSIONS 完整，其余骨架）、双协议 RequestType FLUSS/KAFKA
- [[wiki/Fluss-Arrow列式记录格式]] — 三种 LogFormat、Arrow vs Kafka Record 对比、列裁剪/谓词下推/零拷贝路径

### 调研报告
- [[wiki/事务模型深度调研]] — 从 ACID 到全球分布式事务（MVCC/2PC/3PC/TCC/SAGA/Percolator/Spanner/Calvin）
- [[wiki/InfluxDB深度调研]] — InfluxDB 时序数据库全面调研：从 TSM 到 InfluxDB 3.0 列存引擎的演进（5 模块）
- [[wiki/Doris-深度调研]] — Apache Doris 实时分析数据库全面调研：5 大模块（核心概念/存储引擎/查询流程/架构演进/元数据与一致性）

### 概念卡片

#### 流处理 🆕
- [[wiki/Stream-Processing-System-Generations]] — 流处理三代演化（DSMS → Dataflow → Emerging）：Table 1 七大维度、Figure 1 时间线
- [[wiki/流处理乱序数据管理]] — 五种进度追踪机制（Slack/Heartbeat/LWM/Punctuation/Pointstamp）+ 三种修正策略
- [[wiki/流处理状态管理]] — Synopsis → App-Managed → System-Managed 三阶段 + In-Memory/Out-of-Core/External 架构
- [[wiki/流处理容错模型]] — Exactly-Once 四级分类 + Output Commit Problem + Table 4 四维度 18 系统对比
- [[wiki/流处理弹性与重配置]] — SEEP/Chi/Megaphone 三种重配置方案 + Buffer vs Credit 流控
- [[wiki/Dataflow-Model]] — Google Dataflow 批流统一四抽象 + What/Where/When/How 四问

#### 存储引擎
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

### 2026 顶会论文概念卡片 🆕

#### CockroachDB Leader Leases (SIGMOD 2026)
- [[wiki/CockroachDB-Leader-Lease-整体设计]] — Leader Leases 三层解耦：Lease ← Fortification ← Liveness Fabric，CPU 节省 85%+
- [[wiki/CockroachDB-Liveness-Fabric-故障检测层]] — 去中心化集群故障检测：有向 support 关系 (epoch, expiration)，O(N_nodes²)
- [[wiki/CockroachDB-Leader-Fortification]] — Raft 增强领导保证：MsgFortifyLeader 确定性承诺替代心跳超时

#### Aurora PostgreSQL Limitless (SIGMOD 2026 Industry)
- [[wiki/Aurora-Limitless-分布式架构]] — Router/Shard 解耦架构、三种表类型、co-location、查询 pushdown 优化
- [[wiki/Aurora-Limitless-时间戳事务]] — Clock-SI + HLC 混合方案、Lead Shard 2PC、外部一致性实现
- [[wiki/Aurora-Limitless-自适应扩缩容]] — ACU 垂直扩缩 + Table Slice 水平 shard split 二维扩缩

#### Rosé (CIDR 2026)
- [[wiki/Rosé-异步复制协议设计]] — 主备异步复制：单调前缀一致性、分区灵活配置
- [[wiki/Rosé-Coordinated-Apply-协调应用]] — WAL/KV 持久化解耦的协调应用机制

#### Silo (FAST 2026)
- [[wiki/Silo-分布式LSM-Compaction调度]] — 全局 compaction 调度：Anti-hog / Pro-hog 策略、跨节点 compaction 迁移
- [[wiki/Silo-Compaction-迁移协议]] — Compaction 迁移协议设计：数据一致性、WAL 协调、网络开销

#### Agent-First Data (CIDR 2026)
- [[wiki/Agent-First-Data-Systems]] — Agent 优先的数据系统架构：分支事务、语义缓存、Agentic Speculation
- [[wiki/Agent-First-Branch-Transactions-分支事务]] — MVCC 快照 fork + 分支合并策略的 Agent 事务模型
- [[wiki/Agentic-Memory-语义缓存]] — 基于语义相似度而非精确 key match 的缓存层

#### 共识协议 🆕
- [[wiki/Raft-共识算法协议核心]] — Leader Election (Term 逻辑时钟) + Log Replication + Safety 三维分解
- [[wiki/Paxos-理论到实践的鸿沟]] — Single-decree Paxos 的四大缺失 + Multi-Paxos 实现者魔改问题
- [[wiki/Raft-集群成员变更]] — Joint Consensus (Cold ∪ Cnew) 消除配置变更脑裂风险
- [[wiki/Raft-日志压缩]] — Snapshot 机制替代前缀日志 + InstallSnapshot RPC 分块传输
- [[wiki/Raft-客户端交互]] — Linearizability 保证 / Read Index-Lease Read / 幂等操作去重
- [[wiki/Chandy-Lamport-分布式快照算法]] — 🆕 分布式快照开山论文 (TOCS 1985)：Marker 传播 + Flink Checkpoint 映射
- [[wiki/共识算法族系-从Paxos到广义解]] — 🆕 Heidi Howard 2019 博士论文全景：4 层递进泛化 → 共识算法族
- [[wiki/Paxos-Quorum-Intersection-Revised]] — 🆕 Flexible Paxos: Phase-1/Phase-2 quorum 仅跨 phase 相交
- [[wiki/Paxos-Value-Selection-Revised]] — 🆕 Quorum-based 选值：不被"最高 epoch"规则过度限制
- [[wiki/Paxos-Epochs-Revised]] — 🆕 Epochs by Recovery：去中心化 1 RTT 决策 + Multi-path Paxos
### AI Infra — Agent 基础设施 🆕

#### Agent Memory & Security
- [[wiki/Agent-Memory-Survey-2026综述]] — ArXiv 2026-03：Agent Memory 系统化综述（write→manage→read 循环 + 五大机制家族）
- [[wiki/Parallax-Agent安全架构]] — ArXiv 2026-04：四原则架构（Cognitive-Executive Separation）+ 98.9% 攻击阻断率
- [[wiki/Anthropic-Agent安全容器化实践]] — Anthropic Engineering Blog：三产品容器化实践（三类风险 × 三类防御 × 三种隔离模式）
- [[wiki/Agent-Sandbox-安全沙箱选型]] — LangChain Blog：Lethal Trifecta + Sandbox 五要素 + microVM 内核隔离

#### Agent Harness & 工程实践
- [[wiki/Custom-Agent-Harness-Middleware架构]] — LangChain Blog：agent = model + harness + Middleware 四杠杆 + 能力映射表
- [[wiki/Loop-Engineering-多层Agent循环架构]] — LangChain Blog：四层循环架构（Agent→Verification→Event-Driven→Hill Climbing）
- [[wiki/Model-Neutrality-模型中立与反锁定]] — LangChain Blog：云→模型 锁定模式重演 + 中立 Harness 三要素
- [[wiki/Agent-Fault-Tolerance-容错设计]] — LangChain Blog：RetryPolicy/TimeoutPolicy/error_handler + SAGA 补偿模式
- [[wiki/Agent-Cost-Control-Gateway成本控制]] — LangChain Blog：LLM Gateway 四维预算 + 分钟级成本可观测性

### Fluss 实践 🆕
- [[wiki/Fluss-EKS-生产部署实践-Fresha]] — Fresha Data Engineering Blog：EKS 部署四限制修复 + Flink Connector 踩坑
- [[wiki/Fluss-PR-3420-Watermark-to-Paimon]] — GitHub apache/fluss #3420：Watermark → Paimon Snapshot 全链路（49 文件变更）

---

## 第3层: Schema

> 规则与配置，定义知识库如何运作。

| 文件 | 说明 |
|------|------|
| [[purpose]] | 知识库的目标、研究方向 |
| [[schema]] | 分类体系、模板、[[wikilink]] 规范 |
| [[log]] | 操作日志 |

---

*由 CHANG_AI_TEAM Agent 维护，最后更新: 2026-06-19*
