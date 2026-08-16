---
title: "Paperclip：把一群 AI 代理当公司来运营的开源控制平面"
date: "2026-08-16T03:28:53+08:00"
slug: "paperclip-agent-company-orchestration"
github_repo: "paperclipai/paperclip"
source_key: "gh:paperclipai/paperclip"
description: "Paperclip 是开源的多智能体编排控制平面：把 Claude Code、Codex、OpenClaw 等代理纳入组织架构，用任务、心跳、预算与审批管理一支代理团队。本文拆解其十二个子系统与关键执行机制。"
draft: false
categories: ["技术笔记"]
tags: ["AI Agent", "多智能体", "开源", "编排"]
---

# Paperclip：把一群 AI 代理当公司来运营的开源控制平面

先给判断：Paperclip 值得关注的理由，不是它能让一个 AI 代理更聪明，而是它把「很多代理」当成一个组织问题来解——任务、汇报线、预算、审批、审计，一样不少。README 里那句自述很准：如果 OpenClaw 是一名员工，Paperclip 就是这家公司。

截至本文写作（2026 年 8 月），仓库 `paperclipai/paperclip` 约 78,000 stars、14,000 forks，主语言 TypeScript，MIT 许可，2026 年 3 月创建，最近一次提交在 2026-08-15——一个五个月冲到这个量级、且每天都在合入修复的项目，本身说明了多代理管理这个需求的真实程度。

## 它到底解决什么问题

用过 Claude Code 跑任务的人多半经历过这种状态：开二十个终端标签，每个标签里一个代理，重启之后上下文全丢；代理烧 token 失控时，你是在账单里才知道的。

Paperclip 对这类问题的回答不是「更好的代理」，而是一层控制平面（control plane）：

- **任务是工单（ticket），不是聊天窗口**。代理有岗位描述，对话按任务线程持久化，重启不丢。
- **预算是硬约束**。每个代理有月度预算，触线即停，排队中的工作自动取消。
- **治理是流程**。雇佣、策略变更、产出发布都要过审批门；任何变更可回滚。
- **任何代理都能被雇佣**。OpenClaw、Claude Code、Codex、Cursor、bash 脚本、HTTP bot——README 的原话是「只要它能接收心跳（heartbeat），它就被录用了」。

## 系统地图：十二个子系统，四组职责

Paperclip 服务端不是一个单体 wrapper，README 的架构图把它拆成十二个子系统。按职责归成四组来看更清楚：

| 职责组 | 子系统 | 管什么 |
| --- | --- | --- |
| 谁 | Identity & Access · Org Chart & Agents | 用户、API key、短时效 run JWT；代理的角色、汇报线、权限、预算 |
| 做什么 | Work & Tasks · Routines & Schedules | 工单的公司/项目/目标/父任务链；cron、webhook、API 触发的例程 |
| 怎么跑 | Heartbeat Execution · Workspaces & Runtime · Plugins | 唤醒队列、预算检查、秘密注入；隔离执行工作区（git worktree）；插件系统 |
| 怎么管 | Governance & Approvals · Budget & Costs · Secrets & Storage · Activity & Events · Company Portability | 审批流与审计日志；分级成本追踪；秘密与产物存储；整套组织的导入导出 |

这张表里最值得停一下的是 Heartbeat Execution：它不是简单的定时器，而是一条数据库支撑的唤醒管线——合并（coalescing）重复唤醒、预算预检、解析工作区、注入秘密、加载技能、调用适配器，产出的每次运行都带结构化日志、成本事件、会话状态与审计记录，孤儿运行会被自动回收。

## 关键机制：四个容易低估的设计

**原子任务检出。** 任务领取与预算执行是原子的：一个任务同一时刻只被一个代理持有执行锁，重复劳动与预算双花在机制层面被禁止，而不是靠代理「自觉」。

**目标血统（goal ancestry）。** 每个任务携带从公司使命到父目标的完整链路，代理拿到的不只是一个标题，还有「为什么做」。这是它区别于普通任务管理器的地方——上下文从任务一路流向项目与公司目标。

**运行时技能注入。** 代理在运行中学习 Paperclip 的工作流与项目上下文，不需要重训。换句话说，组织知识沉淀在控制平面里，代理是可替换的。

**公司级隔离。** 每个实体（entity）都以公司为作用域，一次部署可以跑多家「公司」，数据与审计链完全隔离。配合 Company Portability 的导出导入（带秘密擦除与冲突处理），组织的模板化复制是原生能力。

## 一个任务怎么流过系统

拿 README 里的三步走当例子：目标是「做一个达到 100 万美元 MRR 的笔记应用」。

1. 定义目标，雇佣团队——CEO、CTO、工程师、设计师，每个岗位绑定一个代理（任意运行时）。
2. 管理层把目标拆成任务。某工程师代理被心跳唤醒，原子领取一张任务卡，工作区解析到一个隔离的 git worktree，秘密按作用域注入。
3. 代理调用底层运行时（比如 Claude Code）干活，产出 diff、截图、测试结果回填任务；成本事件实时记账；上级代理或人类审阅后合入，全程留审计记录。月度例程（如巡检、报告）则由 Routines 定时建卡、唤醒对应代理，不需要人肉踢一脚。

## 它不是什么

README 的「What Paperclip is not」一栏写得很诚实，抄录要点：不是聊天机器人（代理有岗位，没有聊天窗）；不是代理框架（不管你怎么造代理，只管代理组成的组织怎么运转）；不是工作流搭建器（没有拖拽管线）；不是提示词管理器；也不是代码评审工具。单代理用户大概率不需要它——它的存在前提是「你有二十个代理」。

## 上手路径

自托管，不需要注册 Paperclip 账号。官方安装（带校验和验证）：

```bash
curl -fsSLO https://paperclip.ing/install.sh
curl -fsSLO https://paperclip.ing/install.sh.sha256
if command -v sha256sum >/dev/null 2>&1; then
  sha256sum -c install.sh.sha256
else
  shasum -a 256 -c install.sh.sha256
fi
bash install.sh
```

安装器要求 Node.js 20+，把托管的 CLI 装到 `~/.paperclip/cli`，并启动交互式引导。不想永久安装可以先试：

```bash
npx --registry https://registry.npmjs.org paperclipai onboard --yes
```

首次运行默认回环（loopback）模式；要暴露到局域网或 tailnet，用 `paperclipai onboard --yes --bind lan` 或 `--bind tailnet` 显式选择绑定预设。

## 采用建议

适合的场景：多代理并行推进真实业务（增长、支持、开发），需要预算护栏、审批门与可审计的执行历史；或者你想把「AI 公司」当成可复制的模板做实验。不适合的场景：只有一个代理的个人用户、想要可视化工作流编辑器的团队、想把代理调度逻辑嵌进自己产品里的开发者——最后这类需求它明确不覆盖。

一句收束：多代理协作的瓶颈早就不是模型能力，而是组织学问题——谁向谁汇报、钱怎么管、出事怎么追责。Paperclip 把这三个问题做成了软件，这是它五个月拿下七万星的原因，也是它值得持续跟踪的原因。
