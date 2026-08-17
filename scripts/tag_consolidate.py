#!/usr/bin/env python3
"""标签词表收敛：归一化写法变体 + 语义合并 + 删除低频/零信息标签。

用法:
    python3 scripts/tag_consolidate.py          # dry-run, 只输出统计
    python3 scripts/tag_consolidate.py --apply  # 实际写盘

规则:
    1. 归一化: 大小写/空格/连字符/斜杠/点号差异的变体合并到簇内最高频写法
       (可被 CLUSTER_CANONICAL 覆盖).
    2. 语义合并: SEMANTIC_MAP 中的明显同义词合并; DELETE_TAGS 直接删除.
    3. 长尾清理: 合并后全站使用次数 <= MIN_COUNT 的标签从 frontmatter 删除.
    4. 例外: EXACT_KEEP 中的标签原样保留, 不参与任何合并 (如 ReAct 范式).
"""

import collections
import os
import re
import sys
import tempfile

import yaml

try:
    import tomllib as toml  # type: ignore[import-not-found]
except ModuleNotFoundError:  # pragma: no cover
    import tomli as toml  # type: ignore[import-untyped,no-redef]

MIN_COUNT = 2  # 删除合并后使用次数 <= 2 的标签

# 簇级别的规范写法覆盖 (归一化键 -> 规范标签)
CLUSTER_CANONICAL = {
    "ai编程": "AI 编程",
    "ai工具": "AI 工具",
    "ai安全": "AI 安全",
    "huggingface": "Hugging Face",
    "vscode": "VS Code",
    "vibecoding": "Vibe Coding",
    "awesomelist": "Awesome List",
    "sideproject": "Side Project",
    "swebench": "SWE-bench",
}

# 精确匹配的语义合并 (在簇归一化之前优先生效)
SEMANTIC_MAP = {
    "Agent": "AI Agent",
    "大模型": "LLM",
    "AI Coding": "AI 编程",
    "AI编程助手": "AI 编程",
    "AI 编程助手": "AI 编程",
    "Prompt工程": "Prompt Engineering",
    "prompt工程": "Prompt Engineering",
    "Agent Skill": "Agent Skills",
    "AgentSkill": "Agent Skills",
    "agent-skill": "Agent Skills",
    "AgentSkills": "Agent Skills",
}

DELETE_TAGS = {"AI"}

EXACT_KEEP = {"ReAct"}


def norm(tag):
    return re.sub(r"[\s\-_/\.]+", "", tag.lower())


def parse_inline_list(raw, style):
    """解析单行 inline 列表 ``["a", "b"]``，返回标签列表；解析失败返回 None。

    裸 ``split(",")`` 不理解引号，会把 ``"a, b"`` 劈成两个标签再写回
    （2026-08-17 对抗审查），必须走真正的 YAML/TOML 解析。
    """
    try:
        if style == "yaml":
            value = yaml.safe_load(raw)
        else:
            value = toml.loads("tags = " + raw)["tags"]
    except Exception:
        return None
    if not isinstance(value, list):
        return None
    return [str(x).strip() for x in value if str(x).strip()]


