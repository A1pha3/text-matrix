---
title: "codex-shim：让Codex Desktop支持任意模型的本地产权API垫片"
date: 2026-05-22T20:05:00+08:00
slug: "codex-shim-local-responses-api-shim-codex-desktop"
description: "codex-shim是一个Python本地服务器，伪装成OpenAI Responses API端点，让Codex Desktop能够使用用户在Factory BYOK中配置的任何模型（包括ChatGPT GPT-5.5），无需重新编译Codex。"
draft: false
categories: ["技术笔记"]
tags: ["Codex", "API垫片", "OpenAI", "本地开发", "Python"]
---

# codex-shim：让Codex Desktop支持任意模型的本地产权API垫片

codex-shim 是一个轻量级 Python 服务器，将自己伪装成 OpenAI Responses API 端点，把请求路由到用户配置的任意模型。2026-05-22创建，已获77星。

## 核心判断

Codex Desktop 的模型选择器只显示 Statsig 服务端白名单里的模型。codex-shim 的思路是：不破解 Codex，而是在本地跑一个垫片服务器，把用户自定义模型"伪装"成 Codex 认识的 Responses API 端点。

## 工作原理

```
Codex Desktop
     │
     │ 认为自己连的是 OpenAI Responses API
     ↓
codex-shim (127.0.0.1:8765)
     │
     ├── 读取 ~/.factory/settings.json（Factory BYOK 配置）
     ├── 生成 catalog（模型 slug 列表）
     └── 路由请求到对应的 upstream
           ├── OpenAI /v1/chat/completions
           ├── Anthropic /v1/messages
           └── ChatGPT backend (/backend-api/codex/responses)
```

## 安装

```bash
git clone https://github.com/<you>/codex-shim ~/Documents/codex-shim
cd ~/Documents/codex-shim
python3 -m pip install --user aiohttp pytest

# 创建符号链接
ln -s "$PWD/bin/codex-shim" ~/.local/bin/codex-shim
ln -s "$PWD/bin/codex-app"  ~/.local/bin/codex-app
ln -s "$PWD/bin/codex-model" ~/.local/bin/codex-model
```

要求：Python 3.11+

## 快速开始

### 步骤1：生成catalog并启动垫片

```bash
codex-shim generate          # 读取 ~/.factory/settings.json，写入 catalog
codex-shim start             # 后台服务，监听 127.0.0.1:8765
codex-shim list              # 显示生成的 slug 和 upstream 路由
codex-shim status            # 健康检查
```

### 步骤2：启动 Codex 并指向垫片

```bash
codex-shim app .             # 只对这个启动实例生效，不修改全局配置
```

Codex Desktop 现在能看到 ~/.factory/settings.json 里的所有模型，外加一个可选的 `OpenAI GPT-5.5 (ChatGPT)`。

### 步骤3：切换活跃模型（可选）

```bash
codex-model list
codex-model openai-gpt-5-5    # 切换到 GPT-5.5
codex-app                     # 用新默认模型重新启动 Codex
```

## 支持的 Provider

| Provider | Upstream API |
|---|---|
| `openai` | OpenAI `/v1/chat/completions` |
| `anthropic` | Anthropic `/v1/messages` |
| `generic-chat-completion-api` | 任意 OpenAI 格式的 chat completions |

## Settings 文件格式

垫片读取 `~/.factory/settings.json`（Factory BYOK 格式）：

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
    },
    {
      "model": "deepseek-v4-pro",
      "provider": "anthropic",
      "baseUrl": "https://api.deepseek.com/anthropic",
      "apiKey": "…",
      "displayName": "DeepSeek V4 Pro",
      "noImageSupport": true
    }
  ]
}
```

API Key 永远不复制到 catalog，每次请求实时读取。

## Picker Patch（macOS Codex Desktop 专用）

如果 Codex 的模型选择器只显示"default"而不显示 catalog 条目，还需要对 `app.asar` 打补丁。

这个 patch 关闭 Statsig 服务端白名单检查，让本地 `hidden` 标志生效：

```bash
APP=/Applications/Codex.app
sudo cp -R "$APP" "$APP.unpatched-$(date +%Y%m%d-%H%M%S)"

# 1. 提取 ASAR
cd /tmp && rm -rf codex-asar-patch && mkdir codex-asar-patch && cd codex-asar-patch
npx --yes @electron/asar extract "$APP/Contents/Resources/app.asar" extracted

# 2. 补丁
PATCH_FILE=$(grep -RIl 'useHiddenModels' extracted/webview/assets/model-queries-*.js | head -n1)
sed -i.bak -E 's/let u=c\.useHiddenModels&&o!==`amazonBedrock`,d;/let u=!1,d;/' "$PATCH_FILE"

# 3. 重新打包
npx --yes @electron/asar pack extracted app.asar.new
sudo cp app.asar.new "$APP/Contents/Resources/app.asar"

# 4. 修复 ElectronAsarIntegrity（ASAR头部哈希校验）
python3 - "$APP/Contents/Resources/app.asar" <<'PY'
import struct, hashlib, sys
with open(sys.argv[1], 'rb') as f:
    data_size, header_size, _, json_size = struct.unpack('<4I', f.read(16))
    header_json = f.read(json_size)
print(hashlib.sha256(header_json).hexdigest())
PY
# 用输出更新 Info.plist 的 ElectronAsarIntegrity 字段...

# 5. 重签名
sudo codesign --force --deep --sign - "$APP"

# 6. 启动
open "$APP"
```

**回滚：** `sudo rm -rf "$APP" && sudo mv "$APP.unpatched-…" "$APP"`

## ChatGPT GPT-5.5 Passthrough

如果本地有 `~/.codex/auth.json`（auth_mode: chatgpt），垫片会暴露一个 `openai-gpt-5-5` slug，直连 `https://chatgpt.com/backend-api/codex/responses`。

## 适用边界

**适合：**
- 想在 Codex Desktop 用自定义模型（OpenAI / Anthropic / DeepSeek / Gemini 等）
- 想把 ChatGPT 订阅的 GPT-5.5 和其他模型并排显示
- 不希望改全局 Codex 配置

**不适合：**
- 非 macOS Codex Desktop（patch 不适用，但垫片本身可用）
- 需要深度 Codex 集成（非垫片能做到的）

## 结论

codex-shim 是一个干净的解决方案：不用 fork Codex，不用改配置，用垫片解决服务端口问题。对于想统一开发环境的人（比如同时用 Factory 自定义模型和 ChatGPT），这个工具值得一试。