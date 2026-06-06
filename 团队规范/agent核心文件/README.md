---
category: 规范
tags:
  - agent-core
  - 团队规范
  - 角色定义
created: 2026-05-31
updated: 2026-06-06
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
├── ceo/                ← CEO Agent (Mike)
│   ├── AGENTS.md
│   ├── SOUL.md
│   ├── IDENTITY.md
│   ├── USER.md
│   └── MEMORY.md
├── cto/                ← CTO Agent
│   ├── AGENTS.md
│   ├── SOUL.md
│   ├── IDENTITY.md
│   ├── USER.md
│   └── MEMORY.md
├── pmo/                ← PMO Agent（向 CTO 汇报）
│   ├── AGENTS.md
│   ├── SOUL.md
│   └── MEMORY.md
├── rd/                 ← RD 专家（向 CTO 汇报）
│   ├── AGENTS.md
│   ├── SOUL.md
│   └── MEMORY.md
├── perf/               ← 性能专家（向 CTO 汇报）
│   ├── AGENTS.md
│   ├── SOUL.md
│   └── MEMORY.md
├── qa/                 ← QA 专家（向 CTO 汇报）
│   ├── AGENTS.md
│   ├── SOUL.md
│   └── MEMORY.md
├── sre/                ← SRE 专家（向 CTO 汇报）
│   ├── AGENTS.md
│   ├── SOUL.md
│   └── MEMORY.md
├── cfo/                ← CFO Agent
│   ├── AGENTS.md
│   ├── SOUL.md
│   ├── IDENTITY.md
│   ├── USER.md
│   └── MEMORY.md
├── coo/                ← COO Agent
│   ├── AGENTS.md
│   ├── SOUL.md
│   ├── IDENTITY.md
│   ├── USER.md
│   └── MEMORY.md
└── cpo/                ← CPO Agent
    ├── AGENTS.md
    ├── SOUL.md
    ├── IDENTITY.md
    ├── USER.md
    └── MEMORY.md
```

## Agent 清单

| Agent | 角色 | 层级 | 上级 | 状态 |
|-------|------|------|------|------|
| CEO (Mike) | 首席执行官 | CEO | — | Active |
| CTO | 首席技术官 | VP | CEO | Active |
| PMO | 项目管理办公室 | 专家层 | CTO | Active |
| RD 专家 | 架构与核心系统 | 专家层 | CTO | Active |
| 性能专家 | 性能优化 | 专家层 | CTO | Active |
| QA 专家 | 质量保障 | 专家层 | CTO | Active |
| SRE 专家 | 可靠性与部署 | 专家层 | CTO | Active |
| CFO | 首席财务官 | VP | CEO | Pending |
| COO | 首席运营官 | VP | CEO | Pending |
| CPO | 首席产品官 | VP | CEO | Pending |

## 技术团队组织架构

```
CEO (Mike)
 └── CTO ─── PMO (sessions_send)
      ├── RD 专家 ─── rd-worker (sessions_spawn)
      ├── 性能专家 ─── perf-worker (sessions_spawn)
      ├── QA 专家 ─── qa-worker (sessions_spawn)
      └── SRE 专家 ─── sre-worker (sessions_spawn)
```

## 相关链接

- [[仓库分工说明]]
- [[agent基础设施可观测性平台]]
