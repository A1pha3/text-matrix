---
title: "ECC：把 68 个 agent / 292 个 skill / 22 套语言规则塞进一个 harness-native 控制平面"
date: 2026-09-13T23:42:00+08:00
categories: ["技术笔记"]
tags: ["ecc", "agent-harness", "claude-code", "codex", "cursor", "mcp", "opencode", "agentshield", "supply-chain", "everything-claude-code", "项目解读"]
github_repo: "affaan-m/ECC"
source_key: "gh:affaan-m/ECC"
description: "ECC（affaan-m/ECC，257k★/38.5k fork，MIT）是一个 harness-native agent operating system，把 68 个 agent、292 个 skill、94 个 legacy command、22 套语言 rules、9 套 hook runtime 装进同一个包；用一份 catalog + 一份 manifest + 一份 adapter matrix 同时驱动 Claude Code / Codex / Cursor / OpenCode / Gemini / Zed / Antigravity / Qwen / Hermes / OpenClaw / Kimi Code / CodeBuddy / JoyCode / Copilot。本文是它的一份工程解读——围绕 catalog 一致性、harness adapter 矩阵、Hook fingerprint 体系、AgentShield 供应链扫描、ECC Memory Vault 跨 harness 状态交接五个维度展开。"
draft: false
slug: affaan-m-ecc-agent-harness-os-engineering-guide
---

你装了 Claude Code、装了 Cursor、装了 Codex，想让它们跑同一套工作流——plan → test → implement → review → verify → remember → improve。试过把 5 段 prompt 复制 5 份贴进 5 个工具，3 周后 prompt 已经飘到 5 个不同的版本。`affaan-m/ECC` 就是冲着这件事来的。

`affaan-m/ECC`（Everything Claude Code，简称 ECC）是一个 **harness-native agent operating system**——给已经存在的 AI 编程工具（Claude Code / Codex / Cursor / OpenCode / Gemini / Zed / Antigravity / Qwen / Hermes / OpenClaw / Kimi Code / CodeBuddy / JoyCode / GitHub Copilot 等 14 个 harness）装一套**可发现、可验证、可移植**的 agent / skill / hook / rule / memory 层。仓库自己说的标语只有一句话：**"Optimize the context window. Persist everything else."** 上下文窗口能压就压，其余东西（工作流、记忆、技能、安全规则）都搬到磁盘上。

到 2026-09-13，这个仓库的体量是 **257k★ / 38.5k fork / MIT / v2.2.1 / npm `ecc-universal` + `ecc-agentshield` 两个包 / 50MB / 3716 个文件**。README 第一句话就是它的边界声明——直接引用：

> Your agent can write code, but ECC gives it a coordinated engineering system and toolbox: it plans before it builds, verifies changes with tests, reviews its own work from a fresh context, remembers what matters, and turns repeated wins into reusable skills and workflows.

这篇文章围绕五件事展开：**catalog 一致性 / harness adapter 矩阵 / hook fingerprint 体系 / AgentShield 供应链扫描 / ECC Memory Vault 跨 harness 状态交接**。每一件都不是"功能罗列"——是工程决策的具体落点。

## 一、为什么需要"harness-native operating system"

工业界有个反复出现的张力：**模型越来越强，但 agent 的"工程纪律"还是靠 prompt 维持**。一家团队把"先写测试再写代码"塞进 system prompt，另一家塞进 `~/.claude/CLAUDE.md`，第三家塞进 Cursor 的 `.cursorrules`——三周后三份 prompt 已经对不齐了，没人知道哪条规则现在还有效。

ECC 的判断是：**把 agent 的工程纪律从 prompt 升级成"可声明的 catalog"**。三个公共标识符在 README §1.1 写明——它们不是别名，是三种不同的分发形态：

- **GitHub 源仓库**：`affaan-m/ECC`
- **Claude marketplace / plugin identifier**：`ecc@ecc`
- **npm 包**：`ecc-universal`

Anthropic marketplace/plugin 系统的命名约束决定了 `ecc@ecc`（短到能在 Desktop / API 校验器里活着）；npm 那条因为历史包袱叫 `ecc-universal`。这三个名字互相**不能互换**——你在 Claude Code 里用 `/plugin install ecc@ecc`，在 npm 里用 `npx ecc-universal@2.2.1 setup`，两件事会装到不同的位置、有不同的副作用。

