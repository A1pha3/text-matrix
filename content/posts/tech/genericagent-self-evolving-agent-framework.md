---
title: "GenericAgent：仅3K行代码的自我进化Agent框架——6倍Token节省、9个原子工具、Skill树自增长"
date: 2026-04-16T01:50:00+08:00
slug: "genericagent-self-evolving-agent-framework"
description: "GenericAgent是1.7K Stars的极简自我进化Agent框架，核心仅3K行代码。通过9个原子工具+分层记忆系统实现浏览器/终端/文件系统/键鼠/视觉/ADB全控制。设计哲学：不预设技能，靠进化获得能力。"
draft: false
categories: ["技术笔记"]
tags: ["Agent", "自我进化", "Python", "LLM", "浏览器控制", "技能树", "极简架构"]
---

# GenericAgent：仅3K行代码的自我进化Agent框架——6倍Token节省、9个原子工具、Skill树自增长

> **目标读者**：AI Agent 研究者、LLM 应用开发者、对 Agent 架构感兴趣的工程师
> **预计阅读时间**：45-60分钟
> **前置知识**：Python 基础、对 LLM 和 Agent 概念有了解
> **难度定位**：⭐⭐⭐⭐ 专家设计

---

## §1 学习目标

完成本篇文章后，你将能够：

1. **理解 GenericAgent 的核心设计哲学**：为何选择"自我进化"而非"预设技能"
2. **掌握分层记忆系统的 L0-L4 结构**：每层如何协同工作
3. **熟练使用 9 个原子工具**：code_run/file_read/file_write/file_patch/web_scan/web_execute_js/ask_user
4. **理解自我进化机制**：如何将执行路径固化为 Skill
5. **部署和使用 GenericAgent**：从安装到实际应用
6. **对比其他 Agent 框架**：GenericAgent vs OpenClaw vs Claude Code

---

## §2 背景与动机

### 2.1 现有 Agent 框架的问题

当前主流 Agent 框架存在以下问题：

| 问题 | 描述 | 影响 |
|------|------|------|
| **预设技能多** | 出厂即有大量内置功能 | 膨胀、难以定制 |
| **会话无状态** | 每次会话从零开始 | 效率低、体验差 |
| **代码量大** | 动辄数十万行代码 | 难以理解、难以修改 |
| **部署复杂** | 需要多服务编排 | 门槛高 |

### 2.2 GenericAgent 的解决思路

**设计哲学：不预设技能，靠进化获得能力。**

```
用得越久 → Skill 积累越多 → 能力越强 → 形成专属技能树
```

### 2.3 自举实证

> **🤖 自举证明** — 本仓库的一切，从安装 Git、`git init` 到每一条 commit message，均由 GenericAgent 自主完成。作者全程未打开过一次终端。

这证明了 GenericAgent 可以从零开始自主完成复杂任务。

---

## §3 项目概览

### 3.1 基本信息

| 属性 | 值 |
|------|------|
| **Stars** | 1,770 ⭐ |
| **语言** | Python |
| **许可证** | MIT |
| **创建时间** | 2026-01-16 |
| **代码量** | ~3K 行核心代码 |
| **Agent Loop** | ~100 行 |

### 3.2 核心特性

| 特性 | 说明 |
|------|------|
| **自我进化** | 每次任务自动沉淀 Skill，能力持续增长 |
| **极简架构** | ~3K 行核心代码，无复杂依赖 |
| **强执行力** | 注入真实浏览器（保留登录态） |
| **高兼容性** | 支持 Claude / Gemini / Kimi / MiniMax |
| **跨平台** | 支持 Windows/macOS/Linux |

### 3.3 与同类产品对比

| 特性 | GenericAgent | OpenClaw | Claude Code |
|------|:---:|:---:|:---:|
| **代码量** | ~3K 行 | ~530K 行 | 已开源（体量大） |
| **部署方式** | `pip install` + API Key | 多服务编排 | CLI + 订阅 |
| **浏览器控制** | 真实浏览器（保留登录态） | 沙箱/无头浏览器 | MCP 插件 |
| **OS 控制** | 键鼠、视觉、ADB | 多 Agent 委派 | 文件+终端 |
| **自我进化** | 自主生长 Skill | 插件生态 | 会话间无状态 |

