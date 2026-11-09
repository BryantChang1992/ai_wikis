---
type: survey
title: 技术调研周报 Week 15：从数据留存到可用，读路径上的隐性成本
sources:
- https://www.dremio.com/blog/apache-iceberg-vs-apache-parquet/
- https://www.usenix.org/conference/osdi26/presentation/athlur
- https://www.pdl.cmu.edu/PDL-FTP/Storage/Declarative_IO-OSDI26.pdf#page=6
- https://www.pdl.cmu.edu/PDL-FTP/Storage/Declarative_IO-OSDI26.pdf#page=10
- https://www.automq.com/blog/diskless-kafka-observability-production-framework
- https://www.automq.com/blog/diskless-kafka-schema-evolution-production-framework
- https://www.automq.com/blog/diskless-kafka-security-boundaries-production-framework
- https://vllm.ai/blog/2026-10-12-bidirectional-kvxfer-multiturn-agentic-workload
- https://vllm.ai/blog/2026-10-12-bidirectional-kvxfer-multiturn-agentic-workload#performance-data
- https://vllm.ai/blog/2026-10-14-nixl-push-connector
- https://vllm.ai/blog/2026-10-14-nixl-push-connector#performance-data
tags:
- 数据湖
- 分布式存储
- 流存储
- AI Infra
created: '2026-11-09'
updated: '2026-11-09'
status: draft
publication_scope: 公开技术报告及引用；知识卡和独立专题不因本文同步而扩大发布范围。在线状态以实际部署验收为准。
report_date: '2026-10-18'
issue: 15
issue_date: '2026-10-18'
observation_start: '2026-10-11T00:00:00Z'
observation_end: '2026-10-18T00:00:00Z'
source_checked: '2026-10-18'
source_check_scope: 沿用原报告的原文核验日期与范围；本次仅归档，未重新核读全部外部来源。
related:
- '[[知识库/sources/web/technical-trends-week15/来源索引]]'
---

# 技术调研周报 Week 15：从数据留存到可用，读路径上的隐性成本

> 阅读时间说明：本文保留 2026-10-18 报告的观察窗口、原文核验时间和技术限制。正文中的“本周”、版本阶段及历史交付说明均按原观察时点理解，不代表本次页面整理时的最新状态。本次仅适配发布格式，未重新核读全部外部来源或独立复现实验。 原文核验截止：2026-10-18（原稿只记录检索日期，未记录精确时刻）。

[公开来源索引](../../知识库/sources/web/technical-trends-week15/来源索引.md)

观察窗口：2026 年 10 月 11 日 08:00 至 10 月 18 日 08:00（北京时间）。原文检索日期：10 月 18 日。网页只标日期而未给时间与时区时，按页面日期筛选；10 月 11 日的博客属于窗口起点边界材料，不声称已确认精确上线时刻。

本期重点是一个经常被吞吐数字掩盖的问题：数据已经保存下来，距离真正可用还有多远？湖表要先找到正确文件，历史日志还依赖 schema 与权限，后台维护需要按时读完数据，而推理服务必须在合适的节点及时取得 KV 状态。四者并非同一种系统，但都提醒我们把“有数据”和“能及时、正确地使用数据”分开验收。

本周可展开的新材料来自 vLLM 与 AutoMQ 技术博客。湖方向保留一组基础读物；存储方向补读 OSDI 2026 的 DINGO，明确它不是本周新论文。以下性能数值均为作者报告，未独立复现；本文提出的验收方案也没有当作真实实验。社区 Issue、PR 和开发进展继续由独立专题覆盖。

## 一 数据湖：数据湖的新文，仍以机制梳理为主

