---
type: concept
title: "Paxos Value Selection Revised"
sources:
  - "sources/papers/Distributed-Consensus-Revised/精读分析.md"
tags:
  - 分布式系统
  - 共识算法
  - Paxos
  - Flexible-Paxos
  - Quorum
  - Value-Selection
created: 2026-06-16
updated: 2026-06-16
status: stable
related:
  - "[[共识算法族系-从Paxos到广义解]]"
  - "[[Paxos-Quorum-Intersection-Revised]]"
  - "[[Paxos-Epochs-Revised]]"
  - "[[Raft-共识算法协议核心]]"
---

# Paxos Value Selection Revised

![[diagram/paxos-value-selection.svg]]

> **来源**：Heidi Howard *Distributed Consensus Revised* (Cambridge, 2019) Chapter 6  
> **一句话**：Classic Paxos 强制 proposer 在 Phase-2 中 propose "Phase-1 收到最高 epoch 关联的 value" ，这个规则是**充分的但不是必要的**——通过 quorum 级别的细粒度判断，proposer 有更多机会 propose 自己的 candidate value，从而显著减少被迫继承之前 proposal 的概率。

## 定义：Value Selection 问题的形式化

在 Paxos Phase-1 结束后，proposer 从一组 acceptor 收到了 promise 响应：每个响应要么是 `nil`（该 acceptor 之前未 accept 任何 value），要么是 `(epoch, value)` 对。Value Selection Rule 决定了 **Phase-2 中 proposer 应该 propose 哪个 value**。

### 核心约束

Value Selection Rule 必须满足的唯一安全性约束（Non-triviality）：

> 如果任意 value 已经或可能已被 commit，proposer 必须 propose 该 value。

等价于：

```
possibleValues(R) = { v | ∃ 一个 quorum Q 上可能已 commit v }
mustPropose = 
  - 如果 possibleValues(R) = ∅  → 可以 propose candidate value
  - 如果 possibleValues(R) = {v} → 必须 propose v
  - 如果 |possibleValues(R)| > 1 → 任意选一个即可（对 safety 无影响，选哪个都不会破坏 safety）
```

> **关键洞察**：Classic Paxos 的 "选最高 epoch" 只是计算 `possibleValues(R)` 的**一种实现方式**——而且是最保守的一种。

## Classic Value Selection 回顾

### Algorithm 17: Classic `possibleValues(R)`

```
Input:  R ← { (epoch, value) 对或 nil 的 promise 响应集合 }
Output: 可能已被 commit 的 value 集合

1. 找出 R 中所有 epoch 最大的 (e, v) 对
2. 如果存在这样的 v → return {v}
3. 如果所有响应都是 nil → return ∅
```

**保守性体现**：Algorithm 17 只要看到**任意**一个不同 epoch 的 value pair，就放弃自己的 candidate value。但它没有区分：
- 这个值是否已经在某个 quorum 上被 commit？
- 还是仅仅停留在某些 acceptor 上但从未达成 commit？

### Paxos Made Simple 的规则

Lamport 在 "Paxos Made Simple" 中的表述：

> If the proposer receives responses from a majority of acceptors, then it must propose the value with the highest proposal number.

这只是一个**充分条件**——满足它则 safety 成立。但它**不是必要条件**——在很多情况下 proposer 不必被最高 epoch 的 value 绑定。

**例子**：假定 n=3，majority=2，proposer 收到两个 promise：
- acceptor 1：`(epoch=5, v="a")`
- acceptor 2：`nil`

Classic 规则要求 propose `"a"`（因为 epoch 5 是最高有效 epoch）。但如果 acceptor 2 返回 nil，意味着 acceptor 1 和 acceptor 2 组成的 quorum 上**不可能**已 commit epoch-5 的 `"a"`（因为 acceptor 2 对 epoch 5 一无所知），proposer 完全可以 propose 自己的 value。

## Quorum-based Value Selection

Howard Chapter 6 的核心贡献：将 Value Selection 从"按 epoch 排名"转为"按 quorum 粒度逐一判断"。

