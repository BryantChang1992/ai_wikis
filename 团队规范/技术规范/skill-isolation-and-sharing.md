---
title: Skill 隔离与共享机制
status: proposal
version: v0.3
created: 2026-06-06
updated: 2026-06-06
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

### 2.1 完整 Skill 清单与分类

> 当前团队已安装 **80 个** Skill（去重后）。以下按功能分为 10 类，每个标注来源、优先级、使用建议。

#### 类 1：通用工具（14 个）— 所有 Agent 基础工具，P2 风险

| Skill | 来源 | 功能 | 说明 |
|-------|------|------|------|
| `web_search` | 内置 | Web 搜索（DuckDuckGo） | 核心工具 |
| `web_fetch` | 内置 | URL 内容提取 | 核心工具 |
| `read` | 内置 | 文件读取 | 核心工具 |
| `write` | 内置 | 文件写入 | 核心工具 |
| `edit` | 内置 | 文件精确编辑 | 核心工具 |
| `exec` | 内置 | Shell 命令执行 | 核心工具 |
| `process` | 内置 | 后台进程管理 | 核心工具 |
| `browser` | 内置 | 浏览器自动化 | 核心工具 |
| `canvas` | 内置 | Canvas 画布控制 | 核心工具 |
| `session_status` | 内置 | Session 状态查询 | 核心工具 |
| `memory_search` | 内置 | 记忆语义搜索 | 核心工具 |
| `memory_get` | 内置 | 记忆精确读取 | 核心工具 |
| `sessions_spawn` | 内置 | 创建子 Agent | 核心工具 |
| `sessions_send` | 内置 | 跨 Session 通信 | 核心工具 |

#### 类 2：内容处理（15 个）— 格式转换、提取、翻译，P2 风险

| Skill | 来源 | 功能 | 说明 |
|-------|------|------|------|
| `baoyu-format-markdown` | 个人 | Markdown 格式化美化 | 所有 Agent 可用 |
| `baoyu-translate` | 个人 | 多语言翻译 | 所有 Agent 可用 |
| `baoyu-markdown-to-html` | 个人 | Markdown → HTML 转换 | VP+ 可用 |
| `baoyu-compress-image` | 个人 | 图片压缩优化 | 所有 Agent 可用 |
| `baoyu-youtube-transcript` | 个人 | YouTube 字幕提取 | VP+ 可用 |
| `baoyu-danger-gemini-web` | 个人 | Gemini Web 接口（⚠️ 危险） | CTO only（沙箱） |
| `baoyu-danger-x-to-markdown` | 个人 | X/Twitter 内容转 Markdown | VP+ 可用 |
| `baoyu-wechat-summary` | 个人 | 微信公众号文章摘要 | VP+ 可用 |
| `baoyu-url-to-markdown` | 个人 | 任意 URL 转 Markdown | VP+ 可用 |
| `baoyu-electron-extract` | 个人 | Electron 应用资源提取 | CTO only（研发） |
| `video-frames` | 内置 | 视频帧提取 | VP+ 可用 |
| `nano-pdf` | 内置 | PDF 处理 | VP+ 可用 |
| `summarize` | 内置 | 通用文本摘要 | 所有 Agent 可用 |
| `openai-whisper` | 内置 | 本地语音转文字 | VP+ 可用 |
| `openai-whisper-api` | 内置 | API 语音转文字 | VP+ 可用 |

#### 类 3：内容创作（9 个）— 生成视觉/文档/演示内容，P1 风险

| Skill | 来源 | 功能 | 说明 |
|-------|------|------|------|
| `baoyu-diagram` | 个人 | 技术架构图/流程图 | CTO/专家可用 |
| `baoyu-image-gen` | 个人 | AI 图片生成 | VP+ 可用 |
| `baoyu-infographic` | 个人 | 信息图/长图生成 | VP+ 可用 |
| `baoyu-cover-image` | 个人 | 文章封面图生成 | VP+ 可用 |
| `baoyu-slide-deck` | 个人 | 幻灯片/PPT 生成 | VP+ 可用 |
| `baoyu-comic` | 个人 | 漫画生成 | CPO/CEO 可用 |
| `baoyu-article-illustrator` | 个人 | 文章配图生成 | CPO/CEO 可用 |
| `baoyu-xhs-images` | 个人 | 小红书图片生成 | CPO/CEO 可用 |
| `gemini` | 内置 | Gemini 生图能力 | VP+ 可用 |

