#!/usr/bin/env python3
"""阻止项目模板使用云端旧 Hugo 不支持的语言 API。"""

from pathlib import Path
import sys


TEMPLATE_ROOT = Path("layouts")
FORBIDDEN_APIS = (".Site.Language.Locale",)
TEMPLATE_SUFFIXES = {".html", ".xml"}


def main() -> int:
    violations: list[str] = []
    for path in TEMPLATE_ROOT.rglob("*"):
        if not path.is_file() or path.suffix not in TEMPLATE_SUFFIXES:
            continue
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            for api in FORBIDDEN_APIS:
                if api in line:
                    violations.append(f"{path}:{line_number}: 不兼容的 Hugo API {api}")

    if violations:
        print("Hugo 模板兼容性校验失败：", file=sys.stderr)
        print("\n".join(violations), file=sys.stderr)
        return 1

    print("Hugo 模板兼容性校验通过")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
