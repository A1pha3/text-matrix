#!/usr/bin/env python3
"""Fix AI-flavor issues in anthropic-knowledge-work-plugins-guide.md"""
import pathlib

filepath = pathlib.Path("anthropic-knowledge-work-plugins-guide.md")
content = filepath.read_text(encoding="utf-8")

# Fix remaining: line 409 abstract phrasing
old = '最有价值的地方是把\u201c岗位经验\u201d变成\u201c可安装、可复用、可迭代\u201d的协作系统。'
new = '把\u201c岗位经验\u201d变成\u201c可安装、可复用、可迭代\u201d的协作系统。'
if old in content:
    content = content.replace(old, new)
    print(f'FIXED: {old[:60]}...')
else:
    print(f'SKIP (not found): {old[:60]}...')

filepath.write_text(content, encoding="utf-8")
print('Done!')
