---
type: analysis
title: ⏱ Doris / 分析型数据库 — Week 08 (2026-06-25)
blog_url: https://bryantchang1992.github.io/ai_memory_chang_ai_team/tech_research/doris/week_08_2026-06-25.html
blog_source: tech_research/doris/week_08_2026-06-25.html
blog_source_commit: f83970fa7e6ad32d626cc6ca3ba7428c90a638a5
synced_at: '2026-10-05'
tags:
- 博客同步
---

# ⏱ Doris / 分析型数据库 — Week 08 (2026-06-25)

覆盖周期：2026-06-19 ~ 2026-06-25（部分内容跨月，均为 2026 年重要发布）

## 1. Apache Doris 4.1：AI 统一存储与检索

🔥 2026-04-24 发布。Doris 从 OLAP 引擎向 AI 基础设施转型的标志性版本。

### 1.1 向量搜索全面升级

| 能力 | 4.0 基线 | 4.1 增强 |
| --- | --- | --- |
| 向量索引类型 | HNSW | HNSW + **IVF + IVF\_ON\_DISK** |
| 向量规模 | 千万级 | 十亿 ~ 万亿级（磁盘索引） |
| 向量量化 | 基础 | INT8 / INT4 / 乘积量化 (PQ) |
| 查询性能 | 基线 | **4x 提升**（Ann Index Only Scan） |

#### IVF\_ON\_DISK 技术细节

参照 Microsoft SPANN 论文方案，结合内存缓存 + 本地文件系统缓存，实现低成本高性能向量剪枝。索引构建开销远低于 DiskANN。

#### 性能基准

16-core CPU + 64GB 内存，100 万向量：~900 QPS @ 97% recall。VectorDBBench 数据显示 Doris 向量索引构建速度快于 Milvus、Qdrant、pgvector。

### 1.2 search() 函数：SQL 原生全文搜索

- **BM25 相关性评分**：内置 scoring + 存储层 TopN 优化
- **ES 兼容语法**：TERM / PHRASE / WILDCARD / REGEXP / PREFIX / NOT / NESTED 全部支持
- **NESTED 搜索**：结合 VARIANT 类型，直接搜索嵌套 JSON 数组内部
- **search + 聚合**：一个查询完成搜索过滤 + 统计分析

### 1.3 长上下文 AI 存储

原生支持单行 **100MB JSON 文档**。覆盖场景：

- 多轮对话记录
- Agent 执行轨迹 & tool call 日志
- 长文档文本、音频/视频转录
- RAG 上下文

不需要外部对象存储，写入后即可用 SQL 筛选、条件查询、聚合和 JOIN。

### 1.4 OLAP 性能

| Benchmark | vs 4.0 提升 |
| --- | --- |
| TPC-H | +22.6% |
| TPC-DS | +19.1% |
| SSB | +14.3% |
| ClickBench (冷查询) | 🥇 排名第一 |

### 1.5 湖仓集成

- 完整 Apache Iceberg V2/V3 读写支持
- Apache Paimon DDL 通过 SQL 管理
- Parquet Page Cache +20% 性能

### 1.6 Adoption

存算分离模式已部署 **2000+ 家企业**。

来源：[velodb.io — Doris 4.1 发布博文](https://www.velodb.io/blog/apache-doris-4-1-unified-storage-and-retrieval-for-ai-and-search), [github.com/apache/doris #62406 — 4.1.0 RN](https://github.com/apache/doris/issues/62406)

## 2. Doris 2026 Roadmap

GitHub Issue #60036 明确的 2026 路线图：

- **SQL 能力补全**：UNNEST、递归 CTE、ASOF JOIN
- **AI & Hybrid Search 深耕**：向量搜索扩展至十亿级、BM25 全文搜索成熟化
- **查询性能**：更智能的执行路径选择、跨网络数据传输优化
- **存储效率**：spill-to-disk（Hash Join / Aggregation / Sort）、数据湖集成深化

来源：[github.com/apache/doris #60036 — Roadmap 2026](https://github.com/apache/doris/issues/60036)

## 3. 分布式数据库

### CockroachDB Leader Leases (SIGMOD 2026)

解决分布式 SQL 数据库的 lease 管理扩展瓶颈。核心创新：

- **Liveness Fabric**：去中心化节点间健康检查，替代 per-Range 检查
- **Leader Fortification**：Raft 协议修改，确保 leaseholder 始终是 Raft leader
- **Leader Leases**：合并 leader + leaseholder 角色

CPU 降低 **85%**，TLA+ 形式化验证。论文在 SIGMOD 2026 Industry 3 Session（6/2 3:30 PM）发表。

来源：[cockroachlabs.com/blog — Leader Leases](https://www.cockroachlabs.com/blog/distributed-database-leader-leases/), [emptysqua.re — A. Jesse Jiryu Davis 技术解读](https://emptysqua.re/blog/review-scalable-leader-leases-for-multi-consensus-groups-in-cockroachdb/)

### CXL 与数据库

- EDBT 2026 论文：Dynamic Memory Allocation of CXL Memory Pools in Enterprise Databases
- VLDB 论文：CXL 内存对 IMDBMS 性能影响 < 8%（OLAP 场景，PCIe Gen5）
- 趋势：CXL 3.0 产品化在即，有望从 scale-out 回归 scale-up 弹性内存池

来源：[EDBT 2026 paper](https://openproceedings.org/2026/conf/edbt/paper-280.pdf), [清华 CXL ICDE 论文](https://dbgroup.cs.tsinghua.edu.cn/ligl//papers/CXL_ICDE.pdf)

## 4. 存储引擎

### PASV 入选 ACM Transactions on Storage

LSM-tree 数据库的 double-logging 解决方案 PASV 于 2026 年 5 月入选 ACM TOS（DOI: 10.1145/3813114）。

- 核心思想：完全移除 WAL，利用 SST 文件构建过程本身作为持久化手段
- ACM TOS 版本扩展为 "Passive and Hybrid Data Persistence Scheme"
- 论文历程：Submitted 2025-09-17 → Revised 2026-01-28 → Accepted 2026-04-16 → Published 2026-05-05

来源：[ACM Digital Library — doi:10.1145/3813114](https://dl.acm.org/doi/10.1145/3813114)

### SIGMOD 2026 存储相关

- LSM KV Store for Multi-Tenant Serverless Cloud Databases
- Tree Search using GPUs
