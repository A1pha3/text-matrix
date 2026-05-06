---
title: "Repomix：11.4K Stars·代码库压缩成AI友好格式的利器"
date: "2026-04-12T01:50:00+08:00"
slug: repomix-ai-codebase-compression-guide
description: "Repomix 是一款强大的代码库压缩工具，将 Git 仓库打包成 AI 友好的格式，支持 Claude、ChatGPT、DeepSeek 等大语言模型。"
draft: false
categories: ["技术笔记"]
tags: ["AI", "代码压缩", "Claude", "LLM", "Git"]
---

# Repomix：11.4K Stars·代码库压缩成AI友好格式的利器

## 学习目标

- 理解 Repomix 的核心概念和使用场景
- 掌握 CLI、Web、Web Extension 三种使用方式
- 学会配置 repomix.config.json 实现定制化
- 了解安全检查和压缩原理
- 掌握在 GitHub Actions 中的集成方法
- 学会将 Repomix 作为 Library 集成到自己的应用中

## 项目概述

Repomix 是一款强大的代码库压缩工具，能够将整个 Git 仓库打包成对 AI 模型友好的单一文件格式。当需要向 ChatGPT、Claude、DeepSeek、Gemini 等大语言模型提供代码上下文时，Repomix 可以帮助用户快速整理和压缩代码库，避免手动复制粘贴的繁琐。

Repomix 具备以下核心特点：

- **AI 优化输出**：自动将代码格式化为 LLM 易于理解和处理的结构
- **Token 计数**：为每个文件和整个仓库提供精确的 Token 数量统计
- **Git 感知**：自动尊重 .gitignore、.ignore 和 .repomixignore 文件
- **安全检查**：集成 Secretlint 检测敏感信息泄露
- **代码压缩**：使用 Tree-sitter 提取关键代码元素，减少 Token 用量

Repomix 支持多种使用方式：CLI 命令行、Web 在线平台、Chrome/Firefox 浏览器扩展、VSCode 插件，以及作为 Node.js Library 集成到自己的应用中。

## 核心技术原理

### 代码库打包流程

Repomix 的核心工作流程分为四个阶段：

**第一阶段：文件搜索**

Repomix 使用 glob 模式匹配文件，结合 Git ignore 规则筛选出需要处理的文件列表。配置文件中的 `include` 和 `ignore` 选项可以精确控制文件的包含和排除。

**第二阶段：文件读取**

对于每个匹配的文件，Repomix 读取完整的文件内容，并根据配置决定是否移除注释。支持移除注释的语言包括：HTML、CSS、JavaScript、TypeScript、Vue、Svelte、Python、PHP、Ruby、C、C#、Java、Go、Rust、Swift、Kotlin、Dart、Shell 和 YAML。

**第三阶段：内容处理**

文件内容被包装成统一格式，包含文件路径、相对内容、语言类型和 Token 数量。XML 格式的结构如下：

```xml
<file path="src/index.ts">
  <content>
    <!-- 文件内容 -->
  </content>
  <language>typescript</language>
  <tokens>1234</tokens>
</file>
```

**第四阶段：输出生成**

处理完成的文件被打包成单一输出文件，支持 XML、Markdown、JSON 和纯文本四种格式。

### 智能压缩原理

Repomix 的 `--compress` 选项使用 Tree-sitter 进行代码压缩。Tree-sitter 是一个增量解析库，能够构建代码的抽象语法树（AST）。压缩过程会保留关键的语法结构，去除不必要的实现细节，同时保持代码的可读性和完整性。

对于 TypeScript/JavaScript 文件，压缩会保留函数签名、类定义、接口和类型声明等核心元素。对于 Python 文件，会保留函数定义、类结构和导入语句。

### Token 计数机制

Repomix 内置 TokenCounter 类，支持多种编码方式。默认使用 `o200k_base`（GPT-4o 及更新模型使用的编码）。每个文件的 Token 数量在输出中单独显示，便于用户了解代码库的规模以及是否接近 LLM 的上下文限制。

## 快速上手

### CLI 安装与使用

Repomix 支持多种安装方式，最简单的方式是直接使用 npx 运行：

```bash
npx repomix@latest
```

或者全局安装以便重复使用：

```bash
# 使用 npm 安装
npm install -g repomix

# 使用 yarn 安装
yarn global add repomix

# 使用 bun 安装
bun add -g repomix

# 使用 Homebrew 安装（macOS/Linux）
brew install repomix
```

安装完成后，在任意项目目录中运行：

```bash
repomix
```

Repomix 会在当前目录生成 `repomix-output.xml` 文件，包含整个仓库的 AI 友好格式内容。

### 基础命令

**打包当前目录：**

```bash
repomix
```

**打包指定目录：**

