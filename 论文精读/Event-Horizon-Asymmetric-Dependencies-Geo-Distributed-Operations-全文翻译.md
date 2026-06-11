# Event Horizon：面向快速地理分布式操作的非对称依赖

> **原文标题**：Event Horizon: Asymmetric Dependencies for Fast Geo-Distributed Operations  
> **作者**：Jonathan Arns (KTH Royal Institute of Technology), Harald Ng (KTH Royal Institute of Technology), Kyriakos Psarakis* (Ververica GmbH / TU Delft), Asterios Katsifodimos (Delft University of Technology), Paris Carbone (KTH Royal Institute of Technology)  
> **会议**：CIDR 2026 (16th Annual Conference on Innovative Data Systems Research), January 18-21, Chaminade, USA  
> **许可**：CC-BY 4.0  
> **注**：\* 表示该工作在代尔夫特理工大学（Delft University of Technology）期间完成

---

## 摘要（ABSTRACT）

低延迟地理分布式应用目前面临跨站点协调（coordination）以确保状态一致性的障碍。现有的混合一致性模型（mixed-consistency models）利用给定应用中强一致性操作和弱一致性操作的共存，尽可能避免协调。然而，现有方法相对悲观，执行的协调超过了必要的程度。

本文引入**半线性化（Semi-Linearizability，SL）**：一种一致性模型，仅在严格必要时才以保证线性化（linearizability）的方式执行应用操作，从而避免过度协调。具体而言，我们提出了新颖的操作语义，能够编码应用操作之间的排序关系，并将其映射到协调原语。我们提出的语义可用于推理不同操作之间潜在的、非对称的依赖关系，并优化它们的执行。我们展示了 SL 如何支持一类新的安全、无协调操作——这在以往的模型中本需以全局严格顺序执行——同时在不违反应用不变量的前提下提供显著的性能增益。为展示 SL 的优势，我们实现了 **DeMon**，一个在广泛使用的 RUBiS 基准测试中，相比最先进系统，将最常见操作的延迟降低了**四个数量级**的系统。

![图1：桥接一致性极端。不同于线性化（Linearizability，左）和强最终一致性（Strong Eventual Consistency，中），半线性化（Semi-Linearizability，右）提供了一种混合方法，允许并发执行，直到一个关键操作形成**事件视界（event horizon）**，仅在必要时将发散的历史折叠为统一状态。](图1描述)

---

## 1. 引言（INTRODUCTION）

地理复制应用，如扩展现实（XR）和沉浸式游戏 [1, 2]，正迅速演进以支持越来越交互式的工作负载，这些负载同时要求低延迟以实现响应性，以及强一致性以保证关键共享状态（例如资产所有权）[3]。为此类应用实现低延迟仍然是一项根本性挑战。

一方面，严格可串行化的分布式数据库如 Spanner [4] 构成了根本性的延迟障碍，因为它们通过协调强制实现操作的全局全序（total ordering）：副本（replica）必须首先通过网络通信就应用状态应如何修改达成一致（使用 Paxos [5] 和 2PC [6] 等协议）。另一方面，更弱的一致性模型（例如 CALM [7] 中的单调操作或 CRDT [8]）避免了协调，但在面对并发时无法支持常见的应用不变量，如唯一性或稳定的决策结果。

强一致性和弱一致性模型（如图 1 所示）都过于极端，未能认识到在单个应用内部，严格的线性化通常仅对特定的状态转换是必需的，而其他操作可以安全地容忍暂时的发散。这两极之间的张力反而驱动了各种努力，通过基于操作选择性地应用这两种模型之一来保持应用不变量。不变量汇合（Invariant confluence）[9] 形式化地识别了哪些操作需要协调来保持不变量，哪些操作可以安全地避免协调。混合一致性模型允许应用定义哪些操作需要协调，并以不同的方式处理它们。例如，RedBlue 一致性 [10] 将非交换（red）操作和可交换（blue）操作分开，使得只有 red 操作被全局全序化。类似地，PoR [11] 和 ECROs [12] 采用基于冲突的推理来确定何时严格需要协调。

虽然这些混合方法成功地打破了强一致性与协调避免之间的二分法，但它们受到"冲突"二元视角的限制。通过将操作分类为要么需要完全协调，要么完全不需要，它们未能捕捉到介于这些极端之间的工作负载语义的细微差别。至关重要的是，它们假设冲突关系是**对称的**，忽略了许多真实世界应用语义是**非对称的**这一事实——仅在某个方向上需要排序。因此，这些模型可能遭受**过度协调**的困扰。

要理解这种固有的非对称性，请考虑图 2 中分布式拍卖 [13] 的经典示例。这涉及两个操作：`new_bid` 插入一个出价条目，而 `close_auction` 结束拍卖并确定中标者。本质上，`new_bid` 操作彼此可交换，但必须被随后的 `close_auction` 观察到。现有的模型（如 I-Confluence、RedBlue 和 PoR）将这种依赖关系处理为对称的，要求操作之间要么是全局全序（↔），要么是无序（↔）。强制全局全序需要过多的协调来串行化所有的 `new_bid` 和 `close_auction` 操作，而无序则存在不变量违反的风险——在 `close_auction` 时刻中标的出价可能被遗漏，导致拍卖授给了另一个出价者。

本文的核心思想是利用**方向性依赖**（directional dependencies）来捕获不变量。具体而言，我们观察到 `new_bid` 操作最终必须被纳入拍卖或被拒绝，但并不立即对拍卖关闭施加秩序：`new_bid → close_auction`。这意味着出价操作可以并发执行而无需任何协调。然而，`close_auction` 必须对前置出价集合施加秩序（即，在每个副本上观察到相同的出价集合），以一致地选出相同的胜者：`close_auction → new_bid`。因此，只有 `close_auction` 需要就与出价的关系进行协调。拍卖关闭后，出价可以被忽略或拒绝而不违反正确性。在本文中，我们扩展这一观察，展示如何用方向性依赖更精确地捕捉应用意图，即 `close_auction` 基于 `new_bid` 的因果历史确定结果，但反之不然。这种非对称性支持更细粒度的语义、新的一致性模型以及减少协调的系统。

