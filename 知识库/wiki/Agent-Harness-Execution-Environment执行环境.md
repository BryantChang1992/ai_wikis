---
type: concept
title: "Agent Harness: Execution Environment & Sandbox (E)"
sources:
  - "sources/papers/Agent-Harness-Engineering-Survey/Agent-Harness-Engineering-Survey-OpenReview2026.pdf"
  - "sources/papers/Agent-Harness-Engineering-Survey/精读分析.md"
tags:
  - "Agent-Harness"
  - "Agent基础设施"
  - "沙箱"
  - "AI-Infra"
created: 2026-06-20
updated: 2026-06-20
status: draft
related:
  - "[[Agent-Harness-Engineering-Survey综述]]"
  - "[[Agent-Sandbox-安全沙箱选型]]"
  - "[[Anthropic-Agent安全容器化实践]]"
---

# Agent Harness: Execution Environment & Sandbox (E)

> ETCLOVG 第一层：Agent 的执行基板——提供安全边界、重置机制和限定的行动区域。

---

## 1. 层级定位

Execution Environment 是 Agent Harness 的**物理基板**。它提供三个核心功能：

1. **安全边界**：Agent 可行动的最大范围
2. **重置机制**：可复制评估和训练的干净状态恢复
3. **限定行动区域**：长期 Agent 无需人工批准即可行动的范围

设计空间不再由单一隔离原语主导，而是由**工作负载保真度、威胁模型和运营模式**三者共同决定。

---

## 2. 七大沙箱类别

### 2.1 Computer-Use Agent Infrastructure（桌面级）

| 维度 | 详情 |
|------|------|
| 定位 | 为 Agent 提供接近真实桌面的操作环境 |
| 代表系统 | Claude Computer Use (Anthropic), OpenAI Operator |
| 隔离级别 | VM 级或强容器隔离 |
| 典型场景 | 桌面自动化、GUI 操作、跨应用任务 |
| 风险 | 真实操作系统意味着更大的逃逸面——需要 VM 级隔离 |
| 设计权衡 | 真实性强但启动慢、镜像大、状态管理复杂 |

### 2.2 Code-Specialized Sandboxes（代码专用）

| 维度 | 详情 |
|------|------|
| 定位 | 为代码生成/修复/测试定制的轻量执行环境 |
| 代表系统 | SWE-bench Docker, R2E, OpenHands, SWE-agent |
| 隔离级别 | Docker 容器或等价 |
| 典型场景 | 代码评估、自动修复、测试运行 |
| 核心设计 | 预装工具链（Python/Node/Go）+ 仓库快照 + 标准化的依赖管理 |
| 关键挑战 | 包版本差异影响评估再现性；Docker 镜像缓存和预构建优化 |

### 2.3 Framework-Integrated Runtimes（框架集成）

| 维度 | 详情 |
|------|------|
| 定位 | 作为 Agent 框架的一部分捆绑的运行时 |
| 代表系统 | LangChain (LocalSandbox), AutoGen (DockerRuntime), CrewAI |
| 隔离级别 | 框架级（可选 Docker 后端） |
| 典型场景 | 框架内的快速原型和工具调用 |
| 核心风险 | 默认隔离弱，开发者容易在生产中忽略安全配置 |
| 设计趋势 | "Bundle vs. Compose" 之争：框架打包 vs. 独立沙箱服务组合 |

### 2.4 Browser Evaluation Environments（浏览器环境）

| 维度 | 详情 |
|------|------|
| 定位 | 为 Web Agent 评估定制的浏览器沙箱 |
| 代表系统 | BrowserGym, WebArena, VisualWebArena, WorkArena |
| 隔离级别 | 浏览器级 + 可选网络隔离 |
| 典型场景 | Web 任务自动化、UI 交互评估 |
| 核心设计 | 标准化的浏览器状态管理、DOM 快照、操作录制 |
| 独特挑战 | 浏览器版本差异、CDP 协议稳定性、动态网页的不可复制性 |

### 2.5 OS-Level Permission Sandboxes（OS 内核级）

