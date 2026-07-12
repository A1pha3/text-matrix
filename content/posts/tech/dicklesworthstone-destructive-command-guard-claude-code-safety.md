---
title: "DCG 实战：把 AI 编码代理挡在破坏性命令之外"
date: 2026-07-13T03:01:47+08:00
categories: ["技术笔记"]
tags: ["Rust", "AI-Agent", "Claude-Code", "安全", "CLI工具"]
description: "DCG 是为 Claude Code、Codex CLI 等 AI 编码代理设计的高性能钩子。50+ 安全包拦截破坏命令,Rust+SIMD 压时延,heredoc 三层管线捕获嵌入式脚本危险语句。"
slug: dicklesworthstone-destructive-command-guard-claude-code-safety
---
# DCG 实战：把 AI 编码代理挡在破坏性命令之外

> 仓库：`Dicklesworthstone/destructive_command_guard`（[GitHub](https://github.com/Dicklesworthstone/destructive_command_guard)），截至 2026-07-13 公开数据 2672 stars、101 forks，主语言 Rust。

## 一、为什么会有这个项目

AI 编码代理（Claude Code、Codex CLI、Gemini CLI、Copilot CLI、Cursor 等）让代码编写速度上了一个台阶，但它们偶尔会跑出让人心跳骤停的命令：`git reset --hard HEAD~5`、`rm -rf ./src`、`DROP TABLE users`、`chmod 777 -R /`。一条命令几秒就能毁掉几小时甚至几天的未提交工作。

`destructive_command_guard`（下文简称 `dcg`）正是为这类场景设计的防护层。它是一个 PreToolUse（工具调用前）钩子，在命令真正交给 shell 执行之前做一次语义过滤，命中规则就拒绝执行，并把"为什么被拦、应该改用什么"以人可读的格式返回给代理。

它的核心判断是：危险操作必须可恢复。`core.git` 和 `core.filesystem` 是不可关闭的硬底线，`core.filesystem` 覆盖危险 `rm -rf` 模式，`core.git` 拦截破坏性 git 操作，包括未提交修改丢失、历史重写、stash 销毁等场景。其他 50+ 安全包则按需启用，覆盖数据库、Kubernetes、Docker、AWS、Terraform、Stripe 等常见生产环境。

## 二、设计目标与整体形态

`dcg` 的目标受众是使用 AI 编码代理的开发者与团队。它的整体形态可以归纳为四点：

1. **零配置防护**：开箱即用，三个默认启用的"核心包"（`core.filesystem`、`core.git` 在所有平台启用，`system.disk` 在 Linux/macOS 启用，Windows 上额外启用 `windows.filesystem` 与 `windows.system`）覆盖最常见的不可逆操作。
2. **亚毫秒拦截**：基于 Rust + SIMD 加速的正则匹配 + 懒编译模式，热路径在 100 微秒以下，常见命令在 1 毫秒以内完成判断，代理不会因为防护层感知到明显延迟。
3. **上下文感知**：能在文本匹配和"这是一条要被执行的命令"之间做区分。它不会拦截 `grep "rm -rf"` 这样的字符串检索，但会拦截 `rm -rf /` 这种真实执行意图。
4. **优雅降级**：解析失败、超时、扫描器异常时默认允许通过（fail-open），避免把代理的正常工作流锁死。可以通过 `DCG_FAIL_CLOSED=1` 切换到 fail-closed。

支持的代理非常广，README 明确列出的包括：Claude Code、Codex CLI 0.125.0+、Gemini CLI、GitHub Copilot CLI、VS Code Copilot Chat（通过 Claude-hook 兼容层）、Cursor IDE、Hermes Agent、Grok（xAI）（同时支持 `~/.grok/hooks/` 原生接口与 Claude 兼容层）、Antigravity CLI（`agy`）、OpenCode（社区插件）、Pi（扩展配方）、Aider（仅 git hook 范围）、Continue（仅检测范围）。Windows 原生通过 PowerShell 安装器支持。

## 三、安全包系统：50+ 规则的模块化组织

`dcg` 的核心抽象是"安全包（pack）"。一个 pack 是一组针对特定工具或生态的破坏性命令模式。官方 README 列出了完整的包目录，这里按类别梳理一遍：

**存储类**（`storage.*`）：覆盖 S3、GCS、MinIO、Azure Blob Storage 的桶删除、对象删除、递归删除等。

**远程操作类**（`remote.*`）：覆盖 rsync 的 `--delete`、scp 覆盖系统路径、ssh 远程命令与密钥管理。

**数据库类**（`database.*`）：postgresql 的 DROP DATABASE / TRUNCATE / dropdb；MySQL；MongoDB 的 dropDatabase / dropCollection / 无条件 remove；Redis 的 FLUSHALL / FLUSHDB / 批量删除键；SQLite 的 DROP TABLE / 无 WHERE 的 DELETE；Supabase CLI 的数据库重置、迁移回滚、函数/密钥/存储删除、项目移除等。

**容器类**（`containers.*`）：Docker 的 `system prune` / `volume prune` / `force removal`；Compose 的 `down -v`（连同卷一起删）；Podman 同样操作。

**Kubernetes 类**（`kubernetes.*`）：kubectl 的 `delete namespace` / `drain` / 批量删除；Helm 的 `uninstall` / 无 dry-run 的 rollback；Kustomize 与 kubectl delete 组合的危险用法。

**云服务类**（`cloud.*`）：AWS 的 `terminate-instances` / `delete-db-instance` / `s3 rm --recursive`；Azure 的 `vm delete` / 存储账户删除 / 资源组删除；GCP 的 `instances delete` / `sql instances delete` / `gsutil rm -r`。

**API 网关类**（`apigateway.*`）：Apigee、AWS API Gateway（REST + HTTP）、Kong。

**基础设施类**（`infrastructure.*`）：Ansible、Atmos、Pulumi、Terraform（`destroy` / `taint` / 带 `-auto-approve` 的 `apply`）。

**系统类**（`system.*`）：磁盘操作（`dd` 写设备、`mkfs`、`fdisk` / `parted`、`mdadm`、btrfs、dmsetup、nbd-client、LVM 命令）；权限操作（`chmod 777`、递归 `chmod` / `chown` 打到系统目录）；服务操作（停关键服务、改 init 配置）。

**CI/CD 类**（`cicd.*`）：CircleCI、GitHub Actions（删除 secrets/variables、对 `/actions` 端点 DELETE）、GitLab CI、Jenkins。

**密钥管理类**（`secrets.*`）：AWS Secrets Manager / SSM Parameter Store；Doppler；1Password CLI；Vault CLI（删除密钥、禁用引擎、撤销租约/令牌、删除策略）。

**平台类**（`platform.*`）：GitHub CLI（删仓库、gists、releases、SSH keys）；GitLab；Kamal 2.x（`kamal remove` / `kamal accessory remove`）；Modal；Railway。

**DNS 类**（`dns.*`）：Cloudflare（记录删除、zone 删除）、Route53、nsupdate 类的通用 DNS 工具。

**邮件类**（`email.*`）：Mailgun、Postmark、SendGrid、AWS SES。

**特性开关类**（`featureflags.*`）：Flipt、LaunchDarkly、Split、Unleash。

**负载均衡类**（`loadbalancer.*`）：AWS ELB/ALB/NLB；HAProxy；nginx；Traefik。

**消息类**（`messaging.*`）：Kafka（删除 topic、删除 consumer group、重置 offset、删除 records）；NATS/JetStream；RabbitMQ；AWS SQS/SNS。

**监控类**（`monitoring.*`）：Datadog；New Relic；PagerDuty；Prometheus/Grafana；Splunk。

**支付类**（`payment.*`）：Braintree/PayPal、Stripe、Square。

**搜索引擎类**（`search.*`）：Algolia、Elasticsearch、Meilisearch、OpenSearch。

**备份类**（`backup.*`）：Borg、rclone、Restic、Velero。

**Windows 类**（`windows.*`）：默认在 Windows 启用 `windows.filesystem`（cmd `del /s`、PowerShell `Remove-Item -Recurse -Force`、`Clear-RecycleBin`）和 `windows.system`（`vssadmin delete shadows` / `wmic shadowcopy delete`、`diskpart`、`Format-Volume`、`Clear-Disk`、`Remove-Partition`、`cipher /w`、`bcdedit /delete`）；`windows.misc`（`reg delete`、`net user /delete`、`sc delete`、`wsl --unregister`、robocopy `/MIR`）与 `windows.powershell`（注册表/provider 删除、`Remove-LocalUser`、`Disable-ComputerRestore`、强制 `Stop-Computer` / `Restart-Computer`、Hyper-V 与 Appx 删除）在所有平台都是 opt-in。

**其他**：`package_managers`（危险包发布与系统包移除）、`strict_git`（更严格的 git 防护，阻止所有 force push、rebase、历史重写）。

启用方式是在 `~/.config/dcg/config.toml` 中显式列出包 ID：

```toml
[packs]
enabled = [
    "database.postgresql",
    "database.redis",
    "database.supabase",
    "containers.docker",
    "kubernetes",
    "cloud.aws",
    "cloud.gcp",
    "secrets.aws_secrets",
    "secrets.vault",
    "cicd.jenkins",
    "cicd.gitlab_ci",
    "messaging.kafka",
    "messaging.sqs_sns",
    "search.elasticsearch",
    "backup.restic",
    "platform.github",
    "platform.railway",
    "monitoring.splunk",
]
```

支持"包组"语法，写 `"kubernetes"` 等价于同时启用该命名空间下的全部子包。

### 自定义包

`dcg` 也允许团队定义自己的安全包。YAML 文件即可，可以放在 `~/.config/dcg/packs/*.yaml`（用户级）或 `.dcg/packs/*.yaml`（项目级）。`dcg pack validate mypack.yaml` 会在部署前做语法与模式校验。详细格式参考 `docs/custom-packs.md`。

## 四、安装与上手

README 给出的一键安装命令会自动检测平台、下载二进制、配置已检测到的代理 hook：

```bash
curl -fsSL "https://raw.githubusercontent.com/Dicklesworthstone/destructive_command_guard/main/install.sh?$(date +%s)" | bash -s -- --easy-mode
```

Windows 原生版本使用 PowerShell：

```powershell
& ([scriptblock]::Create((irm "https://raw.githubusercontent.com/Dicklesworthstone/destructive_command_guard/main/install.ps1"))) -EasyMode -Verify
```

`install.ps1` 会下载 `dcg.exe`、校验 SHA256（如本机装了 `cosign` 还会验证 Sigstore 签名）、把 `dcg` 加入用户 PATH、跑一次自检、并配置已检测到的代理 hook（Claude Code、Codex CLI、Gemini CLI、Copilot CLI、Cursor IDE、Hermes Agent 等）。Copilot 在 Windows 上配在 `%COPILOT_HOME%\hooks`（或 `%USERPROFILE%\.copilot\hooks`），这样所有 workspace 都被覆盖。版本可以用 `-Version vX.Y.Z` 锁定。

安装完成后做几个快速验证：

```bash
# 查看当前生效的安全包
dcg packs --verbose

# 解释一条命令为什么被拦（或为什么不拦）
dcg explain "git reset --hard HEAD~5"

# CI 集成：扫描整个仓库，输出 SARIF
dcg scan --format sarif > dcg.sarif
```

## 五、配置体系

`dcg` 的配置分为三层优先级：环境变量最高，其次是配置文件，最低是内置默认值。

### 5.1 代理差异化配置

`dcg` 能在调用时识别是哪个 AI 代理在执行命令，并应用不同的策略。在 `~/.config/dcg/config.toml` 中：

```toml
[agents.claude-code]
trust_level = "high"
additional_allowlist = ["npm run build", "cargo test"]
disabled_packs = ["kubernetes"]

[agents.unknown]
trust_level = "low"
extra_packs = ["paranoid"]
disabled_allowlist = true
```

`trust_level` 是写进 JSON 输出与日志的**标签**，并不直接改变规则评估。真正影响行为的是其他字段：`disabled_packs` 从评估中移除规则包，`extra_packs` 额外启用规则包，`additional_allowlist` 增加绕过规则，`disabled_allowlist = true` 时完全忽略 allowlist。

这种设计把"信任信号"和"行为策略"解耦开来，方便日后引入多源信任评估而无需改规则引擎。

### 5.2 Heredoc 与内联脚本扫描

AI 代理经常写出形如 `python -c "import os; os.remove('...')"` 或 `bash -c "git reset --hard"` 的命令。这类命令表面无害，深层却包含破坏性语句。`dcg` 通过三层管线处理这类输入。

先看配置：

```toml
[heredoc]
enabled = true
timeout_ms = 50
max_body_bytes = 1048576
max_body_lines = 10000
max_heredocs = 10
languages = ["python", "bash", "javascript", "typescript", "ruby", "perl", "go"]
fallback_on_parse_error = true
fallback_on_timeout = true
```

CLI 上可以用 `--heredoc-scan` / `--no-heredoc-scan` 覆盖，可以用 `--heredoc-timeout <ms>` 调时间预算，可以用 `--heredoc-languages` 限定语言。

#### 三层管线

**Tier 1 — 触发检测**（<100 μs）

用 `RegexSet` 同时跑全部触发模式，命中即进入下一层；不命中直接放行。这一层是热路径，对绝大多数命令零开销。

**Tier 2 — 内容提取**（<1 ms）

从 heredoc / here-string / `python -c` / `bash -c` 中提取真实代码。提取有边界：默认 body 不超过 1 MB、10 000 行、每条命令最多 10 个 heredoc、总耗时 50 ms。超过任一边界就 fallback 放行并打日志。

**Tier 3 — AST 模式匹配**（<5 ms）

用 tree-sitter/ast-grep 解析语言 AST，再匹配结构化模式。例如检测 `subprocess.run(..., shell=True)` 是否包含 `rm -rf`，或者把"内部仍是 bash 脚本"的内容递归拆开再交给整个流水线处理。

三层流水线的成本与收益：绝大多数命令在 Tier 1 直接放行；少数含 heredoc/内联脚本的命令进入 Tier 2 提取；只有真正命中破坏性模式的命令才在 Tier 3 被拦截并返回结构化结果。递归 shell 分析意味着即使把 `git reset --hard` 藏在 `bash -c "..."` 里，也会被捕获。

### 5.3 行为模式

`dcg` 默认是 fail-open（解析失败或超时时放行）。这背后的判断是：防护层的目标是拦截明显破坏性操作，而不是替代理做决策。误拦截会让代理反复重试或绕过防护层，整体更危险；误放行的成本由下游备份、版本控制、CI 兜底。

如确需 fail-closed，可以设 `DCG_FAIL_CLOSED=1`，钩子在输入解析失败时改为拒绝。

### 5.4 输出格式

`--format` 与 `DCG_FORMAT` 是命令相关的：每个子命令只接受自己的一套值，未识别的值会被识别为用法错误（退出码 2）。

| 命令 | 接受的 `--format` 值 |
|------|----------------------|
| `dcg scan` | `pretty`、`json`、`markdown`、`sarif`（这是唯一输出真正 SARIF 2.1.0 的命令） |
| `dcg test` | `pretty`（`text` 别名）、`json`（`sarif`、`structured` 别名）、`toon` |
| `dcg config` | `pretty`（`text` 别名）、`json`（`sarif` 别名） |
| `dcg packs` | `pretty`（`text` 别名）、`json`（`sarif` 别名） |
| `dcg explain` | `pretty`、`json`（`sarif` 别名） |
| `dcg doctor` | `pretty`、`json`（`sarif` 别名） |
| `dcg simulate` | `pretty`、`json`（`sarif` 别名） |
| `dcg corpus` | `json`、`pretty`（`sarif` 别名） |
| `dcg suggest-allowlist` | `text`、`json`（`sarif` 别名） |

设计上，`sarif` 在除 `dcg scan` 之外的所有命令上是 JSON 的别名——这是为了让 `DCG_FORMAT=sarif` 全局设置时优雅降级：`scan` 产生真 SARIF，其他命令退回到结构化 JSON 而不是报错。需要机器可读输出时优先用 `--format json`；需要 SARIF 时用 `dcg scan --format sarif`。`--robot` 强制 JSON，忽略 `--format`。

## 六、Codex CLI 的特殊处理

Codex CLI 0.125.0+ 在 README 中被作为"一等 hook 目标"对待，而不只是 Claude-shaped 兼容路径。安装器会自动检测 `PATH` 上的 `codex` 或已有的 `~/.codex/` 目录，并配置 hook。

具体协议差异：

- **Hook 配置**：合并一个 `PreToolUse` Bash hook 到 `~/.codex/hooks.json`。
- **拒绝路径**：以退出码 0 + 最小 `hookSpecificOutput` 拒绝体写到 stdout；人类警告留在 stderr。
- **允许路径**：退出码 0，stdout 和 stderr 都为空。
- **已有 hook**：保留并存的 hook，把 dcg 放在 Bash 上的第一位；遇到损坏 JSON 时拒绝覆盖。
- **验证**：subprocess 协议测试覆盖，加一个可选的真实 Codex E2E harness。

Codex 的 hook 输入和 Claude Code 接近，但 Codex 拒绝 hook 输出中的未知字段。`dcg` 通过非空的 `turn_id` 字段识别 Codex 输入，仅发出 Codex 文档化的拒绝字段，使被拦的命令被报告为"blocked"而不是"hook failed"。详细协议说明、probe 命令、故障排查见 `docs/codex-integration.md`。

## 七、绕过机制

`dcg` 不做硬锁，因为生产环境确实存在"明知风险但需要执行"的场景。文档里给出了四个层次的绕过通道：

| 方法 | 作用域 | 方式 |
|------|--------|------|
| **环境变量** | 单条命令 | `DCG_BYPASS=1 <command>` |
| **Allow-once 短码** | 单条命令 | 从拦截消息中复制短码，运行 `dcg allow-once <code>` |
| **永久 allowlist** | 规则或命令 | `dcg allowlist add core.git:reset-hard -r "reason"` |
| **移除 hook** | 全部命令 | 在 `~/.claude/settings.json`（或对应代理的等价位置）注释/删除 dcg 条目 |

`DCG_BYPASS=1` 会禁用本次调用的全部防护，应慎用；周期性的需求应改用 allowlist 而不是每次都开 bypass。

## 八、典型使用场景与边界

`dcg` 适合以下场景：

- **个人 AI 编码工作流**：Claude Code、Codex CLI、Gemini CLI 等每天跑数百条命令的开发场景。即使配置不变，三个默认核心包也能覆盖大多数破坏性误操作。
- **小团队共享 .dcg 配置**：通过 `.dcg/packs/*.yaml` 把团队特定的内部工具、部署脚本的危险模式集中管理，并随仓库提交。
- **CI 扫描**：用 `dcg scan --format sarif` 把扫描结果直接推到 GitHub Code Scanning 或类似平台，PR 阶段就能拦截。
- **多代理差异化**：用 `[agents.*]` 配置给不同代理不同的 trust_level 与 allowlist，比如让 Claude Code 跑构建流水线，让 unknown 代理走 paranoid 模式。

不适合：

- **完全无 AI 代理的环境**：此时它的价值主要在 `dcg scan` 的 CI 扫描上。
- **需要 fail-closed 的金融/医疗关键路径**：默认 fail-open 是为代理场景设计的，关键场景需要先评估 `DCG_FAIL_CLOSED=1` 的实际表现。
- **多租户 SaaS**：拦截是单租户视角的，多租户隔离需要应用层额外设计。

## 九、与同类方案的对比

`dcg` 占据的位置相对独特：

- **相对 shell 层的传统防护（如 sudo 策略、限制 rm 之类）**：`dcg` 是针对 AI 代理这一新场景设计的，能识别代理上下文、应用差异化 trust_level，并且不强制 fail-closed。
- **相对代理内置的权限系统**：内置系统通常只能拦截"是否允许执行某工具"，无法对命令做语义识别。`dcg` 是在工具已经被允许的前提下再做命令级过滤，是更细的一层。
- **相对 Open Policy Agent / Cedar 之类通用策略引擎**：`dcg` 内置了 50+ 覆盖常见 SaaS 的现成 pack，开箱即用；通用策略引擎需要团队自己写大量规则。

## 十、上手建议与读懂源码的路径

如果想了解 `dcg` 的实现细节，建议按这个顺序看：

1. 先读 `README.md` 的 TLDR 与"Enabled by default"两段，建立安全包 ID 与作用域的直觉。
2. 读 `docs/adr-001-heredoc-scanning.md`，理解三层管线为什么这么设计。
3. 翻 `src/packs/` 目录，看几个核心 pack（`core.git`、`core.filesystem`、`database.postgresql`）的实际模式定义。
4. 读 `src/heredoc/` 下 Tier 1 的 `RegexSet` 与 Tier 2 的提取器，再读 Tier 3 的 AST 匹配代码。
5. 跑一遍 `dcg doctor` 与 `dcg packs --verbose`，对照自己机器上启用的包与实际拦截日志。

对于只想用它的人，按这个顺序：

1. 跑一键安装，安装后立即用 `dcg explain` 测几条常见破坏性命令。
2. 在 `~/.config/dcg/config.toml` 中按自己工作流加上团队实际用到的 pack（比如 backend 团队加 `database.*` 与 `kubernetes.*`，前端团队加 `cloud.*` 与 `platform.*`）。
3. 把 CI 接入 `dcg scan --format sarif`，对提交做静态扫描。
4. 对个别反复需要执行的"明知风险"命令，用 `dcg allowlist add` 持久放行；对一次性绕过用 `DCG_BYPASS=1`。

## 十一、小结

`destructive_command_guard` 不是又一个 `rm -rf` 黑名单。它的设计假设是：AI 代理是高吞吐但偶尔失误的执行者，防护层应当默认可信，误拦截的代价比误放行大，因此坚持 fail-open 与显式 opt-in 安全包；又通过 SIMD 加速、懒编译、三层 heredoc 管线把延迟压到亚毫秒，让代理不会把它当作噪声；最后通过 50+ pack 与自定义 YAML 体系，让团队既能用现成规则覆盖常见 SaaS，也能把内部工具的危险模式沉淀为共享规则。

对于每天和 Claude Code / Codex CLI 一起工作的开发者，它值得装一次；对于运维多代理协作的团队，它值得把 `.dcg/` 配置纳入仓库基线。