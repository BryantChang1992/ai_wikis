---
title: 可观测性深度设计
status: draft
version: v0.1
created: 2026-06-06
tags:
  - observability
  - agent-infra
  - 精密度设计
  - CHANG_AI_TEAM
parent: 设计文档.md
---

# 可观测性深度设计

> [!note] 定位
> 本文是对 [[设计文档]] §5 "可观测性" 的精密化展开。原设计停留在"列几张表 + 画一个 Dashboard"的层面，本文回答三个根本问题：
> 1. **观测什么** → 按角色、场景、时间维度确定观测需求
> 2. **怎么采集** → 每条数据的源头、链路、频率、一致性保障
> 3. **如何展示** → 不同角色用不同视图，不是一张大屏打天下

---

## 1. 观测需求分层分析

> 可观测性的核心不是"能看多少数据"，而是"对的人在对的时间看到对的数据"。

### 1.1 按角色分层

```
                    CEO (Frank)
                   /            \
              CTO (我)          CFO
           /     |     \
    专家·Infra 专家·Perf 专家·SRE
      /  \       |       /  \
    RD1  RD2   RD3    SRE1 SRE2
```

| 角色 | 核心关切 | 观测频率 | 粒度 | 典型问题 |
|------|---------|---------|------|---------|
| **CEO** | 团队整体运行状态、关键产出、是否有异常 | 1-2 次/天 | 团队级汇总 | "这周谁在做什么？有阻塞吗？" |
| **CTO** | 任务流水线健康度、技术决策执行情况、成本与效率 | 多次/天 | 项目级/Agent 级 | "为什么 Kafka 调研花了两天？token 消耗是否合理？" |
| **CFO** | 成本归因、预算控制 | 1 次/周 | 按项目归因 | "哪个项目的 token 成本最高？" |
| **VP 层** | 领域内的 Agent 状态、产出质量 | 按需 | 领域级 | "Infra 团队的 RD 都在做什么任务？" |
| **专家层** | 自己派发的子任务进度、执行层状态 | 多次/天 | 任务级 | "我派给 RD 的三个任务各到什么阶段了？" |
| **Agent 自身** | 自身任务队列、依赖是否就绪 | 实时 | 自身状态 | "我的子任务都完成了吗？可以汇总了吗？" |

### 1.2 按场景分层

| 场景 | 角色 | 时间约束 | 核心需求 | 数据时效 |
|------|------|---------|---------|---------|
| **日常监控** | CTO/CEO | 10s 刷新可接受 | 一眼看出有没有问题 | 近实时（10s 延迟） |
| **主动排查** | CTO/专家 | 需要细粒度历史 | 深入单个任务/Agent 的完整行为轨迹 | 完整历史 |
| **告警响应** | CTO（被通知） | 秒级 | 立即定位问题 Agent/任务 | 实时 |
| **周复盘** | CEO/CTO | 不限 | 趋势分析、效率评估、成本报告 | 汇总数据 |
| **月结** | CFO | 不限 | 按项目/层级归因的成本报表 | 汇总数据 |

### 1.3 按时间维度分层

| 层级 | 时效 | 用途 | 存储策略 |
|------|------|------|---------|
| **实时** (秒级) | < 5s | 告警触发、Supervisor 对账 | 内存 + SQLite |
| **近实时** (分钟级) | 10s-60s | Dashboard 刷新 | SQLite |
| **近期** (小时/天) | 按需 | 主动排查、回溯 | SQLite |
| **长期** (周/月) | 按需 | 趋势分析、成本报告 | SQLite → Git 归档 |
| **永久** | — | 审计、复盘 | Git 版本控制 |

### 1.4 观测需求矩阵（V1）

综合以上三层，得到第一版观测需求矩阵：

| 观测对象 | CEO | CTO | CFO | 专家 | Agent 自身 | 数据源 |
|---------|-----|-----|-----|------|-----------|--------|
| 活跃 Agent 数 / 离线 Agent 数 | ✅ | ✅ | — | — | — | agents 表 |
| 任务总数 / 进行中 / 阻塞 / 今日完成 | ✅ | ✅ | — | ✅ (领域) | — | tasks 表 |
| 阻塞任务列表 + 阻塞原因 | — | ✅ | — | ✅ | ✅ (自身) | tasks + block_reason |
| Token 消耗（今日/本周/本月） | ✅ 汇总 | ✅ 按 Agent | ✅ 按项目 | ✅ 按任务 | ✅ 自身 | sessions 表 |
| Token 趋势图（7d/30d） | ✅ | ✅ | ✅ | — | — | sessions 汇总 |
| 任务吞吐量（hourly/daily） | — | ✅ | — | — | — | tasks 汇总 |
| 任务成功率 | — | ✅ | — | ✅ | — | tasks 汇总 |
| Agent 利用率 | — | ✅ | — | ✅ | — | sessions + tool_calls |
| 工具调用分布 | — | ✅ (异常检测) | — | ✅ (审计) | — | tool_calls 表 |
| 记忆操作频率 | — | ✅ (质量) | — | — | — | memory_ops 表 |
| 知识引用排行 | — | ✅ (质量) | — | — | — | wiki_access 表 |
| 子任务 Fan-out 比率 | — | ✅ | — | ✅ | — | tasks parent |
| 单 Agent Timeline | — | ✅ | — | ✅ | — | sessions + tool_calls |
| 单任务调用链追踪 | — | ✅ (排查) | ✅ (排查) | ✅ | — | tasks → sessions → tool_calls |

---

## 2. 指标体系设计

> 指标是观测的"语言"。没有精准定义，看到的数据就只是墨水。

### 2.1 指标分层