```bash
repomix path/to/directory
```

**使用 glob 模式打包特定文件：**

```bash
repomix --include "src/**/*.ts,**/*.md"
```

**排除特定文件或目录：**

```bash
repomix --ignore "**/*.log,tmp/"
```

**打包远程仓库：**

```bash
# 直接使用 URL
repomix --remote https://github.com/yamadashy/repomix

# 使用 GitHub 简写
repomix --remote yamadashy/repomix

# 指定分支
repomix --remote https://github.com/yamadashy/repomix --remote-branch main

# 指定提交哈希
repomix --remote https://github.com/yamadashy/repomix --remote-branch 935b695
```

**通过 stdin 管道传入文件列表：**

```bash
# 使用 find 命令
find src -name "*.ts" -type f | repomix --stdin

# 使用 git 获取已跟踪的文件
git ls-files "*.ts" | repomix --stdin

# 使用 ripgrep 查找包含特定内容的文件
rg -l "TODO|FIXME" --type ts | repomix --stdin

# 使用 fzf 交互式选择文件
find . -name "*.ts" -type f | fzf -m | repomix --stdin
```

**包含 Git 提交历史：**

```bash
# 包含默认 50 条提交记录
repomix --include-logs

# 指定提交数量
repomix --include-logs --include-logs-count 10

# 同时包含 diff
repomix --include-logs --include-diffs
```

**启用压缩：**

```bash
repomix --compress

# 远程仓库也支持压缩
repomix --remote yamadashy/repomix --compress
```

### Web 在线平台

