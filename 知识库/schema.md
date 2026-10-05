---
type: meta
title: 知识库的结构规则
tags:
- meta
- schema
created: 2026-06-14
updated: '2026-10-05'
---

# 知识库的结构规则

> **v2 升级 (2026-07-05)**：基于 [CentiMatrix/karpathy-llm-wiki-v2](https://github.com/CentiMatrix/karpathy-llm-wiki-v2) 引入置信度评分、实体提取 (.entities.json)、迭代覆盖 (Supersession)、遗忘机制 (Forgetting)。详细操作流程见 `ai-wiki-maintain` skill v2。

## 四层架构（v2 升级）

基于 Karpathy LLM Wiki 方法论，知识库分为四层：

```
知识库/
├── sources/              ← 第1层: 原始资料 + 可修订分析（权限见下表）
│   ├── README.md         ← 源文件索引
│   ├── papers/           ← 论文（每篇一个父目录）
│   │   ├── Event-Horizon/
│   │   │   ├── Event-Horizon-CIDR2026.pdf   ← 英文原文
│   │   │   ├── 精读分析.md                  ← 精读分析
│   │   │   └── 全文翻译.md                  ← 译文（标明覆盖范围）
│   │   └── ...
│   ├── web/              ← 网页存档
│   └── notes/            ← 原始笔记
│
├── wiki/                 ← 第2层: Wiki（LLM 生成的知识，持续更新）
│   ├── .entities.json         ← v2 新增：结构化实体图谱（实体+关系）
│   ├── 事务模型深度调研.md
│   ├── LSM-Tree.md
│   ├── synthesis/             ← 子目录：领域综述 + Lint 报告
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
| 原始资料 | `sources/` 中的原文 PDF、网页存档 | 保留原件 | 不把精读稿的结论反写成原文；错配/拦截页必须标识，正确原件另行核验 |
| 派生分析 | `sources/**/精读*.md`、译文与技术摘录 | 可修订，保留 Git 历史 | 可纠错与补深度；译述、选译和全文翻译必须区分 |
| Wiki | `wiki/` | Agent 全权维护 | LLM 生成的结构化知识，survey/concept/analysis/decision/lesson 等页面 |
| Wiki → Entities | `wiki/.entities.json` | Agent 全权维护 | **v2 新增**：结构化实体图谱，存储概念/项目/机制及其关系 |
| Wiki → Synthesis | `wiki/synthesis/` | Agent 全权维护 | 领域综述 + Lint 报告，从 wiki 网状结构提炼的元层次知识 |
| Schema | 根目录 `.md` 文件 | 人类定义，Agent 遵守 | 规则、目的、日志，定义知识库如何运作 |

### 数据流（v2）

```
sources/papers/论文名/（原文PDF+精读分析+翻译）
    ↓ Agent 读取精读分析.md 作为输入
wiki/（LLM 生成知识 + 置信度标注）
    ↓ Agent 提取实体
wiki/.entities.json（结构化实体 + 关系图谱）
    ↓ 遵循
Schema（purpose.md + schema.md）
    ↓ 记录
log.md（操作日志）
    ↓ 定期检查
Confidence Decay + Supersession Detection（每周五维护日）
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

### 标签体系指导

领域标签（建议每张卡至少 1 个），Agent 写入时参考此表，新领域出现后自动加入：

| 领域 tag | 适用卡片举例 |
|----------|-------------|
| `存储引擎` | LSM-Tree 系、Doris 存储层、InfluxDB TSM |
| `流处理` | 流处理系、Dataflow、Fluss |
| `OLAP` | Doris 系 |
| `时序数据库` | InfluxDB 系 |
| `事务` | 事务模型调研、CockroachDB 系、Aurora 系、Rosé 系 |
| `分布式协调` | CockroachDB Leader Lease、HATS、Fluss 分布式协调 |
| `消息系统` | Fluss 系 |
| `Agent-First` | Agent-First 系列 |

> 非强制，指导性。标签粒度建议：领域标签 + 核心技术名 + 关注点。

## Frontmatter 模板（v2 扩展）

```yaml
---
type: survey | decision | analysis | lesson | concept | meta
title: "标题"
sources:
  - "sources/papers/论文名/论文名-会议年份.pdf"
  - "sources/papers/论文名/精读分析.md"
  - "sources/papers/论文名/全文翻译.md"
tags:
  - "标签1"
  - "标签2"
created: YYYY-MM-DD
updated: YYYY-MM-DD
status: draft | reviewed | final | deprecated
confidence: 0.85              # v2 新增：必填，0-1 置信度分值
confidence_rationale: >-      # v2 新增：可选，评分理由简述
related:
  - "[[相关页面1]]"
  - "[[相关页面2]]"
---
```

### 字段说明
- **type**：必填
- **title**：必填
- **sources**：强烈建议，指回 sources/ 下的原文 PDF + 精读分析 + 翻译
- **tags**：必填，至少 1 个标签
- **status**：`draft` → `reviewed` → `final` → `deprecated`
- **confidence**：**v2 新增必填**，0-1 置信度分值，见下方评分规则
- **confidence_rationale**：**v2 新增可选**，评分理由简述
- **related**：建议，[[wikilink]] 链接到相关知识页面

---

## 置信度评分（v2 新增）

### 评分等级

| 分值 | 含义 | 判定标准 |
|------|------|----------|
| 0.90+ | 高度可信 | 多源确认（≥3），近期验证（<30天），无矛盾 |
| 0.75-0.89 | 可信 | 单源但逻辑自洽，或多源但时效差（30-90天） |
| 0.60-0.74 | 待验证 | 单源，或新信息与旧信息矛盾中 |
| 0.40-0.59 | 低置信 | 推测/噪音/单一blog来源 |
| <0.40 | 不可信 | 标记 deprecated 或 archived |

### 证据更新规则（2026-10-05 修订）

- `updated` 表示内容修改时间；`source_checked` 表示实际核对原文的时间，两者不能互相替代。
- 同一原文的翻译、卡片、博客副本只算一个证据来源，不能按链接数量增加置信度。
- `confidence` 是维护者的粗粒度判断，不是概率证明。记录依据和未核验部分，不能通过统一加减分制造精确感。
- 只因日期较旧、未访问或调整图表，不自动降低置信度、改成 deprecated 或升级为 reviewed。
- 新证据推翻旧断言时，直接修正正文并记录出处；重大替代关系再标记 superseded。
- 经典算法仍有效但软件版本过时的页面，分别标注适用假设与版本范围，不整页判为过时。

### 内联置信度标注

关键断言段落之后使用标准格式：

```markdown
> **Confidence: 0.85** | 来源×2 | 3周前确认 | 无矛盾
```

### 过时与筛选

30 天未复核仅进入待审清单。不得以“遗忘”为由自动删除正文或仅留标题。归档/合并必须给出内容依据、保留历史和可追溯的替代入口。综述不能靠引用卡片 confidence 的均值自动取得新的可信度。

---

## Supersession 机制（v2 新增）

旧断言标记 `>[!SUPERSEDED by 页面名#章节]` 并链接新版本。

entities.json 中记录 `{type: "supersededBy", to: "new-entity-id"}`。

---

## 知识图谱层（v2 新增 — .entities.json）

### 文件位置：`wiki/.entities.json`

### 实体类型

| 类型 | 适用 |
|------|------|
| `Concept` | 技术概念（LSM-Tree、MVCC） |
| `Project` | 系统/项目（Fluss、Doris） |
| `Person` | 关键人物 |
| `Paper` | 论文 |
| `Mechanism` | 具体机制/算法 |
| `Taxonomy` | 分类体系 |
| `Tool` | 工具/框架 |

### 关系类型

`extends` | `contrastsWith` | `implements` | `uses` | `basedOn` | `competitorOf` | `inspiredBy` | `supersededBy`

### 实体格式

```json
{
  "entities": [
    {
      "id": "kebab-case-id",
      "type": "Concept",
      "name": "人类可读名称",
      "confidence": 0.85,
      "attributes": {
        "description": "...",
        "created": "YYYY-MM-DD"
      },
      "relationships": [
        {"to": "other-id", "type": "extends", "confidence": 0.90, "note": "关系说明"}
      ]
    }
  ],
  "lastUpdated": "YYYY-MM-DD",
  "updatedBy": "CTO Agent"
}
```

---

## [[wikilink]] 规范

### Lint 检查维度

| 问题类型 | 严重度 | 处理 |
|----------|--------|------|
| Dangling 引用 | 🔴 阻断 | 删除或补建页面 |
| 重复引用 | 🟡 警告 | 去重 |
| 循环自引 | 🔴 阻断 | 删除 |
| 来源引用缺失 | 🟡 警告 | 删除或补源 |
| Synthesis 隔离 | 🟡 警告 | 确认意图 |
| **跨卡片矛盾（v2）** | 🔴 阻断 | 触发 Supersession |
| **低置信度（v2）** | 🟡 警告 | 标记需审阅 |
| **长衰减（v2）** | 🟡 警告 | 标记需审阅 |
| **孤立实体（v2）** | 🟡 警告 | 补关系或标记 [ORPHAN] |
| **Supersession 悬空（v2）** | 🔴 阻断 | 修复或删除标记 |

### GitPage 转义规则

| Obsidian 引用 | GitPage 应转成 |
|--------------|---------------|
| `[[wiki/页面名]]` | 按 `.blog-sync-manifest.json` 转为公开文章 URL |
| `[[页面名\|别名]]` | 同上，保留显示别名 |
| `[[页面名#章节]]` | 同上 + `#章节锚点` |
| `sources/papers/...` | 已发布精读文章或经过核验的原文附件；无公开对应时保留来源说明 |

## Agent 写入规则

### 写前自检清单（v2 强制）

- [ ] frontmatter 含 `type`/`sources`/`tags`/`status`/`created`/`related`/**`confidence`（v2 新增）**
- [ ] `sources` 指向实际文件
- [ ] `related` [[wikilink]] 指向实际 .md
- [ ] **`confidence` 分值合理（新卡起步 0.70）（v2 新增）**
- [ ] **关键断言内联置信度标注（v2 新增）**
- [ ] 含深度信息（论文章节号、对比数据、架构图）

### 写入流程（v2 扩展）

1. 读 `purpose` + 本文档
2. 完整 frontmatter（含 confidence）
3. 更新 README.md
4. **更新 `wiki/.entities.json`（v2 新增）**
5. 追加 log.md
6. 检查相关页面 + [[wikilink]]
7. **检查矛盾 → 触发 Supersession（v2 新增）**
8. git add -A && git commit && git push

---

## Ingest 规则

### 执行流程（v2 扩展）

```
Step 1: 源文件入库 → sources/
Step 2: 更新 sources/README.md
Step 3: spawn Worker 生成卡片（含 confidence）
Step 4: CTO 提取实体 → wiki/.entities.json（v2 新增）
Step 5: 涟漪更新 — 同领域卡片矛盾检测 + Supersession（v2 新增）
Step 6: 更新索引 + 日志 + commit
```

---

## Synthesize 规则

### 临界质量：集群 ≥ 5 页 或 含 ≥ 2 个 type

### Synthesize 的置信度：按综合证据及冲突评估，不取卡片分数的机械均值

### 定时：每周五 10:00 CST + Confidence Decay + Supersession Detection

---

## Synthesis Refresh（增量更新）

| 信号 | 阈值 | 动作 |
|------|------|------|
| 新页面 ≥ 3 且含新 type | 重写 | CTO |
| 新页面 1-2 张 | 增量追加 | CTO |
| 状态升级/连接变化 | 局部修订 | CTO |
| Dangling 引用 | 快速修复 | CTO |
| updated > 30 天 | 确认无变更 | CTO |
| **confidence < 0.60（v2）** | **重新评估** | **CTO** |

## 知识网络分层与 Lint 范围

| 分类 | 目录 | Lint 规则 |
|------|------|-----------|
| A 类 | `wiki/`、`wiki/synthesis/`、`wiki/.entities.json` | 全量 Lint |
| B 类 | README, sources/README, log, purpose, schema | 不参与 Lint |
| C 类 | sources/papers/**, sources/web/** | 原件做格式/来源检查；精读和译文检查证据、覆盖范围、链接与图表 |

---

## 精读质量门槛（2026-10-05）

逐篇区分实验论文、系统设计、综述、理论证明和 vision paper，不用统一字数衡量质量。

1. **身份核对**：标题、作者、年份、版本、页数和实际 PDF 内容一致。拦截提示、下载错误页不得视为原文。
2. **问题与假设**：交代解决什么问题、系统/故障模型、适用条件；理论结果写清保证与前提。
3. **机制拆解**：说明数据结构、关键路径、状态变化和不变量，给出一个能走通的例子；不能只罗列名词。
4. **证据定位**：关键结论指到章节、定理、图或表；区分 PDF 页序与论文印刷页码。数字须附工作负载、配置、指标、基线和适用条件；缺测项明确写未报告。
5. **评价与局限**：综述写分类方法和覆盖边界；vision paper 明确没有实现/统一实验；系统论文不得把某一实验结果当成普遍收益。
6. **结论分层**：分清“论文证明/测得”“作者主张”“本文工程推论”，互相引用的卡片不得造成独立证据假象。
7. **关联与传播**：纠错同时检查概念卡、综述、别名副本与博客。保留稳定路径/网址，用标题或别名修正误命名。
8. **译文标识**：全文翻译应覆盖正文全部章节，图表/附录若省略应注明。压缩总结只能称译述/选译，不能靠标题“全文”掩盖缺失。

## Diagram 规范（Mermaid 优先）

- 架构、流程、时序、状态机、分类关系优先写入正文的 `mermaid` 代码块；不要求安装专用制图 skill。
- 一张图表达一个问题，附图题、阅读说明和适用边界。节点文字避免超长，长流程拆图；不能把相关性画成因果或依赖。
- 只有精确曲线/坐标、原论文图形、复杂布局或 Mermaid 无法准确表达时才用 SVG，并在相邻说明或 `diagram_fallback_reason` 中解释原因。原始图资产可保留历史副本，不再作为默认显示图。
- ASCII 树若只是目录/代码示例可保留；表达架构/状态流时改 Mermaid。对比数据用表格通常比框图更合适。
- 转换前先核验图意；原 SVG 中的错误标签、版本混用与无源数字必须纠正，不能照抄错误。
- Obsidian 与博客使用相同 Mermaid 源码；Jekyll 对应文章设置 `mermaid: true`。清单与附件引用同步更新。
- 必须进行语法检查和实际页面渲染检查，桌面/手机无整页横向溢出。构建成功不能代替图表渲染验证。

## 本轮同步约定

本轮由 Obsidian 完成质量修订，再更新对应 GitPage；沿用稳定 URL、来源映射和技术知识公开范围。维护规则、团队运行信息不发布到博客。只有完成原文核验的条目才写 `source_checked`，筛查记录与深读记录分开保存。

*2026-10-05：按用户最新要求补充精读质量门槛，修正资料权限、证据与日期语义，并改为 Mermaid 优先。*
