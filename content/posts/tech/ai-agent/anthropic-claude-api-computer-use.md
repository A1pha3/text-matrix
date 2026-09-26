---
title: "Claude API基础专题（六）：Claude Code与Computer Use"
date: "2026-03-25T11:00:00+08:00"
lastmod: "2026-09-21T11:00:00+08:00"
slug: "claude-api-computer-use-automation"
aliases:
  - /posts/tech/claude-api-computer-use-automation/
description: "Computer Use 让 Claude 通过截图、鼠标、键盘操作桌面，真正的执行由调用方在自己控制的环境里完成。覆盖三版工具与模型对应关系、17 个成员工具、batch action、agent loop 代码、截图缩放与坐标换算，以及 Claude Code CLI 里开箱即用的 computer use 与提示注入防御。"
draft: false
categories: ["技术笔记"]
tags: ["Claude", "Computer Use", "自动化"]
github_repo: "anthropics/claude-quickstarts"
source_key: "gh:anthropics/claude-quickstarts"
---

# Claude API 基础专题（六）：Claude Code 与 Computer Use

> 预计阅读时间：45 分钟 | 难度：⭐⭐⭐⭐

---

> **目标读者**：希望让 Claude 操控计算机完成任务的开发者
> **前置知识**：已完成第一篇《API基础》、第三篇《工具调用》、第五篇《MCP协议》

---

Computer Use（计算机使用）是 Anthropic 提供的界面操作能力：它在 Messages API 里把「截图、鼠标、键盘」打包成一组工具，让 Claude 能对着桌面界面工作。它看起来像 Claude 在亲手操作电脑，实际分工恰恰相反——**Claude 只负责看屏幕、决定下一步，真正的截图、移动光标、敲键盘，必须由你的应用在自己控制的环境里替它执行**。这个边界是理解整个功能的关键。

下面从六个角度展开：它把工具调用的边界推到了哪里、观察-决策-执行循环怎么运转、用 API 怎么落地一个 agent loop、Claude Code 里的开箱即用版本长什么样、安全上要额外扛住哪些风险，以及常见的坑和排查顺序。

**本文目录**

- 6.1 从工具调用到计算机控制
- 6.2 Computer Use 原理解析
- 6.3 用 API 实现 Computer Use
- 6.4 Claude Code 里的 Computer Use
- 6.5 安全机制与数据边界
- 6.6 推荐做法与注意事项
- 6.7 常见问题与排查

## 学习目标

读完本文，你应该能：

- 说清 Computer Use 里模型与应用的分工边界，以及它和普通工具调用的区别
- 画出观察-决策-执行循环，并说明每个环节由谁执行
- 区分三版工具与各自支持的模型，选对版本和 beta 头
- 用 Python SDK 搭出一个能跑的最小 agent loop，处理好 batch action 与坐标换算
- 在 Claude Code CLI 里启用 computer use，说清它与 API 沙箱方案的信任边界差异
- 判断一个任务该用 Computer Use、browser use 还是直接调 API，并解释理由

## 6.1 从工具调用到计算机控制

工具调用解决的是「模型知道该调什么，但不知道现实世界长什么样」。它把外部能力封装成一个个函数，模型选择函数、填参数、读返回值。这一切的前提是：**能力边界是预先画好的**。查天气、查数据库、跑代码，都能写成函数；但「这个页面长什么样、提交按钮在哪个坐标」这种信息，工具调用拿不到。

| 任务类型 | 传统工具调用 | Computer Use |
|----------|------------|--------------|
| 查天气、查数据库 | 能，封装成函数即可 | 能 |
| 填一个没见过结构的表单 | 难，得先知道字段位置 | 能，看截图定位 |
| 跨应用操作（复制粘贴、拖文件） | 很难，每对应用都要专门写 | 能，操作桌面本身 |
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
│  ③ 应用在自己的环境里执行该动作（截图/点击/输入）           │
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

这套环境是 Linux 下的参考实现。如果你更想让 Claude 操作真实的 macOS 桌面，Claude Code 已经把「环境 + 工具实现 + 循环」整个打包好了，见 6.4 节。

### 工具版本与模型对应

Computer Use 的工具经历过三个版本，新版是客户端工具集（client toolset），两个旧版仍以 beta 形式保留：

