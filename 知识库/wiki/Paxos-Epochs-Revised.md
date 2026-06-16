---
type: concept
title: "Paxos Epochs Revised"
sources:
  - "sources/papers/Distributed-Consensus-Revised/精读分析.md"
tags:
  - 分布式系统
  - 共识算法
  - Paxos
  - Flexible-Paxos
  - Epoch
  - Fast-Paxos
created: 2026-06-16
updated: 2026-06-16
status: stable
related:
  - "[[共识算法族系-从Paxos到广义解]]"
  - "[[Paxos-Quorum-Intersection-Revised]]"
  - "[[Paxos-Value-Selection-Revised]]"
  - "[[Raft-共识算法协议核心]]"
  - "[[Raft-集群成员变更]]"
---

# Paxos Epochs Revised

![[diagram/paxos-epochs-revised.svg]]

> 基于 Heidi Howard 博士论文 "Distributed Consensus Revised" Chapter 7 的核心内容。Howard 在 Ch 4–6 分别弱化了 Quorum Intersection、Phase Completion、Value Selection 三个维度的要求后，在 Ch 7 将目光投向 Classic Paxos 的第四个核心假设——**epoch 全局唯一性**，提出了 4 种 epoch 分配方案，其中 **Epochs by Recovery** 是最重要的理论突破。

## 一句话总结

**Classic Paxos 要求 epoch 全局唯一（每个 proposer 预分配互不重叠的 epoch 区间）——这不是共识问题的内在约束，而是工程便利的实现选择。Howard 通过 4 种替代的 epoch 分配方案证明：epoch 可以按需动态分配、从 value 映射得到、甚至允许多个 proposer 共用同一个 epoch，从而在 quorum intersection 弱化的基础上进一步释放了 Paxos 的性能潜力和去中心化能力。**

## 痛点：为什么 Epoch 分配需要 "Revised"

### Classic Paxos 的 Epoch 假设

在 Classic Paxos 中，每个 proposer 被**预分配一组互不相交的 epoch 区间**，epoch 严格递增且全局唯一。这一假设带来了三个工程后果：

| 后果 | 机制 | 影响 |
|------|------|------|
| **只有最小 epoch 的 proposer 能跳过 phase-1** | 因为 Revision B (Ch 4.2) 要求 phase-1 quorum 与所有更小 epoch 的 phase-2 quorum 相交，只有 e<sub>min</sub> 的 proposer 没有更小的 epoch 需要 intersect | 其他 proposer 都必须执行完整两轮 |
| **Multi-Paxos 需要中央 Leader** | 为了让一个 proposer 始终拥有 e<sub>min</sub>，必须锁定一个固定的 leader → **leader bottleneck** | 吞吐受限于 Leader 节点 |
| **Fast Paxos 试图去中心化但受限** | Fast Paxos 允许任意 proposer 直接发起 phase-2，但要求 fast quorum 和 classic quorum intersect → 实际中需要 ~3/4 多数 | 去中心化代价高，不如预想中高效 |

### Howard 的核心质疑

> "What if epoch uniqueness is an unnecessary engineering convenience, not a theoretical necessity?"

Howard 的洞见：**epoch 可以用来排序提案（ordering），但排序不要求唯一性**。如果允许多个 proposer 使用同一个 epoch，只要它们提出的还是同一个 value，就不需要区分谁先谁后——多 proposer 并发相同 value 是无冲突的。

## 四种 Epoch 分配方案

Howard 在 Ch 7 中提出了 4 种 epoch 分配方案，从保守到激进，构成一个 flexibility ladder：

| 方案 | Epoch 唯一性 | 最少 RTT | 中心化程度 | 去中心化程度 |
|------|-------------|---------|-----------|------------|
| Pre-allocation (Classic Paxos) | 全局唯一 | 2 RTT | 强中心化 (Leader) | ↓ 低 |
| Epochs by Allocator (§7.1) | Allocator 分配 | 2 RTT | 中等 (Allocator 是瓶颈) | |
| Epochs by Value Mapping (§7.2) | 同值同 epoch | 1~2 RTT | 无 (hash-based) | |
| ★ Epochs by Recovery (§7.3) | 不强求唯一 | 1 RTT | 无 (去中心化) | ↑ 高 |
| Multi-path Paxos (§7.4) | 混合 | 自适应回退 | 可配 | 最佳 |

