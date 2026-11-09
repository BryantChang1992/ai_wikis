---
type: survey
title: 技术调研周报 Week 17：并发改写、持久化边界与状态复用
sources:
- https://www.starburst.io/blog/equality-deletes-compaction-and-iceberg-v4/
- https://github.com/apache/iceberg/blob/60897e0b828580cc20e591424179d9b5c574e8d6/core/src/main/java/org/apache/iceberg/MergingSnapshotProducer.java
- https://alexmerced.blog/blog/2026-10-28-iceberg-v4-table-constraints
- https://iceberg.apache.org/spec/
- https://paimon.apache.org/blog/
- https://mirrorship.ai/en/blog/multimodal-retrieval-starrocks-paimon
- https://www.usenix.org/conference/osdi26/technical-sessions
- https://www.usenix.org/conference/osdi26/presentation/kim-jongyul
- https://www.usenix.org/system/files/osdi26-kim-jongyul.pdf
- https://github.com/xlab-uiuc/oxbow
- https://github.com/xlab-uiuc/oxbow/blob/osdi26-ae/Documentation/artifact-evaluation.md
- https://www.usenix.org/conference/osdi26/presentation/ahn
- https://www.usenix.org/system/files/osdi26-ahn.pdf
- https://github.com/syslab-CAU/DeLFS
- https://fluss.apache.org/blog/how-jd-built-a-lakestream-with-fluss-and-hudi/
- https://hudi.apache.org/blog/2026/10/14/how-jd-built-a-lakestream-with-fluss-and-hudi/
- https://kafka.apache.org/blog/
- https://www.automq.com/blog
- https://blog.cloudflare.com/kv-cache-exposure-remediation/
- https://www.lmsys.org/blog/2026-10-26-cf-security
- https://arxiv.org/html/2610.36355v1
- https://www.lmsys.org/blog/2026-10-22-miles-mi355x-agentic-rl
tags:
- 数据湖
- Iceberg
- Fluss
- 分布式存储
- AI Infra
created: '2026-11-09'
updated: '2026-11-09'
status: draft
publication_scope: 公开技术报告及引用；知识卡和独立专题不因本文同步而扩大发布范围。在线状态以实际部署验收为准。
report_date: '2026-11-01'
issue: 17
issue_date: '2026-11-01'
observation_start: '2026-10-25T00:00:00Z'
observation_end: '2026-11-01T00:00:00Z'
source_checked: '2026-11-01'
source_check_scope: 沿用原报告的原文核验日期与范围；本次仅归档，未重新核读全部外部来源。
related:
- '[[知识库/sources/web/technical-trends-week17/来源索引]]'
---

# 技术调研周报 Week 17：并发改写、持久化边界与状态复用

> 阅读时间说明：本文保留 2026-11-01 报告的观察窗口、原文核验时间和技术限制。正文中的“本周”、版本阶段及历史交付说明均按原观察时点理解，不代表本次页面整理时的最新状态。本次仅适配发布格式，未重新核读全部外部来源或独立复现实验。 原文核验截止：2026-11-01 00:18 UTC。

[公开来源索引](../../知识库/sources/web/technical-trends-week17/来源索引.md)

观察窗口：2026 年 10 月 25 日 00:00（含）至 11 月 1 日 00:00（不含）UTC，即北京时间 10 月 25 日至 11 月 1 日 08:00。检索核验截止：2026-11-01 00:18 UTC。仅标日期的博客按页面日期筛选，不臆测上线时刻。最新已发表仍为 Week14；Week15、Week16 已文件交付但未上线，本期按这些稿件去重并保留 Week17 编号，不重复补发旧稿。

本周值得集中理解的是：优化改变数据位置或资源归属之后，谁仍有权修改它？Iceberg 文件整理要与并发删除协调；文件系统可以拆分主机与设备的持久化职责；推理服务回收 KV 页之前必须确认远端写入已经结束。这些不是同一个协议，却都要求为“下一步可以开始”提供明确证据。

