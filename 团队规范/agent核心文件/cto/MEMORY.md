# CTO 长期记忆

## 角色
- CHANG_AI_TEAM 首席技术官，向 CEO (Mike) 和 Frank 汇报
- 下属：专家·Infra / 专家·Perf / 专家·SRE → 执行层 RD/SRE/QA

## 当前活跃项目
- Agent 基础设施可观测性平台（五维度框架，Phase 1 done，Phase 2 进行中）
- Kafka KIP 深度调研（KIP-1279 Cluster Mirroring + KIP-1290 Rack-Aware Min ISR）
- 技术调研周报（每周四自动运行，三个方向：AI Agent、数据平台、Kafka 生态）

## 关键决策
- 2026-06-05：记忆系统方案确定——物理隔离+协议上报，不搞复杂分权；检索靠 OpenClaw 原生；冷启动由 Phase 3 SQLite 兜底
- 2026-05-31：Agent 规范落地——所有 VP 的 AGENTS.md 统一模板、权限矩阵、通信协议、状态机
- 2026-05-28：Agent 基建设计从可观测性单维度升级为五维度框架（记忆/知识/工作流/可观测/可靠性）

## 技术栈
- 语言：Python (数据采集), HTML+JS (Dashboard), Markdown (文档)
- 存储：SQLite + Git (状态持久化), Obsidian Vault (知识管理)
- Agent 框架：OpenClaw (DeepSeek v4-pro/v4-flash)
