---
type: concept
title: "Paxos Quorum Intersection Revised"
sources:
  - "sources/papers/Distributed-Consensus-Revised/精读分析.md"
tags:
  - 分布式系统
  - 共识算法
  - Paxos
  - Flexible-Paxos
  - Quorum
created: 2026-06-16
updated: 2026-06-16
status: stable
related:
  - "[[共识算法族系-从Paxos到广义解]]"
  - "[[Raft-共识算法协议核心]]"
  - "[[Paxos-理论到实践的鸿沟]]"
  - "[[Paxos-Value-Selection-Revised]]"
  - "[[Paxos-Epochs-Revised]]"
  - "[[分布式数据系统一致性体系]]"
---

# Paxos Quorum Intersection Revised

![[diagram/paxos-quorum-intersection.svg]]

> **来源**：Heidi Howard 博士论文 *Distributed Consensus Revised* (Cambridge, 2019) Chapter 4  
> **一句话**：Classic Paxos 要求所有 quorum 两两相交是过度保守的——只需 phase-1 quorums 与 phase-2 quorums 相交，且只需与过往 epoch 相交，即可保证安全。解除这一约束后，可以自由重配 Leader Election 的代价和 Log Replication 的性能。

---

## 1. 痛点：Classic Paxos 的过度保守

Classic Paxos（Lamport, 1998）的 Safety 建立在三个 quorum 不等式上：

```
(1) |Q| > n/2        → Majority Quorum 的基数假设
(2) Q₁ ∩ Q₂ ≠ ∅     → Phase-1 quorums 与 Phase-2 quorums 必须相交
(3) Q ∩ Q' ≠ ∅      → 所有 quorums 两两相交（all-to-all intersection）
```

其中 (1) 和 (3) 本质是等价的——当所有 quorums 使用同一集合 Q 时，(1) 是 (3) 的充分条件。而 Howard 指出：**(3) 中的 all-to-all intersection 是不必要的**。

### 为什么 all-to-all 是多余的？

Paxos 的两阶段协议分别在不同 quorum 上操作：

| 阶段 | 操作 | 使用的 Quorum |
|------|------|--------------|
| Phase 1 (Prepare/Promise) | Proposer 广播 Prepare(n)，收集 Promise 确认 | Phase-1 Quorum (Q₁) |
| Phase 2 (Propose/Accept) | Proposer 广播 Accept(n,v)，收集 Accept 确认 | Phase-2 Quorum (Q₂) |

Safety 只需要保证：**Phase-1 看到的任何已 commit value 不会在 Phase-2 被覆盖**。这就要求 Phase-1 quorum 与 Phase-2 quorum 相交——即 Q₁ ∩ Q₂ ≠ ∅。**但 Q₁ 内部不需要两两相交，Q₂ 内部也不需要两两相交**。

> **直觉**：Phase-1 只需要"看到"至少一个 Phase-2 quorum 中的 acceptor，从而发现可能已经 commit 的 value。不需要 Phase-1 quorum 内的 acceptor 之间互相认识。

---

## 2. Revision A：Flexible Paxos（跨 Phase 弱化）

### 2.1 形式化定义

设全体 acceptor 集合为 A，|A| = n。

**Classic Paxos 的 Quorum 约束**：

$$∀Q₁, Q₂ ∈ \mathcal{Q}: Q₁ ∩ Q₂ ≠ ∅ \quad\text{且}\quad ∀Q ∈ \mathcal{Q}: |Q| > n/2$$

**Revision A (Flexible Paxos) 的 Quorum 约束**：

$$∀Q₁ ∈ \mathcal{Q}₁, ∀Q₂ ∈ \mathcal{Q}₂: Q₁ ∩ Q₂ ≠ ∅$$

其中：
- $\mathcal{Q}₁$ 是 Phase-1 quorum 集合
- $\mathcal{Q}₂$ 是 Phase-2 quorum 集合
- Q₁ 内部不需要相交（$\exists Q₁^a, Q₁^b ∈ \mathcal{Q}₁: Q₁^a ∩ Q₁^b = ∅$ 是合法的）
- Q₂ 内部不需要相交

### 2.2 算法描述（伪码）

```
Algorithm: Flexible Paxos — Proposer
    
    /* Phase 1: Prepare */
    send ⟨Prepare, n⟩ to acceptors
    wait until promise from any Q₁ ∈ Q₁         ← 只需任意一个 Q₁
    if any promise contains (n', v') with committed flag:
        v ← v'  /* must use highest-epoch committed value */
    else:
        v ← own_value  /* free to propose own value */
    
    /* Phase 2: Propose */
    send ⟨Accept, n, v⟩ to acceptors
    wait until accept from any Q₂ ∈ Q₂           ← 只需任意一个 Q₂
    return v  /* value committed */
```