新材料集中在 Iceberg 技术博客及 AI Infra 原文。存储会议部分为标明会期的 OSDI 旧论文补读；Fluss/JD 案例区分本周转载与原始首发。所有基准均为作者报告，本期未复现。正文不汇总 issue、PR 或项目开发进度，社区观察与 KIP 专题保持独立。

## 一 数据湖：更轻的读取表示，不能省掉并发正确性的代价

### Iceberg：删除向量解决读开销，却没有自动解决整理冲突

**本周新技术博客，10 月 29 日。** Starburst 工程师把问题从“哪种删除格式更快”推进到“持续更新时维护还能不能完成”：按键删除在文件整理后仍能定位同一逻辑行，按位置删除则依赖具体文件布局。作者描述 LakeOps 以分批应用删除、落本地中间结果的方式，拿额外 I/O 换受控内存；两个客户案例解释了维护压力，但不是 Flink 删除转换器基准，不能推出通用性能倍数。[原文](https://www.starburst.io/blog/equality-deletes-compaction-and-iceberg-v4/)

实现核验给出了这个差异的正确性基础。在博客固定引用的 Iceberg 代码中，重写验证在配置允许忽略 equality deletes 时，仍会拒绝作用于被替换文件的新 position delete；否则连新 equality delete 也要检查。这不是把全部并发写都放过，而是仅在相应序列号语义成立时，允许按键删除继续作用于替换数据。[固定版本验证代码](https://github.com/apache/iceberg/blob/60897e0b828580cc20e591424179d9b5c574e8d6/core/src/main/java/org/apache/iceberg/MergingSnapshotProducer.java)

可以用本文构造的例子理解：整理器把 A、B 重写成 X，期间更新器为 B 的第 7 行生成删除位图。即使 X 仍含同一业务记录，B 的位置 7 也不一定对应 X 的位置 7。只重试目录元数据提交不能修好这个映射；要重新定位，或者设计经过证明的映射修补路径。相反，按业务键表示的删除不直接依赖物理位置。这个例子是机制解释，不是本期复现实验。

**工程判断。** 对高更新 CDC 表，建议把验收改成固定写入速率下持续运行更新与整理，而不是分别测两个任务：记录成功整理字节、重复计算字节、目标快照落后时间及失败后的追赶速度。缩小重写组可以缩短冲突窗口，但也可能降低文件合并效率；统一锁可以排除重叠，却把维护时间转化为更新可见延迟。不能在没有长期负载实验时宣称任一策略总能稳定收敛。本期没有实施该实验。

### Iceberg V4 约束：写入承诺与快照事实必须分开

10 月 28 日 Alex Merced 的技术解读将主键能力分成“如何声明”和“是否已经证明”，这一问题比新增 DDL 名称更值得关注。[博客](https://alexmerced.blog/blog/2026-10-28-iceberg-v4-table-constraints)。本期另查官方规范：**V4 仍在开发、尚未正式采用**，不应把博客标题理解为所有引擎已提供可用功能。

规范把 enforced 与快照的 validated、valid、invalid、unvalidated 分开：前者约束新增或修改的行，不要求修复历史坏数据；后者说明这一快照的数据事实。重试换了父快照时，强制约束必须针对新结果重新成立，状态也须重算；未提供状态按 unvalidated 处理。旧 identifier fields 升级成未强制主键，不是自动获得唯一性证明。[官方规范：Constraints 与 Format Versioning](https://iceberg.apache.org/spec/)

**分析示例。** 两个写者都从同一无重复快照插入同一个业务键，各自的本地检查都可能通过。第一人提交后，第二人不能只更换元数据指针并沿用“已验证”的结论。因此性能评估需要同时报告成功写入和冲突重验成本。对使用多个引擎的团队，优先列出所有写入口、检查每个入口遇到不支持的 enforced 约束时会拒绝还是忽略，比先加一个“主键”标签更重要。这不是对当前所有产品行为的保证。

### Paimon 覆盖范围

本轮读取官方博客入口并定向检索作者技术文；找到 10 月 26 日关于 StarRocks/Paimon 多模态检索的演讲整理线索，但正文获取失败，因此不依据搜索摘要复述其机制或收益。官方 Rust 0.4.0 的 10 月 12 日发行说明属于旧材料，也不拿来充当本周机制研究。本节未确认可完整核验的新 Paimon 深文，不等于项目没有进展。[官方入口](https://paimon.apache.org/blog/) · [候选原文（本次未完整读取）](https://mirrorship.ai/en/blog/multimodal-retrieval-starrocks-paimon)


## 二 存储论文补读：拆开执行路径之前，先找出不能拆的恢复边界

本周没有核实到观察区间内新发表、又适合本栏目展开的存储顶会论文。以下是 **OSDI 2026（7 月 13–15 日）的补读，不是 10 月 25 日以来的新发布**：Oxbow 研究用户态、内核和计算存储设备如何分工；DeLFS 研究多核日志结构文件系统的元数据所有权。两篇均区别于前期 TensorDex/Prism、DINGO、LESS，也不重复 Week12–13 已展开的 AgileLog。覆盖不是全部会议的穷尽检索，不能据此断言本周没有新论文。[会议官方日程](https://www.usenix.org/conference/osdi26/technical-sessions)

### Oxbow：让 fsync 在主机上完成，但不要把“设备后台还没完成”变成恢复漏洞

全用户态能减少系统调用，但还需要缓存、权限和跨进程共享；把整个文件系统搬进计算 SSD，又会让较弱的设备 CPU 和 PCIe 往返进入请求关键路径。Oxbow 选择按操作分工：读路径利用内核页缓存，写路径由用户态处理，后台日志由设备侧承担。它的重要性在于拒绝把“绕过内核”当成非此即彼的架构选择，而不是声称每种操作都应该离开内核。[官方论文介绍](https://www.usenix.org/conference/osdi26/presentation/kim-jongyul)

真正的正确性约束在 Split Journaling：fsync 的数据和 inode 写入独立的持久 staging area，不等待后台 journal；若该文件仍有未提交修改，也一并重新记录，使 staging transaction 能独立恢复。它保存最近已提交 journal 的 ID，恢复时结合该前缀重建状态，再处理未被后台提交覆盖的 staging。数据先复制进 DMA snapshot，页锁只覆盖复制时段，不延伸到设备 I/O。因而“提前返回”来自提前建立另一份可恢复状态，而不是把持久性义务推迟。代价包括额外复制、重复日志和 staging 空间管理。[论文 §4.4–4.5](https://www.usenix.org/system/files/osdi26-kim-jongyul.pdf)

实验边界尤其值得保留：作者用 BlueField-2 DPU 与支持 SR-IOV/namespace sharing 的 SSD 模拟计算存储设备，并非商用计算 SSD 全系列测试。主机模式也能运行，但设备工作回到主机，不能拿它证明卸载节约 CPU。[作者实现与硬件要求](https://github.com/xlab-uiuc/oxbow)。AE 文档进一步说明，虚拟机模式的 D-Server 使用另一块虚拟 SSD，checkpoint 需要跨两块盘复制；它适合功能探索，不等价于论文测试床。[实验说明](https://github.com/xlab-uiuc/oxbow/blob/osdi26-ae/Documentation/artifact-evaluation.md)

论文中的收益也不是一条可套用的倍数：例如单进程反复写 4 GB tensor 并 fsync 的五轮 checkpoint 模型，报告吞吐比 Ext4 高 58%；同文却报告某个八进程、缓存命中为主的 LevelDB YCSB D 场景比 µFS 慢 20%。这说明保留内核服务与用户态零拷贝各有适用区间。本文未运行作者实验，数字仅作原文条件下的证据，不能推演成完整训练任务加速。[论文 §6.4](https://www.usenix.org/system/files/osdi26-kim-jongyul.pdf)

对系统设计的启发是：先画出 ack/fsync 到故障恢复的证据链，再决定后台任务可移到哪里。把 journal worker 换成另一颗 CPU 本身并不解除依赖；只有恢复信息已自足，前台才有理由不等它。反过来，若压缩、合并或 checkpoint 产生的新布局仍是唯一可恢复副本，就不能只凭“后台异步”缩短确认路径。这是阅读后的分析，不是论文对其他系统的实测结论。

### DeLFS：拆掉全局锁之后，还要解释旧块何时才能真正失效

DeLFS 关注另一种瓶颈：页缓存刷新可以并行，不代表 LFS 的当前 segment、块有效性与提交元数据也能并行。它把资源划到 per-core 域，并把部分跨域更新解耦；目标是减少正常写入和垃圾回收对集中式管理的争用，而非只增加 GC 线程。作者在 128 核机器上观察到显著写吞吐收益，但读路径本已接近设备上限，不应预期同样提升。[官方论文介绍](https://www.usenix.org/conference/osdi26/presentation/ahn)

关键不是简单把 mutex 换成数组。覆盖写需要把新块置为有效，并使旧块失效；若每个核持有自己的锁再拿别人的锁，可能互相等待。DeLFS 将同类跨域锁的更新拆开，并进一步把远端旧块失效委托给对应核：先保证新块有效、节点指向它，旧块可暂时仍被标为有效；checkpoint 提交前必须完成这些延期任务。暂时多保留一块和提前释放仍被引用的一块，安全性完全不同。[论文 §4.4–4.6](https://www.usenix.org/system/files/osdi26-ahn.pdf)

它也没有消灭空间压力：原文 fileserver 在仅剩 1% 空间时，与 F2FS 的表现已经近似；按核本地选 GC victim 可能偏离全局最优。论文给出的一个 GC 实验中，总写放大从 1.088 到 1.101。用局部性换并行不是免费的，不能把该实验的小幅差值当作所有倾斜负载下的保证。[论文 §5.2、§5.6](https://www.usenix.org/system/files/osdi26-ahn.pdf)

复现也要区分来源：作者仓库提供 Linux 6.6.8、不同对照文件系统、FIO/Filebench/RocksDB 脚本和 CrashMonkey 目录；但仓库安装示例写 Intel SSD，而论文测试床列的是 FireCuda 530。选择测试设备时应以要复现的具体实验为准，不混用 README 环境和论文结果。作者提供可运行材料不等于本文已经验证崩溃一致性。[实现与测试入口](https://github.com/syslab-CAU/DeLFS)

两篇放在一起看，值得借鉴的是同一个分析顺序：先区分“必须在确认前完成的工作”和“可以延期、但必须在下一恢复边界前完成的工作”，再讨论多核、用户态或设备卸载。评审一个类似设计时，应追问延期队列是否有界、空间耗尽会把哪些操作重新串行化、故障恢复如何发现未完成工作。这比把两篇概括成“异步化提升性能”更接近可复用的设计方法。

## 三 流系统：湖内提交成功，还需要把流湖边界变成可恢复状态

### JD 的 Fluss/Hudi 案例：新转载，旧实践补读

**日期必须拆开。** Fluss 官方页面发布于 10 月 25 日，但其明确链接的 Hudi 首发为 10 月 14 日；本期是新增转载带来的补读，不把生产实践发生时间推断为本周。[Fluss 转载](https://fluss.apache.org/blog/how-jd-built-a-lakestream-with-fluss-and-hudi/) · [Hudi 首发](https://hudi.apache.org/blog/2026/10/14/how-jd-built-a-lakestream-with-fluss-and-hudi/)

作者描述将新鲜数据留在 Fluss、历史落入 Hudi，统一推荐训练的数据来源。每轮分层使用同一 Hudi instant，并在提交后回报对应 Fluss bucket offsets。它减少的是重复处理路径，而不是把“两份物理介质”魔法变为一个原子事务。案例声称批计算成本降低超过 80%、存储成本超过 50%、训练数据鲜度改善超过 30%；没有公开可复现配置、逐项成本分解或 A/B 统计细节，本期不将其当作通用产品基准，也不能据此认定所有企业定制功能都已成为上游发布能力。[案例原文](https://hudi.apache.org/blog/2026/10/14/how-jd-built-a-lakestream-with-fluss-and-hudi/)

**本文分析：真正该追问的是两个提交之间的空隙。** 面向自己的分层系统，至少要枚举三种状态：湖表尚未提交、湖表已经提交但流端尚未收到进度、两端都已确认。第二种不能简单从旧 offset 再写一遍后就认为安全，也不能仅凭流端未收到通知判定湖中没有数据。恢复协议需要能从持久化元数据识别同一轮结果，再决定补报还是重做。本文是在提出设计审查问题，未声称该博客已经证明了所有崩溃窗口。

同样，统一查询还应回答：湖快照与流端尾部使用哪个稳定切点，分层落后时热数据保留多久，读者拿旧快照时是否仍可访问所需流数据。这些条件决定无遗漏、无重复是否能在故障和延迟下成立。可采用一个未执行的验证方案：在湖提交后、进度回报前注入故障，以已知事件编号比对恢复后 union read，再让落后读者跨过一次热数据清理。成本测试应随后加入恢复期间的额外 I/O 和重复写入，不能只比较正常态存储账单。

本轮同时检查 Kafka 官方博客和 AutoMQ 官方博客入口，未确认窗口内可全文核验、且不与既有报告重复的机制深文；不以版本公告、issue 或 PR 动态补位。[Kafka 博客](https://kafka.apache.org/blog/) · [AutoMQ 博客](https://www.automq.com/blog)

## 四 AI Infra：复用之前，先证明状态仍然有效

本周选取 10 月 26 日的两篇披露/论文与 10 月 29 日的训练系统博客。它们分别回答 KV 状态何时安全回收、保留什么最划算，以及训练流水线为什么等不到有效样本。它们不是上期弹性专家并行和前期双向 KV 传输的重复报道。以下性能均来自作者实验，本次未复现；论文只按预印本介绍，不暗示会议接收。

### 1. SGLang：请求结束，不等于远端写入已经结束

10 月 26 日 Cloudflare 公开了先前生产事件：GLM-5.3 的配置上下文大于 prefill KV 池，超容量请求虽被标记拒绝，仍通过 P/D 交接；占位输入没有覆盖完整目标页，decode 却继续读取旧内容。Cloudflare 报告影响发生在 8 月 27 日至 9 月 9 日，共识别 155 个受影响响应，并明确未发现其他 Workers AI 模型受影响。**本周新增的是公开技术复盘，不是本周才发生事故。**容量配平能阻断触发条件，但正确拒绝还必须发生在 bootstrap、分配和传输之前。[Cloudflare 原文，10 月 26 日](https://blog.cloudflare.com/kv-cache-exposure-remediation/)

配套的 SGLang 博客解释了另一种相关、但不能与上述事故混为一谈的失效：请求 abort 后，已经交给 NIC 的 RDMA 操作仍可能落地；立即回收目标页，会让旧请求覆盖新请求。方案是通知发送端停止后续工作，隔离请求占用的页，并等待所有相关 rank 排空确认；失败调用不能冒充已排空。超时释放只是有限等待的后备路径，**超时本身不是远端已停止写入的证明**。校验和只能检测部分损坏，也不能代替生命周期约束。[SGLang 技术说明，10 月 26 日](https://www.lmsys.org/blog/2026-10-26-cf-security)

代价是异常风暴时被隔离页暂时不能服务新请求。作者的 2×H100、1P1D 测试中正常吞吐变化在 ±2% 内，置信区间跨零；不能据此宣称高 abort 率、超长上下文也无代价。本文的设计判断是：取消传播、数据排空、内存复用应分别建模，不能共用一个“请求已完成”布尔量。对存储系统读者，这类似于异步 I/O 返回失败后，仍必须确认设备或远端不再持有可写引用。

### 2. WAKMan：缓存策略应由访问轨迹检验，而不是先猜业务类型

10 月 26 日发布的 [WAKMan 原文](https://arxiv.org/html/2610.36355v1) 用同一批 block hash 轨迹模拟 LRU 和 S3FIFO，每 15 分钟选择上一窗口命中率更高者用于下一窗口，不读取 prompt 或依赖请求类型标签。短间隔 agent 回合偏向近期性，长间隔对话和热门固定前缀更需要抗一次性扫描污染；因此没有一个静态策略在所有混合流量中占优。

实验在四张 RTX PRO 6000 Blackwell 上运行 Gemma-4-26B-A4B/vLLM，使用合成请求，报告平均命中率比 LRU 高约 **5 个百分点**。这里不是吞吐提升 5%，更不是生产流量结论。纯多轮负载中，动态策略命中率 15.0%，仍低于静态 S3FIFO 的 26.0%；初始 LRU 与十五分钟决策窗口付出了明显冷启动代价。作者还承认回放、切换和突变流量可能抵消收益。

这项工作的可迁移价值是把策略比较移到旁路，而不是把预测模型塞进每次淘汰路径。本文推断，实际落地还应记录估计开销、端到端首 token 延迟和切换期间的容量变化：只提高命中率，不足以证明服务收益。租户隔离也不能因“只记录 hash”而被忽略，跨租户共享前缀仍可能暴露命中时延信号。它与 KV 压缩的分工不同：这里选择保留哪些完整块，不改变保留块的数值精度。

### 3. Miles：GPU 等待的可能是沙箱与长尾，而非算子

[AMD 与 Miles 团队 10 月 29 日博客](https://www.lmsys.org/blog/2026-10-22-miles-mi355x-agentic-rl)将 rollout 与训练分开，Harbor 管理执行测试的 CPU 沙箱，Miles 向 Megatron 提供已完成轨迹并向 SGLang 更新权重。原文 URL 含 10 月 22 日，但正文署名日期是 10 月 29 日，本期按正文日期归档。上下文和轨迹上限避免少数失败任务长期占住 KV；沙箱并发、镜像获取和连接池也进入关键路径。

证据必须拆开读：约 860→3480 trajectories/hour 同时包含推理从一个扩至三个八卡 MI355X 节点、云沙箱和并发整改，不能称固定硬件软件优化四倍；850→284 秒的步时改善才是同一八卡推理节点上的长度约束比较。7.3%→27.5% pass@1 使用 SWE-bench Verified 的 100 题分层子集、每题四次尝试，不是完整 500 题榜单。以上均为作者报告。

本文认为，最值得复用的是把“基础设施失败”从模型失败中分离：如果沙箱起不来或网络请求失败也被记成零奖励，系统故障会污染学习信号。异步流水线降低等待，但还应分别观察样本新鲜度、完成率、奖励有效性及每单位硬件产出的有效样本。单看 GPU 利用率或完成轨迹数，容易把更多失败尝试误认成训练加速。

这三项工作的共同趋势并不是缓存越多越好或并发越高越好，而是为资源状态增加可检查的证据：何时允许复用、何种轨迹支持保留、哪个样本值得进入更新。后续评估应把性能与异常路径一起测量，而不只报告正常请求的平均吞吐。


## 本期综合判断与下一步

按机制比较，这些系统可以用三个不同的审查问题串起来。第一，验证是否绑定到了仍然有效的对象：旧文件位置不能直接套到新文件，旧快照上的约束证明不能直接套到新父快照。第二，完成通知究竟承诺了什么：调用者不再等待，不代表设备或远端没有继续执行的工作。第三，性能分母是否变了：新增 GPU、缓存命中、设备内持久化和故障恢复分别消耗不同资源，不能把各处的最好数字拼成一条端到端结论。

这些是本文基于原文提出的系统设计判断，不是已经统一实现的架构。若进一步实验，可优先选择一个能明确制造故障窗口的原型：让文件整理与更新重叠，或在远端传输未排空时取消请求；先证明没有数据遗漏、重复或跨请求污染，再测吞吐和尾延迟。稳定状态下的微基准只能回答其中一部分问题。

来源与检索范围随本期来源索引保存。未取得的原文不用于机制或性能断言；未核验到本周新文不等于相应项目没有进展。
