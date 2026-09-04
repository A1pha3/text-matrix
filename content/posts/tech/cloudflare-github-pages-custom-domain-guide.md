---
title: "Cloudflare + GitHub Pages 自定义域名配置指南"
date: "2026-03-24T19:30:00+08:00"
slug: "cloudflare-github-pages-custom-domain-guide"
github_repo: "username/text-matrix"
description: "详细讲解如何将 Spaceship 购买的域名通过 Cloudflare DNS 解析，并绑定到 GitHub Pages 上，包含完整配置步骤与常见问题排查。"
draft: false
categories: ["技术笔记"]
tags: ["Cloudflare", "DNS", "域名"]
---

# Cloudflare + GitHub Pages 自定义域名配置指南

> 更新时间：2026 年 3 月 24 日｜整理：钳岳星君 🦞
>
> 适用场景：Spaceship 购买域名 → Cloudflare 边缘代理 → GitHub Pages 托管

---

## 学习目标

完成本指南后，你将能够：

- [ ] 理解 DNS 解析全过程（从用户输入域名到服务器响应）
- [ ] 独立完成 Spacing → Cloudflare → GitHub Pages 的完整配置
- [ ] 排查常见的 DNS 传播、HTTPS 证书、Cloudflare 521 错误
- [ ] 配置 Cloudflare SSL/TLS 加密模式和自动 HTTPS 重写
- [ ] 设置 www 子域名到根域名的 301 永久重定向

---

## 前置知识｜新手必看

### 什么是域名？

**域名（Domain）** 是网站的地址，例如 `example.com`。它代替了难以记忆的 IP 地址（如 `185.199.108.153`）。

**域名的结构：**

```
example.com        ← 根域名（也叫 apex domain）
www.example.com   ← 子域名（subdomain）
blog.example.com  ← 子域名
```

> 💡 `www` 是一个约定俗成的子域名，表示"万维网"，但它不是域名的一部分——它是一个子域名。

### 什么是 DNS？

**DNS（Domain Name System）** 是互联网的"电话簿"，负责将域名解析为 IP 地址。

**DNS 解析过程：**

```
用户输入 www.example.com
        ↓
    DNS 服务器查询
        ↓
    返回 IP 地址（如 185.199.108.153）
        ↓
    用户连接到该 IP 的服务器
```

### 什么是 Nameserver（域名服务器）？

**Nameserver** 是存储 DNS 记录的专业服务器。你的域名注册商（如 Spaceship）给你分配 Nameserver，你域名下的所有 DNS 记录都存储在那里。

> 💡 **类比**：域名像是公司名称，Nameserver 像是公司的档案室。档案室在哪里（Nameserver 地址），别人就能查到公司的所有信息（DNS 记录）。

### 什么是 DNS 传播？

当你修改 DNS 记录后，全世界的 DNS 服务器需要同步这个变化。这个同步过程叫 **DNS 传播**。

> ⚠️ 传播通常需要 **5 分钟到 48 小时**，取决于各 DNS 服务器的缓存时间。

### 什么是 TTL？

**TTL（Time To Live）** 是 DNS 记录的"保质期"，告诉其他 DNS 服务器缓存这条记录多久。

- TTL 越短，变化传播越快，但查询压力越大
- 常见值：300 秒（5 分钟）、3600 秒（1 小时）、86400 秒（1 天）

### 什么是根域名（@）？

在 DNS 记录中，`@` 符号代表**你的根域名**（不含 www）。

| 符号 | 含义 | 示例 |
|------|------|------|
| `@` | 根域名 | `example.com` |
| `www` | www 子域名 | `www.example.com` |
| `blog` | 自定义子域名 | `blog.example.com` |

---

## 一、整体架构

```
用户请求 www.example.com
        ↓
   用户本机 / 运营商 DNS 解析
   得到 Cloudflare 的 IP
        ↓
   Cloudflare 边缘代理
   （橙云：SSL、CDN、重定向在这里生效）
        ↓
   GitHub Pages 源站服务器
   (username.github.io)
        ↓
   你的静态网站
      返回并🔒 HTTPS 加密传输
```

