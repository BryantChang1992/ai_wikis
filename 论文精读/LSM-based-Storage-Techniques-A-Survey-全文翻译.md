# LSM-based Storage Techniques: A Survey — 全文翻译

> **论文**：LSM-based Storage Techniques: A Survey  
> **作者**：Chen Luo, Michael J. Carey (UC Irvine)  
> **期刊**：VLDB Journal, 2019 (pre-print arXiv:1812.07527v3)  
> **译者**：CHANG_AI_TEAM CTO (Stark)  
> **翻译日期**：2026-06-12

---

## 摘要

近年来，日志结构合并树（Log-Structured Merge-tree, LSM-tree）已被广泛采用于现代 NoSQL 系统的存储层。正因如此，来自数据库社区和操作系统社区的大量研究工作试图改进 LSM-tree 的各个方面。本文对 LSM-tree 的最新研究工作进行了综述，以便读者了解 LSM-based 存储技术的最新进展。我们提供了一个通用分类体系来对 LSM-tree 文献进行分类，详细调研了相关研究工作，并讨论了它们的优势和权衡。我们进一步调研了几个代表性的基于 LSM 的开源 NoSQL 系统，并基于本次调研的结果讨论了一些潜在的未来研究方向。

**关键词**：LSM-tree · NoSQL · 存储管理 · 索引

---

## 1 引言

日志结构合并树（LSM-tree）已被广泛采用于现代 NoSQL 系统的存储层，包括 BigTable、Dynamo、HBase、Cassandra、LevelDB、RocksDB 和 AsterixDB。与传统采用原地更新的索引结构不同，LSM-tree 首先将所有写入缓冲在内存中，随后将它们刷新到磁盘并使用顺序 I/O 进行合并。这种设计带来了多项优势，包括卓越的写入性能、高空间利用率、可调性以及对并发控制和恢复的简化。这些优势使得 LSM-tree 能够服务于多种工作负载。据 Facebook 报告，RocksDB 这一基于 LSM 的键值存储引擎已被用于实时数据处理、图处理、流处理和 OLTP 工作负载。

由于 LSM-tree 在现代数据存储中的流行，研究社区提出了大量 LSM-tree 的改进方案，这些方案来自数据库和操作系统两个社区。本文综述了这些关于改进 LSM-tree 的最新研究工作，范围从单一 LSM-tree 的键值存储场景到具有二级索引的更通用数据库场景。本文旨在成为研究人员、从业者和用户了解 LSM-based 存储技术最新进展的指南。我们首先提供了一个通用分类体系，基于它们试图优化的具体方面对现有的 LSM-tree 改进进行分类。然后我们详细介绍了各种改进，并讨论了它们的优势和权衡。为了反映 LSM-tree 在实际系统中的使用方式，我们进一步调研了五个代表性的基于 LSM 的开源 NoSQL 系统，包括 LevelDB、RocksDB、HBase、Cassandra 和 AsterixDB。最后，我们还基于对现有 LSM-tree 改进的分类，识别出几个有趣的未来研究方向。

本文其余部分组织如下：第 2 节简要回顾 LSM-tree 的历史并介绍当今 LSM-tree 实现的基础知识。第 3 节提出 LSM-tree 改进的分类体系，并使用该分类调研现有工作。第 4 节调研一些代表性的基于 LSM 的 NoSQL 系统，重点关注它们的存储层。第 5 节反思本综述的结果，识别出 LSM-based 存储系统未来工作的若干空白和机会。最后，第 6 节总结全文。

---

## 2 LSM-tree 基础

本节介绍 LSM-tree 的背景。我们首先简要回顾 LSM-tree 工作的历史，然后更详细地讨论当今存储系统中使用的 LSM-tree 的基本结构。最后，我们给出 LSM-tree 的写入、读取和空间利用率的成本分析。

### 2.1 LSM-tree 的历史

一般来说，索引结构可以选择两种策略来处理更新：原地更新（in-place updates）和异地更新（out-of-place updates）。原地更新结构（如 B+ 树）直接覆盖旧记录以存储新更新。例如在图 1a 中，要将键 k1 关联的值从 v1 更新为 v4，索引条目 (k1, v1) 被直接修改以应用此更新。这些结构通常是读优化的，因为只存储每个记录的最新版本。然而，这种设计牺牲了写入性能，因为更新会产生随机 I/O。此外，索引页面可能因更新和删除而产生碎片，从而降低空间利用率。

相比之下，异地更新结构（如 LSM-tree）总是将更新存储到新位置，而不是覆盖旧条目。例如在图 1b 中，更新 (k1, v4) 被存储到新位置，而不是直接更新旧条目 (k1, v1)。这种设计提高了写入性能，因为它可以利用顺序 I/O 来处理写入。它还可以通过不覆盖旧数据来简化恢复过程。然而，这种设计的主要问题是读取性能被牺牲了，因为一条记录可能存储在多个位置中的任何一个。此外，这些结构通常需要一个单独的数据重组过程来持续提高存储和查询效率。

顺序、异地更新的思想并不新鲜；它自 1970 年代以来已成功应用于数据库系统。差异文件（Differential Files，1976 年）是异地更新结构的早期例子。在这种设计中，所有更新首先应用于一个差异文件，该文件定期与主文件合并。后来，在 1980 年代，Postgres 项目开创了日志结构存储的思想。Postgres 将所有写入追加到顺序日志中，实现了快速恢复和"时间旅行"查询。它使用一个称为 vacuum cleaner 的后台进程来持续垃圾回收日志中的过时记录。类似的思想已被文件系统社区采用以充分利用磁盘写入带宽，如日志结构文件系统（LFS）所示。

在 LSM-tree 之前，日志结构存储方法存在几个关键问题。首先且最重要的是，将数据存储到仅追加日志中导致查询性能低下，因为相关记录分散在日志中。另一个问题是过时记录未及时删除导致空间利用率低。尽管设计了各种数据重组过程，但没有一个原则性的成本模型来分析写入成本、读取成本和空间利用率之间的权衡，这使得早期日志结构存储难以调优；数据重组很容易成为性能瓶颈。

LSM-tree 于 1996 年提出，通过设计一个集成到结构本身的合并过程解决了这些问题，在提供高写入性能的同时保证了有界的查询性能和空间利用率。原始 LSM-tree 设计包含一系列组件 C₀, C₁, ..., C_k，如图 2 所示。每个组件以 B+ 树结构组织。C₀ 驻留在内存中并服务传入的写入，而所有其余组件 C₁, ..., C_k 驻留在磁盘上。当 C_i 满时，触发滚动合并（rolling merge）过程，将 C_i 中的一段叶子页范围合并到 C_{i+1} 中。这种设计今天通常被称为 leveling merge policy。然而，正如我们将会看到的，由于实现复杂性，最初提出的滚动合并过程并未被当今基于 LSM 的存储系统使用。LSM-tree 的原始论文进一步表明，在稳定工作负载下——即层级数量保持静态——当所有相邻组件之间的大小比例 T_i = |C_{i+1}| / |C_i| 相同时，写入性能是最优的。这一原则影响了后续所有 LSM-tree 的实现和改进。

与 LSM-tree 并行，Jagadish 等人提出了一个类似的结构，采用 stepped-merge policy 以实现更好的写入性能。它将组件组织为层级，当层级 L 充满 T 个组件时，这 T 个组件被合并到一起形成层级 L+1 的一个新组件。这种策略成为当今 LSM-tree 实现中使用的 tiering merge policy。

### 2.2 当今的 LSM-tree

#### 2.2.1 基本结构

当今的 LSM-tree 实现仍然应用异地更新以减少随机 I/O。所有传入的写入被追加到一个内存组件中。插入或更新操作简单地添加一个新条目，而删除操作添加一个反物质条目（anti-matter entry）来指示某个键已被删除。然而，当今的 LSM-tree 实现通常利用磁盘组件的不可变性来简化并发控制和恢复。多个磁盘组件被合并到一起形成一个新组件，而不修改现有组件。这与原始 LSM-tree 提出的滚动合并过程不同。

在内部，LSM-tree 组件可以使用任何索引结构来实现。当今的 LSM-tree 实现通常使用并发数据结构（如跳表或 B+ 树）来组织其内存组件，而使用 B+ 树或排序字符串表（SSTable）来组织其磁盘组件。SSTable 包含一个数据块列表和一个索引块；数据块存储按键排序的键值对，索引块存储所有数据块的键范围。

对 LSM-tree 的查询必须搜索多个组件以执行调和（reconciliation），即找到每个键的最新版本。点查找查询——获取特定键的值——可以简单地逐个搜索所有组件，从最新到最旧，并在找到第一个匹配后立即停止。范围查询可以同时搜索所有组件，将搜索结果送入优先队列以执行调和。

随着磁盘组件随时间累积，LSM-tree 的查询性能趋于下降，因为必须检查更多组件。为了解决这个问题，磁盘组件被逐步合并以减少组件总数。实践中通常使用两种合并策略，如图 3 所示。两种策略都将磁盘组件组织为逻辑层级（或层），并由大小比例 T 控制。

**Leveling Merge Policy**（图 3a）：每个层级只维护一个组件，但层级 L 的组件比层级 L-1 的组件大 T 倍。因此，层级 L 的组件将与来自层级 L-1 的传入组件多次合并，直到填满，然后合并到层级 L+1。

**Tiering Merge Policy**（图 3b）：每个层级维护最多 T 个组件。当层级 L 满时，其 T 个组件被合并到一起形成层级 L+1 的一个新组件。如果层级 L 已经是配置的最大层级，则结果组件保留在层级 L。

一般来说，leveling 优化了查询性能，因为需要搜索的组件更少。tiering 更优化写入性能，因为它减少了合并频率。

#### 2.2.2 两个著名的优化