仓库用一句话锁死这件事的边界：**"OSS stays free. This repo is MIT-licensed forever. ECC Pro is the hosted GitHub App for private repos."**——核心开源、付费的只是给私有 repo 用的托管 GitHub App。这一句话让仓库的工程决策可以独立于商业压力：要不要 hooks、要不要 memory 持久化、要不要 supply-chain 扫描，都按"对 OSS 用户有没有用"来判断，不是按"对 Pro 用户怎么定价"来判断。

## 二、catalog 一致性：68 agents / 292 skills / 94 commands 怎么保证数量不出错

任何一个用过 AI 工具市场的团队都会遇到这种问题：README 上写着 "我们支持 150 个 skill"，但实际 `ls skills/` 数下来是 147 个，差 3 个没人解释。ECC 的解法是把 catalog 数量**写进 CI**。

`scripts/ci/catalog.js` 干一件事——**扫盘、读 README、把数字对齐**。代码节选（已精简）：

```js
function buildCatalog(root = ROOT) {
  const agents = listMatchingFiles(root, 'agents', entry => entry.isFile() && entry.name.endsWith('.md'));
  const commands = listMatchingFiles(root, 'commands', entry => entry.isFile() && entry.name.endsWith('.md'));
  const skills = listMatchingFiles(root, 'skills', entry => (
    entry.isDirectory() && fs.existsSync(path.join(root, 'skills', entry.name, 'SKILL.md'))
  )).map(skillDir => `${skillDir}/SKILL.md`);

  return {
    agents: { count: agents.length, files: agents, glob: 'agents/*.md' },
    commands: { count: commands.length, files: commands, glob: 'commands/*.md' },
    skills: { count: skills.length, files: skills, glob: 'skills/*/SKILL.md' }
  };
}

function parseReadmeExpectations(readmeContent) {
  const expectations = [];
  const quickStartMatch = readmeContent.match(
    /access to\s+(\d+)\s+agents,\s+(\d+)\s+skills,\s+and\s+(\d+)\s+(?:commands|legacy command shims?)/i
  );
  // ...
  expectations.push(
    { category: 'agents', mode: 'exact', expected: Number(quickStartMatch[1]), source: 'README.md quick-start summary' },
    { category: 'skills', mode: 'exact', expected: Number(quickStartMatch[2]), source: 'README.md quick-start summary' },
    // ...
  );
}
```

CI 跑这条的时候如果 `agents/*.md` 数下来是 67、README 写的是 68，**PR 直接 fail**。`npm test` 的入口脚本就是这个文件以及它的 9 个 sibling validator：

```text
test: node scripts/ci/check-unicode-safety.js \
  && node scripts/ci/validate-agents.js \
  && node scripts/ci/validate-commands.js \
  && node scripts/ci/validate-rules.js \
  && node scripts/ci/validate-skills.js \
  && node scripts/ci/validate-hooks.js \
  && node scripts/ci/validate-install-manifests.js \
  && node scripts/ci/validate-no-personal-paths.js \
  && npm run catalog:check \
  && npm run command-registry:check \
  && node tests/run-all.js
```

8 个 validator 加 2 个 catalog 检查，每个跑挂就直接终止 pipeline。我数了当前仓库：

| 目录 | 实际文件数 | README 标称数 |
|---|---|---|
| `agents/*.md` | 68 | 68 ✅ |
| `skills/*/SKILL.md` | 292 | 292 ✅ |
| `commands/*.md` | 94 | 94 ✅ |

这种"目录数 vs README 标称数"的对齐看起来琐碎，但在一个 257k★ 仓库里是**长期可维护性的硬基础**。没有它，6 个月后就会有 5 个 "我装的时候明明说是 300 个 skill" 的 issue 飘在 GitHub。

**值得注意的取舍**：validator 用 glob 数文件，而不是解析 frontmatter 数逻辑条目。这意味着一个 `agents/foo.md` 即使 frontmatter 错乱，也被算作 1 个 agent。**目录结构是 catalog 的真相源，frontmatter 是 metadata**——这条规则让 catalog 校验能在 50ms 跑完，没有解析开销，也避免了"frontmatter 语法漂移"导致 catalog 误报。

