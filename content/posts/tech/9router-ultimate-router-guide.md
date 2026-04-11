# 9Router：1.5K Stars·Ultimate Router for Claude Code·多后端路由·本地模型网关·Ollama·Jan

## 一、项目概述

### 1.1 9Router 是什么

**9Router** 是 **decolua** 开发的** AI 模型路由器**，支持 Claude Code 和 Cursor，可以将提示路由到不同的 AI 后端，如 OpenAI、Anthropic、Deepseek、Grok 等。它还提供本地模型网关，支持 Ollama 和 Jan，实现离线工作和成本节省。

> "9Router is the ultimate router for Claude Code and Cursor. It allows you to route your prompts to different AI backends like OpenAI, Anthropic, Deepseek, Grok, and more."

### 1.2 核心数据

| 指标 | 数值 |
|------|------|
| Stars | **1.5k** ⭐ |
| Forks | 66 |
| 贡献者 | 2 (decolua, gaborkut) |
| 最新版本 | **2026-03-06** |
| 最新提交 | **2026-03-30** |
| 许可证 | MIT |
| 语言 | Python 93.5%, Shell 6.5% |

### 1.3 核心定位

```
┌─────────────────────────────────────────────────────────────┐
│                    9Router 核心定位                                      │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│   Claude Code / Cursor                                        │
│         ↓                                                     │
│   ┌─────────────────────────────────────────────────────┐   │
│   │                    9Router 路由器                              │   │
│   │                                                       │   │
│   │   ┌─────────┐  ┌─────────┐  ┌─────────┐           │   │
│   │   │ OpenAI  │  │Anthropic│  │ Deepseek│           │   │
│   │   │  GPT-4  │  │Claude 3 │  │         │           │   │
│   │   └─────────┘  └─────────┘  └─────────┘           │   │
│   │                                                       │   │
│   │   ┌─────────┐  ┌─────────┐  ┌─────────┐           │   │
│   │   │   Grok  │  │  Ollama │  │   Jan   │           │   │
│   │   │   xAI   │  │  本地模型│  │  本地模型│           │   │
│   │   └─────────┘  └─────────┘  └─────────┘           │   │
│   │                                                       │   │
│   │   ┌─────────────────────────────────────────┐       │   │
│   │   │        OpenAI Compatible API               │       │   │
│   │   └─────────────────────────────────────────┘       │   │
│   └─────────────────────────────────────────────────────┘   │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### 1.4 支持的 AI 提供商

| 提供商 | 模型 | 说明 |
|--------|------|------|
| **OpenAI** | GPT-4, GPT-4 Turbo, GPT-3.5 | OpenAI API |
| **Anthropic** | Claude 3 Opus, Sonnet, Haiku | Anthropic API |
| **Deepseek** | Deepseek Chat, Deepseek Coder | Deepseek API |
| **Grok** | Grok-1, Grok-2 | xAI API |
| **Ollama** | 所有 Ollama 支持的模型 | 本地模型 |
| **Jan** | 所有 Jan 支持的模型 | 本地模型 |
| **OpenAI Compatible** | 任何兼容 API 的模型 | 灵活扩展 |

## 二，技术架构

### 2.1 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                    9Router 系统架构                                    │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│   ┌─────────────────────────────────────────────────────┐   │
│   │                 客户端 (Claude Code / Cursor)                  │   │
│   │                 (设置 OPENAI_BASE_URL 等)                        │   │
│   └─────────────────────────────────────────────────────┘   │
│                           ↓                                   │
│   ┌─────────────────────────────────────────────────────┐   │
│   │                    9Router 核心                                 │   │
│   │   ┌─────────────┐  ┌─────────────┐  ┌─────────────┐       │   │
│   │   │   Router    │  │   Auth      │  │   Logger    │       │   │
│   │   │   路由      │  │   认证      │  │   日志      │       │   │
│   │   └─────────────┘  └─────────────┘  └─────────────┘       │   │
│   │   ┌─────────────┐  ┌─────────────┐                       │   │
│   │   │  Provider   │  │   Cache     │                       │   │
│   │   │   提供商    │  │   缓存      │                       │   │
│   │   └─────────────┘  └─────────────┘                       │   │
│   └─────────────────────────────────────────────────────┘   │
│                           ↓                                   │
│   ┌─────────────────────────────────────────────────────┐   │
│   │                    AI 后端                                      │   │
│   │   ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐   │   │
│   │   │ OpenAI  │  │Anthropic │  │ Deepseek │  │  Grok   │   │   │
│   │   └─────────┘  └─────────┘  └─────────┘  └─────────┘   │   │
│   │   ┌─────────┐  ┌─────────┐  ┌─────────┐               │   │
│   │   │ Ollama  │  │   Jan   │  │ Custom   │               │   │
│   │   └─────────┘  └─────────┘  └─────────┘               │   │
│   └─────────────────────────────────────────────────────┘   │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 项目结构

```
9router/
├── src/
│   └── 9router/
│       ├── __init__.py
│       ├── router.py          # 路由核心
│       ├── providers/
│       │   ├── __init__.py
│       │   ├── openai.py      # OpenAI 提供商
│       │   ├── anthropic.py    # Anthropic 提供商
│       │   ├── deepseek.py     # Deepseek 提供商
│       │   ├── grok.py         # Grok 提供商
│       │   ├── ollama.py      # Ollama 本地
│       │   └── jan.py          # Jan 本地
│       ├── auth.py            # 认证管理
│       ├── cache.py          # 响应缓存
│       └── logger.py         # 日志管理
├── tests/
│   ├── test_router.py
│   └── test_providers.py
├── examples/
│   ├── basic.py
│   ├── multi_provider.py
│   └── local_models.py
├── scripts/
│   └── setup.sh              # 安装脚本
├── docs/
│   └── README.md
├── .env.example              # 环境变量模板
├── pyproject.toml
└── README.md
```

### 2.3 核心组件

| 组件 | 说明 |
|------|------|
| **Router** | 路由核心，根据配置转发请求 |
| **Provider** | AI 提供商适配器 |
| **Auth** | API Key 认证管理 |
| **Cache** | 响应缓存，减少 API 调用 |
| **Logger** | 请求/响应日志 |

## 三，主要功能

### 3.1 核心特性

| 特性 | 说明 |
|------|------|
| **多后端支持** | OpenAI、Anthropic、Deepseek、Grok、Ollama、Jan |
| **本地模型网关** | Ollama + Jan 实现离线工作 |
| **统一 API** | OpenAI 兼容 API，易于集成 |
| **成本节省** | 本地模型减少 API 费用 |
| **简单配置** | 环境变量配置，无需代码修改 |
| **缓存机制** | 减少重复 API 调用 |

### 3.2 使用场景

```
┌─────────────────────────────────────────────────────────────┐
│                    使用场景                                              │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│   💰 成本优化                                                  │
│   ┌─────────────────────────────────────────────────────┐   │
│   │ OpenAI GPT-4: $0.03/1K tokens                        │   │
│   │ Ollama (本地): $0/1K tokens (电费)                  │   │
│   │ → 节省 99%+                                         │   │
│   └─────────────────────────────────────────────────────┘   │
│                                                               │
│   🔒 隐私保护                                                  │
│   ┌─────────────────────────────────────────────────────┐   │
│   │ 敏感代码不离开本地环境                                  │   │
│   │ 本地模型处理，API不传输                                │   │
│   └─────────────────────────────────────────────────────┘   │
│                                                               │
│   🌐 离线工作                                                  │
│   ┌─────────────────────────────────────────────────────┐   │
│   │ 无网络连接时仍可使用 AI                                 │   │
│   │ Ollama/Jan 提供本地推理                               │   │
│   └─────────────────────────────────────────────────────┘   │
│                                                               │
│   🔄 模型切换                                                  │
│   ┌─────────────────────────────────────────────────────┐   │
│   │ 一个 API 调用，自动路由到不同后端                        │   │
│   │ 按需切换，无需改代码                                    │   │
│   └─────────────────────────────────────────────────────┘   │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### 3.3 支持的模型