**Bloom Filter**：Bloom filter 是一种空间高效的概率数据结构，用于辅助集合成员查询。它支持插入键和测试给定键的成员资格两种操作。Bloom filter 可以构建在磁盘组件之上，以大大提高点查找性能。搜索一个磁盘组件时，点查找查询可以先检查其 Bloom filter，只有在其关联的 Bloom filter 报告阳性结果时才继续搜索其 B+ 树。Bloom filter 的假阳性率可以计算为 (1-e^(-kn/m))^k，其中 k 是哈希函数数量，n 是键数量，m 是总位数。最优哈希函数数量为 k = (m/n)·ln2。在实践中，大多数系统通常使用 10 bits/key 作为默认配置，这给出 1% 的假阳性率。

**分区（Partitioning）**：另一个常用的优化是将 LSM-tree 的磁盘组件按范围分区为多个（通常是固定大小的）小分区。为最小化术语混淆，我们使用术语 SSTable 表示这样的分区（遵循 LevelDB 的术语）。此优化有多个优势：首先，分区将大的组件合并操作分解为多个小的操作，限制了每个合并操作的处理时间以及创建新组件所需的临时磁盘空间。此外，分区可以通过仅合并具有重叠键范围的组件来优化顺序创建键或倾斜更新的工作负载。PE-file（partitioned exponential file）是将分区应用于 LSM-tree 的早期提案。如今，只有 partitioned leveling policy 被工业 LSM-based 存储系统充分实现，如 LevelDB 和 RocksDB。

**Partitioned Leveling**（由 LevelDB 首创）：每个层级的磁盘组件被按范围分区为多个固定大小的 SSTable。层级 0 的磁盘组件不分区，因为它们直接从内存刷新。要将层级 L 的一个 SSTable 合并到层级 L+1，会选中其在层级 L+1 的所有重叠 SSTable，并将这些 SSTable 与之合并以产生仍位于层级 L+1 的新 SSTable。可以选择不同的策略来决定每个层级接下来合并哪个 SSTable，例如 LevelDB 使用 round-robin 策略。图 4 展示了分区 leveling 中合并操作的例子：层级 0 的 SSTable 0-30 与层级 1 的 0-15 和 16-32 重叠，因此这三个 SSTable 被合并以产生层级 1 的两个新 SSTable 0-20 和 21-32，以及两个未修改的 SSTable 33-50 和 51-100。

**Partitioned Tiering**：分区优化也可以应用于 tiering 合并策略。一个主要问题是每个层级可能包含多个具有重叠键范围的 SSTable。这些 SSTable 必须基于其新近度正确排序。两种可能的方案可用于组织每个层级的 SSTable，即**垂直分组（vertical grouping）**和**水平分组（horizontal grouping）**，如图 5 所示。

在垂直分组方案（图 5a）下，具有重叠键范围的 SSTable 被分组在一起，使得各组具有不相交的键范围。当满足合并条件时（由使用的具体 tiering 策略决定），合并操作将组内的所有 SSTable 合并在一起，基于下一层级重叠组的键范围产生结果 SSTable。在水平分组方案（图 5b）下，每个按范围分区为一组固定大小 SSTable 的组件直接作为逻辑组。每个层级 L 维护一个活跃组（也是第一个组）来接收从前一层级合并来的新 SSTable。当活跃组变满时，它被密封，而下一个组变为活跃组。当层级 L 满时（例如，拥有 T 个组），所有组被合并到层级 L+1。

#### 2.2.3 并发控制与恢复

对于并发控制，LSM-tree 需要处理并发读写，并管理并发的刷新和合并操作。根据事务隔离要求，当今的 LSM-tree 实现要么使用锁方案，要么使用多版本方案。多版本方案与 LSM-tree 配合良好，因为键的过时版本可以在合并期间自然被垃圾回收。并发的刷新和合并操作是 LSM-tree 独有的——这些操作修改 LSM-tree 的元数据（如活跃组件列表），因此对组件元数据的访问必须正确同步。为防止正在使用的组件被删除，每个组件可以维护一个引用计数器。

由于所有写入首先追加到内存中，可以执行预写日志（WAL）以确保持久性。为简化恢复过程，现有系统通常使用 no-steal 缓冲区管理策略——即内存组件只能在所有活跃写事务终止后才能刷新。恢复时，重放事务日志以重做所有成功事务，但由于 no-steal 策略不需要 undo。同时，活跃磁盘组件列表也必须在崩溃时恢复。对于未分区的 LSM-tree，可以通过向每个磁盘组件添加一对时间戳来实现（记录组件的创建时间和删除时间）。对于分区 LSM-tree，典型方法（如 LevelDB 和 RocksDB）是维护单独的元数据日志来存储结构元数据的所有更改。

### 2.3 成本分析

为了帮助理解 LSM-tree 的性能权衡，我们参考了 Dayan 等人提出的写入、点查找、范围查询和空间放大的成本分析。

令 LSM-tree 的大小比例为 T，设 LSM-tree 包含 L 个层级。令 B 为页面大小（每个数据页可存储的条目数），P 为内存组件的页数。一个内存组件最多包含 B·P 个条目，层级 i（i ≥ 0）最多包含 T^(i+1)·B·P 个条目。给定 N 个总条目，最大层级包含约 N·T/(T+1) 个条目，因为它是前一层级的 T 倍。因此，N 个条目的层级数可近似为 L = ⌈log_T(N/(B·P) · T/(T+1))⌉。

**写入成本**（文献中也称为写放大）：度量将一条条目插入 LSM-tree 的摊销 I/O 成本。需要注意的是，该成本度量的是这条条目合并到最大层级的总 I/O 成本，因为写入内存不产生任何磁盘 I/O。对于 leveling，每个层级的组件将被合并 T-1 次直到填满并被推到下一层级。对于 tiering，每个层级的多个组件仅合并一次并直接推到下一层级。因此，每条条目的写入成本对于 leveling 为 O(T·L/B)，对于 tiering 为 O(L/B)。

**点查找**：没有 Bloom filter 时，点查找的 I/O 成本对于 leveling 为 O(L)，对于 tiering 为 O(T·L)。使用 Bloom filter 后，零结果点查找（搜索不存在的键）的 I/O 成本对于 leveling 为 O(L·e^(-M/N))，对于 tiering 为 O(T·L·e^(-M/N))，其中 M 为分配给 Bloom filter 的总位数，N 为唯一条目总数。对于点查找返回结果的查询，无论哪种合并策略，成本均为 O(1)：首先检查每个层级组件的 Bloom filter，若 Bloom filter 报告阳性则执行一次磁盘 I/O 继续搜索组件（可能遇到假阳性），但最终总会在找到匹配条目时停止。

**范围查询**：令 s 为范围查询访问的唯一键数量。对于长范围查询（s/B > 2·L），成本由最大层级主导，因为最大层级包含大部分数据。长范围查询的成本对于 leveling 为 O(s/B)，对于 tiering 为 O(T·s/B)。对于短范围查询，磁盘 I/O 成本（几乎）均等地来自所有层级：leveling 为 O(L)，tiering 为 O(T·L)。

**空间放大（space amplification）**：定义为总条目数除以唯一条目数。对于 leveling，最坏情况发生在最新层级的前一层级包含与最大层级相同的键集时，最坏情况空间放大为 O((T+1)/T)。对于 tiering，最坏情况发生在最大层级的所有组件都包含完全相同的键集时，因此 tiering 的最坏情况空间放大为 O(T)。在实践中，空间放大是部署存储系统时需要考虑的重要因素，因为它直接影响给定工作负载的存储成本。

**成本复杂度总结**（见表 1）：

| 合并策略 | 写入 | 点查找(零结果/非零结果) | 短范围查询 | 长范围查询 | 空间放大 |
|----------|------|------------------------|-----------|-----------|---------|
| Leveling | O(T·L/B) | O(L·e^(-M/N)) / O(1) | O(L) | O(s/B) | O((T+1)/T) |
| Tiering | O(L/B) | O(T·L·e^(-M/N)) / O(1) | O(T·L) | O(T·s/B) | O(T) |

请注意大小比例 T 对 leveling 和 tiering 性能的不同影响。一般来说，leveling 通过每层级维护一个组件来优化查询性能和空间利用率。然而，组件必须更频繁地合并，这会带来高出 T 倍的写入成本。相比之下，tiering 通过每层级维护最多 T 个组件来优化写入性能。但这会使查询性能下降、空间利用率变差，影响程度均为 T 倍。由此可见，LSM-tree 是高度可调的。例如，通过将合并策略从 leveling 改为 tiering，可以大幅改善写入性能，而由于 Bloom filter 的存在，对点查找查询只有很小的负面影响。然而，范围查询和空间利用率将受到显著影响。当我们继续考察关于改进 LSM-tree 的最新文献时会看到，每种改进都在做出某些性能权衡。实际上，基于 RUM 猜想，每种访问方法必须在读成本（R）、更新成本（U）和内存/存储成本（M）之间做出取舍。读者应牢记上述成本复杂度，以更好地理解各改进所做的权衡。

---

## 3 LSM-tree 改进

在本节中，我们首先提出一个分类体系，用于对现有的 LSM-tree 改进研究进行分类。然后，我们按照该分类体系的结构对 LSM-tree 文献进行深入调研。

### 3.1 LSM-tree 改进的分类体系

尽管 LSM-tree 在现代 NoSQL 系统中广受欢迎，但基本 LSM-tree 设计存在各种不足和缺陷。我们现在识别基本 LSM-tree 设计的主要问题，并基于这些缺陷提出 LSM-tree 改进的分类体系。

**写放大（Write Amplification）**：尽管 LSM-tree 通过减少随机 I/O 可以提供比原地更新结构（如 B+ 树）更好的写入吞吐量，但被 LevelDB 和 RocksDB 等现代键值存储采用的 leveling merge policy 仍然会产生相对较高的写放大。高写放大不仅限制了 LSM-tree 的写入性能，还因频繁的磁盘写入缩短了 SSD 的寿命。大量研究致力于降低 LSM-tree 的写放大。