详见配图 `![[diagram/paxos-epochs-revised.svg]]`。

## Epochs by Allocator (§7.1)

### 方案

引入一个外部 **Allocator** 服务，专门负责分配最小的 epoch。任何 proposer 在开始新一轮 proposal 之前，先向 Allocator 请求一个最小 epoch (e<sub>min</sub>)，然后用该 epoch 执行 phase-2（跳过 phase-1）。

### 协议流程

![[diagram/epochs-by-allocator-sequence.svg]]

### 性质

| 属性 | 说明 |
|------|------|
| **延迟** | 2 RTT（allocator + acceptors），与 Classic Paxos 两阶段相当 |
| **吞吐瓶颈** | Allocator 是单点，成为新的瓶颈 |
| **可用性** | Allocator 故障 → 无法分配新 epoch → 系统不可用 |
| **适用场景** | 延迟敏感但吞吐需求不高的部署 |

### 与 Classic Paxos Leader 的区别

Allocator 比 Leader 更轻量：
- Leader 需要执行完整的提案流程（phase-1 + phase-2 + 日志复制）
- Allocator 只需要分配一个 epoch number，不参与 proposal 流程
- 但 Allocator 仍然是单点瓶颈（性能 + 可用性），没有从根本上解决去中心化问题

## Epochs by Value Mapping (§7.2)

### 方案

Epoch 通过 **hash(value)** 映射得到。如果两个 proposer 有相同的 candidate value，它们将自动使用相同的 epoch，因此不会产生 dueling。如果 value 不同，则按 Classic Paxos 的正常流程处理。

### 协议

```
e = hash(value) mod MAX_EPOCH

Proposer:
  1. 确定 candidate value v
  2. 计算 e = hash(v)
  3. 以 epoch e 执行 phase-1（收集之前 epoch 的 promise）
  4. 以 epoch e 执行 phase-2（propose v）
```

### 性质

| 属性 | 说明 |
|------|------|
| **去中心化** | ✅ 无需外部协调器，proposer 自行计算 epoch |
| **Dueling 特性** | 同 value → 同 epoch → 无冲突；异 value → 正常 dueling resolution |
| **局限性** | epoch 由 value 决定，无法保证 proposer 获得 e<sub>min</sub>（可能仍需 phase-1） |
| **适用场景** | 高 value 重复率的工作负载（如配置更新、元数据操作） |

### 限制

1. **Hash 碰撞**：虽然概率极低，但 hash 碰撞会导致不同 value 映射到同一 epoch → 需要额外的冲突处理
2. **epoch 不可控**：proposer 无法控制自己获得的是 e<sub>min</sub>，因此未必能跳过 phase-1
3. **value 必须先确定**：必须先有 candidate value 才能计算 epoch → 如果 proposer 在 phase-1 后改变了 candidate value（按 value selection 规则），epoch 会随之改变

## Epochs by Recovery (§7.3) — 核心突破

### 核心思想

**不再要求 epoch 全局唯一。**允许多个 proposer 使用同一个 epoch，但施加额外约束以确保 safety：

> **Property 17 (Same Value Requirement)**：如果一个 acceptor 在 epoch `e` 收到了某个 value 的 propose，那么它在该 epoch 内只能接受同一个 value 的后续 propose。

换句话说：同一个 epoch 内，所有 proposer 必须提议**相同的 value**，否则该 epoch 内的冲突需要通过额外的 recovery 机制解决。

### 为什么这能工作？

在 Classic Paxos 中，epoch 的唯一性保证的是：如果两个 proposer 在竞争，epoch 大的"赢"，epoch 小的"输"。但这本质上是一个**排序机制**——我们需要的不是 epoch 的唯一性，而是**冲突时的决议能力**。

Epochs by Recovery 的洞察：**如果两个 proposer 提出相同 value，根本不需要排序——它们达成了一致**。只有当它们提出不同 value 时，才需要区分"哪个赢"。而允许多 proposer 共用 epoch 后，如果它们在同一 epoch 内提出不同 value，则通过 recovery（重新分配新 epoch 并走完整 round）来 resolve。

### 安全性质

Howard 通过以下性质证明 Epochs by Recovery 的 safety：

