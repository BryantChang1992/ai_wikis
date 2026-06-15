---
type: concept
title: "Event Horizon: 非对称依赖与跨地域操作"
sources:
  - "sources/papers/Event-Horizon/Event-Horizon-CIDR2026.pdf"
  - "sources/papers/Event-Horizon/精读分析.md"
  - "sources/papers/Event-Horizon/全文翻译.md"
tags:
  - 分布式系统
  - 一致性
  - Geo-Distributed
  - CIDR-2026
  - 非对称依赖
  - Event-Horizon
  - 半线性化
  - 协调
created: 2026-06-14
updated: 2026-06-14
status: draft
related:
  - "[[事务模型深度调研]]"
---

# Event Horizon：非对称依赖与半线性化

> **论文**：*Event Horizon: Asymmetric Dependencies for Fast Geo-Distributed Operations*  
> **作者**：Jonathan Arns, Harald Ng (KTH), Kyriakos Psarakis (Ververica/TU Delft), Asterios Katsifodimos (TU Delft), Paris Carbone (KTH)  
> **会议**：CIDR 2026

---

## 1. 核心问题

地理分布式应用（XR、实时竞拍、沉浸式游戏）面临一个根本矛盾：

| 需求 | 方案 | 代价 |
|------|------|------|
| 低延迟 | CALM / CRDT 等弱一致性模型 | **无法保证常见不变量**（唯一性、拍卖最终结果确定性） |
| 强一致 | [[事务模型深度调研]] / Paxos / [[事务模型深度调研]] 全序 | **延迟根本意义上无法突破**（跨地域 replica 通信） |

现有混合一致性模型（RedBlue、PoR、ECROs）按操作二分法划分：
- **强操作**（red / conflict）→ 全序，需协调
- **弱操作**（blue / commutative）→ 无协调，可并发

**但二分法假设冲突关系是对称的，忽略了大量真实语义中冲突是单向的。** 由此导致**过度协调**——对所有操作或对不必要的一组操作执行全序。

---

## 2. 关键洞察：非对称依赖

### 2.1 拍卖案例揭示过度协调

| 操作 | 语义 | 关系 |
|------|------|------|
| `new_bid` | 插入新出价 | 与其他 `new_bid` 可交换（commutative） |
| `close_auction` | 结束拍卖，确定赢家 | 必须**观察到**所有前置 `new_bid` |

**真实依赖方向**：`close_auction → new_bid`（单向）
- `close_auction` 需要看到所有 bid 的历史
- 但 `new_bid` 不需要关心 `close_auction` 何时发生
- `close_auction` 执行后产生的新 `new_bid` 可以被拒绝——不违反正确性

现有模型的问题：

| 模型 | 对拍卖的建模 | 问题 |
|------|-------------|------|
| RedBlue | `new_bid ↔ new_bid`（强冲突）+ `close_auction ↔ new_bid`（强冲突） | **过度协调**：对所有操作执行全序 |
| PoR | 同 RedBlue | **过度协调** |
| ECROs | `close_auction ↔ new_bid`（冲突） | **违反不变量**：`close_auction` 可能遗漏并发 `new_bid` |

### 2.2 非对称依赖模型

用**有向依赖图**替代无向冲突图：

<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 700 180" width="700" height="180">
  <defs>
    <marker id="arrow-eh1" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <path d="M0,0 L8,3 L0,6 Z" fill="currentColor"/>
    </marker>
    <marker id="arrow-eh2" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <path d="M0,0 L8,3 L0,6 Z" fill="currentColor"/>
    </marker>
    <marker id="arrow-eh3" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <path d="M0,0 L8,3 L0,6 Z" fill="currentColor"/>
    </marker>
  </defs>
  <!-- new_bid box -->
  <rect x="40" y="60" width="230" height="40" rx="6" fill="transparent" stroke="currentColor" stroke-width="1.5"/>
  <text x="155" y="80" font-family="sans-serif" font-size="13" fill="currentColor" text-anchor="middle" dominant-baseline="middle">new_bid</text>
  <!-- close_auction box -->
  <rect x="420" y="60" width="240" height="40" rx="6" fill="transparent" stroke="currentColor" stroke-width="1.5"/>
  <text x="540" y="80" font-family="sans-serif" font-size="13" fill="currentColor" text-anchor="middle" dominant-baseline="middle">close_auction</text>
  <!-- new_bid (self loop box) -->
  <rect x="40" y="130" width="230" height="40" rx="6" fill="transparent" stroke="currentColor" stroke-width="1.5"/>
  <text x="155" y="150" font-family="sans-serif" font-size="13" fill="currentColor" text-anchor="middle" dominant-baseline="middle">new_bid</text>
  <!-- Arrow 1: new_bid --> close_auction -->
  <line x1="270" y1="80" x2="410" y2="80" stroke="currentColor" stroke-width="1.5" marker-end="url(#arrow-eh1)"/>
  <text x="340" y="72" font-family="sans-serif" font-size="11" fill="currentColor" text-anchor="middle" dominant-baseline="middle">eventually ordered</text>
  <!-- Arrow 2: new_bid (self) with curve -->
  <path d="M270,150 Q320,150 320,130 Q320,110 270,110" fill="none" stroke="currentColor" stroke-width="1.5" marker-end="url(#arrow-eh2)"/>
  <text x="338" y="130" font-family="sans-serif" font-size="11" fill="currentColor" text-anchor="middle" dominant-baseline="middle">commutative</text>
  <!-- Arrow 3: close_auction --> new_bid (dashed, no dep) -->
  <line x1="420" y1="75" x2="280" y2="145" stroke="currentColor" stroke-width="1.5" stroke-dasharray="5,4" marker-end="url(#arrow-eh3)"/>
  <text x="370" y="130" font-family="sans-serif" font-size="11" fill="currentColor" text-anchor="middle" dominant-baseline="middle">no dep</text>
  <text x="390" y="150" font-family="sans-serif" font-size="11" fill="currentColor" text-anchor="middle" font-weight="bold">← 非对称！</text>