本周核验到的湖方向官方技术文，以既有机制讲解为主，没有建立新论文或新性能实验的证据。Dremio 的 Alex Merced 在 10 月 12 日文章中区分两层裁剪：Iceberg 的 manifest 描述文件集合与文件级统计，帮助引擎在打开文件前排除候选；Parquet 内部统计再帮助跳过 row group 或 page。两者作用在不同层级，是否实际采用还取决于读者实现。[Dremio 原文](https://www.dremio.com/blog/apache-iceberg-vs-apache-parquet/)

该文适合作为读路径的基础读物，本期不将它扩写成研究突破。Paimon 同期未核验到符合本节要求的原创技术长文，不用发行记录补齐。


## 二 分布式存储：让维护任务主动创造缓存复用

**旧文补读，不计本周新发表。** 《Scaling the IO Wall with Declarative IO》发表于 OSDI ’26（7 月 13–15 日）。它追问的是：磁盘容量增加以后，后台维护是否还来得及完成？作者调研六家 hyperscaler，发现缓存之后到达 HDD 的 I/O 中，维护任务占 45%–70%。因此，扩充前台缓存不一定解决后台扫描的成本。[论文与发表信息](https://www.usenix.org/conference/osdi26/presentation/athlur)

DINGO 让维护任务声明数据集合、截止时间与回调，再安排不同任务在相近时刻读同一批块，把原本相隔很久的重复访问变成短期缓存命中。它面向 append-only 系统的 sealed、不可变块；收到回调后仍通过普通接口读取。声明之后新增的数据不自动纳入，已删除块也须处理。紧急的关联磁盘故障恢复应走即时请求。[作者全文 §4–5](https://www.pdl.cmu.edu/PDL-FTP/Storage/Declarative_IO-OSDI26.pdf#page=6)

HDFS 原型使用 10 节点、3 TB HDD，针对四类维护任务运行 81 小时，容量和时间均按八分之一缩放，读字节减少 26%。可支持 1.7 倍大磁盘则来自 100 PB 仿真，不能写成生产实测。读预算还没有约束所有资源：集中转码产生的写突发仍可能推高前台延迟。[作者全文 §6](https://www.pdl.cmu.edu/PDL-FTP/Storage/Declarative_IO-OSDI26.pdf#page=10)

**本文判断与验证建议。** 这项工作提示，维护流量治理不应只给每个后台作业单独限速。可先收集 scrub、重建、转码、均衡的数据重叠和最迟完成时间，再判断共同调度是否有价值。验收至少要同时检查维护截止时间、读写量、前台尾延迟与故障时的退路。尤其不要把平均节省的 I/O 全部用于提高容量：否则一旦复用失效，系统可能缺少恢复余量。以上为评估建议，不是对原型的新实验结论。


## 三 流存储：流存储的重放，依赖的不只是历史字节

**页面标注 10 月 11 日的官方技术博客。** 原文未提供发布时间和时区，无法严格确认其相对于 10 月 11 日 00:00 UTC 窗口起点的归属；本节按日期粒度列为边界材料。AutoMQ Team 的可观测性、Schema 演进和安全边界三篇生产评审文章，共同问题是：数据离开 broker 本地持久盘后，怎样证明一条历史记录仍然可找到、可解码、可被正确授权，并在约定时间内返回？这些文章提供的是评审方法，没有新增算法的对照实验或可复现性能数字，不据此宣称 AutoMQ 本周性能提升。

### 延迟曲线需要对应到具体读取路径

可观测性文章把 Kafka 请求与消费进度，同缓存、对象存储和网络排队放到一条时间线上。热读与历史回放可能出现相似的 lag，却经过不同路径。作者给出的排查顺序先看请求与分区是否可用，再关联缓存未命中、远端下载、限流等待和消费者处理；一次对象存储慢请求本身不足以解释一次业务停顿。文章还要求记录 WAL 类型和端点，因为不同部署不能混为同一种恢复路径。[AutoMQ：可观测性](https://www.automq.com/blog/diskless-kafka-observability-production-framework)

### 字节留存与 Schema 留存是两个承诺

Schema 演进文强调，记录携带的 schema 标识并不包含整个注册中心的可用性保证。新消费者能否读取旧记录，除了兼容规则，还受历史 schema 是否保留、凭据是否有效、客户端是否缓存过该版本影响。作者将热读、冷读、长时间暂停后恢复和跨版本读者分开测试；“注册成功”“Kafka 写入成功”和“历史回放成功”分别证明不同环节。[AutoMQ：Schema 演进](https://www.automq.com/blog/diskless-kafka-schema-evolution-production-framework)

### Topic 权限之外，还有存储服务身份

安全边界文讨论 Kafka 客户端身份与 broker 访问对象存储所用身份的分离。Topic ACL 不会自动约束一个拥有宽泛对象读取权限的云角色；恢复 broker、运维工具和跨租户路径也需要独立核验。文章建议同时测试正常访问与越界拒绝，并检查更换可用区后的端点路由。它是部署评审框架，并非对任意 AutoMQ 安装的隔离保证。[AutoMQ：安全边界](https://www.automq.com/blog/diskless-kafka-security-boundaries-production-framework)

### 将三条检查链合成一次受控回放

本刊的推论是：对象存储降低了计算节点与历史字节的绑定程度，但恢复验收仍然需要完整的依赖链。只保留“对象还在”的截图，无法回答消费者为什么不能继续处理；只看恢复完成时间，也可能把缓存命中掩盖的问题带入下一次事故。

可做一个小而完整的验证：保存一段跨 schema 版本的固定记录，分别由旧、新读者回放，核对主键、记录数、顺序与解码结果；再以新启动的消费者和替换 broker 复测。每轮记录最早可读 offset、首条返回时间、回放完成时间、注册中心调用和对象存储请求。最后在隔离测试环境中一次只注入一种权限或端点故障，确认失败明确可诊断，恢复后没有跳过记录。这是本文提出的实验方案，本期未执行，也不把方案中的预期行为当作产品已验证事实。

本周 Kafka 项目博客没有找到窗口内可展开的原创机制文章；Fluss 最新已核验技术文发表于 10 月 8 日，属于上期窗口，因此本期不作为新增材料展开。


## 四 AI Infra：KV 的复用方向与传输时机是两种选择

本周 vLLM 发布两篇原创技术博客，分别讨论跨轮次复用与首 token 关键路径。它们解决不同问题，性能数字不能相乘。

### 双向 KV：上一轮生成的状态能否服务下一轮

10 月 12 日文章由 AWS 的 Sunita Nadampalli 撰写。decode 保存上一轮 KV，路由器只保留位置元数据，下一轮 prefill 先查本地缓存，再按阈值从 decode 拉回状态。固定 TTL 默认 480 秒，不会自动续期，因此复用以显存占用为代价。[原文机制与 TTL](https://vllm.ai/blog/2026-10-12-bidirectional-kvxfer-multiturn-agentic-workload)

实验采用 EFA 连接的两个 p5en 节点，1P1D；**主动关闭 prefill 前缀缓存**，模拟缓存淘汰或请求来到另一节点。长输入下，Qwen3-32B 的 TTFT 为 778→460 ms，GLM-5-FP8 为 2334→702 ms。它证明失配场景下远端复用可胜过重算，不证明所有线上会话都有同等收益。[原文 Performance data 与附录](https://vllm.ai/blog/2026-10-12-bidirectional-kvxfer-multiturn-agentic-workload#performance-data)

**本文建议。** 测试时应把“本地已命中”“本地未命中、远端仍存活”“TTL 已过期”分开，再改变轮次间隔与会话并发。只记录命中率不够，还要测保留 KV 导致的显存压力，以及其他会话的排队时间。对长时间工具调用，TTL 是否覆盖真实等待时间，比单次传输带宽更值得先确认。

### Push：把准备工作提前，但更早锁定 decode 节点

10 月 14 日 AWS 与 Mistral 作者介绍 NixlPushConnector：decode 提前分配并登记目标块，prefill 完成后由后台线程执行 NIXL WRITE，减少串行准备。代价是提前选择 decode 节点；原文明确，**需要双向 KV 或较晚择节点时仍应使用 pull**。[原文架构与适用边界](https://vllm.ai/blog/2026-10-14-nixl-push-connector)

Qwen3-32B、1P1D、p5en/EFA 实验关闭 **decode** 前缀缓存，输出 128 token。16K 输入、8 QPS 时 TTFT 约为 pull 1744 ms、push 540 ms；低负载短输入差异很小。该比较隔离了每请求完整 P→D 传输，并非双向复用实验。不能把前一篇关闭 prefill 缓存的条件抄到这里。[原文 Performance data 与附录](https://vllm.ai/blog/2026-10-14-nixl-push-connector#performance-data)

**本文判断。** “更早准备”与“保留晚绑定路由选择”是工程取舍。真实系统应先观察延迟花在重算、传输、元数据准备还是排队，再选择实验路径。建议分别固定模型、并发、输入输出长度与缓存策略，记录 TTFT、TPOT、吞吐和路由偏斜；单独量化后台线程与协议方向的效果。本文没有验证两种 connector 的联合配置，也不将原文提到的后续工作写成已实现能力。
