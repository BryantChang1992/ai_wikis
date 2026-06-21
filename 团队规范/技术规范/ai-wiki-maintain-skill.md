---
type: meta
title: "AI Wiki Maintain Skill 规范"
tags:
  - skill
  - wiki
  - 技术规范
created: 2026-06-21
updated: 2026-06-21
status: reviewed
related:
  - "[[skill-isolation-and-sharing]]"
  - "[[画图规范]]"
---

# AI Wiki Maintain Skill

> 知识库全生命周期维护 skill 规范文档。触发: "入库" "wiki维护" "知识库更新" "ingest论文" "生成综述" "wiki lint" "知识库清理"。

## 前置依赖

本 skill 依赖 `fireworks-tech-graph` skill 生成所有 UML 技术图。

```bash
npx skills add yizhiyanhua-ai/fireworks-tech-graph
```

## 知识库根路径

```
work/ai_wikis/知识库/
```

核心文件：

| 文件 | 作用 |
|------|------|
| `purpose.md` | 知识库方向与灵魂 |
| `schema.md` | 结构规则（三层架构、frontmatter、wikilink、Lint） |
| `README.md` | 知识库总索引 |
| `log.md` | 操作日志 |
| `wiki/` | 概念卡片 + synthesis 综述 |
| `wiki/diagram/` | SVG + PNG 技术图 |
| `sources/` | 原始资料（只读） |

---

## 完整工作流

```
触发（CEO 指令 / 定时任务）
    │
    ├── 1. 源文件入库 ─── 论文/网页 → sources/ + 索引
    │
    ├── 2. Ingest ──────── spawn Worker 拆概念卡片
    │        │               │
    │        │               ├── CTO review Worker 产出
    │        │               ├── 有问题 → 打回重做
    │        │               └── 通过 → 继续
    │        │
    │        ├── 2a. 精读分析 ─── CTO 自产（如尚不存在）
    │        │
    ├── 3. Diagram ─────── CTO 用 fireworks-tech-graph 生成 UML 图
    │        │               (Style 1 Flat Icon, 浅色背景)
    │        │
    ├── 4. Lint ────────── wikilink 完整性 / frontmatter / 孤儿页
    │        │               (增量: 仅新卡片 / 全量: 周五)
    │        │
    ├── 5. Synthesize ──── CTO 自执行 生成/更新领域综述
    │        │               │
    │        │               └── IO 密集 + 跨页推理，Worker 超时不够
    │        │
    └── 6. Commit ──────── git add/commit/push + log.md + MEMORY.md
```

### 触发矩阵

| 场景 | 执行范围 | 触发方式 |
|------|---------|---------|
| CEO 指定论文入库 | 1 → 2 → 3 → 4(增量) → 6 | CEO 指令 |
| CEO 指定文章入库 | 1 → 2 → 3 → 6 | CEO 指令 |
| 已有精读分析，只需拆卡 | 2 → 3 → 4(增量) → 6 | CEO 指令 |
| 已有卡片，需配图 | 3 → 6 | CTO 判断 / CEO 指令 |
| 每周五 Wiki 维护 | 4(全量) → 5 → 6 | HEARTBEAT 定时 |
| ASCII 残留自动修复 | 3 → 6 | Lint 阶段自动触发 |

---

## 1. 源文件入库

### 1.1 论文入库

```
sources/papers/{论文简称}/
├── {论文简称}-{会议}{年份}.pdf   ← 英文原文
├── 精读分析.md                  ← CTO 自产（如不存在则先写）
└── 全文翻译.md                  ← 可选
```

CTO 先写精读分析（如尚不存在），然后进入 Ingest。

### 1.2 更新 sources/README.md

在 `sources/README.md` 的对应子目录表格中追加一行。

---

## 2. Ingest（拆概念卡片）

### 2.1 Worker 配置

```yaml
runtime: subagent
mode: run
model: qwenProvider/qwen3-coder-plus
context: isolated
timeout: 10 min
```

### 2.2 Worker 任务

每个 Worker 处理 **1 篇论文**，产出 **1~N 张概念卡片**。

Worker 必须先读 `purpose.md` + `schema.md` 理解规则：
- 每张卡片含完整 frontmatter（type/sources/tags/status/created/related）
- 卡片文件直接写入 `wiki/` 目录
- 超时 10 分钟

### 2.3 CTO Review 清单

Worker 返回后，CTO 逐卡检查：

- [ ] frontmatter 字段完整（type/sources/tags/status/created/related）
- [ ] **无重复 YAML key**（特别是 `created` 不能出现两次）
- [ ] `sources` 指向实际存在的文件（`sources/` 前缀的文件路径，非 [[wikilink]]）
- [ ] `related` 的 [[wikilink]] 引用已有页面（非凭空捏造）
- [ ] `related` 中 **无重复 [[wikilink]] 引用**
- [ ] 内容非纯摘要——含论文章节号、公式、对比数据等深度信息
- [ ] 无 ASCII box-drawing 图（`┌└├│─`）——如有则标记待替换
- [ ] tags 至少一个领域标签