| 工具版本 | beta 头 | 可用模型 |
|----------|---------|----------|
| `computer_toolset_20260801` | 不需要 | Fable 5.1、Mythos 5.1、Fable 5、Mythos 5、Opus 5、Sonnet 5、Opus 4.8 |
| `computer_20251124` | `computer-use-2025-11-24` | 上行全部模型，外加 Opus 4.7、Opus 4.6、Sonnet 4.6、Opus 4.5 |
| `computer_20250124` | `computer-use-2025-01-24` | Sonnet 4.5、Haiku 4.5，以及已退役的 Opus 4.1、Sonnet 4、Opus 4（Bedrock 与 Google Cloud 上仍可调用，见官方退役说明） |

三条使用规则值得记牢：

- **Opus 4.7 及更早的模型不支持新版工具集**，只能走 `computer_20251124` 加 beta 头。看模型名字猜版本不可靠，同一模型家族不同代际支持的工具版本可能不同，拿不准就查官方兼容性表格。
- **新版工具集目前只在 Claude API 和 Google Cloud 上提供**，Bedrock、Microsoft Foundry 等平台暂时只有旧版 beta 工具。
- 已有的 `computer_20251124` 集成可以继续工作；要升级到工具集时，官方提供了迁移说明，核心动作是去掉 beta 头、换 `type` 声明、删掉工具集已不接受的旧字段（见 6.7 节 Q2）。

### 工具参数

新旧两版工具接受的参数完全不同，混用会被直接拒绝。

新版 `computer_toolset_20260801` 在 `tools` 数组里只接受四个参数：

| 参数 | 必填 | 说明 |
|------|------|------|
| `type` | 是 | 固定为 `computer_toolset_20260801` |
| `configs` | 否 | 按成员工具名逐个配置：`enabled`（17 个成员默认全开，含 `zoom`）与 `defer_loading`（配合 tool search 延迟加载） |
| `cache_control` | 否 | 在工具集定义处打 prompt caching 断点 |
| `allowed_callers` | 否 | 只允许 `["direct"]` |

注意新版**没有** `name`、`display_width_px`、`display_height_px`、`display_number`、`enable_zoom` 这些字段——请求里带任何一个都会收到 `invalid_request_error`。坐标永远以你返回的截图的像素空间为准（见 6.3 节），所以也不再需要声明显示尺寸。如果环境实现不了 zoom，用 `configs` 明确关掉它：

```json
{
  "type": "computer_toolset_20260801",
  "configs": {
    "zoom": { "enabled": false }
  }
}
```

旧版工具（`computer_20251124` / `computer_20250124`）才使用下面这套参数：

| 参数 | 必填 | 说明 |
|------|------|------|
| `type` | 是 | 工具版本标识 |
| `name` | 是 | 固定为 `"computer"` |
| `display_width_px` | 是 | 显示宽度（像素） |
| `display_height_px` | 是 | 显示高度（像素） |
| `display_number` | 否 | X11 环境下的显示器编号 |
| `enable_zoom` | 否 | 仅 `computer_20251124`，开启 zoom 动作，默认 `false` |

无论新旧版本，Computer Use 工具都是**无 schema 的**：不像普通工具那样要你提供 `input_schema`，schema 内置在模型里，不能修改。

### 可用动作

新版工具集把动作收敛成 17 个成员工具（member tools）。Claude 的每次调用是一个 `tool_use` 块，`name` 写成员名、带着 `"toolset_name": "computer"` 标识，`input` 里只有该成员自己的参数：

| 成员工具 | 输入 | 作用 |
|----------|------|------|
| `screenshot` | 无 | 截取整个显示，返回图像 |
| `zoom` | `region: [x0, y0, x1, y1]` | 以全分辨率截取指定区域，按纵横比缩放到常规截图尺寸返回，用于读小字 |
| `left_click` | `coordinate`（可选）、`text`（修饰键） | 左键点击；省略坐标则在当前光标处点击 |
| `right_click` / `middle_click` / `double_click` / `triple_click` | 同 `left_click` | 其他鼠标键与多击 |
| `left_click_drag` | `start_coordinate`、`coordinate` | 从起点按下、拖到终点释放 |
| `mouse_move` | `coordinate` | 移动光标不点击，例如悬停 |
| `left_mouse_down` / `left_mouse_up` | 无 | 在当前光标处按下/释放，表达 `left_click_drag` 表达不了的拖拽 |
| `cursor_position` | 无 | 以文本返回当前光标坐标 |
| `scroll` | `scroll_direction`、`scroll_amount`、`coordinate`（可选） | 按方向滚动指定格数 |
| `type` | `text` | 在当前键盘焦点处输入文本 |
| `key` | `text`、`repeat`（1–100，默认 1） | 按键或组合键（如 `ctrl+s`），可重复 |
| `hold_key` | `text`、`duration`（最长 300 秒） | 按住某个键 |
| `wait` | `duration`（最长 300 秒） | 暂停等待，例如等应用加载 |

