# Bottling the River: Apache Fluss on EKS — 精读分析

- **URL**: https://medium.com/fresha-data-engineering/bottling-the-river-apache-fluss-on-eks-6aa63c00d9e9
- **作者**: Nicoleta Lazar, Fresha Data Engineering
- **发布日期**: 2026-04-30
- **精读日期**: 2026-06-19

---

## 1. 文章定位

Fresha 团队在生产 EKS 集群上部署 Apache Fluss 的完整实战记录。不是 tutorial——是 debug log。文章的价值不在"怎么做"，而在"什么地方会坏"。

---

## 2. Fluss 本质理解

### 2.1 "Searchable Kafka"

数据流式写入 tablet server 上的表，可选 tier 到对象存储（Iceberg/Paimon）。每表按 bucket 分片→分布到 tablet server→多副本复制。这是与 Kafka topic/partition 同构的水平扩展模型。

### 2.2 列式存储栈：Arrow IPC End-to-End

日志段以 Apache Arrow IPC 列式存储——**从 wire 到 disk**。消除了行-列转换、启用压缩、解锁服务端列裁剪（服务于高吞吐分析扫描）。

### 2.3 Primary Key Tables：Log + Cache 统一

每 bucket 嵌入 RocksDB 实例存储每条 key 的最新值，同时 emit 所有变更的 CDC log。这让**流消费和点查询共享同一存储层**——传统架构中这需要两个独立系统（Kafka + 外部 KV store）。

### 2.4 Flink 深度融合

- 将 Flink state 外部化到 Fluss → lookup joins / delta joins 变为快速（近似）无状态
- 同一表可跨多个 Flink job 共享（而非每个 job 重建自己的 state）
- 运维收益：更小 checkpoint、更快恢复、更少 state-related failure

---

## 3. EKS 部署经验

### 3.1 Helm Charts 发现的问题

| 问题 | 影响 | 修复 | 版本 |
|------|------|------|------|
| IRSA 不支持 | 无法通过 IAM Roles for Service Accounts 认证 | #2142，由 Fresha 团队提交 | 0.9 |
| S3 Delegation Token 硬编码 static credentials | IRSA-bound pods 失败 | #3066: 切换为 AWS SDK default credentials chain | 0.9.1 |
| 密码管理无 clean path | SASL 密码和 S3 key 必须裸写在 values.yaml | #3172 | 0.9.1 |
| Pod Anti-Affinity 缺失 | 单节点故障可同时 destroy 所有副本 | #3153 | 0.9.1 |

**关键教训**：早期项目的 Helm chart 普遍缺失生产级安全配置（IRSA、密钥管理、调度约束）。

### 3.2 存储丢失事故

核心发现：**Fluss 默认写 emptyDir + 无优雅关闭 flush**。
- 默认：RemoteLogManager 按定时器（默认 1 分钟 `remote.log.task-interval-duration`）tier 关闭的 segment 到 S3
- 无 Graceful Shutdown Hook：pod 重启前如果定时器未触发 → 未 tier 的 segment **永久丢失**

**修复三步**：
1. Coordinator + Tablet Server 全部切换为 PersistentVolumeClaims
2. min ISR 提至 2（replication factor 3 下容忍单 pod 故障）
3. Pod anti-affinity 确保副本分布不同节点

---

## 4. Flink-Fluss Connector 实战

### 4.1 依赖地狱

| 错误 | 根因 | 修复 |
|------|------|------|
| `UnsupportedFileSystemSchemeException for s3` | 缺少 `fluss-fs-s3` jar | 添加 |
| `NoAwsCredentialsException` | S3 delegation token 使用 static credentials provider，IRSA 无法生成 | 临时写 static key；0.9.1 修复 |
| `NoSuchMethodError: base64DecoderStringLookup()` | 缺少 `commons-text-1.11.0.jar` / `commons-lang3-3.14.0.jar` | 添加 |
| `OutOfMemoryError: Direct buffer memory` | Flink TaskManager off-heap 不足 | `taskmanager.memory.task.off-heap.size: 1g` |

### 4.2 Delegation Token 机制深度

**客户端侧 S3 认证流程**：
```
Fluss Coordinator → Fluss Client: delegation token (临时凭证)
Fluss Client → S3: 使用 delegation token 读取 tiered data
```

**两个关键点**：
1. Dummy credentials 可绕过服务端写（server-side write 使用 IRSA），但客户端读取 PrimaryKey table 时依赖服务器生成的 delegation token——dummy credentials 使 token 无效
2. 修复后的架构：server 和 delegated-client identity 独立配置，read-write server role vs read-only client role，**全链路无 static key**

---

## 5. 架构判断：Fluss 在 Lakehouse 生态中的位置

### 5.1 与 Kafka 的定位差异

| 维度 | Kafka | Fluss |
|------|-------|-------|
| 存储格式 | Row-based (append-only log) | Columnar (Arrow IPC) |
| 查询能力 | 仅 offset 消费 | 支持点查询 (RocksDB) + 分析扫描 (column pruning) |
| Lakehouse 集成 | Tier 到 S3 需要外部工具 | 原生 Tier 到 Iceberg/Paimon |
| Flink 集成 | 广泛成熟 | 深度优化（外部化 state） |
| 成熟度 | 生产级（2011-） | incubating（2025-） |

### 5.2 适用场景判断

Fluss 适合**同时需要流处理和点查询/分析的工作负载**——传统需要 Kafka + KV store + OLAP 三件套。不适合纯消息队列场景（Kafka 更简单成熟）。

### 5.3 生产就绪度

从 Fresha 的经验看，0.9 版本的生产部署需要**大量补丁**（4 个 issue 修复 + 配置调优）。0.9.1 应接近"可接受的基线"。

---

## 6. 工程启示

1. **早期项目的 Helm chart 几乎肯定缺生产所需**：IRSA、密钥管理、调度约束是必检项
2. **默认 emptyDir + 定时 tier 是数据丢失的地雷**：必须确认 graceful shutdown flush + 持久化存储
3. **Store/Lake 的统一是正确方向**：Fluss 的 PK Table（log + cache 统一）和 Kafka 的外部 KV store 集成本质解决同一问题，但统一后运维复杂度大幅降低
4. **Flink-Fluss connector 的依赖管理需要改进**：3+ 个独立的 jar 依赖，期待未来 fat jar 或 BOM
5. **Delegation token 是流存储安全的关键设计点**：server 和 client 身份的独立配置比共享 credential 安全得多

---

## 7. 与 CHANG_AI_TEAM 知识库的关联

- **[[Fluss-PR-3420-Watermark-to-Paimon]]**：本文的 tiering 基础设施正是 PR #3420 的应用场景
- **[[LSM-Tree-存储引擎体系综述]]**：Fluss 的 PK Table（RocksDB + CDC log）是 LSM-Tree 在流存储领域的实现
