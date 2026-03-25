---
title: "Claude API基础专题（六）：Claude Code与Computer Use"
date: 2026-03-25
draft: false
categories:
  - 技术笔记
tags:
  - Claude
  - Claude Code
  - Computer Use
  - 自动化
slug: "claude-api-computer-use-automation"
description: "本文详细介绍了Claude的Computer Use能力与Claude Code命令行工具，解析了观察-决策-执行循环的工作原理，探讨了安全机制与沙箱环境，并提供了自动化脚本的开发实战案例。"
---

# Claude API基础专题（六）：Claude Code与Computer Use ⭐⭐⭐⭐

> **目标读者**：希望让Claude真正操控计算机完成复杂任务的开发者
> **前置知识**：已完成第一篇《API基础》、第二篇《提示词工程》、第三篇《工具调用》、第四篇《RAG系统》、第五篇《MCP协议》
> **学习提醒**：Computer Use是Claude最强大的能力之一，但也是最需要谨慎使用的功能

---

## 章节导航

| 小节 | 主题 | 重要程度 |
|------|------|----------|
| 6.1 | 从工具调用到计算机控制 | ⭐⭐⭐⭐⭐ |
| 6.2 | Computer Use原理解析 | ⭐⭐⭐⭐⭐ |
| 6.3 | Claude Code架构与设计 | ⭐⭐⭐⭐ |
| 6.4 | 安全机制与沙箱环境 | ⭐⭐⭐⭐⭐ |
| 6.5 | 开发实战：构建自动化脚本 | ⭐⭐⭐⭐ |
| 6.6 | 最佳实践与注意事项 | ⭐⭐⭐⭐⭐ |

---

## 6.1 从工具调用到计算机控制

### 演进的必然路径

在讨论Computer Use之前，让我们先理解一个根本问题：**为什么Claude要从"回答问题"演进到"操控计算机"？**

回顾LLM的能力演进历程：

**第一阶段：纯文本生成（2020年前）**

这个阶段的LLM只能生成文本。用户输入问题，模型输出答案，就这么简单。

**问题**：模型的知识是静态的，无法获取最新信息，无法执行实际操作。

**第二阶段：工具调用（2022-2023）**

LLM开始能够调用外部工具——搜索网页、查询数据库、执行代码。

```
用户：帮我查一下今天北京的天气
LLM：调用get_weather工具
工具：返回"北京今天晴，25度"
LLM：根据工具返回结果回答用户
```

**进步**：模型能够获取实时信息并执行具体操作。

**局限**：工具是预先定义好的，能力边界固定。模型无法应对未曾预料的情况。

**第三阶段：Computer Use（2024-至今）**

Claude获得了直接操控计算机的能力——操作鼠标、键盘，打开应用程序，浏览网页。

```
用户：帮我填一下这个表格
LLM：
  1. 先截图看一下表格长什么样
  2. 分析表格结构
  3. 操作鼠标点击第一个输入框
  4. 从文件中读取数据
  5. 用键盘输入数据
  6. 点击提交按钮
```

**为什么这种演进是必然的？**

因为**任务的复杂性要求越来越强**：

| 任务类型 | 工具调用能否完成？ | Computer Use能否完成？ |
|----------|------------------|---------------------|
| 查天气 | ✅ | ✅ |
| 填表格 | ❌ | ✅ |
| 自动化测试 | ❌ | ✅ |
| 写代码并调试 | 部分 | ✅ |
| 跨应用数据迁移 | ❌ | ✅ |

当任务需要**多步骤、多工具协调、实时视觉反馈**时，传统工具调用就力不从心了。

### 什么是Computer Use？

Computer Use（计算机使用）是Anthropic在2024年推出的一项突破性能力。它让Claude能够：

1. **查看屏幕内容** - 截取屏幕截图，理解UI布局
2. **操作鼠标** - 点击、拖拽、悬停
3. **操作键盘** - 输入文本、按下快捷键
4. **打开关闭应用** - 启动程序、关闭窗口
5. **浏览网页** - 导航、点击链接、填写表单

**这意味着什么？**