</svg>

关键特征：
- `close_auction` **不依赖**未来的 `new_bid`（消息方向 ≠ 依赖方向）
- 这消除了 `close_auction` 与并发 `new_bid` 间的协调需求
- 协调代价从"全序所有相关操作"降为"仅共识强操作本身"

---

## 3. 半线性化（Semi-Linearizability, SL）

### 3.1 直觉

> **可交换（弱）操作可以相互并发执行，自由流动；直到一个更强的操作形成"事件视界"（Event Horizon），将之前所有松散的操作强制塌缩为一个全局一致的历史顺序。**

类比天体物理学：事件视界是黑洞的边界——一切物质和信息一旦越过此边界就不可逆地内落。对应到分布式系统，大量并发事件可以随意发散，直到被一次"关键操作"收束。

### 3.2 操作依赖的三个层次

| 层级 | 符号 | 语义 | 协调代价 |
|------|------|------|----------|
| **strictly ordered**（严格有序） | `OP1 → OP2` | OP1 必须在 OP2 之前全局可见 | 最高（需共识） |
| **commutative**（可交换） | `OP1 ∥ OP2` | 两个操作可以以任意顺序执行 | 无协调 |
| **eventually ordered**（最终有序） | `OP1 ⇝ OP2` | OP2 最终需要"知道"OP1，但在 OP2 执行前可暂不建立全序 | **少量协调** |

`⇝`（eventually ordered）是 SL 的关键创新——**比严格有序更轻量，但比完全无约束更有保证**。它在强操作执行时才"开袋查阅"所有因果相关的弱操作。

### 3.3 SL vs 现有模型

| 模型 | 依赖建模 | 弱操作延迟 | 强操作协调范围 |
|------|---------|-----------|---------------|
| [[事务模型深度调研]] / 严格可串行化 | 全序 | N/A（无弱操作概念） | 所有操作 |
| RedBlue / PoR | 对称冲突 | 毫秒级 | 全序所有强操作 + 前序弱操作 must durable |
| ECROs | 对称冲突（更精确） | 毫秒级 | 同上 |
| **SL (DeMon)** | **非对称有向图** | **微秒级** | **仅共识强操作本身** |

---

## 4. DeMon 系统实现

DeMon 是 SL 的参考执行引擎，核心架构：

### 4.1 双版本机制

| 版本 | 语义 | 用途 |
|------|------|------|
| **Weak Guard** | 可交换的轻量执行 | 弱操作（如 `new_bid`）的快速路径 |
| **Strong Guard** | 线性化执行 | 强操作的持久化保证 |

### 4.2 执行流程

1. **弱操作**通过**因果广播**（Causal Broadcast）快速传播，使用**袋子（Bag）**数据结构在全局日志中记录而不强制全序
2. **强操作**向**主副本（Primary）**发送请求，由 Primary 执行并广播
3. **强操作执行时**，从 bag 中收集所有因果相关的弱操作 → 本地重排序确定最终序列

