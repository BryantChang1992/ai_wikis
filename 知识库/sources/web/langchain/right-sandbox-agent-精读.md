# How to Choose the Right Sandbox for Your Agent

- **URL**: https://www.langchain.com/blog/how-to-choose-the-right-sandbox-for-your-agent
- **来源**: LangChain Blog, Rahul Verma
- **日期**: 2026-06-12

## 核心主题

Agent 最有价值的能力是写代码并执行，但这同时也是最大安全风险。Sandbox 是控制风险的边界。

## The Lethal Trifecta（致死三要素）

由 Simon Willison 提出。以下三个条件同时满足时，Agent 允许攻击者窃取数据：

1. **访问敏感数据**
2. **暴露于不可信内容**
3. **能对外通信**

Meta 提出的**"Rule of Two"**：三个条件同时满足时，Agent 不能完全自主运行。Sandbox 的作用是**缩小**（而非消除）这三个条件。

## 安全 Sandbox 五要素

| 特性 | 说明 |
|------|------|
| **隔离文件系统** | 仅包含所需数据，阻断其他数据访问 |
| **有限网络访问** | 只允许白名单端点 |
| **资源限制** | 控制 CPU/内存/时长 |
| **受控复用性** | 选择是否复用沙箱（复用 = 持久化攻击风险） |
| **内核级隔离** | microVM 提供独立内核（Kubernetes 默认 Pod 无此隔离） |

## LangSmith Sandboxes 设计

- 每个沙箱 = 独立 microVM（专用内核 + 文件系统）
- 生命周期可控
- 网络白名单
- Auth proxy：凭据在沙箱外注入，不可信代码无直接访问

## 关键 Insight

"Sandbox 不是消除 Lethal Trifecta 的全部，而是把它缩小到团队可以自信管理的规模。"——不是安全的终点，而是安全的支点。
