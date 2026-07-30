#!/usr/bin/env python3
"""animate.css 裁剪流水线（text-matrix 专用）。

扫描模板/主题 JS/SCSS 中实际使用的 animate__ 类，
从 LoveIt 主题自带的全量 animate.min.css 提取所需规则（含 :root 变量、
基础类、速度修饰、对应 @keyframes、prefers-reduced-motion 媒体块）。

输出（项目 assets，同路径覆盖主题文件，主题文件不改动）：
  assets/lib/animate/animate.min.css

用法（在项目根目录）：
  /Users/matrix/.workbuddy/binaries/python/envs/default/bin/python scripts/subset_animatecss.py

主题升级 animate.css 版本后重跑本脚本即可。
"""
import glob
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "themes/LoveIt/assets/lib/animate/animate.min.css")
DST = os.path.join(ROOT, "assets/lib/animate/animate.min.css")

CLASS_PAT = re.compile(r"animate__[a-zA-Z0-9_-]+")


def scan_used():
    files = (glob.glob(os.path.join(ROOT, "layouts/**/*.html"), recursive=True)
             + glob.glob(os.path.join(ROOT, "themes/LoveIt/layouts/**/*.html"), recursive=True)
             + glob.glob(os.path.join(ROOT, "themes/LoveIt/assets/js/**/*.js"), recursive=True)
             + glob.glob(os.path.join(ROOT, "themes/LoveIt/assets/css/**/*.scss"), recursive=True)
             + glob.glob(os.path.join(ROOT, "assets/css/**/*.scss"), recursive=True)
             + glob.glob(os.path.join(ROOT, "public/js/*.js"))
             + glob.glob(os.path.join(ROOT, "content/**/*.md"), recursive=True))
    used = set()
    for f in set(files):
        text = open(f, encoding="utf-8", errors="ignore").read()
        used |= set(CLASS_PAT.findall(text))
    return used


def split_rules(css):
    """按大括号配平切分为顶层规则（含 @keyframes/@media 整块）。"""
    rules, start, depth = [], 0, 0
    for i, ch in enumerate(css):
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                rules.append(css[start:i + 1])
                start = i + 1
    return rules


def main():
    used = scan_used()
    print(f"[1/3] 使用中的动画类：{len(used)} 个: {sorted(used)}")

    css = open(SRC, encoding="utf-8").read()
    # 保留文件头许可证注释
    header = re.match(r"^\s*(/\*!.*?\*/)", css, re.S)
    header = header.group(1) if header else ""

    rules = split_rules(css)
    kept, keyframes_needed = [], set()

    for rule in rules:
        brace = rule.find("{")
        prelude, body = rule[:brace], rule[brace + 1:]

        if prelude.startswith("@media"):
            if "prefers-reduced-motion" in prelude:
                kept.append(rule)
            continue
        if prelude.startswith("@keyframes"):
            continue  # 先跳过，稍后按需补回
        if prelude.startswith(":root"):
            kept.append(rule)
            continue

        classes = set(CLASS_PAT.findall(prelude))
        if classes & used:
            kept.append(rule)
            for name in re.findall(r"animation-name:\s*([a-zA-Z0-9_-]+)", body):
                keyframes_needed.add(name)

    # 补回所需的 @keyframes
    keyframes_kept = set()
    for rule in rules:
        brace = rule.find("{")
        prelude = rule[:brace]
        if prelude.startswith("@keyframes"):
            name = prelude[len("@keyframes"):].strip()
            if name in keyframes_needed:
                kept.append(rule)
                keyframes_kept.add(name)

    missing = keyframes_needed - keyframes_kept
    if missing:
        print(f"!! 警告：缺少 keyframes: {sorted(missing)}")

    out = header + "".join(kept)
    os.makedirs(os.path.dirname(DST), exist_ok=True)
    with open(DST, "w", encoding="utf-8") as f:
        f.write(out)

    print(f"[2/3] CSS: {os.path.getsize(SRC)/1024:.1f}KB -> {len(out)/1024:.1f}KB，"
          f"keyframes {sorted(keyframes_kept)}")
    print(f"[3/3] 输出: {os.path.relpath(DST, ROOT)}")
    return 1 if missing else 0


if __name__ == "__main__":
    sys.exit(main())
