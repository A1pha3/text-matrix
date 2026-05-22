---
title: "codex-shim：让 Codex Desktop 支持任意自定义模型"
date: "2026-05-23T03:15:00+08:00"
slug: "codex-shim-local-responses-api-shim-guide"
description: "codex-shim 是一个本地 Python 服务，通过模拟 OpenAI Responses API 让 Codex Desktop 能够调用用户在 Factory.ai 配置的任意 BYOK 自定义模型，包括 OpenAI、Anthropic、DeepSeek 等。它还支持将 ChatGPT 订阅的 GPT-5.5 以 Passthrough 方式接入 Codex 模型选择器，无需重新编译即可扩展 Codex 的模型支持范围。"
draft: false
categories: ["技术笔记"]
tags: ["Codex", "OpenAI", "AI工具", "Python", "本地代理"]
---

# codex-shim：让 Codex Desktop 支持任意自定义模型

## 核心判断

codex-shim 是一个本地 Python 服务，它做的事不复杂：**模拟一个 Responses API 端点，接收 Codex Desktop 的请求，再按上游 provider 的格式转发出去。** 这样 Codex Desktop 在不自备 API key 的情况下，也能调用用户在 Factory.ai 配置的各种自定义模型——OpenAI、Anthropic、DeepSeek、Z.ai 等都行，还能顺带把 ChatGPT 订阅的 GPT-5.5 接入模型选择器。

这个方案的价值在于**：Codex Desktop 有自己的服务端 Statsig 白名单，普通用户没法自由添加模型；codex-shim 绕过了这层限制，让 picker 里出现所有你在 Factory 配置过的模型。**

---

## 适用读者

