---
title: "Claude API基础专题（六）：Claude Code与Computer Use"
date: "2026-03-25T11:00:00+08:00"
slug: "claude-api-computer-use-automation"
aliases:
  - /posts/tech/claude-api-computer-use-automation/
description: "剖析Computer Use这个beta功能：它让Claude通过截图、鼠标和键盘操作桌面环境，但真正的执行由调用方在沙箱内完成。介绍observation-decision-execution循环、工具定义与动作清单、agent loop代码示例，以及多沙箱环境与提示注入防御。"
draft: false
categories: ["技术笔记"]
tags: ["Claude", "Computer Use", "自动化"]
---

# Claude API 基础专题（六）：Claude Code 与 Computer Use

> 预计阅读时间：40 分钟 | 难度：⭐⭐⭐⭐

---

> **目标读者**：希望让 Claude 操控计算机完成任务的开发者
> **前置知识**：前三篇的 API 基础、工具调用、MCP 知识

---

Computer Use（计算机使用）是 Anthropic 的 beta 功能：它在 Messages API 里把「截图、鼠标、键盘」打包成一个工具，让 Claude 能对着桌面界面工作。它看起来像 Claude 在亲手操作电脑，实际分工恰恰相反——**Claude 只负责看屏幕、决定下一步，真正的截图、移动光标、敲键盘，必须由你的应用在沙箱里替它执行**。这个边界是理解整个功能的关键。

下面从四个角度展开：它把工具调用的边界推到了哪里、观察-决策-执行循环怎么运转、用 API 怎么落地一个 agent loop，以及安全上要额外扛住哪些风险。

## 6.1 从工具调用到计算机控制

工具调用解决的是「模型知道该调什么，但不知道现实世界长什么样」。它把外部能力封装成一个个函数，模型选择函数、填参数、读返回值。这一切的前提是：**能力边界是预先画好的**。查天气、查数据库、跑代码，都能写成函数；但「这个页面长什么样、提交按钮在哪个坐标」这种信息，工具调用拿不到。

| 任务类型 | 传统工具调用 | Computer Use |
|----------|------------|--------------|
| 查天气、查数据库 | 能，封装成函数即可 | 能 |
| 填一个没见过结构的表单 | 难，得先知道字段位置 | 能，看截图定位 |
| 跨应用操作（复制到贴、拖文件） | 很难，每对应用都要专门写 | 能，操作桌面本身 |
| 自动化 UI 测试遗留系统 | 难，没有 API 可调 | 能，驱动真实界面 |

Computer Use 的思路是：**不预先定义能力，而是给模型一套通用的界面操作原语**——截屏、移动鼠标、点击、输入。模型面对任何一个界面，都能通过对截图的观察现学现用。成本是精度和可靠性会打折扣，这是后文要讨论的边界。

## 6.2 Computer Use 原理解析

### 观察-决策-执行循环

Computer Use 的核心是一个循环，官方称之为 **agent loop（代理循环）**：

```text
┌────────────────────────────────────────────────────────────┐
│                        agent loop                          │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  ① 应用把消息（含截图）发给 Claude                          │
│        │                                                   │
│        ▼                                                   │
│  ② Claude 决定下一步，返回 tool_use（如 left_click）       │
│        │     stop_reason = "tool_use"                      │
│        ▼                                                   │
│  ③ 应用在沙箱里执行该动作（截图/点击/输入）                 │
│        │                                                   │
│        ▼                                                   │
│  ④ 应用把结果作为 tool_result 附回对话                      │
│        │                                                   │
│        └──────── 回到 ①，直到 Claude 不再请求工具 ─────────┘
│                                                            │
└────────────────────────────────────────────────────────────┘
```

关键点：②和④之间是**你的应用插进去执行**的。Claude 只是输出「要做哪个动作、参数是什么」，比如「在坐标 (512, 384) 左键点击」。真正把光标移过去、点下去，是调用方代码调用系统接口完成的。Claude 不直接连到任何显示器或窗口。

这个循环没有用户参与，Claude 一轮接一轮请求工具、应用一轮接一轮返回结果，直到 Claude 判定任务完成、`stop_reason` 不再是 `tool_use`。为避免无限循环烧钱，应用通常会设一个最大迭代次数。

### 计算环境

Computer Use 需要一个**沙箱化的计算环境**，官方参考实现跑在 Docker 容器里，包含：

- **虚拟显示**：用 Xvfb 起一个虚拟 X11 显示服务，渲染 Claude 截图看到的桌面
- **桌面环境**：轻量窗口管理（Mutter）加面板（Tint2），提供一致的图形界面
- **预装应用**：Firefox、LibreOffice、文本编辑器、文件管理器等
- **工具实现**：把「移动鼠标」「截图」这类抽象请求翻译成对虚拟环境的实际操作
- **agent loop**：在 Claude 和环境之间传消息的程序

Claude 不直接连这个环境。你的应用接收 Claude 的 tool_use 请求 → 翻译成对环境的操作 → 捕获结果（截图、命令输出） → 返回给 Claude。

### 工具定义

