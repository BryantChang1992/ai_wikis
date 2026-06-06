# CTO 长期记忆

## 角色
- CHANG_AI_TEAM 首席技术官，向 CEO (Mike) 和 Frank 汇报
- 下级：PMO（sessions_send）+ 4 位专家（RD/性能/QA/SRE，sessions_spawn）
  - 专家 → 执行层 worker（rd-worker/perf-worker/qa-worker/sre-worker）

## 当前活跃项目
- Agent 基础设施可观测性平台（五维度框架，Phase 1 done，Phase 2 进行中）
- Kafka KIP 深度调研（KIP-1279 Cluster Mirroring + KIP-1290 Rack-Aware Min ISR）
- 技术调研周报（每周四自动运行，三个方向：AI Agent、数据平台、Kafka 生态）

## 关键决策
- 2026-06-06：团队组织架构正式化——去除 Infra 角色，新增 PMO + RD 专家 + QA 专家，专家层扩至 4 人
- 2026-06-06：feishu-bot-chat 插件接入完成，Agent 间可通过飞书群 @ 原生通信
- 2026-06-06：PMO 协作模式确定——混合 A+B（被动监控 Dashboard + CTO 关键节点推送 sessions_send），PMO 负责所有 Wiki 发布
- 2026-06-05：Phase 3 知识管理第一阶段落地——知识检索规则写入所有 Agent AGENTS.md；知识沉淀规则+沉淀路径定义；spawn 知识传递规范；冷启动流程增强
- 2026-06-05：记忆系统方案确定——物理隔离+协议上报，不搞复杂分权；检索靠 OpenClaw 原生；冷启动由 Phase 3 SQLite 兜底
- 2026-05-31：Agent 规范落地——所有 VP 的 AGENTS.md 统一模板、权限矩阵、通信协议、状态机
- 2026-05-28：Agent 基建设计从可观测性单维度升级为五维度框架（记忆/知识/工作流/可观测/可靠性）

## 技术栈
- 语言：Python (数据采集), HTML+JS (Dashboard), Markdown (文档)
- 存储：SQLite + Git (状态持久化), Obsidian Vault (知识管理)
- Agent 框架：OpenClaw (DeepSeek v4-pro/v4-flash)
- 插件：feishu-bot-chat (飞书群 Bot 间 @ 通信)
