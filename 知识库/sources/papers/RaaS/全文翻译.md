# 降低存储计算分离数据库系统中的尾延迟

**XI PANG**, Purdue University, USA
**JIANGUO WANG**, Purdue University, USA

存储计算分离数据库（Storage-Disaggregated Database）因其诸多优势已成为云端的标准架构，包括提高资源利用率、减少资源碎片化，以及能够独立弹性地扩缩计算和存储资源，最终实现成本节约。本文聚焦于 OLTP（在线事务处理）数据库。代表性系统包括 Amazon Aurora、Microsoft Socrates 和 Neon。然而，我们发现存储计算分离数据库存在一个显著的局限性——高尾延迟（tail latency）问题。该问题源于这类数据库独特的架构设计，特别是"日志即数据库"（log-as-the-database）的设计原则。在该设计下，当提交事务时，仅将日志通过网络发送至存储引擎以最小化数据移动，而实际的数据页则在存储侧通过日志回放（log replay）来重建。因此，某些页请求可能遇到较长的日志回放链，从而导致高延迟。

本文提出了一种名为 RaaS（Replay-as-a-Service，回放即服务）的新技术，以解决存储计算分离数据库中的高尾延迟问题。RaaS 的核心思想是将日志回放逻辑从存储引擎中解耦，使其成为一个独立的服务。这种方法能够灵活地利用集群中的空闲服务器甚至专用服务器来高效执行日志回放。为实现这一目标，我们引入了一系列技术和优化手段来应对关键的技术挑战。我们在 OpenAurora（一个基于 PostgreSQL 的开源存储计算分离数据库）中实现了 RaaS 技术。在 SysBench 上的实验表明，RaaS 将 P95 尾延迟降低了 40.1%，并将总体吞吐量提升了 75.9%。

**CCS 概念**：• 信息系统 → DBMS 引擎架构；关系型并行和分布式 DBMS。

**关键词**：存储计算分离数据库，云原生数据库，尾延迟

**ACM 引用格式**：
Xi Pang and Jianguo Wang. 2026. Reducing Tail Latency in Storage-Disaggregated Database Systems. *Proc. ACM Manag. Data* 4, 1 (SIGMOD), Article 74 (February 2026), 26 pages. https://doi.org/10.1145/3786688

---

## 1 引言

以 Amazon Aurora [36]、Microsoft Socrates [9]、Google AlloyDB [1]、Huawei Taurus [15] 和 Neon [3] 为代表的存储计算分离数据库已广泛应用于基于云的数据库架构中。通过将计算与存储解耦，这些数据库能够独立弹性地扩缩各个组件以满足不同的工作负载需求。此外，它们还可以通过资源池化提高资源利用率并减少资源碎片化，从而降低成本。因此，存储计算分离数据库已成为客户将数据迁移至云端的首选。例如，Amazon Aurora 已被数以万计的客户使用，成为 AWS 历史上增长最快的服务 [2, 34]。

尽管存储计算分离数据库广受欢迎，但我们观察到其性能并不稳定，面临着显著的尾延迟问题。例如，我们使用 Amazon Aurora（PostgreSQL v16.6）在 db.r6g.large 实例（2 vCPU，16 GB DRAM）上进行了一项实验。我们加载了来自 SysBench 基准测试 [6] 的 10 GB 数据并测量了 Aurora 的性能。具体而言，我们执行了 20 分钟的 SysBench 工作负载，并在图 1 中绘制了查询延迟分布图。结果显示，Aurora 的整体查询延迟较低，平均延迟为 33.2 ms，中位延迟为 26.7 ms。然而，其尾延迟很高——P95 延迟为 69.3 ms，是中位延迟的 2.6 倍；P99 延迟为 153.1 ms，是中位延迟的 5.7 倍。

**图 1. Amazon Aurora 的查询延迟分布**

本文旨在降低存储计算分离数据库系统（尤其是 OLTP 数据库）中的尾延迟。降低尾延迟对于许多延迟敏感型应用至关重要 [14, 16, 24]，例如在线游戏、金融交易平台、实时通信服务以及需要快速且可预测响应时间的 Web 应用。此外，随着存储计算分离数据库在支撑 AI Agent 工作负载方面变得日益重要 [7, 45]，尾延迟将成为确保 AI Agent 稳定响应的更加关键的因素。

为解决尾延迟问题，我们观察到该问题源于存储计算分离数据库的独特设计，特别是"日志即数据库"（log-as-the-database）[30, 36] 设计原则。具体而言，当事务在计算节点提交时，与传统数据库不同，它并非发送实际的数据页，而仅将预写日志（write-ahead logs）发送至存储节点，以最小化网络上的数据移动。实际的数据页随后在存储节点异步物化。因此，不同查询在等待页面通过回放不同数量的日志而物化时，可能经历不同的等待时间。虽然存储节点中存在后台回放线程，可以在一定程度上缩短待回放日志的长度，但不同页面仍可能具有不同长度的日志回放链。我们将在第 3 节中提供更详细的分析。

一种直接的解决方案是为存储节点分配更多的计算资源，从而加快日志回放速度。然而，这与存储计算分离的原则相悖——存储节点通常具有有限的计算能力，而计算节点则配置有充足的计算容量。如若为存储节点配置高计算能力，在轻前台工作负载下（此时存储节点的日志回放任务较少）将导致显著的资源浪费（和高成本）。

**核心思想**。本文引入了一种名为 RaaS（Replay-as-a-Service，回放即服务）的新技术来解决存储计算分离数据库（特别是 OLTP 数据库）中的尾延迟问题。RaaS 的核心思想是将后台日志回放逻辑从存储引擎中解耦，并将其卸载到集群中的空闲实例甚至专用实例上。我们的观察是，后台日志回放过程消耗大量计算资源，通常由繁重的前台写入工作负载触发，这反过来导致对存储节点有限计算资源的竞争加剧。通过将日志回放逻辑移出，后台回放过程将不再与前台查询处理竞争资源。同时，通过利用集群中的空闲资源，后台日志回放可以更频繁、更高效地执行。这将缩短日志链，不仅加速前台查询处理，还能减少尾延迟——尾延迟通常由访问积累了大量日志的页面所致。此外，该方法不一定需要额外资源，因为正如许多先前工作 [17, 19, 33, 35, 39] 所述，由于工作负载变化（例如突发性工作负载），集群中的其他节点在任何时刻通常都有充足的可用资源。

**挑战与技术概述**。然而，构建 RaaS 并非易事，需要解决以下几个挑战。

首先，后台日志回放逻辑与存储引擎中处理前台页请求（即 GetPage@LSN）的逻辑紧密耦合，这使得将回放任务卸载到空闲实例变得困难。为解决这一问题，我们确定了在何处将资源密集型的页面物化阶段从存储节点解耦，并将日志回放作为无状态服务来执行（第 5.1 节）。

其次，由于日志回放任务的执行依赖于海量数据，并且是从资源受限的存储节点卸载到空闲实例的，因此必须在数据传输过程中最小化存储节点的 CPU 开销——因为其 CPU 资源有限。为此，我们引入了一种利用云对象存储进行高效数据传输的新机制，显著降低了任务卸载期间存储节点的 CPU 负担（第 5.2 节）。

第三，由于将日志回放任务从存储节点解耦后可利用空闲实例上充足的资源，因此必须充分利用这些资源。为此，我们重新设计了原为存储节点资源受限环境定制的单线程日志回放逻辑，通过解决关键的技术挑战来实现并行日志回放。这种新设计显著提升了日志回放性能（第 5.3 节）。

最后，将日志回放任务调度到合适的实例上并非易事，因为这需要选择具有足够可用资源以满足每个任务需求的实例，同时还要尊重任务优先级，防止紧急任务被低优先级任务延迟。为此，我们引入了一个新的控制协调器（control coordinator），通过综合考虑任务优先级和实例资源利用率来管理任务的调度与分配（第 5.4 节）。

**实现**。我们在 OpenAurora [4, 30]（一个基于 PostgreSQL 的开源存储计算分离数据库）中实现了 RaaS。最终系统命名为 RaaS-OpenAurora。值得注意的是，RaaS 可以集成到其他存储计算分离数据库中（如 Amazon Aurora 或 Microsoft Socrates），因为它们与 OpenAurora 共享相同的设计原则。

**实验概述**。我们在第 7 节中使用 84 GB 的 SysBench 数据集进行了实验。结果表明，RaaS 将 P95 尾延迟降低了 40.1%（从 68.28 ms 降至 40.9 ms），并将数据库总体吞吐量提升了 75.9%。

**贡献**。本文做出以下贡献：

- 本文首次识别了存储计算分离数据库（特别是 OLTP 数据库）中的重要尾延迟问题，并分析了其根本原因（第 3 节）。
- 提出了名为 RaaS 的新技术，将后台日志回放任务从存储引擎解耦并在空闲实例上执行，从而在不引入额外资源的情况下降低尾延迟（第 4 节和第 5 节）。
- 在 OpenAurora（一个基于 PostgreSQL 的真实存储计算分离数据库）中实现了 RaaS，证明了 RaaS 与现有数据库的兼容性，便于实际集成和部署（第 6 节）。

**开源**。代码可在 https://github.com/purduedb/OpenAurora/tree/RaaS 获取。

---

## 2 背景

### 2.1 存储计算分离

存储计算分离已成为现代云数据库中的主流架构 [1, 3, 9, 15, 30, 36]。在传统的单体数据库中，计算引擎和存储引擎紧密集成在单个服务器实例中，同时处理查询处理和数据持久化。相比之下，存储计算分离数据库将这些组件分离到不同层次——通过网络连接——以实现独立扩展。

