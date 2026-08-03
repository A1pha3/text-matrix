---
title: "Repomix：11.4K Stars·把代码库压缩成AI可读的单一文件"
date: "2026-04-12T01:50:00+08:00"
slug: repomix-ai-codebase-compression-guide
description: "Repomix 把 Git 仓库打包成 AI 可读的单一文件，内置安全检查、Token 计数和 Tree-sitter 压缩。从 CLI 到 CI 集成全覆盖。"
draft: false
categories: ["技术笔记"]
tags: ["Claude", "LLM", "Git"]
---

# Repomix：把代码库压缩成 AI 可读的单一文件

把一整个仓库扔给 ChatGPT 或 Claude 之前，你通常得手动挑文件、拼 prompt、算 Token。Repomix 把这个过程压缩成一条命令：扫描仓库 → 按规则筛选文件 → 打包成一份带 Token 计数的 XML/Markdown/JSON 输出，直接丢给模型。

输入输出对照：

| 你给的 | Repomix 还给你的 |
|--------|-----------------|
| 一个 Git 仓库目录（或 GitHub URL） | 一份 `repomix-output.xml`（或其他可选格式） |
| `.gitignore` / `.repomixignore` 规则 | 自动跳过不该打包的文件 |
| 可选的 `--compress` 开关 | Tree-sitter 抽取函数签名、类定义，砍掉实现细节 |
| 可选的 `--include-logs` | 附带最近 N 条提交记录和 diff |

打包分四步：glob 搜索 → 逐文件读取 → AST 压缩（可选）→ 拼接输出。

---

## 核心技术原理

### 代码库打包流程

**第一阶段：文件搜索。** 通过 glob 模式匹配文件，结合 Git ignore 规则筛选出待处理文件列表，`include` 和 `ignore` 选项支持精确控制。

**第二阶段：文件读取。** 对每个匹配文件读取完整内容，根据配置决定是否移除注释。支持移除注释的语言包括：HTML、CSS、JavaScript、TypeScript、Vue、Svelte、Python、PHP、Ruby、C、C#、Java、Go、Rust、Swift、Kotlin、Dart、Shell 和 YAML。

**第三阶段：内容处理。** 每个文件被包装成统一格式，包含路径、内容、语言类型和 Token 数量：

```xml
<file path="src/index.ts">
  <content>
    <!-- 文件内容 -->
  </content>
  <language>typescript</language>
  <tokens>1234</tokens>
</file>
```

**第四阶段：输出生成。** 处理完成的文件打包成单一文件，支持 XML、Markdown、JSON 和纯文本四种格式。

### 智能压缩原理

`--compress` 选项使用 Tree-sitter 构建 AST，保留函数签名、类定义、接口和类型声明等核心结构，去除实现细节。TypeScript/JavaScript 和 Python 文件均支持相应语言结构的精确提取。

### Token 计数机制

内置 TokenCounter 类，默认使用 `o200k_base`（GPT-4o 及更新模型使用的编码）。每个文件的 Token 数量在输出中单独显示，便于了解代码库规模是否接近 LLM 上下文限制。

---

## 快速上手

### CLI 安装与使用

直接使用 npx：

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

在任意项目目录中运行：

```bash
repomix
```

会在当前目录生成 `repomix-output.xml` 文件，包含整个仓库的 AI 友好格式内容。

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

