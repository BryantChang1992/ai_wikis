---
title: 技术调研周报 Week 14：兼容读路径、流湖交接与数据搬运成本
type: survey
created: '2026-10-11'
tags:
- 数据湖
- Parquet
- Fluss
- 分布式存储
- AI Infra
- vLLM
blog_url: https://bryantchang1992.github.io/ai_memory_chang_ai_team/posts/tech-research/week-14/
blog_source: _posts/2026-10-11-tech-research-week-14.md
blog_source_commit: 57eb988393c53e0f64ef3dd1d850e9434e7b7449
blog_body_sha256: adfdc64e1b8eccfb08d60f2235783d731bd8f78afd76377b52b4f82b1fea69d0
synced_at: '2026-10-11'
issue: 14
issue_date: '2026-10-11'
observation_start: '2026-10-04T08:00:00+08:00'
observation_end: '2026-10-11T08:00:00+08:00'
related:
- '[[知识库/wiki/虚拟Parquet-固定布局与按需转码]]'
- '[[知识库/wiki/流湖交接-快照进度与Freshness边界]]'
- '[[知识库/wiki/纠删恢复-读取量与寻道共同优化]]'
- '[[知识库/wiki/SWA缓存-有界重算与图捕获开销]]'
- '[[知识库/wiki/synthesis/读路径优化的四种边界]]'
---

观察窗口：2026 年 10 月 4 日 08:00 至 10 月 11 日 08:00（北京时间）。原文检索与核验日期：10 月 11 日。

本周可展开的新材料集中在 Fluss 与 vLLM 的作者技术博客；数据湖和分布式存储选取两篇明确标注日期的论文补读。四组材料都涉及数据如何被读取、转换或搬运：开放接口能否兼容新布局，流与湖怎样衔接进度，纠删恢复如何兼顾读取量和寻道，以及推理怎样减少重算与跨局部性域的权重访问。

