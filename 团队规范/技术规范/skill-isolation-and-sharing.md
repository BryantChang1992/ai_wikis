---
title: Skill 隔离与共享机制
status: proposal
version: v0.1
created: 2026-06-06
tags:
  - skill
  - agent-infra
  - 权限
  - CHANG_AI_TEAM
---

# Skill 隔离与共享机制

> [!note] 背景
> OpenClaw skills 目前对全部 Agent 开放，没有任何限制。现在需要设计一套 Skill 隔离与共享规则，确保每个 Agent 只能使用其角色职责范围内的 Skill。

---

## 1. 问题诊断

### 1.1 现状

| 现状 | 问题 |
|------|------|
| 所有 Agent 无限制访问全部 Skill | CFO 可以用 `baoyu-post-to-x`（发推）——不应该 |
| 无 Skill 分类/分组 | CTO 不知道哪些 Skill 该给谁 |
| 执行层 Worker 能调发布类 Skill | RD 不应该能执行 `baoyu-post-to-wechat` |
| 无 Skill 使用审计 | 不知道谁用了什么 Skill |

### 1.2 OpenClaw 已有的机制（利用好，不重复造）

| 机制 | 说明 |
|------|------|
| **路径分层** | `~/.agents/skills`（个人级）vs `~/.openclaw/skills`（托管级）vs `<workspace>/skills`（Workspace 级），同名 Skill 高 precedence 覆盖 |
| **Agent allowlist** | `agents.defaults.skills` 定义默认 Skill 集，`agents.list[].skills` 做按 Agent 精确控制 |
| **Environment conditions** | Skill 可以声明 `requires.env` 或 `requires.binaries`，条件不满足时自动隐藏 |

### 1.3 核心原则

1. **最小权限**：Agent 只能拿到完成职责所必需的 Skill
2. **按层级分组**：不同层级有不同的 Skill 集，不搞每 Agent 逐一配置
3. **利用原生机制**：技能隔离靠 OpenClaw 的 `agents.list[].skills`，不另造权限系统
4. **可审计**：每次 Skill 调用记录到 `tool_calls` 表

---

## 2. Skill 分类

### 2.1 按功能分类

| 类别 | Skill 列表 | 用途 | 风险 |
|------|-----------|------|------|
| **通用工具** | `web_search`, `web_fetch`, `read`, `write`, `edit`, `exec`, `process`, `memory_search`, `memory_get`, `canvas`, `session_status` | 所有 Agent 的基本工具 | 低 |
| **知识管理** | `obsidian`, `skill-creator`, `github`, `gh-issues`, `taskflow`, `taskflow-inbox-triage`, `clawhub`, `release-skills` | 知识沉淀、发布、管理 | 低-中 |
| **内容发布** | `baoyu-post-to-x`, `baoyu-post-to-wechat`, `baoyu-post-to-weibo` | 对外发布内容 | 高 |
| **内容创作** | `baoyu-article-illustrator`, `baoyu-comic`, `baoyu-cover-image`, `baoyu-diagram`, `baoyu-image-gen`, `baoyu-infographic`, `baoyu-slide-deck`, `baoyu-xhs-images` | 生成视觉/文档内容 | 中 |
| **内容处理** | `baoyu-compress-image`, `baoyu-format-markdown`, `baoyu-markdown-to-html`, `baoyu-electron-extract`, `baoyu-translate`, `baoyu-youtube-transcript`, `baoyu-danger-gemini-web`, `baoyu-danger-x-to-markdown`, `baoyu-wechat-summary`, `baoyu-url-to-markdown` | 格式转换、提取、翻译 | 低-中 |
| **基础设施** | `node-connect`, `healthcheck`, `feishu-*`, `wecom-*`, `qqbot-*`, `weather` | 运维、通讯、基础设施 | 低-中 |
| **娱乐/个人** | `apple-notes`, `apple-reminders`, `things-mac`, `openhue`, `spotify-player`, `goplaces`, `sonoscli`, `songsee`, `camsnap`, `gifgrep` | 个人助手功能 | 低 |

### 2.2 按风险等级分类

