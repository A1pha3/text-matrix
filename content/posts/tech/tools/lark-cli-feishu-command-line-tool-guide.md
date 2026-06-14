---
title: "Lark CLI：飞书官方命令行工具从入门到精通"
date: "2026-04-01T20:47:00+08:00"
slug: lark-cli-feishu-command-line-tool-guide
aliases:
  - /posts/tech/lark-cli-feishu-command-line-tool-guide/
categories: ["技术笔记"]
tags: ["Lark", "飞书", "CLI", "AI Agent", "OpenAPI"]
description: "基于官方公开信息系统讲解飞书官方 Lark CLI：功能版图、三层命令架构、认证机制、AI Agent Skills、源码阅读路径、开发扩展与从新手到专家的实践路线。"
---

## 学习目标

阅读本文后，您将能够：

- ✅ 准确认识 Lark CLI 的定位、边界与适用场景
- ✅ 理解 Shortcuts、API Commands、Raw API 三层命令架构
- ✅ 掌握人类用户与 AI Agent 两种使用路径
- ✅ 理解认证、权限范围、身份切换与安全机制
- ✅ 熟练使用输出格式、分页、`--dry-run`、`schema` 等高级能力
- ✅ 看懂 Lark CLI 的 Skills 体系与扩展思路
- ✅ 按照“新手 → 熟手 → 专家”的路线逐步进阶
- ✅ 从公开仓库结构出发，建立可靠的源码阅读路径

---

## 一、Lark CLI 是什么

### 1.1 定义

**Lark CLI**（仓库名 `larksuite/cli`，命令名 `lark-cli`）是飞书 / Lark 官方提供的命令行工具，面向两类用户：

- **人类用户**：希望在终端里高效完成飞书开放平台操作的开发者、运维人员、自动化工程师
- **AI Agent**：需要通过结构化命令、安全凭证和稳定输出接入飞书能力的智能体系统

它的作用，不是简单把网页按钮搬到终端里，而是把飞书开放平台能力整理成一套**可脚本化、可审计、可自动化、对 Agent 友好**的命令系统。

### 1.2 截至 2026-04-01 的公开信息

| 指标 | 数值 |
| ---- | ---- |
| **GitHub Stars** | 8,013 |
| **GitHub Forks** | 512 |
| **许可证** | MIT |
| **主语言** | Go 98.2% |
| **npm 当前版本** | 1.0.13 |
| **最新发布** | 2026-03-31 |
| **覆盖能力** | 11 个业务领域、200+ 命令、20+ 个 AI Agent Skills |

> 上表来自项目 GitHub 仓库首页与 npm 包页面的公开展示信息。由于 Stars、Forks 等数据会动态变化，实际数值请以访问当日页面为准。

### 1.3 一句话定位

Lark CLI 的定位：

> **它是飞书开放平台的官方命令行操作层，也是 AI Agent 调用飞书能力的工程化接口层。**

### 1.4 为什么它值得单独研究

很多 CLI 只是“给开发者看的工具”，而 Lark CLI 明显多做了一层：

- 对人类用户，它提供了更短、更直观、更适合终端操作的快捷命令
- 对 AI Agent，它提供了结构化输出、智能默认值、权限检查与安全保护
- 对平台能力，它又没有把自己限制死，而是保留了原始 API 直通能力

它同时解决了三个问题：

1. **效率问题**：常见操作不必每次写复杂请求
2. **抽象问题**：把高频 API 提炼成更易调用的命令
3. **覆盖问题**：当封装不够时，仍可回退到原始 API

---

## 二、Lark CLI 解决了什么问题

### 2.1 传统开放平台调用的痛点

在没有官方 CLI 的情况下，调用飞书开放平台常见有三种方式：

- 直接写后端代码接 SDK
- 手写 HTTP 请求调 OpenAPI
- 在网页后台与 API 文档之间反复切换

这些方式都能工作，但对很多场景并不友好：

