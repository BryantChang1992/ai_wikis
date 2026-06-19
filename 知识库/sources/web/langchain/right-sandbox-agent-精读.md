# How to Choose the Right Sandbox for Your Agent — 精读分析

- **URL**: https://www.langchain.com/blog/how-to-choose-the-right-sandbox-for-your-agent
- **作者**: Rahul Verma, LangChain
- **发布日期**: 2026-06-12
- **精读日期**: 2026-06-19

---

## 1. 问题陈述

Agent 最有价值的能力（写代码并执行）也是最大的安全风险。Sandbox 是控制这个风险的边界。

### 1.1 Lethal Trifecta（Simon Willison）

三项条件同时满足时，Agent 允许攻击者窃取数据：
1. **访问敏感数据**
2. **暴露于不可信内容**
3. **能对外通信**

> "目前没有确定的防止 prompt injection 的方法。"

不可信内容进入 Agent 上下文的众多方式：终端用户输入、外部 MCP server 响应、第三方编写的 skills。

### 1.2 Rule of Two（Meta）

三项条件同时满足时，Agent **不应完全自主运行**。

**困境**：给 Agent 所需的工具通常意味着同时给予敏感数据和外部通信能力。模型和 harness 工程让 Agent 能掌控越来越多上下文→增加了攻击者注入 prompt injection 攻击的可能性。

→ 需要对 Agent 的操作用什么数据能做什么进行隔离。Sandbox 是缩小（非消除）三项风险因子的基础设施。

---

## 2. 安全 Sandbox 五要素

| 要素 | 含义 | 工程实现 |
|------|------|---------|
| **隔离文件系统** | 仅包含工作所需数据，阻断其他数据访问 | Mount 特定目录，其余不可见 |
| **有限网络访问** | 仅允许白名单端点 | Egress firewall 或代理层 |
| **资源限制** | 控制 CPU/内存/时间 | cgroups / K8s limits |
| **受控可复用性** | 可复用 sandbox 方便状态持久化，但一次 compromise 可持续存在 | 可选 ephemeral vs persistent |
| **Kernel 级隔离** | 防止 Agent exploit kernel bug → 接管主机 → 绕过控制 | MicroVM (Firecracker) 而非共享 kernel 容器 |

### 2.1 最关键的警告：Kernel 级隔离

> "市面上自称 'sandbox' 的产品很多不包含这些功能。例如：开源 Kubernetes Agent Sandbox 仅在其 K8s 集群已执行容器间 kernel 级隔离时才安全——**而大多数 K8s 集群不强制执行**。"

共享 kernel 容器不是真正的 sandbox——一旦 Agent exploit kernel bug 就能 escape 到其他容器或主机。

---

## 3. Sandbox 的防御范围

**Sandbox 单一不消除 Lethal Trifecta 的任何方面。它缩小敏感数据访问和外部通信能力，使 prompt injection 风险管理缩小到团队可以自信应对的程度。**

这是一个重要的务实定位：不追求完美安全，而是追求**使安全问题变得可管理的边界**。

---

## 4. LangSmith Sandboxes 架构

### 4.1 分层隔离设计

```
MicroVM (per sandbox)
  ├── 独立 Kernel
  ├── 独立文件系统
  ├── 网络控制: 出站白名单
  └── Auth Proxy: 凭据注入在出站流量内部而非 Sandbox 内

Host
  └── 不见 sandbox 内部
```

**Auth Proxy 的关键设计**：
- 凭据**不在 sandbox 内部**——不受信任的进程不能读取或误用
- 代理在出站流量离开 sandbox 后注入安全凭据
- 这是 Anthropic 容器化文章同样强调的模式

### 4.2 生命周期

从启动→关闭→最终销毁，全可控。可复用（persistent 状态）或一次性（ephemeral）。

---

## 5. Sandbox 选型决策树

### 5.1 按场景

| 场景 | 需求 | 推荐方案 |
|------|------|---------|
| 简单脚本执行 | 低风险，无需网络/文件系统 | 短暂进程隔离（Docker 容器） |
| Coding Agent | 需文件系统编辑/Shell 访问/有限网络 | OS 级沙箱（Seatbelt/bubblewrap）+ 网络阻断 |
| 通用 Agent 工作空间 | 持久文件系统 + 网络 + 工具集成 | Managed MicroVM (LangSmith Sandboxes / Firecracker) |
| 企业多 Agent | 多租户隔离 + 凭据安全 + 合规 | 全 VM 隔离 + Auth Proxy + MDM 控制 |

### 5.2 按组织成熟度

| 组织 | 需求 | 方案 |
|------|------|------|
| 初创/个人开发者 | 快速上线 | OS 沙箱（Claude Code sandbox runtime 模式） |
| 成长型团队 | 多人 + 集中安全策略 | Managed Sandbox (LangSmith 或自建 Firecracker) |
| 大企业 | 合规 + 多 Agent + 审计 | 全 VM 隔离 + Auth Proxy + MDM + 网络段 + SIEM |

---

## 6. 与相关概念的交叉

- **[[Agent-Sandbox-安全沙箱选型]]**：Wiki 卡片
- **[[Anthropic-Agent安全容器化实践]]**：Anthropic 的三种隔离模式（短暂容器 / HITL Sandbox / 本地 VM）是此文理论的工程实现
- **[[Parallax-Agent安全架构]]**：Sandbox 在环境层隔离，Parallax 在架构层隔离——纵深防御

---

## 7. 工程启示

1. **"自称 sandbox ≠ 真正的 sandbox"** 是首要认知：Kubernetes namespace 不等同于 kernel 级隔离
2. **凭据不应进入 sandbox**：Auth proxy 模式是正确方向
3. **可复用性的安全成本常被低估**：persistent sandbox 方便但一次 compromise 可持续存在
4. **Sandbox 不消除风险——使风险可管理**：务实的安全定位
