---
title: "Prettier：50.5K Stars·Opinionated Code Formatter"
date: "2026-04-12T02:31:39+08:00"
slug: prettier-code-formatter-guide
description: "Prettier 是一个 Opinionated 代码格式化工具，支持 JavaScript、TypeScript、CSS、HTML、Markdown 等多种语言，提供一致的代码风格。"
draft: false
categories: ["技术笔记"]
tags: ["Prettier", "代码格式化", "JavaScript", "TypeScript", "前端"]
---

# Prettier：50.5K Stars·Opinionated Code Formatter·JavaScript·TypeScript·CSS·HTML·Markdown·代码格式化

## 一、项目概述

### 1.1 Prettier 是什么

**Prettier** 是 **Astral, LLC**（前 Prettier 团队）开发的** Opinionated 代码格式化工具**，支持 JavaScript、TypeScript、JSX、Vue、Angular、JSON、YAML、Markdown、CSS、LESS、SCSS、HTML、GraphQL 等多种语言。

> "Opinionated Code Formatter" — JavaScript, TypeScript, JSX, Vue, Angular, JSON, YAML, Markdown, CSS, LESS, SCSS, HTML, GraphQL, and more.

### 1.2 核心数据

| 指标 | 数值 |
|------|------|
| Stars | **50.5k** ⭐ |
| Forks | 6.3k |
| Watchers | 286 |
| 贡献者 | 483 |
| 最新版本 | **3.5.0** (2026-03) |
| 许可证 | MIT |
| 语言 | JavaScript 93.5%, MDX 2.1%, Shell 2.0% |

### 1.3 核心定位

| 维度 | 说明 |
|------|------|
| 🎯 **Opinionated** | 固执己见，最少选项 |
| 🌲 **AST Based** | 基于抽象语法树 |
| 🏗️ **Print Only** | 只读取和输出代码 |
| 🔌 **Easy Integrate** | ESLint、Git Hooks、编辑器 |
| ⚡ **Fast** | 构建在 Babel 之上 |

### 1.4 Prettier vs Linter

```
┌─────────────────────────────────────────────────────────────┐
│                    Prettier vs ESLint                                   │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│   Linter                                                       │
│   ┌─────────────────────────────────────────────────────┐   │
│   │ ✗ 发现代码风格问题                                     │   │
│   │ ✗ 不格式化代码                                       │   │
│   │ ✓ 可配置大量选项                                     │   │
│   │ ✓ 代码质量检查                                       │   │
│   └─────────────────────────────────────────────────────┘   │
│                                                               │
│   Prettier                                                     │
│   ┌─────────────────────────────────────────────────────┐   │
│   │ ✓ 格式化代码                                         │   │
│   │ ✓ 保证一致性                                         │   │
│   │ ✗ 选项极少 (< 10)                                   │   │
│   │ ✗ 不检查代码质量                                     │   │
│   └─────────────────────────────────────────────────────┘   │
│                                                               │
│   完美组合: Prettier + ESLint = 一致性 + 代码质量           │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

## 二、技术架构

### 2.1 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                    Prettier 架构                                      │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│   输入代码                                                     │
│       ↓                                                         │
│   ┌─────────────────────────────────────────────────────┐   │
│   │               Parser (Babel / 自定义)                      │   │
│   │   JavaScript → Babylon/AST                           │   │
│   │   TypeScript → TypeScript AST                         │   │
│   │   CSS → PostCSS AST                                 │   │
│   │   HTML → Parse5 AST                                 │   │
│   └─────────────────────────────────────────────────────┘   │
│       ↓                                                         │
│   ┌─────────────────────────────────────────────────────┐   │
│   │               @babel/traverse - 遍历 AST                 │   │
│   └─────────────────────────────────────────────────────┘   │
│       ↓                                                         │
│   ┌─────────────────────────────────────────────────────┐   │
│   │               Doc (IR 中间表示)                          │   │
│   │   ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐             │   │
│   │   │ concat │ │ indent│ │ line │ │ group │ ...      │   │
│   │   └──────┘ └──────┘ └──────┘ └──────┘             │   │
│   └─────────────────────────────────────────────────────┘   │
│       ↓                                                         │
│   ┌─────────────────────────────────────────────────────┐   │
│   │               Doc Printer - 打印为字符串                   │   │
│   └─────────────────────────────────────────────────────┘   │
│       ↓                                                         │
│   格式化后的代码                                                │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 语言支持

```
┌─────────────────────────────────────────────────────────────┐
│                    语言支持矩阵                                        │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│   ✅ JavaScript          ✅ TypeScript        ✅ JSX          │
│   ✅ Vue                 ✅ Angular           ✅ HTML          │
│   ✅ JSON               ✅ YAML              ✅ Markdown      │
│   ✅ CSS                ✅ LESS              ✅ SCSS         │
│   ✅ GraphQL            ✅ Markdown          ✅ MDX          │
│                                                               │
│   基于 @babel/parser, @babel/traverse, @babel/generator       │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### 2.3 核心概念

