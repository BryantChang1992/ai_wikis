# How We Made Coding Agent Spend Predictable

- **URL**: https://www.langchain.com/blog/how-we-made-coding-agent-spend-predictable
- **来源**: LangChain Blog, Martha Janicki
- **日期**: 2026-06-15

## 核心主题

LangChain 内部 AI 支出从可控跃变为难以追踪的两个触发条件：
1. 少数团队 → 全公司使用
2. 最好模型越来越贵 + Agent 可轻易在单任务中触发数十次模型调用

## LangSmith LLM Gateway 方案

### 预算维度
- 组织级 / 工作空间级 / 用户级 / API Key 级
- 时间窗口：月/周/天/小时
- 支持例外（特定项目需要高用量）

### 集成深度
- 所有 coding agent 调用（Claude Code / Codex / Deep Agents）集中通过 Gateway 路由
- 成本数据关联到 agent、模型调用、trace、故障模式

### Dogfood 三教训

1. **模型计价比静态查找表复杂**：caching、token 分级、频繁的价格变化 → 需要系统化处理
2. **并非所有客户端都能通过 Gateway 路由**：Cursor 只暴露 base-url swap（Chat only），Claude Desktop 需 managed config
3. **硬限制需要配套工作流**：提前预警 + 快速、可审计的提额流程

## 关键 Insight

成本可观测性不仅看月末账单——工程领导需要**按分钟级**看到消费、设置正确的限制粒度、给团队灵活使用 coding agent 的权限而不必担心意外账单。
