---
title: "google/agents-cli：把 ADK 智能体的上线流程拆成命令和技能"
date: "2026-06-30T21:10:22+08:00"
slug: "google-agents-cli-gemini-enterprise-guide"
github_repo: "google/agents-cli"
source_key: "gh:google/agents-cli"
lastmod: "2026-09-19T00:00:00+08:00"
description: "google/agents-cli 是 Google 官方的 CLI + Skill 套件，让 Antigravity CLI、Claude Code、Codex 等编程助手按同一套流程创建、评估、部署和观测 ADK 智能体。本文按 1.6.1 版逐项核对命令面、Skill 设计、评估指标与部署差异，并说明它在 1.0 GA 时砍掉 RAG 路径的原因。"
draft: false
categories: ["技术笔记"]
tags: ["Google Cloud", "Gemini", "AI Agent", "CLI", "Claude Code", "Codex", "ADK"]
---

# google/agents-cli：把 ADK 智能体的上线流程拆成命令和技能

让编程助手写一个 ADK（Agent Development Kit，智能体开发套件）智能体，它写得挺像样。让它把这个智能体部署到 Cloud Run、配好 CI/CD（持续集成/持续部署）里的评估门禁、事后再补上调用链追踪，它就开始编了——编一套 `gcloud` 命令，或者干脆生成一个 Makefile。难的不是代码，是代码之外那圈工程动作：该按什么顺序做、哪一步不能改、报 403 该翻哪个文件。

