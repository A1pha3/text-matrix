---
title: "Mini-Coding-Agent 源码深度解析：Sebastian Raschka 的代码代理第一性原理"
date: 2026-04-07T01:05:00+08:00
slug: "mini-coding-agent-sebastian-raschka-source-code-guide"
description: "深入源码解读 Sebastian Raschka 的 Mini-Coding-Agent，详解六大核心组件（Live Context、Prompt Cache、Structured Tools、Context Reduction、Memory、Delegation）的第一性原理，650行代码揭示代码代理的本质，附完整代码注释和流程图。"
draft: false
categories: ["技术笔记"]
tags: ["代码代理", "AI Agent", "源码解析", "Sebastian Raschka", "Ollama", "Python", "LLM", "自主编程", "工具调用", "上下文管理"]
---

## 学习目标

通过本文，你将深入掌握以下核心能力：

- 理解代码代理的六大核心组件的第一性原理
- 深入理解 WorkspaceContext 如何构建实时仓库上下文
- 掌握 Prompt Shape 如何实现缓存复用和计算节省
- 理解 Structured Tools 的设计模式和批准机制
- 掌握 Context Reduction 的去重和截断策略
- 理解 Transcripts 和 Memory 的持久化设计
- 掌握 Delegation 子代理的受限作用域机制
- 从 ~650 行精简代码中领悟 AI Agent 的本质

---

## 1. 项目概述与架构总览

### 1.1 为什么选择 Mini-Coding-Agent

Sebastian Raschka 明确指出：这是一个**教学示范项目**，不是生产级代理。它的价值在于：

| 特性 | 说明 |
|------|------|
| **代码量** | 仅 ~650 行 Python（vs LangChain 的 ~10 万行） |
| **可读性** | 每个组件 < 50 行，核心逻辑一目了然 |
| **完整性** | 涵盖代码代理的 6 大核心组件 |
| **实用性** | 可实际运行，处理真实编程任务 |

### 1.2 六大组件与代码映射

```python
##############################
#### Six Agent Components ####
##############################
# 1) Live Repo Context -> WorkspaceContext
# 2) Prompt Shape And Cache Reuse -> build_prefix, memory_text, prompt
# 3) Structured Tools, Validation, And Permissions -> build_tools, run_tool, validate_tool
# 4) Context Reduction And Output Management -> clip, history_text
# 5) Transcripts, Memory, And Resumption -> SessionStore, record, note_tool
# 6) Delegation And Bounded Subagents -> tool_delegate
```

这是代码中直接注释的六大组件映射关系。

### 1.3 核心类图

```
┌─────────────────────────────────────────────────────────────┐
│                      MiniAgent                               │
│  ┌─────────────────────────────────────────────────────┐  │
│  │ 1. WorkspaceContext.build() → 实时仓库上下文           │  │
│  │ 2. build_prefix() + prompt() → 提示构建与缓存复用    │  │
│  │ 3. build_tools() + run_tool() → 工具系统与批准       │  │
│  │ 4. history_text() → 上下文缩减                       │  │
│  │ 5. SessionStore + record() → 会话持久化               │  │
│  │ 6. tool_delegate() → 子代理委托                      │  │
│  └─────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. 组件一：Live Repo Context（实时仓库上下文）

### 2.1 WorkspaceContext 类

```python
class WorkspaceContext:
    def __init__(self, cwd, repo_root, branch, default_branch,
                 status, recent_commits, project_docs):
        self.cwd = cwd
        self.repo_root = repo_root
        self.branch = branch
        self.default_branch = default_branch
        self.status = status
        self.recent_commits = recent_commits
        self.project_docs = project_docs
