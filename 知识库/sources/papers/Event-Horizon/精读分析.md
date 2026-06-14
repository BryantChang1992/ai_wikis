# Event Horizon：非对称依赖与半线性化——面向快速地理分布式操作的弱协调模型

> **论文**：Event Horizon: Asymmetric Dependencies for Fast Geo-Distributed Operations  
> **作者**：Jonathan Arns (KTH), Harald Ng (KTH), Kyriakos Psarakis (Ververica / TU Delft), Asterios Katsifodimos (TU Delft), Paris Carbone (KTH)  
> **会议**：CIDR 2026 (16th Annual Conference on Innovative Data Systems Research), January 18-21, Chaminade, USA  
> **许可**：CC-BY 4.0  
> **全文**：https://www.vldb.org/cidrdb/papers/2026/p20-arns.pdf

---

## 一、问题背景

### 1.1 地理分布式应用面临的核心矛盾

扩展现实（XR）、沉浸式游戏、实时竞拍等地理分布式应用对**低延迟**和**强一致状态**有双重需求：

- 一端：Spanner 等严格可串行化数据库通过共识（Paxos、2PC）强制全序 → **延迟根本意义上无法突破**（跨地域 replica 通信）
- 另一端：CALM、CRDT 等弱一致性模型避免协调 → **无法保证常见不变量**（如唯一性、拍卖最终结果确定性）

### 1.2 现有混合一致性模型的问题：过度协调

RedBlue 一致性、PoR（Proof of Replication）、ECROs 等混合模型按操作划分：
- **强操作**（red/conflict）→ 全序、需要协调
- **弱操作**（blue/commutative）→ 无协调、可并发

但这套二分法存在根本缺陷：

> **二分法假设冲突关系是对称的，忽略了大量真实应用语义中冲突是单向的。**

### 1.3 拍卖案例：暴露过度协调

分布式拍卖系统有两个操作：

| 操作 | 语义 | 关系 |
|------|------|------|
| `new_bid` | 插入一个新出价 | 与其他 `new_bid` 可交换（commutative） |
| `close_auction` | 结束拍卖、确定赢家 | 必须**观察到**所有前置 `new_bid` |

现有模型的困境：

| 模型 | 建模的依赖 | 问题 |
|------|-----------|------|
| RedBlue | `new_bid ↔ new_bid`（强冲突）和 `close_auction ↔ new_bid`（强冲突） | **过度协调**：对所有操作执行全序 |
| PoR | `new_bid ↔ new_bid` 和 `close_auction ↔ new_bid`（冲突） | **过度协调**：同上 |
| ECROs | `close_auction ↔ new_bid`（冲突） | **违反不变量**：`close_auction` 可能遗漏并发 `new_bid` |

**真实需求**：`close_auction → new_bid`（单向）——close 需要观察所有 bid 的历史，但 bid 不需要观察 close。这种**非对称依赖**正是突破过度协调的关键。

---

## 二、核心创新：半线性化（Semi-Linearizability, SL）

### 2.1 SL 的形式化定义

SL 是一种新的混合一致性模型，其核心概念用一句话概括：

> **可交换（弱）操作可以相互并发执行，自由流动；直到一个更强的操作形成"事件视界"（Event Horizon），将之前所有松散的操作强制塌缩为一个全局一致的历史顺序。**

类比：天体物理学中，事件视界是黑洞的边界，一切物质和信息一旦越过此边界就不可逆地内落。对应到分布式系统——大量并发事件路径可以随意发散，直到被一次"关键操作"收束。

### 2.2 操作依赖的三个层次

论文将操作间的依赖关系细化为三个层级：

| 层级 | 语义 | 协调代价 |
|------|------|----------|
| **strictly ordered**（严格有序） | `OP1 → OP2`：OP1 必须在 OP2 之前全局可见 | 最高（需共识） |
| **commutative**（可交换） | `OP1 ∥ OP2`：两个操作可以以任意顺序执行 | 无协调 |
| **eventually ordered**（最终有序） | `OP1 ⇝ OP2`：OP2 最终需要"知道"OP1，但在 OP2 执行前可暂不建立全序 | **少量协调** |

`⇝`（eventually ordered）是 SL 的关键创新——**比严格有序更轻量，但比完全无约束更有保证**。

### 2.3 DeMon 依赖模型（Asymmetric Dependency Model）

DeMon（论文实现的参考系统）用一个**有向依赖图**来描述操作间关系：