图 2 展示了一个典型存储计算分离数据库的系统架构（例如 Microsoft Socrates [9] 和 Neon [3]），由四层组成：计算层、存储层、日志存储层和对象存储层。计算节点——具有充足的计算能力——负责计算密集型任务，如查询解析、优化、执行和事务处理。存储节点——具有巨大的存储容量——用于持久化和存储数据。日志存储层被引入以加速事务提交。对象存储层（如 Amazon S3）用于通过存储冷数据来降低数据持久化成本。注意，某些存储计算分离数据库（如 Amazon Aurora）将日志存储集成到存储节点中。

**图 2. 存储计算分离数据库架构**

为最小化计算节点与存储节点之间的通信开销，存储计算分离数据库通常采用一种称为"日志即数据库"（log-as-the-database）[1, 3, 9, 15, 30, 36] 的设计原则，即计算节点在事务提交期间仅向存储节点发送日志，存储节点异步回放日志以重建数据页。

### 2.2 写入路径与读取路径

对于**写入路径**（write path），主计算节点在事务执行期间生成日志，如图 2 所示。这些日志被刷写到日志存储层并持久化以确保事务的持久性。之后，日志存储层向主计算节点发送确认以提交事务。日志存储层还异步地将日志转发至次级计算节点和存储节点。在收到日志后，每个次级计算节点检查这些日志是否涉及当前缓存在其缓冲区中的任何页面。若是，则回放相关日志以更新其缓冲区页面；否则，丢弃这些日志，因为任何缺失的更新稍后可以从存储节点获取。与此同时，存储节点在本地存储中临时缓存传入的日志。当累积的日志量超过阈值时，触发后台回放过程以生成新页面。为降低存储成本，另一个后台进程定期将冷页面及其未应用的日志刷写到远程对象存储（如 Amazon S3）中。

对于**读取路径**（read path），当计算节点访问其本地缓冲区中不存在的页面时，它向存储节点发送请求。存储节点检查目标页面是否缓存在本地或远程对象存储中。如果已缓存，则将其取出并返回给计算节点。如果未缓存，存储节点从本地磁盘和远程存储中检索该页面的旧版本及相关日志，回放日志以重建页面，缓存之，并返回给计算节点。

### 2.3 GetPage@LSN

如图 2 所示，主计算节点和多个次级计算节点共享相同的存储节点。如第 2.2 节所述，次级计算节点异步接收日志。这意味着它们在接收和应用日志以更新本地状态之前存在延迟，导致每个次级计算节点处于不同的复制状态。因此，不同的计算节点可能请求相同的页面，但根据其复制状态期望不同的版本。为支持这一点，存储引擎必须维护每个页面的多个版本。

在多版本存储的支持下，每个计算节点使用最近接收日志的日志序列号（Log Sequence Number, LSN）来表示其当前复制状态。当计算节点需要访问一个页面时，它会发出一个 GetPage 请求及其当前的 LSN。此操作称为 GetPage@LSN [9, 36]。在收到此类请求后，存储节点检查是否有与目标页面相关的任何未应用日志，并按 LSN 顺序回放这些日志，以重建与指定 LSN 匹配的页面版本。重建后的页面随后返回给计算节点。这种机制使计算和存储节点能够独立扩展，同时避免由不同计算节点之间复制延迟引起的并发问题。

### 2.4 后台日志回放

在"日志即数据库"的设计下，存储节点可能需要按需回放日志以服务 GetPage@LSN 请求。这种即时的日志回放会引入延迟，并可能导致整体数据库性能下降。为缓解此问题，存储节点运行一个后台日志回放进程（background log replay process），该进程主动在后台应用日志。通过减少 GetPage@LSN 请求时未应用日志的数量，该方法有助于降低请求延迟并提高整体系统性能。

为进一步降低日志回放的成本，一些数据库（如 Amazon Aurora [36] 和 Neon [3]）对 GetPage@LSN 进行了优化，仅回放与目标页面直接相关的一小部分日志，而非按 LSN 顺序扫描所有日志。具体而言，存储节点维护每个页面与其对应日志之间的映射，形成按 LSN 排序的逐页日志链（per-page log chain）。这种设计使存储节点能够快速检索每个 GetPage@LSN 请求所需的最少量相关日志，从而降低其延迟。后台日志回放过程也充分利用了相同的机制。

此外，在某些存储计算分离数据库（如 Neon [3]）中，后台回放过程并非持续活跃；它是周期性触发的。激活后，它会检查每个页面的日志链长度。如果有许多页面的日志链超过预定义阈值，系统开始回放日志，将这些链缩短到可接受的长度。该机制有助于确保大多数页面保持较短的日志链，从而稳定性能并降低尾延迟。

### 2.5 日志存储设计

如第 2.1 节所述，日志存储层被引入以加速事务提交。这是因为提交事务需要计算节点将日志刷写到存储节点以确保持久性。因此，加速日志持久化非常重要。一种广泛采用的优化方案——用于 Socrates [9] 和 Neon [3] 等系统——是在计算层和存储层之间引入一个专用的日志层。该日志层通常使用高性能、低延迟的设备（如 NVMe SSD）构建，并采用分布式复制以确保持久性。为最小化成本，日志存储仅临时保留日志。如图 2 所示，它快速持久化来自计算节点的传入日志以支持事务提交，然后将日志异步转发到存储节点进行长期保留，并最终从自己的本地存储中删除它们。通过这种方式，日志存储充当一个瞬态层，在不增加长期存储成本的情况下加速事务提交。

### 2.6 对象存储层

为进一步降低成本，存储节点通常依赖低成本存储设备进行长期数据保留和超高可用性。一种常见方法是根据访问频率来组织数据。由于数据局部性，大多数数据保持冷状态且很少被访问，而只有一小部分数据是热的且经常被访问。因此，冷数据可以卸载到更慢、更便宜的存储（如 HDD 或云对象存储）。例如，在 Neon [3] 中，存储节点仅在本地 SSD 上存储热数据，并将冷数据卸载到远程对象存储系统（如 Amazon S3），如图 2 所示。这种分层存储策略在不牺牲频繁访问数据性能的情况下显著降低了总体存储成本。

---

## 3 性能特征分析

在本节中，我们提供性能特征分析以理解存储计算分离数据库中尾延迟问题的根本原因。具体而言，我们旨在验证两个假设：

1. 前台 GetPage@LSN 请求（在存储节点上）的延迟与回放的日志数量呈正相关。
2. 后台日志回放进程（同样运行在存储节点上）与前台 GetPage@LSN 请求竞争资源，从而增加请求延迟。

**开源平台**。为验证这些假设，首要问题是使用哪个数据库。Amazon Aurora [36] 不可行，因为它是闭源系统。我们需要一个开源存储计算分离数据库，因为这种分析通常需要访问尾延迟请求的内部指标——这些信息通常无法通过 Aurora 这类闭源系统的标准 API 暴露。通过插桩开源存储计算分离数据库的代码库，我们可以精确了解后台回放何时触发以及回放了多少日志，从而有效地验证这些假设。

因此，我们选择 OpenAurora [4, 30] 作为测试平台，因为它是一个基于 PostgreSQL 构建的开源存储计算分离数据库。OpenAurora 的计算节点基于 PostgreSQL 构建。其存储节点复用 PostgreSQL 的日志复制实现来接收计算节点的更新，并采用 Neon 基于 LSM 的分层存储实现 [3] 来组织和持久化复制数据，支持将冷数据卸载到对象存储以节省成本。

为验证这些假设，我们进行了两个实验来分析高尾延迟问题。我们按如图 2 所示的存储计算分离配置部署了 OpenAurora [4, 30]，包括一个计算节点、一个日志存储节点和一个存储节点，通过 10 Gbps TCP/IP 网络连接。计算节点配置了 8 个 CPU 核心和 16 GB 内存，而日志存储和存储节点各配置了 4 个 CPU 核心、8 GB 内存和一块 1.5 TB NVMe SSD。我们使用了 24 GB 的 SysBench 数据集 [6]，并将基准测试配置为以 16 个线程运行。

**实验 1**。第一个实验旨在验证第一个假设——GetPage@LSN 请求的延迟与回放的日志数量之间是否存在强相关性。该假设的动机是观察到每个 GetPage@LSN 请求需要存储节点即时回放目标页面日志链中累积的日志，如第 2.4 节所述。由于日志链长度可能差异很大，且日志回放涉及大量计算和 I/O，我们推测高延迟的 GetPage@LSN 请求往往涉及更多的日志回放量。

在此实验中，我们插桩了 OpenAurora [4, 30] 的代码库，为每个 GetPage@LSN 请求增加了额外的度量指标，记录回放日志的数量和计算节点观察到的延迟。我们使用 24 GB SysBench 数据集 [6] 的仅更新工作负载预热 OpenAurora。经过 120 秒的预热阶段后，我们再运行 10 秒的仅更新工作负载，以收集日志度量数据进行分析。

**图 3. 查询延迟与回放日志数量之间的关系**
**(a) 查询延迟分布 (b) 平均回放日志数**

图 3a 展示了查询延迟分布。如图所示，大多数查询表现出约 80 ms 的延迟。然而，一些查询经历了明显更高的延迟——约 150 ms——这些被归类为尾延迟。对于每组具有相同延迟的查询，我们计算了回放日志的平均数量，如图 3b 所示。结果表明，**请求延迟与回放日志数量之间存在强正相关关系**。例如，延迟为 86.5 ms 的查询平均回放了 272 条日志，而延迟为 145 ms 的查询平均回放了 380 条日志。相比之下，低延迟（<50 ms）的查询平均回放不到 25 条日志。这些结果表明，需要回放更多日志的 GetPage@LSN 查询往往经历更长的回放时间，最终导致更高的请求延迟。因此，本实验验证了我们的第一个假设。

**实验 2**。第二个实验旨在验证我们的第二个假设——后台日志回放进程与前台 GetPage@LSN 请求竞争有限资源，从而增加其延迟。该假设的灵感来自图 1 中 Amazon Aurora 实验的观察结果。

