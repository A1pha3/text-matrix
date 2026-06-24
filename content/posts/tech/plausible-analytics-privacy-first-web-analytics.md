---
title: "Plausible Analytics：隐私优先的开源网站分析利器"
date: "2026-05-18T19:56:00+08:00"
categories: ["技术笔记"]
tags: ["网站分析", "隐私保护", "Elixir", "GDPR合规", "Google Analytics替代", "开源"]
slug: "plausible-analytics-privacy-first-web-analytics"
description: "Plausible Analytics 是一款开源、隐私优先的无 Cookie 网站分析工具，轻量级脚本、完全兼容 GDPR/CCPA/PECR，是 Google Analytics 的优秀替代方案，支持自托管社区版。"
---

## 目录

- [学习目标](#学习目标)
- [1. 为什么需要隐私优先的分析工具](#1-为什么需要隐私优先的分析工具)
- [2. Plausible 是什么](#2-plausible-是什么)
- [3. 云托管版：快速上手](#3-云托管版快速上手)
- [4. 自托管版：从零部署](#4-自托管版从零部署)
- [5. 核心功能详解](#5-核心功能详解)
- [6. 技术架构：Elixir + ClickHouse](#6-技术架构elixir--clickhouse)
- [7. 云托管 vs 自托管对比](#7-云托管-vs-自托管对比)
- [8. 常见问题](#8-常见问题)
- [9. 总结](#9-总结)
- [自测检查](#自测检查)
- [进阶路径](#进阶路径)

---

## 学习目标

阅读本文并完成练习后，你将能够：

- 理解为什么传统网站分析工具（如 Google Analytics）存在隐私问题
- 在网站上正确部署 Plausible 追踪脚本
- 区分云托管版和自托管版的适用场景
- 使用 Events API 发送自定义事件
- 配置 Google Search Console 集成
- 在 Docker 环境中部署自托管版 Plausible
- 排查常见部署问题（脚本不生效、数据不显示等）

**预计阅读时间**：25 分钟
**实践时间**：40 分钟

---

## 1. 为什么需要隐私优先的分析工具

### 1.1 传统分析工具的隐私困境

Google Analytics（GA）是最流行的网站分析工具，但它有个核心问题：**它用访问者的个人数据来给自己做广告定向**。

具体来说：

- GA 会存储访问者的 IP 地址、User-Agent、设备信息
- 这些数据会被 Google 用来完善广告画像
- 为了合规，网站管理员必须在页面上显示 Cookie 提示条（Cookie Banner），让用户"同意被追踪"

### 1.2 隐私法规的压力

全球多个隐私法规对网站分析提出了严格要求：

| 法规 | 适用地区 | 核心要求 |
|------|----------|----------|
| **GDPR** | 欧盟 | 必须获得用户明确同意才能存储个人数据 |
| **CCPA** | 美国加州 | 用户有权选择不出售其个人数据 |
| **PECR** | 英国/欧盟 | Cookie 必须获得同意才能设置 |

如果你的网站用了 Google Analytics，**大多数情况下需要显示 Cookie 提示条**，否则就违法了。

### 1.3 Plausible 的解决思路

Plausible 的核心主张：**测量流量，而非个人**。

它不存储个人数据、不记录 IP 地址、不使用 Cookie 或持久化标识符。这意味着：

- **不需要 Cookie 提示条**（很多司法管辖区豁免）
- 访问者的隐私得到尊重
- 网站管理员不用担心合规风险

---

## 2. Plausible 是什么

[Plausible Analytics](https://plausible.io) 是一款开源、隐私优先的网站分析工具。

### 2.1 核心特点

| 特点 | 说明 |
|------|------|
| **无 Cookie** | 不使用 Cookie，不存储个人数据 |
| **轻量级脚本** | 约 1KB（GA 约 45KB），不拖慢网站 |
| **GDPR 合规** | 不需要 Cookie 提示条（多数地区） |
| **开源** | 社区版基于 AGPLv3 开源 |
| **自有数据** | 自托管版可以直接访问原始数据 |

### 2.2 与 Google Analytics 的核心区别

| 对比项 | Google Analytics | Plausible Analytics |
|--------|-------------------|----------------------|
| 数据存储 | Google 服务器 | 可选（云托管或自托管） |
| 数据用途 | Google 用于广告定向 | 仅用于你的网站分析 |
| Cookie | 需要 | 不需要 |
| Cookie 提示条 | 多数情况下需要 | 多数地区不需要 |
| 脚本大小 | ~45KB | ~1KB |
| 定价 | 免费（有使用限制）| 云托管付费 / 自托管免费 |

### 2.3 项目数据

| 指标 | 数值 |
|------|------|
| GitHub Stars | **25,705+** |
| 编程语言 | Elixir + TypeScript |
| 开源许可 | AGPLv3（社区版）|
| 最新版本 | 持续更新中 |

---

## 3. 云托管版：快速上手

### 3.1 注册账号

1. 访问 [plausible.io](https://plausible.io)
2. 点击 "Start free trial"（14 天免费试用）
3. 填入邮箱和密码
4. 验证邮箱后登录

### 3.2 添加网站

1. 登录后点击 "Add a site"
2. 填入你的域名（如 `example.com`）
3. 选择时区
4. 点击 "Add site"

系统会给你一段追踪代码：

```html
<!-- 将以下代码放在 </head> 之前 -->
<script defer data-domain="example.com" src="https://plausible.io/js/script.js"></script>
```

### 3.3 部署追踪代码

**方式一：直接编辑 HTML**

将上面的 `<script>` 标签放到你网站的 `</head>` 之前。

**方式二：用 Google Tag Manager**

1. 在 GTM 中创建新的 Tag
2. 选择 "Custom HTML"
3. 粘贴 Plausible 提供的脚本
4. 设置 Trigger 为 "All Pages"
5. 保存并发布

**方式三：React/Vue/Next.js（SPA）**

对于单页应用，需要手动触发页面浏览事件：

```javascript
// React（使用 useEffect）
import { useEffect } from 'react';
import { useLocation } from 'react-router-dom';

function App() {
  const location = useLocation();

  useEffect(() => {
    // Plausible 会自动处理 SPA 的页面切换
    // 但如果你用了 history API，需要手动推送
    if (window.plausible) {
      window.plausible('pageview', { u: window.location.href });
    }
  }, [location]);
}
```

### 3.4 验证部署

部署后，访问你的网站，然后：

1. 登录 Plausible 仪表盘
2. 选择你的网站
3. 应该能看到实时访问数据

如果看不到数据，参考 [8. 常见问题](#8-常见问题)。

---

## 4. 自托管版：从零部署

如果你不想把数据交给第三方，可以自托管 Plausible。

### 4.1 系统要求

| 组件 | 最低要求 |
|--------|----------|
| CPU | 2 核 |
| 内存 | 4GB RAM |
| 存储 | 20GB（取决于流量） |
| 操作系统 | Linux（推荐 Ubuntu 20.04+）|
| Docker | 20.10+ |

### 4.2 使用 Docker Compose 部署（推荐）

**步骤 1：克隆官方自托管仓库**

```bash
git clone https://github.com/plausible/analytics.git
cd analytics

# 切换到稳定版本
git checkout v2.0.0  # 查看最新 release
```

**步骤 2：配置环境变量**

```bash
# 复制示例配置
cp .env.example .env

# 编辑配置
vim .env
```

关键配置项：

```bash
# 数据库连接
DATABASE_URL=postgresql://postgres:postgres@db:5432/plausible

# ClickHouse 连接
CLICKHOUSE_DATABASE_URL=http://clickhouse:8123/plausible

# 域名（重要！）
BASE_URL=https://analytics.yourdomain.com

# 邮件配置（用于发送邀请邮件）
MAILER_EMAIL=your-email@gmail.com
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

**步骤 3：启动服务**

```bash
# 构建并启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 等待所有服务启动（约 1-2 分钟）
```

**步骤 4：创建管理员账号**

```bash
# 进入 app 容器
docker-compose exec app /bin/sh

# 在容器内执行
/usr/bin/entrypoint.sh /app/bin/plausible create_user "admin@example.com" "your-password"
```

**步骤 5：访问仪表盘**

打开浏览器，访问 `https://analytics.yourdomain.com`（需要提前配置 Nginx/Caddy 反向代理）。

### 4.3 使用预构建 Docker 镜像（更简单）

Plausible 社区维护了预构建的 Docker 镜像：

```bash
# 使用社区维护的 docker-compose 配置
curl -L https://raw.githubusercontent.com/plausible/hosting/master/docker-compose.yml -o docker-compose.yml

# 启动
docker-compose up -d
```

详细文档：[Plausible Self-hosting Guide](https://plausible.io/docs/self-hosting)

---

## 5. 核心功能详解

### 5.1 实时流量监控

Plausible 仪表盘首页显示：

- **当前在线人数**：实时更新
- **访问量（Visits）**：去重后的访问次数
- **独立访客（Visitors）**：去重后的访客数
- **页面浏览量（Pageviews）**：总页面浏览次数
- **跳出率（Bounce Rate）**：只访问一个页面就离开的比例
- **访问时长（Visit Duration）**：平均访问时长

### 5.2 流量来源（Traffic Sources）

查看访问者从哪来：

| 来源类型 | 说明 |
|----------|------|
| **Search** | 搜索引擎（Google、Bing、DuckDuckGo 等）|
| **Social** | 社交媒体（Twitter、Facebook、LinkedIn 等）|
| **Referrals** | 其他网站的反向链接 |
| **Direct** | 直接输入网址或书签访问 |
| **Email** | 邮件中的链接 |

### 5.3 页面热度（Top Pages）

显示哪些页面最受欢迎，以及每个页面的：

- 独立访客数
- 页面浏览量
- 平均停留时间
- 跳出率

### 5.4 地理位置和設備

- **国家/地区**：访问者来自哪些国家
- **设备类型**：桌面端 vs 移动端 vs 平板
- **操作系统**：Windows、macOS、iOS、Android 等
- **浏览器**：Chrome、Firefox、Safari、Edge 等

### 5.5 目标追踪（Goals）

你可以定义"目标"（Goal），追踪关键转化事件：

**示例：追踪表单提交**

```javascript
// 在表单提交成功后的回调中
window.plausible('Signup', { props: { plan: 'free' } });
```

然后在 Plausible 仪表盘中：

1. 点击 "Goals" 标签
2. 添加目标 "Signup"
3. 查看转化漏斗和转化率

### 5.6 自定义事件（Events API）

除了页面浏览，你还可以追踪自定义事件：

```javascript
// 追踪按钮点击
document.getElementById('buy-button').addEventListener('click', () => {
  window.plausible('Buy', { props: { product: 'ebook', price: '29.99' } });
});
```

**服务端发送事件（推荐用于关键业务事件）**：

```bash
# 使用 Events API（需要 API Key）
curl -X POST https://plausible.io/api/event \
  -H "Content-Type: application/json" \
  -d '{
    "domain": "example.com",
    "name": "payment_completed",
    "props": { "amount": "99.99", "currency": "USD" },
    "api_key": "your-api-key"
  }'
```

### 5.7 Google Search Console 集成

Plausible 可以直接拉取 Google Search Console 的数据，在仪表盘中查看：

1. 进入网站设置
2. 点击 "Integrations"
3. 选择 "Google Search Console"
4. 授权 Plausible 访问你的 GSC 数据
5. 在仪表盘中查看关键词排名和点击量

---

## 6. 技术架构：Elixir + ClickHouse

Plausible 使用了一套相当独特的技术栈：

### 6.1 技术栈概览

| 组件 | 技术 | 作用 |
|--------|------|------|
| **后端** | Elixir + Phoenix | 处理 HTTP 请求、Events API、仪表盘后端 |
| **主数据库** | PostgreSQ L | 存储站点配置、用户账号、目标定义 |
| **分析数据库** | ClickHouse | 存储访问事件，支持快速聚合查询 |
| **前端** | React + TailwindCSS | 仪表盘 UI |
| **缓存** | Redis（可选）| 缓存常用查询结果 |

### 6.2 为什么用 ClickHouse？

Plausible 需要处理的查询类型：

- "过去 30 天每天有多少访客？"（时间序列聚合）
- "哪个国家带来的流量最多？"（分组聚合）
- "Referral 流量top 10 来源是哪些？"（排序 + 限制）

这些查询在传统关系型数据库（如 PostgreSQ L）上会很慢，因为数据量会随访问量线性增长。

**ClickHouse 的优势**：

- 列式存储，聚合查询极快
- 压缩率高，存储成本低
- 水平扩展能力强

对于需要承载日均百万级访问的网站来说，ClickHouse 是必需品。

### 6.3 数据流示意

```
访问者浏览器
    ↓（加载 script.js）
    ↓（发送页面浏览事件）
Plausible 后端（Elixir + Phoenix）
    ↓（写入）
ClickHouse（分析数据） + PostgreSQ L（配置数据）
    ↓（查询）
React 仪表盘（数据可视化）
```

---

## 7. 云托管 vs 自托管对比

| 对比项 | Plausible Cloud | Plausible 社区版（自托管） |
|--------|----------------|--------------------------|
| **基础设施管理** | 官方托管，2 分钟上线，高可用 | 完全自管理，需自备服务器 |
| **功能更新频率** | 每周多次更新，含全部高级功能 | 每年约两次更新，高级功能受限 |
| **Bot 过滤** | 高级 Bot 过滤，排除约 32K 数据中心 IP 段 | 基础过滤，仅基于 User-Agent |
| **数据可移植性** | 聚合数据查看，API/CSV 导出 | 可直接访问 ClickHouse 原始数据 |
| **数据主权** | 数据留存在 EU 境内 | 可部署在任意国家/地区 |
| **成本** | 按月付费（$9/月起，取决于流量）| 服务器成本 + 运维时间 |

### 7.1 高级 Bot 过滤的价值

Plausible Cloud 的算法能自动识别并排除非人类流量模式，默认排除约 32,000 个数据中心 IP 段。

**为什么这很重要？** 如果你用基础过滤（只看 User-Agent），很多爬虫和bot 会混进统计数据，导致"访客数"虚高。高级过滤能显著提升数据的纯净度。

### 7.2 如何选择？

**选云托管，如果你：**

- 不想管服务器
- 需要最新功能
- 流量不大（每月 10 万次页面浏览以下成本可控）

**选自托管，如果你：**

- 有合规要求（数据不能出境内）
- 流量很大（云托管成本已经超过服务器成本）
- 想完全掌控数据（直接查 ClickHouse）

---

## 8. 常见问题

### 8.1 部署后仪表盘不显示数据

**症状**：已添加脚本，但 Plausible 仪表盘没有数据。

**排查步骤**：

1. **检查脚本是否加载成功**

   在浏览器中打开你的网站，然后按 F12 打开开发者工具：

   ```javascript
   // 在 Console 中运行
   console.log(window.plausible);
   // 应该输出一个函数，而不是 undefined
   ```

2. **检查 AdBlock 是否拦截**

   Plausible 的脚本域名（`plausible.io`）可能被某些广告拦截器屏蔽。

   解决方案：使用自定义域名代理（[文档](https://plausible.io/docs/proxy/introduction)）。

3. **检查 `data-domain` 是否正确**

   ```html
   <!-- 错误示例 -->
   <script defer data-domain="wrong-domain.com" src="..."></script>

   <!-- 正确示例 -->
   <script defer data-domain="example.com" src="..."></script>
   ```

### 8.2 自托管版启动失败

**症状**：`docker-compose up` 后访问 `localhost:8000` 显示 502 错误。

**排查步骤**：

```bash
# 1. 检查所有容器是否正常运行
docker-compose ps

# 2. 查看 app 容器日志
docker-compose logs app

# 3. 常见错误：数据库连接失败
# 解决方案：等待 PostgreSQ L 完全启动（约 30 秒）
# 或者增加 app 服务的 depends_on 等待时间
```

### 8.3 想停止收集数据，如何移除脚本？

直接从网站 HTML 中删除 Plausible 的 `<script>` 标签即可。不需要在 Plausible 后台做额外操作。

**如果想删除已收集的数据**：

1. 登录 Plausible
2. 进入网站设置
3. 点击 "Danger zone"
4. 选择 "Delete site"（会删除该网站的所有历史数据）

### 8.4 自托管版如何升级？

```bash
# 1. 拉取最新代码
cd /path/to/analytics
git pull origin master

# 2. 重新构建 Docker 镜像
docker-compose build

# 3. 运行数据库迁移（如果有）
docker-compose run --rm app /app/bin/plausible ecto.migrate

# 4. 重启服务
docker-compose down && docker-compose up -d
```

### 8.5 如何导出我的数据？

**云托管版**：

1. 进入网站仪表盘
2. 点击右上角 "Export"
3. 选择导出格式（CSV 或 JSON）
4. 下载文件

**自托管版**：

直接查询 ClickHouse：

```bash
# 进入 ClickHouse 容器
docker-compose exec clickhouse clickhouse-client

# 查询过去 30 天的页面浏览
SELECT toDate(time) as date, count(*) as views
FROM events
WHERE time >= now() - INTERVAL 30 DAY
GROUP BY date
ORDER BY date;
```

---

## 9. 总结

Plausible Analytics 为隐私优先的网站分析提供了一个出色的解决方案。

**核心价值**：

- **合规**：不需要 Cookie 提示条，尊重访问者隐私
- **轻量**：1KB 脚本，不拖慢网站
- **开源**：社区版免费自托管，数据完全自主
- **精准**：高级 Bot 过滤，数据纯净度高

**适用场景**：

- 个人博客（不想用 Google Analytics 的隐私负担）
- 企业官网（有 GDPR 合规需求）
- SaaS 产品（需要追踪转化漏斗）
- 电商网站（需要自定义事件追踪）

**官方资源**：

- GitHub：https://github.com/plausible/analytics
- 官方文档：https://plausible.io/docs
- 自托管指南：https://plausible.io/docs/self-hosting
- 社区论坛：https://github.com/plausible/analytics/discussions

---

## 自测检查

完成阅读后，请确认你能回答以下问题：

- [ ] Plausible 为什么不需要 Cookie 提示条？
- [ ] 云托管版和自托管版的核心区别是什么？
- [ ] 如何在 React/Vue 等 SPA 中正确追踪页面切换？
- [ ] Events API 和页面浏览自动追踪的区别？
- [ ] ClickHouse 在 Plausible 架构中扮演什么角色？
- [ ] 如何排查仪表盘不显示数据的问题？
- [ ] 自托管版升级的正确步骤是什么？

---

## 进阶路径

**如果你完成了本文的学习，可以继续探索：**

1. **自定义部署代理**：配置自定义域名代理 Plausible 脚本，避免被 AdBlock 拦截（[文档](https://plausible.io/docs/proxy/introduction)）
2. **深入 ClickHouse**：学习如何直接查询 Plausible 的 ClickHouse 数据库，构建自定义报表
3. **对比其他隐私分析工具**：了解 [Umami](https://umami.is/)、[Matomo](https://matomo.org/)、[Fathom](https://usefathom.com/) 的优缺点
4. **集成到 CI/CD**：将 Plausible 部署自动化（Terraform、Ansible 等）
5. **自定义仪表盘**：基于 Plausible Stats API 构建自己的数据看板

**推荐阅读**：

- [Plausible 官方文档](https://plausible.io/docs)
- [ClickHouse 官方文档](https://clickhouse.com/docs)
- [GDPR 与网站分析：合规指南](https://gdpr.eu/)
- [为什么 Cookie 提示条是个糟糕的用户体验](https://plausible.io/blog/google-analytics-cookie-banner)

---

## 练习

### 练习 1：部署 Plausible 脚本（预计 15 分钟）

在你自己的网站（或本地测试页面）上部署 Plausible 追踪脚本，然后在仪表盘中确认能看到实时访问数据。

**验收标准**：

- 脚本加载成功（浏览器开发者工具 Console 中 `window.plausible` 是一个函数）
- Plausible 仪表盘显示你的访问记录

### 练习 2：发送自定义事件（预计 10 分钟）

在你的网站上部署后，添加一段 JavaScript 代码，在用户点击某个按钮时发送自定义事件。

```html
<button id="demo-button">点击我</button>

<script>
document.getElementById('demo-button').addEventListener('click', () => {
  window.plausible('DemoButtonClick', { props: { location: 'homepage' } });
});
</script>
```

**验收标准**：Plausible 仪表盘的 "Goals" 或 "Custom Events" 中能看到 `DemoButtonClick` 事件。

### 练习 3：自托管版部署（预计 30 分钟）

在一台 Linux 服务器（或本地虚拟机）上，用 Docker Compose 部署 Plausible 社区版。

**验收标准**：

- `docker-compose ps` 显示所有服务正常运行
- 能访问 Plausible 仪表盘网页
- 能创建管理员账号并登录

### 练习 4：查询 ClickHouse 原始数据（预计 10 分钟）

如果你完成了练习 3，尝试直接查询 ClickHouse 数据库，获取过去 7 天的页面浏览量。

```bash
docker-compose exec clickhouse clickhouse-client

# 在 ClickHouse 客户端中运行：
SELECT toDate(time) as date, count(*) as views
FROM events
WHERE time >= now() - INTERVAL 7 DAY
GROUP BY date
ORDER BY date;
```

**验收标准**：能成功执行查询并看到按日期聚合的页面浏览量数据。