访问 [repomix.com](https://repomix.com)，输入仓库名称和可选配置，点击 Pack 按钮即可在线生成打包文件。支持自定义输出格式和即时 Token 数量估算。

### 浏览器扩展

Chrome 和 Firefox 扩展在任意 GitHub 仓库页面添加便捷的 Repomix 按钮：

- Chrome 扩展：[Repomix - Chrome Web Store](https://chromewebstore.google.com/detail/repomix/fimfamikepjgchehkohedilpdigcpkoa)
- Firefox 插件：[Repomix - Firefox Add-ons](https://addons.mozilla.org/firefox/addon/repomix/)

### VSCode 插件

社区维护的 [Repomix Runner](https://marketplace.visualstudio.com/items?itemName=DorianMassoulier.repomix-runner) 插件允许用户在编辑器中直接运行 Repomix，管理输出文件和控制清理选项。

---

## 配置文件详解

### 初始化配置文件

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

**output.format**：指定输出文件的格式，可选 `xml`（适合 Claude 等模型处理）、`markdown`（便于阅读）、`json`（适合程序解析）、`plain`（纯文本，最小依赖）。

**output.style**：控制输出样式的详细配置：
- `tableStyle`：文件列表的表格样式，可选 `pretty`（带边框）或 `plain`（纯文本）
- `separateFiles`：是否在文件之间添加分隔符
- `lineNumbers`：是否为每行添加行号
- `title`：是否包含文件路径标题

**include 和 ignore**：数组类型的配置项，支持 glob 模式：

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

**outputInstructionFile**：指定包含指令的文件路径。指令内容会被追加到输出文件的末尾——将指令放在提示顶部可以获得更好的效果。

**security.enableSecurityCheck**：布尔值，控制在打包前是否运行 Secretlint 安全检查。检测到敏感信息时会发出警告：

```
🔍 Security Check:
──────────────────
2 suspicious file(s) detected:
1. src/utils/test.txt
2. tests/utils/secretLintUtils.test.ts
```

### 配置继承与覆盖

CLI 参数会覆盖配置文件中的对应设置。例如，配置文件设置了压缩但 CLI 使用 `--no-compress`，则实际运行时不进行压缩。

---

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

这条流水线里，压缩砍掉了实现细节让 Token 不超限，Git 日志提供了改动动机，安全检查在送出去之前拦住了硬编码密钥——三个机制分别解决不同层面的问题。

---

## GitHub Actions 集成

### 基础工作流

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

---

## 作为 Library 使用

### Node.js 集成

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

```javascript
import { searchFiles, collectFiles, processFiles, TokenCounter } from 'repomix';

async function analyzeFiles(directory) {
  const { filePaths } = await searchFiles(directory, { /* config */ });
  const rawFiles = await collectFiles(filePaths, directory);
  const processedFiles = await processFiles(rawFiles, { /* config */ });
  
  const tokenCounter = new TokenCounter('o200k_base');
  
  return processedFiles.map(file => ({
    path: file.path,
    tokens: tokenCounter.countTokens(file.content)
  }));
}
```

### 打包注意事项

使用 Rolldown 或 esbuild 打包时：

**必须保持为外部依赖（不能打包）：** `tinypool`——使用文件路径生成 Worker 线程。

**需要复制的 WASM 文件：**
- `web-tree-sitter.wasm` → 打包后的 JS 同目录
- Tree-sitter 语言文件 → 通过 `REPOMIX_WASM_DIR` 环境变量指定目录

---

## 安全检查详解

Repomix 集成 [Secretlint](https://github.com/secretlint/secretlint) 进行敏感信息检测，能够识别以下类型的敏感数据：

- AWS 访问密钥、AWS Secret Access Key
- GitHub Personal Access Token、GitHub OAuth Access Token
- Google API Key、Google OAuth Token
- JWT Token、Mailchimp API Key
- NPI Number、OpenAI API Key
- Password in URL
- Private Key（RSA, EC, DSA, ED25519, PGP）
- Slack Token、Square OAuth Secret
- Stripe Access Token、Twilio API Key

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

---

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

---

## 实践建议

**与 Claude 配合。** 把 Repomix 输出发给 Claude 时，用这个提示模板开头：

```
This file contains all the files in the repository combined into one.
I want to refactor the code, so please review it first.
```

将仓库内容放在提示顶部（指令之前），Claude 的响应质量可提升最高 30%——这在 Anthropic 的长上下文实践建议中也有对应建议。

**仓库太大。** Token 数接近 LLM 上下文上限时：开 `--compress` 让 Tree-sitter 砍掉实现细节；用 `--include` 只打包关心的目录；用 `--ignore` 排除测试、文档等非核心内容；调 `--include-logs-count` 控制历史条数。

**安全检查。** 保持 `enableSecurityCheck: true`（默认已开启）；输出发给 AI 之前扫一眼告警；测试文件里如果放了假凭证，确保内容无害再用 `--no-security-check`。

---

## 社区项目

Repomix 催生了多个社区项目：

- [Repomix Runner](https://github.com/massdo/repomix-runner)：VSCode 扩展
- [Repomix Desktop](https://github.com/KevanMacGee/Repomix-Desktop)：Python+Tkinter 桌面应用
- [Python Repomix](https://github.com/AndersonBY/python-repomix)：Python 实现，基于 AST 压缩
- [Rulefy](https://github.com/niklub/rulefy)：将 GitHub 仓库转换为 Cursor AI 规则
- [Codebase MCP](https://github.com/DeDeveloper23/codebase-mcp)：MCP 服务器，提供 AI 代码库分析
- [vibe-tools](https://github.com/eastlondoner/vibe-tools)：CLI 工具集，包含 Web 搜索、仓库分析、浏览器自动化

---

## 参考链接

- GitHub 仓库：https://github.com/yamadashy/repomix
- 在线平台：https://repomix.com
- Discord 社区：https://discord.gg/wNYzTwZFku
- npm 包：https://www.npmjs.com/package/repomix