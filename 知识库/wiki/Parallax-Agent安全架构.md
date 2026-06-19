---
type: analysis
title: "Parallax — Agent 安全架构"
sources:
  - "sources/papers/Parallax/arxiv-2604.12986-精读.md"
  - "https://arxiv.org/abs/2604.12986"
tags:
  - "agent-infra"
  - "agent-security"
  - "prompt-injection"
  - "sandbox"
created: 2026-06-19
updated: 2026-06-19
status: draft
related:
  - "[[Agent-Sandbox-安全沙箱选型]]"
  - "[[Anthropic-Agent安全容器化实践]]"
  - "[[Custom-Agent-Harness-Middleware架构]]"
  - "[[Agent-First-Data-Systems]]"
  - "[[AI-Infra-Agent基础设施体系综述]]"
---

# Parallax — Agent 安全架构

Fokou et al. (2026) 提出 **Parallax 范式**。核心论断：**think 和 act 必须在架构层面分离**。Prompt 级安全（prompt-level guardrails）对于具备执行能力的 Agent 架构是不足的——因为 Prompt 级防护和推理系统在同一被攻破的进程中，相当于让被入侵的大脑监督自己。

## 四原则

### 1. Cognitive-Executive Separation（认知-执行分离）

**结构性地阻止推理系统执行动作。** 推理系统（LLM）只产出"意图"（intent），独立的执行系统负责将意图转化为动作。这从根本上切断了 prompt injection 的攻击链路——即使推理被攻破，执行系统不会自动执行攻击意图。

### 2. Adversarial Validation with Graduated Determinism（对抗验证 + 渐进确定性）

推理与执行之间插入**独立的多层验证器**，按确定性递减排列：
1. **高确定性层**：规则引擎、签名匹配、白名单
2. **中确定性层**：ML classifier（检测异常意图模式）
3. **低确定性层**：LLM as validator（判断意图是否安全）

验证失败 → 拒绝执行 → 触发回滚。

### 3. Information Flow Control（信息流控制）

通过 Agent 工作流传播**数据敏感性标签**：
- 敏感数据（如 PII、credentials）打上 `confidential` 标签
- 标签跟随数据流动，任何组件读写 sensitive data 时触发验证
- 与 [[Anthropic-Agent安全容器化实践]] 中的"凭证不进沙箱"原则互补——IFC 处理策略层，沙箱处理隔离层

### 4. Reversible Execution（可逆执行）

捕捉预破坏状态（pre-destructive state）以支持验证失败时回滚：
- 每个执行步骤前做 snapshot
- 验证失败 → 回滚到最近的 snapshot
- 回滚不仅是数据层面（如 SQL rollback），还包括副作用层面（撤销已发送的消息、已修改的配置）

## 实验结果

| 配置 | 攻击阻断率 | 误报率 | 说明 |
|------|-----------|--------|------|
| 默认 | 98.9% | 0% | 280 对抗用例，9 类攻击 |
| 最高安全 | 100% | 未公布 | 可能引入性能开销 |

**关键结论**：当推理系统被攻破时，prompt-level guardrails 提供零保护。

## 与现有安全方案的对比

| 方案 | 防御层次 | 核心机制 | 被攻破时 |
|------|----------|----------|----------|
| Prompt guardrails | 推理层内 | "Don't do X" prompt | ❌ 完全失效 |
| Sandbox（[[Agent-Sandbox-安全沙箱选型]]） | 环境层 | 隔离执行 | ✅ 限制攻击面 |
| Anthropic 三层（[[Anthropic-Agent安全容器化实践]]） | 环境+模型+内容 | 多重叠加 | ⚠️ 模型层仍可被绕过 |
| **Parallax** | 架构层 | think-act 分离 | ✅ 推理被破，执行不受控 |

## 在 [[Custom-Agent-Harness-Middleware架构]] 中的落地

Parallax 的认知-执行分离可以通过 Harness Middleware 实现：

```
Agent Core (推理系统)
     ↓ 产出 intent
SecurityMiddleware (Parallax 验证层)
     ├── RuleEngineMiddleware   (高确定性)
     ├── ClassifierMiddleware   (中确定性)
     └── LLMValidatorMiddleware (低确定性)
     ↓ 验证通过
ToolMiddleware (执行系统)
     ↓
SandboxMiddleware
```

关键是 Intent 和执行之间必须有一个独立的 Middleware 层——不依赖同一个 LLM context。

## 工程启示

1. **Think 和 Act 分离不是性能优化，是安全架构原则**——任何允许 Agent 直接执行代码的架构都有这个安全缺口
2. **Graduated Determinism 是实用方案**——纯规则太死板、纯 LLM 太不可靠，分层验证兼顾准确性和灵活性
3. **Reversible Execution 在 Agent 语境下难度很高**——Agent 的副作用不限于数据（消息、配置、文件），完整回滚需要 infrastructure 支持