| 性质 | 内容 | 作用 |
|------|------|------|
| **Property 17** | Acceptor 在同一个 epoch 内只接受一个 value | 防止同一 epoch 内出现两个不同 value |
| **Property 18** | 如果某个 value 在 epoch `e` 被 commit，则所有更大的 epoch 也必须 commit 同一 value | 保证跨 epoch 的 value 一致性 |
| **Property 19** | 如果某个 value 在 epoch `e` 被 commit，则任何在 epoch `e` 之后启动的 proposer 都会通过 phase-1 获知该 value | 保证 recovery 能发现已 commit 的 value |

### 核心 Lemma

> **Lemma 26**：在 Epochs by Recovery 下，acceptor 不会在同一个 epoch 内接受两个不同的 value。

> **Lemma 27**：在 Epochs by Recovery 下，同一个 epoch 内不能有两个不同的 value 被 commit。

这两个 Lemma 共同保证：**即使多个 proposer 共享同一个 epoch，safety 仍然成立**——要么它们提出相同 value（无冲突），要么提出不同 value 但至少一方会在 phase-1 中检测到冲突并进入 recovery。

### 算法伪码

```
=== Acceptor (Epochs by Recovery) ===

state:
  promised:  epoch   # 承诺不接受小于此 epoch 的 proposal
  accepted:  (epoch, value) or nil

on Prepare(e):
  if e > promised:
    promised = e
    reply Promise(e, accepted)

on Propose(e, v):
  if e >= promised:
    if accepted == nil or accepted.epoch < e or accepted.value == v:
      # Property 17: same epoch → must be same value
      accepted = (e, v)
      promised = e
      reply Accept(e, v)
    else:
      # 同 epoch 不同 value → 拒绝
      reply Reject(e, accepted)


=== Proposer (Epochs by Recovery) ===

state:
  candidate_value: v        # 要 propose 的 value
  current_epoch:   e        # 当前使用的 epoch

on start(v):
  e = choose_epoch()        # 任意 epoch 分配策略
  # Phase 1
  promises = broadcast Prepare(e) to acceptors
  if received quorum Q₁ of promises:
    # 检查是否有已 commit 的 value
    committed_v = check_quorum_based_value_selection(promises)
    if committed_v:
      v = committed_v
    # Phase 2
    accepts = broadcast Propose(e, v) to acceptors
    if received quorum Q₂ of accepts:
      # 决策达成
      decide(v)
    else:
      # Phase 2 失败 → 递增 epoch 重试（recovery 路径）
      e = e + 1
      retry from Phase 1

on Recovery(e_old, conflict):
  # 当同 epoch 出现 value 冲突时触发
  e_new = choose_new_epoch()  # 确保不与任何活跃 proposer 的 epoch 冲突
  restart with e_new and Phase 1
```

### 与 Classic Paxos 的关键差异

| 维度 | Classic Paxos | Epochs by Recovery |
|------|--------------|-------------------|
| **Epoch 唯一性** | 全局唯一（pre-allocated） | 不要求唯一 |
| **同一 epoch 多 proposer** | 不允许 | 允许，只要 value 相同 |
| **Phase-1 可跳过** | 只有 e<sub>min</sub> 的 proposer | 任何 proposer，只要 value 与之前 commit 的相同 |
| **冲突处理** | Epoch 竞争（更高的赢） | Recovery（检测冲突后重新分配 epoch） |
| **去中心化能力** | 需要 Leader | 天然多 proposer |

### 泛化 Fast Paxos

Epochs by Recovery 可以视为 **Fast Paxos 的广义版本**：

- **Fast Paxos**：允许 proposer 跳过 phase-1 直接进入 phase-2（fast path），但要求 fast quorum 和 classic quorum intersect → 多数场景下需要 ~3/4 的 quorum size
- **Epochs by Recovery**：允许多个 proposer 并发使用同一个 epoch 直接进入 phase-2，不要求 fast/classic quorum 的额外 intersection → quorum requirement **更弱**

原因：Fast Paxos 必须保证 fast path 上的任何两个 proposal 之间存在 quorum intersection，因为这两个 proposal 可能包含不同的 value。而 Epochs by Recovery 通过 Property 17 将冲突限制为"同一 epoch 内 value 必须相同"，因此**不同 value 的冲突不会发生在同一 epoch 内**，自然不需要额外的 quorum intersection 来保证 safety。