| 痛点 | 表现 |
| ---- | ---- |
| **试错成本高** | 每次都要处理鉴权、参数、请求体与响应解析 |
| **自动化门槛高** | 临时脚本多、复用性差 |
| **Agent 集成差** | 原始 API 返回结构复杂，不利于模型稳定调用 |
| **权限风险大** | 缺少明确的范围检查与操作前预览 |
| **学习路径断裂** | 新手不知道应该先学 API，还是先学权限、事件、资源模型 |

### 2.2 Lark CLI 的应对方式

Lark CLI 的设计思路很清晰：**把“最常用的能力”做成高层命令，把“全部能力”保留在底层通道里。**

对应到产品形态上，就是三层命令系统：

- **Shortcuts**：最适合人和 Agent 的快捷操作层
- **API Commands**：与平台 API 1:1 映射的中间层
- **Raw API**：对任意开放平台端点的直接访问层

这是一种很工程化的折中方案：既追求效率，也不牺牲覆盖率。

---

## 三、功能版图：Lark CLI 到底能做什么

### 3.1 11 大业务领域

根据官方 README，Lark CLI 当前覆盖以下 11 个业务领域：

| 业务领域 | 主要能力 |
| -------- | -------- |
| **📅 Calendar** | 查看议程、创建活动、邀请参与者、查询忙闲状态、时间建议 |
| **💬 Messenger** | 发送 / 回复消息、管理群聊、查看历史、搜索消息、下载媒体 |
| **📄 Docs** | 创建、读取、更新、搜索文档，读写媒体与白板 |
| **📁 Drive** | 上传 / 下载文件，搜索文档与知识库，管理评论 |
| **📊 Base** | 管理表格、字段、记录、视图、仪表盘、工作流、表单、角色权限、数据分析 |
| **📈 Sheets** | 创建、读取、写入、追加、查找、导出电子表格 |
| **✅ Tasks** | 创建、查询、更新、完成任务，管理任务清单、子任务、提醒、评论 |
| **📚 Wiki** | 创建和管理知识空间、节点、文档 |
| **👤 Contact** | 按姓名、邮箱、电话搜索用户，获取资料 |
| **📧 Mail** | 浏览、搜索、阅读邮件，发送、回复、转发、草稿管理 |
| **🎥 Meetings** | 搜索会议记录，查询会议纪要与录制内容 |

### 3.2 这张功能表意味着什么

从这张能力表可以看出，Lark CLI 不只是“消息发送器”或“简单的机器人工具”，而是把飞书开放平台中最常见、最实用的一组业务面全部串了起来。

这让它特别适合以下任务：

- 工作流自动化
- 团队协同数据同步
- 文档与知识库批量处理
- Agent 驱动的任务执行
- 会议、邮件、消息的一体化自动汇总

---

## 四、核心概念：先把名词讲清楚

### 4.1 什么是 Shortcuts

**Shortcuts** 是 Lark CLI 为高频操作设计的快捷命令层，命令前通常带 `+`。

它的目标不是完全还原底层 API，而是把用户真正常用的动作变成更顺手的命令，例如：

```bash
lark-cli calendar +agenda
lark-cli im +messages-send --chat-id "oc_xxx" --text "Hello"
lark-cli docs +create --title "Weekly Report" --markdown "# Progress\n- Completed feature X"
```

Shortcuts 的特点是：

- 参数更短
- 默认值更合理
- 输出更适合人类阅读或 Agent 消费
- 更强调“完成任务”，而不是“复刻 HTTP 请求”

### 4.2 什么是 API Commands

**API Commands** 是平台 API 的命令行映射层。官方说明它们是**根据 Lark OAPI 元数据自动生成，并经过评估和质量门控筛选**的命令集合。

：

- 它们比 Shortcuts 更贴近开放平台原始模型
- 它们比 Raw API 更结构化、更安全
- 当您已经熟悉某个 API 时，用它会更直接

例如：

```bash
lark-cli calendar calendars list
lark-cli calendar events instance_view --params '{"calendar_id":"primary","start_time":"1700000000","end_time":"1700086400"}'
```

### 4.3 什么是 Raw API

**Raw API** 是逃生口，也是全量覆盖层。命令前缀是 `api`，允许您直接调用开放平台端点。

```bash
lark-cli api GET /open-apis/calendar/v4/calendars
```

它的意义有两个：

