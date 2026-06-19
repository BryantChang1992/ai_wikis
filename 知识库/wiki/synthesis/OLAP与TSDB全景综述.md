---
type: synthesis
title: "OLAP 与时序数据库全景综述"
sources:
  - "[[Doris-深度调研]]"
  - "[[Doris-数据模型]]"
  - "[[Doris-Segment-v2-存储格式]]"
  - "[[Doris-Compaction-策略]]"
  - "[[Doris-MPP-向量化查询引擎]]"
  - "[[Doris-Nereids-CBO-优化器]]"
  - "[[Doris-架构演进]]"
  - "[[Doris-元数据与一致性复制]]"
  - "[[InfluxDB深度调研]]"
  - "[[InfluxDB-数据模型]]"
  - "[[InfluxDB-TSM存储引擎]]"
  - "[[InfluxDB-3-列存引擎]]"
  - "[[InfluxDB-写入与查询路径]]"
  - "[[InfluxDB-指标设计与基数管理]]"
  - "[[InfluxDB-多副本与高可用]]"
  - "[[InfluxDB-Catalog元数据]]"
tags:
  - OLAP
  - 时序数据库
  - 数据分析
  - 综述
created: 2026-06-14
updated: 2026-06-14
status: draft
related:
  - "[[LSM-Tree-存储引擎体系综述]]"
  - "[[事务模型深度调研]]"
---

# OLAP 与时序数据库全景综述

> 本页横向对比两大分析型数据库赛道：OLAP（以 Doris 为代表）与时序数据库（以 InfluxDB 为代表）。


![[diagram/olap-tsdb-comparison.svg]]

## 1. 领域定义

| 赛道 | 代表系统 | 核心场景 | 数据特征 |
|------|---------|---------|---------|
| OLAP（在线分析处理） | Doris, ClickHouse, StarRocks | 多维聚合查询、BI 报表、实时分析 | 大批量写入、列式存储、宽表 |
| 时序数据库（TSDB） | InfluxDB, TimescaleDB, TDengine | 监控、IoT、金融行情 | 追加写入、时间有序、高压缩率 |

## 2. 概念关系图


## 3. 存储引擎对比

| 维度 | Doris | InfluxDB |
|------|-------|----------|
| 引擎类型 | Segment v2（自研列式） | TSM（时序优化 LSM）→ 3.0 列存 |
| 索引设计 | ZoneMap / BloomFilter / Bitmap / Inverted | TSI（倒排索引，Tag 维度） |
| Compaction | Cumulative / Base / Quick / Vertical | 自动合并 + 碎片清理 |
| 编码压缩 | RLE / BitPacking / Dict / ZSTD | 时序专用（Delta / Gorilla / Simple8b） |
| 数据模型 | 宽表 + Aggregate Key | 窄表 + Tag/Field/Timestamp |
| 与 LSM-Tree 关系 | 不直接基于 LSM | TSM 是 LSM 变体；3.0 列存脱离 LSM |

## 4. 核心差异根因

| 差异 | Doris 选择 | InfluxDB 选择 | 原因 |
|------|-----------|---------------|------|
| 查询模式 | 全表扫描聚合 | 时间范围 + Tag 过滤 | 场景不同：BI vs 监控 |
| 写入模式 | 批量导入 / Stream Load | 逐点写入 / 批量写入 | 定时报表 vs 实时采集 |
| 一致性需求 | 强一致（2PC + WAL） | 最终一致 / 可调 | 财务数据 vs 可容忍丢点 |
| 扩展方式 | 水平分片（Tablet） + 计算节点 Scale-out | 分片/副本 + Influx 3.0 存算分离 | 各自按场景优化 |

## 5. 架构趋同趋势

两大赛道在以下方向上正在融合：

1. **存算分离**：Doris 3.0 和 InfluxDB 3.0 都走向了存算分离架构
2. **列式存储**：InfluxDB 3.0 从 TSM（行层 + 列层混合）转向纯列式（Parquet + Arrow），向 OLAP 靠拢
3. **Lakehouse 集成**：Doris 支持 Iceberg/Hudi 联邦查询；InfluxDB 3.0 原生支持 Parquet 在对象存储
4. **向量化执行**：两个系统都在引入 SIMD 向量化（Doris 已成熟，Influx 3.0 通过 DataFusion/Arrow 获得）

## 6. 跨页连接洞察

1. **[[Doris-Compaction-策略|Doris Compaction]] 与 [[LSM-Tree-合并优化|LSM-Tree 合并优化]]**：虽然设计理念不同（Doris 是 segment 级合并，LSM 是 level 级归并），但核心矛盾相同——如何在低峰期整理数据而不影响写入
2. **[[InfluxDB-指标设计与基数管理|基数管理]]** 是 TSDB 独有的挑战，OLAP 不存在这个问题的根本原因是数据模型设计哲学不同
3. **元数据管理**：Doris 从 BDB-JE 演进到自研 Meta Service，InfluxDB 从 BoltDB 演进到 Catalog，都经历了一场"从嵌入式 KV 到独立元数据服务"的架构变革

## 7. 对外桥接

- [[LSM-Tree-存储引擎体系综述]]：两大引擎的共同基石
- [[事务模型深度调研]]：Doris 的 2PC 导入事务、InfluxDB 的副本一致性都直接依赖分布式事务理论
- [[存储计算分离数据库的-Tail-Latency]]：二者都在往存算分离方向演进

## 8. 待探索方向

- [ ] ClickHouse / StarRocks 与 Doris 的竞品对比
- [ ] TimescaleDB / TDengine 与 InfluxDB 的时序竞品对比
- [ ] Lakehouse 架构（Iceberg/Hudi/Paimon）是否会同时侵蚀 OLAP 和 TSDB 的市场
- [ ] AI/ML 在查询优化中的应用（Learned Index、Learned Cost Model）
