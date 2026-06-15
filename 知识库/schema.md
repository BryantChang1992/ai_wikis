---
type: meta
title: "知识库的结构规则"
tags: ["meta", "schema"]
created: 2026-06-14
updated: 2026-06-15 12:00
---

# 知识库的结构规则

## 三层架构

基于 Karpathy LLM Wiki 方法论，知识库分为三层：

```
知识库/
├── sources/              ← 第1层: Raw Sources（原始资料，只读，永不修改）
│   ├── README.md         ← 源文件索引
│   ├── papers/           ← 论文（每篇一个父目录）
│   │   ├── Event-Horizon/
│   │   │   ├── Event-Horizon-CIDR2026.pdf   ← 英文原文
│   │   │   ├── 精读分析.md                  ← 精读分析
│   │   │   └── 全文翻译.md                  ← 中文翻译
│   │   └── ...
│   ├── web/              ← 网页存档
│   └── notes/            ← 原始笔记
│
├── wiki/                 ← 第2层: Wiki（LLM 生成的知识，持续更新）
│   ├── 事务模型深度调研.md
│   ├── LSM-Tree.md
│   ├── synthesis/             ← 子目录：领域综述 + Lint 报告（Synthesize 产出）
│   │   ├── LSM-Tree-存储引擎体系综述.md
│   │   ├── OLAP与TSDB全景综述.md
│   │   ├── Lint-2026-06-14.md
│   │   └── ...
│   └── ...
│
├── purpose.md            ← 第3层: Schema（规则与配置）
├── schema.md             ← 本文件
├── log.md                ← 操作日志
└── README.md             ← 知识库总索引
```

### 各层角色

| 层 | 目录 | 谁读写 | 说明 |
|----|------|--------|------|
| Raw Sources | `sources/` | 人类放入，Agent 只读 | 原始资料，是知识的源头，不可修改 |
| Wiki | `wiki/` | Agent 全权维护 | LLM 生成的结构化知识，survey/concept/analysis/decision/lesson 等页面 |
| Wiki → Synthesis | `wiki/synthesis/` | Agent 全权维护 | 领域综述（synthesis）+ Lint 报告，从 wiki 网状结构提炼的元层次知识 |
| Schema | 根目录 `.md` 文件 | 人类定义，Agent 遵守 | 规则、目的、日志，定义知识库如何运作 |

### 数据流

```
sources/papers/论文名/（原文PDF+精读分析+翻译）
    ↓ Agent 读取精读分析.md 作为输入
wiki/（LLM 生成知识）
    ↓ 遵循
Schema（purpose.md + schema.md）
    ↓ 记录
log.md（操作日志）
```

## Wiki 页面分类

| 类型 | 说明 | 示例 |
|------|------|------|
| `survey` | 调研报告 — 对技术主题的系统性研究 | 事务模型深度调研 |
| `decision` | 技术决策 — 选型理由、架构变更记录 | 为什么选择 X 而不是 Y |
| `analysis` | 架构分析 — 源码阅读、系统设计拆解 | Fluss 存储引擎设计 |
| `lesson` | 踩坑记录 — 故障复盘、教训总结 | Week 04 调研踩坑 |
| `concept` | 概念卡片 — 单一技术概念的深度解释 | MVCC、LSM-Tree |
| `meta` | 元信息 — 知识库自身的说明文件 | purpose、schema、log |

## Frontmatter 模板

```yaml
---
type: survey | decision | analysis | lesson | concept | meta
title: "标题"
sources:
  - "sources/papers/论文名/论文名-会议年份.pdf"   # 英文原文 PDF
  - "sources/papers/论文名/精读分析.md"            # 精读分析
  - "sources/papers/论文名/全文翻译.md"            # 中文全文翻译（可选）
tags:
  - "标签1"
  - "标签2"
created: YYYY-MM-DD
updated: YYYY-MM-DD
status: draft | reviewed | final | deprecated
related:
  - "[[相关页面1]]"
  - "[[相关页面2]]"
---
```

### 字段说明
- **type**：必填，决定知识库如何分类和组织
- **title**：必填，人类可读的标题
- **sources**：强烈建议，指回 `sources/papers/论文名/` 下的原文 PDF + 精读分析 + 翻译
- **tags**：必填，至少 1 个标签
- **status**：`draft`（初稿）→ `reviewed`（已审核）→ `final`（定稿）→ `deprecated`（已过时）
- **related**：建议，[[wikilink]] 链接到相关知识页面