意味着Claude不再只是一个"能对话的程序"，而是进化成了一个**能像人一样操作计算机的智能助手**。

---

## 6.2 Computer Use原理解析

### 整体工作流程

Computer Use的核心是一个**观察-决策-执行循环**：

```
┌─────────────────────────────────────────────────────────────────┐
│                      Computer Use 循环                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   ┌──────────────┐                                               │
│   │  1. 观察     │  ← Claude截取屏幕截图，理解当前状态            │
│   └──────┬───────┘                                               │
│          │                                                       │
│          ▼                                                       │
│   ┌──────────────┐                                               │
│   │  2. 决策     │  ← 基于观察结果，决定下一步行动                 │
│   └──────┬───────┘                                               │
│          │                                                       │
│          ▼                                                       │
│   ┌──────────────┐                                               │
│   │  3. 执行     │  ← 执行鼠标/键盘操作                          │
│   └──────┬───────┘                                               │
│          │                                                       │
│          └───────────────────────────────────────┐               │
│                                                  │               │
│                     循环直到任务完成              │               │
│                                                  │               │
└──────────────────────────────────────────────────────────────────┘
```

### 为什么需要"观察-决策-执行"循环？

**答案：LLM无法直接"看到"计算机状态**

传统的工具调用是**确定性的**：

```python
# 工具调用：输入确定，输出确定
result = get_weather(city="北京")
# 要么成功返回天气，要么抛出异常
```

但计算机操作是**非确定性的**：

```
场景：点击"提交"按钮
问题：
- 按钮真的在那个位置吗？
- 按钮是否被其他窗口遮挡？
- 点击后会发生什么？
- 如果按钮不存在怎么办？
```

所以Claude需要：
1. **先观察** - 截图看看当前屏幕状态
2. **再决策** - 基于观察决定操作
3. **后执行** - 执行操作
4. **再观察** - 验证操作效果

**这种循环让Claude能够应对各种意外情况**，就像人类操作计算机一样——先看看，再操作，再看看效果。

### 核心技术组件

Computer Use由以下几个核心组件构成：

```python
class ComputerUseConfig:
    """
    Computer Use 的核心配置
    
    为什么要这些配置？
    每个配置都对应着一个现实问题
    """
    
    display_size: tuple = (1920, 1080)
    # 问题：Claude如何知道屏幕有多大？
    # 答案：通过display_size指定屏幕分辨率
    
    available_terminals: list = ["bash", "zsh", "powershell"]
    # 问题：Claude能在哪些环境中执行命令？
    # 答案：通过available_terminals指定可用的终端
    
    max_actions_per_turn: int = 10
    # 问题：一次循环中最多执行多少操作？
    # 答案：限制max_actions_per_turn防止失控
    
    screenshot_delay_ms: int = 100
    # 问题：执行操作后需要等多久才能截图？
    # 答案：等待UI更新完成后再截图
```

---

## 6.3 Claude Code架构与设计

### Claude Code是什么？

Claude Code是Anthropic官方推出的命令行工具，让开发者能够在终端中与Claude交互。它不仅仅是另一个CLI工具——它是**Computer Use能力的官方载体**。

**为什么Claude要推出自己的CLI工具？**

这里有一个深层次的原因：**工具调用的局限性**

当开发者想让Claude帮助写代码时，工具调用面临以下问题：

| 问题 | 描述 | 后果 |
|------|------|------|
| 上下文丢失 | 新会话无法保留之前的决策 | Claude反复问相同问题 |
| 工具碎片化 | 每个IDE插件各自实现 | 体验不一致 |
| 安全边界模糊 | 难以控制Claude能做什么 | 风险不可控 |

Claude Code通过**深度集成**解决了这些问题：

```python
# Claude Code的核心理念
principles = {
    "continuous_context": "整个开发会话的上下文持久保持",
    "unified_tools": "统一的文件操作、Git、终端工具",
    "explicit_consent": "敏感操作需要用户确认",
    "transparent_actions": "所有操作都记录日志"
}
```

### Claude Code的核心功能

