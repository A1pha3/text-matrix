---
title: Agent Skills - 安全验证的 AI 编码智能体技能注册表
date: 2026-05-18
slug: agent-skills-secure-agentic-skills-registry
github_repo: "tech-leads-club/agent-skills"
source_key: "gh:tech-leads-club/agent-skills"
categories: ["技术笔记"]
description: "Snyk 2026 年报告扫描 3,984 个技能：13.4% 含 critical 级安全问题。Agent Skills 用五层发布审查加 CLI 纵深防御把安全审查前置到发布流程。"
tags: ["AI Agent", "安全", "Claude Code", "Cursor"]
---

# Agent Skills：安全验证的 AI 编码智能体技能注册表

GitHub: [tech-leads-club/agent-skills](https://github.com/tech-leads-club/agent-skills)

## 快速信息卡

| 指标 | 数值 |
|------|--------|
| GitHub Stars | 6.5k |
| Forks | 537 |
| 许可证 | MIT（软件）+ CC-BY-4.0（技能内容），GitHub API 口径显示 NOASSERTION |
| 主要语言 | TypeScript |
| CLI 版本 | v1.5.0（npm 包 `@tech-leads-club/agent-skills`） |
| 仓库地址 | [tech-leads-club/agent-skills](https://github.com/tech-leads-club/agent-skills) |

> 数据采集于 2026-09-20。最新数据以仓库首页为准。

---

Agent Skills 把 AI 编码 agent 的技能（Skills）当成供应链依赖来管理。Snyk 2026 年 2 月的技术报告扫描了 ClawHub、skills.sh 等主流市场的 3,984 个技能，确认了 76 个恶意载荷，其中 13.4% 的技能至少包含一个 critical 级安全问题。技能市场不前置安全审查，agent 就是在直接执行来历不明的代码。

Agent Skills 把安全审查前置到发布流程——100% 开源、CI 静态分析、lockfile（锁文件）内容哈希、人工 prompt 审核、Snyk Agent Scan（Snyk 智能体扫描），五层全部通过才进 catalog。CLI 安装侧另有纵深防御：输入清理、路径隔离、符号链接防护、原子锁文件、审计日志。截至 2026 年 9 月，catalog 发布到 skills-catalog-v0.17.9，CLI 发布到 v1.5.0，累计约 1,200 次提交、81 个 release，支持 19 个 AI 编码 agent，catalog 里有 92 个技能。

这篇文章拆开两层来看：catalog 侧的发布审查机制怎么挡住恶意技能，CLI 侧的安装路径怎么挡住路径穿越和供应链篡改。

## 目录

- [学习目标](#学习目标)
- [前置知识](#前置知识)
- [威胁模型：技能市场的四个攻击面](#威胁模型技能市场的四个攻击面)
- [五层发布审查](#五层发布审查)
- [CLI 纵深防御的五道关卡](#cli-纵深防御的五道关卡)
- [一次安装的完整路径](#一次安装的完整路径)
- [跟 Claude Code Skills 和 Cursor Skills 的生态对比](#跟-claude-code-skills-和-cursor-skills-的生态对比)
- [MCP Server 与渐进式披露](#mcp-server-与渐进式披露)
- [采用建议](#采用建议)
- [自测题](#自测题)
- [常见问题与排查](#常见问题与排查)
- [动手练习](#动手练习)
- [进阶路径](#进阶路径)
- [附录：技能结构](#附录技能结构)

## 学习目标

读完这篇文章后，你应该能够：

- 说出 Agent Skills 的五层发布审查机制，以及每层各自拦截哪类威胁
- 解释 CLI 安装路径上的五道关卡，说明为什么单层绕过不足以攻破整体防御
- 验证已安装技能的内容哈希是否被篡改，并从审计日志还原操作历史
- 区分 lockfile 的四道保护（Zod schema（模式验证）、原子写入、内容哈希、移除授权）各自针对的威胁
- 为团队设计技能采用策略，判断哪些场景适合 Agent Skills、哪些需要并行厂商市场

## 前置知识

阅读本文前，建议先了解以下概念：

- **AI 编码 agent**：能在 IDE 或终端里自主读写代码、执行命令的智能体，如 Claude Code、Cursor、Cline 等
- **供应链安全**：第三方依赖被植入恶意代码或静默更新带来的风险，以及 lockfile、内容哈希等应对手段
- **TypeScript 基础**：能看懂 `async/await`、`Promise`、模板字符串等语法，理解 `resolve()`、`normalize()` 等 Node.js path 模块函数的作用

## 威胁模型：技能市场的四个攻击面

SECURITY.md 里列了四类威胁，每类对应一层防御：

| 威胁 | 公开市场的表现 | Agent Skills 的应对 |
| --- | --- | --- |
| 恶意载荷（Malicious Payloads） | 混淆代码、二进制文件、"黑盒"指令 | 100% 开源，无二进制，每行可审计 |
| 凭据窃取（Credential Theft） | 技能静默读取环境变量发往远程服务器 | CI/CD 静态分析，拦截可疑网络调用和密钥访问 |
| 供应链攻击（Supply Chain Attacks） | 作者向已发布技能推送恶意更新 | lockfile + SHA-256 内容哈希，未显式升级则代码不变 |
| 提示注入（Prompt Injection） | 隐藏指令劫持 agent 行为（"越狱"） | 人工 code review，维护者逐条审查 prompt 安全边界 |

这四类威胁覆盖了技能从发布到安装到执行的全链路。公开市场的问题在于这四层都没有强制机制——作者可以推二进制、可以静默更新、可以塞隐藏 prompt，用户安装时没有任何拦截。

## 五层发布审查

catalog 侧的发布审查有五层，每层独立运作：

| 层级 | 机制 | 拦截目标 |
| --- | --- | --- |
| 1. 开源审计 | 100% 开源，无二进制文件 | 混淆代码、闭源黑盒 |
| 2. CI 静态分析 | 每次 PR 自动扫描 | 可疑网络调用、密钥访问、危险 API |
| 3. lockfile 完整性 | SHA-256 内容哈希 + 不可变 lockfile | 发布后篡改、静默更新 |
| 4. 人工审核 | 维护者逐条 review prompt 内容 | 提示注入、越狱指令 |
| 5. Snyk Agent Scan | 发布前强制扫描（增量） | 已知漏洞模式、CVE 匹配 |

Snyk Agent Scan（前身是 mcp-scan）负责发布前的最后一道机器审查（见 [SECURITY.md](https://github.com/tech-leads-club/agent-skills/blob/main/SECURITY.md) 的 Security Scanning 章节及 [snyk/agent-scan](https://github.com/snyk/agent-scan) 仓库）。扫描是增量的——每个技能有 SHA-256 内容哈希，缓存在 `.security-scan-cache.json` 里，内容没变就跳过重扫。这让扫描快到可以运行在每个 PR 和 release 上：

```bash
export SNYK_TOKEN=your-token   # 从 https://app.snyk.io/account 获取
npm run scan                   # 增量扫描（默认，只扫变更的技能）
npm run scan -- --force        # 强制全量重扫
```

误报处理走 allowlist 机制，配置在 `packages/skills-catalog/security-scan-allowlist.yaml`。每条 allowlist 记录包含技能名、规则代码、理由、审核人、过期时间。`expiresAt` 字段可选但强烈推荐，采用 ISO 8601 日期格式（如 `'2027-01-01'`）——过期后 finding 自动重新激活，避免例外变成永久后门。

有一个值得知道的边界：扫描要读 `SNYK_TOKEN`，而 GitHub 不向 fork PR 的 workflow 暴露仓库 secrets，所以来自 fork 的 PR 在普通 workflow 里不会跑扫描。仓库的应对是提供 Merge Queue 路径——把 "Security Scan (merge queue)" 设为必需状态检查，让所有 PR（包括 fork）在合并前都被扫描拦截。

## CLI 纵深防御的五道关卡

catalog 侧挡住恶意技能进入仓库，CLI 侧挡住安装过程中的路径穿越、符号链接攻击、lockfile 篡改。SECURITY.md 给出了每道关卡的设计与示例代码。需要说明的是，仓库近期把核心逻辑重构成了 Nx monorepo：清理与路径校验函数现在住在 `libs/core/src/lib/utils.ts`，安装流程在 `libs/core/src/lib/services/installer.service.ts`（SECURITY.md 里的代码片段仍标注旧路径 `packages/cli/src/services/installer.ts`，读代码时以 `libs/` 为准）。

### 1. 输入清理（Input Sanitization）

技能名和文件路径在使用前先过清理函数。下面这段来自 `libs/core/src/lib/utils.ts`：

```typescript
// libs/core/src/lib/utils.ts
export function sanitizeName(name: string): string {
  const sanitized = name
    .replace(/[/\\]/g, '')           // 移除路径分隔符
    .replace(/[\0:*?"<>|]/g, '')     // 移除 null 字节和 Windows 禁用字符
    .replace(/^[.\s]+|[.\s]+$/g, '') // 去掉首尾点和空格
    .replace(/\.{2,}/g, '')          // 折叠连续点（禁止 ".."）
    .replace(/^\.+/, '')             // 禁止前导点（隐藏文件）

  return (sanitized || 'unnamed-skill').substring(0, 255) // 文件系统名称长度限制
}
```

这一层拦截 `../../../etc/passwd`、`skill\0name`、`/etc/passwd`、`skill:name`、`.hidden`、300 字符超长名等输入。

### 2. 路径隔离（Filesystem Isolation）

清理之后，每个解析后的路径还要验证是否严格在允许的基目录内。`libs/core/src/lib/utils.ts` 里的守卫是这样的：

```typescript
// libs/core/src/lib/utils.ts
export function isPathSafe(basePath: string, targetPath: string): boolean {
  const normalizedBase = normalize(resolve(basePath))
  const normalizedTarget = normalize(resolve(targetPath))
  return normalizedTarget.startsWith(normalizedBase + sep) ||
         normalizedTarget === normalizedBase
}
```

两个路径都经过 `resolve()` 完全解析——相对路径、符号链接、`..` 序列在比较前被消除。使用 OS 特定的分隔符 `sep` 防止 `/allowed/dir../escape` 这类技巧。

这个守卫应用在每次写、读、删操作上：`installSkillForAgent()`、`getInstallPath()`、`getCanonicalPath()`、`removeSkill()`、`isSkillInstalled()`。

### 3. 符号链接防护（Symlink Guard）

符号链接默认不可信。处理逻辑用 `lstat()` 而不是 `stat()`——`lstat()` 不跟随链接，能检测到符号链接本身，避免 TOCTOU（Time-of-Check-Time-of-Use）攻击。SECURITY.md 用 `validateSymlinkTarget()` 示意这条防线：读到符号链接就解析真实目标，目标必须落在允许目录内；链式符号链接递归解析到最终目标；`ELOOP` 错误（循环符号链接）触发后强制删除链接。

```typescript
// SECURITY.md 示意代码；当前实现在 libs/core/src/lib/services/installer.service.ts
const validateSymlinkTarget = async (linkPath: string, baseDir: string): Promise<boolean> => {
  const stats = await lstat(linkPath) // 不跟随链接
  if (stats.isSymbolicLink()) {
    const target = await readlink(linkPath)
    const resolvedTarget = resolve(join(linkPath, '..'), target)
    return isPathSafe(baseDir, resolvedTarget) // 目标必须在允许目录内
  }
  return true
}
```

重构成 monorepo 后，这套逻辑落在 `installer.service.ts` 的 `createSymlink()` 和 `cleanExistingPath()` 两个函数里：创建前先 `lstat()` 检查既有路径——是符号链接且目标一致就复用，目标不一致或不是链接就删掉重建；`ELOOP` 被捕获后无条件 `rm` 掉坏链接。Windows 上用 directory junction（目录连接点）替代 symlink，获得更好的 OS 级隔离（见 [SECURITY.md](https://github.com/tech-leads-club/agent-skills/blob/main/SECURITY.md) Symlink Guard 章节）。

### 4. 原子锁文件（Lockfile Integrity）

锁文件 `.agents/.skill-lock.json` 是已安装技能的事实来源。SECURITY.md 列了四道机制，前三道保护文件本身，第四道控制移除授权——Zod schema 防格式损坏（锁文件被外部工具改写或磁盘错误导致字段缺失），原子写入防进程中断（kill、断电、OOM 时不会留下半截文件），内容哈希防事后篡改（攻击者手动改了技能文件，下次操作时哈希对不上就会被发现），移除授权防误删和未授权清除：

**Zod schema 验证**：每次读取锁文件都过严格 Zod schema，非法或格式错误的条目被拒绝，文件优雅迁移到干净状态——不会静默损坏。

**原子写入**：锁文件从不原地写入，而是走三步：

```text
1. 备份现有文件  → .skill-lock.json.bak
2. 写入新内容    → .skill-lock.json.tmp
3. 原子重命名    → .skill-lock.json.tmp → .skill-lock.json
```

进程被 kill 时旧文件完好；重命名失败时临时文件被清理。

**内容哈希**：每个已安装技能记录 SHA-256 内容哈希，由该技能所有文件计算得出。如果技能文件在安装后被篡改，下次操作时哈希不匹配会被检测到。

**移除授权**：技能不在锁文件里就不能被移除。`--force` 标志可以绕过这个检查，但会写入审计日志。

### 5. 审计日志（Audit Trail）

每次 install、update、remove 操作都追加到 `~/.config/agent-skills/audit.log`，格式是 JSON Lines：

```json
{"action":"install","skillName":"codenavi","agents":["cursor"],"success":1,"failed":0,"timestamp":"2026-02-25T10:00:00Z"}
{"action":"remove","skillName":"codenavi","agents":["cursor"],"success":1,"failed":0,"forced":false,"timestamp":"2026-02-25T11:00:00Z"}
```

日志是 append-only——条目永不覆盖，机器上所有 agent skill 操作都留在这里供事后取证。

## 一次安装的完整路径

以安装 `tlc-spec-driven` 技能到 Cursor 为例，完整路径穿过五道 CLI 关卡：

```bash
# 1. 启动交互式安装向导
npx @tech-leads-club/agent-skills

# 2. 选择 "Install skills" → 搜索 tlc-spec-driven → 选择 Cursor
# 3. 选择安装方式：Copy（推荐）或 Symlink
# 4. 选择范围：Global（~/.cursor）或 Local（项目内）
```

CLI 拿到技能名 `tlc-spec-driven` 后，先过 `sanitizeName()` 清理输入，确认没有路径分隔符和 null 字节。然后从 CDN 下载技能包，缓存到 `~/.cache/agent-skills/`。下载完成后计算 SHA-256 内容哈希，跟 catalog 里的哈希比对，确认下载内容没被篡改。

安装写入时，目标路径过 `isPathSafe()` 验证，确认落在 Cursor 的技能目录内（如 `~/.cursor/skills/` 或项目内 `.cursor/skills/`）。如果选择 Symlink 方式，符号链接守卫会解析链接目标并确认它在允许目录内。

写入完成后，锁文件 `.agents/.skill-lock.json` 通过原子写入更新，记录技能名、安装路径、内容哈希、安装时间。最后，这次操作追加到 `~/.config/agent-skills/audit.log`。

整个过程中，任何一道关卡失败都会中断安装，已写入的文件回滚，锁文件恢复到备份状态。

## 跟 Claude Code Skills 和 Cursor Skills 的生态对比

AI 编码 agent 的技能生态目前有三条路线：

| 维度 | Claude Code Skills | Cursor Skills | Agent Skills |
| --- | --- | --- | --- |
| 来源 | Anthropic 官方 + 社区 | Cursor 官方 + 社区 | Tech Leads Club 社区 |
| 绑定 agent | Claude Code | Cursor | 19 个 agent（Claude Code、Cursor、Cline、Windsurf、GitHub Copilot 等） |
| 安全审查 | 官方技能有审查，社区技能无强制 | 官方技能有审查，社区技能无强制 | 五层发布审查 + CLI 纵深防御 |
| 供应链保护 | 无 lockfile 机制 | 无 lockfile 机制 | lockfile + SHA-256 内容哈希 |
| 安装审计 | 无 | 无 | append-only 审计日志 |
| 技能许可 | 官方公开仓库未附统一 LICENSE，按产品条款使用 | 无统一技能许可，按产品条款使用 | MIT（软件）+ CC-BY-4.0（技能内容），复用需署名 |

Claude Code Skills 和 Cursor Skills 是厂商绑定的——技能只能在对应 agent 里用，安装路径和格式由厂商决定。Agent Skills 跨 agent，同一个技能可以安装到 Cursor、Claude Code、Cline 等多个 agent，安装路径根据 agent 类型自动适配。

厂商官方技能有人工审查，社区技能市场则缺少强制安全门槛。Agent Skills 把五层审查做成发布前的强制要求——不通过就进不了 catalog。lockfile 机制是厂商技能生态里没有的：厂商技能安装后，作者可以推送更新，用户下次启动时自动拉取，中间没有内容哈希校验。Agent Skills 的 lockfile 锁定已安装技能的哈希，未显式 `agent-skills update` 则代码不变。

## MCP Server 与渐进式披露

除了 CLI 安装，Agent Skills 还提供 MCP server（MCP 服务器）`@tech-leads-club/agent-skills-mcp`，让 agent 在运行时按需查询 catalog：

```json
{
  "mcpServers": {
    "agent-skills": {
      "command": "npx",
      "args": ["-y", "@tech-leads-club/agent-skills-mcp"]
    }
  }
}
```

MCP server 暴露五个工具，按渐进式披露（progressive disclosure）原则设计：

| 工具 | 用途 |
| --- | --- |
| `list_skills` | 按分类浏览所有技能 |
| `search_skills` | 按意图模糊搜索技能 |
| `read_skill` | 加载技能的 SKILL.md 主指令 |
| `fetch_skill_files` | 按需获取特定参考文件（内容进上下文） |
| `prepare_skill_files` | 把要执行的文件（通常是 `scripts/`）写入本地缓存目录，内容不进上下文 |

`list_skills` 只在用户明确要求浏览 catalog 时调用。agent 先用 `search_skills` 找到候选技能，再用 `read_skill` 读取主指令；之后按文件用途分流——要读的参考文档走 `fetch_skill_files`，要跑的脚本走 `prepare_skill_files`。这种分层加载避免一次性把整个 catalog 灌进上下文窗口，也让"进上下文的"和"进文件系统的"走不同的安全通道。

`prepare_skill_files` 是五个工具里唯一写磁盘的。它把技能文件写到按技能版本（revision）键控的缓存目录并返回 `$SKILL_DIR`，每个文件先过校验和验证；`dry_run` 参数可以先预览将写入哪些文件。目录按版本键控意味着新版本落在旧版本旁边而不是覆盖它，同样的文件重复写入是幂等的。源码注释里对这一点说得很直白：这是唯一写盘的工具，所以 `readOnlyHint` 必须是 false。

MCP server 的安全设计：对 registry 只读，数据只来自 CDN，没有任何写回 registry 的通道；本地 stdio 通信，无网络暴露端点；`fetch_skill_files` 和 `prepare_skill_files` 在发起网络请求前都验证文件路径是否在 registry 的 `files[]` 数组里，无法获取或写入任意路径；不读写本地文件系统（`prepare_skill_files` 的缓存目录除外）；stdout 保留给 JSON-RPC 协议，所有日志走 stderr。

## 采用建议

企业安全团队需要管控 AI agent 使用的工具集——Agent Skills 的五层发布审查和 CLI 审计日志能直接接入安全合规流程。从 `npx @tech-leads-club/agent-skills` 开始，先在开发环境安装 `security-best-practices` 技能，跑一轮安全审查流程，确认审计日志和 lockfile 机制符合内部要求，再推广到生产 agent。

开发团队用 Claude Code 或 Cursor 做日常编码，想装社区技能但担心供应链风险——Agent Skills 的 lockfile + 内容哈希能挡住静默更新，Snyk Agent Scan 能挡住已知漏洞。把 Agent Skills 作为技能安装的唯一入口，禁用 agent 自带的社区技能市场，可以收窄攻击面。

Agent 框架开发者参考安全技能的设计规范——SECURITY.md 里的威胁模型表、CLI 纵深防御代码、allowlist 机制可以直接复用到自己的技能市场里。lockfile 原子写入和符号链接防护这两段代码值得直接复用。

但 Agent Skills 的 catalog 规模还小——92 个技能、15 个分类，覆盖面不如 Claude Code 或 Cursor 的官方市场。如果团队需要的技能不在 catalog 里，要么自己写技能提交审核，要么等社区贡献。对于需要大量长尾技能的团队，目前可能需要 Agent Skills + 厂商市场并行使用，把安全敏感场景（凭据访问、文件系统操作、网络调用）的技能走 Agent Skills，其他技能走厂商市场。

完整威胁模型和漏洞报告流程见 [SECURITY.md](https://github.com/tech-leads-club/agent-skills/blob/main/SECURITY.md)。官方文档在 https://tech-leads-club.github.io/agent-skills/。

## 自测题

1. 如何验证已安装技能的哈希是否被篡改？

   <details>
   <summary>查看答案</summary>

   查看锁文件 `.agents/.skill-lock.json`，里面记录了每个已安装技能安装时计算的 SHA-256 内容哈希。手动对该技能目录下所有文件重新计算哈希，跟锁文件里的值比对——如果不一致，说明技能文件在安装后被改动过。下次执行任何 agent-skills 操作（install、update、remove）时，CLI 也会自动做这个比对，哈希不匹配会被检测到。

   </details>

2. allowlist 过期后会发生什么？

   <details>
   <summary>查看答案</summary>

   `expiresAt` 字段一旦过期，该条 allowlist 记录自动失效，原本被压制的 finding 会重新激活，对应的扫描结果会重新报出这条问题。这意味着例外不会变成永久后门——维护者必须重新评估这条 finding 是否仍然属于误报，如果是，就更新 `expiresAt` 并在 PR 里说明理由；如果不是，就要修复代码。

   </details>

3. CLI 的五道关卡中，如果攻击者绕过了输入清理（第一道），后面还有哪些关卡能拦住路径穿越攻击？

   <details>
   <summary>查看答案</summary>

   至少还有两道关卡能拦。路径隔离（第二道）会在每次写、读、删操作时用 `isPathSafe()` 验证目标路径是否严格在允许的基目录内，`resolve()` 会消除 `..` 序列和符号链接后再比较。符号链接防护（第三道）用 `lstat()` 检测符号链接并递归解析目标，确保最终目标落在允许目录内。纵深防御的设计意图就是单层绕过不足以攻破整体——即使第一道漏掉了某个恶意输入，后续关卡仍然会拦截。

   </details>

4. 安装失败时，应该怎么排查路径验证不通过的问题？

   <details>
   <summary>查看答案</summary>

   确认目标 agent 的技能目录存在且有写权限。如果是 Local 安装，检查项目根目录下 `.cursor/skills/`（或对应 agent 的目录）是否被 `.gitignore` 或权限策略限制。技能名里如果包含路径分隔符或特殊字符，`sanitizeName()` 会清理掉，但清理后可能变成空字符串并回退为 `unnamed-skill`——检查输入的技能名是否来自官方 catalog。

   </details>

5. MCP server 和 CLI 安装应该怎么选？两者的安全覆盖有什么差异？

   <details>
   <summary>查看答案</summary>

   两者解决不同问题。CLI 安装把技能文件写到本地 agent 的技能目录，agent 启动时直接读取，适合需要长期使用、离线可用的场景。MCP server 在运行时按需查询 catalog，agent 通过 `list_skills`、`search_skills`、`read_skill` 渐进式定位技能，再按文件用途分流——参考文档走 `fetch_skill_files` 进上下文，可执行文件走 `prepare_skill_files` 进校验和验证过的缓存目录，适合探索新技能、按任务临时加载的场景。安全敏感场景优先用 CLI 安装，因为 lockfile 和审计日志只覆盖 CLI 路径；MCP 路径的完整性靠校验和验证与 `files[]` 路径白名单，但不进锁文件。

   </details>

## 常见问题与排查

**安装失败，提示路径验证不通过**

按从外到内的顺序排查：

1. 确认目标 agent 的技能目录存在且有写权限。Local 安装先看项目根目录下的 `.cursor/skills/`（或对应 agent 的目录）是否被 `.gitignore`、权限策略或只读挂载挡住
2. 检查锁文件 `.agents/.skill-lock.json` 是否可写——锁文件写入失败同样会让安装中断
3. 如果技能名含路径分隔符或特殊字符，`sanitizeName()` 清理后可能变成空字符串并回退为 `unnamed-skill`，安装的就不是你以为的那个技能——确认技能名来自官方 catalog
4. 把 `~/.config/agent-skills/audit.log` 最后几行拉出来看，`success`/`failed` 计数能定位是哪个 agent 的写入失败

**audit.log 被误删或损坏，如何还原操作历史**

audit.log 是 append-only 的取证日志，没有内置还原机制。如果文件丢失，操作历史无法从 CLI 侧恢复。但锁文件 `.agents/.skill-lock.json` 仍然记录了当前已安装技能的名称、路径、内容哈希和安装时间——可以从锁文件重建"当前状态快照"，只是中间的 install/update/remove 操作序列无法还原。建议把 `~/.config/agent-skills/audit.log` 纳入定期备份。

**allowlist 过期导致 CI 扫描失败**

这是预期行为。过期后 finding 重新激活，扫描会报出这条问题并阻断 release。处理方式：评估这条 finding 是否仍然是误报。如果是，更新 `packages/skills-catalog/security-scan-allowlist.yaml` 里对应条目的 `expiresAt`，在 PR 里说明继续豁免的理由，由维护者 review。如果不是误报，修复技能代码让扫描通过。不要为了绕过失败而删除 `expiresAt` 字段——无过期时间的例外正是这套机制要避免的永久后门。

**锁文件 `.agents/.skill-lock.json` 损坏，CLI 报 schema 验证失败**

这是 Zod schema 验证在起作用。锁文件被外部工具改写或磁盘错误导致字段缺失时，schema 验证会拒绝非法条目并尝试优雅迁移到干净状态。如果自动迁移失败，备份文件 `.skill-lock.json.bak` 里有上一次成功写入的完整内容——手动把 `.bak` 复制回 `.skill-lock.json` 即可恢复。恢复后运行 `npx @tech-leads-club/agent-skills` 列出已安装技能，确认状态一致。

## 动手练习

### 练习一：安装技能并验证哈希

按本文"一次安装的完整路径"一节的操作，用 CLI 安装一个官方 catalog 中的技能（如 `tlc-spec-driven`），然后检查锁文件 `.agents/.skill-lock.json`，确认该技能的 SHA-256 哈希已记录。手动对该技能目录下的所有文件重新计算哈希，与锁文件中的值比对，验证一致性。

<details>
<summary>参考答案</summary>

步骤：
1. 运行 `npx @tech-leads-club/agent-skills install -s tlc-spec-driven -a cursor`
2. 检查 `.agents/.skill-lock.json`，找到 `tlc-spec-driven` 条目
3. 用 `shasum -a 256` 对技能目录下所有文件计算哈希，与锁文件中记录比对
4. 如果一致，说明技能文件未被篡改

</details>

### 练习二：触发路径穿越检测

创建一个测试技能，尝试在 `SKILL.md` 中写入路径穿越序列（如 `../../../../etc/passwd`），然后运行安装命令，观察 CLI 的哪道关卡拦截了这个输入，以及错误信息是什么。

<details>
<summary>参考答案</summary>

步骤：
1. 创建测试技能目录，在 `SKILL.md` 的 `name` 字段中尝试插入路径穿越字符
2. 运行安装命令
3. 第一道关卡（输入清理）会调用 `sanitizeName()` 清理特殊字符
4. 如果清理后变成空字符串，会回退为 `unnamed-skill`
5. 如果绕过第一道，第二道关卡（路径隔离）会在写入时用 `isPathSafe()` 验证目标路径

</details>

### 练习三：解读安全扫描结果

找一个已安装技能，运行 `npm run scan`（需要 Snyk 订阅），解读扫描报告中的 finding 条目，判断哪些是真漏洞、哪些是误报，并尝试为误报配置 allowlist。

<details>
<summary>参考答案</summary>

步骤：
1. 确保已安装 Snyk 且已认证（`SNYK_TOKEN` 可用）
2. 在仓库根目录运行 `npm run scan`（脚本实际执行 `npx nx run @tech-leads-club/skills-catalog:security-scan`）
3. 查看输出的 finding 条目，每个条目包含：技能名、漏洞类型、严重等级、位置
4. 对于误报，在 `packages/skills-catalog/security-scan-allowlist.yaml` 中添加条目，设置 `expiresAt` 字段
5. 重新运行扫描，确认误报已被压制

</details>

## 进阶路径

- **深入理解安全机制**：直接读仓库里的 `SECURITY.md`，五层发布审查和 CLI 五道关卡的设计 rationale 都在里面。重点关注"威胁模型"表和每道关卡的实现代码指针（读代码时注意 SECURITY.md 里的路径是重构前的，现行为 `libs/core/`）。
- **为团队定制**：fork 仓库后修改 `packages/skills-catalog/security-scan-allowlist.yaml`，加入团队内部的误报规则。lockfile 的过期时间（`expiresAt`）建议设短一些（1-3 个月），强制定期重新评估。
- **贡献新技能**：按 `CONTRIBUTING.md` 的 "Creating a New Skill" 一节写 `SKILL.md`，提交 PR 后会自动走五层发布审查。想跳过某层检查可以在 PR 里说明，但维护者会逐条 review。
- **扩展到其他 agent**：CLI 支持 19 个 agent，定义集中在 `libs/core/src/lib/services/agents.service.ts` 的 `agentDefinitions` 表里——每个 agent 只声明显示名、技能目录和安装检测逻辑。如果团队用的 agent 不在列表里，照着这张表加一条再提交 PR，合并后所有人都能用。
- **结合 Snyk Agent Scan**：如果团队已有 Snyk 订阅，`npm run scan` 可以接入你们的 CI。扫描结果是增量的，每个技能的 SHA-256 哈希缓存到 `.security-scan-cache.json`，内容没变不重扫。

## 附录：技能结构

每个技能是一个目录，包含三个部分：

```text
packages/skills-catalog/skills/
  (category-name)/
    skill/
      SKILL.md          ← 主要指令（agent 读取的核心 prompt）
      templates/        ← 文件模板（代码骨架、配置文件）
      references/       ← 按需文档（agent 按需加载的参考资料）
```

`SKILL.md` 是 agent 读取的主指令文件，定义技能的工作流、触发条件、输出格式。`templates/` 存放代码模板，agent 可以直接复制到项目里。`references/` 存放按需加载的参考文档——agent 不会一次性读取全部，而是根据任务需要选择性加载，避免上下文窗口膨胀。

分类目录用括号包裹，如 `(development)`、`(cloud)`、`(web-automation)`、`(design)`、`(security)`，当前共 15 个分类、92 个技能。代表技能包括 `tlc-spec-driven`（规格驱动开发，4 个自适应阶段：Specify → Design → Tasks → Execute，按复杂度自动调节深度，用 EARS 记法写可测试需求）、`aws-advisor`（AWS 架构顾问）、`playwright-skill`（浏览器自动化）、`figma`（设计稿转代码）、`security-best-practices`（安全审查）。完整清单见 `packages/skills-catalog/skills-registry.json`。

## 资料口径说明

1. **数据时点**：Stars、Forks、release 数、提交数采集于 2026-09-20（GitHub API），catalog 版本 skills-catalog-v0.17.9、CLI 版本 v1.5.0。这类数字每天都在变，引用前请以仓库首页为准。
2. **事实来源**：安全机制与代码行为对照仓库 `SECURITY.md`、`README.md`、`CONTRIBUTING.md` 及 `libs/core`、`packages/mcp` 源码核实；13.4% 出自 Snyk 技能生态技术报告（2026-02-05，`snyk/agent-scan` 仓库 `skills-report.pdf`）。
3. **文档与代码的时差**：仓库正在从 `packages/cli` 向 Nx monorepo（`libs/core`）迁移，SECURITY.md 部分代码片段仍标旧路径，本文已按当前源码修正并逐处注明。
4. **引用许可**：软件部分为 MIT，技能内容为 CC-BY-4.0；复用 catalog 技能需按 README 要求署名 Tech Leads Club。