<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 720 220" width="720" height="220">
  <defs>
    <marker id="arrow-eh-exec1" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <path d="M0,0 L8,3 L0,6 Z" fill="currentColor"/>
    </marker>
    <marker id="arrow-eh-exec2" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <path d="M0,0 L8,3 L0,6 Z" fill="currentColor"/>
    </marker>
    <marker id="arrow-eh-exec3" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <path d="M0,0 L8,3 L0,6 Z" fill="currentColor"/>
    </marker>
  </defs>
  <!-- Client A: new_bid -->
  <rect x="10" y="20" width="280" height="30" rx="4" fill="transparent" stroke="currentColor" stroke-width="1.2"/>
  <text x="150" y="35" font-family="sans-serif" font-size="12" fill="currentColor" text-anchor="middle" dominant-baseline="middle">Client A: new_bid("item1", 100)</text>
  <line x1="290" y1="35" x2="470" y2="35" stroke="currentColor" stroke-width="1.5" marker-end="url(#arrow-eh-exec1)"/>
  <text x="380" y="28" font-family="sans-serif" font-size="10" fill="currentColor" text-anchor="middle" dominant-baseline="middle">causal broadcast</text>
  <rect x="475" y="20" width="220" height="30" rx="4" fill="transparent" stroke="currentColor" stroke-width="1.2" stroke-dasharray="3,2"/>
  <text x="585" y="35" font-family="sans-serif" font-size="11" fill="currentColor" text-anchor="middle" dominant-baseline="middle">副本本地执行（微秒级）</text>

  <!-- Client B: new_bid -->
  <rect x="10" y="65" width="280" height="30" rx="4" fill="transparent" stroke="currentColor" stroke-width="1.2"/>
  <text x="150" y="80" font-family="sans-serif" font-size="12" fill="currentColor" text-anchor="middle" dominant-baseline="middle">Client B: new_bid("item1", 150)</text>
  <line x1="290" y1="80" x2="470" y2="80" stroke="currentColor" stroke-width="1.5" marker-end="url(#arrow-eh-exec2)"/>
  <text x="380" y="73" font-family="sans-serif" font-size="10" fill="currentColor" text-anchor="middle" dominant-baseline="middle">causal broadcast</text>
  <rect x="475" y="65" width="220" height="30" rx="4" fill="transparent" stroke="currentColor" stroke-width="1.2" stroke-dasharray="3,2"/>
  <text x="585" y="80" font-family="sans-serif" font-size="11" fill="currentColor" text-anchor="middle" dominant-baseline="middle">副本本地执行（微秒级）</text>

  <!-- Client A: close_auction -->
  <rect x="10" y="115" width="290" height="30" rx="4" fill="transparent" stroke="currentColor" stroke-width="1.2"/>
  <text x="155" y="130" font-family="sans-serif" font-size="12" fill="currentColor" text-anchor="middle" dominant-baseline="middle">Client A: close_auction("item1")</text>

  <!-- Sub-steps -->
  <line x1="30" y1="145" x2="30" y2="160" stroke="currentColor" stroke-width="1.2"/>
  <text x="50" y="160" font-family="sans-serif" font-size="11" fill="currentColor" text-anchor="start" dominant-baseline="middle">├── 发送给 Primary</text>
  <text x="50" y="176" font-family="sans-serif" font-size="11" fill="currentColor" text-anchor="start" dominant-baseline="middle">├── Primary 从 bag 中收集所有相关 new_bid</text>
  <text x="50" y="192" font-family="sans-serif" font-size="11" fill="currentColor" text-anchor="start" dominant-baseline="middle">├── 本地重排序确定最终 bid 序列</text>
  <text x="50" y="208" font-family="sans-serif" font-size="11" fill="currentColor" text-anchor="start" dominant-baseline="middle">├── 广播结果</text>
  <text x="50" y="220" font-family="sans-serif" font-size="11" fill="currentColor" text-anchor="start" dominant-baseline="middle">└── 所有副本执行 close → 确定赢家 = Client B</text>
</svg>

### 4.3 与现有系统的关键差异

- **Bag + Local Reordering** 替代全序广播：弱操作之间无协调需求，只记录因果关系
- **非对称依赖图**替代冲突矩阵：`close_auction` 不需要等待并发 `new_bid` 的确认
- 强操作不再需要等待前序弱操作**持久化到所有副本**——只需在本地 bag 中可见即可

---

## 5. 实验评估

### 5.1 设置

- 基准：RUBiS（经典分布式拍卖/电商 benchmark）
- 对比系统：OmniPaxos（全序）、Gemini+ / UniStore（RedBlue 类混合模型）、No Guarantees（下界）

### 5.2 关键结果

| 操作类型 | DeMon | Gemini+ | UniStore | OmniPaxos | No Guarantees |
|----------|-------|---------|----------|-----------|---------------|
| `Bid`（最常见操作） | **亚毫秒** | 毫秒级 | 毫秒级 | 245ms | 亚毫秒 |
| `CloseAuction` | ~245ms | 371ms | 391ms | 245ms | N/A |