**1. 智能代码生成**

```bash
# 在终端中启动Claude Code
claude

# 简单的代码生成请求
claude "写一个快速排序算法"

# 复杂的项目级请求
claude "帮我重构这个React项目，使用TypeScript"
```

**2. Git操作集成**

```bash
# 让Claude帮你写commit message
claude "commit current changes"

# 让Claude帮你分析PR
claude "review this pull request"

# 让Claude帮你处理merge conflict
claude "resolve the merge conflict in src/app.tsx"
```

**3. 终端命令执行**

```bash
# Claude可以执行终端命令
claude "run the tests and fix any failures"

# Claude可以安装依赖
claude "install the required npm packages"
```

**4. 多文件编辑**

```bash
# Claude可以同时修改多个文件
claude """
创建以下文件：
- src/api/users.ts - 用户API模块
- src/api/posts.ts - 文章API模块
- src/types/index.ts - 类型定义
"""
```

### Claude Code vs 传统IDE插件

| 特性 | 传统IDE插件 | Claude Code |
|------|------------|-------------|
| 上下文保持 | 差（每次都是新会话） | 强（整个会话持久） |
| 工具一致性 | 差（各插件实现不同） | 强（统一工具集） |
| 安全控制 | 弱 | 强（明确授权机制） |
| 跨项目能力 | 弱 | 强（能跨项目工作） |
| 学习曲线 | 各插件不同 | 统一体验 |

---

## 6.4 安全机制与沙箱环境

### 为什么要这么强调安全？

Computer Use能力的危险性很容易理解：**如果LLM能像人一样操作计算机，它就能执行任何操作——包括删除文件、发送邮件、甚至泄露数据。**

这就引出了一个根本问题：

> **我们如何让Claude变得有用，同时又不让它变得危险？**

### Anthropic的安全策略

Anthropic采用了**多层防御策略**：

**第一层：明确授权（Explicit Consent）**

```python
class ConsentManager:
    """
    consent_level决定了Claude能做什么
    
    为什么需要分层？
    不同任务需要不同的信任级别
    """
    
    levels = {
        "read_only": {
            "description": "只读模式",
            "allowed": ["read_file", "search", "browse"],
            "denied": ["write_file", "execute", "delete"]
        },
        "read_write": {
            "description": "读写模式",
            "allowed": ["read_file", "write_file", "search", "browse"],
            "denied": ["execute", "delete", "send_email"]
        },
        "full_access": {
            "description": "完全访问",
            "allowed": ["*"],  # 所有操作
            "requires_confirmation": ["delete", "send_email", "execute"]
        }
    }
```

**第二层：沙箱环境（Sandbox）**

```python
class SandboxConfig:
    """
    沙箱配置
    
    为什么需要沙箱？
    即使Claude出错，也只会影响沙箱内的模拟环境
    """
    
    sandbox_type = "docker"  # Docker容器隔离
    network_isolation = True   # 网络隔离
    filesystem_boundary = "/workspace/sandbox"  # 文件系统边界
    cpu_limit = "2 cores"     # CPU限制
    memory_limit = "4GB"      # 内存限制
```

**第三层：操作日志（Audit Log）**

```python
class AuditLogger:
    """
    操作日志
    
    为什么需要日志？
    1. 问题追溯：如果出了问题，能知道发生了什么
    2. 信任建立：用户可以看到Claude在做什么
    3. 合规要求：某些行业必须保留操作记录
    """
    
    def log_action(self, action: dict):
        entry = {
            "timestamp": datetime.now().isoformat(),
            "action_type": action["type"],
            "target": action["target"],
            "parameters": action.get("params", {}),
            "result": action.get("result", "pending"),
            "consent_level": self.current_consent_level
        }
        self.log_file.write(json.dumps(entry) + "\n")
```

**第四层：实时监控（Human-in-the-Loop）**

