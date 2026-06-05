# Phase 3 知识管理 · 细化方案

> CTO 出品 · 2026-06-05 · v1.0

---

## 一句话定义

让 Agent 把 ai_wikis 当成"活的参考手册"来用，而不只是"一堆文件躺在那"。

---

## 现状盘点

### 我们已有的知识资产

| 类别 | 文件数 | 内容 |
|------|--------|------|
| 团队核心规范 | 5 个文件 | 仓库分工、Agent 核心文件、记忆管理规范、权限矩阵、通信协议 |
| 技术/产品/财务/运营规范 | 4 个 README | 占位，待内容填充 |
| Agent 核心文件 | 5 个角色 × 5-6 个文件 | AGENTS.md / SOUL.md / IDENTITY.md / USER.md / MEMORY.md |
| 项目文档 | 2 个文件 | 设计文档 + Frank 思考笔记 |
| 技术文章 | 空目录 | — |
| 知识库 | 空目录 | — |
| 合计 | ~35 个 .md | 大部分是规范类，知识库和技术文章基本空白 |

### Agent 目前能用什么

| 能力 | 能做什么 | 做不到的 |
|------|---------|----------|
| `memory_search` | 语义搜索自己的 MEMORY.md + memory/*.md | 搜不到 ai_wikis 里的规范文件 |
| `read` | 手动读取任何文件 | 不知道自己应该读什么 |
| `exec` git pull | 拉取最新代码 | 不会主动去拉 |
| AGENTS.md 注入 | 自动加载自身 AGENTS.md 等 | 加载不到别人的知识、团队规范 |

### 关键发现：AGENTS.md 已经包含了大部分规范

你的 AGENTS.md 里已经有权限矩阵、通信协议、任务状态机、模型分配规则。这些内容不是 OpenClaw 自动从 ai_wikis 加载的——是我们**手动 copy 进去的**。

问题就在这：**规范写了两次**。一次在 ai_wikis（给人和 review 看的），一次在 AGENTS.md（给 Agent 执行的）。以后规范改了，必须两头同步——这是知识管理的裂缝。

---

## Phase 3 要解决的三个问题

### 问题 1：Agent 不知道该查什么

**场景**：你问 CTO "我能让 CFO 也去派技术专家吗？"
- 现状：CTO 的 AGENTS.md 里没有"别人能不能派我的专家"这条规则。它可能答错。
- 理想：CTO 自动去查团队核心规范，发现 "任命专家仅限同领域"，然后告诉你"CFO 没有任命技术专家的权限"。

**根因**：AGENTS.md 存了一份规范的子集，但 Agent 不知道遇到边界问题时去哪查完整版。

### 问题 2：新知识沉淀不回来

**场景**：CTO 做了一个技术决策（SQLite over Postgres），在飞书里跟你汇报了。
- 现状：这个决策只存在会话记录里，下次新 Agent 做类似选型时，完全不知道有人做过。
- 理想：重要决策自动回写 ai_wikis/知识库/，下次 Agent 用 `read` 就能查到。

**根因**：没有"Agent 产出 → 知识库"的回流机制。

### 问题 3：规范两端不同步

**场景**：你改了一条权限规则，在团队核心规范里更新了。
- 现状：所有 Agent 的 AGENTS.md 不会自动更新。他们继续用旧规则。
- 理想：规则改一次，所有 Agent 下一次启动时自动生效。

**根因**：ai_wikis 里的规范 和 Agent workspace 的 AGENTS.md 是两套独立副本。

---

## 三个子任务（按优先级）

### A. 知识注入（优先级 P0，核心）

**目标**：Agent 启动时，自动加载"该知道的事"，而不是只靠自己 AGENTS.md 那一小段。

**怎么做**：利用 OpenClaw 的 **Project Context（Workspace Files）机制**。

OpenClaw 在构建 system prompt 时，会自动注入工作区下的指定文件。目前 CTO 的 AGENTS.md 已经靠这个机制加载了。我们要做的是：**让 Agent 关键信息不在 AGENTS.md 里重复维护，而是引用 ai_wikis 里的规范文件**。

但这里有技术限制：OpenClaw 的 workspace files 注入只限 agent workspace 根目录下的几个特定文件（AGENTS.md, SOUL.md, TOOLS.md, IDENTITY.md, USER.md, HEARTBEAT.md, MEMORY.md），不支持子目录文件。

**所以实际策略分两步**：

#### A1. 规范压缩注入（AGENTS.md 保留现状，但加一条规则）

在当前架构下，AGENTS.md 里保留核心规则的子集是必要的。但我们加一条明确的"知识检索规则"：

```markdown
## 知识检索规则（Phase 3）

遇到以下情况时，主动用 `read` 工具查阅 ai_wikis 中的完整规范：
- 权限/职责边界不明确 → 查 `ai_wikis/团队规范/团队核心规范/`
- 记忆/可见性问题 → 查 `ai_wikis/团队规范/团队核心规范/记忆管理规范.md`
- 仓库操作/同步规则 → 查 `ai_wikis/团队规范/仓库分工说明.md`
- 项目设计背景 → 查 `ai_wikis/项目文档/`

关键决策后，将决策摘要回写到 ai_wikis/知识库/。
```

#### A2. 知识推送脚本（冷启动增强）

CTO 的 AGENTS.md 冷启动流程中，已经有第 5 步"推送相关项目文档"。现在把它细化成一个具体操作：

```bash
# 冷启动第 5 步：推送相关文档
$ openclaw memory-load --from ai_wikis/团队规范/团队核心规范/ --top 3
```

实际上这等同于用 `memory_search` 搜 ai_wikis 文件夹。但目前 memory_search 只索引 memory/ 目录。

**技术决策**：不等 OpenClaw 原生支持子目录索引。Phase 3 用"AGENTS.md 规则 + 手动 read"的组合，代价是 Agent 多一步 tool call，收益是零基础设施依赖。

#### A3. 子 Agent 知识注入（spawn 时传递）

`sessions_spawn` 的 `context: "isolated"` 模式下，子 Agent 只收到一条 task 消息。它不知道父 Agent 知道的团队规范。

**做两件事**：

1. **spawn 时在 task 里写清楚该查什么**。
   CTO 派专家 Infra 做技术选型时，task 里加上：
   > "决策前先 read /home/admin/.openclaw/workspace/agents/cto/work/ai_wikis/团队规范/技术规范/README.md 了解技术选型规范"

2. **每个 Agent 的 AGENTS.md 加入知识检索规则**。
   让所有 Agent 都知道遇到边界问题去哪查，不依赖 CTO 手动写 task。

### B. 知识沉淀闭环（优先级 P1）

**目标**：Agent 的重要产出自动回流到 ai_wikis，形成闭环。

**怎么做**：分两层。

#### B1. 任务完成时自动沉淀（规则层）

在每个 Agent 的 AGENTS.md 的"任务状态机"部分加入沉淀规则：

```markdown
任务完成后，如果满足任一条件，将产出回写到 ai_wikis：
1. 做了技术决策（选型、架构变更） → 写 ai_wikis/知识库/
2. 产生了新的流程/方法     → 写 ai_wikis/团队规范/<对应领域>/
3. 调研/分析结果           → 写 ai_wikis/技术文章/
```

这不是强制执行的代码逻辑，而是 Agent 的行为规则——CTO review 时能发现 Agent 有没有遵守。

#### B2. 知识沉淀质量保证

- CTO 在汇总子 Agent 结果时，检查是否满足沉淀条件
- 如果 Agent 忘了，CTO 补写
- 沉淀内容格式：标题 + 背景 + 结论 + 日期 + 标签（YAML frontmatter）

### C. 规范统一（优先级 P2，依赖 A 完成）

**目标**：消除 AGENTS.md 和 ai_wikis 的双写问题。

**现状分析**：

| 内容 | 在 AGENTS.md 里？ | 在 ai_wikis 里？ | 同步方式 |
|------|------------------|-----------------|---------|
| 角色定位 | ✅ CTO AGENTS.md | ✅ agent核心文件/cto/AGENTS.md | 现在是人肉同步 |
| 权限矩阵 | ✅ CTO AGENTS.md | ✅ 设计文档.md | 人肉同步 |
| 通信协议 | ✅ CTO AGENTS.md | ✅ 设计文档.md | 人肉同步 |
| 任务状态机 | ✅ CTO AGENTS.md | ✅ 设计文档.md | 人肉同步 |
| 冷启动流程 | ✅ CTO AGENTS.md | ✅ 记忆管理规范.md | 人肉同步 |
| 记忆分层 | ❌ | ✅ 记忆管理规范.md | L2 单独维护 |
| 知识检索规则 | ⬜ 本轮新增 | ⬜ 本轮新增 | P0 先建 |

**P2 要做的事**：

1. 明确 **ai_wikis 为规范唯一源（single source of truth）**
2. AGENTS.md 对规范的引用改为**摘要 + 指向 ai_wikis 的路径**（而不是完整复制）
3. 规则变更时：改 ai_wikis → 同步更新 Agent 核心文件目录 → Agent 冷启动自动 git pull → 生效

**但这有个现实问题**：AGENTS.md 是 OpenClaw workspace file，它在 agent workspace 根目录。ai_wikis 是子仓库。两者不能直接互相引用。所以 P2 的最终形态可能是：

```
~agents/cto/
  AGENTS.md          ← 保留核心规则摘要（最小集合）
  SOUL.md            ← 身份语气
  MEMORY.md          ← 长期记忆
  memory/
    ...
  ai_wikis →         ← 符号链接或 git submodule，指向 ai_wikis
或者
  work/
    ai_wikis/        ← git clone 产物（冷启动拉取）
```

现在我们已经是第二种（work/ai_wikis），所以 AGENTS.md 里写 `read work/ai_wikis/...` 就能引用。

---

## 具体落地计划

### 第一周：知识注入（A1 + A2）

- [ ] **所有 Agent 的 AGENTS.md 加入"知识检索规则"**
  - CTO、CEO、CFO、COO、CPO 各一份
  - 规则内容：遇到哪类问题查哪个路径
- [ ] **CTO 的冷启动流程更新**
  - 第 5 步细化：推送哪些文档、怎么匹配任务类型
- [ ] **spawn task 模板**
  - CTO 的 AGENTS.md 加入 spawn 时嵌入知识引用的规则

### 第二周：知识沉淀闭环（B1 + B2）

- [ ] **所有 Agent 的任务完成流程加入沉淀规则**
  - 什么条件触发沉淀、沉淀到哪个路径
  - CTO review 检查清单
- [ ] **试运行：至少完成 1 次端到端闭环**
  - Agent 执行任务 → 产出知识 → 回写 ai_wikis → CTO review → 提交 Git
- [ ] **ai_wikis/知识库/ 创建初始目录结构**

### P2（择机启动，依赖 Phase 3 运行稳定）

- [ ] **规范唯一源评估**
  - 选一个规范文件做试点（比如记忆管理规范），看能不能只存在 ai_wikis，AGENTS.md 只留引用
  - 跑通后逐步推行

---

## 预期的 Agent 行为变化

### Before Phase 3

```
用户: "CTO 帮我做个技术选型"
CTO: [靠自己的经验判断]
      [如果遇到边界问题，可能猜错规则]
```

### After Phase 3

```
用户: "CTO 帮我做个技术选型"
CTO: [看自己 AGENTS.md 的知识检索规则]
      → "技术选型需要先查技术规范"
      → read ai_wikis/团队规范/技术规范/
      → 发现规范里写了"SQLite 是标准存储，新项目需评审"
      → 基于规范做决策
      → 做完后，写决策摘要回 ai_wikis/知识库/
```

---

## 不做的

- ❌ 不做复杂的检索引擎（Phase 2 已决策，用 OpenClaw 原生）
- ❌ 不做自动文件监听 + 热加载（太重）
- ❌ 不做知识图谱 / 向量数据库（远超当前需求）
- ❌ 不做规范格式校验 / lint（现阶段不必要）

---

## 成本估算

| 事项 | 涉及文件 | 人力 |
|------|---------|------|
| 5 个 Agent AGENTS.md 加知识检索规则 | 5 个文件 | 小 |
| CTO 冷启动流程更新 | 1 个文件 | 小 |
| spawn task 模板 | 1 个文件 | 小 |
| 沉淀规则写入 + 知识库目录 | 5 个文件 + 目录创建 | 小 |
| 试运行 1 个闭环 | 1 次执行 | 中 |
| 合计 | | ~2-3 小时实际执行 |

大部分是改 AGENTS.md（规则声明），核心靠 Agent 自己遵守。不是写代码，是写 prompt。

---

## 成功标准

- [ ] 任意 Agent 遇到边界权限问题时，会主动 read ai_wikis 规范文件
- [ ] 至少 1 次任务闭环：任务执行 → 知识沉淀 → ai_wikis 更新 → Git push → 可 review
- [ ] CTO 汇总子 Agent 结果时，能检查沉淀质量
- [ ] 新启的 Agent（CFO/COO/CPO 任一个）能通过冷启动加载到最近的项目文档

---

## 与 Phase 4 的衔接

Phase 3 落地后，Phase 4 可观测性可以采集以下新增数据：

- Agent 读取了多少次规范文件（wiki_access 表已设计）
- 什么规范被读得最多（哪些规则 Agent 最常需要确认）
- 知识沉淀频率（Agent 会不会主动写回知识库）
- 这些数据反过来优化 AGENTS.md——读得最多的规则值得直接注入，读不到的说明路径不对