为进一步分析图 1 中观察到的高尾延迟问题，我们重新组织了实验结果，根据请求的开始时间将其分组为 10 秒间隔，并计算每个间隔的平均吞吐量。绘制这些间隔，如图 4a 所示，揭示了短时间内吞吐量的明显下降，这与后台回放进程的预期执行模式一致。然而，由于 Amazon Aurora 是闭源的且未通过其 API 暴露后台回放指标，我们无法直接分析吞吐量下降的根本原因。

**图 4. 数据库吞吐量与后台回放任务执行**
**(a) Amazon Aurora 吞吐量 (b) OpenAurora 吞吐量**

为解决此问题，我们在开源替代方案 OpenAurora [4, 30] 中分析了同样的问题。我们运行了一个持续的仅更新 SysBench 工作负载并监控吞吐量变化。如图 4b 所示，OpenAurora 也表现出周期性的吞吐量下降，类似于 Aurora 中观察到的现象。我们随后插桩了 OpenAurora 以记录后台回放任务的开始和结束时间。通过将图 4b 中的这些下降与回放任务日志进行关联，我们发现每次吞吐量下降都与后台回放任务的启动时间重合。一旦这些任务完成，吞吐量随即恢复正常。这些发现揭示了后台回放执行与吞吐量下降之间存在的强相关性。

接下来，我们分析后台回放进程降低数据库吞吐量的根本原因。为此，我们使用 perf 和火焰图（flame graph）分析存储节点上的 CPU 使用情况，并研究吞吐量下降与后台回放任务执行之间的关系。具体而言，我们记录了两个 10 秒时间段内的 CPU 使用情况：一个无后台回放任务，一个有后台回放。我们将 CPU 使用分为三类：GetPage@LSN（前台请求处理）、后台回放任务（计时器和执行逻辑）以及其他（杂项函数）。如图 5 所示，当没有后台回放任务运行时，GetPage@LSN 处理消耗了存储节点 90.6% 的 CPU，仅有 3.7% 用于后台回放进程的周期性超时触发阈值检查。然而，在后台回放执行期间，这些任务消耗了 43.0% 的 CPU，将 GetPage@LSN 可用的 CPU 份额降至 49.4%——下降了 45.5%。这种资源竞争解释了观察到的吞吐量下降。

**图 5. 存储节点 CPU 使用情况**

尽管后台回放任务对于减少累积日志和降低未来请求延迟至关重要，但它们是资源密集型的，涉及大量的日志处理和 I/O。因此，它们限制了前台 GetPage@LSN 请求可用的 CPU 资源，增加了其延迟。因此，在后台回放期间发出的所有请求都经历了更高的延迟，导致了存储计算分离数据库中的尾延迟问题。这些发现揭示了**后台回放进程通过与 GetPage@LSN 请求竞争资源而增加了其延迟**，从而支持了我们的第二个假设。

---

## 4 系统概述

在本节中，我们在第 4.1 节中介绍 RaaS（Replay-as-a-Service）的核心思想，并在第 4.2 节中介绍将 RaaS 集成到存储计算分离数据库系统中的总体系统架构。

### 4.1 核心思想

如第 3 节所示，存储计算分离数据库中的尾延迟产生是由于不同页面可能需要回放不同数量的日志。然而，解决这一问题面临挑战。一方面，后台日志回放进程应在存储节点上积极运行，以尽可能地缩短日志链长度。另一方面，这样做会消耗存储节点上大量的计算资源，可能对前台页面访问（在存储节点上）产生负面影响。简单地为存储节点增加更多计算资源也并非理想方案，因为这违背了存储计算分离的原则，并且在工作负载较轻时可能导致资源浪费。

**图 6. 系统架构概览**

本文提出了一种名为 RaaS（Replay-as-a-Service，回放即服务）的新技术。RaaS 的主要思想是将后台日志回放逻辑从存储引擎中解耦，并使用集群中的空闲实例甚至专用实例来执行它。RaaS 从两个方面解决尾延迟问题：(1) RaaS 可以将后台日志回放任务卸载到其他服务器。通过将这些计算密集型任务移出存储节点，前台的 GetPage@LSN 请求不再与后台回放竞争资源，从而避免了后台任务执行期间出现的高尾延迟。(2) 通过使后台任务能够在其他服务器上执行，RaaS 允许它们更频繁、更积极地运行，而无需担心存储节点的资源约束。更频繁的后台回放减少了日志积累，缩短了日志回放链，并进一步降低了 GetPage@LSN 请求的延迟，从而降低了总体尾延迟。

注意，即使存储节点拥有充足的计算资源，RaaS 仍然有效。在这种情况下，回放任务仍然可以由存储节点本地执行。这是因为存储节点在将任务卸载到 RaaS 之前会检查其可用资源，并在资源充足时选择本地执行。因此，RaaS 通过将日志回放任务与存储节点解耦，提供了执行日志回放任务的灵活性。

然而，构建 RaaS 并非易事，其设计和实现面临几个挑战：

- **C1**：如何解决存储引擎中后台日志回放逻辑与前台页面访问逻辑之间的代码耦合？
- **C2**：如何将日志回放任务卸载，同时最小化资源受限存储节点的 CPU 开销？
- **C3**：如何充分利用空闲实例的充足资源来加速日志回放任务？
- **C4**：如何设计调度策略，将日志回放任务分配到合适的实例？

### 4.2 总体架构

图 6 展示了集成 RaaS（Replay-as-a-Service）与 OpenAurora 的架构。注意，RaaS 也兼容其他存储计算分离数据库，如 AWS Aurora [36]、Microsoft Socrates [9]、Google AlloyDB [1] 和 Huawei Taurus [15]。本文中，我们以 OpenAurora 为例说明 RaaS，并将系统称为 OpenAurora-RaaS。

OpenAurora-RaaS 保留了 OpenAurora 的所有核心组件。RaaS 仅修改 OpenAurora 的后台回放机制，不影响任何其他数据库功能，如读写路径（如第 2.2 节所述）。特别地，RaaS 引入了两个新组件：回放服务代理（Replay Service Agent, RSA）和控制协调器（Control Coordinator）。

**RSA** 是一个服务，旨在接收卸载的日志回放任务并作为无状态函数执行它们。它可以快速部署到任何实例上。当主机实例空闲时，RSA 接受来自协调器的回放任务并执行以利用空闲资源。为执行任务，除了从控制协调器接收数据外，RSA 还从 AWS S3 获取必要的数据库文件。在图 6 中，部署了三个 RSA，每个都能够独立接收和执行后台回放任务。

**控制协调器**是一个无状态服务，负责接收来自存储节点的后台回放任务并将其转发到合适的 RSA。其无状态特性使其在崩溃后能够快速恢复，可以部署为单个节点或作为集群的一部分。由于任务的计算成本可能不同，协调器根据可用资源选择合适的 RSA。为此，它执行周期性心跳检查以收集每个 RSA 的最新资源状态。任务调度决策基于这些信息和预定义策略进行，详见第 5.4 节。

在 RaaS 下，后台回放执行流程如下。当后台任务被触发时，存储节点首先检查自身是否有足够的本地资源来执行任务。如果有，则继续其原始的本地后台回放工作流程。否则，存储节点通过以下步骤将后台任务卸载到 RaaS：(a) 存储节点收集并封装回放任务所需的元数据——如页面到日志的映射和日志位置索引——并将其发送到 RaaS 控制协调器。(b) 协调器接收任务并根据其调度策略选择合适的 RSA。(c) 协调器将任务转发到选定的 RSA。(d) 收到任务后，RSA 从 AWS S3 获取所需的额外数据库文件，执行回放，并将结果数据文件刷写回 AWS S3。(e) RSA 向协调器报告任务状态和结果文件的位置。(f) 协调器将此信息转发给存储节点，存储节点随后从 AWS S3 检索结果文件。

---

## 5 系统设计

在本节中，我们介绍 RaaS 的设计选择，并解释它们如何应对第 4.1 节中讨论的挑战。

### 5.1 解耦日志回放逻辑

后台回放任务最初设计为在存储节点本地运行，其逻辑与前台 GetPage@LSN 请求的处理紧密耦合。为使这些任务能够卸载，我们必须解决两个关键问题：如何使任务在 RSA 上可执行，以及如何高效地执行它们。

为使后台回放任务在 RSA 上可执行，RSA 必须复用数据库的回放逻辑，包括解析日志和应用它们来更新数据库文件。然而，执行这些任务还需要元数据，例如页面-日志映射（即哪些日志属于哪些页面）和位置元数据（即页面和日志的存储位置）。这些元数据在后台回放任务和前台 GetPage@LSN 请求之间共享，导致代码紧密耦合。为解耦它们，存储节点必须提取每个任务所需的最小元数据，并将其发送给 RaaS 以指导远程执行。由于 RSA 和存储节点现在各自维护元数据的独立副本，每次远程任务后需要一个最终的元数据同步步骤以确保一致性。这种方法实现了后台回放逻辑的解耦，使其能够在远程 RSA 上执行。

为提高卸载效率，我们需要确定后台回放任务中应开始卸载的合适时机。这需要将任务拆分为多个步骤，并确定哪些部分应保留在本地以避免不必要的开销。在存储计算分离数据库（如 Neon）中，后台回放通常涉及两个主要步骤：(1) 一个超时触发的元数据检查，扫描元数据以决定是否需要回放；(2) 实际的日志回放执行。我们发现只有日志回放步骤是计算密集型的，而元数据检查虽然轻量但发生频率更高。在许多情况下，存储节点因超时而卸载任务，但 RSA 在元数据检查后发现没有足够的日志来支持回放而取消任务。这些频繁的取消浪费了任务打包和网络传输的资源。

为避免这一点，我们仅将日志回放步骤卸载到 RaaS，而将元数据检查保留在存储节点上。这消除了由于频繁取消任务而产生的不必要网络开销，提高了卸载效率。

