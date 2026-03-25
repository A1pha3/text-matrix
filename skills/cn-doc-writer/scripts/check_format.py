#!/usr/bin/env python3
"""
中文技术文档格式检查工具

功能：
- 检查中英文空格
- 检查标点符号使用
- 检查术语一致性（从 terminology.json 加载）
- 检查 Markdown 结构
- 自动修复常见格式问题

术语表从 references/terminology.json 加载（Single Source of Truth）。
"""

import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional

from utils import (
    load_terminology,
    build_terminology_lookup,
    is_in_code_block,
    is_frontmatter,
    should_skip,
    find_frontmatter_end,
    count_consecutive_blank_lines,
    is_in_inline_code,
    is_in_latex,
    _parse_fence,
)


# === 格式检查器 ===

class DocChecker:
    """中文文档格式检查器"""

    def __init__(self, terminology_path: Optional[Path] = None):
        self._term_data = load_terminology(terminology_path)
        self.terminology = build_terminology_lookup(self._term_data)

        # 常见错误模式
        self.error_patterns = {
            "chinese_english_no_space": {
                "pattern": re.compile(
                    r"[\u4e00-\u9fff][a-zA-Z]|[a-zA-Z][\u4e00-\u9fff]"
                ),
                "message": "中英文之间缺少空格",
            },
            "chinese_number_no_space": {
                "pattern": re.compile(
                    r"[\u4e00-\u9fff]\d|\d[\u4e00-\u9fff]"
                ),
                "message": "中文与数字之间缺少空格",
            },
            "heading_without_space": {
                "pattern": re.compile(r"^#{1,6}[^ \n#]"),
                "message": "标题标记后应有空格",
            },
            "trailing_space": {
                "pattern": re.compile(r"[ \t]+$"),
                "message": "行尾有多余空格",
            },
        }

    # --- 位置判断 helpers（委托给 utils 模块） ---

    @staticmethod
    def _is_in_code_block(lines: List[str], line_number: int) -> bool:
        return is_in_code_block(lines, line_number)

    @staticmethod
    def _is_frontmatter(lines: List[str], line_number: int) -> bool:
        return is_frontmatter(lines, line_number)

    def _should_skip(self, lines: List[str], line_number: int) -> bool:
        return should_skip(lines, line_number)

    # --- 检查方法 ---

    def check_format(self, lines: List[str]) -> List[str]:
        """检查格式错误，返回错误描述列表

        跳过以下区域（按优先级）：
        - YAML frontmatter / 代码块（由 should_skip 处理）
        - 行内代码 `...`（由 is_in_inline_code 处理）
        - LaTeX 公式 $...$（由 is_in_latex 处理）
        - Markdown 换行符（行尾恰好 2 个空格）
        """
        errors = []
        for line_number, line in enumerate(lines, 1):
            if self._should_skip(lines, line_number):
                continue
            for _key, info in self.error_patterns.items():
                # 允许 Markdown 换行（行尾恰好 2 个空格）
                if _key == "trailing_space":
                    stripped = line.rstrip(" \t")
                    trailing = line[len(stripped):]
                    if trailing == "  ":
                        continue  # 恰好 2 个空格 = Markdown <br>
                # 逐个匹配，跳过行内代码和 LaTeX 公式内的匹配
                found = False
                for m in info["pattern"].finditer(line):
                    col = m.start()
                    if is_in_inline_code(line, col) or is_in_latex(line, col):
                        continue
                    found = True
                    break
                if found:
                    errors.append(f"第 {line_number} 行: {info['message']}")
        return errors

    def check_terminology(self, content: str) -> List[str]:
        """检查术语使用一致性"""
        issues = []
        lines = content.split("\n")

        for eng, (chi, chi_alt) in self.terminology.items():
            pattern = re.compile(rf"\b{re.escape(eng)}\b", re.IGNORECASE)
            for match in pattern.finditer(content):
                line_start = content[: match.start()].count("\n") + 1
                if self._should_skip(lines, line_start):
                    continue

                # 在术语前后 120 字符范围内查找中文标注
                ctx_start = max(0, match.start() - 120)
                ctx_end = min(len(content), match.end() + 120)
                ctx = content[ctx_start:ctx_end]

                has_chi = chi in ctx
                has_alt = False
                if chi_alt:
                    for alt_term in chi_alt.split("|"):
                        if alt_term in ctx:
                            has_alt = True
                            break
                if not has_chi and not has_alt:
                    display = f"{chi}（{chi_alt}）" if chi_alt else chi
                    issues.append(
                        f"第 {line_start} 行: 术语 '{eng}' 首次出现时应标注中文: {display}"
                    )
                break  # 只报告每个术语的第一次出现
        return issues

    def check_markdown_structure(self, content: str) -> List[str]:
        """检查 Markdown 结构"""
        issues = []
        lines = content.split("\n")

        # 标题层级跳跃
        prev_level = 0
        for i, line in enumerate(lines):
            m = re.match(r"^(#{1,6})\s", line)
            if m:
                if self._should_skip(lines, i + 1):
                    continue
                level = len(m.group(1))
                if level > prev_level + 1 and prev_level > 0:
                    issues.append(
                        f"第 {i + 1} 行: 标题层级跳跃（从 H{prev_level} 跳到 H{level}）"
                    )
                prev_level = level

        # 代码块闭合（使用 CommonMark 围栏长度规则，支持 ` 和 ~ 围栏）
        in_code = False
        code_start = -1
        code_fence_char = None
        code_fence_len = 0
        fm_end = find_frontmatter_end(lines)
        for i, line in enumerate(lines):
            if i <= fm_end and fm_end > 0:
                continue
            stripped = line.strip()
            ch, count, rest = _parse_fence(stripped)
            if ch is None:
                continue
            if not in_code:
                in_code = True
                code_start = i
                code_fence_char = ch
                code_fence_len = count
            else:
                if ch == code_fence_char and rest == "" and count >= code_fence_len:
                    in_code = False
        if in_code:
            issues.append(f"第 {code_start + 1} 行开始的代码块未闭合")

        # 空链接 / 未闭合链接
        for i, line in enumerate(lines):
            if self._should_skip(lines, i + 1):
                continue
            if re.search(r"\[([^\]]+)\]\(\s*\)", line):
                issues.append(f"第 {i + 1} 行: 发现空链接")
            if re.search(r"\[[^\]]*\]\([^)]*$", line):
                issues.append(f"第 {i + 1} 行: 发现未闭合的链接")

        # 连续空行检测（>2 行连续空行）
        blank_runs = count_consecutive_blank_lines(lines)
        for start_line, count in blank_runs:
            issues.append(
                f"第 {start_line} 行: 连续 {count} 个空行（建议不超过 2 个）"
            )

        # 代码块无语言标记（使用 CommonMark 围栏长度规则，支持 ` 和 ~ 围栏）
        in_code_scan = False
        scan_fence_char = None
        scan_fence_len = 0
        for i, line in enumerate(lines):
            stripped = line.strip()
            ch, count, rest = _parse_fence(stripped)
            if ch is None:
                continue
            if not in_code_scan:
                # 开启围栏
                in_code_scan = True
                scan_fence_char = ch
                scan_fence_len = count
                if rest == "":
                    if not is_frontmatter(lines, i + 1):
                        issues.append(
                            f"第 {i + 1} 行: 代码块未指定语言（建议添加如 ```python）"
                        )
            else:
                # 闭合围栏：同种字符、纯围栏字符且长度 >= 开启围栏
                if ch == scan_fence_char and rest == "" and count >= scan_fence_len:
                    in_code_scan = False

        return issues

    def check(self, file_path: Path) -> Dict:
        """完整检查，返回结果字典"""
        result = {
            "file": str(file_path),
            "errors": [],
            "terminology_issues": [],
            "structure_issues": [],
            "total_issues": 0,
            "summary": {},
        }

        try:
            content = file_path.read_text(encoding="utf-8")
        except Exception as e:
            result["errors"].append(f"无法读取文件: {e}")
            result["total_issues"] = 1
            return result

        lines = content.split("\n")
        result["errors"] = self.check_format(lines)
        result["terminology_issues"] = self.check_terminology(content)
        result["structure_issues"] = self.check_markdown_structure(content)
        result["total_issues"] = (
            len(result["errors"])
            + len(result["terminology_issues"])
            + len(result["structure_issues"])
        )
        result["summary"] = {
            "format_errors": len(result["errors"]),
            "terminology_issues": len(result["terminology_issues"]),
            "structure_issues": len(result["structure_issues"]),
            "total_lines": len(lines),
        }
        return result

    # --- 可读性量化指标 ---

    def check_readability(self, content: str) -> Dict:
        """计算中文文档可读性量化指标

        指标说明：
        - avg_sentence_length: 平均句长（字/句），15-35 为宜
        - paragraph_density: 段落平均行数，3-8 为宜
        - code_text_ratio: 代码占比，教程 30-50%，参考 ≤60%
        - heading_spacing: 同级标题间平均字数，50-300 为宜
        - long_sentence_ratio: 超长句（>50 字）占比，<15% 为宜
        """
        lines = content.split("\n")
        text_lines = []
        code_lines = 0
        in_code = False
        fence_char = None
        fence_len = 0

        for line in lines:
            stripped = line.strip()
            ch, count, rest = _parse_fence(stripped)
            if ch is not None:
                if not in_code:
                    in_code = True
                    fence_char = ch
                    fence_len = count
                elif ch == fence_char and rest == "" and count >= fence_len:
                    in_code = False
                code_lines += 1
                continue
            if in_code:
                code_lines += 1
                continue
            if stripped:
                text_lines.append(stripped)

        # 句子分割（中文句号/问号/叹号/分号）
        text_content = "\n".join(text_lines)
        # 排除标题行、列表标记等
        clean_text = re.sub(r"^#{1,6}\s+", "", text_content, flags=re.MULTILINE)
        clean_text = re.sub(r"^[-*+]\s+", "", clean_text, flags=re.MULTILINE)
        clean_text = re.sub(r"^\d+\.\s+", "", clean_text, flags=re.MULTILINE)

        sentences = re.split(r"[。！？；\n]", clean_text)
        sentences = [s.strip() for s in sentences if s.strip() and len(s.strip()) > 1]

        # 平均句长
        if sentences:
            lengths = [len(s) for s in sentences]
            avg_sentence_length = sum(lengths) / len(lengths)
            long_sentences = [l for l in lengths if l > 50]
            long_sentence_ratio = len(long_sentences) / len(lengths) * 100
        else:
            avg_sentence_length = 0
            long_sentence_ratio = 0

        # 段落密度（以空行为段落分隔）
        paragraphs = []
        current_para = 0
        in_code_p = False
        fence_char_p = None
        fence_len_p = 0
        for line in lines:
            stripped = line.strip()
            ch_p, count_p, rest_p = _parse_fence(stripped)
            if ch_p is not None:
                if not in_code_p:
                    in_code_p = True
                    fence_char_p = ch_p
                    fence_len_p = count_p
                elif ch_p == fence_char_p and rest_p == "" and count_p >= fence_len_p:
                    in_code_p = False
                continue
            if in_code_p:
                continue
            if stripped == "":
                if current_para > 0:
                    paragraphs.append(current_para)
                    current_para = 0
            else:
                current_para += 1
        if current_para > 0:
            paragraphs.append(current_para)

        avg_paragraph_density = (
            sum(paragraphs) / len(paragraphs) if paragraphs else 0
        )

        # 代码文本比
        total_non_blank = len(text_lines) + code_lines
        code_text_ratio = (
            code_lines / total_non_blank * 100 if total_non_blank > 0 else 0
        )

        # 同级标题间距
        headings = []
        char_count = 0
        for line_idx, line in enumerate(lines):
            stripped = line.strip()
            m = re.match(r"^(#{1,6})\s", stripped)
            if m and not is_in_code_block(lines, line_idx + 1):
                headings.append((len(m.group(1)), char_count))
            char_count += len(line)

        heading_spacings = []
        for i in range(1, len(headings)):
            if headings[i][0] == headings[i - 1][0]:
                spacing = headings[i][1] - headings[i - 1][1]
                heading_spacings.append(spacing)
        avg_heading_spacing = (
            sum(heading_spacings) / len(heading_spacings)
            if heading_spacings
            else 0
        )

        # 评级
        issues = []
        if avg_sentence_length > 50:
            issues.append(f"平均句长 {avg_sentence_length:.0f} 字，建议控制在 35 字以内")
        if avg_paragraph_density > 10:
            issues.append(f"段落平均 {avg_paragraph_density:.1f} 行，建议 3-8 行")
        if long_sentence_ratio > 15:
            issues.append(f"超长句占比 {long_sentence_ratio:.0f}%，建议控制在 15% 以内")
        if code_text_ratio > 70:
            issues.append(f"代码占比 {code_text_ratio:.0f}%，正文可能不足")

        return {
            "avg_sentence_length": round(avg_sentence_length, 1),
            "avg_paragraph_density": round(avg_paragraph_density, 1),
            "code_text_ratio": round(code_text_ratio, 1),
            "avg_heading_spacing": round(avg_heading_spacing, 0),
            "long_sentence_ratio": round(long_sentence_ratio, 1),
            "total_sentences": len(sentences),
            "total_paragraphs": len(paragraphs),
            "total_text_lines": len(text_lines),
            "total_code_lines": code_lines,
            "issues": issues,
        }

    # --- 自动修复 ---

    @staticmethod
    def _add_space(text: str) -> str:
        """在中英文 / 中文数字之间添加空格

        跳过行内代码 `...` / ``...`` 和 URL 区域，避免误修改。
        """
        # 收集需要保护的区间 [start, end)
        protected: list[tuple[int, int]] = []

        # 行内代码区间（支持多反引号）
        i = 0
        while i < len(text):
            if text[i] == '`':
                open_start = i
                while i < len(text) and text[i] == '`':
                    i += 1
                tick_count = i - open_start
                j = i
                close_start = -1
                while j < len(text):
                    if text[j] == '`':
                        cs = j
                        while j < len(text) and text[j] == '`':
                            j += 1
                        if j - cs == tick_count:
                            close_start = cs
                            break
                    else:
                        j += 1
                if close_start != -1:
                    protected.append((open_start, close_start + tick_count))
                    i = close_start + tick_count
                else:
                    protected.append((open_start, len(text)))
                    break
            else:
                i += 1

        # URL 区间
        for m in re.finditer(r"https?://[^\s<>\"')]+", text):
            protected.append((m.start(), m.end()))

        # LaTeX 公式区间
        i = 0
        while i < len(text):
            if text[i] == '$':
                if i + 1 < len(text) and text[i + 1] == '$':
                    close = text.find('$$', i + 2)
                    if close != -1:
                        protected.append((i, close + 2))
                        i = close + 2
                    else:
                        protected.append((i, len(text)))
                        break
                else:
                    close = text.find('$', i + 1)
                    if close != -1:
                        protected.append((i, close + 1))
                        i = close + 1
                    else:
                        protected.append((i, len(text)))
                        break
            else:
                i += 1

        # 按位置排序
        protected.sort()

        def is_protected(pos: int) -> bool:
            for s, e in protected:
                if s <= pos < e:
                    return True
            return False

        patterns = [
            (re.compile(r"([\u4e00-\u9fff])([a-zA-Z])"), r"\1 \2"),
            (re.compile(r"([a-zA-Z])([\u4e00-\u9fff])"), r"\1 \2"),
            (re.compile(r"([\u4e00-\u9fff])(\d)"), r"\1 \2"),
            (re.compile(r"(\d)([\u4e00-\u9fff])"), r"\1 \2"),
        ]

        for pattern, replacement in patterns:
            result = []
            last_end = 0
            for m in pattern.finditer(text):
                if is_protected(m.start()):
                    continue
                result.append(text[last_end:m.start()])
                result.append(m.expand(replacement))
                last_end = m.end()
            if result:
                result.append(text[last_end:])
                text = "".join(result)

        return text

    def fix_file(self, file_path: Path) -> bool:
        """自动修复格式问题

        修复内容：
        - 中英文/中文数字之间添加空格（跳过行内代码和 LaTeX）
        - 去除多余行尾空格（保留 Markdown 换行的 2 个空格）
        - 为无语言标记的代码块添加 `text` 标记
        """
        try:
            content = file_path.read_text(encoding="utf-8")
        except Exception as e:
            print(f"无法读取文件: {e}")
            return False

        lines = content.split("\n")
        new_lines = []
        in_code = False
        fence_char = None
        fence_len = 0
        fm_end = find_frontmatter_end(lines)
        for line_number, line in enumerate(lines, 1):
            # frontmatter 保持原样
            if 1 <= line_number <= fm_end and fm_end > 0:
                new_lines.append(line)
                continue

            stripped = line.strip()
            # 代码块边界处理（支持 ` 和 ~ 围栏）
            ch, count, rest = _parse_fence(stripped)
            if ch is not None:
                if not in_code:
                    in_code = True
                    fence_char = ch
                    fence_len = count
                    # 无语言标记 → 添加 text
                    if rest == "":
                        marker = ch * count
                        line = line.replace(marker, marker + "text", 1)
                elif ch == fence_char and rest == "" and count >= fence_len:
                    in_code = False
                new_lines.append(line)
                continue

            # 代码块内保持原样
            if in_code:
                new_lines.append(line)
                continue

            fixed = self._add_space(line)
            # 行尾空格处理：保留 Markdown 换行（恰好 2 个空格）
            raw_trailing = len(fixed) - len(fixed.rstrip())
            if raw_trailing == 2 and fixed.endswith("  "):
                pass  # 保留 Markdown <br>
            else:
                fixed = fixed.rstrip()
            new_lines.append(fixed)

        try:
            file_path.write_text("\n".join(new_lines), encoding="utf-8")
            return True
        except Exception as e:
            print(f"无法写入文件: {e}")
            return False