| 维度 | 详情 |
|------|------|
| 定位 | 通过操作系统级权限边界的细粒度隔离 |
| 代表系统 | Progent（进程级权限）, IsolateGPT, SAFEFLOW |
| 隔离级别 | OS 内核级（seccomp, capability, namespace） |
| 典型场景 | 高风险 Agent 部署、多租户环境 |
| 核心设计 | 文件系统访问控制、网络 egress 限制、syscall 过滤 |
| 独特价值 | 绕过容器层直接控制内核权限——防御纵深中最内层 |

### 2.6 Managed Sandbox Platforms（托管平台）

| 维度 | 详情 |
|------|------|
| 定位 | 云托管、开箱即用的沙箱服务 |
| 代表系统 | E2B, Daytona, CodeSandbox, Replit |
| 隔离级别 | 托管 VM/容器 |
| 典型场景 | 生产级 Agent 部署、SaaS 集成 |
| 核心优势 | 不需运维、弹性扩展、预置安全策略 |
| 权衡 | 厂商锁定、网络延迟、成本随规模增长 |

### 2.7 Sandbox Abstraction Layers（抽象层）

| 维度 | 详情 |
|------|------|
| 定位 | 在多种沙箱实现之上的统一接口 |
| 代表系统 | Composio, AgentConnect |
| 隔离级别 | 取决于后端 |
| 典型场景 | 跨平台的工具/沙箱编排 |
| 核心价值 | 解耦 Agent 代码与沙箱实现——支持"一次编写，多后端运行" |
| 局限 | 抽象层的"最小公分母"效应——高级特性在各后端间不统一 |

---

## 3. 核心挑战

### 3.1 沙箱逃逸（Sandbox Escape）

**SandboxEscapeBench**（Marchand et al., 2026）表明前沿模型可在现实配置下利用沙箱弱点：
- 多层嵌套的符号链接
- 内核版本特定的漏洞
- 共享卷和 sidecar 容器的配置错误
- 防御工作分散在不同威胁模型和评估协议之间，尚未统一

### 3.2 可复制性 vs. 真实性

| 维度 | 真实环境 | 简化环境 |
|------|----------|----------|
| 任务成功率 | 更高（现实因素） | 更低 |
| 评估再现性 | 低（镜像差异、网络波动、第三方服务变更） | 高 |
| 启动延迟 | 分钟级 | 秒级 |
| 适合场景 | 生产部署 | 批量评估 |

### 3.3 规模化挑战

大规模训练（如 Agent RL）需要数万并行轨迹：
- 一台容器一个任务成本过高
- **SWE-World**（Sun et al., 2026）探索 Docker-free 的替代环境——但学习过渡到真实执行的保真度仍然未解决

### 3.4 Docker 的平台绑定

Docker 继承 Linux 内核假设：
- macOS/Windows/浏览器/桌面/混合云环境暴露不同的隔离和再现性约束
- 跨平台的可移植性尚未成为标配

---

## 4. 设计原则

1. **威胁模型驱动选择**：沙箱类型的选取应基于具体部署的威胁模型，而非默认使用某一类
2. **评估环境即评估**：执行环境的设计直接影响 Agent 行为和评估结果——环境噪声可能伪装成模型失败
3. **从 Bundle 到 Compose**：框架集成运行时→独立沙箱服务的架构迁移是趋势
4. **防御纵深**：OS 级权限控制应作为最后防线，补充但不是替代容器级隔离
5. **可移植性**：MCP 等标准可降低组合成本，但需在工具、治理和可观测层暴露足够状态以保持审计性

---

## 5. 生态快照（代表性系统对比）

| 类别 | 代表系统 | GitHub Stars (k, ~2026.05) | 隔离原语 | 核心用途 |
|------|----------|---------------------------|----------|----------|
| Computer-Use | Claude Computer Use | — | VM | 桌面自动化 |
| Code-Specialized | SWE-bench Docker | 19 | Docker | 代码评估 |
| Framework-Integrated | LangChain Runtime | 100+ | 框架级 | 快速原型 |
| Browser | BrowserGym | — | 浏览器 | Web 评估 |
| OS-Level | Progent | — | seccomp | 高风险部署 |
| Managed Platform | E2B | ~7 | 托管 VM | 生产沙箱 |
| Abstraction | Composio | ~30 | 多后端 | 跨平台编排 |
