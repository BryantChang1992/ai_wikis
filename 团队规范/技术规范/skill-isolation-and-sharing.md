---
title: Skill 隔离与共享机制
status: active
version: v0.5
created: 2026-06-06
updated: 2026-06-07
tags:
  - skill
  - 权限
  - CHANG_AI_TEAM
---

# Skill 隔离与共享机制

> [!note] 背景
> 团队架构精简为 **CEO + CTO + 临时 Worker** 三层。Skill 分配不再按人类公司职级（CFO/COO/CPO 等），而是按**上下文是否真正隔离**来分。

---

## 1. 架构与 Skill 分层

```
CEO (Mike) —— 全量 Skill，对外发布，向 Bryant 汇报
  └── CTO (Stark) —— 技术域全权 Skill，Spawn Worker，Wiki 管理
        └── Worker (临时) —— 最小集：通用工具 + 基础内容处理
```

| 层级 | 承担者 | Skill 数 | 上下文 |
|------|--------|:---:|------|
| 决策/发布层 | CEO | ~60 | 独立：全局决策、对外发布、Bryant 交互 |
| 技术执行层 | CTO | ~50 | 独立：技术全栈、Worker 编排、Wiki/Skill 管理 |
| 临时执行层 | Worker | ~15 | 独立：单任务单上下文，结束即销毁 |

---

## 2. Skill 分类（当前 126 个）

### 类 1：通用工具（14 个）—— 所有层级

`web_search` `web_fetch` `read` `write` `edit` `exec` `process` `browser` `canvas` `session_status` `memory_search` `memory_get` `sessions_spawn` `sessions_send`

> OpenClaw 内置，所有 Agent 默认可用

### 类 2：内容处理（14 个）

| Skill | CEO | CTO | Worker |
|-------|:---:|:---:|:---:|
| baoyu-format-markdown | ✅ | ✅ | ✅ |
| baoyu-translate | ✅ | ✅ | ✅ |
| baoyu-compress-image | ✅ | ✅ | — |
| summarize | ✅ | ✅ | — |
| baoyu-markdown-to-html | ✅ | ✅ | — |
| baoyu-youtube-transcript | ✅ | ✅ | — |
| baoyu-url-to-markdown | ✅ | ✅ | — |
| baoyu-danger-x-to-markdown | ✅ | ✅ | — |
| baoyu-wechat-summary | ✅ | ✅ | — |
| nano-pdf | ✅ | ✅ | — |
| video-frames | ✅ | ✅ | — |
| baoyu-danger-gemini-web | ✅ | ✅ | — |
| baoyu-electron-extract | ✅ | ✅ | — |
| openai-whisper / api | ✅ | ✅ | — |

### 类 3：内容创作（10 个）

| Skill | CEO | CTO | Worker |
|-------|:---:|:---:|:---:|
| baoyu-diagram | ✅ | ✅ | — |
| baoyu-image-gen | ✅ | ✅ | — |
| baoyu-infographic | ✅ | ✅ | — |
| baoyu-cover-image | ✅ | ✅ | — |
| baoyu-slide-deck | ✅ | ✅ | — |
| baoyu-comic | ✅ | — | — |
| baoyu-article-illustrator | ✅ | — | — |
| baoyu-xhs-images | ✅ | — | — |
| gemini | ✅ | ✅ | — |

### 类 4：内容发布（3 个）—— ⚠️ P0 仅 CEO

| Skill | CEO | CTO | Worker |
|-------|:---:|:---:|:---:|
| baoyu-post-to-x | ✅ | — | — |
| baoyu-post-to-wechat | ✅ | — | — |
| baoyu-post-to-weibo | ✅ | — | — |

### 类 5：知识管理（10 个）

| Skill | CEO | CTO | Worker |
|-------|:---:|:---:|:---:|
| obsidian | ✅ | ✅ | — |
| wiki-maintainer | ✅ | ✅ | — |
| obsidian-vault-maintainer | — | ✅ | — |
| taskflow | ✅ | ✅ | — |
| taskflow-inbox-triage | ✅ | ✅ | — |
| skill-creator | — | ✅ | — |
| clawhub | — | ✅ | — |
| release-skills | — | ✅ | — |
| github | ✅ | ✅ | — |
| gh-issues | ✅ | ✅ | — |

### 类 6：飞书生态（13 个）

| Skill | CEO | CTO | Worker |
|-------|:---:|:---:|:---:|
| feishu-doc | ✅ | ✅ | — |
| feishu-drive | ✅ | ✅ | — |
| feishu-wiki | ✅ | ✅ | — |
| feishu-perm | — | ✅ | — |
| feishu-bitable | ✅ | ✅ | — |
| feishu-task | ✅ | ✅ | — |
| feishu-calendar | ✅ | ✅ | — |
| feishu-create-doc | ✅ | ✅ | — |
| feishu-fetch-doc | ✅ | ✅ | — |
| feishu-update-doc | ✅ | ✅ | — |
| feishu-im-read | ✅ | ✅ | — |
| feishu-troubleshoot | — | ✅ | — |
| feishu-channel-rules | — | ✅ | — |

### 类 7：基础设施（12 个）

| Skill | CEO | CTO | Worker |
|-------|:---:|:---:|:---:|
| node-connect | — | ✅ | — |
| healthcheck | — | ✅ | — |
| browser-automation | ✅ | ✅ | — |
| diffs | — | ✅ | — |
| coding-agent | — | ✅ | — |
| model-usage | — | ✅ | — |
| session-logs | — | ✅ | — |
| weather | ✅ | ✅ | ✅ |
| sherpa-onnx-tts | ✅ | ✅ | — |
| tavily | — | ✅ | — |
| searxng | — | ✅ | — |
| prose | ✅ | ✅ | — |

### 类 8：企微 / QQ / 其他通讯（16 个）—— 未启用，暂不分配

企微 13 个 + QQ 3 个，全部不分配。Discord/Slack/iMessage 等 8 个也未启用。

### 类 9：未分配（34 个）—— 娱乐 / 个人 / Mac-only / 实验

不予分配。包含 spotify, sonos, apple-notes, self-improving-agent 等。

---

## 3. Worker 最小权限（硬编码于 openclaw.json）

```
通用工具 14 个（web_search, read, write, edit, exec, browser, canvas,
  memory_search, memory_get, session_status, process, sessions_spawn, sessions_send）
+ weather
+ baoyu-format-markdown
+ baoyu-translate
```

Worker **不应有**：内容创作、内容发布、知识管理、通讯操作、基础设施管理。

---

## 4. 实施状态

| Phase | 内容 | 状态 |
|-------|------|:---:|
| Phase 1 | 文档落地 + AGENTS.md 引用 | ✅ 已完成 |
| Phase 2 | Worker skills 白名单（openclaw.json） | ✅ 已配置 |
| Phase 3 | CEO/CTO skills 白名单（openclaw.json） | ⏳ 按需（当前全量开放够用） |

---

## 5. 修订记录

| 版本 | 日期 | 内容 |
|------|------|------|
| v0.1 | 2026-06-06 | 初版，80 Skill + 旧组织架构 |
| v0.2 | 2026-06-06 | OpenClaw 配置示例 |
| v0.3 | 2026-06-06 | 权限矩阵 + 实施计划 |
| v0.4 | 2026-06-07 | 对齐 10 Agent 架构，126 Skill 矩阵 |
| v0.5 | 2026-06-07 | 精简为 CEO + CTO + Worker 三层，移除 CFO/COO/CPO/PMO/专家 |
