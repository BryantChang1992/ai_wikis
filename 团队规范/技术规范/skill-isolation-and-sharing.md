---
title: Skill 隔离与共享机制
status: active
version: v0.8
created: 2026-06-06
updated: 2026-06-21
tags:
  - skill
  - 权限
  - CHANG_AI_TEAM
---

# Skill 隔离与共享机制

> [!note] 背景
> 团队架构为 **CXO 全保留（CEO + CFO + COO + CPO + CTO）+ 临时 Worker**。Skill 分配按组织层级和职责边界划分。

---

## 1. 架构与 Skill 分层

```
Bryant
  └── CEO (Mike) —— 全量 Skill，对外发布，全局决策
        ├── CFO (Trinity) —— 审计视角：成本分析、报告生成
        ├── COO (Neo) —— 运营视角：调度监控、效能分析
        ├── CPO (Morpheus) —— 产品视角：路线规划、产品化
        └── CTO (Stark) —— 技术域全权：Worker 编排、Wiki/Skill 管理、基础设施
              └── Worker (临时) —— 最小集：通用工具 + 基础内容处理
```

| 层级 | 承担者 | Skill 数 | 上下文 |
|------|--------|:---:|------|
| 决策/发布层 | CEO | ~60 | 独立：全局决策、对外发布、Bryant 交互 |
| CXO 管理层 | CFO/COO/CPO | ~30 | 独立：各自领域决策、运营/财务/产品分析 |
| 技术执行层 | CTO | ~50 | 独立：技术全栈、Worker 编排、Wiki/Skill 管理 |
| 临时执行层 | Worker | ~15 | 独立：单任务单上下文，结束即销毁 |

---

## 2. Skill 分类（当前 126 个）

### 类 1：通用工具（14 个）—— 所有层级

`web_search` `web_fetch` `read` `write` `edit` `exec` `process` `browser` `canvas` `session_status` `memory_search` `memory_get` `sessions_spawn` `sessions_send`

> OpenClaw 内置，所有 Agent 默认可用

### 类 2：内容处理（14 个）

| Skill | CEO | CFO | COO | CPO | CTO | Worker |
|-------|:---:|:---:|:---:|:---:|:---:|:---:|
| baoyu-format-markdown | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| baoyu-translate | ✅ | — | — | — | ✅ | ✅ |
| baoyu-compress-image | ✅ | — | — | — | ✅ | — |
| summarize | ✅ | ✅ | ✅ | ✅ | ✅ | — |
| baoyu-markdown-to-html | ✅ | — | — | — | ✅ | — |
| baoyu-youtube-transcript | ✅ | — | — | — | ✅ | — |
| baoyu-url-to-markdown | ✅ | — | — | — | ✅ | — |
| baoyu-danger-x-to-markdown | ✅ | — | — | — | ✅ | — |
| baoyu-wechat-summary | ✅ | — | — | — | ✅ | — |
| nano-pdf | ✅ | — | — | — | ✅ | — |
| video-frames | ✅ | — | — | — | ✅ | — |
| baoyu-danger-gemini-web | ✅ | — | — | — | ✅ | — |
| baoyu-electron-extract | ✅ | — | — | — | ✅ | — |
| openai-whisper / api | ✅ | — | — | — | ✅ | — |

### 类 3：内容创作（11 个）

| Skill | CEO | CFO | COO | CPO | CTO | Worker |
|-------|:---:|:---:|:---:|:---:|:---:|:---:|
| fireworks-tech-graph 🔴 | ✅ | — | — | ✅ | ✅ | — |
| baoyu-diagram | ✅ | — | — | ✅ | ✅ | — |
| baoyu-image-gen | ✅ | — | — | — | ✅ | — |
| baoyu-infographic | ✅ | — | — | — | ✅ | — |
| baoyu-cover-image | ✅ | — | — | — | ✅ | — |
| baoyu-slide-deck | ✅ | — | — | ✅ | ✅ | — |
| baoyu-comic | ✅ | — | — | — | — | — |
| baoyu-article-illustrator | ✅ | — | — | — | — | — |
| baoyu-xhs-images | ✅ | — | — | — | — | — |
| gemini | ✅ | — | — | — | ✅ | — |