核心变化仅 2 处：
1. **Phase 1 等待条件**：从"任意 majority" 变为 "任意 Q₁ ∈ Q₁"
2. **Phase 2 等待条件**：从"任意 majority" 变为 "任意 Q₂ ∈ Q₂"

Acceptor 侧**无需任何修改**——这是最优雅之处：Flexible Paxos 对 acceptor 完全透明，所有变化仅体现在 proposer 的 quorum 等待条件上。

### 2.3 约束条件

合法配置必须满足：

$$∀q₁ ∈ Q₁, ∀q₂ ∈ Q₂: q₁ ∩ q₂ ≠ ∅$$

等价地，用补集表示：

$$|Q₁| + |Q₂| > n$$

即最小的 Q₁ 基数与最小的 Q₂ 基数之和必须大于总 acceptor 数。这揭示了 quorum 配置的**灵活性和代价**：

- Q₁ 越小 → Leader Election 代价越低，但 Q₂ 必须越大 → Log Replication 代价越高
- Q₂ 越小 → Log Replication 越快（降低提交延迟），但 Q₁ 必须越大 → Leader Election 门槛越高

---

## 3. Revision B：Per-Epoch 弱化

### 3.1 动机

Revision A 对 Phase-1 的要求仍然跨所有 epoch 生效。但实际安全要求更弱：**epoch e 的 Phase-1 只需要收集到那些 epoch < e 的 Phase-2 quorums 中可能已经 commit 的 value**。与 epoch > e 的未来 Phase-2 quorums 无关。

### 3.2 形式化定义

$$∀Q ∈ \mathcal{Q}^e_1, ∀f ∈ E: f < e ⇒ ∀Q' ∈ \mathcal{Q}^f_2: Q ∩ Q' ≠ ∅$$

其中：
- $\mathcal{Q}^e_1$ 是 epoch e 的 Phase-1 quorum 集合
- $\mathcal{Q}^f_2$ 是 epoch f 的 Phase-2 quorum 集合
- E 是所有 epoch 的集合

### 3.3 关键推论：Minimum Epoch 可跳过 Phase-1

设 $e_{min}$ 为当前所有 active proposer 中的最小 epoch 编号。由于不存在 $f < e_{min}$ 的 Phase-2 quorum，约束退化为 trivially true。因此：

> **持有 $e_{min}$ 的 proposer 可以跳过 Phase-1，直接进入 Phase-2。**

这为 Leader-based 优化（如 Multi-Paxos 的 Leader 预分配 epoch）提供了理论依据。在一个 epoch 被唯一分配后，Phase-1 完全可省略。

### 3.4 与 Multi-Paxos 的关系

这正好解释了 Multi-Paxos 中"Leader Election 后跳过 Phase-1"为什么安全——不是因为 Leader 特殊，而是因为 Leader 被分配了一个唯一的 epoch，且**该 epoch 在 active proposer 中是最小（或唯一）的**。

`Revision B ⇒ Multi-Paxos Phase-1 skipping`，但反过来 Multi-Paxos 也可以配置为非最小 epoch 的 proposer 跳过 Phase-1，只要保证 quorum intersection 约束。Revision B 比 Multi-Paxos 更通用。

---

## 4. 安全证明策略

### 4.1 经典证明中的缺陷

Classic Paxos 的 Lemma 11（Safety Lemma）证明依赖于：

> 如果 value v 已在 round i 的 majority 中被 accepted，则所有 round j > i 的 proposer 必然 propose v。

该证明的关键步骤是：round i 的 majority Q₂ 与 round j 的 majority Q₁ 相交 → round j 的 proposer 必定在 Phase-1 收到至少一个承诺了 v 的 acceptor。

### 4.2 Howard 的修正

Howard 证明：**Lemma 11 不需要 all-to-all intersection**。仅需：

1. **跨 phase 相交**（Revision A）：proposer 的 Phase-1 quorum Q₁ 与已接受 v 的 Phase-2 quorum Q₂ 相交
2. **跨 epoch 向前相交**（Revision B）：只需要与 epoch < e 的 Phase-2 quorums 相交

证明结构（简化）：

```
Lemma (Safety under Revision A):
  Assume: ∃Q₂ ∈ Q₂ s.t. all a ∈ Q₂ have accepted (n, v)
  For any proposer p in epoch e' > e with Q₁ ∈ Q₁^e':
    Q₁ must intersect Q₂ (by Revision A constraint)
    → ∃a ∈ Q₁ ∩ Q₂ s.t. a returns promise with (n, v)
    → p must propose v (by value selection rule)
  ∴ No different value can be chosen
```

完整的 TLA+/PlusCal 形式化验证在论文附录中。

---

## 5. Implications 与应用场景

### 5.1 典型配置