**为什么用 Cloudflare？**

| 优势 | 说明 |
|------|------|
| 🆓 免费 CDN | 全球服务器加速访问 |
| 🛡️ DDoS 防护 | 抵御恶意流量攻击 |
| 🔒 免费 SSL | 自动 HTTPS 加密 |
| ⚡ DNS 速度快 | 采用 Anycast 技术，全球低延迟 |
| 🚀 SEO 优化 | Google 等搜索引擎偏好 HTTPS 网站 |

---

## 二、配置步骤总览

| 步骤 | 操作位置 | 操作内容 | 耗时 |
|------|----------|----------|------|
| 1 | Spaceship | 修改 Nameservers 指向 Cloudflare | 5 分钟 |
| 2 | Cloudflare | 添加域名到 Cloudflare | 10 分钟 |
| 3 | Cloudflare | 配置 DNS 记录指向 GitHub | 5 分钟 |
| 4 | GitHub | 仓库设置自定义域名 | 5 分钟 |
| 5 | GitHub | 启用 HTTPS | 5 分钟 |

> ⚠️ **重要提醒**：Nameserver 修改后，DNS 传播可能需要 **24-48 小时** 才能完全生效。在此期间部分用户可能暂时无法访问你的网站，这是正常现象。

---

## 三、详细配置步骤

### 第一步｜在 Spaceship 修改 Nameservers

**目标：** 将域名的 DNS 管理权从 Spaceship 转移到 Cloudflare

> 🔑 **为什么要改 Nameserver？**
>
> 域名注册商（如 Spaceship）默认提供 DNS 服务，但功能有限。通过将 Nameserver 指向 Cloudflare，我们可以使用 Cloudflare 强大的 DNS 服务、CDN 加速和安全防护功能。

#### 操作步骤：

**1. 登录 Spaceship**

