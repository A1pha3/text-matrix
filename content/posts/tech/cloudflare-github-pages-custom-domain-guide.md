---
title: "Cloudflare + GitHub Pages 自定义域名配置指南"
date: 2026-03-24T19:30:00+08:00
draft: false
categories: ["技术笔记"]
tags: ["Cloudflare", "GitHub Pages", "DNS", "域名", "建站"]
---

# 🌐 Cloudflare + GitHub Pages 自定义域名配置指南

> 更新时间：2026年3月24日｜整理：钳岳星君 🦞
>
> 适用场景：Spaceship 购买域名 → Cloudflare DNS 解析 → GitHub Pages 托管

---

## 一、整体架构

```
用户请求 → Cloudflare CDN → GitHub Pages 服务器 → 你的静态网站
              ↓
         DNS 解析（Cloudflare）
              ↓
         免费 SSL 证书
              ↓
         DDoS 防护 + CDN 加速
```

**为什么用 Cloudflare？**
- 🆓 免费 CDN 加速
- 🛡️ DDoS 防护
- 🔒 免费 SSL 证书（自动 HTTPS）
- ⚡ DNS 解析速度快
- 🚀 优化 SEO

---

## 二、配置步骤总览

| 步骤 | 操作位置 | 耗时 |
|------|----------|------|
| 1 | Spaceship：修改 Nameservers | 5 分钟 |
| 2 | Cloudflare：添加域名 | 10 分钟 |
| 3 | Cloudflare：配置 DNS 记录 | 5 分钟 |
| 4 | GitHub：仓库设置自定义域名 | 5 分钟 |
| 5 | GitHub：启用 HTTPS | 5 分钟 |

---

## 三、详细配置步骤

### 第一步｜在 Spaceship 修改 Nameservers

**目标：** 将域名的 DNS 管理权从 Spaceship 转移到 Cloudflare

#### 操作步骤：

