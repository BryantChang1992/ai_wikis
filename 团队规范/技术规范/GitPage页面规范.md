# GitPage 页面规范 v1.0

> **重要**：所有需要发布到 GitPage 的 HTML 页面，开发前必须先阅读本规范。
> 
> 违反本规范的产出将被拒绝合并。如有规范未覆盖的场景，提 Issue 讨论。

---

## 1. 设计原则

- **统一**：所有页面共享同一套视觉语言，用户跨页跳转无割裂感
- **简洁**：深色主题，减少视觉噪音，突出内容本身
- **可维护**：CSS 变量驱动，修改一个变量全局生效
- **响应式**：移动端友好，保持可读性

---

## 2. 全局 Design Token

所有页面必须使用以下 CSS 变量，**禁止硬编码颜色值**：

```css
:root {
  /* 背景 & 表面 */
  --bg: #09090b;           /* 页面主背景 */
  --surface: #18181b;      /* 卡片、区块背景 */
  --border: #27272a;       /* 边框/分割线 */

  /* 文字层级 */
  --text: #fafafa;         /* 正文 */
  --muted: #a1a1aa;        /* 次要描述 */
  --dim: #71717a;          /* 最低层级文字 */

  /* 强调色 */
  --accent: #22d3ee;       /* 主强调 cyan */
  --accent2: #818cf8;      /* 次强调 indigo */
  --accent3: #f472b6;      /* 第三强调 pink */

  /* 语义色 */
  --green: #34d399;
  --amber: #fbbf24;
  --red: #f87171;

  /* 代码 */
  --code-bg: #1e1e2e;

  /* 圆角 */
  --radius: 10px;
  --radius-sm: 6px;
}
```

### 渐变色使用规范

标题使用渐变色提升视觉品质，不同模块可使用不同渐变色组合：

| 用途 | 渐变 |
|------|------|
| Brand / 首页标题 | `cyan → indigo → pink` |
| 技术调研标题 | `cyan → indigo` |
| 技术方案设计标题 | `cyan → indigo` |
| Badge | `accent → accent2` |

```css
/* 标准渐变标题 */
background: linear-gradient(135deg, var(--accent), var(--accent2));
-webkit-background-clip: text;
-webkit-text-fill-color: transparent;
background-clip: text;
```

---

## 3. 页面骨架模板

每一个 HTML 页面都必须从以下骨架开始：

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title><!-- 页面标题 --></title>
<style>
  :root {
    --bg: #09090b;
    --surface: #18181b;
    --border: #27272a;
    --text: #fafafa;
    --muted: #a1a1aa;
    --dim: #71717a;
    --accent: #22d3ee;
    --accent2: #818cf8;
    --accent3: #f472b6;
    --green: #34d399;
    --amber: #fbbf24;
    --red: #f87171;
    --code-bg: #1e1e2e;
    --radius: 10px;
    --radius-sm: 6px;
  }
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans SC', sans-serif;
    background: var(--bg);
    color: var(--text);
    line-height: 1.75;
    -webkit-font-smoothing: antialiased;
    min-height: 100vh;
  }
  a { color: var(--accent); text-decoration: none; }
  a:hover { text-decoration: underline; }

  /* ═══════════════════════════════════════════
     全局导航栏 - 所有页面必须包含
     ═══════════════════════════════════════════ */
  .global-nav {
    display: flex; align-items: center; gap: 0;
    padding: 0 24px;
    background: rgba(9,9,11,0.92);
    backdrop-filter: blur(12px);
    border-bottom: 1px solid var(--border);
    position: sticky; top: 0; z-index: 100;
    height: 52px;
  }
  .global-nav .brand {
    font-weight: 700; font-size: 0.95rem;
    background: linear-gradient(135deg, var(--accent), var(--accent2));
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    background-clip: text; text-decoration: none; margin-right: 28px;
  }
  .global-nav .nav-links { display: flex; gap: 4px; overflow-x: auto; flex: 1; }
  .global-nav .nav-link {
    color: var(--muted); text-decoration: none; font-size: 0.88rem;
    padding: 6px 14px; border-radius: 8px; white-space: nowrap;
    transition: background 0.15s, color 0.15s;
  }
  .global-nav .nav-link:hover { background: var(--surface); color: var(--text); }
  .global-nav .nav-link.active {
    background: var(--surface); color: var(--accent); font-weight: 500;
  }

  /* ═══════════════════════════════════════════
     基础排版 - 以下为页面特有样式
     ═══════════════════════════════════════════ */

  /* 页面容器 */
  .container { max-width: 920px; margin: 0 auto; padding: 32px 24px 80px; }

  /* 统一样式（以下是所有内容页必须包含的） */
  h2 { font-size: 1.4rem; font-weight: 700; margin: 40px 0 16px; padding-bottom: 8px; border-bottom: 1px solid var(--border); color: var(--accent); }
  h3 { font-size: 1.15rem; font-weight: 600; margin: 28px 0 12px; color: var(--accent2); }
  h4 { font-size: 1rem; font-weight: 600; margin: 20px 0 8px; color: var(--text); }
  p { margin-bottom: 14px; font-size: 0.95rem; color: var(--text); }
  strong { color: var(--text); font-weight: 600; }
  ul, ol { margin-bottom: 14px; padding-left: 24px; }
  li { margin-bottom: 6px; font-size: 0.95rem; }
  blockquote {
    border-left: 3px solid var(--accent);
    background: rgba(34,211,238,0.06);
    padding: 10px 16px; margin: 14px 0;
    border-radius: 0 var(--radius-sm) var(--radius-sm) 0;
    font-size: 0.9rem; color: var(--muted);
  }
  hr { border: none; border-top: 1px solid var(--border); margin: 32px 0; }
