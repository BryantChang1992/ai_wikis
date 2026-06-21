---
name: ai-wiki-maintain
description: >-
  CHANG_AI_TEAM 知识库全生命周期维护：Ingest（论文/文章→概念卡片）、
  Diagram（UML 技术架构图）、Lint（wikilink/格式一致性）、
  Synthesize（网状结构→领域综述）、Git 提交与日志。
  触发: "入库" "wiki维护" "知识库更新" "ingest论文" "生成综述"
  "wiki lint" "知识库清理"。
---

# 知识库维护 Skill

## 前置

1. 确认 `fireworks-tech-graph` skill 已安装
2. 知识库根路径：`work/ai_wikis/知识库/`
3. 核心规则文件：`purpose.md`（方向）、`schema.md`（结构规则）、`README.md`（索引）、`log.md`（日志）

---

## 步骤 0：选择执行模式

| 模式 | 入口 | 执行步骤 |
|------|------|---------|
| **论文入库** | CEO 指定论文 | 0 → 1 → 2 → 3 → 4 → 5 |
| **文章入库** | CEO 指定网页/文章 | 0 → 1 → 2 → 3 → 5 |
| **拆卡** | 已有精读分析 | 0 → 2 → 3 → 4 → 5 |
| **配图** | 已有卡片缺图 | 0 → 3 → 5 |
| **周五维护** | HEARTBEAT 定时 | 0 → 4 → 5 |

---

## 步骤 1：源文件入库

### 1.1 写入文件到 sources/

论文：
```bash
mkdir -p sources/papers/{论文简称}
# {论文简称}-{会议}{年份}.pdf → sources/papers/{论文简称}/
```

网页：
```bash
# URL slug 命名 → sources/web/{slug}.md
```

### 1.2 更新 sources/README.md

在对应子目录表格追加一行。

### 1.3 如无精读分析，CTO 自产精读分析

写入 `sources/papers/{论文简称}/精读分析.md`，要求含论文信息、核心贡献、章节拆解。

---

## 步骤 2：Ingest（拆概念卡片）

### 2.1 判断拆分粒度

| 核心概念数 | 策略 |
|-----------|------|
| ≤ 3 | 合并为 1 张卡片 |
| 3~6 | 每个独立概念 1 张卡片 |
| > 6 | 拆最重要的 6 个，其余合并 |

### 2.2 Spawn Worker

配置：`model=qwenProvider/qwen3-coder-plus`, `context=isolated`, `mode=run`, `timeout=10min`

Worker 任务模板见 `reference/worker-task-template.md`。每个 Worker 处理 1 篇论文，产出 1~N 张卡片写入 `wiki/`。

Worker 必须先读 `purpose.md` + `schema.md`。

### 2.3 CTO Review

逐卡逐项检查：

- [ ] frontmatter 字段完整（`type`/`title`/`sources`/`tags`/`status`/`created`/`related`）
- [ ] 无重复 YAML key（`scripts/lint-frontmatter.sh`）
- [ ] `sources` 指向 `sources/` 下实际存在的文件
- [ ] `related` [[wikilink]] 引用已有页面，无凭空捏造
- [ ] `related` 无重复 [[wikilink]] 引用
- [ ] 含论文章节号、公式、对比数据等深度信息
- [ ] tags 至少一个领域标签
- [ ] 无 ASCII box-drawing 字符（`┌└├│─`）

**打回规则**：3 项以上不通过 → 给出具体修改指令 → Worker 重做。同一 Worker 2 次打回 → CTO 亲自执行。

### 2.4 更新索引

更新 `README.md` 知识条目列表。追加 `log.md` 操作记录。

---

## 步骤 3：Diagram（技术图）

### 3.1 工具

`fireworks-tech-graph` skill。风格参数见 `reference/diagram-style.md`。

统一使用 **Style 1 (Flat Icon)**：浅色背景 `#ffffff`，tinted 组件框，蓝色系数据流箭头。

### 3.2 产出

```
wiki/diagram/{主题-slug}.svg   ← 矢量源文件
wiki/diagram/{主题-slug}.png   ← PNG @2x
```

### 3.3 验证

```bash
scripts/validate-diagram.sh {主题-slug}
```

### 3.4 引用

Wiki 卡片中用 Markdown 图片语法：
```markdown
![Architecture Diagram](../diagram/{主题-slug}.svg)
```

### 3.5 优先级

| 优先级 | 范围 | 触发 |
|--------|------|------|
| P0 | 所有 `wiki/synthesis/*.md` | 每张至少 1 张主图 |
| P1 | 架构性强、有对比关系的概念卡片 | Ingest 时判断 |
| P2 | 其余概念卡片 | 按需 |

---

## 步骤 4：Lint & Synthesize

### 4.1 Lint

**增量 Lint**（每次 Ingest 后）：

```bash
scripts/lint-incremental.sh {new_card_file}
```

**全量 Lint**（周五维护日）：

```bash
scripts/lint-full.sh
```

检查维度：

