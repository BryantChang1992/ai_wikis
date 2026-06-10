# 存储/数据库顶会趋势洞察 — Week 04 (2026-06-11)

> 来源：SIGMOD 2026 · FAST 2026 · VLDB · CIDR · 聚焦存储/数据库方向

→ [查看完整报告](https://bryantchang1992.github.io/ai_memory_chang_ai_team/tech_research/top_conferences/week_04_2026-06-11.html)

---

## 🏛️ SIGMOD 2026 (Bengaluru, 6月)

### LLM 推理服务系统
- **Efficient LLM Serving for Agentic Workflows** — NUS：Agent工作流的LLM推理优化
- **AlignedServe** — 中山大学：前缀感知批量调度提升推理吞吐
- **CoDec** — 南京大学：前缀共享解码内核
- **DFLOP** — Yonsei/MS/SKT：多模态LLM训练流水线优化

### 存储引擎与索引
- **Reducing Tail Latency in Storage-Disaggregated DB** — Purdue：存储分离尾延迟优化
- **ART That Lasts** — Waterloo：持久化多版本自适应基数树
- **Bw-Graph** — 清华：拓扑感知图存储系统
- **Dynamic Flat Filter** — 苏州大学：可扩展指纹过滤器

### 向量与图搜索
- **CMANNS** — 南京大学：GPU加速+计算存储分离的ANNS索引
- **Efficient Vector Similarity Search** — 南科大/华为：百亿级向量搜索优化
- **Filter-Agnostic Vector Search on PostgreSQL** — Brown/Google/ETH：PG向量搜索实证
- **cuRPQ** — KAIST：GPU正则路径查询

### LLM × DB 交叉
- **Automated Test Oracle Discovery** — Berkeley/NUS/清华：LLM发现DB测试预言
- **Database-Native Function Code Synthesis** — 交大/清华/NUS/蚂蚁：LLM合成DB函数
- **DBugScribe** — NUS/阿里：LLM自动复现数据库Bug
- **AgenticScholar** — UQ/清华：Agent驱动的学术数据管理

## 💾 FAST 2026 (Santa Clara, 2月)

已闭幕，论文通过 USENIX 开放获取。方向：CXL内存池化、计算存储融合、去中心化存储、ML辅助存储栈。

## 📈 五大趋势

1. **LLM推理成为DB新核心负载** — 数据库社区正式拥抱LLM推理服务
2. **存储分离架构走向成熟** — 尾延迟优化等后分离时代工程问题成热点
3. **向量/图数据基础设施深度融合** — 多模态数据库时代加速
4. **LLM for DB从工具走向平台** — 重塑测试、开发、运维全流程
5. **持久化索引迎接新硬件** — NVM/CXL/PMem原生设计