```

### 2.2 构建过程

```python
@classmethod
def build(cls, cwd):
    cwd = Path(cwd).resolve()

    def git(args, fallback=""):
        # 调用 git 命令获取信息
        result = subprocess.run(
            ["git", *args], cwd=cwd, capture_output=True,
            text=True, check=True, timeout=5,
        )
        return result.stdout.strip() or fallback

    repo_root = Path(git(["rev-parse", "--show-toplevel"], str(cwd))).resolve()

    # 读取项目文档
    docs = {}
    for base in (repo_root, cwd):
        for name in DOC_NAMES:
            path = base / name
            if not path.exists():
                continue
            key = str(path.relative_to(repo_root))
            if key in docs:
                continue
            docs[key] = clip(path.read_text(...), 1200)

    return cls(
        cwd=str(cwd),
        repo_root=str(repo_root),
        branch=git(["branch", "--show-current"], "-") or "-",
        default_branch=...,
        status=clip(git(["status", "--short"], "clean"), 1500),
        recent_commits=[line for line in git(["log", "--oneline", "-5"]).splitlines() if line],
        project_docs=docs,
    )
```

### 2.3 收集的信息类型

| 信息 | 获取方式 | 示例 |
|------|----------|------|
| **cwd** | `Path.cwd()` | `/home/user/project` |
| **repo_root** | `git rev-parse --show-toplevel` | `/home/user/project` |
| **branch** | `git branch --show-current` | `main` |
| **default_branch** | `git symbolic-ref --short origin/HEAD` | `main` |
| **status** | `git status --short` | `M README.md` |
| **recent_commits** | `git log --oneline -5` | `abc123 fix: typo` |
| **project_docs** | 读取文件 | README.md, pyproject.toml 等 |

### 2.4 WorkspaceContext.text() 输出格式

```python
def text(self):
    commits = "\n".join(f"- {line}" for line in self.recent_commits) or "- none"
    docs = "\n".join(f"- {path}\n{snippet}"
                       for path, snippet in self.project_docs.items()) or "- none"
    return f"""
Workspace:
  - cwd: {self.cwd}
  - repo_root: {self.repo_root}
  - branch: {self.branch}
  - default_branch: {self.default_branch}
  - status: {self.status}
  - recent_commits: {commits}
  - project_docs: {docs}
"""
```

---

## 3. 组件二：Prompt Shape 与缓存复用

### 3.1 三段式 Prompt 结构

```python
def prompt(self, user_message):
    return f"""
{self.prefix}           ← 静态部分（不变）
{memory_text()}         ← 记忆部分（变化慢）
Transcript:             ← 历史部分（持续增长）
{history_text()}
Current user request: {user_message}  ← 动态部分
""".strip()
```

### 3.2 build_prefix() 的静态提示词

```python
def build_prefix(self):
    tool_lines = []
    for name, tool in self.tools.items():
        fields = ", ".join(f"{key}: {value}"
                         for key, value in tool["schema"].items())
        risk = "approval required" if tool["risky"] else "safe"
        tool_lines.append(
            f"- {name}({fields}) [{risk}] {tool['description']}"
        )
    tool_text = "\n".join(tool_lines)

    examples = """
        <tool>{"name":"list_files","args":{"path":"."}}</tool>
        <tool>{"name":"read_file","args":{"path":"README.md","start":1,"end":80}}</tool>
        <final>Done.</final>
    """

    return f"""
You are Mini-Coding-Agent, a small local coding agent running through Ollama.

Rules:
- Use tools instead of guessing about the workspace.
- Return exactly one <tool>...</tool> or one <final>...</final>.
- Tool calls must look like: <tool>{{"name":"tool_name","args":{{...}}}}</tool>
- ...

Tools:
{tool_text}

{self.workspace.text()}
""".strip()
```

### 3.3 缓存复用的关键洞察

**核心洞察**：将 Prompt 分为静态部分和动态部分。

| 部分 | 内容 | 变化频率 |
|------|------|----------|
| **Static Prefix** | 系统指令、工具定义、仓库上下文 | 每会话仅构建一次 |
| **Memory** | 当前任务、已访问文件、笔记 | 变化慢 |
| **History** | 对话历史 | 每次交互增长 |
| **User Message** | 用户请求 | 每次交互变化 |

```python
# 静态前缀在 __init__ 中构建，仅一次
self.prefix = self.build_prefix()