本文只收录论文与原创技术博客，不重复社区 Issue、PR 和开发讨论；那部分继续在[流存储技术观察](https://bryantchang1992.github.io/ai_memory_chang_ai_team/stream-storage-observer/)维护。作者的性能数据与本文建议的验证步骤分开表述，所有基准均未独立复现。

## 一 数据湖：把兼容接口与物理文件拆开
{: #lakehouse }

**旧文补读。** 本节选读 Pascal Ginter、Viktor Leis 的《Active Data Lakes: Regaining Physical Data Independence Without Losing Interoperability》。正式论文刊于 PVLDB 19(6)，官方刊头标注 **2026 年 2 月**，并列入 VLDB 2026 议程；本轮于 10 月 11 日核验，不属于本周新发表成果。它为 Iceberg 等开放表格式提供兼容读路径的研究参考，不表示 Iceberg 或 Paimon 已实现该架构。[正式论文](https://www.vldb.org/pvldb/vol19/p1372-ginter.pdf) · [刊期](https://www.vldb.org/pvldb/vol19/FrontMatterVol19No6.pdf)

### 让旧引擎继续读取，并给存储留下演进空间

一个值得反复追问的问题是：开放格式解决了多引擎读同一份数据，是否也让更换底层格式变得容易？假设新引擎采用更快的编码，而旧引擎只认识 Parquet，只要让旧引擎直接读取新文件，兼容性就会中断。要求所有读者同时升级，可能比实现新格式本身更困难。

论文在查询引擎与持久存储之间加入主动服务：内部可以保存 BtrBlocks，向只支持 Parquet 的引擎提供按需生成的虚拟 Parquet；支持原生格式的引擎则走另一条接口。核心是让“线上传输什么”不再完全等于“磁盘保存什么”，而不是多存一份完整的 Parquet 副本。[论文 §3–4](https://www.vldb.org/pvldb/vol19/p1372-ginter.pdf#page=3)

真正的技术约束来自随机范围读取。引擎往往先取 footer，再按其中的偏移请求列块；服务端必须在转码前算出虚拟文件的位置。原型因此采用大小可预测的编码，放弃通用压缩及许多编码方式，保留可计算长度的字典和位打包。这用额外网络传输换取按需转换，避免为了答复一个小范围请求先转换整个文件。[论文 §4.2](https://www.vldb.org/pvldb/vol19/p1372-ginter.pdf#page=6)

### “接近原生”有严格的实验范围

图 5 使用 TPC-H **SF10 的 lineitem 全表扫描、DuckDB 1.2.1 单工作线程**；查询端与 HTTP 服务分别运行在 AWS 同一可用区的两台 c5n.9xlarge。数据先从 S3 读取时，虚拟 Parquet 比 Zstd Parquet 慢 **1.3%**；数据已在服务端内存时，则慢 **22%**。这两组结果必须一起看：对象存储 I/O 可以改变转码成本在总延迟中的占比。[论文 §4.3、图 5](https://www.vldb.org/pvldb/vol19/p1372-ginter.pdf#page=7)

文件小也不等于传输少：该例底层 BtrBlocks 为 **1.58 GiB**，启用字典后的虚拟读取需要传输 **4.3 GiB**。因此这里的证据是指定环境中的兼容性成本，并非通用查询加速，更不能把同文其他原型的吞吐结果套到这条读取路径上。论文分别评估三类优化，分布式系统的可扩展性与高可用仍列为后续工作。[论文 §4.3、§8.4](https://www.vldb.org/pvldb/vol19/p1372-ginter.pdf)

### 对湖存储评估的启发

本刊认为，这篇论文最有价值的地方是把迁移问题变成可测的接口问题：一个旧读者能否继续使用它原有的投影、范围读取和文件裁剪能力？新增服务的成本，应由减少的升级协调和存储成本来支付，不能只看一次扫描。

如果做小范围验证，可保留同一批数据与查询，分别测试冷数据、热数据、窄列扫描和并发读者；记录对象存储读取字节、服务端转码 CPU、返回字节及尾延迟。再单独测试服务重启、缓存失效和退回普通开放文件的流程。以上是依据架构提出的评估建议，本轮未执行实验，也没有用这些建议推导项目现有性能。

本周窗口内，已检索的 Iceberg/Paimon 来源尚未建立足以另写机制分析的新论文或原创技术长文证据；不以发行说明或开发讨论补齐篇幅，也不据此判断项目没有其他活动。

## 二 流存储：共享表的关键是进度能够衔接
{: #streaming }

**本周技术博客。** Fluss PMC 成员 Giannis Polyzos、Anton Borisov 于 **10 月 5 日**发表《The Streamhouse And Lakestream With Apache Fluss》。文章讨论怎样让多个计算和服务任务复用同一张逻辑表。本节据此提出问题，再用明确标注日期的旧文补足 tiering 机制；新文章的发表不等于其描述的全部能力都在本周新增。[作者原文](https://fluss.apache.org/blog/streamhouse-lakestream-fluss/)

### 同一张表，不代表两层数据可以直接拼接

文章把流层的新鲜数据和湖层的历史数据视为同一逻辑表的不同进度。读湖表得到已经提交的版本；支持联合读取的引擎，还需依据对应的流进度取得后续变化。主键表尤其不能直接把两侧结果拼起来：旧键可能刚被更新或删除。支持读取 Iceberg 或 Paimon 文件，也不自动意味着引擎具备流湖联合读取能力。[作者原文：读路径](https://fluss.apache.org/blog/streamhouse-lakestream-fluss/#how-metadata--tiering-coordinate-reads)

这里需要明确的还有写入责任。流湖协调依赖指定写入口、受管理的落湖过程与共享元数据；格式开放不等于任意引擎可以绕过它们修改湖表。业务计算仍由计算引擎负责，共享存储也不会自动提供所有索引或事务能力。文章的贡献是划清复用边界，没有提供可以量化“节省多少副本、快多少倍”的端到端实验。[作者原文：引擎协作](https://fluss.apache.org/blog/streamhouse-lakestream-fluss/#how-independent-engines-read--write-shared-tables)

### 补读：先落湖快照，再公布对应进度

**机制补读，发表于 6 月 4 日。** 同一作者的 tiering 长文把交接展开为可检查的顺序：Flink 作业在规划时固定各 bucket 的停止 offset，从上次湖进度读到本轮边界；完成文件写入后，将文件及各 bucket 的进度提交为湖快照，再把湖进度登记回 Fluss。仅看见对象文件，不能说明表提交已经完成。[原作者机制文](https://fluss.apache.org/blog/fluss-tiering-service-deep-dive-part1/)

可以用一个说明性例子理解：湖快照对应两个 bucket 的进度分别为 100、140，那么后续读取应从各自进度衔接，不能拿其中较大的 140 当成整张表的统一边界。这是本文举例，不是上游测试数据。

该文还区分完成通知与常规轮询：完成后立即触发 heartbeat，不必等待下一个周期；新尝试带有新 epoch，协调器据此忽略旧尝试的迟到成功报告。由此可见，数据文件、湖快照、Fluss 中登记的进度和任务完成状态，是需要分别观察的几个环节。[原作者机制文：完整轮次](https://fluss.apache.org/blog/fluss-tiering-service-deep-dive-part1/#a-complete-tiering-round-step-by-step)

### 补读：freshness 配置不是最大陈旧时间

**调优补读，发表于 6 月 9 日。** 作者说明，正常轮次完成后才重新等待 freshness 间隔；以单表、没有额外排队、轮次耗时稳定且未触发提前结束为前提，5 分钟配置加 90 秒处理时间，启动间隔约为 6.5 分钟。刚错过本轮截止位置的记录还要再等一轮，湖可见延迟可接近 8 分钟。这里是时序推导，不是压测结果或服务保证。[原作者调优文](https://fluss.apache.org/blog/fluss-tiering-service-deep-dive-part2/#the-freshness-knob)

两种情况会进一步改变模型：多表排队增加等待；主键表首轮读取已有 KV 快照时，为取得完整的增量衔接位置，不能像普通日志 split 一样按 freshness 提前结束。因而不能只缩短配置值，就宣称湖中数据更及时。[原作者调优文：边界](https://fluss.apache.org/blog/fluss-tiering-service-deep-dive-part2/#job-2-the-ceiling-on-a-rounds-wall-clock-duration)

本刊建议用同一条测试记录分别观测流层可见、湖快照可见和联合查询可见的时刻，再注入慢 bucket 与落湖作业重启。查询响应时间、数据陈旧程度和恢复后的结果一致性应该分别验收。本轮未运行这些实验。

Kafka、AutoMQ 在本节作为同领域检索对象，但本周没有纳入已核验的原创技术长文。已有的协调器分配、客户端修复和对象存储重试讨论留在独立专题中，不重复包装为本期研究材料。

## 三 分布式存储：纠删恢复要同时看读取量与寻道
{: #distributed-storage }

本节补读 FAST ’26 的 LESS，不将它计作本周新论文。论文收录于 2 月 24–26 日的会议，本周窗口内尚未核验到足够可靠、又不重复上期的存储论文新发表证据。[会议论文页](https://www.usenix.org/conference/fast26/presentation/cheng)

### LESS：少读一些数据，也要少做一些零散读取

恢复一个丢失的数据块，可以从其他节点读取编码片段，再计算出原内容。选择方案时，常先比较“需要读多少字节”；但对 HDD 存储，许多分散的小读取可能让磁头忙于定位。读取量最少的编码，未必拥有最短恢复时间。这也是评估存储系统时值得保留的一组指标：字节数反映搬运成本，I/O 次数与连续性反映服务这些字节的成本。

LESS 将每块切成少量子块，再把它们组织成相互重叠、使用 Reed–Solomon 编码的扩展子条带，使单块恢复可以在一个扩展子条带内完成。它保留 MDS 性质，并允许调整子块数量，在读取量与寻道之间取舍。论文表 2 的 (14,10)、LESS 每块四个子块配置给出如下对照。数值是作者对编码修复路径的比较，不是本刊测量。[论文 §3、表 2](https://www.usenix.org/system/files/fast26-cheng.pdf)

| 编码 | 平均读取量（折合块） | 平均寻道次数 |
|------|-------------:|-------------:|
| LESS | 4.64 | 13 |
| Clay | 3.25 | 286 |

这里的意义是给编码选择补上一条工程约束。将网络升级后的恢复任务放回原有磁盘上，链路可能已经有余量，磁盘的小 I/O 却仍然排队。反过来，换成 NVMe 以后，也不能继续沿用 HDD 上寻道主导的判断。相同的冗余比例只是比较的起点，介质、请求粒度和后台流量还会改变最好的参数。

### 性能数字来自什么条件

作者在 OpenEC/Hadoop 3.3.4 HDFS 上实现原型，使用 15 台 i5-7500、16 GiB 内存、7200 RPM SATA HDD 机器。交换机为 10 Gbps，默认将每节点网络限为 1 Gbps；配置为 (14,10)、64 MiB 块、256 KiB 包。每块四个子块时，LESS 的单块恢复时间比 RS 少 50.8%、比 Clay 少 33.9%。同配置单机内存实验的单线程编码吞吐则由 RS 的 2.8 GiB/s 降至 1.6 GiB/s。[论文 §4.2、图 4](https://www.usenix.org/system/files/fast26-cheng.pdf)

“整节点恢复”的实验只恢复该节点上来自不同条带的 20 个块；它提供了受控比较，不能用来估算装满数据的生产节点重建时长。编码变慢也意味着恢复收益需要与正常写入成本一起核算。本刊未独立复现上述实验。

若据此设计验证，可以先固定冗余比例、磁盘与包大小，再分别记录恢复字节数、I/O 数、编码 CPU、恢复时长，以及前台请求的尾延迟。第二步改变网络限速和恢复并发，观察瓶颈是否转移；第三步再扩展到完整节点数据量和业务并行读写。这样的实验能回答“节约的资源是否恰好是当前瓶颈”，比直接套用最佳百分比更有用。这些是本文建议的验证步骤，并非论文已完成的生产验收。

跟踪范围也继续包含 [ACM SIGOPS ATC ’26](https://sigops.org/s/conferences/atc/2026/)；不能用 USENIX 旧系列停办替代新会议信息。其 11 月会期不构成本周论文发表证据。

## 四 AI Infra：减少计算以后，启动与数据位置成为瓶颈
{: #ai-infra }

本周两篇 vLLM 作者技术博客适合放在一起读：10 月 7 日讲 DeepSeek-V4.1-Flash 的有界重放，10 月 9 日讲 Rubin 的内存局部性。前者减少必须执行的工作，后者改善权重读取；两者都说明，模型计算量下降以后，系统还要重新识别剩余瓶颈。[DeepSeek 技术文](https://vllm.ai/blog/2026-10-07-deepseek-v41-flash) · [Rubin 技术文](https://vllm.ai/blog/2026-10-09-vera-rubin-preview)

### 有界重放需要配合分段 CUDA Graph

DeepSeek-V4.1 的全局 KV 与滑动窗口 KV 有不同用途。前缀命中时，vLLM 只保留全局 KV，再重算末尾 128 个 token 的窗口状态；解码器第 20 层仍处理所有输入，21–39 层只处理末尾窗口。这依赖模型的跨层 KV 共享结构，不能直接搬到任意模型。重放还裁剪了窗口边界，因此不保证逐位一致；作者在 GSM8K、GPQA 等测试上未观察到显著精度变化，也不能据此外推所有长程任务。[机制与质量说明](https://vllm.ai/blog/2026-10-07-deepseek-v41-flash)

计算变少后，尾部层的 kernel 启动开销反而突出。实现分别为完整批次与裁剪后批次捕获 CUDA Graph。原文的 GB200 单请求实验关闭前缀缓存、取三次运行中位数：DEP2、1K 输入时，关闭重放的 TTFT 为 103.8 ms；只开重放为 116.2 ms，加入尾部 CUDA Graph 后为 72.5 ms。这个对照很好地说明了为什么“少算 token”仍可能更慢。[作者交互图及数据表](https://vllm.ai/blog-assets/interactive_pages/dsv41-prefill-ttft.html)

文章标题中的约五倍提升则属于另一层证据。其 AgentX 图比较 GB300 NVL72 上 9 月 11 日与 10 月 2 日的最佳配置，固定约 155 tok/s/user 的 P90 交互性时，每芯片吞吐由约 27K 到 144K tok/s，标为 5.3 倍。它是三周累计优化的结果，不能归因于有界重放一项，也不能算成本周新增性能。[原始图](https://vllm.ai/blog-assets/figures/2026-10-07-deepseek-v41-flash/agentx-results.png)

### Rubin：让执行单元读取本地权重

Rubin 博客中的具体机制是 locality domain：用 CUDA 的执行资源分区，让 MoE 两个全连接层的权重按列分片，分别放在对应域的 HBM，域内 SM 主要读取本地分片。小批量解码时权重读取占主导，因而这种布局有机会提高有效带宽。作者也明确将完整启用 locality domain 列在后续工作中，应按早期实验理解。[作者设计说明](https://vllm.ai/blog/2026-10-09-vera-rubin-preview)

这里也要分开单层与端到端结果。MiniMax M3 的 TP2 微基准使用全部 212 个 SM、平衡专家路由与固定内核配置，五次重复、CUDA Graph 计时，不计通信；32–4096 token 的十二个点，局部化相对非局部化的加速几何均值为 1.18 倍。它说明布局本身的潜力，还没有覆盖真实专家偏斜与通信成本。[单层实验数据表](https://vllm.ai/blog-assets/interactive_pages/vera-rubin-moe-locality-latency.html)

另一张 AgentX 图在 MiniMax M3、P90 交互性 150 tok/s/user 时，给出 Rubin NVL72 相对 GB200 NVL72 每芯片吞吐 5.18 倍的预览结果。图中两侧采用不同的最佳并行配置，硬件也跨代，不能把这个倍数解释成局部性优化的独立收益；图上同时提示结果仍可能随验证而变化。[原始图](https://vllm.ai/blog-assets/figures/2026-10-09-vera-rubin-preview/agentx-results.png)

最后要记住 AgentX 的吞吐口径：它计入输入、输出和缓存 token。作者 9 月 8 日的前序文章在本期仅用于解释这一指标，不列为本周新进展。[指标定义](https://vllm.ai/blog/2026-09-08-vllm-agentx)

实际验收可沿着这三层逐步展开：先用开关对照验证算法与图捕获，再用相同硬件和形状测布局，最后在固定交互性目标下比较完整服务。质量、TTFT、输出速度与含缓存的总吞吐分别记录，才能判断收益来自哪里；本期引用的实验均未独立复现。

## 来源与阅读范围

本期没有将旧论文的补读日期、会议日期或博客中累计优化的截止日期混作“本周新发表”。Active Data Lakes 与 LESS 分别对应湖存储和纠删恢复的补读；Fluss 的六月机制文章以及 AgentX 的九月指标定义只用于解释本周作者文章。正文中的日期与实验条件以链接原文为准。

本轮筛选覆盖 Iceberg/Paimon、Kafka/AutoMQ/Fluss 的原创技术文章，以及 FAST、OSDI、SOSP、ATC、SIGMOD/PVLDB/VLDB 和 AI Infra 的相关研究入口。没有足够新材料的方向直接说明，不用发行说明或开发动态凑数；这也不构成对所有来源的穷尽检索。材料选择、原文定位、发布日期、核验时间及未覆盖范围保存在[本期来源索引](https://github.com/BryantChang1992/ai_memory_chang_ai_team/blob/main/docs/drafts/weekly/2026-10-11/sources.json)。