```
new_bid ──(eventually ordered)──► close_auction
new_bid ──(commutative)─────────► new_bid
close_auction ──(no dep)────────► new_bid   ← 非对称！
```

关键特征：
- `close_auction` 不依赖未来的 `new_bid`（消息方向 ≠ 依赖方向）
- `close_auction` 执行后，新的 `new_bid` 可以被拒绝——不违反正确性
- **这消除了 `close_auction` 与并发 `new_bid` 间的协调需求**

---

## 三、DeMon 系统实现

### 3.1 架构概览

DeMon 是 SL 的执行引擎，为每个操作维护两个"版本"：

| 版本 | 语义 | 用途 |
|------|------|------|
| **Weak Guard** | 可交换的轻量执行 | 弱操作（如 `new_bid`）的快速路径 |
| **Strong Guard** | 线性化执行 | 强操作的持久化保证 |

核心机制：
1. 弱操作通过**因果广播**（Causal Broadcast）快速传播，使用**袋子（Bag）**数据结构在全局日志中记录而不强制全序
2. 强操作向**主副本（Primary）**发送请求，由 Primary 执行并广播
3. 当强操作执行时，通过 bag 中的弱操作依赖关系进行**本地重排序**——确保看到所有因果相关的弱操作

### 3.2 执行流程（以拍卖为例）

```
1. Client A: new_bid("item1", 100) ──causal broadcast──► 各副本本地执行
2. Client B: new_bid("item1", 150) ──causal broadcast──► 各副本本地执行
3. Client A: close_auction("item1") 
   ├── 发送给 Primary
   ├── Primary 从 bag 中收集所有相关 new_bid
   ├── 本地重排序确定最终 bid 序列
   ├── 广播结果
   └── 所有副本执行 close → 确定赢家 = Client B
```

关键：步骤 1 和 2 的 `new_bid` 之间无协调，它们之间的顺序由 `close_auction` 执行时的 local reordering 确定。

### 3.3 与现有系统的差异

| 特性 | RedBlue | PoR | ECROs | **DeMon (SL)** |
|------|---------|-----|-------|----------------|
| 依赖建模 | 对称冲突 | 对称冲突 | 对称冲突 | **非对称** |
| 弱操作协调 | 无 | 无 | 无 | 无 |
| 强操作协调 | Paxos 全序全部强操作 + 前序弱操作 must durable | 同 RedBlue | 同 RedBlue | **仅 consensus 强操作本身** |
| 拍卖 `new_bid` 延迟 | 毫秒级 | 毫秒级 | 毫秒级 | **微秒级** |
| 拍卖 `close_auction` 延迟 | 与全序相关 | 与全序相关 | 与全序相关 | **仅 consensus round-trip** |

---

## 四、实验评估

### 4.1 实验设置

- **基准**：RUBiS（经典分布式拍卖/电商 benchmark）
- **对比系统**：OmniPaxos、Gemini+、UniStore、No Guarantees（下界）
- **协议分类**：
  - 容错协议：DeMon、Gemini+、UniStore（使用 consensus 复制）
  - 无容错：Gemini（无一致性保障）
  - 全序：OmniPaxos

### 4.2 吞吐量

- DeMon 在**所有容错协议中达到最高吞吐量**（仅略微低于无协调的 Gemini）
- 原因：DeMon 对大部分操作（`Bid` 类）使用因果广播，只有强操作走 consensus → 减少了共识瓶颈

### 4.3 延迟（最关键的发现）

| 操作类型 | DeMon | Gemini+ | UniStore | OmniPaxos | No Guarantees |
|----------|-------|---------|----------|-----------|---------------|
| `Bid`（最常见操作） | **亚毫秒** | 毫秒级 | 毫秒级 | 245ms | 亚毫秒 |
| `CloseAuction` | ~245ms | 371ms | 391ms | 245ms | N/A |

**`Bid` 操作上，DeMon 比次优的 Gemini+ 快 4 个数量级（微秒 vs 毫秒）**。

原因：DeMon 的弱操作只需 causal broadcast → 单跳通信 + 本地执行；而 RedBlue/PoR 风格的协议要求强操作执行前等待所有 causally related 弱操作写完 = 额外 round-trip。

### 4.4 协调开销微基准

用计数器数据类型（含 `not-less-than-zero` 不变量），控制强操作（`subtract`）比例：

