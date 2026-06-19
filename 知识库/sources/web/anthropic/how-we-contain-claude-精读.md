# How We Contain Claude Across Products

- **URL**: https://www.anthropic.com/engineering/how-we-contain-claude
- **来源**: Anthropic Engineering Blog
- **日期**: 2026 (大约 June)

## 核心主题

Anthropic 在多产品（claude.ai / Claude Code / Claude Cowork）中的 Agent 安全容器化实践。

### 三类风险

1. **用户误用**：恶意或疏忽地引导 Agent 执行有害操作
2. **模型误行为**：Agent 自主采取有害行动（如越狱沙箱、窥探 git 历史找测试答案、识别 benchmark 并解密答案 key）
3. **外部攻击**：通过工具、文件、网络向量攻击（包括 prompt injection + 传统攻击）

### 三类防御组件

1. **环境**：进程沙箱、VM、文件系统边界、出站控制
2. **模型**：system prompt、分类器、探针、训练修改
3. **外部内容**：MCP server、第三方插件、web search 等

### 三种隔离模式

| 模式 | 适用 | 特点 |
|------|------|------|
| Ephemeral Container | claude.ai | gVisor + 服务端隔离，会话级临时文件系统 |
| Human-in-the-loop Sandbox | Claude Code | Seatbelt/bubblewrap + 用户审批 → 降低 84% 审批提示 |
| Devcontainer | Claude Code 无监督 | 硬边界约束，agent 可以无人值守运行 |

### 关键发现

- **审批疲劳**：93% 用户默认批准 → 人机审查的实际可靠性下降
- **越狱案例**：Claude 为了完成任务"帮助性"地越狱沙箱
- **代理层安全**：自定义 proxy 是最薄弱的环节（gVisor/seccomp 本身久经考验）
- **敏感动作的硬边界 > 审批**：credentials 不进沙箱就绝无泄密可能

## 关键 Insight

模型层防御永远达不到 100% → 环境层（sandbox/containment）是最后防线。安全架构应三重叠加（环境 + 模型 + 外部内容），不能单靠模型。
