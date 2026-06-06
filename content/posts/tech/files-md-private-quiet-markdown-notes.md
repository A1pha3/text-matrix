+++
date = '2026-05-20T00:00:00+08:00'
draft = false
title = 'files.md：安静私密的 Markdown 思考空间'
slug = 'files-md-private-quiet-markdown-notes'
description = 'files.md 是一款极简开源笔记应用，提供安静私密的 Markdown 写作环境，纯本地存储，无需注册联网，用 Git 管理版本。'
categories = ['技术笔记']
tags = ['工具', '开源', 'Markdown', '笔记']
+++

# files.md：安静私密的 Markdown 思考空间

## 一、项目概述

**files.md**（[zakirullin/files.md](https://github.com/zakirullin/files.md)）是一款极简的本地笔记应用，核心理念是提供一个**安静、私密、无干扰**的 Markdown 写作环境。

> 仓库：[zakirullin/files.md](https://github.com/zakirullin/files.md)｜TypeScript

## 二、为什么需要 files.md？

当下笔记应用越来越复杂：

- Notion：过于庞大，文档/数据库/wiki 一应俱全，但启动慢、加载慢
- Obsidian：功能强但需要配置一堆插件才能舒服使用
- 飞书/钉钉文档：云端、有审查担忧、不够私密
- 各种云笔记：数据不上传就丢，上传了又担心隐私

**files.md 的哲学：**

> Private, quiet space for thinking. A simple app for your .md files.

你的 Markdown 文件躺在本地磁盘上，无需注册、无需联网、无需同步，只有你和你的文字。

## 三、核心特性

### 1. 纯本地存储

- 所有笔记以 `.md` 文件存储在指定目录
- 文件完全属于你，可用任意编辑器打开
- 路径即目录结构，Finder/Explorer 可见
- 配合 Git 实现版本控制

### 2. 极简界面

```
┌────────────────────────────────────────────┐
│  选择文件夹                               │
├──────────────┬─────────────────────────────┤
│  文件列表     │                             │
│              │       编辑区域              │
│  - 笔记1.md  │   # 我的思考               │
│  - 笔记2.md  │                             │
│  - 子目录/   │   这里是纯 Markdown 编辑    │
│    - 笔记3.md│                             │
│              │   **加粗** *斜体* `代码`    │
│              │                             │
└──────────────┴─────────────────────────────┘
```

- **左侧**：文件系统树（只读展示）
- **右侧**：编辑器（支持实时预览切换）
- **顶部**：路径导航面包屑

### 3. Markdown 完整支持

- 标题、列表、引用、代码块
- 表格（支持编辑）
- 任务列表（`- [ ]`）
- 数学公式（LaTeX 渲染）
- 代码高亮（多语言支持）

### 4. 快速启动

- 打开即用，无需注册账号
- 选择任意文件夹，立即显示所有 .md 文件
- 搜索功能（标题/内容全文搜索）

### 5. 隐私优先

- 不需要网络连接
- 不上传任何数据
- 不收集任何使用统计
- 没有云同步（可选搭配 Git）
- 所有数据在本地磁盘

## 四、安装方式

### macOS

```bash
# 如果通过 Homebrew 发布
brew install files-md

# 或下载 .app 放在 Applications
```

### Windows

下载 `.exe` 安装包，双击运行即可。

### Linux

```bash
# AppImage
chmod +x files-md-linux.AppImage
./files-md-linux.AppImage
```

## 五、使用场景

### 适合的场景

| 场景 | 说明 |
|------|------|
| **每日笔记** | 每天一个 `.md` 文件，简单记录 |
| **技术文档** | 代码笔记、文档草稿、技术方案 |
| **写作草稿** | 长文写作，无干扰环境 |
| **私密日记** | 本地加密存储，不上云 |
| **知识积累** | 长期沉淀，用 Git 管理版本 |

### 不适合的场景

- 多设备同步（建议用 Git 方案）
- 实时协作（用 Notion/飞书）
- 结构化数据库（用 Notion/Airtable）

## 六、与 Obsidian 的区别

| 对比项 | files.md | Obsidian |
|--------|----------|----------|
| 定位 | **极简写作工具** | PKM 知识管理 |
| 复杂度 | 低 | 高（插件系统复杂） |
| 数据格式 | 纯 .md 文件 | Vault（也是 md） |
| 同步方案 | DIY（Git/iCloud） | 官方 Sync（付费） |
| 学习曲线 | 平缓 | 陡峭 |
| 启动速度 | **极快** | 较慢 |

**files.md 与 Obsidian 的定位差异：** Obsidian 是瑞士军刀式的知识管理工具，files.md 是一支专注写作的笔。

## 七、Git 版本控制示例

```bash
# 初始化笔记仓库
cd ~/Documents/Notes
git init

# 每次写完笔记后提交
git add .
git commit -m "更新今日笔记"

# 配合 GitHub 私有仓库做备份
git remote add origin git@github.com:you/notes.git
git push -u origin main
```

## 八、技术细节

**技术栈：**

- **语言**：TypeScript
- **框架**：Electron（跨平台桌面）
- **编辑器**：CodeMirror 或 Monaco Editor
- **构建**：Electron Builder

**文件格式：**

```
Notes/
├── 每日笔记/
│   ├── 2026-05-20.md
│   └── 2026-05-19.md
├── 技术文档/
│   ├── Docker 入门.md
│   └── Git 技巧.md
└── 写作/
    └── 长篇小说/
        └── 第一章.md
```

## 九、项目信息

- **作者**：zakirullin
- **开源协议**：MIT
- **当前状态**：活跃维护

## 十、资源链接

- GitHub：[zakirullin/files.md](https://github.com/zakirullin/files.md)