---
category: 规范
tags:
  - 团队核心规范
  - 治理
created: 2026-05-31
updated: 2026-06-08
---

# 团队核心规范

> [!important] 负责人
> **CEO (Mike)** + **CTO (Stark)** 共同负责修改。

## 适用范围

团队核心规范约束所有 Agent，是对 **CHANG_AI_TEAM 整体运作方式** 的定义，包括但不限于：

- Agent 组织架构与层级关系
- 角色定义与汇报关系
- 通信协议（spawn/send 使用规则）
- 任务状态机与生命周期
- 冷启动流程
- 仓库分工与 Git 操作规范
- 模型分配规则

## 组织架构

```
Bryant
  └── CEO (Mike) ← 全局决策 + 对外发布
        ├── CFO (Trinity) ← 财务/资源管理
        ├── COO (Neo) ← 运营/流程管理
        ├── CPO (Morpheus) ← 产品/技术方向
        └── CTO (Stark/我) ← 技术域全权
              └── Worker (临时, 按标签: rd/perf/qa/sre)
```

**常驻 Agent：CEO + CFO + COO + CPO + CTO（共 5 个 C 层，CXO 平级，均直接向 CEO 汇报）**，其余（PMO/专家层）通过 VP 层自由 `sessions_spawn` 按需创建。

**设计原则：上下文驱动。** 只有上下文真正不同的才拆分 Agent。VP 层通过 spawn 灵活扩展，不常驻。

## 与其他规范领域的关系

```
团队核心规范 ← 最高层级，所有 Agent 必须遵守
└── 技术规范  ← CTO 负责（Skill 隔离、技术选型、架构规范）
```

## 文件清单

- [[仓库分工说明]]
- [[agent核心文件/README]] — Agent 身份与权限定义
- [[通信协议规范]]
- [[冷启动流程]]
- [[知识管理规范]]