</style>
</head>
<body>

<!-- 全局导航栏 -->
<nav class="global-nav">
  <a href="<!-- 首页相对路径 -->/index.html" class="brand">BryantChang</a>
  <div class="nav-links">
    <a href="<!-- 首页相对路径 -->/index.html" class="nav-link">🏠 首页</a>
    <a href="<!-- 技术调研相对路径 -->/tech_research/" class="nav-link">🔬 技术调研</a>
    <a href="<!-- 技术方案设计相对路径 -->/tech_designs/" class="nav-link">📐 技术方案设计</a>
    <a href="<!-- 博客相对路径 -->/blog/" class="nav-link">✍️ 博客</a>
  </div>
</nav>

<!-- 页面内容 -->
<div class="container">
  <!-- 正文 -->
</div>

</body>
</html>
```

### 导航栏相对路径规则

导航栏链接的相对路径取决于当前页面在目录树中的深度：

| 页面深度 | 首页路径 | 技术调研路径 | 示例 |
|----------|----------|-------------|------|
| 根目录 | `index.html` | `tech_research/` | `./index.html` |
| 一级子目录 | `../index.html` | `./` 或 `index.html` | `./tech_research/index.html` |
| 二级子目录 | `../../index.html` | `../` | `./tech_research/doris/index.html` |
| 三级子目录 | `../../../index.html` | `../../` | `./tech_research/kafka_research/deep_dives/index.html` |

---

## 4. 页面类型与模板

根据功能，页面分为 4 种类型。每种类型在基础骨架之外有特定结构。

### 类型 A：首页 (index.html)

根目录唯一的首页，展示所有模块入口。

```html
<!-- Hero 区域 -->
<section class="hero" style="text-align:center; padding:80px 20px 60px; background:linear-gradient(180deg, rgba(34,211,238,0.05) 0%, transparent 100%); border-bottom:1px solid var(--border);">
  <h1 style="font-size:2.8rem; font-weight:800; letter-spacing:-0.02em;
    background:linear-gradient(135deg, var(--accent) 0%, var(--accent2) 50%, var(--accent3) 100%);
    -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text;
    margin-bottom:12px;"><!-- 标题 --></h1>
  <p class="tagline" style="color:var(--muted); font-size:1.1rem; max-width:500px; margin:0 auto;">
    <!-- 副标题 -->
  </p>
  <div class="meta" style="margin-top:20px; display:flex; gap:24px; justify-content:center; flex-wrap:wrap;">
    <span style="color:var(--dim); font-size:0.85rem;"><!-- meta 项 --></span>
  </div>
</section>

<!-- 模块卡片网格 -->
<div class="container">
  <div class="module-grid" style="display:grid; gap:20px;">
    <a href="<!-- 链接 -->" class="module-card" style="background:var(--surface); border:1px solid var(--border); border-radius:14px; padding:28px 32px; text-decoration:none; color:var(--text); transition:border-color 0.2s, transform 0.15s; position:relative; overflow:hidden;">
      <div class="module-icon" style="font-size:2rem; margin-bottom:12px;"><!-- emoji --></div>
      <div class="module-name" style="font-size:1.3rem; font-weight:700; margin-bottom:6px;"><!-- 模块名 --></div>
      <div class="module-desc" style="color:var(--muted); font-size:0.92rem; margin-bottom:12px;"><!-- 描述 --></div>
      <div class="module-stats" style="display:flex; gap:16px; flex-wrap:wrap; font-size:0.8rem; color:var(--dim);">
        <!-- 统计数据 -->
      </div>
    </a>
  </div>
