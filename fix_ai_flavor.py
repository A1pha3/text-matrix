#!/usr/bin/env python3
"""Fix AI-flavor in token-tracker-guide.md and slavingia-skills-real-startup-case.md"""
import pathlib

# === token-tracker-guide.md ===
f = pathlib.Path('/Volumes/mini_matrix/github/a1pha3/web/text-matrix/content/posts/tech/tools/token-tracker-guide.md')
content = f.read_text()

replacements = [
    ('\u5b83\u7684\u4ef7\u503c\u4e0d\u662f\u201c\u4f1a\u4e0d\u4f1a\u8bfb\u65e5\u5fd7\u201d\uff0c\u800c\u662f\u201c\u628a\u591a\u5de5\u5177\u89e3\u6790\u3001\u540c\u6b65\u3001\u540e\u53f0\u670d\u52a1\u548c\u5c55\u793a\u9762\u677f\u90fd\u5305\u597d\u4e86\u201d\u3002',
     '\u5b83\u7684\u4ef7\u503c\u5728\u201c\u628a\u591a\u5de5\u5177\u89e3\u6790\u3001\u540c\u6b65\u3001\u540e\u53f0\u670d\u52a1\u548c\u5c55\u793a\u9762\u677f\u90fd\u5305\u597d\u4e86\u201d\uff0c\u4e0d\u662f\u201c\u4f1a\u4e0d\u4f1a\u8bfb\u65e5\u5fd7\u201d\u3002'),
]

for old, new in replacements:
    content = content.replace(old, new)

f.write_text(content)
print('token-tracker done')