```
P0 · 高权限 Skill（影响团队外部声誉或基础设施）：
    ├── 内容发布类：baoyu-post-to-x, baoyu-post-to-wechat, baoyu-post-to-weibo
    ├── 仓库操作类：github, gh-issues -> push/PR 必须审慎
    └── 通讯类：feishu-*, wecom-*, qqbot-* -> 误发消息影响团队

P1 · 中权限 Skill（影响团队内部产出）：
    ├── 内容创作类：baoyu-comic, baoyu-diagram, baoyu-image-gen ...
    ├── 知识管理类：obsidian, skill-creator, release-skills
    └── 基础设施类：node-connect, healthcheck

P2 · 低权限 Skill（日常工具，无副作用）：
    ├── 通用工具：web_search, read, write, edit, exec
    ├── 内容处理：baoyu-translate, baoyu-format-markdown ...
    └── 个人娱乐：spotify-player, weather ...
```

---

## 3. 按层级的 Skill 分配方案

### 3.1 分配矩阵

| 层级 | 角色示例 | 通用工具 | 内容处理 | 内容创作 | 知识管理 | 基础设施 | 内容发布 | 娱乐 |
|------|---------|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **CEO** | Frank | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ |
| **VP** | CTO, CPO, CFO, COO | ✅ | ✅ | 🔶 审批 | ✅ | ✅ | 🔶 审批 | ❌ |
| **专家** | expert-infra/perf/sre | ✅ | ✅ | ❌ | 🔶 受限 | ✅ | ❌ | ❌ |
| **执行层** | RD, SRE, QA | ✅ | 🔶 受限 | ❌ | ❌ | ❌ | ❌ | ❌ |

### 3.2 详细规则

#### CEO（全部放开，除娱乐）
```
CEO 需要：
- 对外发布（发推、发公众号）→ 需要内容发布 Skill
- 审查团队产出 → 需要内容创作 Skill 预览
- 直接操作仓库 → 全量 git 权限
- 排除：个人娱乐类（不需要）
```

#### VP 层（CTO/CPO/CFO/COO）
```
VP 层需要：
- 技术决策和方案评估 → 通用工具 + 知识管理
- 审查/批准内容发布 → 内容发布类按"审批模式"（见 §3.4）
- 生成技术图表/幻灯片 → 内容创作（但发布型需审批）
- 管理知识库 → obsidian, github
- 排除：个人娱乐类
```

#### 专家层（Infra/Perf/SRE）
```
专家需要：
- 技术调研、设计文档 → 通用工具 + 内容处理
- 生成图表 → baoyu-diagram（但不涉及发布）
- 有限的仓库操作 → github read-only
- 排除：内容发布、内容创作（除 diagram）、个人娱乐
```

#### 执行层（RD/SRE/QA）
```
执行层需要：
- 实现代码、调试 → 通用工具
- 基础格式转换 → baoyu-translate, baoyu-format-markdown
- 排除：发布、创作、知识管理、基础设施
```

### 3.3 OpenClaw 配置

