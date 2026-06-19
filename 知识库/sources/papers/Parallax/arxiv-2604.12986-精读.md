# Parallax: Why AI Agents That Think Must Never Act

- **URL**: https://arxiv.org/abs/2604.12986
- **日期**: 2026-04-14
- **来源**: ArXiv (cs.CR / cs.AI)
- **作者**: Joel Fokou et al.
- **开源实现**: https://github.com/openparallax/openparallax

## 摘要

随着自主 AI Agent 从实验工具过渡为运营基础设施（预测 2026 年底 80% 企业应用嵌入 AI Copilot），一个根本性安全缺口浮现：**提示层安全（prompt-level guardrails）对具备执行能力的 Agent 架构不足**。

本文提出 **Parallax 范式**，四原则：

1. **Cognitive-Executive Separation**：结构性地阻止推理系统执行动作
2. **Adversarial Validation with Graduated Determinism**：在推理与执行之间插入独立的多层验证器
3. **Information Flow Control**：通过 Agent 工作流传播数据敏感性标签
4. **Reversible Execution**：捕捉预破坏状态以支持验证失败时回滚

## 实验结果

- 280 个对抗性测试用例，9 个攻击类别
- 默认配置下阻断 98.9% 攻击，零误报
- 最高安全配置下 100% 阻断
- **当推理系统被攻破时，prompt-level guardrails 提供零保护**（因为两者在同一被攻破的系统中）

## 关键 Insight

Agent 安全架构的决定性洞察：**think 和 act 必须在架构层面分离**。Prompt 级安全相当于让同一个被入侵的大脑来监督自己——无效。

## 标签

agent-security, agent-architecture, adversarial-validation, prompt-injection, sandbox
