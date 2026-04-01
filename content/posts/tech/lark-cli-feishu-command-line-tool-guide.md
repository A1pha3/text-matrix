---
title: "Lark CLI：飞书官方命令行工具完全指南"
date: 2026-04-01T20:47:00+08:00
slug: lark-cli-feishu-command-line-tool-guide
categories: ["技术笔记"]
tags: ["Lark", "飞书", "CLI", "命令行", "AI Agent", "Open Platform"]
description: "飞书官方 CLI 工具完全指南，涵盖 11 大业务领域、200+ 命令、19 个 AI Agent Skills，从安装配置到高级用法的全方位讲解。"
---
# Lark CLI：飞书官方命令行工具完全指南

## 一、项目概述

### 1.1 什么是 Lark CLI

**Lark CLI**（larksuite/cli）是飞书/Lark官方提供的命令行工具，由 larksuite 团队维护，同时支持人类用户和 AI Agent 操作飞书平台的核心业务功能。

### 1.2 关键数据

| 指标 | 数值 |
|------|------|
| **GitHub Stars** | 5,809 |
| **GitHub Forks** | 296 |
| **协议** | MIT |
| **主语言** | Go 98.2% |
| **最新版本** | v1.0.1（2026-03-31） |
| **贡献者** | 20 |

### 1.3 核心定位

| 定位 | 说明 |
|------|------|
| **Agent 原生设计** | 19 个开箱即用的 Skills，兼容主流 AI 工具 |
| **广泛覆盖** | 11 大业务领域，200+ 命令，19 个 AI Agent Skills |
| **AI 友好** | 简洁参数、智能默认值、结构化输出 |
| **3 分钟上手** | 一键创建应用、交互式登录 |
| **安全可控** | 输入注入保护、操作系统原生密钥存储 |

---

## 二、支持业务领域

### 2.1 完整功能矩阵

| 业务领域 | 核心功能 |
|----------|----------|
| **📅 日历 Calendar** | 查看议程、创建活动、邀请参与者、查询忙闲状态、时间建议 |
| **💬 消息 Messenger** | 发送/回复消息、群聊管理、消息搜索、媒体下载 |
| **📄 云文档 Docs** | 创建、读取、更新、搜索文档 |
| **📁 云盘 Drive** | 上传/下载文件、搜索文档和知识库、管理评论 |
| **📊 多维表格 Base** | 创建管理表格、字段、记录、视图、仪表盘、工作流、表单 |
| **📈 电子表格 Sheets** | 创建、读取、写入、追加、查找、导出电子表格数据 |
| **✅ 任务 Tasks** | 创建、查询、更新、完成任务，管理任务清单、子任务 |
| **📚 知识库 Wiki** | 创建和管理知识空间、节点、文档 |
| **👤 联系人 Contact** | 按姓名/邮箱/电话搜索用户、获取用户资料 |
| **📧 邮件 Mail** | 浏览、搜索、阅读邮件，发送、回复、转发 |
| **🎥 视频会议 Meetings** | 搜索会议记录、查询会议纪要和录制内容 |

---

## 三、AI Agent Skills 体系

### 3.1 Skills 完整列表

| Skill 名称 | 功能说明 |
|------------|----------|
| **lark-shared** | 应用配置、身份登录、身份切换、权限管理、安全规则（所有 Skills 自动加载） |
| **lark-calendar** | 日历事件、议程视图、忙闲查询、时间建议 |
| **lark-im** | 发送/回复消息、群聊管理、消息搜索、上传下载媒体、表情反应 |
| **lark-doc** | 创建、读取、更新、搜索文档（基于 Markdown） |
| **lark-drive** | 上传、下载文件、管理权限和评论 |
| **lark-sheets** | 创建、读取、写入、追加、查找、导出电子表格 |
| **lark-base** | 多维表格的表格、字段、记录、视图、仪表盘、数据聚合与分析 |
| **lark-task** | 任务、任务清单、子任务、提醒、成员分配 |
| **lark-mail** | 浏览、搜索、阅读邮件，发送、回复、转发、草稿管理 |
| **lark-contact** | 按姓名/邮箱/电话搜索用户、获取用户资料 |
| **lark-wiki** | 知识空间、节点、文档 |
| **lark-event** | 实时事件订阅（WebSocket）、正则路由、Agent 友好格式 |
| **lark-vc** | 搜索会议记录、查询会议纪要（摘要、待办事项） |
| **lark-whiteboard** | 白板/图表 DSL 渲染 |
| **lark-minutes** | 会议纪要元数据和 AI 生成内容（摘要、待办事项、章节） |
| **lark-openapi-explorer** | 从官方文档探索底层 API |
| **lark-skill-maker** | 自定义 Skill 创建框架 |
| **lark-workflow-meeting-summary** | 工作流：会议纪要聚合与结构化报告 |
| **lark-workflow-standup-report** | 工作流：议程和待办事项汇总 |