# 动态部分在每次 ask() 时构建
def prompt(self, user_message):
    return f"{self.prefix} {self.memory_text()} Transcript: {history_text()} ..."
```

---

## 4. 组件三：Structured Tools 与安全批准

### 4.1 工具定义结构

```python
def build_tools(self):
    tools = {
        "list_files": {
            "schema": {"path": "str='.'"},
            "risky": False,
            "description": "List files in the workspace.",
            "run": self.tool_list_files,
        },
        "read_file": {
            "schema": {"path": "str", "start": "int=1", "end": "int=200"},
            "risky": False,
            "description": "Read a UTF-8 file by line range.",
            "run": self.tool_read_file,
        },
        "write_file": {
            "schema": {"path": "str", "content": "str"},
            "risky": True,  # 危险操作！
            "description": "Write a text file.",
            "run": self.tool_write_file,
        },
        "run_shell": {
            "schema": {"command": "str", "timeout": "int=20"},
            "risky": True,  # 危险操作！
            "description": "Run a shell command in the repo root.",
            "run": self.tool_run_shell,
        },
        # ...
    }
    return tools
```

### 4.2 三种批准模式

```python
def approve(self, name, args):
    if self.read_only:
        return False
    if self.approval_policy == "auto":
        return True   # 自动批准
    if self.approval_policy == "never":
        return False  # 始终拒绝
    # ask 模式：交互式确认
    try:
        answer = input(f"approve {name} {json.dumps(args)}? [y/N] ")
    except EOFError:
        return False
    return answer.strip().lower() in {"y", "yes"}
```

| 模式 | 行为 | 适用场景 |
|------|------|----------|
| `auto` | 自动批准所有操作 | 可信代码库、实验 |
| `never` | 拒绝所有危险操作 | 严格安全环境 |
| `ask` | 交互式确认 | 日常使用（默认） |

### 4.3 路径验证防止逃逸

```python
def path(self, raw_path):
    path = Path(raw_path)
    path = path if path.is_absolute() else self.root / path
    resolved = path.resolve()

    # 核心安全检查：确保路径在 workspace 内
    if not self.path_is_within_root(resolved):
        raise ValueError(f"path escapes workspace: {raw_path}")
    return resolved

def path_is_within_root(self, resolved):
    probe = resolved
    while not probe.exists() and probe.parent != probe:
        probe = probe.parent
    for candidate in (probe, *probe.parents):
        try:
            if candidate.samefile(self.root):
                return True
        except OSError:
            continue
    return False
```

---

## 5. 组件四：Context Reduction（上下文缩减）

### 5.1 history_text() 的去重策略

```python
def history_text(self):
    history = self.session["history"]
    if not history:
        return "- empty"

    lines = []
    seen_reads = set()  # 去重集合
    recent_start = max(0, len(history) - 6)

    for index, item in enumerate(history):
        recent = index >= recent_start

        # 写操作清除路径的去重记录
        if item["role"] == "tool" and item["name"] in ("write_file", "patch_file"):
            path = str(item["args"].get("path", ""))
            seen_reads.discard(path)

        # 非最近的读取操作去重
        if (item["role"] == "tool"
            and item["name"] == "read_file"
            and not recent):
            path = str(item["args"].get("path", ""))
            if path in seen_reads:
                continue  # 跳过重复读取
            seen_reads.add(path)

        # 根据角色和是否最近决定截断长度
        if item["role"] == "tool":
            limit = 900 if recent else 180
            lines.append(f"[tool:{item['name']}] {json.dumps(item['args'])}")
            lines.append(clip(item["content"], limit))
        else:
            limit = 900 if recent else 220
            lines.append(f"[{item['role']}] {clip(item['content'], limit)}")

    return clip("\n".join(lines), MAX_HISTORY)
```

### 5.2 clip() 截断函数

```python
MAX_TOOL_OUTPUT = 4000
MAX_HISTORY = 12000