#### 类 4：内容发布（3 个）— 对外发布内容，P0 风险

| Skill | 来源 | 功能 | 说明 |
|-------|------|------|------|
| `baoyu-post-to-x` | 个人 | 发布推文到 X/Twitter | CEO 直接发；VP 审批模式 |
| `baoyu-post-to-wechat` | 个人 | 发布微信公众号文章 | CEO 直接发；VP 审批模式 |
| `baoyu-post-to-weibo` | 个人 | 发布微博 | CEO 直接发；VP 审批模式 |

#### 类 5：知识管理（13 个）— 知识沉淀、仓库操作、任务管理，P1 风险

| Skill | 来源 | 功能 | 说明 |
|-------|------|------|------|
| `obsidian` | 内置 | Obsidian Vault 操作 | VP+ 可用 |
| `skill-creator` | 内置 | 创建/维护 Skill | CTO/CPO 可用 |
| `github` | 内置 | GitHub 仓库操作 | VP+ 可用 |
| `gh-issues` | 内置 | GitHub Issues 管理 | VP+ 可用 |
| `taskflow` | 内置 | 任务流管理 | 所有 Agent（核心） |
| `taskflow-inbox-triage` | 内置 | 任务收件箱分类 | VP+ 可用 |
| `clawhub` | 内置 | ClawdHub Skill 市场 | CTO 可用 |
| `release-skills` | 个人 | Skill 发布流程 | CTO 可用 |
| `find-skills` | workspace | 发现/安装新 Skill | CTO 可用 |
| `skill-vetter` | workspace | Skill 安全审查 | CTO 可用 |
| `coding-agent` | 内置 | 编码助手子 Agent | VP+ 可用 |
| `self-improving-agent` | workspace | Agent 自我改进循环 | CTO 可用（实验） |
| `proactive-agent` | workspace | Agent 主动行为框架 | CTO 可用（实验） |

#### 类 6：通讯·飞书（14 个）— 飞书生态操作，P0-P1 风险

| Skill | 来源 | 功能 | 说明 |
|-------|------|------|------|
| `feishu-doc` | 内置 | 飞书文档操作 | VP+ 可用 |
| `feishu-drive` | 内置 | 飞书云盘操作 | VP+ 可用 |
| `feishu-wiki` | 内置 | 飞书知识库 | VP+ 可用 |
| `feishu-perm` | 内置 | 飞书权限管理 | CTO only |
| `feishu-bitable` | 插件 | 飞书多维表格 | VP+ 可用 |
| `feishu-task` | 插件 | 飞书任务管理 | COO/CTO 可用 |
| `feishu-calendar` | 插件 | 飞书日历 | COO/CTO 可用 |
| `feishu-channel-rules` | 插件 | 飞书频道规则 | CTO only |
| `feishu-create-doc` | 插件 | 飞书创建文档 | VP+ 可用 |
| `feishu-fetch-doc` | 插件 | 飞书读取文档 | VP+ 可用 |
| `feishu-update-doc` | 插件 | 飞书更新文档 | VP+ 可用 |
| `feishu-im-read` | 插件 | 飞书 IM 读消息 | VP+ 可用 |
| `feishu-troubleshoot` | 插件 | 飞书故障排查 | CTO only |
| `feishu-multi-bot` | workspace | 多飞书机器人绑定 | CTO only |

#### 类 7：通讯·企微（13 个）— 企业微信生态，P0-P1 风险