### 3.2 Skills 核心架构

lark-shared 是所有 Skills 的基础模块，提供：
- 应用配置管理
- OAuth 身份认证
- 多身份切换
- 权限范围管理
- 安全规则执行

---

## 四、三层命令架构

### 4.1 架构设计

Lark CLI 提供三层命令粒度，从快捷操作到完全自定义 API 调用：

| 层级 | 前缀 | 说明 |
|------|------|------|
| **Shortcuts（快捷命令）** | `+` | 为人类和 AI 双友好设计，带智能默认值、表格式输出、干运行预览 |
| **API Commands（API 命令）** | 无前缀 | 平台 API 1:1 映射，经过质量门控验证 |
| **Raw API（原始 API）** | `api` | 直接调用飞书开放平台任意端点，覆盖 2500+ API |

### 4.2 快捷命令示例

```bash
# 查看日历议程
lark-cli calendar +agenda

# 发送消息
lark-cli im +messages-send --chat-id "oc_xxx" --text "Hello"

# 创建文档
lark-cli docs +create --title "Weekly Report" --markdown "# Progress\n- Completed feature X"
```

### 4.3 API 命令示例

```bash
# 列出日历
lark-cli calendar calendars list

# 查看事件详情
lark-cli calendar events instance_view --params '{"calendar_id":"primary","start_time":"1700000000","end_time":"1700086400"}'
```

### 4.4 原始 API 调用

```bash
# 获取日历列表
lark-cli api GET /open-apis/calendar/v4/calendars

# 发送消息
lark-cli api POST /open-apis/im/v1/messages \
  --params '{"receive_id_type":"chat_id"}' \
  --body '{"receive_id":"oc_xxx","msg_type":"text","content":"{\"text\":\"Hello\"}"}'
```

---

## 五、快速开始

### 5.1 系统要求

| 要求 | 规格 |
|------|------|
| **Node.js** | npm / npx |
| **Go** | v1.23+ |
| **Python 3** | 仅从源码编译时需要 |

### 5.2 安装步骤

**方式一：从 npm 安装（推荐）：**

```bash
# 安装 CLI
npm install -g @larksuite/cli

# 安装 CLI SKILL（必需）
npx skills add larksuite/cli -y -g
```

**方式二：从源码安装：**

```bash
# 需要 Go v1.23+ 和 Python 3
git clone https://github.com/larksuite/cli.git
cd cli
make install

# 安装 CLI SKILL（必需）
npx skills add larksuite/cli -y -g
```

### 5.3 配置和授权

```bash
# 1. 配置应用凭证（一次性交互式引导设置）
lark-cli config init --new

# 2. 登录（--recommend 自动选择常用权限范围）
lark-cli auth login --recommend

# 3. 验证登录状态
lark-cli auth status
```

### 5.4 AI Agent 快速开始

AI Agent 安装步骤与人类用户相同，但配置过程需后台运行：

```bash
# 1. 安装（如上）

# 2. 后台配置应用凭证
lark-cli config init --new

# 3. 后台登录
lark-cli auth login --recommend

# 4. 验证
lark-cli auth status
```

---

## 六、权限认证

### 6.1 认证命令

| 命令 | 说明 |
|------|------|
| `auth login` | OAuth 登录，支持交互式选择或 CLI 参数指定权限范围 |
| `auth logout` | 登出并删除存储的凭证 |
| `auth status` | 显示当前登录状态和已授权范围 |
| `auth check` | 验证特定权限范围（退出码 0=有权限，1=无权限） |
| `auth scopes` | 列出应用所有可用权限范围 |
| `auth list` | 列出所有已认证用户 |

### 6.2 认证参数示例

```bash
# 交互式登录（显示 TUI 引导）
lark-cli auth login

# 按域名过滤
lark-cli auth login --domain calendar,task

# 推荐自动审批权限
lark-cli auth login --recommend

# 精确指定权限范围
lark-cli auth login --scope "calendar:calendar:readonly"

# Agent 模式：立即返回验证 URL，非阻塞
lark-cli auth login --domain calendar --no-wait

# 后续恢复轮询
lark-cli auth login --device-code <DEVICE_CODE>

# 身份切换：以用户或机器人身份执行命令
lark-cli calendar +agenda --as user
lark-cli im +messages-send --as bot --chat-id "oc_xxx" --text "Hello"
```

---

## 七、高级用法

### 7.1 输出格式