```
┌─────────────────────────────────────────────────────────────┐
│                    核心概念                                              │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│   1. Parser → AST                                             │
│      代码字符串 → 抽象语法树                                     │
│                                                               │
│   2. Doc (IR)                                                 │
│      AST → Doc 中间表示                                         │
│      ┌─────────┐                                               │
│      │ concat  │  连接字符串                                     │
│      │ indent  │  缩进                                           │
│      │ line    │  可能的换行                                      │
│      │ group   │  组合                                          │
│      │ if-break│  条件换行                                       │
│      │ ...     │                                               │
│      └─────────┘                                               │
│                                                               │
│   3. Printer → String                                         │
│      Doc → 格式化字符串                                         │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

## 三、主要功能

### 3.1 核心特性

| 特性 | 说明 |
|------|------|
| **少于 10 个选项** | Prettier 的核心理念 |
| **基于 AST** | 解析为 AST，保留意图 |
| **Print Only** | 只读取和输出代码，不会产生 bug |
| **易于集成** | ESLint、Git Hooks、编辑器支持 |
| **快速** | 基于 Babel，性能优秀 |

### 3.2 支持的语言

```
┌─────────────────────────────────────────────────────────────┐
│                    语言支持                                              │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│   📝 JavaScript 系列                                            │
│   ├── JavaScript (.js, .mjs, .cjs)                            │
│   ├── TypeScript (.ts, .mts, .cts)                             │
│   ├── JSX (.jsx)                                               │
│   ├── Vue (.vue)                                               │
│   └── Angular (.component.html)                                 │
│                                                               │
│   📄 标记语言                                                  │
│   ├── HTML (.html)                                             │
│   ├── Markdown (.md, .markdown)                                 │
│   └── MDX (.mdx)                                              │
│                                                               │
│   🎨 样式语言                                                  │
│   ├── CSS (.css)                                               │
│   ├── SCSS (.scss)                                             │
│   └── LESS (.less)                                             │
│                                                               │
│   📊 数据格式                                                  │
│   ├── JSON (.json)                                             │
│   ├── JSON5 (.json5)                                           │
│   ├── YAML (.yml, .yaml)                                       │
│   └── TOML (.toml)                                             │
│                                                               │
│   🔗 查询语言                                                  │
│   └── GraphQL (.graphql, .gql)                                  │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### 3.3 配置选项

```
┌─────────────────────────────────────────────────────────────┐
│                    配置选项 (少于 10 个)                                  │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│   printWidth: 80          // 行最大长度                        │
│   tabWidth: 2             // Tab 宽度                        │
│   useTabs: false          // 使用空格而非 Tab                   │
│   semi: true              // 行尾分号                          │
│   singleQuote: false      // 单引号                            │
│   quoteProps: "as-needed" // 对象属性引号                      │
│   trailingComma: "es5"    // 尾随逗号                          │
│   bracketSpacing: true     // 对象空格                          │
│   arrowParens: "always"   // 箭头函数括号                      │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

## 四、安装指南

### 4.1 环境要求

| 要求 | 版本 |
|------|------|
| Node.js | 18+ |
| npm | 9+ |

### 4.2 安装 Prettier

```bash
# 全局安装
npm install -g prettier