```python
class HumanOversight:
    """
    人工监督机制
    
    核心思想：关键操作需要人工确认
    """
    
    HIGH_RISK_ACTIONS = [
        "delete_files",
        "send_emails",
        "make_purchases",
        "push_to_production",
        "modify_security_settings"
    ]
    
    def requires_confirmation(self, action: dict) -> bool:
        """
        判断操作是否需要确认
        """
        return action["type"] in self.HIGH_RISK_ACTIONS
    
    async def request_confirmation(self, action: dict) -> bool:
        """
        请求用户确认
        返回True表示用户批准，False表示拒绝
        """
        print(f"⚠️ Claude想要执行高风险操作：{action['type']}")
        print(f"目标：{action.get('target', 'N/A')}")
        response = input("是否允许？(y/n): ")
        return response.lower() == 'y'
```

### 开发者的安全实践

作为开发者，我们应该如何安全地使用Computer Use？

```python
class SafeComputerUse:
    """
    安全使用Computer Use的最佳实践
    """
    
    @staticmethod
    def create_limited_session(config: dict) -> dict:
        """
        创建受限会话
        
        最佳实践1：最小权限原则
        只给Claude它需要的权限，不要给多了
        """
        return {
            "consent_level": "read_only",  # 除非必要，不用更高权限
            "allowed_paths": ["/workspace/project"],  # 只允许访问项目目录
            "denied_paths": [
                "/etc",           # 系统配置
                "/home/*/.ssh",   # SSH密钥
                "/var/secrets"    # 敏感信息
            ],
            "max_actions_per_turn": 5,  # 限制单次操作数
            "enable_audit_log": True     # 开启日志
        }
    
    @staticmethod
    def validate_target(target: str, allowed_paths: list) -> bool:
        """
        验证操作目标是否在允许范围内
        
        最佳实践2：路径验证
        在执行任何文件操作前，验证路径是否安全
        """
        import os
        real_path = os.path.realpath(target)
        
        for allowed in allowed_paths:
            allowed_real = os.path.realpath(allowed)
            if real_path.startswith(allowed_real):
                return True
        
        return False
```

---

## 6.5 开发实战：构建自动化脚本

### 场景：自动填表机器人

让我们通过一个实际例子来学习如何构建基于Computer Use的自动化脚本。

**场景描述**：我们需要让Claude帮助填写一个网页表单。

```python
import asyncio
from anthropic import Anthropic
from computer_use import ComputerUse

class FormFillingBot:
    """
    自动填表机器人
    
    为什么需要这个类？
    封装常见操作，提供高级API
    """
    
    def __init__(self, consent_level: str = "read_write"):
        self.client = Anthropic()
        self.computer = ComputerUse(consent_level=consent_level)
        self.task_history = []  # 记录操作历史
    
    async def fill_form(self, form_url: str, form_data: dict):
        """
        填写表单的主要流程
        
        为什么分步骤？
        1. 便于调试 - 出问题能快速定位
        2. 便于重试 - 失败的操作可以单独重试
        3. 便于日志 - 详细记录每一步
        """
        try:
            # 步骤1：打开表单页面
            await self._navigate_to_form(form_url)
            
            # 步骤2：分析表单结构
            form_structure = await self._analyze_form()
            
            # 步骤3：逐个填写字段
            for field_name, value in form_data.items():
                await self._fill_field(field_name, value)
            
            # 步骤4：提交表单
            await self._submit_form()
            
            return {"success": True, "steps_completed": len(self.task_history)}
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "steps_completed": self.task_history
            }
    
    async def _navigate_to_form(self, url: str):
        """导航到表单页面"""
        # 1. 先截一张图确认当前位置
        screenshot = await self.computer.screenshot()
        
        # 2. 打开新标签页（Ctrl+T）
        await self.computer.keyboard.press("ctrl+t")
        
        # 3. 输入URL
        await self.computer.keyboard.type(url)
        
        # 4. 按回车
        await self.computer.keyboard.press("enter")
        
        # 5. 等待页面加载
        await asyncio.sleep(2)
        
        # 6. 再次截图确认页面已加载
        await self.computer.screenshot()
        
        self.task_history.append({
            "step": "navigate",
            "url": url
        })
    
    async def _analyze_form(self) -> dict:
        """分析表单结构"""
        # 截取当前屏幕
        screenshot = await self.computer.screenshot()
        
        # 让Claude分析截图中的表单字段
        analysis_prompt = """
        请分析这个截图中的表单结构。
        返回JSON格式，包含：
        - fields: 字段列表，每个字段包含name、type、position
        - submit_button: 提交按钮的位置
        """
        
        response = self.client.messages.create(
            model="claude-opus-4-20241120",
            max_tokens=1024,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "image", "source": screenshot},
                    {"type": "text", "text": analysis_prompt}
                ]
            }]
        )
        
        return self._parse_form_analysis(response.content[0].text)
    
    async def _fill_field(self, field_name: str, value: str):
        """填写单个字段"""
        # 1. 点击字段位置
        # （实际实现中需要根据_analyze_form的结果确定位置）
        await self.computer.mouse.click(x=field_name["x"], y=field_name["y"])
        
        # 2. 输入内容
        await self.computer.keyboard.type(value)
        
        # 3. 按Tab跳到下一个字段
        await self.computer.keyboard.press("tab")
        
        self.task_history.append({
            "step": "fill_field",
            "field": field_name,
            "value": value
        })
    
    async def _submit_form(self):
        """提交表单"""
        # 点击提交按钮
        # （实际实现中需要根据_analyze_form的结果确定位置）
        await self.computer.mouse.click(x="submit_x", y="submit_y")
        
        # 等待提交完成
        await asyncio.sleep(3)
        
        # 截图确认提交结果
        result_screenshot = await self.computer.screenshot()
        
        self.task_history.append({
            "step": "submit",
            "screenshot": result_screenshot
        })
```