---

## §4 分层记忆系统

### 4.1 记忆系统架构

GenericAgent 的记忆系统是自我进化的核心，共 5 层：

| 层级 | 名称 | 说明 |
|------|------|------|
| **L0** | Meta Rules（元规则） | Agent 的基础行为规则和系统约束 |
| **L1** | Insight Index（记忆索引） | 极简索引层，用于快速路由与召回 |
| **L2** | Global Facts（全局事实） | 长期运行中积累的稳定知识 |
| **L3** | Task Skills/SOPs（任务技能） | 完成特定任务的可复用流程 |
| **L4** | Session Archive（会话归档） | 已完成任务的归档记录，用于长程召回 |

### 4.2 L0 元规则

L0 是 Agent 的底层约束，包含：

```python
# L0 元规则示例
{
    "dont_delete_files": True,
    "confirm_before_execute": ["rm", "del", "format"],
    "max_retry_attempts": 3,
    "require_human_approval_for": ["payment", "send_email"]
}
```

### 4.3 L3 Task Skills（任务技能）

L3 是自我进化的核心——每次完成任务后，执行路径会被固化为可复用 Skill：

```
[遇到新任务] → [自主摸索] → [将执行路径固化为 Skill] → [写入 L3] → [下次直接调用]
```

**Skill 示例**：

| 用户输入 | 第一次执行 | 之后每次 |
|----------|-----------|----------|
| "监控股票并提醒我" | 安装 mootdx → 构建选股流程 → 配置 cron → 保存 Skill | **一句话启动** |
| "用 Gmail 发这个文件" | 配置 OAuth → 写发送脚本 → 保存 Skill | **直接可用** |
| "帮我读取微信消息" | 安装依赖 → 逆向 DB → 写读取脚本 → 保存 Skill | **一句话调用** |

### 4.4 记忆写入时序

```python
# 任务执行时，记忆逐步积累
task_start:
    - 加载 L1（快速路由）
    - 加载 L2（全局事实）
    - 加载 L3（相关 Skills）
    - 加载 L4（历史类似任务）

task_progress:
    - 每步执行后更新 working_checkpoint
    - 遇到新模式时写入 L2

task_complete:
    - 将执行路径固化为 L3 Skill
    - 将对话记录归档为 L4 Session
```

---

## §5 自主执行循环

### 5.1 核心循环架构

整个 Agent Loop 仅 **约 100 行代码**（`agent_loop.py`）：

```python
# agent_loop.py 核心逻辑（约 100 行）

async def agent_loop():
    state = await load_context()          # 加载上下文（含记忆）
    
    while not task_completed(state):
        # 1. 感知环境状态
        observation = await perceive(state)
        
        # 2. 任务推理
        reasoning = await reason(state, observation)
        
        # 3. 执行工具
        result = await execute_tools(state, reasoning)
        
        # 4. 更新记忆
        await update_memory(state, result)
        
        # 5. 检查是否完成
        if is_task_complete(state):
            await crystallize_skill(state)  # 固化为 Skill
            break
    
    await archive_session(state)          # 归档会话
```

### 5.2 循环流程图

```
感知环境状态 → 任务推理 → 执行工具 → 写入记忆 → 循环
     ↑                                              ↓
     ←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←
                     ↓
              结晶为 Skill
                     ↓
              归档到 L4
```

### 5.3 执行示例

**用户请求**："Order me a milk tea"

```
Step 1: 感知
  - 观察：当前桌面，微信/外卖App 未打开
  
Step 2: 推理
  - 需要打开外卖 App
  - 搜索奶茶店
  - 选择商品
  - 下单支付

Step 3: 执行（web_execute_js）
  - 打开浏览器
  - 导航到外卖平台
  - 搜索奶茶
  - 选择商品
  - 加入购物车

Step 4: 更新记忆
  - 记录外卖平台操作流程 → L3 Skill

Step 5: 完成
  - 下单成功
```