访问 [repomix.com](https://repomix.com)，输入仓库名称和可选配置，点击 Pack 按钮即可在线生成打包文件。在线平台支持自定义输出格式（XML、Markdown、纯文本）和即时 Token 数量估算。

### 浏览器扩展

Repomix 提供 Chrome 和 Firefox 扩展，在任意 GitHub 仓库页面添加便捷的 Repomix 按钮：

- Chrome 扩展：[Repomix - Chrome Web Store](https://chromewebstore.google.com/detail/repomix/fimfamikepjgchehkohedilpdigcpkoa)
- Firefox 插件：[Repomix - Firefox Add-ons](https://addons.mozilla.org/firefox/addon/repomix/)

### VSCode 插件

社区维护的 [Repomix Runner](https://marketplace.visualstudio.com/items?itemName=DorianMassoulier.repomix-runner) 插件允许用户在编辑器中直接运行 Repomix，管理输出文件，控制清理选项。

## 配置文件详解

### 初始化配置文件

在项目目录中运行以下命令生成默认配置文件：

```bash
repomix --init
```

生成的 `repomix.config.json` 文件结构如下：

```json
{
  "output": {
    "format": "xml",
    "filePath": "repomix-output.xml",
    "style": {
      "tableStyle": "pretty",
      "separateFiles": true,
      "lineNumbers": false,
      "title": true
    }
  },
  "include": [],
  "ignore": [
    "**/.git/**",
    "**/node_modules/**",
    "**/dist/**",
    "**/.venv*/**",
    "**/venv*/**"
  ],
  "security": {
    "enableSecurityCheck": true
  },
  "compression": {
    "enabled": false
  }
}
```

### 核心配置项

**output.format**

指定输出文件的格式，可选值包括：

- `xml`：XML 格式，适合 Claude 等模型处理
- `markdown`：Markdown 格式，便于阅读
- `json`：JSON 格式，适合程序解析
- `plain`：纯文本格式，最小依赖

**output.style**

控制输出样式的详细配置：

- `tableStyle`：文件列表的表格样式，可选 `pretty`（带边框）或 `plain`（纯文本）
- `separateFiles`：是否在文件之间添加分隔符
- `lineNumbers`：是否为每行添加行号
- `title`：是否包含文件路径标题

**include 和 ignore**

数组类型的配置项，支持 glob 模式：

```json
{
  "include": [
    "src/**/*.ts",
    "tests/**/*.ts",
    "**/*.md"
  ],
  "ignore": [
    "**/*.test.ts",
    "**/tmp/**",
    "**/coverage/**"
  ]
}
```

**outputInstructionFile**

指定包含指令的文件路径。指令内容会被追加到输出文件的末尾，这对于 Claude 等模型特别有效，因为将长文档放在提示的顶部可以获得更好的效果。

**security.enableSecurityCheck**

布尔值，控制在打包前是否运行 Secretlint 安全检查。检测到敏感信息时会发出警告：

```
🔍 Security Check:
──────────────────
2 suspicious file(s) detected:
1. src/utils/test.txt
2. tests/utils/secretLintUtils.test.ts
```

### 配置继承与覆盖

CLI 参数会覆盖配置文件中的对应设置。例如，配置文件设置了压缩但 CLI 使用 `--no-compress`，则实际运行时不进行压缩。

## GitHub Actions 集成

### 基础工作流

在 GitHub Actions 中使用 Repomix 打包代码库：

```yaml
name: Pack repository with Repomix

on:
  workflow_dispatch:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  pack-repo:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Pack repository with Repomix
        uses: yamadashy/repomix/.github/actions/repomix@main
        with:
          output: repomix-output.xml
          style: xml

      - name: Upload Repomix output
        uses: actions/upload-artifact@v4
        with:
          name: repomix-output.xml
          path: repomix-output.xml
          retention-days: 30
```

### Action 参数详解

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `directories` | 空格分隔的目录列表 | `.` |
| `include` | 逗号分隔的 glob 模式 | `""` |
| `ignore` | 逗号分隔的忽略模式 | `""` |
| `output` | 输出文件路径（扩展名决定格式） | `repomix-output.xml` |
| `compress` | 启用智能压缩 | `true` |
| `style` | 输出样式：`xml`、`markdown`、`json`、`plain` | `xml` |
| `additional-args` | 额外的 CLI 参数 | `""` |
| `repomix-version` | npm 包版本 | `latest` |

### 完整示例

打包指定目录并上传为 Artifact：

```yaml
- name: Pack repository with Repomix
  uses: yamadashy/repomix/.github/actions/repomix@main
  with:
    directories: src tests
    include: "**/*.ts,**/*.md"
    ignore: "**/*.test.ts"
    output: repomix-output.txt
    compress: true

- name: Upload Repomix output
  uses: actions/upload-artifact@v4
  with:
    name: repomix-output
    path: repomix-output.txt
```

## 作为 Library 使用

### Node.js 集成

在 Node.js 应用中使用 Repomix：

```bash
npm install repomix
```

**基础用法：**

```javascript
import { runCli, type CliOptions } from 'repomix';

async function packProject() {
  const options = {
    output: 'output.xml',
    style: 'xml',
    compress: true,
    quiet: true
  } as CliOptions;
  
  const result = await runCli(['.'], process.cwd(), options);
  return result.packResult;
}
```

**处理远程仓库：**

```javascript
import { runCli, type CliOptions } from 'repomix';

async function processRemoteRepo(repoUrl) {
  const options = {
    remote: repoUrl,
    output: 'output.xml',
    compress: true
  } as CliOptions;
  
  return await runCli(['.'], process.cwd(), options);
}
```

### 低级 API

需要更多控制时，可以直接使用低级 API：

```javascript
import { searchFiles, collectFiles, processFiles, TokenCounter } from 'repomix';

async function analyzeFiles(directory) {
  // 查找并收集文件
  const { filePaths } = await searchFiles(directory, { /* config */ });
  const rawFiles = await collectFiles(filePaths, directory);
  const processedFiles = await processFiles(rawFiles, { /* config */ });
  
  // Token 计数
  const tokenCounter = new TokenCounter('o200k_base');
  
  // 返回分析结果
  return processedFiles.map(file => ({
    path: file.path,
    tokens: tokenCounter.countTokens(file.content)
  }));
}
```

### 打包注意事项

使用 Rolldown 或 esbuild 打包时，需要注意：

**必须保持为外部依赖（不能打包）：**

- `tinypool`：使用文件路径生成 Worker 线程

**需要复制的 WASM 文件：**

- `web-tree-sitter.wasm` → 打包后的 JS 同目录
- Tree-sitter 语言文件 → 通过 `REPOMIX_WASM_DIR` 环境变量指定目录

## 安全检查详解

Repomix 集成 [Secretlint](https://github.com/secretlint/secretlint) 进行敏感信息检测，能够识别以下类型的敏感数据：

- AWS 访问密钥
- AWS Secret Access Key
- GitHub Personal Access Token
- GitHub OAuth Access Token
- Google API Key
- Google OAuth Token
- JWT Token
- Mailchimp API Key
- NPI Number
- OpenAI API Key
- Password in URL
- Private Key (RSA, EC, DSA, ED25519, PGP)
- Slack Token
- Square OAuth Secret
- Stripe Access Token
- Twilo API Key

安全检查默认启用。可以通过以下方式禁用：

**配置文件方式：**

```json
{
  "security": {
    "enableSecurityCheck": false
  }
}
```

**命令行方式：**

```bash
repomix --no-security-check
```

## 输出格式对比

### XML 格式（默认）

```xml
<?xml version="1.0" encoding="UTF-8"?>
<repomix>
  <header>
    <repository>yamadashy/repomix</repository>
    <branch>main</branch>
    <commit>935b695</commit>
    <date>2026-04-12</date>
    <fileCount>42</fileCount>
    <totalTokens>52340</totalTokens>
  </header>
  <files>
    <file path="src/index.ts">
      <content>
import { repomix } from 'repomix';
      </content>
      <language>typescript</language>
      <tokens>1247</tokens>
    </file>
  </files>
</repomix>
```

### Markdown 格式

```markdown
# Repository: yamadashy/repomix

## Files

### src/index.ts
```typescript
import { repomix } from 'repomix';
```
- Language: typescript
- Tokens: 1247

---
```

### JSON 格式

```json
{
  "header": {
    "repository": "yamadashy/repomix",
    "branch": "main",
    "totalTokens": 52340,
    "fileCount": 42
  },
  "files": [
    {
      "path": "src/index.ts",
      "content": "import { repomix } from 'repomix';",
      "language": "typescript",
      "tokens": 1247
    }
  ]
}
```

## 社区项目

Repomix 催生了多个社区项目：

- [Repomix Runner](https://github.com/massdo/repomix-runner)：VSCode 扩展
- [Repomix Desktop](https://github.com/KevanMacGee/Repomix-Desktop)：Python+Tkinter 桌面应用
- [Python Repomix](https://github.com/AndersonBY/python-repomix)：Python 实现，基于 AST 压缩
- [Rulefy](https://github.com/niklub/rulefy)：将 GitHub 仓库转换为 Cursor AI 规则
- [Codebase MCP](https://github.com/DeDeveloper23/codebase-mcp)：MCP 服务器，提供 AI 代码库分析
- [vibe-tools](https://github.com/eastlondoner/vibe-tools)：CLI 工具集，包含 Web 搜索、仓库分析、浏览器自动化

## 最佳实践

### 与 Claude 配合使用

将 Repomix 输出发送给 Claude 时，建议使用以下提示模板：

```
This file contains all the files in the repository combined into one.
I want to refactor the code, so please review it first.
```

对于复杂的多文档输入，将 Repomix 输出放在提示的顶部（指令之前），可以提升 Claude 的响应质量最高达 30%。

### 处理大型代码库

当代码库 Token 数量接近 LLM 上下文限制时：

1. 使用 `--compress` 选项启用智能压缩
2. 使用 `--include` 限定只打包需要的部分
3. 使用 `--ignore` 排除测试文件、文档等非核心内容
4. 利用 `--include-logs-count` 控制提交历史的数量

### 安全建议

1. 始终保持 `enableSecurityCheck: true`（默认开启）
2. 在推送代码到 AI 服务之前，检查安全警告
3. 对于包含真实凭证的测试文件，使用 `--no-security-check` 前确保文件内容是安全的

## 常见问题

### Q：Repomix 和 Gitingest 有什么区别？

A：Repomix 使用 TypeScript 开发，主要针对 JavaScript/TypeScript 生态系统优化，支持更多配置选项和输出格式。Gitingest 使用 Python 开发，更适合 Python 数据科学工作流。

### Q：压缩后的代码可以完全替代原始代码吗？

A：不能。`--compress` 选项会移除部分实现细节以减少 Token 用量。对于需要完整代码上下文的场景（如详细代码审查、重构），建议使用非压缩模式。

### Q：支持私有仓库吗？

A：支持。使用 `--remote` 时，Repomix 会通过 GitHub API 获取公开仓库。对于私有仓库，需要先将仓库克隆到本地，然后使用本地模式打包。

### Q：如何处理 Mono-repo？

A：对于 Mono-repo 架构，可以使用 `--include` 和 `--ignore` 选项精确指定需要打包的子包或目录。

## 总结

Repomix 是现代 AI 辅助开发的利器，它能够快速将任意规模的代码库压缩成 AI 模型易于处理的格式。通过支持 CLI、Web、浏览器扩展和 Library 多种使用方式，Repomix 满足了不同场景的需求。其内置的安全检查和 Git 感知功能，确保了打包过程的安全性和准确性。

无论是需要向 AI 模型寻求代码审查帮助，还是进行跨仓库的技术调研，Repomix 都能显著提升效率。随着 AI 代码助手的普及，掌握 Repomix 的使用将成为每位开发者的必备技能。

## 安装速查表

```bash
# 快速试用（无需安装）
npx repomix@latest

# npm 全局安装
npm install -g repomix

# Homebrew 安装
brew install repomix

# 在当前目录打包
repomix

# 打包并压缩
repomix --compress

# 打包远程仓库
repomix --remote owner/repo

# 初始化配置文件
repomix --init
```

## 参考链接

- GitHub 仓库：https://github.com/yamadashy/repomix
- 在线平台：https://repomix.com
- Discord 社区：https://discord.gg/wNYzTwZFku
- npm 包：https://www.npmjs.com/package/repomix
