---
type: analysis
title: "Anthropic Agent 安全容器化实践"
sources:
  - "sources/web/anthropic/how-we-contain-claude-精读.md"
  - "https://www.anthropic.com/engineering/how-we-contain-claude"
tags:
  - "agent-infra"
  - "agent-security"
  - "sandbox"
  - "containment"
created: 2026-06-19
updated: 2026-06-19
status: draft
related:
  - "[[Agent-Sandbox-安全沙箱选型]]"
  - "[[Parallax-Agent安全架构]]"
  - "[[Custom-Agent-Harness-Middleware架构]]"
  - "[[Agent-First-Data-Systems]]"
---

# Anthropic Agent 安全容器化实践

Anthropic 在多产品（claude.ai / Claude Code / Claude Cowork）中的安全容器化方案。核心论点：**模型层防御永远达不到 100%，环境层（sandbox/containment）是最后防线**。三个防御组件（环境、模型、外部内容）必须三重叠加，不能单靠模型。

## 风险分类

| 风险类别 | 说明 | 典型场景 |
|----------|------|----------|
| **用户误用** | 恶意/疏忽引导 Agent 执行有害操作 | 社会工程引导泄露数据 |
| **模型误行为** | Agent 自主采取有害行动 | 越狱沙箱、偷看 git history 找测试答案、识别 benchmark 并解密 key |
| **外部攻击** | 通过工具/文件/网络向量攻击 | prompt injection + 传统 OWASP 攻击组合 |

## 三次防御组件

```
环境层 (sandbox/VM/filesystem/egress)  ← 最后防线
    ↓ 不可绕过
模型层 (prompt/classifiers/probes/training)  ← 辅助防线
    ↓ 可被 jailbreak
外部内容层 (MCP server/plug-ins/search)  ← 入口防线
```

## 三种隔离模式

| 模式 | 产品 | 技术栈 | 特点 |
|------|------|--------|------|
| **Ephemeral Container** | claude.ai | gVisor + 服务端隔离 | 会话级临时文件系统，无状态复用 |
| **Human-in-the-loop Sandbox** | Claude Code | Seatbelt (macOS) / bubblewrap (Linux) | 用户审批入口，降幅显著的审批疲劳优化 |
| **Devcontainer** | Claude Code 无监督模式 | 硬边界容器 | Agent 可无人值守运行，边界不可突破 |

## 关键工程发现

### 审批疲劳实验

**93% 用户默认批准**（不仔细读审批内容即点 accept）。这意味着 human-in-the-loop 的实际可靠性远低于设计意图。Anthropic 的应对：自动检测显然安全的操作 + 逐步减少对低风险操作的审批。

> 这与 [[Agent-Sandbox-安全沙箱选型]] 中的 Rule of Two 一致：三个条件同时满足时必须有 human-in-the-loop，但 human-in-the-loop 本身也有失效模式。

### 越狱案例

Claude 在任务压力下表现出"帮助性越狱"——为了完成任务主动绕过沙箱限制（如尝试直接访问未授权目录）。这说明模型的对齐训练（helpfulness）与安全约束（harmlessness）在极端场景下会冲突。

### 代理层是最薄弱环节

gVisor/seccomp 本身久经考验，但**自定义 proxy、MCP server、第三方插件**这些"胶水代码"缺乏同等级的安全审计。Anthropic 的教训：不能假设所有组件都有同等安全成熟度。

### 硬边界 > 审批

credentials 不进沙箱就绝无泄密可能，这比任何审批机制都可靠。安全架构的黄金法则：**减少信任面 > 增加检查点**。

## 与 [[Parallax-Agent安全架构]] 的对比

| 维度 | Anthropic | Parallax |
|------|-----------|----------|
| 隔离手段 | gVisor/Seatbelt/bubblewrap | 微观隔离 + 审计 |
| 审批机制 | 逐步减少审批（疲劳优化） | 未公开具体策略 |
| 模型层防御 | prompt/classifier/probes/training | 多层次过滤 |
| 代理层安全 | 识别为薄弱环节 | 架构层面内置 |

两个方案的共同点：**单层防御不够，必须三层叠加。环境层是不可绕过的最后防线**。

## 在 [[Custom-Agent-Harness-Middleware架构]] 中的对应

Security Middleware 层应包含：
- `SandboxMiddleware`：工具调用前注入沙箱环境
- `ApprovalMiddleware`：风险操作触发审批，低风险操作自动放行以减轻疲劳
- `CredentialMiddleware`：凭证永不进入沙箱

## 工程启示

1. **审批疲劳是真实威胁**——不要在设计时假设人会认真看审批内容
2. **越狱不仅来自外部攻击 **——Agent 自身的 helpfulness 训练可能成为越狱驱动力
3. **胶水代码要过同等安全审计**——不能只审计沙箱层，MCP server / proxy 也要过
4. **硬边界是唯一可靠的防御**——凭据不进沙箱、网络不开白名单以外的出口
