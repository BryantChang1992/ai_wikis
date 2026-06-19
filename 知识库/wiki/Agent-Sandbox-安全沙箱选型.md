---
type: concept
title: "Agent Sandbox — 安全沙箱选型"
sources:
  - "sources/web/langchain/right-sandbox-agent-精读.md"
  - "https://www.langchain.com/blog/how-to-choose-the-right-sandbox-for-your-agent"
tags:
  - "agent-infra"
  - "agent-security"
  - "sandbox"
  - "prompt-injection"
created: 2026-06-19
updated: 2026-06-19
status: draft
related:
  - "[[Anthropic-Agent安全容器化实践]]"
  - "[[Parallax-Agent安全架构]]"
  - "[[Custom-Agent-Harness-Middleware架构]]"
  - "[[Agent-First-Data-Systems]]"
---

# Agent Sandbox — 安全沙箱选型

Agent 最有价值的能力——写代码并执行——同时也是最大安全风险。[[Parallax-Agent安全架构]] 中的 prompt injection 攻击路径在沙箱上下文中尤为致命。LangChain 基于 Simon Willison 的 Lethal Trifecta 理论提出沙箱选型框架。

## Lethal Trifecta（致死三要素）

Simon Willison 提出：以下**三个条件同时满足**时，Agent 允许攻击者窃取数据：

1. **访问敏感数据**
2. **暴露于不可信内容**（用户输入 / 网页 / 邮件 / prompt injection）
3. **能对外通信**（curl / requests / 文件上传）

Meta 补充的 **Rule of Two**：三个条件同时满足时，Agent **不能完全自主运行**——必须有 human-in-the-loop。Sandbox 的作用是**缩小**这三个条件的范围，而非消除。

## 安全 Sandbox 五要素

| 特性 | 说明 | 风险面 |
|------|------|--------|
| **隔离文件系统** | 仅包含所需数据，阻断其他访问 | 缩小条件 1 |
| **有限网络访问** | 白名单端点，拒绝任意 outbound | 缩小条件 3 |
| **资源限制** | CPU/内存/时长上限 | 防 DoS / 煤矿攻击 |
| **受控复用性** | 选择复用 or 销毁；复用 = 持久化攻击风险 | 跨会话污染 |
| **内核级隔离** | microVM 提供独立内核（Kubernetes Pod 默认无） | 容器逃逸的最后防线 |

## LangSmith Sandboxes 设计

关键技术决策：
- **每个沙箱 = 独立 microVM**（专用内核 + 文件系统，非容器共享内核）
- **生命周期可控**：用完即毁，无状态残留
- **网络白名单**：仅允许预设 endpoint
- **Auth proxy**：凭据在沙箱外注入，不可信代码无直接访问凭证

这与 [[Anthropic-Agent安全容器化实践]] 中 Claude 的容器化方案理念一致但层次更低——microVM 提供比容器更强的隔离保证。

## 选型决策树

```
Agent 需要执行代码？
├── 否 → 无需沙箱
├── 是 → 是否处理不可信输入？
│   ├── 否 → Docker 容器（信任输入源）
│   ├── 是 → Lethal Trifecta 检查
│       ├── 三项不全满足 → Docker + 网络白名单 + 资源限制
│       └── 三项全满足 → microVM（Firecracker/gVisor）+ human-in-the-loop
```

## 与相关领域交叉

### 与 [[Anthropic-Agent安全容器化实践]] 的对比

| 维度 | LangSmith Sandboxes | Anthropic 容器化 |
|------|---------------------|-------------------|
| 隔离层 | microVM（独立内核） | 容器（共享内核） + policy |
| 生命周期 | 用完即毁 | 持久化但是受限 |
| 网络 | 白名单 | 多层代理控制 |
| 凭证管理 | 外部注入 | 沙箱内 MCP 限制 |

两种方案不是排他的——**microVM 是硬防线，容器 + policy 是软防线，两者可叠用**。

### 在 [[Custom-Agent-Harness-Middleware架构]] 中的位置

Sandbox 是 Harness 的 Security Middleware 层的核心模块——工具调用前注入沙箱环境，调用后销毁沙箱清理残留。整个生命周期由 Middleware 管理，Agent 自身无感知。

### 在 [[Agent-First-Data-Systems]] 中的角色

Agent-First 架构中，Agent 直接与数据系统交互。Sandbox 是数据访问的最后一道防线——防止 Agent 在不可信输入下执行危险的数据操作。

## 工程要点

1. **microVM vs 容器不是二选一**：微信任环境用容器，高威胁环境用 microVM，成本差异 ~10x
2. **Auth proxy 的位置很关键**：凭证在沙箱外 → 沙箱内代码永远拿不到真实 key
3. **生命周期策略影响安全基线**：复用沙箱 = 允许攻击者在多次调用间累积状态
4. **网络白名单细化到 endpoint 级别**：不要只开 domain，要精确到 path + method
