---
type: concept
title: Loop Engineering — 多层 Agent 循环架构
sources:
- '[[知识库/sources/web/langchain/the-art-of-loop-engineering-精读]]'
- https://www.langchain.com/blog/the-art-of-loop-engineering
tags:
- agent-infra
- agent-harness
- loop-engineering
- langchain
created: 2026-06-19
updated: '2026-10-05'
status: draft
related:
- '[[知识库/wiki/Custom-Agent-Harness-Middleware架构]]'
- '[[知识库/wiki/Agent-Fault-Tolerance-容错设计]]'
- '[[知识库/wiki/Agent-Cost-Control-Gateway成本控制]]'
- '[[知识库/wiki/Agent-First-Data-Systems]]'
- '[[知识库/wiki/synthesis/AI-Infra-Agent基础设施体系综述]]'
synced_at: '2026-10-05'
blog_url: https://bryantchang1992.github.io/ai_memory_chang_ai_team/knowledge/Loop-Engineering-多层Agent循环架构/
blog_source: _posts/2026-06-19-knowledge-94bcbdbdbc.md
source_checked: '2026-10-05'
diagram_format: mermaid
---

# Loop Engineering — 多层 Agent 循环架构

四种循环分别处理执行、结果验证、事件触发和跨运行改进。它们可以组合，但不要求所有系统都堆满四层。

```mermaid
flowchart TD
 E[事件触发] --> A[Agent 执行循环]
 A --> V[结果验证]
 V -->|反馈重试：有预算| A
 V -->|通过| D[交付]
 A --> T[Trace]
 V --> T
 T --> H[跨运行分析与改进候选]
 H --> R[独立回归与审查]
 R --> C[更新配置]
 C --> A
```

[原文](https://www.langchain.com/blog/the-art-of-loop-engineering) 用文档 Agent 举例：链接/CI 检查负责可执行判据，事件连接持续工作，Trace 分析发现重复问题并请求修改 Harness。它没有提供每一层带来多少收益的消融实验。

- 验证循环提供反馈；grader 的覆盖与可靠性决定它能发现哪些错误，不能保证所有结果正确。
- 事件循环需要去重、限频和持久任务标识，避免重投产生重复副作用。
- 改进循环产生候选方案；以独立样本和人工判断接受变更，避免只追逐当前 grader 的分数。
- 总费用受调用数、上下文和频率影响；嵌套重试可放大费用，但不存在通用“层数越多必然指数增长”规律。

例如链接全通的文档仍可能写错参数语义，必须增加事实核验或测试；新增 grader 后又要检查其费用和误拦截。外层 deadline 应向内传播剩余预算，而不是机械要求比所有内层超时之和更大。

详读：[[知识库/sources/web/langchain/the-art-of-loop-engineering-精读]]；相关：[[Agent-Harness-Verification-Evaluation评估]]、[[Custom-Agent-Harness-Middleware架构]]、[[Agent-Fault-Tolerance-容错设计]]。