# === CLI ===

def _print_section(title: str, items: List[str], limit: int = 15):
    if not items:
        return
    print(f"\n{title}:")
    for item in items[:limit]:
        print(f"  - {item}")
    if len(items) > limit:
        print(f"  ... 还有 {len(items) - limit} 项")


def _print_readability(metrics: Dict):
    """打印可读性指标"""
    print("\n📊 可读性指标:")
    print(f"  平均句长: {metrics['avg_sentence_length']} 字/句 (建议 15-35)")
    print(f"  段落密度: {metrics['avg_paragraph_density']} 行/段 (建议 3-8)")
    print(f"  代码占比: {metrics['code_text_ratio']}% ", end="")
    print(f"({metrics['total_code_lines']} 代码行 / {metrics['total_text_lines']} 正文行)")
    print(f"  标题间距: {metrics['avg_heading_spacing']:.0f} 字 (建议 50-300)")
    print(f"  超长句占比: {metrics['long_sentence_ratio']}% (建议 <15%)")
    print(f"  共 {metrics['total_sentences']} 句, {metrics['total_paragraphs']} 段")
    if metrics["issues"]:
        print("\n  ⚠️ 建议:")
        for issue in metrics["issues"]:
            print(f"    - {issue}")
    else:
        print("\n  ✅ 可读性指标均在合理范围内")


