---
title: "CloakBrowser：源代码级打补丁的隐身Chromium浏览器"
date: 2026-05-18
tags: ["AI工具", "爬虫", "反检测", "开源"]
categories: ["工具"]
---

# CloakBrowser：源代码级打补丁的隐身Chromium浏览器

![CloakBrowser](https://i.imgur.com/cqkp6fG.png)

**CloakBrowser** 是一个从 Chromium 源代码层面进行指纹修改的隐身浏览器，49个源代码补丁覆盖 canvas、WebGL、audio、fonts、GPU、screen、WebRTC、network timing 等所有自动化信号。能通过 Cloudflare Turnstile、FingerprintJS、BrowserScan 等 30+ 检测平台的测试，在 headless 模式下依然保持人类浏览器级别的 reCAPTCHA v3 评分（0.9分）。

<!-- more -->

## 核心特性

- **49个源代码级 C++ 补丁** — 不是配置文件修改，不是 JS 注入，是真实的 Chromium 二进制层修改
- **`humanize=True` 参数** — 人类化的鼠标曲线、键盘时序、滚动模式，一行代码开启行为检测绕过
- **reCAPTCHA v3 评分 0.9** — 人类级别，已在服务器端验证
- **通过 Cloudflare Turnstile**、FingerprintJS、BrowserScan 等 30+ 检测平台测试
- **Auto-updating binary** — 后台更新检查，始终保持最新 stealth 构建
- **多语言 SDK** — Python (`pip install cloakbrowser`)、JavaScript (Playwright/Puppeteer)、Docker

## 安装与使用

**Python:**
```python
from cloakbrowser import launch

browser = launch()
page = browser.new_page()
page.goto("https://protected-site.com")  # 不再被拦截
browser.close()
```

**JavaScript (Playwright):**
```javascript
import { launch } from 'cloakbrowser';

const browser = await launch();
const page = await browser.new_page();
await page.goto('https://protected-site.com');
await browser.close();
```

**Docker:**
```bash
docker run --rm cloakhq/cloakbrowser cloaktest
```

## 技术架构

49个源代码补丁分布在：
- Canvas / WebGL 渲染指纹
- Audio 上下文指纹
- Font 枚举行为
- GPU WebGL 参数
- Screen 分辨率/颜色深度
- WebRTC ICE 候选生成
- Network timing 特征
- Automation 端口/Header 检测
- CDP input 行为模拟

## 支持平台

| 平台 | 状态 | 补丁数 |
|------|------|--------|
| Linux x64 — Chromium 146 | ✅ 已发布 | 57 |
| macOS arm64/x64 — Chromium 145 | ✅ 已发布 | 26 |
| Windows x64 — Chromium 146 | ✅ 已发布 | 57 |
| JavaScript/Puppeteer + Playwright | ✅ 已发布 | — |
| Fingerprint rotation per session | ✅ 已发布 | — |
| 内置代理轮换 | 📋 计划中 | — |

## 安全性验证

```bash
# GPG 签名验证
gpg --keyserver keyserver.ubuntu.com --recv-keys C60C0DDC9D0DE2DD
git verify-tag chromium-v146.0.7680.177.3

# GitHub binary attestation
gh attestation verify cloakbrowser-linux-x64.tar.gz --repo CloakHQ/cloakbrowser

# Docker 镜像签名验证
cosign verify \
  --certificate-identity-regexp "https://github.com/CloakHQ/CloakBrowser/" \
  --certificate-oidc-issuer "https://token.actions.githubusercontent.com" \
  cloakhq/cloakbrowser:latest
```

## 与竞品对比

| 特性 | CloakBrowser | Camoufox |
|------|-------------|---------|
| 底层 | Chromium (源代码补丁) | Firefox |
| Playwright 支持 | ✅ 原生支持 | ❌ |
| TLS 指纹 | 匹配真实 Chrome | 较差 |
| 生产可用 | ✅ 稳定版 | ⚠️ 不稳定 beta |

## 链接

- GitHub: https://github.com/CloakHQ/CloakBrowser
- PyPI: https://pypi.org/project/cloakbrowser
- npm: https://www.npmjs.com/package/cloakbrowser
- 官网: https://cloakbrowser.dev

> ⚠️ 本工具仅供合法的自动化测试和研究使用。自动化未授权系统、凭证填充、账号批量创建等行为均被明确禁止。
