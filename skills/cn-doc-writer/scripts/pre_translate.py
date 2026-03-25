#!/usr/bin/env python3
"""
翻译前分析工具

功能：
- 分析文档结构和工作量
- 识别不可翻译区域（代码块、URL、命令等）
- 提取术语清单（对照 terminology.json）
- 生成翻译计划报告

配合 AI 翻译使用：先用本工具分析，再交给 AI 翻译，最后用 post_translate.py 校验。
"""

import re
import sys
from pathlib import Path
from typing import Dict, List, Optional

from utils import load_terminology, build_detailed_lookup, is_in_code_block, _parse_fence


class PreTranslateAnalyzer:
    """翻译前分析器"""

    # 需要保留的内容模式
    PRESERVE_PATTERNS = [
        ("code_block", re.compile(r"```[\s\S]*?```")),
        ("inline_code", re.compile(r"`[^`]+`")),
        ("url", re.compile(r"https?://[^\s<>\"')]+", re.ASCII)),
        ("email", re.compile(r"[\w.-]+@[\w.-]+\.\w+", re.ASCII)),
        ("image_link", re.compile(r"!\[.*?\]\([^)]+\)")),
        ("link", re.compile(r"\[([^\]]+)\]\(([^)]+)\)")),
        ("file_path", re.compile(
            r"[\w/.\\-]+\.(py|js|ts|go|java|cpp|c|h|md|txt|json|yaml|yml|html|css|sh|toml|rs|rb)\b"
        )),
        ("frontmatter", re.compile(r"^---\n[\s\S]*?\n---", re.MULTILINE)),
    ]

    def __init__(self, terminology_path: Optional[Path] = None):
        self._term_data = load_terminology(terminology_path)
        self._build_lookups()

    def _build_lookups(self):
        """构建术语查找结构"""
        self.term_lookup = build_detailed_lookup(self._term_data)
        self.no_translate = self._term_data.get("no_translate", {})
        self.translation_dict = self._term_data.get("translation_dict", {})

    def analyze(self, content: str) -> Dict:
        """分析文档，返回翻译计划"""
        lines = content.split("\n")

        # 基本统计
        stats = {
            "total_lines": len(lines),
            "total_chars": len(content),
            "total_words": len(content.split()),
        }

        # 识别保留区域
        preserved = self._find_preserved_regions(content)
        stats["preserved_regions"] = len(preserved)

        # 代码块统计（只计算开始标记即带语言名的，以及无语言名的开始标记）
        code_block_pairs = re.findall(r"```[\s\S]*?```", content)
        stats["code_blocks"] = len(code_block_pairs)
        code_langs = re.findall(r"```(\w+)\n", content)
        stats["code_languages"] = list(set(code_langs)) if code_langs else []

        # 链接统计
        stats["links"] = len(re.findall(r"\[([^\]]+)\]\([^)]+\)", content))
        stats["images"] = len(re.findall(r"!\[", content))

        # 标题结构
        headings = []
        for i, line in enumerate(lines, 1):
            m = re.match(r"^(#{1,6})\s+(.+)", line)
            if m:
                headings.append({
                    "line": i,
                    "level": len(m.group(1)),
                    "text": m.group(2).strip(),
                })
        stats["headings"] = headings

        # 术语发现
        found_terms = self._find_terms(content, lines)
        stats["found_terms"] = found_terms

        # 待翻译文本行数（排除代码块、frontmatter）
        text_lines = self._count_translatable_lines(lines)
        stats["translatable_lines"] = text_lines

        # 估算工作量
        stats["estimated_minutes"] = round(text_lines * 0.3, 1)

        return stats

    def _find_preserved_regions(self, content: str) -> List[Dict]:
        """找到所有不应翻译的区域"""
        regions = []
        for name, pattern in self.PRESERVE_PATTERNS:
            for match in pattern.finditer(content):
                regions.append({
                    "type": name,
                    "start": match.start(),
                    "end": match.end(),
                    "preview": match.group(0)[:80],
                })
        return regions

    def _find_terms(self, content: str, lines: List[str]) -> List[Dict]:
        """在文档中查找已知术语"""
        found = []
        seen = set()

        for term_lower, info in self.term_lookup.items():
            if term_lower in seen:
                continue
            pattern = re.compile(rf"\b{re.escape(info['en'])}\b", re.IGNORECASE)
            match = pattern.search(content)
            if match:
                line_num = content[: match.start()].count("\n") + 1
                # 跳过代码块中的术语
                if not self._is_in_code_block(lines, line_num):
                    found.append({
                        "en": info["en"],
                        "cn": info["cn"],
                        "keep_en": info["keep_en"],
                        "alt": info.get("alt"),
                        "first_line": line_num,
                    })
                    seen.add(term_lower)

        # 按首次出现行号排序
        found.sort(key=lambda x: x["first_line"])
        return found

    @staticmethod
    def _is_in_code_block(lines: List[str], line_number: int) -> bool:
        return is_in_code_block(lines, line_number)

    def _count_translatable_lines(self, lines: List[str]) -> int:
        """统计需要翻译的文本行数

        使用 _parse_fence 正确处理 CommonMark 变长围栏（反引号和波浪号）。
        """
        count = 0
        in_code = False
        in_frontmatter = False
        fence_char = None
        fence_len = 0

        for i, line in enumerate(lines):
            stripped = line.strip()
            # frontmatter 检测
            if i == 0 and stripped == "---":
                in_frontmatter = True
                continue
            if in_frontmatter:
                if stripped == "---":
                    in_frontmatter = False
                continue
            # 代码块检测（使用 _parse_fence 正确支持变长围栏）
            ch, ch_count, rest = _parse_fence(stripped)
            if ch is not None:
                if not in_code:
                    in_code = True
                    fence_char = ch
                    fence_len = ch_count
                elif ch == fence_char and rest == "" and ch_count >= fence_len:
                    in_code = False
                continue
            if in_code:
                continue
            # 非空行计数
            if stripped:
                count += 1
        return count

    def print_report(self, stats: Dict, file_name: str = ""):
        """打印翻译分析报告"""
        print("=" * 60)
        print(f"📋 翻译前分析报告{f' - {file_name}' if file_name else ''}")
        print("=" * 60)

        print(f"\n📊 基本统计:")
        print(f"  总行数: {stats['total_lines']}")
        print(f"  总字符: {stats['total_chars']}")
        print(f"  代码块: {stats['code_blocks']} 个")
        if stats["code_languages"]:
            print(f"  代码语言: {', '.join(stats['code_languages'])}")
        print(f"  链接: {stats['links']} 个")
        print(f"  图片: {stats['images']} 个")
        print(f"  待翻译行数: {stats['translatable_lines']}")
        print(f"  预估耗时: {stats['estimated_minutes']} 分钟")

        if stats["headings"]:
            print(f"\n📑 文档结构:")
            for h in stats["headings"]:
                indent = "  " * h["level"]
                print(f"  {indent}{'#' * h['level']} {h['text']}")

        if stats["found_terms"]:
            print(f"\n📖 发现的术语 ({len(stats['found_terms'])} 个):")
            print(f"  {'英文':<20} {'中文':<15} {'保留英文':>8}  首次出现")
            print(f"  {'─' * 20} {'─' * 15} {'─' * 8}  {'─' * 8}")
            for t in stats["found_terms"]:
                keep = "✓" if t["keep_en"] else ""
                alt = f" / {t['alt']}" if t.get("alt") else ""
                print(f"  {t['en']:<20} {t['cn']}{alt:<15} {keep:>8}  第 {t['first_line']} 行")

        print("\n" + "=" * 60)


def main():
    if len(sys.argv) < 2:
        print("用法: python pre_translate.py <英文文档路径>")
        print("\n分析文档结构和翻译工作量，生成翻译计划报告。")
        sys.exit(1)

    input_path = Path(sys.argv[1])
    if not input_path.exists():
        print(f"文件不存在: {input_path}")
        sys.exit(1)

    try:
        content = input_path.read_text(encoding="utf-8")
    except Exception as e:
        print(f"无法读取文件: {e}")
        sys.exit(1)

    analyzer = PreTranslateAnalyzer()
    stats = analyzer.analyze(content)
    analyzer.print_report(stats, input_path.name)


if __name__ == "__main__":
    main()
