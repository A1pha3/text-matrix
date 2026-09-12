---
title: "Repomix：28K Stars·把代码库压缩成 AI 可读的单一文件"
date: "2026-04-12T01:50:00+08:00"
slug: repomix-ai-codebase-compression-guide
github_repo: "yamadashy/repomix"
source_key: "gh:yamadashy/repomix"
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

**第三阶段：内容处理。** 按配置逐文件处理：`removeComments` 剔除注释，`compress` 交给 Tree-sitter 抽取结构，`truncateBase64` 截断超长 Base64 数据。处理后的文件以「路径 + 内容」成对保存，例如 XML 输出里的文件块：

```xml
<file path="src/index.ts">
import { repomix } from 'repomix';
</file>
```

**第四阶段：输出生成。** 所有文件拼成单一文件。输出固定包含四部分：文件摘要（file_summary）、目录结构（directory_structure）、文件内容（files）和可选的 Git 日志（git_logs）。支持 XML、Markdown、JSON 和纯文本四种格式。

### 智能压缩原理

`--compress` 选项使用 Tree-sitter 构建 AST，保留函数签名、类定义、接口和类型声明等核心结构，去除实现细节。TypeScript/JavaScript 和 Python 文件均支持相应语言结构的精确提取。

### Token 计数机制

Token 估算基于 gpt-tokenizer，默认使用 `o200k_base`（GPT-4o 及更新模型使用的编码），可在配置中通过 `tokenCount.encoding` 切换（如 `cl100k_base` 对应 GPT-4/3.5）。CLI 会按文件统计 Token；`repomix --token-count-tree` 则按目录列出分布，一眼看清哪些目录在占上下文。

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

会在当前目录生成 `repomix-output.xml`，整个仓库被打包成 AI 可直接读取的格式。

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

生成 `repomix.config.json`。文件支持 JSON5 语法——可以写注释、加尾随逗号，配合 `$schema` 字段还能在编辑器里获得自动补全和校验：

```bash
# 生成全局配置，作为本地配置缺失时的兜底
repomix --init --global
```

