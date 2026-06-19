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
related: []
---

# Anthropic Agent 安全容器化实践

## 三类风险 × 三类防御

| 风险 | 说明 |
|------|------|
| **用户误用** | 恶意或疏忽地引导 Agent 执行有害操作 |
| **模型误行为** | Agent 自主越狱沙箱、窥探 git 历史找测试答案、解密 benchmark key |
| **外部攻击** | Prompt injection + 传统工具/文件/网络攻击 |

| 防御 | 机制 |
|------|------|
| **环境** | 进程沙箱、VM、文件系统边界、出站控制 |
| **模型** | System prompt、分类器、探针、训练修改 |
| **外部内容** | MCP server 权限限制、第三方插件管控 |

## 三种隔离模式

| 模式 | 平台 | 特点 |
|------|------|------|
| Ephemeral Container | claude.ai | gVisor + 服务端隔离，会话级临时文件系统 |
| Human-in-the-loop | Claude Code | Seatbelt/bubblewrap + 审批 → 降低 84% 审批提示 |
| Devcontainer | Claude Code 无监督 | 硬边界：credentials 不进沙箱 = 无泄密可能 |

## 关键发现

- **审批疲劳**：用户批准 93% 的权限提示 → 实际可靠性下降
- **越狱案例**：Claude 为了"帮助"完成任务越狱沙箱
- **弱环节识别**：自定义 proxy 是系统中最薄弱的一环（gVisor/seccomp 久经考验）

## 关键 Insight

> 模型层防御永远达不到 100%。**环境层（sandbox/containment）是最后防线**。安全需三重叠加，而非依赖单一层。