**合并操作（Merge Operations）**：合并操作对 LSM-tree 的性能至关重要，因此必须谨慎实现。此外，合并操作可能对系统产生负面影响，包括合并后缓冲区缓存失效和大型合并期间的写入停顿。已提出若干改进来优化合并操作以解决这些问题。

**硬件（Hardware）**：为了最大化性能，LSM-tree 必须精心实现以充分利用底层硬件平台。原始 LSM-tree 是为硬盘设计的，目标是减少随机 I/O。近年来，新的硬件平台为数据库系统实现更好性能提供了新的机会。大量近期研究致力于改进 LSM-tree 以充分利用底层硬件平台，包括大内存、多核、SSD/NVM 和原生存储。

**特殊工作负载（Special Workloads）**：除硬件机会外，某些特殊工作负载也可以被考虑在内，以在这些用例中实现更好的性能。在这种情况下，必须对基本 LSM-tree 实现进行调整和定制，以利用这些特殊工作负载表现出的独特特征。

**自动调参（Auto-Tuning）**：基于 RUM 猜想，没有一种访问方法可以同时做到读最优、写最优和空间最优。LSM-tree 的可调性是一个有前景的解决方案，可以为给定工作负载实现最优权衡。然而，LSM-tree 可能难以调优，因为需要调节的参数太多，如内存分配、合并策略、大小比例等。为解决这个问题，文献中已提出了几种自动调参技术。

**二级索引（Secondary Indexing）**：单个 LSM-tree 只提供简单的键值接口。为支持对非键属性查询的高效处理，必须维护二级索引。该领域的一个问题是如何以较小的写入性能开销高效地维护一组相关的二级索引。各种基于 LSM 的二级索引结构和技术也已被设计和评估。

基于基本 LSM-tree 设计的这些主要问题，我们提出了 LSM-tree 改进的分类体系（如图 7 所示），以突出现有研究工作试图优化的具体方面。基于此分类体系，表 2 进一步按每个改进的主要关切和次要关切对 LSM-tree 改进进行分类。有了这个分类体系和表，我们现在逐一深入考察每个改进。

分类体系六个一级类别：
- Write Amplification → Tiering, Merge Skipping, Data Skew
- Merge Operations → Merge Performance, Caching, Write Stall
- Hardware → Large Memory, Multi-Core, SSD/NVM, Native Storage
- Special Workloads → Temporal, Small, Semi-Sorted, Append-Mostly
- Auto-Tuning → Parameter Tuning, Bloom Filter, Data Placement
- Secondary Indexing → Index Structure, Index Maintenance, Statistics Collection, Distributed Indexing

### 3.2 降低写放大

在本节中，我们回顾文献中旨在降低 LSM-tree 写放大的改进。这些改进大多基于 tiering，因为它比 leveling 具有更好的写入性能。其他提出的改进则开发了新技术来执行合并跳过或利用数据倾斜。

#### 3.2.1 Tiering

降低写放大的一种方式是应用 tiering，因为它比 leveling 的写放大低得多。但回顾第 2.3 节可知，这会导致更差的查询性能和空间利用率。此类别中的改进都可视为第 2.2.2 节讨论的垂直分组或水平分组的 partitioned tiering 设计的某种变体。这里我们主要讨论这些改进所做的修改。

**WB-tree（WriteBuffer Tree）**：可视为垂直分组的 partitioned tiering 变体。它做了以下修改：第一，它依赖哈希分区实现工作负载均衡，使每个 SSTable 组存储大致相同数量的数据；第二，它将 SSTable 组组织为类 B+ 树结构以实现自平衡，以最小化层级总数。具体而言，每个 SSTable 组被当作 B+ 树中的一个节点。当非叶节点充满 T 个 SSTable 时，这 T 个 SSTable 被合并形成新的 SSTable 加入其子节点。当叶节点充满 T 个 SSTable 时，通过将其所有 SSTable 合并到两个键范围更小的叶节点中进行分裂，使得每个新节点获得约 T/2 个 SSTable。

**LWC-tree（Light-Weight Compaction Tree）**：采用类似的垂直分组 partitioned tiering 设计。它进一步提出了一种通过动态调整 SSTable 组键范围来实现工作负载均衡的方法。在垂直分组方案下，SSTable 不再是严格的固定大小，因为它们是基于下一层级重叠组的键范围产生的，而非基于其大小。在 LWC-tree 中，如果某个组包含过多条目，它会在该组被合并后（此时暂时为空）收缩其键范围，并相应扩大其兄弟组的键范围。

**PebblesDB**：也采用垂直分组的 partitioned tiering 设计。主要区别在于，它使用受跳表启发的 guard 思想来确定 SSTable 组的键范围。guards 即 SSTable 组的键范围，是基于插入的键概率性地选择以实现工作负载均衡。一旦选定 guard，它在下次合并期间被惰性地应用。PebblesDB 进一步执行 SSTable 的并行搜索以改善范围查询性能。

**dCompaction**：引入了虚拟 SSTable 和虚拟合并的概念以减少合并频率。虚拟合并操作产生一个虚拟 SSTable，它简单地指向输入 SSTable 而不执行实际合并。然而，由于虚拟 SSTable 指向多个具有重叠范围的 SSTable，查询性能会下降。为解决这个问题，dCompaction 引入一个基于真实 SSTable 数量的阈值来触发实际合并。它也让查询在遇到指向过多 SSTable 的虚拟 SSTable 时触发实际合并。总的来说，dCompaction 将合并操作延迟直到多个 SSTable 可以一起合并，因此也可以被视为 tiering merge policy 的变体。

**Zhang et al. 和 SifrDB**：采用水平分组的设计。SifrDB 还提出了早期清理技术以在合并期间减少磁盘空间使用，并利用 I/O 并行加速查询。

从上可见，前四种结构（WB-tree, LWC-tree, PebblesDB, dCompaction）都共享类似的基于垂直分组 partitioned tiering 的高层设计。它们主要在 SSTable 组的工作负载均衡方式上不同。WB-tree 依赖哈希，但放弃了支持范围查询的能力。LWC-tree 动态收缩密集 SSTable 组的键范围，而 PebblesDB 依赖概率选择的 guards。相比之下，dCompaction 不提供内置的工作负载均衡支持。尚不清楚偏斜的 SSTable 组会如何影响这些结构的性能。

一个关键的批评是：这些改进通常只与未调参的 LevelDB 或 RocksDB 默认配置比较。例如，LevelDB 默认使用 leveling，当与 tiering 变体对比评估时，测评结果通常是 tiering 变体有更高的写入吞吐量，但查询性能和空间利用率更差。这种测评未充分考虑 LSM-tree 的可调性，即可以通过增大 size ratio T 来改善 leveling 的写入性能。空间放大几乎总是被忽视。

#### 3.2.2 合并跳过

**Skip-tree**：将条目直接从低层级推到高层级的可变缓冲区（mutable buffers），跳过中间层级合并。条目被推到多少层之下取决于该条目创建之后进入的条目数量。由于条目可能被跳过某些层级，查询这些层级时必须检查其 Bloom filter 以确保跳过层级的某个组件中不包含该键。Skip-tree 引入了管理可变缓冲区的非平凡实现复杂性，且查询性能有额外开销。

#### 3.2.3 利用数据倾斜

**TRIAD**：将热键与冷键在内存组件中分离，仅冷键刷新到磁盘。热键定期复制到新事务日志。TRIAD 还通过延迟 L0（层级 0 磁盘组件）的合并、将事务日志用作磁盘组件（消除刷新）来降低写放大。

### 3.3 优化合并操作

#### 3.3.1 提高合并性能

**VT-tree**：引入 stitching 操作。在合并时，如果某输入 SSTable 页面的键范围不与其他任何 SSTable 的任何页面重叠，则该页面可以直接被结果 SSTable 指向，无需读取和复制该页面。缺点是：stitching 导致组件碎片化；stitching 不兼容 Bloom filter（转而使用 Quotient filter）；碎片化组件可能需要额外清理。

**Zhang et al. (流水线合并)**：将合并操作流水线化——读取阶段（I/O 密集）、归并排序阶段（CPU 密集）和写入阶段（I/O 密集）重叠执行，以更好利用 CPU 和 I/O 并行性。

#### 3.3.2 减少缓冲区缓存失效

合并操作后，新组件的启用会导致大量缓冲区缓存缺失，因为新组件中的数据之前未被缓存。简单的写穿缓存维护策略（合并后将新组件写入缓存）不能完全解决该问题。

**Ahmad et al.**：将大型合并卸载到远程服务器，并使用智能缓存预热算法增量获取新组件（逐块而非一次性），将缓存缺失的突发分解为大量较小的缺失。

**LSbM-tree**：合并后不立即删除旧 SSTable，而是将其附加到目标层级 L+1 的缓冲区中作为缓冲 SSTable。这些缓冲 SSTable 同样被查询搜索，并根据访问频率逐渐删除——访问频率越低的 SSTable 被越早删除。这意味着热 SSTable 可能被保留很长时间。对热数据有效，但冷数据会因不得不访问额外 SSTable 而产生额外开销。

#### 3.3.3 最小化写入停顿

**bLSM**：提出 spring-and-gear 合并调度器，在每层级容忍额外一个组件以允许不同层级并行合并。调度器控制合并进度，确保层级 L 仅在前一次合并完成后才产生层级 L+1 的新组件。局限：仅设计用于未分区 leveling；仅限制了写入内存组件的最大延迟，但未处理因大量排队写入造成的排队延迟。

### 3.4 硬件机会

#### 3.4.1 大内存