**`Bid` 操作上 DeMon 比次优的 Gemini+ 快约 4 个数量级**（微秒 vs 毫秒）。原因：DeMon 弱操作只需 causal broadcast = 单跳通信 + 本地执行。

### 5.3 强操作比例与收益

| 强操作比例 | DeMon 表现 |
|------------|-----------|
| 0% | 与 No Guarantees 一致（亚毫秒） |
| 10-50% | 延迟逐步接近 OmniPaxos 下界 |
| 50%+ | 所有混合模型趋同 |

**核心结论**：SL 的价值在强操作比例较低时最大化——这正是大多数交互式应用的典型模式。

---

## 6. 与已有知识的关联

### 6.1 与 [[事务模型深度调研|事务模型]] 的关系

- **[[事务模型深度调研]] / [[事务模型深度调研]]**：SL 不是替代 2PC，而是让部分操作**绕过协调**。2PC 只在强操作上触发，弱操作走因果广播。相当于把 2PC 的适用范围收窄到真正需要全序的操作子集。
- **[[事务模型深度调研]] / TrueTime**：Spanner 为所有事务强加全序（通过 TrueTime + Paxos），SL 则承认并非所有操作都需要全序。在跨地域场景中，SL 可以在 Spanner 的延迟墙上撕开一道口子。
- **[[事务模型深度调研]]**：Calvin 通过确定性执行避免 2PC，但仍在每个 epoch 对事务全排序。SL 可以进一步降低 epoch 内"非关键事务"的排序代价。

### 6.2 与一致性模型的关系

- **线性化（Linearizability） vs SL**：线性化要求所有操作都有且仅有一个全序；SL 只要求"关键操作"所见的历史一致，弱操作之间可以以任意顺序出现。
- **CRDT**：CRDT 通过数学性质（结合律、交换律、幂等律）保证最终一致，SL 不要求操作本身是可交换的——只要求它们在依赖图中**不互相依赖**。
- **CALM 理论**：CALM 证明 monotonic → coordination-free。SL 将这一边界进一步细化：non-monotonic 不一定需要全序——只需在关键点（事件视界）建立偏序。

### 6.3 与流系统的关联

- **Kafka Consumer Group Offset**：日常 offset commit 是弱操作（可交换），只有 rebalance 时是强操作。SL 可将日常 commit 降为因果广播。
- **Flink Checkpoint Barrier**：本质上是一个事件视界——barrier 之前所有算子状态必须塌缩为一致快照。SL 形式化可能为更轻量 checkpoint 变体提供理论基础。
- **Kafka Tiered Storage Compaction**：`delete_records` / `truncate` 操作形成事件视界，与大多数 segment 对象间的无依赖关系形成鲜明对比。

---

## 7. 实践启示

### 7.1 对技术选型的指导

1. **不要被强/弱二分法束缚**：真实依赖关系是**有向图**，识别操作间的非对称依赖可以大幅降低协调开销
2. **事件视界思维**：设计系统时主动识别哪些操作是"收束点"——只有这些点需要全局协调
3. **Bag + Reordering > 全序**：对于不需要全序的弱操作，bag 数据结构比全序日志更轻量且足够

### 7.2 对 CHANG_AI_TEAM 内部系统的启示

- **Agent 基础设施可观测性平台**中，大多数指标采集是弱操作（可交换），只有告警触发 / 状态变更才是事件视界——可以参考 SL 的分层设计
- **状态机设计**应从"哪些操作冲突"升级为"哪些操作需要观察哪些操作"——方向性依赖建模

---

## 8. 待深入

- [ ] **SL 在复杂多步事务中的适用性**：RUBiS 是理想场景，带条件依赖的多步事务效果未知
- [ ] **弱操作"惊喜"的 UI 层处理**：弱操作可能被重排（如 bid 被后到的 close 覆盖），论文承认这是工程挑战
- [ ] **Byzantine 容错**：论文 §7 讨论了 BFT 方向但未实现，实际可行性待验证
- [ ] **单主写入的扩展性瓶颈**：DeMon 强操作依赖单 Primary，高强操作比例场景下可能成为瓶颈
- [ ] **与 TrueTime 类机制的结合**：SL + 时钟约束能否进一步降低强操作延迟？
- [ ] **形式化验证**：SL 的形式化定义是否足够严格以保证工业级正确性？Coq / TLA+ 建模待做
- [ ] **对流存储（Kafka / Fluss）的具体改造方案**：将 SL 应用到 Kafka 多 DC 复制的详细设计

---

*精读分析：Stark (CTO) · 概念卡片生成：2026-06-14*
