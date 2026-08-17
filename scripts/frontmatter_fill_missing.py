"""frontmatter_fill_missing.py：批量补缺 ``slug`` 和 ``categories``。

为什么只补这两个？
-----------------
- ``slug``：从文件名推（小写英文 + 连字符），零歧义；Page Bundle 的
  ``index.md`` 取父目录名（文件名恒为 index，推出的是构建毒药 slug:index）。
- ``categories``：项目内已有稳定的子目录→分类映射（见 :data:`CATEGORY_BY_DIR`）。

``description`` 和 ``tags`` 必须读懂正文，由 LLM 或人工处理，本脚本不碰。

调用方式
--------
::

    uv run python scripts/frontmatter_fill_missing.py --root content
    uv run python scripts/frontmatter_fill_missing.py --root content --dry-run
    uv run python scripts/frontmatter_fill_missing.py --root content --target content/posts/tech/xxx.md
    uv run python scripts/frontmatter_fill_missing.py --root content --target content/posts/a.md content/posts/b.md
"""
from __future__ import annotations

import argparse
import os
import re
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import yaml

try:
    import tomllib as toml  # type: ignore[import-not-found]
except ModuleNotFoundError:  # pragma: no cover
    import tomli as toml  # type: ignore[import-untyped,no-redef]


# 子目录 → 默认 categories。最长前缀匹配。
CATEGORY_BY_DIR: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("posts/tech", ("技术笔记",)),
    ("posts/wealth", ("财富自由",)),
    ("posts/thoughts", ("思考与随笔",)),
    ("posts/video", ("视频精读",)),
    ("posts/news", ("行业快讯",)),
    ("docs", ("技术笔记",)),
)

# slug 合法字符：英文小写、数字、连字符
SLUG_VALID_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")


def default_categories_for(rel: Path) -> tuple[str, ...] | None:
    """根据文件相对路径返回默认 categories。"""
    rel_str = rel.as_posix()
    for needle, cats in CATEGORY_BY_DIR:
        if rel_str == needle or rel_str.startswith(needle + "/"):
            return cats
    return None


def slug_from_path(path: Path) -> str | None:
    """从文件路径推导 slug。

    单文件取文件名 stem；Page Bundle 的 ``index.md`` 文件名没有语义，必须取
    父目录名——否则会注入 ``slug: index``（lint 判 fatal 的构建毒药：所有这么
    写的页面争抢 ``.../index/index.html``，2026-08-06 实证事故，2026-08-17 审查
    发现本脚本正是注入源之一）。
    """
    if path.name == "index.md":
        stem = path.parent.name
    else:
        name = path.name
        stem = name[:-3] if name.endswith(".md") else name
    return stem if SLUG_VALID_RE.match(stem) else None


# ---------------------------------------------------------------------------
# frontmatter 解析 + 渲染
# ---------------------------------------------------------------------------

def _detect_fence(text: str) -> str | None:
    # 容忍 BOM 与开头空行，与 autofill/lint 的 strip_bom 行为对齐
    first = text.lstrip("\ufeff\n").split("\n", 1)[0].rstrip()
    return first if first in ("---", "+++") else None


def _split_fm(text: str) -> tuple[str, str, str, list[str], int] | None:
    """返回 ``(fence, frontmatter_text, body, lines, end)``。

    ``lines``/``end`` 供 :func:`apply` 按行区间重组文件——不要用
    ``str.replace(fm, new_fm, 1)`` 做手术：空 frontmatter 时 ``fm == ""``，
    ``replace("", x, 1)`` 会把字段插到文件第 0 个字符（opening fence 之前），
    frontmatter 整体失效、draft 闸门丢失（2026-08-17 对抗审查实证）。
    """
    fence = _detect_fence(text)
    if fence is None:
        return None
    lines = text.lstrip("\ufeff\n").splitlines()
    try:
        end = next(i for i, ln in enumerate(lines[1:], 1) if ln.rstrip() == fence)
    except StopIteration:
        return None
    fm = "\n".join(lines[1:end])
    body = "\n".join(lines[end + 1 :])
    return fence, fm, body, lines, end


def _parse(fence: str, fm: str) -> dict[str, object] | None:
    """解析 frontmatter；结果不是键值映射（fence 之间是正文等）时返回 None。

    调用方必须判 None：对 str 做 ``"slug" not in data`` 是子串匹配，
    会把字段注入正文（2026-08-17 对抗审查：正文以 ``---`` 水平线开头的
    无 frontmatter 文件被当成有 frontmatter）。
    """
    loaded = yaml.safe_load(fm) if fence == "---" else toml.loads(fm)
    if loaded is None:
        return {}
    if not isinstance(loaded, dict):
        return None
    return loaded


def _indent_for(fm: str) -> str:
    """从已有 title/draft 行推断缩进。"""
    for line in fm.splitlines():
        m = re.match(r"^(\s*)[A-Za-z_][\w-]*\s*:", line)
        if m:
            return m.group(1)
    return ""


# 这些裸值会被 YAML 1.1 解析成 bool/null——slug: yes 会变成 True
_YAML_BARE_UNSAFE_RE = re.compile(
    r"^(?:~|null|Null|NULL|true|True|false|False|yes|Yes|no|No|on|On|off|Off"
    r"|[+-]?\d+(?:\.\d+)?)$"
)


def _yaml_scalar(value: str) -> str:
    if _YAML_BARE_UNSAFE_RE.match(value):
        return f'"{value}"'
    if not value or re.search(r'[:\n"#&*?|<>=!%@`[\]{}]', value):
        escaped = value.replace("\\", "\\\\").replace('"', '\\"')
        return f'"{escaped}"'
    return value


