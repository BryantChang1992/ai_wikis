---
type: concept
title: "Agent Harness: Governance (G)"
sources:
  - "sources/papers/Agent-Harness-Engineering-Survey/Agent-Harness-Engineering-Survey-OpenReview2026.pdf"
  - "sources/papers/Agent-Harness-Engineering-Survey/精读分析.md"
tags:
  - "Agent-Harness"
  - "Agent基础设施"
  - "Agent安全"
  - "AI治理"
created: 2026-06-20
updated: 2026-06-20
status: draft
related:
  - "[[Agent-Harness-Engineering-Survey综述]]"
  - "[[Agent-Harness-Execution-Environment执行环境]]"
  - "[[Agent-Harness-Tool-Interface工具接口]]"
  - "[[Custom-Agent-Harness-Middleware架构]]"
  - "[[Anthropic-Agent安全容器化实践]]"
---

# Agent Harness: Governance (G)

> ETCLOVG 第七层：Agent 部署中的身份、权限、护栏、审计与合规——从"提示安全"到"系统安全"的范式转变。

---

## 1. 层级定位

Governance 不是安全补丁的叠加，而是**可组合的治理模块和可移植策略语言的系统设计**。论文将 Governance 分为六大机制，从身份管理到跨 Agent 审计。

关键发现（Kim et al., 2026）：在 6 个真实 Agent 系统（Codex, Gemini CLI, OpenHands, Browser Use, Nanobrowser, Skyvern）的审计中——**信息流控制、身份管理和形式化验证在全部系统中缺失**。

---

## 2. 六大治理机制

### 2.1 Identity & Permissions（身份与权限）

| 维度 | 当前状态 | 目标 |
|------|----------|------|
| 身份模型 | 大多数系统简单继承本地用户身份 | 组织级身份、OAuth 委派、跨系统联合 |
| 权限粒度 | 粗粒度（"Agent 可以访问文件系统"） | 细粒度（"Agent 可以读取 `/project/docs/` 但不可写入 `/etc/`"） |
| 委派 | Agent 以自己的身份行动 | Agent 代表用户、受用户权限限制 |

**核心挑战**：Agent 不是单一用户——它是代表用户跨多个系统行动的软件实体。身份管理需要支持"Agent X 以用户 Y 的名义、受策略 Z 的约束、调用服务 W"。

### 2.2 Guardrails & Information Flow Control（护栏与信息流控制）

**三层护栏**：

| 护栏类型 | 位置 | 功能 | 代表实现 |
|----------|------|------|----------|
| **Input Guardrails** | 输入到 Agent 之前 | 检测 Prompt Injection、越狱、不安全指令 | NeMo Guardrails, Guardrails AI |
| **Output Guardrails** | Agent 输出之后 | 过滤 PII 泄露、有害内容、不安全代码 | LLM Guard, AutoHarness |
| **Information Flow Control** | 工具间数据流动 | 追踪敏感数据在工具链中的传播 | Progent, SAFEFLOW |

**护栏组合问题**：独立护栏层可能相互干扰：
- Input Guardrail 可能误拦截合法工具调用结果
- Output Guardrail 可能过度过滤导致工具链中断
- 多层护栏的协调尚未标准化

### 2.3 Lifecycle Hooks（生命周期钩子）

在 Agent 执行的关键节点嵌入检查点：

| 钩子点 | 用途 |
|--------|------|
| Pre-Tool-Call | 权限验证、风险分类、策略检查 |
| Post-Tool-Call | 结果验证、异常检测、审计记录 |
| Pre-Context-Update | 上下文一致性检查、敏感信息过滤 |
| Post-Session-End | 状态持久化、交接准备、审计完整性 |

当前状态：大多数系统只在工具调用层有钩子——**上下文中和 Session 间的钩子是缺失的**。

### 2.4 Constitutions（章程）

**两层章程体系**：

| 类型 | 机制 | 可修改性 | 可审计性 | 代表 |
|------|------|----------|----------|------|
| **Training-Time** | RLHF 对齐阶段内化 | ❌ 需要重新训练 | ❌ 只能通过行为探测推断 | Claude Constitution |
| **Deployment-Time YAML** | 外部 YAML 文件声明治理规则 | ✅ 版本化、可 diff | ✅ 直接可读 | AutoHarness (AIMing Lab, 2026) |
| **Programmable Policy DSL** | 形式化语言（布尔谓词、量词、有限自动机） | ✅ 但需要专业知识 | ✅ 形式化可验证 | Progent, Formal-LLM, VeriSafeAgent |

**Deployment-Time 宪法的优势**（AutoHarness）：
- 安全团队无需触碰 Agent 代码即可修改策略
- YAML 文件可版本化、diff、纳入 CI/CD
- 风险分类模式、允许/禁止的工具、Token 预算、审计目标——全部声明式配置

**三种模式对比**：

| 模式 | 表达能力 | 使用门槛 | 适合场景 |
|------|----------|----------|----------|
| YAML 声明式 | 模式匹配 | 低（非开发者可用） | 标准合规场景 |
| DSL 可编程 | 逻辑谓词 + 量词 | 中 | 需要条件逻辑的场景 |
| 形式化验证 | 有限自动机约束 | 高（需形式化专家） | 安全关键场景 |

**开放挑战**：
- 无广泛采用的章程标准 Schema——每个 Harness 定义自己的 YAML 结构 → 策略不可移植
- 章程内部一致性验证（无矛盾的 allow/deny 规则）和完整性验证（无未处理的工具类别）的工具链有限
- Training-Time 与 Deployment-Time 章程的交互——YAML deny-rule 能否可靠覆盖 RLHF 强化的行为？

### 2.5 Audit Infrastructure（审计基础设施）