总之，我们主张建立更丰富的操作依赖语义，以使混合一致性模型能够有效利用隐式协调。我们的关键贡献如下：

- 我们**形式化了非对称操作依赖**（§2），以更精确地表达应用不变量，超越二元的冲突视角来捕捉方向性的排序需求。
- 我们**引入半线性化**（Semi-Linearizability，§3），一种新的混合一致性模型（如图 1 所示）。该模型允许放松的依赖关系保持可交换，直到一个更强的操作形成"**事件视界**"（event horizon）：一条将这些操作折叠为全局一致顺序的边界，仅在严格必要时强制执行同步。
- 我们**提出 DeMon**（§4），一个运行时执行框架，通过使用袋子（bags）在全局日志中提交依赖关系来实现该模型。在我们的评估（§5）中，我们展示了 DeMon 显著减少了协调开销，同时保持了正确性。
- 最后，我们**讨论了影响**（§6）以及将此愿景进一步演进为具有隐式协调的大规模系统的挑战（§7）。

> **事件视界的隐喻**：在天体物理学中，黑洞的事件视界标志着一个边界，超过此边界后，所有事件——包括物质、辐射、光和信息的运动——都不再可能从向内的路径中发散。无论到达该边界之前的轨迹多么混乱，跨越它的每一事物都被不可逆转地推向奇点，所有可能的未来路径在此处坍塌。类似地，分布式应用产生大量并发事件，其顺序通常不受约束，但某些操作最终必须跨越一条共识边界，即**事件视界**，在此处它们的结果及其因果依赖关系坍塌为固定的、持久的状态。在半线性化中，可交换操作自由流动，直到一个相对更强的操作"将它们拉入"不可变的顺序中。

---

## 2. 排序语义（ORDERING SEMANTICS）

在过去十年中，数据库研究越来越关注将协调与**应用级语义**对齐，而非强制实施统一的、系统级别的保证。ACID 数据库中一个众所周知的例子是不变量汇合 [9]，它通过分析用户定义的应用不变量得以保持的条件，来推理无需协调的安全执行。同样的视角影响了一系列利用读写集、可交换性和操作依赖关系来最小化同步开销的系统 [10–12, 14–17]。这些方法假设操作之间存在**对称关系**，要么需要全局全序，要么假定完全独立。在实践中，许多应用涉及**方向性依赖**——一个操作必须以正确顺序观察到另一个操作，但反之不然。例如，拍卖必须在关闭拍卖之前观察到已提交的出价（称为 happened-before 关系 [18]）。同时，当用户竞拍时，应用开发者可能不要求出价必须在拍卖关闭之前提交。这是因为用户稍后可以被通知其出价是否未及时提交。

### 2.1 非对称操作依赖

让我们考虑一个更通用的操作依赖模型，即有向图 `G = (V, E)`，其中每个顶点 `v ∈ V` 代表一个操作，每条边 `(v → v') ∈ E` 代表两个操作 `v` 和 `v'` 之间的排序不变量。为了说明图 2 中描述的不同依赖类型，我们采用 RUBiS 应用 [13] 中操作的一个子集，该应用被用于对混合一致性模型进行基准测试 [10–13]。我们再次使用 `new_bid` 和 `close_auction`。当拍卖关闭时，一个常见的不变量是拍卖的胜者（由最高出价确定）在 `close_auction` 执行后不能改变。现有工作简单地将 `new_bid` 和 `close_auction` 标记为强操作，必须严格排序以确保在并发执行期间拍卖结果不会改变 [10, 11, 14–17, 19, 20]。相反，我们现在考虑这两个操作之间的四种相互依赖类型，并使用图 2 中的示例来讨论这些依赖关系。

