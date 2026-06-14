+++
date = '2026-05-17T20:25:00+08:00'
draft = false
title = 'Dograh：开源语音 AI Agent 平台'
slug = 'dograh-devops-tool-guide'
description = 'Dograh 是一个开源自托管的语音 AI Agent 平台，支持拖拽式工作流构建、Docker 一键部署，可作为 Vapi 和 Retell 的替代方案。'
categories = ['技术笔记']
tags = ['AI', '语音', '开源', 'Docker']
+++

# Dograh：开源语音 AI Agent 平台

在语音 AI 领域，Vapi 和 Retell 等闭源平台长期占据主导地位——但它们意味着高昂的按分钟计费、供应商锁定以及对基础设施的零可视化。**Dograh**（Zansat Technologies Private Limited）正在改变这一格局：由 YC 校友和退出创业老兵打造，BSD 2-Clause 许可证开源，一个 Docker 命令即可自托管，支持拖拽式工作流构建，真正做到代码全透明、基础设施全可控。

## 一、项目概览

### 1.1 是什么

Dograh 是一个**开源、自托管的语音 AI Agent 构建与运行平台**。它允许你：

- 用**拖拽式可视化编辑器**设计对话流程（工作流）
- 将 Agent 连接到电话网络（呼入/呼出）
- 配置 LLM、TTS（Text-to-Speech）、STT（Speech-to-Text）提供者
- 通过 MCP（Model Context Protocol）让 AI 助手直接驱动你的 Agent

### 1.2 核心定位对比

| 维度 | **Dograh** | **Vapi** | **Retell** |
|------|-----------|----------|------------|
| 许可证 | BSD 2-Clause（开源） | 专有 | 专有 |
| 部署方式 | 自托管 + 云托管 | 仅 SaaS | 仅 SaaS |
| 定价 | 免费（自托管）/ 按用量（云） | 按分钟 | 按分钟 |
| 自带 LLM/STT/TTS | ✅ 任意 provider | 有限集成 | 有限集成 |
| 源码级定制 | ✅ 完全开放 | ❌ | ❌ |
| 数据主权 | 你的服务器，你做主 | 供应商云 | 供应商云 |
| 供应商锁定 | 无 | 完全锁定 | 完全锁定 |

### 1.3 技术栈一览