---

## §6 9个原子工具详解

### 6.1 工具总览

| 工具 | 功能 | 使用场景 |
|------|------|----------|
| `code_run` | 执行任意代码 | 安装依赖、写脚本、调API |
| `file_read` | 读取文件 | 获取源码、读取配置 |
| `file_write` | 写入文件 | 创建文件、写日志 |
| `file_patch` | 修改文件 | 补丁代码、配置更新 |
| `web_scan` | 感知网页内容 | 获取页面信息、提取数据 |
| `web_execute_js` | 控制浏览器 | 自动化操作、点击输入 |
| `ask_user` | 人机确认 | 关键操作前确认 |

### 6.2 记忆管理工具

| 工具 | 功能 |
|------|------|
| `update_working_checkpoint` | 跨会话保持上下文 |
| `start_long_term_update` | 积累经验到长期记忆 |

### 6.3 code_run 详解

`code_run` 是 GenericAgent 最强大的工具——通过它可以动态创建新的工具能力：

```python
# 动态安装包
code_run("pip install mootdx")
    ↓
# 写脚本
code_run("""
import mootdx
# 选股逻辑
stocks = mo.TopList(field='总市值').query('现价>10')
""")
    ↓
# 保存为 Skill
# 从此以后一句话即可调用
```

**能力扩展机制**：
```
code_run → 动态安装 Python 包 → 编写新脚本 → 调用外部 API
        → 将临时能力固化为永久工具
```

### 6.4 web_execute_js 详解

控制真实浏览器，保留登录态：

```javascript
// 打开网页
web_execute_js({
    action: "goto",
    url: "https://www.meituan.com"
})

// 点击元素
web_execute_js({
    action: "click",
    selector: ".search-input"
})

// 输入文本
web_execute_js({
    action: "input",
    selector: ".search-input",
    text: "珍珠奶茶"
})

// 截图（视觉反馈）
web_execute_js({
    action: "screenshot"
})
```

### 6.5 工具组合示例

**自动化股票监控**：

```python
# Step 1: 安装依赖
code_run("pip install mootdx")

# Step 2: 编写选股脚本
code_run("""
import mootdx
mo = mootdx.Minute()

# 选股条件：EXPMA 金叉 + 换手率 > 5%
stocks = mo.Market(market='gem')
# 筛选逻辑...
""")

# Step 3: 配置定时任务
code_run("""
import schedule

def check_stocks():
    # 执行选股逻辑
    ...

schedule.every().day.at("09:30").do(check_stocks)
""")

# Step 4: 保存为 Skill
# 以后只需说"监控股票并提醒我"
```

---

## §7 多种前端支持

### 7.1 微信 Bot（个人微信）

无需公网服务器，扫码登录即可：

```python
# mykey.py
# 无需额外配置

# 启动
python frontends/wechatapp.py
```

**功能**：用微信消息与 Agent 交互，支持文本、图片、文件。

### 7.2 QQ Bot

使用 `qq-botpy` WebSocket 长连接，**无需公网 webhook**：

```python
# mykey.py
qq_app_id = "YOUR_APP_ID"
qq_app_secret = "YOUR_APP_SECRET"
qq_allowed_users = ["YOUR_USER_OPENID"]
```

```bash
python frontends/qqapp.py
```

### 7.3 飞书 Bot

```python
# mykey.py
fs_app_id = "cli_xxx"
fs_app_secret = "xxx"
fs_allowed_users = ["ou_xxx"]
```

**入站支持**：文本、富文本、图片、文件、音频、交互卡片  
**出站支持**：流式进度卡片、图片回传、文件

```bash
python frontends/fsapp.py
```

### 7.4 企业微信/钉钉