| Skill | 来源 | 功能 | 说明 |
|-------|------|------|------|
| `wecom-msg` | 插件 | 企微消息发送 | COO/CTO 可用 |
| `wecom-contact-lookup` | 插件 | 企微通讯录查询 | COO/CTO 可用 |
| `wecom-preflight` | 插件 | 企微环境检查 | COO 可用 |
| `wecom-schedule` | 插件 | 企微日程管理 | COO 可用 |
| `wecom-meeting-create` | 插件 | 企微创建会议 | COO 可用 |
| `wecom-meeting-manage` | 插件 | 企微会议管理 | COO 可用 |
| `wecom-meeting-query` | 插件 | 企微会议查询 | COO 可用 |
| `wecom-edit-todo` | 插件 | 企微待办编辑 | COO 可用 |
| `wecom-get-todo-list` | 插件 | 企微待办列表 | COO 可用 |
| `wecom-get-todo-detail` | 插件 | 企微待办详情 | COO 可用 |
| `wecom-smartsheet-data` | 插件 | 企微智能表格数据 | COO 可用 |
| `wecom-smartsheet-schema` | 插件 | 企微智能表格结构 | COO 可用 |
| `wecom-doc-manager` | 插件 | 企微文档管理 | COO 可用 |

#### 类 8：通讯·其他（8 个）— QQ/Discord/Slack 等，P0-P1 风险

| Skill | 来源 | 功能 | 说明 |
|-------|------|------|------|
| `qqbot-channel` | 内置 | QQ 频道操作 | VP+ 可用 |
| `qqbot-media` | 内置 | QQ 媒体消息 | VP+ 可用 |
| `qqbot-remind` | 内置 | QQ 提醒功能 | VP+ 可用 |
| `discord` | 内置 | Discord 集成 | —（未启用） |
| `slack` | 内置 | Slack 集成 | —（未启用） |
| `bluebubbles` | 内置 | BlueBubbles (iMessage) | —（未启用） |
| `imsg` | 内置 | iMessage | —（未启用） |
| `himalaya` | 内置 | 邮件客户端 | —（未启用） |

#### 类 9：基础设施（8 个）— 运维、健康检查、搜索，P1 风险

| Skill | 来源 | 功能 | 说明 |
|-------|------|------|------|
| `node-connect` | 内置 | 远程节点连接 | CTO/专家可用 |
| `healthcheck` | 内置 | 系统健康检查 | CTO/专家可用 |
| `sherpa-onnx-tts` | 内置 | 本地 TTS 语音合成 | VP+ 可用 |
| `model-usage` | 内置 | 模型用量统计 | CTO/CFO 可用 |
| `session-logs` | 内置 | Session 日志分析 | CTO 可用 |
| `weather` | 内置 | 天气查询 | 所有 Agent 可用 |
| `searxng` | workspace | 自建隐私搜索引擎 | CTO 可用（实验） |
| `agent-browser-fradser-dotclaude` | workspace | 浏览器自动化增强 | CTO 可用（实验） |
| `blogwatcher` | 内置 | 博客更新监控 | —（未启用） |

#### 类 10：娱乐/个人/未启用（26 个）— 不赋予任何 Agent，P2 风险

| Skill | 来源 | 功能 | 不予分配原因 |
|-------|------|------|------------|
| `1password` | 内置 | 1Password 密码管理 | 个人工具 |
| `apple-notes` | 内置 | Apple Notes | Mac only |
| `apple-reminders` | 内置 | Apple Reminders | Mac only |
| `things-mac` | 内置 | Things 3 任务管理 | Mac only |
| `spotify-player` | 内置 | Spotify 播放器 | 个人娱乐 |
| `sonoscli` | 内置 | Sonos 音箱控制 | 个人娱乐 |
| `songsee` | 内置 | 歌曲识别 | 个人娱乐 |
| `camsnap` | 内置 | 摄像头抓拍 | 个人娱乐 |
| `openhue` | 内置 | Philips Hue 灯光 | 个人娱乐 |
| `goplaces` | 内置 | 地点管理 | 个人 |
| `gog` | 内置 | GOG 游戏平台 | 个人娱乐 |
| `gifgrep` | 内置 | GIF 搜索 | 个人娱乐 |
| `bear-notes` | 内置 | Bear 笔记 | Mac only |
| `blucli` | 内置 | Blue 命令行 | Mac only |
| `eightctl` | 内置 | Eight Sleep 床垫控制 | 个人 |
| `mcporter` | 内置 | Minecraft 服务器 | 个人娱乐 |
| `peekaboo` | 内置 | 屏幕监控 | 个人 |
| `sag` | 内置 | 未知 | 未知用途 |
| `wacli` | 内置 | WhatsApp CLI | —（未启用） |
| `xurl` | 内置 | URL 短链接 | —（未启用） |
| `tmux` | 内置 | Tmux 会话管理 | 开发工具 |
| `voice-call` | 内置 | 语音通话 | —（未启用） |
| `notion` | 内置 | Notion 集成 | —（未启用） |
| `trello` | 内置 | Trello 集成 | —（未启用） |
| `oracle` | 内置 | Oracle 数据库 | —（未启用） |
| `ordercli` | 内置 | 点餐 CLI | 个人工具 |