def clip(text, limit=MAX_TOOL_OUTPUT):
    text = str(text)
    if len(text) <= limit:
        return text
    return text[:limit] + f"\n...[truncated {len(text) - limit} chars]"
```

### 5.3 去重逻辑图解

```
历史操作序列：
[1] read_file("src/main.py")     → 加入 seen_reads
[2] read_file("src/main.py")     → 跳过（已存在）
[3] read_file("src/utils.py")   → 加入 seen_reads
[4] write_file("src/main.py")   → 从 seen_reads 移除
[5] read_file("src/main.py")     → 读取（已清除）
```

---

## 6. 组件五：Transcripts 与 Memory（会话持久化）

### 6.1 SessionStore 类

```python
class SessionStore:
    def __init__(self, root):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def path(self, session_id):
        return self.root / f"{session_id}.json"

    def save(self, session):
        path = self.path(session["id"])
        path.write_text(json.dumps(session, indent=2))
        return path

    def load(self, session_id):
        return json.loads(self.path(session_id).read_text())

    def latest(self):
        files = sorted(self.root.glob("*.json"),
                      key=lambda path: path.stat().st_mtime)
        return files[-1].stem if files else None
```

### 6.2 会话数据结构

```python
session = {
    "id": "20260407-143022-a1b2c3",  # 时间戳 + UUID
    "created_at": "2026-04-07T06:30:22+00:00",
    "workspace_root": "/home/user/project",
    "history": [
        {"role": "user", "content": "Add CLI entry point",
         "created_at": "..."},
        {"role": "tool", "name": "read_file",
         "args": {"path": "pyproject.toml"},
         "content": "[tool:read_file] ...", "created_at": "..."},
        # ...
    ],
    "memory": {
        "task": "Add CLI entry point with --help",
        "files": ["pyproject.toml", "src/cli.py"],
        "notes": ["使用 click 库"]
    }
}
```

### 6.3 记忆更新机制

```python
def note_tool(self, name, args, result):
    memory = self.session["memory"]
    path = args.get("path")

    # 追踪已访问文件（用于上下文）
    if name in {"read_file", "write_file", "patch_file"} and path:
        self.remember(memory["files"], str(path), 8)

    # 记录关键信息
    note = f"{name}: {clip(str(result).replace(chr(10), ' '), 220)}"
    self.remember(memory["notes"], note, 5)

@staticmethod
def remember(bucket, item, limit):
    if not item:
        return
    if item in bucket:
        bucket.remove(item)  # 移至末尾（最新）
    bucket.append(item)
    del bucket[:-limit]     # 保留最近 N 条
```

---

## 7. 组件六：Delegation（子代理委托）

### 7.1 委托机制

```python
def tool_delegate(self, args):
    if self.depth >= self.max_depth:
        raise ValueError("delegate depth exceeded")

    task = str(args.get("task", "")).strip()
    if not task:
        raise ValueError("task must not be empty")

    # 创建子代理，继承父代理的上下文
    child = MiniAgent(
        model_client=self.model_client,
        workspace=self.workspace,
        session_store=self.session_store,
        approval_policy="never",  # 子代理不允许危险操作
        max_steps=int(args.get("max_steps", 3)),
        max_new_tokens=self.max_new_tokens,
        depth=self.depth + 1,       # 深度 +1
        max_depth=self.max_depth,      # 最大深度限制
        read_only=True,              # 只读模式
    )

    # 传递任务和部分历史
    child.session["memory"]["task"] = task
    child.session["memory"]["notes"] = [clip(self.history_text(), 300)]

    return "delegate_result:\n" + child.ask(task)
```

### 7.2 深度限制机制

```python
# MiniAgent.__init__ 中
self.depth = depth      # 当前深度
self.max_depth = max_depth  # 最大深度（默认 1）

# 递归终止条件
if self.depth >= self.max_depth:
    raise ValueError("delegate depth exceeded")