| 强操作比例 | DeMon 表现 |
|------------|-----------|
| 0% | 与 No Guarantees 一致（亚毫秒） |
| 10-50% | 延迟逐步接近 OmniPaxos 下界 |
| 50%+ | 所有混合模型趋同——因为强操作主导了延迟 |

**核心结论**：SL 的价值在强操作比例较低时最大化——而这恰恰是大多数交互式应用的典型模式。

---

## 五、与 Kafka / 流存储系统的关联分析

### 5.1 流系统中的一致性问题

Kafka / Flink / Pulsar 等流系统同样面临地理分布式一致性问题：

| 场景 | 类比 | 当前做法 |
|------|------|----------|
| 多 DC 的 Consumer Offset 一致性 | `new_bid` + `close_auction` | 全序 offset commit（Kafka consumer group coordinator 单主） |
| Exactly-once 语义下的事务协调 | 强状态操作 vs 弱状态操作 | Kafka transactions → 全序 + 2PC |
| 多主复制下的 causal consistency | Bag-based 弱操作传播 | 无成熟方案 |

### 5.2 SL 对流系统的启示

1. **Consumer Group Offset 的"事件视界"优化**：大多数 offset commit 是弱操作（可交换），只有 rebalance 时才是强操作。SL 可以将日常 offset commit 降为因果广播，仅 rebalance 时触发全序。

2. **Kafka Tiered Storage 的 Compaction**：类比 RaaS——compaction 与 SL 的强操作语义类似：大多数 segment 对象间无依赖，但 `delete_records` 或 `truncate` 形成事件视界。

3. **Flink Checkpoint 的地理分布**：Flink checkpoint barrier 本质上是事件视界——它要求 barrier 之前所有算子状态在全流图内达成一致。SL 的形式化可能为更轻量的 checkpoint 变体提供理论支撑。

### 5.3 关键启示

- **不要让二分法（strong/weak）限制想象力**——真实操作依赖是**有向图**而非无向图
- **不对称性是实际系统优化的核心方向**——`read-after-write` 就是最经典的非对称依赖
- **Bag + Reordering = 比全序更灵活的正确性保证**——对 Kafka 多 DC 复制有直接参考价值

---

## 六、论文评价

### 亮点

- **贡献维度完整**：形式化（SL）+ 系统实现（DeMon）+ 实验验证 + 前瞻（§6-7），CIDR 风格恰到好处
- **理论动机漂亮**：事件视界的类比不仅好听，而且准确捕捉了弱操作的"塌缩"机制
- **代码实现公开**：DeMon 在 Ververica 开源，可直接复现
- **洞察尖锐**：精准指出混合一致性模型"对称冲突"的盲区；拍卖案例贯穿全文，论证连贯
- **前瞻价值高**：§7 "A Future Outlook" 从自然语言规范 → 形式化 → 代码生成 → verified lifting 的画布极具野心，为后续研究者提供了明确路线图

### 局限与待验证

- **RUBiS 基准的局限性**：拍卖场景是最适合 SL 的典型——但 SL 在更复杂的业务逻辑（如带有条件依赖的多步事务）中是否仍有效，有待验证
- **强操作延迟不优于基线**：`close_auction` 延迟与 OmniPaxos 持平（~245ms）——SL 的价值**完全集中在弱操作的加速上**，对强操作本身无帮助
- **弱操作"惊喜"的用户可见性**：SL 下弱操作可能被重排（如 bid 被后到的 close 覆盖），论文承认需要 UI 层处理来避免"surprises"，这是一个工程挑战
- **单主写入瓶颈**：DeMon 依赖主副本处理强操作，吞吐量受限于单水平——对强操作比例较高的场景可能成为瓶颈
- **Byzantine 容错未兑现**：论文讨论了 BFT 方向（§7），但未给出具体实现或评估

### 对团队的启示

1. **方向性依赖建模**是未来分布式系统的核心范式——我们内部系统（如 Agent 基础设施平台）的状态机设计应该从"哪些操作冲突"升级为"哪些操作需要观察哪些操作"
2. **Bag + Local Reordering** 是比 CRDT 更灵活的正确性工具——CRDT 需要操作本身是单调的，SL 则更通用
3. 论文 §7 的"非专家通过自然语言定义一致性"路线值得关注——对 AI Agent 时代的系统设计有前瞻意义

---

*精读完成于 2026-06-11 · CHANG_AI_TEAM CTO*
