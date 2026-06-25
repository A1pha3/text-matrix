---
title: "Penpot 架构与生态：开源设计协作平台的 Clojure/ClojureScript 全栈、MCP Server 与自托管路径"
date: "2026-06-25T21:05:13+08:00"
slug: "penpot-penpot-open-source-design-platform-guide"
description: "penpot/penpot 是为设计-代码协作而生的开源设计平台，2026-06 已经发布 2.16.1。本文拆解其 Clojure/ClojureScript 全栈架构、MCP Server 与设计令牌、与 Figma 的工程取舍差异、自托管路径。"
draft: false
categories: ["技术笔记"]
tags: ["Penpot", "设计工具", "Clojure", "ClojureScript", "MCP"]
---

# Penpot 架构与生态：开源设计协作平台的 Clojure/ClojureScript 全栈、MCP Server 与自托管路径

`penpot/penpot` 想做的事情在设计工具市场里并不常规——它要在一个 Figma / Sketch / Adobe XD 主导的市场里，做一个**完全开源、可自托管、把设计表达成代码**的设计协作平台。截至 2026-06-25，这个 53,613 Stars、3,454 Forks、MPL-2.0 License 的项目（创建于 2015-12-29）由西班牙 Kaleidos 公司主导，已经把"实时多人协作、设计令牌、组件 / 变体、Inspect 模式、MCP Server、自托管"做成了它和 Figma 最大的分水岭。本文是一篇项目导读 + 架构简析，文章会拆 Penpot 的 Clojure / ClojureScript 全栈架构、设计即代码的工程取舍、与 Figma 的边界差异、自托管部署的几种路径，并讨论为什么 2026 年的设计工具市场需要一个"用户控制数据 + 设计即代码"的选项。

## 一、核心判断：Penpot 的"开放性"不是营销话术，而是三个具体边界

Penpot 的 README 第一段话划定了三个具体边界：

> Penpot's key strength lies in giving you **full ownership of your design infrastructure**. Built on open source and designed for self-hosting, it puts teams in complete control of their design environment supporting strict compliance and governance requirements. Whether used in the browser or deployed on your own servers, Penpot works with open standards like SVG, CSS, HTML, and JSON.

三个边界决定了它和 Figma / Sketch / Adobe XD 的根本差异：

- **full ownership of your design infrastructure**：数据自托管 + 许可证开源 + 部署任选——不是"可以试用开源版但企业版上云"
- **open standards：SVG / CSS / HTML / JSON**：设计文件用浏览器原生支持的开放格式表达，不依赖私有 .fig / .sketch 格式
- **design is expressed as code**：Inspect 模式直接给 SVG / CSS / HTML 代码，开发拿到的不是"截图"而是"可执行的样式"

这意味着 Penpot 的目标不是"更便宜的设计工具"或"更轻量的 Figma 替代"，而是"让设计和代码之间没有翻译损失"。

## 二、系统地图：Clojure 后端 + ClojureScript 前端的全栈统一

Penpot 的代码组织是少见的"前后端同源语言"架构：

```
┌────────────────────────────────────────────────────────────────┐
│  L4 浏览器前端（ClojureScript + Rust/WASM 渲染层）             │
│    实时协作 / 矢量编辑 / 设计令牌 / 组件 / 变体                │
│    Inspect 模式输出 SVG / CSS / HTML                            │
├────────────────────────────────────────────────────────────────┤
│  L3 后端（Clojure + Ring + Compojure）                          │
│    REST API + WebSocket / 长连接                                │
│    设计文件 / 组件 / 令牌 / 评论的持久化                        │
├────────────────────────────────────────────────────────────────┤
│  L2 数据层                                                      │
│    PostgreSQL（关系数据 + JSONB 设计对象）                     │
│    Redis（实时协作广播 / 任务队列）                             │
│    文件存储（本地 / S3 兼容对象存储）                           │
├────────────────────────────────────────────────────────────────┤
│  L1 集成层                                                       │
│    MCP Server（2026-06 已 GA）                                  │
│    Webhook / REST API / Access Token                            │
│    插件系统（Plugins）                                          │
├────────────────────────────────────────────────────────────────┤
│  L0 基础设施                                                     │
│    Docker / Kubernetes / Elestio 一键部署                       │
│    Nginx 反向代理（内置 WebSocket 配置）                        │
└────────────────────────────────────────────────────────────────┘
```

