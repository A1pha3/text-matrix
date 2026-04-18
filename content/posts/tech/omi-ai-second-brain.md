---
title: "Omi：你的第二大脑——9K Stars的全平台AI记忆助手，支持桌面/手机/可穿戴设备"
date: 2026-04-18T15:30:00+08:00
slug: "omi-ai-second-brain"
description: "Omi是一款开源AI助手产品，捕捉屏幕和对话、实时转录、生成摘要和行动项，让AI记住你看到和听到的一切。支持桌面(macOS)、手机(iOS/Android)和可穿戴设备，GitHub获300K+专业人士信赖。"
draft: false
categories: ["技术笔记"]
tags: ["AI助手", "记忆系统", "RAG", "可穿戴设备", "实时转录", "Omi"]
---

# Omi：你的第二大脑——9K Stars的全平台AI记忆助手，支持桌面/手机/可穿戴设备

> **目标读者**：追求个人知识管理效率的开发者、AI产品爱好者、寻求"第二大脑"解决方案的知识工作者
> **预计阅读时间**：40-50分钟
> **前置知识**：了解RAG（检索增强生成）基本概念，对AI助手产品有使用经验
> **难度定位**：⭐⭐⭐⭐ 专家设计

---

## §1 学习目标

1. **理解Omi的核心定位**：为何被称为"比第一大脑更可信的第二大脑"
2. **掌握Omi的技术架构**：端侧设备+云端后端+多模态AI的协同原理
3. **了解多平台覆盖**：macOS应用、iOS/Android App、可穿戴设备固件
4. **能够部署和二次开发**：本地运行后端、构建应用、使用SDK
5. **理解AI记忆系统**：上下文捕捉→向量检索→对话生成的完整链路

---

## §2 背景与动机：为何需要"第二大脑"

### 2.1 人类记忆的局限性

| 记忆类型 | 容量 | 保持时间 | 检索速度 |
|----------|------|----------|----------|
| 工作记忆 | 7±2个信息块 | 几秒~几分钟 | 即时但有限 |
| 短期记忆 | 20~30秒 | 几分钟 | 慢，容易遗忘 |
| 长期记忆 | 无限 | 数年~一生 | 最慢，需要线索 |

**问题**：人类记忆在信息爆炸时代严重过载，导致"知识焦虑"和"决策疲劳"。

### 2.2 现有方案的局限

**方案一：笔记应用（Notion/Obsidian）**
- 手动记录，依赖用户主动整理
- 无法捕捉口头交流、屏幕内容
- 检索是精确匹配，非语义搜索

**方案二：AI助手聊天记录**
- 上下文窗口有限，超出即遗忘
- 无法搜索历史对话
- 无法与个人知识库结合

### 2.3 Omi的设计理念

Omi提出了"第二大脑"的概念：**让AI实时捕捉你的屏幕和对话，主动整理成可检索的知识图谱。**

```
你看到的内容 + 你说的话 → Omi实时捕捉 → 向量化存储 → AI对话检索
```

**核心价值**：
- **被动记录**：无需主动操作，Omi自动记录
- **上下文完整**：屏幕+语音+文字，多模态融合
- **语义检索**：不只是关键词，是理解意图的搜索
- **跨设备同步**：桌面→手机→可穿戴，无缝衔接

---

## §3 技术架构：全栈开源方案

### 3.1 整体架构

```
┌─────────────────────────────────────────────────────────┐
│                      Your Devices                        │
│                                                          │
│  ┌──────────┐  ┌──────────────┐  ┌───────────────────┐  │
│  │ Omi      │  │ macOS App    │  │ Mobile App        │  │
│  │ Wearable │  │ (Swift/Rust) │  │ (Flutter)         │  │
│  └────┬─────┘  └──────┬───────┘  └────────┬──────────┘  │
│       │    BLE          │   HTTPS/WS        │             │
└───────┼────────────────┼───────────────────┼─────────────┘
        │                │                   │
        ▼                ▼                   ▼
┌─────────────────────────────────────────────────────────┐
│                    Omi Backend (Python)                  │
│                                                          │
│  ┌─────────┐  ┌──────────┐  ┌─────────┐  ┌──────────┐  │
│  │ Listen  │  │ Pusher   │  │ VAD     │  │ Diarizer │  │
│  │ (REST)  │  │ (WS)     │  │ (GPU)   │  │ (GPU)    │  │
│  └─────────┘  └──────────┘  └─────────┘  └──────────┘  │
│                                                          │
│  ┌─────────┐  ┌──────────┐  ┌─────────┐  ┌──────────┐  │
│  │ Deepgram│  │ Firestore│  │ Redis   │  │ LLMs     │  │
│  │ (STT)   │  │ (DB)     │  │ (Cache) │  │ (AI)     │  │
│  └─────────┘  └──────────┘  └─────────┘  └──────────┘  │
└─────────────────────────────────────────────────────────┘
```

