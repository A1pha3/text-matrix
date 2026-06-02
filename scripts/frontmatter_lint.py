"""Frontmatter lint 脚本：预防 content/**/*.md 的 frontmatter 把 Hugo 构建卡住。

设计动机
--------
历史教训：2026-06-02 的 Netlify 构建因为
``description: "…不是"又一个 Agent 框架"…"`` 中内嵌了
未转义的 ASCII 双引号 (U+0022) 触发
``yaml: line 3: did not find expected key``，整站构建挂掉。

本脚本做两件事：
1. **致命错误（exit 1）**：
   - frontmatter 整体解析失败（同时支持 YAML ``---`` 和 TOML ``+++``）
   - YAML 单行 ``key: "..."`` 字符串值内嵌未转义的 ASCII 双引号
2. **软警告（exit 0，可通过 ``--strict`` 升级为 fatal）**：
   - 缺关键字段（必填集合按文件类型分档：section 索引页 / 顶级单页 / 普通文章）
   - date 不是 Hugo 接受的时间戳格式

调用方式
--------
- 本地：
    ``uv run --with pyyaml python scripts/frontmatter_lint.py --root content``
- CI（GitHub Actions）：见 ``.github/workflows/hugo.yml`` 中 ``Lint frontmatter`` 步骤
- pre-commit：见 ``.githooks/pre-commit``，仅校验本次改动的文件
"""
from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Iterable

import yaml

# tomllib 是 Python 3.11+ 的标准库；老版本回退到 tomli
try:
    import tomllib as toml  # type: ignore[import-not-found]
except ModuleNotFoundError:  # pragma: no cover
    import tomli as toml  # type: ignore[import-untyped,no-redef]


# ---- 必填字段分档 ----------------------------------------------------------

# 普通文章页（posts/**\/*.md 且不是 _index.md）
ARTICLE_REQUIRED: tuple[str, ...] = (
    "title",
    "date",
    "slug",
    "description",
    "categories",
    "tags",
)

# section 索引页（_index.md）：title/description 视情况，但项目里目前都填了
INDEX_REQUIRED: tuple[str, ...] = (
    "title",
    "date",
    "description",
)

# 顶级单页（content/about.md、content/contact.md 等，不在 posts/ 下也不在 docs/）
# Hugo 用 front matter 控制 layout 即可，对字段没硬要求；只对 metadata 类核心字段做软提示
TOP_LEVEL_REQUIRED: tuple[str, ...] = (
    "title",
    "date",
    "description",
)


# 匹配 ``key: "value with possible \"escapes\"`` 这种单行双引号字符串。
# 不跨行、不处理 list-of-strings 缩进场景（那是另一类错误，靠 yaml.safe_load 兜底）。
DQ_STRING_RE = re.compile(
    r"""^(\s*[A-Za-z_][\w-]*\s*:\s*)"((?:\\.|[^"\\])*)"\s*$"""
)


@dataclass
class FileReport:
    """单文件的校验结果聚合。"""

    path: Path
    fatal: list[str] = field(default_factory=list)
    warn: list[str] = field(default_factory=list)

    def add_fatal(self, msg: str) -> None:
        self.fatal.append(msg)

    def add_warn(self, msg: str) -> None:
        self.warn.append(msg)

    @property
    def has_fatal(self) -> bool:
        return bool(self.fatal)


def strip_bom(text: str) -> str:
    return text[1:] if text.startswith("\ufeff") else text


def detect_fence(text: str) -> str | None:
    """识别 frontmatter 用的是 ``---`` (YAML) 还是 ``+++`` (TOML)。"""
    first = strip_bom(text).lstrip("\n").split("\n", 1)[0].rstrip()
    if first in ("---", "+++"):
        return first
    return None


def split_front_matter(text: str) -> tuple[str, str, str] | None:
    """切分 frontmatter。

    返回 (fence, frontmatter_text, body)；
    fence 是 ``"---"`` 或 ``"+++"``；格式错误或缺失返回 ``None``。
    """
    fence = detect_fence(text)
    if fence is None:
        return None
    lines = strip_bom(text).lstrip("\n").splitlines()
    try:
        end = next(
            i for i, ln in enumerate(lines[1:], start=1) if ln.rstrip() == fence
        )
    except StopIteration:
        return None
    body = "\n".join(lines[end + 1 :])
    return fence, "\n".join(lines[1:end]), body


def check_unterminated_quotes(fm: str) -> list[str]:
    """扫单行 ``key: "..."``，揪出 value 内未转义的 ASCII 双引号。"""
    issues: list[str] = []
    for ln_no, line in enumerate(fm.splitlines(), 1):
        m = DQ_STRING_RE.match(line)
        if not m:
            continue
        body = m.group(2)
        # 把合法的 \" 转义去掉再检测，避免误报
        unescaped = body.replace('\\"', "")
        if '"' in unescaped:
            issues.append(
                f"line {ln_no}: 双引号字符串内嵌未转义 ASCII 双引号 -> {line.strip()[:120]}"
            )
    return issues


