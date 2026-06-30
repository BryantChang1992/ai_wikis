---
category: 项目文档
tags:
  - fluss
  - kafka
  - 源码分析
  - 流存储
created: 2026-06-10
updated: 2026-06-10
status: draft
---

# Fluss 源码分析

> [!abstract] 项目概述
> 对 Apache Fluss (Incubating) 最新 trunk 进行完整源码分析，梳理核心模块关系，并与 Apache Kafka 2.7.2 进行架构对照。分析报告优先内部审阅，通过后提交 GitHub Pages。

## 目录

- [[Fluss源码分析/01-整体架构对比|01 - 整体架构对比（Fluss vs Kafka）]]
- [[Fluss源码分析/02-存储引擎模块|02 - 存储引擎：Log/KV/Remote Storage]]
- [[Fluss源码分析/03-分布式协调|03 - 分布式协调：Coordinator / ZK / Metadata]]
- [[Fluss源码分析/04-数据面-网络与RPC|04 - 数据面：网络与 RPC]]
- [[Fluss源码分析/05-客户端与计算集成|05 - 客户端与计算引擎集成（Flink/Spark）]]
- [[Fluss源码分析/05b-客户端写入流程深度分析|05b - 客户端写入流程深度分析]]
- [[Fluss源码分析/06-Lake层与湖仓融合|06 - Lake 层与湖仓融合]]
- [[Fluss源码分析/07-模块对应关系总表|07 - 模块对应关系总表（Fluss ↔ Kafka）]]

## 分析范围

| 维度 | Fluss | Kafka 2.7.2 |
|------|-------|-------------|
| 版本 | trunk (latest) | 2.7.2 (tagged @ 37a1cc3) |
| 语言 | Java | Scala/Java |
| 构建 | Maven (mvnw) | Gradle |
| 核心模块 | 12 Maven modules (1747 source files) | 10+ Gradle sub-projects |

## 进度

| 模块 | 状态 | 产出 |
|------|------|------|
| 01 - 整体架构对比 | ✅ 完成 | [[01-整体架构对比]] |
| 02 - 存储引擎模块 | ✅ 完成 | [[02-存储引擎模块]] |
| 03 - 分布式协调 | ✅ 完成 | [[03-分布式协调]] |
| 04 - 数据面 & RPC | ✅ 完成 | [[04-数据面-网络与RPC]] |
| 05 - 客户端与计算集成 | ✅ 完成 | [[05-客户端与计算集成]] |
| 05b - 客户端写入流程深度分析 | ✅ 完成 | [[05b-客户端写入流程深度分析]] |
| 06 - Lake 层与湖仓融合 | ✅ 完成 | [[06-Lake层与湖仓融合]] |
| 07 - 模块对应关系总表 | ✅ 完成 | [[07-模块对应关系总表]] |

## 关键发现

1. **Fluss 约 30% 代码复用 Kafka**（Log Segment 管理 + Replica 复制框架），70% 自研
2. **最大差异化**：KV 存储（RocksDB）、Arrow 列式记录、Lakehouse 集成
3. **Kafka 兼容层处于骨架阶段**：协议栈就绪，绝大部分 API handler 为空方法
4. **存算分离**：CoordinatorServer 独立进程 vs Kafka Controller 内嵌 Broker
5. **Lake Tiering**：原生 Flink 作业将实时数据持续写入 Iceberg/Paimon

## 更新日志

- 2026-06-10：全部 7 个模块分析完成，提交内部审阅
- 2026-06-30：新增 05b 客户端写入流程深度分析