```json5
{
  agents: {
    defaults: {
      // 最小集：通用工具 + 基础内容处理
      skills: [
        // 通用工具（OpenClaw 内置，不需显式列但建议保留）
        "web_search", "web_fetch",
        "read", "write", "edit", "exec",
        "memory_search", "memory_get",
        "session_status", "canvas",
        // 基础内容处理
        "baoyu-format-markdown",
        "baoyu-translate",
      ],
    },
    list: [
      // CEO — 全量（除娱乐）
      {
        id: "main",
        skills: [
          "web_search", "web_fetch", "read", "write", "edit", "exec",
          "memory_search", "memory_get", "session_status", "canvas",
          "obsidian", "taskflow", "taskflow-inbox-triage", "skill-creator", "clawhub",
          "github", "gh-issues",
          "baoyu-article-illustrator", "baoyu-comic", "baoyu-cover-image",
          "baoyu-diagram", "baoyu-image-gen", "baoyu-infographic",
          "baoyu-slide-deck", "baoyu-xhs-images",
          "baoyu-format-markdown", "baoyu-markdown-to-html",
          "baoyu-electron-extract", "baoyu-translate",
          "baoyu-youtube-transcript", "baoyu-danger-gemini-web",
          "baoyu-danger-x-to-markdown", "baoyu-wechat-summary",
          "baoyu-compress-image",
          "baoyu-post-to-x", "baoyu-post-to-wechat", "baoyu-post-to-weibo",
          "baoyu-url-to-markdown", "release-skills",
          "node-connect", "healthcheck", "weather",
          "feishu-doc", "feishu-drive", "feishu-wiki", "feishu-perm",
          "feishu-task", "feishu-calendar", "feishu-bitable",
          "feishu-channel-rules", "feishu-create-doc",
          "feishu-fetch-doc", "feishu-update-doc",
          "feishu-im-read", "feishu-troubleshoot",
          "wecom-msg", "wecom-contact-lookup", "wecom-preflight",
          "wecom-schedule", "wecom-meeting-create", "wecom-meeting-manage",
          "wecom-meeting-query", "wecom-edit-todo",
          "wecom-get-todo-list", "wecom-get-todo-detail",
          "wecom-smartsheet-data", "wecom-smartsheet-schema",
          "wecom-doc-manager",
          "qqbot-channel", "qqbot-media", "qqbot-remind",
          "coding-agent", "browser-automation",
        ],
      },

      // CTO — VP 层标准
      {
        id: "cto-agent",
        skills: [
          // 通用工具
          "web_search", "web_fetch", "read", "write", "edit", "exec",
          "memory_search", "memory_get", "session_status", "canvas",
          // 知识管理
          "obsidian", "skill-creator", "github", "gh-issues",
          "taskflow", "taskflow-inbox-triage", "clawhub", "release-skills",
          // 内容创作
          "baoyu-diagram", "baoyu-image-gen", "baoyu-infographic",
          "baoyu-cover-image", "baoyu-slide-deck",
          // 内容处理
          "baoyu-format-markdown", "baoyu-markdown-to-html",
          "baoyu-translate", "baoyu-compress-image",
          "baoyu-youtube-transcript", "baoyu-danger-gemini-web",
          "baoyu-danger-x-to-markdown", "baoyu-wechat-summary",
          "baoyu-url-to-markdown",
          // 基础设施
          "node-connect", "healthcheck", "weather",
          "feishu-doc", "feishu-drive", "feishu-wiki", "feishu-perm",
          "feishu-task", "feishu-bitable",
          "feishu-channel-rules", "feishu-create-doc",
          "feishu-fetch-doc", "feishu-update-doc",
          "feishu-im-read", "feishu-troubleshoot",
          "qqbot-channel", "qqbot-media", "qqbot-remind",
          "coding-agent", "browser-automation",
          // VP 审批模式：内容发布类（限审阅，不直接发）
          "baoyu-post-to-x",
          "baoyu-post-to-wechat",
          "baoyu-post-to-weibo",
        ],
      },

      // CPO — 内容/产品 VP（需要内容创作全量，加内容发布审批权）
      {
        id: "cpo-agent",
        skills: [
          "web_search", "web_fetch", "read", "write", "edit", "exec",
          "memory_search", "memory_get", "session_status", "canvas",
          "obsidian", "skill-creator", "github", "gh-issues",
          "taskflow", "taskflow-inbox-triage", "clawhub", "release-skills",
          "baoyu-article-illustrator", "baoyu-comic", "baoyu-cover-image",
          "baoyu-diagram", "baoyu-image-gen", "baoyu-infographic",
          "baoyu-slide-deck", "baoyu-xhs-images",
          "baoyu-format-markdown", "baoyu-markdown-to-html",
          "baoyu-translate", "baoyu-compress-image",
          "baoyu-youtube-transcript", "baoyu-danger-gemini-web",
          "baoyu-danger-x-to-markdown", "baoyu-wechat-summary",
          "baoyu-url-to-markdown", "baoyu-electron-extract",
          "baoyu-post-to-x", "baoyu-post-to-wechat", "baoyu-post-to-weibo",
          "node-connect", "healthcheck", "weather",
          "feishu-doc", "feishu-drive", "feishu-wiki", "feishu-perm",
          "qqbot-channel", "qqbot-media",
          "coding-agent", "browser-automation",
        ],
      },

      // CFO — 财务 VP（核心工具 + 知识管理，无内容创作/发布）
      {
        id: "cfo-agent",
        skills: [
          "web_search", "web_fetch", "read", "write", "edit", "exec",
          "memory_search", "memory_get", "session_status", "canvas",
          "obsidian", "skill-creator", "github", "gh-issues",
          "taskflow", "taskflow-inbox-triage",
          "baoyu-format-markdown", "baoyu-markdown-to-html",
          "baoyu-translate", "baoyu-compress-image",
          "baoyu-youtube-transcript", "baoyu-url-to-markdown",
          "feishu-doc", "feishu-wiki",
          "coding-agent", "browser-automation",
        ],
      },

      // COO — 运营 VP（核心工具 + 通讯类 + 有限内容创作）
      {
        id: "coo-agent",
        skills: [
          "web_search", "web_fetch", "read", "write", "edit", "exec",
          "memory_search", "memory_get", "session_status", "canvas",
          "obsidian", "skill-creator", "github", "gh-issues",
          "taskflow", "taskflow-inbox-triage", "clawhub",
          "baoyu-diagram", "baoyu-image-gen", "baoyu-cover-image",
          "baoyu-format-markdown", "baoyu-markdown-to-html",
          "baoyu-translate", "baoyu-compress-image",
          "baoyu-url-to-markdown",
          "node-connect", "healthcheck", "weather",
          "feishu-doc", "feishu-drive", "feishu-wiki",
          "feishu-task", "feishu-calendar", "feishu-bitable",
          "feishu-create-doc", "feishu-fetch-doc", "feishu-update-doc",
          "feishu-im-read", "feishu-troubleshoot",
          "wecom-msg", "wecom-contact-lookup", "wecom-preflight",
          "wecom-schedule", "wecom-meeting-create", "wecom-meeting-manage",
          "wecom-meeting-query", "wecom-edit-todo",
          "wecom-get-todo-list", "wecom-get-todo-detail",
          "wecom-doc-manager",
          "qqbot-channel", "qqbot-media", "qqbot-remind",
          "coding-agent", "browser-automation",
        ],
      },
    ],
  },
}
```