> 🔴 **fireworks-tech-graph** 是团队所有非 UML 技术图的**强制统一 skill**。
> 覆盖：架构图、数据流图、流程图、序列图、Agent 架构图、Memory 架构图、对比矩阵、时间线、思维导图、网络拓扑、状态机、ER 图。
> UML 类图 / 用例图 / 状态机图 / ER 图也由 fireworks-tech-graph 覆盖（含完整 UML 14 种图支持）。
> `baoyu-diagram` 仅保留作为 UML 之外的备选（不得主动使用）。
> 详细规范见 [[画图规范]]。

### 类 4：内容发布（3 个）—— ⚠️ P0 仅 CEO

| Skill | CEO | CFO | COO | CPO | CTO | Worker |
|-------|:---:|:---:|:---:|:---:|:---:|:---:|
| baoyu-post-to-x | ✅ | — | — | — | — | — |
| baoyu-post-to-wechat | ✅ | — | — | — | — | — |
| baoyu-post-to-weibo | ✅ | — | — | — | — | — |

### 类 5：知识管理（10 个）

| Skill | CEO | CFO | COO | CPO | CTO | Worker |
|-------|:---:|:---:|:---:|:---:|:---:|:---:|
| obsidian | ✅ | — | ✅ | ✅ | ✅ | — |
| wiki-maintainer | ✅ | — | ✅ | ✅ | ✅ | — |
| obsidian-vault-maintainer | — | — | — | — | ✅ | — |
| taskflow | ✅ | — | ✅ | ✅ | ✅ | — |
| taskflow-inbox-triage | ✅ | — | ✅ | — | ✅ | — |
| skill-creator | — | — | — | — | ✅ | — |
| clawhub | — | — | — | — | ✅ | — |
| release-skills | — | — | — | — | ✅ | — |
| github | ✅ | — | — | — | ✅ | — |
| gh-issues | ✅ | — | — | — | ✅ | — |

### 类 6：飞书生态（13 个）

| Skill | CEO | CFO | COO | CPO | CTO | Worker |
|-------|:---:|:---:|:---:|:---:|:---:|:---:|
| feishu-doc | ✅ | ✅ | ✅ | ✅ | ✅ | — |
| feishu-drive | ✅ | ✅ | ✅ | ✅ | ✅ | — |
| feishu-wiki | ✅ | ✅ | ✅ | ✅ | ✅ | — |
| feishu-perm | — | — | — | — | ✅ | — |
| feishu-bitable | ✅ | ✅ | ✅ | ✅ | ✅ | — |
| feishu-task | ✅ | — | ✅ | ✅ | ✅ | — |
| feishu-calendar | ✅ | — | ✅ | — | ✅ | — |
| feishu-create-doc | ✅ | ✅ | ✅ | ✅ | ✅ | — |
| feishu-fetch-doc | ✅ | ✅ | ✅ | ✅ | ✅ | — |
| feishu-update-doc | ✅ | ✅ | ✅ | ✅ | ✅ | — |
| feishu-im-read | ✅ | — | — | — | ✅ | — |
| feishu-troubleshoot | — | — | — | — | ✅ | — |
| feishu-channel-rules | — | — | — | — | ✅ | — |

### 类 7：基础设施（12 个）

| Skill | CEO | CFO | COO | CPO | CTO | Worker |
|-------|:---:|:---:|:---:|:---:|:---:|:---:|
| node-connect | — | — | — | — | ✅ | — |
| healthcheck | — | — | — | — | ✅ | — |
| browser-automation | ✅ | — | — | — | ✅ | — |
| diffs | — | — | — | — | ✅ | — |
| coding-agent | — | — | — | — | ✅ | — |
| model-usage | — | — | — | — | ✅ | — |
| session-logs | — | — | — | — | ✅ | — |
| weather | ✅ | — | — | — | ✅ | ✅ |
| sherpa-onnx-tts | ✅ | — | — | — | ✅ | — |
| tavily | — | — | — | — | ✅ | — |
| searxng | — | — | — | — | ✅ | — |
| prose | ✅ | — | — | — | ✅ | — |