1. 登录 [Spaceship](https://spaceship.com/) 账户

2. 进入 **Domain Management**（域名管理）

3. 找到你的域名，点击 **Nameservers** 或 **DNS Settings**

4. 选择 **Custom Nameservers**（自定义 Nameservers）

5. 填入 Cloudflare 的 Nameservers：

   ```
   Nameserver 1: amir.ns.cloudflare.com
   Nameserver 2: violet.ns.cloudflare.com
   ```

   > ⚠️ Cloudflare 会为你分配专属的 Nameservers，登录 Cloudflare Dashboard 后可在域名概览页面找到

6. 点击保存

#### 验证生效：

```bash
# 在终端输入以下命令查看是否生效
# 将 example.com 替换为你的域名
whois example.com | grep -i "name server"

# 或者
dig NS example.com
```

预期输出应包含 `cloudflare.com`

---

### 第二步｜在 Cloudflare 添加域名

**目标：** 在 Cloudflare 中接管你的域名

#### 操作步骤：

1. 登录 [Cloudflare Dashboard](https://dash.cloudflare.com/)

2. 点击 **Add a Site**（添加网站）

3. 输入你的域名（如 `example.com`），点击 **Add Site**

4. 选择 plan（个人网站选 **Free** 即可），点击 **Continue**

5. Cloudflare 会扫描现有的 DNS 记录（可跳过）

6. **重要：记录 Cloudflare 分配的 Nameservers**，格式类似：
   ```
   amir.ns.cloudflare.com
   violet.ns.cloudflare.com
   ```

7. 点击 **Done, take me to DNS**

---

### 第三步｜在 Cloudflare 配置 DNS 记录

**目标：** 将域名指向 GitHub Pages

#### 获取 GitHub Pages 的 IP 地址

GitHub Pages 使用的 IP 地址：

```
185.199.108.153
185.199.109.153
185.199.110.153
185.199.111.153
```

> 📝 2024年起 GitHub 推荐使用 CNAME 记录而非 A 记录，但如果你的域名不支持 CNAME（如根域名 apex domain），则使用 A 记录。

#### 配置 DNS 记录

在 Cloudflare DNS 设置页面，添加以下记录：

**方案一：使用 CNAME（推荐，www 子域名）**

| 类型 | 名称 | 目标 | 代理状态 |
|------|------|------|----------|
| CNAME | www | `username.github.io` | 🚀 DNS only（灰色云） |
| CNAME | @ | `username.github.io` | 🚀 DNS only（灰色云） |

**方案二：使用 A 记录（根域名，ipoint to GitHub IPs）**

| 类型 | 名称 | IPv4 地址 | 代理状态 |
|------|------|-----------|----------|
| A | @ | `185.199.108.153` | 🚀 DNS only（灰色云） |
| A | @ | `185.199.109.153` | 🚀 DNS only（灰色云） |
| A | @ | `185.199.110.153` | 🚀 DNS only（灰色云） |
| A | @ | `185.199.111.153` | 🚀 DNS only（灰色云） |

> ⚠️ **代理状态说明：**
> - ☁️ 橙色云 = 启用 Cloudflare CDN 代理（推荐，用于网站加速）
> - ⚪ 灰色云 = 仅 DNS 解析（GitHub Pages 要求必须为灰色云）

#### 重要注意事项

1. **GitHub Pages 要求 DNS 记录必须为灰色云（DNS only）**
   - Cloudflare 的代理（橙色云）会干扰 GitHub Pages 的 SSL 证书验证
   - 因此 GitHub Pages 的 DNS 记录**不能使用 Cloudflare 的代理功能**

2. **根域名（@）vs www**
   - GitHub 建议同时配置根域名和 www
   - 访问 www 子域名时自动跳转到根域名

---

### 第四步｜在 GitHub 配置自定义域名

**目标：** 告诉 GitHub Pages 使用你的自定义域名

#### 操作步骤：

1. 登录 GitHub，进入你的仓库（如 `https://github.com/username/text-matrix`）

2. 点击 **Settings**（设置）

3. 左侧菜单找到 **Pages**

4. 在 **Custom domain** 输入框中输入你的域名（如 `example.com`）

5. 点击 **Save**

6. 等待 DNS 验证（通常 5-10 分钟，最多 24 小时）

7. 验证通过后，勾选 **Enforce HTTPS**（强制 HTTPS）

#### GitHub 会自动验证你的域名

GitHub 会检查以下 DNS 记录是否存在：

```
# 如果你配置了 CNAME
CNAME www.example.com → username.github.io

# 如果你配置了 A 记录
A example.com → 185.199.108.153 等
```

> 💡 如果验证失败，GitHub 会显示错误信息，常见原因：
> - DNS 记录尚未传播（等待更长时间）
> - DNS 记录配置错误（检查第二步）
> - 使用了 Cloudflare 橙色云代理（改为灰色云）

---

### 第五步｜验证配置是否成功

#### 检查 DNS 传播

```bash
# 检查你的域名 DNS 记录
dig www.example.com

# 检查是否有 CAA 记录（可选，用于指定 CA）
dig CAA example.com
```

#### 访问网站测试

1. 在浏览器中访问 `https://www.example.com`
2. 应该显示你的 GitHub Pages 网站
3. 浏览器地址栏应显示 🔒 HTTPS 标志

#### GitHub Pages 设置检查

在 GitHub Pages 设置页面，确认：
- [x] **Custom domain**: `example.com`
- [x] **Enforce HTTPS** 已勾选
- [x] 显示绿色的 ✓ DNS check passed

---

## 四、Cloudflare SSL/TLS 配置

虽然 GitHub Pages 负责提供证书，但 Cloudflare 的 SSL 设置会影响用户体验。

### 推荐配置

1. 登录 [Cloudflare Dashboard](https://dash.cloudflare.com/)

2. 进入你的域名 → **SSL/TLS**

3. 将 **Encryption Mode** 设置为 **Flexible**
   > 原因：GitHub Pages 负责处理源服务器的 HTTPS，Cloudflare 作为中间层使用 Flexible 即可

4. 开启 **Always Use HTTPS**（始终使用 HTTPS）

5. 开启 **Automatic HTTPS Rewrites**（自动 HTTPS 重写）

---

## 五、常见问题排查

### 问题 1：DNS 记录修改后网站无法访问

**原因：** DNS 传播需要时间（全球 DNS 服务器更新通常 5 分钟到 48 小时）

**解决方法：**
```bash
# 清除本地 DNS 缓存（macOS）
sudo dscacheutil -flushcache
sudo killall -HUP mDNSResponder

# Windows
ipconfig /flushdns
```

### 问题 2：GitHub Pages 显示 404

**原因：** GitHub 尚未完成域名验证

**解决方法：**
1. 确认 DNS 记录已正确配置（参考第三步）
2. 在 GitHub Pages 设置中点击 **Check for custom domain**
3. 等待验证完成

### 问题 3：HTTPS 证书错误

**原因：** GitHub 的 Let's Encrypt 证书尚未生成

**解决方法：**
1. 确认已勾选 **Enforce HTTPS**（但不要在证书生成前勾选）
2. 等待 GitHub 自动生成证书（通常 24-48 小时）
3. 如果超过 72 小时仍然失败，尝试：
   - 在 GitHub Pages 设置中暂时移除自定义域名
   - 清除浏览器缓存
   - 重新添加自定义域名

### 问题 4：访问 www 跳转到根域名失败

**解决方法：** 在 Cloudflare 添加页面规则（Page Rules）

1. 进入 **Rules** → **Page Rules**
2. 点击 **Create Page Rule**
3. URL 匹配：`www.example.com/*`
4. 设置：**Forwarding URL** → **301 Redirect** → `https://example.com/$1`
5. 点击 **Save and Deploy**

### 问题 5：Cloudflare 显示 521 错误

**原因：** 源服务器（GitHub Pages）拒绝 Cloudflare 的连接

**解决方法：**
- 确认 DNS 记录已设置为灰色云（DNS only）
- GitHub Pages 不允许通过 Cloudflare 代理访问

---

## 六、配置完成后的维护

### 定期检查

| 检查项 | 频率 | 说明 |
|--------|------|------|
| 网站可访问性 | 每周 | 确认无 404/500 错误 |
| HTTPS 证书 | 每月 | GitHub 自动续期，Cloudflare 检查 Flexible 模式 |
| DNS 记录 | 每季度 | 确认无意外修改 |

### Spaceship 域名续费

- 记得在域名到期前续费
- Spaceship 通常会发送续费提醒邮件

---

## 七、进阶优化（可选）

### 1. 开启 Cloudflare CDN 加速

对于非 GitHub Pages 的子域名（如 API 服务），可以开启 Cloudflare 橙色云代理：

```dns
| 类型 | 名称 | 目标           | 代理状态 |
|------|------|----------------|----------|
| A     | api  | 你的服务器 IP  | ☁️ 已代理 |
```

### 2. 添加 Cloudflare Analytics

登录 Cloudflare Dashboard → 域名 → **Analytics & Threats** 可查看：
- 流量来源
- 带宽使用
- 安全威胁

### 3. 开启 Cloudflare Speed 优化

在 **Speed** 设置中：
- 开启 **Auto Minify**（自动压缩 HTML/CSS/JS）
- 开启 **Brotli** 压缩
- 优化图片（Polish 功能）

---

## 八、参考链接

| 资源 | 链接 |
|------|------|
| GitHub Pages 官方文档 | https://docs.github.com/en/pages |
| Cloudflare 官方文档 | https://developers.cloudflare.com/ |
| Cloudflare DNS 配置 | https://developers.cloudflare.com/dns/ |
| GitHub Pages 自定义域名 | https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site |
| Let's Encrypt | https://letsencrypt.org/ |

---

🦞 **钳岳星君整理 | 2026年3月24日**

> 💡 如果配置过程中遇到问题，欢迎交流指正！