### 3.4 "审批模式"：VP 层使用内容发布 Skill 的约束

VP 层可以调用内容发布 Skill（如 `baoyu-post-to-x`），但有语义约束——VP 不应该在没有 CEO 审批的情况下自己发。这个约束无法通过 OpenClaw 原生机制实现（原生机制只有 allow/deny 二分），有两种实现路径：

#### 方案 A：利用 Skill 自身约束（推荐 MVP）
在 VP 的 AGENTS.md / SOUL.md 中写入规则：
```markdown
## 内容发布规则
- 对外发布（X/公众号/微博）必须先得到 CEO 确认
- 你只能生成发布内容草稿，不能直接发布
- 如果 CEO 明确说"发"，你才能调 baoyu-post-to-x
```
✅ 简单，不依赖额外基础设施
❌ 依赖 prompt 遵守度，Agent 可能出错

#### 方案 B：Skill 内嵌审批流程（进阶）
在 `baoyu-post-to-x` 的 SKILL.md 中增加检查步骤：
```markdown
## 发布前检查
1. 检查调用者身份：如果是 VP 层（非 CEO），必须检查
   CEO 是否在上下文中明确授权"可以发"
2. 如果没有授权，输出草稿并询问："请 CEO 确认发布"
3. CEO 确认后，再次调用执行发布
```
✅ 强制流程，Agent 不太可能跳过
❌ 需要修改 Skill 自身，提高维护成本

**建议：** Phase 1 用方案 A（prompt 约束），Phase 2 用方案 B（Skill 内嵌）。

---

## 4. Skill 使用审计

### 4.1 tool_calls 表已覆盖

Skill 调用本质上是通过工具调用触发的（在 OpenClaw 中，Skill 是工具的"使用说明书"），因此从 `tool_calls` 表可以间接追溯：

```sql
-- 审计 Skill 使用情况
SELECT
    a.id as agent_id,
    a.role,
    tc.tool_name,
    COUNT(*) as call_count,
    SUM(tc.token_cost) as est_token_cost
FROM tool_calls tc
JOIN sessions s ON tc.session_id = s.id
JOIN agents a ON s.agent_id = a.id
WHERE tc.created_at >= datetime('now', '-7 days')
  AND tc.tool_name IN (
    'read',           -- 可能在调用 Skill 说明
    'feishu_doc',     -- feishu 系列
    'feishu_wiki',
    'message'         -- 发布消息（含 Skill 指导的发布）
  )
GROUP BY a.id, tc.tool_name
ORDER BY call_count DESC;
```

### 4.2 可观测性视图新增：Skill 使用面板

在 Dashboard 运营视图（View 2）中增加：

```
🔧 Skill 使用分布 (本周)
┌────────────────────────────────────────────┐
│ baoyu-diagram         ████████ 32次   CTO │
│ baoyu-format-markdown  ██████  24次   全员 │
│ github                ████    18次   CTO │
│ feishu-doc            ███     12次   COO │
│ baoyu-post-to-x       ██       6次   CEO │
└────────────────────────────────────────────┘
```

