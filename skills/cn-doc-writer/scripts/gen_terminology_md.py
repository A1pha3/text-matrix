#!/usr/bin/env python3
"""
术语表 Markdown 生成器

从 terminology.json（Single Source of Truth）自动生成 terminology.md。
确保两者始终保持同步，消除手工维护导致的数据漂移。

用法:
    python gen_terminology_md.py                      # 输出到 stdout
    python gen_terminology_md.py --write              # 写入 references/terminology.md
    python gen_terminology_md.py --output output.md   # 写入指定文件
"""

import sys
from pathlib import Path
from typing import Dict, Optional

from utils import load_terminology, REFERENCES_DIR


def generate_markdown(data: Dict) -> str:
    """从术语表 JSON 数据生成 Markdown 文档"""
    lines = []

    # 头部
    lines.append("# 技术术语中英文对照表")
    lines.append("")
    lines.append("> 本文件由 `scripts/gen_terminology_md.py` 从 `terminology.json` 自动生成。")
    lines.append("> **请勿手工编辑**，修改请编辑 `terminology.json` 后重新生成。")
    lines.append("")

    # 分类术语表
    categories = data.get("categories", {})
    for cat_key, cat in categories.items():
        label = cat.get("label", cat_key)
        terms = cat.get("terms", {})

        lines.append(f"## {label}")
        lines.append("")
        lines.append("| 英文 | 中文 | 说明 |")
        lines.append("|-----|------|------|")

        for en, info in terms.items():
            cn = info.get("cn", "")
            keep_en = info.get("keep_en", False)
            note = info.get("note", "")
            alt = info.get("alt")

            # 中文列：保留英文的术语显示 "英文 / 中文"
            if keep_en:
                cn_display = f"{en} / {cn}"
            else:
                cn_display = cn
                if alt:
                    cn_display += f" / {alt}"

            # 说明列
            desc = note if note else ""
            if alt and keep_en:
                desc = f"{note}，又作「{alt}」" if note else f"又作「{alt}」"

            lines.append(f"| {en} | {cn_display} | {desc} |")

        lines.append("")

    # 不翻译的术语
    no_translate = data.get("no_translate", {})
    if no_translate:
        lines.append("## 不翻译的术语")
        lines.append("")
        lines.append("以下术语通常保持英文，不翻译：")
        lines.append("")

        section_labels = {
            "tech_names": "技术名称",
            "protocols": "协议和标准",
            "code_concepts": "代码概念",
            "units": "单位和度量",
        }

        for key, items in no_translate.items():
            label = section_labels.get(key, key)
            lines.append(f"**{label}**：")
            # 每行显示多个，用逗号分隔
            lines.append(f"- {', '.join(items)}")
            lines.append("")

    return "\n".join(lines)


def main():
    # 加载术语表
    data = load_terminology()

    # 生成 Markdown
    md_content = generate_markdown(data)

    # 输出模式
    if "--write" in sys.argv:
        output_path = REFERENCES_DIR / "terminology.md"
        output_path.write_text(md_content, encoding="utf-8")
        print(f"✓ 已写入 {output_path}")
    elif "--output" in sys.argv:
        idx = sys.argv.index("--output")
        if idx + 1 < len(sys.argv):
            output_path = Path(sys.argv[idx + 1])
            output_path.write_text(md_content, encoding="utf-8")
            print(f"✓ 已写入 {output_path}")
        else:
            print("错误: --output 参数需要指定文件路径")
            sys.exit(1)
    else:
        print(md_content)


if __name__ == "__main__":
    main()