## 三、harness adapter 矩阵：14 个工具的"能力声明"是显式的

ECC 同时声称支持 14 个 AI 编程工具，但**任何诚实的跨平台抽象都承认：能力不平价**。ECC 把这件事写成一份**强校验的 adapter 记录**，由 `scripts/lib/harness-adapter-compliance.js` 把 14 条 adapter record 锁进 `ADAPTER_RECORDS` 数组。每条记录有 11 个必填字段：

```js
const REQUIRED_FIELDS = Object.freeze([
  'id', 'harness', 'state', 'supported_assets',
  'unsupported_surfaces', 'install_or_onramp', 'verification_commands',
  'risk_notes', 'last_verified_at', 'owner', 'source_docs',
]);

const COMPLIANCE_STATES = Object.freeze({
  Native:              'ECC can install or verify the surface directly for this harness.',
  'Adapter-backed':    'ECC has a thin adapter, plugin, or package surface, but parity differs by harness.',
  'Instruction-backed':'ECC can provide the guidance and files, but the harness does not expose the runtime hook/session surface ECC needs for enforcement.',
  'Reference-only':    'The tool is useful as a design pressure or external runtime, but ECC does not yet ship a direct installer or adapter for it.',
});
```

四个 state 不含糊——**Native / Adapter-backed / Instruction-backed / Reference-only**——分别对应"我能直接装/验"、"我有薄适配层但能力按 harness 漂移"、"我能给文件但没有 hook runtime"、"我不装但可以当外部运行时参考"。当前仓库的实际状态（节选 4 条）：

| Harness | State | 时间戳 | 备注 |
|---|---|---|---|
| Claude Code | Native | 2026-05-12 | 主参考，含 plugin/skills/commands/hooks/MCP/local rules |
| Codex | Instruction-backed | 2026-05-12 | AGENTS.md + plugin metadata + skills + MCP；hooks 不对等 |
| OpenCode | Adapter-backed | 2026-05-12 | package + 共享 skills + 事件 adapter；事件名/打包/调度与 Claude Code 不同 |
| Pi | Adapter-backed | 2026-08-10 | canonical skills/commands/rules + session lifecycle adapter；subagent/chain/approval 不在本 adapter |
| Cursor | Adapter-backed | 2026-05-12 | rules + project skills + hook adapter；Cursor 加载语义与 Claude Code 不同 |
| Gemini | Instruction-backed | 2026-05-12 | 项目本地 instructions + 共享 skills + rules；没有 hook parity |
| GitHub Copilot | (未列完整，README 标 instruction-only) | – | 只有 `.github/copilot-instructions.md` + `.github/prompts/`；没有 ECC hook |

每条 adapter 还有一个 `risk_notes` 字段把"别做什么"也写明——比如 Claude Code 那条写 **"Avoid loading every skill by default; keep hooks opt-in and inspectable."**，Codex 那条写 **"Treat hooks as policy text unless a native Codex hook surface exists."**，Cursor 那条写 **"Cursor adapters must preserve existing project rules and avoid silent overwrite."** 这些 risk notes 直接进 README 的 platform support 矩阵——它不是 marketing 等级，是**工程上"按这个状态来用"的明确边界**。

CI 校验在两条路径上都跑：

```bash
npm run harness:audit        # 生成 markdown / JSON / text 报告
npm run harness:adapters     # --check 模式：adapters 或 docs 不一致就 fail
```

`--check` 模式意味着 `ADAPTER_RECORDS` 和 README 的 platform support 表**任何不一致都会被 PR 拦下来**。这相当于把"我支持什么 / 不支持什么"这件事**锁在 CI**——任何营销驱动的能力声明都会被工程现实拖回。

## 四、hook fingerprint 体系：9 个 PreToolUse matcher 不是"越多越好"

hooks 是 ECC 在 Claude Code 这条线上的核心 runtime。`hooks/hooks.json` 列了 9 个 PreToolUse matcher（不全展开，按功能分类）：