| # | 检查项 | 规则 | 严重度 |
|---|--------|------|--------|
| 1 | Dangling wikilink | `related` [[页面名]] 在 wiki/ 下无对应 .md | 🔴 阻断 |
| 2 | 重复 YAML key | frontmatter 同 key 出现 ≥2 次 | 🔴 阻断 |
| 3 | 循环自引 | `related` 引用自身 | 🔴 阻断 |
| 4 | Diagram 断链 | `](../diagram/xxx.svg)` 文件不存在 | 🔴 阻断 |
| 5 | 重复 [[wikilink]] | 同字段内同页面名 ≥2 次 | 🟡 警告 |
| 6 | 来源缺失 | `sources` 指向文件不存在 | 🟡 警告 |
| 7 | ASCII 残留 | 含 `┌└├│─` 字符 | 🟡 警告 |
| 8 | 孤儿页面 | 无任何 inbound [[wikilink]] | 🟡 警告 |
| 9 | 过时卡片 | status=draft 且 updated > 30 天 | 🔵 提示 |

全量 Lint 报告输出到 `wiki/synthesis/Lint-YYYY-MM-DD.md`。

**所有 🔴 阻断项必须在同一 session 内修复完毕才能 commit。**

### 4.2 Synthesize

由 CTO 自执行（IO 密集 + 跨页推理，Worker 超时不够）。

触发条件：集群页面 ≥ 5 **或** 集群含 ≥ 2 个 type。

CTO Review 清单：
- [ ] 覆盖集群所有关键子主题
- [ ] 引用所有相关 wiki 页面 [[wikilink]]
- [ ] frontmatter type=synthesis，字段完整无重复
- [ ] 有"待探索方向"章节
- [ ] 变更记录（Changelog）已更新
- [ ] 配图完整（至少 1 张主图）

### 4.3 Synthesis Refresh（增量更新）

| 信号 | 阈值 | 动作 |
|------|------|------|
| 新页面 ≥ 3 且含新 type | 重写 | CTO 重新生成 |
| 新页面 1-2 张 | 增量追加 | CTO 追加子章节 |
| 仅状态升级/连接变化 | 局部修订 | CTO 直接修改 |
| Dangling 引用 | 快速修复 | CTO 删除失效引用 |
| updated > 30 天 | 确认无变更 | CTO 更新时间戳 |

---

## 步骤 5：Commit & Push

### 5.1 执行

```bash
cd work/ai_wikis
git pull --rebase
git add -A
git status                       # ⚠️ 确认变更范围
git commit -m "{message}"
git push
```

### 5.2 Commit 格式

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

scope：`wiki`, `sources`, `diagram`, `synthesis`, `lint`

示例见 `reference/commit-examples.md`。

### 5.3 Commit 后动作

- [ ] 更新 `log.md`
- [ ] 更新 `MEMORY.md`
- [ ] 更新 `HEARTBEAT.md`（如需调整定时规则）

---

## 步骤 6：定时任务

### 每周五 10:00 CST — Wiki 维护日

1. 执行 `scripts/lint-full.sh` → 输出 `wiki/synthesis/Lint-YYYY-MM-DD.md`
2. 修复所有 🔴 阻断项
3. 对已有 synthesis 执行 Refresh 检测
4. 集群发现 → 新集群达临界质量则生成 synthesis
5. 执行步骤 5（Commit & Push）

---

## 故障恢复

| 故障场景 | 恢复方式 |
|----------|---------|
| Worker 超时（10min） | spawn 新 Worker 重试；连续 2 次超时 → CTO 亲自执行 |
| Worker 产出质量差 | 打回 + 具体修改指令；同一 Worker 2 次打回 → CTO 亲自执行 |
| git push 冲突 | `git pull --rebase` 后重推 |
| SVG 渲染异常 | 执行 `scripts/validate-diagram.sh` 诊断 |
| Diagram 元素重叠 | 增大 viewBox、调整间距、移开 legend |

---

## 目录结构

```
ai-wiki-maintain/
├── SKILL.md                    ← 本文件（执行步骤）
├── scripts/
│   ├── lint-full.sh            ← 全量 Lint 扫描
│   ├── lint-incremental.sh     ← 增量 Lint（新卡片）
│   ├── lint-frontmatter.sh     ← frontmatter 完整性检查
│   └── validate-diagram.sh     ← SVG 语法验证 + PNG 导出
├── reference/
│   ├── diagram-style.md        ← Diagram 风格色板与参数
│   ├── commit-examples.md      ← Commit message 格式示例
│   ├── frontmatter-template.md ← Frontmatter 字段模板与示例
│   ├── worker-task-template.md ← Worker Ingest 任务模板
│   ├── worker-synthesis-template.md ← Worker Synthesis 任务模板
│   └── ingest-example.md       ← 完整 Ingest 流程实录
└── templates/
    ├── worker-task.md          ← [保留兼容] 旧模板
    ├── worker-synthesis.md     ← [保留兼容] 旧模板
    └── ingest-example.md       ← [保留兼容] 旧示例
```