通过使后台回放任务可在远程 RSA 实例上执行，并确定了合适的卸载时机，挑战 C1 中描述的代码耦合问题得到了有效解决。

### 5.2 最小化卸载开销

简单地将后台任务从存储节点卸载到远程 RSA 可能不会带来显著的性能提升。这是因为后台回放任务依赖大量的数据，而准备数据文件（如序列化和传输）会消耗存储节点上大量资源。由于存储节点本身已资源受限——否则它们会自行执行后台回放——必须在任务卸载期间最小化数据准备和传输的成本。

为最小化卸载开销，我们引入了一种利用云对象存储（如 AWS S3）进行高效数据传输的新机制。在存储计算分离数据库中，除了存储节点外，通常还有一个额外的云存储层用于超高可用性。例如，Amazon Aurora 和 Neon 使用 AWS S3，而 Azure Socrates 使用 XStore。后台回放任务所需的文件通常存储在这些云存储系统中。因此，存储节点无需直接传输大文件，而只需向 RSA 发送元数据，指明所需文件在云存储中的位置。RSA 可以直接获取这些文件。完成回放任务后，RSA 还可以将更新后的文件写回云存储，使存储节点可以按需检索。这种设计显著降低了任务卸载期间存储节点的开销。

一种直接的解决方案是在每次回放任务前将存储节点中所有未刷写的数据刷写到云存储，以确保云存储拥有完整的数据集。然而，这会引入过多的数据传输，并且还可能降低前台请求的性能。我们观察到，每个回放任务通常只需要未刷写文件的一小部分。基于这一洞察，我们允许存储节点有选择地仅将必要的未刷写文件刷写到云存储。这种有针对性的同步是轻量级的，保留了前台请求的资源。

通过上述优化，存储节点在任务卸载期间有效地最小化了与 RSA 之间的卸载开销，回应了挑战 C2 中强调的问题。

### 5.3 并行回放

由于后台日志回放消耗大量资源，在当前存储计算分离数据库（如 Neon）中，由于存储节点的资源有限，通常以单线程方式执行。借助 RaaS，这些回放任务可以卸载到资源充足的实例上，消除了此类约束。为充分利用可用资源并提高执行效率，日志回放过程必须重新设计以支持高效的并行执行。

对于特定页面 *p* 的日志回放涉及两个主要步骤。第一步是收集与 *p* 相关的日志。由于日志最初按 LSN 顺序存储并分割为固定大小文件，单个页面的日志可能分散在多个文件中，增加了访问开销。为解决此问题，我们按页面对日志进行分组并将它们放到同一个文件中。OpenAurora 也实现了此操作，但是以单线程方式。相比之下，我们采用基于并行 MergeSort 的方法。多个线程读取日志并按页面本地排序。当所有线程完成后，进行全局合并和重新分区。这确保了同一页面的日志聚在一起，减少了 GetPage@LSN 期间的文件访问。

第二步是将这些日志应用到 *p* 的基础页面（base page）。由于将日志应用到基础页面会使中间版本不可用（考虑到为支持多个计算节点，每个页面有多个版本），系统必须首先验证这些版本不再被需要。OpenAurora 使用单线程后台任务实现此操作，该任务扫描基础页面并依次应用日志。这种方法速度慢，且未充分利用任务卸载后 RSA 上充足的资源。为解决此问题，我们采用多线程设计，每个线程独立地将日志应用到不同页面，确保并行性而不会产生数据冲突。

总之，RaaS 使后台日志回放任务能够并行执行，回应了挑战 C3。该方法充分利用了远程实例的空闲资源，显著提高了回放任务的执行效率，从而降低了 GetPage@LSN 请求的延迟。

### 5.4 控制协调器

控制协调器是一个无状态服务，管理从计算节点卸载的后台回放任务，并将它们分发到合适的 RSA。如图 7 所示，它由三个关键组件组成：监控器（Monitor）、调度器（Scheduler）和分发器（Dispatcher）。监控器跟踪每个 RSA 实例的可用资源。调度器接收传入任务，将其加入待处理队列，并选择高优先级任务执行。分发器随后将选定的任务发送到合适的 RSA。

**图 7. 控制协调器设计**

#### 5.4.1 监控器

控制协调器旨在根据每个 RSA 的可用资源将任务分配到合适的 RSA。由于 RSA 作为守护服务运行在与其它工作负载共享的实例上，将计算密集型任务分配给资源受限的 RSA 可能会降低共存服务的性能。为防止这种情况，监控器维护一个 RSA IP 地址列表，并定期轮询它们以获取资源使用情况。每个 RSA 以当前的资源可用性回应，监控器收集这些信息。

监控器将这些信息存储在一个有序的条目列表中，格式为（可用 CPU 和内存资源, RSA IP），按可用资源排序。该列表使分发器能够过滤掉容量不足的 RSA，并选择可用资源最多的 RSA。当任务被分配后，估计的资源需求将从列表中该 RSA 的条目中扣除，以反映其更新后的状态。

#### 5.4.2 调度器

调度器负责接收来自存储节点的后台回放任务，并选择优先级最高的任务执行。为支持将任务卸载到 RaaS，所有存储节点向控制协调器注册，并与调度器保持一个持久 socket 连接。回放任务通过此连接提交。

当新任务到达时，调度器的行为取决于当前队列状态。如果没有待处理任务，调度器立即将新任务转发给分发器执行。如果有多个任务排队，它计算它们的优先级并选择最高优先级的任务转发给分发器。任务优先级根据以下规则确定：

第一，工作负载较重的任务被分配更高的优先级。当平均日志链长度超过阈值时触发回放任务，这表明潜在的性能下降。更重的任务意味着更长的日志链和更高的优先级。调度器通过分析任务元数据和关联磁盘文件的数量来估算工作负载。

第二，为避免饥饿，任务优先级随等待时间增加。较轻的任务最初可能被推迟以支持较重的任务，但此规则确保它们最终会被执行。

第三，极重的任务可能被暂时推迟。如果没有 RSA 有足够的资源来执行任务，调度器延迟其分发。如果任务的等待时间超过预定义超时，它将被拒绝以防止无限期排队。

#### 5.4.3 分发器

分发器负责为调度器选择的任务选择合适的 RSA。它使用监控器维护的 RSA 有序列表，该列表按可用资源对实例进行排序。在从调度器接收到任务后，分发器首先根据其元数据估计任务的资源需求。然后，它通过以下启发式策略选择合适的 RSA：

第一，过滤掉资源利用率超过 75% 的 RSA，因为将后台任务分配给高负载实例可能导致资源竞争并降低共存服务的性能。

第二，排除可用资源不足以满足当前任务估计资源需求的 RSA，该估计基于此任务涉及的文件数量。

第三，如果先前曾服务同一存储节点的 RSA 在前两个过滤后仍然合格，分发器优先选择它。此 RSA 可能仍缓存了一些磁盘文件——例如先前生成的结果文件——可以被新任务复用，从而减少网络开销（例如从 Amazon S3 获取数据）。

第四，如果先前的 RSA 不合格，分发器在剩余候选中选择可用资源最多的 RSA。

总之，控制协调器使用调度器接受和优先处理紧急任务，并利用监控器和分发器的组合将任务分发到合适的 RSA 执行。该设计有效地回应了挑战 C4 中概述的任务分配挑战。

### 5.5 容错

由于 RaaS 是引入到存储计算分离数据库中的一个新模块，我们现在讨论如何处理与 RaaS 相关的故障。我们将可能的故障分为三个级别：RSA 上的单个任务失败、RSA 崩溃和控制协调器崩溃。

第一，RSA 上的任务失败可能发生在两种情况下：数据损坏或网络错误。RSA 自动重试与网络相关的失败直到成功。对于数据损坏，RSA 通知存储节点重新尝试任务卸载。

第二，RSA 可能独立发生故障。控制协调器通过周期性心跳消息检测此类故障，并将相应的 RSA 从池中移除。如果失败的 RSA 有未完成的任务，控制协调器通知存储节点重新尝试任务卸载。

第三，我们讨论控制协调器的崩溃。协调器被设计为无状态服务，使其能够在接收到所有 RSA 的资源报告后快速重启并恢复。同时，它还可以冗余部署以消除单点故障并确保高可用性。然而，如果所有协调器实例同时失败，存储节点将暂时回退到不使用 RaaS 的模式运行，直到协调器恢复。

注意，本节描述的容错能力是 RaaS 组件引入的新型故障。此外，使用更好的配置无法解决 RaaS 中的容错问题，因为它无法防止 RSA 上的任务失败、RSA 崩溃或控制协调器崩溃——这些都是 RaaS 组件所特有的问题。

---

## 6 将 RaaS 集成到 OpenAurora

在本节中，我们介绍如何在 OpenAurora 中实现 RaaS。RaaS 也可以在其他存储计算分离数据库中实现。集成涉及两个关键步骤：(1) 将存储节点的后台任务执行代码迁移到 RaaS；(2) 使存储节点能够通过 RaaS 远程调用任务执行。

首先，将存储节点的后台任务执行代码迁移到 RSA，使卸载的任务能够被正确解析和执行。为实现这一目标，我们解耦了 OpenAurora 的后台日志回放函数 `compact_tiered()`，并将其作为名为 `remote_compact_tiered()` 的无状态服务部署在 RSA 上。该函数在从存储节点接收到必要的元数据后即可执行。元数据包含四个关键组成部分：(1) `KeySpace`，指定回放任务涉及的页面 ID 范围——通常是最频繁修改的页面；(2) `LsnRange`，代表日志积累最多的时间跨度；(3) 一个映射索引，将每个页面 ID 链接到其对应的日志 ID；(4) 一个位置索引，用于定位存储在 AWS S3 中的数据文件。借助这些元数据，RSA 从 S3 获取所需的数据文件并开始执行 `remote_compact_tiered()`。完成后，该函数生成两种类型的输出文件：`delta_layer` 和 `page_layer`，分别包含结果日志和页面。RSA 随后将这些文件刷写回 S3，并通知控制协调器它们的位置作为响应的一部分。