- 当 CLI 尚未对某个能力做高层封装时，您仍可直接调用
- 当您要调试底层接口、对照文档、验证请求体时，它是最透明的一层

### 4.4 什么是 Skill

在 Lark CLI 的语境里，**Skill** 不是单个 API，而是一组围绕某个业务域组织起来的 Agent 能力包。

可以把它理解为：

- 对人类：一个更高层的任务能力分组
- 对 Agent：一套可直接接入的结构化工具定义

### 4.5 什么是 Schema 内省

`schema` 命令不是业务操作命令，而是**自我描述能力**。它可以显示某个命令或 API 方法的参数、请求体、响应结构、支持的身份与权限范围。

这对两类人特别重要：

- 想准确调用接口的开发者
- 需要先读结构、再决定如何组装调用的 AI Agent

---

## 五、三层命令架构：这是本文最重要的部分

### 5.1 三层架构总览

| 层级 | 关键词 | 适合谁 | 典型用途 |
| ---- | ------ | ------ | -------- |
| **Shortcuts** | 快、顺手、面向任务 | 新手、人类用户、Agent | 高频操作、日常工作流 |
| **API Commands** | 结构化、贴近平台模型 | 熟悉 API 的开发者 | 精准调用某个公开方法 |
| **Raw API** | 完整覆盖、最低抽象 | 调试者、平台开发者 | 访问未封装端点、底层联调 |

### 5.2 为什么要做三层，而不是只做一层

这是 Lark CLI 最值得学习的设计点之一。

如果只有 Shortcuts：

- 上手容易
- 但覆盖会不完整

如果只有 Raw API：

- 覆盖完整
- 但学习和使用成本都很高

如果只有 API Commands：

- 技术上比较平衡
- 但仍不够“任务导向”

所以，三层方案实际上是在解决**抽象层级冲突**：

- **高层**负责效率
- **中层**负责结构
- **底层**负责完整性

### 5.3 一个命令在三层中的长相

以“发送消息”为例：

```bash
# Shortcuts：目标导向
lark-cli im +messages-send --chat-id "oc_xxx" --text "Hello"

# Raw API：协议导向
lark-cli api POST /open-apis/im/v1/messages \
  --params '{"receive_id_type":"chat_id"}' \
  --body '{"receive_id":"oc_xxx","msg_type":"text","content":"{\"text\":\"Hello\"}"}'
```

二者的区别不在于“能不能做”，而在于**调用者需要承担多少底层细节**。

### 5.4 可把它理解成一条能力漏斗

```text
用户目标 / Agent 任务
        ↓
Shortcuts（以任务为中心）
        ↓
API Commands（以平台方法为中心）
        ↓
Raw API（以 HTTP 端点为中心）
        ↓
Lark / 飞书开放平台
```

这条漏斗体现出一个很实用的原则：

> **优先用最高层、最省心的抽象；只有在不够用时，才向下走。**

---

## 六、快速开始：从 0 到第一次成功调用

### 6.1 环境要求

| 项目 | 说明 |
| ---- | ---- |
| **Node.js** | 需要 npm / npx |
| **Go 1.23+** | 仅在从源码构建时需要 |
| **Python 3** | 同样仅在从源码构建时需要 |

### 6.2 安装方式

#### 方式一：从 npm 安装（推荐）

```bash
npm install -g @larksuite/cli
npx skills add larksuite/cli -y -g
```

#### 方式二：从源码安装

```bash
git clone https://github.com/larksuite/cli.git
cd cli
make install
npx skills add larksuite/cli -y -g
```

### 6.3 人类用户的最短路径

官方 README 给出的人类用户快速开始如下：

```bash
# 1. 配置应用凭证
lark-cli config init

# 2. 登录
lark-cli auth login --recommend

# 3. 开始使用
lark-cli calendar +agenda
```

这里有一个常被忽略的关键点：

- `config init` 更适合常规人工引导
- `auth login --recommend` 会自动选择常用权限范围
- 第一次成功调用业务命令，才意味着整个链路真正打通

### 6.4 AI Agent 的最短路径

对于 AI Agent，官方建议走另一条更适合自动化的路径：