**FloDB**：两层内存设计。顶层小型并发哈希表（例如 64KB）支持快速写入，底层大型跳表支持高效范围查询。所有写入首先进入顶层哈希表，满了后批量合并到底层跳表。这限制了随机写入仅发生在小内存区域。问题：写入和范围查询可能争用底层跳表，且跳表的内存占用较大（指针开销）。

**Accordion**：多层内存架构。小型可变内存组件处理写入，满了之后通过内存内刷新操作进入更紧凑的不可变内存组件（不写磁盘）。不可变组件可通过内存内合并操作回收空间。仅当不可变组件过多时才写入磁盘。减少了整体磁盘 I/O 并更好利用了内存。

#### 3.4.2 多核

**cLSM**：将 LSM 组件组织为并发链表以最小化同步阻塞。刷新和合并操作仅对链表进行原子修改，永不阻塞查询。支持通过多版本和原子 RMW 操作进行快照扫描。提交操作使用两阶段锁方案。刷新和合并通过引用计数回收旧组件。

#### 3.4.3 SSD/NVM

**FD-tree**：利用分数级联（fractional cascading）代替 Bloom filter 改善点查找性能。每层组件附带指向下一层每页的栅栏指针，点查找每个层级仅需一次随机 I/O。问题：合并需重建所有低层级的栅栏指针；对不存在键的点查找仍需所有层级的磁盘 I/O。

**FD+tree**：改进 FD-tree 的合并过程。增量激活新组件，从旧组件回收不再被活跃查询使用的页面，减少合并时的临时空间开销。

**MaSM**：为数据仓库设计。先将更新缓冲到 SSD（使用 tiering），然后合并回位于 HDD 的基础数据。可视为 Dostoevsky lazy-leveling 的简化形式——小层级使用 tiering，最大层级使用 leveling。

**WiscKey（KV 分离）**：核心思想如图 13 所示。将值存入仅追加日志，LSM-tree 仅作为主索引映射键到日志位置。大幅降低写放大（合并只涉及键而非值），但范围查询显著变差（值不再排序，需要随机 I/O）。值日志需独立 GC：三步流程——扫描日志尾部验证条目 → 将有效条目追加到日志头部 → 截断日志尾部。利用 SSD 的 I/O 并行性搜索多个层级以减少读取延迟。

**HashKV**：改进 WiscKey 的 GC。将值日志按键哈希分区为多个独立日志段，每段独立 GC。冷条目单独存储以减少 GC 频率。

**Kreon**：利用内存映射 I/O 减少 CPU 开销（避免不必要的数据拷贝）。在内核中实现自定义 mmap I/O 管理器控制缓存替换并支持盲写。为改善范围查询性能，Kreon 在查询期间重组数据——将访问的键值对一起存储到新位置。

**NoveLSM**：在 NVM 上增加持久化内存组件。当 DRAM 内存组件满时，写入进入 NVM 组件而不停顿。NVM 组件上跳过日志（NVM 本身提供持久性）。利用 I/O 并行同时搜索多个层级以减少查找延迟。

#### 3.4.4 原生存储

**LDS（LSM-tree-based Direct Storage）**：绕过文件系统，直接管理磁盘布局以更好地利用 LSM-tree 的顺序和聚合 I/O 模式。磁盘布局包含三部分：chunks（存储磁盘组件）、version log（记录每次刷新和合并的元数据变更，如合并产生的废弃 chunks 和新 chunks，定期 checkpoint）、backup log（通过 WAL 为内存写入提供持久性）。

**LOCS**：在开放通道 SSD 上实现 LSM-tree。开放通道 SSD 通过称为 channels 的接口暴露内部 I/O 并行性——每个 channel 独立作为逻辑磁盘设备。LOCS 利用最少加权队列长度策略将刷新和合并产生的磁盘写入分发到所有通道以均衡负载。为进一步提高分区 LSM-tree 的 I/O 并行性，LOCS 将不同层级相似键范围的 SSTable 放入不同通道以并行读取。

**NoFTL-KV**：将闪存转换层（FTL）从存储设备提取到键值存储中以直接控制存储设备。传统上，FTL 将逻辑块地址转换为物理块地址以实现磨损均衡。NoFTL-KV 论证了提取 FTL 的若干优势：将任务下推到存储设备、更高效的数据放置以利用 I/O 并行性、以及将存储设备的 GC 过程与 LSM-tree 的合并过程集成以降低写放大。

#### 3.4.5 小结

在本小节中，我们回顾了利用硬件平台的 LSM-tree 改进，包括大内存（FloDB, Accordion）、多核（cLSM）、SSD/NVM（FD-tree, FD+tree, MaSM, WiscKey, HashKV, Kreon, NoveLSM）和原生存储（LDS, LOCS, NoFTL-KV）。为管理大内存组件，FloDB 和 Accordion 都采用多层方法将随机写入限制在小内存区域。区别在于 FloDB 仅使用两层，而 Accordion 使用多层以提供更好的并发性和内存利用率。对于多核机器，cLSM 提出一套新的并发控制算法以提高并发性。

SSD/NVM 改进的一般主题是利用高随机读吞吐量的同时降低 LSM-tree 的写放大以延长这些存储设备的寿命。FD-tree 及其后继 FD+tree 提议使用分数级联来改善点查找性能，使每个组件只需一次随机 I/O。但当今的实现通常更喜欢 Bloom filter，因为点查找可以避免大部分不必要的 I/O。将键与值分离（WiscKey, HashKV, Kreon）可以显著改善 LSM-tree 的写入性能，因为只有键参与合并。但这导致查询性能和空间利用率下降。同时，值必须单独进行 GC 以回收磁盘空间，这类似于传统的 LFS 设计。最后，一些近期工作提出对存储设备进行原生管理（包括 HDD 上的 LDS 和 SSD 上的 LOCS, NoFTL-KV），这通常能通过利用 LSM-tree 表现出的顺序和非覆盖 I/O 模式带来显著的性能提升。### 3.5 处理特殊工作负载

我们现在回顾一些针对特殊工作负载以实现更好性能的现有 LSM-tree 改进。考虑的特殊工作负载包括时序数据、小数据、半排序数据和仅追加数据。

**LHAM（Log-Structured History Access Method）**：改进原始 LSM-tree 以更高效地支持时序工作负载。关键改进是：为每个组件附加一个时间戳范围，以通过剪枝不相关组件来促进时序查询的处理。进一步保证各组件的时间戳范围互不相交。这是通过修改滚动合并过程实现的——总是将 C_i 中具有最旧时间戳的记录合并到 C_{i+1}。

**LSM-trie**：一种基于 LSM 的哈希索引，用于管理大量键值对且每个键值对都很小的场景。它提出了多项优化以降低元数据开销。LSM-trie 采用 partitioned tiering 设计以降低写放大。它不是直接存储每个 SSTable 的键范围，而是使用其哈希值的前缀来组织 SSTable，如图 14 所示（每层级使用三个比特进行分区）。LSM-trie 进一步消除了索引页，改为基于哈希值将键值对分配到固定大小的桶中。溢出的键值对被分配到未满的桶中，这一信息记录在迁移元数据表中。LSM-trie 还为每个桶构建 Bloom filter。由于每个层级的组中有多个 SSTable，LSM-trie 将这些 SSTable 中相同逻辑桶的所有 Bloom filter 聚集在一起，使得点查找查询可以通过单次 I/O 获取它们。总的来说，LSM-trie 主要在键值对数量极大、以至于连元数据（如索引页和 Bloom filter）都无法完全缓存的情况下有效。但 LSM-trie 仅支持点查找，因为其优化严重依赖哈希。

**SlimDB**：针对半排序数据，即每个键包含一个前缀 x 和一个后缀 y。它支持正常的点查找（同时给定前缀和后缀）以及获取共享同一前缀键的所有键值对。为降低写放大，SlimDB 采用混合结构，低层级使用 tiering，高层级使用 leveling。SlimDB 进一步使用多级 cuckoo filter 来改善使用 tiering merge policy 的层级的点查找性能。在每个层级，多级 cuckoo filter 将每个键映射到存储该键最新版本的 SSTable 的 ID，因此点查找只需一次 filter 检查。为降低 SSTable 的元数据开销，SlimDB 使用多级索引结构：首先将每个前缀键映射到包含该前缀键的页面列表，以便在给定前缀键时高效检索键值对；然后存储每个页面的后缀键范围，以高效支持基于前缀和后缀键的点查找查询。

**Mathieu et al.**：针对仅追加工作负载（数据量持续增加），在最多 K 个组件的有界约束下提出两种新的合并策略。leveling 和 tiering 的一个问题是层级数量取决于总条目数。在仅追加工作负载下，随着数据量持续增加，层级总数将无界增长。为了解决这个问题，该工作研究了在最多 K 个组件的约束下，仅追加工作负载的在线合并策略写入成本的理论下界，并提出了 MinLatency 和 Binomial 两种合并策略来达到该下界。

此处介绍的四种改进各自针对专门的工作负载。需要注意的是，它们的优化对通用工作负载可能无效甚至不适用。例如，LSM-trie 仅支持点查找，而 SlimDB 仅支持有限形式的前缀范围查询。这些优化的采用应基于给定的工作负载谨慎选择。

### 3.6 自动调参

我们现在回顾一些开发 LSM-tree 自动调参技术以减少终端用户调参负担的研究工作。

#### 3.6.1 参数调优