### 场景：自动化测试助手

```python
class TestingAssistant:
    """
    自动化测试助手
    
    使用Computer Use执行UI测试
    """
    
    def __init__(self, app_url: str):
        self.app_url = app_url
        self.computer = ComputerUse()
        self.test_results = []
    
    async def run_ui_test(self, test_case: dict) -> dict:
        """
        执行UI测试
        
        测试流程：
        1. 打开应用
        2. 执行测试操作
        3. 验证结果
        4. 记录测试报告
        """
        test_id = test_case["id"]
        steps = test_case["steps"]
        expected = test_case["expected"]
        
        try:
            # 打开应用
            await self._open_application()
            
            # 执行测试步骤
            for step in steps:
                await self._execute_step(step)
            
            # 验证结果
            actual = await self._capture_result()
            
            # 比对结果
            passed = self._compare_results(expected, actual)
            
            result = {
                "test_id": test_id,
                "status": "passed" if passed else "failed",
                "expected": expected,
                "actual": actual,
                "screenshots": self.test_results
            }
            
            self.test_results.append(result)
            return result
        
        except Exception as e:
            return {
                "test_id": test_id,
                "status": "error",
                "error": str(e)
            }
    
    async def _open_application(self):
        """打开测试应用"""
        await self.computer.browser.open(self.app_url)
        await asyncio.sleep(2)  # 等待页面加载
    
    async def _execute_step(self, step: dict):
        """执行单个测试步骤"""
        action = step["action"]
        
        if action == "click":
            await self.computer.mouse.click(x=step["x"], y=step["y"])
        elif action == "type":
            await self.computer.keyboard.type(step["text"])
        elif action == "select":
            await self.computer.mouse.click(x=step["x"], y=step["y"])
            await self.computer.keyboard.press("down")
            await self.computer.keyboard.press("enter")
        
        await asyncio.sleep(step.get("delay", 1))
        
        # 每步都截图记录
        await self.computer.screenshot()
    
    async def _capture_result(self) -> dict:
        """捕获测试结果"""
        screenshot = await self.computer.screenshot()
        
        # 让Claude分析截图中的关键信息
        return {"screenshot": screenshot}
    
    def _compare_results(self, expected: dict, actual: dict) -> bool:
        """比对测试结果"""
        # 实际实现中需要根据具体测试类型比对
        return True
```

---

## 6.6 最佳实践与注意事项

### 最佳实践

**1. 从简单任务开始**