| Matcher | Hook ID | 作用 | 阻断 |
|---|---|---|---|
| `Bash` | `pre:bash:dispatcher` | 统一 bash preflight（quality / tmux / push / GateGuard） | 失败阻断 |
| `PowerShell` | `pre:powershell:gateguard-fact-force` | PS 专用 fact-forcing gate（不跑 bash-only preflight） | 阻断 |
| `Write` | `pre:write:doc-file-warning` | 非标准 doc 文件警告 | 不阻断（warn only） |
| `Edit\|Write` | `pre:edit-write:suggest-compact` | 在编辑到达一定体量时建议手动 compact | 不阻断 |
| `.*` | `pre:observe:continuous-learning` | 持续学习：记录工具调用信号 | async, 不阻断 |
| `Bash\|PowerShell\|Write\|Edit\|MultiEdit` | `pre:governance-capture` | 治理事件捕获（secrets / 策略 / 审批） | 默认不启用 (`ECC_GOVERNANCE_CAPTURE=1` 打开) |
| `Write\|Edit\|MultiEdit` | `pre:config-protection` | 阻挡改 linter/formatter config 的尝试 | 阻断 |
| `.*` | `pre:mcp-health-check` | MCP server 健康检查 | 阻断 |
| `Edit\|Write\|MultiEdit` | `pre:edit-write:gateguard-fact-force` | 编辑前 fact-forcing：先调研（importers / schemas / 上下文）再允许 | 阻断 |

每一个 hook 配一个 fingerprint（在 `hooks/hooks.metadata.json` 里），例如 `0d30f37d2148`（bash dispatcher）、`d99998a8f039`（suggest-compact）、`922686364d01`（mcp-health-check）。

这套 fingerprint 干什么？**版本溯源**。hook 逻辑是 determinstic 的，但运行它的 node 版本、平台、`PATH` 都会漂。`harness:audit` 在不同机器上跑出来的 fingerprint 必须一致；如果不一致，要么是 hook 本身被改了（要发版），要么是环境脏了（要修）。这是把 hook runtime 从"魔法脚本"升格成"可观测组件"的工程基础。

**更细一层的工程纪律**：每个 hook 都有**profile gating**——`ECC_HOOK_PROFILE` 环境变量默认 `standard`，可以选更严格的 `strict` 或者干脆 `ECC_DISABLED_HOOKS="pre:bash:tmux-reminder,post:edit:typecheck"` 临时关掉。这一设计在 README §1.7 明确写出来，把"是否启用 hook"的选择权留给操作者，不让 hooks 强加给所有人。

**`pre:edit-write:gateguard-fact-force` 是这套 hook 里最有意思的一条**——它的 description 是："block first Edit/Write/MultiEdit per file and demand investigation (importers, data schemas, user instruction) before allowing"。第一次编辑某个文件的时候**强制阻断**，要求 agent 先回答：哪些 importer 引用这个文件？数据结构是什么？用户给的原始指令是什么？这一条 hook 把 ECC 的核心哲学——**让 agent 在动手前先理解上下文**——直接编码成可执行的边界。同样的哲学在 `pre:config-protection` 里再次出现："Block modifications to linter/formatter config files. Steers agent to fix code instead of weakening configs."——别让 agent 通过改 lint 配置来"修复"代码错误，把锅甩给规则。

## 五、AgentShield + 供应链扫描：在 agent runtime 里加一条供应链防线

2025 年到 2026 年，npm / PyPI 上的 agent 供应链攻击连续爆发：恶意包名伪装、版本号投毒、`postinstall` 脚本偷凭证、`tarball` 替换。ECC 没把这件事当"安全团队的事"——它做了一套 `ecc-agentshield` 单独打包，内置在仓库的扫描脚本 `scripts/ci/scan-supply-chain-iocs.js` 里。

代码开头一段就把意图写明：

```js
/**
 * Scan dependency manifests, lockfiles, AI-tool configs, and installed package
 * payload paths for active supply-chain incident indicators.
 */
const MALICIOUS_PACKAGE_VERSIONS = {
  '@beproduct/nestjs-auth': ['0.1.2', ..., '0.1.19'],
  '@cap-js/db-service': ['2.10.1'],
  '@cap-js/postgres': ['2.2.2'],
  '@cap-js/sqlite': ['2.2.2'],
  '@dirigible-ai/sdk': ['0.6.2', '0.6.3'],
  // ...
};
```

`MALICIOUS_PACKAGE_VERSIONS` 是一份**已知恶意包+版本的指纹表**——超过 100 个包被点名，每个都附精确版本号。`scripts/ci/supply-chain-advisory-sources.js` 进一步把数据源、advisory URL、scan 命令绑在一起，让 AgentShield 扫描不依赖"我记得"的内存，而是依赖"机器可读的事实表"。

