from __future__ import annotations

import argparse
import os
import re
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Iterable, NamedTuple


class RunResult(NamedTuple):
    total: int
    changed: int
    failed: int


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default="content")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--recursive", dest="recursive", action="store_true", default=True)
    parser.add_argument("--no-recursive", dest="recursive", action="store_false")
    parser.add_argument(
        "--target",
        action="extend",
        nargs="+",
        default=[],
        help="显式指定要处理的文件（可多个）；传入后不再全量扫描（pre-commit 增量场景）",
    )
    parser.add_argument(
        "--live",
        action="store_true",
        help="补全出的 frontmatter 写 draft = false（存量回填专用）；"
        "默认 draft = true——发布闸门是 draft 布尔位，自动补全不得替它翻闸",
    )
    return parser.parse_args()


def strip_bom_prefix(text: str) -> str:
    return text[1:] if text.startswith("\ufeff") else text


def has_front_matter(text: str) -> bool:
    text = strip_bom_prefix(text)
    text = text.lstrip("\n")
    return bool(re.match(r"^(\+\+\+|---)\s*$", text.splitlines()[0])) if text else False


def extract_title(text: str, file_path: Path) -> str:
    in_code = False
    for line in text.splitlines():
        stripped = line.strip()
        # 跳过 fenced code block：代码里的 `# 注释` 不是标题
        # （2026-08-17 对抗审查：正文以代码块开头的文件曾把注释抓成 title）
        if stripped.startswith("```") or stripped.startswith("~~~"):
            in_code = not in_code
            continue
        if in_code:
            continue
        if stripped.startswith("# "):
            title = stripped[2:].strip().strip("#").strip()
            if title:
                return title
    return file_path.stem.replace("-", " ").replace("_", " ").strip().title()


def build_front_matter(title: str, live: bool = False) -> str:
    now = datetime.now().astimezone().isoformat(timespec="seconds")
    safe_title = title.replace("'", "’")
    # 默认 draft = true：无 frontmatter 的文件可能是未审半成品，draft 布尔位是
    # 发布唯一闸门，自动补全不得替它翻闸（2026-08-17 对抗审查：draft=false 默认值
    # 与钩子全量 git add 联级可绕过评分闸静默发版）。存量回填确认要上线用 --live。
    draft = "false" if live else "true"
    return f"+++\ndate = '{now}'\ndraft = {draft}\ntitle = '{safe_title}'\n+++\n\n"


def normalize_line_endings(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n")


def needs_insert(file_path: Path) -> bool:
    if file_path.suffix.lower() != ".md":
        return False
    name = file_path.name.lower()
    # 只跳 section 索引页。Page Bundle 文章的 index.md 是普通文章页，同样需要
    # autofill——08-16 前此处误跳 index.md，导致 52 篇 bundle 期文章漏补字段
    # （knockoutez 篇缺 slug 即实证，拍平后才补上）。
    if name == "_index.md":
        return False
    return True


def write_text_atomic(path: Path, text: str) -> None:
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        newline="\n",
        dir=path.parent,
        delete=False,
        prefix=f".{path.name}.",
        suffix=".tmp",
    ) as tmp:
        tmp.write(text)
        temp_name = tmp.name
    os.replace(temp_name, path)


def iter_files(root: Path, recursive: bool, targets: Iterable[Path] | None) -> list[Path]:
    """枚举待处理文件：targets 非空时只处理显式指定的（pre-commit 增量场景）。"""
    if targets:
        result = []
        for t in targets:
            if not t.is_file():
                continue
            try:
                t.relative_to(root)
            except ValueError:
                print(f"[warn] {t} 不在根目录 {root} 下，跳过", file=sys.stderr)
                continue
            result.append(t)
        return sorted(result)
    pattern = "**/*.md" if recursive else "*.md"
    return sorted([p for p in root.glob(pattern) if p.is_file()])


def run(
    root: Path,
    dry_run: bool,
    recursive: bool,
    targets: Iterable[Path] | None = None,
    live: bool = False,
) -> RunResult:
    files = [p for p in iter_files(root, recursive, targets) if needs_insert(p)]
    changed = 0
    failed = 0

    for path in files:
        try:
            original = normalize_line_endings(path.read_text(encoding="utf-8"))
        except Exception as exc:
            failed += 1
            print(f"读取失败: {path} ({exc})")
            continue

        if has_front_matter(original):
            continue

        title = extract_title(original, path)
        updated = build_front_matter(title, live=live) + original.lstrip("\n")
        changed += 1

        if not dry_run:
            try:
                write_text_atomic(path, updated)
            except Exception as exc:
                failed += 1
                changed -= 1
                print(f"写入失败: {path} ({exc})")

    return RunResult(total=len(files), changed=changed, failed=failed)


def main() -> None:
    args = parse_args()
    root = Path(args.root).resolve()
    if not root.exists() or not root.is_dir():
        raise SystemExit(f"目录不存在: {root}")

    targets = [Path(t).resolve() for t in args.target] if args.target else None
    result = run(
        root=root,
        dry_run=args.dry_run,
        recursive=args.recursive,
        targets=targets,
        live=args.live,
    )
    mode = "预览模式" if args.dry_run else "写入模式"
    print(f"{mode} 扫描 {result.total} 个 Markdown 文件，补齐 {result.changed} 个文件，失败 {result.failed} 个")
    if result.failed > 0:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
