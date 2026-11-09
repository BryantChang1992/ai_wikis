---
type: survey
title: 技术调研周报 Week 16：关系索引、恢复契约与在线变更的真实成本
sources:
- https://arxiv.org/html/2610.25131v1
- https://lakeops.dev/blog/iceberg-merge-into-performance
- https://lakeops.dev/blog/real-time-lakehouse-guide
- https://arxiv.org/abs/2604.17104
- https://arxiv.org/pdf/2604.17104v2
- https://arxiv.org/pdf/2604.17104v3
- https://sigops.org/s/conferences/sosp/2026/schedule.html
- https://dassl-uiuc.github.io/pdfs/papers/prism.pdf
- https://fluss.apache.org/blog/tracing-job-retries/
- https://vllm-project.github.io/2026/10/19/elastic-ep-near-zero-downtime.html
- https://arxiv.org/abs/2610.28223
- https://arxiv.org/html/2610.28223v1
tags:
- 数据湖
- Iceberg
- Fluss
- 分布式存储
- AI Infra
- vLLM
created: '2026-11-09'
updated: '2026-11-09'
status: draft
publication_status: github_archive
publication_scope: 仅 GitHub 正文归档；GitHub Pages、知识卡及双库同步暂缓。
report_date: '2026-10-25'
issue: 16
issue_date: '2026-10-25'
observation_start: '2026-10-18T00:00:00Z'
observation_end: '2026-10-25T00:00:00Z'
source_checked: '2026-10-25'
source_check_scope: 沿用原报告的原文核验日期与范围；本次仅归档，未重新核读全部外部来源。
related:
- '[[知识库/sources/web/technical-trends-week16/来源索引]]'
---

# 技术调研周报 Week 16：关系索引、恢复契约与在线变更的真实成本

> 归档范围：本页保存 2026-10-25 的 Week 16 报告完整正文及公开引用，仅供 GitHub 阅读；不进行 GitHub Pages、知识卡或双库同步。目录名称不代表已完成博客同步。正文中的“本周”“未发布”等状态均保留原观察时点语境，不代表归档日最新状态。原文核验截止：2026-10-25 00:17 UTC。

[公开来源索引](../../知识库/sources/web/technical-trends-week16/来源索引.md)

观察区间：以 2026 年 10 月 18 日 08:00 至 10 月 25 日 08:00（北京时间，UTC 10 月 18 日 00:00 至 25 日 00:00）为主；自最新已发表 Week 14（10 月 11 日）以来的必要补查单列。检索核验截止：2026 年 10 月 25 日 00:17 UTC（北京时间 08:17）。只标日期、没有时区的博客按页面日期筛选，不推测精确上线时刻。Week 15 已交付但尚未公开发布，本期保留 Week 16 编号，不覆盖或重发其内容。

本期更值得留意的变化，是系统开始把过去隐藏在实现里的成本变成显式契约：数据湖要告诉 Agent 表之间有什么关系，故障恢复要向外部系统确认副作用，推理扩容要分别报告准备时间与服务停顿。存储论文也提示我们，压缩比、解码带宽和冷加载速度并不等价，共享内存的高性能更不能自动推出可恢复性。

本周新增材料包括 Data.Readme 预印本、Iceberg 运维技术博客、Fluss 外部副作用恢复示例、vLLM 弹性专家并行博客及单用户推理剖析。存储顶会部分明确为旧论文／修订补读。所有测量都是作者报告，本期没有独立复现；分析和建议不视为上游已实现能力。这里不汇总 issue、PR、投票或开发状态，这些由独立专题承担。

## 一 数据湖：把结构关系和维护代价暴露出来

### Data.Readme：让数据湖向 Agent 暴露关系，而不只是表名

