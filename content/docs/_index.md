---
title: "项目系统文档"
date: 2026-03-24T12:00:00+08:00
draft: false
---

# 📚 项目系统文档 (Docs)

欢迎来到 **Text Matrix** 的系统文档库。这里不仅是本站的“操作指南”，更是我构建整个 AI 内容矩阵站点的“知识资产库”。

本目录下的文档被分为两大核心模块：**Hugo 架构设计** 与 **GitHub 基础设施**。

---

## 🛠️ Hugo 架构与设计 (Architecture)
本站采用 Hugo 构建，并基于 LoveIt 主题进行了深度定制。以下是核心的设计决策与操作手册：

### 核心规范
*   **[网站内容架构与主页设计规范](./site-content-architecture-design/)**：定义了物理目录、逻辑分类及主页流量分流策略。
*   **[Hugo 目录结构解析：docs 与 posts 的区别](./hugo-docs-vs-posts/)**：解释了为什么文档和博文要分开存储。

### 学习与研究
*   **[Hugo 静态网站生成器完全指南](./hugo使用教程/)**：面向 Web 开发者的 Hugo 全面技术教程与入门指南。
*   **[Hugo 系统学习路线图](./system-learning/)**：面向源码学习的训练手册与闭环方法。
*   **[Hugo 系统调研记录](./system-research/)**：前期技术选型与功能调研记录。
*   **[Hugo 系统使用手册](./system-usage/)**：日常维护、本地预览与内容更新的实操流程。

### 功能增强
*   **[Hugo 静态网站访问统计方案全解析](./hugo-website-analytics-guide/)**：如何接入 Google Analytics、百度统计等三方工具。

---

## 🐙 GitHub 基础设施 (Infrastructure)
本站的代码托管、版本控制与自动化部署主要依赖 GitHub 平台。

### 托管与部署
*   **[GitHub Pages 自定义域名配置指南](./github-pages-custom-domain/)**：详解 Apex 域名、子域名配置及 DNS 踩坑排查。
*   **[Hugo 新手多平台上线实战](./hugo-multi-platform-deploy/)**：如何通过 GitHub 自动同步部署至 Vercel 和 Cloudflare。

### 权限管理
*   **[GitHub 个人访问令牌 (PAT) 生成与使用](./github_personal_access_tokens/)**：在 macOS 终端操作 GitHub 时解决身份认证问题的必备手册。

---

## 📝 维护说明
1.  **Docs vs Posts**：本目录下的内容属于“常青文档”，不具有强烈的时效性。
2.  **更新机制**：所有文档均应保持最新，若底层架构发生变化，请同步更新本文档导航。
