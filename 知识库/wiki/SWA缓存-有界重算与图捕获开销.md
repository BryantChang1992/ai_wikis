---
type: concept
title: SWA 缓存：有界重算与图捕获开销
sources:
- '[[知识库/sources/web/vllm-inference-20261007-09/来源记录]]'
- '[[技术文章/博客同步/tech-research-week-14]]'
- https://vllm.ai/blog/2026-10-07-deepseek-v41-flash
- https://vllm.ai/blog-assets/interactive_pages/dsv41-prefill-ttft.html
- https://vllm.ai/blog/2026-10-09-vera-rubin-preview
tags:
- AI Infra
- KV Cache
- vLLM
created: '2026-10-11'
updated: '2026-10-11'
status: draft
report_as_of: '2026-10-11'
review_scope: 基于本期已核验公开报告与来源记录提炼；不增加独立证据数，不声称复现实验或完成额外源码审计。
related:
- '[[知识库/wiki/KV缓存-路由索引缺口与有限重放]]'
- '[[知识库/wiki/synthesis/读路径优化的四种边界]]'
---

# SWA 缓存：有界重算与图捕获开销

## 问题

前缀缓存命中后，减少需要重算的 token，为什么仍可能让 TTFT 变差？

## 机制

在特定跨层 KV 共享结构上仅缓存全局 KV，重算末尾128个token的滑动窗口状态；第20层仍处理全部输入，21–39层处理尾部窗口。计算减少后，kernel启动占比上升，因此分别为完整与裁剪批次捕获 CUDA Graph。

## 取舍

减少重算与降低启动开销需要同时考虑。窗口边界裁剪不保证逐位一致；有限质量测试未出现显著变化，也不能证明所有长程任务无损。

## 适用边界

该机制依赖 DeepSeek-V4.1 结构。GB200 单请求、前缀缓存关闭、三次中位数的开关实验与累计5.3倍AgentX吞吐不是同一证据；后者包含多项优化且计入缓存token。Rubin跨代预览和局部性微基准同样不能算成本机制收益。本轮均未复现。

## 与已有知识的区别

已有有限重放卡修复的是缓存路由索引丢事件后的状态同步；这里重算的是模型窗口状态。两者都需边界，但序号补账、模型计算和质量保证不能混用。

既有页面：[[知识库/wiki/KV缓存-路由索引缺口与有限重放]]。

## 来源

- [[知识库/sources/web/vllm-inference-20261007-09/来源记录|来源与阅读范围]]
- [[技术文章/博客同步/tech-research-week-14|本期完整报告及实验条件]]
- 发表时间：本周vLLM作者博客2026-10-07、2026-10-09；后者保留作局部性对照。
- 原文定位：10/7作者机制/质量说明及prefill TTFT交互数据；10/9作者局部性与跨代基准仅作边界对照。