| 提供商 | 模型 | 本地支持 |
|--------|------|----------|
| **OpenAI** | GPT-4, GPT-4 Turbo, GPT-4o, GPT-3.5-turbo | ❌ |
| **Anthropic** | Claude 3 Opus, Sonnet, Haiku, Claude 3.5 | ❌ |
| **Deepseek** | Deepseek-chat, Deepseek-coder | ❌ |
| **Grok** | Grok-1, Grok-2, Grok-2 Vision | ❌ |
| **Ollama** | llama2, codellama, mistral, mixtral, qwen 等 | ✅ |
| **Jan** | 所有 Hugging Face 模型 | ✅ |

## 四，安装指南

### 4.1 环境要求

| 要求 | 版本 |
|------|------|
| Python | 3.10+ |
| pip | 23+ |
| Ollama | 0.1+ (可选，本地模型) |
| Jan | 0.2+ (可选，本地模型) |

### 4.2 安装 9Router

```bash
# 安装 9Router
pip install 9router

# 或从源码安装
git clone https://github.com/decolua/9router.git
cd 9router
pip install -e .

# 验证安装
9router --version
```

### 4.3 安装本地模型支持（可选）

```bash
# 安装 Ollama
# macOS/Linux
curl -fsSL https://ollama.com/install.sh | sh

# Windows: 从 https://ollama.com/download 下载

# 拉取模型
ollama pull llama2
ollama pull codellama
ollama pull mistral

# 安装 Jan
# 从 https://jan.ai 下载

# 拉取模型
jan models install llama2
```