其次，我们使存储节点能够调用 RaaS 上的无状态服务。在 OpenAurora 中，后台回放任务最初由 `compaction_execution()` 函数触发，该函数是日志回放的入口点。如第 5.1 节所述，此函数包括两个步骤：(1) 确定累积的日志是否达到回放任务的激活阈值；(2) 执行实际的日志回放。只有第二步需要卸载到 RaaS。详细而言，第一步检查元数据以生成 `KeySpace` 和 `LsnRange`，然后估计涉及的文件数量以决定是否有足够的累积日志。第二步执行日志回放，调用 `compact_tiered()` 函数。我们将此函数调用替换为通过存储节点与 RaaS 控制协调器之间的 socket 连接触发 RaaS 的 `remote_compact_tiered()`。任务完成后，存储节点接收响应，指明执行是否成功以及结果文件在 AWS S3 中的位置。存储节点随后用这些文件位置更新其索引元数据，使前台的 GetPage@LSN 请求能够访问新生成的数据，从而降低请求延迟。

---

## 7 实验评估

### 7.1 实验设置

对于数据库部署，我们启动了 8 个处于存储计算分离模式的 OpenAurora 实例。每个实例包括一个计算节点、一个日志存储节点、一个存储节点，并使用 AWS S3 存储冷数据（遵循图 2）。这些节点运行在配备 Intel Xeon Gold 6330 CPU（2.0 GHz）、250 GB DRAM 和 1.5 TB NVMe SSD 的服务器上，通过 10 Gb TCP/IP 网络连接。每个计算节点分配 8 个 CPU 核心和 32 GB DRAM。每个日志存储和存储节点分配 4 个 CPU 核心和 16 GB DRAM。

对于 RaaS 部署，我们配置了一个协调器节点，配备 2 个 CPU 核心和 8 GB DRAM。协调器节点同样通过 10 Gb TCP/IP 网络连接每个存储节点。此外，每个存储节点托管一个共存的 RSA 服务，以利用其空闲资源而无需引入额外资源。此部署假设在现实场景中，大多数存储节点彼此靠近。通过将 RSA 放置在邻近的存储节点上，可以降低任务卸载的网络开销。然而，RSA 也可以根据需要部署在计算节点或专用实例上。

所有实验都使用 86 GB 的 SysBench 数据集来评估系统性能。我们使用 32 个线程执行读写混合工作负载。

### 7.2 总体吞吐量

在本实验中，我们通过比较两个数据库集群的性能来评估 RaaS 带来的吞吐量提升——一个启用 RaaS，另一个未启用。具体而言，我们部署了 8 个处于存储计算分离模式的 OpenAurora 数据库实例，每个实例加载了 86 GB 的 SysBench 数据集。我们首先运行了 10 分钟的混合读写工作负载来预热数据库。然后，我们对每个实例执行了三轮 5 分钟的混合读写工作负载，各轮之间有 10 分钟的空闲间隔以模拟真实世界的间歇性工作负载。为模拟不同用户间的工作负载变化，8 个数据库并非同时接收工作负载；相反，db5–8 比 db1–4 延迟了 8 分钟。

第一个集群由原始的 8 个未集成 RaaS 的 OpenAurora 实例组成。每个实例独立执行其工作负载。我们以 1 秒间隔测量了平均事务吞吐量。

第二个集群使用相同的 8 个 OpenAurora 实例，配置完全相同，但集成了 RaaS。在此设置中，每个存储节点托管一个专用的 RSA。对此集群应用了相同的工作负载。

**图 8. 平均吞吐量对比**

图 8 展示了结果。没有 RaaS 时，所有实例的平均吞吐量为每秒 1351 个事务。启用 RaaS 后，平均吞吐量显著增加到每秒 2376 个事务。这代表了 75.9% 的提升，仅通过 RaaS 将计算密集型的后台任务卸载到空闲存储节点来实现。通过卸载日志回放任务，RaaS 消除了前台 GetPage@LSN 请求与后台回放之间的资源竞争。此外，频繁且高效的日志回放确保每个 GetPage@LSN 请求只需要应用少量日志。

### 7.3 评估尾延迟

在本实验中，我们分析启用 RaaS 所带来的查询延迟下降。使用与上一实验相同的 8 实例设置，我们比较两个集群：一个启用 RaaS，另一个未启用。在执行三轮 5 分钟混合工作负载后，我们收集并分析每个集群中 db1 的查询延迟直方图。

**图 9. Neon 中的查询延迟分布**
**(a) 无 RaaS (b) 有 RaaS**

图 9a 展示了没有 RaaS 的 db1 延迟直方图，而图 9b 展示了启用 RaaS 的结果。没有 RaaS 时，P95 延迟为 68.28 ms；启用 RaaS 后降至 40.9 ms——降低了 40.1%。对于 P99 延迟，它从 106.75 ms 降至 62.19 ms，延迟下降了 41.7%。

图 9 中的每个直方图显示两个明显的峰值。第一个峰值对应于不涉及或仅涉及极少日志回放的查询，其延迟主要来自网络延迟。这些查询访问的是经历了少量更新或累积日志已通过先前日志回放任务应用的页面。第二个峰值代表需要从多个日志文件进行大量日志回放的查询，其延迟主要由磁盘 I/O 和回放计算主导。

通过比较两个直方图，我们观察到在启用 RaaS 的集群中，落入第一个峰值的查询比未启用 RaaS 的集群更多，表明日志积累减少。具体而言，启用 RaaS 后，53.3% 的查询在 10 ms 内完成，而未启用 RaaS 时仅为 32.5%——增加了 20.8%。至于第二个峰值，没有 RaaS 时，查询延迟分布较为平坦。具体而言，1.33% 的查询超过 100 ms 延迟，而启用 RaaS 后只有 0.06% 的查询超过 100 ms 延迟。这表明 RaaS 实现了更频繁、更高效的日志回放，减少了频繁更新页面上的日志积累，并显著降低了尾延迟。

### 7.4 数据库集群的 CPU 利用率

在本实验中，我们使用 perf 分析混合读写工作负载期间存储节点内不同组件的 CPU 利用率。目标是理解 RaaS 如何通过解决前台 GetPage@LSN 请求与后台日志回放任务之间的资源竞争问题来降低尾延迟。

**图 10. CPU 使用情况**
**(a) 无 RaaS 的 CPU 使用 (b) 有 RaaS 的 CPU 使用**

我们记录了两种配置下存储节点的 CPU 利用率：一种无 RaaS，一种有 RaaS。每个存储节点分配了 4 个 CPU 核心，因此 400% 的利用率代表所有核心的完全使用。图中显示了两种设置下 CPU 使用随时间的变化。

图 10a 显示了没有 RaaS 的独立 OpenAurora 实例的 CPU 利用率。图中，黑色箭头表示工作负载执行期间，红色箭头标记后台日志回放任务被触发的时间。实验期间执行了三个工作负载。在第一个和第三个工作负载期间，存储节点由于从计算节点持续流入 xlog 导致 xlog 缓冲区超过阈值，启动了后台回放。在第二个工作负载期间，没有触发后台任务，CPU 利用率保持在 200% 至 320% 之间，意味着每个核心以大约 50% 至 80% 的利用率运行。此水平足以满足用户工作负载，并避免了由于 CPU 过度饱和导致的性能下降。

然而，在第一个和第三个工作负载期间，后台任务触发后，CPU 利用率达到了高达 400%。如图 5b 所示，只有 49.4% 的 CPU 资源用于前台查询，留下大约 197.6% 的可用资源——远低于实现最佳性能所需的 320%。此外，每个核心 100% 的利用率增加了内核调度开销，进一步降低了性能。值得注意的是，第二个工作负载完成后，即使没有后台回放，CPU 使用率仍保持在 200% 以上约 50 秒。这是因为计算节点的 xlog 产生速率超过了存储节点的 xlog 消耗速率，导致 xlog 在存储节点内存中积累。存储节点临时缓冲这些日志，并在工作负载后逐渐解析和持久化它们。

图 10b 显示了参与 RaaS 集群的存储节点的 CPU 利用率。同样，执行了三个工作负载。我们使用蓝色箭头表示 RSA 执行来自其他服务器的卸载任务。在每个事务工作负载期间，CPU 利用率范围为 200% 至 320%，类似于图 10a 中未受后台回放影响的第二个工作负载。与独立设置不同，这些期间没有可见的后台回放，即使后台任务已被触发。这是因为 RaaS 将回放任务卸载到其他空闲服务器，避免了 CPU 资源的竞争，保持了稳定的性能。在工作负载之间的空闲期间，RSA 接收并执行来自其他节点的回放任务。如蓝色箭头所示，这些任务消耗约 360% 的 CPU，但由于没有活跃的用户事务，它们不影响数据库性能。

在独立设置中，存储节点必须配置为能够处理前台工作负载和后台回放的组合峰值需求，因为两者可能同时发生。然而，在实践中，用户工作负载通常是突发性的，导致空闲期间后台任务要么竞争资源，要么使资源闲置。根据时间的不同，这种耦合导致资源利用不足或不堪重负。

RaaS 解耦了这两种资源需求。在负载下，存储节点将其后台任务卸载到其他节点；空闲时，它接受来自其他节点的任务。这种动态任务交换使集群能够充分利用现有资源而无需添加新硬件。在我们的实验中，独立存储节点在前 2000 秒中空闲了 48%，而启用 RaaS 的节点仅空闲了 18%。这表明 RaaS 主要通过提高资源利用率而非增加配置容量来改善系统性能。

### 7.5 日志回放数量分析

本实验展示了 RaaS 如何通过缓解日志积累来降低尾延迟。