```

### 7.3 委托的安全边界

| 属性 | 父代理 | 子代理 |
|------|--------|--------|
| **depth** | 0 | 1 |
| **max_depth** | 1 | 1 |
| **approval_policy** | `ask/auto/never` | `never`（强制） |
| **read_only** | False | True（强制） |
| **max_steps** | 6 | 3（默认） |

---

## 8. 工具实现详解

### 8.1 read_file（带行号读取）

```python
def tool_read_file(self, args):
    path = self.path(args["path"])
    if not path.is_file():
        raise ValueError("path is not a file")

    start = int(args.get("start", 1))
    end = int(args.get("end", 200))
    if start < 1 or end < start:
        raise ValueError("invalid line range")

    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    body = "\n".join(
        f"{number:>4}: {line}"
        for number, line in enumerate(lines[start - 1:end], start=start)
    )
    return f"# {path.relative_to(self.root)}\n{body}"
```

### 8.2 search（带回退的搜索）

```python
def tool_search(self, args):
    pattern = str(args.get("pattern", "")).strip()
    if not pattern:
        raise ValueError("pattern must not be empty")

    path = self.path(args.get("path", "."))

    # 优先使用 ripgrep（更快）
    if shutil.which("rg"):
        result = subprocess.run(
            ["rg", "-n", "--smart-case", "--max-count", "200",
             pattern, str(path)],
            cwd=self.root, capture_output=True, text=True
        )
        return result.stdout.strip() or result.stderr.strip() or "(no matches)"

    # 回退：纯 Python 实现
    matches = []
    for file_path in path.rglob("*"):
        if file_path.is_file():
            for number, line in enumerate(
                    file_path.read_text(encoding="utf-8", errors="replace").splitlines(),
                    start=1):
                if pattern.lower() in line.lower():
                    matches.append(
                        f"{file_path.relative_to(self.root)}:{number}:{line}"
                    )
                    if len(matches) >= 200:
                        return "\n".join(matches)
    return "\n".join(matches) or "(no matches)"
```

### 8.3 patch_file（精确文本替换）

```python
def tool_patch_file(self, args):
    path = self.path(args["path"])
    if not path.is_file():
        raise ValueError("path is not a file")

    old_text = str(args.get("old_text", ""))
    if not old_text:
        raise ValueError("old_text must not be empty")
    if "new_text" not in args:
        raise ValueError("missing new_text")

    text = path.read_text(encoding="utf-8")
    count = text.count(old_text)
    if count != 1:
        raise ValueError(f"old_text must occur exactly once, found {count}")

    path.write_text(text.replace(old_text, str(args["new_text"]), 1),
                   encoding="utf-8")
    return f"patched {path.relative_to(self.root)}"
```

---

## 9. 输出格式解析

### 9.1 XML 工具调用格式

```xml
<!-- 标准 JSON 格式 -->
<tool>{"name":"read_file","args":{"path":"README.md","start":1,"end":80}}</tool>

<!-- XML 风格（多行内容首选） -->
<tool name="write_file" path="src/cli.py"><content>
def main():
    print("Hello")
</content></tool>

<tool name="patch_file" path="src/cli.py"><old_text>
def main():
    print("Hello")
</old_text><new_text>
def main():
    print("Hello, World!")
</new_text></tool>
```

### 9.2 parse() 解析器

```python
@staticmethod
def parse(raw):
    raw = str(raw)

    # 优先匹配 <tool>
    if "<tool>" in raw and ("<final>" not in raw or
                           raw.find("<tool>") < raw.find("<final>")):
        body = MiniAgent.extract(raw, "tool")
        try:
            payload = json.loads(body)
        except Exception:
            return "retry", "model returned malformed tool JSON"
        # ... 验证 payload
        return "tool", payload

    # 匹配 <final>
    if "<final>" in raw:
        final = MiniAgent.extract(raw, "final").strip()
        if final:
            return "final", final

    return "retry", "model returned malformed output"