[google/agents-cli](https://github.com/google/agents-cli) 就是冲着这圈来的。它由两层组成：一层是 CLI（命令行工具），把创建、评估、部署、注册收敛成 `agents-cli` 一个入口；另一层是 Skill（技能，写给编程助手读的结构化指令集），把那圈工程判断写成文本装进编程助手。装完之后你在 Claude Code 里说“给我搭一个部署到 Cloud Run 的智能体”，它调的是 `agents-cli`，走的是 Skill 里定的流程。

下面的核对以 1.6.1（2026-09-16 发布）为准。命令表、Skill 行数和参数默认值都从仓库里的源码与文档取，README 与代码不一致时以代码为准并写明了分歧在哪。RAG（检索增强生成）那条路径的去留在最后一节单独说，它是理解这个项目取舍的一把钥匙。

## 事实基线

| 项 | 内容 |
| ---- | ---- |
| 仓库 | [google/agents-cli](https://github.com/google/agents-cli) |
| 当前版本 | 1.6.1（2026-09-16） |
| Star / Fork（收藏 / 派生） | 5,957 / 669 |
| 语言 / 协议 | Python / Apache-2.0 |
| 仓库创建 | 2026-04-08，源码公开随 0.5.0（2026-06-15） |
| 正式可用 | 1.0.0（2026-06-30）GA，此前为 Preview |
| 文档 | https://google.github.io/agents-cli/ |
| PyPI 包名 | `google-agents-cli` |

Star 与 Fork 数是 2026-09-19 从仓库元数据取的读数。`RELEASE_NOTES.md` 里从 0.1.0（2026-04-21）到 1.6.1 一共 24 条记录，平均不到一周一条，项目还在快速动。快速动不等于没稳定下来：1.0.0 的官方口径已经是 GA、生产可用，旧资料里“Preview”的状态标签过期了。它的前身是 Agent Starter Pack（ASP），`agents-cli` 在文档里自称 ASP 的继任者，两条关键差别写得很直白：ASP 面向人敲交互式命令，`agents-cli` 面向编程助手；ASP 用 `make dev` / `make eval` / `make deploy` 这类 Makefile 目标，`agents-cli` 换成了带参数、帮助文本和结构化输出的统一 CLI。项目配置也从 `pyproject.toml` 里的 `[tool.agent-starter-pack]` 挪到了独立的 `agents-cli-manifest.yaml`。

## 两层结构各自负责什么

README 的定位是一句话：“Turn your favorite coding assistant into an expert at building and deploying agents on Google Cloud.”，列出的适配对象是 Antigravity CLI、Claude Code、Codex 以及“其他任意编程助手”。官方 FAQ 又排掉了三个常见误解：它不是替代编程助手的第三个助手，而是**给**编程助手用的工具；它不替代 ADK，ADK 是框架，它管框架之外的事；它不要求你必须配编程助手，`create`、`run`、`eval`、`deploy` 每条命令都能单独在终端里跑。

两层的分工就一句：CLI 负责执行，Skill 负责在执行之前把判断做掉。

## Skill 层：真正起作用的是禁令，不是命令清单

7 个 Skill 各自的名字与体量（`SKILL.md` 行数，在 1.6.1 的 `skills/` 目录下量的，不含各自的 `references/`）：

| Skill | 行数 | 负责 |
| ---- | ---- | ---- |
| `google-agents-cli-workflow` | 336 | 全生命周期入口，常驻激活 |
| `google-agents-cli-adk-code` | 72 + 大量 references | ADK Python API（应用程序接口）：智能体类型、工具定义、编排、callback、state（状态） |
| `google-agents-cli-scaffold` | 269 | `create` / `enhance` / `upgrade`、模板与部署目标 |
| `google-agents-cli-eval` | 378 | 指标、数据集、LLM-as-judge（大语言模型判分）、compare / analyze / optimize |
| `google-agents-cli-deploy` | 428 | Agent Runtime / Cloud Run / GKE、服务账号、回滚、排障 |
| `google-agents-cli-publish` | 213 | Gemini Enterprise 注册、Agent Registry 舰队管理 |
| `google-agents-cli-observability` | 162 | Cloud Trace、prompt-response（提示词与响应）日志、第三方集成 |

`adk-code` 只有 72 行不是笔误：它的正文是一张速查表，真正的代码样板放在 `references/` 里按需展开。相比之下 `deploy` 有 428 行，因为部署这层的坑最具体。

七个 Skill 的 description 末尾都写着“Do NOT use for”，并且点名该转去哪个 Skill：`scaffold` 说自己不管部署，`deploy` 说自己不管代码模式。这不是走过场。Skill 靠语义匹配被编程助手拉进来，没有排除项的话，一句“部署我的智能体”会同时召来 adk-code 和 deploy，两边给出的建议互相打架。

版本也被锁死。workflow 的 metadata 里写着 `version: 1.6.1`，正文顶部要求 `google-agents-cli ~= 1.6.1`，落后时直接给重装命令；CLI 启动时有一道 `check_skills_version`，`agents-cli info` 能看当前项目配置与版本。Skill 与 CLI 错配会显式提醒，而不是放编程助手拿着旧指令继续跑。

真正改变输出质量的是 workflow 里的“代码保留”原则（Principle 1）：只改用户明确点到的那几行，其余代码、配置值、注释、格式逐字保持。它给的反例正是最常见的越界：用户只让改 instruction，编程助手顺手把 `model` 从脚手架的默认值换成了自己记忆里的型号。Principle 1 之前还有一张表，左列是编程助手会说服自己的话，右列是为什么站不住。“我要用一个更新更好的模型”那行的驳回理由是，脚手架选的模型是刻意挑的，擅自换掉既破坏代码保留，又经常直接坏掉（位置不对、版本已废弃、或者 404）。同一格里紧跟的一句是说给助手自己听的，也值得抄进任何一套 Skill：“你的训练数据大概率过期，靠 Skill 和模型列表命令，不要靠你对模型名的记忆”。

阶段调度上也是同一套逻辑。workflow 是唯一标着“always active”的 Skill，它给了一张阶段到 Skill 的映射表，并要求在每个阶段开始前重读对应 Skill，理由写得很直白：上下文压缩可能已经把前面读过的内容丢掉了。它还要求在设计阶段、还没 scaffold 之前就先读 adk-code 的 recipe 索引，因为沙箱、记忆、审批门这些能力“已经在 recipe 里实现过并且经过实战，你别重新发明一遍，而且发明得更差”。

命令速查表式的 Skill 列出有哪些命令，这套 Skill 针对助手的确定失败模式下禁令。

## CLI 命令面：以代码注册为准

`src/google/agents/cli/main.py` 里的注册表比 README 的折叠命令表更全，个别措辞也不同。按生命周期列一遍：

```bash
# 安装与认证
agents-cli setup                     # 装 CLI + Skill 到检测到的编程助手
agents-cli login                     # 与 Google Cloud 或 AI Studio 认证
agents-cli login --status            # 查看认证状态
agents-cli info                      # 项目配置与 CLI 版本（支持 --json）
agents-cli update                    # 强制把 Skill 重装到所有检测到的助手

# Scaffold（创建）
agents-cli create <name>             # 创建新项目
agents-cli scaffold enhance          # 给已有项目加部署 / CI/CD
agents-cli scaffold upgrade          # 升级项目到新版 agents-cli

# 本地开发
agents-cli run "prompt"              # 单条提示词非交互运行
agents-cli playground                # 启动本地调试界面
agents-cli install                   # 安装项目依赖
agents-cli lint                      # 代码质量检查（Ruff）

# 评估
agents-cli eval run                  # 跑推理 + 打分，一步到位
agents-cli eval generate             # 只跑推理产出 traces（调用链记录）
agents-cli eval grade                # 只对已有 traces 打分
agents-cli eval dataset synthesize   # 合成多轮评估场景
agents-cli eval compare              # 对比两份评估结果
agents-cli eval analyze              # 聚类失败模式
agents-cli eval metric list          # 列出可用指标
agents-cli eval optimize             # 用评估数据自动调提示词

# 部署与注册
agents-cli deploy                    # 部署到 Google Cloud
agents-cli publish gemini-enterprise # 注册到 Gemini Enterprise
agents-cli infra single-project      # 单项目基础设施
agents-cli infra cicd                # CI/CD 流水线 + staging/prod 基础设施
agents-cli infra show                # 查看 single-project 产出的 Terraform 配置

# 扩展（experimental）
agents-cli extension add / list / remove / update
```

四个容易读错的点：

- `create` 和 `scaffold create` 是同一个命令的两次注册，`main.py` 的注释里专门说了这件事，别当成两个命令。文档里那张 ASP 命令对照表也把它标成 “create（alias for `scaffold create`）”。
- `eval run` 是 `generate` + `grade` 的合并步骤，三者都在。
- `data-ingestion` 和 `infra datastore` 仍然注册着，执行却只打印一句“Removed: RAG is now a clone-and-study recipe”。命令名还在列表里，照着旧命令表拼流程会在这里卡住（最后一节说原因）。
- `build`（构建二进制）藏在实验开关 `build_command` 后面，默认不可见。

安装的前置条件官方写的是 Python 3.11+、uv、Node.js，括号里注明 Node 只为装 Skill；部署另需 Google Cloud SDK（软件开发包）和 Terraform，标成可选。除 `uvx google-agents-cli setup` 外，文档还给了 pipx、venv + pip 两条路，以及 `npx skills add google/agents-cli` 这条只装 Skill 的捷径。

`setup` 会检测已装的编程助手（它自己的帮助文本列举 Claude Code、Antigravity CLI、Cursor、Windsurf 等），也可以用 `--agent claude-code --agent cursor` 指名。Antigravity 是个例外：它不读 `npx skills` 的规范目录 `~/.agents/skills`，于是 `setup` 额外把 Skill 镜像链到 `~/.gemini/config/skills` 和 `~/.gemini/antigravity-cli/skills`，代码注释里直说是临时兼容层。自 1.5.0 起 `setup` 不再需要网络和 git，Skill 已经打进包里。

平台边界要留意：macOS、Linux 和 Windows 下的 WSL 2，原生 Windows 不在官方支持范围内，尽管 1.1.0 做过一轮大范围的 Windows 兼容性修复。

## scaffold：一条命令出多少文件

内置模板只有两个：`adk`（Python，默认）和 `adk_go`（Go，1.6.1 起无需实验开关，仍标 Preview）。其他框架以模板仓库形式提供，例如：

```bash
agents-cli create my-agent --agent google/agents-cli/extensions/langchain/template@v1.6.1
```

这个 LangChain 模板就在 agents-cli 自己的 `extensions/langchain/template/` 下，不需要先装扩展就能用；它自带一个 `agents-cli-langchain` Skill。

`create` 的开关空间比 README 那行示例大不少（以下取自 `skills/google-agents-cli-scaffold/references/flags.md`）：

| 开关 | 默认 | 作用 |
| ---- | ---- | ---- |
| `--deployment-target` / `-d` | `agent_runtime` | `agent_runtime` / `cloud_run` / `gke` / `none` |
| `--prototype` / `-p` | off | 跳过 CI/CD 和 Terraform，官方建议第一遍就用它 |
| `--session-type` | — | `in_memory` / `cloud_sql` / `agent_platform_sessions`，配 `cloud_run`、`gke` 用；Agent Runtime 自己管会话 |
| `--cicd-runner` | — | `github_actions` / `google_cloud_build` / `skip` |
| `--region` | `us-east1` | GCP 区域 |
| `--agent-guidance-filename` | `GEMINI.md` | 可换成 `CLAUDE.md` 或 `AGENTS.md` |
| `--bq-analytics` | off | 启用 BigQuery Agent Analytics 插件 |
| `--adk` | off | 快捷模式：adk + agent_runtime + prototype，跳过所有提问，强制 Python |

文档给的口径是：完整配置产出约 72 个文件，分布在智能体代码、评估样板、Terraform、GitHub Actions 工作流和部署清单里。`--prototype` 砍掉的正是其中的 Terraform 与 CI 工作流。

scaffold Skill 里有一条硬规则：**永远不要手写 A2A（Agent2Agent 协议）代码**。A2A 已经织进 `adk`、`adk_go` 和框架模板的产物里，各语言的 A2A 接口面（import 路径、`AgentCard` 结构之类）非平凡且跨版本会变。Skill 在这里做的是减法：不是“你可以这样”，而是“别自己写，你已经会的那套是过期的”。

版本层面，1.6.1 起脚手架默认模型是 `gemini-3.8-flash`；Python 模板自 0.4.0 起把依赖锁在 `google-adk[gcp]>=2.0.0,<3.0.0`，也就是跟着 ADK 2.0 GA 走。

## eval：默认数据集能直接跑，自定义度量要选执行位置

scaffold 出来的项目自带 `tests/eval/datasets/basic-dataset.json` 和 `tests/eval/eval_config.yaml`，所以第一次评估不需要准备任何东西：

```bash
agents-cli eval run
agents-cli eval run --dataset tests/eval/datasets/custom-dataset.json --metrics general_quality
```

常用内置指标里，几个有代表性的（全集用 `agents-cli eval metric list` 看）：

| 指标 ID | 评什么 |
| ---- | ---- |
| `general_quality` | 整体响应质量，官方推荐的非智能体评估起点 |
| `tool_use_quality` | 单轮的工具选择、参数准确性与步骤顺序 |
| `multi_turn_trajectory_quality` | 跨轮次的顺序逻辑、效率与错误恢复 |
| `multi_turn_task_success` | 整段对话里用户目标是否达成 |
| `hallucination`（幻觉） | 把回答拆成原子断言，逐条对照工具返回的上下文验证 |
| `final_response_reference_free` | 无参考答案的最终响应质量，要求评估用例上带 `rubric_groups` |
| `safety` | 对照安全策略（PII、仇恨、危险内容等）合规 |

自定义度量有两类，真正的区别是那段时间代码跑在谁的机器上：

- Code Execution Metric：写一个 `def evaluate(instance)`。默认在 CLI 进程内本地执行，不需要 GCP 项目，代价是你的代码以 CLI 的权限跑。想要隔离，得显式加 `"execution": "remote"` 走 Vertex AI 的沙箱 `CodeExecutionMetric`，此时需要配好项目和区域。
- LLM-as-a-Judge Metric：给 `prompt_template`，可选 `judge_model`（如 `gemini-3.8-flash`）与 `judge_model_sampling_count`，取值 1–32。多次采样意味着评委模型的调用次数按倍数算，这是直接的成本项。

`eval optimize` 用评估数据自动调提示词。官方文档给的时间量级是“几分钟到几小时，取决于数据集规模和指标复杂度”，并建议在你自己改过提示词、调过指标、手工修过失败用例之后再上。1.5.0 起 `eval` 支持 `--qps` 控制请求速率，不然会按默认值被限流。

## deploy 与 publish：三个目标做的是三件不同的事

| 目标 | 实际动作 |
| ---- | ---- |
| `agent_runtime` | 全托管；始终从 Dockerfile 构建，不接受预构建 `--image`；部署耗时 5–10 分钟量级 |
| `cloud_run` | 从源码构建容器，底层是 `gcloud beta run deploy` |
| `gke` | Terraform + Docker build + `kubectl apply` |

三个目标之外，`deploy` 从 1.5.0 起有 `--update-only`（更新已有的 Agent Runtime engine，而不是建出一个重复实例）和 `--labels`。需要 Cloud Run 的进阶参数而 CLI 没暴露时，官方给的路子是用 `--dry-run`（`-n`）打印完整 `gcloud` 命令，你复制了再加参数；CLI 不打算覆盖所有 flag。1.6.1 另外修掉一个报表错误：用了 Agent Identity 的智能体，部署完打印出来的 principal 是错的，容易把人往错的方向查。

`publish gemini-enterprise` 的默认注册模式按部署目标分：Agent Runtime 走 ADK 原生注册（0.6.1 起，A2A 在 Agent Runtime 上会告警并建议改用 ADK），Cloud Run 和 GKE 仍默认 A2A。另一侧还有 Agent Registry，Google Cloud 上跨项目的智能体与 MCP（Model Context Protocol，模型上下文协议）服务器目录，能做舰队管理。Skill 文档给它标的是 Preview。

## 观测：默认常开的只有一层

Cloud Trace 在所有模板、所有环境默认开启，不需要额外基础设施。另外两项要 Terraform 先开资源：Prompt-Response Logging（把提示词与响应落到 GCS 的 JSONL、BigQuery 和 Cloud Logging）和 BigQuery Agent Analytics。对应的命令是 `agents-cli infra single-project --project PROJECT_ID`，它开出服务账号、GCS 桶和 BigQuery 数据集。

留痕范围上有个容易忽略的取舍。0.6.0 起 Cloud Trace 的 span 不再捕获 LLM 的提示词与响应。官方那份讲生命周期的文档把 Terraform 部署的默认组合描述为“全文进 GCS/BigQuery，trace 里不放内容”。查延迟和执行流程看 trace，做审计与合规看前者，两件事别互相替代。另外 Skill 文档注明 GCS 完成度上传和 BigQuery 插件只支持 Python，Go 项目仅有 BigQuery 遥测栈。第三方那一层（AgentOps、Phoenix、MLflow 等）走 OpenTelemetry，按提供方逐个配。

## 一次走查，带验收点

```bash
# 0) 前置：Python 3.11+、uv、Node.js
uvx google-agents-cli setup
agents-cli info                      # 验收：能打印项目配置与 CLI 版本

# 1) 先写 .agents-cli-spec.md：工具清单 / 约束 / 成功标准
#    workflow Skill 的 Phase 0 是一轮提问式 brainstorm，用来把 spec 逼出来

# 2) 出原型（跳过 CI/CD 与 Terraform）
agents-cli create my-agent -p -d cloud_run
#    验收：项目里有 app/、tests/eval/、agents-cli-manifest.yaml 和智能体指导文件

# 3) 本地跑通
export GEMINI_API_KEY="your-key"     # 或者已经 gcloud 登录，ADC（应用默认凭证）会被自动拾取
agents-cli run "一句话输入"
agents-cli playground                # 想在界面上点着试的时候

# 4) 第一次评估
agents-cli eval run
#    验收：每条评估用例都对你配置的指标出分，默认集就是 basic-dataset.json

# 5) 补上 CI/CD 与基础设施
agents-cli scaffold enhance -d cloud_run --cicd-runner github_actions

# 6) 部署
agents-cli deploy --dry-run          # 先看它要执行什么
agents-cli deploy

# 7) 注册（可选）
agents-cli publish gemini-enterprise
```

生命周期文档把这圈收敛成四个动词——`scaffold`、`eval`、`deploy`、observe——循环往复；展开成八个阶段则是 Spec、Scaffold、Build、Orchestrate、Evaluate、Deploy、Publish、Observe，每个阶段挂一个 Skill。同一份文档在第 2 阶段给了一个很实在的判断：智能体本体无非模型、指令、工具列表和一个 `App` 包装，“有意义的代码差不多 30 行，真正有意思的活都在工具里面”。

## 已知会踩的坑

deploy Skill 的排障表是可以直接抄的一段，挑几条：

| 现象 | 处理 |
| ---- | ---- |
| Terraform state 锁住 | 在 `deployment/terraform/` 里 `terraform force-unlock -force LOCK_ID` |
| 部署时报 403 | 查 `deployment/terraform/iam.tf`，`cicd_runner_sa` 需要在目标项目里有部署与 SA impersonation 角色 |
| Cloud SQL 连不上 / 403 | 手工部署时给运行时服务账号 `roles/cloudsql.client` |
| secret 读不到 | 确认 `secretAccessor` 授给了 `app_sa`，不是默认的 compute 服务账号 |
| 测试 Cloud Run 返回 403 | 默认是 `--no-allow-unauthenticated`，请求要带 `Authorization: Bearer $(gcloud auth print-identity-token)` |
| Cloud Build 授权一直挂着 | 换 `github_actions` 作为 runner |
| GitHub Actions 认证失败 | 在 CI/CD 的 terraform 目录重跑 `terraform apply`，核对 WIF（Workload Identity Federation，工作负载身份联邦）的 pool 与 provider |

发布记录里还有四条更实际的回归：

- 1.6.1 把 `google-adk` 卡在 2.9.0 以下，因为 2.9.0 上 Cloud Run 智能体的提示词与响应不再进 BigQuery Agent Analytics。
- `eval generate` 会静默丢掉逐用例的 session state，1.6.1 修掉（issue #52）。
- `run` 和 `eval` 会关掉自己只是借用的后台服务，1.6.1 修掉（issue #71）。
- `agents-cli create` 在前置条件失败时成功退出、或者甩一段 traceback 了事，1.5.0 改成明确报错（issue #68）。

这几条没有一个会让命令直接失败，它们只是给出不对的结果。Skill 与 CLI 版本要锁死在一起，理由就在这里。

## RAG 被删掉这件事

1.0.0（2026-06-30）的发布记录里有一条不太起眼的收缩：

> RAG is now a clone-and-study recipe: start from the `rag-vector-search` / `rag-agent-search` samples in `google/adk-samples`. The `agentic_rag` template, the `--datastore` flag, and the `infra datastore` / `data-ingestion` commands were removed and now print a redirect.

命令保留是为了让旧脚本至少能收到一句提示，而不是静默失败。scaffold Skill 的模板表下面把这条界线写成了通则：检索、沙箱执行、跨会话记忆、OAuth（开放授权）、guardrails 这些都属于 recipe（配方），不属于模板。

这个判断站得住。脚手架能参数化的是工程骨架：部署到哪、CI 用什么、会话存哪里，都是有限选项。检索不是，它要决定切块策略、向量库和 rerank，任何一组 flag 假装覆盖了这些决定，用户就会在错误的默认值上开工。把它退回“抄一个样例再改”，比给一个 `--datastore` 诚实。

顺带说明第二处收缩的边界：FAQ 说 agents-cli 不绑框架，deploy Skill 也写着适用于它能部署的任何框架（ADK、LangChain……）；但 `adk-code` 那个 Skill 是纯 ADK Python API，别的框架得自带模板仓库和自己的 Skill（LangChain 那份就带了一个）。中立只到工程骨架这一层，代码知识的默认路径仍是 ADK。

## 什么时候不必接它

- 不部署到 Google Cloud：`deploy` / `publish` 全部指向 GCP 服务。本地 `create` / `run` / `eval` 用一个 AI Studio 的 key 就能跑完，这是 FAQ 明确回答过的。
- 不写 ADK：能拿到的是工程骨架和评估流程，代码层的 Skill 帮不上。
- 现在就要 RAG：这条路已经不在 CLI 里了，得从 `google/adk-samples` 起步。
- 只想要一个省样板的脚手架：即使用了 `--prototype`，产出仍是 app / tests / deployment 三块结构，得有人读懂。
- 已有成熟部署管线：`scaffold enhance` 支持 smart-merge（智能合并）、`--dry-run`、`--prefer-new`、`--force`，把已有项目的 CI 交给它管通常不划算。

收益最直接的两种情形：团队里有多个 ADK 项目要统一评估门禁和 CI；或者本人不打算碰 GCP 控制台，只想让编程助手把部署干完，同时不希望它在背后擅自换掉模型和配置。

## 自测：逐条验一遍文中的断言

文中的断言都能在本地复核，不需要跑完整部署。前四条只要装好 CLI 就能跑，最后两条要在源码仓库里执行：

```bash
agents-cli --help                         # 对照本文命令表；playground 在这里，README 折叠表没有
agents-cli eval metric list               # 指标全集
agents-cli infra datastore                # 只打印一句 Removed 重定向
agents-cli info --json                    # 项目配置与 CLI 版本
agents-cli create verify-me -d cloud_run  # 之后 find . -type f | wc -l，看离 72 有多远
grep -n "experiment=\"build_command\"" src/google/agents/cli/main.py   # build 在实验开关后
grep -c "^## \[" RELEASE_NOTES.md         # 24 条发布记录
```

## 来源

本文事实核对截至 2026-09-19，版本与参数以 agents-cli 1.6.1 为准，后续版本会变。

- 仓库、README 与 `RELEASE_NOTES.md`：https://github.com/google/agents-cli
- 官方文档：Getting Started、The Lifecycle、Evaluation Guide、Deployment、Skills Reference、From Agent Starter Pack — https://google.github.io/agents-cli/
- 命令注册与开关源码：`src/google/agents/cli/main.py`、`skills/google-agents-cli-scaffold/references/flags.md`
- Skill 正文：`skills/google-agents-cli-{workflow,adk-code,scaffold,eval,deploy,publish,observability}/SKILL.md`
- 仓库元数据与 Star / Fork 读数：GitHub API 的 repositories 端点

升级版本后要重新对照的四处，按出错概率排：命令表（`main.py` 的注册）、`scaffold` 参数默认值（`flags.md`）、7 个 Skill 的行数与 `metadata.version`、以及废弃命令清单。文中所有具体数字都标了自己的出处和时间，改哪条都能直接回到源文件。