几个容易踩的细节：

- **坐标一律是截图像素**。所有 `coordinate`、`start_coordinate`、`region` 都以你返回的全屏截图为坐标系，原点在左上角；zoom 之后 Claude 给出的坐标仍在这个全屏空间里，不是相对放大图的。自己缩放过截图，就要把坐标按比例换算回去。
- **`left_click` 支持修饰键**：`text` 可传 `shift`、`ctrl`、`alt`、`super` 或其组合（如 `ctrl+shift`），只在该次点击期间按住。
- **17 个成员默认全部启用**。环境实现不了的成员应该用 `configs` 收回，而不是留着启用然后每次返回错误；Claude 调用了你未实现的成员时，给那条 `tool_result` 标 `is_error: true`。

### 返回结果与 batch action

Claude 可以在一条响应里一次返回多个成员调用——先点击、再输入、最后截图，官方称为 **batch action**。形状与并行工具调用相同，但执行语义不同：**必须按 `content` 里的顺序逐个执行，不能并发**，因为后面的动作往往依赖前面的（比如 `type` 输入到上一次点击聚焦的输入框）。一旦某个动作失败，停止执行后面的动作，但每个 `tool_use` 块都必须有对应的 `tool_result`：

- 执行成功的返回正常结果
- 失败的那条返回 `is_error: true` 并说明原因
- 之后未执行的每条都返回 `is_error: true`，内容用固定文本 `Not executed: an earlier computer action in this turn failed.`

任何一条 `tool_use` 没有被回答，下一次请求会被 `invalid_request_error` 拒绝——只读第一个块就调 API 的 loop，会在下一次调用直接报错。

回结果时还有一条硬规则：**每个 `tool_result` 都要原样带回 `"toolset_name": "computer"`**，漏掉或者写了别的工具集名，结果会被拒绝。`screenshot` 和 `zoom` 的结果必须是图像；其他成员回一句 `OK` 这样的短文本就够（`cursor_position` 回坐标文本）。Claude 通常会让一个 batch 以 `screenshot` 收尾来确认结果；如果一批没有截图收尾，你的应用也可以在最后一条结果上主动附一张截图，省掉一个来回。

## 6.3 用 API 实现 Computer Use

### 定义工具并发出请求

现在的推荐路径是新版工具集：不需要 beta 头，直接走 `client.messages.create`。官方快速开始同时声明了 text editor 和 bash 工具——Claude 处理桌面任务时通常会把它们搭配着用：

```python
import anthropic

client = anthropic.Anthropic()

response = client.messages.create(
    model="claude-opus-5",
    max_tokens=1024,
    tools=[
        {"type": "computer_toolset_20260801"},
        {"type": "text_editor_20250728", "name": "str_replace_based_edit_tool"},
        {"type": "bash_20250124", "name": "bash"},
    ],
    messages=[{
        "role": "user",
        "content": "把一张猫的图片保存到桌面上。",
    }],
)
```

响应里如果 `stop_reason == "tool_use"`，说明 Claude 想要执行动作。工具集成员的 `tool_use` 块长这样——动作名在 `name` 字段，`input` 里只有参数，没有 `action` 字段：

```json
{
  "type": "tool_use",
  "id": "toolu_01WkoTUvSHDzTBu2xnGk8Ep8",
  "name": "left_click",
  "toolset_name": "computer",
  "input": { "coordinate": [512, 742] }
}
```

已有集成仍在用旧版工具的话，写法是走 beta 命名空间并带 beta 头（`claude-sonnet-4-5` 在支持名单内，示例依然有效）：

```python
response = client.beta.messages.create(
    model="claude-sonnet-4-5",
    max_tokens=1024,
    betas=["computer-use-2025-01-24"],  # 旧版工具需要 beta 头
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

旧版工具的成员调用长另一个样子：`name` 固定为 `"computer"`，具体动作在 `input.action` 里。这是新旧 loop 代码最大的分叉点。

还有一点对调试很有用：**声明了 computer use 工具后，API 会自动在系统提示词里注入一段专用指令**（告诉模型它面对的是一个沙箱计算环境、只能通过这些函数行事），你自己传的 `system` 参数仍然生效，会被合并进最终系统提示词。

### 一个最小的 agent loop

下面的循环处理新版工具集，省略了 `run_computer_action` 的具体实现——它负责对接你的沙箱：

```python
import anthropic