### 2.2 分类统计

| 类别 | 数量 | 风险 | 默认分配 |
|------|:---:|:---:|---------|
| 通用工具 | 14 | P2 | 全层级 |
| 内容处理 | 15 | P2 | 全层级（部分 VP+） |
| 内容创作 | 9 | P1 | VP+（部分 CTO/CPO） |
| 内容发布 | 3 | P0 | CEO + VP 审批模式 |
| 知识管理 | 13 | P1 | VP+（部分 CTO） |
| 通讯·飞书 | 14 | P0-P1 | VP+（按角色） |
| 通讯·企微 | 13 | P0-P1 | COO + CTO |
| 通讯·其他 | 8 | P0-P1 | VP+（部分未启用） |
| 基础设施 | 9 | P1 | CTO/专家 |
| 娱乐/未启用 | 26 | P2 | 不赋予 |
| **唯一 Skill 总数** | **80** | | |

### 2.3 按风险等级分类

```
P0 · 高权限 Skill（共 ~33 个，影响对外声誉/基础设施安全）：
    ├── 内容发布类 (3)：baoyu-post-to-x, wechat, weibo
    ├── 通讯·飞书 (14)：feishu-doc/drive/wiki/perm/bitable/...
    ├── 通讯·企微 (13)：wecom-msg/contact/meeting/...
    └── 通讯·其他 (3)：qqbot-channel/media/remind

P1 · 中权限 Skill（共 ~30 个，影响团队内部产出/数据一致性）：
    ├── 内容创作 (9)：baoyu-diagram, image-gen, infographic...
    ├── 知识管理 (13)：obsidian, skill-creator, github, taskflow...
    └── 基础设施 (9)：node-connect, healthcheck, searxng...

P2 · 低权限 Skill（共 ~55 个，纯工具/个人使用，无外部影响）：
    ├── 通用工具 (14)：web_search, read, write, exec...
    ├── 内容处理 (15)：baoyu-translate, format-markdown...
    └── 娱乐/未启用 (26)：spotify-player, weather, apple-notes...
```

---

## 3. 按层级的 Skill 分配方案


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

---

## 相关链接