```
L1: 健康指标（CEO 看）──────────────────────────
    ├── 团队健康分 (0-100)
    ├── 活跃 Agent 比例
    └── P0 告警数量

L2: 运营指标（CTO 看）──────────────────────────
    ├── 任务吞吐量 & 成功率
    ├── Token 消耗 & 归因
    ├── Agent 利用率
    └── 阻塞率 & 阻塞时长

L3: 效能指标（CTO/专家看）──────────────────────
    ├── 平均任务耗时
    ├── 子任务发散度
    ├── 知识引用效率
    └── Token 效率比

L4: 审计指标（排查用）──────────────────────────
    ├── 工具调用详情
    ├── 记忆操作记录
    ├── 错误率 & 错误分布
    └── 外部依赖延迟
```

### 2.2 核心 KPI 精确定义

#### KPI-1: 任务吞吐量 (Tasks Throughput)

```
定义：单位时间内完成的任务数量
公式：tasks_completed / time_window

粒度：
  hourly_throughput = COUNT(tasks WHERE status='done' AND completed_at IN last_hour)
  daily_throughput  = COUNT(tasks WHERE status='done' AND completed_at IN last_24h)
  weekly_throughput = COUNT(tasks WHERE status='done' AND completed_at IN last_7d)

排除条件：
  - 跳过 cancelled 状态的任务
  - 子任务从父任务维度合并计算（可选模式：raw vs merged）

展示方式：时序折线图 + 同环比
```

#### KPI-2: 任务成功率 (Success Rate)

```
定义：成功完成任务占总完成（done + failed）的比例
公式：done_count / (done_count + failed_count) × 100%

粒度：
  hourly / daily / weekly

注意：
  - blocked 状态不计入（不是终态）
  - cancelled 不计入
  - 考虑区分"Agent 失败"和"用户取消"

告警阈值：success_rate < 80% (daily) → P1
         success_rate < 60% (daily) → P0
```

#### KPI-3: Agent 利用率 (Agent Utilization)

```
定义：Agent 处于 busy 状态的时间占比
公式：SUM(busy_duration) / total_time × 100%

busy_duration 计算方式：
  busy_start = MIN(tasks.started_at) for agent in time_window
  busy_end   = MAX(tasks.completed_at OR NOW()) for agent in time_window
  busy_duration = busy_end - busy_start, 但需减去空闲间隔

简化版（MVP）：
  utilization = COUNT(agent WHERE status='busy') / COUNT(all_agents) AS ratio
  + session_active_count / agent_count AS active_ratio

精确版（后续）：
  需要在 sessions 表中记录 agent 每次"开始处理"和"结束处理"的时间戳，
  做 interval merge 后计算真正的工作时长。

告警阈值：
  utilization < 10% for 2h → "Agent 可能卡死" → P1
  utilization = 100% for 24h → "Agent 可能陷入死循环" → P1
```

#### KPI-4: 平均任务耗时 (Avg Task Duration)

```
定义：从任务开始到结束的平均耗时
公式：AVG(completed_at - started_at) WHERE status IN ('done', 'failed')

粒度：
  per agent / per task_type / per priority

分段统计（更有意义）：
  P50 / P95 / P99 耗时

  SELECT
    agent_id,
    COUNT(*) as total,
    AVG(duration) as avg_ms,
    -- SQLite 不原生支持 percentile，用 Python 侧计算
  FROM tasks
  WHERE status IN ('done','failed')
    AND completed_at >= datetime('now', '-7 days')
  GROUP BY agent_id

告警阈值：
  P95 耗时超过历史均值的 3 倍 → P1
```

#### KPI-5: Token 效率比 (Token Efficiency)

```
定义：单位有效产出消耗的 Token 数
公式：total_token_consumed / tasks_completed

含义：完成一个任务平均要花多少 token。越低越好。

需要区分：
  - raw efficiency: 包含所有任务
  - typed efficiency: 按 task_type 分类（research 类自然消耗更多）

告警阈值：
  单任务 token 消耗超过同类型任务 P95 的 2 倍 → P2（可能 agent 陷入循环）
```

#### KPI-6: 子任务发散度 (Fan-Out Ratio)

```
定义：一个父任务拆分出的子任务数量
公式：COUNT(child_tasks) WHERE parent_task_id = :task_id

统计维度：
  - 平均发散度：AVG(child_count) grouped by agent_id
  - 最大发散度：MAX(child_count) —— 发现异常拆分

告警阈值：
  fan_out > 20 → P1（可能存在不合理的任务拆分）
```

#### KPI-7: 团队健康分 (Team Health Score)

```
这是一条复合指标，作为 CEO 视图的核心数字。

组件（V1 权值）：
  health_score = 
    (active_agent_ratio      × 0.2) +   // 活跃 Agent 比例
    (success_rate_24h        × 0.3) +   // 24h 任务成功率
    (blocked_rate_inv        × 0.3) +   // 1 - 阻塞率（越低越好）
    (no_p0_alert             × 0.2)     // 0 if any P0, 1 if clear

范围：0-100，越高越好
颜色：>= 80 绿 / 50-79 黄 / < 50 红

Dashboard 顶部大数字 + 仪表盘。
```

### 2.3 衍生指标

| 衍生指标 | 公式 | 用途 |
|---------|------|------|
| 阻塞率 | blocked_count / active_count | 发现流程瓶颈 |
| 平均阻塞时长 | AVG(unblocked_at - blocked_at) | 衡量阻塞严重程度 |
| 工具调用错误率 | error_toolcalls / total_toolcalls | 发现 API/工具问题 |
| 知识引用密度 | wiki_access_count / tasks_completed | Agent 是否在规范指引下工作 |
| 记忆召回质量 | avg(memory_search_result_count) | 记忆系统是否有效 |
| 跨层消息密度 | count(spawn + send) / time | 协作活跃度指标 |

### 2.4 指标关联分析框架

