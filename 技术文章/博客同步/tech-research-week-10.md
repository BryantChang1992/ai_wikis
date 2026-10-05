---
title: 技术调研周报 — Week 10 (2026-07-09)
blog_url: https://bryantchang1992.github.io/ai_memory_chang_ai_team/posts/tech-research/week-10/
blog_source: _posts/2026-07-09-tech-research-week-10.md
blog_source_commit: f83970fa7e6ad32d626cc6ca3ba7428c90a638a5
blog_body_sha256: f64d11b867345d78b7ab0c447c8a22a92200800b6e22b1ef578ecffadcbd9c2e
synced_at: '2026-10-05'
type: survey
created: '2026-07-09'
tags:
- AI Infra
- Agent
- GPT-5.5
- Claude Sonnet 5
- MAS SAFR
- LSM-Tree
- 存储引擎
- 知识库升级
- Schema V2
issue: 10
issue_date: '2026-07-09'
---

> 覆盖周期：2026-07-03 ~ 2026-07-09 | Week 10

---

## 🧠 AI Infra · Agent 基础设施

→ [子调研详情](https://bryantchang1992.github.io/ai_memory_chang_ai_team/tech_research/ai_harness/week_10_2026-07-09.html)

### 🤖 OpenAI GPT-5.5 Instant Mini：无声升级底层 Fallback 模型

OpenAI 于 7 月 6 日在 ChatGPT 中上线 **GPT-5.5 Instant Mini**，替代 GPT-5.3 Instant Mini 作为用户达到速率限制后的 fallback 模型。该模型不在模型选择器中显示，不影响 API 和 Codex，但会影响大量重度用户的体验。

**改进点**：
- 更好地跟踪用户意图变化，校准语气
- 减少重复或过度结构化的回复
- 更强的个性化能力，减少事实性错误

**Insight**：OpenAI 的"无声 fallback"策略是一种低风险渐进式发布模式。对 Agent 应用而言，底层模型静默变化可能影响 tool call 一致性和输出格式——值得在 Agent Pipeline 中增加回归测试。

### 🧪 Claude Sonnet 5：Anthropic 最强 Agentic Sonnet

Anthropic 于 6 月 30 日发布 **Claude Sonnet 5**，在推理、工具调用、编码和知识工作方面全面超越 Sonnet 4.6。Sonnet 是 Claude 的工作马等级，也是 Microsoft 365 Copilot 的底层模型——此次升级直接影响广大企业用户的 Agent 体验。

**Insight**：Anthropic 和 OpenAI 的竞争进入"Agentic Workhorse"阶段——双方都在工作马级模型上押注 Agent 能力，而非仅靠旗舰模型。底层模型 Agent 原生能力越强，框架的编排负担越轻。

### 🏦 MAS SAFR：全球首个金融 Agent 安全治理框架

新加坡金融管理局（MAS）于 7 月 3 日联合头部金融机构和 FinTech 发布 **SAFR（Safeguards for Agentic Finance at Runtime）** 白皮书，提出全球首个 AI Agent 金融安全治理框架。

| 能力 | 描述 |
|------|------|
| **Policy-Bound Execution** | Agent 行为受预定义策略边界约束，所有拟执行动作须通过治理检查点 |
| **Real-Time Validation** | 执行前的运行时验证，确保不超出机构风险边界 |
| **Auditability** | 全部 Agent 决策链路可审计、可追溯 |
| **Interoperability** | 跨系统、跨机构的 Agent 互操作性保障 |

SAFR 基于 MAS Project Mindforge 的 AI 风险管理工具包构建，已在多个金融用例中测试。这标志着 Agent 治理从"行业最佳实践"进入"监管框架"阶段。

**Insight**：金融监管率先对 Agent 安全提出运行时检查点（而非仅部署前审查）要求。对 Agent Harness Governance 模块有直接指导意义——实时拦截 `before_action` 钩子 + 审计日志将成为基本要求。

---

## 💾 存储引擎与数据基础设施

→ [子调研详情](https://bryantchang1992.github.io/ai_memory_chang_ai_team/tech_research/doris/week_10_2026-07-09.html)

### 📚 LSM-tree KV Store：十篇论文与研究方向

基于 Week 09 入库的 ArXiv LSM-tree KV Store 综述，本期梳理了综述引用的十篇顶会和期刊论文，关注合并优化、硬件适配与存算分离。

| 论文/系统 | 方向 | 出处 |
|-----------|------|------|
| Bourbon | Learned Index + LSM | SIGMOD |
| CaaS | Compaction-as-a-Service | VLDB |
| ElasticBF | 弹性 Bloom Filter | ICDE |
| Hailstorm | 存算分离 LSM | VLDB |
| Lethe | 删除感知 LSM | SIGMOD |
| Nova-LSM | 分布式组件化 LSM | FAST |
| Pacman | 持久内存 Compaction | USENIX ATC |
| PebblesDB | 碎片化 LSM-Tree | SOSP |
| REMIX | 全局排序索引 | SIGMOD |
| gLSM | GPU 加速 Compaction | OSDI |

**三大趋势**：
1. **Compaction 是 LSM 研究高地**：10 篇中 4 篇（CaaS/Pacman/PebblesDB/gLSM）直接研究 Compaction 优化
2. **异构硬件适配**：Learned Index + GPU Compaction + PMEM Compaction → LSM 引擎走向异构硬件协同
3. **存算分离共识**：Hailstorm + CaaS 与 Fluss/CockroachDB 的存算分离趋势一脉相承


---

## 📊 统计

| 方向 | 动态数 | 亮点 |
|------|--------|------|
| AI Infra · Agent 基础设施 | 3 | GPT-5.5 Instant Mini、Claude Sonnet 5、MAS SAFR 金融 Agent 治理框架 |
| 存储引擎 | 1 | LSM-tree 十篇论文与研究方向 |

**合计 4 条动态 | 2 方向覆盖**

---

> ⚡ **本周特征**：外部 Agent 动态密集——OpenAI/Anthropic 工作马模型同时升级 + 金融监管率先建立 Agent 安全框架。存储方向关注 LSM-tree 的合并优化、异构硬件与存算分离。
>
> 📎 子调研详情详见各方向页面。