| 配置 | Q₁ | Q₂ | Q₁∩Q₂ 约束 | 特点 |
|------|-----|-----|-------------|------|
| **Classic Paxos** | Majority (⌊n/2⌋+1) | Majority (⌊n/2⌋+1) | All-to-all | 退化到标准 Paxos |
| **All Aboard Paxos** | `{{a₁}, {a₂}, {a₃}}` | `{{a₁,a₂,a₃}}` | ∀q₁ ∃q₂ 相交 | 全存活时 1 RTT 提交（单 acceptor Phase-1）|
| **Singleton Paxos** | `{{a₁,a₂,a₃}}` | `{{a₁}, {a₂}, {a₃}}` | ∀q₁ ∃q₂ 相交 | 1 RTT 提交+高读吞吐 |
| **General Flexible** | `{{a₁,a₂}, {a₃,a₄}}` | `{{a₁,a₃}, {a₂,a₄}}` | 跨 quorum 相交 | 2/4 即可完成每次 phase |

### 5.2 Multi-Paxos 优化：偶数节点 Quorum 减半

Classic Paxos 在 n 个节点中要求 $f = \lfloor (n-1)/2 \rfloor$ 容错，quorum size = $\lceil n/2 \rceil + 1$。但 n 为偶数时存在浪费：

- n = 4：Classic → Q₁ = Q₂ = 3，容错 1
- n = 4：Flexible → Q₁ = 2, Q₂ = 2，容错仍为 1（一个节点故障仍可完成）

**推论**：对于偶数节点集群，Flexible Paxos 可将 Phase-2 quorum 从 n/2+1 降至 n/2，**同时保持相同容错能力**。

### 5.3 Phase-1 与 Phase-2 的 Trade-off

| 目标 | Q₁ 配置 | Q₂ 配置 | 代价 |
|------|---------|---------|------|
| **降低 Leader Election 成本** | 缩小 Q₁ | 必须扩大 Q₂ | Log Replication 变慢 |
| **降低提交延迟（Fast Commit）** | 扩大 Q₁ | 缩小 Q₂ | Leader Election 门槛升高 |
| **最小化 RTT** | 缩小 Q₁ 到单节点 | 扩大 Q₂ 到全节点 | 仅在全存活时可用 |

---

## 6. 与 Raft / CockroachDB 的对比

| 维度 | Raft | Flexible Paxos |
|------|------|----------------|
| Quorum 模型 | 固定 Majority（⌊n/2⌋+1） | 可配置 Q₁ ≠ Q₂ |
| Leader Election | 随机超时 → Candidate → RequestVote | Phase-1 受 Q₁ 约束 |
| 跳过 Phase-1 | Leader 隐式跳过（固定 Leader） | 通过 Revision B 显式跳过（最小 epoch） |
| Quorum 灵活性 | 无 | Q₁/Q₂ 独立可调 |
| 工程成熟度 | etcd/TiKV/CockroachDB 广泛验证 | WPaxos/DPaxos 有部分实践验证 |

**CockroachDB** 使用 Raft 的 majority quorum，但在 geo-distributed 场景下性能受限于跨地域 RTT。Flexible Paxos 的衍生方案 **WPaxos** (Ailijiang, 2016) 允许 WAN 延迟代价更高的一方使用更小的 Q₂，降低跨地域提交延迟，已部分应用于生产环境。

---

## 7. Core Insight 回顾

1. **Classic Paxos 的 all-to-all quorum intersection 是不必要的**——只需跨 phase 相交
2. **Quorum 可以按 phase 拆分**——Phase-1（Prepare）和 Phase-2（Accept）使用不同的 quorum 集合
3. **Per-epoch weakening 进一步缩减约束**——只需和过往 epoch 相交
4. **最小 epoch proposer 可跳过 Phase-1**——为 Leader-based 优化提供理论基础
5. **Acceptor 侧零修改**——所有变化仅在 proposer 的 quorum 等待逻辑
6. **偶数节点可直接受益**——quorum size 从 n/2+1 降至 n/2
7. **Q₁ 和 Q₂ 的 trade-off 是可配置的**——从 Leader Election 成本到提交延迟可灵活调整

---

## 8. 待深挖问题

- [ ] Flexible Paxos 在**跨地域部署**场景下 Q₁/Q₂ 的最优配置策略（WPaxos 的扩展）
- [ ] Revision B 与 **Raft Leader Election + No-op Entry** 的效率量化对比
- [ ] 动态 Q₁/Q₂ 重配（Dynamic Quorum Reconfiguration）的安全条件——论文 Ch 4 未覆盖
- [ ] Flexible Paxos 在 **Byzantine Fault Tolerance** 下的扩展（论文 §1.6 明确排除 BFT）
- [ ] Q₁ 与 Q₂ 非对称配置下的**负载均衡**问题（小 Q₁ 的 proposer 可能成为热点）
- [ ] Ch 5（Quorum Transitivity）与 Ch 4 的工程融合——如何利用 transitivity 进一步缩小 Phase-1 等待