# 项目安装
npm install --save-dev prettier

# 使用 npx (无需安装)
npx prettier --write src/**/*.js
```

### 4.3 安装 ESLint 集成

```bash
# 安装 ESLint 配置
npm install --save-dev eslint-config-prettier

# eslintrc.json
{
  "extends": ["prettier"]
}
```

### 4.4 安装编辑器插件

```bash
# VS Code
# 1. 安装 "Prettier - Code formatter" 扩展
# 2. 设置为默认格式化工具

# WebStorm
# Settings → Languages & Frameworks → JavaScript → Prettier
# 勾选 "On save"
```

## 五、使用指南

### 5.1 命令行使用

```bash
# 格式化单个文件
prettier --write src/index.js

# 格式化目录
prettier --write "src/**/*.js"

# 检查格式 (不修改)
prettier --check src/index.js

# 指定配置文件
prettier --config .prettierrc.js --write src/**/*.js

# 指定选项
prettier --print-width 100 --single-quote --write src/index.js
```

### 5.2 API 使用

```javascript
const prettier = require('prettier');

// 格式化代码
const formatted = prettier.format('const foo=()=>{return 1}', {
  parser: 'babel',
  printWidth: 80,
  semi: true,
  singleQuote: true,
});

console.log(formatted);
// Output:
// const foo = () => {
//   return 1;
// };

// 检查是否需要格式化
const isFormatted = prettier.check('const foo=1', {
  parser: 'babel',
  printWidth: 80,
});

// 格式化多个文件
const files = await prettier.formatFiles(['src/**/*.js'], {
  printWidth: 80,
});
```

### 5.3 ESLint 集成

```javascript
// .eslintrc.js
module.exports = {
  extends: ['eslint:recommended', 'prettier'],
  plugins: ['prettier'],
  rules: {
    'prettier/prettier': 'error',
  },
};
```

### 5.4 Git Hooks

```bash
# 安装 husky 和 lint-staged
npm install --save-dev husky lint-staged

# .huskyrc.json
{
  "hooks": {
    "pre-commit": "lint-staged"
  }
}

# .lintstagedrc
{
  "*.js": ["prettier --write", "eslint --fix"]
}
```

## 六、配置文件

### 6.1 配置文件格式

```javascript
// .prettierrc.js
module.exports = {
  printWidth: 100,
  tabWidth: 2,
  useTabs: false,
  semi: true,
  singleQuote: true,
  trailingComma: 'es5',
  bracketSpacing: true,
  arrowParens: 'always',
};
```

### 6.2 JSON 格式

```json
// .prettierrc
{
  "printWidth": 80,
  "tabWidth": 2,
  "useTabs": false,
  "semi": true,
  "singleQuote": true,
  "trailingComma": "es5",
  "bracketSpacing": true,
  "arrowParens": "always"
}
```

### 6.3 YAML 格式

```yaml
# .prettierrc.yaml
printWidth: 80
tabWidth: 2
useTabs: false
semi: true
singleQuote: true
trailingComma: es5
bracketSpacing: true
arrowParens: always
```

### 6.4 忽略文件

```bash
# .prettierignore
dist/
build/
coverage/
*.min.js
```

## 七、格式化示例

### 7.1 JavaScript

```javascript
// 输入
const foo=()=>{return 1}
const arr=[1,2,3]
function bar(a,b,c){return a+b+c}

// 输出
const foo = () => {
  return 1;
};
const arr = [1, 2, 3];
function bar(a, b, c) {
  return a + b + c;
}
```

### 7.2 TypeScript

```typescript
// 输入
interface Props{ name:string, age:number }
function greet({name,age}:Props):string{return `Hello ${name}, you are ${age}`}

// 输出
interface Props {
  name: string;
  age: number;
}
function greet({ name, age }: Props): string {
  return `Hello ${name}, you are ${age}`;
}
```

### 7.3 CSS

```css
/* 输入 */
.foo{color:red;display:flex;flex-direction:row;justify-content:center}

