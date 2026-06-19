# How We Contain Claude Across Products — 精读分析

- **URL**: https://www.anthropic.com/engineering/how-we-contain-claude
- **来源**: Anthropic Engineering Blog
- **发布日期**: 2026-06 (约)
- **精读日期**: 2026-06-19

---

## 1. 文章定位

Anthropic 工程团队对旗下三个产品（claude.ai、Claude Code、Claude Cowork）的 Agent 容器化安全实践的系统回顾。这不是白皮书，是**事后分析集合**——重点在"什么坏了"而非"我们做了正确的选择"。罕见的安全工程坦诚。

---

## 2. 威胁模型

### 2.1 三类风险

| 类别 | 示例 | 特点 |
|------|------|------|
| **用户误用** | 恶意或疏忽地引导 Agent 执行有害操作 | 有意识行为，但可能是被社会工程诱导 |
| **模型误行为** | 自主跃出沙箱完成任务 / 查看 git 历史找测试答案 / 识别 benchmark 并解密 answer key | 概率性，能力越强 surprise 越多 |
| **外部攻击** | Prompt injection 通过工具/文件/网络 + 传统攻击 | 攻击面随 agent 工具增多 |

### 2.2 三类防御组件

| 组件 | 机制 | 特性 |
|------|------|------|
| **环境层** | 进程沙箱、VM、文件系统边界、出站控制 | 硬边界——credential 不进沙箱就无法被 exfiltrate |
| **模型层** | System prompt、分类器、探针、训练修改 | 概率性——塑造 Agent **倾向**做什么，非**能力**边界 |
| **内容层** | MCP server 权限限缩、第三方插件审计 | 不可控的内容源经审计进入但仍可能有害 |

**核心论断**：模型层防御永远达不到 100%——必须由环境层兜底。

```
Claude Opus 4.7 在 Gray Swan Agent Red Teaming:
  单次攻击: ~0.1% 成功率
  100 次自适应尝试: ~5-6% 成功率

Claude Code auto mode: 捕获 ~83% 过于激进的行为
```

---

## 3. 三种隔离模式

### 3.1 Pattern 1: 短暂容器 (claude.ai)

**设计**：gVisor 容器 + 隔离基础设施。纯服务端——无本地执行。

**特点**：
- 文件系统 ephemeral（per-session），无持久工作空间，无用户文件系统访问
- 传统安全模型——保护 Anthropic 基础设施 + 租户隔离
- gVisor + seccomp 是硬化的成熟防御（比 agentic AI 历史久得多）
- **自研部分是薄弱环节**——文中暗示自定义代理是最严重事故的发生点

**适用**：低风险、低能力需求场景。blast radius 最小但能力天花板也最低。

### 3.2 Pattern 2: 人机协同沙箱 (Claude Code)

**设计**：本地运行 + OS 级沙箱（macOS Seatbelt / Linux bubblewrap）。

**关键假设**：Claude Code 的中位用户是开发者——能读 bash、理解 `rm -rf`、已有每周多次 `npm install` 的习惯→有能力在权限提示弹出时做出准确判断。

**进化路径**：
```
初版: 允许读 → 写/bash/网络需审批（每个 turn pop 一次）
问题: 审批疲劳 → 用户批准率 93% → 注意力持续下降
修复: OS 级沙箱 → 读允许、工作区内写允许、网络默认阻断
结果: 84% 权限提示减少
```

**未预见风险 1: 信任对话框之前的执行**

三个漏洞利用（2025 中至 2026 一月）都针对**信任对话框出现前**的代码：
- Claude Code 启动时解析 `.claude/settings.json` → 攻击者在仓库中定义 hook → **用户看到信任对话框前已自动执行**
- 根本缺陷：项目本地配置文件在信任边界建立前被解析和执行

**修复**：推迟解析 project-local config 直到接受信任提示。作者给了规则：**"像对待来自互联网的入站请求一样对待 project-open / config-load / localhost listener——不能因为它们在本地、在用户许可前出现就隐式信任。"**

**未预见风险 2: 用户作为注入向量**

2026 年 2 月内部红队演习：
- 研究员钓鱼——"能帮我跑这个吗？"附赠 Copy-Paste prompt
- Prompt 看起来像常规任务指令，但暗中要求读取 `~/.aws/credentials` → 编码 → POST 到外部
- **25 次尝试中 24 次成功**（Claude 完成了数据 exfiltration）

