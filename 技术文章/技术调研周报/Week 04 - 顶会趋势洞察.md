# 存储/数据库顶会趋势洞察 — Week 04 (2026-06-11)

> 来源：SIGMOD 2026 · FAST 2026 · CIDR 2026 · 四主题深度调研

→ [查看完整报告](https://bryantchang1992.github.io/ai_memory_chang_ai_team/tech_research/top_conferences/week_04_2026-06-11.html)

---

## 调研框架

| 主题 | 论文数 | 亮点 |
|------|--------|------|
| 🗄️ 存储引擎 & 索引 | 12篇 | LSM-Raft, ART持久化, PartitionKV, RASK |
| 🤝 分布式共识协议 | 6篇 | CockroachDB Lease, LSM-Raft协同, Rosé |
| 🏭 工业系统 | 12篇 | Aurora Limitless, ByteHouse, TDSQL, ACOS |
| 🤖 AI Infra | 8篇 | KV Cache×3, ANNS×3, GPU Ckpt×2 |

---

## 一、存储引擎 & 索引技术（12篇）

### SIGMOD 2026
- **ART That Lasts** — Waterloo：持久化多版本自适应基数树
- **Concurrent Path-Copying Update** — CUHK/HKUST：无锁并发索引
- **Bw-Graph** — 清华：拓扑感知树 + 分页 CSR 图存储
- **Dynamic Flat Filter** — 苏州大学：LSM-Tree 过滤器统一框架
- **PartitionKV** — 西电/NWPU：NVM 自适应分区 LSM-Tree
- **Efficient Vector Index Layout** — 南科大/华为：百亿级向量搜索

### FAST 2026
- **DMTree** — USTC：分离式内存的树索引优化
- **RASK** — SJTU："Range as Key" 云块存储索引
- **分布式 LSM-Tree 调度** — USTC/CUHK：compaction 全局调度
- **DOGI** — 日志结构数据放置

### CIDR 2026
- **Raster is Faster** — IISc：光栅化 GPU 索引
- **xNVMe** — ITU：统一 NVMe 硬件抽象层

---

## 二、分布式共识协议（6篇）

- **LSM-Raft** 🔥 — 清华/Timecho：Raft 与 LSM-Tree 深度协同，感知 compaction 状态调节日志同步
- **CockroachDB Leader Lease** — Cockroach Labs：数十万 Raft 组 Lease 管理
- **Epoch-based OCC** — U Toronto：Geo-Distributed 数据库乐观并发控制
- **Tail Latency in Storage-Disaggregated DB** — Purdue：分离式架构尾延迟优化
- **Rosé** — Columbia/Microsoft：per-partition 灵活复制协议
- **Event Horizon** — TU Delft：非对称依赖降低跨地域延迟

---

## 三、工业系统（12篇）

- **Aurora PostgreSQL Limitless** — AWS：PG 兼容的多写分布式架构
- **ByteHouse** — ByteDance：多模态实时数仓
- **TDSQL-Boundless** — 腾讯：异构多表分布式 DB
- **CoddSpeed** — Microsoft：FPGA 加速查询引擎（50+ 作者）
- **TokaDB** — HUST/ByteDance：推荐系统训推统一存储
- **ByteGraph-Dione** — ByteDance：自适应双格式图引擎
- **LindormVector** — 阿里云：多模 NoSQL 向量引擎
- **Azure SQL Hyperscale 存储层** — Microsoft
- **ACOS** — Apple：EB 级地理分布式对象存储
- **Discard-Based GC** — ByteDance：日志结构存储零拷贝 GC
- **PolarStore** — 云原生 DB 高性能压缩
- **Salesforce 多租户 OLTP** — Salesforce

---

## 四、AI Infra（8篇）

### LLM 推理 · KV Cache
- **CacheSlide** (FAST '26) — SJTU：跨位置感知 KV Cache 复用
- **Bidaw** (FAST '26) — 清华：双向计算-存储感知 KV Cache
- **SolidAttention** (FAST '26) — SJTU：SSD 低延迟注意力

### 向量搜索
- **CMANNS** (SIGMOD '26) — 南大/清华：GPU+分离式内存 ANNS
- **Filter-Agnostic Vector Search on PG** (SIGMOD) — Brown/Google/ETH
- **FAVOR** (SIGMOD '26) — HUST/浙大：过滤无关 ANNS

### AI 训练
- **GPU Checkpoint/Restore** (FAST '26) — 清华：快速轻量 GPU Ckpt
- **AdaCheck** (FAST '26) — 自适应 LLM 训练 Checkpoint
- **Fast Cloud Storage for AI** (FAST '26) — SJTU：分组 I/O API

### Vision
- **Agent-First 数据系统** (CIDR '26) — Berkeley：AI Agent 时代数据库重构

---

## 📈 六大趋势

1. **共识协议与存储引擎深度协同** — LSM-Raft 标志拐点，共识不再黑盒
2. **持久化索引走向工程落地** — ART 多版本化、分离式内存索引
3. **工业数据库论文爆发** — 系统架构深度融合新硬件/新负载
4. **AI Infra 已成 P0 方向** — 存储顶会 AI 论文密度同比+3x
5. **"One-size-fits-one"成潜在线** — 复制/事务协议转向场景定制
6. **向量搜索从独立品类走向融合** — 回归数据库原生能力