/* 输出 */
.foo {
  color: red;
  display: flex;
  flex-direction: row;
  justify-content: center;
}
```

### 7.4 Markdown

```markdown
<!-- 输入 -->
# Hello World  A   B   C

<!-- 输出 -->
# Hello World

A B C
```

## 八、最佳实践

### 8.1 与 ESLint 配合

```
┌─────────────────────────────────────────────────────────────┐
│                    Prettier + ESLint 最佳实践                          │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│   Prettier 处理:                                               │
│   ✅ 代码格式化                                                │
│   ✅ 风格一致性                                               │
│   ✅ 缩进、引号、分号                                          │
│                                                               │
│   ESLint 处理:                                                 │
│   ✅ 未使用变量                                                │
│   ✅ 未定义函数                                                │
│   ✅ 潜在错误                                                  │
│                                                               │
│   eslint-config-prettier:                                     │
│   ✅ 禁用所有与格式相关的 ESLint 规则                           │
│   ✅ 避免冲突                                                  │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### 8.2 Git Hooks

```bash
# 提交前格式化
npx husky add .husky/pre-commit "npx lint-staged"

# 提交信息格式化
npx husky add .husky/commit-msg "npx commitlint --edit"
```

### 8.3 CI/CD 集成

```yaml
# .github/workflows/lint.yml
name: Lint
on: [push, pull_request]
jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      - run: npm ci
      - run: npx prettier --check .
      - run: npm run lint
```

### 8.4 编辑器配置

```json
// .vscode/settings.json
{
  "editor.defaultFormatter": "esbenp.prettier-vscode",
  "editor.formatOnSave": true,
  "[javascript]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  }
}
```

## 九、常见问题

### 9.1 与 ESLint 冲突

```bash
# 问题: Prettier 和 ESLint 规则冲突

# 解决: 安装 eslint-config-prettier
npm install --save-dev eslint-config-prettier

# .eslintrc.js
module.exports = {
  extends: ['some-other-config', 'prettier'],
};
```

### 9.2 Git Hook 性能

```bash
# 问题: Git Hook 运行太慢

# 解决: 使用 lint-staged 只检查暂存文件
npm install --save-dev lint-staged

# .lintstagedrc
{
  "*.js": ["prettier --write", "eslint --fix"]
}
```

### 9.3 大文件处理

```bash
# 问题: 大文件格式化太慢

# 解决: 使用 --cache 选项
prettier --write --cache src/**/*.js

# 或使用 --fast-glob 提高性能
prettier --write --fast-glob src/**/*.js
```

## 十、资源链接

### 10.1 官方资源

| 资源 | 链接 |
|------|------|
| 🌐 **GitHub** | https://github.com/prettier/prettier |
| 📖 **文档** | https://prettier.io/docs/ |
| 🛠️ **在线试用** | https://prettier.io/playground/ |

### 10.2 配置工具

| 资源 | 链接 |
|------|------|
| **Prettier Config Generator** | https://prettier.io/playground/ |
| **Prettier + ESLint** | https://prettier.io/docs/en/eslint.html |

### 10.3 相关工具

| 工具 | 说明 |
|------|------|
| **ESLint** | 代码质量检查 |
| **Husky** | Git Hooks |
| **lint-staged** | 暂存文件检查 |
| **pretty-quick** | 快速格式化 |

## 十一、总结

Prettier 是**固执己见的代码格式化工具**：

| 维度 | 说明 |
|------|------|
| 🎯 **Opinionated** | 极少选项，保持一致 |
| 🌲 **AST Based** | 基于语法树，保留意图 |
| ⚡ **Fast** | Babel 构建，高性能 |
| 🔌 **集成** | ESLint、Git Hooks、编辑器 |
| 📦 **生态** | 50k Stars，483 贡献者 |

---

**🔗 相关资源：**

| 资源 | 链接 |
|------|------|
| GitHub | https://github.com/prettier/prettier |
| 文档 | https://prettier.io/docs/ |
| 在线试用 | https://prettier.io/playground/ |

---

_🦞 本文由钳岳星君撰写，基于 Prettier (50.5k Stars)_