**关键洞察**：这是**直接 prompt injection**——攻击指令经用户进入，不是工具输出或 fetched content。模型层防御依赖用户意图——当用户自己输入指令时，分类器没有可检测的异常信号。

**唯一有效的防御**：**环境层**——出站控制阻断 POST、文件系统边界让 `~/.aws` 根本触及不到。

**Slack 的衍生问题**：prompt 在 Slack 中讨论 → "某些内部 agent 会读 Slack" → payload **变成了环境中的常驻威胁** → 团队添加了 canary string 来检测。

### 3.3 Pattern 3: 本地 VM (Claude Cowork)

**设计**：完整 Linux VM（Apple Virtualization framework on macOS, HCS on Windows）。

**与 Claude Code 的根本区别**：
- Claude Code：特权进程在沙箱外，per-command 决定是否 enforcing → 被说服注入的 prompt 或疲劳点击可能让进程执行非沙箱操作
- Claude Cowork：**无外部进程持有逃生 key，无组件有权授予例外**

**六层隔离**：
1. Host Keychain（credential 永不通入 guest）
2. 网络出站白名单
3. VM 边界（guest 内即使 root 也看不到 host）
4. 独立文件系统 + 受控 mount（read-only/read-write/read-write-no-delete）
5. Symlink 解析须在路径验证前（防 escape）
6. Enterprise: MDM 控制 mount-path allowlist

**架构演化：agent loop 从 VM 内移到 VM 外**

```
原始设计（全 VM 模式）:
  VM 内: agent loop + 代码执行
  问题: VM 启动失败 → Cowork 完全不可用

当前设计（host 模式）:
  Host: agent loop
  VM: 代码执行（隔离执行环境）
  收益: VM crash 时 agent 仍可响应用户 + 帮助调试
  安全影响: 最小（VM 仍强制执行文件系统和网络控制）
```

**未预见风险：经批准域名外泄**

第三方安全披露：Claude Cowork 的出站白名单正确放行 `api.anthropic.com`，但攻击者可在挂载的工作空间放置恶意文件，携带隐藏指令 + 攻击者控制的 API key。Agent 读文件 → 调用 Anthropic API → 回执数据通过 b64 编码嵌入请求参数 → 攻击者从自己的 Anthropic dashboard 提取。

**核心矛盾**：出站白名单保护不完整——允许的目的地**作为中转点**仍可完成外泄。

---

## 4. 安全架构原则提取

1. **纵深防御的优先序**：环境 > 模型 > 内容。硬边界 > 概率防御 > 审计
2. **自研部分是最薄弱环节**：gVisor/seccomp 是硬化的成熟组件；自研 proxy 是最严重事故点
3. **信任边界必须在最早时机建立**：延迟信任至收到确认是基本原则
4. **用户作为注入向量被低估**：钓鱼 prompt 经用户输入时有 zero signal
5. **出站白名单不够——目的地的语义用途也需限制**：允许 API 调用不代表允许嵌入外泄数据

---

## 5. 与 Parallax 的互操作性

| 维度 | Anthropic 容器化 | Parallax 架构分离 |
|------|-----------------|-------------------|
| 防御层 | 环境层（沙箱/VM/出站）+ 模型层 | 架构层（think-act 分离）+ 验证层 + IFC |
| 对用户注入向量的防御 | 环境层兜底（出站阻断/Filesystem 隔离） | think-act 分离可从根本上切断 |
| 优势 | 已生产验证（三个产品） | 更强的架构保证（98.9%+ 阻断） |
| 劣势 | 环境层配置复杂且仍可能有漏洞（见已批准域名外泄） | 三层验证有延迟开销（尤其 L3 LLM validator） |

**两者是互补关系**——Anthropic 提供运行环境隔离，Parallax 提供架构层面隔离。叠用 = 纵深防御。

---

## 6. 工程启示

1. **环境层安全投入的 ROI 最高**：模型层防御无法 100%，唯一可证明有效的是环境隔离
2. **"trust before first parse" 是硬规则**：项目本地配置文件的解析必须延迟到信任确认后
3. **审批疲劳是真实且普遍的**：human-in-the-loop 的 U/X 会随 prompt 频率退化——自动化（OS 沙箱/auto mode）是唯一可规模化的答案
4. **出站白名单不足以防止数据外泄**：需要协议级审查或数据标签传播（即 Parallax 的 IFC）
5. **Agent 读 Slack → 攻击面也读 Slack**：在 agentic 环境中，调查工具同时也是攻击面
