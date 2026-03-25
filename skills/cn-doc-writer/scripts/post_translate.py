#!/usr/bin/env python3
"""
翻译后校验工具

功能：
- 检查翻译后文档的术语一致性
- 验证保留区域（代码块、URL、命令）未被错误翻译
- 检查中英文混排格式
- 对比原文和译文的结构完整性
- 生成翻译质量报告

配合 AI 翻译使用：先用 pre_translate.py 分析，交给 AI 翻译，最后用本工具校验。
"""

import re
import sys
from pathlib import Path
from typing import Dict, List, Optional

from utils import load_terminology, build_detailed_lookup, is_in_code_block, should_skip, _parse_fence, is_in_inline_code, is_in_latex


class PostTranslateChecker:
    """翻译后校验器"""

    def __init__(self, terminology_path: Optional[Path] = None):
        self._term_data = load_terminology(terminology_path)
        self._build_lookups()

    def _build_lookups(self):
        self.term_lookup = build_detailed_lookup(self._term_data)
        self.no_translate_names = set()
        for _key, items in self._term_data.get("no_translate", {}).items():
            self.no_translate_names.update(items)
        self.translation_dict = self._term_data.get("translation_dict", {})

    def check_translated(self, translated: str, original: Optional[str] = None) -> Dict:
        """检查翻译后的文档质量"""
        report: Dict = {
            "format_issues": [],
            "terminology_issues": [],
            "structure_issues": [],
            "preservation_issues": [],
            "score": 100,
        }

        lines = translated.split("\n")

        # 1. 格式检查
        report["format_issues"] = self._check_format(lines)

        # 2. 术语一致性
        report["terminology_issues"] = self._check_terminology_consistency(translated, lines)

        # 2.5 翻译词典一致性
        report["terminology_issues"].extend(self._check_translation_dict(translated, lines))

        # 3. 保留区域校验
        if original:
            report["preservation_issues"] = self._check_preservation(original, translated)
            report["structure_issues"] = self._check_structure_match(original, translated)

        # 4. 计算扣分
        deductions = (
            len(report["format_issues"]) * 1
            + len(report["terminology_issues"]) * 2
            + len(report["structure_issues"]) * 3
            + len(report["preservation_issues"]) * 5
        )
        report["score"] = max(0, 100 - deductions)

        return report

    def _check_format(self, lines: List[str]) -> List[str]:
        """检查中英文混排格式

        跳过以下区域（与 check_format.py 保持一致）：
        - YAML frontmatter / 代码块 / HTML 注释（由 should_skip 处理）
        - 行内代码 `...`（由 is_in_inline_code 处理）
        - LaTeX 公式 $...$（由 is_in_latex 处理）
        """
        issues = []

        check_patterns = [
            (re.compile(r"[\u4e00-\u9fff][a-zA-Z]|[a-zA-Z][\u4e00-\u9fff]"), "中英文之间缺少空格"),
            (re.compile(r"[\u4e00-\u9fff]\d|\d[\u4e00-\u9fff]"), "中文与数字之间缺少空格"),
            (re.compile(r"[\u4e00-\u9fff]\.(?:[^0-9a-zA-Z_/]|$)"), "可能使用了英文句号（应使用「。」）"),
            (re.compile(r"[\u4e00-\u9fff],(?:[^0-9a-zA-Z_]|$)"), "可能使用了英文逗号（应使用「，」）"),
        ]

        for i, line in enumerate(lines, 1):
            if should_skip(lines, i):
                continue

            for pattern, message in check_patterns:
                found = False
                for m in pattern.finditer(line):
                    col = m.start()
                    if is_in_inline_code(line, col) or is_in_latex(line, col):
                        continue
                    found = True
                    break
                if found:
                    issues.append(f"第 {i} 行: {message}")

        return issues

    def _check_terminology_consistency(self, content: str, lines: List[str]) -> List[str]:
        """检查术语翻译一致性"""
        issues = []
        in_code = False

        for term_lower, info in self.term_lookup.items():
            en = info["en"]
            cn = info["cn"]
            keep_en = info["keep_en"]
            alt = info.get("alt")

            # 查找英文术语出现位置
            pattern = re.compile(rf"\b{re.escape(en)}\b", re.IGNORECASE)
            occurrences = []

            for match in pattern.finditer(content):
                line_num = content[: match.start()].count("\n") + 1
                # 检查是否在代码块内
                if not self._is_in_code_block(lines, line_num):
                    occurrences.append(line_num)

            if not occurrences:
                continue

            # 如果术语需要保留英文，检查附近是否有中文注释
            if keep_en and len(occurrences) > 0:
                first_line = occurrences[0]
                first_pos = content.find(en)
                if first_pos >= 0:
                    ctx = content[max(0, first_pos - 80): first_pos + len(en) + 80]
                    if cn not in ctx and (not alt or alt not in ctx):
                        issues.append(
                            f"第 {first_line} 行: '{en}' 首次出现时建议标注中文「{cn}」"
                        )

            # 检查多次出现时翻译是否一致（只看非代码区域）
            if len(occurrences) > 3:
                issues.append(
                    f"术语 '{en}' 出现 {len(occurrences)} 次，请确认翻译一致性"
                )

        return issues

    def _check_translation_dict(self, content: str, lines: List[str]) -> List[str]:
        """检查翻译词典中的常用词是否被正确翻译

        使用 translation_dict 检查译文中残留的未翻译英文常用词。
        仅检查非代码区域，作为辅助建议（不强制）。
        """
        issues = []
        if not self.translation_dict:
            return issues

        for en, cn in self.translation_dict.items():
            pattern = re.compile(rf"\b{re.escape(en)}\b", re.IGNORECASE)
            for match in pattern.finditer(content):
                line_num = content[: match.start()].count("\n") + 1
                if should_skip(lines, line_num):
                    continue
                # 检查是否在行内代码内
                line_text = lines[line_num - 1]
                col = match.start() - content.rfind("\n", 0, match.start()) - 1
                if is_in_inline_code(line_text, max(0, col)):
                    continue
                issues.append(
                    f"第 {line_num} 行: 英文 '{en}' 建议翻译为「{cn}」"
                )
                break  # 每个词只报告第一次
        return issues

    @staticmethod
    def _extract_code_blocks(content: str) -> List[dict]:
        """使用 _parse_fence 提取代码块（支持变长围栏和波浪号围栏）

        Returns:
            列表，每项为 {"lang": str, "code": str, "start_line": int}
        """
        lines = content.split("\n")
        blocks = []
        in_code = False
        fence_char = None
        fence_len = 0
        block_lang = ""
        block_lines: List[str] = []
        block_start = 0

        for i, line in enumerate(lines):
            stripped = line.strip()
            ch, count, rest = _parse_fence(stripped)
            if ch is not None:
                if not in_code:
                    in_code = True
                    fence_char = ch
                    fence_len = count
                    block_lang = rest
                    block_lines = []
                    block_start = i + 1
                elif ch == fence_char and rest == "" and count >= fence_len:
                    blocks.append({
                        "lang": block_lang,
                        "code": "\n".join(block_lines),
                        "start_line": block_start,
                    })
                    in_code = False
            elif in_code:
                block_lines.append(line)

        return blocks

    def _check_preservation(self, original: str, translated: str) -> List[str]:
        """检查代码块等保留区域是否完整

        使用 _parse_fence 正确处理 CommonMark 变长围栏（反引号和波浪号）。
        """
        issues = []

        # 使用 _parse_fence 提取代码块
        orig_blocks = self._extract_code_blocks(original)
        trans_blocks = self._extract_code_blocks(translated)

        if len(orig_blocks) != len(trans_blocks):
            issues.append(
                f"代码块数量不匹配：原文 {len(orig_blocks)} 个，译文 {len(trans_blocks)} 个"
            )
        else:
            for idx, (orig, trans) in enumerate(zip(orig_blocks, trans_blocks)):
                if orig["lang"] != trans["lang"]:
                    issues.append(
                        f"代码块 {idx + 1}: 语言标记不匹配（{orig['lang']} → {trans['lang']}）"
                    )
                if orig["code"].strip() != trans["code"].strip():
                    # 代码内容不同可能是注释被翻译了，这是允许的
                    # 但关键代码结构应该保持
                    orig_lines = [
                        l for l in orig["code"].split("\n")
                        if l.strip() and not l.strip().startswith(("#", "//", "/*", "*"))
                    ]
                    trans_lines = [
                        l for l in trans["code"].split("\n")
                        if l.strip() and not l.strip().startswith(("#", "//", "/*", "*"))
                    ]
                    if orig_lines != trans_lines:
                        issues.append(
                            f"代码块 {idx + 1}: 代码内容被修改（仅允许翻译注释）"
                        )

        # 检查 URL 保留
        orig_urls = set(re.findall(r"https?://[^\s<>\"')]+", original))
        trans_urls = set(re.findall(r"https?://[^\s<>\"')]+", translated))
        missing_urls = orig_urls - trans_urls
        if missing_urls:
            for url in list(missing_urls)[:5]:
                issues.append(f"URL 丢失: {url[:60]}...")

        return issues

    def _check_structure_match(self, original: str, translated: str) -> List[str]:
        """检查原文和译文的结构是否匹配"""
        issues = []

        orig_headings = re.findall(r"^(#{1,6})\s+(.+)", original, re.MULTILINE)
        trans_headings = re.findall(r"^(#{1,6})\s+(.+)", translated, re.MULTILINE)

        if len(orig_headings) != len(trans_headings):
            issues.append(
                f"标题数量不匹配：原文 {len(orig_headings)} 个，译文 {len(trans_headings)} 个"
            )
        else:
            for idx, (orig, trans) in enumerate(zip(orig_headings, trans_headings)):
                if orig[0] != trans[0]:  # 标题级别
                    issues.append(
                        f"标题 {idx + 1} 级别不匹配：原文 H{len(orig[0])}，译文 H{len(trans[0])}"
                    )

        # 行数偏差检测（排除空行和代码块）
        orig_text_lines = self._count_text_lines(original)
        trans_text_lines = self._count_text_lines(translated)
        if orig_text_lines > 0:
            deviation = abs(trans_text_lines - orig_text_lines) / orig_text_lines
            if deviation > 0.3:
                issues.append(
                    f"文本行数偏差过大：原文 {orig_text_lines} 行，"
                    f"译文 {trans_text_lines} 行（偏差 {deviation:.0%}，建议 ≤20%）"
                )

        return issues

    @staticmethod
    def _count_text_lines(content: str) -> int:
        """统计非空、非代码块的文本行数

        使用 _parse_fence 正确处理 CommonMark 变长围栏（反引号和波浪号）。
        """
        lines = content.split("\n")
        count = 0
        in_code = False
        fence_char = None
        fence_len = 0
        for line in lines:
            stripped = line.strip()
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
            if stripped:
                count += 1
        return count

    @staticmethod
    def _is_in_code_block(lines: List[str], line_number: int) -> bool:
        return is_in_code_block(lines, line_number)

    def print_report(self, report: Dict, file_name: str = ""):
        """打印校验报告"""
        print("=" * 60)
        print(f"📋 翻译后校验报告{f' - {file_name}' if file_name else ''}")
        print("=" * 60)

        score = report["score"]
        if score >= 90:
            grade = "S 级 ✨"
        elif score >= 80:
            grade = "A 级 ✅"
        elif score >= 70:
            grade = "B 级 ⚠️"
        elif score >= 60:
            grade = "C 级 ⚠️"
        else:
            grade = "D 级 ❌"

        print(f"\n🎯 总分: {score}/100（{grade}）")

        sections = [
            ("格式问题", report["format_issues"]),
            ("术语问题", report["terminology_issues"]),
            ("结构问题", report["structure_issues"]),
            ("保留区域问题", report["preservation_issues"]),
        ]

        for title, items in sections:
            if items:
                print(f"\n📌 {title} ({len(items)} 项):")
                for item in items[:10]:
                    print(f"  - {item}")
                if len(items) > 10:
                    print(f"  ... 还有 {len(items) - 10} 项")

        if all(len(items) == 0 for _, items in sections):
            print("\n✅ 未发现问题，翻译质量良好！")

        print("\n" + "=" * 60)


def main():
    if len(sys.argv) < 2:
        print("用法:")
        print("  python post_translate.py <译文文件>")
        print("  python post_translate.py <译文文件> --original <原文文件>")
        print("\n带 --original 参数时，会对比原文和译文的结构完整性。")
        sys.exit(1)

    trans_path = Path(sys.argv[1])
    orig_path = None

    if "--original" in sys.argv:
        idx = sys.argv.index("--original")
        if idx + 1 < len(sys.argv):
            orig_path = Path(sys.argv[idx + 1])

    if not trans_path.exists():
        print(f"文件不存在: {trans_path}")
        sys.exit(1)

    try:
        translated = trans_path.read_text(encoding="utf-8")
    except Exception as e:
        print(f"无法读取译文: {e}")
        sys.exit(1)

    original = None
    if orig_path:
        if not orig_path.exists():
            print(f"原文文件不存在: {orig_path}")
            sys.exit(1)
        try:
            original = orig_path.read_text(encoding="utf-8")
        except Exception as e:
            print(f"无法读取原文: {e}")
            sys.exit(1)

    checker = PostTranslateChecker()
    report = checker.check_translated(translated, original)
    checker.print_report(report, trans_path.name)


if __name__ == "__main__":
    main()
