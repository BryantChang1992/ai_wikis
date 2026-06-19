# Why Model Neutrality Matters More Than Cloud Neutrality

- **URL**: https://www.langchain.com/blog/model-neutrality
- **来源**: LangChain Blog
- **日期**: 2026-06 (约)

## 核心论点

模型层正在复制云时代的故事：供应商卖商品（tokens），然后通过工具层（harness）锁客。

### 云时代的教训

- AWS/GCP 存储是商品 → 锁定靠 CloudFormation/ARM templates
- HashiCorp Terraform 从一层之上提供中立抽象 → 赢得市场
- 早期采用中立的企业的议价能力和故障转移是真实的

### 为什么模型中立比云中立更重要

1. **变化速度不同**：云迁移以年计，模型能力以月/季度跳变
2. **选择性商品化**：Anthropic 编码强、OpenAI 多模态强 → 最优方案是同一 workflow 中用多个模型
3. **开源权重模型是实在选项**：Mistral、DeepSeek、Qwen 可混合使用

### 中立 Harness 的三要素

1. **开源**：每行代码可审计
2. **多模型**：同一 harness，任意后端，一视同仁
3. **Profile-aware**：不强求模型无差别化，而是暴露各自长处

## 关键 Insight

"Cloud neutrality stopped at the contract. Agent neutrality has to follow the request."——agent 中的模型切换发生在**单次请求内**，而不是合同续约时。这是本质区别。
