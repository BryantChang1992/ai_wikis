---
type: concept
title: "Model Neutrality — 模型中立与反锁定"
sources:
  - "sources/web/langchain/model-neutrality-精读.md"
  - "https://www.langchain.com/blog/model-neutrality"
tags:
  - "agent-infra"
  - "agent-harness"
  - "model-neutrality"
  - "vendor-lockin"
created: 2026-06-19
updated: 2026-06-19
status: draft
related: []
---

# Model Neutrality — 模型中立与反锁定

## 模式重演

云时代剧情：AWS/GCP 底层存储是商品 → 锁定靠工具层（CloudFormation / ARM templates）→ Terraform 以一层之上的中立抽象赢得市场。

模型时代重演：Labs 卖 tokens（商品）→ 锁定靠 harness（Claude Agent SDK / OpenAI Agents API / Vertex AI Agent Builder）。

## 为什么比云中立更重要

1. **变化速度**：云迁移以年计，模型能力以月/季度跳变
2. **选择性商品化**：Anthropic 编码强、OpenAI 多模态强 → 最优方案是同一 workflow 用多模型，按任务路由
3. **开源权重模型实在**：Mistral / DeepSeek / Qwen 可混用

## 本质区别

> Cloud neutrality stopped at the contract. **Agent neutrality has to follow the request.**

模型切换发生在**单次请求内**（选择 Claude 编码 → GPT 图像 → 降级到便宜模型），而非合同续约时。

## 中立 Harness 三要素

| 要素 | 说明 |
|------|------|
| **开源** | 每行代码可审计，无隐藏 vendor bias |
| **多模型** | 同一 harness，任意后端，一视同仁 |
| **Profile-aware** | 不强求模型无差别化，暴露各自长处 |

## 关键 Insight

> Harness lock-in 比 model lock-in 更难解，因为 harness 里存的是你的 business logic。