**打回规则**：3 项以上不通过 → CTO 给出具体修改指令 → Worker 重做

---

## 3. Diagram（UML 技术图）

### 3.1 工具链

所有图用 `fireworks-tech-graph` skill 生成。

### 3.2 风格规范

**统一使用 Style 1 (Flat Icon)**：白色背景、tinted 彩色组件框、蓝色系数据流箭头。

| 属性 | 值 |
|------|-----|
| 背景 | `#ffffff` |
| 组件框 | `rx="8"` 圆角，tinted 背景色（`#eff6ff` / `#f0fdf4` / `#faf5ff` / `#fff7ed` 等） |
| 文字 | `#111827`（主标题）/ `#6b7280`（副标签） |
| 箭头 | `stroke-width="1.5"`，颜色按语义：蓝=数据流、绿=存储/持久化、紫=计算/查询、红=异常/Compaction |
| 字体 | `Helvetica Neue, Arial, PingFang SC, Microsoft YaHei, sans-serif` |

> **为什么不用 Dark Terminal（Style 2）？** 浅色背景在 GitHub README、飞书文档、GitPage 上阅读体验更佳，可读性更强，适合知识库长期维护。（决策日期：2026-06-19）

### 3.3 产出要求

每张图同时产出 SVG + PNG @2x：

```bash
# 验证 SVG
python3 -c "import xml.etree.ElementTree as ET; ET.parse('file.svg')"

# 导出 PNG @2x (rsvg-convert)
rsvg-convert -w {2x宽度} -o output.png input.svg
```

存储位置：`wiki/diagram/{主题-slug}.svg` + `{主题-slug}.png`

### 3.4 引用方式

Wiki 卡片中用 Markdown 图片语法（非 Obsidian embed）：

```markdown
![Architecture Diagram](../diagram/{主题-slug}.svg)
```

### 3.5 配图优先级

| 优先级 | 范围 | 触发 |
|--------|------|------|
| **P0** | 所有 `wiki/synthesis/*.md` 综述页 | 每张至少 1 张主图 |
| **P1** | 架构性强、有对比关系的概念卡片 | Ingest 时判断 |
| **P2** | 其余概念卡片 | 按需 |

### 3.6 ASCII 残留检测

每次 Lint 阶段扫描 wiki 卡片中是否含 box-drawing 字符：

```bash
grep -rl '[┌└├│─]' wiki/*.md
```

发现则标记为"待替换"，列入当前 session 的 diagram 生成任务。

---

## 4. Lint（一致性检查）

### 4.1 增量 Lint（每次 Ingest 后）

仅检查新卡片的 frontmatter + [[wikilink]] + sources 引用。

### 4.2 全量 Lint（每周五 Wiki 维护日）

扫描维度：

| 检查项 | 规则 | 严重度 |
|--------|------|--------|
| Dangling wikilink | `related` 中的 [[页面名]] 在 wiki/ 下无对应 .md | 🔴 阻断 |
| 重复引用 | 同一字段内同一页面名出现 ≥2 次 | 🟡 警告 |
| 循环自引 | `related` 中引用了自身 | 🔴 阻断 |
| 来源缺失 | `sources` 指向的文件不存在 | 🟡 警告 |
| ASCII 残留 | 含 `┌└├│─` 字符 | 🟡 警告 |
| 孤儿页面 | 无任何 inbound [[wikilink]] 的卡片 | 🟡 警告 |
| 过时卡片 | status=draft 且 updated > 30 天 | 🔵 提示 |
| Diagram 断链 | `![[diagram/xxx.svg]]` 引用不存在 | 🔴 阻断 |
| **重复 YAML key** | frontmatter 中间一 key 出现 ≥2 次 | 🔴 阻断 |

Lint 报告输出到 `wiki/synthesis/Lint-YYYY-MM-DD.md`。

---

## 5. Synthesize（领域综述）

### 5.1 CTO 自执行

Synthesize 是 **IO 密集 + 跨页推理** 任务，Worker 超时不够。所有 synthesis 的创建和更新均由 CTO Agent 自己执行。

触发条件：

| 条件 | 说明 |
|------|------|
| 集群页面 ≥ 5 | 同 tag 族的页面达到临界质量 |
| 集群含 ≥ 2 个 type | 如 survey + concept 同时出现 |
| 定时扫描 | 每周五全量扫描 |

### 5.2 CTO Review 清单