client = anthropic.Anthropic()

TOOLS = [
    {"type": "computer_toolset_20260801"},
]

def agent_loop(messages, max_iterations=10):
    for _ in range(max_iterations):
        response = client.messages.create(
            model="claude-opus-5",
            max_tokens=4096,
            tools=TOOLS,
            messages=messages,
        )

        # 任务完成：Claude 不再请求工具
        if response.stop_reason != "tool_use":
            return [
                block.text
                for block in response.content
                if block.type == "text"
            ]

        # 一轮里可能有多个成员调用（batch action），逐个执行
        results = []
        for block in response.content:
            if block.type != "tool_use":
                continue
            # 按 (toolset_name, name) 分发：toolset_name 把 computer 成员
            # 和同请求里的其他工具区分开
            if block.toolset_name != "computer":
                continue
            result = run_computer_action(block.name, block.input)
            results.append({
                "type": "tool_result",
                "tool_use_id": block.id,
                "toolset_name": "computer",  # 必须原样带回
                "content": result,
            })

        # 整轮 assistant 消息附回，全部 tool_result 放进同一条 user 消息
        messages.append({"role": "assistant", "content": response.content})
        messages.append({"role": "user", "content": results})

    raise RuntimeError("超过最大迭代次数，任务未完成")
```

`run_computer_action` 是真正干活的地方，按成员名分发：

```python
def run_computer_action(name, tool_input):
    if name == "screenshot":
        return capture_screenshot()          # 返回图像块列表
    if name == "left_click":
        return click(tool_input.get("coordinate"))
    if name == "type":
        return type_text(tool_input["text"])
    if name == "key":
        return press_key(tool_input["text"])
    # ... 其余成员按需实现
    raise ValueError(f"未实现的成员工具：{name}")
```

两个容易写错的点，都来自 batch action 的语义：其一，所有 `tool_result` 必须放进**同一条** user 消息，而不是每个动作后面各跟一条；其二，遇到失败要停止执行后续动作，但别漏掉给它们回固定的 halt 文本（见 6.2 节）。执行完把新截图作为 `tool_result` 返回——Claude 看到新截图，才知道上一动作有没有生效，再决定下一步。

### 截图尺寸与坐标换算

截图发给模型前要控制尺寸，而且**新旧版本的行为完全不同**：

- **新版工具集：API 不帮你缩图**。返回的截图和 zoom 图必须已经符合模型的图像上限，超限的 `tool_result` 会被校验错误直接拒绝。
- **旧版工具：超出上限的图会被 API 静默降采样**——模型看到的是一张被缩小的图，坐标对应的也是缩放后的空间，不换算就会系统性点偏。

上限本身按模型分两档：Opus 4.7 及之后的模型（包括所有支持新版工具集的模型）长边最长 2576 像素、总计 4784 个视觉 token（约 3.75 兆像素）；更早的模型是长边 1568 像素、总计约 1.15 兆像素。

正确的做法是自己把截图缩到上限之内，并**记住缩放比例**，好把 Claude 返回的坐标换算回真实屏幕：

```python
import math

screen_width, screen_height = 1512, 982

def get_scale_factor(width, height):
    """同时满足长边与总像素上限，取最紧的那个约束。"""
    long_edge_scale = 1568 / max(width, height)
    total_pixels_scale = math.sqrt(1_150_000 / (width * height))
    return min(1.0, long_edge_scale, total_pixels_scale)

scale = get_scale_factor(screen_width, screen_height)

# 截图后按 scale 缩小再返回
# 执行点击时把坐标放大回去：
def execute_click(x, y):
    perform_click(x / scale, y / scale)