```bash
# 1. 安装
npm install -g @larksuite/cli
npx skills add larksuite/cli -y -g

# 2. 后台配置应用凭证
lark-cli config init --new

# 3. 后台登录
lark-cli auth login --recommend

# 4. 验证状态
lark-cli auth status
```

为什么 AI Agent 路径里强调后台运行？

因为配置和登录都可能产生浏览器授权 URL，需要：

1. 命令先启动
2. 提取授权链接
3. 让用户在浏览器完成操作
4. 再回到终端继续轮询或验证

这条路径比人类用户多了一层“人机协作”，但也更符合 Agent 实际工作方式。

---

## 七、认证、权限与身份切换

### 7.1 认证命令一览

| 命令 | 作用 |
| ---- | ---- |
| `auth login` | 执行 OAuth 登录 |
| `auth logout` | 清除本地凭证并登出 |
| `auth status` | 查看当前登录状态和已授权范围 |
| `auth check` | 检查特定权限是否已经授权 |
| `auth scopes` | 列出应用可用权限范围 |
| `auth list` | 列出全部已认证用户 |

### 7.2 为什么权限是 Lark CLI 的核心主题

对飞书开放平台来说，真正难的往往不是“发出请求”，而是“有没有资格发出请求”。

Lark CLI 把权限问题放到了非常显眼的位置，这很合理，因为它直接影响：

- 请求是否成功
- Agent 能执行到什么边界
- 自动化是否安全

### 7.3 常见认证方式

```bash
# 交互式登录
lark-cli auth login

# 按业务域过滤权限
lark-cli auth login --domain calendar,task

# 推荐范围
lark-cli auth login --recommend

# 精确指定权限
lark-cli auth login --scope "calendar:calendar:readonly"
```

### 7.4 Agent 相关的关键参数

```bash
# 立即返回验证 URL，适合自动化协作
lark-cli auth login --domain calendar --no-wait

# 后续恢复轮询
lark-cli auth login --device-code <DEVICE_CODE>
```

这两个参数值得重点理解：

- `--no-wait`：把“授权动作”拆成异步流程
- `--device-code`：允许把登录过程拆成前后两步恢复

对 Agent 而言，这比单次阻塞式交互更实用。

### 7.5 身份切换

Lark CLI 支持以不同身份执行命令，例如用户身份或机器人身份：

```bash
lark-cli calendar +agenda --as user
lark-cli im +messages-send --as bot --chat-id "oc_xxx" --text "Hello"
```

这项能力的意义很大，因为很多自动化任务并不适合始终以同一种身份执行。

可以把它理解成：

- **用户身份**：更接近“代人操作”
- **机器人身份**：更接近“系统自动执行”

---

## 八、从新手到专家：最推荐的学习顺序

### 8.1 新手阶段：先学 Shortcuts，不要一上来就研究 Raw API

如果您第一次接触 Lark CLI，最合理的路径是：

1. 完成安装与登录
2. 跑通一个 `+` 命令
3. 理解业务域是怎么组织的
4. 再去看 `schema`
5. 最后再研究 Raw API

建议先练这三条：

```bash
lark-cli calendar +agenda
lark-cli im +messages-send --chat-id "oc_xxx" --text "Hello"
lark-cli docs +create --title "Weekly Report" --markdown "# Progress\n- Completed feature X"
```

### 8.2 熟手阶段：转向 API Commands

当您已经熟悉常见 Shortcut 后，就该学会：

- 查帮助
- 看 schema
- 找对应 API 命令
- 判断什么时候该从 Shortcut 下沉到 API Commands

例如：

```bash
lark-cli schema calendar.events.instance_view
lark-cli calendar events instance_view --params '{"calendar_id":"primary","start_time":"1700000000","end_time":"1700086400"}'
```

### 8.3 专家阶段：掌握 Raw API、权限设计与扩展

高级使用者通常会关注：

- 未封装 API 如何直连
- 如何把命令接入自动化脚本
- 如何为 Agent 设计最小权限范围
- 如何扩展自定义 Skill

这个阶段的重点已经不是“会不会用”，而是：

> **如何把它嵌入自己的工程体系里。**