```
任务吞吐量 ──正相关── Agent 利用率
    │                    │
    └──弱相关── Token 消耗 ──正相关──┘

任务成功率 ──负相关── 阻塞率
    │                    │
    └──负相关── 工具调用错误率 ──正相关──┘

平均耗时 ──正相关── 子任务发散度 ─── Token 效率比
```

> 关联分析的意义：当某个指标异常时，能沿着关联链快速定位根因。例如：
> - 吞吐量下降 → 先看阻塞率 → 阻塞率正常 → 看利用率 → 利用率低 → 看 Agent 是否 offline
> - Token 暴增 → 看 fan-out → fan-out 正常 → 看单任务 token 效率 → 定位到具体任务

---

## 3. 数据采集链路精密设计

> 采集是地基。数据不完整/不一致，Dashboard 再好看也没用。

### 3.1 数据流全景

```
                    ┌─────────────────────────────────────────────┐
                    │              OpenClaw Gateway                │
                    │                                              │
  User ──────────▶  │  ┌──────┐  ┌──────┐  ┌───────────┐        │
  Message          │  │Agent │  │Hook  │  │Structured │        │
                    │  │Runtime│  │System│  │Log Files  │        │
                    │  └──┬───┘  └──┬───┘  └─────┬─────┘        │
                    │     │         │             │               │
                    └─────┼─────────┼─────────────┼───────────────┘
                          │         │             │
            ┌─────────────┼─────────┼─────────────┼───────────────┐
            │             ▼         ▼             ▼               │
            │    ┌────────────┐ ┌─────────┐ ┌───────────┐        │
            │    │ taskboard  │ │Hook     │ │Log Parser │        │
            │    │ CLI        │ │Handler  │ │Daemon     │        │
            │    │(Agent 调用)│ │(实时事件)│ │(轮询日志) │        │
            │    └─────┬──────┘ └────┬────┘ └─────┬─────┘        │
            │          │             │            │               │
            │          ▼             ▼            ▼               │
            │    ┌─────────────────────────────────────┐         │
            │    │           SQLite (WAL mode)          │         │
            │    │  agents | tasks | sessions |         │         │
            │    │  tool_calls | memory_ops |           │         │
            │    │  wiki_access | alerts                │         │
            │    └────────────────┬────────────────────┘         │
            │                     │                              │
            │    ┌────────────────▼────────────────────┐         │
            │    │          FastAPI Server              │         │
            │    │  /api/agents  /api/tasks  /api/tokens│         │
            │    └────────────────┬────────────────────┘         │
            │                     │                              │
            │              ngrok tunnel / LAN                    │
            │                     │                              │
            │    ┌────────────────▼────────────────────┐         │
            │    │     Dashboard (GitHub Pages)         │         │
            │    │     HTML + Chart.js + fetch()        │         │
            │    └─────────────────────────────────────┘         │
            │                                                    │
            └─── 数据采集层 ──────────────────────────────────────┘
```

### 3.2 每条数据的采集链路

| 数据项 | 产生源 | 采集方式 | 链路 | 频率 | 延迟 |
|-------|--------|---------|------|------|------|
| Agent 注册/上线 | Agent Bootstrap | Hook: `agent:bootstrap` | Hook Handler → SQLite | 事件驱动 | < 1s |
| Agent 下线 | Gateway 关闭 / Agent 结束 | Log Parser 检测无活动 | Log Parser → SQLite | 30s 对账 | < 30s |
| 任务创建 | 用户消息 → Agent 解析 | Agent 调 `taskboard task create` | taskboard CLI → SQLite | Agent 决定 | < 1s |
| 任务状态变更 | Agent 执行关键节点 | Agent 调 `taskboard task update` | taskboard CLI → SQLite | Agent 决定 | < 1s |
| Session 开始 | Gateway 创建 session | Log Parser 匹配 lifecycle:start | Log Parser → SQLite | 2s 轮询 | < 3s |
| Session 结束 | Gateway 关闭 session | Log Parser 匹配 lifecycle:end | Log Parser → SQLite | 2s 轮询 | < 3s |
| Session token 消耗 | lifecycle:end 中的 usage 字段 | Log Parser 提取 | Log Parser → SQLite | 事件驱动 | < 3s |
| Tool Call | Agent 调工具 | Log Parser 匹配 tool_call event | Log Parser → SQLite | 2s 轮询 | < 3s |
| Memory 操作 | Agent 调 memory_search/get | Hook: 可扩展 | 待 Phase 4 | 按需 | < 1s |
| Wiki 访问 | Agent 使用 read 工具读 ai_wikis | Log Parser 解析 tool=read | Log Parser → SQLite | 2s 轮询 | < 3s |
| Spawn 事件 | Agent 调 sessions_spawn | Log Parser 匹配 tool_call | Log Parser → SQLite | 2s 轮询 | < 3s |
| 告警触发 | Supervisor 或 Log Parser | 直接写入 alerts 表 | Python → SQLite | 30s 检查 | < 30s |

### 3.3 采集方式选择决策树

```
数据需要语义理解吗？
├── 是（例如"这个任务因用户等待被阻塞"）
│   └── Agent 自主上报（taskboard CLI）
│       理由：只有 Agent 自己知道为什么被阻塞
│       风险：Agent 不稳定可能不上报
│       缓解：Supervisor 对账兜底
│
└── 否（例如"Agent 调用了 web_search"）
    ├── 是生命周期事件（session start/end）？
    │   └── Log Parser
    │       理由：Gateway 保证日志完整，外部解析可靠
    │
    ├── 需要实时性（< 2s）？
    │   └── Hook
    │       理由：事件驱动，不依赖轮询
    │       限制：OpenClaw Hook 能力有限，不是所有事件都能 Hook
    │
    └── 不要求实时性
        └── Log Parser（主力采集方式）
            理由：最可靠，外部观察，不依赖 Agent 行为
            成本：2s 延迟可接受
```

