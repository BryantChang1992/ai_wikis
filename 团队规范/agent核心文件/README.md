---
category: 规范
tags:
  - agent-core
  - 团队规范
  - 角色定义
created: 2026-05-31
updated: 2026-06-08
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
│   └── IDENTITY.md
├── cfo/                ← CFO Agent (Trinity)
│   ├── AGENTS.md
│   ├── SOUL.md
│   └── IDENTITY.md
├── coo/                ← COO Agent (Neo)
│   ├── AGENTS.md
│   ├── SOUL.md
│   └── IDENTITY.md
├── cpo/                ← CPO Agent (Morpheus)
│   ├── AGENTS.md
│   ├── SOUL.md
│   └── IDENTITY.md
└── cto/                ← CTO Agent (Stark)
    ├── AGENTS.md
    ├── SOUL.md
    └── IDENTITY.md
```

## Agent 清单

| Agent | 角色 | 职责 | 上级 | 状态 |
|-------|------|------|------|------|
| CEO (Mike) | 首席执行官 | 全局决策、对外发布、向 Bryant 汇报 | Bryant | Active |
| CFO (Trinity) | 首席财务官 | 财务规划、资源分配、成本审计 | CEO | Active |
| COO (Neo) | 首席运营官 | 运营管理、任务调度、效能分析 | CEO | Active |
| CPO (Morpheus) | 首席产品官 | 产品方向、技术产品化、CTO 上级 | CEO | Active |
| CTO (Stark) | 首席技术官 | 技术决策、任务执行、Wiki/Skill 管理 | CPO | Active |

## 组织架构

```
Bryant
  └── CEO (Mike) ← 全局决策 + 对外发布
        ├── CFO (Trinity) ← 财务/资源管理
        ├── COO (Neo) ← 运营/流程管理
        ├── CPO (Morpheus) ← 产品/技术方向
        └── CTO (Stark) ← 技术域全权
              └── Worker (临时, 按标签: rd/perf/qa/sre)
```

## 设计原则

1. **上下文隔离驱动架构**：只有上下文真正不同的才拆 Agent
2. **C 层 (CXO)** 是常驻层级，平级，均直接向 CEO 汇报
3. **Worker** 是临时进程，任务结束即销毁，不保留状态
4. **PMO/专家层** 通过 CXO 自由 `sessions_spawn`，不再常驻

## 相关链接

- [[skill-isolation-and-sharing]] — Skill 权限分配矩阵
- [[仓库分工说明]] — 仓库操作规范
- [[agent基础设施可观测性平台]] — 活跃项目
