#!/usr/bin/env python3
"""Batch fix AI-flavor issues across multiple files."""
import pathlib

fixes = {
    "chatdev-multi-agent-platform-guide.md": [
        ("读完这篇文章，你能回答下面几个问题：", "这篇文章回答以下几个问题："),
    ],
    "baoyu-skills-ai-agent-guide.md": [
        ("完成本文档后，你会了解：", "本文档覆盖以下内容："),
        ("baoyu-skills 无缝集成到 Coding Agent 工作流中：", "baoyu-skills 集成到 Coding Agent 工作流中："),
        ("| **集成** | 与 Coding Agent 无缝 | 需手动复制粘贴 |", "| **集成** | 与 Coding Agent 直接集成 | 需手动复制粘贴 |"),
        ("| **无缝集成** | 与 Coding Agent 工作流融合 |", "| **集成** | 与 Coding Agent 工作流融合 |"),
    ],
    "xiaohongshu-mcp-xiaohongshu-model-context-protocol-guide.md": [
        ("完成本文档后，可以：", "本文档覆盖以下内容："),
    ],
    "trae-agent-llm-agent-guide.md": [
        ("完成本文档后，可以：", "本文档覆盖以下内容："),
    ],
    "squad-ai-agent-team-framework.md": [
        ("Squad 的做法是，不是把 Copilot 当成一个聊天窗口来用在项目里部署一支带角色分工的 AI 团队",
         "Squad 的做法不是把 Copilot 当成一个聊天窗口来用，而是在项目里部署一支带角色分工的 AI 团队"),
    ],
    "smux-tmux-ai-agent-setup.md": [
        ("学完本文后，你将掌握：", "本文覆盖以下内容："),
        ("它不仅仅是给人类用的终端配置，更重要的是**让 AI Agent 能够读、写、控制终端**。",
         "它既是给人类用的终端配置，也**让 AI Agent 能够读、写、控制终端**。"),
    ],
    "self-rationalization-guard-ai-agent-quality-guide.md": [
        ("是，不是惩罚这些冲动**识别它们并做相反的事**：",
         "不是惩罚这些冲动，而是**识别它们并做相反的事**："),
        ("是，不是变慢避免\u201c看起来完成但实际没完成\u201d导致的返工。一次做对比多次返工更快。",
         "不是变慢，而是避免\u201c看起来完成但实际没完成\u201d导致的返工。一次做对比多次返工更快。"),
    ],
}

for filename, replacements in fixes.items():
    filepath = pathlib.Path(filename)
    if not filepath.exists():
        print(f"SKIP (file not found): {filename}")
        continue
    content = filepath.read_text(encoding="utf-8")
    changed = False
    for old, new in replacements:
        if old in content:
            content = content.replace(old, new)
            print(f"FIXED [{filename}]: {old[:50]}...")
            changed = True
        else:
            print(f"SKIP [{filename}]: {old[:50]}...")
    if changed:
        filepath.write_text(content, encoding="utf-8")

print("\nAll done!")