```

分辨率怎么选，官方给出的建议是：一般桌面任务用 1024×768 或 1280×720；网页应用用 1280×800 或 1366×768；避免超过 1920×1080，否则性能会受影响。分辨率太低会让 Claude 看不清小字，配合 zoom 成员可以让它按需看全分辨率的局部区域。

一个常踩的坑是 **macOS Retina 屏**：截图按设备像素比 2 输出，图像分辨率是逻辑坐标的两倍。要么发图前缩一半，要么把 Claude 返回的坐标对半再点击，否则每次都点偏。

## 6.4 Claude Code 里的 Computer Use

前面几节讲的是 API 路径：自己搭环境、自己写工具实现、自己跑循环。Claude Code 把这整条链路打包了——它把 computer use 做成**内置的 MCP 服务器** `computer-use`，启用后 Claude 就能直接操作你面前的真实 macOS 桌面：打开应用、点击、输入、截图，和写代码在同一个会话里完成。编译一个 Swift 应用、启动它、把每个按钮点一遍、截图确认，全程不需要离开终端。

这个能力目前是 **macOS 上的研究预览（research preview）**：需要 Pro 或 Max 订阅，Team 与 Enterprise 计划不可用，必须 claude.ai 登录（第三方云渠道接入的 Claude Code 用不了），且只在交互式会话中可用（`-p` 非交互模式不支持）。CLI 版仅限 macOS；Desktop 桌面应用版支持 macOS 和 Windows，两者共用同一套引擎。

### 启用与授权

computer use 默认关闭，按项目开启一次即可：

1. 在交互式会话里运行 `/mcp`，在服务器列表里找到 `computer-use`（显示为 disabled）
2. 选中它并选择 **Enable**，设置按项目持久化
3. 第一次实际使用时，macOS 会要求授予两个权限：**辅助功能**（Accessibility，对应点击、输入、滚动）和**屏幕录制**（Screen Recording，对应看屏幕）——授权后可能需要重启 Claude Code

启用之后，直接用自然语言布置需要 GUI 的任务即可，比如「构建 app target，启动，把每个 tab 都点一遍确认没有崩溃，发现的错误界面截图」。

### 按应用审批

启用服务器不等于把整台机器交给 Claude。会话内第一次需要操作某个应用时，终端里会出现审批提示，写明：要控制哪些应用、申请了哪些额外权限（如剪贴板）、工作期间会隐藏多少其他应用。你可以选择 **Allow for this session**（仅本会话有效）或拒绝。

敏感应用会额外标警：

| 警告 | 适用应用 |
|------|----------|
| 等价于 shell 访问 | Terminal、iTerm、VS Code、Warp 等终端与 IDE |
| 可读写任意文件 | Finder |
| 可更改系统设置 | System Settings |

这些应用不会被禁止使用，警告只是让你判断任务是否值得给这个级别的权限。控制粒度也按应用类型分级：浏览器和交易平台是只读，终端和 IDE 只能点击，其余应用是完全控制。

### 运行时的行为

几个机制决定了 Claude 工作时你的桌面会发生什么：

- **单会话锁**：同一时刻只有一个会话能控制电脑。锁在会话第一次执行 computer use 动作时获取，会话退出才释放；第二个会话的 computer use 请求会报错并指名持锁会话
- **其他应用被隐藏**：Claude 控制屏幕期间，其他可见应用会被隐藏，只留下批准的应用；终端窗口保持可见，但**被排除在截图之外**——Claude 看不到自己会话的输出，屏幕上的提示词无法回流进模型。一轮结束后隐藏的应用自动恢复
- **截图自动降采样**：Claude Code 在发送前自动缩图，16 英寸 MacBook Pro 的原生 Retina 截图 3456×2234 会被缩到约 1372×887，保持纵横比。没有设置可改；如果 Claude 总看不清某个小字，去应用里把字号调大，而不是调显示分辨率
- **随时可停**：每轮第一次操作时会出现 macOS 通知「Claude is using your computer · press Esc to stop」，按 `Esc` 立即中止当前动作（这个按键会被消费掉，屏幕上的提示注入无法伪造它），终端里 `Ctrl+C` 也可以

### 工具选择的优先级

Claude 并不会一上来就控制屏幕。它按精确度从高到低选工具：有 MCP 服务器的服务走 MCP；能一行 shell 解决的走 Bash；浏览器任务且装了 Claude in Chrome 就走浏览器；都不适用才落到 computer use。屏幕控制留给「其他工具都够不着」的场景——原生应用、iOS Simulator 这类模拟器、没有 API 的专有软件。

### 与 API 沙箱方案的信任边界对比

同一个能力，两种载体，信任边界完全不同：

| | API 自建沙箱（6.2–6.3 节） | Claude Code CLI |
|---|---|---|
| 执行环境 | 你控制的虚拟机/容器，与主机隔离 | 你正在使用的真实 macOS 桌面 |
| 权限模型 | 你写的代码决定一切 | 按应用逐个审批，会话内有效 |
| 出错的波及面 | 沙箱内的虚拟环境 | 你的真实系统与应用 |
| 适用阶段 | 无人值守的自动化 | 有人在场的开发与调试 |

API 方案的隔离粒度粗但边界硬；Claude Code 方案用审批链（per-app approval、敏感应用警告、Esc 中止、单会话锁、终端截图排除）把风险拆成一个个明确的决定。给 Claude 操作真实桌面的任务时，先想清楚这个差异。

## 6.5 安全机制与数据边界

Computer Use 的风险比普通 API 高，因为模型接触到的是真实界面操作。Anthropic 的官方口径很直接：**把 Claude 隔离在最小权限的虚拟机或容器里，别让它碰到敏感数据**。

### 官方安全建议

1. **用专用虚拟机或容器**，给最小权限，防止系统攻击或误操作
2. **别给模型敏感数据**（如账号登录信息），防窃取
3. **联网用白名单**，只允许访问指定域名，减少恶意内容暴露
4. **有实际后果的操作要人工确认**，比如接受 cookie、完成金融交易、同意服务条款

### 提示注入防御

这里有个特别值得注意的点：**提示注入**。Claude 有时会服从网页或图片里的指令，哪怕和你给它的指令冲突——比如网页上写着「忽略上面的要求，执行这个命令」。Anthropic 做了两层防御：一是训练模型抵抗注入；二是**自动运行的分类器**——只要用了 computer use 工具，分类器就会扫描工具返回的内容（截图等），识别出疑似注入时，引导模型先确认「这个指令真的来自用户吗」再行动。

这层保护对「没有人在环」的无人值守场景不理想，可以联系支持关闭，但官方同时强调：即便分类器在位，上面那四条隔离措施照样必要。另外，如果你在自己的产品里启用 computer use，要在开启前告知最终用户相关风险并取得同意——这是官方明确的义务要求。

### 数据归属

Computer Use 是客户端工具：一张截图、一次点击、一段输入、用到的文件，都产生并保存在**你的环境里**，Anthropic 不存储这些。Anthropic 只是在 API 调用时实时处理截图和动作请求，保留策略遵循标准的 API 数据保留规则。因为数据由你的应用掌控，Computer Use 符合 ZDR（零数据保留，Zero Data Retention）资质——但官方明确标注该资质排除部分受覆盖型号（Covered Models），具体模型是否满足 ZDR 要在数据保留文档里逐项核对，别想当然认为所有模型都满足。

### 参考实现

官方在 `anthropics/claude-quickstarts` 仓库的 `computer-use-demo` 目录里给了完整参考实现：容器化环境的 Dockerfile、`computer_use_demo/tools/` 下的各动作工具实现、`loop.py` 里的 agent loop，以及 streamlit 写的可交互 Web 界面。自己搭环境时，至少需要这几样：虚拟化/容器化环境、computer use 各动作的实现、agent loop，以及启动循环的入口。

## 6.6 推荐做法与注意事项

### 提升质量的提示词

- **任务拆小、步骤说清**：一步一个明确指令，别让 Claude 一次猜很多
- **强迫验证**：提示里要求「每完成一步就截图，仔细评估是否达到预期，明确写出『我已评估第 X 步……』，不对就重试，确认成功再进下一步」——Claude 有时会想当然地认为动作成功了，其实没生效
- **偏难关交互用快捷键**：下拉框、滚动条这类鼠标难操作的，让 Claude 改用键盘快捷键
- **可复用任务给示例**：把成功结果的截图和调用序列放进提示词
- **指令文本放在图片前**：构造 `content` 数组时，先放指令文字再放截图，能提升点击准确性
- **需要登录时显式给凭据**：用 `<robot_credentials>` 这类 XML 标签在提示词里提供用户名密码；同时要意识到，在需要登录的应用上跑 computer use 会放大提示注入的风险
- **小字看不清就引导 zoom**：问具体区域（「侧边栏的文件名是什么」）而不是整个屏幕，Claude 才会用 zoom 去看全分辨率的局部
- **让每批动作以截图收尾**：在系统提示里写明「每组动作结束后截图确认再继续」，你的 loop 就总能拿到最新画面

### 模型选择与思考配置

点击精度和模型代际相关：在使用 `computer_20251124` 的模型里，Sonnet 4.6 的机械点击比 Opus 4.6 更稳，截图被重度缩小时也更稳健；Opus 4.7 把差距拉平到与 Sonnet 4.6 大致相当，而且它的分辨率上限更高、需要降采样的场合更少。

官方还按内部基准给过 effort 配置建议（适用于 `computer_20251124`）：Opus 4.7 默认 `high`，高吞吐或成本敏感的负载用 `low`；Sonnet 4.6 与 Opus 4.6 默认 `medium`（精度成本比最好），避免 `max`——token 成本上去了，UI 任务精度并没有提升。这两个模型上 `low` 的输出 token 甚至比完全关闭 thinking 更少（少犯错意味着少重试），成本敏感的循环值得试试。

排查「为什么点这里」时注意：支持新版工具集的模型默认省略 thinking 文本，要在 thinking 配置里设 `display: "summarized"` 才能看到摘要化的思考过程。

### 已知限制

- **延迟**：对人机交互来说可能偏慢，适合后台信息收集、自动化测试这类对速度不敏感的场景
- **视觉精度**：Claude 生成坐标时可能出错或幻觉，摘要化思考（见上）有助于看清它为什么这么选
- **工具选择**：复杂任务里可能选错工具或采取意外动作；操作小众应用或同时操作多个应用时可靠性下降
- **滚动**：滚轮动作在有些应用里不生效，可用 Page Down 等键盘替代
- **电子表格**：用细粒度鼠标动作（`left_mouse_down` / `left_mouse_up`）加修饰键组合来选中单个单元格，复杂表格操作可能要试几次
- **社交平台账号行为**：Claude 能访问网站，但创建账号、发帖、冒充真人等能力是受限的

### 成本概览

新版工具集的声明本身就有开销：加进请求约 4500 个 input token（Fable 5、Mythos 5、Opus 5、Opus 4.8 上约 4520，Sonnet 5 上约 4590），覆盖成员工具定义和专用系统提示词；用 `configs` 关掉 zoom 能省约 410。旧版工具的开销小得多：系统提示词增量 466–499 token，工具定义约 735 token。真正的消耗大头是截图——每张截图或 zoom 图按图像输入计费，一张约 1000–1800 input token，长循环里截图会迅速堆积（处理办法见 6.7 节 Q6）。

### 什么时候不划算

| 场景 | 为什么不建议 | 替代方案 |
|------|------------|----------|
| 任务全程在网页里 | 桌面环境是多余的载体 | browser use 工具，直接读写页面本身 |
| 纯数据处理 | 绕了界面一大圈 | 直接调 API 或脚本 |
| 定期批量任务 | 慢且贵 | Cron + 脚本 |
| 需要精确坐标的操作 | 视觉判断有误差 | 专用 API 或原生驱动 |
| 涉及敏感账号/资金 | 风险不可控 | 人工执行 |

一句话：**Computer Use 适合「没有现成 API、只能操作界面」的场景**。能用 API 或脚本解决的就别用它，它是对付遗留系统、动态界面、跨应用工作流的最后手段；全程在浏览器内的任务，官方也提供了更轻的 browser use 工具，两个工具集可以在同一个请求里声明、按 `toolset_name` 区分。

## 6.7 常见问题与排查

### Q1：Claude 每次点击都偏一小段距离

优先查坐标空间不一致，但新旧版本要分别对待：

- **新版工具集**：坐标就是「你返回的截图」的像素空间。逐项自查：自己缩放过截图的话，坐标放大回去了吗（`x / scale`）；缩放时纵横比保持了吗；Retina 屏的 2 倍设备像素比换算了吗
- **旧版工具**：先对三件套——声明给模型的 `display_width_px` / `display_height_px` 是否和实际发出的截图分辨率一致；原始尺寸超出模型上限时旧版会静默降采样，主动缩到 1280×720 一类合规尺寸再发；Retina 屏是否做了换算

这三处错一处，偏移都是系统性的，不是偶发。

### Q2：报错信息提示 beta 头不对、字段不支持或工具版本不匹配

先核对模型与工具版本的对应表（见 6.2 节）。最容易踩的是从旧版迁到工具集时的两类报错：忘记去掉 beta 头，或者 `tools` 条目里还留着 `name`、`display_width_px`、`display_height_px`、`display_number`、`enable_zoom`——工具集会拒绝这些字段并返回 `invalid_request_error`。zoom 的开关改用 `configs` 控制，注意默认值也反过来了（旧版 `enable_zoom` 默认关，工具集默认开）。

### Q3：agent loop 卡在无限循环，费用一直涨

loop 里 `max_iterations` 就是兜底。设成一个任务合理需要的上界（通常是 10–20），超限抛异常或返回未完成，别让它无限跑。另外 batch action 一次会返回多个 `tool_use`，每个都要回 `tool_result`：要按顺序执行、遇错停止，后续未执行的回固定 halt 文本；漏回任何一条，下一次请求直接被拒。

### Q4：滚轮滚动在某些应用里没反应

这是已知限制。改用键盘替代：提示词里要求 Claude 用 `Page Down`、方向键或快捷键来滚动，比硬调滚轮可靠。

### Q5：提示注入分类器拦住了无人值守的流程

分类器识别到疑似注入时会让模型先确认指令来源，这本身是保守的安全设计。对「没有人在环」的场景它确实碍事，可以联系支持关闭，但要先想清楚：关了这层防御，你的沙箱是否仍有足够的隔离兜底。

### Q6：长任务跑着跑着上下文和费用都膨胀

截图是主要来源，一张约 1000–1800 input token。两个约束叠加：单请求超过 20 张图时，每张图都会被施加更严的每边 2000 像素限制；而不剪枝的话，几十轮就会撞上这个数。处理原则：

- 每张截图控制在单边 2000 像素以内，就不用操心 20 图限制
- 剪旧图要**成批**剪，别一轮剪一张——每轮都改前缀会让 prompt caching 完全失效；一个可用的默认值是保留最近 3 张、每 25 轮剪一次
- 在支持新版工具集的模型（如 Fable 5.1）上，客户端剪枝会作废其后所有 thinking 块——改用服务端的 tool result clearing 来清理旧截图

### 排查顺序

先把「报什么错」记下来，再决定从哪查：

```text
请求被拒 / 报错
├── beta 头或工具版本不匹配 → 查模型兼容表
├── 工具集条目字段被拒 → 删掉 name / display_* / enable_zoom
├── 截图校验错误（工具集） → 主动缩到模型上限内
├── tool_result 漏回 / 格式错 → 每条 tool_use 都要回，带回 toolset_name
└── 正常返回但点不准
    ├── 坐标空间不一致 → 记缩放比例，坐标放大回去
    ├── 纵横比被拉伸 → 缩放时保持比例
    └── Retina 未换算 → 做设备像素比换算
