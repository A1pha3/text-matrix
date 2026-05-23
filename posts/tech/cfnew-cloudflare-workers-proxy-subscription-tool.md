---
title: "CFnew：Cloudflare Workers 订阅转换与代理管理工具"
date: 2026-05-23T15:06:34+08:00
slug: "cfnew-cloudflare-workers-proxy-subscription-tool"
description: "CFnew 是一款运行在 Cloudflare Workers 上的订阅转换工具，支持 VLESS、Trojan、xhttp 多协议，提供图形化配置界面和全平台客户端订阅输出，当前已积累 13,360 ★。"
draft: false
categories: ["技术笔记"]
tags: ["Cloudflare Workers", "代理工具", "订阅转换", "VLESS", "Trojan"]
---

# CFnew：Cloudflare Workers 订阅转换与代理管理工具

CFnew（byJoey/cfnew）是一个运行在 Cloudflare Workers 上的订阅转换与代理节点管理工具，当前星标 13,360，Fork 6,488。作为一个在 GitHub Trending 今日上榜的项目，它的定位非常明确：**不依赖外部 sub-converter，在 Worker 内部直接生成多平台订阅配置**。

## 为什么值得看

传统订阅转换服务通常依赖第三方节点转换后端，部署者自己维护一套机场订阅，再通过 API 输出转换后的节点。CFnew 的做法是把整个流程搬到 Cloudflare Workers 里：

- 多协议节点（VLESS、Trojan、xhttp）在 Worker 内生成，不再调用外部转换服务
- 自带图形化配置面板，改完参数立即生效，无需重新部署
- 订阅格式覆盖 CLASH、SURGE、SING-BOX、LOON、QUANTUMULT X、V2RAY、Shadowrocket、STASH、NEKORAY、V2RAYNG 等主流客户端
- 支持自定义路径、多级路径、多客户端自动识别

对已经有机场订阅、想要自建管理界面的用户来说，这是一个值得测试的方案。

## 核心能力

### 多协议支持

CFnew 同时支持三种协议：

| 协议 | 默认状态 | 说明 |
|------|---------|------|
| VLESS | 启用 | 主流协议，兼容性强 |
| Trojan | 禁用 | 需要额外密码配置 |
| xhttp | 禁用 | 支持 HTTP/2 传输 |

### 订阅转换内部化

从 v2.9.8 开始，CLASH / Stash / Sing-box / Surge / Loon / Quantumult X 的配置全部由 Worker 直接生成，不再依赖任何外部 sub-converter。具体规则来源：

- CLASH 使用 Loyalsoldier `rule-providers`
- Sing-box 使用 MetaCubeX SRS
- Surge / Loon / QuanX 使用 ACL4SSR / blackmatrix7 远端规则

各策略分组均包含「策略组 + 全部节点」组合，可以直接切换到具体节点。

### 图形化配置

通过 KV 存储配置，部署者在管理界面里改完参数保存后立即生效，不需要重新触发一次部署。具体操作路径：

1. 在 Workers 中创建 KV 命名空间，绑定环境变量 `C`
2. 部署后访问 `/{UUID}` 或 `/{自定义路径}` 打开图形化面板
3. 在面板中配置协议、路径、优选 IP 等参数
4. 点击「保存全部」或按 `Ctrl+S` / `Cmd+S` 确认

配置变更通过 `c_ver` 跨 isolate 版本键实现 30 秒短窗口缓存，减少 KV 读取次数。

### 优选 IP 与节点管理

CFnew 内置 IP 优选功能，可以按地区（HK、SG、US、JP 等）筛选节点，也可以只显示延迟最低的 10 个。优选来源支持自定义 URL，也可以使用 GitHub 默认优选列表。

API 管理功能允许通过 curl 动态添加或删除优选 IP：

```bash
# 添加单个 IP
curl -X POST "https://your-worker.workers.dev/{UUID}/api/preferred-ips" \
  -H "Content-Type: application/json" \
  -d '{"ip": "1.2.3.4", "port": 443, "name": "香港节点"}'

# 批量添加
curl -X POST "https://your-worker.workers.dev/{UUID}/api/preferred-ips" \
  -H "Content-Type: application/json" \
  -d '[{"ip": "1.2.3.4", "port": 443, "name": "节点1"}]'

# 清空所有 IP
curl -X DELETE "https://your-worker.workers.dev/{UUID}/api/preferred-ips" \
  -H "Content-Type: application/json"
```

### 传输优化

v2.9.8 引用 GrainTCP 思路优化了 WebSocket/TCP 转发：

- 上行小包队列合并
- 下行小包聚合、大包直发
- 优化 VLESS 解析热路径

SOCKS5 降级超时：直连 3.5s 无数据自动走 fallback。

### ECH 支持

支持 Encrypted Client Hello（ECH），每次刷新订阅时自动获取最新 ECH 配置，启用后自动切换到"仅 TLS"模式避免 80 端口干扰。图形界面可一键开启或关闭。

## 部署步骤

CFnew 部署分 Workers 和 Pages 两条路，核心都是先设置兼容性日期，再上传代码。

### Workers 部署

1. 登录 [Cloudflare 控制台](https://dash.cloudflare.com/)
2. 进入 **Workers 和 Pages** → 创建 Worker
3. 点击 **设置** → **兼容性日期**，选择 `2026-01-20`，保存
4. 上传 CFnew 代码

### Pages 部署

1. 登录 Cloudflare 控制台
2. 进入 **Workers 和 Pages** → 创建 Pages 项目
3. 点击 **设置** → **运行时**，选择兼容性日期 `2026-01-20`
4. 创建部署并上传文件

### 基础环境变量

| 变量名 | 必需 | 说明 |
|------|------|------|
| `u` | 是 | 你的 UUID，用于访问订阅和配置界面 |
| `p` | 否 | 自定义 Proxy IP 和端口，格式 `host:port` |
| `d` | 否 | 自定义路径，如 `/mypath`，不填用 UUID 路径 |
| `s` | 否 | SOCKS5 地址，格式 `user:pass@host:port` |
| `wk` | 否 | Worker 地区，如 `SG`、`HK`、`US`、`JP` |

### 启用协议配置

| 变量名 | 说明 |
|------|------|
| `ev` | 启用 VLESS（默认 yes） |
| `et` | 启用 Trojan（默认 no） |
| `ex` | 启用 xhttp（默认 no） |
| `ech` | 启用 ECH（默认 no） |
| `alpn` | TLS ALPN 参数，留空由客户端协商 |

## 适用边界

**适合：**
- 已有机场订阅，想要自建管理面板的用户
- 需要多客户端格式输出的个人用户
- 希望订阅地址稳定、不依赖商业 sub-converter 的场景

**不适合：**
- 企业用途或大规模分发（CF Workers 有请求频率限制）
- 需要长期稳定代理服务的高流量场景
- 完全不想接触 Cloudflare 控制台配置的用户

## 阅读路径

如果想深入了解，建议按这个顺序看：

1. README 的「主要功能」和「v2.9.8 更新」章节，理解核心架构变化
2. 图形化配置和 KV 存储设置，搞清楚参数在哪改
3. API 管理接口，了解动态节点管理的可编程空间
4. 各协议配置参数，根据自己客户端选择对应格式