---
title: "Biome 2.x 全栈 Web 工具链：单二进制替代 Prettier + ESLint 的 Rust 实践"
date: "2026-06-18T21:03:00+08:00"
slug: "biomejs-biome-2-rust-web-toolchain-guide"
description: "biomejs/biome 是用 Rust 写的一体化 Web 工具链，格式化兼容 Prettier 97%、Linter 收录 500+ 规则、原生支持 JS/TS/JSX/JSON/CSS/GraphQL，本文拆解其架构、安装与 vs Prettier+ESLint 的取舍。"
draft: false
categories: ["技术笔记"]
tags: ["Biome", "Rust工具链", "Prettier", "ESLint", "代码格式化", "前端工程化", "Linter"]
---

> **快速信息卡**
> - **GitHub**: [biomejs/biome](https://github.com/biomejs/biome)
> - **Stars**: 25,187+
> - **Forks**: 1,047+
> - **License**: Apache-2.0
> - **语言**: Rust
> - **最后更新**: 2026-06-25

## 学习目标

读完这篇，你应该能回答下面几个问题：

1. Biome 把哪些活儿从 Prettier + ESLint 接了过来，哪些还没接
2. 单二进制 + Rust 在大仓库 CI 上具体省在哪里
3. 从一个跑着 Prettier + ESLint 的存量项目迁过来，按什么顺序最稳
4. 什么情况下不该上 Biome

## 全文地图

`biomejs/biome` 想做的事情可以一句话讲完：**用 Rust 重写 Prettier + ESLint 的核心能力，做成一个单二进制工具链**。和"在 Prettier / ESLint 上叠配置文件"的传统玩法不同，Biome 的目标是"开箱即用、零配置、跨语言统一"，并且把性能压到极限。截至 2026 年，Biome 在格式化层做到了 **97% Prettier 兼容**、Linter 收录 **500+ 规则**（来自 ESLint、typescript-eslint 等生态），原生支持 **JavaScript / TypeScript / JSX / JSON / CSS / GraphQL**。

## 你会读到什么

读完这篇，你应该能回答下面几个问题：

- Biome 把哪些活儿从 Prettier + ESLint 接了过来，哪些还没接
- 单二进制 + Rust 在大仓库 CI 上具体省在哪里
- 从一个跑着 Prettier + ESLint 的存量项目迁过来，按什么顺序最稳
- 什么情况下不该上 Biome

### 全文地图

```text
┌─────────────────────────────────────────────────────────┐
│  Biome 的三层能力                                        │
│  ├─ Formatter  ── 97% Prettier 兼容（JS/TS/JSX/JSON/CSS）│
│  ├─ Linter     ── 500+ 规则（来自 ESLint 生态）          │
│  └─ Editor     ── VS Code / Open VSX 即时反馈            │
├─────────────────────────────────────────────────────────┤
│  工程取舍                                                 │
│  ├─ 收益：单二进制、零配置、CI 秒级                       │
│  └─ 代价：3% Prettier 差异、插件 API 不完全等价 ESLint   │
├─────────────────────────────────────────────────────────┤
│  采用顺序                                                 │
│  新项目 → 直接上                                          │
│  存量项目 → Prettier 先迁 → ESLint 推荐集 → 清理配置     │
└─────────────────────────────────────────────────────────┘
```

### 目录

- [一、为什么需要 Biome](#一为什么需要-biome)
- [二、定位：三个核心能力](#二定位三个核心能力)
- [三、性能：为什么用 Rust](#三性能为什么用-rust)
- [四、安装与最小上手](#四安装与最小上手)
- [五、迁移路径：从 Prettier + ESLint 迁过来](#五迁移路径从-prettier--eslint-迁过来)
- [六、Biome 不适合的场景](#六biome-不适合的场景)
- [七、与 oxlint / Prettier 的关系](#七与-oxlint--prettier-的关系)
- [八、采用建议](#八采用建议)
- [九、常见问题排查](#九常见问题排查)
- [十、自测题](#十自测题)
- [十一、进阶路径](#十一进阶路径)
- [十二、参考与延伸](#十二参考与延伸)

## 一、为什么需要 Biome

一个典型前端项目的工具链现状：

```text
Prettier  ── 格式化 JS / TS / JSON / CSS
ESLint    ── 静态分析 JS / TS
typescript-eslint ── TS 专属规则
Stylelint ── CSS 专属
```

问题集中在四处：

- 工具数量多（4-5 个 npm 包），配置文件冗余
- 性能受 Node.js 单线程限制，大项目 CI 卡顿明显
- 规则冲突（Prettier 格式化 vs ESLint 风格规则要互相让位）
- 依赖膨胀（数百个传递依赖）

Biome 给的方案是**单二进制 + 单配置文件 + 一致行为**。

## 二、定位：三个核心能力

README 把 Biome 定位成三层能力：

### 1. 快速格式化

> **Biome is a fast formatter** for JavaScript, TypeScript, JSX, JSON, CSS and GraphQL that scores 97% compatibility with Prettier.

这是 Biome 最早的能力。97% 不是 100%——Biome 团队的态度很明确：剩下 3% 是 Prettier 历史设计里不合理的边角，强行兼容只会拖累维护节奏。

### 2. 高性能 Linter

> **Biome is a performant linter** for JS / TS / JSX / JSON / CSS / GraphQL that features more than 500 rules from ESLint, typescript-eslint, and other sources. It outputs detailed and contextualized diagnostics.

500+ 规则不是凭空造出来的——是从 ESLint 生态"复刻 + 重写"来的。这意味着从 ESLint 迁过来时大部分规则名、配置选项是兼容的。

### 3. 实时编辑器集成

> **Biome is designed from the start to be used interactively within an editor.** It can format and lint malformed code as you are writing it.

第一方支持 VS Code 和 Open VSX 上的扩展，编辑器内即时反馈。

## 三、性能：为什么用 Rust

Biome 全栈用 Rust 写，最大的收益是**冷启动 + 大仓库 lint 速度**。

对开发机：

- 单文件 lint：`< 10 ms`（来源：Biome 官网性能页）
- 中型 monorepo（数千文件）：比 ESLint 快 10-50 倍（来源：Biome benchmark 仓库）

对 CI：

- 从"分钟级"压到"秒级"，PR 反馈更快
- 不需要维护 Node 版本 / npm 依赖

代价：安装包是二进制（不是 npm script），需要操作系统匹配（README 标注 GitHub Releases 上有全平台构建）。但从工程总账看，单二进制反而比 npm 几百个依赖更可控。

> 上面两个数字测的是"单文件 lint 耗时"和"中型仓库全量 lint 耗时"，反映的是 Rust 解析 + 单线程调度相对 Node.js 的差距。它们不能推出"在你的项目里 CI 一定快 10 倍"——真实收益取决于文件数量、规则集大小和 CI 机器规格。

## 四、安装与最小上手

### 安装

```bash
npm install --save-dev --save-exact @biomejs/biome
```

`--save-exact` 是 README 显式强调的——Biome 团队希望团队里所有人锁同一版本，避免 CI 和本地差异。

### 最小配置（`biome.json`）

```json
{
  "formatter": {
    "enabled": true,
    "indentStyle": "space",
    "indentWidth": 2
  },
  "linter": {
    "enabled": true,
    "rules": {
      "recommended": true
    }
  }
}
```

### CLI 常用命令

```bash
# 格式化整个项目
npx @biomejs/biome format --write .

# Lint + 自动修复
npx @biomejs/biome lint --write .

# 检查（CI 用）
npx @biomejs/biome ci .
```

`biome ci` 是为 CI 专门设计的入口——格式化、Lint、import 排序一次性跑完，遇到问题直接非零退出。

### 最小可运行示例

在一个空目录里走一遍，验证安装是否正常：

```bash
mkdir biome-demo && cd biome-demo
npm init -y
npm install --save-dev --save-exact @biomejs/biome
cat > biome.json <<'EOF'
{
  "formatter": { "enabled": true, "indentStyle": "space", "indentWidth": 2 },
  "linter": { "enabled": true, "rules": { "recommended": true } }
}
EOF
cat > index.js <<'EOF'
const x=1
var y = 2;
console.log( x,y )
EOF
npx @biomejs/biome check --write .
cat index.js
```

`biome check --write` 会同时跑格式化和 Lint 修复。`index.js` 里的多余空格会被抹平、分号补齐；如果 `noVar` 规则在 recommended 集里开启，`var` 还会被自动改成 `let`。如果没看到任何变化，先检查 `biome.json` 是否在项目根目录、`npx` 是否走的是本地安装。

## 五、迁移路径：从 Prettier + ESLint 迁过来

Biome 团队提供了官方迁移工具 `biome migrate eslint` / `biome migrate prettier`，能读 `eslintrc` 和 `.prettierrc`，按规则名映射成 `biome.json` 的等价配置。

迁移步骤建议：

1. **保留 ESLint 一段时间**：Biome 不是 100% ESLint 替代，业务里一些高度定制的 ESLint 规则可能没有覆盖
2. **先迁 Prettier**：97% 兼容性 + 自动化迁移工具，风险最低
3. **再迁 ESLint 推荐集**：开 `rules.recommended = true`，看哪些规则在工程里"误报"
4. **最后清理配置文件**：删掉 `.eslintrc`、`.prettierrc`，统一到 `biome.json`

> 不要一上来把 `.eslintrc` 全删——Biome 没覆盖的规则会沉默失效，比 ESLint 报错更危险。

## 六、Biome 不适合的场景

边界要写清楚：

- **需要 100% Prettier 兼容**：现存项目对比 PR 时，3% 差异会肉眼可见
- **需要 ESLint 高度自定义插件**：Biome 的插件体系还在演进（plugin API 尚未完全等价 ESLint）
- **多语言 linter 需求（如 Python、Go）**：Biome 只覆盖 Web 栈
- **团队对 npm 生态高度绑定**：二进制发布 + npm 包装并存，可能和团队既有 release 流程冲突

## 七、与 oxlint / Prettier 的关系

近两年出现了几个竞争者，最常被对比的是：

| 工具 | 定位 |
|---|---|
| **Biome** | 一体化（formatter + linter），覆盖多语言，规则丰富 |
| **oxlint** | 纯 Linter（Rust 写），覆盖 ESLint 规则集，性能极致 |
| **Prettier** | 格式化事实标准（Node.js） |
| **ESLint** | Linter 事实标准（Node.js），插件生态最全 |

按场景挑：

- **新项目**：直接上 Biome，一个工具搞定
- **已有 ESLint + 想提速**：先上 oxlint 平替 Lint，保留 Prettier
- **存量 Prettier + ESLint + 不愿动**：保持现状，Biome 收益主要在新项目

## 八、采用建议

### 适合

- 新建项目（特别是 monorepo）
- 大型项目 CI 慢、想压时间
- 团队受够"配置文件地狱"
- 跨 JS / TS / JSON / CSS 多种文件类型，需要统一格式化风格

### 不适合

- 高度依赖 ESLint 插件生态
- 必须 100% Prettier 兼容（CI diff 卡严格规则）
- 团队完全没 Rust 工具链运维经验（虽然安装简单，但 debug 二进制时要懂）

### 入门三步

1. **新项目直接装**：从第一天就用 Biome
2. **旧项目先并行跑**：保留 ESLint 一段时间，CI 同时跑两套，对比结果
3. **再切流量**：确认 Biome 误报率低于阈值后，把 ESLint 退到次要位置

## 九、常见问题排查

### Q1：`biome ci` 在本地能过，CI 上报错

最常见原因是 CI 跑的 `biome.json` 和本地不一致。先在 CI 里加一步 `npx @biomejs/biome --version` 和 `git rev-parse HEAD`，确认版本和代码分支一致；再检查 `biome.json` 是否被 `.gitignore` 误伤。

### Q2：迁移后部分文件没被格式化

Biome 默认只处理它认识的语言。检查 `formatter.include` 和 `files.include` 是否覆盖到目标文件；CSS、GraphQL 需要在 `formatter` 里显式开启对应语言。

### Q3：Linter 规则和原 ESLint 行为不一致

`biome migrate eslint` 是按规则名映射，不是按行为映射。少数规则在 Biome 里的默认严重级别、修复策略和 ESLint 不同。迁移后跑一遍 `npx @biomejs/biome lint .`，把 diff 和原 ESLint 输出对比，逐条调整 `rules` 里的 `severity`。

### Q4：二进制下载失败 / 平台不匹配

`@biomejs/biome` 的 npm 包会按 `os` / `cpu` 拉对应平台二进制。CI 镜像如果是 Alpine（musl），需要确认 `@biomejs/biome-linux-x64-musl` 是否被装上；npm v7+ 的 `optionalDependencies` 偶尔会被 `--no-optional` 关掉。

### Q5：VS Code 扩展不生效

确认扩展用的是项目本地的 Biome 而不是全局版本。在 `.vscode/settings.json` 里指定：

```json
{
  "biome.lsp.bin.path": "node_modules/@biomejs/biome/bin/biome"
}
```

## 十、自测题

下面 5 题用来检验是否读进去了。答案在题后。

1. Biome 格式化的 Prettier 兼容率是多少？为什么不是 100%？
2. `biome ci` 和 `biome check` 的差别在哪？为什么 CI 用前者？
3. 从 Prettier + ESLint 迁过来，为什么建议先迁 Prettier 而不是 ESLint？
4. 一个用 ESLint 自定义插件做业务规则校验的项目，能不能直接换 Biome？为什么？
5. Biome 用 Rust 写，但 `npm install @biomejs/biome` 也能装上，这是怎么做到的？

### 参考答案

1. **97%**。剩下 3% 是 Prettier 历史设计里不合理的边角，Biome 团队选择不强行兼容，避免拖累维护节奏。
2. `biome check` 跑格式化、Lint、import 排序，可以带 `--write` 自动修复；`biome ci` 是专为 CI 设计的入口，不带 `--write`，遇到问题直接非零退出。CI 用 `ci` 是因为它语义明确、退出码可控，不会因为自动修复而掩盖问题。
3. Prettier 兼容率 97% + 官方迁移工具，风险最低；ESLint 规则集大、自定义多，迁移后误报需要逐条调，风险更高。
4. 不建议直接换。Biome 的插件 API 还没完全等价 ESLint，业务自定义规则可能没有对应实现。建议先并行跑，确认 Biome 覆盖了所有业务规则后再切。
5. `@biomejs/biome` 的 npm 包本身是 JS 包装层，真正的 Rust 二进制通过 `optionalDependencies` 按平台分发（如 `@biomejs/biome-darwin-arm64`、`@biomejs/biome-linux-x64-musl`）。`npm install` 时会根据当前 `os` / `cpu` 拉对应平台包。

## 十一、进阶路径

如果已经跑通最小示例，可以按下面顺序继续深入：

1. **读 `biome.json` schema**：`https://biomejs.dev/reference/configuration/` 列出了所有字段。重点看 `assists`、`javascript.globals`、`overrides`，这三个决定了 Biome 能不能贴合你的工程约定。
2. **跑一遍规则索引**：`https://biomejs.dev/linter/javascript/rules/` 把 500+ 规则按类别分了组。挑出和团队风格冲突的规则，在 `rules` 里关掉或调 `severity`。
3. **接 monorepo**：Biome 原生支持 monorepo，根目录放一份 `biome.json`，子包可以 `extends`。配合 `files.include` 限定每个子包的检查范围。
4. **接 Git Hook**：用 `husky` + `lint-staged` 把 `biome check --write` 挂到 `pre-commit`，只检查暂存区文件，避免全量扫描。
5. **看一次源码 issue**：`https://github.com/biomejs/biome/issues` 上有大量真实迁移问题。挑 `migrate` 标签看一遍，能提前避开大部分坑。

## 十二、参考与延伸

- 仓库：`https://github.com/biomejs/biome`
- 官网：`https://biomejs.dev`
- 性能基准：`https://github.com/biomejs/benchmark`
- VS Code 扩展：`https://marketplace.visualstudio.com/items?itemName=biomejs.biome`
- 规则索引：`https://biomejs.dev/linter/javascript/rules/`

> 本文证据全部来自 Biome README + 官网公开文档。未在 README 中明确给出的"插件 API 完整度"、"未来 ESM/TS 类型支持计划"，本文未作推断。