| 格式参数 | 说明 |
|----------|------|
| `--format json` | 完整 JSON 响应（默认） |
| `--format pretty` | 人类友好的格式化输出 |
| `--format table` | 可读的表格形式 |
| `--format ndjson` | 换行分隔的 JSON（用于管道） |
| `--format csv` | 逗号分隔值 |

### 7.2 分页处理

| 参数 | 说明 |
|------|------|
| `--page-all` | 自动翻页获取所有页面 |
| `--page-limit 5` | 最多 5 页 |
| `--page-delay 500` | 页面请求间隔 500ms |

### 7.3 干运行预览

对于可能有副作用的命令，先用 `--dry-run` 预览请求：

```bash
lark-cli im +messages-send --chat-id oc_xxx --text "hello" --dry-run
```

### 7.4 Schema 内省

使用 `schema` 命令查看任何 API 方法的参数、请求体结构、响应结构：

```bash
lark-cli schema
lark-cli schema calendar.events.instance_view
lark-cli schema im.messages.delete
```

---

## 八、安全机制

### 8.1 安全风险提示

Lark CLI 可被 AI Agent 调用以自动化飞书开放平台操作，存在以下固有风险：

| 风险类型 | 说明 |
|----------|------|
| **模型幻觉** | AI 可能产生错误决策 |
| **不可预测执行** | 执行结果可能不符合预期 |
| **提示注入** | 恶意输入可能操控工具行为 |

### 8.2 默认安全保护

Lark CLI 在多层默认启用安全保护：

| 保护层 | 说明 |
|--------|------|
| **输入注入保护** | 过滤恶意输入 |
| **输出清理** | 终端输出内容 sanitization |
| **操作系统密钥链** | 凭证安全存储 |

### 8.3 安全使用建议

1. **不主动修改默认安全设置** — 限制一旦放松，风险显著增加
2. **使用飞书机器人作为私有对话助手** — 不添加到群聊，避免权限滥用
3. **充分了解所有使用风险** — 使用此工具即视为自愿承担相关责任

---

## 九、开发扩展

### 9.1 自定义 Skill 创建

使用 `lark-skill-maker` 框架创建自定义 Skill：

```bash
# 创建新的 Skill
lark-cli skill-maker create --name my-custom-skill
```

### 9.2 API 探索

使用 `lark-openapi-explorer` 从官方文档探索底层 API：

```bash
# 启动 API 探索器
lark-cli lark-openapi-explorer
```

### 9.3 工作流自动化

预置工作流 Skills：

| Skill | 用途 |
|-------|------|
| **lark-workflow-meeting-summary** | 会议纪要聚合与结构化报告 |
| **lark-workflow-standup-report** | 议程和待办事项汇总 |

---

## 十、最佳实践

### 10.1 权限范围选择

| 场景 | 推荐命令 |
|------|----------|
| **最小权限** | `lark-cli auth login --domain <具体域名>` |
| **常用场景** | `lark-cli auth login --recommend` |
| **精确控制** | `lark-cli auth login --scope "<精确范围>"` |

### 10.2 常见错误排查

| 问题 | 解决方案 |
|------|----------|
| 权限不足 | 运行 `lark-cli auth check <scope>` 检查 |
| 登录过期 | 重新运行 `lark-cli auth login --recommend` |
| 命令找不到 | 运行 `lark-cli <service> --help` 查看可用命令 |

---

## 十一、常见问题

**Q1: 如何查看所有可用命令？**

```bash
lark-cli <service> --help
# 例如
lark-cli calendar --help
lark-cli im --help
```

**Q2: 如何验证特定权限？**

```bash
lark-cli auth check "calendar:calendar:readonly"
# 退出码 0 = 有权限，1 = 无权限
```

**Q3: 支持多身份切换吗？**

是的，支持以不同用户或机器人身份执行命令：

```bash
lark-cli calendar +agenda --as user
lark-cli im +messages-send --as bot --chat-id "oc_xxx" --text "Hello"
```

**Q4: 如何获取原始 API 响应？**

```bash
lark-cli api GET /open-apis/calendar/v4/calendars --format json
```

---

## 十二、项目信息

| 信息 | 内容 |
|------|------|
| 许可证 | MIT |
| 主语言 | Go 98.2% |
| 最新版本 | v1.0.1（2026-03-31） |
| 贡献者 | 20 |

---

## 相关链接

💻 **GitHub**：[larksuite/cli](https://github.com/larksuite/cli)

📦 **npm**：[@larksuite/cli](https://www.npmjs.com/package/@larksuite/cli)

📖 **中文文档**：[README.zh.md](https://github.com/larksuite/cli/blob/main/README.zh.md)