### 4.4 环境变量配置

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env
nano .env
```

**.env 配置内容:**
```bash
# OpenAI API
OPENAI_API_KEY=sk-...

# Anthropic API
ANTHROPIC_API_KEY=sk-ant-...

# Deepseek API
DEEPSEEK_API_KEY=sk-...

# Grok API
GROK_API_KEY=xk-...

# 默认提供商
DEFAULT_PROVIDER=openai

# 本地模型端点
OLLAMA_BASE_URL=http://localhost:11434
JAN_BASE_URL=http://localhost:1337

# 缓存设置
CACHE_ENABLED=true
CACHE_TTL=3600
```

## 五，使用指南

### 5.1 基础使用

```python
from 9router import Router

# 创建路由器
router = Router(provider="openai")

# 发送请求
response = router.chat(
    messages=[{"role": "user", "content": "Hello!"}]
)

print(response)
```

### 5.2 多提供商切换

```python
from 9router import Router

# 使用 OpenAI
router_openai = Router(provider="openai")
response_openai = router_openai.chat(
    messages=[{"role": "user", "content": "写 Python 代码"}]
)

# 使用 Anthropic
router_anthropic = Router(provider="anthropic")
response_anthropic = router_anthropic.chat(
    messages=[{"role": "user", "content": "写 Python 代码"}]
)

# 使用 Deepseek
router_deepseek = Router(provider="deepseek")
response_deepseek = router_deepseek.chat(
    messages=[{"role": "user", "content": "写 Python 代码"}]
)
```

### 5.3 本地模型

```python
from 9router import Router

# 使用 Ollama
router = Router(provider="ollama", model="llama2")
response = router.chat(
    messages=[{"role": "user", "content": "解释什么是光合作用"}]
)

# 使用 Jan
router = Router(provider="jan", model="llama2")
response = router.chat(
    messages=[{"role": "user", "content": "解释什么是光合作用"}]
)
```

### 5.4 Claude Code 配置

```bash
# 设置环境变量
export OPENAI_API_KEY=sk-...
export ANTHROPIC_API_KEY=sk-ant-...
export DEEPSEEK_API_KEY=sk-...

# 或使用 9Router 作为代理
export OPENAI_BASE_URL=http://localhost:8000/v1
export OPENAI_API_KEY=any-value

# 启动 9Router
9router serve

# 现在 Claude Code 会自动路由请求
```

### 5.5 Cursor 配置

```json
// Cursor 设置 (Settings → Models → Advanced)
{
  "openaiApiKey": "any-value",
  "openaiBaseUrl": "http://localhost:8000/v1"
}
```

## 六，API 参考

### 6.1 端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/v1/chat/completions` | POST | 聊天完成 |
| `/v1/models` | GET | 列出可用模型 |
| `/health` | GET | 健康检查 |

### 6.2 请求格式

```bash
# 聊天完成
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer any-value" \
  -d '{
    "model": "gpt-4",
    "messages": [
      {"role": "user", "content": "Hello!"}
    ]
  }'
```

### 6.3 响应格式

```json
{
  "id": "chatcmpl-xxx",
  "object": "chat.completion",
  "created": 1234567890,
  "model": "gpt-4",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "Hello! How can I help you today?"
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 10,
    "completion_tokens": 20,
    "total_tokens": 30
  }
}
```

### 6.4 模型列表

```bash
curl http://localhost:8000/v1/models
```

```json
{
  "object": "list",
  "data": [
    {"id": "gpt-4", "object": "model"},
    {"id": "gpt-4-turbo", "object": "model"},
    {"id": "claude-3-opus", "object": "model"},
    {"id": "claude-3-sonnet", "object": "model"},
    {"id": "deepseek-chat", "object": "model"},
    {"id": "llama2", "object": "model"},
    {"id": "mistral", "object": "model"}
  ]
}
```

