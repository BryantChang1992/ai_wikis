---
title: Skill 隔离与共享机制
status: proposal
version: v0.4
created: 2026-06-06
updated: 2026-06-07
tags:
  - skill
  - agent-infra
  - 权限
  - CHANG_AI_TEAM
---

# Skill 隔离与共享机制

> [!note] 背景
> OpenClaw skills 目前对全部 Agent 开放，没有任何限制。需要设计一套 Skill 隔离与共享规则，确保每个 Agent 只使用其角色职责范围内的 Skill。

---

## 1. 问题诊断

### 1.1 现状

| 现状 | 问题 |
|------|------|
| 126 个 Skill 对所有 Agent 无限制开放 | Agent 可以用职权范围外的 Skill |
| 无 Skill 分类 / 分组 | 不知道哪些 Skill 该给谁 |
| Worker 能调发布类 Skill | RD Worker 不应该能执行 `baoyu-post-to-x` |
| 无 Skill 使用审计 | 不知道谁用了什么 Skill |

### 1.2 核心原则

1. **最小权限**：Agent 只能拿到完成职责所必需的 Skill
2. **按层级分组**：不同层级有不同 Skill 集，不搞每 Agent 逐一定制
3. **利用原生机制**：技能隔离靠 OpenClaw 的 `agents.list[].skills`，不另造权限系统
4. **可审计**：每次 Skill 调用记录到 `tool_calls` 表

---

## 2. 团队组织架构（当前）