**Lim et al.**：提出了一个纳入键分布的分析模型，以改进 LSM-tree 操作的成本估计，并使用该模型来调优 LSM-tree 的参数。关键洞察是：传统的基于最坏情况的分析（第 2.3 节）未能将键分布纳入考虑。如果在早期合并中发现某个键已被删除或更新，则该键将不会参与后续合并，从而降低其总体写入成本。该模型假设由概率质量函数 f_X(k) 测量的键分布的先验知识——该函数度量特定键 k 被写入请求写入的概率。给定 p 个总写入请求，唯一键数使用其期望估计为 Unique(p) = N − ∑_{k∈K} (1 − f_X(k))^p，其中 N 是唯一条目总数，K 是键空间大小。基于该公式，p 次写入的总写入成本可以通过将所有刷新和合并的成本求和来计算，只是重复键（如有）将从后续合并中排除。最后，该成本模型用于通过最小化总写入成本来找到最优系统参数。

**Monkey**：协同调优合并策略、大小比例以及内存组件与 Bloom filter 之间的内存分配，为给定工作负载找到最优 LSM-tree 设计。Monkey 的第一项贡献是证明了通常的 Bloom filter 内存分配方案（所有 Bloom filter 分配相同的每键位数）导致次优性能。直觉是：最后一层（最大层级）的 T 个组件包含了大部分数据，消耗了大部分 Bloom filter 内存，但它们的 Bloom filter 最多只能为点查找节省 T 次磁盘 I/O。为最小化所有 Bloom filter 的整体假阳性率，Monkey 分析性地证明应为较低层级的组件分配更多位数，使得 Bloom filter 假阳性率呈指数增长。在这种方案下，零结果点查找查询的 I/O 成本将由最大层级主导，新的 I/O 成本对于 leveling 变为 O(e^(-M/N))，对于 tiering 变为 O(T·e^(-M/N))。Monkey 然后使用类似于第 2.3 节的成本模型，通过考虑工作负载中各种操作的混合来最大化总体吞吐量，找到最优 LSM-tree 设计。

#### 3.6.2 合并策略调优

**Dostoevsky**：证明了现有合并策略（tiering 和 leveling）对某些工作负载是次优的。直觉是：对于 leveling，零结果点查找、长范围查询和空间放大的成本由最大层级主导，但写入成本均等地来自所有层级。为解决这个问题，Dostoevsky 引入了 lazy-leveling 合并策略，在较低层级执行 tiering，但在最大层级执行 leveling。Lazy-leveling 的写入成本比 leveling 好得多，但与 leveling 具有相似的点查找成本、长范围查询成本和空间放大。它仅在短范围查询上比 leveling 更差，因为组件数量增加了。Dostoevsky 还提出了混合策略：最大层级最多 Z 个组件，每个较小层级最多 K 个组件，其中 Z 和 K 可调。它然后使用与 Monkey 类似的方法为给定工作负载找到最优 LSM-tree 设计。值得注意的是，Dostoevsky 的性能评估非常全面；它针对经过良好调参的 LSM-tree 进行评估，证明 Dostoevsky 在某些工作负载下严格优于现有的 LSM-tree 设计。

**Thonangi and Yang**：形式化地研究了分区对 LSM-tree 写入成本的影响。首先提出了 ChooseBest 策略——总是选择在下一层级具有最少重叠 SSTable 的 SSTable 进行合并，以界定最坏情况合并成本。虽然 ChooseBest 策略在总体写入成本方面优于未分区的合并策略，但在某些时期未分区的合并策略具有更低的写入成本，因为完整合并后当前层级变空，减少了未来的合并成本。为利用完整合并的这一优势，该工作进一步提出了混合合并策略，根据相邻层级的相对大小选择性地执行完整合并或分区合并，并动态学习这些大小阈值以最小化给定工作负载的总体写入成本。

#### 3.6.3 动态 Bloom filter 内存分配

所有现有 LSM-tree 实现——甚至包括 Monkey——都采用静态方案来管理 Bloom filter 内存分配，即一旦为组件创建了 Bloom filter，其假阳性率就保持不变。与之不同，**ElasticBF** 基于数据热度和访问频率动态调整 Bloom filter 假阳性率以优化读取性能。给定每键 k bits 的 Bloom filter 内存预算，ElasticBF 构建多个较小的 Bloom filter，分别具有 k₁, ..., k_n bits，使得 k₁ + ... + k_n = k。当所有这些 Bloom filter 一起使用时，它们提供与原始单一 Bloom filter 相同的假阳性率。ElasticBF 然后基于访问频率动态激活和停用这些 Bloom filter，以最小化额外的 I/O 总量。实验表明，ElasticBF 主要在 Bloom filter 总体内存非常有限时（例如平均仅 4 bits per key）有效。在这种情况下，由 Bloom filter 假阳性引起的磁盘 I/O 将占主导。当内存相对较大、可以容纳更多 bits per key（例如 10）时，ElasticBF 的收益变得有限，因为由假阳性引起的磁盘 I/O 数量远小于定位键的实际磁盘 I/O 数量。

#### 3.6.4 优化数据放置

**Mutant**：优化 LSM-tree 在云存储上的数据放置。云供应商通常提供多种具有不同性能特征和货币成本的存储选项。给定货币预算，将 SSTable 适当地放置在不同的存储设备上以最大化系统性能可能是重要的。Mutant 通过监控每个 SSTable 的访问频率，并找到一个 SSTable 子集放置到快速存储中，使得对快速存储的总访问次数最大化，同时所选 SSTable 数量受约束。此优化问题等价于 0/1 背包问题（NP 难），可使用贪心算法近似解决。

#### 3.6.5 小结

本类别中介绍的技术旨在为给定工作负载自动调优 LSM-tree。Lim et al. 和 Monkey 都试图为 LSM-tree 找到最优设计以最大化系统性能。然而，这两种技术是互补的。Lim et al. 使用新颖的分析模型来改进成本估计，但仅聚焦于调优 leveling merge policy 的最大层级大小。相比之下，Monkey 及其后续工作 Dostoevsky 协同调优 LSM-tree 的所有参数以找到最优设计，但仅针对最坏情况 I/O 成本进行优化。将这两种技术结合起来以实现更准确的性能调优和预测将是有用的。

Dostoevsky 通过结合 leveling 和 tiering 的新合并策略扩展了 LSM-tree 的设计空间。这对某些需要高效写入、点查找和长范围查询但不太强调短范围查询的工作负载非常有用。Thonangi and Yang 提议将完整合并与分区合并结合以获得更好的写入性能。其他调优技术聚焦于 LSM-tree 实现的某些方面，如 ElasticBF 调优 Bloom filter 和 Mutant 优化数据放置。

### 3.7 二级索引

到目前为止，我们讨论了仅包含单个 LSM-tree 的键值存储场景中的 LSM-tree 改进。现在我们讨论基于 LSM 的二级索引技术，以支持高效的查询处理，包括索引结构、索引维护、统计信息收集和分布式索引。

在详细介绍这些研究工作之前，我们首先讨论 LSM-based 二级索引的一些基本概念。一般来说，基于 LSM 的存储系统将包含一个主索引和多个二级索引。主索引存储按主键索引的记录值。每个二级索引使用复合键方案或键列表方案为每个二级键存储对应的主键。在复合键方案中，二级索引的索引键是二级键和主键的组合。在键列表方案中，二级索引为每个二级键关联一个主键列表。无论哪种方式，使用二级索引处理查询时，首先搜索二级索引以返回匹配主键列表，然后这些主键用于从主索引获取记录（如需要）。LSM-based 二级索引的示例如图 15 所示。示例 User 数据集有三个字段：Id、Name 和 Age，其中 Id 是主键。主索引存储按 Id 索引的完整记录，而两个二级索引存储二级键（即 Name 和 Age）及其对应的 Id。

#### 3.7.1 索引结构

**LSII（Log-Structured Inverted Index）**：为微博精确实时关键词搜索设计的索引结构。查询 q 搜索具有最高分数的 top K 微博，分数计算为显著性、新鲜度和相关性的加权和。为支持高效查询处理，磁盘组件中的每个关键词存储三个倒排列表，分别按显著性、新鲜度和频率降序排列。存储三个倒排列表使查询能够通过阈值算法高效处理——一旦未见到微博的分数上界低于当前 top K 答案，查询评估即停止。然而，内存组件中只存储一个倒排列表，因为内存组件中的文档通常具有高新鲜度且大多会被查询访问，且存储多个倒排列表会显著增加内存组件的写入成本。

**Kim et al.**：对地理标记数据的 LSM-based 空间索引结构进行了实验研究，包括 R-tree、Dynamic Hilbert B+ tree (DHB-tree)、Dynamic Hilbert Value B+ tree (DHVB-tree)、Static Hilbert B+ tree (SHB-tree) 和 Spatial Inverted File (SIF) 的 LSM-tree 版本。R-tree 是一种平衡搜索树，使用最小边界矩形存储多维空间数据。DHB-tree 和 DHVB-tree 使用空间填充曲线将空间点直接存储到 B+ 树中。SHB-tree 和 SIF 利用基于网格的方法，将二维空间静态分解为多级网格层级。对于每个空间对象，存储其重叠单元格的 ID。这两种结构的区别在于：SHB-tree 将单元格 ID 和主键的对存储到 B+ 树中，而 SIF 在倒排索引中为每个单元格 ID 存储主键列表。该研究的关键结论是：这些索引结构中没有绝对的赢家，但 LSM-based R-tree 在摄取和查询工作负载上都表现合理，不需要太多调优。它也能很好地处理点数据和非点数据。此外，对于非仅索引查询，最终的主键查找步骤通常是主导性的，因为它通常需要为每个主键执行单独的磁盘 I/O，这进一步缩小了这些空间索引方法之间的差异。

