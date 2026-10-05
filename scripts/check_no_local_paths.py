#!/usr/bin/env python3
"""检查 content/ 中是否泄漏本机真实路径（部署门禁，stdlib-only）。

内部产物（审核报告、反写笔记等）若混入 content/ 会把构建机绝对路径
发布到公网。本检查只针对**本机真实前缀**，文档里常见的示例路径
（/Users/demo、/Users/username、/Users/alice 等）不在拦截范围内，
避免误伤教程代码。

用法:
    python3 scripts/check_no_local_paths.py [--content-dir content]

退出码: 发现泄漏返回 1（供 CI 卡点），否则 0。
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# 本机真实路径前缀：出现即泄漏。新增构建机/用户时在此追加。
FORBIDDEN_PREFIXES = (
    "/Volumes/mini_matrix",
    "/Volumes/damon",
    "/Users/damon",
    "/Users/matrix",
)


def scan(content_dir: Path) -> list[tuple[str, int, str]]:
    hits: list[tuple[str, int, str]] = []
    for path in sorted(content_dir.rglob("*.md")):
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            print(f"warn: 无法读取 {path}: {exc}", file=sys.stderr)
            continue
        for lineno, line in enumerate(text.splitlines(), 1):
            for prefix in FORBIDDEN_PREFIXES:
                if prefix in line:
                    hits.append((str(path), lineno, line.strip()[:120]))
                    break  # 一行报一次即可
    return hits


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--content-dir", default="content")
    args = ap.parse_args()

    hits = scan(Path(args.content_dir))
    if not hits:
        print(f"[no-local-paths] 检查通过：{args.content_dir}/ 下无本机路径泄漏")
        return 0

    print(f"[no-local-paths] 发现 {len(hits)} 处本机路径泄漏：", file=sys.stderr)
    for path, lineno, line in hits:
        print(f"  {path}:{lineno}\n      {line}", file=sys.stderr)
    print("\n请把这些内容移出 content/（内部产物放 docs/）或改写为通用路径。", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