1. **严格有序依赖（Strictly Ordered Dependency）[V ↔ V']**：要求线性化实时顺序的操作之间的一种对称依赖。即，如果 `v1 ↔ v2`，则期望在任何有效的执行调度中，`v1` 和 `v2` 的所有调用必须彼此全局全序化。

   在图 2 的示例中，`close_auction` 操作之间存在严格有序依赖，即它们必须彼此全局全序化，因为并发的 `close_auction` 操作可能会为同一拍卖选择不同的胜者。严格有序依赖已通过强协调机制（如原子寄存器和共识 [5, 21]）得到支持。在现有混合一致性模型中，这些依赖关系可以通过声明跨操作冲突（PoR [11] 和 ECROs [12]）或强到强的依赖关系（RedBlue [10]）来捕获。

2. **可交换依赖（Commutative Dependency）[V ↔ V']**：一种对称依赖，要求两个操作完全可交换，使得它们不需要排序。

   在我们的示例中，`new_bid` 操作彼此可交换。因此，不需要对 `new_bid` 操作相对于其他 `new_bid` 操作进行排序。虽然纯可交换操作很容易支持，但在（强）最终一致性 [8, 22–24]、CRDT [25] 和 CALM [26] 等主题下已有活跃的研究。这些工作线利用了操作之间更弱的属性（如更新的单调性）来提供可交换性和最终收敛。现有的以冲突为中心的混合一致性模型可以在没有冲突的情况下捕获可交换依赖（图 2 中的 PoR [11] 和 ECROs [12]）。

3. **有序依赖（Ordered Dependency）[V → V']**：一种非对称依赖，当排序不变量需要相对于其中一个操作严格保持时产生。给定 `v1 → v2`，如果 `v1` 的某个操作在一个服务器上读取了 `v2` 的某个操作，那么它必须在所有服务器上都这样做。我们说 `a` 读取了 `b`，如果 `b` 写了一个值，随后被 `a` 读取。

   理解有序依赖的一种直观方式是 `close_auction` 和 `new_bid` 之间的关系。关闭拍卖意味着基于已执行的出价集合确定胜者。拍卖胜者不能改变，并且必须在所有副本上相同。关键在于，当 `close_auction` 在远程副本上执行时，它读取的 `new_bid` 集合必须与在发起副本上读取的集合相同。据我们所知，现有的共识模型尚未考虑这种依赖类型，系统退而将其作为对称的严格有序依赖来处理。

4. **最终有序依赖（Eventually Ordered Dependency）[V → V']**：一种非对称依赖，要求两个操作最终有序。给定 `v1 → v2`，`v1` 的每次调用最终必须在所有服务器上读取相同集合的 `v2` 调用。为实现这一点，允许对 `v1` 的调用进行重排序。

   在我们的示例中，与 `close_auction` 操作不同，`new_bid` 允许被应用标记为无效，如果相应的拍卖在另一个副本上被并发关闭。这种情况发生在 `new_bid` 未在 `close_auction` 操作的发起副本上被应用时。该 `new_bid` 在所有副本上被重排序到 `close_auction` 之后，使其无效。最终有序依赖已在 ECROs [12] 的背景下被探索过，但该模型只能表达对称的最终有序依赖。ECROs 允许违反有序不变量安全性，这限制了其在需要正确性保障时的适用性。

---

## 3. 半线性化模型（A MODEL OF SEMI-LINEARIZABILITY）

基于我们从非对称操作依赖中获得的洞察，我们定义了一个实用的共识模型，能够准确捕获这些依赖关系。传统上，将操作二分为强操作和弱操作只能捕获对称依赖。我们将其扩展为也能表达两种类型的非对称依赖。具体而言：强操作之间的**严格有序**（s ↔ s'）；弱操作之间的**可交换**（w ↔ w'）；从强到弱的**有序**（s → w）；以及从弱到强的**最终有序**（s ← w）。这样，弱操作和强操作之间的交互可以表达有序依赖和最终有序依赖的非对称性。

**系统模型**：副本是状态机，在接收到操作 `v` 时，可以（a）直接将 `v` 应用到其状态，或（b）撤销前 `x` 个操作，应用 `v`，然后重新应用那 `x` 个操作。在这种情况下，`v` 现在被视为在这 `x` 个操作之前被应用。这种对 `x` 个操作的重排序是实现最终有序依赖（v → v'）所必需的。

**半线性化顺序**：如图 3 所示，半线性化顺序表示一个全局全序日志，由严格有序的强操作和介于其间的可交换（w ↔ w'）弱操作的袋子（bags）组成。我们将半线性化顺序定义为所有强操作和所有弱操作的并集 `U = S ∪ W` 上的偏序 `O = (U, ≺o)`。

- 为表示严格有序依赖（s ↔ s'），`≺o` 根据所有强操作的线性化实时顺序对其排序。
- 为表示有序依赖（s → w），`≺o` 将每个弱操作 `w` 排序到所有发生于 `w` 之前的强操作之后的某个袋子中。因此，相对于所有强操作，`w` 被排序在该袋子的位置上。
- 由于基于 CRDT 的可交换操作通常需要因果性 [8]，我们还定义弱操作彼此之间按因果顺序排列。

**半线性化**：给定一个半线性化顺序 `O = (U, ≺o)`，一个复制系统满足半线性化，当且仅当对于每个副本 `p`，以下两个条件成立：

1. 在任何时刻，`p` 已应用的所有操作都按照它们在 `O` 中的顺序被应用，即 `p` 遵守由应用不变量所设定的依赖关系所强制执行的顺序。
2. 在应用任何强操作 `s` 之前，`p` 已预先应用了所有在 `O` 中被排序到 `s` 之前的操作。

这两个条件共同保证了：i) 强操作是严格有序的（s ↔ s'）；ii) 强操作永远不会被重排序，始终在所有先前的弱操作之后按精确顺序排列（s → w）；以及 iii) 弱操作相对于强操作是最终有序的（w → s）。

因此，回到 `new_bid` 和 `close_auction` 操作，我们必须将 `close_auction` 操作标记为强操作。与现有混合一致性模型不同，我们可以安全地将 `new_bid` 操作标记为弱操作，并允许其无协调执行。

该模型为强操作读取弱写入保证了顺序一致性（Sequential Consistency）。弱操作在其初始执行时也以顺序一致性读取强写入。然而，如图 3 所示，在应用强操作（例如通过共识）后，弱操作最终可能被重排序，从而以线性化一致性读取该强操作（SEQ→LIN）。

**表 1**：不同混合一致性模型下强操作（S）和弱操作（W）的一致性级别。LIN：线性化 [27]；SEQ：顺序一致性 [28]；CC：因果一致性 [29]。\*PoR 和 Well-Coordination 对称地放松了非冲突操作对的这些一致性级别。

| 模型 | S ↔ S | S ↔ W | W ↔ W |
|------|-------|-------|-------|
| RedBlue [10] | LIN | CC | CC |
| PoR [11] | LIN\* | CC | CC |
| Well-Coordination [16] | LIN\* | CC\* | CC\* |
| OAC [14] | LIN | LIN | CC |
| **Semi-Linearizability** | LIN | SEQ→LIN | CC |

表 1 显示 SL 是唯一根据排序限制统一了三个不同一致性级别的共识模型。现有的 RedBlue [10]、PoR [11]、Well-Coordination [16] 和 OAC [14] 模型都归结为线性化和因果一致性之间的二元划分，不存在中间地带。虽然 Explicit Consistency（纯粹基于不变量保持定义）允许通过重排序操作来减少协调的概念，但没有任何实现它的系统支持 SL 所捕获的非对称操作依赖 [12, 30, 31]。

---

## 4. DEMON

为了展示半线性化的潜力，我们实现了 **DeMon**，一个地理复制的内存存储系统。DeMon 的目标是通过利用弱操作和相对较强操作之间的非对称依赖来最小化协调。为此，DeMon 使用共识协议复制强操作，使用可靠因果广播复制弱操作。这使得 DeMon 能够实现强操作所需的严格排序，同时使弱操作能够像 CRDT 一样在本地执行而无需协调。半线性化顺序进一步要求强操作和弱操作之间的排序：任何弱操作 `w` 必须排序在所有发生于 `w` 之前的强操作之后（§3）。DeMon 通过**水位线（watermarks）**来保证这一点，水位线充当同步屏障，确保弱操作保持与强操作正确的因果依赖关系。

### 4.1 操作流程

DeMon 使用共识协议（OmniPaxos [32]）复制一个定义强操作严格顺序的日志。弱操作通过可靠因果广播进行传播，以保持基于 CRDT 的操作所需的因果排序。此外，每个副本维护自己的弱操作计数器。这些计数器用于形成向量时钟，作为水位线。我们使用图 4 来解释 DeMon 中水位线和强/弱操作的不同路径。

**弱操作**的处理如下：
1. 从客户端接收弱操作的副本立即执行它。
2. 一旦执行，响应即发送给客户端，类似于基于操作的 CRDT [8]。
3. 然后，该操作通过因果广播异步复制。
4. 因果广播按因果顺序传递消息。
5. 在远程副本上接收后，弱操作被执行。

为了跟踪复制进度，副本还定期广播它们已接收到的最新弱操作的 ID。基于此，每个副本记录哪些弱操作已被复制到副本的多数法定人数（majority quorum）。

**强操作**的处理如下：
1. 在接收到强操作时，副本附加一个向量时钟，总结其对每个副本已被法定人数看到的最新弱操作的了解。该向量时钟表示必须在强操作之前排序的弱操作的**低水位线**。
2. 该操作连同水位线一起被提议到共识协议中。共识条目需要同步通信来决定。
3. 在共识日志中接收到已决定的强操作及其水位线后，每个副本通过合并新水位线与先前的水位线来计算最新水位线。最新水位线定义了所有新操作所应用的**稳定状态**。如果副本观察到最新水位线未包含它已执行的某些弱操作，则这些操作需要重排序并在稳定状态之上执行。我们接下来用一个示例来描述这种场景。
4. 最终，执行后向客户端发送响应。

**示例**：考虑三个副本 A、B 和 C 管理一个分布式拍卖。A 首先接受 `new_bid(100)`，而 B 并发接受 `new_bid(200)`；两者都在本地执行并通过因果广播异步传输到其他副本。最终，这些更新传播到所有副本，它们收敛到最高出价 200。现在，假设 C 发出 `new_bid(300)`。然而，在操作到达任何其他副本之前，B 发出 `close_auction`。B 随操作附加水位线 `[a 1, b 1, c 0]` 到共识条目中，该水位线排除了来自 C 的未看到出价。当 `close_auction` 通过共识被决定时，它强制实施该水位线指定的状态，以 `new_bid(200)` 作为胜者敲定拍卖。我们考虑 `new_bid(300)` 在副本上的两种可能情况：如果副本在 `close_auction` 之前收到 `new_bid(300)`，它已被应用到本地状态，需要回滚（见 §4.2）。相反，如果 `new_bid(300)` 在关闭之后到达，则简单地应用于已敲定状态之上。在这两种情况下，`new_bid(300)` 实际上被排序在 `close_auction` 之后，使其无效。

### 4.2 操作重排序

从语义上讲，当强操作 `s` 被执行时，重排序一个已经应用到本地状态的弱操作 `w` 等价于：回滚 `w`，将 `s` 应用到状态，然后再次应用 `w`。为了避免对每个操作实现逆操作的需要，DeMon 保持两个版本的状态。**稳定状态**包含所有先前的强操作及其间的弱操作；**不稳定状态**额外应用了该副本已接收到的所有最近的弱操作。弱操作最初仅应用于不稳定状态。然而，当执行强操作 `s` 时，首先将 `s` 的水位线中任何新的稳定弱操作应用到稳定状态。副本可能需要等待，如果它尚未接收到这些新的弱操作。然后，将 `s` 应用于稳定状态。最后：i) 通过生成 `s` 所做更改的增量（delta）并将该增量应用于不稳定状态来更新不稳定状态；ii) 所有被该增量覆盖的近期弱操作再次被应用于不稳定状态。

---

## 5. 评估（EVALUATION）

我们在地理复制环境中评估 DeMon，使用一个非负计数器微基准测试和 RUBiS [13] 基准测试。虽然主要目标是低延迟，我们还评估了吞吐量，并特别比较了协议之间的协调开销。

**硬件**：我们使用跨越五个区域的设置：US-East、芬兰、巴西、US-West 和新加坡。我们测量了它们之间的平均往返延迟，范围从 73.7ms（US-East ↔ US-West）到 387.6ms（巴西 ↔ 新加坡）。对于使用主副本（primary replica）的协议，主区域设置为 US-East。在每个区域中，一个 DeMon 副本部署在 Google Compute Engine 的 n2-standard-4 实例上（4 vCPU，16GB 内存）。客户端作为轻量级任务运行在同一实例上，以消除客户端与副本之间的网络延迟。

**基线**：在性能评估中，我们将 DeMon 与五个参考协议进行对比，所有这些协议均在同一个 Rust 代码库中（与 DeMon 相同）实现（代码见 https://github.com/JonathanArns/demon）。

- **Gemini** 是原始 Gemini 协议的 RedBlue 一致性 [10] 的实现。注意 Gemini 不保证容错写入。
- **Gemini+** 是 RedBlue 一致性的容错实现，使用 OmniPaxos [32] 建立强操作之间的全局全序，并使用与 DeMon 类似的确定性水位线策略建立与弱操作的偏序。
- **UniStore** 通过类似于 UniStore [20] 的乐观提交协议实现部分顺序限制（PoR）一致性。
- **OmniPaxos** [32] 是一个共识协议，作为实现强一致性所需性能的评估基线。它遵循典型的 Paxos 模式，有一个需要与多数法定人数协调来提交操作的主节点（leader）。
- **No Guarantees** 代表无协调的理想性能。类似于基于操作的 CRDT，操作通过因果广播传播到其他副本，并在本地执行后立即完成。如下所述，对于具有非交换操作依赖的工作负载，它是不安全的。

### RUBiS 基准测试

我们使用标准 RUBiS 基准测试，包含五种操作：`BuyNow` 和 `RegisterUser` 是具有严格有序自依赖的强操作，而其他操作（`Bid`、`OpenAuction` 和 `Sell`）是弱操作。与相关工作一致，我们扩展了 RUBiS 以包含 `CloseAuction` 操作 [11, 12, 20]，该操作对 `Bid` 具有非对称依赖（图 2）。基准测试基于竞拍混合的更新部分生成操作分布。关键的是，`Bid` 操作——在半线性化下只能是弱操作——占据了更新操作的 60%。我们专注于更新操作，因为只读操作在所有协议中都可以是本地且无等待的。

**图 5** 展示了各协议 RUBiS 工作负载的累积延迟分布，以及按操作类型划分的延迟情况。尤其在延迟分布中，DeMon 将频繁的 `Bid` 操作作为弱操作的优势非常明显——为超过 75% 的工作负载提供亚毫秒级延迟。对于其他 RUBiS 操作，DeMon 虽未提供如此巨大的增益，但在强操作 `CloseAuction`、`BuyNow` 和 `RegisterUser` 上的延迟与 OmniPaxos 相当，中位延迟为 245ms。该延迟源于将强操作转发到主节点并通过共识决定，共需要两轮消息往返。相比之下，其他使用主写入节点的混合一致性协议在这些操作上至少多一轮额外的延迟往返，因为它们必须在将强操作转发到主节点之前等待新的弱操作被法定人数复制 [20]——这体现为 Gemini+ 和 UniStore 中 `CloseAuction` 的中位延迟分别为 371ms 和 391ms。对于可交换的 `OpenAuction` 和 `Sell` 操作，除 OmniPaxos 外所有协议即使在 99 分位也能提供亚毫秒级延迟。

**图 6（左）**显示 DeMon 的最大吞吐量略微高于所有其他容错协议。值得注意的是，使用共识（Gemini+、UniStore、DeMon）进行复制的协议在吞吐量上受限于共识本身，因为它们受限于单个主写入节点。当主节点过载时，吞吐量急剧下降。由于 DeMon 能够安全地对更多的工作负载（`Bid` 操作）使用因果广播，因此即使有重排序操作带来的额外计算开销，也实现了更高的吞吐量。Gemini 通过省略容错的协调原语实现了比 DeMon 更高的最大吞吐量；然而，这导致强操作的中位延迟高了 3 倍（737ms vs 245ms）。Gemini 的高延迟源于副本等待互斥写访问以调用强操作，而不是将强操作直接发送到始终可以写入的主节点。

### 协调开销

为进一步评估协调强操作对性能的影响，我们使用一个复制非负计数器的微基准测试。该数据类型有两个操作：`add` 和 `subtract`，不变量是计数器永远不能小于零。`subtract` 是不安全的，并且具有对自身的严格有序依赖。我们比较中的所有混合一致性模型通过将 `subtract` 协调为强操作，同时将 `add` 视为可本地执行的弱操作，来保证安全性。这使我们能够通过调整 `subtract` 的比例来控制协调量。

如图 6（右）所示，DeMon 展现了"**按需付费**"（pay-as-you-go）的性能特征：其平均延迟与强操作的比例成比例增长。相比之下，基线协议的表现不同：无论操作混合比例如何，OmniPaxos 都产生固定的协调成本，涉及将请求转发到 leader 后进行一次法定人数往返，导致恒定的 245ms 延迟。在另一个极端，No Guarantees 作为下界，提供亚毫秒级延迟。相反，其他混合协议在强操作比例达到 50% 或之前就超过了 OmniPaxos 的延迟。这是因为 RedBlue 和 PoR 一致性要求强操作等待所有因果相关的操作变得持久化，导致额外一轮同步通信。对于 DeMon，强操作的唯一协调开销在于其底层的共识协议。

---

## 6. 讨论（DISCUSSION）

分析非对称操作依赖为新的共识模型提供了机遇——如本文提出的半线性化——能够在不牺牲应用不变量的前提下大幅减少协调。由此带来的延迟降低可以使地理分布式规模下的交互式应用成为可能。我们展示了这一可能性并提出了进一步的研究方向。

**依赖类型**：我们对操作依赖的分类是强大但开放的。进一步的扩展可以基于可能展现不同依赖类型的不同工作负载。识别这些依赖关系对于在混合一致性模型中实现进一步优化至关重要。

**重排序语义**：在 SL 下，重排序弱操作可能导致意外行为，例如拍卖中的出价被撤销。只有当一个操作被强操作提交到事件视界之后，系统才能保证稳定性。根据应用的不同，弱操作的快速提交状态与稳定提交状态之间的差异应通过用户界面暴露，以防止意外。类似于 CRDT 算法之间的语义权衡（例如 OR-set 与 2P-set [25]），重排序也可能存在多种语义，具有不同的权衡可供选择。设想一个可以通过强操作重置的复制集合，并发的插入操作在重置之后是否应生效取决于应用。

**应用分析**：在单个应用层面，识别操作之间的依赖关系是一项复杂的任务，对开发者可能具有挑战性。不仅需要理解所有操作之间可能的交互，还需要理解应用的**不变量集合**。在拍卖示例中，很明显，一旦确定拍卖胜者，它就永远不应改变，但在此之后拒绝出价是可以接受的不便。如果我们认为这种情况不可接受，就不会存在非对称依赖，也没有避免协调的潜力。静态分析工具可以自动化此过程的困难部分（例如，二元冲突识别 [19]）并帮助识别这些权衡，但最终可能仍需要人工输入来决定它们。

**去中心化系统**：除了交互式应用之外，SL 可能是迈向高效拜占庭容错（BFT）系统的关键一步，通过最小化慢速 BFT 共识 [33] 的使用，转而采用快速的 BFT CRDT [34]。

---

## 7. 未来展望（A FUTURE OUTLOOK）

半线性化和非对称依赖的形式化提供的不仅仅是一个一致性模型；它为组合混合一致性分布式应用提供了一种**中间表示（Intermediate Representation，IR）**的基础。拥有应用的详细非对称依赖图表示，使得分布式代码生成成为一个近乎确定性的过程。然而，一个自然的问题是："我们如何达到那里？"如图 7 所示，我们设想了在用户意图（隐式或显式）、建模和代码生成之间架起桥梁的多种途径。选择正确的途径（即自然语言、形式化、DSL 或源代码）取决于应用用户或创建者的领域专业水平。实现每条途径都面临着不同的相关研究挑战，我们详述如下。

**面向非专家的自然语言规约**：我们当前正目睹一场运动，旨在赋予非专家使用自然语言提示应用和系统的能力 [35, 36]。从自由叙述中进行非正式的需求收集往往缺乏指定正确分布式安全级别所需的精确性。此外，虽然 LLM 可以使用自然语言生成代码，但它们常常无法在不产生幻觉的情况下保证生成的逻辑遵守严格的安全不变量 [37]。这里的主要研究挑战是验证从"氛围编程"（vibe coding）或 LLM-用户交互中提取的一组非对称依赖是否足够完整，以构建足够安全的系统而不诉诸严格的线性化。这需要一个迭代过程，AI 识别模糊性——例如特别询问拍卖关闭中的边界情况以及操作的相对分类法——引导用户走向一个既必要又充分的完整符号化规约。

**面向领域专家的模型翻译**：在数据库领域之外，有大量的领域模型被用于捕获依赖关系。例如，Unity 和 Unreal Engine 等游戏引擎——它们在组合 XR 应用时变得普遍——已经具备捕获共享虚拟对象之间微妙用户定义交互的模型。游戏引擎基于这些模型生成 netcode，在游戏客户端和服务器之间同步操作和状态 [38, 39]。许多其他模型语义也可以提升为非对称依赖。例如，BPMN 2.0 模型化了业务流程 [40]，其中顺序流规定严格的因果排序，而并行网关意味着可交换性。类似地，在基础设施管理中，Terraform 图 [41] 通过显式的 `depends_on` 属性构造有向无环图（DAG）。未来的研究可以针对这些丰富的语义来源，形式化其静态结构（例如 GraphQL [42] 的父子嵌套字段）与安全并发执行所需的动态约束之间的映射。

**面向专家的规约语言**：分布式系统专家目前依赖复杂的形式化验证语言，如 TLA+ [43]（以及模型检查器如 TLC [44]），它们需要对整个系统状态有全面的"上帝视角"来验证全局正确性。这些工具提供了强大的检查能力，但施加了很高的认知负担，并且往往产生难以修改的不透明规约。我们设想去推导一种更简单、更易用的规约语言，仅关注可见的排序和协调成本。这里的一个关键研究挑战是用它来替代手动协议验证和代码合成。通过指定成本模型和一组本地协调约束，最小成本优化器可以合成一个满足给定约束的协议，有效地在抽象规约、形式化证明和实际优化实现之间架起桥梁。

**面向开发者的验证提升**：开发者目前通过从现有框架和系统中手动注入协调原语来实现分布式逻辑。这种手动方法通常是悲观的，导致过度协调，甚至在遗漏依赖时产生意外异常。为了实现更好的解决方案，我们必须推进静态代码分析技术以支持验证提升（verified lifting），如 Katara [45] 等解决方案所示。在这种情况下，目标是通过分析 DSL 中的读写模式和可交换操作，自动推断依赖图。这将使运行时能够通过将检测到的强依赖映射到共识、将弱依赖映射到因果广播，自动注入必要的协调，将正确性的负担从程序员转移到编译器。新的编程语言和框架如 Hydro [46]、Aqua [47]、Lasp [48]、Styx [49] 和 Portals [50] 等正朝着这一轨迹发展。

---

## 8. 结论（CONCLUSION）

强一致性和弱一致性之间的僵化二分法长期迫使开发者做出妥协：要么承受严格排序协调所需的高延迟，要么将应用逻辑限制为可交换或单调的操作。在本文中，我们展示了操作依赖关系更为微妙：操作常常表现出可以被利用来减少协调的**非对称依赖**。为此，我们引入了**半线性化（Semi-Linearizability，SL）**——一种一致性模型，其中可交换操作可以发散，直到一个相对更强的操作强制执行"**事件视界**"（event horizon）——即协调的边界。这在最小化协调开销的同时，严格保持了应用强制执行的不变量正确性。

非对称性的洞察为构建具有更精确一致性保证的系统提供了基础。通过利用静态分析和 AI 辅助开发等技术来识别这些方向性关系，我们可以超越粗粒度的模型，构建强制实施应用精确约束的系统。这为新一代分布式架构铺平了道路——在用户意图与运行时执行之间的鸿沟由自动化合成弥合，确保系统在构造上正确且在默认情况下高效。

---

## 参考文献（REFERENCES）

[1] M. Xu, W. C. Ng, W. Y. B. Lim, J. Kang, Z. Xiong, D. Niyato, Q. Yang, X. Shen, and C. Miao, "A Full Dive Into Realizing the Edge-Enabled Metaverse: Visions, Enabling Technologies, and Challenges," *IEEE Communications Surveys & Tutorials*, vol. 25, no. 1, pp. 656–700, 2023.

[2] M. Ali, F. Naeem, G. Kaddoum, and E. Hossain, "Metaverse Communications, Networking, Security, and Applications: Research Issues, State-of-the-Art, and Future Directions," *IEEE Communications Surveys & Tutorials*, vol. 26, no. 2, pp. 1238–1278, 2024.

[3] P. Bernstein, S. Bykov, A. Geller, G. Kliot, and J. Thelin, "Orleans: Distributed virtual actors for programmability and scalability," *MSRTR2014*, vol. 41, 2014.

[4] J. C. Corbett, J. Dean, M. Epstein, A. Fikes, C. Frost, J. J. Furman, S. Ghemawat, A. Gubarev, C. Heiser, P. Hochschild, W. Hsieh, S. Kanthak, E. Kogan, H. Li, A. Lloyd, S. Melnik, D. Mwaura, D. Nagle, S. Quinlan, R. Rao, L. Rolig, Y. Saito, M. Szymaniak, C. Taylor, R. Wang, and D. Woodford, "Spanner: Google's Globally Distributed Database," *ACM Transactions on Computer Systems*, vol. 31, pp. 1–22, Aug. 2013.

[5] L. Lamport, "Paxos Made Simple," *ACM SIGACT News (Distributed Computing Column) 32, 4 (Whole Number 121, December 2001)*, pp. 51–58, Dec. 2001.

[6] J. Gray, "Notes on data base operating systems," in *Operating Systems, An Advanced Course*, (Berlin, Heidelberg), p. 393–481, Springer-Verlag, 1978.

[7] J. M. Hellerstein and P. Alvaro, "Keeping CALM: when distributed consistency is easy," *Communications of the ACM*, vol. 63, pp. 72–81, Aug. 2020.

[8] M. Shapiro, N. Preguiça, C. Baquero, and M. Zawirski, "Conflict-Free Replicated Data Types," in *Stabilization, Safety, and Security of Distributed Systems*, Springer, 2011.

[9] P. Bailis, A. Fekete, M. J. Franklin, A. Ghodsi, J. M. Hellerstein, and I. Stoica, "Coordination avoidance in database systems," *Proceedings of the VLDB Endowment*, vol. 8, pp. 185–196, Nov. 2014.

[10] C. Li, D. Porto, A. Clement, J. Gehrke, N. Preguiça, and R. Rodrigues, "Making {Geo-Replicated} Systems Fast as Possible, Consistent when Necessary," pp. 265–278, 2012.

[11] C. Li, N. M. Preguiça, and R. Rodrigues, "Fine-grained consistency for geo-replicated systems," in *Proceedings of the 2018 USENIX Annual Technical Conference*, 2018.

[12] K. De Porre, C. Ferreira, N. Preguiça, and E. Gonzalez Boix, "ECROs: building global scale systems from sequential code," *Proceedings of the ACM on Programming Languages*, vol. 5, pp. 107:1–107:30, Oct. 2021.

[13] E. Cecchet, "RUBiS archive," 2009. Publication Title: OW2 Projects.

[14] X. Zhao and P. Haller, "Observable atomic consistency for CvRDTs," in *Proceedings of the 8th ACM International Workshop on Programming Based on Actors, Agents, and Decentralized Control*, ACM, 2018.

[15] M. Whittaker and J. M. Hellerstein, "Interactive checks for coordination avoidance," *Proceedings of the VLDB Endowment*, 2018.

[16] F. Houshmand and M. Lesani, "Hamsaz: replication coordination analysis and synthesis," *Proc. ACM Program. Lang.*, vol. 3, no. POPL, 2019.

[17] X. Zhao and P. Haller, "Replicated data types that unify eventual consistency and observable atomic consistency," *Journal of Logical and Algebraic Methods in Programming*, vol. 114, p. 100561, Aug. 2020.

[18] L. Lamport, "Time, clocks, and the ordering of events in a distributed system," *Communications of the ACM*, vol. 21, no. 7, pp. 558–565, 1978.

[19] J. Wang, C. Li, K. Ma, J. Huo, F. Yan, X. Feng, and Y. Xu, "AUTOGR: automated geo-replication with fast system performance and preserved application semantics," *Proceedings of the VLDB Endowment*, vol. 14, pp. 1517–1530, May 2021.

[20] M. Bravo, A. Gotsman, B. de Régil, and H. Wei, "UNISTORE: A fault-tolerant marriage of causal and strong consistency," *Proceedings of the 2021 USENIX Annual Technical Conference*, 2021.

[21] D. Ongaro and J. Ousterhout, "In Search of an Understandable Consensus Algorithm," pp. 305–319, 2014.

[22] D. Terry, A. Demers, K. Petersen, M. Spreitzer, M. Theimer, and B. Welch, "Session guarantees for weakly consistent replicated data," in *Proceedings of 3rd International Conference on Parallel and Distributed Information Systems*, pp. 140–149, Sept. 1994.

[23] W. Vogels, "Eventually Consistent: Building reliable distributed systems at a worldwide scale demands trade-offs—between consistency and availability.," *Queue*, vol. 6, pp. 14–19, Oct. 2008.

[24] P. Bailis and A. Ghodsi, "Eventual consistency today: limitations, extensions, and beyond," *Communications of the ACM*, May 2013.

[25] M. Shapiro, N. Preguiça, C. Baquero, and M. Zawirski, "A comprehensive study of Convergent and Commutative Replicated Data Types," 2011.

[26] S. Laddad, C. Power, M. Milano, A. Cheung, N. Crooks, and J. M. Hellerstein, "Keep CALM and CRDT On," *Proceedings of the VLDB Endowment*, vol. 16, pp. 856–863, Dec. 2022.

[27] M. P. Herlihy and J. M. Wing, "Linearizability: a correctness condition for concurrent objects," *ACM Transactions on Programming Languages and Systems*, vol. 12, pp. 463–492, July 1990.

[28] Lamport, "How to Make a Multiprocessor Computer That Correctly Executes Multiprocess Programs," *IEEE Transactions on Computers*, vol. C-28, pp. 690–691, Sept. 1979.

[29] P. Hutto and M. Ahamad, "Slow memory: weakening consistency to enhance concurrency in distributed shared memories," in *10th International Conference on Distributed Computing Systems*, 1990.

[30] V. Balegas, S. Duarte, C. Ferreira, R. Rodrigues, N. Preguiça, M. Najafzadeh, and M. Shapiro, "Putting consistency back into eventual consistency," in *EuroSys*, 2015.

[31] V. Balegas, C. Li, M. Najafzadeh, D. Porto, A. Clement, S. Duarte, C. Ferreira, J. Gehrke, J. Leitao, N. Preguia, R. Rodrigues, M. Shapiro, and V. Vafeiadis, "Geo-Replication: Fast If Possible, Consistent If Necessary," *Bulletin of the IEEE Computer Society Technical Committee on Data Engineering*, 2016.

[32] H. Ng, S. Haridi, and P. Carbone, "Omni-Paxos: Breaking the Barriers of Partial Connectivity," in *Proceedings of the Eighteenth European Conference on Computer Systems*, EuroSys '23, 2023.

[33] G. Zhang, F. Pan, Y. Mao, S. Tijanic, M. Dang'Ana, S. Motepalli, S. Zhang, and H.-A. Jacobsen, "Reaching consensus in the byzantine empire: A comprehensive review of bft consensus algorithms," *ACM Computing Surveys*, vol. 56, no. 5, pp. 1–41, 2024.

[34] M. Kleppmann, "Making crdts byzantine fault tolerant," in *Proceedings of the 9th Workshop on Principles and Practice of Consistency for Distributed Data*, pp. 8–15, 2022.

[35] A. Beheshti, "Natural language-oriented programming (nlop): Towards democratizing software creation," in *2024 IEEE International Conference on Software Services Engineering (SSE)*, pp. 258–267, 2024.

[36] X. Hou, Y. Zhao, Y. Liu, Z. Yang, K. Wang, L. Li, X. Luo, D. Lo, J. Grundy, and H. Wang, "Large language models for software engineering: A systematic literature review," *ACM Trans. Softw. Eng. Methodol.*, vol. 33, Dec. 2024.

[37] Z. Zhang, C. Wang, Y. Wang, E. Shi, Y. Ma, W. Zhong, J. Chen, M. Mao, and Z. Zheng, "Llm hallucinations in practical code generation: Phenomena, mechanism, and mitigation," *Proc. ACM Softw. Eng.*, vol. 2, June 2025.

[38] "Replicating UObjects in Unreal Engine | Unreal Engine 5.7 Documentation | Epic Developer Community — dev.epicgames.com." https://dev.epicgames.com/documentation/en-us/unreal-engine/replicating-uobjects-in-unreal-engine. [Accessed 05-12-2025].

[39] T. Köylüoglu and J. Larsson, "Zero self-view latency: An implementation of conflict-free replicated data types in unity: A benchmark of operation-based crdts," 2025.

[40] T. Allweyer, *BPMN 2.0: introduction to the standard for business process modeling*. BoD–Books on Demand, 2016.

[41] "Terraform | HashiCorp Developer — developer.hashicorp.com." https://developer.hashicorp.com/terraform. [Accessed 05-12-2025].

[42] A. Quiña-Mera, P. Fernandez, J. M. García, and A. Ruiz-Cortés, "Graphql: A systematic mapping study," *ACM computing surveys*, vol. 55, no. 10, pp. 1–35, 2023.

[43] Y. Yu, P. Manolios, and L. Lamport, "Model checking tla+ specifications," in *Advanced research working conference on correct hardware design and verification methods*, pp. 54–66, Springer, 1999.

[44] L. Lamport and Y. Yu, "Tlc–the tla+ model checker," 2001.

[45] S. Laddad, C. Power, M. Milano, A. Cheung, and J. M. Hellerstein, "Katara: Synthesizing crdts with verified lifting," *Proceedings of the ACM on Programming Languages*, vol. 6, no. OOPSLA2, pp. 1349–1377, 2022.

[46] A. Cheung, N. Crooks, J. M. Hellerstein, and M. Milano, "New Directions in Cloud Programming," Jan. 2021.

[47] K. Segeljakt, S. Haridi, and P. Carbone, "Aqualang: A dataflow programming language," in *Proceedings of the 18th ACM International Conference on Distributed and Event-Based Systems*, DEBS '24, (New York, NY, USA), p. 42–53, Association for Computing Machinery, 2024.

[48] C. Meiklejohn and P. Van Roy, "Lasp: A language for distributed, coordination-free programming," in *Proceedings of the 17th International Symposium on Principles and Practice of Declarative Programming*, pp. 184–195, 2015.

[49] K. Psarakis, G. Christodoulou, G. Siachamis, M. Fragkoulis, and A. Katsifodimos, "Styx: Transactional stateful functions on streaming dataflows," *Proc. ACM Manag. Data*, vol. 3, June 2025.

[50] J. Spenger, P. Carbone, and P. Haller, "Portals: An extension of dataflow streaming for stateful serverless," in *Proceedings of the 2022 ACM SIGPLAN International Symposium on New Ideas, New Paradigms, and Reflections on Programming and Software*, Onward! 2022, (New York, NY, USA), p. 153–171, Association for Computing Machinery, 2022.

---

> **翻译说明**：本文基于 CIDR 2026 发表的论文 *Event Horizon: Asymmetric Dependencies for Fast Geo-Distributed Operations* 原文全文翻译。学术术语首次出现时保留英文原文，参考文献条目保留原文不翻译。图表标题已翻译，图表内的英文保留原文描述。