![组织架构图](https://raw.githubusercontent.com/BryantChang1992/ai_wikis/master/%E5%9B%A2%E9%98%9F%E8%A7%84%E8%8C%83/assets/org-chart.png)

```
层级关系：

  CEO (Mike)
  ├── CTO ───┬── PMO ─── (pmo-worker)*
  │          ├── RD 专家 ─── rd-worker
  │          ├── 性能专家 ─── perf-worker
  │          ├── QA 专家 ─── qa-worker
  │          └── SRE 专家 ─── sre-worker
  ├── CPO
  ├── CFO
  └── COO

  * PMO 可 spawn worker，但通常通过专家层委派任务
```

| 层级 | 成员 | 通信方式 |
|------|------|----------|
| **C 层** | CEO → VP(CTO/CPO/CFO/COO) | `sessions_send` |
| **VP 层** | CTO/CPO/CFO/COO ↔ 同级 | `sessions_send` |
| **专家层** | PMO/RD/Perf/QA/SRE | `sessions_send`（收）/ `sessions_spawn`（发 worker） |
| **执行层** | worker（临时） | 由专家 `sessions_spawn` 创建 |

---

## 3. Skill 分类（当前 126 个）

### 3.1 分类一览

| 类别 | 数量 | 风险 | 说明 |
|------|:---:|:---:|------|
| 🛠️ 通用工具 | 14 | P2 | web_search, read, write, exec 等（OpenClaw 内置） |
| 📝 内容处理 | 14 | P2 | 翻译、格式化、URL 提取等 |
| 🎨 内容创作 | 10 | P1 | 图表、生图、幻灯片、封面等 |
| 📡 内容发布 | 3 | P0 | X/微信公众号/微博发布 |
| 📚 知识管理 | 10 | P1 | Obsidian, GitHub, TaskFlow, Skill 管理等 |
| ☁️ 飞书生态 | 13 | P0-P1 | 文档、表格、日历、IM、故障排查等 |
| 💬 企微生态 | 13 | P0-P1 | 消息、通讯录、会议、待办、智能表格等 |
| 📞 其他通讯 | 3 | P1 | QQ 频道/媒体/提醒（Discord/Slack/iMessage 未启用） |
| 🔧 基础设施 | 12 | P1 | 健康检查、节点连接、模型用量、session 日志等 |
| 🎮 未分配 | 34 | P2 | 娱乐/个人工具/Mac-only 等（不予分配） |

### 3.2 完整 Skill 清单

#### 类 1：通用工具（14 个）—— 所有 Agent 基础工具

| Skill | 功能 |
|-------|------|
| `web_search` | Web 搜索（DuckDuckGo） |
| `web_fetch` | URL 内容提取 |
| `read` | 文件读取 |
| `write` | 文件写入 |
| `edit` | 文件精确编辑 |
| `exec` | Shell 命令执行 |
| `process` | 后台进程管理 |
| `browser` | 浏览器自动化 |
| `canvas` | Canvas 画布控制 |
| `session_status` | Session 状态查询 |
| `memory_search` | 记忆语义搜索 |
| `memory_get` | 记忆精确读取 |
| `sessions_spawn` | 创建子 Agent |
| `sessions_send` | 跨 Session 通信 |

> 注：这些是 OpenClaw 内置工具，不在 skills 目录里，所有 Agent 默认可用。

#### 类 2：内容处理（14 个）

| Skill | 功能 | 建议权限 |
|-------|------|----------|
| `baoyu-format-markdown` | Markdown 格式化美化 | 全层级 |
| `baoyu-translate` | 多语言翻译 | 全层级 |
| `baoyu-markdown-to-html` | Markdown → HTML 转换 | VP+ |
| `baoyu-compress-image` | 图片压缩优化 | 全层级 |
| `baoyu-youtube-transcript` | YouTube 字幕提取 | VP+ |
| `baoyu-danger-gemini-web` | Gemini Web 接口 | CTO only |
| `baoyu-danger-x-to-markdown` | X/Twitter 内容转 Markdown | VP+ |
| `baoyu-wechat-summary` | 公众号文章摘要 | VP+ |
| `baoyu-url-to-markdown` | 任意 URL 转 Markdown | VP+ |
| `baoyu-electron-extract` | Electron 资源提取 | CTO only |
| `summarize` | 通用文本摘要 | 全层级 |
| `nano-pdf` | PDF 处理 | VP+ |
| `video-frames` | 视频帧提取 | VP+ |
| `openai-whisper` / `openai-whisper-api` | 语音转文字 | VP+ |

#### 类 3：内容创作（10 个）

| Skill | 功能 | 建议权限 |
|-------|------|----------|
| `baoyu-diagram` | 技术架构图/流程图 | CTO/专家 |
| `baoyu-image-gen` | AI 图片生成 | VP+ |
| `baoyu-infographic` | 信息图/长图生成 | VP+ |
| `baoyu-cover-image` | 文章封面图生成 | VP+ |
| `baoyu-slide-deck` | 幻灯片/PPT 生成 | VP+ |
| `baoyu-comic` | 漫画生成 | CPO/CEO |
| `baoyu-article-illustrator` | 文章配图生成 | CPO/CEO |
| `baoyu-xhs-images` | 小红书图片生成 | CPO/CEO |
| `gemini` | Gemini 生图能力 | VP+ |
| `baoyu-infographic` | 信息图 | VP+ |

#### 类 4：内容发布（3 个）—— ⚠️ P0 对外发布

| Skill | 功能 | 建议权限 |
|-------|------|----------|
| `baoyu-post-to-x` | 发布推文到 X/Twitter | CEO 直接；VP 审批模式 |
| `baoyu-post-to-wechat` | 发布公众号文章 | CEO 直接；VP 审批模式 |
| `baoyu-post-to-weibo` | 发布微博 | CEO 直接；VP 审批模式 |

#### 类 5：知识管理（10 个）

| Skill | 功能 | 建议权限 |
|-------|------|----------|
| `obsidian` | Obsidian Vault 操作 | VP+ |
| `wiki-maintainer` | Wiki 维护 | VP+ |
| `obsidian-vault-maintainer` | Vault 维护 | CTO |
| `taskflow` | 任务流管理 | 全层级（核心） |
| `taskflow-inbox-triage` | 任务收件箱分类 | VP+ |
| `skill-creator` | 创建/维护 Skill | CTO |
| `clawhub` | ClawdHub Skill 市场 | CTO |
| `release-skills` | Skill 发布流程 | CTO |
| `github` | GitHub 仓库操作 | VP+ |
| `gh-issues` | GitHub Issues 管理 | VP+ |

#### 类 6：飞书生态（13 个）

| Skill | 功能 | 建议权限 |
|-------|------|----------|
| `feishu-doc` | 飞书文档读写 | VP+ |
| `feishu-drive` | 飞书云盘 | VP+ |
| `feishu-wiki` | 飞书知识库 | VP+ |
| `feishu-perm` | 飞书权限管理 | CTO only |
| `feishu-bitable` | 飞书多维表格 | VP+ |
| `feishu-task` | 飞书任务管理 | PMO/COO |
| `feishu-calendar` | 飞书日历 | PMO/COO |
| `feishu-create-doc` | 飞书创建文档 | VP+ |
| `feishu-fetch-doc` | 飞书读取文档 | VP+ |
| `feishu-update-doc` | 飞书更新文档 | VP+ |
| `feishu-im-read` | 飞书 IM 读消息 | VP+ |
| `feishu-troubleshoot` | 飞书故障排查 | CTO only |
| `feishu-channel-rules` | 飞书频道规则 | CTO only |

> 另有 `a2a-*` 系列 6 个 Skill（alwaysActive=true），飞书群聊自动激活，无需分配。

#### 类 7：企微生态（13 个）

| Skill | 功能 | 建议权限 |
|-------|------|----------|
| `wecom-msg` | 企微消息发送 | COO |
| `wecom-contact-lookup` | 企微通讯录查询 | COO |
| `wecom-preflight` | 企微环境检查 | COO |
| `wecom-schedule` | 企微日程管理 | COO |
| `wecom-meeting-create` | 企微创建会议 | COO |
| `wecom-meeting-manage` | 企微会议管理 | COO |
| `wecom-meeting-query` | 企微会议查询 | COO |
| `wecom-edit-todo` | 企微待办编辑 | COO |
| `wecom-get-todo-list` | 企微待办列表 | COO |
| `wecom-get-todo-detail` | 企微待办详情 | COO |
| `wecom-smartsheet-data` | 企微智能表格数据 | COO |
| `wecom-smartsheet-schema` | 企微智能表格结构 | COO |
| `wecom-doc-manager` | 企微文档管理 | COO |

#### 类 8：其他通讯（3 个）

| Skill | 功能 | 建议权限 |
|-------|------|----------|
| `qqbot-channel` | QQ 频道操作 | CTO |
| `qqbot-media` | QQ 媒体消息 | CTO |
| `qqbot-remind` | QQ 提醒功能 | CTO |

> Discord, Slack, BlueBubbles, iMessage 等（8 个）未启用，不予分配。

#### 类 9：基础设施（12 个）

| Skill | 功能 | 建议权限 |
|-------|------|----------|
| `node-connect` | 远程节点连接 | CTO/SRE |
| `healthcheck` | 系统健康检查 | CTO/SRE |
| `browser-automation` | 浏览器自动化 | QA/Perf |
| `diffs` | 代码变更 diff | RD/Perf/QA |
| `coding-agent` | 编码助手子 Agent | CTO/专家 |
| `model-usage` | 模型用量统计 | CTO |
| `session-logs` | Session 日志分析 | CTO |
| `weather` | 天气查询 | 全层级 |
| `sherpa-onnx-tts` | 本地 TTS 语音合成 | VP+ |
| `tavily` | Tavily 搜索 | CTO |
| `searxng` | 自建隐私搜索引擎 | CTO（实验） |
| `prose` | 文档写作工具 | VP+ |

#### 类 10：未分配（34 个）—— 娱乐/个人/Mac-only

| Skill | 原因 |
|-------|------|
| `1password`, `apple-notes`, `apple-reminders`, `things-mac`, `bear-notes` | Mac only |
| `spotify-player`, `sonoscli`, `songsee`, `gifgrep` | 个人娱乐 |
| `camsnap`, `openhue`, `goplaces`, `eightctl`, `peekaboo` | 个人/IoT 工具 |
| `blucli`, `wacli`, `imsg`, `himalaya`, `voice-call`, `tmux` | 个人通讯/开发工具 |
| `gog`, `mcporter`, `ordercli` | 个人娱乐/工具 |
| `notion`, `trello`, `oracle` | 未启用 |
| `sag`, `xurl`, `blogwatcher` | 未知用途/未启用 |
| `self-improving-agent`, `proactive-agent`, `agent-browser-fradser-dotclaude` | 实验性，暂不分配 |
| `find-skills`, `skill-vetter` | Skill 管理（CTO 可用，按需） |
| `feishu-multi-bot`, `acp-router` | 基础设施（CTO 可用） |

---

## 4. 按层级 Skill 分配矩阵

### 4.1 分配总表

| Skill | CEO | CTO | CPO | CFO | COO | PMO | RD | Perf | QA | SRE | Worker |
|-------|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **通用工具 (14)** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **内容处理** | | | | | | | | | | | |
| baoyu-format-markdown | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| baoyu-translate | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| baoyu-compress-image | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — |
| summarize | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — |
| baoyu-markdown-to-html | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | — | — | — | — |
| baoyu-youtube-transcript | ✅ | ✅ | ✅ | ✅ | ✅ | — | — | — | — | — | — |
| baoyu-url-to-markdown | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | — | — | — | — |
| baoyu-danger-x-to-markdown | ✅ | ✅ | ✅ | — | — | — | — | — | — | — | — |
| baoyu-wechat-summary | ✅ | ✅ | ✅ | — | — | — | — | — | — | — | — |
| nano-pdf | ✅ | ✅ | ✅ | — | ✅ | ✅ | — | — | — | — | — |
| video-frames | ✅ | ✅ | ✅ | — | — | — | — | — | — | — | — |
| baoyu-danger-gemini-web | ✅ | ✅ | — | — | — | — | — | — | — | — | — |
| baoyu-electron-extract | ✅ | ✅ | — | — | — | — | — | — | — | — | — |
| openai-whisper / api | ✅ | ✅ | — | — | ✅ | — | — | — | — | — | — |
| **内容创作** | | | | | | | | | | | |
| baoyu-diagram | ✅ | ✅ | ✅ | — | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — |
| baoyu-image-gen | ✅ | ✅ | ✅ | — | ✅ | ✅ | — | — | — | — | — |
| baoyu-infographic | ✅ | ✅ | ✅ | — | ✅ | ✅ | — | — | — | — | — |
| baoyu-cover-image | ✅ | ✅ | ✅ | — | ✅ | — | — | — | — | — | — |
| baoyu-slide-deck | ✅ | ✅ | ✅ | — | ✅ | ✅ | — | — | — | — | — |
| baoyu-comic | ✅ | — | ✅ | — | — | — | — | — | — | — | — |
| baoyu-article-illustrator | ✅ | — | ✅ | — | — | — | — | — | — | — | — |
| baoyu-xhs-images | ✅ | — | ✅ | — | — | — | — | — | — | — | — |
| gemini | ✅ | ✅ | ✅ | — | — | — | — | — | — | — | — |
| **内容发布 (P0)** | | | | | | | | | | | |
| baoyu-post-to-x | ✅ | ⬜ | ⬜ | — | — | — | — | — | — | — | — |
| baoyu-post-to-wechat | ✅ | ⬜ | ⬜ | — | — | — | — | — | — | — | — |
| baoyu-post-to-weibo | ✅ | ⬜ | ⬜ | — | — | — | — | — | — | — | — |
| **知识管理** | | | | | | | | | | | |
| obsidian | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | — | — | — | — |
| wiki-maintainer | ✅ | ✅ | — | — | — | — | — | — | — | — | — |
| obsidian-vault-maintainer | ✅ | ✅ | — | — | — | — | — | — | — | — | — |
| taskflow | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — |
| taskflow-inbox-triage | ✅ | ✅ | — | — | ✅ | ✅ | — | — | — | — | — |
| skill-creator | ✅ | ✅ | — | — | — | — | — | — | — | — | — |
| clawhub | ✅ | ✅ | — | — | — | — | — | — | — | — | — |
| release-skills | ✅ | ✅ | — | — | — | — | — | — | — | — | — |
| github | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | — | — | — |
| gh-issues | ✅ | ✅ | ✅ | — | ✅ | ✅ | — | — | — | — | — |
| **飞书生态** | | | | | | | | | | | |
| feishu-doc | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | ✅ | — | — |
| feishu-drive | ✅ | ✅ | ✅ | — | ✅ | ✅ | — | — | — | — | — |
| feishu-wiki | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | — | — | — | — |
| feishu-perm | ✅ | ✅ | — | — | — | — | — | — | — | — | — |
| feishu-bitable | ✅ | ✅ | ✅ | — | ✅ | ✅ | — | — | — | — | — |
| feishu-task | ✅ | ✅ | — | — | ✅ | ✅ | — | — | — | — | — |
| feishu-calendar | ✅ | ✅ | — | — | ✅ | ✅ | — | — | — | — | — |
| feishu-create-doc | ✅ | ✅ | ✅ | — | ✅ | ✅ | — | — | — | — | — |
| feishu-fetch-doc | ✅ | ✅ | ✅ | — | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — |
| feishu-update-doc | ✅ | ✅ | ✅ | — | ✅ | ✅ | — | — | — | — | — |
| feishu-im-read | ✅ | ✅ | ✅ | — | ✅ | ✅ | — | — | — | — | — |
| feishu-troubleshoot | ✅ | ✅ | — | — | — | — | — | — | — | — | — |
| feishu-channel-rules | ✅ | ✅ | — | — | — | — | — | — | — | — | — |
| **企微生态** | | | | | | | | | | | |
| wecom-* (全 13 个) | ✅ | — | — | — | ✅ | — | — | — | — | — | — |
| **其他通讯** | | | | | | | | | | | |
| qqbot-* (3 个) | ✅ | ✅ | — | — | — | — | — | — | — | — | — |
| **基础设施** | | | | | | | | | | | |
| node-connect | ✅ | ✅ | — | — | — | — | — | — | — | ✅ | — |
| healthcheck | ✅ | ✅ | — | — | — | — | — | — | — | ✅ | — |
| browser-automation | ✅ | ✅ | ✅ | — | — | — | — | ✅ | ✅ | — | — |
| diffs | ✅ | ✅ | — | — | — | — | ✅ | ✅ | ✅ | — | — |
| coding-agent | ✅ | ✅ | — | — | — | ✅ | ✅ | ✅ | ✅ | ✅ | — |
| model-usage | ✅ | ✅ | — | — | — | — | — | — | — | — | — |
| session-logs | ✅ | ✅ | — | — | — | — | — | — | — | — | — |
| weather | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| sherpa-onnx-tts | ✅ | ✅ | — | — | ✅ | — | — | — | — | — | — |
| tavily | ✅ | ✅ | — | — | — | — | — | — | — | — | — |
| prose | ✅ | ✅ | ✅ | — | ✅ | — | — | — | — | — | — |

**图例：** ✅ 直接可用 | ⬜ 审批模式（起草后提交 CEO 审批） | — 不分配

### 4.2 各层级 Skill 计数

| 层级 | Agent | Skill 数（含通用工具 14） |
|------|-------|:---:|
| C 层 | CEO | ~75 |
| VP 层 | CTO | ~70 |
| VP 层 | CPO | ~35 |
| VP 层 | CFO | ~20 |
| VP 层 | COO | ~48 |
| 专家层 | PMO | ~32 |
| 专家层 | RD | ~15 |
| 专家层 | Perf | ~12 |
| 专家层 | QA | ~12 |
| 专家层 | SRE | ~12 |
| 执行层 | Worker | ~8（仅通用工具） |

---

## 5. Worker 权限

### 5.1 Worker 最小权限集

Worker（由专家 `sessions_spawn` 创建）仅授予：

```
通用工具 14 个（web_search, read, write, edit, exec, browser, canvas,
  memory_search, memory_get, session_status, process, sessions_spawn, sessions_send）
+ weather
+ baoyu-format-markdown
+ baoyu-translate
```

**Worker 不应有**：内容创作、内容发布、知识管理、飞书/企微通讯、基础设施管理能力。

### 5.2 实现方式

在 `openclaw.json` 的 `agents.defaults.subagents` 中配置 Worker 默认 skills 白名单。

---

## 6. 审批模式（P0 发布类）

对于 `baoyu-post-to-x`, `baoyu-post-to-wechat`, `baoyu-post-to-weibo` 三个 P0 发布 Skill：

1. **CEO 直接发布**：不经过审批
2. **CTO/CPO 审批模式**：起草 → 通过 `sessions_send` 提交 CEO 审批 → CEO 决定发布/驳回
3. **其他 Agent 不可用**：COO/CFO/PMO/专家/Worker 完全不能使用

---

## 7. OpenClaw 配置实施

### 7.1 配置方式

使用 `openclaw.json` 的 `agents.list[].skills` 字段做白名单控制。

当前状态：**所有 Agent 均无 skills 限制（全量开放）**，需要分阶段实施：

### 7.2 实施计划

| Phase | 内容 | 风险 |
|-------|------|------|
| **Phase 1** —— 文档落地 | 本文档定稿，各 Agent AGENTS.md 引用 | 无 |
| **Phase 2** —— Worker 限制 | 配置 `agents.defaults.subagents.skills` 白名单 | 低（Worker 当前本就不应该用那些 Skill） |
| **Phase 3** —— 专家层限制 | 逐个专家 Agent 配置 skills 白名单 | 中（可能影响现有 workflow） |
| **Phase 4** —— VP 层限制 | VP Agent 配置 skills 白名单 | 中 |
| **Phase 5** —— 审计 | 启用 Skill 调用日志，记录到 tool_calls 表 | 低 |

### 7.3 Phase 2 Worker 配置示例

```json5
{
  agents: {
    defaults: {
      subagents: {
        model: { primary: "qwenProvider/qwen3-coder-plus" },
        skills: [
          "web_search", "web_fetch",
          "read", "write", "edit", "exec",
          "browser", "canvas",
          "memory_search", "memory_get",
          "session_status", "process",
          "weather",
          "baoyu-format-markdown",
          "baoyu-translate"
        ]
      }
    }
  }
}
```

---

## 8. Skill 生命周期

### 8.1 新增 Skill 流程

```
提出需求 → CTO 评估 → 安装测试 → 更新本文档 → 分配权限 → 通知团队
```

### 8.2 废弃 Skill 流程

```
CTO 评估 → 标记 deprecated → 30 天观察 → 从配置移除 → 更新本文档
```

### 8.3 审计

建议在可观测性平台（Agent 基础设施可观测性平台）的 `tool_calls` 表中记录每次 Skill 调用，支持按 Agent、Skill、时间维度查询。

---

## 9. 修订记录

| 版本 | 日期 | 修订内容 |
|------|------|---------|
| v0.1 | 2026-06-06 | 初版，80 个 Skill 分类 + 旧组织架构 |
| v0.2 | 2026-06-06 | 补充 OpenClaw 配置示例 |
| v0.3 | 2026-06-06 | 完善权限矩阵 + 实施计划 |
| v0.4 | 2026-06-07 | 对齐当前 10 Agent 组织架构（CEO→VP→专家→Worker），重算 126 个 Skill，新增矩阵总表，移除 ASCII 图 |
