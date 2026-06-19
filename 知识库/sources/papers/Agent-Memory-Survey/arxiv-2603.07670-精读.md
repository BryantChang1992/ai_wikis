# Memory for Autonomous LLM Agents: Mechanisms, Evaluation, and Emerging Frontiers

- **URL**: https://arxiv.org/abs/2603.07670
- **日期**: 2026-03-08
- **来源**: ArXiv (cs.AI)
- **作者**: Eric Du et al.

## 摘要

LLM Agent 越来越频繁地在单次上下文窗口远不足够的环境中运行。Memory——跨交互持久化、组织、选择性召回信息的能力——是把无状态文本生成器转变为真正自适应 Agent 的关键。

本综述提供了 LLM Agent 记忆的系统化梳理（2022 - 2026 年初）：

1. **形式化定义**：Agent 记忆是一个 write → manage → read 循环，与感知和行动紧密耦合
2. **三维分类法**：时间维度（temporal scope）、表示基底（representational substrate）、控制策略（control policy）
3. **五大机制家族**：
   - Context-resident compression（上下文驻留压缩）
   - Retrieval-augmented stores（检索增强存储）
   - Reflective self-improvement（反思性自我改进）
   - Hierarchical virtual context（层级虚拟上下文）
   - Policy-learned management（策略学习管理）
4. **评估演进**：从静态 recall benchmark 到多会话 agentic 测试
5. **工程实践**：write-path filtering、矛盾处理、延迟预算、隐私治理
6. **开放挑战**：持续整合、因果驱动检索、可信反思、学习性遗忘、多模态具身记忆

## 关键 Insight

Agent 记忆不是单一的功能，而是一个横跨写入、管理、读取的系统架构问题。当前最大瓶颈不是存储容量，而是选择性遗忘和因果准确检索。

## 标签

agent-memory, llm-agents, survey, retrieval, context-management
