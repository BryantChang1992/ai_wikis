---
type: lesson
title: "Fluss EKS 生产部署实践 — Fresha"
sources:
  - "sources/web/fresha/bottling-the-river-fluss-eks-精读.md"
  - "https://medium.com/fresha-data-engineering/bottling-the-river-apache-fluss-on-eks-6aa63c00d9e9"
tags:
  - "流处理"
  - "fluss"
  - "kubernetes"
  - "flink"
created: 2026-06-19
updated: 2026-06-19
status: draft
related:
  - "[[Fluss-整体架构]]"
  - "[[Fluss-KV存储-RocksDB]]"
  - "[[Fluss-Lake层与湖仓融合]]"
  - "[[Fluss-Tiering分层架构]]"
  - "[[Fluss-分布式协调]]"
  - "[[流处理弹性与重配置]]"
---

# Fluss EKS 生产部署实践 — Fresha

Fresha 团队在 EKS 上部署 Fluss 0.9.x 的生产实战。核心理念：Fluss 是"Searchable Kafka"——数据流入 tablet server 上的表，可选 tier 到对象存储（Iceberg/Paimon），Primary Key Table 嵌入 RocksDB 统一 log 与 cache。

## 架构理解

### Fluss = Searchable Kafka

Fresha 团队将 Fluss 定位为：

```
数据流入 → Tablet Server (按 bucket 分片)
             ├── 日志段 → Apache Arrow IPC 列式存储（端到端，wire → disk）
             ├── Primary Key Table → RocksDB 存储最新值 + CDC log
             └── 可选 tier → 对象存储 (Iceberg/Paimon)
```

- 每个表按 bucket 分片，分布到 tablet servers 并复制（含主备本）
- Arrow IPC 列式格式从网络传输到磁盘存储一以贯之——这一点与 [[Fluss-Arrow列式记录格式]] 直接相关
- KV Table 嵌入 RocksDB，与 [[Fluss-KV存储-RocksDB]] 描述的存储引擎一致

### 与 Flink 深度集成的价值

Fresha 团队最看重的能力：**外部化 Flink state → lookup joins / delta joins 几乎无状态**。这与 [[Fluss-客户端与计算集成]] 的设计意图吻合——Fluss 不仅存储数据，还替代了 Flink 的 state backend。

## EKS 部署踩坑与修复

| 问题 | 根因 | 修复 | 状态 |
|------|------|------|------|
| **IRSA 不支持** | Fluss 0.9 无 K8s IRSA 集成 | PR #2142 | ✅ v0.9 |
| **S3 delegation token** | 硬编码 static credentials，IRSA pod 认证失败 | PR #3066 | ✅ v0.9.1 |
| **Secrets 管理** | 无 K8s secret / IRSA 路径 | PR #3172 | ✅ v0.9.1 |
| **Pod Anti-Affinity** | 无默认反亲和配置，所有 tablet server 可能调度到同节点 | PR #3153 | ✅ v0.9.1 |

这些修复全部由 Fresha 团队贡献 upstream，说明 **Fluss 0.9.x 在 Kubernetes 上的开箱即用度还不够**，需要运维团队有一定 K8s 和 AWS 经验才能顺利部署。

## Flink-Fluss Connector 依赖问题

实际使用中缺 JAR 导致 S3 读写失败：
1. `fluss-fs-s3-0.9.0-incubating.jar` — S3 文件系统实现
2. `commons-text-1.11.0.jar` / `commons-lang3-3.14.0.jar` — Flink 基础库

临时绕过：values.yaml 中设 static credentials。生产建议：等 IRSA 修复生效后切回 IRSA。

## 与 [[Fluss-Tiering分层架构]] 的关系

Fresha 的部署直接使用了 Fluss 的 Lake Tiering 能力——数据可选 tier 到对象存储。这是 [[Fluss-Lake层与湖仓融合]] 在生产环境的实际验证。

## 与 [[流处理弹性与重配置]] 的关联

Pod Anti-Affinity 缺失 → 所有 tablet server 可能同节点 → 单点故障风险。修复后配合 Kubernetes 的弹性调度，Fluss 可以做到 tablet server 跨节点高可用——这是 [[流处理弹性与重配置]] 在 Fluss 上的具体体现。

## 生产启示

1. **Fluss 0.9.x 的 K8s 就绪度可以通过贡献 upstream 快速补足**——Fresha 团队在几周内修复了 4 个 blocker
2. **Fluss + Flink 的 state 外置是杀手级能力**——lookup join 零状态、跨作业共享表
3. **Arrow IPC 列式端到端**是 Fluss 的性能基础——从 wire 到 disk 零序列化开销
4. **Lake Tiering 在生产中已经可用**——但依赖 Iceberg/Paimon catalog 配置正确