- [ ] 综述覆盖了集群所有关键子主题
- [ ] 引用了所有相关 wiki 页面的 [[wikilink]]
- [ ] frontmatter 完整：type=synthesis, sources, tags, status, created, updated, related
- [ ] **无重复 YAML key**（特别是 `created`）
- [ ] **related 中无重复 [[wikilink]]**
- [ ] 有"待探索方向"章节
- [ ] 变更记录（Changelog）已更新
- [ ] 配图完整（至少 1 张主图）

### 5.3 增量更新（Refresh）

对已有 synthesis 页做增量检测：

| 信号 | 阈值 | 动作 |
|------|------|------|
| 新页面 ≥ 3 且含新 type | 重写 | CTO 重新生成 |
| 新页面 1-2 张 | 增量追加 | CTO 追加子章节 |
| 仅状态升级/连接变化 | 局部修订 | CTO 直接修改 |
| Dangling 引用 | 快速修复 | CTO 直接删除失效引用 |
| updated > 30 天 | 确认无变更 | CTO 更新时间戳 |

---

## 6. Commit & Push

### 6.1 Commit Message 格式

```
{type}({scope}): {简短描述}

{详细说明——改了什么、为什么}
```

| type | 用途 |
|------|------|
| `feat` | 新论文入库、新卡片、新综述 |
| `fix` | Lint 修复、格式修正、ASCII 替换 |
| `refactor` | 卡片重命名、结构调整 |
| `docs` | README/log/schema 更新 |
| `style` | Diagram 风格统一、配色调整 |

scope 使用知识库模块名：`wiki`, `sources`, `diagram`, `synthesis`, `lint`

### 6.2 Commit 流程

```bash
cd work/ai_wikis
git pull --rebase
git add -A
git status  # 确认变更范围
git commit -m "{message}"
git push
```

### 6.3 Commit 后动作

1. **更新 log.md**：追加操作记录（时间/操作类型/描述/commit hash）
2. **更新 MEMORY.md**：记录重要决策或知识体系变化
3. **更新 HEARTBEAT.md**：如需调整定时任务规则

---

## 7. 定时任务

### 每周四 10:00 CST — GitPage 技术调研周报

> 不在本 skill 范围内。由 HEARTBEAT.md 的周报流程独立执行。

### 每周五 10:00 CST — Wiki 维护日

本 skill 的完整流程执行：

1. **Lint 全量扫描** → 输出 `Lint-YYYY-MM-DD.md`
2. **修复所有阻断级问题**（dangling、循环自引、diagram 断链、重复 YAML key、重复引用）
3. **Synthesize Refresh** — 对已有综述做增量更新
4. **集群发现** — 检查是否有新集群达到临界质量 → 生成新综述
5. **Commit & Push**

---

## 8. Worker 管理

### 8.1 Worker 类型

| 标签 | 用途 | 超时 |
|------|------|------|
| `rd-task` | 拆概念卡片 | 10 min |
| `rd-task` | 生成综述 | 15 min |

模型统一：`qwenProvider/qwen3-coder-plus`

### 8.2 并行策略

- Ingest 拆卡：**按论文并行**（1 篇论文 = 1 Worker）
- Synthesize：**按集群串行**（集群间有 [[wikilink]] 依赖，逐集群生成）
- Diagram 生成：**CTO 串行**（每张图需要 review 视觉质量）

---

## 9. 故障恢复

| 故障场景 | 恢复方式 |
|----------|---------|
| Worker 超时（10min） | spawn 新 Worker 重试；同一任务连续 2 次超时 → CTO 亲自执行 |
| Worker 产出质量差（3+ review 项不通过） | 打回 + 给具体修改指令；同一 Worker 2 次打回 → CTO 亲自执行 |
| git push 冲突 | `git pull --rebase` 解决冲突后重推 |
| SVG 渲染异常 | 检查 `@import url()`（cairosvg 不支持外部请求）、检查 marker 引用完整性、用 `validate-svg.sh` 诊断 |
| Diagram 内容覆盖/重叠 | 增大 viewBox、调整元素间距、移开 legend |

---

## 10. 与 schema.md 的关系

本 skill 是 schema.md 的**操作层规范**。schema.md 定义"知识库的结构规则（是什么）"，本 skill 定义"如何执行维护操作（怎么做）"。两者是正交互补关系：

| | schema.md | ai-wiki-maintain skill |
|------|-----------|----------------------|
| **定位** | 知识库结构宪法 | 维护操作 SOP |
| **读者** | Agent（写卡片时参考）| CTO Agent（维护时执行）|
| **内容** | 三层架构、frontmatter 模板、wikilink 规范、Lint 规则 | Ingest → Diagram → Lint → Synthesize → Commit 完整流程 |
| **触发** | 每次写 wiki 卡片 | 每次 wiki 维护操作 |

---

*本文件定义了知识库维护的"怎么做"。CTO 在每次 wiki 维护操作前加载此 skill。*

*源文件路径: `~/.agents/skills/ai-wiki-maintain/SKILL.md`*