## 命名约定

- 文件名 = 标题（中文即可，Obsidian 友好）
- 避免特殊字符（`/` `\` `:` 等）
- 同类型文件用相同命名风格

## [[wikilink]] 规范

### 语法

- **页面链接**：`[[页面名]]` — 链接到同一 wiki/ vault 内的页面
- **标题链接**：`[[页面名#标题]]` — 链接到页面内具体章节
- **别名链接**：`[[页面名|显示文本]]` — 链接但显示不同文字
- 每个概念首次出现时优先用 `[[wikilink]]` 而非裸文本

### 引用完整性（强制）

每个 `[[wikilink]]` 引用必须指向 `wiki/` 或 `wiki/synthesis/` 目录下实际存在的 .md 文件。

**Lint 检查维度**：

| 问题类型 | 检测方式 | 严重度 | 处理 |
|----------|----------|--------|------|
| **Dangling 引用** | frontmatter `related` 中的 `[[页面名]]` 在 wiki/ 下无对应 .md 文件 | 🔴 阻断 | 删除该引用，或补建对应页面 |
| **重复引用** | 同一字段内同一 `[[页面名]]` 出现 ≥2 次 | 🟡 警告 | 去重，保留首次出现 |
| **循环自引** | `related` 中引用了自身页面名 | 🔴 阻断 | 删除 |
| **来源引用缺失** | `sources` 字段指向的文件在 sources/ 下不存在 | 🟡 警告 | 删除或补源 |
| **Synthesis 隔离** | wiki/ 根目录页面引用了 `[[synthesis/xxx]]`（synthesis 只能在 related 中交叉引用） | 🟡 警告 | 确认意图，通常移入 related |

**Lint 触发时机**：
1. 每次 Synthesize 任务（周五 Wiki 维护日）自动全量扫描
2. 每次 Ingest 新卡片后，增量检查新卡片的 related/sources
3. 所有 dangling 引用必须在同一次会话中修完才能 commit

**去重规则**：
- `related` 列表中有重复 `[[页面名]]` → 只保留第一个，其余删除
- 去重时忽略 `#章节` 和 `|别名` 差异（以页面名为去重 key）
- 例如 `[[事务模型深度调研]]`、`[[事务模型深度调研#MVCC章节]]`、`[[事务模型深度调研\|事务调研]]` 视为同一页面引用，只保留第一个（最完整的，通常带 `#` 锚点的优先）

### GitPage 转义规则

Obsidian wikilink 在 GitPage 上没有 Obsidian wiki 文件，所有引用必须转为原始 GitHub raw URL：

| Obsidian 引用 | GitPage 应转成 |
|--------------|---------------|
| `[[wiki/页面名]]` | `https://github.com/BryantChang1992/ai_wikis/blob/master/知识库/wiki/页面名.md` |
| `[[wiki/synthesis/页面名]]` | `https://github.com/BryantChang1992/ai_wikis/blob/master/知识库/wiki/synthesis/页面名.md` |
| `[[页面名\|别名]]` | 同上，显示别名 |
| `[[页面名#章节]]` | 同上 + `#章节锚点` |
| `sources/papers/...` | `https://github.com/BryantChang1992/ai_wikis/blob/master/知识库/sources/papers/...` |

## Agent 写入规则

1. **写前必读** `[[purpose]]` + 本文档
2. **新建页面必须**：完整 frontmatter + type 字段 + sources 指向
3. **必须更新** `README.md` 中的知识条目列表
4. **必须追加** `[[log]]` 操作记录
5. **必须检查** 是否有可关联的已有页面，加 `[[wikilink]]`
6. **写后执行** `git add -A && git commit && git push`

---

*本文件定义了知识库的"怎么做"。Agent 写入知识库时必须遵循。*

## Ingest 规则（源文件 → Wiki 卡片）

### 触发条件

| 触发方式 | 何时执行 | 执行者 |
|----------|---------|--------|
| **周报联动** | 每周技术调研周报产出后，自动执行 | CTO Agent |
| **手动触发** | CEO/CTO 指定具体文件时 | CTO Agent |
| **定时扫描** | CTO 定时检查 `sources/` 目录增量（未来） | CTO Agent |

### 执行流程

```
Step 1: 源文件入库
  周报中引用的网页/论文 → 下载 → 写入 sources/ 对应子目录
  ├── 网页 → sources/web/（以 URL slug 命名）
  └── 论文 → sources/papers/论文名/（每篇一父目录，内含 PDF+精读分析+翻译）

Step 2: 源文件索引更新
  更新 sources/README.md，追加新入库文件条目

Step 3: Ingest 分析（spawn Worker）
  CTO 读取 sources/ 新文件 → spawn Worker（rd-task）
  Worker 任务：
    1. 读取源文件全文
    2. 读取 purpose.md（了解知识库方向）+ schema.md（了解格式要求）
    3. 分析源文件：关键概念、核心观点、与已有 wiki 的关联
    4. 生成 wiki 概念卡片到 wiki/ 目录
    5. 确保每张卡片含：完整 frontmatter（type/sources/tags/status/related）+ [[wikilink]]

Step 4: 索引与日志更新
  1. 更新 README.md 知识条目列表
  2. 追加 log.md 操作记录
  3. git add -A && git commit && git push
```

### 源文件目录结构

每篇论文一个父目录（论文简称），内含三件套：英文原文 PDF + 精读分析 + 全文翻译。

```
sources/
├── README.md          ← 源文件索引（必维护）
├── web/               ← 网页存档
│   └── example-com-article.md
├── papers/            ← 论文
│   ├── Event-Horizon/
│   │   ├── Event-Horizon-CIDR2026.pdf   ← 英文原文
│   │   ├── 精读分析.md                  ← 精读分析
│   │   └── 全文翻译.md                  ← 中文翻译
│   └── ...
└── notes/             ← 原始笔记、会议记录
    └── ...
```

入库规则：
1. 论文原文 PDF 放入 `sources/papers/论文名/` 下
2. 精读分析和全文翻译作为同目录的 .md 文件
3. Agent ingest 时优先读取精读分析.md，以 PDF 为溯源引用

### 增量去重

- CTO 在 ingest 前检查 `sources/README.md` 索引，已入库的源文件不重复处理
- 未来可升级为 SHA256 checksum 自动去重

### Worker 配置

- 模型: `qwenProvider/qwen3-coder-plus`
- 一次 ingest 处理 1 个源文件
- 生成 1～N 张 wiki 概念卡片（取决于源文件信息密度）
- 每张卡片独立 commit，便于回滚

---

## Synthesize 规则（网状结构 → 领域提炼）

### 目标

当 wiki 卡片积累到一定数量后，卡片间的 [[wikilink]] 会自然形成**概念集群**。定时扫描这些集群，提炼出更高层次的领域综述页，避免知识碎片化。

### 触发条件

| 触发方式 | 频率 | 执行者 |
|----------|------|--------|
| **定时扫描** | 每周五 10:00 CST（Wiki 维护日，周四周报产出后） | CTO Agent |
| **手动触发** | CEO/CTO 意图触发 | CTO Agent |

### 执行流程

```
Step 1: 集群发现
  CTO Agent 扫描 wiki/ 目录：
  1. 读取 README.md 索引，获取所有页面清单
  2. 解析所有页面的 frontmatter（related / tags）
  3. 通过 [[wikilink]] 关系 + tag 共现 发现概念集群
  4. 输出集群识别结果（每个集群的页面列表 + 核心概念）

Step 2: 领域提炼分析
  对每个集群：
  1. 读取集群内所有页面全文
  2. 提取跨页面的共同主题、矛盾、互补关系
  3. 识别缺失的连接（应建立但未建立的 [[wikilink]]）
  4. 判断该集群是否已达到"需要一张综述页"的临界质量

Step 3: 生成合成页
  对达到临界质量的集群，生成一张 type: synthesis 页面到 `wiki/synthesis/` 目录：
  - 标题格式: "{领域名}综述" 或 "{主题}体系"
  - 内容: 领域定义 → 核心概念关系图（文本）→ 子主题展开 → 待探索方向
  - sources: 引用集群内所有相关 wiki 页面
  - related: 交叉引用相关集群
  - status: draft（后续可升级为 reviewed）

Step 4: 健康检查 (Lint)
  在提炼过程中同步执行：
  1. 孤儿页面检测：哪些页面没有任何 inbound [[wikilink]]
  2. 矛盾检测：不同页面对同一事物的描述是否矛盾
  3. 过时检测：状态为 draft > 30 天未更新的页面
  4. 缺口检测：集群中常见概念缺少对应页面的
  5. 输出 lint 报告到 `wiki/synthesis/`

Step 5: 索引更新
  1. README.md 新增 "领域综述" 分类，列出 synthesis 页面
  2. 追加 log.md 操作记录
  3. git add -A && git commit && git push
```

### 页面类型扩展

| 新增类型 | 说明 | 示例 |
|----------|------|------|
| `synthesis` | 领域综述 — 从网状结构提炼的高层领域知识 | 存储引擎体系综述、分布式一致性全景 |

### 临界质量判断

一个概念集群达到以下任一条件即认为可以生成 synthesis 页：
- 集群内页面数 ≥ 5
- 集群内涉及 ≥ 2 个不同的 type（如 survey + concept 同时出现）
- 集群内至少 1 个页面的 status 为 final，且相关页面 ≥ 3

### 定时任务配置

- CTO HEARTBEAT.md 中配置定时任务
- 频率: 每周五 10:00 CST（Wiki 维护日）
- 动作: 扫描 wiki 网状结构 → 执行 Synthesize 流程（含增量更新检查，见下文）

---

## 综述增量更新机制（Synthesis Refresh）

### 问题

Synthesis 不是静态文档。wiki 卡片持续增长（当前 51 张且每周增加），已有综述页面临两个风险：
1. **内容过时**：新卡片带来了旧综述没有覆盖的子主题或新观点
2. **连接断裂**：新卡片与旧综述之间缺乏 [[wikilink]] 双向引用

### 触发条件

| 触发方式 | 频率 | 条件 |
|----------|------|------|
| **定时扫描** | 每周五 10:00 CST Wiki 维护日，Synthesize 时一并执行 | 对每一张已存在的 synthesis 页做增量评估 |
| **事件驱动** | 同一领域新增 ≥ 3 张概念卡片时 | 立即标记对应 synthesis 为 `status: draft`，触发下一轮更新 |
| **手动触发** | CTO 判断某领域变化显著 | 直接启动单领域 refresh |

### 增量检测信号

在每周五 Wiki 维护日的定时扫描中，对每张已有 synthesis 页做以下检查：

| 信号 | 检测方式 | 阈值 | 动作 |
|------|----------|------|------|
| **新页面注入** | synthesis 的 `sources`/`related` 列表 vs wiki/ 全部页面 — 同一 tag 族下是否有未被引用的新页面 | ≥ 2 张新页面 | 标记需更新 |
| **连接变化** | 旧 synthesis 引用的页面中，是否有新增了 [[wikilink]] 到其他 synthesis 未覆盖页面的 | 任意 | 记录为潜在新关系 |
| **状态升级** | synthesis 引用的页面中是否有 `draft → reviewed → final` 的状态变化 | 任意 | 更新引用页面的描述准确度 |
| **Lint 触发** | 旧 synthesis 中是否出现了 dangling 引用（引用的页面被删除/重命名） | ≥ 1 | 🔴 必须立即修复 |
| **时间衰减** | synthesis 的 `updated` 字段距今 | > 30 天 | 🟡 标记过时，即使无其他信号也要人工确认 |

### 更新决策矩阵

| 信号组合 | 决策 | 执行方式 |
|----------|------|----------|
| 新页面 ≥ 3 且含新的 type（如新出现 analysis 类型） | **重写** — 领域结构已变化，需要重新组织全文 | CTO 自己执行 |
| 新页面 1-2 张，无新 type | **增量追加** — 在原 synthesis 中追加子章节或补充段落 | CTO 自己执行 |
| 仅有状态升级 / 连接变化 | **局部修订** — 更新相关段落和 frontmatter | CTO 自己执行 |
| 仅有 dangling 引用 | **快速修复** — 删除失效引用，无需改正文 | CTO 自己执行 |
| 时间衰减 > 30 天且无其他信号 | **确认无变更** — 仅更新 `updated` 时间戳，标记 status 不变 | CTO 自己执行 |

### 更新执行流程

```
Step 1: 信号检测
  对 synthesis/ 下每张页面：
  1. 提取 sources/related 中的引用列表
  2. 与当前 wiki/ 全部页面做 diff
  3. 生成每张 synthesis 的「变更信号清单」

Step 2: 决策
  按决策矩阵判定每张 synthesis 的更新策略
  输出：本次需更新的 synthesis 列表 + 每张的变更摘要

Step 3: 执行更新
  按优先级执行（重写 > 增量追加 > 局部修订 > 快速修复）
  每张 synthesis 更新后：
    1. 更新 frontmatter updated 字段
    2. 如为增量/重写，追加或更新「变更记录」章节（见下）
    3. 确保新增页面的 [[wikilink]] 已加入 sources/related

Step 4: 关联修复
  新加入 synthesis 的 wiki 页面，在其自身 frontmatter 中追加该 synthesis 的 [[wikilink]]

Step 5: 提交
  git commit 格式: "synthesis-refresh: {页面名} — {变更摘要}"
```

### 变更记录（Changelog）

每张 synthesis 页面末尾必须维护变更历史段落，格式如下：

```markdown
## 变更记录

| 日期 | 动作 | 变更说明 |
|------|------|----------|
| 2026-06-14 | 创建 | 初始版本，覆盖 X 个页面 |
| YYYY-MM-DD | 增量更新 | 新增 [[新页面A]]、[[新页面B]]，补充 C 领域分析 |
| YYYY-MM-DD | 重写 | 因 D 领域新类型页面出现，重构全文结构 |
```

### 提醒：Synthesis 始终由 CTO 执行

Synthesis refresh 与首次 synthesis 一样，是 **IO 密集 + 跨页推理** 任务，Worker 超时不够。所有 synthesis 的创建和更新均由 CTO Agent 自己执行。

---

## 知识网络分层与 Lint 范围

### 核心原则

**知识网络只存在于 wiki 层。** raw 层的 [[wikilink]] 是写作时的随意引用，不应在 Lint 中检查。元信息文件是导航工具，不是知识节点。

### 三类文件

| 分类 | 目录/文件 | 角色 | wikilink 处理 | Lint 规则 |
|------|----------|------|--------------|-----------|
| **A 类：知识节点** | `wiki/*.md`、`wiki/synthesis/*.md` | 知识网络核心，互相引证 | ✅ 所有 wikilink 有效 | 全量：dangling、重复、循环自引 |
| **B 类：工具索引** | `README.md`、`sources/README.md`、`log.md`、`purpose.md`、`schema.md` | 纯导航/清单，不参与知识推理 | ⚠️ 允许使用 [[wikilink]] 但不检查 | 不参与 Lint |
| **C 类：原始资料** | `sources/papers/**`、`sources/web/**`、`sources/notes/**` | 只读层，来源可溯 | ❌ 不检查，不视为网络节点 | 不参与 Lint |

### 连接方向

```
C 类 (sources/)
  ↕ sources 字段（文件路径，非 wikilink）
A 类 (wiki/)
  ↕ related + sources（[[wikilink]]）
A 类 (wiki/synthesis/)
  ↕ [[wikilink]] 导航（非检查）
B 类 (README 等)
```

规则：
1. A 类 → C 类：通过 `sources` 字段引用文件路径（如 `sources/papers/Event-Horizon/精读分析.md`），不是 [[wikilink]]
2. A 类 ↔ A 类：通过 frontmatter `related` + 正文 [[wikilink]] 连接，全量 Lint
3. B 类 → A 类：可用 [[wikilink]] 做导航，不检查有效性
4. B 类 → C 类：可用文件路径做导航
5. C 类内 [[wikilink]]：允许存在但不检查，不修复

### 旧有 raw 层 wikilink 处理

sources/papers/ 下精读分析和翻译文件中现有的 [[wikilink]] 引用**全部不检查、不修复**。它们是写作时的原始笔记，与 wiki 网络没有强制一致性要求。未来新写入的 raw 层文件也遵循此规则。

### README.md 定位

READER.md 不是知识节点，是**导航索引页**：
- 不参与 wikilink 网络（不被 B 类以外的文件 [[wikilink]] 引用）
- 不被 Lint 扫描
- 内部可用 [[wikilink]] 列出 wiki 页面清单
- Agent 写入 wiki 新卡片时仍需更新 README.md，但 README 的正确性依赖 Agent 遵守规范，而非 Lint 自动检查