def main():
    if len(sys.argv) < 2:
        print("用法: python check_format.py <文件或目录> [--fix] [--readability] [--json]")
        sys.exit(1)

    target = Path(sys.argv[1])
    auto_fix = "--fix" in sys.argv
    show_readability = "--readability" in sys.argv
    json_output = "--json" in sys.argv
    checker = DocChecker()

    if target.is_file():
        if target.suffix not in (".md", ".txt", ".rst", ".adoc"):
            if json_output:
                print(json.dumps({"error": "不支持的文件类型"}))
            else:
                print("不支持的文件类型")
            sys.exit(1)

        result = checker.check(target)

        if show_readability:
            content = target.read_text(encoding="utf-8")
            result["readability"] = checker.check_readability(content)

        if json_output:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(f"\n检查文件: {result['file']}")
            print(f"总问题数: {result['total_issues']}")
            _print_section("格式错误", result["errors"])
            _print_section("术语问题", result["terminology_issues"])
            _print_section("结构问题", result["structure_issues"])
            if show_readability:
                _print_readability(result["readability"])

        if auto_fix:
            if checker.fix_file(target):
                if not json_output:
                    print("\n✓ 文件已自动修复（中英文空格 + 行尾空格）")
            else:
                if not json_output:
                    print("\n✗ 自动修复失败")

    elif target.is_dir():
        md_files = sorted(target.rglob("*.md"))
        all_results = []
        total = 0

        for md_file in md_files:
            result = checker.check(md_file)
            if show_readability:
                content = md_file.read_text(encoding="utf-8")
                result["readability"] = checker.check_readability(content)
            all_results.append(result)
            total += result["total_issues"]
            if not json_output:
                if result["total_issues"] > 0:
                    print(f"  {md_file.name}: {result['total_issues']} 个问题")
                if auto_fix:
                    checker.fix_file(md_file)
                if show_readability:
                    print(f"\n  [{md_file.name}]")
                    _print_readability(result["readability"])

        if json_output:
            print(json.dumps({
                "total_files": len(md_files),
                "total_issues": total,
                "files": all_results,
            }, ensure_ascii=False, indent=2))
        else:
            print(f"找到 {len(md_files)} 个 Markdown 文件")
            print(f"\n总计: {total} 个问题")
            if auto_fix and total > 0:
                print("✓ 已自动修复格式问题")
    else:
        if json_output:
            print(json.dumps({"error": f"路径不存在: {target}"}))
        else:
            print(f"路径不存在: {target}")
        sys.exit(1)


if __name__ == "__main__":
    main()
