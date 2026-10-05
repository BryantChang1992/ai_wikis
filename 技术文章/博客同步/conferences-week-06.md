---
title: 存储/数据库/AI Infra 顶会趋势 — Week 06
blog_url: https://bryantchang1992.github.io/ai_memory_chang_ai_team/posts/tech-research/week-06/conferences/
blog_source: _posts/2026-06-18-conferences-week-06.md
blog_source_commit: f83970fa7e6ad32d626cc6ca3ba7428c90a638a5
blog_body_sha256: 9a65fb77033abe0e5c2b380422a89accf36d9898b1bd265b7a89551dae49bcb7
synced_at: '2026-10-05'
type: survey
created: '2026-06-18'
tags:
- SIGMOD
- VLDB
- 顶会
- ArXiv
- VectorDB
- AI Infra
issue: 6
issue_date: '2026-06-18'
---

> 采集窗口：2026-06-11 ~ 2026-06-18 · 来源：ArXiv + 顶会官网
>
> ⚠️ 本周 SearXNG 无法响应，改为 ArXiv 直接检索。SIGMOD 2026 已闭幕（5/31-6/5, Bengaluru），论文列表尚未公开索引；VLDB 2026 将于 8/31-9/4 在 Boston 举行。

---

## 📊 本周概览

| 会议 | 状态 | 本周动态 |
|------|------|----------|
| **SIGMOD 2026** | 已闭幕 (5/31-6/5, Bengaluru) | 论文列表待后续跟踪 |
| **VLDB 2026** | 筹办中 (8/31-9/4, Boston) | PVLDB 滚动卷进行中 |
| **FAST 2026** | 投稿期 | 暂无公开论文列表 |
| **OSDI/SOSP 2026** | 待公布 | 暂无 |
| **CIDR 2026** | 待公布 | 暂无 |

---

## 🔬 本周论文

### 1. Ghost Vectors: Soft-Deleted Embeddings Remain Reconstructible in HNSW Vector Databases

