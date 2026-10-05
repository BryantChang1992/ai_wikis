---
type: analysis
title: 🗄️ Week 10 · 存储引擎 & 数据基础设施
blog_url: https://bryantchang1992.github.io/ai_memory_chang_ai_team/tech_research/doris/week_10_2026-07-09.html
blog_source: tech_research/doris/week_10_2026-07-09.html
blog_source_commit: f83970fa7e6ad32d626cc6ca3ba7428c90a638a5
synced_at: '2026-10-05'
tags:
- 博客同步
---

# 🗄️ Week 10 · 存储引擎 & 数据基础设施

2026-07-09 · 覆盖周期 2026-07-03 ~ 2026-07-09

## 📚 LSM-tree KV Store 综述深度扩展：Top 10 CCF-A 论文入库

基于上周入库的 ArXiv LSM-tree KV Store 综述（ArXiv 2507.09642），本周完成了综述引用的 **Top 10 CCF-A 顶会/期刊论文的追踪入库**（Commit `22f6a69`，2026-07-02 + Commit `615bba6` 精读分析重写）。

### 10 篇入库论文覆盖方向

| 论文/系统 | 方向 | 出处 |
| --- | --- | --- |
| **Bourbon** | Learned Index + LSM（机器学习索引加速查找） | SIGMOD |
| **CaaS** | LSM Compaction-as-a-Service（云原生 Compaction 分离） | VLDB |
| **ElasticBF** | 弹性 Bloom Filter（动态调整误判率-内存权衡） | ICDE |
| **Hailstorm** | 存算分离 LSM 数据库（存储-计算解耦架构） | VLDB |
| **Lethe** | 删除感知 LSM 引擎（TTL/数据生命周期管理） | SIGMOD |
| **Nova-LSM** | 分布式组件化 LSM（组件化存储架构） | FAST |
| **Pacman** | 持久内存 Compaction（PMEM 加速 Compaction） | USENIX ATC |
| **PebblesDB** | 碎片化 LSM-Tree（减少写放大） | SOSP |
| **REMIX** | 全局排序索引（SSTable 范围查询优化） | SIGMOD |
| **gLSM** | GPU 加速 Compaction（异构计算加速存储引擎） | OSDI |

### 技术洞察

- **Compaction 是 LSM 研究的高地**：10 篇中 4 篇（CaaS/Pacman/PebblesDB/gLSM）直接研究 Compaction 优化——分别从云服务化、持久内存、碎片化和 GPU 加速四个维度切入
- **异构硬件适配趋势明确**：Learned Index（Bourbon）+ GPU Compaction（gLSM）+ PMEM Compaction（Pacman）表明 LSM 引擎正在从纯 CPU/DRAM 走向异构硬件协同
- **存算分离成为架构共识**：Hailstorm + CaaS 从不同角度探索存储与计算解耦，与业界 Fluss/CockroachDB 的存算分离趋势一脉相承
- **数据生命周期管理浮现**：Lethe 提出了"删除感知"的 Compaction 策略，与 GDPR/数据合规需求直接相关

📎 相关卡片：
[综述](https://github.com/BryantChang1992/ai_wikis/blob/master/知识库/wiki/LSM-tree-KV-Survey-综述.md) ·
[Bourbon](https://github.com/BryantChang1992/ai_wikis/blob/master/知识库/wiki/Bourbon-Learned-Index-LSM.md) ·
[CaaS](https://github.com/BryantChang1992/ai_wikis/blob/master/知识库/wiki/CaaS-LSM-Compaction即服务.md) ·
[Hailstorm](https://github.com/BryantChang1992/ai_wikis/blob/master/知识库/wiki/Hailstorm-存算分离LSM数据库.md) ·
[gLSM](https://github.com/BryantChang1992/ai_wikis/blob/master/知识库/wiki/gLSM-GPU加速Compaction.md)

## 🔧 内部：Schema V2 升级与知识图谱构建

本周知识库方法论从 V1 升级到 V2（基于 Karpathy LLM Wiki v2 方法论），核心变更：

- **confidence 字段**：每张 Wiki 卡片新增 0.0-1.0 置信度评分 + confidence\_rationale
- **.entities.json**：全量 119 实体 + 485 关系知识图谱，支持结构化查询
- **Supersession 检测**：卡片内容过时自动标记，支持知识版本管理
- **增强 Lint**：URL 有效性检查、外部引用完整性、synthesis 内容容忍度

V2 升级后，知识库具备了自我评估能力——每张卡片明确标注"我知道什么、我有多确定"。
