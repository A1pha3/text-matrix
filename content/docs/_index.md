---
title: "项目系统文档"
date: 2026-03-24T12:00:00+08:00
draft: false
build:
  render: never
  list: never
cascade:
  build:
    render: never
    list: never
---

## 📚 项目系统文档 (Docs)

这一栏是 Text Matrix 站点的系统文档集合，面向站点读者，也作为我自己维护 AI 内容矩阵站点的资料库。

当前 `content/docs/` 目录只保留 5 篇面向站点读者的核心文档。其余工程内部资料已迁移到仓库根目录 `docs/`，不在站点页面导航中展示。

---

## 核心文档

* **[Hugo 目录结构解析：docs 与 posts 的区别](./hugo-docs-vs-posts/)**：解释文档和博文为什么要分开存储。
* **[Hugo 新手多平台上线实战](./hugo-multi-platform-deploy/)**：通过 GitHub 自动同步部署到 Vercel 和 Cloudflare。
* **[Hugo 站内搜索方案对比与迁移成本评估](./hugo-search-solution-comparison/)**：对比 LoveIt 内置 Lunr 与 Pagefind 两种搜索路径，并评估当前仓库的改造成本。
* **[Hugo 静态网站访问统计方案全解析](./hugo-website-analytics-guide/)**：接入 Google Analytics、百度统计等三方工具。
* **[Hugo 静态网站生成器完全指南](./hugo使用教程/)**：面向 Web 开发者的 Hugo 全面技术教程与入门指南。

---

## 📝 维护说明

1. **Docs vs Posts**：本目录下的内容属于"常青文档"，不具有强烈的时效性。
2. **目录边界**：站点公开文档保留在 `content/docs/`，仓库内部资料统一维护在仓库根目录 `docs/`。
3. **更新机制**：若新增或移除站点公开文档，请同步更新本文档导航。