---

## 5. 专家层 / 执行层的 Skill 需求场景分析

### 5.1 什么时候专家需要"越权"Skill？

| 场景 | 需要的 Skill | 当前规则 | 方案 |
|------|-------------|---------|------|
| 专家需要生成架构图 | `baoyu-diagram` | 禁止 | 加入专家 Skill 集 |
| 专家需要翻译技术文档 | `baoyu-translate` | 允许 | 已在默认集 |
| 专家需要格式化输出 | `baoyu-format-markdown` | 允许 | 已在默认集 |
| RD 需要发飞书通知 | `feishu-msg` | 禁止 | 通过 CTO 转发 |
| RD 需要提交代码 | `github` | 禁止 | 通过 CTO 提交 |

### 5.2 专家层 Skill 集的例外规则

```markdown
## 专家层 Skill 例外规则

如果任务需要 Skill 不在专家 Skill 集中：
1. 专家向 CTO 申请："任务需要 X Skill，因为 Y"
2. CTO 决定：
   a. 临时授权（单次）→ 专家在 spawn 子 agent 时用 sessions_send 请 CTO 执行该步骤
   b. 永久加入 → CTO 修改配置
3. 不允许专家自行绕过限制
```

---

## 6. 实施路径

| 步骤 | 动作 | 优先级 |
|------|------|--------|
| 1 | 按 §3.3 配置 OpenClaw `agents.list[].skills` | 🔴 P0 |
| 2 | 各 VP 的 AGENTS.md 写入 Skill 使用约束规则 | 🟡 P1 |
| 3 | Dashboard View 2 增加 Skill 使用面板 | 🟢 P2 |
| 4 | tool_calls 表增加 skill_name 字段（或通过正则关联） | 🟢 P2 |
| 5 | 发布 Skill 审批流程 Skill 内嵌 | 🔵 P3 |

---

## 7. 附录：Skill 列表完整分类

### 通用工具（全部赋予）
```
web_search, web_fetch, read, write, edit, exec, process,
memory_search, memory_get, canvas, session_status, browser
```

### 内容处理（全部赋予）
```
baoyu-format-markdown, baoyu-markdown-to-html, baoyu-translate,
baoyu-compress-image, baoyu-youtube-transcript, baoyu-danger-gemini-web,
baoyu-danger-x-to-markdown, baoyu-wechat-summary, baoyu-url-to-markdown,
baoyu-electron-extract
```

### 内容创作（VP+ 可用）
```
baoyu-article-illustrator, baoyu-comic, baoyu-cover-image,
baoyu-diagram, baoyu-image-gen, baoyu-infographic,
baoyu-slide-deck, baoyu-xhs-images
```

### 知识管理（VP+ 可用）
```
obsidian, skill-creator, github, gh-issues,
taskflow, taskflow-inbox-triage, clawhub, release-skills
```

### 基础设施（VP+ 可用，专家层受限）
```
node-connect, healthcheck, weather,
coding-agent, browser-automation
```

### 通讯类（VP+ 可用，按角色分配）
```
feishu-doc, feishu-drive, feishu-wiki, feishu-perm,
feishu-task, feishu-calendar, feishu-bitable,
feishu-channel-rules, feishu-create-doc,
feishu-fetch-doc, feishu-update-doc,
feishu-im-read, feishu-troubleshoot,
wecom-*, qqbot-*
```

### 内容发布（CEO 全量，VP 审批模式）
```
baoyu-post-to-x, baoyu-post-to-wechat, baoyu-post-to-weibo
```

### 娱乐/个人（不赋予，CEO 除外可选）
```
apple-notes, apple-reminders, things-mac, openhue,
spotify-player, goplaces, sonoscli, songsee, camsnap, gifgrep
```

---

## 相关链接

- [[../项目文档/agent基础设施可观测性平台/设计文档]] — 五维度框架 + 权限矩阵
- [[../项目文档/agent基础设施可观测性平台/observability-deep-design]] — 可观测性深度设计（Skill 审计面板）
- [[../../agent核心文件/cto/AGENTS]] — CTO 现有权限定义
- [OpenClaw Skills 文档](https://docs.openclaw.ai/tools/skills) — 原生机制参考
