---
title: "GitHub Pages 自定义域名配置指南"
date: 2026-03-23T10:00:00+08:00
draft: false
---

# GitHub Pages 自定义域名配置指南 ⭐⭐ 核心概念

> **目标读者**：已成功部署 GitHub Pages，希望使用自己购买的域名（如 `example.com`）替代默认 `github.io` 域名的使用者。
> **核心问题**：什么是 Apex 域名和子域名？如何在 DNS 服务商和 GitHub 中正确配置它们？

---

## 🎯 本节目标

完成本教程后，你将能够：
- [ ] 理解 Apex 域名（顶级域名）与子域名（如 www）的区别。
- [ ] 在 DNS 提供商处正确配置 A 记录或 CNAME 记录。
- [ ] 在 GitHub 仓库中绑定自定义域名并开启 HTTPS。

---

## 📝 概念定义

### 什么是自定义域名？

默认情况下，GitHub Pages 提供的网址类似 `https://<用户名>.github.io/<仓库名>/`。自定义域名允许你将这个地址替换为你自己拥有的域名（例如 `https://example.com` 或 `https://blog.example.com`）。

### 两类常见的自定义域名

在配置前，我们需要先理解两种类型的域名：

1. **Apex 域名（顶级域名/根域名）**：
   - **长什么样**：`example.com`（不带任何前缀）。
   - **适用场景**：你希望用户直接输入主域名就能访问你的站点。
   - **配置方式**：通常需要配置 **A 记录** 或 **ALIAS/ANAME 记录**。

2. **子域名（Subdomain）**：
   - **长什么样**：`www.example.com` 或 `blog.example.com`。
   - **适用场景**：`www` 是最常见的子域名；或者你想把主域名留给主站，用 `blog` 子域名专门做博客。
   - **配置方式**：必须配置 **CNAME 记录**。

> 💡 **最佳实践**：GitHub 强烈建议，如果你使用了 Apex 域名（`example.com`），**最好同时配置** `www` 子域名（`www.example.com`）。GitHub Pages 会自动在它们之间建立跳转（Redirect），让用户访问哪个都能到达你的网站。

---

## 🚀 步骤指南

以下步骤分为 DNS 服务商配置和 GitHub 配置两部分。请确保你已经拥有一个域名，并能登录你的域名解析控制台（如阿里云、腾讯云、Cloudflare 等）。

### 步骤 1：在 GitHub 仓库中填写自定义域名

**做什么**：告诉 GitHub 你的站点将使用哪个域名。

1. 打开你的 GitHub 仓库，点击顶部的 **Settings**（设置）标签。
2. 在左侧菜单栏的 "Code and automation" 部分，点击 **Pages**。
3. 找到 **Custom domain**（自定义域名）输入框。
4. 输入你的域名（例如 `example.com` 或 `blog.example.com`），然后点击 **Save**。

> ⚠️ **注意**：
> - 这一步会在你的仓库根目录下自动生成一个 `CNAME` 文件（如果你使用 Actions 部署则不需要此文件）。
> - **先在 GitHub 填写域名，再去 DNS 服务商配置**，这能防止域名被他人恶意接管（Domain Takeover）。

### 步骤 2：在 DNS 服务商处添加解析记录

根据你选择的域名类型，选择以下一种方式进行配置。

#### 选项 A：配置子域名（如 `blog.example.com` 或 `www.example.com`）

**做什么**：使用 CNAME 记录将你的子域名指向 GitHub 默认域名。

1. 登录你的 DNS 提供商控制台。
2. 添加一条新记录：
   - **类型（Type）**：选择 `CNAME`。
   - **主机记录（Name/Host）**：填写你的子前缀（例如 `blog` 或 `www`）。
   - **记录值（Value/Target）**：填写你的 GitHub Pages 默认域名 `<你的用户名>.github.io`（注意：不需要包含仓库名或 `https://`）。

#### 选项 B：配置 Apex 域名（如 `example.com`）

**做什么**：使用 A 记录将你的根域名指向 GitHub Pages 的服务器 IP。

1. 登录你的 DNS 提供商控制台。
2. 添加以下 **4 条 A 记录**：
   - **类型（Type）**：`A`
   - **主机记录（Name/Host）**：`@`（或留空，代表根域名）
   - **记录值（Value/Target）**：分别添加以下 4 个 IP 地址（每条建一个记录）：
     - `185.199.108.153`
     - `185.199.109.153`
     - `185.199.110.153`
     - `185.199.111.153`

> 💡 **如果你支持 IPv6**：可以额外添加 4 条 `AAAA` 记录，指向 `2606:50c0:8000::153` 到 `8003::153`。

### 步骤 3：验证 DNS 解析是否生效

**做什么**：检查你刚才的 DNS 设置是否已经全网生效。

打开电脑终端（Terminal），运行以下命令替换为你的域名：

```bash
# 验证 A 记录 (Apex 域名)
dig example.com +noall +answer -t A

# 验证 CNAME 记录 (子域名)
dig blog.example.com +noall +answer -t CNAME
```

**预期输出**：
如果是 A 记录，你应该能看到上面配置的 4 个 `185.199.x.153` IP；如果是 CNAME，应指向你的 `github.io` 域名。

> ⏳ DNS 更改可能需要几分钟到 24 小时不等才能全球生效，请耐心等待。

### 步骤 4：强制启用 HTTPS

**做什么**：为你的网站加上小绿锁，保证访问安全。

1. 回到 GitHub 仓库的 **Settings -> Pages** 页面。
2. 勾选 **Enforce HTTPS**（强制 HTTPS）。

> ⚠️ 如果该选项是灰色的，说明证书还在申请中。DNS 生效后，GitHub 通常需要几十分钟自动为你签发 Let's Encrypt 证书。稍后再回来勾选即可。

---

## ❓ 常见问题

### Q1: 为什么我的样式（CSS）丢失了，页面只剩下纯文本？

**A**: 这是配置自定义域名后最常见的问题。通常是因为 Hugo 的 `baseURL` 配置不正确。
**解决办法**：修改你项目根目录下的 `hugo.toml`（或 `config.toml`），将 `baseURL` 修改为你刚刚配置的**完整自定义域名**（必须包含 `https://` 和末尾的 `/`）。
例如：`baseURL = "https://example.com/"`

### Q2: 为什么我的 GitHub Pages 设置里一直提示 "DNS check unsuccessful"？

**A**: 
1. 你的 DNS 记录可能还没生效（等待 24 小时）。
2. 你配置的记录类型错误。请仔细检查是否多打了一个空格，或者误把 CNAME 记录的值写成了 IP 地址。

### Q3: 如果我把一个自定义域名绑定到 User Site（`<username>.github.io`），我的其他 Project Site 会受影响吗？

**A**: 会的。如果你把 `www.example.com` 绑定到了主站，那么你账户下所有没有单独配置自定义域名的项目站点，都会自动变成 `www.example.com/<repo-name>` 的形式。

---

## 🔄 故障排除

1. **检查 DNS 配置**：使用命令 `dig +short A example.com` 或 `dig +short CNAME www.example.com` 验证。
2. **检查 CNAME 文件**：如果不是通过 GitHub Actions 部署的，确保你仓库的 `public/` 或根目录下存在名为 `CNAME` 的文件，里面只包含一行你的域名（例如 `example.com`）。
3. **不要使用通配符 DNS**：不要使用 `*.example.com` 这样的 A 记录，这会导致极其严重的安全风险（Domain Takeover）。

---
**文档元信息**
难度：⭐⭐ | 类型：核心概念 | 预计阅读时间：10 分钟