### 8.4 一张阶段路线图

| 阶段 | 目标 | 重点能力 |
| ---- | ---- | -------- |
| **新手** | 跑通第一个命令 | 安装、登录、Shortcut |
| **进阶** | 理解平台结构 | 业务域、schema、API Commands |
| **熟练** | 进行真实自动化 | 输出格式、分页、`--dry-run`、权限检查 |
| **专家** | 接入 Agent / 工作流 | Skills、Raw API、最小权限设计、二次扩展 |

---

## 九、常用高级能力：真正好用的地方在这里

### 9.1 输出格式

| 参数 | 说明 |
| ---- | ---- |
| `--format json` | 默认完整 JSON 输出 |
| `--format pretty` | 更适合人类阅读 |
| `--format table` | 表格形式展示 |
| `--format ndjson` | 适合管道处理 |
| `--format csv` | 适合导出到表格工具 |

这说明 Lark CLI 不只是“执行命令”，还考虑了命令结果接下来要流向哪里：

- 人看
- 脚本接
- 管道传
- 表格分析

### 9.2 分页

```bash
--page-all
--page-limit 5
--page-delay 500
```

分页参数的重要性在于，它让 CLI 从“单次调用工具”变成“可控批量处理工具”。

尤其在处理消息、任务、记录这类列表型资源时，分页能力决定了您能不能稳定做自动化。

### 9.3 干运行

对于可能带副作用的命令，先用 `--dry-run` 非常重要：

```bash
lark-cli im +messages-send --chat-id oc_xxx --text "hello" --dry-run
```

这对生产环境尤其关键，因为它相当于在真正执行前先做一次“预演”。

### 9.4 Schema 内省

```bash
lark-cli schema
lark-cli schema calendar.events.instance_view
lark-cli schema im.messages.delete
```

`schema` 的价值，远远不只是“看文档”：

- 它帮您确认参数长什么样
- 它帮 Agent 在调用前先理解结构
- 它帮您减少“猜参数”带来的失败率

---

## 十、AI Agent Skills 体系：为什么它对 Agent 友好

### 10.1 19 个 Skills 的整体结构

官方列出的 19 个 Skills 如下：

| Skill | 作用 |
| ----- | ---- |
| `lark-shared` | 应用配置、登录、身份切换、权限管理、安全规则 |
| `lark-calendar` | 日历事件、议程、忙闲查询、时间建议 |
| `lark-im` | 消息、群聊、搜索、文件上传下载、表情反应 |
| `lark-doc` | Markdown 风格的文档创建、读取、更新、搜索 |
| `lark-drive` | 云盘上传下载、权限与评论管理 |
| `lark-sheets` | 表格读写、追加、导出 |
| `lark-base` | 多维表格的表、字段、记录、视图与分析 |
| `lark-task` | 任务、清单、子任务、提醒、成员分配 |
| `lark-mail` | 邮件浏览、搜索、发送、回复、草稿 |
| `lark-contact` | 用户搜索与资料获取 |
| `lark-wiki` | 知识空间、节点、文档 |
| `lark-event` | 实时事件订阅、WebSocket、正则路由 |
| `lark-vc` | 会议记录与纪要查询 |
| `lark-whiteboard` | 白板 / 图表 DSL 渲染 |
| `lark-minutes` | 会议纪要元数据、摘要、待办、章节 |
| `lark-openapi-explorer` | 探索底层开放平台 API |
| `lark-skill-maker` | 自定义 Skill 创建框架 |
| `lark-workflow-meeting-summary` | 会议纪要聚合与结构化报告 |
| `lark-workflow-standup-report` | 议程与待办事项汇总 |

### 10.2 `lark-shared` 为什么最关键

所有其他 Skills 都依赖 `lark-shared`，这说明官方把一些“横切能力”抽到了公共层：

- 应用配置
- OAuth 登录
- 多身份切换
- 权限范围管理
- 安全规则执行

这是一种很成熟的设计方式。因为认证、安全、身份并不属于某个具体业务域，但每个业务域都离不开它。

### 10.3 为什么 Skills 天然适合 Agent

Agent 最怕三件事：