```

---

### 参考文献

- Anthropic 官方文档 · Computer use tool：https://platform.claude.com/docs/en/agents-and-tools/tool-use/computer-use-tool
- Claude Code · Let Claude use your computer from the CLI：https://code.claude.com/docs/en/computer-use
- 参考实现 claude-quickstarts / computer-use-demo：https://github.com/anthropics/claude-quickstarts/tree/main/computer-use-demo
- 工具与模型兼容性： https://platform.claude.com/docs/en/agents-and-tools/tool-use/tool-reference
- Browser use tool（网页内任务）：https://platform.claude.com/docs/en/agents-and-tools/tool-use/browser-use-tool
- 数据保留与 ZDR： https://platform.claude.com/docs/en/manage-claude/api-and-data-retention

## 参考来源与口径说明

- **版本锚点**：本文以官方 Computer use tool 文档 2026-09-21 的口径为准：现行工具集 `computer_toolset_20260801`（17 个成员工具）加两个 beta 旧版 `computer_20251124`、`computer_20250124`。工具版本与支持模型迭代较快，更新时以「参考文献」中的官方兼容性表格为准，不要只凭本文判断。
- **模型状态**：Opus 4.1、Sonnet 4、Opus 4 已从 Claude API 退役（Bedrock 与 Google Cloud 上仍可调用，Opus 4 仅 Google Cloud），故 6.2 节在 `computer_20250124` 的可用模型里单独标注。早期资料常把 Sonnet 3.7 列入该版本支持名单，现行官方兼容表已不列。
- **仓库改名**：参考实现仓库已由 `anthropics/anthropic-quickstarts` 更名为 `anthropics/claude-quickstarts`，旧路径会重定向，本文一律使用新路径。
- **Claude Code 口径**：6.4 节依据 code.claude.com 的 computer use 文档（macOS research preview，Pro/Max 计划），功能状态与计划要求可能随版本调整，以官方文档为准。
- **代码性质**：`run_computer_action`、`capture_screenshot`、`click` 等函数为占位示意，接入时按自己的环境实现；agent loop 结构对齐官方参考实现的 `loop.py`。截图缩放示例取官方文档的 `get_scale_factor` 逻辑。

**文档元信息**
难度：⭐⭐⭐⭐ | 类型：API 解析 | 更新日期：2026-09-21 | 预计阅读时间：45 分钟 | 字数：约 7000 字