**图 11. 尾延迟与日志回放**

我们比较两种配置：独立数据库和连接到 RaaS 的数据库。两者都使用 1200 秒的仅更新工作负载进行预热。预热后，我们运行 30 秒的仅更新工作负载，并测量每种设置的平均延迟、P95 延迟和 P99 延迟。此外，对于每个 GetPage@LSN 请求，我们记录即时回放的日志数量。对于图 11 中显示的每个延迟桶，我们识别具有该延迟的所有请求，并计算为服务它们而回放的日志的平均数量。

首先，我们分析独立数据库。结果显示请求延迟与回放日志数量之间存在强相关性。平均请求延迟为 9.95 ms，每个请求平均回放 69.4 条日志。P95 延迟为 48.34 ms——约为平均延迟的 485%——对应于回放 167.8 条日志的请求（平均日志数的 241%）。P99 延迟达到 102.69 ms（平均延迟的 1031%），这些请求平均回放 437.8 条日志（平均日志数的 630%）。这证实了需要回放更多日志的请求往往经历更高的延迟。

接下来，我们将其与启用 RaaS 的数据库进行比较。平均而言，它每个请求只回放 11.5 条日志——仅为独立情况的 16.6%——并实现了更低的平均延迟 5.88 ms（独立延迟的 59.1%）。对于尾延迟，RaaS 设置中的 P95 和 P99 请求分别仅回放 24.4 和 262.5 条日志，分别是独立数据库中相应回放数量的 14.5% 和 59.95%。因此，P95 延迟下降了 26.91%（从 48.34 ms 降至 35.33 ms），P99 延迟下降了 37.3%（从 102.69 ms 降至 64.35 ms）。

这些结果表明，RaaS 有效地提前执行了后台回放任务，减少了每个 GetPage@LSN 请求必须回放的日志数量。回放量的减少显著降低了尾延迟。

### 7.6 故障处理

我们展示了四种故障恢复场景。第一，我们考虑 RSA 任务执行期间发生的网络故障。RSA 必须从 S3 下载大量数据以执行回放任务，并将新生成的文件上传回 S3。在这些阶段，网络不稳定可能导致下载或上传失败。RSA 检测到此类故障并在短暂延迟后重试相应操作。如图 12a 所示，RSA 成功生成了新数据文件，但在将这些文件发送到 S3 时发生了两次上传失败。RSA 自动重试上传，无需向协调器或存储节点报告故障。结果，存储节点的后台任务不受影响，系统性能保持稳定。

**图 12. 评估故障恢复**
**(a) S3 上传失败 (b) 单个 RSA 崩溃 (c) 所有 RSA 崩溃 (d) RaaS 崩溃**

第二，RSA 可能因断电或主机故障等原因崩溃，且可能不会立即恢复。图 12b 说明了此场景。存储节点卸载后台任务后，分配的 RSA 在执行期间崩溃。协调器检测到断开连接，将失败的 RSA 标记为不可用，并将任务重新调度到另一个健康的 RSA，后者成功完成了任务。在整个过程中，存储节点对故障保持不知情，也不重新发出任务。唯一可观察到的效果是任务完成延迟——比平常长约 200 秒——这不会导致明显的性能下降。

第三，我们模拟了所有 RSA 临时不可用的场景。为此，我们最初只连接了一个 RSA 到协调器。如图 12c 所示，我们随后关闭了这个 RSA，有效地从系统中移除了所有 RSA。当存储节点稍后发出后台任务请求时，协调器因缺少可用 RSA 而拒绝此请求。结果，存储节点放弃请求并等待下一次触发后台任务的机会。之后，我们向系统添加了一个新的 RSA。在下一次回放触发时，协调器成功将任务调度到新加入的 RSA。在此场景中，存储节点可能暂时错过一次后台回放机会，但这没有长期影响，因为完全的 RSA 不可用是罕见且通常短暂的。

第四，通过在几次成功的任务卸载后关闭协调器来模拟协调器故障（图 12d）。存储节点检测到不可用并回退到本地回放。性能暂时恢复到独立节点的水平，但后台回放继续，没有数据丢失或存储节点故障的风险。

### 7.7 网络开销降低

**表 1. 利用 S3 减少网络传输**

|                     | 数据发送 | 数据接收 |
|---------------------|----------|----------|
| 无 RaaS             | 38 GB    | 11 GB    |
| 有 RaaS             | 3 GB     | 26 KB    |

表 1 评估了利用 AWS S3 如何降低存储节点的卸载开销。在基准设置中，存储节点必须将大型数据文件传输给 RSA 以准备任务，并在回放完成后接收更新文件，从而产生巨大的网络成本。表 1 中的结果表明，利用 AWS S3 可以降低此网络开销。

第一，在任务初始化期间，每个存储节点准备约 33 GB 的数据（152 个文件，每个 256 MB）供 RSA 使用。通过 S3 集成，节点仅同步最近生成的未刷写文件，平均为 3 GB（12 个文件，每个 256 MB），并向 RaaS 发送一条 18 KB 的小型元数据消息。第二，在任务完成期间，存储节点否则将从 RSA 接收 11 GB 的回放数据（44 个文件，每个 256 MB）。通过 S3，RSA 直接将结果刷写到 S3——存储节点的数据仓库——因此节点仅接收一条 26 KB 的元数据消息以同步结果。

总体而言，在卸载路径中利用 S3 将存储节点的网络开销降低了 93.9%（从 49 GB 降至 3 GB）。

### 7.8 TPC-C 结果

**图 13. TPC-C 实验**

我们进行了实验以验证 RaaS 在 TPC-C 上的性能。我们准备了 35 GB 的 TPC-C 数据集并完全预热了数据库。然后分别评估了有和没有 RaaS 的数据库。结果如图 13 所示。结果表明，RaaS 仍然降低了 TPC-C 的尾延迟。例如，启用 RaaS 后，P95 延迟下降了 42.76%（从 225.49 ms 降至 129.08 ms），P99 延迟下降了 36.81%（从 300.43 ms 降至 189.84 ms）。

### 7.9 只读工作负载

**表 2. 评估只读查询**

|                     | 核心数 | 平均值  | P95    | P99    | P999   |
|---------------------|--------|---------|--------|--------|--------|
| 无 RaaS             | 2      | 15.58   | 28.67  | 35.58  | 44.97  |
| 有 RaaS             | 2      | 15.70   | 29.19  | 36.89  | 45.79  |
| 无 RaaS             | 4      | 2.67    | 6.43   | 9.06   | 12.52  |
| 有 RaaS             | 4      | 2.60    | 6.09   | 8.58   | 12.30  |
| 无 RaaS             | 8      | 2.28    | 4.65   | 7.29   | 11.45  |
| 有 RaaS             | 8      | 2.29    | 4.67   | 7.29   | 11.87  |

在本实验中，我们在与第 7.2 节一致的三种资源配置下分析了 RaaS 在只读工作负载上的性能。在运行实验之前，我们预热了数据库并等待所有后台任务完成，确保累积的日志被清除。如表 2 所示，尾延迟显著降低。例如，与图 9a 中的写入工作负载结果相比，在相同配置下，P95 延迟从 68.28 ms 降至 6.43 ms（降低 90.6%），P99 延迟从 106.75 ms 降至 9.06 ms（降低 91.5%）。

此外，在三种配置下，RaaS 表现出与无 RaaS 情况相似的性能。这是因为在只读工作负载下，存储节点上没有日志积累，且由计时器触发的任何回放任务在到达 RaaS 执行阶段之前就被取消了。

### 7.10 非共存 RSA

在本实验中，我们在非共存场景下评估 RaaS，即 RSA 部署在与计算和存储节点分离的专用节点上。我们以第 7.2 节中描述的相同集群配置评估 RaaS 性能，并将其与共存 RaaS 部署和未启用 RaaS 的设置进行比较。

**图 14. 评估非共存部署和非突发性工作负载**
**(a) 突发性工作负载下的吞吐量 (b) 非突发性工作负载下的吞吐量**

基于实验，非共存部署达到了每秒 2365 个事务（TPS），而未启用 RaaS 的配置为 1351 TPS，表明即使部署在专用节点上，RaaS 仍然有效。共存部署达到了 2376 TPS，表现出与非常共存设置相似的性能。这是因为在共存设置中，存储节点将回放任务卸载到其他空闲存储节点，实现了与卸载到专用节点的非共存设置可比的功能。

### 7.11 非突发性工作负载

在本实验中，我们在非突发性工作负载下评估 RaaS 性能，即集群中的所有数据库都持续经历繁重的写入工作负载。如图 14b 所示，在这种非突发性工作负载下，RaaS 的平均性能为 1267 TPS，而不使用 RaaS 的平均性能为 1253 TPS，这意味着在非突发性繁重工作负载下，RaaS 不会对数据库性能产生明显影响。这是预期的结果，因为在非突发性工作负载下，所有存储节点都完全被占用，没有空闲资源来执行 RSA，特别是在共存部署中。因此，共存部署的 RaaS 针对的是现实场景中常见的突发性工作负载，尤其是在云环境中。

然而，图 14b 还显示，如果允许使用额外的服务器（不同于存储或计算节点）进行日志回放，即在非共存部署下，我们的 RaaS 即使在非突发性工作负载下仍然可以提升性能——例如，通过 RaaS 吞吐量提高到 2151 TPS。

### 7.12 评估并行回放

**表 3. RaaS 与本地并行回放对比**

|                                  | 平均值 | P99    | P999   |
|----------------------------------|--------|--------|--------|
| 本地单线程回放                    | 23.69  | 106.75 | 164.45 |
| 本地并行回放                      | 19.83  | 147.61 | 308.84 |
| RaaS 单线程回放                   | 16.28  | 81.48  | 144.97 |
| RaaS 并行回放                     | 13.47  | 62.19  | 92.42  |

