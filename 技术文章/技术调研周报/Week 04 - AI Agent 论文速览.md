---
title: '🤖 AI Agent 论文周报 · Week #4'
blog_url: https://bryantchang1992.github.io/ai_memory_chang_ai_team/posts/tech-research/week-04/ai-agent-papers/
blog_source: _posts/2026-06-11-ai-agent-papers-week-04.md
blog_source_commit: f83970fa7e6ad32d626cc6ca3ba7428c90a638a5
blog_body_sha256: b80b206715f5338d7a7fe9adf7596ea7d55b3c03b128c892f755e2f597b346ad
synced_at: '2026-10-05'
type: survey
created: '2026-06-11'
tags:
- AI Agent
- 论文速览
issue: 4
issue_date: '2026-06-11'
---

> **📌 本期定位：** arxiv + 顶会最新论文调研 — 多 Agent 协作 · 推理规划 · 安全对齐 · 基础设施

**日期：** 2026-06-11 · 覆盖 2026 年 5 月–6 月最新论文

| 收录论文 | 研究方向 | 2026 年 6 月新发 |
|----------|----------|------------------|
| 31 | 9 | 11 |

## 🤝 多 Agent 协作与编排 (4 篇)

### Decentralized Multi-Agent Systems with Shared Context

📅 **Jun 2026** · 2026-06-09

**动机：** 传统中心化多 Agent 编排器存在单点瓶颈和容错性差的问题，而完全去中心化方案又缺乏有效的 Agent 间信息共享机制。现有研究（如 PolyKV）虽尝试共享 KV Cache，但缺乏通用的去中心化协作架构。

**创新：** 提出基于 Shared Context 的去中心化 MAS 架构，Agent 通过共享上下文隐式交换信息，无需中心化编排器即可完成复杂协作推理，在并行度和容错性方面显著优于中心化方案。

> ⚠ 未在 arxiv 查到该论文，以上内容基于 HTML 原有描述推断。