### 应用场景

| 场景 | 优势 | 说明 |
|------|------|------|
| **低冲突工作负载** | 多数 proposer 提出相同 value → 一轮完成 | 类似于 "majority always agrees" 的乐观路径 |
| **去中心化系统** | 无需固定 Leader | 符合 P2P / edge 共识场景 |
| **Geo-distributed** | 各区域 proposer 可用不同 epoch 并发 | 跨地域场景减少 WAN 往返次数 |
| **高可用优先** | Leader 故障不影响系统运行 | 无 Leader bottleneck |

## Multi-path Paxos (§7.4) — 混合方案

### 动机

Epochs by Recovery 在大多数场景高效，但在 Allocator 可用时如果能利用它获得 e<sub>min</sub> 会更优。Multi-path Paxos 是一种**自适应混合方案**，根据系统状态动态选择最优路径。

### 设计

Multi-path Paxos 提供 4 条自适应执行路径，详见配图 `![[diagram/paxos-epochs-revised.svg]]`。

### 路径优先级

| 路径 | Epoch 来源 | 延迟 | 条件 |
|------|-----------|------|------|
| **A (Allocator)** | Allocator 分配的 e<sub>min</sub> | 2 RTT | Allocator 可用 |
| **B (Value Mapping)** | hash(value) | 2–4 RTT | candidate value 已知 |
| **C (Recovery)** | 自选任意 epoch | 2–4 RTT | 无外部依赖 |
| **D (Classic)** | Pre-allocated | 4 RTT (P1+P2) | 所有优化路径均失败 |

### 自适应策略

Multi-path Paxos 的关键在于**运行时自适应**：
1. 优先尝试路径 A（Allocator 可用且响应快）
2. 如果 Allocator 超时或不可用 → 回退到路径 B/C
3. 如果路径 C 发生冲突（同 epoch 不同 value）→ Recovery 后走路径 D

> 这种设计哲学与 Howard 的整体 thesis 方法一致：**不强求单一最优解，而是提供一个可配置的算法族，让部署者根据实际条件选择**。

## 与 Fast Paxos 的形式对比

### Fast Paxos 的 Quorum 约束

Fast Paxos (Lamport, 2006) 要求：任意 fast quorum 必须与任意 classic quorum 相交，即：

```
∀ Q_fast ∈ Q_fast, ∀ Q_classic ∈ Q_classic: Q_fast ∩ Q_classic ≠ ∅
```

对于 n 个 acceptor，如果 fast quorum size = f，classic quorum size = c，则要求 `f + c > n`。在最常见的配置中（c = ⌊n/2⌋ + 1），这意味着 f ≥ ⌈n/2⌉ + 1，即 fast quorum 需要 ~3/4 的节点。

| n | Classic Quorum (c) | Fast Quorum (f) 最小 | 占比 |
|---|-------------------|---------------------|------|
| 3 | 2 | 2 | 66.7% |
| 5 | 3 | 3 | 60.0% |
| 7 | 4 | 4 | 57.1% |
| 9 | 5 | 5 | 55.6% |

### Epochs by Recovery 的简化

Epochs by Recovery **不需要** fast quorum 和 classic quorum 之间的额外 intersection 要求。原因详见对比图：

![[diagram/epochs-recovery-vs-fast-paxos.svg]]

### 完整对比表

| 维度 | Fast Paxos | Epochs by Recovery |
|------|-----------|-------------------|
| **去中心化程度** | 中（任意 proposer 可 fast path，但有 quorum 限制） | 高（proposer 可自由使用 epoch） |
| **Quorum 要求** | f + c > n（通常 ~3/4） | 无额外要求，用 standard quorum |
| **乐观路径** | Fast path（跳过 phase-1） | 多 proposer 同 epoch 直接 phase-2 |
| **冲突处理** | 回退到 slow path（classic Paxos） | Recovery（分配新 epoch 重走完整 round） |
| **Epoch 约束** | 全局唯一 | 不要求唯一（Property 17 替代） |
| **Value 冲突** | 必须 intersect（safety 由 quorum 保证） | 同一 epoch 不同 value → recovery 解决 |
| **论文发表** | Lamport, 2006 | Howard, 2019 |

