---
type: concept
title: "Agent Harness: Verification & Evaluation (V)"
sources:
  - "sources/papers/Agent-Harness-Engineering-Survey/Agent-Harness-Engineering-Survey-OpenReview2026.pdf"
  - "sources/papers/Agent-Harness-Engineering-Survey/精读分析.md"
tags:
  - "Agent-Harness"
  - "Agent基础设施"
  - "Agent评估"
  - "基准测试"
created: 2026-06-20
updated: 2026-06-20
status: draft
related:
  - "[[Agent-Harness-Engineering-Survey综述]]"
  - "[[Agent-Harness-Observability可观测性]]"
---

# Agent Harness: Verification & Evaluation (V)

> ETCLOVG 第六层：如何将 Agent 评估从"终局打分"转化为"质量闭环"——论文从 Lifecycle Hooks 独立出来的第二层。

---

## 1. 层级定位

传统 LLM 评估 vs. Agent 评估的本质区别：

| 维度 | 传统 LLM 评估 | Agent Harness 评估 |
|------|-------------|-------------------|
| 评估对象 | 固定输入 → 输出 | **执行剧集（Execution Episode）** |
| 环境 | 无状态 | 有状态（任务在环境中展开） |
| 交互 | 单次调用 | 多轮推理 + 工具调用 + 状态变化 |
| 评估维度 | 输出质量 | 最终结果 + **轨迹质量** + 评估器可靠性 |
| 归因 | 模型 | 模型 + Sandbox + Tools + Context + Orchestrator + Evaluator |

**核心主张**：评估分数应被理解为 **model–harness pair** 的属性，而非模型的单独属性。

---

## 2. 五阶段评估生命周期（Task-to-Feedback Lifecycle）

```
Stage 1: Task & Benchmark Grounding
    ↓
Stage 2: Pre-Execution Readiness Validation
    ↓
Stage 3: Controlled Execution & Trace Capture
    ↓
Stage 4: Multi-Level Judgement & Failure Attribution
    ↓
Stage 5: Continuous Regression & Deployment Feedback
    ↑___________________________________________↓ (反馈循环)
```

### Stage 1: Task & Benchmark Grounding（基准接地）

**问题**：评估什么？在什么环境里？用什么工具？什么约束？什么成功标准？

| 基准 | 领域 | 核心设计 | 验证方式 |
|------|------|----------|----------|
| **SWE-bench** (Jimenez et al., 2024) | 软件工程 | 真实 GitHub Issue + 仓库快照 → 测试验证 Patch | 可执行测试 |
| **Terminal-Bench** (Merrill et al., 2026) | 命令行工作流 | 终端环境交互（编辑文件、执行命令、依赖管理） | 输出验证 |
| **WebArena** (Zhou et al., 2024) | Web 任务 | 模拟电商/社交/论坛网站 | 状态变化检测 |
| **OSWorld** (Xie et al., 2024) | 桌面操作 | 完整 Ubuntu 虚拟机内的真实应用 | 屏幕状态检查 |
| **GAIA** (Mialon et al., 2023) | 通用推理 | 需要多步推理的问答任务 | 精确匹配 |
| **TheAgentCompany** (Xu et al., 2024) | 企业工作 | 模拟公司场景的多步任务 | 端到端验证 |
| **WorkArena++** (Boisvert et al., 2024) | 企业 SaaS | ServiceNow 平台操作 | 平台状态检查 |

关键洞察：**强结果验证器需要强任务接地**——测试只有在仓库状态/依赖/成功标准精确指定时才是可靠的评估器。

### Stage 2: Pre-Execution Readiness Validation（执行前验证）

**问题**：沙箱、依赖、工具、上下文、权限、预算、评估器是否初始化正确？

| 系统 | 验证方法 |
|------|----------|
| **Repo2Run** (Hu et al., 2025a) | 确保仓库依赖可正确安装和执行 |
| **HAL** (Kapoor et al., 2025) | 多维度前检查：环境状态、工具可用性、评估器校准 |
| **SWE-ReX** (SWE-agent Team, 2024) | 为 SWE-bench 任务的评估器做完整性验证 |

**为什么这步重要**：评估噪声可能伪装成模型失败——环境未正确初始化时，失败的测试用例无法区分"模型写错了代码"和"环境不一致"。

