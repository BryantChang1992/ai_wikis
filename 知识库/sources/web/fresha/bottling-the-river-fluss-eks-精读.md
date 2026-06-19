# Bottling the River: Apache Fluss on EKS

- **URL**: https://medium.com/fresha-data-engineering/bottling-the-river-apache-fluss-on-eks-6aa63c00d9e9
- **来源**: Fresha Data Engineering Blog (Medium), Nicoleta Lazar
- **日期**: 2026-04-30

## 核心内容

Fresha 团队在 EKS 生产集群中部署和集成 Apache Fluss 的实战经验。

### Fluss 本质理解

- "Searchable Kafka"：数据流入 tablet server 上的表，可选 tier 到对象存储（Iceberg/Paimon）
- 每个表按 bucket 分片，分布到 tablet servers 并复制
- 日志段以 Apache Arrow IPC 列式存储（端到端，从 wire 到 disk）
- Primary Key (KV) Tables：嵌入 RocksDB 实例存储最新值 + 输出 CDC log → 统一 log 和 cache
- 与 Flink 深度集成：外部化 Flink state → lookup joins / delta joins 几乎无状态

### EKS 部署遇到的限制与修复（已贡献 upstream）

| 问题 | 状态 |
|------|------|
| IRSA (IAM Roles for Service Accounts) 不支持 | v0.9 已修复 (PR #2142) |
| S3 delegation token 硬编码 static credentials → IRSA pod 失败 | 已修复 (#3066)，v0.9.1 落地 |
| Secrets 管理无 K8s secret/IRSA 路径 | 已修复 (#3172)，v0.9.1 落地 |
| 无 Pod Anti-Affinity → 所有 tablet server 可调度到同节点 | 已修复 (#3153)，v0.9.1 落地 |

### Flink-Fluss Connector 踩坑

1. 缺少 `fluss-fs-s3-0.9.0-incubating.jar` → S3 读写失败
2. 缺少 `commons-text-1.11.0.jar` / `commons-lang3-3.14.0.jar`
3. S3 delegation token 问题 → set static creds in values.yaml 临时绕过

## 关键 Insight

Fluss 在 EKS 上的生产部署门槛仍然较高（0.9.x 版本），但团队通过贡献 upstream 修复了关键 gap。Fluss + Flink 集成带来的状态外置收益（lookup join 零状态、跨作业共享表）值得投入。
