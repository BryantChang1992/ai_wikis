---
type: concept
title: gLSM：GPU 加速 Compaction 的证据边界
sources:
- '[[知识库/sources/papers/LSM-tree-KV-Survey-2025/精读分析]]'
- '[[知识库/sources/papers/LSM-tree-KV-Survey-2025/LSM-tree-KV-Survey-2025.pdf]]'
tags:
- 存储引擎
- LSM-Tree
- Compaction
- GPU
- 硬件加速
- 归并排序
created: 2026-07-02
updated: '2026-10-05'
status: draft
related:
- '[[知识库/wiki/LSM-Tree]]'
- '[[知识库/wiki/LSM-Tree-合并优化]]'
- '[[知识库/wiki/LSM-Tree-硬件适配]]'
- '[[知识库/wiki/LSM-tree-KV-Survey-综述]]'
synced_at: '2026-10-05'
blog_url: https://bryantchang1992.github.io/ai_memory_chang_ai_team/knowledge/gLSM-GPU加速Compaction/
blog_source: _posts/2026-07-02-knowledge-a0826cae53.md
source_check_scope: 综述级核验：页16硬件卸载段、参考文献[101]（页34）；未取得/核验独立原文，撤除未确认量化与协议细节。
source_checked: '2026-10-05'
diagram_format: mermaid
---

# gLSM：GPU 加速 Compaction 的证据边界

> **来源层级**：本次只核验本地2025 LSM综述的页16硬件卸载段、参考文献[101]（页34）。这是二级来源概念卡，不是gLSM独立原论文精读；原有`draft`审核状态不升级。

## 综述明确支持的结论

综述确认gLSM利用GPGPU并行能力加速compaction；书目为Hui Sun等，ACM Transactions on Storage 2024。本地没有独立原论文。

## 为什么值得研究

Compaction的排序/合并具有可并行工作，但端到端耗时也包含读入、编码、传输和写出。GPU擅长并行计算，只有被加速部分足够大、其他成本可控时才有净收益。不能从“GPU有更多线程”推出任意compaction更快。

```mermaid
flowchart LR
  Input[输入有序数据] --> Transfer[准备并传输数据]
  Transfer --> GPU[GPU并行compaction计算]
  GPU --> Output[回传与持久化输出]
  Output --> Publish[引擎安装新版本]
```

这是一般卸载成本分解图，非已核验的gLSM缓冲区结构、流水线调度或GPU Router实现。正确性仍要求遵守key比较器、版本顺序、tombstone和快照规则。

## 教学成本模型与例子

令CPU本地耗时为T_cpu，GPU路径总耗时为T_prepare+T_transfer+T_gpu+T_write+T_install。只有比较相同输入、相同输出语义和资源预算，才能判断卸载价值。

教学数值：原本合并10ms，其中可加速计算6ms；即使该部分快3倍，也只节约4ms。若传输与准备新增5ms，端到端反而慢1ms。该例不是gLSM实验数据，只说明为什么不能把kernel加速比当成数据库吞吐提升。

## 待核问题与已撤除断言

- 原文的批次大小、比较器支持、GPU内存布局、去重/删除规则、CPU回退策略与崩溃后安装顺序尚待核验。
- 原卡的“1MB以下CPU、10MB以上GPU”、固定分流阈值和伪代码并非综述内容，已撤除。
- GPU云成本3–10倍及各种加速范围没有当前报价或独立论文条件支持，不保留为事实。

**工程推论**：应测全流程而非只测GPU kernel，报告PCIe/互联带宽、输入key/value布局、压缩、batch、显存占用、前台P99以及能耗/成本；小任务和自定义比较器可能需要不同路径，但不能冒称原系统已经实现。

相关：[[LSM-Tree-硬件适配]]、[[CaaS-LSM-Compaction即服务]]、[[LSM-tree-KV-Survey-综述]]。