- 已经在用 [Factory.ai](https://factory.ai) 的 BYOK 功能配置了自定义模型，想在 Codex Desktop 里直接调用的人。
- 希望在 Codex 的模型选择器里看到 GPT-5.5（ChatGPT 订阅）的人。
- 对 Codex Desktop 的模型路由机制感兴趣，想本地搭建一套类似代理的开发者。

---

## 系统结构概览

codex-shim 的架构非常直接：它是一个跑在 `127.0.0.1:8765` 的本地 Python 服务，Codex Desktop 把请求发到这里，shim 再根据请求的 slug 查到对应上游配置，最终翻译请求格式后转发。

```
Codex Desktop ── /v1/responses ──▶ codex-shim (127.0.0.1:8765)
                                     │
                                     ├── slug "openai-gpt-5-5"
                                     │       └─▶ chatgpt.com/backend-api/codex/responses
                                     │           (使用 ChatGPT 订阅的 access_token)
                                     │
                                     ├── provider "openai" / "generic-…"
                                     │       └─▶ baseUrl/chat/completions
                                     │           (Authorization: Bearer apiKey)
                                     │
                                     └── provider "anthropic"
                                             └─▶ baseUrl/messages
                                                 (x-api-key: apiKey)
```

关键点：**shim 不存储任何 API key**，这些 credentials 始终在你本地的 `~/.factory/settings.json` 文件里，shim 每次收到请求时实时读取。catalog 文件里只写入 slug 路由表，不含任何敏感信息。

---

## 支持的上游类型

| provider 值 | 对应上游 API |
|---|---|
| `openai` | OpenAI `/v1/chat/completions` |
| `generic-chat-completion-api` | 任意兼容 OpenAI chat completions 格式的 API |
| `anthropic` | Anthropic `/v1/messages` |

其中 `anthropic` 类型的上游（如 Claude、DeepSeek）如果支持 extended-thinking 块，会通过 `reasoning.encrypted_content` 做往返传输。

---

## 安装步骤

### 环境要求

- Python 3.11+
- Codex Desktop 0.133.0-alpha.1（macOS arm64 已测试）
- Linux/Windows 用户可跳过 ASAR patch 部分

### 安装命令

```bash
git clone https://github.com/<you>/codex-shim ~/Documents/codex-shim
cd ~/Documents/codex-shim
python3 -m pip install --user aiohttp pytest    # 唯一运行时依赖是 aiohttp
ln -s "$PWD/bin/codex-shim" ~/.local/bin/codex-shim
ln -s "$PWD/bin/codex-app"  ~/.local/bin/codex-app
ln -s "$PWD/bin/codex-model" ~/.local/bin/codex-model
```

### 生成模型目录并启动 shim

```bash
codex-shim generate          # 读取 ~/.factory/settings.json，写入 catalog
codex-shim start             # 后台守护进程，监听 127.0.0.1:8765
codex-shim list              # 查看生成的 slug 和上游路由
codex-shim status            # 健康检查 + 模型数量
```

`codex-shim generate` 会读取你在 Factory.ai 配置的 `customModels` 列表（包括 model 名、provider、baseUrl、apiKey、displayName 等），生成一份不含真实 apiKey 的路由 catalog 存到 `.codex-shim/` 目录。

### 启动 Codex 并接入 shim

```bash
codex-shim app .             # 启动 Codex，通过 -c 参数注入 shim 配置
```

这个命令只针对本次启动生效，不会改动你本地的 `~/.codex/config.toml`。Codex Desktop 启动后，模型选择器里应该能看到你在 Factory 配置的所有模型，外加一个 `OpenAI GPT-5.5 (ChatGPT)` 条目。

如果模型选择器只显示 "default" 而看不到 catalog 条目，需要额外执行下面的 **Picker Patch**。

---

## 可选步骤：Picker Patch（macOS）

Codex Desktop 的 Statsig 配置里有一个服务端白名单 `use_hidden_models: true`，所有不在白名单里的自定义模型 slug 都会被隐藏，即使 catalog 里有记录也不会渲染到 picker 里。

Picker Patch 的原理是用 ASAR 包里的 JS 文件打补丁，将白名单校验逻辑关闭，让 picker 只看本地 `hidden` 标志（shim 的 catalog 不设置这个标志）。

### 操作步骤

> ⚠️ **操作前务必备份原文件**，教程里每次操作都有备份指令，不要跳过。

```bash
APP=/Applications/Codex.app
sudo cp -R "$APP" "$APP.unpatched-$(date +%Y%m%d-%H%M%S)"
```

#### 第 1 步：解压 ASAR 包

```bash
cd /tmp && rm -rf codex-asar-patch && mkdir codex-asar-patch && cd codex-asar-patch
npx --yes @electron/asar extract "$APP/Contents/Resources/app.asar" extracted
```

#### 第 2 步：修改 picker 过滤逻辑

```bash
PATCH_FILE=$(grep -RIl 'useHiddenModels' extracted/webview/assets/model-queries-*.js | head -n1)
sed -i.bak -E 's/let u=c\.useHiddenModels&&o!==`amazonBedrock`,d;/let u=!1,d;/' "$PATCH_FILE"
diff "$PATCH_FILE.bak" "$PATCH_FILE" || true
rm "$PATCH_FILE.bak"
```

确认只有一处修改后，进入第 3 步。

#### 第 3 步：重新打包 ASAR

```bash
npx --yes @electron/asar pack extracted app.asar.new
sudo cp app.asar.new "$APP/Contents/Resources/app.asar"
```

#### 第 4 步：修复 ASAR 完整性哈希

Electron 的 `ElectronAsarIntegrity` 字段存储的是 ASAR JSON 头部的 SHA-256，而不是整个文件。先计算新哈希：

```bash
HEADER_HASH=$(python3 - "$APP/Contents/Resources/app.asar" <<'PY'
import struct, hashlib, sys
with open(sys.argv[1], 'rb') as f:
    data_size, header_size, _, json_size = struct.unpack('<4I', f.read(16))
    header_json = f.read(json_size)
print(hashlib.sha256(header_json).hexdigest())
PY
)
echo "new header hash: $HEADER_HASH"
```

#### 第 5 步：更新 Info.plist

```bash
sudo /usr/libexec/PlistBuddy -c \
  "Set :ElectronAsarIntegrity:Resources/app.asar:hash $HEADER_HASH" \
  "$APP/Contents/Info.plist"
```

#### 第 6 步：重新签名

```bash
sudo codesign --force --deep --sign - "$APP"
```

#### 第 7 步：启动

```bash
open "$APP"
```

回滚操作：

```bash
sudo rm -rf "$APP" && sudo mv "$APP.unpatched-…" "$APP"
```

---

## 切换默认模型

shim 提供了独立的 `codex-model` 命令用来管理 Codex 的默认模型：

```bash
codex-model list              # 列出所有可用 slug
codex-model openai-gpt-5-5   # 设置某个 slug 为默认模型
codex-app                     # 用新默认模型重新启动 Codex
```

---

## 自定义配置文件

shim 默认读取 `~/.factory/settings.json`，但也支持任意自定义 JSON 文件：

```bash
codex-shim --settings /path/to/my-models.json generate
codex-shim --settings /path/to/my-models.json start
```

配置文件格式（Factory.ai 格式）：

```json
{
  "customModels": [
    {
      "model": "gpt-5.5",
      "provider": "openai",
      "baseUrl": "https://api.openai.com/v1",
      "apiKey": "sk-…",
      "displayName": "OpenAI GPT-5.5",
      "maxContextLimit": 400000
    },
    {
      "model": "claude-opus-4-7-20251109",
      "provider": "anthropic",
      "baseUrl": "https://api.anthropic.com/v1",
      "apiKey": "sk-ant-…",
      "displayName": "Claude Opus 4.7"
    }
  ]
}
```

`apiKey` 只存在于你的 settings 文件里，shim 生成 catalog 时不会把这些 key 写进去。

---

## ChatGPT GPT-5.5 Passthrough

如果你有付费 ChatGPT 订阅且 `~/.codex/auth.json` 里 `auth_mode: chatgpt`，shim 在 `codex-shim generate` 时会自动在 catalog 里写入一个名为 `openai-gpt-5-5` 的 synthetic slug，显示为 `OpenAI GPT-5.5 (ChatGPT)`。

这个 slug 不走 Factory，直接代理请求到 `https://chatgpt.com/backend-api/codex/responses`，使用你在 `auth.json` 里保存的 ChatGPT access_token。走的是你自己的 ChatGPT 订阅配额。

如果不想看到这个条目，从生成的 catalog 文件里删除 slug 为 `openai-gpt-5-5` 的那行即可，或者设置环境变量 `CODEX_SHIM_DISABLE_CHATGPT=1`（TODO）。

---

## MCP 工具转发

Codex Desktop 会将三个通用 MCP 工具转发给每个模型：

- `list_mcp_resources`
- `list_mcp_resource_templates`
- `read_mcp_resource`

codex-shim 不对这些 MCP 工具做任何转换，直接透传。上游模型收到的是与内置 OpenAI 模型相同的 MCP 工具列表——模型需要主动调用 `list_mcp_resources` 来发现可用的 MCP 资源。这是 Codex 客户端的行为，不是 shim 的限制。

---

## 命令速查

| 命令 | 作用 |
|---|---|
| `codex-shim generate` | 从 settings.json 重新生成 catalog |
| `codex-shim start` | 启动本地 shim 守护进程 |
| `codex-shim stop` | 停止守护进程 |
| `codex-shim restart` | 重启守护进程 |
| `codex-shim status` | 健康检查 + 模型计数 |
| `codex-shim list` | 列出生成的所有 slug 和路由 |
| `codex-shim model list` | 列出当前可用的模型 slug |
| `codex-shim model use <slug>` | 设置 Codex 默认模型 |
| `codex-shim app [path]` | 通过 shim 启动 Codex Desktop |
| `codex-shim codex -- <args>` | 通过 shim 执行 codex CLI |

所有命令支持 `--settings <path>` 和 `--port <port>` 参数。

---

## 文件结构

```
codex_shim/             Python 源码（server + cli + 格式翻译）
bin/codex-shim          主入口
bin/codex-app           launch Codex 的快捷命令
bin/codex-model         切换默认模型的快捷命令
.codex-shim/            生成的 catalog、配置、日志、PID（gitignored）
tests/                  pytest 测试套件
```

shim 不会修改 `~/.codex/config.toml`，所有配置通过 `-c key=value` 参数在每次启动时内联注入。

---

## 采用建议

- 如果你只用 Codex 内置模型，不需要这个项目。
- 如果你在 Factory.ai 配置了多款自定义模型，希望在 Codex Desktop 的 picker 里统一管理，这是一个开箱即用的方案。
- Picker Patch 涉及 ASAR 打包和代码签名，适合愿意花时间折腾 macOS 的用户；Linux/Windows 用户可直接跳过这步。
- shim 本身是单文件依赖（只有 aiohttp），不需要复杂的部署，适合作为个人本地工具使用。

---

## 项目信息

- GitHub：[0xSero/codex-shim](https://github.com/0xSero/codex-shim)
- Stars：181
- 语言：Python 3.11+
- 依赖：aiohttp
- License：MIT
- 测试环境：Codex Desktop 0.133.0-alpha.1，macOS arm64