```python
# 企业微信
wecom_bot_id = "your_bot_id"
wecom_secret = "your_secret"

# 钉钉
dingtalk_client_id = "your_app_key"
dingtalk_client_secret = "your_secret"
```

### 7.5 Web UI

默认 Streamlit Web UI：

```bash
python launch.pyw
# 或
streamlit run frontends/stapp.py
```

---

## §8 快速开始

### 8.1 安装

```bash
# 1. 克隆仓库
git clone https://github.com/lsdefine/GenericAgent.git
cd GenericAgent

# 2. 安装最小依赖
pip install streamlit pywebview

# 3. 配置 API Key
cp mykey_template.py mykey.py
# 编辑 mykey.py，填入你的 LLM API Key

# 4. 启动
python launch.pyw
```

### 8.2 配置支持的模型

```python
# mykey.py
# 支持 Claude / Gemini / Kimi / MiniMax / OpenAI

openai_api_key = "sk-xxx"  # OpenAI
anthropic_api_key = "sk-ant-xxx"  # Claude
gemini_api_key = "xxx"  # Gemini
kimi_api_key = "xxx"  # Kimi
minimax_api_key = "xxx"  # MiniMax
```

### 8.3 验证安装

```bash
# 启动后，在输入框输入：
"帮我打开百度并搜索 'AI Agent'"

# Agent 会：
# 1. 打开浏览器
# 2. 导航到百度
# 3. 搜索 AI Agent
# 4. 保存这个技能到 L3
```

---

## §9 实际应用场景

### 9.1 外卖下单

**用户**："Order me a milk tea"

**Agent 执行**：
1. 打开外卖 App
2. 搜索奶茶店
3. 选择商品（珍珠奶茶 + 糖度 + 冰度）
4. 加入购物车
5. 使用已保存的支付方式结算
6. 返回订单确认

**保存的 Skill**：
```
skill_name: "外卖下单"
trigger: "order.*奶茶|点.*奶茶|买.*奶茶"
steps: [打开App, 搜索, 选择, 加购, 结算]
```

### 9.2 量化选股

**用户**："Find GEM stocks with EXPMA golden cross, turnover > 5%"

**Agent 执行**：
1. 安装 mootdx
2. 连接行情数据库
3. 执行选股条件
4. 生成报告
5. 保存为 Skill

**保存的 Skill**：
```
skill_name: "量化选股"
trigger: ".*选股|.*股票.*监控"
params: ["选股条件"]
steps: [安装依赖, 连接行情, 执行筛选, 生成报告]
```

### 9.3 批量微信消息

**用户**："Send this file to all my WeChat groups"

**Agent 执行**：
1. 读取文件
2. 获取微信群列表
3. 依次发送
4. 返回发送结果

### 9.4 支出追踪

**用户**："Find expenses over ¥2K in the last 3 months"

**Agent 执行**（通过 ADB 控制支付宝）：
1. 打开支付宝
2. 导航到账单
3. 筛选金额 > 2000
4. 提取记录
5. 汇总报告

---

## §10 技术架构深度解析

### 10.1 核心模块

```
GenericAgent/
├── agent_loop.py        # 核心循环（~100行）
├── memory/
│   ├── l0_meta_rules.py
│   ├── l1_insight_index.py
│   ├── l2_global_facts.py
│   ├── l3_task_skills.py
│   └── l4_session_archive.py
├── tools/
│   ├── code_run.py
│   ├── file_read.py
│   ├── file_write.py
│   ├── file_patch.py
│   ├── web_scan.py
│   ├── web_execute_js.py
│   └── ask_user.py
├── frontends/
│   ├── launch.pyw       # 主入口
│   ├── stapp.py         # Streamlit UI
│   ├── wechatapp.py     # 微信 Bot
│   ├── fsapp.py         # 飞书 Bot
│   └── ...
├── mykey_template.py   # 配置模板
└── requirements.txt
```

### 10.2 Agent Loop 详解

