---
type: meta
title: "知识库的结构规则"
tags: ["meta", "schema"]
created: 2026-06-14
updated: 2026-07-05
confidence: 0.92
confidence_rationale: "基于 Karpathy LLM Wiki v2 方法论升级，团队已验证生效"
---

# 知识库的结构规则

> **v2 升级 (2026-07-05)**：基于 [CentiMatrix/karpathy-llm-wiki-v2](https://github.com/CentiMatrix/karpathy-llm-wiki-v2) 引入置信度评分、实体提取 (.entities.json)、迭代覆盖 (Supersession)、遗忘机制 (Forgetting)。详细操作流程见 `ai-wiki-maintain` skill v2。

## 四层架构（v2 升级）

基于 Karpathy LLM Wiki 方法论，知识库分为四层：

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
| Raw Sources | `sources/` | 人类放入，Agent 只读 | 原始资料，是知识的源头，不可修改 |
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
| `分布式协调` | CockroachDB Leader Lease、Silo、Fluss 分布式协调 |
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

### 动态调整规则

| 事件 | 调整 | 方向 |
|------|------|------|
| 新卡片首次 Ingest | 起步 0.70 | 初始 |
| 每多一个独立来源确认 | +0.10（上限 0.95） | ↑ |
| 每 30 天未访问或验证 | -0.05 | ↓ |
| 发现矛盾时相关卡片 | 各 -0.20 | ↓ |
| 被新来源更新（Supersession） | 旧标记 superseded，新起步 0.75 | — |
| CEO 审阅通过 | +0.10 且 status → reviewed | ↑ |

### 内联置信度标注

关键断言段落之后使用标准格式：

```markdown
> **Confidence: 0.85** | 来源×2 | 3周前确认 | 无矛盾
```

### 衰减规则（每周五维护日执行）

| 衰减类型 | 触发条件 | 幅度 |
|----------|---------|------|
| 未访问衰减 | `updated` 距今 > 30 天 | -0.05 |
| 矛盾衰减 | 与其他卡片存在事实矛盾 | 各 -0.20 |
| 降权阈值 | confidence < 0.30 | → status: deprecated |
| 遗忘阈值 | 距今 > 180 天未更新 | 保留标题 + `archived:` 标签 |
| 架构决策慢衰减 | type=decision | 每 90 天 -0.02 |
| Bug/事件快衰减 | type=lesson | 每 30 天 -0.10 |

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
| `[[wiki/页面名]]` | GitHub raw URL |
| `[[页面名\|别名]]` | 同上，显示别名 |
| `[[页面名#章节]]` | 同上 + `#章节锚点` |
| `sources/papers/...` | GitHub raw URL |

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

### Synthesize 含 confidence（v2 新增）：取引用卡片置信度均值

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
| C 类 | sources/papers/**, sources/web/** | 不检查 |

---

## Diagram 规范（技术架构图）

工具：`fireworks-tech-graph` skill，Style 1 (Flat Icon)。

产出：`wiki/diagram/{主题-slug}.svg` + `wiki/diagram/{主题-slug}.png`

---

*本文件定义了知识库的"怎么做"。Agent 写入知识库时必须遵循。*

*Last updated: 2026-07-05 | v2 upgrade from [CentiMatrix/karpathy-llm-wiki-v2](https://github.com/CentiMatrix/karpathy-llm-wiki-v2)*