def _yaml_list(values: list[str]) -> str:
    return "[" + ", ".join(_yaml_scalar(v) for v in values) + "]"


def _toml_scalar(value: str) -> str:
    if "'" not in value and "\n" not in value:
        return f"'{value}'"
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def _toml_list(values: list[str]) -> str:
    return "[" + ", ".join(_toml_scalar(v) for v in values) + "]"


@dataclass
class FillResult:
    path: Path
    added: dict[str, object]   # 实际写入的新字段
    skipped: list[str]          # 未补的理由

    @property
    def changed(self) -> bool:
        return bool(self.added)


def fill_one(path: Path, root: Path) -> FillResult:
    """计算要补的字段 + 渲染好的新 frontmatter。返回的 ``path`` 不做实际写入。"""
    rel = path.relative_to(root)
    text = path.read_text(encoding="utf-8")
    split = _split_fm(text)
    if split is None:
        return FillResult(path, {}, ["没有 frontmatter"])
    fence, fm, _body, _lines, _end = split
    data = _parse(fence, fm)
    if data is None:
        return FillResult(path, {}, ["frontmatter 解析结果不是键值映射，跳过（可能是正文水平线被误认）"])

    added: dict[str, object] = {}
    skipped: list[str] = []

    if "slug" not in data or data["slug"] in (None, ""):
        candidate = slug_from_path(path)
        if candidate:
            added["slug"] = candidate
        else:
            skipped.append("slug (文件名不是英文小写连字符，跳过)")
    else:
        skipped.append("slug (已有)")

    if "categories" not in data or data["categories"] in (None, [], ""):
        cats = default_categories_for(rel)
        if cats:
            added["categories"] = list(cats)
        else:
            skipped.append("categories (子目录无默认映射，跳过)")
    else:
        skipped.append("categories (已有)")

    return FillResult(path, added, skipped)


def render_fm(fence: str, fm: str, added: dict[str, object]) -> str:
    """把要补的字段追加到 frontmatter 末尾，保持原有 fence/缩进风格。"""
    indent = _indent_for(fm)
    assignment = ":" if fence == "---" else "="
    new_lines: list[str] = []
    for key, value in added.items():
        if key == "categories":
            rendered = _yaml_list(value) if fence == "---" else _toml_list(value)
        else:  # slug
            rendered = _yaml_scalar(value) if fence == "---" else _toml_scalar(value)
        new_lines.append(f"{indent}{key} {assignment} {rendered}")
    # fm 为空（---\n---）时不得产生前导空行，否则字段行会漂到空行后
    base = fm.rstrip()
    return f"{base}\n" + "\n".join(new_lines) + "\n" if base else "\n".join(new_lines) + "\n"


def write_atomic(path: Path, text: str) -> None:
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", newline="\n",
        dir=path.parent, delete=False,
        prefix=f".{path.name}.", suffix=".tmp",
    ) as tmp:
        tmp.write(text)
        os.replace(tmp.name, path)


def apply(path: Path, root: Path, dry_run: bool) -> FillResult:
    """计算改动 + 实际写盘（或仅打印）。"""
    result = fill_one(path, root)
    if not result.changed:
        return result
    rel = path.relative_to(root)
    verb = "将补" if dry_run else "已补"
    print(f"[{verb} ] {rel}")
    for k, v in result.added.items():
        print(f"   + {k}: {v!r}")
    if dry_run:
        return result

    text = path.read_text(encoding="utf-8")
    split = _split_fm(text)
    if split is None:
        print(f"   ! 写入失败: frontmatter 丢失", file=sys.stderr)
        return result
    fence, fm, _body, lines, end = split
    if _parse(fence, fm) is None:
        print(f"   ! 写入失败: frontmatter 不是键值映射", file=sys.stderr)
        return result
    new_fm = render_fm(fence, fm, result.added)
    # 按行区间重组：opening fence + 新 fm（render_fm 已含旧内容）+ closing fence
    # 起的原文。splitlines 会丢掉文件末尾换行，按原样补回
    trailing = "\n" if text.endswith("\n") else ""
    new_text = lines[0] + "\n" + new_fm + "\n".join(lines[end:]) + trailing
    write_atomic(path, new_text)
    return result


def iter_targets(root: Path, explicit: Iterable[Path] | None) -> list[Path]:
    if explicit:
        result = []
        for t in explicit:
            if not t.is_file() or t.suffix != ".md":
                continue
            try:
                # 验证文件在 root 子树中
                t.relative_to(root)
                result.append(t)
            except ValueError:
                print(f"[warn] {t} 不在根目录 {root} 下，跳过", file=sys.stderr)
        return result
    return sorted(p for p in root.rglob("*.md") if p.is_file())


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--root", default="content")
    p.add_argument(
        "--target",
        action="extend",
        nargs="+",
        default=[],
    )
    p.add_argument("--dry-run", action="store_true")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    root = Path(args.root).resolve()
    if not root.exists():
        print(f"[fill-missing] root 不存在: {root}", file=sys.stderr)
        return 1
    explicit = [Path(t).resolve() for t in args.target] if args.target else None
    targets = iter_targets(root, explicit)

    changed = 0
    failed = 0
    for path in targets:
        try:
            result = apply(path, root, dry_run=args.dry_run)
        except Exception as exc:
            failed += 1
            try:
                rel = path.relative_to(root)
            except ValueError:
                rel = path
            print(f"[ERR ] {rel}: {exc}")
            continue
        if result.changed:
            changed += 1

    mode = "预览" if args.dry_run else "写入"
    print(f"\n[fill-missing] {mode} {len(targets)} 个文件，补 {changed} 个，失败 {failed} 个")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