**本周新论文，2026-10-18，arXiv v1。** 系统离线记录易混淆、可连接、可合并三类表关系；连接候选经向量召回、键值包含检查、实际连接抽样验证，仍有歧义则留到查询时。Agent 按需检索并沿关系跳转，避免每道题重新摸索整个湖。[论文全文](https://arxiv.org/html/2610.25131v1)

**证据。** 在扩增湖的 BIRD NL2SQL、GPT-5.4 设置中，Data.Readme 得分 43.8%，单表说明基线 AutoDDG 为 31.1%，不限轮次的 Copilot CLI 为 26.9%。这比只引用“最高提升40个百分点”更能说明比较对象。[表3](https://arxiv.org/html/2610.25131v1)

**边界与启示。** 原始湖由公开基准拼接出4,127表；12,829表版本含合成聚合与水平分区，主实验限制4轮交互，另做不限轮次比较。因此结果不是企业生产湖的保证，也不是 Iceberg/Paimon 格式升级。值得迁移的是把关系解释作为可复用索引；落地仍须验证更新成本、错误关系及权限隔离，不能把推断连接当作已声明外键。[实验设置](https://arxiv.org/html/2610.25131v1)

### Iceberg 的实时性，开始从写入频率转向“可持续的查询鲜度”

**本周新文，2026-10-22／10-18；厂商技术博客，不是新算法或性能基准。** LakeOps 的两篇深文可以合读：MERGE 的成本应按“触碰多少目标文件”而非“改变多少行”衡量；实时性则要把提交、引擎看到快照、查询返回三个阶段一起计时。[MERGE INTO 深文](https://lakeops.dev/blog/iceberg-merge-into-performance)；[实时湖仓深文](https://lakeops.dev/blog/real-time-lakehouse-guide)。

**机制与取舍。** Copy-on-write 改少数行也可能重写整文件；merge-on-read 缩短本次写入，却把删除应用推给读者和后续整理。故应先看复制行／变更行、每次新增删除文件，以及热点分区碎片，而不是直接扩容。分区裁剪缩小范围，按键聚簇缩窄文件统计区间；但为 MERGE 排序可能伤害其他查询，声明新排序也不会自动重排旧文件。[来源](https://lakeops.dev/blog/iceberg-merge-into-performance)

**为什么值得关注。** 高频提交不断产生小文件与元数据，刚写入的热分区往往也是主要读取对象。维护不应只是夜间清理：按实际积压触发小批整理，避免与在线写入争抢同一组文件；快照保留期要覆盖落后消费者的恢复需要，孤儿文件清理不能误删尚未提交的在途文件。[来源](https://lakeops.dev/blog/real-time-lakehouse-guide)

**判断与边界。** 这两篇提供了可测指标与操作机制，没有给出足以支持通用加速倍数的可复现实验，不能把导航栏营销数字当成结论。建议验证的是：固定到达率和查询组合，长期观察“事件到答案”尾延迟、整理积压、冲突重试及总成本是否稳定。另一个正确性检查是：给 MERGE 的 ON 增加时间范围前，必须证明范围外不会存在应匹配的旧记录，否则优化可能改变业务语义。这是本文分析，而非原文完成的实验证明。


### 从原文到工程评估：先证明索引和裁剪没有改变问题

两组材料分别解决“选哪张表”和“读写哪些文件”，都把工作提前到了可复用的元数据层，但不能用同一把尺子验收。表关系索引的错误会把查询引向语义不对的数据；文件裁剪的错误则可能漏掉本来应参与更新的记录。前者应保留候选与证据供查询时核验，后者需要可证明的谓词覆盖关系。

下面是本文提出的评估例子，并非论文实验：对一组每天追加并偶尔回补旧订单的湖表，先固定查询题集和回补数据，分别测表发现准确率与 MERGE 触碰文件数。然后加入同名、不同口径的派生表，以及跨分区回补，观察优化是否仍返回正确答案。这样才能分清“更少探索、更少重写”和“错误地排除了应处理的数据”。离线构建关系与重排数据的成本也应计入，不能只报告热路径改善。

Paimon 本轮检查了官方博客和定向论文检索，找到的同期发行或功能公告不作为机制长文补位；这意味着本节覆盖有限，而不是 Paimon 没有进展。

## 二 存储顶会：单项最优不能替代端到端路径
本轮核查 FAST、OSDI、SOSP 官方议程、PVLDB Vol.20 页面及相关 SIGMOD／ATC 检索，未确认 10 月 18–24 日内新增且可全文核验的合适论文；PVLDB 页面可读范围有限，不能把这个结果当作全量结论。以下两项均明确标注补读。

### TensorDex：逐 tensor 配对，仍要付冷恢复的账

SOSP 2026 论文 TensorDex 的 arXiv v3 于 10 月 15 日修订，初稿为 4 月 18 日。对读 v2/v3 后可确认，新版补入 S3/EBS 的实际取回测量；旧版相关表只测内存 codec。这是距最新已发表周报以来的修订补查，不是本周新论文。[版本与全文](https://arxiv.org/abs/2604.17104) · [v2](https://arxiv.org/pdf/2604.17104v2) · [v3](https://arxiv.org/pdf/2604.17104v3)

系统先精确去重，再用 TensorSketch 为每个 tensor 找相似基底，预测 delta 收益并计入完整基底成本；FlexSplit 局部重组，保持一跳 base＋delta 恢复。§6 的 70.5% 节省来自 FM++、以去重后容量为分母；28.4 GB/s 则来自 TX、192 线程的 DRAM 实验，不能合并成一个配置。更关键的 Table 4：64 并发 S3 I/O 下，冷恢复 2.83 GB/s，低于未压缩的 3.43；base 热后才到 4.10。删除仍被引用的 base 还涉及离线重编码。[机制及 Tables 1/3/4](https://arxiv.org/pdf/2604.17104v3)

本文判断：模型仓库选布局时，应该把容量、基底热度和删除频率同时放进成本函数。可以设置一个不带作者收益假设的验收方案：同一组模型分别冷启动一次、重复启动多次、删除热门祖先后再启动；记录下载量、恢复时间、CPU 和维护时间。若只在稳态热缓存中验收，就可能把节省容量换来的首次加载罚时藏起来。这个实验尚未执行，不能从论文数字推导出任意模型服务的启动收益。

### Prism：不可变布局节省一致性预算，但还不是持久数据库

*Disk-Based LSMs: An Unexpectedly Good Index for Partly Coherent CXL Memory* 属 SOSP 2026（9 月 29 日至 10 月 2 日），本节是旧文补读，没有将其认定为本周新增。[正式议程](https://sigops.org/s/conferences/sosp/2026/schedule.html) · [作者全文](https://dassl-uiuc.github.io/pdfs/papers/prism.pdf)

Prism 针对小块硬件一致共享区 SCR 与大块非跨主机一致区域 LNR：用 memtable 缓存热点写、受限可变 BUL 吸收更新，其余放不可变 SSTable，以控制需追踪版本的状态。默认 1 亿 KV、Zipf 0.99、SCR 128 MB 的 YCSB-A/F，作者报告对 SC-BTree 吞吐 7.4×/9.4×；纯读优势很小，部分低倾斜 trace 不占优。测试用 NUMA 模拟 CXL，并非真实多主机 CXL 实测；§5.7 明确任一主机或设备失败即整体停机，没有恢复，持久性不在范围。[§3–7](https://dassl-uiuc.github.io/pdfs/papers/prism.pdf)

本文判断：值得借鉴的是围绕稀缺的一致性预算控制可变状态，而不是把“磁盘结构也能用于内存”当作万能选型结论。若业务需要写后确认持久化，至少要补上日志落点、故障域、恢复和地址复用的完整论证，再测其成本。一个无恢复原型的正常态吞吐，不能替带复制与持久性要求的生产 KV 做容量估算。与 TensorDex 相比，两者都改变了组织粒度，但前者的存储 I/O 证据和后者的硬件模拟证据处在不同层次，不能统称生产就绪。

## 三 流系统：把可回放与可安全重试分开

### Fluss：日志不能独自证明外部副作用是否发生

**来源与日期：**[Crash-safe retries for side-effecting workers with Apache Fluss](https://fluss.apache.org/blog/tracing-job-retries/)，Apache Fluss 官方博客，2026-10-20，Tejesh Vaish。

**问题与机制：**同一段日志只有 ACTION_REQUESTED、没有确认，既可能表示请求尚未发出，也可能表示服务已提交、worker 来不及记账。示例先持久化完整请求及摘要，跨重启保持 action_id；恢复时向下游查询权威回执。下游把效果与回执原子提交，并绑定请求内容：查到原回执就补记确认，权威确认不存在才重发；普通 404、认证失败或不确定结果一律暂停。Fluss Log Table 负责恢复历史，PK 投影供查询，不能替外部服务证明提交。

**证据与边界：**Fluss 1.0.0 合成工单实验通过 7 个核心用例、344 项断言。测试范围是 worker 进程被杀，Fluss 与 SQLite 服务仍运行；单 worker、单 bucket、恢复期间停止全部写入。它没有证明主机丢失、多副本故障或通用外部 exactly-once，也没有吞吐提升数据。

**我们的解读：**这是恢复契约范例，不是 Fluss 自动提供事务工作流的新能力。设计评审应把日志保留、owner fencing、回执有效期及下游幂等语义一起验收；仅增加 event sourcing 或 PK 表，不会关闭“调用成功但记账失败”的窗口。


### 恢复协议必须能够承认“不知道”

一个简化推演是：worker 已把请求写入日志，外部工单服务完成创建，随后 worker 在写确认前退出。重启后再次看到同一请求，只能证明它曾打算执行，不能证明外部世界没有变化。若恢复程序把任何查不到回执都当成未执行，一次鉴权故障、读副本延迟或回执过期就可能触发重复效果。正确的接口应能区分“权威确认不存在”“查到既有结果”“目前无法判定”，并为第三种情况保留人工或稍后对账出口。这是对原文契约的工程解释，不是新的完整分布式事务协议。

与前期湖表提交不确定性相比，共同问题是响应丢失后的结果歧义；不同点在于这次副作用跨越日志系统与外部服务。Fluss 的持久化、下游原子回执、恢复期间的写入约束必须共同成立。换成多 worker 后还需要论证谁有权重试及如何隔离旧 owner，不能仅把串行样例加线程就声称保留原保证。

Kafka 本轮官方博客未查到窗口内值得展开的新技术主文；AutoMQ 定向检索未形成比前期已读历史回放与安全边界更强的新增证据，因此不重复刊登 10 月 11 日文章。Fluss 本节只讨论公开博客的恢复实验，不重复流湖交接背景或社区开发动态。

## 四 AI Infra：优化的单位从算子速度扩展到生命周期

### 本周主读｜Elastic EP：保住 CUDA graph，才真正缩短扩缩容停顿

**来源与日期：**[Achieving near-zero-downtime scaling in Elastic Expert Parallelism](https://vllm-project.github.io/2026/10/19/elastic-ep-near-zero-downtime.html)，vLLM 官方博客，2026-10-19，Itay Alroy（NVIDIA）。

**机制：**扩容拆成后台 prepare 与短 commit。旧 worker 继续服务，新 worker 接收权重并独立 warmup/capture。NIXL EP 原地改变成员，保持 graph 可见的地址、参数及 launch 配置稳定；成员状态和专家映射原地更新，避免旧 worker 全量 recapture。新增 worker 准备时屏蔽远端 peer，避免阻塞正在服务的通信组。

**证据：**DeepSeek V4 Pro，GB200，TP=1，DP/EP 16↔20，使用预下载权重及热编译缓存：扩容停顿由 99.62 秒降至 0.82 秒，缩容由 56.25 秒降至 1.96 秒。但扩容总耗时仍是 92.34 秒，不能写成“0.82 秒完成扩容”。负载实验完成 11,391 个请求，滚动 p95 TTFT 保持低于 5 秒。

**边界与解读：**这是特定配置、作者自报结果，不是任意 MoE/互连的保证；失败请求在图中被计入 30 秒惩罚。缩短 interruption 与缩短 capacity-ready time 是不同目标，调度器仍须提前触发扩容。Dynamo/llm-d 自动扩缩容集成在文章中仍是后续工作，不能写成已具备完整生产闭环。

### 本周论文｜长上下文单用户推理：显存紧张不等于 GPU 已吃满

**来源与日期：**[Local Inference of LLMs on Long Contexts: A Data Systems Perspective](https://arxiv.org/abs/2610.28223)，Mattias Dürrmeier、Alberto Lerner，arXiv v1，2026-10-20 13:56:12 UTC；[全文](https://arxiv.org/html/2610.28223v1)。

**方法与发现：**作者对单 decoder block 做冷缓存、逐 kernel 的 decode profiling，覆盖 GPT 系列、Qwen3 4B/8B/32B 及 Turing、Ada、Blackwell 三代工作站 GPU。长上下文中 attention 主导耗时，却不必耗尽带宽或算力：Qwen3-8B 在 Blackwell 的长上下文 attention 带宽利用率只有约 21%。batch=1、head 数有限，使 kernel 暴露的并行度不足。

**方向与权衡：**沿 KV 序列切分增加并行度；合并小 kernel、减少同步；利用 attention 的带宽空档预取后续层 KV。但 attention 越快，可隐藏传输的时间窗越短，不能把“更快计算”和“免费 offload”收益直接相加。

**边界与解读：**这是预印本性能剖析，不是新 serving 引擎的端到端加速证明。单 block 刻意排除了整模型容量问题，部分测量延伸到超过模型支持长度的百万 token，不能视为实际长上下文质量验证。“无损分页可取代压缩”仍是研究方向。实践中应先比较真实 batch=1 的 attention backend 与 TPOT，再决定量化、换卡或 offload。


## 本期的三个工程判断

第一，优化效果要跟着路径走。湖表文件裁剪、模型冷加载、batch=1 decode 和扩容准备的瓶颈可能完全不同；一个层次的高吞吐不应跨层借用。第二，正确性边界要跟着故障走。共享内存、持久日志和外部回执各自解决不同一段问题，组合时缺失的一段不能用产品名称补齐。第三，把准备成本和在线成本分开报告，会比只展示最好数字更接近容量规划的需要。

下一轮值得继续追踪的是两个可验证问题：关系索引怎样在频繁更新且存在权限边界的数据湖里保持新鲜；异步扩容怎样在突发负载到来之前完成准备，同时证明 prepare 失败和 commit 失败都能安全退回。这里提出的是研究与实验问题，不是新增任务或已完成验证。

## 来源、范围与阅读深度

正文链接均指向作者、项目、厂商或正式论文原文；技术解释基于完整正文及关键实验章节。两篇 arXiv 新文称为预印本，不根据排版模板认定会议录用；LakeOps 属厂商技术博客，不是 Apache 发布声明。TensorDex 和 Prism 的时间与证据条件见存储章节。详细逐项来源、检索范围及重复项处置另见随附来源索引。

已对照 Week 14 全文和 Week 15 待发布稿：本期不重述 virtual Parquet、Fluss lake bridge、DINGO、AutoMQ 历史回放依赖，以及双向／push KV transfer。既有知识库卡片是导航，不计为与原文相独立的支持证据。全文不包含私有训练资料或内部问答，也不附未经许可的论文全文转载。