在本实验中，我们评估并行回放的有效性，如表 3 所示。结果表明，本地并行回放无法缓解尾延迟问题。例如，它甚至将 P99 延迟增加了 38.3%（从 106.75 ms 增至 147.61 ms），因为并行回放消耗大量系统资源，留给前台 GetPage@LSN 请求的资源更少。注意，在第 4.1 节中，我们也解释了简单为存储节点增加更多计算资源并非理想方案，因为这违背了存储计算分离的原则，且在工作负载较轻时可能导致资源浪费。

我们进一步评估了 RaaS 内并行回放的有效性。结果表明，通过将并行回放纳入 RaaS，平均延迟降低了 17.3%（从 16.28 ms 降至 13.47 ms），P95 延迟进一步下降了 23.7%（从 81.48 ms 降至 62.19 ms），通过比较表 3 中的"RaaS 并行回放"和"RaaS 单线程回放"。

### 7.13 评估回放频率

**表 4. 回放频率**

| 回放间隔 | 平均值 | P99    | P999   |
|----------|--------|--------|--------|
| 5 分钟   | 22.72  | 152.15 | 324.45 |
| 2 分钟   | 19.83  | 147.61 | 308.84 |
| 1 分钟   | 19.86  | 147.19 | 295.29 |
| 0.5 分钟 | 19.82  | 148.52 | 303.80 |

在本实验中，我们分析回放频率如何影响数据库性能。我们部署了没有 RaaS 的 OpenAurora，运行 10 分钟的仅更新工作负载，同时将回放频率从 30 秒变化到 5 分钟。结果如表 4 所示。实验表明，增加回放频率并未显著降低尾延迟。例如，当回放间隔从 5 分钟减少到 2 分钟（即更频繁）时，P99 延迟仅改善了 3.0%。改善有限是因为尽管更频繁的回放减少了日志积累，但回放过程与工作负载并发运行，导致资源竞争，减慢了前台 GetPage@LSN 请求。此外，当回放间隔变得更短（例如 1 分钟或 30 秒）时，性能保持不变。这是因为回放任务会检查累积的日志是否超过执行阈值，如果未超过则取消。在激进的回放间隔下，大多数任务因日志积累不足而被取消。

---

## 8 相关工作

**存储计算分离数据库**。本文聚焦于存储计算分离数据库 [40]，特别是 OLTP 数据库。此类数据库的例子包括 Amazon Aurora [36]、OpenAurora [30]、Microsoft Socrates [9]、Google AlloyDB [1]、Huawei Taurus [15]、Alibaba PolarDB [5, 11] 和 Neon [3]。然而，它们都未解决本文关注的尾延迟问题。本文是首次优化存储计算分离 OLTP 数据库中尾延迟问题的工作。文献中还存在存储计算分离的 OLAP 数据库（例如 Snowflake [13, 38]、AnalyticDB [46]、Polaris [8]、Redshift [10, 29] 和 Dremel [27]），但本文聚焦于存储计算分离的 OLTP 数据库。

**数据系统中降低尾延迟**。降低尾延迟已在各种数据系统中得到了研究，但存储计算分离 OLTP 的上下文因其"日志即数据库"的设计而呈现了独特的挑战，此前的工作未涉及此方面。例如，Li 等人 [25] 对多核系统上高吞吐量服务器的尾延迟进行了系统性研究，识别了导致延迟尖峰的关键系统级因素。Bonspiel 提出了设计新的并发控制协议来缓解地理分布式数据库中的尾延迟 [12]。他们的见解与我们的 RaaS 方法互补，但本文聚焦于从存储计算分离数据库独有的日志回放角度来降低尾延迟。

聚焦于数据中心应用，Xu 等人 [43] 识别出共存虚拟机之间的性能干扰——通常被称为"嘈杂邻居"（noisy neighbors）——是尾延迟的一个主要来源。他们提出了 Bobtail，一个主动检测和避免此类干扰的系统。但他们的方法聚焦于隔离多租户之间的资源竞争。我们的工作通过将后台任务卸载到远程存储实例，专注于消除单个资源受限 VM 内的资源竞争，补充了 Bobtail 的工作。

在信息检索系统中，尾延迟通常由慢查询或繁重的后台任务驱动。为解决此问题，Haque 等人 [16] 提出了通过根据任务执行时间分配额外资源和增加并行度来动态加速慢查询。任务运行时间越长，获得的资源越多，有助于缩短其剩余运行时间。这种自适应并行机制也可以与 RaaS 结合，以提高处理极重日志回放任务的效率。

除了反应式策略外，一些工作 [20, 21, 23] 专注于提前预测慢查询。例如，Jeon 等人 [20] 提出了估计每个任务的执行时间和资源需求，使用动态校正技术处理预测误差。类似地，Jeon 等人 [21] 引入了识别长运行查询并有选择地并行化它们以减少延迟的方法。虽然这些技术可用于识别繁重的后台回放任务，但它们未解决存储计算分离数据库中的尾延迟问题。我们的 RaaS 方法通过将资源密集型后台任务卸载到远程、未充分利用的节点，直接应对了这一挑战。

其他研究 [18, 37] 提出利用其他服务器上的空闲资源来降低尾延迟。Jalaparti 等人 [18] 探索了重新发出慢查询，返回部分结果，以及为选定查询分配额外资源。Vulimiri 等人 [37] 提出在空闲服务器上启动冗余操作并返回第一个完成的结果。虽然这些方法共享利用空闲资源的高层思想，但它们不直接适用于存储计算分离数据库。

**数据系统中的组件解耦**。将资源受限数据库中的计算密集型组件卸载到空闲服务器是一种广泛采用的策略。这遵循了构建可组合数据系统的最新趋势 [31, 32]，其目标是将复杂数据系统的各个模块解耦，以获得诸如定制优化、简化开发、独立扩展和弹性等好处。例如，CaaS-LSM 将 LSM 系统中的压缩（compaction）解耦为服务 [44]，Microsoft Oasis 将查询优化器解耦为服务 [22]，Amazon Redshift 将编译解耦为服务 [10]，PostgreSQL-V 将向量索引从 PostgreSQL 引擎中解耦出来 [26]。我们的工作受到这一研究方向的启发，将日志回放从存储计算分离数据库中解耦，而这是一个先前工作未曾研究过的新上下文。

---

## 9 结论

在本文中，我们首先诊断了存储计算分离数据库中高尾延迟的根本原因，识别出两个关键因素：累积的日志增加了 GetPage@LSN 请求的延迟，以及后台日志回放任务与前台查询竞争资源。为解决这些问题，我们提出将日志回放解耦为无状态服务。具体而言，我们概述了挑战，并通过 RaaS（Replay-as-a-Service）框架的设计和实现提出了解决方案，该框架能够将日志回放任务从资源受限的数据库卸载到空闲实例。我们的评估表明，RaaS 在不需要额外硬件资源的情况下显著提高了吞吐量并降低了尾延迟。

作为未来工作，一个有趣的方向是研究多租户环境下存储计算分离数据库中的尾延迟 [28]，其中资源共享和干扰可能引入新的尾延迟来源。另一个方向是研究内存分离数据库中的尾延迟 [41, 42]，其中基于 RDMA 或 CXL 的远程内存访问可能引入额外的延迟可变性。

---

## 致谢

Jianguo Wang 感谢美国国家科学基金会（National Science Foundation）在 Grant Number 2337806 下的支持。

---

## 参考文献

