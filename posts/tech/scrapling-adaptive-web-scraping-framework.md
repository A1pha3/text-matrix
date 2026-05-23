# Scrapling: 自适应Web爬虫框架，单次请求到全站爬取一键搞定

**🏷️ 分类：** 工具 · 爬虫  
**⭐ Stars：** 53,257  
**🔗 地址：** https://github.com/D4Vinci/Scrapling  
**🌐 官网：** -

**一句话总结：** 一款自适应Web爬取框架，能自动处理登录验证、CSS选择器、反爬机制，从单次请求到全站爬取一条命令搞定。

---

## 🎯 这个工具解决什么问题？

手动写爬虫最痛苦的几件事：
- 每个网站结构不同，CSS选择器写完就废
- 遇到登录墙、验证码、反爬机制直接卡死
- 想全站爬取要写一堆递归逻辑
- 改版后选择器全部失效

Scrapling 通过**自适应解析引擎**自动解决这些问题，号称"handles everything from a single request to a full-scale crawl"。

---

## ⚡ 核心特性

### 1. 自适应解析
自动检测页面结构，无需手动写复杂选择器

### 2. 内置登录/验证码处理
能自动处理 Cookie 登录、基础认证，部分情况可绕过验证码

### 3. 全站爬取模式
一条命令递归爬取整站，支持深度控制和去重

### 4. 反爬对抗
内置请求间隔、UA轮换、代理池支持

### 5. 多种输出格式
JSON / CSV / HTML / 自定义模板均可

---

## 📦 安装

```bash
pip install scrapling
```

---

## 🚀 快速上手

### 单页爬取
```python
from scrapling import Spider

# 简单爬取
spider = Spider("https://example.com")
data = spider.extract(selector=".article-content")
print(data)
```

### 全站爬取
```python
from scrapling import Crawler

crawler = Crawler("https://example.com", depth=3)
crawler.run()
```

---

## 💡 使用场景

| 场景 | 说明 |
|------|------|
| 竞品监控 | 全站爬取电商/媒体内容 |
| 数据集构建 | 快速采集训练数据 |
| 价格监控 | 竞品价格实时爬取 |
| 内容聚合 | 多源内容整合 |

---

## ⚠️ 注意事项

- 请遵守网站的 `robots.txt` 和使用条款
- 不要对目标网站造成过大负载
- 部分反爬机制可能需要配合代理池使用

---

**相关工具：** [ShadowBroker](shadowbroker-open-source-intelligence-platform) · [OpenWA](https://example.com)