</div>
```

**约束**：
- 模块卡片 hover 效果：`border-color: rgba(255,255,255,0.15); transform: translateY(-2px); box-shadow: 0 8px 30px rgba(0,0,0,0.3);`
- 卡片顶部色条用 `::before` 伪元素实现

### 类型 B：模块首页（如 tech_research/index.html）

列出该模块下所有子模块/文章的索引页。

```html
<div class="container">
  <!-- 返回链接 -->
  <a href="../index.html" class="back-link" style="display:inline-block; margin-bottom:24px; color:var(--muted); text-decoration:none; font-size:0.85rem; padding:6px 12px; border-radius:8px; border:1px solid var(--border); transition:background 0.15s;">
    ← 返回首页
  </a>

  <!-- 页面标题 -->
  <header style="text-align:center; padding:24px 0 32px; border-bottom:1px solid var(--border); margin-bottom:40px;">
    <h1 style="font-size:2rem; font-weight:700;
      background:linear-gradient(135deg, var(--accent), var(--accent2));
      -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text;
      margin-bottom:8px;"><!-- 标题 --></h1>
    <p style="color:var(--muted); font-size:0.95rem;"><!-- 描述 --></p>
  </header>

  <!-- 子模块列表 -->
  <div class="section">
    <div class="section-title" style="display:flex; align-items:center; gap:12px; font-size:1.25rem; font-weight:600; margin-bottom:20px; padding-bottom:12px; border-bottom:1px solid var(--border);">
      <span class="icon" style="font-size:1.5rem;"><!-- emoji --></span>
      <span><!-- 分类名 --></span>
      <span class="count" style="color:var(--muted); font-size:0.85rem; font-weight:400; margin-left:auto;"><!-- 计数 --></span>
    </div>
    <!-- 文章卡片列表 -->
  </div>
</div>
```

### 类型 C：内容详情页（周报、深度调研、设计文档）

标准内容展示页，包含标题区、TOC、正文。

```html
<div class="container">
  <!-- 返回链接（可选） -->
  <a href="./" class="back-link" style="...">← 返回上级</a>

  <!-- 文档头部 -->
  <div class="doc-header" style="text-align:center; padding:48px 0 36px; border-bottom:2px solid var(--border); margin-bottom:40px;">
    <div class="badge" style="display:inline-block;
      background:linear-gradient(135deg, var(--accent), var(--accent2));
      color:#fff; font-size:12px; font-weight:600; letter-spacing:0.5px;
      padding:4px 16px; border-radius:20px; margin-bottom:16px;"><!-- TAG --></div>
    <h1 style="font-size:2rem; font-weight:700; letter-spacing:-0.3px; margin-bottom:8px;"><!-- 标题 --></h1>
    <p class="meta" style="font-size:0.88rem; color:var(--muted);">
      <!-- 作者 | 日期 | 标签 -->
    </p>
  </div>

  <!-- TOC 目录（如果有 >= 3 个章节） -->
  <div class="toc" style="background:var(--surface); border:1px solid var(--border); border-radius:var(--radius); padding:24px 28px; margin-bottom:40px; border-left:4px solid var(--accent);">
    <h2 style="font-size:0.9rem; color:var(--dim); text-transform:uppercase; letter-spacing:0.06em; margin:0 0 14px; border:none; padding:0;">目录</h2>
    <ol style="padding-left:22px; display:flex; flex-direction:column; gap:8px;">
      <li><a href="#section-id" style="color:var(--accent); text-decoration:none; font-weight:500; font-size:0.92rem;">章节名</a></li>
    </ol>
  </div>

  <!-- 正文内容 -->
  <div class="content">
    <!-- 使用 h2/h3/h4 标准层级 -->
    <!-- 所有组件使用下方统一组件样式 -->
  </div>

  <!-- 页脚（可选） -->
  <footer style="text-align:center; padding:48px 0 32px; color:var(--muted); font-size:0.85rem; border-top:1px solid var(--border); margin-top:60px;">
    <p>由 <strong>CHANG_AI_TEAM</strong> 维护 · 内容由 AI Agent 自动生成</p>
  </footer>