### 3.4 Hybrid 采集机制的协同

三种采集方式不是互斥的，而是**互补验证**：

```
┌─────────────────────────────────────────────────────┐
│                 同一事件可能被多方采集                  │
│                                                       │
│  例：Task 完成                                        │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐│
│  │ Agent 上报   │  │ Log Parser   │  │ Supervisor  ││
│  │ "done"       │  │ 检测到       │  │ 对账验证    ││
│  │ + summary    │  │ session 结束 │  │ 一致性      ││
│  └──────┬───────┘  └──────┬───────┘  └──────┬──────┘│
│         │                  │                  │       │
│         ▼                  ▼                  ▼       │
│  语义信息         客观事件               纠错        │
│  (只有 Agent      (Log Parser            (解决冲突   │
│   知道为什么)      保证不丢)             以客观为准) │
└─────────────────────────────────────────────────────┘
```

#### 对账规则

```python
# Supervisor 对账伪代码
def reconcile():
    # 规则 1: Agent 报 done，但 session 还在 → stale
    tasks_done_no_session = query("""
        SELECT t.id FROM tasks t
        LEFT JOIN sessions s ON t.id = s.task_id
        WHERE t.status = 'done' AND s.status = 'active'
    """)
    for t in tasks_done_no_session:
        mark_as('stale', reason='agent-reported-done-but-session-active')

    # 规则 2: Session 已结束，任务仍 in_progress → 补标记
    tasks_lost = query("""
        SELECT t.id FROM tasks t
        JOIN sessions s ON t.id = s.task_id
        WHERE t.status = 'in_progress' AND s.status = 'completed'
    """)
    for t in tasks_lost:
        # session 正常结束 → done; session error → failed
        mark_as('done' if s.status == 'completed' else 'failed',
                reason='auto-resolved-by-session-lifecycle')

    # 规则 3: Agent 30 分钟无 tool call → stuck
    stuck_agents = query("""
        SELECT t.agent_id, t.id FROM tasks t
        WHERE t.status = 'in_progress'
          AND t.id NOT IN (
            SELECT DISTINCT tc.session_id
            FROM tool_calls tc
            WHERE tc.created_at >= datetime('now', '-30 minutes')
          )
    """)
    for t in stuck_agents:
        mark_as('stuck', reason='no-tool-call-30min')
```

### 3.5 数据完整性和补全

| 风险场景 | 检测方式 | 补全策略 |
|---------|---------|---------|
| 任务创建了但 session 未关联 | 定期扫描 orphan tasks | 通过 agent_id + 时间窗口模糊匹配 |
| Token 数据缺失 | session 结束但 usage 为空 | 从 tool_calls 估算 token_cost 求和 |
| Agent 上报失败 | taskboard 写入异常 | taskboard 内部重试 3 次，失败后写日志 |
| Log Parser 漏行 | 文件轮转 / 日志格式变更 | checkpoint 机制 + 启动时全量扫描缺失段 |
| 时区混乱 | SQLite 用 datetime('now') | 统一存储 UTC，展示层转 Asia/Shanghai |

### 3.6 隐私和安全边界

| 数据 | 存储 | 理由 |
|------|------|------|
| Agent 对话内容 (prompt/completion) | ❌ 不存储 | 隐私风险 + 存储太大 |
| Tool call 参数 | ⚠️ 仅摘要前 200 字符 | 够排查用，不存敏感信息 |
| Tool call 结果 | ⚠️ 仅摘要前 200 字符 | 同上 |
| 任务描述 (task title/desc) | ✅ 完整存储 | 维度分析需要 |
| Token 数量 | ✅ 完整存储 | 成本和效率分析必须 |
| Agent ID / Session ID | ✅ 完整存储 | 核心标识 |
| 时间戳 | ✅ 完整存储 | 分析基础 |

---

## 4. Dashboard 展示方案

> Dashboard 不是"一张大屏把所有数据怼上去"，而是"带着问题来，带着答案走"。

### 4.1 四种视图，四种目的

```
┌──────────────────────────────────────────────────────────────┐
│  View 1: 总览视图 (Overview)    │  View 2: 运营视图 (Ops)     │
│  ─────────────────────────────  │  ─────────────────────────  │
│  For: CEO, CTO 日常             │  For: CTO, VP 深度          │
│  Goal: 3 秒判断有没有问题       │  Goal: 发现瓶颈、优化资源   │
│  Content: 健康分 + 告警 + 简要  │  Content: 吞吐量趋势 +      │
│           任务状态 + Token 汇总  │          成本归因 + 阻塞详情 │
├─────────────────────────────────┼─────────────────────────────┤
│  View 3: 排查视图 (Trace)       │  View 4: 历史分析 (History) │
│  ─────────────────────────────  │  ─────────────────────────  │
│  For: CTO, 专家 排查问题        │  For: 所有人 复盘            │
│  Goal: 追踪一个任务的全链路     │  Goal: 趋势对比、异常发现    │
│  Content: 时间线 + Tool Chain + │  Content: 对比图 + 排行榜 +  │
│           Spawn Tree + 耗时分析  │          周期报告            │
└──────────────────────────────────────────────────────────────┘
```

### 4.2 View 1: 总览视图 (Overview)

