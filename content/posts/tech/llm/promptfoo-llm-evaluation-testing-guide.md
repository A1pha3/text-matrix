---
title: "Promptfoo：LLM 评测与 Red Teaming 实战指南"
date: "2026-04-12T10:00:00+08:00"
slug: promptfoo-llm-evaluation-testing-guide
aliases:
  - /posts/tech/promptfoo-llm-evaluation-testing-guide/
categories: ["技术笔记"]
tags: ["Promptfoo", "LLM评测", "Red Teaming", "Prompt工程", "CI/CD", "RAG"]
description: "Promptfoo 是开源 LLM 评测与 Red Teaming 工具，支持 60+ 模型统一评测、断言系统、Red Teaming 对抗测试、CI/CD 集成。本文基于官方文档，覆盖真实配置格式、断言类型、扩展机制与实战场景。"
---

> **目标读者**：AI 应用开发者、Prompt 工程师、测试工程师
> **核心问题**：如何用测试驱动开发替代"调 Prompt 靠猜"？
> **难度**：⭐⭐⭐（中级）
> **事实边界**：本文所有配置示例和 API 均来自 promptfoo 官方文档和 GitHub 仓库，未经验证的功能不做展开。

## 一、项目概述

### 1.1 什么是 Promptfoo

Promptfoo（[promptfoo/promptfoo](https://github.com/promptfoo/promptfoo)）是一个开源的 LLM 评测和 Red Teaming 工具。它帮助开发者通过测试套件评估 Prompts、Models 和 RAG 系统，并扫描 LLM 应用的安全漏洞。

**定位**：从"调 Prompt 靠猜"到"用测试驱动开发"。

2026 年 Promptfoo 已加入 OpenAI，但项目仍保持 MIT 开源协议。

### 1.2 关键特性

| 特性 | 说明 |
|------|------|
| **本地运行** | LLM 评测 100% 在本地执行，Prompt 不会离开你的机器 |
| **60+ 模型** | OpenAI、Anthropic、Google、Azure、AWS Bedrock、Ollama 等 |
| **YAML 配置** | 声明式配置，高度可定制 |
| **Red Teaming** | 自动化对抗测试，扫描安全漏洞 |
| **Web UI** | 可视化查看评测结果 |
| **CI/CD** | 集成 GitHub Actions 等持续集成流程 |
| **缓存** | 自动缓存结果，加速迭代 |
| **扩展** | 支持 JavaScript/Python 自定义 Provider 和断言 |

### 1.3 解决的问题

| 传统痛点 | Promptfoo 方案 |
|----------|---------------|
| Prompt 调优靠猜 | 测试驱动开发，量化评估 |
| 模型对比困难 | 统一配置，多模型并排对比 |
| RAG 效果难测 | 内置 RAG 评测指标（事实性、相关性、忠实度） |
| 上线后才发现问题 | CI/CD 集成，自动化测试 |
| 安全漏洞难发现 | Red Teaming 自动化扫描 |

---

## 二、快速开始

### 2.1 安装

```bash
# 使用 npx（无需安装）
npx promptfoo@latest eval

# 或全局安装
npm install -g promptfoo

# 或使用 Homebrew
brew install promptfoo

# 或使用 pip
pip install promptfoo
```

### 2.2 运行示例

```bash
# 初始化示例项目
npx promptfoo@latest init --example getting-started

# 进入目录，运行评测
cd getting-started
npx promptfoo@latest eval

# 查看结果
npx promptfoo@latest view
```

### 2.3 交互式配置

```bash
# 通过 CLI 向导创建配置
npx promptfoo@latest init

# 或通过 Web UI 配置
npx promptfoo@latest eval setup
```

### 2.4 环境变量

大多数 Provider 需要 API Key：

```bash
export OPENAI_API_KEY=sk-abc123
export ANTHROPIC_API_KEY=sk-ant-xxx
```

---

## 三、配置详解

Promptfoo 使用 `promptfooconfig.yaml` 作为核心配置文件。

### 3.1 最小配置

```yaml
# promptfooconfig.yaml
prompts:
  - 'Convert the following English text to {{language}}: {{input}}'

providers:
  - openai:gpt-4o

tests:
  - vars:
      language: French
      input: Hello world
    assert:
      - type: contains
        value: 'Bonjour le monde'
```

### 3.2 配置结构

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `prompts` | string[] | 是 | Prompt 列表，支持 `{{variable}}` 变量 |
| `providers` | string[] | 是 | LLM Provider 列表 |
| `tests` | Test[] | 是 | 测试用例列表 |
| `defaultTest` | Test | 否 | 默认测试配置（如全局断言） |
| `outputPath` | string | 否 | 输出文件路径 |
| `evaluateOptions` | object | 否 | 评测选项（并发数、超时等） |
| `extensions` | string[] | 否 | 扩展钩子文件列表 |
| `env` | object | 否 | 环境变量覆盖 |

### 3.3 Provider 格式

Provider 使用简洁的字符串标识符：

```yaml
providers:
  # OpenAI
  - openai:gpt-4o
  - openai:gpt-4o-mini

  # Anthropic
  - anthropic:messages:claude-sonnet-4-20250514

  # Google
  - google:gemini-2.5-pro

  # 本地模型
  - ollama:chat:llama3

  # 自定义 Provider（JS/Python 文件）
  - file://path/to/custom_provider.py
```

也支持带配置的对象格式：

```yaml
providers:
  - id: openai:gpt-4o
    config:
      temperature: 0.7
      max_tokens: 1024
```

### 3.4 Prompt 格式

Prompt 支持多种写法：

```yaml
prompts:
  # 内联字符串
  - '翻译以下文本为{{language}}：{{input}}'

  # 外部文件
  - file://prompts/translation.txt

  # 带标签的对象
  - id: file://prompts/v1.txt
    label: 简洁版
  - id: file://prompts/v2.txt
    label: 详细版
```

---

## 四、评测场景

### 4.1 Prompt 对比评测

对比不同 Prompt 变体的效果：

```yaml
prompts:
  - '翻译：{{input}}'
  - '你是一个专业翻译。请将以下{{language}}文本翻译成{{target_language}}，保持原意并符合目标语言习惯：{{input}}'

providers:
  - openai:gpt-4o

tests:
  - vars:
      input: "The quick brown fox"
      language: English
      target_language: 中文
    assert:
      - type: contains
        value: 快速
```

运行后，Web UI 会并排展示两个 Prompt 在同一组测试上的输出，方便对比。

### 4.2 模型对比评测

对比不同模型的表现：

```yaml
prompts:
  - '解释量子计算的基本原理。'

providers:
  - openai:gpt-4o
  - anthropic:messages:claude-sonnet-4-20250514
  - google:gemini-2.5-pro

tests:
  - assert:
      - type: contains-any
        value: ["量子", "叠加", "纠缠"]
```

也可以通过命令行临时替换 Provider：

```bash
npx promptfoo@latest eval -r google:gemini-2.5-pro google:gemini-2.5-flash
```

### 4.3 RAG 评测

评估检索增强生成系统的质量：

```yaml
providers:
  - id: 'http://localhost:3000/api/rag'
    config:
      transformResponse: 'json.data'

prompts:
  - '根据以下上下文回答问题。\n\n上下文：{{context}}\n\n问题：{{question}}'

tests:
  - vars:
      question: 什么是向量数据库？
      context: 向量数据库是一种专门存储和检索向量表示的数据库系统...
    assert:
      - type: contains
        value: 向量
      - type: context-faithfulness
        contextTransform: 'output.sources.map(s => s.content).join("\n")'
        threshold: 0.9
```

RAG 评测的关键指标包括：事实性（factuality）、答案相关性（answer relevance）、上下文召回（context recall）、上下文相关性（context relevance）、上下文忠实度（context faithfulness）。

### 4.4 Agent 评测

评测 Agent 工作流：

```bash
npx promptfoo@latest init --example openai-agents-basic
```

Agent 评测关注任务完成度和轨迹正确性（trajectory）。

---

## 五、断言系统

断言是 Promptfoo 的核心机制，用于自动检查 LLM 输出是否满足预期。

### 5.1 常用断言类型

| 类型 | 说明 | 示例 |
|------|------|------|
| `contains` | 包含指定文本（区分大小写） | `value: "风险"` |
| `icontains` | 包含指定文本（不区分大小写） | `value: "risk"` |
| `contains-any` | 包含任一关键词 | `value: ["风险", "问题"]` |
| `contains-all` | 包含所有关键词 | `value: ["优点", "缺点"]` |
| `not-contains` | 不包含文本 | `value: "错误"` |
| `regex` | 正则匹配 | `value: "^\\d+$"` |
| `equals` | 完全相等 | `value: "expected"` |
| `is-json` | 输出是合法 JSON | |
| `similar` | 语义相似度（需 Provider） | `value: "预期输出", threshold: 0.8` |
| `llm-rubric` | LLM 评分（需 Provider） | `value: "评分标准"` |
| `javascript` | 自定义 JS 逻辑 | `value: "output.length > 100"` |
| `python` | 自定义 Python 逻辑 | `value: "len(output) > 100"` |
| `cost` | 检查 API 调用成本 | `threshold: 0.01` |
| `perplexity` | 困惑度检查 | `threshold: 10` |
| `context-faithfulness` | 上下文忠实度 | `threshold: 0.9` |
| `context-relevance` | 上下文相关性 | `threshold: 0.8` |

### 5.2 断言配置示例

```yaml
tests:
  - vars:
      question: 什么是机器学习？
    assert:
      - type: contains
        value: 算法
      - type: not-contains
        value: 我不知道
      - type: similar
        value: 机器学习是人工智能的一个分支，通过数据训练模型
        threshold: 0.7
        provider: openai:gpt-4o-mini
      - type: javascript
        value: output.length >= 50 && output.length <= 500
```

### 5.3 自定义 JavaScript 断言

```yaml
tests:
  - vars:
      input: 请列出三种编程语言
    assert:
      - type: javascript
        value: |
          const languages = ['python', 'javascript', 'java', 'go', 'rust', 'c++', 'typescript'];
          const output_lower = output.toLowerCase();
          const count = languages.filter(l => output_lower.includes(l)).length;
          return { pass: count >= 3, score: count / 3 };
```

### 5.4 自定义 Python 断言

```yaml
tests:
  - vars:
      input: 计算斐波那契数列第10项
    assert:
      - type: python
        value: |
          import re
          numbers = re.findall(r'\d+', output)
          pass_test = '55' in numbers
          return {"pass": pass_test, "score": 1.0 if pass_test else 0.0}
```

### 5.5 默认断言与阈值

```yaml
defaultTest:
  assert:
    - type: not-contains
      value: "Error"
    - type: not-contains
      value: "我无法"

tests:
  - vars:
      question: 你好
    assert:
      - type: contains
        value: 你好
    threshold: 0.5
```

`threshold` 设置测试的最低通过分数，低于此值则测试失败。

---

## 六、Red Teaming

Promptfoo 内置 Red Teaming 功能，用于扫描 LLM 应用的安全漏洞。

### 6.1 快速开始

```bash
# 初始化 Red Team 配置
npx promptfoo@latest redteam

# 运行 Red Team 扫描
npx promptfoo@latest redteam eval
```

Red Teaming 会自动生成各种对抗性输入，测试你的 LLM 应用是否存在安全漏洞。

### 6.2 扫描范围

Red Teaming 覆盖的安全类别包括：

| 类别 | 说明 |
|------|------|
| **Prompt 注入** | 尝试覆盖系统指令 |
| **越狱（Jailbreak）** | 尝试绕过安全限制 |
| **数据泄露** | 尝试提取训练数据或系统提示 |
| **PII 泄露** | 检测是否泄露个人信息 |
| **有害内容** | 测试是否生成有害输出 |

### 6.3 Red Team 配置

Red Team 通过交互式向导生成配置，也可手动编辑 `promptfooconfig.yaml` 中的 `redteam` 部分。配置完成后，运行 `npx promptfoo@latest redteam eval` 即可启动扫描。

扫描结果会在 Web UI 中以安全报告形式展示，标注每个漏洞的严重程度。

---

## 七、Web UI

### 7.1 启动与使用

```bash
# 查看最近一次评测结果
npx promptfoo@latest view

# 通过 Web UI 配置评测
npx promptfoo@latest eval setup
```

### 7.2 核心功能

| 功能 | 说明 |
|------|------|
| **结果概览** | 测试通过率、评分分布 |
| **对比视图** | 多模型/多 Prompt 并排对比 |
| **详情查看** | 完整输入/输出/断言结果 |
| **导出** | CSV、JSON、YAML、HTML 格式 |

---

## 八、扩展机制

### 8.1 自定义 Provider

通过 JavaScript 或 Python 文件实现自定义 Provider：

```javascript
// custom_provider.js
async function callApi(prompt, context) {
  const response = await fetch('https://your-api.com/generate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ prompt }),
  });
  const data = await response.json();
  return {
    output: data.text,
    tokenUsage: { total: data.tokens },
  };
}

module.exports = { callApi };
```

在配置中引用：

```yaml
providers:
  - file://custom_provider.js
```

### 8.2 扩展钩子

Promptfoo 支持在评测生命周期的特定节点执行自定义代码：

| 钩子 | 触发时机 | 用途 |
|------|----------|------|
| `beforeAll` | 评测开始前 | 初始化、添加测试用例 |
| `afterAll` | 评测结束后 | 汇总报告、清理 |
| `beforeEach` | 每个测试前 | 修改变量、创建会话 |
| `afterEach` | 每个测试后 | 日志记录、清理会话 |

```javascript
// extension.js
async function extensionHook(hookName, context) {
  if (hookName === 'beforeAll') {
    console.log('评测开始');
  } else if (hookName === 'afterEach') {
    console.log(`测试完成: ${context.test.description}, 通过: ${context.result.success}`);
  }
}

module.exports = extensionHook;
```

配置中引用：

```yaml
extensions:
  - file://extension.js:extensionHook
```

### 8.3 输出转换

对于返回非标准格式的 API，可以通过 `transformResponse` 转换：

```yaml
providers:
  - id: 'http://localhost:3000/api'
    config:
      transformResponse: 'json.data.answer'
```

测试级别也可以转换输出：

```yaml
tests:
  - vars:
      query: 退款政策是什么？
    options:
      transform: 'output.answer'
    assert:
      - type: contains
        value: 30天
```

---

## 九、CI/CD 集成

### 9.1 GitHub Actions

```yaml
# .github/workflows/llm-eval.yml
name: LLM Evaluation

on:
  push:
    paths:
      - 'prompts/**'
      - 'promptfooconfig.yaml'
  pull_request:

jobs:
  evaluate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'

      - name: Install Promptfoo
        run: npm install -g promptfoo

      - name: Run Evaluation
        run: promptfoo eval --config promptfooconfig.yaml --output results.json
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}

      - name: Upload Results
        uses: actions/upload-artifact@v4
        with:
          name: promptfoo-results
          path: results.json
```

### 9.2 命令行选项

```bash
# 运行评测
promptfoo eval

# 指定配置文件
promptfoo eval -c path/to/config.yaml

# 覆盖 Provider
promptfoo eval -r openai:gpt-4o openai:gpt-4o-mini

# 过滤测试
promptfoo eval --filter-pattern "auth.*"

# 控制并发
promptfoo eval --max-concurrency 10

# 禁用缓存
promptfoo eval --no-cache

# 输出格式
promptfoo eval --output results.json
promptfoo eval --output results.csv
promptfoo eval --output results.html
```

---

## 十、适用场景与边界

### 10.1 适合的场景

| 场景 | 说明 |
|------|------|
| **Prompt 开发** | 对比多个 Prompt 变体，量化评估效果 |
| **模型选型** | 在真实任务上评测多个模型，数据驱动决策 |
| **RAG 优化** | 评测检索策略、块大小、向量搜索参数 |
| **安全加固** | Red Teaming 扫描 Prompt 注入、越狱等漏洞 |
| **回归测试** | CI/CD 集成，确保 Prompt 变更不引入退化 |

### 10.2 边界与注意事项

| 边界 | 说明 |
|------|------|
| **不是模型训练工具** | Promptfoo 评测和测试 LLM 输出，不训练模型 |
| **评测依赖断言质量** | 断言设计不合理会导致误判，需持续优化 |
| **语义类断言有成本** | `similar`、`llm-rubric` 等需要额外 LLM 调用 |
| **本地运行为主** | 评测在本地执行，大规模并发需注意 API 限流 |
| **Red Teaming 不是渗透测试** | 它是自动化扫描，不能替代专业安全审计 |

---

## 十一、常见问题

**Q: 支持本地模型吗？**

支持。配置 Ollama、LM Studio 或 LocalAI：

```yaml
providers:
  - ollama:chat:llama3
```

**Q: 如何减少 API 成本？**

1. 使用缓存（默认开启）：`promptfoo eval` 自动缓存已运行的测试
2. 使用 `--filter-pattern` 只运行相关测试
3. 语义类断言使用更小的模型：`provider: openai:gpt-4o-mini`
4. 设置 `--max-concurrency` 控制并发

**Q: 如何在测试间共享变量？**

使用 `defaultTest` 设置全局断言和变量：

```yaml
defaultTest:
  assert:
    - type: not-contains
      value: "Error"

tests:
  - vars:
      input: 你好
```

**Q: 支持多轮对话测试吗？**

支持。通过 `options.storeOutputAs` 将前一轮输出存储为变量，供后续测试使用。

---

## 相关链接

- GitHub：[promptfoo/promptfoo](https://github.com/promptfoo/promptfoo)
- 官方文档：[promptfoo.dev/docs](https://promptfoo.dev/docs)
- Red Teaming 指南：[promptfoo.dev/docs/red-teaming](https://promptfoo.dev/docs/red-teaming)
- 支持的 Provider：[promptfoo.dev/docs/providers](https://promptfoo.dev/docs/providers)
- 断言类型：[promptfoo.dev/docs/configuration/expected-outputs](https://promptfoo.dev/docs/configuration/expected-outputs)
