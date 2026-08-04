#!/usr/bin/env python3
"""Font Awesome 子集化流水线（text-matrix 专用）。

从模板/JS/内容/构建产物中扫描实际使用的 FA 图标类，
从 LoveIt 主题自带的全量 all.min.css 提取所需规则，
并用 fonttools 对 woff2 字体做子集化。

输出（项目 assets，不改动主题文件）：
  assets/lib/fontawesome-free-subset/css/all.min.css
  assets/lib/fontawesome-free-subset/webfonts/{fa-solid-900,fa-regular-400,fa-brands-400}.woff2

用法（在项目根目录）：
  /Users/matrix/.workbuddy/binaries/python/envs/default/bin/python scripts/subset_fontawesome.py

主题升级 FA 版本后重跑本脚本即可。
"""
import glob
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FA_CSS = os.path.join(ROOT, "themes/LoveIt/assets/lib/fontawesome-free/css/all.min.css")
FA_FONTS = os.path.join(ROOT, "themes/LoveIt/assets/lib/fontawesome-free/webfonts")
OUT = os.path.join(ROOT, "assets/lib/fontawesome-free-subset")

# FA 工具/修饰类（不是图标，其规则保留在「基础规则」桶中）
UTILITY = set(
    "fa-spin fa-pulse fa-fw fa-li fa-ul fa-border fa-pull-left fa-pull-right "
    "fa-stack fa-stack-1x fa-stack-2x fa-inverse fa-layers fa-layers-counter "
    "fa-layers-text fa-xs fa-sm fa-lg fa-xl fa-2xl fa-1x fa-2x fa-3x fa-4x "
    "fa-5x fa-6x fa-7x fa-8x fa-9x fa-10x fa-rotate-90 fa-rotate-180 "
    "fa-rotate-270 fa-rotate-by fa-flip-horizontal fa-flip-vertical "
    "fa-flip-both fa-beat fa-bounce fa-fade fa-flip fa-shake fa-sr-only".split()
)

ICON_PAT = re.compile(r"\bfa-[a-z0-9-]+\b")


def scan_inventory():
    """扫描所有可能引用 FA 图标的位置。"""
    sources = [
        glob.glob(os.path.join(ROOT, "layouts/**/*.html"), recursive=True),
        glob.glob(os.path.join(ROOT, "themes/LoveIt/layouts/**/*.html"), recursive=True),
        glob.glob(os.path.join(ROOT, "themes/LoveIt/assets/js/**/*.js"), recursive=True),
        glob.glob(os.path.join(ROOT, "public/js/*.js")),
        glob.glob(os.path.join(ROOT, "public/**/*.html"), recursive=True),
        glob.glob(os.path.join(ROOT, "content/**/*.md"), recursive=True),
    ]
    icons = set()
    for files in sources:
        for f in files:
            try:
                text = open(f, encoding="utf-8", errors="ignore").read()
            except OSError:
                continue
            for m in ICON_PAT.findall(text):
                if m not in UTILITY and not re.match(r"fa-(rotate|flip)-", m):
                    icons.add(m)
    return icons


def split_rules(css):
    """按大括号配平切分压缩 CSS 为顶层规则列表。"""
    rules, start, depth = [], 0, 0
    for i, ch in enumerate(css):
        if ch == "{":
            if depth == 0:
                start_rule = i
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                rules.append(css[start:i + 1])
                start = i + 1
    return rules


def build_subset_css(css, icons):
    """保留基础规则 + 清单内图标规则 + FA7 三个 @font-face。"""
    rules = split_rules(css)
    kept, codepoints = [], set()
    kept_icons = set()

    for rule in rules:
        brace = rule.find("{")
        prelude = rule[:brace]
        body = rule[brace + 1:]

        if prelude.startswith("@font-face"):
            # 只保留 FA7 原生三个族，丢弃 FA5/v4 兼容别名
            if '"Font Awesome 7' in body:
                kept.append(rule)
            continue
        if prelude.startswith("@"):
            kept.append(rule)
            continue

        # FA7 渲染主规则：:is(.fas,.far,...):before{content:var(--fa)/""}
        # 双值 content 语法是现代浏览器渲染图标的唯一入口；
        # 它的类集合（fa-solid/fa-regular 等风格类）不在图标清单里，
        # 若走下方 icons 过滤会被误判为「未使用」而丢弃，导致图标全部不渲染。
        if re.search(r":before\b", prelude) and re.search(r"content:\s*var\(--fa\)", body):
            kept.append(rule)
            continue

        classes = set(re.findall(r"\.(fa-[a-z0-9-]+)", prelude))
        is_icon_rule = ("--fa:" in body or "content:" in body) and classes
        if is_icon_rule and not (classes & icons):
            continue  # 未使用的图标规则，丢弃

        if is_icon_rule:
            kept_icons |= classes & icons
            for cp in re.findall(r'--fa:"\\([0-9a-fA-F]{1,6})"', body):
                codepoints.add(int(cp, 16))
            for cp in re.findall(r'content:"\\([0-9a-fA-F]{1,6})"', body):
                codepoints.add(int(cp, 16))
        kept.append(rule)

    return "".join(kept), codepoints, kept_icons


def subset_font(src, dst, codepoints):
    from fontTools import subset

    opts = subset.Options()
    opts.flavor = "woff2"
    opts.name_IDs = ["*"]  # 保留字体名表，许可证要求
    font = subset.load_font(src, opts)
    ss = subset.Subsetter(opts)
    ss.populate(unicodes=sorted(codepoints))
    ss.subset(font)
    font.save(dst)


def main():
    icons = scan_inventory()
    print(f"[1/3] 图标清单：{len(icons)} 个")

    css = open(FA_CSS, encoding="utf-8").read()
    subset_css, codepoints, kept_icons = build_subset_css(css, icons)
    missing = icons - kept_icons
    if missing:
        print(f"!! 警告：{len(missing)} 个图标在 CSS 中未找到规则: {sorted(missing)}")
    print(f"[2/3] 子集 CSS：{len(css)} -> {len(subset_css)} 字节，码点 {len(codepoints)} 个")

    os.makedirs(os.path.join(OUT, "css"), exist_ok=True)
    os.makedirs(os.path.join(OUT, "webfonts"), exist_ok=True)
    with open(os.path.join(OUT, "css/all.min.css"), "w", encoding="utf-8") as f:
        f.write(subset_css)

    total_before = total_after = 0
    for name in ("fa-solid-900", "fa-regular-400", "fa-brands-400"):
        src = os.path.join(FA_FONTS, name + ".woff2")
        dst = os.path.join(OUT, "webfonts", name + ".woff2")
        subset_font(src, dst, codepoints)
        b, a = os.path.getsize(src), os.path.getsize(dst)
        total_before += b
        total_after += a
        print(f"      {name}.woff2: {b/1024:.1f}KB -> {a/1024:.1f}KB")
    print(f"[3/3] 字体合计：{total_before/1024:.1f}KB -> {total_after/1024:.1f}KB")
    return 1 if missing else 0


if __name__ == "__main__":
    sys.exit(main())
