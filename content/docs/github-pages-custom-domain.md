---
title: "GitHub Pages 自定义域名配置指南"
date: 2026-03-23T10:00:00+08:00
draft: false
---

# GitHub Pages 自定义域名配置指南 ⭐⭐ 核心概念

> **目标读者**：已经成功部署 GitHub Pages，准备绑定自有域名的使用者。  
> **你将解决**：域名类型选择、DNS 正确配置、GitHub 侧绑定、HTTPS 启用与常见故障排查。

---

## 🎯 学习目标

完成本文后，你将能够：
- [ ] 区分 Apex 域名与子域名，并做出正确选型。
- [ ] 在 DNS 服务商中正确配置 A / AAAA / CNAME 记录。
- [ ] 在 GitHub Pages 中安全绑定域名并开启 HTTPS。
- [ ] 独立排查 “DNS check unsuccessful” 和样式丢失问题。

---

## 🧭 先做决策：你应该用哪种域名？

| 方案 | 示例 | DNS 记录类型 | 适合场景 |
|---|---|---|---|
| Apex 域名（根域名） | `example.com` | `A`（可选 `AAAA`） | 希望用户直接访问主域名 |
| 子域名 | `www.example.com` / `blog.example.com` | `CNAME` | 想把博客放在子域名 |

> 💡 推荐：如果你使用 Apex 域名，最好同时配置 `www` 子域名。GitHub Pages 会在二者之间做重定向，提升可用性与一致性。

---

## 📝 核心概念

### GitHub Pages 默认地址

默认地址通常是：
- User / Organization Site：`https://<用户名>.github.io/`
- Project Site：`https://<用户名>.github.io/<仓库名>/`

绑定自定义域名后，用户访问的是你的域名，而不是 `github.io` 地址。

### 为什么要先在 GitHub 填域名，再配 DNS？

这是为了降低域名被错误占用或恶意接管的风险。  
正确顺序是：**先 GitHub，后 DNS**。

---

## 🚀 配置步骤（推荐顺序）

### 步骤 1：在 GitHub Pages 中填写自定义域名

1. 打开仓库 `Settings`。
2. 进入 `Pages`。
3. 在 `Custom domain` 中输入域名（如 `example.com` 或 `blog.example.com`）。
4. 点击 `Save`。

> ⚠️ 注意：  
> - 分支发布模式下，GitHub 会在发布分支写入 `CNAME`。  
> - Actions 发布模式下，建议在站点构建产物中包含 `CNAME`（例如 Hugo 项目可放在 `static/CNAME`），避免后续发布覆盖。  
> - 仍然建议保留在 Pages 设置页的域名配置，作为权威配置入口。

### 步骤 2：在 DNS 服务商处添加解析

按你的域名类型选择其一。

#### 方案 A：子域名（`www` / `blog`）

- **Type**：`CNAME`
- **Host/Name**：`www` 或 `blog`
- **Value/Target**：`<你的用户名>.github.io`

> 不要写 `https://`，也不要追加仓库名路径。

#### 方案 B：Apex 域名（`example.com`）

添加 4 条 `A` 记录：

| Type | Host | Value |
|---|---|---|
| A | @ | 185.199.108.153 |
| A | @ | 185.199.109.153 |
| A | @ | 185.199.110.153 |
| A | @ | 185.199.111.153 |

可选：若启用 IPv6，再添加 4 条 `AAAA`：
- `2606:50c0:8000::153`
- `2606:50c0:8001::153`
- `2606:50c0:8002::153`
- `2606:50c0:8003::153`

> ⚠️ 不建议对 GitHub Pages 记录启用 CDN 代理模式（如 Cloudflare 橙云）进行首次排障。先用纯 DNS 解析打通，再按需启用代理。

### 步骤 3：本地验证 DNS 是否生效（macOS）

将示例域名替换成你自己的：

```bash
# 1) 查根域名 A 记录
dig example.com +noall +answer -t A

# 2) 查子域名 CNAME
dig www.example.com +noall +answer -t CNAME

# 3) 可选：查 AAAA（IPv6）
dig example.com +noall +answer -t AAAA
```

预期结果：
- Apex 域名：看到 `185.199.108.153` ~ `185.199.111.153`（及可选 AAAA）。
- 子域名：看到指向 `<用户名>.github.io` 的 `CNAME`。

> ⏳ DNS 全球传播通常需要几分钟到 24 小时。

### 步骤 4：开启 HTTPS

1. 回到 `Settings -> Pages`。
2. 勾选 `Enforce HTTPS`。

若选项是灰色，通常表示证书仍在签发中。等待 DNS 稳定后重试即可。

---

## ✅ 最终验收清单

- [ ] `Custom domain` 已保存且无拼写错误。
- [ ] DNS 记录类型与域名类型匹配（Apex 用 A/AAAA，子域名用 CNAME）。
- [ ] `dig` 查询结果与预期一致。
- [ ] 页面可通过 `https://你的域名` 访问。
- [ ] 已开启 `Enforce HTTPS`。

---

## ❓ 常见问题（FAQ）

### Q1：页面变成纯文本，CSS 丢失怎么办？

最常见原因是 Hugo 的 `baseURL` 不匹配当前域名。  
请在 `hugo.toml`（或 `config.toml`）中设置完整地址，包含 `https://` 和末尾 `/`：

```toml
baseURL = "https://example.com/"
```

### Q2：Pages 提示 “DNS check unsuccessful” 怎么办？

按顺序检查：
1. DNS 是否刚修改（先等待传播）。
2. 记录类型是否正确（CNAME 不应写 IP）。
3. `Host` 与 `Value` 是否填反。
4. 是否存在冲突记录（如同名 `A` 与 `CNAME` 冲突）。

### Q3：绑定到 User Site 会影响其他项目吗？

会。若你把域名绑定到 User / Organization Site，未单独配置域名的 Project Site 通常会体现为该域名下的子路径形式。

### Q4：Actions 部署到底要不要 `CNAME` 文件？

建议要。  
对于 Hugo，可在 `static/CNAME` 放一行域名，这样每次构建都会复制到发布产物，避免被后续发布覆盖。

---

## 🔒 安全与稳定性建议

1. 不要配置通配符记录（如 `*.example.com` 指向 Pages），避免子域名接管风险。  
2. 首次配置阶段先关闭第三方代理，确保问题定位在 DNS 与 Pages。  
3. 只在你实际使用的仓库保留域名绑定，废弃仓库及时清理域名配置。  
4. 变更后用无痕窗口和移动网络复测，避免本地缓存误判。

---

**文档元信息**  
难度：⭐⭐ | 类型：核心概念 | 预计阅读时间：12 分钟