```
┌──────────────────────────────────────────────────────────────┐
│  🏠 CHANG_AI_TEAM Dashboard                   2026-06-06 14:30 │
├──────────┬──────────┬──────────┬──────────┬──────────────────┤
│  💚 87   │   5      │   12     │   -3%   │  ¥12.35          │
│  健康分  │ 活跃Agent│ 今日任务 │ Token环比│  今日成本        │
├──────────┴──────────┴──────────┴──────────┴──────────────────┤
│                                                               │
│  🚨 告警 (1)                                                  │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │ ⚠️ P1 · expert-perf-agent · 45min 无响应 · 3 分钟前     │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                               │
│  📊 任务概览                   📈 Token 消耗 (7 天)           │
│  ┌────────────────────┐     ┌────────────────────────────┐   │
│  │ done:  ████████ 12 │     │      ╱╲                     │   │
│  │ active: ████    5  │     │  ╱──╱  ╲──╲     ╱╲        │   │
│  │ blocked:██     1  │     │ ╱        ╲   ╲──╱  ╲──╲   │   │
│  │ failed: █      1  │     │╱                   ╲──╱    │   │
│  └────────────────────┘     └────────────────────────────┘   │
│                                                               │
│  👥 Agent 状态                                          [展开] │
│  ┌──────────┬─────────┬───────┬──────────┬─────────────────┐ │
│  │ Agent    │ 状态    │ 任务数 │ Token/日 │ 最后活动        │ │
│  ├──────────┼─────────┼───────┼──────────┼─────────────────┤ │
│  │ CTO      │ 🟢 idle │   3   │  45K     │ 2 分钟前        │ │
│  │ Expert·Infra│ 🟡 busy│  2   │  32K     │ 12 分钟前       │ │
│  │ RD-Kafka │ 🟢 idle │   0   │   8K     │ 1 小时前        │ │
│  │ Expert·Perf│ 🔴 stuck│  1   │  28K     │ 45 分钟前       │ │
│  └──────────┴─────────┴───────┴──────────┴─────────────────┘ │
│                                                               │
│  View: [● 总览] [ 运营 ] [ 排查 ] [ 历史 ]                    │
└──────────────────────────────────────────────────────────────┘
```

**特点：**
- 顶部 4 个数字卡片，一眼看出核心状态
- 告警区固定在第二行，P0/P1 不折叠
- 任务概览用简单条形图，Token 用迷你折线图
- Agent 列表默认显示前 5 个，其余折叠

### 4.3 View 2: 运营视图 (Ops)

```
┌──────────────────────────────────────────────────────────────┐
│  🔧 运营视图                                    时间范围 [7d ▼]│
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  📊 任务吞吐量                            📊 任务成功率       │
│  ┌────────────────────────────────┐  ┌─────────────────────┐ │
│  │  12 ┤     ╭╮                   │  │ 100% ┤───●──●──●    │ │
│  │  10 ┤   ╭─╯╰╮  ╭╮             │  │  80% ┤      ╲ ╱     │ │
│  │   8 ┤ ╭─╯   ╰──╯╰╮            │  │  60% ┤       ●      │ │
│  │   6 ┤─╯          ╰──╮         │  │        Mon Tue Wed… │ │
│  │       M  T  W  T  F  S  S     │  └─────────────────────┘ │
│  └────────────────────────────────┘                          │
│                                                               │
│  💰 Token 消耗归因                        💰 按项目成本       │
│  ┌──────────────────────────────┐  ┌───────────────────────┐ │
│  │ CTO:     ████████ 28%       │  │ Kafka调研:  ████ 35% │ │
│  │ Infra:   ██████   22%       │  │ Agent基建: ███  25%  │ │
│  │ Perf:    ████     16%       │  │ 技术周报:  ██   15%  │ │
│  │ SRE:     ██        8%       │  │ 其他:      ███  25%  │ │
│  │ Worker:  ██████   26%       │  └───────────────────────┘ │
│  └──────────────────────────────┘                            │
│                                                               │
│  🚧 阻塞明细                                                │
│  ┌──────────┬──────────────┬──────────┬───────────────────┐ │
│  │ 任务     │ 阻塞原因     │ 阻塞时长  │ Agent             │ │
│  ├──────────┼──────────────┼──────────┼───────────────────┤ │
│  │ KIP调研  │ 等待用户确认  │ 2h 15m   │ expert-infra     │ │
│  │ 部署方案 │ 等待PR review │ 45m      │ expert-sre       │ │
│  └──────────┴──────────────┴──────────┴───────────────────┘ │
│                                                               │
│  View: [ 总览 ] [● 运营] [ 排查 ] [ 历史 ]                    │
└──────────────────────────────────────────────────────────────┘
```

**特点：**
- 双列布局：左侧图表，右侧归因
- 时间范围可切换（今日/本周/本月/自定义）
- 阻塞区显示所有活跃阻塞，按阻塞时长排序
- 成本归因支持按 Agent 层级和按项目两个维度

### 4.4 View 3: 排查视图 (Trace)

```
┌──────────────────────────────────────────────────────────────┐
│  🔍 任务追踪                        [输入 task_id 或 agent 搜索]│
├──────────────────────────────────────────────────────────────┤
│  任务: KIP-1279 集群镜像调研 #task-a1b2c3                       │
│  Agent: expert-infra-agent    状态: done    耗时: 2h 15m      │
│  Token: 48,500    子任务: 2    创建: 06-06 09:00              │
│                                                               │
│  ⏱️ Timeline                                                  │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │ 09:00 ● 任务创建 (expert-infra 收到 CTO 指令)             │ │
│  │ 09:01 ● web_search "KIP-1279" ──────── 0.8s ── ✅        │ │
│  │ 09:02 ● web_fetch apache-kafka-kip ─── 2.1s ── ✅        │ │
│  │ 09:05 ● read 本地Kafka文档 ─────────── 0.1s ── ✅        │ │
│  │ 09:10 ● sessions_spawn → RD-Kafka ─── 0.3s ── ✅         │ │
│  │         └── 📤 子任务 #bb2c3d "翻译KIP原文"               │ │
│  │ 09:15 ● memory_search "Kafka" ─────── 0.4s ── ✅ 3 hits  │ │
│  │ 10:30 ● sessions_spawn → RD-Kafka ─── 0.3s ── ✅         │ │
│  │         └── 📤 子任务 #cc3d4e "对比KIP实现"               │ │
│  │ 11:00 ● 子任务 #bb2c3d 完成 ✅                             │ │
│  │ 11:15 ● 子任务 #cc3d4e 完成 ✅                             │ │
│  │ 11:15 ● read 子任务输出 ──────────── 0.1s ── ✅           │ │
│  │ 11:15 ● taskboard update --status done                   │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                               │
│  🌳 Spawn 树                                                  │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │ expert-infra-agent (task #a1b2c3, 48.5K tokens)          │ │
│  │  ├── RD-Kafka (task #bb2c3d, 12.3K tokens) ✅            │ │
│  │  └── RD-Kafka (task #cc3d4e, 18.7K tokens) ✅            │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                               │
│  📈 耗时分布                                                  │
│  Tool Calls: ████████░░ 8.4s (3%)                            │
│  等待子任务: ████████████████████████████████████ 1h45m (78%) │
│  自身处理:   ██████░░ 26m (19%)                               │
│                                                               │
│  View: [ 总览 ] [ 运营 ] [● 排查] [ 历史 ]                     │
└──────────────────────────────────────────────────────────────┘
```

