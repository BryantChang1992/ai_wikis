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
related: []
---

# Agent Sandbox — 安全沙箱选型

## Lethal Trifecta（致死三要素）

由 Simon Willison 提出，三条件**同时满足**时 Agent 允许攻击者窃取数据：

1. **访问敏感数据**
2. **暴露于不可信内容**（用户输入、MCP server 响应、第三方 skills）
3. **能对外通信**

Meta 的 **"Rule of Two"**：三要素齐全时 Agent 不能完全自主运行。

## 安全 Sandbox 五要素

| 特性 | 说明 |
|------|------|
| **隔离文件系统** | 仅含所需数据，阻断越权访问 |
| **有限网络访问** | 只允许白名单端点 |
| **资源限制** | 控制 CPU/内存/时长 |
| **受控复用性** | 选择复用 = 持久化攻击风险，需权衡 |
| **内核级隔离** | microVM 提供独立内核（K8s 默认 Pod 无此隔离） |

## Sandbox 的定位

沙箱不消除 Trifecta 的任何要素，而是**缩小**每个要素的暴露面，使之缩到团队可以自信管理的规模。

## LangSmith Sandboxes 设计要点

- 每个沙箱 = 独立 microVM（专用内核 + 文件系统）
- 生命周期可控（创建→使用→销毁）
- Auth proxy：凭据在沙箱外注入，不可信代码无直接访问

## 关键 Insight

> Sandbox 不是安全的终点，是安全的支点——让 Lethal Trifecta 问题小到可解。