## 七，高级配置

### 7.1 缓存配置

```python
from 9router import Router
from 9router.cache import RedisCache

# 使用 Redis 缓存
cache = RedisCache(host="localhost", port=6379, ttl=3600)
router = Router(provider="openai", cache=cache)

# 相同请求会返回缓存结果
response1 = router.chat(messages=[...])  # API 调用
response2 = router.chat(messages=[...])  # 缓存命中
```

### 7.2 负载均衡

```python
from 9router import Router

# 配置多个 API Key
router = Router(
    provider="openai",
    api_keys=[
        "sk-key1-...",
        "sk-key2-...",
        "sk-key3-..."
    ],
    load_balance=True
)

# 请求会自动分配到不同 Key
for i in range(10):
    router.chat(messages=[...])  # 轮询分配
```

### 7.3 回退机制

```python
from 9router import Router

# 配置回退策略
router = Router(
    provider="openai",
    fallback_providers=[
        {"provider": "anthropic", "model": "claude-3-sonnet"},
        {"provider": "ollama", "model": "llama2"}
    ]
)

# OpenAI 失败时自动切换到 Anthropic
# Anthropic 也失败时切换到 Ollama
response = router.chat(messages=[...])
```

### 7.4 自定义提供商

```python
from 9router import Router, BaseProvider

class MyProvider(BaseProvider):
    def __init__(self, api_key, base_url):
        super().__init__("my-provider", api_key, base_url)

    def chat(self, messages, **kwargs):
        # 实现聊天逻辑
        response = self._call_api(messages, **kwargs)
        return response

# 注册自定义提供商
router = Router(provider=MyProvider(
    api_key="my-key",
    base_url="https://my-api.com/v1"
))
```

## 八，故常排除

### 8.1 常见问题

| 问题 | 解决方案 |
|------|----------|
| 连接超时 | 检查网络，确认 API 端点可访问 |
| API Key 错误 | 检查环境变量中的 Key 是否正确 |
| 本地模型不响应 | 确认 Ollama/Jan 已启动并运行 |
| 缓存未命中 | 检查缓存服务是否正常运行 |

### 8.2 诊断命令

```bash
# 检查版本
9router --version

# 运行测试
9router test

# 查看日志
tail -f ~/.9router/logs/router.log

# 检查 API 连接
curl http://localhost:8000/health
```

### 8.3 日志配置

```yaml
# config.yaml
logging:
  level: INFO
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  file: ~/.9router/logs/router.log

handlers:
  console:
    enabled: true
    level: DEBUG
  file:
    enabled: true
    level: INFO
    rotation: daily
    retention: 7days
```

## 九，资源链接

### 9.1 官方资源

| 资源 | 链接 |
|------|------|
| 🌐 **GitHub** | https://github.com/decolua/9router |
| 📦 **PyPI** | https://pypi.org/project/9router |
| 📖 **Ollama** | https://ollama.com |
| 📦 **Jan** | https://jan.ai |

### 9.2 相关工具

| 工具 | 说明 |
|------|------|
| **Claude Code** | AI 编程工具 |
| **Cursor** | AI 代码编辑器 |
| **OpenAI API** | OpenAI API |
| **Anthropic API** | Anthropic API |

### 9.3 本地模型

| 模型 | 说明 |
|------|------|
| **Llama 2** | Meta 开源 LLM |
| **Code Llama** | 代码专用 Llama |
| **Mistral** | 高效开源 LLM |
| **Mixtral** | 混合专家模型 |

## 十，总结

9Router 是** Claude Code 和 Cursor 的终极路由器**：

| 维度 | 说明 |
|------|------|
| 🔀 **多后端** | OpenAI、Anthropic、Deepseek、Grok |
| 🏠 **本地模型** | Ollama + Jan 离线支持 |
| 💰 **成本节省** | 本地模型减少 99%+ 费用 |
| 🔒 **隐私保护** | 敏感代码不离开本地 |
| 🔄 **统一 API** | OpenAI 兼容，易于集成 |
| ⚡ **简单配置** | 环境变量，无需改代码 |

---

**🔗 相关资源：**

| 资源 | 链接 |
|------|------|
| GitHub | https://github.com/decolua/9router |
| PyPI | https://pypi.org/project/9router |
| Ollama | https://ollama.com |
| Jan | https://jan.ai |

---

_🦞 本文由钳岳星君撰写，基于 9Router (1.5k Stars)_