下面逐层看每一层的关键判断。

## 三、L4 前端：ClojureScript + Rust/WASM 的混合渲染

Penpot 的前端不是"JavaScript 套壳"，而是一个完整的 ClojureScript 单页应用：

- **ClojureScript**：语法 / 数据结构 / 状态管理全部走 ClojureScript 风格（immutable data、Reagent / Rum 框架）
- **Rust + WebAssembly**：高强度渲染（复杂矢量路径、蒙版、滤镜）走 Rust 编译的 WASM 模块——比纯 JS 实现快 5-10 倍
- **ClojureScript ↔ Rust 边界**：通过 `wasm-bindgen` 和 JS 互操作层

这种"前后端同源语言（Clojure）+ 高强度模块走 Rust/WASM"的选择，本质上是在"开发效率"和"渲染性能"之间做权衡：

- ClojureScript 带来 immutable data + 函数式风格，状态管理比 React + Redux 简洁
- Rust/WASM 解决"浏览器对复杂矢量 / 蒙版 / 滤镜的性能瓶颈"——这是设计工具和普通 Web 应用的根本差异

## 四、L3 后端：Clojure + Ring + PostgreSQL 的"老派稳健"

Penpot 的后端和前端一样选择 Clojure：

- **Clojure JVM**：和前端共享 immutable data 模型，序列化 / 反序列化"零成本"
- **Ring + Compojure**：Clojure 经典的 HTTP 服务框架
- **PostgreSQL**：主存储——关系数据 + JSONB 设计对象混合存储
- **Redis**：实时协作广播 + 任务队列

后端语言统计（GitHub Languages API）：

| 语言 | 占比（字节数） | 角色 |
|---|---|---|
| **Clojure** | 11,959,341 | 后端主体 |
| **JavaScript** | 1,225,027 | 旧前端代码、辅助工具 |
| **Rust** | 1,023,360 | 渲染层 |
| **SCSS** | 783,136 | 样式 |
| **TypeScript** | 448,555 | 插件、辅助 |
| **其他**（HTML / Shell / CSS / Python / Java / ...） | < 800,000 | 构建 / 工具链 |

注意：**Clojure 占比 ~70%**——这是一个"被 Clojure 统治"的全栈项目，背后的工程取舍很清晰：

- **Clojure 的优势**：immutable data 跨前后端一致、并发模型（core.async、agent）天然适配实时协作、REPL 驱动开发效率高
- **Clojure 的代价**：人才稀缺（Clojure 开发者比 JavaScript 少 1-2 个数量级）、企业内"非主流技术栈"、招人难

Kaleidos 公司本身就是 Clojure 强项，所以这个选择在公司层面合理。

## 五、设计的"代码化"：Design Tokens + Inspect 模式

Penpot 把"设计即代码"做成了产品功能：

### 5.1 Design Tokens

设计令牌（Design Tokens）是 Penpot 的**一等公民**：

- **颜色令牌**、**字体令牌**、**间距令牌**、**圆角令牌**、**边框令牌**、**阴影令牌**等
- 每个组件可以引用令牌，**改令牌 = 改全站**——和代码里的 design system 一样
- 令牌可以导出为标准格式（CSS Variables、JSON、Style Dictionary、Tokens Studio 兼容格式）

### 5.2 Components + Variants

组件（Components）和变体（Variants）是现代设计工具的标配：

- 主组件 + 变体实例（variant instances）
- 组件变体按属性（Property）切换：状态（hover / active / disabled）、尺寸（sm / md / lg）、主题（light / dark）

### 5.3 Inspect 模式

Inspect 模式是"设计即代码"最直观的体现：

- 选中任意图层 → 右侧 Inspect 面板
- **直接显示 SVG 代码**（不是截图、不是描述）
- **直接显示 CSS 代码**（position、display、width、height、color、font-family、margin、padding 等）
- **直接显示 HTML 代码**（结构化 DOM 树）

