---
title: "public-apis: 免费API聚合器 —— 427K星背后的宝藏资源库"
date: "2026-04-28T20:00:00+08:00"
slug: "public-apis-free-api-aggregator"
description: "public-apis 是一个聚合了超过1800+免费API的资源列表，涵盖动物、动漫、反恶意软件、艺术设计、区块链、货币兑换、机器学习、音乐、新闻、天气等数十个分类。本文深入解析其内容结构、使用方法及常见API推荐。"
categories: ["技术笔记"]
tags: ["public-apis", "API", "免费API", "开发者资源", "开源"]
author: "钳岳星君"
---

# public-apis: 免费 API 聚合器

## 学习目标

阅读本文后，你应该能够：

1. **了解 public-apis 项目**：理解其定位、覆盖范围和社区维护机制
2. **快速查找 API**：掌握按分类浏览和关键词搜索的方法
3. **正确使用 API**：理解 Auth 类型、HTTPS 和 CORS 对实际使用的影响
4. **评估 API 适用性**：判断某个 API 是否适合你的项目（稳定性、认证要求、CORS 限制）
5. **贡献和维护**：了解如何向 public-apis 提交新的 API 或报告过期链接

## 目录

- [项目概览](#项目概览)
- [核心特点](#核心特点)
  - [分类齐全](#1-分类齐全)
  - [结构统一](#2-结构统一)
  - [持续更新](#3-持续更新)
- [使用方法](#使用方法)
  - [快速查找](#快速查找)
  - [使用示例](#使用示例)
- [精选 API 推荐](#精选-api-推荐)
  - [机器学习类](#机器学习类)
  - [天气类](#天气类)
  - [动漫类](#动漫类)
- [注意事项](#注意事项)
  - [CORS 限制](#cors-限制)
  - [认证要求](#认证要求)
  - [稳定性](#稳定性)
- [适用场景](#适用场景)
- [常见问题](#常见问题)
- [自测题](#自测题)
- [练习](#练习)
- [进阶路径](#进阶路径)
- [资料口径说明](#资料口径说明)
- [总结](#总结)

## 项目概览

**public-apis**（https://github.com/public-apis/public-apis）是GitHub上最受欢迎的免费API聚合仓库之一，**星标数超过42.7万**，Fork数达4.6万，被广泛应用于教学、原型开发、创新项目等场景。

| 项目信息 | |
|----------|---|
| **星标** | 427,495 ⭐ |
| **Fork** | 46,707 |
| **语言** | Python |
| **创建时间** | 2016-03-20 |
| **维护者** | public-apis 组织 + 社区贡献者 |
| **许可证** | MIT |

该项目由社区志愿者维护，所有 API 均为免费或提供免费层，帮助开发者快速找到可用的 Web API 资源。

## 核心特点

### 1. 分类齐全
项目将 API 按功能分为**40+个分类**，覆盖：

- **动物**（猫咪图片、狗狗 API、物种保护）
- **动漫**（AnimeDB、Jikan、MyAnimeList）
- **反恶意软件**（VirusTotal、AbuseIPDB、URLhaus）
- **艺术与设计**（IconFinder、Dribbble、ColourLovers）
- **区块链**（CoinGecko、Etherscan）
- **货币兑换**（Fixer、Exchangerate Host）
- **机器学习**（OpenAI、Hugging Face）
- **音乐**（Spotify、Apple Music）
- **新闻**（NewsAPI、Bing News）
- **天气**（OpenWeatherMap、Weatherstack）
- **更多**：日历、云存储、加密货币、环境、金融、食品、游戏、地理编码、政府、健康、职位、摄影、社交、体育、追踪、交通、视频...

### 2. 结构统一
每个 API 条目包含：
- **API 名称** + 官方链接
- **描述**：一句话说明用途
- **Auth 类型**：API Key / OAuth / 无需认证
- **HTTPS 支持**：是/否
- **CORS 支持**：是/否/未知

### 3. 持续更新
社区贡献者持续提交新的 API 和维护现有条目，确保资源的时效性。

## 使用方法

### 快速查找

1. **浏览分类**：在 README 中直接定位所需分类
2. **搜索关键词**：在 GitHub 页面按 `T` 键调出文件搜索，输入关键词
3. **提交 Issue**：若未找到所需 API，可提交 Issue 请求添加

### 使用示例

以获取随机猫咪图片为例：

```markdown
| [Cats](https://docs.thecatapi.com/) | Pictures of cats from Tumblr | `apiKey` | Yes | No |
```

访问 `https://docs.thecatapi.com/` 了解如何使用该 API。

## 精选 API 推荐

### 机器学习类

| API | 描述 | Auth | HTTPS |
|-----|------|------|-------|
| OpenAI | GPT 模型 API | `apiKey` | Yes |
| Hugging Face | 预训练模型 | `apiKey` | Yes |
| Coqui | 语音识别/TTS | No | Yes |

### 天气类

| API | 描述 | Auth | HTTPS |
|-----|------|------|-------|
| OpenWeatherMap | 全球天气预报 | `apiKey` | Yes |
| Weatherstack | 天气数据 | `apiKey` | Yes |
| Aviationstack | 航班天气 | `apiKey` | Yes |

### 动漫类

| API | 描述 | Auth | HTTPS |
|-----|------|------|-------|
| Jikan | 免费 MyAnimeList API | No | Yes |
| AniList | 动漫发现与追踪 | `OAuth` | Yes |
| NekosBest | 动漫图片 | No | Yes |

## 注意事项

### CORS 限制
部分 API 不支持 CORS（即前端直接调用会失败）。使用前请注意：
- 标记为 `Yes` 的可直接从浏览器调用
- 标记为 `No` 的需通过后端代理
- 标记为 `Unknown` 的需实际测试

### 认证要求
- **无认证**：可直接使用，适合公开数据
- **API Key**：需在官网注册获取，通常有免费额度
- **OAuth**：需开发者账号和授权流程

### 稳定性
社区维护的 API 质量参差不齐，正式项目使用前请：
1. 查看 API 的维护状态
2. 检查最后一次更新时间
3. 测试 API 响应稳定性
4. 关注 Issue 中是否有大量问题

## 适用场景

- **快速原型开发**：无需自己爬取数据，直接调用现成 API
- **学习与实验**：探索不同类型的 Web API
- **Hackathon**：快速集成第三方服务
- **教学演示**：展示 API 调用和数据获取流程

## 常见问题

### Q1: public-apis 中的 API 真的都免费吗？
不完全是。项目名为"public-apis"，但部分 API 仅有免费层（Free tier），超出额度后需要付费。使用前请查看 API 官网的定价页。

### Q2: 为什么有些 API 无法访问？
可能原因：
1. API 已停用或变更（社区维护有延迟）
2. 需要 API Key 但未获取
3. CORS 限制（前端直接调用失败）
4. 网络限制（某些 API 在某些地区无法访问）

### Q3: 如何判断一个 API 是否稳定？
建议：
1. 查看 API 官网的状态页（Status page）
2. 搜索该 API 的 Downtime 历史（如 downdetector.com）
3. 查看 public-apis 的 Issue 中是否有相关报告
4. 自己编写简单的健康检查脚本

### Q4: 可以在生产环境中使用这些 API 吗？
取决于具体 API。建议：
1. 优先选择有 SLA（服务等级协议）的付费 API
2. 为免费 API 设计降级方案（如缓存、备用 API）
3. 监控 API 的可用性和响应时间
4. 避免过度依赖单一免费 API

## 自测题

1. **public-apis 项目的主要价值是什么？**
   <details>
   <summary>查看答案</summary>
   聚合了 1800+ 免费 API，覆盖 40+ 分类，帮助开发者快速找到可用的 Web API 资源。
   </details>

2. **CORS 限制会影响哪种调用方式？**
   <details>
   <summary>查看答案</summary>
   影响前端浏览器直接调用。如果 API 不支持 CORS，需通过后端代理转发请求。
   </details>

3. **使用 public-apis 中的 API 前，应该检查哪些方面？**
   <details>
   <summary>查看答案</summary>
   1. Auth 类型（是否需要 API Key 或 OAuth）
   2. HTTPS 支持（是否加密传输）
   3. CORS 支持（是否可直接从浏览器调用）
   4. API 维护状态和稳定性
   </details>

4. **如果你正在开发一个前端项目，需要调用一个不支持 CORS 的 API，有哪些解决方案？**
   <details>
   <summary>查看答案</summary>
   1. 通过自己的后端服务器代理请求
   2. 使用云端函数（如 AWS Lambda、Vercel Edge Functions）作为代理
   3. 联系 API 提供方请求开启 CORS
   4. 寻找支持 CORS 的替代 API
   </details>

5. **为什么在使用免费 API 时建议设计降级方案？**
   <details>
   <summary>查看答案</summary>
   免费 API 可能有速率限制、停机维护、或突然停止服务。降级方案（如缓存、备用 API）可以确保你的应用在这些情况下仍能正常工作。
   </details>

## 练习

### 练习 1：查找并测试一个天气 API
**目标**：从 public-apis 中找到一个天气类 API，注册获取 API Key，然后编写代码调用它。

**步骤**：
1. 在 public-apis README 中找到"天气"分类
2. 选择一个 API（如 OpenWeatherMap）
3. 访问其官网注册并获取免费 API Key
4. 编写代码调用该 API 获取当前天气
5. 处理可能出现的错误（如网络错误、API 限制）

**参考答案**：
```python
import requests

def get_weather(city, api_key):
    url = f"https://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": city,
        "appid": api_key,
        "units": "metric"
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        return data["main"]["temp"]
    else:
        raise Exception(f"API 调用失败：{response.status_code}")

# 使用示例
api_key = "YOUR_API_KEY"
temperature = get_weather("Beijing", api_key)
print(f"北京当前温度：{temperature}°C")
```

### 练习 2：构建一个 API 代理服务
**目标**：创建一个简单的后端代理服务，解决 CORS 限制问题。

**步骤**：
1. 选择一个不支持 CORS 的 API
2. 使用 Python Flask 或 Node.js Express 创建一个简单的代理服务器
3. 在代理服务器中调用目标 API
4. 将结果返回给前端，并设置适当的 CORS 头

**参考答案**：
```python
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests

app = Flask(__name__)
CORS(app)  # 允许所有来源的跨域请求

@app.route('/proxy/weather')
def proxy_weather():
    city = request.args.get('city')
    api_key = "YOUR_API_KEY"
    url = f"https://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": city,
        "appid": api_key,
        "units": "metric"
    }
    response = requests.get(url, params=params)
    return jsonify(response.json())

if __name__ == '__main__':
    app.run(port=5000)
```

### 练习 3：评估一个 API 的适用性
**目标**：选择一个 API，从多个维度评估它是否适合你的项目。

**评估维度**：
1. **功能匹配度**：API 提供的功能是否满足需求？
2. **稳定性**：API 的 uptime 历史如何？
3. **速率限制**：免费层允许的请求频率是否足够？
4. **文档质量**：文档是否清晰、完整、有示例？
5. **社区支持**：是否有活跃的社区、Stack Overflow 讨论、或 GitHub Issue？
6. **数据质量**：返回的数据是否准确、及时更新？

**输出**：一份简短的评估报告（200-300 字）

## 进阶路径

如果你想深入学习和使用 Web API，可以按照以下路径进阶：

### Level 1：API 使用者 ⭐
- 能够使用 public-apis 中的 API
- 理解 HTTP 基础（GET/POST、状态码、Header）
- 能够处理 API 返回的数据（JSON/XML 解析）

### Level 2：API 集成者 ⭐⭐
- 能够处理 API 认证（API Key、OAuth）
- 能够实现错误处理和重试机制
- 能够设计简单的缓存策略

### Level 3：API 架构者 ⭐⭐⭐
- 能够设计自己的 API（RESTful、GraphQL）
- 能够实现 API 网关、速率限制、认证
- 能够选择和配置 API 文档工具（Swagger、Postman）

### Level 4：API 生态构建者 ⭐⭐⭐⭐
- 能够设计和维护开放的 API 平台
- 能够建立 API 生态系统（开发者社区、文档、SDK）
- 能够制定 API 版本管理和平滑升级策略

## 资料口径说明

本文档基于以下来源编写，请注意其局限性：

1. **信息来源**：主要基于 public-apis GitHub 仓库的 README（2026-04-28 访问）。该仓库由社区维护，信息可能有延迟或错误。
2. **API 状态时效性**：API 的可用性、认证要求、CORS 支持可能随时间变化。使用前请务必访问 API 官网确认。
3. **未实际测试**：本文档未逐一测试列出的 API。实际使用时可能会遇到文档中未说明的问题。
4. **分类主观性**：API 的分类由 public-apis 维护者决定，可能与你的理解不完全一致。
5. **免费定义**：本文档中的"免费"指有免费层或完全免费。具体限制请查看各 API 官网。
6. **更新频率**：public-apis 仓库每天都有新的提交，本文档无法实时同步最新状态。

## 总结

public-apis 是开发者必备的资源库之一，聚合了 1800+免费 API，分类清晰、结构统一。无论是寻找某个特定领域的 API，还是探索新的开发可能性，都是极佳的起点。

建议收藏并在需要时定向查询，而非一次性浏览全部内容。

---

**项目地址**：https://github.com/public-apis/public-apis

**相关项目**：
- [public-api](https://github.com/davemachado/public-api) - public-apis 的官方 API 接口
- [public-apis-cli](https://github.com/public-apis/public-apis-cli) - 命令行工具