</div>
```

### 类型 D：章节导航页（如 doris/index.html, fluss/index.html）

多章节项目的目录页，展示章节卡片列表。

```html
<div class="container">
  <a href="../" class="back-link" style="...">← 返回上级</a>

  <!-- Hero -->
  <section class="hero" style="text-align:center; padding:60px 20px 50px; background:linear-gradient(180deg, rgba(34,211,238,0.05) 0%, transparent 100%); border-bottom:1px solid var(--border);">
    <h1 style="font-size:2.2rem; font-weight:800; letter-spacing:-0.02em;
      background:linear-gradient(135deg, var(--accent) 0%, var(--accent2) 50%, var(--accent3) 100%);
      -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text;
      margin-bottom:12px;"><!-- 项目名 --></h1>
    <p class="meta" style="color:var(--muted); font-size:0.95rem; max-width:600px; margin:0 auto 8px;"><!-- 描述 --></p>
    <div class="meta-tags" style="margin-top:12px; display:flex; gap:8px; justify-content:center; flex-wrap:wrap;">
      <span class="tag" style="font-size:0.75rem; padding:3px 10px; border-radius:12px; border:1px solid var(--border); color:var(--dim);"><!-- tag --></span>
    </div>
  </section>

  <!-- 章节卡片列表 -->
  <div class="chapter-list" style="display:flex; flex-direction:column; gap:12px; margin-top:40px;">
    <a href="01-xxx.html" class="chapter-card" style="background:var(--surface); border:1px solid var(--border); border-radius:12px; padding:24px 28px; text-decoration:none; color:var(--text); display:flex; gap:18px; align-items:flex-start; transition:border-color 0.2s, transform 0.15s;">
      <span class="chapter-num" style="font-size:1.6rem; font-weight:800; color:var(--accent); min-width:40px;">01</span>
      <div class="chapter-info">
        <h3 style="font-size:1.1rem; font-weight:700; margin-bottom:4px;"><!-- 章节名 --></h3>
        <p class="desc" style="font-size:0.85rem; color:var(--muted); margin-bottom:6px;"><!-- 描述 --></p>
        <div class="stats" style="font-size:0.75rem; color:var(--dim); display:flex; gap:16px;"><!-- 统计 --></div>
      </div>
    </a>
  </div>
</div>
```

**章节卡片 hover**：`border-color: rgba(255,255,255,0.2); transform: translateY(-1px);`

---

## 5. 组件规范

以下组件必须在所有内容页（类型 B/C/D）中保持一致。

### 5.1 代码块

```css
pre {
  background: var(--code-bg);
  border-radius: 8px;
  padding: 16px 20px;
  overflow-x: auto;
  margin: 14px 0;
  font-size: 0.85rem;
  line-height: 1.65;
}
pre code {
  background: none;
  padding: 0;
  color: #e2e8f0;
  font-size: inherit;
}
code {
  font-family: 'SF Mono', 'Fira Code', 'Menlo', monospace;
  font-size: 0.88em;
}
p code, li code {
  background: rgba(255,255,255,0.08);
  padding: 2px 6px;
  border-radius: 4px;
  color: var(--accent3);
}
```

### 5.2 表格

```css
table {
  width: 100%;
  border-collapse: collapse;
  margin: 16px 0;
  font-size: 0.88rem;
}
th {
  background: var(--surface);
  color: var(--accent);
  text-align: left;
  padding: 10px 14px;
  border: 1px solid var(--border);
  font-weight: 600;
}
td {
  padding: 10px 14px;
  border: 1px solid var(--border);
  color: var(--text);
}
tr:nth-child(even) td {
  background: rgba(24,24,27,0.4);
}
```

### 5.3 Callout

4 种语义类型：

```css
.callout {
  border-radius: var(--radius);
  padding: 14px 18px;
  margin: 16px 0;
  font-size: 0.9rem;
  border-left: 4px solid;
}
.callout.info  { background: rgba(34,211,238,0.06);  border-color: var(--accent); }
.callout.success { background: rgba(52,211,153,0.06); border-color: var(--green); }
.callout.warn  { background: rgba(251,191,36,0.06);  border-color: var(--amber); }
.callout.danger { background: rgba(248,113,113,0.06); border-color: var(--red); }
```

用法：
```html
<div class="callout info">
  <strong>💡 提示</strong>
  <p>这是提示信息。</p>