### 核心思想

Phase-1 收到底 promise 响应后，对每个 quorum Q ∈ Q₂，判断 Q 上是否可能已 commit 某个 value：

```
For each quorum Q ∈ Q₂:
  检查 Q 中 acceptor 的 promise 响应
  → 判断 Q 上是否 commit 了 value v
  → D[Q] = no | yes(v)
```

### Algorithm 18: Quorum-based `possibleValues(R)`

```
Input:  R ← promise 响应集合（每个响应: nil | (epoch, value)）
        Q₂ ← Phase-2 quorum 集合
Output: 可能已被 commit 的 value 集合

possible ← ∅
For each quorum Q ∈ Q₂:
   如果 ∀a ∈ Q, a 返回 nil:
       → D[Q] = no  (Q 上未 commit 任何 value，因为 Q 中无人 accept)
   如果 ∃a ∈ Q 返回 (e, v)，且 ∀a' ∈ Q 也返回 (e, v) 或 nil:
       → D[Q] = yes(v)  (Q 上可能已 commit v)
   如果 ∃a₁ ∈ Q 返回 (e, w)，∃a₂ ∈ Q 返回 (f, x) 且 w ≠ x:
       → D[Q] = no  (两个不同 value 不可能同时在一个 quorum 上 commit)

   如果 D[Q] = yes(v):
       possible = possible ∪ {v}

return possible
```

### 规则的关键扩展

相比 Algorithm 17，Algorithm 18 增加了两个"排除条件"：

| 条件 | 含义 | 为什么安全 |
|------|------|-----------|
| Q 中存在 nil 响应 | Q 上未 commit（commit 要求 Q 中所有 acceptor 都 accept） | 如果 Q 中存在一个未 accept 的 acceptor，Q 不可能形成 commit |
| Q 中存在两个不同 epoch 的不同 value | Q 上未 commit（同一 quorum 不可能 commit 两个不同的 value） | 一个 quorum 的 commit 只能对应一个 value |

> **本质区别**：Classic 对整个 response set 做全局最大值判断；Quorum-based 对**每个 quorum 独立**做 commit 可能性判断。

## 关键引理

### Lemma 19: nil promise 的排除力

> 如果 acceptor a 对 epoch g 返回 nil promise，则**任何包含 a 的 quorum** 上未 commit 任何 epoch ≤ g 的 value。

**直觉**：如果 acceptor a 对 epoch g 返回 nil，说明 a 在 epoch g 之前（或之时）从未 accept 任何 value。而任何包含 a 的 quorum 要 commit 一个 epoch ≤ g 的 value，必须要求 a 在 ≤ g 的 epoch 上 accept 该 value——这与 nil 响应矛盾。

**推论**：
- 一个 nil 响应可以同时排除**多个 quorum**（所有包含该 acceptor 的 quorum）
- 这比 Classic 的"只看最高 epoch"具有更强的排除力

### Lemma 20: 不同 epoch 不同 value 的排除力

> 如果 acceptor a₁ 返回 (g, e, w) 且 acceptor a₂ 返回 (g, f, x)，其中 e < f 且 w ≠ x，则包含 a₁ 的 quorum 上未 commit 任何 epoch ≤ g 的 value。

**直觉**：如果包含 a₁ 的 quorum Q 已 commit epoch ≤ g 的 value v'，则 a₁ 必须在 epoch ≤ g 时 accept v'。但 a₁ 承诺的是 epoch g 时 accept 了 w（e ≤ g），而 w ≠ x。同时 a₂ 承诺的是 epoch f 时 accept 了 x。若 v' 已被 commit，必须存在一个 quorum Q' 上 commit v'——这个 Q' 和包含 a₁, a₂ 的 quorum 的交集会导致矛盾。

**推论**：即使两个不同的 value 在不同的 epoch 被不同的 acceptor accept，也可以排除 commit 的可能性——**只要存在 epoch 的差异**。

### Lemma 21: Epoch-dependent 扩展