全局配置在 macOS/Linux 上位于 `~/.config/repomix/`，Windows 上位于 `%LOCALAPPDATA%\Repomix\`。查找顺序：本地配置 > 全局配置 > CLI 默认值。

### 完整配置示例

```json
{
  "$schema": "https://repomix.com/schemas/latest/schema.json",
  "output": {
    "filePath": "repomix-output.xml",
    "style": "xml",
    "compress": false,
    "fileSummary": true,
    "directoryStructure": true,
    "removeComments": false
  },
  "include": ["**/*"],
  "ignore": {
    "useGitignore": true,
    "useDefaultPatterns": true,
    "customPatterns": ["**/*.log", "tmp/"]
  },
  "security": {
    "enableSecurityCheck": true
  },
  "tokenCount": {
    "encoding": "o200k_base"
  }
}
```

### 核心配置项

| 配置项 | 作用 | 默认值 |
|--------|------|--------|
| `output.filePath` | 输出文件名，扩展名决定格式 | `repomix-output.xml` |
| `output.style` | 输出格式：`xml`、`markdown`、`json`、`plain` | `xml` |
| `output.compress` | 用 Tree-sitter 压缩代码省 Token | `false` |
| `output.removeComments` | 剔除支持语言的注释 | `false` |
| `output.fileSummary` | 输出开头是否带文件摘要 | `true` |
| `output.directoryStructure` | 输出是否带目录树 | `true` |
| `output.filePathStyle` | 文件路径显示方式：`target-relative` / `cwd-relative` | `target-relative` |
| `output.parsableStyle` | 按格式转义输出，可解析性更好但更耗 Token | `false` |
| `output.git.includeLogs` | 是否附带 Git 提交历史 | `false` |
| `output.git.includeLogsCount` | 提交历史条数 | `50` |
| `output.instructionFilePath` | 指定指令文件，内容追加到输出末尾 | `null` |
| `ignore.useGitignore` | 采用项目的 `.gitignore` 规则 | `true` |
| `ignore.useDefaultPatterns` | 采用内置默认忽略（node_modules、.git 等） | `true` |
| `ignore.customPatterns` | 额外忽略模式 | `[]` |
| `security.enableSecurityCheck` | 打包前运行 Secretlint 安全检查 | `true` |
| `tokenCount.encoding` | Token 计数编码 | `o200k_base` |

`include` 和 `ignore.customPatterns` 都支持 glob 模式：

```json
{
  "include": ["src/**/*.ts", "tests/**/*.ts", "**/*.md"],
  "ignore": {
    "customPatterns": ["**/*.test.ts", "**/tmp/**", "**/coverage/**"]
  }
}
```

忽略规则的优先级从高到低：自定义模式 > 忽略文件（`.repomixignore`、`.ignore`、`.gitignore`、`.git/info/exclude`）> 内置默认模式。命令行 `-i, --ignore` 会覆盖配置文件中的自定义模式。

**output.instructionFilePath**：指向一个指令文件，其内容会追加到输出末尾，CLI 对应 `--instruction-file-path`。把指令写进文件、和代码一起维护，比每次手敲 prompt 更可复用。

**security.enableSecurityCheck**：默认开启，打包前用 Secretlint 扫描敏感信息。检测到可疑文件时会列出路径：

```
🔍 Security Check:
──────────────────
2 suspicious file(s) detected:
1. src/utils/test.txt
2. tests/utils/secretLintUtils.test.ts
```

### 配置继承与覆盖

配置文件按 TS > JS > JSON 的顺序查找：`repomix.config.ts`、`repomix.config.js`、`repomix.config.json5/jsonc/json`。CLI 参数优先级最高，覆盖配置文件里的对应设置。例如配置文件开启了压缩，但命令行传 `--no-compress`，实际不压缩。

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

这条流水线里，压缩砍掉实现细节让 Token 不超限，Git 日志补上改动动机，安全检查在送出去之前拦住硬编码密钥。三处改动各管一段。

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
| `compress` | 启用智能压缩，传 `false` 关闭 | `true` |
| `style` | 输出样式：`xml`、`markdown`、`plain` | `xml` |
| `additional-args` | 额外透传给 CLI 的原始参数 | `""` |
| `repomix-version` | npm 包版本（或 tag） | `latest` |
| `node-version` | Action 使用的 Node.js 版本 | `24` |

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

## 作为 MCP 服务器使用

Repomix 能以 MCP 服务器模式运行，让 Claude Code 等 AI 助手直接调用打包能力。这是实验性功能，官方会按反馈持续改进。

```bash
repomix --mcp
```

在 Claude Code 里注册：

```bash
claude mcp add repomix -- npx -y repomix --mcp
```

服务器暴露 `pack_codebase`、`pack_remote_repository` 等工具：agent 可以直接让它打包本地目录或远程仓库，再用 `grep_repomix_output` 按需检索输出内容，不必把整个文件塞进上下文。

对不受信任的客户端，用 `--sandbox` 把服务器限制在单个工作区内，只开放只读工具：

```bash
# 限制在当前工作目录内
repomix --mcp --sandbox

# 限制在指定目录内
repomix --mcp --sandbox path/to/project
```

`--sandbox` 是应用层的权限收窄，不是操作系统级沙箱；对外提供服务时，仍应在容器或独立用户下运行。

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

四种格式装的内容一样，组织方式不同。以下示例省略文件正文，只保留结构。

### XML 格式（默认）

```xml
<file_summary>
此文件是整个代码库的合并表示形式，供 AI 处理和上下文分析使用。
文件数量: 42
总 token 数: 52,340
</file_summary>
<directory_structure>
src/
  index.ts
  utils/
    helper.ts