执行链路是：

```bash
npm run security:ioc-scan           # 扫盘
npm run security:advisory-sources   # 列 advisory 来源
npm run release:approval-gate       # 发版前最后一道
```

`release:approval-gate` 在 `package.json` 里是个独立脚本节点——它的存在意味着 **ECC 不允许 release 时跳过 supply-chain 检查**。即使 release.sh 里手动改过流程，approval-gate 仍然作为一个独立入口被 PR CI 触发。

文档 `docs/architecture/agentshield-enterprise-research-roadmap.md` 把 AgentShield 的设计意图写得很清楚：它**不是 lint tool**——它有 policy pack、GitHub Action 策略执行、SARIF policy violation、supply-chain provenance、corpus benchmark、HTML executive report、exception lifecycle audit。证据消费链路是 first-class 的：`agentshield evidence-pack inspect <dir>` 验证一个 bundle 后输出 JSON/text 摘要；`agentshield evidence-pack fleet <dirs...>` 把多个 bundle 聚合成 ready / security-blocker / policy-review / baseline-regression / supply-chain-review / invalid 六条路由。

**值得停下来想一想的工程决策**：AgentShield 把"`runtimeConfidence: plugin-cache`"作为分类指标——已安装的 Claude plugin cache 内容标记为 plugin-cache，`score impact 0.5x`，**不影响 plugin-cache 评分但避免把"装了就跑"的 cache 误判为 "active hook-code"**。这条决策写得很细：它的代价是漏报率上升一点点，收益是误报率下降一大截。对一个要在 14 个 harness 上跑的 scanner 来说，**误报会立刻失去操作者信任**——0.5x score impact + 显式分类标记，是把"信噪比"作为 first-class 约束的设计选择。

## 六、ECC Memory Vault：跨 harness 的状态交接

把 14 个 harness 装好之后，下一个问题：**怎么让 Claude → Codex → Hermes → Cursor 互相交接任务**？每个 harness 都有自己的 session state、inbox、transcript 格式——硬塞一个标准是不可能的。ECC 的解法是建一个**便携的 Markdown vault**：`ecc.memory.v1` 文档存到磁盘，路径约定如下：

| Scope | 路径 | 用途 |
|---|---|---|
| `project` | `<repo>/.ecc/memory/project/` | 仓库本地，受 fail-closed `.gitignore` 保护 |
| `team` | `<repo>/.ecc/memory/team/` | 团队共享，进版本控制 |
| `user` | `~/.ecc/memory/` | 用户级，跨仓库跟随 |

`skills/unified-memory/SKILL.md` 把操作流程写得很清楚：

```bash
# 1. 检索：在写之前先查
ecc memory search "authentication migration" --target-harness codex
ecc memory read <memory-id>

# 2. 保存：从 stdin 或文件喂正文（不出现在 process list）
printf '%s\n' 'The migration tests pass; rollout is still pending.' |
  ecc memory save \
    --title "Authentication migration status" \
    --kind context \
    --source-harness codex \
    --target all \
    --tag auth \
    --stdin

# 3. 交接：明确 from / target / title / body-file
ecc memory handoff \
  --from codex \
  --target claude \
  --title "Finish authentication rollout" \
  --body-file handoff.md

# 4. 验证：在 commit team memory 前跑一遍
# (commands/security checks per skill)
```

最值得注意的是 **"recall 是证据，不是定论"** 这一段（skill 文件原文翻译）：

> Bind the lookup to the current workspace, intended recipient and allowed scopes. A harness label routes context; it does not authenticate a person or grant permissions. Never recover a denied lookup by broadening the scope.
>
> Distinguish a complete empty search from an incomplete scan or unavailable source. Inspect search diagnostics. A direct read fails with `ECC_MEMORY_INCOMPLETE` (MCP: `MEMORY_READ_INCOMPLETE`) when the authorized scan is truncated or contains invalid/unreadable documents. Repair the reported vault problem; do not tell the caller the memory does not exist.
>
> Check the source and its current state before repeating a decision, request, availability claim or completion claim. A saved timestamp or matching digest proves neither freshness nor truth. Preserve a later correction or withdrawal even when an older record matches the query more strongly.

