---
title: "Biome 2.x 全栈 Web 工具链：单二进制替代 Prettier + ESLint 的 Rust 实践"
date: "2026-06-18T21:03:00+08:00"
slug: "biomejs-biome-2-rust-web-toolchain-guide"
github_repo: "biomejs/biome"
description: "biomejs/biome 是用 Rust 写的一体化 Web 工具链，格式化兼容 Prettier 97%、Linter 收录 514 条规则、原生支持 JS/TS/JSX/JSON/CSS/GraphQL，下面拆解其架构、安装与相对 Prettier+ESLint 的取舍。"
draft: false
categories: ["技术笔记"]
tags: ["代码格式化"]
---

> **快速信息卡**
> - **GitHub**: [biomejs/biome](https://github.com/biomejs/biome)
> - **Stars**: 25,460+（GitHub API 2026-08-05 验证）
> - **Forks**: 1,166+
> - **License**: Apache-2.0
> - **语言**: Rust
> - **最后更新**: 2026-08-01

## 一句话判断

Biome 给前端工具链提供了一个"单二进制替代"的选项。新项目直接上，受够了 Prettier + ESLint 配置地狱的旧项目也可以考虑迁。但如果深度定制了 ESLint 插件，迁移成本需要仔细评估。

---

## 全文地图

```text
┌─────────────────────────────────────────────────────────┐
│  Biome 的三层能力                                        │
│  ├─ Formatter  ── 97% Prettier 兼容（JS/TS/JSX/JSON/CSS）│
│  ├─ Linter     ── 514 条规则（来自 ESLint 生态）         │
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

这是 Biome 最早的能力。97% 不是 100%——剩下 3% 落在 Prettier 历史设计里的一些边角，Biome 团队选择不强行兼容，以免拖累维护节奏。

### 2. 高性能 Linter

> **Biome is a performant linter** for JS / TS / JSX / JSON / CSS / GraphQL that features more than 500 rules from ESLint, typescript-eslint, and other sources. It outputs detailed and contextualized diagnostics.

现在规则数到 514 条（biomejs.dev 当前计数），不是凭空造的，是从 ESLint、typescript-eslint 等生态移植加重写来的。规则名和大多数配置选项与原生态对齐，从 ESLint 迁过来时改动面可控。

### 3. 实时编辑器集成

> **Biome is designed from the start to be used interactively within an editor.** It can format and lint malformed code as you are writing it.

第一方支持 VS Code 和 Open VSX 上的扩展，编辑器内即时反馈。

## 三、性能：为什么用 Rust

Biome 全栈用 Rust 写，收益集中在冷启动和大仓库的 lint 速度上。

官方给出的是格式化方向的基准：在 2,104 个文件、171,127 行代码上，Biome 比 Prettier 快约 35 倍（来源：biomejs.dev）。lint 方向没有统一口径，不同基准里相对 ESLint 快 10 倍到上百倍都出现过，同为 Rust 的 oxlint 还能再拉开一截。与其记住某个倍数，不如看它实际省在哪：

- 对开发机：保存即反馈，编辑器里 lint 基本无感知
- 对 CI：整仓 check 从"分钟级"压到"秒级"，PR 反馈更快
- 运维：不用再维护 Node 版本和 npm 依赖

代价是安装包变成二进制，需要操作系统匹配（GitHub Releases 提供全平台构建）。但单二进制比 npm 几百个传递依赖反而更好管理。

> 上面的 35x 测的是那个格式化场景，反映的是 Rust 解析 + 并行调度相对 Node.js 单线程的差距。它不能推出"你的 CI 一定快这么多"——真实收益取决于文件数量、规则集大小和 CI 机器规格。更细的基准口径见 biomejs/biome 仓库的 benchmark 目录。

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

一次 `biome check` 在文件上走的路，大致是这样：

```mermaid
flowchart LR
    A[源文件<br/>.js / .ts / .jsx / .css] --> B[biome check]
    B --> C{语言识别}
    C --> D[Formatter<br/>补齐分号、统一缩进]
    C --> E[Linter<br/>514 条规则逐条判]
    C --> F[Assist<br/>import 排序 / 语义动作]
    D --> G{带 --write?}
    E --> G
    F --> G
    G -- 是 --> H[写回文件]
    G -- 否 --> I[只输出 diff]
    H --> J[biome ci<br/>有差异即非零退出]
    I --> J
```

Formatter、Linter 与 Assist 三条线并行处理，最后统一决定写回还是只报 diff。这也是为什么 `biome check` 和 `biome ci` 的差别只在"要不要改文件"上。

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

这几类场景不适合直接换 Biome：

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

## 十、再深入：schema、monorepo 与 Git Hook

跑通最小示例后，下面几点决定 Biome 能不能贴合你的工程约定：

1. **读 `biome.json` schema**：`https://biomejs.dev/reference/configuration/` 列出了所有字段。重点看 `assists`、`javascript.globals`、`overrides`，这三个直接决定工程约定能不能贴合。
2. **跑一遍规则索引**：`https://biomejs.dev/linter/javascript/rules/` 把 514 条规则按类别分了组。挑出和团队风格冲突的，在 `rules` 里关掉或调 `severity`。
3. **接 monorepo**：Biome 原生支持，根目录放一份 `biome.json`，子包可以 `extends`，配合 `files.include` 限定每个子包的检查范围。
4. **接 Git Hook**：用 `husky` + `lint-staged` 把 `biome check --write` 挂到 `pre-commit`，只检查暂存区文件，避免全量扫描。
5. **看一次源码 issue**：`https://github.com/biomejs/biome/issues` 上有大量真实迁移问题，挑 `migrate` 标签看一遍能提前避开大部分坑。

## 十一、参考与延伸

- 仓库：`https://github.com/biomejs/biome`
- 官网：`https://biomejs.dev`
- 性能基准：`https://github.com/biomejs/benchmark`
- VS Code 扩展：`https://marketplace.visualstudio.com/items?itemName=biomejs.biome`
- 规则索引：`https://biomejs.dev/linter/javascript/rules/`