</directory_structure>
<files>
<file path="src/index.ts">
import { repomix } from 'repomix';
</file>
</files>
<git_logs>
<git_log_commit>
<date>2026-04-10 00:47:19 +0900</date>
<message>feat(cli): Add --include-logs option</message>
<files>
  src/index.ts
</files>
</git_log_commit>
</git_logs>
```

Repomix 把 XML 定为默认格式，是因为 Anthropic、Google、OpenAI 都在官方提示词指南里推荐 XML 标签组织结构——Claude 等模型在训练中见过大量这类格式，解析更稳。

### Markdown 格式

````markdown
# File Summary
（元数据与 AI 指令）

# Directory Structure
```
src/
  index.ts
  utils/
    helper.ts
```

# Files
## File: src/index.ts
```typescript
import { repomix } from 'repomix';
```

# Git Logs
## 提交：2026-04-10 00:47:19 +0900
**消息：** feat(cli): Add --include-logs option
**文件：**
- src/index.ts
````

### JSON 格式

```json
{
  "fileSummary": {
    "generationHeader": "此文件是使用 Repomix 将整个代码库合并到单个文档中的表示形式。",
    "fileCount": 42,
    "totalTokens": 52340
  },
  "directoryStructure": "src/\n  index.ts\n  utils/\n    helper.ts",
  "files": {
    "src/index.ts": "import { repomix } from 'repomix';"
  }
}
```

JSON 使用 camelCase 键名，适合程序解析——比如用 `jq` 直接取出某个文件的内容，再做进一步处理。

### 纯文本格式

`plain` 去掉全部标记，只保留文件路径和内容，是四种格式里最省 Token 的一种。

---

## 实践建议

**与 Claude 配合。** 把 Repomix 输出发给 Claude 时，用这个提示模板开头：

```
This file contains all the files in the repository combined into one.
I want to refactor the code, so please review it first.
```

把仓库内容放在提示顶部（指令之前），Claude 能先读完整上下文再开始干活，响应质量比对着片段好。

**仓库太大。** Token 数接近 LLM 上下文上限时：开 `--compress` 让 Tree-sitter 砍掉实现细节；用 `--include` 只打包关心的目录；用 `--ignore` 排除测试、文档等非核心内容；调 `--include-logs-count` 控制历史条数。

**安全检查。** 保持 `enableSecurityCheck: true`（默认已开启）；输出发给 AI 之前扫一眼告警；测试文件里如果放了假凭证，确保内容无害再用 `--no-security-check`。

---

## 常见问题

**打包后没有生成文件？** 确认没用 `--stdout`——该模式把内容写到标准输出，不落盘；`--quiet` 只是静默日志，文件照常生成。也可以先 `cd` 到一个有写权限的目录再跑。

**某些文件没被打包进去？** 按三层忽略依次排查：`.gitignore`、`.repomixignore` / `.ignore`、内置默认模式（`node_modules/`、`.git/`、`coverage/`、`dist/`）。确认文件不在忽略列表里；被误伤时可用 `--no-gitignore` 或 `--no-default-patterns` 临时绕过。默认不包含二进制文件内容，但路径会出现在目录结构中。

**打包结果太大，Token 接近上限？** 按顺序试三招：`--compress` 让 Tree-sitter 砍掉实现细节，官方称平均能省约 70% 的 Token；`--include` 只打包关心的目录；`--remove-comments` 剔除注释。提交历史太长就调小 `--include-logs-count`。

**安全检查误报？** 安全检查只警告，不阻断打包。确认文件里的疑似密钥确实无害后，用 `--no-security-check` 关闭，或把该文件加进忽略列表。

**远程仓库打包失败？** 先确认网络连通；私有仓库需要在环境中提前配置好 Git 认证；GitHub 简写 `user/repo` 仅对公开仓库有效，私有仓库请用完整 URL 并配合认证。

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