### 3.2 各组件详解

| 组件 | 技术栈 | 路径 | 功能 |
|------|--------|------|------|
| **macOS App** | Swift/SwiftUI/Rust | `desktop/` | 屏幕捕捉、语音输入 |
| **Mobile App** | Flutter | `app/` | iOS/Android双端 |
| **Backend API** | Python/FastAPI | `backend/` | 业务逻辑、LLM调用 |
| **Firmware** | C/nRF/Zephyr | `omi/` | 可穿戴设备固件 |
| **Omi Glass** | ESP32-S3/C | `omiGlass/` | 眼镜设备固件 |
| **SDKs** | React Native/Swift/Python | `sdks/` | 多语言SDK |

### 3.3 核心技术栈

**前端**：
- macOS：SwiftUI（声明式UI）+ Rust（高性能后端）
- 移动端：Flutter（跨平台）+ 平台原生SDK

**后端**：
- Python + FastAPI（高性能API框架）
- Firebase Firestore（NoSQL数据库）
- Redis（缓存层）
- Deepgram（语音转文本STT）
- VAD（语音活动检测，GPU加速）
- Diarizer（说话人分离，GPU加速）

**AI**：
- LLMs集成：OpenAI/Anthropic等主流模型
- RAG管道：向量检索+生成

---

## §4 核心功能详解

### 4.1 屏幕捕捉与实时转录

**macOS应用**：
- 实时屏幕捕捉（隐私保护设计）
- 本地音频采集
- 与后端实时同步

**技术实现**：
```
屏幕帧 → 本地处理（脱敏）→ 压缩传输 → 后端VAD检测 → Deepgram STT → 向量化
```

### 4.2 多设备同步

**Omi Wearable**：
- BLE（低功耗蓝牙）连接
- 连续音频捕捉
- 24小时+续航设计

**Omi Glass**：
- ESP32-S3芯片
- 摄像头+音频
- 开发者套件开放购买

### 4.3 AI对话与记忆检索

**对话流程**：
```
用户问题 → 意图分析 → 向量检索（Omi自研向量引擎）→ 上下文组装 → LLM生成 → 回复
```

*注：Omi使用自研的向量检索引擎，具体实现细节未完全开源。*

**特性**：
- 记得你见过的所有内容
- 跨对话的长期记忆
- 主动建议和行动项

### 4.4 应用开发平台

**SDK支持**：
- Python SDK：后端集成
- Swift SDK：iOS/macOS集成
- React Native SDK：跨平台移动开发
- MCP Server：Model Context Protocol集成

**可能的应用场景**：
- 个人知识管理：构建第二大脑
- 会议记录：自动转录和摘要
- 项目文档：跨设备同步

---

## §5 快速开始：5分钟上手

### 5.1 macOS桌面应用

**方式一：快速开始（推荐）**
```bash
git clone https://github.com/BasedHardware/omi.git && cd omi/desktop && ./run.sh
```

这会自动构建macOS应用、连接云端后端、启动App。无需配置env文件或本地后端。

**依赖**：
- macOS 14+
- Xcode（包含Swift和代码签名）

**方式二：本地完整开发**
```bash
xcode-select --install
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

git clone https://github.com/BasedHardware/omi.git
cd omi/desktop
cp Backend-Rust/.env.example Backend-Rust/.env

./run.sh
```

### 5.2 移动端（iOS/Android）

**iOS**
```bash
cd app && bash setup.sh ios
```

**Android**
```bash
cd app && bash setup.sh android
```

### 5.3 可穿戴设备

**刷固件**
```bash
# 参考文档
https://docs.omi.me/doc/get_started/Flash_device
```

---

## §6 开发扩展：基于Omi构建应用

### 6.1 MCP Server集成

Omi提供了MCP Server，可以与各类AI编码助手集成：

```json
{
  "mcpServers": {
    "omi": {
      "command": "npx",
      "args": ["-y", "@based/omi-mcp"]
    }
  }
}
```

### 6.2 Python SDK使用

