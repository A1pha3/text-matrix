+++
date = '2026-04-13T23:51:22+08:00'
draft = false
title = 'Domain Check：通用域名可用性检查引擎'
slug = 'domain-check-universal-domain-checker-guide'
description = 'Domain Check 是一个通用域名可用性检查引擎，支持 CLI、Rust 库和 MCP 服务器三种使用方式，覆盖 1200+ TLD。'
categories = ['技术笔记']
tags = ['工具', 'CLI', 'Rust', 'MCP']
+++

# Domain Check：通用域名可用性检查引擎

**Domain Check** 是一个通用域名可用性检查引擎，支持 CLI、Rust 库和 MCP 服务器三种使用方式。项目地址：[saidutt46/domain-check](https://github.com/saidutt46/domain-check)

## 为什么选择 Domain Check？

### 1,200+ TLDs 开箱即用

IANA自动引导加载完整注册表，无需任何配置。32个硬编码TLD可在离线环境下作为备用：

```bash
# 检查单个域名
domain-check example.com

# 跨多个TLD检查
domain-check mystartup -t com,org,io,dev
```

### 双协议引擎：RDAP + WHOIS

采用RDAP优先策略，自动回退到WHOIS。覆盖约189个缺乏RDAP支持的ccTLD（如`.es`、`.co`、`.eu`、`.jp`）：

| 协议 | 优先级 | 覆盖率 |
|------|--------|--------|
| RDAP | 首选 | ~85% TLDs |
| WHOIS | 备用 | 覆盖RDAP缺失的ccTLDs |

### 高性能：100并发检查

最多支持100个并发检查，流式输出结果，2.7MB二进制文件：

```bash
# 高并发批量检查
domain-check --file domains.txt --concurrency 100 --streaming
```

### 域名生成与模式扩展

支持正则模式生成、前缀/后缀组合，dry-run预览：

```bash
# 预览生成的域名（不执行检查）
domain-check --pattern "app\d" -t com --dry-run

# 带前缀后缀生成
domain-check myapp --prefix get,try --suffix hub,ly -t com,io
```

## 11个精选预设

| 预设 | TLDs | 适用场景 |
|------|------|----------|
| startup | com, org, io, ai, tech, app, dev, xyz | 科技创业公司 |
| popular | com, net, org, io, ai, app, dev, tech, me, co, xyz | 通用覆盖 |
| classic | com, net, org, info, biz | 传统gTLD |
| enterprise | com, org, net, info, biz, us | 企业和政府 |
| tech | io, ai, app, dev, tech, cloud, software +5 | 开发者工具 |
| creative | design, art, studio, media, photography +5 | 创意和媒体 |
| ecommerce | shop, store, market, sale, deals +3 | 电商零售 |
| finance | finance, capital, fund, money, investments +4 | 金融科技 |
| country | us, uk, de, fr, ca, au, br, in, nl | 国际市场 |

```bash
# 使用预设快速检查
domain-check coolname --preset startup --pretty

# 列出所有预设
domain-check --list-presets
```

## 四种输出格式

### 1. 默认输出（彩色单行）
```
myapp.com TAKEN
myapp.io AVAILABLE
myapp.dev TAKEN
```

### 2. Pretty格式（分组展示）
```
domain-check v0.9.1 — Checking 8 domains
Preset: startup | Concurrency: 20
── Available (3) ──────────────────────────────
rustcloud.org
rustcloud.ai
rustcloud.app
── Taken (5) ──────────────────────────────────
rustcloud.com
rustcloud.io
...

8 domains in 0.8s | 3 available | 5 taken | 0 unknown
```

### 3. JSON格式（供脚本处理）
```json
[
  { "domain": "myapp.com", "available": false, "method": "RDAP" },
  { "domain": "myapp.io", "available": true, "method": "RDAP" }
]
```

### 4. CSV格式（导入数据库）
```csv
domain,status,method
myapp.com,TAKEN,RDAP
myapp.io,AVAILABLE,RDAP
```

### 5. Info格式（注册信息）
```bash
domain-check target.com --info
# 输出：
# myapp.com TAKEN
# Registrar: Example Registrar, Inc.
# Created: 2015-03-12
# Expires: 2026-03-12
# Status: clientTransferProhibited
```

## 配置文件与环境变量

### TOML配置
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
```

配置查找顺序：`./domain-check.toml` > `~/.domain-check.toml` > `~/.config/domain-check/config.toml`

### 环境变量
```bash
DC_CONCURRENCY=50
DC_PRESET=startup
DC_TLD=com,io,dev
DC_PRETTY=true
DC_TIMEOUT=10s
DC_PREFIX=get,my
DC_SUFFIX=hub,ly
DC_FILE=domains.txt
```

## CI/自动化友好

```bash
# 非交互式结构化输出
domain-check --file required-domains.txt --json

# 管道到jq过滤可用域名
domain-check --pattern "app\d" -t com --yes --json \
  | jq '.[] | select(.available==true)'

# 大批量无提示运行
domain-check --file huge-list.txt --all --force --yes --csv > results.csv
```

**CI友好特性：**
- `--yes`/`--force` 跳过所有确认提示
- 非TTY环境自动不弹出提示
- `spinner`输出到stderr，stdout保持干净

## 三种使用方式

### 1. CLI (domain-check)

```bash
# 安装
brew install domain-check
# 或
cargo install domain-check

# 基础用法
domain-check example.com
domain-check myapp --preset startup --pretty
```

### 2. Rust库 (domain-check-lib)

```toml
[dependencies]
domain-check-lib = "1.0.2"
```

```rust
use domain_check_lib::DomainChecker;

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let checker = DomainChecker::new();
    let result = checker.check_domain("example.com").await?;
    println!("{} -> {:?}", result.domain, result.available);
    Ok(())
}
```

### 3. MCP服务器 (domain-check-mcp)

为AI Coding Agent提供域名检查工具，支持Claude Code、Codex、Cursor、VS Code Copilot等：

```bash
# 安装
cargo install domain-check-mcp

