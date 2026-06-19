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
related: []
---

# Fluss EKS 生产部署实践 — Fresha

## Fluss 本质

"Searchable Kafka"：
- 数据流入 tablet server 上的表，可选 tier 到 Iceberg/Paimon
- 表按 bucket 分片，分布到 tablet servers 并复制
- 日志段以 **Apache Arrow IPC 列式存储**（端到端，wire → disk）
- PK Table = RocksDB（最新值）+ CDC log → **统一 log 和 cache**

## EKS 部署修复（已贡献 upstream）

| 问题 | PR | 版本 |
|------|-----|------|
| IRSA（IAM Roles for Service Accounts）不支持 | #2142 | v0.9 |
| S3 delegation token 硬编码 static creds | #3066 | v0.9.1 |
| Secrets 管理无 K8s secret 路径 | #3172 | v0.9.1 |
| 无 Pod Anti-Affinity | #3153 | v0.9.1 |

## Flink Connector 踩坑

1. 缺少 `fluss-fs-s3-0.9.0-incubating.jar` → S3 读写失败
2. 缺少 `commons-text-1.11.0.jar` / `commons-lang3-3.14.0.jar`
3. S3 delegation token 临时绕过：set static creds in values.yaml

## 核心价值

Flink state 外置到 Fluss → **lookup join 几乎无状态、跨作业共享同一表**、更小 checkpoint、更快恢复。

## 关键 Insight

> v0.9.x 生产部署门槛仍较高，但团队通过贡献 upstream 修复了关键 gap。投入的回报：从"每个作业自己重建 state"到"共享存储层"，运维成本质变。