**Filters**：为主索引和二级索引的每个组件附加一个 filter，以便在查询处理期间基于过滤键进行数据剪枝。filter 存储组件中条目的选定过滤键的最小值和最大值。因此，如果查询的搜索条件与 filter 的最小值和最大值不相交，该组件可以被查询剪枝。虽然 filter 可以构建在任意字段上，但它实际上只对时间相关字段有效，因为组件自然按时间分区，并且可能具有不相交的 filter 范围。需要注意的是，当键被更新或删除时，维护 filter 需要特殊处理。在这种情况下，内存组件的 filter 必须同时基于旧记录和新记录进行维护，以便未来查询不会错过新更新。考虑图 16 中的例子，它描绘了一个带有 filter 的主 LSM-tree。在 upsert 新记录 (k1, v4, T4) 之后，内存组件的 filter 变为 [T1, T4]，以便未来查询将正确看到磁盘组件中的旧记录 (k1, v1, T1) 已被删除。否则，如果内存组件的 filter 仅基于新值 T4 维护（将为 [T3, T4]），搜索条件为 T ≤ T2 的查询将错误地剪枝内存组件，从而实际看到已删除的记录 (k1, v1, T1)。

**Qadar et al.**：对 LSM-based 二级索引技术进行了实验研究，包括 filters 和二级索引。对于 filters，他们评估了组件级范围 filter 和基于二级键的 Bloom filter。对于二级索引，他们评估了基于复合键和键列表的两种二级索引方案。根据二级索引的维护方式，键列表方案可进一步分类为急切（eager）或惰性（lazy）。急切键列表方案总是读取先前列表以创建包含新条目的完整新列表，并将新列表插入内存组件。惰性键列表方案简单地在每个组件维护多个部分列表。实验结果表明，急切倒排列表方案在数据摄取时产生大量开销，因为涉及点查找和高写放大。当查询选择性变大时（即结果集包含更多条目），惰性键列表方案与复合键方案之间的性能差异缩小，因为最终的点查找步骤成为主导。最后，filter 被发现对于时间相关负载非常有效，且存储开销小。然而，该研究未考虑在更新情况下清理二级索引，这意味着二级索引可能返回过时的主键。
#### 3.7.2 索引维护

维护 LSM-based 二级索引的关键挑战是处理更新。对于主 LSM-tree，更新可以盲目地将新条目（具有相同键）添加到内存组件中，从而使旧条目自动被删除。然而，这种机制对二级索引不起作用，因为二级键值在更新期间可能改变。必须执行额外工作以在更新期间从二级索引中清理过时条目。

**Diff-Index**：提出了四种 LSM-based 二级索引的维护方案：sync-full、sync-insert、async-simple 和 async-session。在更新期间，必须执行两个步骤来更新二级索引，即插入新条目和清理旧条目。插入新条目对 LSM-tree 非常高效，但清理旧条目通常代价昂贵，因为它需要点查找来获取旧记录。Sync-full 在摄取期间同步执行这两个步骤，优化查询性能，因为二级索引始终是最新的，但数据摄取时因点查找而产生高开销。Sync-insert 仅将新数据插入二级索引，而将过时条目的清理交给查询惰性执行。Async-simple 异步执行索引维护，但通过将更新追加到异步更新队列来保证其最终执行。Async-session 通过将新更新临时存储在客户端的本地缓存中，为应用增强 async-simple 的会话一致性。

**DELI（Deferred Lightweight Indexing）**：增强了 Diff-Index 的 sync-insert 更新方案，提供了一种通过扫描主索引组件来清理二级索引的新方法。具体而言，在扫描主索引组件时遇到具有相同键的多个记录时，过时的记录用于产生反物质条目以清理二级索引。注意，此过程可以自然地与主索引的合并过程集成以减少额外开销。同时，由于二级索引不总是最新的，查询必须始终通过从主索引获取记录来验证搜索结果。因此，DELI 不能高效支持仅索引查询，因为必须执行点查找进行验证。

**Luo and Carey (PVLDB 2019)**：提出了高效利用和维护 LSM-based 辅助结构（包括二级索引和 filters）的若干技术。他们首先进行了实验研究，评估了各种点查找优化的有效性，包括新提出的批量查找算法（按批次为多个键顺序访问组件）、有状态 B+ 树搜索游标和阻塞 Bloom filter。他们发现批量查找算法是减少随机 I/O 的最有效优化，而其他两种主要在进一步降低内存搜索成本方面对非选择性查询有效。为高效维护辅助结构，进一步提出了两种策略。关键洞察是维护和利用一个主键索引——它仅存储主键加时间戳——以减少磁盘 I/O。提出了一种验证策略，在后台惰性维护二级索引，消除了同步点查找开销。查询必须验证二级索引返回的主键，要么直接从主索引获取记录，要么搜索主键索引以确保返回的主键仍具有最新时间戳。二级索引使用主键索引在后台高效清理，避免访问完整记录；清理的基本思想是搜索主键索引以验证每个二级索引条目是否仍具有最新时间戳，如查询验证中一样。与 DELI 相比，验证策略显著降低了清理二级索引的 I/O 成本，因为只访问主键索引。还引入了可变位图策略，为每个磁盘组件附加一个可变位图，直接将旧记录标记为已删除，从而避免了基于旧记录维护 filter 的需要。

#### 3.7.3 统计信息收集

**Absalyamov et al.**：提出了一种用于 LSM-based 系统的轻量级统计信息收集框架。基本思想是将统计信息收集任务集成到刷新和合并操作中，以最小化统计维护开销。在刷新和合并操作期间，即时创建统计概要（如直方图和小波）并发送回系统目录。由于 LSM-tree 的多组件特性，系统目录为数据集存储多个统计信息。为减少查询优化期间的开销，可合并的统计信息（如等宽直方图）被预先合并。对于不可合并的统计信息，保留多个概要以提高基数估计的准确性。

#### 3.7.4 分布式索引

**Joseph et al.**：描述了 HBase 上分布式二级索引的两种基本实现，即全局二级索引和本地二级索引，基于并行数据库中两种常见的数据索引方法。全局二级索引实现为单独的表，存储二级键加对应主键，使用 HBase 提供的 co-processor（类似数据库触发器）进行维护。此方法易于实现，但数据摄取时产生较高的通信成本，因为二级索引分区可能存储在与主索引分区不同的节点上。本地二级索引通过将每个二级索引分区与对应的主索引分区共置，避免了数据摄取期间的通信成本。但对 HBase 而言，其缺点是此方法必须从头实现。此外，即使是高度选择性的查询，也必须搜索本地二级索引的所有分区，因为本地二级索引是按主键（而非二级键）分区的。

**Zhu et al.**：引入了一种高效的全局二级索引批量加载方法，使用三步：第一，扫描并排序每个分区的主索引以创建本地二级索引，同时收集二级键的统计信息以促进下一步；第二，基于第一阶段收集的统计信息，对二级索引的索引条目进行范围分区，并将这些分区分配给物理节点；第三，基于分配的二级键范围，每个节点从所有其他节点高效获取二级键及其主键，这可以通过扫描第一阶段构建的本地二级索引高效完成。

**Duan et al.**：提出了一种用于分布式 LSM-tree 上物化视图的惰性维护方法。基本思想是将新更新追加到物化视图的 delta 列表中，以减少数据摄取期间的开销。delta 列表中的变更然后在查询处理期间惰性地应用到物化视图。

#### 3.7.5 小结

此类别中的技术都聚焦于在具有二级索引和其他辅助结构的数据库场景中改进 LSM-tree。已提出了若干 LSM-based 二级索引结构，包括 LSM-based 倒排索引、空间索引和 filters。这些结构将有助于优化某些查询工作负载。在高效维护二级索引方面，常见的方法是将二级索引的维护延迟，以便在摄取期间避免昂贵的点查找。提出的技术主要在二级索引如何在后台被清理方面有所不同——要么由查询清理、扫描主索引清理，要么利用主键索引清理。由于这些方法的最优性可能依赖于工作负载，未来工作设计自适应维护机制以最大化性能将是有用的。Absalyamov et al. 提出的统计信息收集框架是向 LSM-based 系统上基于成本的查询优化迈出的一步。最后，还介绍了若干分布式索引技术。需要注意的是，这些技术并不特定于 LSM-tree，但我们在此纳入它们以求完整。

### 3.8 Trade-off 整体讨论

基于 RUM 猜想，没有一种访问方法可以同时做到读最优、写最优和空间最优。我们将 leveling merge policy 作为本讨论的基线。

各种 LSM-tree 改进的性能权衡总结在表 3 中。可以看到，这些改进大多数试图改善 leveling merge policy 的写入性能，因为它具有相对较高的写放大。现有改进采用的常见方法是应用 tiering merge policy（WB-tree, LWC-tree, PebblesDB, dCompaction, Zhang et al., SifrDB），但这将对查询性能和空间利用率产生负面影响。此外，tiering 对范围查询的负面影响大于点查找，因为范围查询不能受益于 Bloom filter。

其他改进（skip-tree, TRIAD, VT-tree）提出了几个新想法来改善写入性能，但引入了额外实现复杂性。skip-tree 的可变缓冲区与磁盘组件不可变性矛盾。TRIAD 提议使用事务日志作为磁盘组件以消除刷新，但日志与磁盘组件存储格式和操作接口差异很大。VT-tree 的 stitching 导致碎片化且与 Bloom filter 不兼容。

LSM-trie 和 SlimDB 放弃了一些查询能力以改善性能。LSM-trie 利用哈希同时改善读写性能但不能支持范围查询。SlimDB 仅支持基于公共前缀键的有限形式范围查询。

将键与值分离（WiscKey, HashKV, Kreon）可以大幅改善 LSM-tree 的写入性能，因为只有键参与合并。但范围查询显著受影响，值不再排序。即使可通过 SSD I/O 并行性缓解，但在值相对较小时磁盘效率仍低。此外，单独存储值导致较低的空间利用率（合并期间不被 GC），必须设计单独的 GC 过程。

鉴于权衡不可避免，探索 LSM-tree 的设计空间是有价值的。Lim et al. 利用数据冗余调优每个层级的最大大小以优化写入性能（其他指标影响小）。Monkey 统一了设计空间并识别出更好的 Bloom filter 分配方案（点查↑，其他不变）。Dostoevsky 用 lazy-leveling 扩展设计空间：写入接近 tiering，查询和空间接近 leveling。