- 参数太复杂
- 输出太松散
- 权限边界不清楚

而 Lark CLI 正好在这三点上做了优化：

- **简洁参数**
- **结构化输出**
- **权限与身份显式化**

这也是官方把它定义为“built for humans and AI Agents”的关键原因。

---

## 十一、原理分析：Lark CLI 是如何工作的

### 11.1 从公开信息能确认的工作链路

结合官方 README，可以较明确地还原出一条调用链：

```text
用户 / AI Agent
      ↓
lark-cli 命令解析
      ↓
Shortcut / API Command / Raw API 路由
      ↓
身份与权限校验
      ↓
请求组装与发送
      ↓
Lark / 飞书开放平台 API
      ↓
结构化输出 / 表格输出 / JSON 输出
```

### 11.2 这条链路里最关键的四个环节

#### 第一层：命令解析

CLI 首先要判断您输入的是哪一类命令：

- `calendar +agenda` 这种任务型命令
- `calendar calendars list` 这种 API 映射命令
- `api GET /open-apis/...` 这种原始端点命令

#### 第二层：权限与身份

无论命令多短，最终都绕不开：

- 当前凭证是否有效
- 所需范围是否已授权
- 以用户还是机器人身份执行

#### 第三层：请求构造

Shortcuts 的价值之一，就是把底层请求体、参数结构、默认值处理掉，让调用者关注目标，而不是协议细节。

#### 第四层：输出整形

CLI 的最后一公里不是“收到响应”就结束，而是把响应整理成：

- JSON
- pretty
- table
- ndjson
- csv

这一步非常关键，因为它决定了命令结果能否真正进入后续自动化流程。

---

## 十二、架构分析：从产品架构到工程架构

### 12.1 产品架构视角

从产品能力看，Lark CLI 可以拆成五层：

```text
交互层：命令行输入、帮助、schema、自解释能力
抽象层：Shortcuts / API Commands / Raw API
能力层：Calendar / IM / Docs / Base / Mail / Meetings 等业务域
治理层：认证、权限、身份切换、安全规则
平台层：Lark / 飞书开放平台 OpenAPI
```

### 12.2 工程架构视角

从公开仓库首页能看到 `cmd`、`internal`、`shortcuts`、`scripts` 等目录。这至少说明项目在组织上区分了几类职责：

| 目录 | 可合理推断的职责 |
| ---- | ---------------- |
| `cmd/` | 命令行入口与命令注册 |
| `shortcuts/` | 高频快捷命令的定义与实现 |
| `internal/` | 内部共享实现、通用逻辑、不可对外暴露的模块 |
| `scripts/` | 构建、发布、工程辅助脚本 |

这里要注意一个事实边界：

> 我们能根据公开目录结构判断职责分层方向，但不应凭空断言每个包的内部细节实现。

严格来说，可靠的结论只有两类：

- **官方 README 已明确声明的能力**
- **仓库目录与公开文件能直接观察到的组织结构**

### 12.3 这套架构为什么稳

因为它把变化频率不同的东西分开了：

- 业务高频操作放在 Shortcuts
- 平台同步能力放在 API Commands
- 全量兜底能力放在 Raw API
- 认证、安全、身份作为横切基础设施

这种分层在长期演进里很有优势：

- 新业务可继续加 Shortcut
- 新 API 可通过元数据生成中层命令
- 老用户在底层仍有完整能力

---

## 十三、源码分析：如何阅读这个仓库才最高效

### 13.1 先明确一个原则

如果您想阅读 Lark CLI 源码，最有效的方法不是一头扎进 `internal/`，而是先按“从外到内”的路径看。

### 13.2 推荐阅读顺序

#### 第一步：先读 README

目标：

- 建立产品模型
- 弄清三层命令架构
- 明白 Skills、Auth、Security 的边界

#### 第二步：再看 `cmd/`

目标：

- 理解 CLI 的入口
- 看命令树是如何组织的
- 理解全局参数和子命令分发

#### 第三步：看 `shortcuts/`

目标：

- 学习高层任务命令如何封装
- 看默认值、简化参数、输出整形在哪里发生

#### 第四步：再深入 `internal/`