def is_rfc3339_date(value: object) -> bool:
    """粗略判定时间戳是否符合 Hugo 接受的范围。

    Hugo 接受：纯日期 ``2026-05-24``、无时区 ``2026-04-11T23:01:28``、
    带时区 ``2026-04-11T23:01:28+08:00``、``Z`` 结尾的 UTC 时间等。
    """
    # yaml.safe_load 会把纯日期解析成 datetime.date 对象
    if isinstance(value, date):
        return True
    if not isinstance(value, str):
        return False
    if not re.match(
        r"^\d{4}-\d{2}-\d{2}([T ]\d{2}:\d{2}(:\d{2})?(\.\d+)?(Z|[+-]\d{2}:?\d{2})?)?$",
        value,
    ):
        return False
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return True


def parse_front_matter(fence: str, fm: str) -> dict[str, object]:
    """根据 fence 选用 YAML 或 TOML 解析。"""
    if fence == "---":
        loaded = yaml.safe_load(fm)
    else:
        loaded = toml.loads(fm)
    return loaded or {}


def required_keys_for(path: Path) -> tuple[str, ...]:
    """按文件路径判定必填字段集。"""
    name = path.name
    if name == "_index.md":
        return INDEX_REQUIRED
    parts = path.parts
    # 顶级单页：content/<name>.md（不再有子目录）
    # content/docs/<name>.md 视为顶级单页
    if "posts" not in parts:
        return TOP_LEVEL_REQUIRED
    return ARTICLE_REQUIRED


def lint_file(path: Path) -> FileReport:
    """对单个 md 文件做完整 frontmatter 校验。"""
    report = FileReport(path=path)
    try:
        raw = path.read_text(encoding="utf-8")
    except UnicodeDecodeError as e:
        report.add_fatal(f"文件不是 UTF-8 编码: {e}")
        return report

    split = split_front_matter(raw)
    if split is None:
        # 没有 frontmatter 是项目里少数文章的真实状态，提示但不算错
        report.add_warn("没有 frontmatter（--- 或 +++ 包裹）")
        return report

    fence, fm, _body = split

    # 致命 #1：frontmatter 解析失败
    try:
        data = parse_front_matter(fence, fm)
    except (yaml.YAMLError, toml.TOMLDecodeError) as e:
        report.add_fatal(f"frontmatter 解析失败: {e}")
        return report

    if not isinstance(data, dict):
        msg = f"frontmatter 顶层必须是 mapping，实际是 {type(data).__name__}"
        report.add_fatal(msg)
        return report

    # 致命 #2：YAML 单行字符串内嵌未转义引号（TOML 用 ``"...""`` 或 ``'''...'''``
    # 天然不会有这个问题，跨行字符串也很少出错，跳过 TOML 这一层）
    if fence == "---":
        for issue in check_unterminated_quotes(fm):
            report.add_fatal(issue)

    # 软警告：必填字段（按文件类型分档）
    for key in required_keys_for(path):
        if key not in data or data[key] in (None, "", []):
            report.add_warn(f"缺少字段: {key}")

    # 软警告：date 格式
    if "date" in data and not is_rfc3339_date(data["date"]):
        report.add_warn(f"date 不是 Hugo 接受的时间戳: {data['date']!r}")

    return report


def iter_markdown(root: Path, targets: Iterable[Path] | None) -> list[Path]:
    """枚举待校验文件。

    - ``targets`` 为空：递归 ``root`` 下所有 ``.md``
    - ``targets`` 非空：只校验显式指定的（用于 pre-commit 增量场景）
    """
    if targets:
        return [t for t in targets if t.is_file() and t.suffix.lower() == ".md"]
    return sorted(p for p in root.rglob("*.md") if p.is_file())


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--root", default="content", help="扫描根目录，默认 content")
    parser.add_argument(
        "--target",
        action="append",
        default=[],
        help="显式指定要校验的文件，可多次传入（pre-commit 场景）",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="把软警告也当作致命错误",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = Path(args.root).resolve()
    if not root.exists():
        print(f"[frontmatter-lint] root 不存在: {root}", file=sys.stderr)
        return 1

    targets = [Path(t).resolve() for t in args.target] if args.target else None
    files = iter_markdown(root, targets)

    if not files:
        print("[frontmatter-lint] 没有可校验的 .md 文件")
        return 0

    reports = [lint_file(p) for p in files]
    fatal_reports = [r for r in reports if r.has_fatal]
    warn_reports = [r for r in reports if r.warn and not r.has_fatal]

    for r in fatal_reports:
        rel = r.path.relative_to(root)
        print(f"[FATAL] {rel}")
        for msg in r.fatal:
            print(f"   - {msg}")

    if args.strict:
        for r in warn_reports:
            rel = r.path.relative_to(root)
            print(f"[WARN→FATAL] {rel}")
            for msg in r.warn:
                print(f"   - {msg}")
    else:
        for r in warn_reports:
            rel = r.path.relative_to(root)
            print(f"[WARN] {rel}")
            for msg in r.warn:
                print(f"   - {msg}")

    total = len(reports)
    print(
        f"\n[frontmatter-lint] scanned {total} files, "
        f"fatal={len(fatal_reports)}, warn={len(warn_reports)}"
    )
    if fatal_reports:
        return 1
    if warn_reports and args.strict:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