```

---

## 10. 核心流程：ask() 方法

```python
def ask(self, user_message):
    memory = self.session["memory"]
    if not memory["task"]:
        memory["task"] = clip(user_message.strip(), 300)

    # 1. 记录用户消息
    self.record({"role": "user", "content": user_message,
                 "created_at": now()})

    tool_steps = 0
    attempts = 0
    max_attempts = max(self.max_steps * 3, self.max_steps + 4)

    # 2. 主循环
    while tool_steps < self.max_steps and attempts < max_attempts:
        attempts += 1

        # 3. 调用模型
        raw = self.model_client.complete(
            self.prompt(user_message), self.max_new_tokens)

        # 4. 解析输出
        kind, payload = self.parse(raw)

        if kind == "tool":
            tool_steps += 1
            name = payload.get("name", "")
            args = payload.get("args", {})

            # 5. 执行工具
            result = self.run_tool(name, args)

            # 6. 记录结果
            self.record({
                "role": "tool",
                "name": name,
                "args": args,
                "content": result,
                "created_at": now(),
            })
            self.note_tool(name, args, result)
            continue

        if kind == "final":
            final = (payload or raw).strip()
            self.record({"role": "assistant",
                        "content": final, "created_at": now()})
            self.remember(memory["notes"], clip(final, 220), 5)
            return final

    # 7. 循环终止
    final = f"Stopped after reaching step limit."
    self.record({"role": "assistant", "content": final,
                 "created_at": now()})
    return final
```

---

## 11. OllamaModelClient 实现

```python
class OllamaModelClient:
    def __init__(self, model, host, temperature, top_p, timeout):
        self.model = model
        self.host = host.rstrip("/")
        self.temperature = temperature
        self.top_p = top_p
        self.timeout = timeout

    def complete(self, prompt, max_new_tokens):
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "raw": False,
            "think": False,
            "options": {
                "num_predict": max_new_tokens,
                "temperature": self.temperature,
                "top_p": self.top_p,
            },
        }

        request = urllib.request.Request(
            self.host + "/api/generate",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                data = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Ollama HTTP {exc.code}: {body}")
        except urllib.error.URLError as exc:
            raise RuntimeError(
                "Could not reach Ollama.\n"
                "Make sure `ollama serve` is running.\n"
                f"Host: {self.host}\nModel: {self.model}"
            )

        if data.get("error"):
            raise RuntimeError(f"Ollama error: {data['error']}")

        return data.get("response", "")
```

---

## 12. 总结：代码代理的第一性原理

### 12.1 六大组件的核心价值

| 组件 | 解决的问题 | 核心机制 |
|------|-----------|----------|
| **Live Context** | 代理需要理解工作环境 | Git + 文件系统 |
| **Prompt Cache** | 减少 token 消耗 | 动静分离 |
| **Structured Tools** | 安全、可控的工具调用 | 类型化 Schema + 批准 |
| **Context Reduction** | 上下文无限增长 | 去重 + 截断 |
| **Memory** | 跨会话持久化 | JSON 文件 |
| **Delegation** | 复杂任务分解 | 受限子代理 |

### 12.2 设计哲学

```python
# 极简主义：每个组件 < 50 行
# 可读性优先：避免过度抽象
# 教学导向：代码即文档
```

### 12.3 与生产级框架的差距

| 方面 | Mini-Coding-Agent | LangChain |
|------|-------------------|----------|
| 错误恢复 | 基础重试 | 复杂重试策略 |
| 工具生态 | 6 个内置工具 | 100+ 工具 |
| 多模型 | 仅 Ollama | OpenAI/Anthropic/本地 |
| RAG | 无 | 内置支持 |
| **学习价值** | ⭐⭐⭐⭐⭐ | ⭐⭐ |

### 12.4 适用场景

**适合使用 Mini-Coding-Agent**：
- 学习代码代理原理
- 理解六大组件设计
- 作为自定义代理起点
- 教学演示

**不适合使用**：
- 生产环境
- 需要多模型支持
- 需要复杂工具生态

---

**源码地址**：https://github.com/rasbt/mini-coding-agent
**作者**：Sebastian Raschka
**许可证**：Apache-2.0