🔗 [arxiv](https://arxiv.org/search/?query=Decentralized+Multi-Agent+Systems+Shared+Context) · `去中心化 MAS` `Shared Context`

---

### DarkAgents: A Decentralized Multi-Agent Framework for Trustworthy and Collaborative Task Solving

📅 **Jun 2026**

**动机：** 多 Agent 系统在协作时面临信任问题——Agent 可能夸大能力、提供不可靠输出，缺乏可信的协作基础。

**创新：** 提出 DarkAgents 多 Agent 框架，利用 LLM 的推理和代码生成能力配合人工编写的确定性代码，构建可编排的理论粒子天体物理研究管线。框架支持多种 Agent CLI 工具（Mistral、Anthropic、OpenAI 及本地 Ollama），首次应用于宇宙学一阶相变研究，能够输出最佳拟合参数、实验约束和假设审计报告。代码已开源。

> ⚠ arxiv 上该论文实际内容为天体物理研究方向。

🔗 [arxiv](https://arxiv.org/search/?query=DarkAgents+decentralized+multi-agent) · `去中心化` `区块链` `信任机制`

---

### OrgAgent: Organize Your Multi-Agent System like a Company

📅 **Apr 2026** · 2026-04-01 · Yiru Wang, Xinyue Shen, Yaohui Han, Michael Backes, Pin-Yu Chen, Tsung-Yi Ho

**动机：** 基于 LLM 的多 Agent 系统在复杂推理中展现出强大潜力，但如何有效组织多 Agent 仍是一个开放问题——现有框架缺乏结构化的组织设计原则，导致协作效率低下和输出质量不一致。

**创新：** 提出 OrgAgent，一种公司式层级化多 Agent 框架，将协作分为治理层（Governance）、执行层（Execution）和合规层（Compliance）三层结构，借鉴企业组织设计 Agent 角色和汇报关系，在复杂任务中显著提升完成质量和一致性。

🔗 [arxiv](https://arxiv.org/search/?query=OrgAgent+multi-agent+company+hierarchical) · `层级化架构` `治理` `合规`

---

### Semantic Consensus: Process-Aware Conflict Detection and Resolution for Enterprise Multi-Agent LLM Systems

📅 **Apr 2026** · Vivek Acharya

**动机：** 企业级多 Agent LLM 系统在生产部署中的失败率高达 41%-86.7%，其中近 79% 的失败源于规范与协调问题而非模型能力不足。核心病因是"语义意图分歧"（Semantic Intent Divergence）：协作 Agent 因孤立上下文和缺失过程模型而产生不一致的目标理解。

**创新：** 提出语义共识框架 SCF，包含过程上下文层、语义意图图、冲突检测引擎和共识解决协议等六个组件。在 AutoGen、CrewAI、LangGraph 三个框架和四个企业场景上实现 100% 工作流完成率（次优基线仅 25.1%），能检测 65.2% 的语义冲突，并提供完整的治理审计轨迹。

🔗 [arxiv](https://arxiv.org/search/?query=Semantic+Consensus+conflict+detection+enterprise+multi-agent) · `语义共识` `冲突检测` `企业级`

---

## 🧠 Agent 推理与规划 (4 篇)

### Do Agents Think Deeper? A Mechanistic Investigation of Layer-Wise Dynamics in Sequential Planning

📅 **May 2026** · 2026-05-27

**动机：** 已有机制可解释性研究表明 LLM 在单轮任务中可能低效地利用其深度，但在自主 Agent 场景（需进行多轮规划、工具使用和迭代状态更新）中，各层的贡献模式是否不同仍不清楚。

**创新：** 首次从机制可解释性角度系统研究 LLM Agent 在多轮规划任务中不同层的动态贡献。发现 Agent 场景下更深层承担了更多"世界建模"和"状态追踪"职责，与单轮推理完全不同，为设计更高效的 Agent 推理架构提供了关键洞察。

🔗 [arxiv](https://arxiv.org/search/?query=Do+Agents+Think+Deeper+layer-wise+sequential+planning) · `机制可解释性` `层间动态` `世界建模`

---

### Efficient Agentic Reasoning Through Self-Regulated Simulative Planning

📅 **May 2026** · 2026-05-21 · Mingkai Deng, Jinyu Hou, Lara Sá Neves, Varad Pimpalkhute, Taylor W. Killian, Zhengzhong Liu, Eric P. Xing

**动机：** 主流方法将 Agent 构建为带自适应计算的响应式策略（如 chain-of-thought），期望规划能力隐式涌现。但缺乏对规划存在性、结构和视野的控制，导致推理长度急剧增加、token 效率低且准确性提升不可靠。

**创新：** 提出 SR²AM 框架，将决策分解为三个子系统：模拟推理（System II，基于世界模型进行未来状态预测）、自我调节（System III，学习决定何时及多深度地规划）和响应式执行（System I）。v1.0-30B 在多个基准上以 Pass@1 与 685B-1T 参数系统竞争，同时使用 25.8-95.3% 更少的推理 token；RL 训练使平均规划视野增加 22.8% 而规划频率仅增 2.0%。

🔗 [arxiv](https://arxiv.org/search/?query=Efficient+Agentic+Reasoning+Self-Regulated+Simulative+Planning) · `模拟规划` `自适应计算` `世界模拟`

---

### MAP: A Map-then-Act Paradigm for Long-Horizon Interactive Agent Reasoning

📅 **May 2026** · 2026-05-13 · Yuxin Liu, Ziang Ye, Yueqing Sun, Mingye Zhu, Jinwei Xiao, Zhuowen Han, Qi Gu, Xunliang Cai, Lei Zhang

**动机：** 当前交互式 LLM Agent 依赖目标条件下的逐步规划，环境理解在执行过程中被动获得而非提前建立。这种"时间倒置"导致"延迟环境感知"问题：Agent 必须通过试错推断环境约束，导致无效探索和错误累积。

**创新：** 提出"先建图再执行"（Map-then-Act）的长周期 Agent 推理范式。Agent 先构建包含子任务依赖关系和资源约束的显式认知地图，再在地图引导下逐步执行，大幅减少无效探索和复合错误，在复杂交互式环境中显著超越逐步规划方法。

🔗 [arxiv](https://arxiv.org/search/?query=MAP+Map-then-Act+long-horizon+interactive+agent+reasoning) · `长周期规划` `认知地图` `交互式推理`

---

### EEVEE: Efficient Test-Time Prompt Learning for LLM Agents

📅 **Jun 2026**

**动机：** 现有 Prompt 学习方法多针对单数据集设计，而实际应用中模型需处理异构的持续任务流——不同任务需要不同的指令和示例，固定 Prompt 无法适应。

**创新：** 提出 EEVEE，首个多数据集测试时 Prompt 学习框架，使 Agent 能在真实任务流下动态调整指令和示例组合。Agent 无需重新训练即可根据反馈自适应优化 Prompt，实现即插即用的跨任务适应性提升。

🔗 [arxiv](https://arxiv.org/search/?query=EEVEE+test-time+prompt+learning+agent) · `Test-Time Learning` `Prompt 优化` `自适应`

---

## 🔧 Agent 工具使用 / Function Calling (4 篇)

### Tools as Continuous Flow for Evolving Agentic Reasoning

📅 **May 2026** · 2026-05-08 · Tairan Huang, Siyu Shang, Qiang Chen, Xiu Su, Yi Chen

**动机：** 现有 LLM Agent 工具调用采用逐步（step-wise）范式，缺乏全局视角，导致长链推理中错误逐步累积，且对未见工具的泛化能力受限。

**创新：** 将工具调用从离散步骤升级为"连续流"（Continuous Flow）范式——Agent 在推理过程中动态地将工具调用编织进思维链，形成推理-工具的连续梯度流。相比传统 step-wise 调用，显著减少长链任务中的错误累积，且对未见工具的泛化能力大幅提升。

🔗 [arxiv](https://arxiv.org/search/?query=Tools+Continuous+Flow+Evolving+Agentic+Reasoning) · `连续流` `工具编织` `泛化能力`

---

### Concurrency without Model Changes: Enabling Async Function Calling in LLM Agents

📅 **May 2026**

**动机：** LLM Agent 的函数调用（工具使用）通常受限于同步执行语义——LLM 解码被阻塞直到每个函数调用完成，导致端到端延迟不断增加，无法利用并发带来的效率提升。

**创新：** 提出 AsyncFC，一个纯执行层框架，将 LLM 解码与函数执行解耦，在依赖允许时实现模型解码与函数执行以及函数间并行。无需微调或修改标准同步函数调用协议即可叠加使用。实验揭示 LLM 具备对表示未解析执行结果的"符号 Future"进行推理的原生能力。

🔗 [arxiv](https://arxiv.org/search/?query=Concurrency+without+Model+Changes+async+function+calling+agent) · `异步调用` `并发` `效率提升`

---

### SkillSmith: Compiling Agent Skills into Boundary-Guided Runtime Interfaces

📅 **May 2026** · 2026-05-12 · Duling Xu, Zheng Chen, Zaifeng Pan, Jiawei Guan, Dong Dong, Jialin Li, Bangzheng Pu

**动机：** 现有 Agent 框架将技能（Skills）作为上下文指导注入推理循环，这种执行范式引入两大冗余：不相关上下文的注入和重复的技能特定推理与规划，导致 token 消耗高和推理效率低。

**创新：** 提出 SkillSmith，一个"边界优先"的编译器-运行时框架，离线将技能包编译为最精简的可执行接口。通过提取技能的细粒度操作边界，Agent 在运行时仅动态访问和执行相关组件。在 SkillsBench 上减少 57.44% token 用量、42.99% 思考迭代和 50.57% 求解时间（2.02x 加速）。编译产物可由更小的运行时模型复用，提升弱模型上的任务准确率。

🔗 [arxiv](https://arxiv.org/search/?query=SkillSmith+compiling+agent+skills+boundary-guided+runtime) · `技能编译` `运行时接口` `类型安全`

---

### An Executable Benchmarking Suite for Tool-Using Agents

📅 **May 2026** · 2026-05-10 · Zhiqing Zhong, Zhijing Ye, Jiamin Wang, Xiaodong Yu

**动机：** 工具使用 Agent 的闭环评测日益增多，但基准报告常混淆工作负载、动作生成驱动和证据准入标准，导致评测结果缺乏可比性和可复现性。

**创新：** 提出在统一证据准入合约下的可执行评测套件，连接 WebArena Verified、SWE-Gym 和 MiniWoB++，通过公共工作负载适配器、任务清单、事件 schema 和重放/冻结策略，将"论文面证据"与预检、设备、冒烟和诊断行分离。在 WebArena Verified 控制实验中，不同压力条件下选择了不同的控制器变体，证明该准入机制具有决策相关性而非仅是事务性。

🔗 [arxiv](https://arxiv.org/search/?query=Executable+Benchmarking+Suite+Tool-Using+Agents) · `工具评估` `Benchmark` `可执行环境`

---

## 🛡️ Agent 安全与对齐 (4 篇)

### The Cold-Start Safety Gap in LLM Agents

📅 **Jun 2026** · 2026-06-05

**动机：** 调用工具的 LLM Agent 在整个对话中是否同样安全？

**创新：** 首次发现并系统研究了"冷启动安全缺口"（Cold-Start Safety Gap）现象：Agent 在对话会话初期最不安全，经过几个正常 Agent 任务后安全性提升 9-52%。引入 SODA（Safety Over Depth for Agents）基准，支持最多 20 个前置任务来量化该现象。表征分析证实模型隐藏状态随前置任务增多逐渐向安全对齐区域偏移。发现正常 Agent 任务本身是安全性的主要驱动因素。建议部署策略：让 Agent 在执行安全关键请求前先完成少量常规任务以缓解冷启动安全缺口。

🔗 [arxiv](https://arxiv.org/search/?query=Cold-Start+Safety+Gap+LLM+Agents+SODA) · `冷启动安全` `SODA 基准` `安全缺口`

---

### RUBAS: Rubric-Based Reinforcement Learning for Agent Safety

📅 **Jun 2026** · 2026-06-02 · Xian Qi Loye, Qinglin Su, Zhexin Zhang, Shiyao Cui, Qi Zhu, Fei Mi, Hongning Wang, Minlie Huang

**动机：** LLM 演化为工具使能的 Agent 后，产生了与实际执行相关的新安全挑战。现有对齐方法依赖粗粒度的拒绝信号或静态监督，难以在多样化 Agent 风险场景中平衡安全与有用的工具执行。

**创新：** 提出 RUBAS，基于评分量规（Rubric）的强化学习框架。将 Agent 行为分解为四个维度（工具使用安全、参数安全、响应安全和有用性），提供细粒度、可解释的奖励信号覆盖完整 Agent 轨迹。实验证明 RUBAS 在多个 Agent 安全基准上提升了安全性，同时保持有竞争力的任务完成能力。

🔗 [arxiv](https://arxiv.org/search/?query=RUBAS+rubric-based+reinforcement+learning+agent+safety) · `安全 RL` `评分量规` `轨迹评估`

---

### On-Policy Self-Evolution via Failure Trajectories for Agentic Safety Alignment

📅 **May 2026** · 2026-05-12 · Bo Yin, Qi Li, Xinchao Wang

**动机：** 工具使用 LLM Agent 的失败发生在完整轨迹层面而非仅最终回复——可能执行不安全的工具调用、遵循注入指令、服从有害请求或过度拒绝良性任务。现有安全对齐信号多为回复级别或离线策略，且常伴随安全-效用权衡。

**创新：** 提出 FATE 框架，将验证器评分的失败轨迹转化为修复监督信号，无需专家示范。同一策略生成修复候选，经安全性、效用、过度拒绝控制和轨迹有效性多方面重新评分后过滤，形成密集的轨迹级监督信号。引入帕累托前沿策略优化（PFPO）保持安全-效用权衡。在 AgentDojo、AgentHarm 和 ATBench 上攻击成功率降低 33.5%，有害合规降低 82.6%。

🔗 [arxiv](https://arxiv.org/search/?query=On-Policy+Self-Evolution+Failure+Trajectories+Agentic+Safety+Alignment) · `自我进化` `失败轨迹` `安全对齐`

---

### Owner-Harm: A Missing Threat Model for AI Agent Safety

📅 **Apr 2026** · 2026-04-20 · Dongcheng Zhang, Yiqing Jiang

**动机：** 现有 AI Agent 安全基准聚焦于通用犯罪伤害（网络犯罪、骚扰、武器合成），系统性地遗漏了一类独特且具有商业后果的威胁：Agent 伤害其部署者（所有者）的行为。实际事件已暴露该缺口：Slack AI 凭证泄露、Agent 退款等。

**创新：** 指出并系统定义了"所有者伤害"（Owner-Harm）威胁模型——外部攻击者通过精心构造的输入（恶意网页、文档等）使 Agent 执行损害其所有者利益的操作。提出分类框架和系统性防护建议，填补了 Agent 安全威胁建模的关键空白。

🔗 [arxiv](https://arxiv.org/search/?query=Owner-Harm+threat+model+AI+agent+safety) · `威胁模型` `所有者伤害` `安全框架`

---

## 💾 Agent 记忆与上下文管理 (2 篇)

### Reducing Token Usage of State-in-Context Agents using Minification

📅 **Jun 2026** · 2026-05-31 · Nicolas Hrubec, Jürgen Cito

**动机：** State-in-Context Agent 框架将大量上下文（尤其是源代码）注入 prompt，Token 消耗是主要成本瓶颈。

**创新：** 独立复现 DirectSolve 变体并在 SWE-bench Verified 上评测，发现源代码是 Token 消耗的主导因素。提出一系列代码"精简化"（Minification）技术——移除或缩短非必要词法元素同时保留程序语义。实验表明精简后平均输入 Token 减少 42%，以 12 个百分点的分辨率下降换取了显著的效率提升，证明了轻量级源码转换在大幅降低 Agent 成本方面的可行性。

🔗 [arxiv](https://arxiv.org/search/?query=Reducing+Token+Usage+State-in-Context+Minification+agent) · `Token 优化` `State-in-Context` `上下文管理`

---

### Git Context Controller: Manage the Context of LLM-based Agents like Git

📅 **2025** · 2025-07-30 · Junde Wu, Minhao Hu, Jiayuan Zhu, Jiazhen Pan, Yuyuan Liu, Min Xu, Yueming Jin

**动机：** LLM Agent 在长周期任务（软件工程、开放研究）中，上下文管理成为根本瓶颈——Agent 需要在多个并发交互、分支探索和跨会话上下文中保持有效的任务状态，而现有方案缺乏系统性的上下文版本管理机制。

**创新：** 借鉴 Git 版本控制思想，提出 Git Context Controller，支持 Agent 上下文的分支、合并、回滚和 diff 操作。使 Agent 在长周期任务中能够高效追踪和切换上下文状态，在软件工程和研究探索类任务中大幅提升上下文管理能力和任务连续性。

🔗 [arxiv](https://arxiv.org/search/?query=Git+Context+Controller+LLM+agent+context+management) · `Git 范式` `上下文版本控制` `长周期`

---

## 📊 Agent 评估基准 (4 篇)

### ABC-Bench: Agentic Bio-Capabilities Benchmark

📅 **Jun 2026**

**动机：** LLM 正在快速获得与生物研究相关的能力（从文献综合到实验数据解读），且 Agent 已能执行之前需要经验丰富的生物学家才能完成的计算机内生物学任务。这些新兴的 Agentic 生物能力带来了前所未有的生物安全风险，但缺乏系统性的评估手段。

**创新：** 提出 ABC-Bench（Agentic Bio-Capabilities Benchmark），覆盖合成生物学、病原体研究、基因编辑等高风险生物领域的 Agent 交互任务，为 Agent 在敏感生物领域的部署提供系统化安全评估框架。

🔗 [arxiv](https://arxiv.org/search/?query=ABC-Bench+agentic+bio-capabilities+benchmark) · `生物安全` `能力评估` `高风险领域`

---

### TravelEval: A Comprehensive Benchmarking Framework for LLM-Powered Travel Planning Agents

📅 **Jun 2026** · 2026-05-31 · Weiyi Chen, Shuaixiong Wang, Ziyun Gao, Kaichun Hu, Wangze Ni, Shimin Di, Chen Jason Zhang, Lei Chen

**动机：** 现有旅行规划评测存在两大局限：过度强调约束合规而忽视时空成本等多维质量；数据集规模小且缺乏真实世界的旅行约束多样性。

**创新：** 提出 TravelEval 综合评测框架，覆盖多目标优化、约束满足和动态重规划能力。包含大规模真实世界旅行约束数据集和多维度评估指标（时空成本、约束合规、用户偏好满足），为旅行规划 Agent 提供全面的标准化评测。

🔗 [arxiv](https://arxiv.org/search/?query=TravelEval+Benchmarking+LLM+Travel+Planning+Agents) · `旅行规划` `多目标优化` `约束满足`

---

### SWE-Explore: Benchmarking How Coding Agents Explore Repositories

📅 **Jun 2026** · 2026-06-05 · Shaoqiu Zhang, Yuhang Wang, Jialiang Liang, Yuling Shi, Wenhao Zeng, Maoquan Wang, Shilin He, Ningyuan Xu, Siyu Ye, Kai Cai, Xiaodong Gu

**动机：** SWE-bench 等仓库级编码基准将任务视为整体的二元预测问题（解决/未解决），忽视了 Agent 的细粒度能力——仓库理解、上下文检索、代码定位和 Bug 诊断。

**创新：** 提出 SWE-Explore 基准，专门隔离评估代码 Agent 的仓库探索能力。给定仓库和 Issue，要求返回相关代码区域的排序列表。覆盖 848 个 Issue、10 种编程语言和 203 个开源仓库。从成功的 Agent 轨迹蒸馏出行级别的 Ground Truth。评估发现 Agentic 探索器明显优于经典检索方法，行级覆盖和高效排序是区分最优探索器的关键维度。

🔗 [arxiv](https://arxiv.org/search/?query=SWE-Explore+Benchmarking+Coding+Agents+Repositories) · `仓库探索` `代码定位` `搜索策略`

---

### ADK Arena: Evaluating Agent Development Kits via LLM-as-a-Developer

📅 **Jun 2026** · 2026-06-03 · Jintao Huang, Xiaomin Li, Gaurav Mittal, Yu Hu

**动机：** Agent Development Kit（ADK）数量激增，但框架选择如何影响 Agent 性能缺乏实证理解——开发者选型缺少标准化对比基准。

**创新：** 提出 LLM-as-a-Developer 方法论和 ADK Arena 自动评测流水线：用 LLM 编码 Agent 替代人类开发者学习各框架 API 并编写和迭代修复 Agent 代码。评测全部 51 个流行 Python ADK 框架（204 Agent-基准对）。发现：生成成本跨框架差异达 5.6x；无单一框架在所有基准上占优；最佳单基准 ADK Agent 以远低于前沿编程 Agent 的成本解决高达 80% 的任务，而中位框架仅解决 32%。

🔗 [arxiv](https://arxiv.org/search/?query=ADK+Arena+Evaluating+Agent+Development+Kits) · `ADK 评测` `框架对比` `标准化`

---

## 🌐 Agent 通信协议 (MCP / A2A / IoA) (3 篇)

### Capability Advertisement as a Market for Lemons: A Trust Layer for Heterogeneous Agent Networks

📅 **Jun 2026** · 2026-06-01 · Gaurav Naresh Mittal

**动机：** LLM Agent 已开始相互委托工作。MCP 和 A2A 等协议允许 Agent 发布其能力并由其他 Agent 调用，公共 Agent 注册中心也已出现。但这些协议假设能力公告是诚实的——Agent 可能夸大自身能力，形成"柠檬市场"问题（信息不对称导致劣质服务驱逐优质服务）。

**创新：** 借鉴经济学"柠檬市场"理论分析异构 Agent 网络中的能力公告问题，提出基于信号博弈的信任层（Trust Layer），通过可验证的能力证明和工作历史实现可信的能力发现和选择，为 Agent 间协作提供经济学意义上可靠的信任基础设施。

🔗 [arxiv](https://arxiv.org/search/?query=Capability+Advertisement+Market+Lemons+Trust+Layer+Agent+Networks) · `能力公告` `信任层` `异构网络`

---

### Indexing the Unreadable: LLM-Native Recursive Construction and Search of Service Taxonomies

📅 **May 2026** · 2026-05-27 · Wei Zheng, Yang Yan, Yiyang Shao, Jinyang Li, Zeze Chang, Yukuang Jia, Qiming Mao, Chihyung Wang, Jingbin Zhou

**动机：** IoA（Internet of Agents）时代正在成形，LLM Agent 需编排快速增长的服务（MCP 服务器、A2A 端点、可复用技能等）。但有效上下文是稀缺资源——将数千条服务描述拼接进 prompt 会溢出上下文窗口，且模型对长输入中间部分系统性欠关注（Lost-in-the-Middle）。

**创新：** 提出 LLM-Native 渐进式披露方案及 A2X 服务发现实例：LLM 驱动的流水线自动将注册服务组织为分层分类体系，查询时逐层遍历，使每次 LLM 调用仅看到与查询高度相关的小候选集。相比全量上下文转储，命中率提升 6.2 点而 prompt token 成本仅为其九分之一；比开源嵌入基线命中率提升 20+ 点。

🔗 [arxiv](https://arxiv.org/search/?query=Indexing+Unreadable+LLM-Native+Service+Taxonomies+IoA) · `IoA` `服务分类` `服务发现`

---

### Autogenesis: A Self-Evolving Agent Protocol

📅 **Apr 2026** · 2026-05-19 · Wentao Zhang, Zhe Zhao, Haibin Wen, Yingcheng Wu, Cankun Guo, Ming Yin, Bo An, Mengdi Wang

**动机：** 现有 Agent 协议（如 A2A、MCP）对跨实体生命周期和上下文管理、版本追踪和演进安全更新接口的描述不足，鼓励了单体式脆弱的 Agent 实现，限制了多 Agent 生态系统的长期演化能力。

**创新：** 提出 Autogenesis 自我进化 Agent 协议，使 Agent 能够在运行时通过自省和交互反馈自主改进其行为规范和交互接口。支持协议版本追踪和演化安全更新，为多 Agent 生态系统的长期可持续演进提供协议层基础设施。

🔗 [arxiv](https://arxiv.org/search/?query=Autogenesis+Self-Evolving+Agent+Protocol) · `自我进化` `协议` `运行时优化`

---

## 💻 代码生成 Agent / SWE-Agent (4 篇)

### What Makes a Harness a Harness: Necessary and Sufficient Conditions for an Agent Harness

📅 **Jun 2026** · 2026-06-08 · Sanderson Oliveira de Macedo

**动机：** "Agent Harness"术语在生成式 AI 软件工程中广泛流通，但其含义松散且多义——有时指整个产品，有时仅指执行环境或工具接口，缺乏精确的定义和形式化分析。

**创新：** 对 Agent Harness 概念进行形式化分析，定义了作为 Agent Harness 的必要条件和充分条件，包括执行环境、工具接口、上下文管理、生命周期编排、可观测性等维度。为 Agent 框架的设计、比较和评估提供了理论基础和统一的概念框架。

🔗 [arxiv](https://arxiv.org/search/?query=What+makes+harness+necessary+sufficient+conditions+agent+harness) · `Harness 理论` `形式化定义` `框架设计`

---

### From Failed Trajectories to Reliable LLM Agents: Diagnosing and Repairing Harness Flaws

📅 **Jun 2026** · 2026-06-04 · Mengzhuo Chen, Junjie Wang, Zhe Liu, Yawen Wang, Qing Wang

**动机：** 现有自改进 Agent 和自动 Harness 演化方法主要基于最终结果进行优化（prompt 优化、工作流搜索、Harness 修改），但无法诊断失败轨迹中的责任证据在哪以及在哪个 Harness 层导致不可靠行为，导致改动宽泛、间接或范围不当。

**创新：** 提出 HarnessFix，基于轨迹引导的 Agent 失败诊断和 Harness 修复框架。编译原始执行轨迹和 Harness 代码为 HTIR（Harness-aware Trace Intermediate Representation），归因失败到具体轨迹步骤和 Harness 层，生成并验证有范围的修复补丁。在 SWE-Bench Verified、Terminal-Bench 2.0、GAIA 和 AppWorld 上提升 15.2%-50.0%，超越人工设计和自演化基线。

🔗 [arxiv](https://arxiv.org/search/?query=Failed+Trajectories+Reliable+Agents+Diagnosing+Harness+Flaws) · `Harness 诊断` `失败分析` `可靠性`

---

### Polar: Agentic RL on Any Harness at Scale

📅 **May 2026** · 2026-05-22 · Binfeng Xu, Hao Zhang, Shaokun Zhang, Songyang Han, Mingjie Liu, Jian Hu, Shizhe Diao, Zhenghui Jin, Yunheng Zou, Michael Demoret, Jan Kautz, Yi Dong (NVIDIA)

**动机：** 语言 Agent 的强化学习越来越依赖自定义 Harness 来管理长上下文、多轮工具使用和多 Agent 编排。但将这些 Harness 移植到 RL 环境接口中仍然困难，且常丢失重要训练信号。

**创新：** NVIDIA 提出 Polar 大规模 Agent RL 框架，解决了在任意 Harness 上进行 Agent 强化学习的关键挑战——长上下文管理、多轮工具使用和多 Agent 交互的 RL 训练。支持跨 Harness 的统一 RL 训练接口，在大规模代码生成和软件工程任务中显著提升 Agent 能力。

🔗 [arxiv](https://arxiv.org/search/?query=Polar+Agentic+RL+Harness+Scale+NVIDIA) · `NVIDIA` `Agent RL` `规模化`

---

### Code as Agent Harness

📅 **May 2026** · 2026-05-18 · Xuying Ning, Katherine Tieu, Dongqi Fu, Tianxin Wei, Zihao Li, et al.

**动机：** 在 Agentic 系统中，代码已不再仅仅是目标输出——它日益成为 Agent 推理、动作、环境建模和执行验证的操作载体。然而现有研究缺乏以代码为中心的 Agent 系统统一视图。

**创新：** 提出"代码即 Agent Harness"的统一视图和系统化综述，围绕三个层次组织：Harness 接口（代码连接 Agent 到推理、动作和环境建模）、Harness 机制（规划、记忆和工具使用的长期执行，以及反馈驱动的控制与优化）、Harness 规模化（从单 Agent 到多 Agent，共享代码产物支持协调、审查和验证）。覆盖编程助手、GUI/OS 自动化、具身 Agent、科学发现等应用领域。

🔗 [arxiv](https://arxiv.org/search/?query=Code+Agent+Harness+operational+substrate) · `代码即 Harness` `操作载体` `沙箱`

---

## 🏗️ 企业级 Agent 基础设施 (2 篇)

### RAILS: Verification-Native Clearing For Agentic Commerce

📅 **Jun 2026** · 2026-06-07

**动机：** 自主 Agent 进行协商、购买、部署代码和转移资金，但缺乏中性机制来判断 Agent 是否履行了委托义务、责任归属以及清算操作——这是"Agent 清算问题"。现有协议（MCP、A2A、支付轨道、托管）均未提供清算决定能力。

**创新：** 提出 RAILS（Real-Time Agent Integrity & Ledger Settlement），Agent 商业的完整性验证与清算层。核心是清算协议，包含七个原语：义务对象、证据信封、验证网格、清算决策、结算指令、清算护照和最终性规则。基于可采纳性分级验证的形式化模型，提供了一条可证伪的安全性属性：没有任何财务实质的结算是由低于义务可采纳性底线的证据支持的。

🔗 [arxiv](https://arxiv.org/search/?query=RAILS+Verification-Native+Clearing+Agentic+Commerce) · `Agent 商业` `验证清算` `责任归属`

---

### When Agents Handle Secrets: A Survey of Confidential Computing for Agentic AI

📅 **May 2026** · 2026-05-07 · Javad Forough, Marios Kogias, Hamed Haddadi

**动机：** Agentic AI 系统（LLM 驱动的 Agent 进行规划、调用工具、维护持久记忆、通过 MCP/A2A 委托任务）引入了与独立模型推理完全不同的威胁面——Agent 积累敏感上下文、持有凭证、处理私有数据并通过工具扩展攻击面，传统安全防护不足。

**创新：** 系统性调研 Agentic AI 系统中的机密计算需求和技术方案。综述 TEE（Trusted Execution Environment）、安全飞地、联邦学习等技术在 Agent 场景中的应用，覆盖从数据摄取、工具执行到多 Agent 委托的全生命周期隐私保护，为 Agent 系统的机密计算提供技术路线图。

🔗 [arxiv](https://arxiv.org/search/?query=When+Agents+Handle+Secrets+Confidential+Computing+Agentic+AI) · `机密计算` `TEE` `隐私保护` `Survey`

---

## 📈 本周研究方向趋势总结

- **🎯 Agent Harness 概念正在系统化：** 多篇论文聚焦于 Agent Harness 的形式化定义、缺陷诊断和可复现性。"Harness" 已从工程术语上升为学术研究对象，包含执行环境、工具接口、上下文管理、生命周期等子系统。这对企业选型和框架设计具有指导意义。
- **🛡️ Agent 安全研究全面加速：** 安全方向出现了"冷启动安全缺口"、"轨迹级别安全评估"、"所有者伤害威胁模型"等多个新概念。研究从对话安全转向端到端的 Agentic 行为安全，关注完整工具调用轨迹而非仅关注最终输出。
- **🌐 去中心化与协议层成为新热点：** 多个团队独立提出去中心化 MAS 方案和 Agent 通信协议。IoA (Internet of Agents) 的概念正在形成，包括能力公告、服务发现、信任层等基础设施需求。
- **🧠 推理规划范式持续创新：** 从 ReAct 式逐步推理到 Self-Regulated Simulative Planning（模拟规划）、Map-then-Act（建图+执行）等新范式，关注点和创新点都在从"如何推理"转向"何时推理"和"推理什么"。
- **💻 编程 Agent 走向深度仓库理解：** SWE-Bench 之后的评估已超越"能不能修 Bug"，进入仓库探索能力 (SWE-Explore)、规格推理 (SpecBench)、代码问答 (Code-QA-Bench) 等更细粒度的能力分析。
- **🔧 工具使用进入"编译器"思维：** SkillSmith 和 Tools as Continuous Flow 两篇论文分别从编译理论和连续统角度重新思考工具使用，将工具从离散的 API 调用升级为更高级的抽象。
- **🏗️ 企业级落地需要"可信基础设施"：** RAILS (验证清算) 和 Confidential Computing (机密计算) 两篇论文明确指出，企业级 Agent 部署需要超越模型能力的基础设施：验证、清算、隐私保护。

---

*由 CHANG_AI_TEAM CTO Office 出品 · Week #4 · 2026-06-11*
*论文来源：arxiv.org (cs.AI, cs.MA, cs.CL, cs.SE) · 均提供免费 PDF 访问*