```python
# ✅ 好：先从简单操作开始
simple_tasks = [
    "打开浏览器访问 example.com",
    "截取当前屏幕",
    "在文本框输入 Hello World"
]

# ❌ 差：一开始就尝试复杂流程
complex_tasks = [
    "自动登录邮箱，查找特定邮件，提取附件，上传到云存储"
]
```

**原因**：简单任务容易验证和调试，能帮你快速理解Claude的行为模式。

**2. 总是验证操作结果**

```python
async def safe_click(x, y):
    """
    安全点击
    
    为什么需要验证？
    确保点击生效了
    """
    # 点击前截图
    before = await computer.screenshot()
    
    # 执行点击
    await computer.mouse.click(x, y)
    
    # 等待UI更新
    await asyncio.sleep(0.5)
    
    # 点击后截图
    after = await computer.screenshot()
    
    # 验证发生了变化
    if before == after:
        raise Exception("点击似乎没有生效，请检查")
    
    return after
```

**3. 实现超时和重试机制**

```python
async def execute_with_retry(action, max_retries=3, timeout=10):
    """
    带重试的操作执行
    
    为什么需要重试？
    1. 网络可能不稳定
    2. UI响应可能延迟
    3. 临时性的环境问题
    """
    for attempt in range(max_retries):
        try:
            return await asyncio.wait_for(action(), timeout=timeout)
        except TimeoutError:
            if attempt == max_retries - 1:
                raise
            await asyncio.sleep(1)  # 重试前等待
```

### 常见错误与解决方案

| 错误 | 原因 | 解决方案 |
|------|------|----------|
| 截图是空白的 | 页面还在加载 | 增加等待时间 |
| 点击位置不对 | 分辨率不匹配 | 使用相对坐标或百分比 |
| 操作超时 | 应用无响应 | 添加超时检测 |
| 循环无法结束 | 缺乏终止条件 | 设置明确的结束标志 |

### 适用场景判断

**适合使用Computer Use的场景**：

| 场景 | 原因 |
|------|------|
| 跨应用自动化 | 没有API，只能操作UI |
| 遗留系统测试 | 老系统无法接入现代工具 |
| 动态UI交互 | UI是动态生成的，无法预先定义 |
| 复杂表单填写 | 表单结构复杂，需要实时理解 |

**不适合使用Computer Use的场景**：

| 场景 | 替代方案 |
|------|----------|
| 纯数据处理 | 使用API或脚本 |
| 定期批量任务 | 使用Cron + 脚本 |
| 高精度操作 | 使用专用API |
| 敏感操作 | 人工执行 |

---

## 本章总结

### 核心知识点

| 知识点 | 掌握程度 | 关键点 |
|--------|----------|--------|
| 演进路径 | ⭐⭐⭐⭐⭐ | 为什么需要Computer Use |
| 工作原理 | ⭐⭐⭐⭐⭐ | 观察-决策-执行循环 |
| Claude Code | ⭐⭐⭐⭐ | 官方CLI工具的能力 |
| 安全机制 | ⭐⭐⭐⭐⭐ | 多层防御保护 |
| 开发实战 | ⭐⭐⭐⭐ | 填表机器人、测试助手 |
| 最佳实践 | ⭐⭐⭐⭐⭐ | 安全、验证、重试 |

### 关键设计思想

| 设计思想 | 为什么重要 |
|----------|-----------|
| 观察-决策-执行循环 | 非确定性环境需要反馈机制 |
| 多层安全防御 | 能力越强，风险越大 |
| 最小权限原则 | 只给必要的权限 |
| 人工监督 | 关键操作需要人工确认 |

### 下一步

- 继续阅读：Agent架构专题（七）- 了解多Agent协作系统
- 实践项目：用Computer Use构建一个自动化测试工具
- 参考资料：[Anthropic Computer Use文档](https://docs.anthropic.com/)

---

**文档元信息**
难度：⭐⭐⭐⭐ | 类型：专家设计 | 更新日期：2026-03-25 | 预计阅读时间：50分钟 | 字数：约6000字