**完整可重播审计记录的最小字段集**：
1. Trace 标识符
2. 主体身份（哪个 Agent / 代表哪个用户）
3. 工具调用（名称、参数）
4. 策略决策（政策版本、决策结果）
5. 执行结果
6. 资源成本（Token、延迟）
7. 输入/输出完整性哈希

**当前差距**：大多数系统只记录上述字段的子集，且几乎没有人对日志进行签名或哈希——审计日志容易被被入侵的 Agent 进程篡改。

**异常检测分层**：

| 检测级别 | 方法 | 代表系统 | 优点 | 局限 |
|----------|------|----------|------|------|
| **Per-Action** | 逐个工具调用分类风险 | Input/Output Guardrails (§9.2), AgentMonitor | 低延迟、易审计、可内联部署 | 无法识别分布式攻击（如慢速渗出：每分钟读一个文件） |
| **Trajectory-Level** | 行为模式匹配 + LLM 推理全链路 | AgentAuditor (Luo et al., 2025), SentinelAgent (He et al., 2025) | 捕获多步攻击 | 高延迟、归因模糊（哪个动作触发警报？）、实时干预困难 |

**Tiered Governance Pipeline（AutoHarness 三级管道）**：

```
Core (最小):
  Parse → Risk-Classify → Permission-Check → Execute → Audit-Log

Standard:
  + Context-Enrich → Output-Validate → Anomaly-Score

Enhanced:
  + Human-Escalate → Formal-Constraint-Verify
```

Tier 通过 YAML Constitution 声明式选择——治理开销随部署风险扩展。

### 2.6 Situating Governance in Agent Security Landscape

**两篇互补的安全调查**：

| 调查 | 规模 | 视角 | 核心框架 |
|------|------|------|----------|
| **Kim et al. (2026)** | 128 篇论文, 51 攻击方法, 60 防御方法 | 攻击面分析 | 7 设计维度 (Input Trust, Access Sensitivity, Workflow, Action, Memory, Tool, UI) |
| **Chen et al. (2026)** | 50 篇论文 | 软件工程 | 6 维分类法 + 安全构建参考准则 |

**治理机制与安全风险的映射**（Table 3 原文）：

| 治理机制 | 缓解的安全风险 |
|----------|---------------|
| Permissions + Identity Mgmt | R1 (不可信接口), R5 (数据泄露), R6 (未授权行动) |
| Input Guardrails | R1, R2 (错误指令遵循) |
| Output Guardrails | R2, R4 (幻觉), R5, R6 |
| Information Flow Control | R3 (无约束数据流), R5, R6 |
| Component Hardening | R1, R2, R4 |
| Monitoring & Audit | R5, R6, R7 (资源耗尽) |
| Human-in-the-Loop | R2, R6 |
| Privilege Separation | R2, R3 |
| Formal Verification | R2, R6 |
| Declarative Constitution | **交叉切面**：配置以上所有 |

**Contextual Security 提案**（Kim et al., 2026）：
- 提议作为 AI 安全第四目标，补充 CIA 三元组（机密性/完整性/可用性）
- 工程方向：上下文应被视为**受治理的状态**而非被动提示材料（Conseca, CaMeL）
- ⚠️ 尚未被 NIST 等标准机构采纳——论文仅将其作为有用框架而非既定定义

---

## 3. 治理覆盖缺口（Table 4 原文选录）

| 系统 | Permissions | Hooks | Hardening | Constitution | Audit | Multi-Agent |
|------|------------|-------|-----------|-------------|-------|-------------|
| **Codex** | ❌ | ✅ | ❌ | ❌ | ✅ | ❌ |
| **Gemini CLI** | ❌ | ✅ | ❌ | ❌ | ✅ | ❌ |
| **OpenHands** | ✅ | ❌ | ❌ | ❌ | ✅ | ✅ |
| **AutoHarness** | ❌ | ❌ | ✅ | ✅ | ✅ | ❌ |
| **Progent** | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ |
| **CaMeL** | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **SAGA** | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ |

**观察**：✅ 的比例极低——没有一个系统覆盖全部 6 种治理机制。Multi-Agent 治理尤为薄弱（仅 OpenHands 有部分支持）。

---

## 4. 设计原则

1. **从"提示安全"到"系统安全"**：威胁面已扩展到工具调用、沙箱逃逸、多 Agent 社会工程
2. **可组合的治理模块**：Permissions ≠ Guardrails ≠ Hooks ≠ Constitution ≠ Audit——每层应独立可启用/配置
3. **可移植的策略语言**：MCP 为工具接口做了什么，治理需要为策略做什么——需要社区驱动的标准 Schema
4. **防御纵深不免费**：多层护栏可能相互干扰——可组合性尚未在实战中验证
5. **审计的完整性**：审计日志需要签名和哈希——否则 Agent 入侵可篡改自身审计记录
6. **身份是治理的根基**：没有正确的身份模型，权限、审计和追责都是空中楼阁

---

## 5. 对我们（CHANG_AI_TEAM）的启示

1. **身份管理是当前的普遍缺失项**——如果我们要构建生产级 Agent 系统，这是第一个要解决的问题
2. **Deployment-Time YAML Constitution**（AutoHarness 模式）是务实的起点——安全团队不写代码也能定义策略
3. **审计完整性**——我们的 Agent 日志应该包含最小审计字段集，且签名/哈希防止篡改
4. **Contextual Security 值得关注**——虽然未成为标准，但上下文作为受治状态的思路对长期 Agent 有实用价值
5. **Multi-Agent 治理**是最大的空白——如果我们要做多 Agent 系统，需要前瞻性地设计治理机制

---

> 返回父页：[[Agent-Harness-Engineering-Survey综述]] · 上一级：ETCLOVG 七层体系 · G 层（Governance）