**Table 3 完整翻译**（以 leveling 为基线，↑ 提高，↓ 降低，− 不受影响，× 不支持）：

| 文献 | 写入 | 点查 | 短范围 | 长范围 | 空间 | 备注 |
|------|------|------|--------|--------|------|------|
| WB-tree | ↑↑ | ↓ | ↓↓ | ↓↓ | ↓↓ | Tiering |
| LWC-tree | ↑↑ | ↓ | ↓↓ | ↓↓ | ↓↓ | Tiering |
| PebblesDB | ↑↑ | ↓ | ↓↓ | ↓↓ | ↓↓ | Tiering |
| dCompaction | ↑↑ | ↓ | ↓↓ | ↓↓ | ↓↓ | Tiering |
| Zhang et al. | ↑↑ | ↓ | ↓↓ | ↓↓ | ↓↓ | Tiering |
| SifrDB | ↑↑ | ↓ | ↓↓ | ↓↓ | ↓↓ | Tiering |
| Skip-tree | ↑ | ↓ | ↓ | ↓ | − | 可变跳过缓冲区 |
| TRIAD | ↑ | ↓ | ↓ | ↓ | − | 热冷分离；延迟L0合并 |
| VT-tree | ↑ | − | ↓ | ↓ | ↓ | Stitching 合并 |
| MaSM | ↑↑ | ↓ | ↓↓ | ↓ | ↓ | Lazy leveling |
| WiscKey | ↑↑↑ | ↓ | ↓↓↓ | ↓↓↓ | ↓↓↓ | KV 分离 |
| HashKV | ↑↑↑ | ↓ | ↓↓↓ | ↓↓↓ | ↓↓↓ | KV 分离 |
| Kreon | ↑↑↑ | ↓ | ↓↓↓ | ↓↓↓ | ↓↓↓ | KV 分离 |
| LSM-trie | ↑↑ | ↑ | × | × | ↓↓ | Tiering + 哈希 |
| SlimDB | ↑↑ | ↑ | ↓↓/× | ↓/× | ↓ | 仅前缀键组范围查询 |
| Lim et al. | ↑ | − | − | − | − | 利用数据冗余 |
| Monkey | − | ↑ | − | − | − | 更优 Bloom filter 分配 |
| Dostoevsky | ↑↑ | ↓ | ↓↓ | ↓ | ↓ | Lazy leveling |

---

## 4 代表性的基于 LSM 的系统

在详细讨论了 LSM-tree 及其改进之后，我们现在调研五个代表性的基于 LSM 的开源 NoSQL 系统：LevelDB、RocksDB、Cassandra、HBase 和 AsterixDB。我们将重点关注它们的存储层。

### 4.1 LevelDB

LevelDB 是 Google 于 2011 年开源的 LSM-based 键值存储，支持 put、get、scan 接口。它是一个嵌入式存储引擎。LevelDB 的主要贡献是首创了 partitioned leveling merge policy 的设计和实现，影响了后续众多 LSM-tree 改进和实现。

### 4.2 RocksDB

RocksDB 最初是 Facebook 于 2012 年创建的 LevelDB 分支。Facebook 称采用 LSM-based 存储的主要动机之一是其良好的空间利用率——默认 size ratio 10 下约 90% 数据在最大层级，最多 10% 空间浪费（优于 B 树因碎片化通常 2/3 满）。

RocksDB 的 LSM-tree 实现仍基于 partitioned leveling，但做了多项改进：
- **弹性 L0**：可选 tiering 合并层级 0 的 SSTable 以吸收写入突发
- **动态层级大小**：根据最大层级当前大小动态调整低层级最大容量，确保空间放大始终 O((T+1)/T)
- **SSTable 选择策略**：除 round-robin 外增加 cold-first（倾斜负载优化）和 delete-first（快速回收空间）
- **Merge Filter API**：用户提供自定义逻辑在合并期间 GC 过时条目
- **Tiering 和 FIFO 策略**：Tiering 由 K（合并组件数）和 T（大小比例）控制，从最旧到最新检查；有限分区（水平分组）界定 SSTable 最大大小（4GB 限制）
- **速率限制**：基于漏桶机制控制合并操作磁盘写入速度
- **Read-Modify-Write**：增量记录直接写入内存，查询/合并时与基础记录组合

### 4.3 HBase

Apache HBase 是 Hadoop 生态系统中的分布式数据存储系统（仿照 Bigtable），主从架构。数据集分区为 region，每个由 LSM-tree 管理，支持动态分裂和合并。

- 默认 **Exploring merge policy**：检查所有可合并序列，选写入成本最小的（当组件大小不规则时更有鲁棒性）
- **Date-tiered merge policy**：基于时间范围而非大小合并，使组件按时间范围分区
- **Striping**：将大 region 分区独立合并（类似 PE-files）
- 不原生支持二级索引，可通过 co-processor 实现为单独表

### 4.4 Cassandra

Apache Cassandra 仿照 Dynamo + Bigtable，去中心化架构。每个数据分区由 LSM 存储引擎驱动。

- 支持未分区 tiering、partitioned leveling、date-tiered 合并策略
- 支持本地二级索引，惰性维护（类似 DELI）——更新时若旧记录在内存组件则直接清理，否则合并主索引时惰性清理

### 4.5 AsterixDB

Apache AsterixDB 是开源大数据管理系统，无共享架构。每分区由 LSM 存储引擎管理，含主索引、主键索引和多个本地二级索引。

- **通用 LSM-ification 框架**：将原地索引（B+树/R树/倒排索引）转换为 LSM-based
- **LSM-based 倒排索引**：支持全文查询和相似性查询
- **Correlated merge policy**：由主索引代理合并调度，同步合并所有索引以改善 filter 查询性能
- Luo & Carey (2019) 的索引维护技术在此实现

---

## 5 未来研究方向

**全面的性能评估**：多数改进仅与默认（未调参）的 LevelDB/RocksDB 配置对比，未充分考虑 LSM-tree 的可调性。空间放大往往被忽视。

**分区 Tiering 结构对比**：水平分组和垂直分组两种方案的性能特征和 trade-off 尚不明确。垂直分组允许更多 SSTable 选择自由度，水平分组确保 SSTable 固定大小。系统评估并设计结合两者优势的新方案是有价值的方向。

**混合合并策略**：Dostoevsky 已证明同质合并策略是次优的。设计和实现混合策略并重新审视相关设计问题是重要方向。

**最小化性能波动**：LSM-tree 常因解耦内存写入和后台 I/O 而表现出大性能波动。bLSM 是唯一尝试但局限明显（仅未分区 leveling，仅限制写入延迟而非整体方差）。设计最小化性能波动机制非常有用。

**走向数据库存储引擎**：现有改进多聚焦单 LSM-tree KV-store。随着 LSM-tree 被广泛应用于 DBMS 存储引擎，应开发多索引场景下的新技术：辅助结构自适应维护、LSM-aware 查询优化、合并任务与查询执行协同规划。

---

## 6 结论

近年来，LSM-tree 因优越的写入性能、高空间利用率、磁盘数据不可变性和可调性在现代 NoSQL 系统中日益流行。本文综述了数据库和系统两个社区的最新研究进展，提出了通用分类体系，详细讨论了改进及其权衡，回顾了代表性开源系统，并识别了未来研究方向。希望本综述成为研究人员、从业者和用户了解 LSM-based 存储技术前沿的有用指南。

---

**致谢**：感谢 Mark Callaghan、Manos Athanassoulis 和匿名审稿人的宝贵意见。受 NSF 奖项 CNS-1305430、IIS-1447720、IIS-1838248 资助，以及 Amazon、Google、Microsoft 的工业支持和 UC Irvine Donald Bren 基金会（Bren Chair）支持。

---

## 参考文献