> 在 Revision B/C 的 epoch-dependent 框架中，quorum 判断还需区分 epoch：一个 quorum Q 上在 epoch g 之后可能 commit v，但在 epoch g 之前可能 commit w。

这使得 `D[Q]` 从一个简单的 yes/no 二进制判断变为**epoch 依赖的多值判断**：

```
D[Q][e] = 
  - no: 在 epoch ≤ e 的范围内，Q 上未 commit
  - yes(v): 在 epoch ≤ e 的范围内，Q 上可能已 commit v
```

## Epoch-dependent 扩展 (Revision B/C)

### 动机

在 Revision B 的框架中（每个 epoch 有不同的 Phase-2 quorum 集合，Phase-1 quorum 只需和前序 epoch 的 Phase-2 quorum 相交），value selection 面临新挑战：

> 一个更大的 epoch g 的 proposer 收集到的信息可能被**低 epoch 的 stale 信息误导**——因为低 epoch 的 quorum 配置可能已经失效或与当前 epoch 无关。

### Epoch-dependent 判断规则

```
For each epoch f < g (g 是当前 proposer 的 epoch):
  For each quorum Q ∈ Q₂[f] (epoch f 使用的 Phase-2 quorum 集合):
    用 Algorithm 18 的逻辑判断 Q 在 epoch ≤ f 的范围内是否 commit 了某个 value
    → D[Q][f] = no | yes(v)

然后对所有 f < g 的 D[Q][f] 汇总：
  - 如果 ∃v 使得 ∀f, Q 满足 D[Q][f] = yes(v) → 必须 propose v
  - 否则 → 可以 propose candidate value
```

**效果**：更大 epoch 的 proposer 不会被低 epoch 的"可能但未必发生的 commit"束缚——低 epoch 的信息只在其对应 epoch 范围内有约束力。

## 安全证明思路

### 证明目标

> 如果 proposer 使用 Quorum-based Value Selection 规则选择 value v 并成功在 Phase-2 中 propose，则 v 满足 Non-triviality 约束（即不会覆盖一个已 commit 的不同 value w）。

### 证明框架

采用反证法：假设 proposer p 使用 Algorithm 18 选择了 value v，但某个已 commit 的 value w ≠ v 被覆盖。

1. **存在性**：w 的 commit 意味着存在某个 quorum Q* ∈ Q₂，Q* 中所有 acceptor 在某个 epoch e* 上 accept 了 w
2. **证明 Q* 未被排除**：p 在 Phase-1 中必须从 Q* 中的**至少一个** acceptor 收到 promise 响应（由 Quorum Intersection 保证：Q₁ ∩ Q* ≠ ∅）
3. **信息冲突**：如果 p 收到的信息表明 Q* 上可能已 commit w，则 Algorithm 18 的 D[Q*] 应为 yes(w)，p 必须 propose w
4. **结论**：只有 D[Q*] = no 时 p 才不应 propose w，而 Lemma 19/20 保证 D[Q*] = no 时 Q* 上确实未 commit w，矛盾不成立

### 与 Classic 证明的差异

| 维度 | Classic (Algorithm 17) | Quorum-based (Algorithm 18) |
|------|------------------------|---------------------------|
| 排除条件 | 无（只看最高 epoch） | Lemma 19: nil → 排除所有包含该 acceptor 的 quorum |
| 判断粒度 | 全局 | 每个 quorum 独立 |
| 保守程度 | 最大保守（总是取最高 epoch） | 最小保守（仅排除已证不可能的 quorum） |
| 证明复杂度 | 简单（直接依赖 epoch 排序） | 略高（需要 per-quorum 排除推理） |

## 实际应用场景

### 何时有最大收益

Quorum-based Value Selection 在以下场景下收益最大：

| 场景 | 为什么收益大 |
|------|-------------|
| **Phase-1 收集到多于最小所需的 promise** | 更多信息 = 更多 quorum 被排除 = 更多机会 propose candidate |
| **Phase-2 quorum 大小较小**（如 Flexible Paxos 配置） | 较少的 quorum = 更容易用 nil/conflict 完全排除 |
| **高 contention 工作负载**（频繁 dueling） | 经典规则下 proposer 频繁被迫 propose 上一个竞争者的 value；QVS 下可以被 quorum 级排除释放 |
| **大 n 集群**（多数 acceptor） | 更多 acceptor = 更多 nil 响应 = 更多 quorum 被排除 |