- **来源**：ArXiv (2026-06-16)
- **作者**：Chandranil Chakraborttii, Jackeline García Alvarado, Sitora Abdulofizova, Shivanshu Dwivedi
- **链接**：[ArXiv](https://arxiv.org/search/?query=Ghost+Vectors+Soft-Deleted+Embeddings+HNSW)
- **标签**：`#VectorDB` `#Security` `#Privacy` `#HNSW`

研究 RAG pipeline 中 HNSW 向量数据库在用户请求数据删除后，"软删除"的 embedding 仍然可被重建的安全隐患。揭露了当前向量数据库在数据删除合规性方面的系统性缺陷，对 GDPR/隐私合规场景有重要影响。

---

### 2. From Detection to Recovery: Operational Analysis on LLM Pre-training with 504 GPUs

- **来源**：ArXiv (2026-06-15, v1: 2026-05-10)
- **作者**：Daemyung Kang, Eunjin Hwang, Hanjeong Lee, HyeokJin Kim, Hyunhoi Koo 等 (14 人)
- **链接**：[ArXiv](https://arxiv.org/search/?query=Detection+Recovery+LLM+Pre-training+504+GPUs)
- **标签**：`#AIInfra` `#LLMTraining` `#GPUCluster` `#FaultTolerance`

大规模 AI 训练本质上是分布式系统工程问题。本文基于 504 GPU 集群上的 LLM 预训练实战，系统分析了从故障检测到自动恢复的完整运维链路：包括 GPU 故障模式分类、checkpoint 策略优化、训练中断恢复时间 (MTTR) 分析与优化，为生产级大模型训练基础设施提供了宝贵的运维经验。

---

### 3. RollArt: Disaggregated Multi-Task Agentic RL Training at Scale

- **来源**：ArXiv (2026-06-14, v1: 2025-12-27)
- **作者**：Wei Gao, Yuheng Zhao, Tianyuan Wu, Shaopan Xiong 等 (Alibaba)
- **链接**：[ArXiv](https://arxiv.org/search/?query=RollArt+Disaggregated+Multi-Task+Agentic+RL+Training)
- **标签**：`#AIInfra` `#RLTraining` `#DisaggregatedArch` `#AgenticAI`

Agentic RL 训练需要同时管理多个 agent、environment 和 model。RollArt 提出解耦式架构将 RL 训练的推理、环境交互、模型更新分离到不同资源池，实现多任务弹性调度。在大规模集群上展示了显著的资源利用率和训练吞吐提升。

---

### 4. M-CTX: Exact and Scalable Spatial Context Retrieval for Trajectory Analytics

- **来源**：ArXiv (2026-06-13)
- **作者**：Kun Ma, Qilong Han, Chengjing Song, Jingzheng Yao, Xiao Han, Yuee Zhou, Changmao Wu
- **链接**：[ArXiv](https://arxiv.org/search/?query=M-CTX+spatial+context+retrieval+trajectory)
- **标签**：`#SpatialDB` `#TrajectoryAnalytics` `#Systems`

空间上下文检索是轨迹预测的关键步骤，但在大规模 AIS 海事数据中（5.48M anchor 需约 17 CPU-days）已成为系统瓶颈。M-CTX 提出通过符号距离场 (SDF) 索引优化的精确可扩展空间上下文检索方法，大幅降低检索延迟。

---

### 5. Private Information Retrieval for Large-Scale DNA-Based Data Storage

- **来源**：ArXiv (2026-06-12)
- **作者**：Gökberk Erdoğan, Daniella Bar-Lev, Rawad Bitar, Antonia Wachter-Zeh, Zohar Yakhini
- **链接**：[ArXiv](https://arxiv.org/search/?query=Private+Information+Retrieval+DNA+Data+Storage)
- **标签**：`#NovelStorage` `#DNAStorage` `#PIR` `#Privacy`

首次将私有信息检索 (PIR) 理论应用于合成 DNA 数据存储场景。DNA 存储因其超高密度和长期稳定性成为新型存储介质的前沿方向，但随机访问和隐私保护是核心挑战。该工作提出适配 DNA 存储特性的 PIR 方案，为下一代存储架构的安全访问机制奠基。

---

## 📡 近期高相关论文（窗口外，值得关注）

### 6. A Multimodal Machine Learning Framework for Enterprise Database Workload-Aware Root Cause Analysis

- **来源**：ArXiv (2026-06-02)
- **作者**：Ruchi Pakhle, Siddhant Pawar
- **标签**：`#DatabaseOps` `#RootCauseAnalysis` `#ML`

---

### 7. Architectural Evolution and Selection Framework for Database Systems in AI-Ready Data Platforms

- **来源**：ArXiv (2026-06-06)
- **作者**：Mohit Srivastava
- **标签**：`#DatabaseArchitecture` `#AIPlatform` `#Survey`

---

### 8. AIM: A Practical Approach to Automated Index Management for SQL Databases

- **来源**：ArXiv (2026-05-29)
- **作者**：Ritwik Yadav, Satyanarayana R. Valluri, Mohamed Zaït (Oracle)
- **标签**：`#IndexManagement` `#SQL` `#AutoTuning`

---

### 9. Is Agent Memory a Database? Rethinking Data Foundations for Long-Term AI Agent Memory

- **来源**：ArXiv (2026-05-25)
- **作者**：Abdelghny Orogat, Essam Mansour
- **标签**：`#AgentMemory` `#DatabaseTheory` `#AISystems`

---

### 10. High-speed Networking for Giga-Scale AI Factories (NVIDIA Spectrum-X)

- **来源**：ArXiv (2026-05-20)
- **作者**：Sajy Khashab, Albert Gran Alcoz 等 (NVIDIA)
- **标签**：`#AIInfra` `#Networking` `#GPUCluster`

---

## 🏛️ 顶会背景更新

### SIGMOD 2026

- **时间/地点**：2026-05-31 ~ 06-05，Bengaluru, India（已闭幕）
- **重要变化**：ACM 自 2026-01-01 起全面转为 Open Access，APC 临时补贴价 $250-$350
- **待办**：论文列表需后续从 ACM Digital Library 或 dblp 获取

### VLDB 2026

- **时间/地点**：2026-08-31 ~ 09-04，Boston, MA, USA
- **状态**：筹办中，PVLDB 滚动卷持续出版
- **主题**：data management, scalable data science, novel database architectures, ML+DB

---

## 🔍 趋势观察

1. **向量数据库安全与隐私**成为新兴热点——Ghost Vectors 揭露了软删除 embedding 可恢复的安全隐患
2. **AI Infra 运维实战**报告增多——从 504 GPU 故障恢复到 Spectrum-X 网络架构，工程化论文增加
3. **Agent 与数据库的边界模糊化**——"Is Agent Memory a Database?" 标志着长期记忆存储成为数据库领域新课题
4. **新型存储介质研究持续**——DNA 存储 + PIR 的结合展示了基础理论向新型介质延伸
5. **自动化运维 (AIOps for DB)**——多模态根因分析、自动索引管理成为持续热点