1. Cassandra. http://cassandra.apache.org/
2. Dragon: A distributed graph query engine. https://code.fb.com/data-infrastructure/dragon-a-distributed-graph-query-engine/
3. HBase. https://hbase.apache.org/
4. LevelDB. http://leveldb.org/
5. MyRocks. https://http://myrocks.io/
6. RocksDB. http://rocksdb.org/
7. Absalyamov, I., et al.: Lightweight cardinality estimation in LSM-based systems. In: ACM SIGMOD, pp. 841–855 (2018)
8. Ahmad, M.Y., Kemme, B.: Compaction management in distributed key-value datastores. PVLDB 8(8), 850–861 (2015)
9. Alsubaiee, S., et al.: AsterixDB: A scalable, open source BDMS. PVLDB 7(14), 1905–1916 (2014)
10. Alsubaiee, S., et al.: Storage management in AsterixDB. PVLDB 7(10), 841–852 (2014)
11. Alsubaiee, S., et al.: LSM-based storage and indexing: An old idea with timely benefits. In: GeoRich, pp. 1–6 (2015)
12. Amur, H., et al.: Design of a write-optimized data store. Tech. rep., Georgia Institute of Technology (2013)
13. Athanassoulis, M., et al.: MaSM: efficient online updates in data warehouses. In: ACM SIGMOD, pp. 865–876 (2011)
14. Athanassoulis, M., et al.: Designing access methods: The RUM conjecture. In: EDBT, vol. 2016, pp. 461–466 (2016)
15. Balmau, O., et al.: FloDB: Unlocking memory in persistent key-value stores. In: EuroSys, pp. 80–94 (2017)
16. Balmau, O., et al.: TRIAD: Creating synergies between memory, disk and log in log structured key-value stores. In: USENIX ATC, pp. 363–375 (2017)
17. Bender, M.A., et al.: Don't thrash: how to cache your hash on flash. PVLDB 5(11), 1627–1637 (2012)
18. Bloom, B.H.: Space/time trade-offs in hash coding with allowable errors. CACM 13(7), 422–426 (1970)
19. Bortnikov, E., et al.: Accordion: Better memory organization for LSM key-value stores. PVLDB 11(12), 1863–1875 (2018)
20. Chan, H.H.W., et al.: HashKV: Enabling efficient updates in KV storage via hashing. In: USENIX ATC, pp. 1007–1019 (2018)
21. Chang, F., et al.: Bigtable: A distributed storage system for structured data. ACM TOCS 26(2), 4:1–4:26 (2008)
22. Chazelle, B., Guibas, L.J.: Fractional cascading: I. a data structuring technique. Algorithmica 1(1), 133–162 (1986)
23. Chen, G.J., et al.: Realtime data processing at Facebook. In: ACM SIGMOD, pp. 1087–1098 (2016)
24. Dayan, N., Idreos, S.: Dostoevsky: Better space-time trade-offs for LSM-tree based key-value stores via adaptive removal of superfluous merging. In: ACM SIGMOD, pp. 505–520 (2018)
25. Dayan, N., et al.: Monkey: Optimal navigable key-value store. In: ACM SIGMOD, pp. 79–94 (2017)
26. Dayan, N., et al.: Optimal Bloom filters and adaptive merging for LSM-trees. ACM TODS 43(4), 16:1–16:48 (2018)
27. DeCandia, G., et al.: Dynamo: Amazon's highly available key-value store. In: ACM SOSP, pp. 205–220 (2007)
28. Dong, S., et al.: Optimizing space amplification in RocksDB. In: CIDR, vol. 3, p. 3 (2017)
29. D'silva, J.V., et al.: Secondary indexing techniques for key-value stores: Two rings to rule them all. In: DOLAP (2017)
30. Duan, H., et al.: Incremental materialized view maintenance on distributed log-structured merge-tree. In: DASFAA, pp. 682–700 (2018)
31. Fagin, R., et al.: Optimal aggregation algorithms for middleware. In: ACM PODS, pp. 102–113 (2001)
32. Fan, B., et al.: Cuckoo filter: Practically better than Bloom. In: CoNEXT, pp. 75–88 (2014)
33. Fang, Y., et al.: Spatial indexing in Microsoft SQL Server 2008. In: ACM SIGMOD, pp. 1207–1216 (2008)
34. Golan-Gueta, G., et al.: Scaling concurrent log-structured data stores. In: EuroSys, pp. 32:1–32:14 (2015)
35. Guttman, A.: R-trees: A dynamic index structure for spatial searching. In: ACM SIGMOD, pp. 47–57 (1984)
36. Haerder, T., Reuter, A.: Principles of transaction-oriented database recovery. ACM CSUR 15(4), 287–317 (1983)
37. Jagadish, H.V., et al.: Incremental organization for data recording and warehousing. In: VLDB, pp. 16–25 (1997)
38. Jermaine, C., et al.: The partitioned exponential file for database storage management. VLDBJ 16(4), 417–437 (2007)
39. Kannan, S., et al.: Redesigning LSMs for nonvolatile memory with NoveLSM. In: USENIX ATC, pp. 993–1005 (2018)
40. Khodaei, A., et al.: Hybrid indexing and seamless ranking of spatial and textual features of web documents. In: DEXA, pp. 450–466 (2010)
41. Kim, T., et al.: Supporting similarity queries in Apache AsterixDB. In: EDBT, pp. 528–539 (2018)
42. Kim, Y., et al.: A comparative study of log-structured merge-tree-based spatial indexes for big data. In: ICDE, pp. 147–150 (2017)
43. Lawder, J.: The application of space-filling curves to the storage and retrieval of multi-dimensional data. Ph.D. thesis, University of London (2000)
44. Li, Y., et al.: Tree indexing on solid state drives. PVLDB 3(1-2), 1195–1206 (2010)
45. Lim, H., et al.: Towards accurate and fast evaluation of multi-stage log-structured designs. In: USENIX FAST, pp. 149–166 (2016)
46. Lu, L., et al.: WiscKey: Separating keys from values in SSD-conscious storage. In: USENIX FAST, pp. 133–148 (2016)
47. Luo, C., Carey, M.J.: Efficient data ingestion and query processing for LSM-based storage systems. PVLDB 12(5), 531–543 (2019)
48. Mathieu, C., et al.: Bigtable merge compaction. CoRR abs/1407.3008 (2014)
49. Mei, F., et al.: LSM-tree managed storage for large-scale key-value store. In: ACM SoCC, pp. 142–156 (2017)
50. Mei, F., et al.: SifrDB: A unified solution for write-optimized key-value stores in large datacenter. In: ACM SoCC, pp. 477–489 (2018)
51. Muth, P., et al.: The LHAM log-structured history data access method. VLDBJ 8(3), 199–221 (2000)
52. O'Neil, P., et al.: The log-structured merge-tree (LSM-tree). Acta Inf. 33(4), 351–385 (1996)
53. Pan, F.F., et al.: dCompaction: Speeding up compaction of the LSM-tree via delayed compaction. JCST 32(1), 41–54 (2017)
54. Papagiannis, A., et al.: An efficient memory-mapped key-value store for flash storage. In: ACM SoCC, pp. 490–502 (2018)
55. Pugh, W.: Skip lists: a probabilistic alternative to balanced trees. CACM 33(6), 668–676 (1990)
56. Putze, F., et al.: Cache-, hash-, and space-efficient bloom filters. J. Exp. Algorithmics 14, 4:4.4–4:4.18 (2010)
57. Qader, M.A., et al.: A comparative study of secondary indexing techniques in LSM-based NoSQL databases. In: ACM SIGMOD, pp. 551–566 (2018)
58. Raju, P., et al.: PebblesDB: Building key-value stores using fragmented log-structured merge trees. In: ACM SOSP, pp. 497–514 (2017)
59. Ren, K., et al.: SlimDB: A space-efficient key-value storage engine for semi-sorted data. PVLDB 10(13), 2037–2048 (2017)
60. Rosenblum, M., Ousterhout, J.K.: The design and implementation of a log-structured file system. ACM TOCS 10(1), 26–52 (1992)
61. Sears, R., Ramakrishnan, R.: bLSM: A general purpose log structured merge tree. In: ACM SIGMOD, pp. 217–228 (2012)
62. Seltzer, M.I.: File system performance and transaction support. Ph.D. thesis, UC Berkeley (1992)
63. Severance, D.G., Lohman, G.M.: Differential files: Their application to the maintenance of large databases. ACM TODS 1(3), 256–267 (1976)
64. Shetty, P.J., et al.: Building workload-independent storage with VT-trees. In: USENIX FAST, pp. 17–30 (2013)
65. Stonebraker, M.: The design of the Postgres storage system. In: VLDB, pp. 289–300 (1987)
66. Tan, W., et al.: Diff-index: Differentiated index in distributed log-structured data stores. In: EDBT, pp. 700–711 (2014)
67. Tang, Y., et al.: Deferred lightweight indexing for log-structured key-value stores. In: CCGrid, pp. 11–20 (2015)
68. Teng, D., et al.: LSbM-tree: Re-enabling buffer caching in data management for mixed reads and writes. In: IEEE ICDCS, pp. 68–79 (2017)
69. Teng, D., et al.: A low-cost disk solution enabling LSM-tree to achieve high performance for mixed read/write workloads. ACM TOS 14(2), 15:1–15:26 (2018)
70. Thonangi, R., Yang, J.: On log-structured merge for solid-state drives. In: ICDE, pp. 683–694 (2017)
71. Thonangi, R., et al.: A practical concurrent index for solid-state drives. In: ACM CIKM, pp. 1332–1341 (2012)
72. Turner, J.: New directions in communications (or which way to the information age?). IEEE Communications Magazine 24(10), 8–15 (1986)
73. Vinçon, T., et al.: NoFTL-KV: Tackling write-amplification on KV-stores with native storage management. In: EDBT, pp. 457–460 (2018)
74. Wang, P., et al.: An efficient design and implementation of LSM-tree based key-value store on open-channel SSD. In: EuroSys, pp. 16:1–16:14 (2014)
75. Wu, L., et al.: LSII: An indexing structure for exact real-time search on microblogs. In: ICDE, pp. 482–493 (2013)
76. Wu, X., et al.: LSM-trie: an LSM-tree-based ultra-large key-value store for small data. In: USENIX ATC, pp. 71–82 (2015)
77. Yao, A.C.C.: On random 2–3 trees. Acta Informatica 9(2), 159–170 (1978)
78. Yao, T., et al.: Building efficient key-value stores via a lightweight compaction tree. ACM TOS 13(4), 29:1–29:28 (2017)
79. Yao, T., et al.: A light-weight compaction tree to reduce I/O amplification toward efficient key-value stores. In: MSST (2017)
80. Yoon, H., et al.: Mutant: Balancing storage cost and latency in LSM-tree data stores. In: ACM SoCC, pp. 162–173 (2018)
81. Yue, Y., et al.: Building an efficient put-intensive key-value store with skip-tree. IEEE TPDS 28(4), 961–973 (2017)
82. Zhang, W., et al.: Improving the write performance of log-structured key-value stores via pipeline compaction. In: IEEE IPCCC, pp. 1–8 (2017)
83. Zhang, Z., et al.: A novel method of log-structured merge tree based key-value store for a massive amount of small data. In: IEEE UIC, pp. 983–990 (2015)
84. Zhou, J., et al.: Geo-aware erasure coding for high-performance erasure-coded storage clusters. IEEE TPDS 29(6), 1274–1287 (2018)
85. Zhu, Z., et al.: Efficient bulk loading for distributed LSM-based key-value stores. In: ACM SIGMOD, pp. 837–850 (2019)