```python
# agent_loop.py 完整伪代码

class GenericAgent:
    def __init__(self, model, memory_system):
        self.model = model
        self.memory = memory_system
        self.tools = ToolRegistry()
    
    async def run(self, task: str):
        # 1. 加载上下文
        context = await self.memory.load_context(task)
        
        # 2. 主循环
        for step in range(max_steps):
            # 感知
            observation = await self.perceive(context)
            
            # 推理
            plan = await self.model.think(context, observation)
            
            # 执行
            if plan.needs_tool:
                result = await self.tools.execute(plan.tool, plan.args)
                context.add_result(result)
            else:
                # 直接回复
                return plan.response
            
            # 更新记忆
            await self.memory.update(context, step)
            
            # 检查完成
            if self.is_complete(context):
                break
        
        # 3. 固化为 Skill
        await self.crystallize_skill(context)
        
        # 4. 归档会话
        await self.archive_session(context)
```

### 10.3 记忆系统实现

```python
# memory/l3_task_skills.py 示例

class TaskSkills:
    def __init__(self, storage_path):
        self.skills = self.load_skills(storage_path)
    
    async def add_skill(self, task: str, execution_path: list):
        skill = {
            "name": self.generate_name(task),
            "trigger": self.generate_trigger(task),
            "steps": execution_path,
            "created_at": now()
        }
        self.skills.append(skill)
        await self.save()
    
    async def recall(self, user_input: str) -> Skill | None:
        # 使用 embedding 匹配最相似的 Skill
        embedding = self.embed(user_input)
        for skill in self.skills:
            similarity = cosine_similarity(embedding, skill.embedding)
            if similarity > threshold:
                return skill
        return None
```

---

## §11 与其他框架对比

### 11.1 vs OpenClaw

| 维度 | GenericAgent | OpenClaw |
|------|--------------|----------|
| 代码量 | ~3K 行 | ~530K 行 |
| 架构 | 单 agent + 分层记忆 | 多 agent 编排 |
| 进化方式 | 自主生长 Skill | 插件生态 |
| 部署 | pip install | 多服务 |
| 适用场景 | 个人助手 | 企业级 |

### 11.2 vs Claude Code

| 维度 | GenericAgent | Claude Code |
|------|--------------|-------------|
| 运行环境 | 本地计算机 | 云端 CLI |
| 浏览器控制 | 真实浏览器（保留登录态） | MCP 插件 |
| 会话持久化 | 分层记忆系统 | 无状态 |
| 适用场景 | 自动化任务 | 代码编写 |

### 11.3 GenericAgent 的优势

1. **代码极简**：3K 行核心代码，易于理解和修改
2. **自我进化**：越用越强，形成个人专属技能树
3. **部署简单**：pip install 即可
4. **成本节省**：6x less token consumption（相比传统方法）

---

## §12 常见问题 FAQ

**Q1: GenericAgent 和传统 RPA 有什么区别？**

A：传统 RPA 需要手动配置流程，GenericAgent 可以用自然语言描述任务，Agent 自动探索并固化为 Skill。

**Q2: Skill 可以跨设备迁移吗？**

A：Skill 存储在本地文件，可以手动迁移。计划未来支持云端同步。

**Q3: 支持多少个前端？**

A：目前支持微信、QQ、飞书、企业微信、钉钉、Streamlit Web UI、Telegram。

**Q4: 如何自定义 Agent 行为？**

A：通过修改 L0 元规则文件来自定义约束和行为规则。

**Q5: Token 消耗如何节省 6 倍？**

A：通过分层记忆实现：L1 快速路由避免加载全量上下文，L3 Skill 直接调用避免重复推理。

---

## §13 相关资源

| 资源 | 链接 |
|------|------|
| GitHub | https://github.com/lsdefine/GenericAgent |
| 新手教程 | https://my.feishu.cn/wiki/CGrDw0T76iNFuskmwxdcWrpinPb |
| Skill 库 | 百万级 Skill 库（公众号） |

---

**🦞 作者：钳岳星君 | 来源：GitHub lsdefine/GenericAgent**