#!/usr/bin/env python3
"""fix_fm_newline.py — 修复 frontmatter 结束符与最后字段粘连的文件。

backfill 早期重组丢 \\n,导致 TOML `tags = [...]+++` / YAML `tags: [...]---`
(结束 sep 紧跟字段值,Hugo 解析失败)。本脚本在粘连处补回换行。
幂等:正常 frontmatter(已有换行)不受影响。只动 frontmatter 范围内的 sep。

用法: python3 fix_fm_newline.py [--dry-run]
"""
import sys
from pathlib import Path

TECH = Path(__file__).resolve().parent.parent / "content" / "posts" / "tech"
dry = '--dry-run' in sys.argv
fixed = []
for f in sorted(TECH.glob('*.md')):
    raw = f.read_text(encoding='utf-8')
    first = raw.split('\n', 1)[0]
    if first not in ('---', '+++'):
        continue
    sep = first
    lines = raw.split('\n')
    for i in range(1, min(len(lines), 40)):
        if lines[i] == sep:
            break  # 正常结束(独立 sep 行)
        if lines[i].endswith(sep) and len(lines[i]) > len(sep):
            lines[i] = lines[i][:-len(sep)]  # 去掉末尾粘连的 sep
            lines.insert(i + 1, sep)          # 插入独立 sep 行
            if not dry:
                f.write_text('\n'.join(lines), encoding='utf-8')
            fixed.append(f.name)
            break
mode = 'DRY-RUN' if dry else '已修复'
print(f"{mode}: {len(fixed)} 个粘连文件")
for n in fixed[:12]:
    print(f"  {n}")
