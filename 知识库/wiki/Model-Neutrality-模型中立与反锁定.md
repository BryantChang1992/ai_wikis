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
related:
  - "[[Custom-Agent-Harness-Middleware架构]]"
  - "[[Agent-Cost-Control-Gateway成本控制]]"
  - "[[Loop-Engineering-多层Agent循环架构]]"
  - "[[Agent-First-Data-Systems]]"
---

# Model Neutrality — 模型中立与反锁定

LangChain 的核心论点：**模型层正在复制云时代的故事**——供应商卖商品（tokens），然后通过工具层（harness）锁客。云时代的教训是：AWS/GCP 存储是商品 → 锁定靠 CloudFormation/ARM templates → HashiCorp Terraform 从一层之上提供中立抽象 → 赢得市场。

## 为什么模型中立比云中立更重要

| 维度 | 云中立 | 模型中立 |
|------|--------|----------|
| 变化速度 | 迁移以年计 | 模型能力以月/季度跳变 |
| 切换粒度 | 合同续约时 | **单次请求内** |
| 最优策略 | 单一供应商通常够用 | 不同模型各有所长（Anthropic 编码强、OpenAI 多模态强） |
| 开源选项 | 无同等替代 | Mistral、DeepSeek、Qwen 可混合使用 |

> "Cloud neutrality stopped at the contract. Agent neutrality has to follow the request."

## 选择性商品化

模型市场正在形成**选择性商品化**格局：
- **Anthropic** → 编码和推理最强
- **OpenAI** → 多模态（视觉/语音）领先
- **DeepSeek/Qwen** → 成本优势显著，中文场景强
- **Mistral** → 欧洲合规友好

最优方案不是"选最强模型"，而是**同一 workflow 中按任务类型调用不同模型**——编码任务走 Claude，多模态走 GPT-4o，批量简单任务走 DeepSeek。

## 中立 Harness 三要素

| 要素 | 含义 | 对应 Middleware |
|------|------|----------------|
| **开源** | 每行代码可审计，无供应商后门 | 无对应（架构层面） |
| **多模型** | 同一 harness，任意后端，一视同仁 | [[Custom-Agent-Harness-Middleware架构]] 的 `ModelFallbackMiddleware` |
| **Profile-aware** | 不强求模型无差别化，而是暴露各自长处 | `DynamicModelSwitching` |

## 与 [[Agent-Cost-Control-Gateway成本控制]] 的协同

模型中立是成本控制的战略基础设施：
- 没有模型中立，cost control 只能在一个供应商内做 token 配额
- 有模型中立后，cost control 可以做 **cost-aware routing**——便宜任务走 cheap model，昂贵任务才走 expensive model
- **同一任务不同模型的价格差可达 5-10x**

这比单纯的 token 配额控制更根本——不是在"用"这个层面限制，而是在"选"这个层面优化。

## 与 [[Loop-Engineering-多层Agent循环架构]] 的配合

多循环架构中，不同层级适合不同模型：
- **L1 (Agent Loop)**：核心推理 → 走最强模型（Anthropic/OpenAI）
- **L2 (Verification Loop)**：质量校验 → 可以用便宜模型做 grader
- **L4 (Hill Climbing Loop)**：trace 分析 → 可以走极 cheap 模型甚至规则引擎

模型中立让每层循环选择最适合的模型，而非被迫全链路锁死在一个供应商。

## 工程落地要点

1. **Provider abstraction layer**：不是简单的 API 适配，而是调度层——model registry + capability profile + cost model
2. **Single-request switching**：模型切换必须在单次请求内完成，不能在部署时锁死
3. **降级链**：强模型 A 不可用 → fallback 强模型 B → fallback 便宜模型 C → fallback 静态降级响应
4. **审计追踪**：每次模型切换记录原因 + token 消耗 + 延迟影响
