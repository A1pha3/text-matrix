#!/usr/bin/env python3
"""Check that a copied cn-doc-writer skill has not drifted from the source."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import NamedTuple


IGNORED_DIRS = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "__pycache__",
}
IGNORED_NAMES = {".DS_Store"}
IGNORED_SUFFIXES = {".pyc", ".pyo"}


class SyncResult(NamedTuple):
    """Directory comparison result."""

    missing: list[str]
    extra: list[str]
    different: list[str]

    @property
    def is_clean(self) -> bool:
        return not (self.missing or self.extra or self.different)


def should_ignore(rel_path: Path) -> bool:
    """Return True for generated cache files that should not affect sync."""
    if any(part in IGNORED_DIRS for part in rel_path.parts):
        return True
    if rel_path.name in IGNORED_NAMES:
        return True
    return rel_path.suffix in IGNORED_SUFFIXES


def iter_skill_files(root: Path) -> list[str]:
    """Return comparable skill file paths relative to root."""
    files: list[str] = []
    for path in root.rglob("*"):
        rel_path = path.relative_to(root)
        if should_ignore(rel_path):
            continue
        if path.is_file():
            files.append(rel_path.as_posix())
    return sorted(files)


def compare_skill_dirs(source: Path | str, target: Path | str) -> SyncResult:
    """Compare source skill with target copy.

    The first argument is always the canonical source version. The target is a
    copy that should be synchronized from source, never the other way around.
    """
    source_root = Path(source)
    target_root = Path(target)
    if not source_root.is_dir():
        raise NotADirectoryError(f"Source skill directory not found: {source_root}")
    if not target_root.is_dir():
        raise NotADirectoryError(f"Target skill directory not found: {target_root}")

    source_files = set(iter_skill_files(source_root))
    target_files = set(iter_skill_files(target_root))
    missing = sorted(source_files - target_files)
    extra = sorted(target_files - source_files)
    common = sorted(source_files & target_files)
    different = [
        rel_path
        for rel_path in common
        if (source_root / Path(rel_path)).read_bytes()
        != (target_root / Path(rel_path)).read_bytes()
    ]
    return SyncResult(missing=missing, extra=extra, different=different)


def format_result(result: SyncResult, source: Path, target: Path) -> str:
    if result.is_clean:
        return (
            "cn-doc-writer sync guard passed: target copy matches source.\n"
            f"source: {source}\n"
            f"target: {target}"
        )

    lines = [
        "cn-doc-writer sync guard failed: target copy drifted from source.",
        f"source: {source}",
        f"target: {target}",
        "Treat source as canonical; sync target from source after review.",
    ]
    for label, paths in [
        ("missing in target", result.missing),
        ("extra in target", result.extra),
        ("different content", result.different),
    ]:
        if paths:
            lines.append(f"\n{label}:")
            lines.extend(f"  - {path}" for path in paths)
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Compare canonical prompt_alpha cn-doc-writer with a copied "
            "cn-doc-writer skill and fail on drift."
        )
    )
    parser.add_argument(
        "source",
        type=Path,
        help="Canonical source skill directory, usually prompt_alpha/.../cn-doc-writer",
    )
    parser.add_argument(
        "target",
        type=Path,
        help="Copied skill directory, usually text-matrix/skills/cn-doc-writer",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    result = compare_skill_dirs(args.source, args.target)
    print(format_result(result, args.source, args.target))
    return 0 if result.is_clean else 1


if __name__ == "__main__":
    raise SystemExit(main())