**特点：**
- 上半部分是 Timeline，按时间轴排列所有事件
- 每个 tool call 显示耗时和结果状态
- Spawn 树展示父子任务关系 + Token 归因
- 耗时分布饼图帮你一眼看出时间花在哪
- 支持输入任意 task_id / agent_id 跳转

### 4.5 View 4: 历史分析视图 (History)

```
┌──────────────────────────────────────────────────────────────┐
│  📈 历史分析                                   周期 [本周 ▼]   │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌─ 对比面板 ────────────────────────────────────────────┐   │
│  │         本周        上周        环比                    │   │
│  │ 任务数   12          9          +33% ▲                 │   │
│  │ 成功率   91.7%       88.9%      +2.8% ▲                │   │
│  │ Token   352K        298K        +18% ▲                 │   │
│  │ 阻塞率   8.3%        22.2%      -13.9% ▼               │   │
│  │ 健康分   87          72          +15 ▲                  │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                               │
│  📊 任务吞吐量趋势 (30天)                                      │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  15 ┤    ╭╮        ╭╮                                  │  │
│  │  12 ┤ ╭──╯╰──╮  ╭──╯╰╮    ╭╮                          │  │
│  │   9 ┤─╯      ╰──╯    ╰────╯╰────────                  │  │
│  │   6 ┤                                                   │  │
│  │      W1    W2    W3    W4    (虚线 = 7日均线)           │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                               │
│  🏆 Agent 排行榜 (本周)                                       │
│  ┌──────┬───────────────┬────────┬────────┬──────────────┐  │
│  │ 排名 │ Agent         │ 完成任务│ 成功率 │ Token 效率   │  │
│  ├──────┼───────────────┼────────┼────────┼──────────────┤  │
│  │ 🥇  │ RD-Kafka       │   5    │ 100%   │ 8.2K/task    │  │
│  │ 🥈  │ expert-infra   │   4    │ 100%   │ 12.1K/task   │  │
│  │ 🥉  │ expert-perf    │   2    │  67%   │ 28.4K/task   │  │
│  │  4  │ RD-Web         │   1    │ 100%   │  5.6K/task   │  │
│  └──────┴───────────────┴────────┴────────┴──────────────┘  │
│                                                               │
│  🔥 工具调用热点图 (本周)                                     │
│  ┌────────────────────────────────────────────────────────┐  │
│  │ web_search     ████████████████████████ 45%            │  │
│  │ web_fetch      ██████████████ 28%                      │  │
│  │ read           ████████ 15%                            │  │
│  │ exec           ████ 8%                                 │  │
│  │ sessions_spawn ██ 4%                                   │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                               │
│  📋 异常检测日志 (异常任务/异常耗时/异常 Token)                │
│  ┌──────────┬──────────────┬────────────────┬────────────┐  │
│  │ 时间     │ 任务         │ 异常类型       │ 详情        │  │
│  ├──────────┼──────────────┼────────────────┼────────────┤  │
│  │ 06-05    │ 部署方案     │ P95 耗时超 3x  │ 2.5h vs    │  │
│  │          │              │                │ 历史 45m   │  │
│  │ 06-04    │ KIP调研      │ Token 超 P95   │ 48K vs     │  │
│  │          │              │ 2x             │ 历史 22K   │  │
│  └──────────┴──────────────┴────────────────┴────────────┘  │
│                                                               │
│  View: [ 总览 ] [ 运营 ] [ 排查 ] [● 历史]                    │
└──────────────────────────────────────────────────────────────┘
```

**特点：**
- 对比面板：本周 vs 上周，环比指标
- 30 天趋势图 + 7 日均线
- Agent 排行榜支持多种排序（完成任务/成功率/效率）
- 工具调用分布 + 异常检测日志

### 4.6 数据刷新策略

| 视图区域 | 刷新频率 | 刷新方式 | 说明 |
|---------|---------|---------|------|
| 健康分卡片 | 10s | 全量轮询 | 需要感知状态变化 |
| 告警区 | 10s | 增量轮询 | 新告警立刻出现 |
| 任务概览 | 10s | 全量轮询 | 数据量小 |
| Token 趋势图 | 60s | 全量轮询 | 数据变化慢 |
| Agent 列表 | 10s | 全量轮询 | 需要感知状态 |
| 阻塞明细 | 30s | 全量轮询 | 变化不频繁 |
| 排查视图 Timeline | 手动刷新 | 按需 | 进入页面时加载 |
| 历史对比面板 | 手动 / 日刷新 | 按需 | 汇总数据 |

### 4.7 技术约束