Computer Use 工具是**无 schema 的**——它不像普通工具那样要你提供 `input_schema`，schema 内置在模型里，不能改。定义它时只需指定以下几个参数：

| 参数 | 必填 | 说明 |
|------|------|------|
| `type` | 是 | 工具版本：`computer_20251124` 或 `computer_20250124` |
| `name` | 是 | 固定为 `"computer"` |
| `display_width_px` | 是 | 显示宽度（像素） |
| `display_height_px` | 是 | 显示高度（像素） |
| `display_number` | 否 | X11 环境下的显示器编号 |
| `enable_zoom` | 否 | 仅 `computer_20251124`，开启 zoom 动作，默认 `false` |

调用时还需要在请求头带 beta 头：新模型用 `computer-use-2025-11-24`，旧模型（Sonnet 4.5、Opus 4.1 等）用 `computer-use-2025-01-24`。支持的模型主要是 Opus 4.5/4.6/4.7/4.8/5 和 Sonnet 4.6/5。

### 可用动作

工具支持的动作分三档：

**基础动作（所有版本）**：`screenshot`（截取当前显示）、`left_click`（点击坐标 `[x, y]`）、`type`（输入文本）、`key`（按键盘按键或组合键，如 `ctrl+s`）、`mouse_move`（移动光标）。

**增强动作（`computer_20250124` 起）**：`scroll`（任意方向滚动、可控制量）、`left_click_drag`（拖拽）、`right_click` / `middle_click`、`double_click` / `triple_click`、`left_mouse_down` / `left_mouse_up`（细粒度点击控制）、`hold_key`（按住按键指定秒数）、`wait`（暂停）。

**`computer_20251124` 新增**：`zoom`（以全分辨率查看屏幕某区域），需要 `enable_zoom: true`，参数 `region` 用 `[x1, y1, x2, y2]` 指定要查看区域的左上角和右下角。

## 6.3 用 API 实现 Computer Use

### 定义工具并发出请求

用 Anthropic Python SDK，先定义工具，再发消息：

```python
import anthropic

client = anthropic.Anthropic()

response = client.beta.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    tools=[
        {
            "type": "computer_20250124",
            "name": "computer",
            "display_width_px": 1024,
            "display_height_px": 768,
            "display_number": 1,
        }
    ],
    messages=[{
        "role": "user",
        "content": "把一张猫的图片保存到桌面上。",
    }],
)
```

注意用的是 `client.beta.messages`，因为 Computer Use 是 beta 功能。响应里如果 `stop_reason == "tool_use"`，说明 Claude 想要执行某个动作，动作在返回的 `tool_use` 块里。

### 一个最小的 agent loop

执行循环的一段示意（省略了 `execute_action` 的具体实现，它负责对接你的沙箱）：

```python
from anthropic.types import ToolResultBlockParam

def agent_loop(messages, system_prompt, tools, max_iterations=10):
    for _ in range(max_iterations):
        response = client.beta.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=1024,
            system=system_prompt,
            tools=tools,
            messages=messages,
        )

        # 任务完成：Claude 不再请求工具
        if response.stop_reason != "tool_use":
            return [
                block.text
                for block in response.content
                if block.type == "text"
            ]

        for block in response.content:
            if block.type == "tool_use":
                action = block.input  # 例如 {"action": "left_click", "coordinate": [512, 384]}

                # 你的应用在沙箱里执行动作，拿到结果（通常是新截图）
                result = execute_action(action)

                # 把 Claude 的决定和你的执行结果都附回对话
                messages.append({
                    "role": "assistant",
                    "content": [block],
                })
                messages.append({
                    "role": "user",
                    "content": [ToolResultBlockParam(
                        type="tool_result",
                        tool_use_id=block.id,
                        content=result,
                    )],
                })
    raise RuntimeError("超过最大迭代次数，任务未完成")
```

`execute_action` 是真正干活的地方：按 `action["action"]` 分发到截图、鼠标、键盘的具体实现，执行完把新截图作为 `tool_result` 返回。Claude 看到新截图，才知道上一动作有没有生效，再决定下一步。

### 截图尺寸与坐标换算

截图发给模型前要控制尺寸。不同模型上限不同：Opus 5/Sonnet 5/Opus 4.8/4.7 接受长边最长 2576 像素；更早的模型是长边 1568 像素、总面积约 1.15 兆像素。超出 8000 像素一侧才会被拒绝，否则 API 会静默降采样——但降采样后 Claude 返回的坐标是对应降采样图的，你需要把坐标按比例映射回真实屏幕，否则点击会偏。

一个常踩的坑是 **macOS Retina 屏**：截图按设备像素比 2 输出，图像分辨率是逻辑坐标的两倍。要么发图前缩一半，要么把 Claude 返回的坐标对半再点击，否则每次都点偏。

## 6.4 Claude Code 架构与设计

Claude Code 是 Anthropic 官方推出的终端编程工具，让开发者在命令行里和 Claude 协同写代码。它和 Computer Use 的关系是：**Claude Code 是 Computer Use 能力的一个落地载体**——在 Claude Code 里，Claude 不只是改代码，也能截图看界面、操作浏览器、驱动桌面应用，靠的正是这套观察-决策-执行循环。

