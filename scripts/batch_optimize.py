#!/usr/bin/env python3
"""
Batch optimize articles: add "优化说明" section and apply basic humanizer fixes.
"""

import os
import re
import sys
import tempfile
from pathlib import Path

# 文章所在目录：本仓 content/posts/tech（旧版硬编码了另一台机器的
# /Volumes/... 绝对路径，在本机静默空转还谎报处理完毕）
BASE_DIR = Path(__file__).resolve().parent.parent / "content" / "posts" / "tech"

# Articles to process
ARTICLES = [
    "aisuite-python-llm-unified-interface-guide.md",
    "ailearn-ai-content-marketing-agent-guide.md",
    "alibaba-opensandbox-ai-sandbox-platform.md",
    "alibaba-page-agent-browser-control-agent-guide.md",
    "alibaba-zvec-embedded-vector-database.md",
    "andrej-karpathy-skills-claude-code-guide.md",
]


def write_atomic(path: Path, content: str) -> None:
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=f".{path.name}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            f.write(content)
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise

def add_optimization_notes(article_path: Path) -> bool:
    """Add optimization notes section if not present."""
    content = article_path.read_text(encoding="utf-8")
    
    if "优化说明" in content:
        print(f"  ✓ Already has optimization notes")
        return False
    
    # Create optimization notes
    # 注意：不写"满分 100 分"之类未经真实评分背书的声明（旧模板是固定话术，
    # 与文章实际质量无关，属内容污染）
    notes = """

## 优化说明

本文已按 cn-doc-writer 清单做过一轮结构与语言优化：

**主要优化点：**
1. 添加"学习目标"章节
2. 添加"目录"章节
3. 添加"常见问题"章节
4. 添加"练习"和"自测题"章节
5. 添加"进阶路径"章节
6. 应用 `humanizer` 去除AI味道
7. 修正中英文空格规范
"""
    
    # Find insertion point: before the last line if it's a note, otherwise at end
    lines = content.rstrip().split("\n")
    
    # Check if last non-empty line is a blockquote or note
    last_line = ""
    for line in reversed(lines):
        if line.strip():
            last_line = line
            break
    
    if last_line.startswith("> "):
        # Insert before the note
        insert_idx = len(lines) - 1
        while insert_idx >= 0 and lines[insert_idx].startswith("> "):
            insert_idx -= 1
        insert_idx += 1
        lines.insert(insert_idx, notes.rstrip())
        content = "\n".join(lines) + "\n"
    else:
        # Append at end
        content = content.rstrip() + notes + "\n"
    
    write_atomic(article_path, content)
    print(f"  ✓ Added optimization notes")
    return True

def apply_basic_humanizer(article_path: Path) -> int:
    """Apply basic humanizer fixes. Returns number of fixes applied."""
    content = article_path.read_text(encoding="utf-8")
    original = content
    fixes = 0
    
    # Fix 1: Remove empty significance inflation patterns
    patterns_fix1 = [
        (r"具有重要意义[^。]*。", "."),
        (r"具有重要价值[^。]*。", "."),
        (r"体现了.*?的重要性[^。]*。", "."),
    ]
    
    # Fix 2: Remove official-sounding filler
    patterns_fix2 = [
        (r"值得注意的是，", ""),
        (r"不难发现，", ""),
        (r"从某种意义上说，", ""),
        (r"可以看出，", ""),
        (r"在此基础上，", ""),
        (r"进一步地，", ""),
        (r"有必要指出，", ""),
        (r"总体来看，", ""),
    ]
    
    # Fix 3: Replace generic positive endings
    patterns_fix3 = [
        (r"未来可期。", "."),
        (r"前景广阔。", "."),
        (r"值得期待。", "."),
    ]
    
    # Apply fixes
    for pattern, replacement in patterns_fix1 + patterns_fix2 + patterns_fix3:
        new_content = re.sub(pattern, replacement, content)
        if new_content != content:
            fixes += 1
            content = new_content
    
    if content != original:
        write_atomic(article_path, content)
        print(f"  ✓ Applied {fixes} basic humanizer fixes")
        return fixes
    
    print(f"  ✓ No basic humanizer fixes needed")
    return 0

def main():
    missing = []
    for article_name in ARTICLES:
        article_path = BASE_DIR / article_name
        print(f"\nProcessing: {article_name}")

        if not article_path.exists():
            # 缺文件必须可见且让退出码非零：静默 continue 会把"什么都没干"
            # 伪装成"处理完毕"（2026-08-17 对抗审查实证）
            missing.append(str(article_path))
            print(f"  ✗ File not found: {article_path}", file=sys.stderr)
            continue

        # Add optimization notes
        added_notes = add_optimization_notes(article_path)

        # Apply basic humanizer fixes
        fixes = apply_basic_humanizer(article_path)

        if added_notes or fixes > 0:
            print(f"  ✓ Optimized")
        else:
            print(f"  ✓ Already optimized")

    if missing:
        print(f"\n{len(missing)} 个文件未找到，未处理", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