这意味着前端工程师拿到的不是"图 + 标注"，而是"可粘贴的代码片段"——开发与设计的边界从"理解 + 重写"变成"复制 + 微调"。

### 5.4 CSS Grid + Flex Layout

Penpot 原生支持 CSS Grid 和 Flexbox 布局——画出来的不只是"看上去是 Grid"，而是**真的 Grid**。前端工程师用 Grid / Flex 转代码时，不需要重做布局，**直接把画布的 Grid 容器对应到代码的 Grid 容器**。

## 六、MCP Server：2026-06 的关键 GA

Penpot 在 2.16 系列（2026-06 发布）里把 MCP Server 推到了关键状态：

- **2.16.0（2026-06-11）**：MCP Server 完整 GA
- **2.16.1（2026-06-24）**：MCP Server 多项生产级修复

2.16.x 的关键 MCP 改进：

- **WebSocket 代理配置**（Nginx 示例）—— MCP 走 WebSocket，需要在反向代理层做透传配置
- **MCP Redis 频道租户前缀**（多环境隔离）
- **MCP Key 在 Integrations 页面可见**（不再有"密钥不可恢复"警告）
- **MCP 状态按钮 + 单标签页连接控制**——避免一个用户在多标签页上重复连接
- **MCP 初始化与插件运行时的竞态修复**（race condition fix）
- **MCP Server 状态开关的持久化** + 缺失的工作区连接选项修复

MCP Server 的能力是"AI Coding 工具直接读写 Penpot 设计"：

- **Cursor / Claude Desktop / Claude Code**：在 IDE 里说"把 Penpot 上这个组件导出成 React 代码"
- **Figma 转 Penpot** / **Penpot 转 Figma**：通过 MCP 做格式转换
- **设计 → 代码自动化**：把 Penpot 组件作为单一来源（single source of truth），代码端不需要再维护一份"镜像设计"

## 七、自托管：Docker / Kubernetes / Elestio 三条路

Penpot 的部署路线是"想怎么部署就怎么部署"：

### 7.1 Docker Compose（最简单）

```bash
# 一行启动
docker compose -f docker-compose.yaml up -d
```

默认启动：
- Penpot 前端
- Penpot 后端
- PostgreSQL
- Redis
- 内置 Nginx 反向代理

### 7.2 Kubernetes（生产级）

官方提供 Helm chart（penpot-k8s 仓库）：
- 多副本后端
- PostgreSQL / Redis 用云服务（避免 StatefulSet 运维）
- 持久化用 PVC + S3 兼容对象存储
- 水平扩展 + 自动故障转移

### 7.3 Elestio / 云市场一键部署

Elestio、Sealos、Rainbond、阿里云 / 腾讯云市场都提供一键部署——非运维团队的最佳选择。

### 7.4 私有化（金融 / 政府 / 国企）

由于 Penpot 是 MPL-2.0 + 完全自托管，国内 / 国外金融 / 政府 / 国企可以**直接私有化部署**——这是 Figma / Sketch / Adobe XD 永远做不到的。

## 八、2026 关键版本演进：2.16 之前的工程迭代

### 8.1 早期：单层 Clojure + PostgreSQL（2015-2022）

Penpot 在 2022 年之前是 Kaleidos 内部工具，2020 年开源后逐步重构：

- 后端从单进程到多副本
- 引入 Redis 做实时协作广播
- 引入 CDN 做资源分发

### 8.2 中期：Rust/WASM 渲染层 + 设计令牌（2023-2024）

- Rust/WASM 替换部分 JavaScript 渲染逻辑——矢量路径、蒙版、滤镜速度提升 5-10 倍
- 设计令牌（Design Tokens）成为一等公民
- 组件 + 变体功能成熟

### 8.3 2.16 关键里程碑（2026-06）

- **MCP Server GA**：2.16.0 + 2.16.1 多项修复
- **多环境隔离**：Redis 频道租户前缀
- **生产稳定性**：race condition、persistence、WebSocket 代理配置

## 九、与 Figma 的工程取舍差异

