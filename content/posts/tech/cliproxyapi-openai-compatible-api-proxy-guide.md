---
title: "CLIProxyAPI 完整迁移与实战指南（含旧稿说明）"
date: "2026-04-12T18:00:00+08:00"
slug: cliproxyapi-openai-compatible-api-proxy-guide
description: "本文整合CLIProxyAPI核心概念、新旧版本差异、完整迁移步骤与实战示例，帮助开发者快速上手并规避版本漂移风险，旧稿链接已重定向至本文。"
draft: false
categories: ["技术笔记"]
tags: ["CLIProxyAPI", "Claude Code", "Gemini CLI", "OpenAI Codex", "API代理"]
---

## 学习目标
读完本文后，你将能够：
1. 说清CLIProxyAPI解决的核心问题
2. 区分新旧版本的关键差异，避免用过期配置踩坑
3. 独立完成从旧版本到新版本的配置迁移
4. 快速接入Claude Code、Gemini CLI等主流AI客户端

---

## 为什么需要这篇指南
CLIProxyAPI迭代速度很快，早期文章里的支持列表、默认端口、管理能力已经和当前版本不一致。很多开发者照着旧稿配到一半发现命令跑不通，或者功能对不上，就是因为版本漂移。

这篇指南有两个作用：
- 给从旧链接进来的读者一个准确的入口，不用再自己对比版本
- 给新上手CLIProxyAPI的开发者一个完整的实操路径，跳过踩坑步骤

---

## CLIProxyAPI核心价值
它解决的是多AI客户端统一接入的问题：不用给Claude Code、Gemini CLI、Codex每个都单独配API Key、单独管配额，所有客户端都走OpenAI兼容的API格式，不用改代码就能切换底层模型。内置统计、限流、多账号轮询，适合小团队或者个人多Key管理。

举个例子：你有三个Claude API Key，CLIProxyAPI可以自动轮询，避免单个Key超限；同时Gemini CLI也能通过这个代理调用，不用单独申请Gemini API。

---

## 新旧版本关键差异
如果你之前照着旧稿配置，这几个地方一定要注意：
| 功能                | 旧版本                          | 新版本                          |
|---------------------|---------------------------------|---------------------------------|
| 默认端口            | 8080                            | 3000                            |
| 多账号配置          | 只支持环境变量                  | 支持YAML配置文件+动态重载       |
| OAuth接入           | 不支持                          | 支持Claude/Gemini的OAuth2.0    |
| 管理面              | 无                              | 内置Web管理面板（端口自定义）   |
| 统计维度            | 只统计请求数                    | 按Key/按模型/按客户端统计Token |

---

## 平滑迁移步骤
### 第一步：备份旧配置
```bash
# 备份旧的环境变量配置
cp ~/.bashrc ~/.bashrc.cliproxy.bak
# 备份旧的YAML配置（如果有的话）
cp config.yaml config.yaml.bak
```

### 第二步：安装新版本
```bash
# 用npm全局安装最新版
npm install -g cliproxyapi@latest
# 验证版本
cliproxyapi --version
# 预期输出：v2.1.0（或更高版本）
```

### 第三步：迁移配置文件
新版本用YAML做主要配置，把旧的环境变量转成对应的配置项：
```yaml
# config.yaml 示例
port: 3000
keys:
  - "sk-ant-xxx"  # Claude API Key
  - "sk-gemini-xxx" # Gemini API Key
models:
  - "claude-3-7-sonnet-20250219"
  - "gemini-2.5-pro-preview-05-06"
clients:
  - name: "Claude Code"
    type: "openai-compatible"
  - name: "Gemini CLI"
    type: "openai-compatible"
```

### 第四步：验证接入
```bash
# 启动代理
cliproxyapi start -c config.yaml
# 用curl测试接口
curl http://localhost:3000/v1/models \
  -H "Authorization: Bearer sk-ant-xxx"
# 预期输出：模型列表JSON
```

### 第五步：接入客户端
以Claude Code为例，把API Base URL改成`http://localhost:3000/v1`，API Key填配置文件里的任意一个Key即可。

---

## 常见问题
### Q1：旧版本的配置还能用吗？
A：环境变量配置还能兼容，但建议转到YAML配置，支持更多新功能。如果直接用旧环境变量启动，会报「弃用警告」，不影响基本使用，但统计、多账号功能用不了。

### Q2：迁移后请求报错「model not found」？
A：检查配置文件里的`models`字段是否和实际订阅的模型匹配，新版本不会自动拉取可用模型，需要手动配置。

### Q3：Web管理面板怎么开？
A：在配置文件里加`management_port: 3001`，启动后访问`http://localhost:3001`即可，默认不需要账号密码，建议内网使用。

---

## 进一步学习
- 官方完整文档：[CLIProxyAPI Docs](https://cliproxyapi.dev/docs)
- 进阶配置：多账号轮询策略、限流规则、OAuth接入
- 生态工具：和OpenWebUI、Lobechat的配合方式