# 添加到Claude Code
claude mcp add domain-check -- domain-check-mcp
```

**6个可用工具：**
- `check_domain` - 检查单个域名
- `check_domains` - 批量检查
- `check_with_preset` - 使用预设检查
- `generate_names` - 生成域名
- `list_presets` - 列出所有预设
- `domain_info` - 获取域名详细信息

```
"Is coolstartup.com available?"
"Check mybrand across the startup preset"
```

## 使用场景

### 创业公司命名
```bash
domain-check coolname --preset startup --pretty
```

### 品牌保护审计
```bash
domain-check mybrand --all --json > audit.json
```

### 购买前验证
```bash
domain-check target.com --info
```

### 批量流水线
```bash
domain-check --file ideas.txt --preset tech --csv > results.csv
```

## 可靠性说明

域名状态依赖网络和注册表响应。临时错误可能导致`UNKNOWN`状态。

- WHOIS输出标准化程度不如RDAP，解析质量因注册表而异
- 建议CI工作流中使用明确标志固定行为：`--batch`、`--json`、`--no-bootstrap`、`--concurrency`

## 项目结构

```
domain-check/
├── .github/workflows/     # GitHub Actions
├── assets/               # 资源文件
├── docs/                 # 详细文档
├── domain-check-lib/     # Rust库
├── domain-check-mcp/     # MCP服务器
├── domain-check/         # CLI主程序
└── scripts/              # 工具脚本
```

## 总结

Domain Check 是一个生产级的域名检查工具，核心优势：

| 特性 | 说明 |
|------|------|
| **覆盖率** | 1200+ TLDs，RDAP+WHOIS双协议 |
| **性能** | 100并发，流式输出，2.7MB二进制 |
| **灵活性** | 预设+自定义，4种输出格式 |
| **AI原生** | MCP服务器支持所有主流AI Coding Agent |
| **可靠性** | 离线备用32 TLD，CI友好 |

无论是手动命名研究、品牌保护审计，还是自动化流水线，Domain Check都能提供高效可靠的域名可用性检查能力。
