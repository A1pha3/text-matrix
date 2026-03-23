from __future__ import annotations

import argparse
import os
import re
import tempfile
from datetime import datetime
from pathlib import Path
from typing import NamedTuple


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
    return parser.parse_args()


def strip_bom_prefix(text: str) -> str:
    return text[1:] if text.startswith("\ufeff") else text


def has_front_matter(text: str) -> bool:
    text = strip_bom_prefix(text)
    text = text.lstrip("\n")
    return bool(re.match(r"^(\+\+\+|---)\s*$", text.splitlines()[0])) if text else False


def extract_title(text: str, file_path: Path) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            title = stripped[2:].strip().strip("#").strip()
            if title:
                return title
    return file_path.stem.replace("-", " ").replace("_", " ").strip().title()


def build_front_matter(title: str) -> str:
    now = datetime.now().astimezone().isoformat(timespec="seconds")
    safe_title = title.replace("'", "’")
    return f"+++\ndate = '{now}'\ndraft = false\ntitle = '{safe_title}'\n+++\n\n"


def normalize_line_endings(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n")


def needs_insert(file_path: Path) -> bool:
    if file_path.suffix.lower() != ".md":
        return False
    name = file_path.name.lower()
    if name in {"_index.md", "index.md"}:
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


def run(root: Path, dry_run: bool, recursive: bool) -> RunResult:
    pattern = "**/*.md" if recursive else "*.md"
    files = sorted([p for p in root.glob(pattern) if p.is_file() and needs_insert(p)])
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
        updated = build_front_matter(title) + original.lstrip("\n")
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
    root = Path(args.root)
    if not root.exists() or not root.is_dir():
        raise SystemExit(f"目录不存在: {root}")

    result = run(root=root, dry_run=args.dry_run, recursive=args.recursive)
    mode = "预览模式" if args.dry_run else "写入模式"
    print(f"{mode} 扫描 {result.total} 个 Markdown 文件，补齐 {result.changed} 个文件，失败 {result.failed} 个")
    if result.failed > 0:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
