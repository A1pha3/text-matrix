---
title: "Domain Check：RDAP 优先的域名可用性检查引擎，CLI、Rust 库与 MCP 服务器共用同一个内核"
date: "2026-04-13T23:51:22+08:00"
lastmod: "2026-10-02T00:00:00+08:00"
slug: "domain-check-universal-domain-checker-guide"
github_repo: "saidutt46/domain-check"
source_key: "gh:saidutt46/domain-check"
description: "Domain Check 是 Rust 编写的域名可用性检查引擎：RDAP 优先、WHOIS 自动回退，IANA bootstrap 开箱覆盖 1,200+ TLD。同一引擎提供 CLI、Rust 库与 MCP 服务器三种形态，本文拆解其双协议机制、11 个预设、配置体系与 v1.0.2 的准确性修复。"
draft: false
categories: ["技术笔记"]
tags: ["工具", "CLI", "Rust", "MCP"]
---

# Domain Check：RDAP 优先的域名可用性检查引擎

查一个域名有没有被注册，看起来就是发一次 WHOIS 查询的事，但真要做成可靠的自动化能力，问题立刻变多：新 gTLD 大多没有统一的 WHOIS 格式，`.es`、`.jp` 这类 ccTLD 连 RDAP 端点都缺，批量查询会撞上注册表限流，脚本里解析半结构化的 WHOIS 文本更是常年出错的来源。