目标：

- 研究公共逻辑如何复用
- 观察认证、请求发送、格式化输出等底层能力如何沉淀

#### 第五步：最后看 `scripts/` 和工程文件

目标：

- 理解发布、打包、构建流程
- 判断项目工程化成熟度

### 13.3 阅读源码时重点关注什么

| 观察点 | 为什么重要 |
| ------ | ---------- |
| **命令如何注册** | 这决定整个 CLI 的组织方式 |
| **Shortcut 如何映射到底层请求** | 这是产品抽象能力的核心 |
| **身份与权限如何贯穿调用链** | 这是安全与可控性的根基 |
| **输出如何格式化** | 这直接影响自动化可用性 |
| **错误处理策略** | 决定命令是否适合脚本与 Agent 场景 |

### 13.4 二开最有价值的切入点

如果您不是单纯阅读，而是准备扩展或借鉴，最值得研究的是：

- 如何设计一条好的 Shortcut
- 如何让命令既适合人也适合 Agent
- 如何在抽象层和完整覆盖之间取得平衡

这三点，比死记具体函数更有长期价值。

---

## 十四、典型使用场景

### 14.1 场景一：个人效率自动化

适合做：

- 每天早上拉取当天日程
- 生成日报文档
- 从邮件和任务中抽取待办
- 汇总会议纪要

### 14.2 场景二：团队协同自动化

适合做：

- 把任务系统、文档、会议纪要联动起来
- 将群消息或邮件转成结构化追踪项
- 自动生成例会周报、站会报告

### 14.3 场景三：AI Agent 助手

适合做：

- 让 Agent 读取和更新飞书文档
- 让 Agent 查询日程与忙闲
- 让 Agent 汇总会议纪要和待办事项
- 让 Agent 在最小权限下操作指定业务域

### 14.4 场景四：开放平台调试与教学

适合做：

- 快速验证某个 API 是否可用
- 用 `schema` 辅助理解接口
- 用 Raw API 对照官方 OpenAPI 文档调试请求

---

## 十五、开发扩展：Lark CLI 不只是拿来用

### 15.1 自定义 Skill

官方提供了 `lark-skill-maker`：

```bash
lark-cli skill-maker create --name my-custom-skill
```

这说明项目并不希望所有扩展都回到“手写脚本”阶段，而是希望用 Skill 作为一个更高层的扩展单元。

### 15.2 底层 API 探索

如果现有命令不足，可以使用 `lark-openapi-explorer`：

```bash
lark-cli lark-openapi-explorer
```

它适合做两件事：

- 找还没有被高层封装的能力
- 反向推导自己需要的命令调用方式

### 15.3 工作流类 Skill

官方还提供了面向工作流的 Skill：

| Skill | 用途 |
| ----- | ---- |
| `lark-workflow-meeting-summary` | 聚合会议纪要并输出结构化报告 |
| `lark-workflow-standup-report` | 汇总议程与待办事项 |

这类 Skill 说明 Lark CLI 的扩展思路已经不再停留在“单命令封装”，而是开始面向**复合业务流**。

---

## 十六、安全机制与使用边界

### 16.1 官方明确提示的风险

官方 README 明确提醒，AI Agent 调用 Lark CLI 存在以下固有风险：

- 模型幻觉
- 不可预测执行
- 提示注入

如果授权已经交给 Agent，那么风险不只是“答错问题”，而是可能转化成：

- 敏感数据泄露
- 未授权操作
- 对真实业务资源造成影响

### 16.2 默认保护机制

官方明确提到以下保护措施：

| 保护机制 | 作用 |
| -------- | ---- |
| **输入注入保护** | 降低恶意输入操控工具行为的风险 |
| **终端输出清理** | 减少终端输出中的安全隐患 |
| **操作系统原生密钥链存储** | 让凭证存储更安全 |

### 16.3 最佳安全实践

1. **不要主动放松默认安全设置**
2. **优先用最小权限范围**
3. **把机器人用于私有对话，而不是开放群聊**
4. **对有副作用的命令先做 `--dry-run`**
5. **把“能执行”与“应该执行”分开考虑**

---