</div>
```

### 5.4 Tag / Badge

```css
.tag {
  display: inline-block;
  padding: 3px 10px;
  border-radius: 20px;
  font-size: 0.75rem;
  font-weight: 500;
  margin-right: 6px;
  margin-bottom: 4px;
}
.tag-accent  { background: rgba(34,211,238,0.12);  color: var(--accent); }
.tag-accent2 { background: rgba(129,140,248,0.12);  color: var(--accent2); }
.tag-accent3 { background: rgba(244,114,182,0.12);  color: var(--accent3); }
.tag-green   { background: rgba(52,211,153,0.12);   color: var(--green); }
.tag-amber   { background: rgba(251,191,36,0.12);   color: var(--amber); }
.tag-red     { background: rgba(248,113,113,0.12);  color: var(--red); }
```

### 5.5 图片

```css
img {
  display: block;
  max-width: 100%;
  margin: 20px auto;
  border-radius: var(--radius-sm);
}
```

对于 SVG 图表：
```css
img[src$=".svg"] {
  background: rgba(255,255,255,0.03);
  padding: 8px;
}
```

### 5.6 返回链接

```css
.back-link {
  display: inline-block;
  margin-bottom: 24px;
  color: var(--muted);
  text-decoration: none;
  font-size: 0.85rem;
  padding: 6px 12px;
  border-radius: 8px;
  border: 1px solid var(--border);
  transition: background 0.15s;
}
.back-link:hover { background: var(--surface); text-decoration: none; }
```

---

## 6. 目录结构约定

```
/
├── index.html                    # 首页（类型 A）
├── tech_research/
│   ├── index.html               # 技术调研首页（类型 B）
│   ├── kafka_research/
│   │   ├── week_01_xxx.html     # 周报（类型 C）
│   │   ├── deep_dives/
│   │   │   └── index.html       # 深度调研（类型 C/D）
│   ├── doris/
│   │   ├── index.html           # Doris 目录页（类型 D）
│   │   └── 01-xxx.html          # 章节（类型 C）
│   ├── fluss/
│   │   ├── index.html           # Fluss 目录页（类型 D）
│   │   └── 01-xxx.html          # 章节（类型 C）
│   ├── data_for_ai/
│   │   └── week_xx_xxx.html     # 周报（类型 C）
│   ├── ai_harness/
│   │   └── week_xx_xxx.html     # 周报（类型 C）
│   ├── ai_agent_papers/
│   │   └── week_xx_xxx.html     # 周报（类型 C）
│   ├── event-horizon-semi-linearizability/
│   │   └── index.html           # 论文精读（类型 C）
│   ├── paper-notes/
│   │   └── *.html               # 论文笔记（类型 C）
│   └── top_conferences/
│       └── week_xx_xxx.html     # 顶会洞察（类型 C）
├── tech_designs/
│   ├── index.html               # 技术方案设计首页（类型 B）
│   ├── zk-kafka-jbod-failure-handling.html  # 方案（类型 C）
│   └── agent-infra/
│       └── observability-dashboard.html     # 方案（类型 C）
├── blog/
│   ├── index.html               # 博客首页（类型 B）
│   └── *.html                   # 博客文章（类型 C）
└── docs/
    └── GITPAGE_PAGE_SPEC.md     # ← 本规范文件
```

---

## 7. 新增页面流程

1. **确定类型**：是首页(A)、模块首页(B)、内容详情(C)还是章节导航(D)
2. **阅读本规范**：确认 Design Token、骨架模板、组件规范
3. **从模板开始**：复制对应类型模板，不要从零写 CSS
4. **填充内容**：在模板基础上填入正文内容
5. **检查导航**：确保 `.global-nav` 中所有链接路径正确（参考 §3 相对路径表）
6. **检查组件**：表格/代码块/callout 是否使用了规范定义的 class
7. **验证**：在浏览器中打开，检查深色主题一致性

---

## 8. 禁止事项

- ❌ **禁止**自定义 CSS 变量名（如 `--accent1` 替代 `--accent`）
- ❌ **禁止**使用浅色背景（`#ffffff`、`#f8f9fb` 等）
- ❌ **禁止**硬编码颜色值替代 CSS 变量
- ❌ **禁止**省略 `.global-nav` 导航栏
- ❌ **禁止**在子页面中遗漏返回链接
- ❌ **禁止**使用其他字体栈替代规范字体
- ❌ **禁止**创建不在这 4 种类型之内的页面而不讨论

---

## 9. 响应式

所有页面需在 `@media (max-width: 640px)` 下做适配：

```css
@media (max-width: 640px) {
  .global-nav { padding: 0 12px; }
  .global-nav .brand { margin-right: 12px; font-size: 0.85rem; }
  .container { padding: 16px 12px 48px; }
  .hero { padding: 48px 16px 36px; }
  .hero h1, .doc-header h1 { font-size: 1.5rem; }
  pre { font-size: 0.78rem; padding: 12px 14px; }
}
```

---

## 10. 修订历史

| 版本 | 日期 | 作者 | 变更 |
|------|------|------|------|
| v1.0 | 2026-06-14 | Stark (CTO) | 初始版本，统一样式迁移后制定 |