**注意**：Omi的Python SDK主要面向后端集成，具体的import路径需参考官方文档。核心功能包括：

- **搜索记忆**：`client.search(query)` 查询历史记忆
- **对话历史**：`client.conversations.list()` 获取历史会话
- **行动项管理**：`client.action_items` 创建和管理待办

### 6.3 移动端SDK

Omi提供多平台SDK支持：

| 平台 | SDK | 路径 |
|------|-----|------|
| iOS/macOS | Swift SDK | `sdks/swift/` |
| Android | React Native SDK | `sdks/react-native/` |
| 跨平台 | Python SDK | `sdks/python/` |

### 6.4 应用开发示例

以下示例展示如何使用Web API与Omi后端交互：

```typescript
// Web应用接入Omi
const OMI_API_KEY = 'your-api-key';

// 搜索记忆
async function searchMemories(query: string) {
  const response = await fetch('YOUR_OMI_API_ENDPOINT/memories/search', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${OMI_API_KEY}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ query })
  });
  return response.json();
}

// 监听新记忆（通过WebSocket）
const ws = new WebSocket('YOUR_OMI_WS_ENDPOINT');
ws.onmessage = (event) => {
  const memory = JSON.parse(event.data);
  console.log('新记忆:', memory.content);
};
```

### 6.5 练习：构建你的第一个Omi应用

**练习目标**：使用Omi API构建一个简单的记忆搜索工具

**前置准备**：
- 已安装Omi App（macOS/iOS/Android）
- 已注册Omi账号
- 获取了API Key（参考官方文档）

**详细步骤**：

**Step 1：创建一些记忆**
1. 打开Omi App
2. 进行几次对话或添加笔记
3. 确保有足够的内容可供搜索

**Step 2：获取API Key**
参考 https://docs.omi.me/api-reference 获取API访问方式

**Step 3：编写搜索代码**
```typescript
// 使用官方SDK或直接调用API
const OMI_API_KEY = 'your-api-key';

async function searchMemories(query: string) {
  // 参考官方API文档构建请求
  const response = await fetch('YOUR_API_ENDPOINT/memories/search', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${OMI_API_KEY}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ query })
  });
  return response.json();
}

// 测试搜索
const results = await searchMemories('会议');
console.log(results);
```

**验证标准**：
- [ ] 成功调用搜索API
- [ ] 返回结果与记忆内容匹配
- [ ] 实现了错误处理（API Key无效等情况）

**进阶挑战**：
- 尝试实时监听新记忆（WebSocket）
- 构建一个简单的Web界面展示记忆时间线

---

## §7 硬件生态：开源可穿戴设备

### 7.1 Omi Wearable

- **设计**：紧凑轻便，24小时+佩戴
- **BLE连接**：低功耗蓝牙与手机同步
- **固件**：开源（`omi/`目录，nRF/Zephyr）

### 7.2 Omi Glass Dev Kit

- **芯片**：ESP32-S3
- **传感器**：摄像头+音频
- **购买**：https://www.omi.me/glass
- **开源硬件设计**：https://docs.omi.me/doc/hardware/consumer/electronics

### 7.3 开发者资源

| 资源 | 链接 |
|------|------|
| 购买指南 | https://docs.omi.me/doc/assembly/Buying_Guide |
| 构建指南 | https://docs.omi.me/doc/assembly/Build_the_device |
| 固件烧录 | https://docs.omi.me/doc/get_started/Flash_device |
| 硬件规格 | https://docs.omi.me/doc/hardware/DevKit2 |

---

## §8 FAQ

### Q1: Omi免费吗？
Omi的核心功能免费使用。云端服务有免费额度，超出后按量付费。本地部署后可完全自托管。

### Q2: 隐私如何保护？
- 屏幕捕捉在本地处理（脱敏）后再传输
- 音频可选本地处理模式
- 支持自托管后端

### Q3: 支持中文吗？
支持。Omi对多语言（包括中文）均有优化。

### Q4: 如何接入我的LLM？
Omi支持自定义LLM后端，可在配置中指定OpenAI/Anthropic等模型。

---

## §9 相关资源

- [GitHub仓库](https://github.com/BasedHardware/omi)
- [官方文档](https://docs.omi.me/)
- [Discord社区](http://discord.omi.me)
- [API参考](https://docs.omi.me/api-reference/introduction)
- [Omi官网](https://omi.me/)

---

*🦞 撰写于2026年4月18日*