[saidutt46/domain-check](https://github.com/saidutt46/domain-check) 的思路是把这件事重新拆一遍：以结构化的 RDAP 为主协议，WHOIS 只做回退；IANA 的 bootstrap 注册表在首次使用时自动加载，让 1,200 多个 TLD 开箱可用；再把同一个检查内核封装成 CLI、Rust 库和 MCP 服务器三种形态。它不是"又一个 whois 命令"，而是一个可以被脚本、Rust 程序和 AI Agent 共用的检查引擎。

## 系统地图：一个内核，三个封装

仓库是一个 Cargo workspace，三个 crate 共享同一套检查逻辑：

| Crate | 形态 | 适合谁 |
|---|---|---|
| `domain-check` | CLI 二进制（约 2.7 MB） | 命令行、shell 脚本、CI |
| `domain-check-lib` | Rust 库 | 嵌入 Rust 服务的开发者 |
| `domain-check-mcp` | MCP 服务器（stdio） | Claude Code、Cursor 等 AI Agent |

当前版本 v1.0.3（2026-09-28 发布，CLI、库、MCP 三个 crate 同步发版），MIT OR Apache-2.0 双许可，仓库约 308 stars（2026-10-02 读数）。预编译二进制覆盖 Linux（x86_64、musl）、macOS（x86_64、aarch64）和 Windows，MSRV 为 Rust 1.88。

先说结论性的判断：这个项目解决的是"域名可用性检查"这一件小事，但把它做成了三层都好用的样子——人在终端用 CLI，服务端嵌库，Agent 走 MCP。如果你的需求只是偶尔查几个域名，系统自带的 `whois` 就够；它值得上场的是批量检查、CI 集成和 Agent 工作流。

## 检查引擎怎么工作

### 双协议：RDAP 优先，WHOIS 回退

RDAP（RFC 9082）返回结构化 JSON，是 WHOIS 的现代替代协议；WHOIS（RFC 3912）输出是半结构化文本，各注册表格式不一。Domain Check 的策略是 RDAP 优先，失败时自动回退 WHOIS。

IANA 的 bootstrap 注册表（`dns.json`）记录了每个 TLD 的 RDAP 端点。首次使用时工具会抓取这份文件，加载约 1,180 个 TLD 到端点的映射并缓存 24 小时——这就是"1,200+ TLD 开箱即用"的来源（README 的宣传口径是 1,200+，其中约 1,180 个走 RDAP）。32 个硬编码 TLD 作为离线兜底，`--no-bootstrap` 可以完全关闭联网引导。

对于没有 RDAP 端点的约 189 个 ccTLD（如 `.es`、`.co`、`.eu`、`.jp`），工具通过 IANA 的 referral 机制自动发现权威 WHOIS 服务器再查询。也就是说 `.jp` 这类"难缠"的 TLD 不需要手动配置任何东西。

JSON 结果里的 `method_used` 字段会标明实际走的是哪条路：`rdap`、`whois`、`bootstrap`（经 bootstrap 发现的 RDAP 端点）或 `unknown`（查询失败）。

### v1.0.2 修掉了一个关键的准确性问题

这是本文认为最值得知道的一条版本史。v1.0.2（2026-03-22，Issue #30）之前，RDAP 返回 404 会被直接判定为"域名可用"。但 `.moe` 等注册表会对**已注册**但未设置 NS 委派的域名也返回 404，这造成假阳性——脚本以为捡到宝，其实是误报。

修复后的语义对齐了 RFC 7480 §5.3：

- RDAP 404 视为"不确定"，先向 WHOIS 求证再下结论；
- 双协议结论从"任一可用即可"改为"RDAP 和 WHOIS **都**独立指示可用才报 AVAILABLE"，单靠 RDAP 404 只报 UNKNOWN；
- 若用 `--no-whois` 关掉了回退，RDAP 404 会返回 AVAILABLE 并附带警告，而不是静默给出结论。

对写自动化脚本的人，这条修复的含义是：**AVAILABLE 是强结论，UNKNOWN 是"再试一次"的信号**。官方 FAQ 也建议在自动化里把 UNKNOWN 当可重试状态处理，而不是当成不可用。

## CLI：一条命令的主线

安装走 Homebrew（v1.0.3 起已在 homebrew-core，随发布自动更新）或 cargo：

```bash
brew install domain-check
# 或
cargo install domain-check
```

基础用法围绕"一个基础名 + TLD 展开"：

```bash
# 查单个域名
domain-check example.com

# 基础名跨多个 TLD 展开
domain-check mystartup -t com,org,io,dev

# 用预设查一圈
domain-check myapp --preset startup --pretty

# 查所有已知 TLD（1,200+，需 bootstrap）
domain-check brand --all --batch
```

基础名自动展开成 `名字.TLD`，完整域名（FQDN）则原样检查不做展开——`domain-check startup test.com -t io` 查的是 `startup.io` 和 `test.com`。

### 11 个内置预设

预设是挑好的 TLD 组合，`--list-presets` 可查看完整清单：

| 预设 | 数量 | TLD |
|---|---|---|
| `startup` | 8 | com, org, io, ai, tech, app, dev, xyz |
| `popular` | 11 | com, net, org, io, ai, app, dev, tech, me, co, xyz |
| `classic` | 5 | com, net, org, info, biz |
| `enterprise` | 6 | com, org, net, info, biz, us |
| `tech` | 12 | io, ai, app, dev, tech, cloud, software, digital, codes, systems, network, solutions |
| `creative` | 10 | design, art, studio, media, photography, film, music, gallery, graphics, ink |
| `ecommerce` | 8 | shop, store, market, sale, deals, shopping, buy, bargains |
| `finance` | 9 | finance, capital, fund, money, investments, insurance, tax, exchange, trading |
| `web` | 9 | web, site, website, online, blog, page, wiki, host, email |
| `trendy` | 13 | xyz, online, site, top, icu, fun, space, click, website, life, world, live, today |
| `country` | 9 | us, uk, de, fr, ca, au, br, in, nl |

配置文件里定义的自定义预设优先于同名内置预设——想改 `startup` 的含义，直接在配置里定义一个同名预设即可。预设名大小写不敏感。

### 域名生成：模式与前后缀

`--pattern` 支持三种通配符（注意这不是完整正则）：`\d` 展开为 0-9，`\w` 展开为 a-z 加连字符（不出现在首尾），`?` 展开为数字加字母加连字符。`--prefix`/`--suffix` 做前后缀排列，裸名默认包含在组合里。

```bash
# 预览 test0.com 到 test9.com（不发任何网络请求）
domain-check --pattern "app\d" -t com --dry-run

# get、try 前缀 × hub、ly 后缀 × com、io
domain-check myapp --prefix get,try --suffix hub,ly -t com,io --dry-run
```

组合数量容易失控（`\w\w\w -t com` 就是近两万个域名），所以超过 5,000 个域名时交互终端会先请求确认，`--yes` 或 `--force` 跳过，非 TTY 环境（管道、CI）本来就不会提示。

## 五种输出格式

同一个结果有五种出口，按下游需求选：

**默认**——每域名单行，彩色状态，适合终端：

```text
myapp.com TAKEN
myapp.io AVAILABLE
myapp.dev TAKEN
```

**Pretty（`--pretty`）**——按状态分组，带汇总栏，适合人工审查：

```text
domain-check v1.0.3 — Checking 8 domains
Preset: startup | Concurrency: 20

── Available (3) ──────────────────────────────
  rustcloud.org
  rustcloud.ai
  rustcloud.app

── Taken (5) ──────────────────────────────────
  rustcloud.com
  rustcloud.io
  ...

8 domains in 0.8s  |  3 available  |  5 taken  |  0 unknown
```

**JSON（`--json`）**——结构化输出，字段以 `types.rs` 的 serde 定义为准：`domain`、`available`（true/false/null 三态）、`method_used`（小写的 `rdap`/`whois`/`bootstrap`/`unknown`）、按需出现的 `check_duration`、`info` 和 `error_message`：

```json
[
  {
    "domain": "example.com",
    "available": false,
    "method_used": "rdap",
    "check_duration": { "secs": 0, "nanos": 234567890 }
  }
]
```

**CSV（`--csv`）**——表头为 `domain,available,registrar,created,expires,method`，适合导入表格或数据库：

```csv
domain,available,registrar,created,expires,method
example.com,false,Example Inc.,1995-08-14,2025-08-13,rdap
startup.org,true,-,-,-,rdap
```

**Info（`--info`）**——附带注册人、日期与状态码，买域名前的尽调用它：

```bash
domain-check google.com --info
# google.com TAKEN (Registrar: MarkMonitor Inc., Created: 1997-09-15, Expires: 2028-09-14)
```

要注意 README 里的 JSON/CSV 示例字段（`method`、`domain,status,method` 表头）已经滞后于源码，写脚本时以 `--json` 的实际输出为准。

## 配置系统：三层来源，一条优先级链

TOML 配置文件的查找顺序是 `./domain-check.toml` → `~/.domain-check.toml` → `~/.config/domain-check/config.toml`：

```toml
[defaults]
concurrency = 25
preset = "startup"
pretty = true
timeout = "8s"
bootstrap = true

[custom_presets]
my_startup = ["com", "io", "ai", "dev", "app"]

[generation]
prefixes = ["get", "my"]
suffixes = ["hub", "ly"]

[output]
default_format = "pretty"
csv_headers = true
```

所有 CLI 选项几乎都有对应的 `DC_*` 环境变量（完整 14 个：`DC_CONCURRENCY`、`DC_PRESET`、`DC_TLD`、`DC_PRETTY`、`DC_TIMEOUT`、`DC_BOOTSTRAP`、`DC_WHOIS_FALLBACK`、`DC_DETAILED_INFO`、`DC_JSON`、`DC_CSV`、`DC_FILE`、`DC_CONFIG`、`DC_PREFIX`、`DC_SUFFIX`）。两点细节值得知道：`DC_TIMEOUT` 没有对应的 CLI flag——超时只能走配置文件或环境变量；`--pattern` 被刻意排除在配置之外，官方的理由是模式是每次探索性的输入，不适合做成持久默认值。

生效优先级从高到低：CLI 参数 > 环境变量 > 项目配置 > 用户全局配置 > XDG 配置 > 内置默认。用 `--verbose` 可以看到实际加载了哪份配置文件。

## 自动化与 CI

CI 场景的关键是"无提示、可解析、可复现"：

```bash
# 结构化输出
domain-check --file required-domains.txt --json

# 管道过滤可用域名
domain-check --pattern "app\d" -t com --yes --json \
  | jq '.[] | select(.available==true)'

# 大批量：高并发 + 流式 + 无提示
domain-check --file huge-list.txt --all --force --yes --csv > results.csv
```

行为保证来自四条设计：`--yes`/`--force` 跳过一切确认；非 TTY 环境永不提示；进度 spinner 走 stderr，stdout 只留干净的结果数据；`--no-bootstrap` 可以关掉联网引导，让检查只针对 32 个硬编码 TLD，行为完全确定。

并发默认 20，上限 100（`-c/--concurrency`）。大批量建议配合 `--streaming`（结果完成一个输出一个）或 `--batch`（收集完统一输出，spinner 等待），前者要实时反馈，后者要稳定排序。

## MCP 服务器：给 AI Agent 用的同一引擎

```bash
cargo install domain-check-mcp

# 接入 Claude Code
claude mcp add domain-check -- domain-check-mcp
```

接入后直接用自然语言问 Agent："Is coolstartup.com available?" 或 "Check mybrand across the startup preset"。官方验证过的客户端覆盖 Claude Code、Claude Desktop、VS Code Copilot、Cursor、Windsurf、JetBrains、OpenAI Codex CLI 与 Gemini CLI，任何支持 stdio 的 MCP 客户端都能接。

6 个工具全部只读、幂等，错误以工具内容（而非协议错误）返回，Agent 能读到错误信息并自行调整：

| 工具 | 作用 | 关键参数 |
|---|---|---|
| `check_domain` | 查单个完整域名 | `domain`（必填） |
| `check_domains` | 并发批量查询 | `domains`（必填）、`concurrency`（默认 20，批上限 500） |
| `check_with_preset` | 基础名按预设查一圈 | `base_name`、`preset`（均必填） |
| `generate_names` | 按模式/前后缀生成候选 | `pattern`、`base_names`、`prefixes`/`suffixes`、`tlds` |
| `list_presets` | 列出预设与完整 TLD 清单 | 无 |
| `domain_info` | 注册人、日期、域名服务器、状态码 | `domain`（必填） |

安全上限：批量最多 500 个域名，模式生成最多 100,000 个名字。调试用 `RUST_LOG=domain_check_mcp=debug`（日志走 stderr，stdout 留给 JSON-RPC），或用 MCP Inspector 交互测试：`npx @modelcontextprotocol/inspector domain-check-mcp`。GitHub release 还附带 `.mcpb` 安装包并自动发布到官方 MCP Registry。

## Rust 库：直接嵌进服务

```toml
[dependencies]
domain-check-lib = "1.0.3"
tokio = { version = "1", features = ["rt-multi-thread", "macros"] }
```

```rust
use domain_check_lib::DomainChecker;

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let checker = DomainChecker::new();
    let result = checker.check_domain("example.com").await?;

    match result.available {
        Some(true) => println!("{} is AVAILABLE", result.domain),
        Some(false) => println!("{} is TAKEN", result.domain),
        None => println!("{} status is UNKNOWN", result.domain),
    }

    Ok(())
}
```

`available` 是 `Option<bool>`——`None` 就是 UNKNOWN，类型系统逼你处理三态，这对自动化代码是好事。批量走 `check_domains(&domains)`，流式走 `check_domains_stream(&domains)`（`futures_util::Stream`），配置通过 `CheckConfig::default().with_concurrency(20).with_detailed_info(true)` 注入。纯异步 Rust（tokio + reqwest），没有 OpenSSL 依赖，交叉编译省心。

## 任务流：一次创业命名的完整路径

把上面的能力串成一个真实场景——为新产品 `rustcloud` 找名字：

```bash
# 1. 用生成模式扩展候选：rustcloud、getrustcloud、rustcloudhub……
domain-check rustcloud --prefix get,try --suffix hub,app -t com,io,dev --dry-run

# 2. 数量确认后真查（非交互可加 --yes），按 startup 预设的核心 TLD 查
domain-check rustcloud --prefix get,try --suffix hub,app -t com,io,dev --yes --json

# 3. 对可用候选查注册详情，确认不是"即将到期捡漏"的陷阱
domain-check getrustcloud.io --info

# 4. 团队评审用的 CSV 报表
domain-check rustcloud --preset startup --csv > name-options.csv
```

第三步是容易省略但最不该省的一步：`--info` 的到期日期能区分"从未注册"和"上一次注册即将到期"，两者的抢注风险完全不同。

品牌保护审计是同一套动作的另一个方向：`domain-check mybrand --all --batch --json > audit.json` 对全部 1,200+ TLD 做一遍扫描，放进 cron 定期跑，新出现的抢注会直接体现在 JSON diff 里。

## 可靠性边界

三类限制要在设计工作流时心里有数：

- **UNKNOWN 是常态的一部分**。超时、临时网络故障、注册表响应异常都会产生 UNKNOWN。v1.0.2 之后协议语义趋于保守（存疑即 UNKNOWN），官方 FAQ 明确建议自动化里把 UNKNOWN 当可重试信号。
- **WHOIS 回退的质量因注册表而异**。RDAP 结构化解析可靠，WHOIS 文本解析是尽力而为；`~189` 个无 RDAP 的 ccTLD 主要走这条路，结果可信度低于 RDAP 路径。重要决策前对照注册局官方查询复核。
- **检查结果不等于可注册**。可用性是查询时刻的快照，注册局保留、溢价、商标争议都不在检查范围内；`--info` 的注册人信息能辅助判断，但不能替代注册流程本身。

协议级调试有专门开关：`--debug` 显示发现步骤与耗时，`DOMAIN_CHECK_DEBUG_RDAP=1` 环境变量输出 RDAP 请求细节（v1.0.2 起协议调试信息只走这个环境变量，`--debug` 不含）。

## 常见问题排查

**结果大量 UNKNOWN**：先用 `--debug` 看卡在哪个协议；批量场景调大超时（`DC_TIMEOUT=15s` 或配置文件 `[defaults] timeout`）并降低并发；CI 里固定行为用 `--batch --json --yes`。注意没有 `--force-rdap` 这样的 flag——协议控制只有 `--no-whois`（关回退）和 `--no-bootstrap`（关引导）两个开关。

**MCP 服务器连不上**：`which domain-check-mcp` 确认在 PATH 里；不在就 `cargo install domain-check-mcp` 重装；配置后用 MCP Inspector（`npx @modelcontextprotocol/inspector domain-check-mcp`）手动走一遍 initialize → tools/list，能列出 6 个工具说明服务本身正常，问题在客户端配置。

**批量检查慢**：先看并发是不是默认值 20（`-c 100` 拉满）；`--streaming` 让结果边查边出；用 `--preset` 或 `-t` 收窄 TLD 范围比全量 `--all` 快一个量级；超过 5,000 条的列表记得 `--yes`，否则交互终端会卡在确认提示。

**自定义预设没生效**：确认配置文件在三个查找位置之一，`--list-presets` 看预设是否被加载；预设名大小写不敏感，但同名自定义预设会覆盖内置预设——如果 `--preset startup` 的结果和预期不符，先检查是不是配置里定义过同名预设。

## 采用建议

按需求从轻到重：

1. **偶尔查几个域名**：直接 `brew install domain-check`，预设加 `--pretty` 就够，不需要配置文件。
2. **批量命名/品牌审计**：生成模式 + `--file` + JSON/CSV 输出，写进 cron 或 CI；把 UNKNOWN 按可重试处理。
3. **产品里嵌域名检查**（注册引导页、SaaS 租户自定义域名）：用 `domain-check-lib`，三态返回值天然适配服务端逻辑。
4. **AI Agent 工作流**：MCP 服务器一条命令接入，只读工具没有副作用风险，适合让 Agent 自主调用。

反之，如果你的场景是域名投资级的精确判断（竞价、续费、法律状态），任何基于 RDAP/WHOIS 的检查工具都只是初步过滤，最终都要落到注册局官方查询——这不是 Domain Check 的短板，是这类工具共同的边界。

## 相关资源

| 资源 | 链接 |
|---|---|
| GitHub 仓库 | [github.com/saidutt46/domain-check](https://github.com/saidutt46/domain-check) |
| CLI 完整参考 | [docs/CLI.md](https://github.com/saidutt46/domain-check/blob/main/docs/CLI.md) |
| 自动化指南 | [docs/AUTOMATION.md](https://github.com/saidutt46/domain-check/blob/main/docs/AUTOMATION.md) |
| FAQ | [docs/FAQ.md](https://github.com/saidutt46/domain-check/blob/main/docs/FAQ.md) |
| MCP 服务器 | [domain-check-mcp/README.md](https://github.com/saidutt46/domain-check/blob/main/domain-check-mcp/README.md) |
| Rust 库文档 | [docs.rs/domain-check-lib](https://docs.rs/domain-check-lib) |
| RDAP 协议 | [IETF RFC 9082](https://www.rfc-editor.org/rfc/rfc9082.html) |
| WHOIS 协议 | [IETF RFC 3912](https://www.rfc-editor.org/rfc/rfc3912.html) |
