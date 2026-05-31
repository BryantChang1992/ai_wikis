---
category: 规范
tags:
  - agent-core
  - 团队规范
  - 角色定义
created: 2026-05-31
updated: 2026-05-31
---

# Agent 核心文件

> [!important] 用途
> 收录 CHANG_AI_TEAM 各 Agent 的核心配置文件（AGENTS.md、SOUL.md、IDENTITY.md 等），
> 统一存放在 Obsidian 中，方便团队成员和 Frank review。

## 同步规则

- **源文件**：各 Agent 工作区（`/home/admin/.openclaw/workspace/agents/<role>/`）
- **此处**：团队规范的镜像副本，供 review 和历史追溯
- **更新时机**：任何 Agent 核心文件变更后，必须同步更新此处
- **操作方式**：Agent 自行将源文件复制到对应目录并提交 Git

## 目录结构

```
agent核心文件/
├── README.md           ← 本文件
├── cto/                ← CTO Agent
│   ├── AGENTS.md
│   ├── SOUL.md
│   ├── IDENTITY.md
│   └── USER.md
├── cfo/                ← CFO Agent
│   ├── AGENTS.md
│   ├── SOUL.md
│   ├── IDENTITY.md
│   └── USER.md
├── coo/                ← COO Agent
│   ├── AGENTS.md
│   ├── SOUL.md
│   ├── IDENTITY.md
│   └── USER.md
└── cpo/                ← CPO Agent
    ├── AGENTS.md
    ├── SOUL.md
    ├── IDENTITY.md
    └── USER.md
```

## Agent 清单

| Agent | 角色 | 层级 | 状态 |
|-------|------|------|------|
| CTO | 首席技术官 | VP | Active |
| CFO | 首席财务官 | VP | Pending |
| COO | 首席运营官 | VP | Pending |
| CPO | 首席产品官 | VP | Pending |

## 相关链接

- [[仓库分工说明]]
- [[agent基础设施可观测性平台]]