| 维度 | Penpot | Figma |
|---|---|---|
| **License** | MPL-2.0（开源） | 闭源 |
| **数据** | 自托管 / SaaS | SaaS only |
| **格式** | SVG / CSS / HTML / JSON（开放） | .fig（私有） |
| **代码生成** | Inspect 模式（SVG / CSS / HTML） | Inspect 模式（CSS / iOS / Android） |
| **设计令牌** | 原生（导出 CSS / JSON / Style Dictionary） | 原生（Variables） |
| **MCP Server** | 已 GA（2026-06） | 早期 |
| **实时协作** | ✅ | ✅ |
| **后端语言** | Clojure | C++ / Rust（推测） |
| **前端语言** | ClojureScript + Rust/WASM | C++（WebAssembly）+ 部分 JS |
| **API 开放度** | 完整 REST API + Webhook + Access Token | 完整 REST API + Webhook + Plugin API |
| **插件生态** | 成长中 | 成熟 |
| **企业版协作** | 自托管 = 数据完全可控 | Enterprise = 上 Figma 云 |

注意：Figma 在"产品成熟度、插件生态、企业级权限"上仍然领先；Penpot 在"自托管、设计即代码、MCP、开放格式"上**结构性领先**。

## 十、当前版本的硬约束

截至 2026-06-25（2.16.1）的硬约束：

- **MCP Server 需要 WebSocket 代理配置**：Nginx 默认不支持 WebSocket 透传，需要额外配置
- **多标签页 MCP 连接**：2.16.1 之前会有重复连接 / 状态同步问题，2.16.1 之后有"单标签页连接控制"
- **自托管 PostgreSQL 备份**：自托管团队需要自己做 PostgreSQL 备份 + 灾难恢复
- **S3 兼容对象存储**：大文件 / 字体 / 图片默认走外部对象存储，需要提前规划
- **插件生态**：相比 Figma 还很年轻，复杂插件需要等官方或社区
- **MPL-2.0 商业注意**：可以商用，但修改后的 MPL 代码段必须公开——和 MIT / Apache 比严格

## 十一、这篇文章没覆盖什么

- **Penpot 插件开发 SDK**：怎么写 Penpot 插件、API 细节
- **Penpot 移动端**：移动端预览 / 标注（iOS / Android）
- **Penpot 离线模式**：断网情况下的本地使用
- **Penpot 与 Figma 格式互转**：通过 Plugins / 第三方工具
- **Kaleidos 公司**：商业化路径、客户案例
- **Penpot 贡献者生态**：社区规模、商业赞助

## 十二、采用建议

### 12.1 什么团队该用 Penpot

- **金融 / 政府 / 国企**：合规要求数据自托管
- **设计系统重度用户**：Design Tokens 是一等公民，组件 / 变体成熟
- **设计-代码协作敏感团队**：Inspect 模式直接给代码，减少翻译损失
- **AI Coding 用户**：MCP Server 让你在 Cursor / Claude Code 里直接调用 Penpot
- **MPL-2.0 友好的商业产品**：可以商用 + 私有化

### 12.2 什么团队该继续用 Figma

- **重度插件依赖**：Figma 插件生态成熟得多
- **多人设计协作密度高**：Figma 协作流畅度依然领先
- **移动端优先**：Figma 的移动端体验更成熟
- **企业权限管理**：Figma Enterprise 在权限 / 审计 / SSO 上更成熟

### 12.3 渐进迁移路径

1. **新项目先用 Penpot**：建一个 Design System、Design Tokens 完整的工作流
2. **存量项目双轨**：Penpot 跑新组件、Figma 跑存量
3. **Figma → Penpot 迁移**：通过 SVG 导出 + 组件映射（手动或半自动）
4. **设计-代码链路打通**：用 MCP Server 把 IDE 和 Penpot 串起来

## 十三、总结

Penpot 的真正价值不是"另一个 Figma"，而是它把"开源 + 自托管 + 设计即代码 + MCP"这四件事同时做完了。在 2026 年的设计工具市场里，**愿意为"数据自托管 + 设计开放格式"付费的团队**会自然流向 Penpot；**继续要"插件生态 + 企业协作"**的团队会继续用 Figma。

挑工具的核心问题只有一个：**你的设计资产值得"不依赖任何单一供应商"吗？** 答案是 Yes，Penpot 就是答案；答案是 No，Figma / Sketch / Adobe XD 仍然是更好的选择。