### 类 8：企微 / QQ / 其他通讯（16 个）—— 未启用，暂不分配

企微 13 个 + QQ 3 个，全部不分配。Discord/Slack/iMessage 等 8 个也未启用。

### 类 9：未分配（34 个）—— 娱乐 / 个人 / Mac-only / 实验

不予分配。包含 spotify, sonos, apple-notes, self-improving-agent 等。

---

## 3. CXO 权限速查

| 类别 | CFO | COO | CPO |
|------|:---:|:---:|:---:|
| 通用工具 | 14 | 14 | 14 |
| 内容处理 | 2 | 2 | 2 |
| 内容创作 | 0 | 0 | 2 |
| 内容发布 | 0 | 0 | 0 |
| 知识管理 | 0 | 4 | 4 |
| 飞书生态 | 6 | 8 | 7 |
| 基础设施 | 0 | 0 | 0 |
| **合计** | **22** | **28** | **29** |

## 4. Worker 最小权限（硬编码于 openclaw.json）

```
通用工具 14 个（web_search, read, write, edit, exec, browser, canvas,
  memory_search, memory_get, session_status, process, sessions_spawn, sessions_send）
+ weather
+ baoyu-format-markdown
+ baoyu-translate
```

Worker **不应有**：内容创作、内容发布、知识管理、通讯操作、基础设施管理。

---

## 5. 实施状态

| Phase | 内容 | 状态 |
|-------|------|:---:|
| Phase 1 | 文档落地 + AGENTS.md 引用 | ✅ 已完成 |
| Phase 2 | Worker skills 白名单（openclaw.json） | ✅ 已配置 |
| Phase 3 | CXO skills 白名单（openclaw.json） | ⏳ 待配（当前 CXO 全量开放够用，按需收紧） |

---

## 6. 自研 Skill 仓库 (ai_skills)

团队自研的 Skill 统一托管在 GitHub 仓库：
- 仓库地址：`git@github.com:BryantChang1992/ai_skills.git`
- 安装方式：`npx skills add BryantChang1992/ai_skills/{skill-name}`

### 当前自研 Skill

| Skill | 类型 | 负责人 | 说明 |
|-------|------|--------|------|
| ai-wiki-maintain | 知识管理 | CTO | 知识库全生命周期维护（Ingest/Diagram/Lint/Synthesize）|
| release-skills | 基础设施 | CTO | 通用发布流程（版本检测/Changelog/GitHub Release）|

### Skill 目录结构规范

每个自研 Skill 遵循统一目录结构：

```
{skill-name}/
├── SKILL.md              ← 严格编号执行步骤（步骤 0→N）
├── scripts/              ← 确定性操作脚本（Lint/验证/导出）
├── reference/            ← 格式模板、风格色板、示例实录
└── templates/            ← Worker 任务模板（兼容保留）
```

### 脚本化原则

所有确定性操作（Lint 扫描、frontmatter 检查、SVG 验证、PNG 导出）**必须脚本化**放入 `scripts/`，禁止在 SKILL.md 中用叙述性段落描述可脚本化的逻辑。

---

## 7. 修订记录

| 版本 | 日期 | 内容 |
|------|------|------|
| v0.1 | 2026-06-06 | 初版，80 Skill + 旧组织架构 |
| v0.2 | 2026-06-06 | OpenClaw 配置示例 |
| v0.3 | 2026-06-06 | 权限矩阵 + 实施计划 |
| v0.4 | 2026-06-07 | 对齐 10 Agent 架构，126 Skill 矩阵 |
| v0.5 | 2026-06-07 | 精简为 CEO + CTO + Worker 三层 |
| v0.7 | 2026-06-18 | 新增 fireworks-tech-graph 为技术图强制 Skill（替代 baoyu-diagram 非 UML 场景）|
| v0.8 | 2026-06-21 | 自研 Skill 统一仓库 `ai_skills` 建立；`ai-wiki-maintain` 脚本化重构；新增 Skill 目录结构规范
