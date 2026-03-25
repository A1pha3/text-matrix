#!/usr/bin/env python3
"""
共享工具模块

提供所有脚本共用的函数，避免代码重复。
- 术语表加载（Single Source of Truth）
- 代码块/frontmatter 位置判断
- 通用路径解析
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple


# === 路径常量 ===

SCRIPTS_DIR = Path(__file__).parent
REFERENCES_DIR = SCRIPTS_DIR.parent / "references"
DEFAULT_TERMINOLOGY_PATH = REFERENCES_DIR / "terminology.json"


# === 术语表加载 ===

def load_terminology(json_path: Optional[Path] = None) -> Dict:
    """从 terminology.json 加载术语表（Single Source of Truth）

    Args:
        json_path: 可选的 JSON 文件路径。默认使用 references/terminology.json。

    Returns:
        术语表字典，包含 categories、no_translate、translation_dict。
    """
    if json_path is None:
        json_path = DEFAULT_TERMINOLOGY_PATH

    if not json_path.exists():
        print(f"⚠️  术语表文件不存在: {json_path}")
        return {"categories": {}, "no_translate": {}, "translation_dict": {}}

    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)


def build_terminology_lookup(data: Dict) -> Dict[str, Tuple[str, Optional[str]]]:
    """从 JSON 数据构建 (英文小写 -> (中文, 备选中文)) 查找表

    同一术语可能出现在多个分类中（如 Token 在 AI 和安全分类中含义不同），
    此函数会聚合所有中文翻译，避免后出现的覆盖先出现的。

    Args:
        data: load_terminology 返回的字典。

    Returns:
        字典，键为英文术语小写，值为 (中文翻译, 备选翻译)。
        备选翻译可能包含多个值，用 "|" 分隔。
    """
    lookup: Dict[str, Tuple[str, Optional[str]]] = {}
    for _cat_key, cat in data.get("categories", {}).items():
        for en, info in cat.get("terms", {}).items():
            cn = info.get("cn", "")
            alt = info.get("alt")
            key = en.lower()
            if key in lookup:
                existing_cn, existing_alt = lookup[key]
                all_alts: set[str] = set()
                if existing_alt:
                    all_alts.update(existing_alt.split("|"))
                if cn and cn != existing_cn:
                    all_alts.add(cn)
                if alt:
                    all_alts.add(alt)
                lookup[key] = (existing_cn, "|".join(sorted(all_alts)) if all_alts else None)
            else:
                lookup[key] = (cn, alt)
    return lookup


def build_detailed_lookup(data: Dict) -> Dict[str, Dict]:
    """构建包含完整信息的术语查找表

    Args:
        data: load_terminology 返回的字典。

    Returns:
        字典，键为英文术语小写，值为包含 en/cn/keep_en/alt/note 的字典。
    """
    lookup = {}
    for _cat_key, cat in data.get("categories", {}).items():
        for en, info in cat.get("terms", {}).items():
            lookup[en.lower()] = {
                "en": en,
                "cn": info.get("cn", ""),
                "keep_en": info.get("keep_en", False),
                "alt": info.get("alt"),
                "note": info.get("note"),
            }
    return lookup


# === 位置判断 ===

def _parse_fence(stripped: str) -> Tuple[Optional[str], int, str]:
    """解析一行是否为围栏标记

    支持 CommonMark 规范的两种围栏字符：反引号(`) 和波浪号(~)。

    Args:
        stripped: 已去除首尾空白的行文本。

    Returns:
        (fence_char, fence_len, rest) 或 (None, 0, "") 若非围栏。
        fence_char: '`' 或 '~'；fence_len: 围栏字符数量；rest: 信息串。
    """
    for ch in ('`', '~'):
        count = len(stripped) - len(stripped.lstrip(ch))
        if count >= 3:
            rest = stripped[count:].strip()
            # 反引号围栏的信息串不能包含反引号
            if ch == '`' and '`' in rest:
                continue
            return (ch, count, rest)
    return (None, 0, "")


def is_in_code_block(lines: List[str], line_number: int) -> bool:
    """检查指定行是否在代码块内

    支持 CommonMark 变长代码围栏（反引号 ` 和波浪号 ~）。
    闭合围栏必须使用与开启围栏相同的字符，且长度 >= 开启围栏。
    例如 ````markdown ... ```` 内部的 ```bash 不会被误判为闭合。

    Args:
        lines: 文档的行列表。
        line_number: 行号，从 1 开始。

    Returns:
        True 表示在代码块内。
    """
    in_code = False
    fence_char = None
    fence_len = 0
    for i, line in enumerate(lines, 1):
        if i > line_number:
            break
        stripped = line.strip()
        ch, count, rest = _parse_fence(stripped)
        if ch is None:
            continue
        if not in_code:
            # 开启围栏：>=3 个围栏字符，可带信息串
            in_code = True
            fence_char = ch
            fence_len = count
        else:
            # 闭合围栏：同种字符、纯围栏字符（无信息串）、长度 >= 开启围栏
            if ch == fence_char and rest == "" and count >= fence_len:
                in_code = False
    return in_code


def is_frontmatter(lines: List[str], line_number: int) -> bool:
    """检查指定行是否在 YAML frontmatter 区域内

    Args:
        lines: 文档的行列表。
        line_number: 行号，从 1 开始。

    Returns:
        True 表示在 frontmatter 内。
    """
    if len(lines) < 2 or lines[0].strip() != "---":
        return False
    second_dash = -1
    for i, line in enumerate(lines[1:], 1):
        if line.strip() == "---":
            second_dash = i
            break
    if second_dash == -1:
        return False
    return 1 <= line_number <= second_dash


def _is_in_html_comment(lines: List[str], line_number: int) -> bool:
    """检查指定行是否在 HTML 注释 <!-- --> 内

    Args:
        lines: 文档的行列表。
        line_number: 行号，从 1 开始。

    Returns:
        True 表示在 HTML 注释内。
    """
    in_comment = False
    for i, line in enumerate(lines, 1):
        if i > line_number:
            break
        if not in_comment:
            start = line.find('<!--')
            while start != -1:
                end = line.find('-->', start + 4)
                if end != -1:
                    # 单行内闭合注释
                    start = line.find('<!--', end + 3)
                else:
                    # 跨行注释开始
                    in_comment = True
                    break
        else:
            if '-->' in line:
                in_comment = False
    return in_comment


def should_skip(lines: List[str], line_number: int) -> bool:
    """判断指定行是否应跳过检查（在 frontmatter 或代码块内）

    Args:
        lines: 文档的行列表。
        line_number: 行号，从 1 开始。

    Returns:
        True 表示应跳过该行。
    """
    return is_frontmatter(lines, line_number) or is_in_code_block(lines, line_number) or _is_in_html_comment(lines, line_number)


def find_frontmatter_end(lines: List[str]) -> int:
    """找到 frontmatter 结束行的索引（0-based）

    Args:
        lines: 文档的行列表。

    Returns:
        frontmatter 结束行的索引，如果没有 frontmatter 则返回 0。
    """
    if not lines or lines[0].strip() != "---":
        return 0
    for i, line in enumerate(lines[1:], 1):
        if line.strip() == "---":
            return i
    return 0


def is_in_latex(line: str, col: int) -> bool:
    """检查指定列位置是否在 LaTeX 公式内

    通过找出所有 $...$ 和 $$...$$ 区间，判断 col 是否落在某个区间内。

    Args:
        line: 行文本。
        col: 列位置（0-based）。

    Returns:
        True 表示在 LaTeX 公式内。
    """
    # 收集所有 LaTeX 区间 [open, close)
    spans: list[tuple[int, int]] = []
    i = 0
    while i < len(line):
        if line[i] == '$':
            if i + 1 < len(line) and line[i + 1] == '$':
                # $$ 块级公式
                close = line.find('$$', i + 2)
                if close != -1:
                    spans.append((i, close + 2))
                    i = close + 2
                    continue
                else:
                    # 未闭合 $$，col 在 $$ 之后算在公式内
                    if col > i + 1:
                        return True
                    i += 2
                    continue
            else:
                # $ 行内公式
                close = line.find('$', i + 1)
                if close != -1:
                    spans.append((i, close + 1))
                    i = close + 1
                    continue
                else:
                    # 未闭合 $
                    if col > i:
                        return True
                    i += 1
                    continue
        i += 1

    for start, end in spans:
        if start < col < end:
            return True
    return False


def is_in_inline_code(line: str, col: int) -> bool:
    """检查指定列位置是否在行内代码内

    支持 CommonMark 多反引号行内代码，例如 ``literal `backtick` ``。
    反引号串长度匹配规则：开启的 N 个反引号必须由恰好 N 个反引号关闭。

    Args:
        line: 行文本。
        col: 列位置（0-based）。

    Returns:
        True 表示在行内代码内。
    """
    i = 0
    while i < len(line):
        if line[i] == '`':
            # 计算连续反引号数量（开启标记）
            open_start = i
            while i < len(line) and line[i] == '`':
                i += 1
            tick_count = i - open_start
            # 查找恰好相同数量的闭合反引号
            close_start = -1
            j = i
            while j < len(line):
                if line[j] == '`':
                    cs = j
                    while j < len(line) and line[j] == '`':
                        j += 1
                    if j - cs == tick_count:
                        close_start = cs
                        break
                else:
                    j += 1
            if close_start == -1:
                # 未闭合，col 在反引号之后算在代码内
                return col >= open_start + tick_count
            # [open_start, close_start + tick_count) 是一个代码跨度
            if open_start + tick_count <= col < close_start:
                return True
            i = close_start + tick_count
        else:
            i += 1
    return False


def count_consecutive_blank_lines(lines: List[str]) -> List[Tuple[int, int]]:
    """找到连续空行超过 2 行的位置

    Args:
        lines: 文档的行列表。

    Returns:
        列表，每项为 (起始行号, 连续空行数)，行号从 1 开始。
    """
    results = []
    count = 0
    start = 0
    for i, line in enumerate(lines):
        if line.strip() == "":
            if count == 0:
                start = i + 1
            count += 1
        else:
            if count > 2:
                results.append((start, count))
            count = 0
    if count > 2:
        results.append((start, count))
    return results