### 代价

| 代价 | 说明 |
|------|------|
| **可能需要等待更多 promise** | 为获得足够信息排除所有 quorum，proposer 可能需要收集超过 minimal quorum 的 promise 响应 |
| **计算复杂度略高** | 需要检查 O(\|Q₂\|) 个 quorum，每个 quorum O(\|Q\|) |
| **在 minimal 收到底 promise 时可能退化** | 如果只收到底 exact quorum 的响应且其中无 nil/conflict，则退化为 Classic 行为 |

### 与 Flexible Paxos 的协同

Ch 6 的 Value Selection 和 Ch 4 的 Quorum Intersection 之间存在协同效应：

> Flexible Paxos 允许 Phase-2 quorum size 减小（例如从 majority 降至 less-than-majority），这使得 Phase-2 quorum 数量**减少**，更容易被排除。Combining 两者意味着 proposer 有**双重增加 propose candidate value 的机会**。

## 伪码：完整 Value Selection 流程

```
function selectValue(g, R, Q₂):
  // g: 当前 proposer 的 epoch
  // R: Phase-1 promise 响应集合 { (acceptor, epoch, value) | nil }
  // Q₂: Phase-2 quorum 集合
  
  committed ← ∅  // 已知一定被 commit 的 values
  
  for each quorum Q ∈ Q₂:
    decision ← decideQuorum(Q, R)
    if decision.type == "committed":
      committed = committed ∪ {decision.value}
  
  if |committed| == 1:
    return committed[0]  // 必须 propose 这个 value
  else:
    return myCandidate  // 可以 propose 自己的 value

function decideQuorum(Q, R):
  values ← {}
  all_nil ← true
  
  for each acceptor a ∈ Q:
    if a ∉ R:  // 未收到 a 的 promise
      return {type: "unknown"}  // Q 状态未知
    resp ← R[a]
    if resp ≠ nil:
      all_nil ← false
      values = values ∪ {resp.value}
  
  if all_nil:
    return {type: "not_committed"}  // Lemma 19
  
  if len(values) > 1:
    return {type: "not_committed"}  // Lemma 20: 不同 value
  
  return {type: "committed", value: values.only()}  // 可能已 commit
```

### Epoch-dependent 变体

```
function selectValueEpochAware(g, R, Q₂_history):
  // g: 当前 proposer 的 epoch
  // R: Phase-1 promise 响应
  // Q₂_history: Q₂[f] for each f < g
  
  for each epoch f < g:
    for each quorum Q ∈ Q₂[f]:
      decision ← decideQuorumEpoch(Q, R, f)
      // ... 累积 per-epoch 信息
```

## 待深挖问题

1. **Quorum-based Value Selection 在真实系统中的 benchmark**：Howard 在 thesis 中给出了理论正确性证明，但缺少与 Classic Value Selection 在生产级 Multi-Paxos 实现中的吞吐/延迟对比
2. **与 Epochs by Recovery (Ch 7) 的交互**：如果 epoch 不唯一，两个不同 proposer 在 Phase-1 收到重叠的 acceptor 集，QVS 如何确保 safety？
3. **在 Multi-Paxos 中的实例索引管理**：QVS 主要针对 single-decree Paxos，在 Multi-Paxos 中每个 log entry 独立运行 QVS 是否会导致状态空间爆炸？
4. **部分 quorum 未知时的 fallback 策略**：Algorithm 18 中如果某些 quorum 因未收到底足够 promise 而无法判断，是等待更多 promise 还是退化回 Classic 行为？
5. **与 FPaxos 实现的兼容性**：现有的 FPaxos (Go 实现) 是否已采用 QVS，还是依赖简化版的 "highest epoch" 规则？