- [[../项目文档/agent基础设施可观测性平台/设计文档]] — 五维度框架 + 权限矩阵
- [[../项目文档/agent基础设施可观测性平台/observability-deep-design]] — 可观测性深度设计（Skill 审计面板）
- [[../../agent核心文件/cto/AGENTS]] — CTO 现有权限定义
- [OpenClaw Skills 文档](https://docs.openclaw.ai/tools/skills) — 原生机制参考

---

## 8. Skill 生命周期管理

> Skill 不是"加进去就不管了"。新增、修改、删除都需要审批流程和知识沉淀。

### 8.1 生命周期状态机

```
  ┌──────────┐    申请     ┌──────────┐   审批通过   ┌──────────┐
  │ proposed │ ──────────▶ │ pending  │ ──────────▶ │  active  │
  │  (草案)   │             │ (待审批)  │             │  (生效)   │
  └──────────┘             └──────────┘             └────┬─────┘
       ▲                                                  │
       │ 驳回                                              │ 发现废弃/不安全
       │                                                 ▼
       │                                            ┌──────────┐
       └──────────────── 经修改重新申请 ─────────────│deprecated│
                                                    └────┬─────┘
                                                         │ 30 天观察期后
                                                         ▼
                                                    ┌──────────┐
                                                    │ removed  │
                                                    └──────────┘
```

| 状态 | 含义 | Skill 行为 |
|------|------|-----------|
| `proposed` | 草案阶段，有人在调研/编写 | 不在任何 Agent 的 allowlist 中 |
| `pending` | 已提交审批，等待 CTO/CEO 决策 | 不在生产 Agent 的 allowlist 中，允许 CTO 沙箱测试 |
| `active` | 审批通过，正式上线 | 按 §3 分配矩阵加入对应 Agent 的 allowlist |
| `deprecated` | 标记废弃（有替代方案/不再需要/安全风险） | 保留在 allowlist 但 AGENTS.md 提示"禁止使用"，记录替代方案 |
| `removed` | 已删除 | 从 all allowlists 移除，30 天后再删文件 |

### 8.2 新增 Skill 流程

```
┌─────────────────────────────────────────────────────────────┐
│                    新增 Skill 完整流程                         │
│                                                               │
│  Step 1 · 提出需求                                            │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │ 任何人（CEO / VP / 专家 / 执行层）可以提出：              │ │
│  │ "我需要一个做 XXX 的 Skill"                              │ │
│  │                                                           │ │
│  │ 提出人需要：                                              │ │
│  │ □ 说明 Skill 的使用场景（谁会用到，用来干什么）            │ │
│  │ □ 评估风险等级（P0 高 / P1 中 / P2 低）                   │ │
│  │ □ 建议分配到哪些层级                                     │ │
│  └─────────────────────────────────────────────────────────┘ │
│                          │                                    │
│                          ▼                                    │
│  Step 2 · CTO 技术评估                                        │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │ CTO 负责：                                               │ │
│  │ □ 评估与现有 Skill 的重叠度（是否可以用已有 Skill 替代）  │ │
│  │ □ 评估技术复杂度（是否需要脚本、外部依赖）               │ │
│  │ □ 确定风险等级和分配范围                                 │ │
│  │ □ 如果是 P0 风险 Skill → 升级到 CEO 审批                 │ │
│  │ □ 如果是 P1/P2 → CTO 可以直接批准                        │ │
│  │                                                           │ │
│  │ 输出：Skill 提案文档（包含上述评估结果）                  │ │
│  └─────────────────────────────────────────────────────────┘ │
│                          │                                    │
│                          ▼                                    │
│  Step 3 · 审批（按风险等级分流）                              │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │ P0 风险 Skill：                                          │ │
│  │   CTO 审核 → CEO 最终批准                                │ │
│  │ P1 风险 Skill：                                          │ │
│  │   CTO 批准（通知 CEO）                                   │ │
│  │ P2 风险 Skill：                                          │ │
│  │   CTO 批准（记录即可）                                   │ │
│  └─────────────────────────────────────────────────────────┘ │
│                          │                                    │
│                          ▼                                    │
│  Step 4 · 实施                                                │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │ CTO 委派专家·Infra 或自行：                               │ │
│  │ □ 创建 SKILL.md（用 skill-creator 模板）                  │ │
│  │ □ 放到正确的目录（~/.agents/skills/ 或仓库）             │ │
│  │ □ 更新 openclaw.json 中对应 Agent 的 skills allowlist    │ │
│  │ □ 更新本文档的 Skill 分类清单                            │ │
│  │ □ 在 CTO 自己的 Agent 上沙箱测试                         │ │
│  └─────────────────────────────────────────────────────────┘ │
│                          │                                    │
│                          ▼                                    │
│  Step 5 · 上线 & 知识沉淀                                     │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │ □ openclaw gateway restart 生效                          │ │
│  │ □ 通知受影响 Agent 的新 Skill 已可用（更新 AGENTS.md）    │ │
│  │ □ 记录变更日志                                           │ │
│  │ □ 知识沉淀到 ai_wikis/知识库/                            │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### 8.3 修改 Skill 流程

```
修改 Skill = 两步判断：

1. 修改的是内容还是行为？
   ├── 内容修改（文档措辞、示例更新）
   │   └── 专家/CTO 直接改，记录变更日志即可
   │
   └── 行为修改（工具参数变更、执行逻辑调整、依赖变更）
       └── 走 §8.2 完整审批流程

2. 修改影响范围和风险变化？
   ├── 风险不变或降低 → CTO 审批即可
   └── 风险提升（例如从 P2 → P1）→ 重新走 CEO 审批
```

**变更日志模板：**

```markdown
## Skill 变更日志

### baoyu-post-to-x · 2026-06-06
- **变更类型：** 行为修改
- **变更人：** CTO
- **变更内容：** 增加发布前 CEO 确认检查步骤
- **风险变化：** P1 → P1（不变）
- **审批：** CTO 批准
- **影响 Agent：** CEO, CPO（CTO 已有审批约束）
```

### 8.4 删除/废弃 Skill 流程

```
┌─────────────────────────────────────────────────────────────┐
│                    删除/废弃 Skill 流程                        │
│                                                               │
│   触发条件：                                                  │
│   ├── Skill 的依赖服务已停止（如第三方 API 关闭）             │
│   ├── 有更好的替代 Skill 上线                                 │
│   ├── Skill 超过 90 天无人使用                                │
│   └── 发现安全漏洞                                            │
│                          │                                    │
│                          ▼                                    │
│   第 1 阶段 · 标记废弃 (deprecated)                           │
│   ┌───────────────────────────────────────────────────────┐  │
│   │ □ CTO 评估确认废弃原因                                 │  │
│   │ □ 更新本文档 Skill 分类清单：标记 deprecated + 日期    │  │
│   │ □ 在 SKILL.md 顶部加 <!-- DEPRECATED: 2026-06-06 -->   │  │
│   │ □ 如有替代方案，在 SKILL.md 中注明                      │  │
│   │ □ 从所有 Agent allowlist 中移除                        │  │
│   │ □ 通知受影响 Agent（更新 AGENTS.md）                    │  │
│   │ □ 飞书通知团队：XX Skill 已废弃，请用 YY 替代          │  │
│   └───────────────────────────────────────────────────────┘  │
│                          │                                    │
│                   30 天观察期                                  │
│              （确认没有人还在用）                              │
│                          │                                    │
│                          ▼                                    │
│   第 2 阶段 · 正式删除 (removed)                              │
│   ┌───────────────────────────────────────────────────────┐  │
│   │ □ 删除 SKILL.md 文件                                   │  │
│   │ □ 更新变更日志                                         │  │
│   │ □ 知识沉淀：为什么废弃、替代方案是什么                  │  │
│   └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

**紧急删除**（安全漏洞）：跳过 30 天观察期，立即从 allowlist 移除 + 删除文件。

### 8.5 Skill 定期审查 (Quarterly Review)

```
每季度执行一次（CTO 负责，委派专家·Infra 执行）：

审查清单：
□ 哪些 Skill 超过 90 天无人使用？→ 发起废弃流程
□ 哪些 Skill 的依赖有更新？→ 发起修改流程
□ 有哪些新场景需要新 Skill？→ 发起新增流程
□ Skill 风险等级是否需要调整？
□ 各 Agent 的 Skill 使用频率统计（从 tool_calls 表出）
□ 是否有 Agent 在使用不在其 allowlist 中的 Skill？

输出：季度 Skill 审查报告 → 存入 ai_wikis/知识库/
```

---

## 9. 权限矩阵细化

> §3 已给出按层级的 Skill 分配总表。本章细化到每个具体操作和决策权。

### 9.1 Skill 管理权限矩阵

| 操作 | CEO | CTO | CPO | CFO | COO | 专家 | 执行层 |
|------|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **提出新 Skill 需求** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **技术评估** | — | ✅ | ❌ | ❌ | ❌ | 🔶 辅助 | ❌ |
| **批准 P0 风险 Skill** | ✅ | 🔶 审核 | ❌ | ❌ | ❌ | ❌ | ❌ |
| **批准 P1/P2 风险 Skill** | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **编写/修改 SKILL.md** | ✅ | ✅ | ✅ 内容类 | ❌ | ✅ 运营类 | 🔶 被委派 | ❌ |
| **批准 Skill 行为修改** | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **批准 Skill 内容修改** | — | ✅ | ✅ 自身领域 | ❌ | ✅ 自身领域 | 🔶 被委派 | ❌ |
| **发起废弃 Skill** | ✅ | ✅ | ✅ | ❌ | ❌ | 🔶 建议 | ❌ |
| **批准废弃 Skill** | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **执行删除 Skill** | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **修改 openclaw.json allowlist** | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **季度审查** | — | ✅ 负责 | ❌ | ❌ | ❌ | 🔶 执行 | ❌ |
| **沙箱测试新 Skill** | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |

### 9.2 Skill 使用权限矩阵

| Skill 类别 | CEO | CTO | CPO | CFO | COO | 专家·Infra | 专家·Perf | 专家·SRE | 执行层 |
|-----------|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| 通用工具 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 内容处理 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 🔶 基础 |
| 内容创作 | ✅ | ✅ | ✅ | ❌ | 🔶 有限 | 🔶 diagram | ❌ | ❌ | ❌ |
| 知识管理 | ✅ | ✅ | ✅ | ✅ | ✅ | 🔶 受限 | ❌ | ❌ | ❌ |
| 基础设施 | ✅ | ✅ | ❌ | ❌ | ✅ | ✅ | ✅ | ✅ | ❌ |
| 通讯·飞书 | ✅ | ✅ | ❌ | 🔶 doc | ✅ | ❌ | ❌ | ❌ | ❌ |
| 通讯·企微 | ✅ | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ |
| 通讯·QQ | ✅ | ✅ | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ |
| 内容发布 | ✅ | 🔶 审批 | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| 娱乐/个人 | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |

### 9.3 风险等级判定标准

| 风险等级 | 判断标准 | 示例 | 审批链 |
|---------|---------|------|-------|
| **P0** | 影响对外声誉/资金/基础设施安全/团队外部形象 | baoyu-post-to-x, github(force push), wecom-msg(群发) | CTO 审核 → CEO 批准 |
| **P1** | 影响团队内部产出质量/跨 Agent 数据一致性 | baoyu-slide-deck, obsidian, skill-creator | CTO 批准（通知 CEO） |
| **P2** | 低风险，纯工具类/个人使用，无外部影响 | baoyu-translate, baoyu-compress-image, weather | CTO 批准（记录即可） |

**风险升级条件：**
- 如果一个 P2 Skill 的使用频率在 1 个月内暴增 10 倍 → 重新评估风险等级
- 如果一个 Skill 被发现可以用于未预期的危险场景 → 立即升级到 P0，紧急 review

### 9.4 各角色的 Skill 职责

| 角色 | Skill 相关职责 |
|------|--------------|
| **CEO** | P0 风险 Skill 最终批准；紧急删除授权；关注 Skill 使用的整体健康度 |
| **CTO** | Skill 技术评估；P1/P2 审批；allowlist 维护；季度审查；变更日志管理；知识沉淀 |
| **CPO** | 内容创作类 Skill 的领域审批；内容发布流程设计 |
| **COO** | 通讯类 Skill 的领域审批；运营自动化 Skill 的推动 |
| **CFO** | Skill 成本评估（token 消耗、API 费用）；预算建议 |
| **专家** | 辅助 CTO 做技术评估；执行季度审查；提出本领域 Skill 需求 |
| **执行层** | 提出 Skill 需求；反馈 Skill 使用问题 |

### 9.5 Skill 冲突处理

当同名 Skill 在多个路径存在时（见 §1.2 路径分层机制）：

| 场景 | 处理方式 | 责任人 |
|------|---------|--------|
| 团队需要覆盖内置 Skill 行为 | 在 `~/.agents/skills/` 写同名 SKILL.md（高优先级覆盖） | CTO |
| 单 Agent 需要个性化 Skill 版本 | 在 `<workspace>/skills/` 写同名 SKILL.md（最高优先级覆盖） | CTO |
| 两个 Skill 功能重叠 | CTO 评估后合并或废弃其中一个 | CTO |
| Skill 依赖冲突（两个 Skill 依赖同一个包的不同版本） | 用 wrapper script 隔离 | 专家·Infra |

---

## 10. 变更日志

| 日期 | 版本 | 变更 | 作者 |
|------|------|------|------|
| 2026-06-06 | v0.1 | 初稿：Skill 分类 + 分配矩阵 + openclaw.json 配置 | CTO |
| 2026-06-06 | v0.2 | 新增：§8 生命周期管理 + §9 权限矩阵细化 | CTO |
| 2026-06-06 | v0.3 | 重构 §2：完整 Skill 清单（80 个去重），10 类详细表 + 分类统计 + 风险等级 | CTO |

---