## 与 Raft Leader Election 的对比思考

Epochs by Recovery 的 "多 proposer 共享 epoch" 思想与 Raft 的 Term-based Leader Election 形成了有趣的对比：

### 相似之处

| 概念 | Raft | Epochs by Recovery |
|------|------|-------------------|
| 逻辑时钟 | Term（全局递增） | Epoch（不要求严格递增） |
| 冲突处理 | 更高 Term 胜出 | 同 epoch → 同 value 才能胜出 |
| 乐观路径 | Leader 存在 → 一轮 AppendEntries | 多 proposer 同 value → 一轮 Phase-2 |

### 根本差异

| 维度 | Raft | Epochs by Recovery |
|------|------|-------------------|
| **Leader 模型** | 强 Leader，日志单向流动 | 去中心化，多 proposer |
| **Epoch 角色** | Term 必须全局唯一（Leader 独占） | Epoch 可被多个 proposer 共享 |
| **冲突性质** | Term 冲突 = Leader 冲突 → 新选举 | Epoch 冲突 = value 冲突 → recovery |
| **瓶颈** | Leader 是单点瓶颈 | 无单点瓶颈，但 recovery 路径有额外延迟 |

### 一个有趣的假设

如果将 Epochs by Recovery 的 Property 17 引入 Raft 的 Term 机制：

- Raft 的 Leader 在某个 Term 内是唯一的（因为 Term + 多数派投票确保）
- 如果允许多个 Leader 在同一个 Term 内竞争，但要求它们 **propose 相同的 log entries**（Property 17 的类比），会发生什么？

→ 这实际上会退化为：要么所有 Leader 的 log 一致（无冲突，类似 chain replication），要么不一致时需要额外的 recovery 机制（类似 Raft 的 Leader Election 重新收敛）。Raft 选择强 Leader 模型避免了这种复杂性，但牺牲了去中心化写入的潜力。

> **工程判断**：Raft 的"简单强 Leader"和 Howard 的"去中心化 epochs"代表了共识设计的两种极端哲学——前者的简单性是生产系统中更重要的需求，后者的灵活性在特定场景（如 Geo-distributed、P2P）有独特价值。

## 总结

Howard 的 Ch 7 完成了她 thesis 的最后一层泛化：**Epoch Allocation 不要求全局唯一**。通过 Property 17 约束同一 epoch 内的 value 一致性，Epochs by Recovery 实现了：

1. **Multi-proposer 去中心化**：无需固定 Leader，任意 proposer 可以并发决策
2. **比 Fast Paxos 更宽松**：不要求 fast/classic quorum 相交，quorum 配置更灵活
3. **自适应混合**：Multi-path Paxos 根据系统状态选择最优路径（Allocator / Value Mapping / Recovery / Classic）

这是 Howard 广义共识框架中最具**前瞻性**的一层——它挑战了 Paxos 自 Lamport 近 30 年来 "epoch 必须唯一" 的基础假设，为共识算法的去中心化演进提供了新的理论基础。

## 待深挖问题

- [ ] Epochs by Recovery 的工程可行性：Property 17 在真实异步网络下的实现复杂度（acceptor 需要跟踪同一 epoch 内的所有 value 提案）
- [ ] 与传统 Leader-based 共识（Raft/Multi-Paxos）的延迟 benchmark 对比（低冲突 vs 高冲突负载）
- [ ] Epochs by Value Mapping 的 hash 碰撞概率形式分析及缓解策略
- [ ] Multi-path Paxos 的自适应策略在动态负载下的稳定性分析（路径切换抖动问题）
- [ ] Epochs by Recovery 在 geo-distributed 共识（WPaxos/DPaxos）中的适用性
- [ ] 与 BFT 共识中 epoch/round 机制的关系：能否将 Property 17 的思想扩展到 Byzantine 模型？
- [ ] Formal verification（TLA+）：Epochs by Recovery 的完整规约和模型检查

---

*Worker rd-task 产出，基于 Howard (2019) Ch 7 精读分析。相关子卡片：[[共识算法族系-从Paxos到广义解]]、[[Paxos-Quorum-Intersection-Revised]]、[[Paxos-Value-Selection-Revised]]*
