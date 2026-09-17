---
title: "DeskcommCRM：把 AI 销售代理装进自托管的开源 WhatsApp CRM"
date: 2026-09-18T03:50:00+08:00
slug: "deskcommcrm-self-hosted-ai-sales-crm"
github_repo: "melgarafael/DeskcommCRM"
source_key: "gh:melgarafael/DeskcommCRM"
description: "DeskcommCRM 是 Next.js 16 + Supabase 栈的自托管 AI 销售 CRM，AI 代理在 WhatsApp 上接待、资格判定与跟进，一条命令部署到 VPS。本文拆解其安装器设计、自动化规则引擎与适用边界。"
draft: false
categories: ["技术笔记"]
tags: ["CRM", "AI Agent", "WhatsApp", "自托管", "Next.js"]
---

## 核心判断

巴西市场的大量生意在 WhatsApp 上成交，而商业 CRM 按席位收月费、把聊天数据锁在别人服务器里的模式，与这个场景天然冲突。DeskcommCRM 的定位因此非常具体：**一个 MIT 许可、自托管的开源销售系统，内置能接电话的 AI 代理，主通道是 WhatsApp，对标 Kommo、Octadesk 和 Intercom 的开源替代**。

它的工程亮点不在模型层，而在交付层：一条命令的 VPS 安装器、幂等的数据库 schema、自动回滚的一键更新。这些是自托管软件最难做对的部分，这个仓库把它们做出了产品级的完成度。截至本文写作约 3.0k stars、754 forks，v1.32.0 刚发布，主仓库几乎每天都有版本迭代。

## 技术栈与架构

| 层 | 选型 |
|---|---|
| 前端/应用 | Next.js 16 + TypeScript（strict） |
| 数据库/认证/存储 | Supabase（Postgres + Auth + Storage），Session pooler 连接 |
| WhatsApp 通道 | WAHA（开源 WhatsApp HTTP API），扫码接入自有号码；也支持 Meta 官方渠道 |
| AI | OpenRouter / Anthropic / OpenAI 任选一家，装自己的 key |
| 部署 | Docker + 自动 HTTPS，单命令安装器 |
| 代理协议 | MCP-ready，AI 代理可作为 MCP 工具被外部调用 |

技术栈是主流的组合，没有 exotic 依赖；真正的设计含量集中在部署与运维链路，下一节展开。

## 安装器：这个仓库最值得读的部分

大多数自托管项目的 README 停在 "docker compose up"，DeskcommCRM 的 `hostgator-setup-kit/install.sh` 做到了传统商业软件的水准：

1. **只问用户才知道的事**（域名、API key、管理员密码），技术性密钥全部自动生成。
2. **逐项前置校验**：key 填错当场拒绝，而不是跑到第三步才报错。
3. **Supabase 可以由安装器代建**：导出 `SUPABASE_ACCESS_TOKEN` 后，它创建项目、等待数据库就绪、取回四项凭据、实测连接推断 pooler host。
4. **幂等**：重复执行不重复建 cron、不重复建用户，中断后可续跑。
5. **环境自适应**：检测到 VPS 已有反代占用 80/443 时自动改为经由反代发布；Hostinger 式 `--network host` 场景则主动询问而非猜测——README 的原话是"发布在错误的反代后面，会安装出一个'成功'但打不开的站点"。

更新链路同样有讲究：界面上的一键更新只发起请求，实际执行者是安装时部署在 VPS 上的更新代理（每 5 分钟轮询一次）；更新前自动备份数据库，新版本健康检查失败则自动回滚到上一镜像并记录到 `.env`。数据库升级靠重放幂等的 `baseline.sql`，它同时承担"自愈"角色，修复旧版本可能弄乱的数据。

这套设计对想学"自托管软件交付工程"的人是很好的参考实现——尤其适合拿它对照自己项目里 `update.sh` 的粗糙程度。

## AI 代理与自动化

AI 侧的能力围绕销售漏斗组织：代理在 WhatsApp 上接待、资格判定（qualify）、跟进，自动化规则采用 QUANDO/SE/ENTÃO（葡萄牙语的 WHEN/IF/THEN）三元形式，由安装器一并部署的 cron 驱动——没有这个 cron，规则只会停在队列里。代理的提示词可以在界面上调整，仓库还提供了按行业定制客户配置的助手指南。

项目对 AI 辅助开发本身也很上心：仓库内置可被 Claude Code、Codex、Cursor、OpenCode、Antigravity 自动加载的助手指南（安装、建行业模板、分析指标、调提示词），支持用自然语言唤起对应流程。

## 适用边界

- **主场景是 WhatsApp 销售**：不在 WhatsApp 上做生意的团队，它的大部分差异化用不上。
- **巴西基因明显**：README 以葡语为主（有英/西译本），集成对象（Nuvemshop、LGPD 合规）面向巴西市场；中国用户可直接复用其架构，但本地化（企业微信/飞书等通道）需要自行改造。
- **需要一台 VPS + Supabase 账号 + AI API key**：推荐 4 GB 内存起步，总体持有成本不高但不是零。
- **HostGator 合作链接**：README 带有商业推广性质的合作链接，选型时应注意区分工程内容与推广内容。

## 结论

DeskcommCRM 是"垂直场景 + 自托管 + AI 代理"三个趋势交叉点上完成度很高的样本：工程交付链路（单命令安装、幂等升级、自动回滚）达到了许多商业产品都没有的水准。适合两类人：在 WhatsApp 上做销售、想摆脱 SaaS 月费的团队，直接部署；以及在做自托管产品的工程师，把它的 `hostgator-setup-kit/` 当部署工程教材来读。

项目地址：[melgarafael/DeskcommCRM](https://github.com/melgarafael/DeskcommCRM)