这套设计里有 4 个工程决策值得拎出来：

1. **检索必须落到具体 scope + workspace + recipient**——而不是"全局搜"。"放宽 scope 来绕过 denied lookup" 是明令禁止的反模式。
2. **不完整的 scan 必须报错 `ECC_MEMORY_INCOMPLETE`**，不能悄悄返回空集——空集和"我没扫完"是完全不同的两种状态。
3. **时间戳/digest 不证明 freshness**——这一条把"凭记忆决策"这条捷径堵死，必须重新验证 source 的当前状态。
4. **后续修正/撤回必须保留**——即使旧记录匹配得更强，也不能让新修正被旧记录覆盖。链接不是 supersede，operator 显式标记 `superseded` 才能让普通检索排除它。

这套 vault 设计把"AI 跨工具协作"从一个工程问题（怎么传数据）升级成一个**协议问题**（怎么传信任）。所有 14 个 harness 都能读这一份 vault，但 vault 本身不假设任何 harness 是权威——信任来自"我要再查一次"。

## 七、与"everything-claude-code"的命名暗线

打开仓库你会看到一个有趣的双名现象：`.claude-plugin/plugin.json` 的内部字段、Claude marketplace 标识符、CI 校验的 fallback list 都同时提到 `ecc` 和 `everything-claude-code` 两个名字。早期 README 写过 `ECC = Everything Claude Code`，后来重命名为 `ECC`，但**没改名干净**——很多 fallback 路径还保留 `everything-claude-code` 作为别名，README §1.1 明确说"Older posts may still show the former long marketplace identifier; treat that as a legacy alias only"。

这种"双名残留"通常被批评为"项目治理不善"。在 ECC 这个特定情况下，我读出来的是另一种信号：**没有重命名破坏向后兼容**——之前按 `everything-claude-code` 装的 Claude plugin 还能被识别，迁移路径被保留。这是一条有意识的工程纪律，与前文"OSS stays free"的口径一致：商业重命名不能让 OSS 用户掉链子。

但代价是**catalog 表面上的复杂度**——`plugins/ecc/.codex-plugin/plugin.json` 里的 `keywords` 还在用 `codex, agents, skills, tdd, code-review, security, workflow, automation` 这种偏 marketing 的词；harness-adapter-compliance 的 records 里有 14 条记录，每条都引用 `.claude/`、`.cursor/`、`.codex/` 等不同路径；`scripts/lib/install-targets/registry.js` 的 ADAPTERS 数组同时收 `claudeHome`、`claudeProject`、`cursorProject`、`codexHome`、`openclawHome`、`hermesHome` 等 16 个 adapter 文件——`codexHome` 是 `codex` 工具的 home-dir 安装，`claudeProject` 是 `.claude/` 仓库本地安装，`claudeHome` 是 `~/.claude/` 用户目录安装。

**这种复杂度是 ECC 必须承担的代价**，不是设计缺陷。因为它的承诺是"一个仓库覆盖 14 个工具"，任何一个工具的安装语义变化（home-dir vs project-dir vs marketplace-plugin）都要进 adapter 矩阵；任何一个 README 上的标称数（68 / 292 / 94）变了 CI 都会 fail。这把"覆盖广"翻译成"配置矩阵的可维护性"——而可维护性的唯一现实约束是**所有路径都被显式声明，没有"魔法路径"**。

## 八、ECC 2.0 alpha：Rust 重写的 control-plane

仓库根目录有一个 `ecc2/` 子目录——**Rust 重写的 ECC 2.0 alpha**。`ecc2/README.md` 开头就声明状态：

> `ecc2/` is the current Rust-based ECC 2.0 control-plane scaffold. It is usable as an alpha for local experimentation, but it is **not** the finished ECC 2.0 product yet.

现状（README 列的）：

- terminal UI dashboard
- session store backed by SQLite
- session start / stop / resume flows
- background daemon mode
- observability and risk-scoring primitives
- worktree-aware session scaffolding
- basic multi-session state and output tracking

设计意图（README 写明）：

> ECC 2.0 is the layer above individual harness installs. The goal is: manage many agent sessions from one surface; keep session state, output, and risk visible; add orchestration, worktree management, and review controls; support Claude Code first without blocking future harness interoperability.