def _quote_tag(tag):
    escaped = tag.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def write_atomic(path, text):
    fd, tmp = tempfile.mkstemp(
        dir=os.path.dirname(path) or ".", prefix=".tag_consolidate.", suffix=".tmp"
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def parse_frontmatter(text):
    """返回 (kind, full_match_span, tags, tag_span) 或 None。

    kind: 'yaml-inline' | 'yaml-dash' | 'toml'
    tag_span 是可整体替换的字符区间 (相对于全文).
    """
    m = re.match(r"^(---|\+\+\+)\n(.*?)\n\1", text, re.S)
    if not m:
        return None
    fm_start = m.start(2)
    fm = m.group(2)

    # YAML inline: tags: ["a", "b"]
    t = re.search(r"^tags:[ \t]*(\[[^\n]*\])[ \t]*$", fm, re.M)
    if t:
        tags = parse_inline_list(t.group(1), style="yaml")
        if tags is None:
            return None
        return ("yaml-inline", m.span(2), tags,
                (fm_start + t.start(), fm_start + t.end()))

    # YAML dash list: tags:\n  - a\n  - b
    t = re.search(r"^tags:\s*\n((?:\s+-\s+.*\n?)+)", fm, re.M)
    if t:
        tags = re.findall(r"^\s+-\s+(.*?)\s*$", t.group(1), re.M)
        tags = [x.strip("\"'") for x in tags]
        end = fm_start + t.end()
        # 不把块末尾的换行计入替换区间, 避免与后续键粘连
        while end > fm_start + t.start() and m.string[end - 1] == "\n":
            end -= 1
        return ("yaml-dash", m.span(2), tags,
                (fm_start + t.start(), end))

    # TOML inline: tags = ['a', 'b']
    t = re.search(r"^tags[ \t]*=[ \t]*(\[[^\n]*\])[ \t]*$", fm, re.M)
    if t:
        tags = parse_inline_list(t.group(1), style="toml")
        if tags is None:
            return None
        return ("toml", m.span(2), tags,
                (fm_start + t.start(), fm_start + t.end()))

    return None


def collect_files(root="content"):
    for dirpath, _, files in os.walk(root):
        for f in sorted(files):
            if f.endswith(".md"):
                yield os.path.join(dirpath, f)


def main():
    apply = "--apply" in sys.argv

    # 第一遍: 收集全部标签, 建立簇
    file_data = {}
    raw_counter = collections.Counter()
    skipped = []
    for path in collect_files():
        try:
            text = open(path, encoding="utf-8").read()
        except (UnicodeDecodeError, UnicodeError):
            skipped.append(path)
            continue
        parsed = parse_frontmatter(text)
        if not parsed:
            continue
        kind, fm_span, tags, tag_span = parsed
        file_data[path] = (kind, tags, tag_span, text)
        for t in tags:
            if t:
                raw_counter[t] += 1

    clusters = collections.defaultdict(list)
    for t, c in raw_counter.items():
        clusters[norm(t)].append((t, c))

    # 簇规范形: 最高频变体, 或 CLUSTER_CANONICAL 覆盖
    cluster_canon = {}
    for k, variants in clusters.items():
        if k in CLUSTER_CANONICAL:
            cluster_canon[k] = CLUSTER_CANONICAL[k]
        else:
            cluster_canon[k] = max(variants, key=lambda x: x[1])[0]

    def canonical(tag):
        if tag in EXACT_KEEP:
            return tag
        if tag in SEMANTIC_MAP:
            return SEMANTIC_MAP[tag]
        canon = cluster_canon.get(norm(tag), tag)
        # 簇归一化后再过一遍语义表 (如簇规范形是 "大模型")
        return SEMANTIC_MAP.get(canon, canon)

    # 第二遍: 计算合并后的最终频次
    final_counter = collections.Counter()
    for path, (kind, tags, _, _) in file_data.items():
        mapped = set()
        for t in tags:
            if not t:
                continue
            c = canonical(t)
            if c in DELETE_TAGS:
                continue
            mapped.add(c)
        for c in mapped:
            final_counter[c] += 1

    keep_tags = {t for t, c in final_counter.items() if c > MIN_COUNT}

    # 第三遍: 生成每文件的新 tags
    changes = []
    for path, (kind, tags, tag_span, text) in sorted(file_data.items()):
        new_tags = []
        for t in tags:
            if not t:
                continue
            c = canonical(t)
            if c in DELETE_TAGS or c not in keep_tags:
                continue
            if c not in new_tags:
                new_tags.append(c)
        if new_tags != tags:
            changes.append((path, kind, tags, new_tags, tag_span, text))

    # 统计输出
    print(f"扫描文件: {len(file_data)} (跳过无法解码: {len(skipped)})")
    for p in skipped:
        print(f"  SKIP {p}")
    print(f"原始标签: {len(raw_counter)} 个 / {sum(raw_counter.values())} 次")
    print(f"合并后标签: {len(final_counter)} 个")
    print(f"阈值 <= {MIN_COUNT} 次删除后保留: {len(keep_tags)} 个")
    print(f"需要改动的文件: {len(changes)}")
    removed_usages = sum(c for t, c in final_counter.items() if c <= MIN_COUNT)
    print(f"删除的低频标签使用次数: {removed_usages}")

    print("\n== 变更示例 (前 10 个文件) ==")
    for path, kind, old, new, _, _ in changes[:10]:
        print(f"\n{path}")
        print(f"  - {old}")
        print(f"  + {new}")

    if not apply:
        print("\n(dry-run, 加 --apply 才会写盘)")
        return

    for path, kind, old, new, (s, e), text in changes:
        inner = ", ".join(_quote_tag(t) for t in new)
        replacement = f"tags = [{inner}]" if kind == "toml" else f"tags: [{inner}]"
        out = text[:s] + replacement + text[e:]
        write_atomic(path, out)
    print(f"\n已写盘 {len(changes)} 个文件")


if __name__ == "__main__":
    main()