[1] [n. d.]. AlloyDB for PostgreSQL, https://cloud.google.com/alloydb.
[2] [n. d.]. Amazon Aurora Customers, https://aws.amazon.com/rds/aurora/customers/.
[3] [n. d.]. Neon, https://github.com/neondatabase/neon.
[4] [n. d.]. OpenAurora, https://github.com/purduedb/OpenAurora.
[5] [n. d.]. PolarDB for PostgreSQL, https://github.com/ApsaraDB/PolarDB-for-PostgreSQL.
[6] [n. d.]. SysBench Manual, https://imysql.com/wp-content/uploads/2014/10/sysbench-manual.pdf.
[7] 2025. Databricks Agrees to Acquire Neon to Deliver Serverless Postgres for Developers + AI Agents, https://www.databricks.com/company/newsroom/press-releases/databricks-agrees-acquire-neon-help-developers-deliver-ai-systems.
[8] Josep Aguilar-Saborit and Raghu Ramakrishnan. 2020. POLARIS: The Distributed SQL Engine in Azure Synapse. *PVLDB* 13, 12 (2020), 3204–3216.
[9] Panagiotis Antonopoulos, Alex Budovski, Cristian Diaconu, Alejandro Hernandez Saenz, Jack Hu, Hanuma Kodavalla, Donald Kossmann, Sandeep Lingam, Umar Farooq Minhas, Naveen Prakash, Vijendra Purohit, Hugh Qu, Chaitanya Sreenivas Ravella, Krystyna Reisteter, Sheetal Shrotri, Dixin Tang, and Vikram Wakade. 2019. Socrates: The New SQL Server in the Cloud. In *SIGMOD*. 1743–1756.
[10] Nikos Armenatzoglou, Sanuj Basu, Naga Bhanoori, Mengchu Cai, Naresh Chainani, Kiran Chinta, Venkatraman Govindaraju, Todd J. Green, Monish Gupta, Sebastian Hillig, Eric Hotinger, Yan Leshinksy, Jintian Liang, Michael McCreedy, Fabian Nagel, Ippokratis Pandis, Panos Parchas, Rahul Pathak, Orestis Polychroniou, Foyzur Rahman, Gaurav Saxena, Gokul Soundararajan, Sriram Subramanian, and Doug Terry. 2022. Amazon Redshift Re-invented. In *SIGMOD*. 2205–2217.
[11] Wei Cao, Zhenjun Liu, Peng Wang, Sen Chen, Caifeng Zhu, Song Zheng, Yuhui Wang, and Guoqing Ma. 2018. PolarFS: An Ultra-Low Latency and Failure Resilient Distributed File System for Shared Storage Cloud Database. *PVLDB* 11, 12 (2018), 1849–1862.
[12] Fan Cui, Eric Lo, Srijan Srivastava, and Ziliang Lai. 2025. Bonspiel: Low Tail Latency Transactions in Geo-Distributed Databases. *PVLDB* 18, 11 (2025), 3840–3853.
[13] Benoît Dageville, Thierry Cruanes, Marcin Zukowski, Vadim Antonov, Artin Avanes, Jon Bock, Jonathan Claybaugh, Daniel Engovatov, Martin Hentschel, Jiansheng Huang, Allison W. Lee, Ashish Motivala, Abdul Q. Munir, Steven Pelley, Peter Povinec, Greg Rahn, Spyridon Triantafyllis, and Philipp Unterbrunner. 2016. The Snowflake Elastic Data Warehouse. In *SIGMOD*. 215–226.
[14] Jeffrey Dean and Luiz André Barroso. 2013. The Tail at Scale. *Commun. ACM* 56, 2 (2013), 74–80.
[15] Alex Depoutovitch, Chong Chen, Jin Chen, Paul Larson, Shu Lin, Jack Ng, Wenlin Cui, Qiang Liu, Wei Huang, Yong Xiao, and Yongjun He. 2020. Taurus Database: How to be Fast, Available, and Frugal in the Cloud. In *SIGMOD*. 1463–1478.
[16] Md. Enamul Haque, Yong Hun Eom, Yuxiong He, Sameh Elnikety, Ricardo Bianchini, and Kathryn S. McKinley. 2015. Few-to-Many: Incremental Parallelism for Reducing Tail Latency in Interactive Services. In *ASPLOS*. 161–175.
[17] Rubaba Hasan, Timothy Zhu, and Bhuvan Urgaonkar. 2024. AutoBurst: Autoscaling Burstable Instances for Cost-effective Latency SLOs. In *SoCC*. 243–258.
[18] Virajith Jalaparti, Peter Bodik, Srikanth Kandula, Ishai Menache, Mikhail Rybalkin, and Chenyu Yan. 2013. Speeding Up Distributed Request-response Workflows. *ACM SIGCOMM Computer Communication Review* 43, 4 (2013), 219–230.
[19] Deepal Jayasinghe, Simon Malkowski, Jack Li, Qingyang Wang, Zhikui Wang, and Calton Pu. 2014. Variations in Performance and Scalability: An Experimental Study in IaaS Clouds Using Multi-Tier Workloads. *IEEE Transactions on Services Computing* 7, 2 (2014), 293–306.
[20] Myeongjae Jeon, Yuxiong He, Hwanju Kim, Sameh Elnikety, Scott Rixner, and Alan L. Cox. 2016. TPC: Target-Driven Parallelism Combining Prediction and Correction to Reduce Tail Latency in Interactive Services. In *ASPLOS*. 129–141.
[21] Myeongjae Jeon, Saehoon Kim, Seung-won Hwang, Yuxiong He, Sameh Elnikety, Alan L. Cox, and Scott Rixner. 2014. Predictive Parallelization: Taming Tail Latencies in Web Search. In *SIGIR*. 253–262.
[22] Alekh Jindal and Jyoti Leeka. 2022. Query Optimizer as a Service: An Idea Whose Time Has Come! *SIGMOD Record* 51, 3 (2022), 49–55.
[23] Saehoon Kim, Yuxiong He, Seung-won Hwang, Sameh Elnikety, and Seungjin Choi. 2015. Delayed-Dynamic-Selective (DDS) Prediction for Reducing Extreme Tail Latency in Web Search. In *WSDM*. 7–16.
[24] Lucas Lersch, Ivan Schreter, Ismail Oukid, and Wolfgang Lehner. 2020. Enabling Low Tail Latency on Multicore Key-Value Stores. *PVLDB* 13, 7 (2020), 1091–1104.
[25] Jialin Li, Naveen Kr. Sharma, Dan R. K. Ports, and Steven D. Gribble. 2014. Tales of the Tail: Hardware, OS, and Application-level Sources of Tail Latency. In *SoCC*. 9:1–9:14.
[26] Jiayi Liu, Yunan Zhang, Chenzhe Jin, Aditya Gupta, Shige Liu, and Jianguo Wang. 2026. Fast Vector Search in PostgreSQL: A Decoupled Approach. In *CIDR*.
[27] Sergey Melnik, Andrey Gubarev, Jing Jing Long, Geoffrey Romer, Shiva Shivakumar, Matt Tolton, Theo Vassilakis, Hossein Ahmadi, Dan Delorey, Slava Min, Mosha Pasumansky, and Jeff Shute. 2020. Dremel: A Decade of Interactive SQL Analysis at Web Scale. *PVLDB* 13, 12 (2020), 3461–3472.
[28] Vivek Narasayya and Surajit Chaudhuri. 2022. Multi-tenant Cloud Data Services: State-of-the-art, Challenges and Opportunities. In *SIGMOD*. 2465–2473.
[29] Ippokratis Pandis. 2021. The Evolution of Amazon Redshift. *PVLDB* 14, 12 (2021), 3162–3163.
[30] Xi Pang and Jianguo Wang. 2024. Understanding the Performance Implications of the Design Principles in Storage-Disaggregated Databases. *Proc. ACM Manag. Data* 2, 3 (2024), 180:1–26.
[31] Pedro Pedreira, Orri Erling, Konstantinos Karanasos, Scott Schneider, Wes McKinney, Satyanarayana R. Valluri, Mohamed Zaït, and Jacques Nadeau. 2023. The Composable Data Management System Manifesto. *PVLDB* 16, 10 (2023), 2679–2685.
[32] Pedro Pedreira, Deepak Majeti, and Orri Erling. 2024. Composable Data Management: An Execution Overview. *PVLDB* 17, 12 (2024), 4249–4252.
[33] Xiaoting Qin, Minghua Ma, Yuheng Zhao, Jue Zhang, Chao Du, Yudong Liu, Anjaly Parayil, Chetan Bansal, Saravan Rajmohan, Íñigo Goiri, Eli Cortez, Si Qin, Qingwei Lin, and Dongmei Zhang. 2023. How Different are the Cloud Workloads? Characterizing Large-Scale Private and Public Cloud Workloads. In *IEEE/IFIP International Conference on Dependable Systems and Network (DSN)*. 522–530.
[34] Amazon Web Services. 2020. Why Tens Of Thousands Of Companies Rely On Amazon Aurora To Power Their Most Important And Demanding Applications, https://www.forbes.com/sites/amazonwebservices/2020/11/04/why-tens-of-thousands-of-companies-rely-on-amazon-aurora-to-power-their-most-important-and-demanding-applications/.
[35] Yizhou Shan, Yutong Huang, Yilun Chen, and Yiying Zhang. 2018. LegoOS: A Disseminated, Distributed OS for Hardware Resource Disaggregation. In *OSDI*. 69–87.
[36] Alexandre Verbitski, Anurag Gupta, Debanjan Saha, Murali Brahmadesam, Kamal Gupta, Raman Mittal, Sailesh Krishnamurthy, Sandor Maurice, Tengiz Kharatishvili, and Xiaofeng Bao. 2017. Amazon Aurora: Design Considerations for High Throughput Cloud-Native Relational Databases. In *SIGMOD*. 1041–1052.
[37] Ashish Vulimiri, Philip Brighten Godfrey, Radhika Mittal, Justine Sherry, Sylvia Ratnasamy, and Scott Shenker. 2013. Low Latency via Redundancy. In *CoNEXT*. 283–294.
[38] Midhul Vuppalapati, Justin Miron, Rachit Agarwal, Dan Truong, Ashish Motivala, and Thierry Cruanes. 2020. Building An Elastic Query Engine on Disaggregated Storage. In *NSDI*. 449–462.
[39] Hui Wang. 2024. Burst Load Frequency Prediction Based on Google Cloud Platform Server. *IEEE Trans. Cloud Comput.* 12, 4 (2024), 1158–1171.
[40] Jianguo Wang and Qizhen Zhang. 2023. Disaggregated Database Systems. In *SIGMOD*. 37–44.
[41] Ruihong Wang, Jianguo Wang, and Walid G. Aref. 2025. Cache Coherence Over Disaggregated Memory. *PVLDB* 18, 9 (2025), 2978–2991.
[42] Ruihong Wang, Jianguo Wang, Stratos Idreos, M. Tamer Özsu, and Walid G. Aref. 2022. The Case for Distributed Shared-Memory Databases with RDMA-Enabled Memory Disaggregation. *PVLDB* 16, 1 (2022), 15–22.
[43] Yunjing Xu, Zachary Musgrave, Brian Noble, and Michael Bailey. 2013. Bobtail: Avoiding Long Tails in the Cloud. In *NSDI*. 329–341.
[44] Qiaolin Yu, Chang Guo, Jay Zhuang, Viraj Thakkar, Jianguo Wang, and Zhichao Cao. 2024. CaaS-LSM: Compaction-as-a-Service for LSM-based Key-Value Stores in Storage Disaggregated Infrastructure. *Proc. ACM Manag. Data* 2, 3 (2024), 124: 1–28.
[45] Matei Zaharia. 2025. Bringing the Operational and Analytical Worlds Together with Lakebase. *PVLDB* 18, 12 (2025), 5539.
[46] Chaoqun Zhan, Maomeng Su, Chuangxian Wei, Xiaoqiang Peng, Liang Lin, Sheng Wang, Zhe Chen, Feifei Li, Yue Pan, Fang Zheng, and Chengliang Chai. 2019. AnalyticDB: Real-time OLAP Database System at Alibaba Cloud. *PVLDB* 12, 12 (2019), 2059–2070.

---

*Received July 2025; revised October 2025; accepted November 2025*