## 十七、推荐做法与避坑指南

### 17.1 权限策略

| 场景 | 推荐方式 |
| ---- | -------- |
| **只做单一业务域自动化** | `lark-cli auth login --domain <domain>` |
| **快速试用** | `lark-cli auth login --recommend` |
| **精确控制** | `lark-cli auth login --scope "<scope>"` |

### 17.2 命令选择策略

建议遵循下面这条规则：

1. 能用 Shortcut，就先用 Shortcut
2. Shortcut 不够精确，再下沉到 API Commands
3. API Commands 还不够，再使用 Raw API

这样做的好处是：

- 成本更低
- 更不容易出错
- 更符合 CLI 的设计意图

### 17.3 排错策略

| 问题 | 优先检查 |
| ---- | -------- |
| **权限不足** | `auth check` 或重新登录 |
| **命令不清楚** | `lark-cli <service> --help` |
| **参数不会写** | `schema` |
| **请求可能有副作用** | `--dry-run` |
| **需要底层联调** | Raw API |

---

## 十八、常见问题

### Q1：如何查看某个服务下所有可用命令？

```bash
lark-cli <service> --help

# 例如
lark-cli calendar --help
lark-cli im --help
```

### Q2：如何确认自己是否有某个权限？

```bash
lark-cli auth check "calendar:calendar:readonly"
```

退出码语义如下：

- `0`：有权限
- `1`：缺少权限

### Q3：如何拿到原始 JSON 响应？

```bash
lark-cli api GET /open-apis/calendar/v4/calendars --format json
```

### Q4：什么时候应该用 `schema`？

当您出现以下任何一种情况时，就应该先看 `schema`：

- 不知道参数结构
- 不知道请求体字段
- 不知道支持哪种身份
- 不知道需要哪些权限

### Q5：Lark CLI 更适合人用，还是更适合 Agent 用？

答案是：**两者都适合，但擅长点不同。**

- 对人类用户，它更像高效率终端工具
- 对 Agent，它更像结构化、安全可控的操作接口

---

## 十九、自测清单与练习建议

### 19.1 自测清单

如果您能回答下面这些问题，说明已经真正掌握了 Lark CLI 的核心：

- [ ] 我能解释 Shortcuts、API Commands、Raw API 的区别
- [ ] 我知道什么时候用 `config init`，什么时候用 `config init --new`
- [ ] 我会使用 `auth check` 验证权限
- [ ] 我会在危险命令前使用 `--dry-run`
- [ ] 我会在参数不确定时先看 `schema`
- [ ] 我知道如何按最小权限思路设计自动化
- [ ] 我知道如何从仓库入口开始阅读源码

### 19.2 三组练习

#### 练习一：新手

目标：跑通一次日历查询

```bash
lark-cli auth status
lark-cli calendar +agenda
```

#### 练习二：进阶

目标：先看结构，再调具体 API 命令

```bash
lark-cli schema calendar.events.instance_view
lark-cli calendar events instance_view --params '{"calendar_id":"primary","start_time":"1700000000","end_time":"1700086400"}'
```

#### 练习三：专家

目标：对照 Raw API 理解封装边界

```bash
lark-cli api GET /open-apis/calendar/v4/calendars --format json
```

---

## 二十、结语

Lark CLI 最值得学习的地方，不只是“命令多”，而是它把官方开放平台、CLI 工具工程、AI Agent 接口设计三件事结合在了一起。

它提供的不是单一工具，而是一种非常清晰的工程思路：

- **对高频任务做高层抽象**
- **对平台能力保留结构化映射**
- **对未知需求保留底层直通能力**
- **对自动化和 Agent 场景加入权限与安全治理**

如果您只是想快速调用飞书能力，它已经足够实用。
如果您想研究“官方 Agent 友好型 CLI 应该怎么设计”，它同样很值得细读。

---

## 相关链接

- 💻 GitHub：[@larksuite/cli](https://github.com/larksuite/cli)
- 📦 npm：[@larksuite/cli](https://www.npmjs.com/package/@larksuite/cli)
- 📖 中文文档：[README.zh.md](https://github.com/larksuite/cli/blob/main/README.zh.md)
