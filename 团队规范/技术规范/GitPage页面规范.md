# GitPage 页面规范 v1.1

## 概述

本规范定义 CHANG_AI_TEAM GitPage 项目所有 HTML 页面的统一样式标准。所有 Agent 发布 GitPage 内容前，必须先行阅读完整的页面规范。

**版本**：v1.1（2026-06-14）  
**上次决策**：CEO 要求浅色主题 + 居中布局 + 代码渲染

---

## 1. Design Token（CSS 变量）

```css
:root {
  --bg: #ffffff;              /* 纯白背景 */
  --surface: #f8f9fb;        /* 卡片/表面背景 */
  --border: #e5e7eb;         /* 边框 */
  --text: #1a1a2e;           /* 正文 */
  --text-secondary: #555;    /* 次要文字 */
  --muted: #6b7280;          /* 辅助说明 */
  --dim: #9ca3af;            /* 最灰 */
  --accent: #0ea5e9;         /* 主色（sky blue） */
  --accent2: #6366f1;        /* 辅色（indigo） */
  --accent3: #f472b6;        /* 辅色（pink） */
  --green: #10b981;          /* 成功 */
  --amber: #f59e0b;          /* 警告 */
  --red: #ef4444;            /* 错误 */
  --code-bg: #1e293b;        /* 代码块背景（深色） */
  --tag-bg: #eef2ff;         /* 标签背景 */
  --tag-text: #4361ee;       /* 标签文字 */
  --radius: 10px;
  --radius-sm: 6px;
  --shadow: 0 1px 3px rgba(0,0,0,0.06), 0 2px 12px rgba(0,0,0,0.04);
}
```

## 2. 页面骨架

```html
<body>
  <!-- 全局导航栏（所有页面必须有） -->
  <nav class="global-nav">
    <a href="index.html" class="brand">⚡ CHANG_AI_TEAM</a>
    <div class="nav-links">
      <a href="tech_research/index.html" class="nav-link active">🔬 技术调研</a>
      <a href="tech_designs/index.html" class="nav-link">📐 技术方案设计</a>
      <a href="blog/index.html" class="nav-link">✍️ 博客</a>
    </div>
  </nav>

  <!-- 内容区 -->
  <div class="content-wrapper">
    <div class="container">
      <!-- 页面内容 -->
    </div>
  </div>
</body>
```

## 3. 四种页面类型模板

### A 型：首页
- 全宽 Hero header（渐变 accent 背景）
- 模块卡片 grid（module-grid）
- 统计信息栏

### B 型：模块首页
- doc-header 含标题、元数据、标签
- section-title 分区标题 + 计数
- 文章列表（week-card / article-card）

### C 型：内容详情页
- doc-header
- 正文内容区 .content
- page-nav（上一篇/下一篇）

### D 型：章节导航页
- module-card 列表（含图标 + 描述 + 统计）

## 4. 组件规范

| 组件 | 用途 |
|------|------|
| `.global-nav` | 全局导航栏，sticky 置顶 |
| `.hero` | 首页大标题区 |
| `.doc-header` | 文档页标题区 |
| `.content` | Markdown 渲染区 |
| `.module-grid` / `.module-card` | 模块索引卡片 |
| `.weeks-grid` / `.week-card` | 周报列表卡片 |
| `.chapter-list` / `.chapter-card` | 章节导航卡片 |
| `.section-title` | 分区标题（含计数） |
| `.callout` | 提示框（info/success/warn/danger） |
| `.tag` | 标签（blue/green/purple/pink/red） |
| `.back-link` | 返回链接 |
| `.page-nav` | 上一篇/下一篇导航 |
| `footer` | 页脚 |

## 5. 代码段渲染

- inline code：浅底 `#f1f5f9` + 红色文字 `#e11d48`
- pre code block：深底 `#1e293b` + 亮色文字 `#e2e8f0`

## 6. 计数器规范

所有页面中的计数器（篇数、期数、模块数等）必须与仓库中实际文件数一致。新增或删除文件时必须同步更新计数。

## 7. 规则

1. ✅ 禁止硬编码颜色值（使用 CSS 变量）
2. ✅ 每个页面必须包含 `.global-nav` 导航栏
3. ✅ 相对路径必须正确
4. ✅ 禁止使用内联 `<style>` 属性（所有样式集中到 `<style>` 标签）
5. ✅ 所有页面浅色背景（`--bg: #ffffff`）
6. ✅ 所有页面内容居中（max-width 860px）
7. ✅ 代码段必须有深色背景渲染