`Cargo.toml` 锁文件已经在仓库里，`rust-toolchain.rs` 标版本——这不是规划文档，是**实际可编译的 alpha**：

```bash
cd ecc2
cargo run
```

**值得停下来想一想的取舍**：ECC 主仓用 Node.js（适配 Claude Code / Codex / Cursor 的 hook runtime），但 control-plane 用 Rust 重写。一个跨语言工程边界会带来 4 类代价：

1. **构建/分发链分叉**：npm 包 + Cargo 二进制，两套 lockfile，两套 CI。
2. **状态序列化兼容性**：Node.js 端的 SQLite schema 必须和 Rust 端的 SQLite schema 对齐——任何 schema 漂移都会让一个 daemon 读不到另一个 daemon 写的数据。
3. **Hook runtime 仍是 Node**：Rust control-plane 不直接执行 hook，它协调 Node.js runtime 的多 session。这意味着 Rust 端是"调度层"而不是"执行层"，执行层的优化空间被锁在 Node 上。
4. **运维心智两套**：日志格式、错误传播、调试工具、profile 入口都要在两套生态里各自维护。

ECC 选择这条路而不是"全部用 Node"或"全部用 Rust"，是因为它要支持 Claude Code / Codex / Cursor / OpenCode 等不同 harness 的 hook runtime——这些 runtime 主要是 Node。Rust 重写只覆盖"control plane"——这是真正可以从 Node 抽象出来的层（SQLite + session bookkeeping + observability + worktree），没有 hook runtime 的固有语言依赖。

这条决策背后是一个事实：**14 个 harness 没有一个用 Rust 做 hook runtime**——Claude Code / Codex / Cursor / OpenCode / Gemini / Zed / Antigravity / Qwen / Hermes / OpenClaw / Kimi Code / CodeBuddy / JoyCode / Copilot 各自的 hook runtime 几乎都是 Node。Rust control-plane 是"管理这 14 个 harness 的调度层"，不是"替换它们"。

## 九、agent-harness-construction 与 agent-eval：两条可移植 skill

仓库 292 个 skill 里有两条特别值得拎出来——它们不是 ECC 独有的，但 ECC 把它们做成"任何 harness 都能用"的形式。

### 9.1 agent-harness-construction：设计 agent 的 action space

`skills/agent-harness-construction/SKILL.md` 把 agent 输出质量分解成 4 个维度：

> Agent output quality is constrained by:
> 1. Action space quality
> 2. Observation quality
> 3. Recovery quality
> 4. Context budget quality

每条都有具体的设计规则：

- **Action Space**——stable explicit tool names；schema-first narrow inputs；deterministic output shapes；avoid catch-all tools。**Granularity rules**：micro-tools for high-risk (deploy/migration/permissions)；medium for common edit/read/search；macro only when round-trip overhead is the dominant cost。
- **Observation**——every tool response must include `status` (`success|warning|error`)、`summary` (one-line)、`next_actions` (actionable follow-ups)、`artifacts` (file paths / IDs)。
- **Error Recovery Contract**——error path 必须含 root cause hint + safe retry instruction + explicit stop condition。
- **Context Budgeting**——system prompt minimal and invariant；large guidance 移到按需加载的 skill；prefer file references over inline；compact at phase boundaries, not at arbitrary token thresholds。

**anti-patterns** 列出 4 条——overlapping tools、opaque tool output、error-only without next steps、context overloading with irrelevant references。

这条 skill 是一份**agent 工程化的可执行 checklist**。它不是给 LLM 看的——它是给"设计 agent 的人"看的：设计 action space 的时候，颗粒度按"风险/频率/延迟"三维划分；设计 observation 的时候，强制四件套结构；设计 recovery 的时候，强制"根因 + 重试 + 停止"三件套。**ECC 自己就用这套规则**——比如它的 hook observation（`post:observe:continuous-learning`）就强制输出 status/summary/next_actions 四件套。

### 9.2 agent-eval：把 "which coding agent is best" 从印象判断变成可复现实验

`skills/agent-eval/SKILL.md` 的开头一句话就是这个 skill 的动机：

> Every "which coding agent is best?" comparison runs on vibes — this tool systematizes it.

它做三件事：