- **纯静态 HTML**：无后端渲染，所有数据通过 `fetch()` 从 FastAPI 拉取 JSON
- **暗色主题**：默认暗色，CSS 变量支持未来切换亮色
- **Chart.js CDN**：图表库，足够轻量（~60KB gzip）
- **无 WebSocket**：轮询足够，避免额外基础设施
- **移动端**：Viewport 自适应，看板列变为垂直堆叠
- **性能预算**：首页加载 < 2s（含数据），API 响应 < 200ms

---

## 5. 告警规则设计

> 告警不是用来吓人的，是用来"把人叫到该看的地方"。
> 好的告警系统有三个特征：精准（不误报）、及时（不迟到）、可操作（知道该做什么）。

### 5.1 告警分级

| 级别 | 名称 | 含义 | 通知方式 | 响应要求 |
|------|------|------|---------|---------|
| **P0** | 紧急 | 影响系统核心功能，需要立即介入 | 飞书强通知（@CTO）+ Dashboard 红色闪烁 | 5 分钟内响应 |
| **P1** | 警告 | 影响单个 Agent/任务，暂不影响全局 | 飞书普通消息 + Dashboard 黄色标记 | 1 小时内处理 |
| **P2** | 提示 | 效率退化、成本异常，不需要立即处理 | 每日汇总消息 + Dashboard 灰色标记 | 下次周复盘关注 |

### 5.2 告警规则清单

#### P0 告警（紧急）

| 规则 ID | 触发条件 | 检测方式 | 检测频率 | 自动恢复条件 |
|---------|---------|---------|---------|------------|
| P0-01 | 所有 Agent 同时 offline | Supervisor 对账：COUNT(agent WHERE status!='offline') = 0 | 30s | 任 1 Agent 上线 |
| P0-02 | 连续 5 个任务全部 failed | Supervisor 统计：最近 5 个 created 任务 status 全是 failed | 任务创建时 | 出新 done 任务 |
| P0-03 | Token 消耗暴增（1h 内 > 日均 5 倍） | Log Parser：tokens_last_hour > avg_daily_hourly × 5 | 10min | 下一个小时恢复正常 |
| P0-04 | SQLite 损坏 / API 不可达 | Health check：FastAPI /api/health 返回非 200 | 30s | 连续 3 次 200 |

#### P1 告警（警告）

| 规则 ID | 触发条件 | 检测方式 | 检测频率 | 自动恢复条件 |
|---------|---------|---------|---------|------------|
| P1-01 | 单 Agent 30 分钟无 tool call 且状态 in_progress | Supervisor 对账 | 30s | Agent 发出下一个 tool call |
| P1-02 | 单 Agent 利用率 60 分钟持续 100% | Supervisor 计算 busy_duration | 60s | 利用率回落 |
| P1-03 | 任务成功率（24h）< 80% | Supervisor 每日统计 | 每小时 | 成功率回到 80%+ |
| P1-04 | 单任务阻塞超过 4 小时 | Supervisor 扫描 task blocked_at | 5min | 任务解除阻塞 |
| P1-05 | Fan-out > 20（异常子任务拆分） | Agent 上报时检查 child_count | 每次 spawn | 人工确认后关闭 |
| P1-06 | 连续 3 次 taskboard 上报失败 | taskboard CLI 内部重试计数 | 每次调用 | 下一次成功 |

#### P2 告警（提示）

| 规则 ID | 触发条件 | 检测方式 | 检测频率 | 自动恢复条件 |
|---------|---------|---------|---------|------------|
| P2-01 | 单任务 Token 消耗 > 同类型 P95 × 2 | 任务完成后比对历史数据 | 任务完成时 | 一次性告警 |
| P2-02 | 工具调用错误率 > 20% (daily) | Supervisor 每日统计 | 每小时 | 错误率回落 |
| P2-03 | 知识引用密度下降 > 50% (周环比) | Supervisor 每周统计 | 每日 | 指标恢复 |
| P2-04 | 日均 Token 成本超预算 120% | 每日汇总 | 每日 | 次月预算重置 |

### 5.3 告警通知格式

```
P0 告警格式（飞书强通知）：
┌────────────────────────────────────────┐
│ 🚨 P0 告警：Agent 全离线               │
│                                         │
│ 时间：2026-06-06 14:32:15               │
│ 详情：检测到 5 个 Agent 全部处于 offline │
│       状态，Gateway 可能已重启或异常。   │
│ 影响：所有任务暂停执行                  │
│ 建议：检查 OpenClaw Gateway 状态        │
│       运行：openclaw gateway status     │
│                                         │
│ [查看 Dashboard] [静默 30min] [确认处理] │
└────────────────────────────────────────┘

P1 告警格式：
┌────────────────────────────────────────┐
│ ⚠️ P1：expert-perf-agent 可能卡住      │
│                                         │
│ 45 分钟无 tool call，状态仍为 in_progress│
│ 任务：性能基准测试调研                   │
│ [查看任务详情]                           │
└────────────────────────────────────────┘

P2 每日汇总格式（飞书卡片消息）：
┌────────────────────────────────────────┐
│ 📋 每日可观测性摘要 · 2026-06-06        │
│                                         │
│ ✅ 健康分：87（环比 +3）                 │
│ ℹ️ P2 提示：                            │
│   · KIP调研 task 消耗 48K（同类型P95 × 2）│
│   · Token 成本本月累计 ¥156 / 预算 ¥200 │
│                                         │
│ [查看完整报告]                          │
└────────────────────────────────────────┘
```

### 5.4 告警抑制规则

避免告警风暴：

| 规则 | 说明 |
|------|------|
| **相同告警 5 分钟内不重复** | 同一 rule + 同一 target 的告警，5min 内只发一次 |
| **静默期** | P1/P2 在用户手动 "静默 30min" 后暂停 |
| **依赖关系抑制** | 如果 P0-01（全离线）已触发，P1-01（单 Agent 无响应）不再发送（原因相同） |
| **夜间降级** | 22:00-08:00 期间，P1 降级为 P2（静默存储），P0 不受影响 |
| **恢复通知合并** | 同类型告警恢复后，发送汇总恢复通知而非逐条 |