访问 [Spaceship 官网](https://spaceship.com/) 并登录你的账户。

**2. 进入域名管理**

在控制台找到 **Domains** 或 **My Domains** 部分。

**3. 选择你的域名**

点击需要配置的域名，进入域名详情页。

**4. 找到 Nameservers 设置**

寻找以下入口之一：
- **Nameservers**
- **DNS Settings**
- **Advanced DNS**

**5. 选择自定义 Nameservers**

在 Nameserver 设置页面，选择 **Custom** 或 **Manual**（不是 "Default"）。

**6. 填入 Cloudflare 的 Nameservers**

登录 [Cloudflare Dashboard](https://dash.cloudflare.com/)，添加域名后，Cloudflare 会提供两个 Nameserver 地址，格式如下：

```
Nameserver 1: amir.ns.cloudflare.com
Nameserver 2: violet.ns.cloudflare.com
```

> ⚠️ **注意**：Cloudflare 会提供专属的两个 Nameserver，**两个都要填写**，不能只填一个。

**7. 保存设置**

点击保存。Spaceship 可能会显示 "Nameservers updated" 或类似的确认信息。

#### 验证 Nameserver 修改

```bash
# 在电脑终端输入（macOS 打开 Terminal，Windows 打开 PowerShell）
# 将 example.com 替换为你的真实域名

# 方法1：使用 whois 命令
whois example.com | grep -i "name server"

# 方法2：使用 dig 命令（需要安装）
dig NS example.com

# 方法3：使用 nslookup
nslookup -type=NS example.com
```

**预期输出示例：**

```
Name Server: amir.ns.cloudflare.com
Name Server: violet.ns.cloudflare.com
```

> 💡 如果看到 `cloudflare.com` 字样，说明 Nameserver 已经指向 Cloudflare 成功！

---

### 第二步｜在 Cloudflare 添加域名

**目标：** 在 Cloudflare 中接管你的域名

#### 操作步骤：

**1. 登录 Cloudflare Dashboard**

访问 [https://dash.cloudflare.com/](https://dash.cloudflare.com/) 并登录。

**2. 点击添加网站**

在 Dashboard 首页，点击 **Add a Site**（添加网站）按钮。

**3. 输入你的域名**

在输入框中输入你的域名（只输入根域名，不带 www）：

```
example.com
```

点击 **Add Site** 继续。

**4. 选择套餐**

选择 **Free** 套餐（个人博客/网站完全够用），点击 **Continue**。

**5. 选择导入现有 DNS 记录（可选）**

Cloudflare 会尝试扫描你域名现有的 DNS 记录。

> 💡 如果这是新域名，没有任何重要记录，可以选择 **Skip** 跳过这一步。

**6. 记录 Cloudflare 分配的 Nameservers**

⚠️ **这是关键步骤！**

Cloudflare 页面会显示类似下面的信息：

```
We have assigned the following nameservers to your zone:

amir.ns.cloudflare.com
violet.ns.cloudflare.com
```

> 💡 **重要**：Spaceship 和 Cloudflare 都显示这两组 Nameserver 信息是**正常的**。只要你第一步在 Spaceship 填的是 Cloudflare 的 Nameserver，现在两边显示相同就对了。

**7. 完成设置**

点击 **Done, take me to DNS** 进入 DNS 设置页面。

---

### 第三步｜在 Cloudflare 配置 DNS 记录

**目标：** 将域名指向 GitHub Pages

#### 基础知识｜DNS 记录类型

| 记录类型 | 用途 | 示例 |
|----------|------|------|
| **A 记录** | 将域名指向一个 IPv4 地址 | `example.com` → `185.199.108.153` |
| **CNAME** | 将子域名指向另一个域名 | `www.example.com` → `example.com` |
| **TXT** | 用于验证、SPF 邮件安全等 | 验证域名所有权 |
| **AAAA** | 将域名指向 IPv6 地址 | 较少使用 |

> ⚠️ **CNAME 记录不能用于根域名（@）！**
>
> DNS 规范规定 CNAME 记录不能与其他记录类型共存。根域名通常需要同时存在 SOA、NS、A 等记录，所以**根域名不能使用 CNAME**。这是 DNS 协议的限制，不是 Cloudflare 或 GitHub 的限制。

#### GitHub Pages 的 IP 地址

GitHub Pages 使用的固定 IP 地址：

```
185.199.108.153
185.199.109.153
185.199.110.153
185.199.111.153
```

#### 配置 DNS 记录

进入 Cloudflare Dashboard → 你的域名 → **DNS** → **Records**。

点击 **Add record**，按以下方式配置：

**记录 1：根域名（A 记录）**

| 设置项 | 值 | 说明 |
|--------|-----|------|
| Type | `A` | A 记录类型 |
| Name | `@` | 表示根域名（你的域名本身） |
| IPv4 address | `185.199.108.153` | GitHub Pages 的第一个 IP |
| Proxy status | **Proxied**（☁️ 橙云） | 让 Cloudflare 提供 SSL/CDN/重定向（见下文说明） |

点击 **Save**。

**记录 2-4：备用 A 记录**

重复上述步骤，添加另外三个 IP 地址：

```
185.199.109.153
185.199.110.153
185.199.111.153
```

> 💡 四个 A 记录同时存在，GitHub 会自动选择最快响应的 IP。

**记录 5：www 子域名（CNAME）**

| 设置项 | 值 | 说明 |
|--------|-----|------|
| Type | `CNAME` | CNAME 记录类型 |
| Name | `www` | www 子域名 |
| Target | `username.github.io` | ⚠️ 把 `username` 换成你的 GitHub 用户名 |
| Proxy status | **Proxied**（☁️ 橙云） | 让 Cloudflare 提供 SSL/CDN/重定向（见下文说明） |

点击 **Save**。

#### DNS 记录配置完成后的样子

```
| 类型 | 名称 | IPv4 地址 / 目标           | 代理状态 |
|------|------|---------------------------|----------|
| A    | @    | 185.199.108.153          | Proxied |
| A    | @    | 185.199.109.153          | Proxied |
| A    | @    | 185.199.110.153          | Proxied |
| A    | @    | 185.199.111.153          | Proxied |
| CNAME| www  | username.github.io        | Proxied |
```

> ⚠️ **代理状态（Proxy Status）决定 Cloudflare 是否真正接管流量**
>
> 橙云 ☁️ = Proxied，流量先经过 Cloudflare（SSL、CDN、重定向规则才生效）
> 灰云 ⚪ = DNS only，Cloudflare 只做 DNS 解析，上述功能全部不生效
>
> 本文主线使用**橙云（Proxied）**，因为它能让 Cloudflare 的 SSL、重定向和缓存规则真正起作用。GitHub Pages 源站带有 Let's Encrypt 有效证书，配合橙云时务必把 SSL 模式设成 **Full (strict)**（见第四节），否则会出现证书校验失败或重定向循环。若你只想用 Cloudflare 做纯 DNS、让 GitHub 直接托管，也可以全部改灰云，但那样第四节的重定向规则和 HTTP 跳转都不会生效，www 到根域名的跳转需在站点源码里自行实现。

---

### 第四步｜在 GitHub 配置自定义域名

**目标：** 告诉 GitHub："这个域名是我的，请用这个域名来托管我的网站"

#### 前置条件

确保你的仓库已经启用了 GitHub Pages：

1. 进入你的仓库（如 `https://github.com/username/text-matrix`）
2. 点击 **Settings** → **Pages**
3. 确认 **Source** 设置为 **Deploy from a branch**
4. 选择 **main** 分支和 **/ (root)** 文件夹
5. 点击 **Save**

#### 操作步骤：

**1. 进入仓库设置**

登录 GitHub，进入你的仓库页面。

**2. 打开 Pages 设置**

左侧菜单点击 **Pages**。

**3. 配置自定义域名**

在 **Custom domain** 输入框中输入你的域名：

```
example.com
```

> 💡 输入后 GitHub 会立即开始 DNS 检查

**4. 保存设置**

点击 **Save**。

**5. 等待 DNS 验证**

GitHub 会自动检查你的 DNS 配置是否正确。检查项目：

```
✓ DNS check passed
```

或错误信息：

```
✗ DNS check failed
 原因1：DNS 记录尚未传播（等待 5 分钟到 24 小时）
 原因2：DNS 记录配置错误（检查第三步）
 原因3：使用了 Cloudflare 橙色云代理（改为灰色云）
```

> 💡 **如何加速验证？**
> - 等待 5-10 分钟后再试
> - 使用 `dig www.example.com` 命令检查 DNS 是否已生效
> - 清除浏览器缓存或使用无痕模式

**6. 勾选 Enforce HTTPS**

当 DNS 验证通过后，勾选 **Enforce HTTPS**（强制使用 HTTPS）。

> 💡 GitHub 会使用 Let's Encrypt 自动为你的域名申请 SSL 证书。这个过程可能需要 **24-48 小时**。在证书生效前，HTTPS 可能会有警告，这是正常现象。

---

### 第五步｜验证配置成功

#### 方法一：命令行验证

```bash
# 检查域名的 DNS 记录
dig www.example.com

# 检查 A 记录是否指向 GitHub IPs
dig A example.com

# 检查 CAA 记录（用于指定可颁发证书的 CA）
dig CAA example.com
```

**预期输出示例：**

```
;; ANSWER SECTION:
www.example.com.    300    IN    CNAME    username.github.io.
username.github.io.    300    IN    CNAME    github.io.
github.io.        300    IN    CNAME    lbs.github.com.
lbs.github.com.    300    IN    A        185.199.108.153
```

#### 方法二：浏览器访问测试

1. 打开浏览器（建议使用无痕/隐私模式，避免缓存干扰）
2. 访问 `https://www.example.com`
3. 应该看到你的 GitHub Pages 网站

**成功标志：**
- ✅ 浏览器地址栏显示 🔒 HTTPS
- ✅ 点击锁图标显示 "连接安全"
- ✅ GitHub Pages 设置页面显示 ✓ DNS check passed

#### 方法三：GitHub Pages 设置检查

在仓库 **Settings** → **Pages** 页面确认：

```
Custom domain: example.com ✓
Source: Deploy from a branch (main / (root))
Enforce HTTPS: ✓ 已勾选
Build and deployment: ✓ Active
```

---

## 四、Cloudflare SSL/TLS 配置

### SSL 加密模式详解

Cloudflare 提供四种 SSL/TLS 加密模式：

| 模式 | 说明 | 适用场景 |
|------|------|----------|
| **Off** | 不加密（不推荐） | 仅测试环境 |
| **Flexible** | 客户端到 Cloudflare 加密，Cloudflare 到源站不加密 | 源站不支持 HTTPS |
| **Full** | 端到端加密，Cloudflare 验证源站证书 | 源站有证书但非有效 CA 颁发 |
| **Full (strict)** | 端到端加密，Cloudflare 验证源站证书且必须为有效 CA | 源站有有效证书（推荐） |

> 💡 **对于 GitHub Pages：使用 Full (strict)**
>
> - GitHub Pages 源站本身使用 Let's Encrypt 签发的有效证书
> - 橙云（Proxied）下，Cloudflare 到源站的这一段要校验该证书，正好满足 **Full (strict)** 的要求
> - 不要用 **Flexible**：它让 Cloudflare 到源站不加密，遇到源站强制跳转 HTTPS 时容易陷入重定向循环

### 推荐配置步骤

**1. 进入 SSL/TLS 设置**

Cloudflare Dashboard → 你的域名 → **SSL/TLS**。

**2. 设置加密模式**

**Encryption Mode** 选择 **Full (strict)**。

**3. 开启始终使用 HTTPS**

找到 **Always Use HTTPS** 选项，打开它。

**4. 开启自动 HTTPS 重写**

找到 **Automatic HTTPS Rewrites** 选项，打开它。

> 💡 这个功能会自动将页面中的 HTTP 链接转换为 HTTPS，避免"混合内容"警告。

---

## 五、www 子域名跳转到根域名

当用户访问 `www.example.com` 时，自动 301 跳到 `example.com`，且保留之后的路径（如 `www.example.com/blog` 跳到 `example.com/blog`）。

> 前提：这一步依赖 Cloudflare 代理流量，必须使用第三节的**橙云（Proxied）**。若你的记录是灰云（DNS only），重定向规则不会触发，需要从 GitHub 侧另想办法（例如只配置根域名、在站点 HTML 里加跳转脚本），本文不展开。

### 方法：在 Cloudflare 配置重定向规则

**1. 进入重定向规则**

Cloudflare Dashboard → 你的域名 → **Rules** → **Redirect Rules**。

> ⚠️ 新版 Cloudflare UI 中，Page Rules 已迁移到 Redirect Rules。

**2. 创建重定向规则**

点击 **Create rule**。

**3. 配置规则**

| 设置项 | 值 |
|--------|-----|
| Rule name | `Redirect www to root` |
| When incoming requests match | **Hostname equals** `www.example.com` |
| Then redirect to | Dynamic → 表达式 `concat("https://example.com", http.request.uri.path)` |
| Preserve query string | 开启（保留 `?` 后的参数） |
| Redirect type | `301`（Permanent） |

**4. 保存并部署**

点击 **Save and Deploy**。之后访问 `http(s)://www.example.com/任意路径` 都会返回 `301` 并重定向到 `https://example.com/任意路径`。

---

## 六、常见问题排查

### 问题 1：DNS 修改后网站无法访问

**原因：** DNS 传播需要时间（5 分钟到 48 小时）

**排查步骤：**

```bash
# 1. 清除本地 DNS 缓存

# macOS:
sudo dscacheutil -flushcache
sudo killall -HUP mDNSResponder

# Windows (管理员权限 PowerShell):
ipconfig /flushdns

# Linux:
sudo systemd-resolve --flush-caches
# 或
sudo service nscd restart

# 2. 使用在线 DNS 检查工具
# 访问 https://dnschecker.org/
# 输入你的域名，检查全球 DNS 服务器的解析结果
```

**预期结果：** 如果大部分地区显示相同的 IP 地址，说明 DNS 已生效。

---

### 问题 2：GitHub Pages 显示 404

**原因：** GitHub 尚未验证你的域名

**解决方法：**

1. 确认 DNS 记录已正确配置（第三步）
2. 等待 5-10 分钟
3. 在 GitHub Pages 设置中点击 **Check for custom domain** 按钮
4. 如果仍然失败，检查：
   - DNS 记录是否为灰色云
   - A 记录是否指向正确的 GitHub IP
   - CNAME 是否指向 `username.github.io`（不是 `username.github.com`）

---

### 问题 3：HTTPS 证书错误/警告

**原因：** Let's Encrypt 证书尚未颁发，或证书过期

**解决方法：**

**情况 A：刚配置，等待证书生成**

Let's Encrypt 证书生成需要 **24-48 小时**。

1. 暂时不要勾选 **Enforce HTTPS**
2. 等待 48 小时后再次检查
3. 如果仍有问题，尝试重新触发验证：
   - 在 GitHub Pages 设置中移除自定义域名
   - 清除浏览器缓存
   - 重新添加自定义域名

**情况 B：证书已过期**

GitHub 会自动续期，但如果有问题：

1. 在 GitHub Pages 设置中取消勾选 **Enforce HTTPS**
2. 等待几分钟后重新勾选
3. GitHub 会重新申请证书

---

### 问题 4：Cloudflare 显示 521 错误

**错误页面：** `Error 521 - Web server is down`

**原因：** Cloudflare 无法连接到源站（GitHub Pages）

**解决方法：**

1. 确认源站地址正确：`@` 的 4 条 A 记录指向 GitHub 的 4 个 IP，`www` 的 CNAME 指向 `username.github.io`
2. 先直接访问 `https://username.github.io`，确认 GitHub Pages 本身在线
3. SSL 模式保持 **Full (strict)**；若误设成 Flexible，源站强制跳转 HTTPS 时可能与 Cloudflare 之间握手失败
4. 若刚改过记录，等待几分钟再刷新请求（Cloudflare 边缘连接源站需要短暂收敛）

---

### 问题 5：Nameserver 修改后 Spaceship 显示不一致

**现象：** Spaceship 显示的 Nameserver 和 Cloudflare 提供的不一样

**这是正常的！**

- Spaceship 注册商信息可能暂时不更新
- 以 **第二步** 中 Cloudflare Dashboard 显示的 Nameserver 为准
- 使用 `whois example.com` 或 `dig NS example.com` 验证实际生效的 Nameserver

---

## 七、进阶优化（可选）

### 1. 让 Cloudflare 缓存帮你加速

主线使用橙云后，`www` 与 `@` 的流量已经经过 Cloudflare CDN，无需再单独开启代理。

**原理：**

```
用户请求
    ↓
Cloudflare CDN 边缘节点
    ↓
如果缓存命中 → 直接返回
如果缓存未命中 → 回源获取 → 缓存 → 返回
```

静态站的 HTML、CSS、JS、图片变化不频繁，适合让 Cloudflare 缓存。可以到 **Caching → Cache Rules** 给静态资源目录（如 `assets`、`images`）加一条稍长的缓存规则，减少回源请求。

> ⚠️ 改完内容后，Cloudflare 可能仍提供旧缓存。到 **Caching → Purge Cache** 一键清空，或临时关闭缓存再刷新验证。

### 2. 开启 Cloudflare Speed 优化

**适用场景：** 你的静态网站需要更快加载速度

**设置方法：**

Cloudflare Dashboard → 你的域名 → **Speed**：

| 功能 | 说明 |
|------|------|
| **Brotli** | 比 Gzip 压缩率更高的文本压缩算法，对 HTML/CSS/JS 有效 |
| **Early Hints** | 提前推送关键资源，缩短首屏等待 |
| **Content Optimization → Polish** | 图片压缩或转 WebP（依赖你的图片是静态文件） |

### 3. 开启 Cloudflare 安全防护

Cloudflare Dashboard → 你的域名 → **Security** → **Settings**：

| 功能 | 说明 |
|------|------|
| **Security Level** | 设置为 "Medium" 或 "High" |
| **Under Attack Mode** | 遭受 DDoS 攻击时开启，显示验证页面 |
| **Rate Limiting** | 防止恶意爬虫和暴力破解 |

### 4. 使用 Cloudflare Analytics 监控流量

Cloudflare Dashboard → 你的域名 → **Analytics & Threats**：

可以查看：
- 流量趋势（访客数、带宽）
- 流量来源（国家/地区）
- 热门页面
- 安全威胁（被拦截的恶意请求）

---

## 八、定期维护

### 域名续费

| 事项 | 说明 |
|------|------|
| 续费时间 | 域名到期前 30 天开始续费 |
| 续费方式 | Spaceship 控制台 → 域名 → Renew |
| 续费提醒 | Spaceship 会发送邮件提醒 |
| 过期后果 | 过期后域名会被释放，他人可以注册 |

### DNS 记录检查

建议**每季度检查一次**：

1. 确认 A 记录仍然指向正确的 GitHub IPs
2. 确认 CNAME 记录指向正确的 `username.github.io`
3. 确认没有意外的 DNS 记录（如陌生人添加的记录）

---

## 九、原理深入｜DNS 解析全过程

### 完整解析链路

```
用户浏览器输入 www.example.com
        ↓
1. 浏览器检查本地缓存（浏览器 DNS 缓存）
        ↓
2. 浏览器检查 hosts 文件
        ↓
3. 询问操作系统 DNS 解析器
        ↓
4. 操作系统询问配置的 DNS 服务器（通常是 ISP 或 8.8.8.8）
        ↓
5. DNS 服务器检查缓存
        ↓
6. 如果没有缓存，查询根域名服务器（.）
        ↓
7. 根服务器返回 .com 顶级域名的 Nameserver
        ↓
8. 查询 .com Nameserver
        ↓
9. .com Nameserver 返回 example.com 的 Nameserver
        ↓
10. 查询 example.com 的 Nameserver（这就是 Cloudflare）
        ↓
11. Cloudflare 返回 www.example.com 对应的 IP 地址
        ↓
12. 浏览器收到 IP，开始建立 TCP 连接...
```

### 为什么 DNS 传播很慢？

每个 DNS 服务器都会"记住"查询结果一段时间（TTL）。即使你修改了 DNS 记录，全世界所有 DNS 服务器的缓存不会立即更新，必须等到各自的缓存过期后重新查询，才能获得新记录。

---

## 自测问题

完成配置后，尝试回答以下问题以检验理解：

1. **为什么根域名（@）不能使用 CNAME 记录？**
   <details>
   <summary>参考答案</summary>
   DNS 规范规定 CNAME 记录不能与其他记录类型共存。根域名通常需要同时存在 SOA、NS、A 等记录，所以根域名不能使用 CNAME。
   </details>

2. **Cloudflare 的代理状态（Proxy Status）怎么选？**
   <details>
   <summary>参考答案</summary>
   新流量经过 Cloudflare＝橙云（Proxied），SSL、CDN、重定向规则才生效；只做 DNS 解析＝灰云（DNS only）。本文主线用橙云，并把 SSL 模式设成 Full (strict)。若用灰云，Cloudflare 的 SSL/重定向功能无效，www 到根域名的跳转需在站点源码里实现。
   </details>

3. **DNS 传播通常需要多长时间？为什么这么慢？**
   <details>
   <summary>参考答案</summary>
   通常需要 5 分钟到 48 小时。因为：每个 DNS 服务器都会"记住"查询结果一段时间（TTL），必须等到各自的缓存过期后重新查询，才能获得新记录。
   </details>

4. **如果你在 GitHub Pages 设置中看到"DNS check failed"，你会按什么顺序排查？**
   <details>
   <summary>参考答案</summary>
   ① 确认 DNS 记录已正确配置（`@` 的 4 条 A 记录指向 GitHub IPs，`www` 的 CNAME 指向 username.github.io）；② 等待 5-10 分钟后重试；③ 若启用橙云，确认 SSL 模式为 Full (strict)；④ 用 `dig` 检查 DNS 是否已生效；⑤ 清除浏览器缓存。
   </details>

5. **为什么 GitHub Pages 要求自定义域名必须勾选"Enforce HTTPS"？**
   <details>
   <summary>参考答案</summary>
   因为 GitHub 会使用 Let's Encrypt 自动为你的域名申请 SSL 证书。勾选"Enforce HTTPS"后，GitHub 会强制使用 HTTPS 连接，保护用户数据安全。证书生成需要 24-48 小时。
   </details>

## FAQ

### Q1: 我可以同时使用多个自定义域名吗？

**A**: 可以。在 GitHub Pages 设置中，你可以添加多个自定义域名。每个域名都需要单独配置 DNS 记录（A 记录或 CNAME 记录）。

### Q2: 如果我想把域名从 Spaceship 转移到其他注册商，需要重新配置吗？

**A**: 需要。转移注册商后，你需要在新注册商处修改 Nameservers 指向 Cloudflare，然后等待 DNS 传播（5 分钟到 48 小时）。

### Q3: Cloudflare 的"Always Use HTTPS"和 GitHub 的"Enforce HTTPS"有什么区别？

**A**: Cloudflare 的"Always Use HTTPS"是将 HTTP 请求重定向到 HTTPS；GitHub 的"Enforce HTTPS"是要求 GitHub Pages 必须使用 HTTPS 连接。两者应该同时开启。

### Q4: 我可以使用 Cloudflare 的缓存/规则功能来加速 GitHub Pages 吗？

**A**: 可以。主线用橙云时，站点流量已全局走 Cloudflare。想再精确控制，可到 **Caching → Cache Rules** 给静态资源（图片、CSS、JS）设置更长的缓存时间，或用 **Rules → Origin Rules** 调整回源行为。

### Q5: 如果我的 GitHub Pages 网站突然无法访问，我应该先检查什么？

**A**: 检查顺序：① 浏览器是否能访问 `https://username.github.io`（确认 GitHub Pages 本身正常）；② 运行 `dig www.example.com` 检查 DNS 记录；③ 检查 Cloudflare Dashboard 的 SSL/TLS 设置；④ 检查 GitHub Pages 设置中的自定义域名状态。

---

## 十、参考链接

### 官方文档

| 资源 | 链接 |
|------|------|
| GitHub Pages 官方文档 | https://docs.github.com/en/pages |
| Cloudflare 官方文档 | https://developers.cloudflare.com/ |
| Cloudflare DNS 入门 | https://developers.cloudflare.com/dns/ |
| GitHub Pages 自定义域名 | https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site |
| Let's Encrypt | https://letsencrypt.org/ |
| Cloudflare SSL/TLS 设置 | https://developers.cloudflare.com/ssl/get-started_ssl-with-cloudflare/ |

### 实用工具

| 工具 | 用途 |
|------|------|
| [DNS Checker](https://dnschecker.org/) | 检查全球 DNS 传播情况 |
| [Why No HTTPS](https://www.whynopassword.com/) | 检查 HTTPS 配置问题 |
| [SSL Labs](https://www.ssllabs.com/ssltest/) | 检查 SSL 证书配置 |
| [Cloudflare Check](https://cloudflare.com/cdn-cgi/trace/) | 检查 Cloudflare 是否生效 |

---

## 附录：完整配置检查清单

```
□ Spaceship: Nameservers 已改为 Cloudflare
□ Cloudflare: 域名已添加
□ Cloudflare: @ A 记录（4条）已添加，橙云 Proxied
□ Cloudflare: www CNAME 已添加，橙云 Proxied
□ Cloudflare: SSL/TLS 模式设为 Full (strict)
□ Cloudflare: Always Use HTTPS 已开启
□ Cloudflare: Redirect Rule 实现 www → 根域名 301
□ GitHub: Pages 已启用
□ GitHub: 自定义域名已配置
□ GitHub: Enforce HTTPS 已勾选
□ 浏览器: https://example.com 可以访问（显示锁图标）
□ 浏览器: https://www.example.com 访问后 301 跳到根域名
```

---

🦞 **钳岳星君整理 | 2026 年 3 月 24 日**

> ⚠️ AI 技术发展迅速，本文内容会持续更新。如有疏漏，欢迎指正！
>
> 💡 如果配置过程中遇到问题，欢迎交流指正！

---

