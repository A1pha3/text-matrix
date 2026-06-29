---
title: "Repomix：11.4K Stars·把代码库压缩成AI可读的单一文件"
date: "2026-04-12T01:50:00+08:00"
slug: repomix-ai-codebase-compression-guide
description: "Repomix 把 Git 仓库打包成 AI 可读的单一文件，内置安全检查、Token 计数和 Tree-sitter 压缩。从 CLI 到 CI 集成，一篇讲完。"
draft: false
categories: ["技术笔记"]
tags: ["AI", "代码压缩", "Claude", "LLM", "Git"]
---

# Repomix：把代码库压缩成 AI 可读的单一文件

## 读完这篇你会

- 知道什么时候该用 Repomix 打包、什么时候不需要
- 用 CLI 一行命令打包整个仓库，指定格式和压缩
- 配出适合自己项目的 `repomix.config.json`
- 清楚安全检查在挡什么，压缩在省多少 Token
- 在 GitHub Actions 里自动打包，或在 Node.js 项目里当库调用

## 目录

- [Repomix 解决的是什么](#repomix-解决的是什么)
- [核心技术原理](#核心技术原理)
- [快速上手](#快速上手)
- [配置文件详解](#配置文件详解)
- [一次真实流转：把项目发给 Claude 做安全审查](#一次真实流转把项目发给-claude-做安全审查)
- [GitHub Actions 集成](#github-actions-集成)
- [作为 Library 使用](#作为-library-使用)
- [安全检查详解](#安全检查详解)
- [输出格式对比](#输出格式对比)
- [社区项目](#社区项目)
- [实践建议](#实践建议)
- [常见问题](#常见问题)
- [什么时候用、什么时候不用](#什么时候用什么时候不用)
- [安装速查表](#安装速查表)
- [参考链接](#参考链接)
- [自测题](#自测题)
- [练习](#练习)
- [进阶路径](#进阶路径)
- [资料口径说明](#资料口径说明)

---

## Repomix 解决的是什么

把一整个仓库扔给 ChatGPT 或 Claude 之前，你通常得手动挑文件、拼 prompt、算 Token。Repomix 把这个过程压缩成一条命令：扫描仓库 → 按规则筛选文件 → 打包成一份带 Token 计数的 XML/Markdown/JSON 输出，直接丢给模型。

输入输出对照：

| 你给的 | Repomix 还给你的 |
|--------|-----------------|
| 一个 Git 仓库目录（或 GitHub URL） | 一份 `repomix-output.xml`（或其他可选格式） |
| `.gitignore` / `.repomixignore` 规则 | 自动跳过不该打包的文件 |
| 可选的 `--compress` 开关 | Tree-sitter 抽取函数签名、类定义，砍掉实现细节 |
| 可选的 `--include-logs` | 附带最近 N 条提交记录和 diff |

打包分四步：glob 搜索 → 逐文件读取 → AST 压缩（可选）→ 拼接输出。下面先把这个流水线拆开看，再讲怎么配、怎么嵌进 CI 流水线、什么时候用压缩、什么时候不该用。

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

## 一次真实流转：把项目发给 Claude 做安全审查

假设你在维护一个 TypeScript 后端项目，最近加了一套 JWT 认证逻辑，想发给 Claude 做安全审查。

**第一步：打包**

```bash
repomix --compress --include-logs --include-logs-count 20
```

三条事一起做了：Tree-sitter 压缩代码省 Token；附带最近 20 条提交记录让 Claude 了解改动上下文；同时跑 Secretlint 安全检查。

**第二步：安全检查告警**

```
🔍 Security Check:
──────────────────
1 suspicious file(s) detected:
1. src/auth/config.ts
```

打开 `config.ts`，发现测试时硬编码了一个 JWT secret。修掉它，再跑一次 `repomix`，检查通过。

**第三步：发给 Claude**

把 `repomix-output.xml` 贴进 Claude 对话里，前面加一句：

> 这份文件包含了整个仓库的代码和最近 20 条提交记录。请重点审查 src/auth/ 下的认证逻辑，检查是否存在令牌泄露、过期策略不当或权限绕过风险。

Claude 在这一次对话里同时看到模块结构、调用关系和变更历史，不需要你来回补充上下文。

这条流水线里，压缩砍掉了实现细节让 Token 不超限，Git 日志提供了改动动机，安全检查在送出去之前拦住了硬编码密钥 — 三个机制分别解决不同层面的问题。

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

## 实践建议

### 与 Claude 配合

把 Repomix 输出发给 Claude 时，用这个提示模板开头：

```
This file contains all the files in the repository combined into one.
I want to refactor the code, so please review it first.
```

把仓库内容放在提示顶部（指令之前），Claude 的响应质量可以提升最高 30% — 这在 Anthropic 的长上下文实践建议中也有对应建议。

### 仓库太大怎么办

Token 数接近 LLM 上下文上限时：

1. 开 `--compress`，让 Tree-sitter 砍掉实现细节
2. 用 `--include` 只打包关心的目录
3. 用 `--ignore` 排除测试、文档等非核心内容
4. 调 `--include-logs-count` 控制历史条数

### 安全检查

1. 保持 `enableSecurityCheck: true`（默认就是开的）
2. 输出发给 AI 之前扫一眼告警
3. 测试文件里如果放了假凭证，确保内容无害再用 `--no-security-check`

## 常见问题

### Q：Repomix 和 Gitingest 有什么区别？

A：Repomix 使用 TypeScript 开发，主要针对 JavaScript/TypeScript 生态系统优化，支持更多配置选项和输出格式。Gitingest 使用 Python 开发，更适合 Python 数据科学工作流。

### Q：压缩后的代码可以完全替代原始代码吗？

A：不能。`--compress` 选项会移除部分实现细节以减少 Token 用量。对于需要完整代码上下文的场景（如详细代码审查、重构），建议使用非压缩模式。

### Q：支持私有仓库吗？

A：支持。使用 `--remote` 时，Repomix 会通过 GitHub API 获取公开仓库。对于私有仓库，需要先将仓库克隆到本地，然后使用本地模式打包。

### Q：如何处理 Mono-repo？

A：对于 Mono-repo 架构，可以使用 `--include` 和 `--ignore` 选项精确指定需要打包的子包或目录。

## 什么时候用、什么时候不用

**先用起来的场景：**

- 要做跨文件代码审查（安全审计、重构方案评估），一次打包省去手动拼上下文
- 在 CI 里自动生成代码库快照，作为 AI Review 的固定输入
- 接手新项目时，用压缩模式先看模块骨架和调用关系

**可以先不急的场景：**

- 只问单文件问题 — 直接贴代码更快
- 仓库超过 200K Token 且压缩后仍超 — 用 `--include` 拆成多个子包分批发送
- 需要完整逐行审查 — 关闭压缩（`--no-compress`），否则 Tree-sitter 砍掉的实现细节可能恰是你要看的

**从哪开始：**

1. 先 `npx repomix@latest` 在项目里跑一次，看输出长什么样
2. 跑 `repomix --init` 生成配置文件，按项目结构调整 `include` / `ignore`
3. 熟悉后把 `repomix --compress` 嵌进日常流程，或写进 GitHub Actions

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

---

## 自测题

**1. Repomix 的核心价值是什么？**

<details>
<summary>点击查看参考答案</summary>

Repomix 的核心价值在于把整个代码仓库打包成 AI 可读的单一文件，内置安全检查、Token 计数和 Tree-sitter 压缩。它解决了把代码库发给 AI 模型时需要手动挑文件、拼 prompt、算 Token 的痛点。

</details>

**2. 如何使用 Repomix 打包远程 GitHub 仓库？**

<details>
<summary>点击查看参考答案</summary>

使用 `--remote` 参数：
```bash
# 直接使用 URL
repomix --remote https://github.com/yamadashy/repomix

# 使用 GitHub 简写
repomix --remote yamadashy/repomix

# 指定分支
repomix --remote yamadashy/repomix --remote-branch main
```

</details>

**3. Repomix 的 `--compress` 选项是什么原理？**

<details>
<summary>点击查看参考答案</summary>

`--compress` 选项使用 Tree-sitter 进行代码压缩。Tree-sitter 是一个增量解析库，能够构建代码的抽象语法树（AST）。压缩过程会保留关键的语法结构（如函数签名、类定义、接口和类型声明），去除不必要的实现细节，同时保持代码的可读性和完整性。

</details>

**4. 如何禁用 Repomix 的安全检查？**

<details>
<summary>点击查看参考答案</summary>

可以通过以下方式禁用安全检查：

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

但建议保持安全检查开启，除非测试文件中包含无害的假凭证。

</details>

**5. Repomix 支持哪些输出格式？**

<details>
<summary>点击查看参考答案</summary>

Repomix 支持以下输出格式：
1. **XML**（默认）：适合 Claude 等模型处理
2. **Markdown**：便于阅读
3. **JSON**：适合程序解析
4. **Plain**：纯文本格式，最小依赖

</details>

---

## 练习

### 练习 1：基本打包

**任务**：使用 Repomix 打包一个本地项目

1. 选择一个本地 Git 项目
2. 运行 `repomix` 打包整个项目
3. 查看生成的 `repomix-output.xml`
4. 尝试不同输出格式（Markdown、JSON）
5. 检查 Token 计数

**参考答案**：熟悉 Repomix 的基本使用，理解不同输出格式的区别。

### 练习 2：配置文件优化

**任务**：为项目创建自定义配置文件

1. 运行 `repomix --init` 生成配置文件
2. 配置 `include` 只打包源代码文件
3. 配置 `ignore` 排除测试文件和构建产物
4. 启用压缩模式
5. 测试配置是否生效

**参考答案**：掌握配置文件的使用，理解 include/ignore 规则。

### 练习 3：GitHub Actions 集成

**任务**：在 GitHub Actions 中自动打包代码库

1. 创建 GitHub Actions 工作流文件
2. 使用 Repomix Action 打包代码
3. 上传打包结果为 Artifact
4. 测试工作流是否正常运行

**参考答案**：理解 CI/CD 集成，掌握自动化打包流程。

---

## 进阶路径

如果您已经掌握 Repomix 的基本使用，可以参考以下进阶路径：

1. **高级压缩配置**：针对特定语言优化 Tree-sitter 压缩规则
2. **自定义输出格式**：修改 XML/Markdown 模板以满足特定需求
3. **集成到开发流**：在 pre-commit hook 中自动打包，或集成到代码审查流程
4. **开发插件**：为 VSCode/Vim/Emacs 开发编辑器插件
5. **贡献到社区**：参与 Repomix 的开发，提交 PR 或改进文档

---

## 资料口径说明

本文基于以下来源撰写：

1. **官方 GitHub 仓库**：https://github.com/yamadashy/repomix
   - Stars、Forks、贡献者数量等数据来自 GitHub API
   - 最新版本信息来自仓库的 Releases 页面

2. **官方文档和 README**：
   - 安装方法、命令说明、配置选项来自官方文档
   - 技术原理说明基于 README 和源码分析

3. **版本时效性**：
   - 本文基于 Repomix 最新稳定版本编写
   - 新版本可能引入新功能或改变命令参数，请以官方文档为准

4. **事实边界**：
   - 本文提供的信息基于公开可查的官方资料
   - Token 计数和压缩效果因代码库而异，实际效果可能不同
   - 安全检查能力有限，不能保证检测所有敏感信息

---