### Stage 3: Controlled Execution & Trace Capture（受控执行与 Trace 捕获）

**问题**：在可复制条件下运行 Agent，记录什么？

必须捕获的信息：
- 模型输入/输出（Prompt + Response）
- 工具调用（名称、参数、结果、延迟）
- 状态变化（文件修改、环境变更）
- 错误和重试
- Token 消耗和成本
- 执行时间线

代表系统：SWE-agent（AID 接口设计）、OpenHands（可视化执行）、R2E-Gym（可复制评估环境）

### Stage 4: Multi-Level Judgement & Failure Attribution（多级判断与故障归因）

传统评估只问"是否成功"，Agent 评估需要更多维度：

| 判断维度 | 核心问题 | 评估方法 |
|----------|----------|----------|
| **Outcome-Level** | Agent 最终完成了任务吗？ | 测试通过率、任务成功率 |
| **Trajectory-Level** | Agent 到达结果的过程可接受吗？ | 轨迹质量评分、中间步骤审查 |
| **Evaluator-Level** | 评估器本身可信吗？ | 评估器稳定性、评估器间一致性 |
| **Failure Attribution** | 失败归因到哪个 Harness 层？ | Model / Tool / Sandbox / Context / Orchestrator / Evaluator |

**评估工具**：
- **LLM-as-Judge**（Gu et al., 2024 综述）：GPT-4/Claude 作为评估器——但自身也存在偏差和不稳定性
- **SWE-bench**：可执行测试作为客观验证器
- **HAL**：多维度评估 + 故障归因
- **Terminal-Bench**：终端输出模式匹配 + LLM 评估组合

### Stage 5: Continuous Regression & Deployment Feedback（持续回归与部署反馈）

**问题**：如何将评估结果转化为持续的 Harness 改进？

| 系统 | 能力 |
|------|------|
| **promptfoo** | 开源 Prompt 评估和回归测试框架 |
| **DeepEval** (Confident AI) | 单元测试风格的 LLM 评估 |
| **RAGAS** (Es et al., 2024) | RAG 专用评估指标（忠实度、相关性、上下文召回） |
| **lm-evaluation-harness** (Gao et al., 2021) | 标准化 LLM 评估框架 |
| **Meta-Harness** (Lee et al., 2026) | Prompts/Tools/Control Loops 作为可优化目标 |

---

## 3. 核心挑战

### 3.1 评估噪声伪装成模型失败

失败可能来源于：
- **模型推理错误**（传统认为的唯一原因）
- **工具 Schema 误导**（描述不准确 → 错误调用）
- **沙箱配置错误**（依赖缺失、权限不足）
- **过时上下文**（Context Drift → 基于错误信息决策）
- **评估器不稳定**（LLM-as-Judge 偏差、温度敏感）
- **编排循环故障**（错误恢复逻辑不当）

### 3.2 单次运行的不稳定性

Bjarnason et al. (2026)：单次运行 Pass Rate 隐藏巨大方差 → 需要多次运行 + 统计显著性检验。

### 3.3 长期 Agent 的评估困难

- 传统评估：单个任务（5-30 分钟）
- 长期 Agent：跨 Session 任务（数小时-数天）
- 核心评估问题不是"是否成功"，而是"为什么成功/失败，路径是否可接受，哪个 Harness 组件需要改进"

---

## 4. 评估设计原则

1. **评估应锁定 Harness 跨模型比较**——或将 Harness 配置作为显式实验因子（Bölük, 2026b）
2. **报告分数 = model–harness pair 属性**——不能剥离基础设施来讨论"模型能力"
3. **Trace-Native Evaluation**：Trace 应成为评估的主要对象——而非仅限最终分数
4. **多次运行 + 方差报告**：单次 Pass Rate 不可靠
5. **失败归因到 Harness 层**：不是简单地"模型不够好"，而是定位到具体的基础设施组件

---

## 5. 未来方向

- **从 Leaderboard 到 Quality-Control Loop**：评估不再是排行榜，而是 Harness 改进的反馈回路
- **生产 Trace → 回归 Case**：将线上异常 Trace 自动转化为离线测试用例
- **Trajectory 质量的多维评估**：不只是"最终结果对不对"
- **评估器的元评估**：LLM-as-Judge 本身的可靠性和偏差需要持续监控