| 组件 | 技术选型 |
|------|---------|
| 核心语言 | Python |
| 实时音频 | [Pipecat](https://github.com/pipecat-ai/pipecat)（子模块） |
| 后端 API | FastAPI |
| 前端 UI | React |
| 数据库 | PostgreSQL |
| 缓存 | Redis |
| 对象存储 | MinIO |
| 部署 | Docker Compose |
| 实时通信 | WebRTC（可选 coturn TURN 服务器） |
| 协议 | MCP（Model Context Protocol） |

### 1.4 关键数字

- 🚀 **2 分钟**从零到可通话 Agent
- 🐳 **一条 Docker 命令**完成本地部署
- 🔓 **100% 开源**，无许可证侵权风险
- 🌐 支持 Twilio、Vonage、Plivo、Telnyx、Cloudonix、Vobiz、Asterisk ARI 等多种电话供应商

---

## 二、核心概念

理解 Dograh 的运作方式，需要掌握以下几个核心概念及其相互关系。

### 2.1 工作流（Workflow / Agent）

**工作流**是 Dograh 的核心抽象——一个以图为结构的对话逻辑系统。

- **节点（Node）**：对话中的每个步骤，如"说一段开场白"、"收集用户预算"、"转接人工"等
- **边（Edge）**：节点之间的条件转移，决定对话的流向
- **Prompt**：每个节点附带的指令文本，告诉 LLM 在该节点时应说什么、如何判断转移条件

工作流通过可视化编辑器构建，发布后即可接收真实通话。

### 2.2 运行（Run）

每一次工作流的执行产生一个 **Run**（运行记录）。Run 是 Dograh 的计费和审计单元，记录：

- 完整对话转录（Transcript）
- 通话录音
- 提取的结构化数据
- 本次运行成本

### 2.3 通话生命周期

```
触发通话（Dashboard 或 API）
       ↓
[Telephony Provider] 发起外呼或接收来电
       ↓
来电者接听 → 实时音频流建立
       ↓
[STT] 将语音转文字 → 实时转录
       ↓
[LLM Provider] 接收：转录文本 + 节点 Prompt + 对话历史 → 生成回复文本
       ↓
[TTS] 将回复文本转语音 → 音频流推送到来电者
       ↓
[Edge 条件评估] → 满足条件则转移到下一节点
       ↓
到达 End Node → 通话结束
       ↓
提取上下文 → 触发 Webhook → 保存 Run 记录
```

### 2.4 模型配置

Dograh 支持配置多个 LLM、TTS、STT 提供者：

**LLM**：OpenAI、Google（Gemini）、Groq、Azure、Dograh 原生

**TTS**：ElevenLabs、Deepgram、OpenAI、Dograh 原生（支持自定义 Voice ID）

**STT**：Deepgram 等主流提供商

所有密钥通过 Dashboard 的 **API Keys** 页面统一管理。

### 2.5 上下文与变量

工作流支持模板变量和 Pre-Call Data Fetch，可以在通话开始前动态注入外部数据（如 CRM 记录），让 Agent 的首次问候就携带个性化信息。

---

## 三、架构解析

### 3.1 整体架构

```
                    ┌─────────────────────────────────────────────┐
                    │               Dograh Platform               │
                    │                                             │
  Caller ◄──Audio──►│  ┌─────────┐   ┌──────────┐  ┌─────────┐ │
  (Phone)           │  │ Telephony│   │ Pipecat   │  │  FastAPI │ │
                    │  │ Provider │◄──►│ Audio     │◄─┤  REST    │ │
                    │  │(Twilio…) │   │ Pipeline  │  │  + WS    │ │
                    │  └─────────┘   └───────────┘  └─────────┘ │
                    │                     │                      │
                    │              ┌──────┴──────┐               │
                    │              │ LLM │ TTS │ STT │            │
                    │              └─────────────┘               │
                    │                                            │
                    │  ┌──────────┐  ┌────────┐  ┌──────────┐   │
                    │  │PostgreSQL│  │ Redis  │  │  MinIO   │   │
                    │  │(Run records)│(Cache) │(Recordings)│   │
                    │  └──────────┘  └────────┘  └──────────┘   │
                    └─────────────────────────────────────────────┘
```

### 3.2 Docker Compose 服务划分

一条 `docker compose up` 启动以下服务：

| 服务 | 职责 |
|------|------|
| `api` | FastAPI 后端，处理 API 请求、工作流执行 |
| `ui` | React 前端，拖拽式编辑器、Dashboard |
| `postgres` | 主数据库，存储工作流、Run、凭证 |
| `redis` | 缓存、实时队列 |
| `minio` | S3 兼容存储，通话录音、转录文件 |
| `coturn` | TURN 服务器（可选，需 `--profile local-turn`），WebRTC NAT 穿透 |
| `nginx` | 反向代理+HTTPS 终止（远程部署） |

### 3.3 实时音频管线（Pipecat）

Dograh 使用 [Pipecat](https://github.com/pipecat-ai/pipecat) 作为核心实时音频管线：

- **WebSocket 双工通信**：浏览器 ↔ API 容器之间的实时音频流
- **STT 流转**：音频分帧 → STT API → 转录文本
- **LLM 推理**：转录文本连同 Prompt 上下文送入 LLM
- **TTS 合成**：LLM 输出文本 → TTS API → 音频帧 → 推送回通话方
- **打断处理**：支持用户实时打断 Agent 说话（Interruption Handling）

---

## 四、快速部署

### 4.1 本地单机器部署（推荐上手）

一条命令，2 分钟跑起来：

```bash
curl -o docker-compose.yaml https://raw.githubusercontent.com/dograh-hq/dograh/main/docker-compose.yaml \
  && REGISTRY=ghcr.io/dograh-hq ENABLE_TELEMETRY=true docker compose up --pull always
```

> ⚠️ **首次启动需要 2-3 分钟**下载所有 Docker 镜像。

启动完成后访问 **http://localhost:3010** 即可进入 Dashboard。

> 💡 默认自带 LLM/TTS/STT 密钥，**无需任何 API Key 即可开始测试**。正式使用时在 Dashboard 的 API Keys 页面配置你自己的密钥。

关闭遥测：

```bash
ENABLE_TELEMETRY=false docker compose up --pull always
```

### 4.2 远程服务器部署（HTTPS）

适用于将平台部署到云服务器，对外提供服务：

```bash
curl -o setup_remote.sh https://raw.githubusercontent.com/dograh-hq/dograh/main/scripts/setup_remote.sh \
  && chmod +x setup_remote.sh && ./setup_remote.sh
```

脚本交互式询问：

1. 服务器公网 IP 地址
2. TURN 服务器密码（默认自动生成）
3. 部署模式：**prebuilt**（拉取官方镜像，推荐） 或 **build**（从源码编译）
4. FastAPI worker 数量（默认 4 个）

完成后自动配置：

- nginx 反向代理（自签名 HTTPS）
- coturn TURN 服务器（WebRTC 穿透）
- `.env` 环境配置

访问 **https://YOUR_SERVER_IP**（浏览器会提示自签名证书安全警告，接受即可）。

### 4.3 防火墙端口要求（远程部署）

| 端口 | 协议 | 用途 |
|------|------|------|
| TCP 80, 443 | HTTP/HTTPS | Web UI + API |
| TCP 3478, 5349 | TURN | WebRTC NAT 穿透 |
| UDP 3478, 5349 | TURN | WebRTC NAT 穿透 |
| UDP 49152-49200 | TURN | TURN 中继端口范围 |

### 4.4 私有化定制镜像（从源码构建）

如果你维护了 Dograh 的 fork，或有自定义代码修改：

```bash
# 克隆并以 build 模式部署
git clone https://github.com/YOUR_FORK/dograh.git
cd dograh
git submodule update --init --recursive   # 更新 pipecat 子模块
docker compose --profile remote build api ui
docker compose --profile remote up -d
```

强制无缓存完整重建：

```bash
docker compose --profile remote build --no-cache api ui
docker compose --profile remote up -d
```

---

## 五、构建你的第一个语音 Agent

### 5.1 Dashboard 初印象

登录 http://localhost:3010，Dogsrah Dashboard 主要分区：

- **左侧导航**：Workflows、Runs、Campaigns、API Keys、Settings
- **主区域**：拖拽式工作流编辑器（节点面板 + 画布）
- **顶部**：Inbound / Outbound 切换，Web Call 测试按钮

### 5.2 创建 Agent（Inbound 场景）

**目标**：构建一个"保险表单初筛" Agent，识别有购买意向的用户。

**步骤**：

1. 选择 **Inbound**
2. 输入名称：`Lead Qualification`
3. 简短描述：`Screen insurance form submissions for purchase intent`
4. 点击 **Web Call** 直接在浏览器内测试（无需电话）

> 🔑 **无需任何 API Key**——Dograh 默认带有一套开箱即用的 LLM/TTS/STT。

### 5.3 工作流编辑器

编辑器分为两部分：

- **左侧节点面板**：常用节点类型
- **中间画布**：拖拽排列节点、连接边

### 5.4 核心节点类型

| 节点 | 作用 |
|------|------|
| **Agent Node** | 核心节点，指定 Prompt，LLM 在此生成回复 |
| **Start Call** | 触发通话开始（Outbound） |
| **End Call** | 主动结束通话 |
| **Transfer Call** | 转接给人工客服 |
| **HTTP Action** | 调用外部 API |
| **Knowledge Base** | 从文档知识库检索信息辅助 LLM |
| **QA Node** | 评估其他节点 Prompt 质量 |
| **Condition / Edge** | 条件分支（判断用户意图、关键词等） |

### 5.5 Agent Node 示例

在 Agent Node 的 Prompt 中编写：

```
你是一位专业的保险顾问。你需要：
1. 友好地问用户目前是否有保险需求
2. 询问他们的预算范围
3. 如果用户表示有兴趣，记录为"qualified_lead=true"
4. 如果用户明确拒绝，礼貌结束对话

记住：保持专业、简洁，不要过度销售。
```

通过 Edge 连接，可以在 LLM 回复中嵌入条件判断，例如：

```
IF intent == "buy_insurance" AND budget >= 5000 → 转Qualified节点
IF intent == "not_interested" → 转End节点
```

### 5.6 测试模式（Test Mode）

Dashboard 提供 **Test Mode**，在发布前进行端到端测试：

- 不会产生真实通话费用
- 不会影响线上数据
- 可在 Test Mode 中修改工作流后重新测试

---

## 六、电话系统集成（Telephony）

Dograh 支持多种电话供应商，可同时激活多个 Provider。

### 6.1 Twilio 集成示例

在 Dashboard → Telephony 中配置 Twilio：

```python
# 实际上不需要手动配置，通过 Dashboard UI 填写即可
# 以下为 API 层面的连接参数结构（供参考）

TWILIO_ACCOUNT_SID = "ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
TWILIO_AUTH_TOKEN  = "your_auth_token"
TWILIO_PHONE_NUMBER = "+1xxxxxxxxxx"
```

配置完成后：

- **Inbound**：在 Twilio Console 配置 Webhook 指向 Dograh 的 `/call/twilio/inbound`
- **Outbound**：在 Dashboard 直接发起外呼，Dograh 通过 Twilio API 拨号

### 6.2 支持的 Telephony Provider

| Provider | 特点 |
|----------|------|
| **Twilio** | 最流行，支持全球号码 |
| **Vonage** | 欧洲市场强 |
| **Plivo** | 价格竞争力强 |
| **Telnyx** | 直连运营商 |
| **Cloudonix** | 专注 SIP 中继 |
| **Vobiz** | 适合本地部署 |
| **Asterisk ARI** | 自建 PBX 集成 |

### 6.3 自定义 Telephony Provider

通过 Dograh 的 Custom Telephony Provider 接口，可以接入任何符合 SIP/REST 规范的语音网关。详见 [Custom Telephony Provider 文档](https://docs.dograh.com/telephony/custom-telephony-provider)。

### 6.4 Webhook 与通话回调

通话事件通过 Webhook 推送：

```json
{
  "event": "call.ended",
  "run_id": "run_xxxxxxxxxxxx",
  "agent_id": "agent_xxxxxxxxxxxx",
  "transcript": [
    {"role": "agent", "text": "您好，请问有什么可以帮助您的？"},
    {"role": "user", "text": "我想咨询保险产品"}
  ],
  "recording_url": "https://minio...",
  "extracted_data": {
    "intent": "insurance_inquiry",
    "budget": 8000
  },
  "cost": {
    "llm": 0.0023,
    "tts": 0.0011,
    "stt": 0.0008
  },
  "duration_seconds": 187
}
```

---

## 七、高级功能

### 7.1 MCP Server：让 AI 助手驱动你的 Agent

Dograh v0.7+ 推出了 **MCP Server**，允许 Claude、Cursor 等 AI 助手直接操作你的 Dograh 工作区。

#### MCP 端点

- **云托管**：`https://app.dograh.com/api/v1/mcp/`
- **自托管**：`https://YOUR_BACKEND_URL/api/v1/mcp/`

#### Claude Code 接入

```bash
claude mcp add --transport http dograh https://app.dograh.com/api/v1/mcp/ \
  --header "X-API-Key: YOUR_API_KEY"
```

验证连接：

```bash
claude mcp list
```

> ⚠️ 自签名证书场景需要：`NODE_TLS_REJECT_UNAUTHORIZED=0 claude`

#### Claude Desktop 接入

编辑 `claude_desktop_config.json`：

```json
{
  "mcpServers": {
    "dograh": {
      "url": "https://app.dograh.com/api/v1/mcp/",
      "headers": {
        "X-API-Key": "YOUR_API_KEY"
      }
    }
  }
}
```

#### 常用指令示例

```plaintext
"List my agents in Dograh."
"Show me the definition of the agent called Lead Qualifier."
"Add a new agent node after the greeting that asks the caller for their budget."
"Search the Dograh docs for how to configure a TURN server."
"What node types does Dograh support?"
```

Agent 的修改会保存为草稿版本（draft），发布前不会影响线上正在服务的 Agent。

### 7.2 批量外呼（Campaigns）

Campaign 用于大规模外呼场景：

- 上传呼叫列表（CSV）
- 设置呼叫策略（并发数、重试间隔）
- 实时监控接通率、转录质量

### 7.3 知识库（Knowledge Base）

在 Agent Node 中引用知识库节点，LLM 会在回复前先检索相关文档，结合检索结果生成个性化回答，适合产品咨询、客服 FAQ 等场景。

### 7.4 Pre-Call Data Fetch

在通话建立前，Dograh 可以调用外部 API 获取来电者的背景信息（如 CRM 记录），让 Agent 首次开口就说出个性化内容。

### 7.5 Pre-recorded Audio

除了 TTS 合成语音，Dograh 也支持预录音频播放，适合标准化 IVR 流程、法定提示语等场景。

### 7.6 Tracing 与可观测性

Dograh 集成了 Tracing 支持，可监控：

- LLM 推理延迟
- TTS 合成延迟
- 端到端通话延迟
- 各节点执行时间

---

## 八、配置参考

### 8.1 LLM 配置

支持 OpenAI、Google（Gemini）、Groq、Azure、Dograh 原生。模型可通过 Dashboard 下拉菜单选择，也支持手动填入任意兼容模型的 base URL 和模型名称。

```bash
# 环境变量示例（实际通过 UI 配置更便捷）
OPENAI_API_KEY=sk-xxxxx
OPENAI_MODEL=gpt-4o-mini
```

### 8.2 TTS 配置

支持 ElevenLabs、Deepgram、OpenAI、Dograh 原生。

```bash
ELEVENLABS_API_KEY=xxxxx
ELEVENLABS_VOICE_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
```

### 8.3 STT 配置

```bash
DEEPGRAM_API_KEY=xxxxx
DEEPGRAM_MODEL=nova-2
```

### 8.4 TURN 服务器配置（生产环境）

在 `.env` 中配置 coturn：

```bash
TURN_HOST=YOUR_PUBLIC_IP
TURN_SECRET=your_random_secret_here
COTURN_PORT=3478
FORCE_TURN_RELAY=false   # 设为 true 可强制所有媒体流经 TURN，用于调试
```

### 8.5 自定义域名 + Let's Encrypt

在远程部署完成后，通过 Certbot 配置 Let's Encrypt 证书：

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com
```

将 Dograh 的 nginx 配置反向代理指向你的域名即可。

---

## 九、MCP Server 架构解析

### 9.1 MCP 协议简介

MCP（Model Context Protocol）是一种标准化协议，让 AI 助手可以调用外部工具和数据源。Dograh MCP Server 暴露以下工具集：

| 工具 | 能力 |
|------|------|
| `list_agents` | 列出当前工作区所有 Agent |
| `get_agent` | 获取指定 Agent 的完整定义 |
| `list_runs` | 查看通话运行记录 |
| `search_docs` | 搜索 Dograh 官方文档 |
| `update_agent` | 修改 Agent 定义（存为草稿） |

### 9.2 MCP 安全模型

API Key 是 MCP 连接的唯一年份认证手段。Key 决定了 AI 助手能访问哪个工作区——因此：

> ⚠️ **API Key 等同于访问权限**：不要将其提交到 Git 或在公开渠道分享。

### 9.3 在 AI Coding 工具中驱动 Dograh

以 Cursor 为例，在 MCP Settings 中添加：

```json
{
  "dograh": {
    "url": "https://YOUR_DOGRAH_ENDPOINT/api/v1/mcp/",
    "headers": {
      "X-API-Key": "YOUR_KEY"
    }
  }
}
```

配置完成后，就可以在 Cursor 的 AI 聊天中直接说"将 Lead Qualification Agent 的 LLM 模型切换为 gpt-4o-mini"，Cursor 会通过 MCP 自动完成操作。

---

## 十、与同类方案对比

### 10.1 完整对比表

| 维度 | **Dograh** | **Vapi** | **Retell** | **Twilio Flex** |
|------|-----------|----------|------------|----------------|
| 许可证 | BSD 开源 | 专有 | 专有 | 专有 |
| 源码可见 | ✅ | ❌ | ❌ | 部分 |
| 自托管 | ✅ Docker | ❌ | ❌ | ✅ |
| 按用量成本 | 免费自托管 | $0.003/min+ | $0.004/min+ | 按通话+IVR |
| 工作流编辑器 | 拖拽 UI | 部分支持 | 部分支持 | 需要编码 |
| MCP 支持 | ✅ | ❌ | ❌ | ❌ |
| 内置 TTS/STT | ✅ 多种 | 有限 | 有限 | 需自行集成 |
| 知识库 | ✅ | ❌ | ❌ | 有限 |
| Webhook | ✅ | ✅ | ✅ | ✅ |

### 10.2 选型建议

- **个人开发者 / 初期验证**：直接使用云托管版，零基础设施成本
- **中小企业**：自托管部署，数据完全私有，无按分钟计费压力
- **大型企业**：私有化部署 + 自定义 Telephony Provider + 定制工作流节点
- **AI 应用开发者**：通过 MCP 集成到 AI Coding 工作流，实现 Agent 的代码驱动管理

---

## 十一、故障排查速查

### 11.1 WebRTC 无音频

**症状**：通话接通但双方听不到声音，浏览器控制台 `iceConnectionState: failed`

**排查路径**：

1. 检查是否在 NAT 严格环境下（VPN、公司防火墙、手机跨网段）
2. 使用有 TURN 模式：`FORCE_TURN_RELAY=true` 重启 API，确认问题消失
3. 如果问题消失 → 说明直连失败，需要配置 coturn TURN 服务器
4. 本地单机器部署推荐执行 `./setup_local.sh` 启用 coturn

### 11.2 首次启动镜像下载慢

Docker Hub 在国内访问较慢，可以配置镜像加速：

```bash
# 阿里云镜像加速（示例）
mkdir -p /etc/docker
cat > /etc/docker/daemon.json << 'EOF'
{
  "registry-mirrors": ["https://mirror.ccs.tencentyun.com"]
}
EOF
sudo systemctl restart docker
```

### 11.3 端口冲突

远程部署要求端口 80/443/3478/5349 可用，如被占用：

```bash
# 检查端口占用
sudo lsof -i :80
sudo netstat -tlnp | grep 3478
```

### 11.4 API Key 无效

确认 API Key 在 Dashboard 的 `/api-keys` 页面生成，且未过期。MCP 连接时需在请求头中正确传递：

```
X-API-Key: YOUR_KEY
```

---

## 十二、总结与展望

Dograh 以**开源 + 自托管 + 拖拽式工作流**的组合拳，撕开了 Vapi/Retell 等闭源平台在语音 AI 市场的护城河。2 分钟上手、一条 Docker 命令部署、完全可控的技术栈——这对于重视数据主权、预算敏感或需要深度定制的团队来说，是极具吸引力的选择。

随着 MCP Server 的推出，Dograh 又向前迈了一步：AI 助手不再只是外部调用者，而是可以直接**操作**你的语音 Agent——这意味着未来 AI Coding 工作流与 Voice Agent 管理的深度融合将是大势所趋。

---

**参考链接**：

- GitHub：https://github.com/dograh-hq/dograh
- 官方文档：https://docs.dograh.com
- 云托管平台：https://app.dograh.com
- 社区 Slack：https://join.slack.com/t/dograh-community/shared_invite/zt-3czr47sw5-MSg1J0kJ7IMPOCHF~03auQ

---

*本文基于 Dograh 官方 GitHub 仓库 v0.7+ 及 docs.dograh.com 编写，所有信息截至 2026-05-17。*