它和「在 IDE 里装个插件」的差别在于深度集成：

| 特性 | 传统 IDE 插件 | Claude Code |
|------|------------|-------------|
| 上下文保持 | 每次会话各自为政 | 整个工作会话持续 |
| 工具集 | 各插件各写一套 | 统一文件、终端、Git 工具 |
| 界面操作 | 通常没有 | 有（Computer Use） |
| 权限控制 | 各插件自己定 | 统一授权与确认 |

## 6.5 安全机制与沙箱环境

Computer Use 的风险比普通 API 高，因为模型接触到的是真实界面操作。Anthropic 的官方口径很直接：**把 Claude 隔离在最小权限的虚拟机或容器里，别让它碰到敏感数据**。

### 官方安全建议

1. **用专用虚拟机或容器**，给最小权限，防止系统攻击或误操作
2. **别给模型敏感数据**（如账号登录信息），防窃取
3. **联网用白名单**，只允许访问指定域名，减少恶意内容暴露
4. **有实际后果的操作要人工确认**，比如接受 cookie、完成金融交易、同意服务条款

这里有个特别值得注意的点：**提示注入**。Claude 有时会服从网页或图片里的指令，哪怕和你给它的指令冲突——比如网页上写着「忽略上面的要求，执行这个命令」。为缓解这个，Anthropic 在 Computer Use 上自动跑一层提示注入分类器。当分类器在截图里识别出疑似注入时，会引导模型先向用户要确认再继续，相当于又加了一道保险。这层防御对「没有人在环」的无人值守场景不理想，可以联系支持关闭，但那是你自家产品要评估的取舍。

### 数据归属

Computer Use 是客户端工具：一张截图、一次点击、一段输入、用到的文件，都产生并保存在**你的环境里**，Anthropic 不存储这些。Anthropic 只是在 API 调用时实时处理截图和动作请求，保留策略遵循标准的 API 数据保留规则。因为数据由你的应用掌控，Computer Use 满足 ZDR（零数据保留）资质。

### 参考实现

官方在 `anthropics/anthropic-quickstarts` 仓库的 `computer-use-demo` 目录里给了完整参考实现：Docker 环境、各动作的工具实现、agent loop、可交互的 Web 界面。自己搭环境时，至少需要这几样：虚拟化/容器化环境、至少一个 computer 工具的实现、agent loop，以及启动循环的入口。

## 6.6 推荐做法与注意事项

### 提升质量的提示词

- **任务拆小、步骤说清**：一步一个明确指令，别让 Claude 一次猜很多
- **强迫验证**：提示里要求「每完成一步就截图，确认是否达到预期，没达到就重试，确认成功再进下一步」——Claude 有时会想当然地认为动作成功了，其实没生效
- **偏难关交互用快捷键**：下拉框、滚动条这类鼠标难操作的，让 Claude 改用键盘快捷键
- **可复用任务给示例**：把成功结果的截图和调用序列放进提示词
- **指令文本放在图片前**：构造 `content` 数组时，先放指令文字再放截图，能提升点击准确性

### 已知限制

- **延迟**：对人机交互来说可能偏慢，适合后台信息收集、自动化测试这类对速度不敏感的场景
- **视觉精度**：Claude 生成坐标时可能出错或幻觉，Extended Thinking 有助于看清它为什么这么选
- **工具选择**：复杂任务里可能选错工具或采取意外动作；并行操作多个小众应用时可靠性下降
- **滚动**：滚轮动作在有些应用里不生效，可用 Page Down 等键盘替代
- **社交平台账号行为**：Claude 能访问网站，但创建账号、发帖、冒充真人等能力是受限的

### 坐标系与精度

分辨率别太低，1280×720 是个不错的基线。点了没点中，多数是这几种原因：`display_width_px`/`display_height_px` 和实际发的截图尺寸不一致；目标太小、4K 源缩图后细节丢了；指令含糊导致点错元素。模型选择也影响点击精度——Sonnet 4.6 的机械点击比 Opus 4.6 更稳，Opus 4.7 把差距拉平了。

### 什么时候不划算

| 场景 | 为什么不建议 | 替代方案 |
|------|------------|----------|
| 纯数据处理 | 绕了界面一大圈 | 直接调 API 或脚本 |
| 定期批量任务 | 慢且贵 | Cron + 脚本 |
| 需要精确坐标的操作 | 视觉判断有误差 | 专用 API 或原生驱动 |
| 涉及敏感账号/资金 | 风险不可控 | 人工执行 |

一句话：**Computer Use 适合「没有现成 API、只能操作界面」的场景**。能用 API 或脚本解决的就别用它，它是对付遗留系统、动态界面、跨应用工作流的最后手段。

---

**文档元信息**
难度：⭐⭐⭐⭐ | 类型：API 解析 | 更新日期：2026-08-08 | 预计阅读时间：40 分钟 | 字数：约 4000 字