### 5.5 告警数据模型

```sql
CREATE TABLE alerts (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    rule_id     TEXT NOT NULL,              -- 'P0-01'
    level       TEXT NOT NULL,              -- 'P0' | 'P1' | 'P2'
    target      TEXT NOT NULL,              -- agent_id | 'system'
    title       TEXT NOT NULL,
    detail      TEXT,
    status      TEXT DEFAULT 'active',      -- 'active' | 'resolved' | 'silenced'
    silenced_until TEXT,                    -- 静默截止时间
    created_at  TEXT DEFAULT (datetime('now')),
    resolved_at TEXT,
    resolved_by TEXT                        -- 'auto' | 'manual' | 'supervisor'
);

CREATE INDEX idx_alerts_status ON alerts(status);
CREATE INDEX idx_alerts_level ON alerts(level);
CREATE INDEX idx_alerts_created ON alerts(created_at);
```

---

## 6. 实施建议

### 6.1 与其他 Phase 的关系

```
Phase 4: 可观测性 MVP  ──本设计──▶ Phase 5: Dashboard 前端
   │                                    │
   ├── Log Parser 守护进程              ├── View 1: 总览
   ├── SQLite Schema 建表               ├── View 2: 运营
   ├── taskboard CLI                    ├── View 3: 排查
   ├── Supervisor 对账                   ├── View 4: 历史
   └── FastAPI 数据服务                  └── 告警集成
```

### 6.2 MVP 分步交付

**Sprint 1（3 天）：数据就绪**
- SQLite schema 创建（含 alerts 表）
- Log Parser 最小原型（session lifecycle + tool_call 两路）
- 手动运行一次验证数据写入

**Sprint 2（3 天）：CLI + API 上线**
- `taskboard` CLI 实现（task create/update + agent register）
- FastAPI 服务搭建（/api/tasks, /api/agents, /api/tokens）
- ngrok 隧道验证

**Sprint 3（2 天）：Supervisor + 告警**
- Supervisor 对账脚本（30s cron）
- 告警逻辑实现（P0/P1 规则）
- 飞书通知集成

**Sprint 4（3 天）：Dashboard 前端**
- View 1 总览视图（健康分 + Agent 列表 + 告警区）
- View 2 运营视图（趋势图 + 成本归因）
- 部署 GitHub Pages

**Sprint 5（后续）：增强视图**
- View 3 排查视图（Timeline + Spawn Tree）
- View 4 历史分析（对比 + 排行榜 + 异常检测）

### 6.3 可观测性自身也要可观测

```
┌─────────────────────────────────┐
│ 可观测性系统的可观测性          │
│                                 │
│ /api/health                     │
│   ├── db_ok: true/false         │
│   ├── log_parser_alive: true    │
│   ├── last_event_at: timestamp  │
│   └── events_24h: count         │
│                                 │
│ 如果采集器自己挂了 → P0-04 触发│
└─────────────────────────────────┘
```

---

## 附录 A: 现有设计 vs 深度设计 对比

| 维度 | 现有设计 (v0.1/v0.2) | 深度设计 (本文) |
|------|---------------------|----------------|
| 观测需求 | 笼统列举"需要观测什么" | 按角色 × 场景 × 时间三维度分层，产出观测需求矩阵 |
| 指标定义 | 无 | 7 个核心 KPI 精确定义 + 计算公式 + 衍生指标 + 关联分析框架 |
| 数据采集 | Hybrid 机制概念 | 每条数据源的完整链路图 + 采集方式决策树 + 对账规则伪代码 |
| Dashboard | 概念性描述"Kanban + 趋势图" | 4 种视图完整 ASCII 布局 + 数据刷新策略 + 技术约束 |
| 告警 | 未涉及 | 三级告警体系 + 13 条规则 + 抑制规则 + 通知格式 + 数据模型 |
| 实施 | Phase 里程碑 | Sprint 级拆分 + 分步交付建议 |

## 附录 B: 关键风险

| 风险 | 概率 | 影响 | 缓解 |
|------|------|------|------|
| Log Parser 遗漏 lifecycle 事件 | 中 | 高 | Supervisor 对账补全；启动时全量扫描 |
| Agent 不调用 taskboard | 中 | 高 | Log Parser 兜底关键状态；prompt 强化 |
| SQLite 文件增长过大 | 低 | 中 | 定期 VACUUM；tool_calls 表保留 90 天 |
| Dashboard 轮询过频影响性能 | 低 | 低 | 缓存层（FastAPI 缓存 5s）；分区域降低频率 |
| 告警过多导致麻木 | 中 | 中 | 抑制规则 + 夜间降级 + 阈值持续调优 |

## 附录 C: 与五维度框架的关系

```
可观测性 验证 ──▶ 工作流（任务是否按预期流转？）
                记忆管理（记忆检索是否有效？）
                知识管理（规范是否被查阅？）
                可靠性（Supervisor 是否正常工作？）

可观测性 是其他四个维度的"眼睛"，也是"裁判"。
```

---

## 相关链接

- [[设计文档]] — 五维度框架主文档
- [[phase3-knowledge-management]] — 知识管理方案
- [[关于agent基建的一些思考]] — Frank 的原始思考
- `ai_memory_chang_ai_team/tech_designs/agent-infra/observability-dashboard.html` — v0.1 HTML 设计

> [!note] 文档状态
> v0.1 · 2026-06-06 · CTO 初稿。待 CEO/团队 Review。
> 下一步：收到 Review 反馈 → 精调后进入 Phase 4 Sprint 1 实施。