1. **YAML task definition**——每个 task 声明 `name` / `description` / `repo` / `files` / `prompt` / `judge` (含 pytest / grep / commit pin)。
2. **Git worktree isolation**——每个 agent run 自己的 worktree，不需要 Docker。**这是关键决策**——worktree 隔离的代价是"agent 可以看到自己的修改历史"，收益是"不需要 Docker"——`/usr/bin/git worktree add` 在所有平台都有，比 Docker-in-Docker 快一个数量级。
3. **4 个 metric**：pass rate / cost / time / consistency（重复运行的 pass rate，例如 3/3 = 100%）。

它的 README 还给了一个 anti-pattern 警告——"vibes 评估"在 LLM 评测里泛滥了——`agent-eval` 的存在意义是**用一组 YAML 任务 + git worktree 隔离 + 4 个指标** 把"哪个 agent 更好"这个争论从印象判断变成可复现实验。

## 十、这条工程解读的边界

ECC 是一个**真实的工程产品**——50MB 仓库、257k★、14 个 harness 适配、68/292/94 catalog 锁在 CI、9 套 hook runtime + 22 套语言 rules + AgentShield 供应链扫描 + Memory Vault 跨 harness 状态交接——但它的"AI 编程 agent operating system"这一定位有几个**显式边界**：

1. **OSS 不含 Pro 增强**：README 第一句话锁死——`ECC Pro is the hosted GitHub App for private repos`，OSS 用户拿不到 Pro 的 fleet dashboard、hosted security review、PR diff packet guidance。
2. **platform support 不是平等**：Claude Code 是 stable primary；Codex 是 supported native plugin；Cursor / OpenCode 是 beta；其他 8 个是 experimental/minimal。`harness:adapters --check` CI 把这件事锁在代码里。
3. **Windows native 有明确缺陷**：issues #2489 和 #2626 公开承认 continuous-learning v2 的 observer daemon 和 memory-vault writes 在 native Windows 下有问题；macOS Bash 3.2 上的 standalone GAN shell path 不兼容 (#2674)。README 不掩盖——它把"哪条路在哪个 OS 上会断"直接列出来。
4. **instruction-only harness 不假装 hook parity**：GitHub Copilot 是 `instruction-only`——`.github/copilot-instructions.md` + `.github/prompts/` + `.vscode/settings.json` 三个文件，没有 ECC hook、没有 runtime agent、没有 delegation、没有 native skill discovery。CI 不会让它升级到 Adapter-backed，除非真的有 hook surface 可以接。
5. **ECC 2.0 还是 alpha**：`ecc2/` 是 Rust 重写的 control-plane scaffold，README 明说 **"not yet a public GA release"**——`cargo run` 可以跑，但不要把生产 workload 跑在它上面。

如果你的团队在选 AI 编程工具栈，ECC 的价值不在"它最好"，而在**"它把所有 cross-tool 边界写在 CI 里"**——catalog 数字、adapter 矩阵、hook fingerprint、supply-chain IOC、memory vault scope，全部由机器校验而不是人记得。这意味着 6 个月后 50 个 PR 进来，**catalog 仍然对得上、adapter 矩阵仍然如实、hook fingerprint 仍然稳定、IOC 仍然是最新的**。

如果你的团队还没大到需要 14 个 harness 共存，**`install.sh --target claude --profile minimal`** 拿到的就是一个干净的 Claude Code 增强包——292 个 skill 里只有你 `with` 的那几条会落地，9 套 hook runtime 里只有你 profile 里启用的那几条会跑。**OSS 的免费承诺是真的**：核心 catalog + hooks + memory vault 永远在 `affaan-m/ECC` 这个仓库里，MIT 许可下谁都能 fork、谁都能改、谁都能改成自己的私有变体。

ECC 不是 agent operating system 的终点——它是**第一个把 "agent 工程纪律应该用 catalog 表达" 这件事写进 CI** 的工程产品。这条原则的普适性比 ECC 这个具体仓库更重要：把 prompt 升级成目录结构、把"我支持 X"升级成 ADAPTER_RECORDS 强校验、把"安全"升级成 IOC 表 + CI 检查、把"跨工具协作"升级成便携 Markdown vault + scope gating——每一件都是工程现实，**每一件都被机器校验**。这种"把工程纪律机器化"的趋势，会在 2026 年到 2027 年成为 AI 编程工具栈的隐性入场券。