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


# ---- github_repo 结构化身份校验（trending 去重的硬保障） -------------------
# 仅对 content/posts/tech/ 强制：该 section 是 GitHub repo 导向文章，
# frontmatter github_repo: "owner/repo" 是去重身份字段（见 backfill_github_repo.py
# 与 scripts/trending-dedup-check.sh）。机器能验「格式合法 + 该填的填了」，
# 验不了「大小写与 GitHub 实际一致」（那要联网查 API）——后者仍靠
# github-article-writer 取 gh repo view 的 nameWithOwner。
GITHUB_REPO_VALUE_RE = re.compile(
    r"^\s*([A-Za-z0-9](?:[A-Za-z0-9_-]*[A-Za-z0-9])?)/([A-Za-z0-9._-]+)\s*$"
)
# 正文里 github.com/owner/repo 的锚点（与 backfill_github_repo.py 同源，宁缺毋滥）
BODY_REPO_RE = re.compile(
    r"github\.com/([A-Za-z0-9](?:[A-Za-z0-9_-]*[A-Za-z0-9])?)/([A-Za-z0-9._-]+?)(?![A-Za-z0-9._-])"
)
RESERVED_OWNERS = {
    "sponsors", "orgs", "users", "settings", "search", "topics", "trending",
    "explore", "notifications", "login", "signup", "features", "marketplace",
    "about", "pricing", "security",
}
PLACEHOLDER_REPOS = {
    "owner/repo", "user/repo", "username/repo", "account/repo", "org/repo",
    "your-name/your-repo", "namespace/repo", "example/repo",
}


def check_github_repo(path: Path, data: dict, body: str) -> list[str]:
    """校验 posts/tech 文章的 github_repo 身份字段（去重硬保障）。

    返回致命错误列表（空 = 通过）：
    - 有字段但格式非法 / owner 是 GitHub 保留段 / 占位符未替换 → 致命（防错填）
    - 无字段但正文含合法 github.com/owner/repo 链接 → 致命（防漏填：正文有 repo 却没提身份字段，
      trending 去重会因此漏判，如 8-03 Emily2040/seedance 的同类根因）
    - 无字段且正文无合法 repo 链接 → 通过（真·非 repo 文章，如综述/方法论）
    """
    parts = path.parts
    if "posts" not in parts or "tech" not in parts:
        return []
    raw = data.get("github_repo")
    if raw:
        v = str(raw).strip().strip("/").strip("\"'")
        owner = v.split("/")[0].lower() if "/" in v else ""
        if not GITHUB_REPO_VALUE_RE.match(v):
            return [f"github_repo 格式非法（应为 owner/repo）: {raw!r}"]
        if owner in RESERVED_OWNERS:
            return [f"github_repo owner 是 GitHub 保留路径段: {raw!r}"]
        if v.lower() in PLACEHOLDER_REPOS:
            return [f"github_repo 是占位符，未替换实际 owner/repo: {raw!r}"]
        return []
    # 无字段：扫正文，若含合法 repo 链接则判漏填
    for m in BODY_REPO_RE.finditer(body or ""):
        o, r = m.group(1), re.sub(r"\.git$", "", m.group(2))
        if (
            len(o) >= 2
            and len(r) >= 2
            and o.lower() not in RESERVED_OWNERS
            and f"{o}/{r}".lower() not in PLACEHOLDER_REPOS
        ):
            return [
                f"正文含 github.com/{o}/{r} 但 frontmatter 缺 github_repo 字段"
                f"（漏填：trending 去重将漏判此 repo）"
            ]
    return []


# source_key 是免审批自动发布管线的稳定身份锚点（2026-08-06 师父拍板，见
# skills/*/references/frontmatter-template.md）：GitHub 稿 gh:owner/repo、视频稿 bv:/yt:。
# 发布去重/防漏判定唯一依据，替代旧的"正文 grep bvid / 目录名前缀碰运气"。
SOURCE_KEY_RE = re.compile(r"^(gh|bv|yt):[^\s]+$")
# 正文里的 bvid 锚点（视频稿身份）
BODY_BVID_RE = re.compile(r"\bBV1[A-Za-z0-9]{9}\b")


def check_categories_whitelist(path: Path, data: dict) -> list[str]:
    """全局拦截非白名单 categories（所有 posts 文章）。

    首页 layouts/index.html 只策展 5 个分类：技术笔记 / 视频精读 / 思考与随笔 /
    行业快讯 / 财富自由。文章误标其他分类（"技术文章"、"tech"、"技术"、论文类、
    播客反写 等）会已上线但首页永不显示（2026-08-08 实证 51 篇，见 memory
    text-matrix-homepage-curated-categories）。白名单以外的词说明写作时偏离了
    skill 契约（categories 必须是 ["技术笔记"] 或 ["视频精读"]），fatal 拦截。
    """
    cats = data.get("categories")
    if not cats:
        return []
    if isinstance(cats, str):
        cats = [cats]
    allowed = {"技术笔记", "视频精读", "思考与随笔", "行业快讯", "财富自由"}
    bad = [c for c in cats if c not in allowed]
    if bad:
        return [
            f"categories 含非白名单分类 {bad}（首页只策展 技术笔记/视频精读/"
            f"思考与随笔/行业快讯/财富自由），文章将不上首页；请改回 "
            f"['技术笔记'] 或 ['视频精读']（视频/播客/访谈类），其余细分词放 tags"
        ]
    return []


def check_slug_not_index(path: Path, data: dict) -> list[str]:
    """全局拦截 slug:index 构建毒药（所有 posts 文章）。

    page bundle 的 index.md 的 slug 本就该用目录名当 URL；一旦显式写 slug: index，
    所有这么写的页面都试图构建到 .../index/index.html，Hugo 报 Duplicate target paths
    互相覆盖，把文章卡在构建外不上线（2026-08-06 实证，见 memory slug-index-duplicate-target-trap）。
    """
    v = str(data.get("slug", "") or "").strip().strip("\"'").lower()
    if v == "index":
        return [
            "slug 不能是 index（会造成全站 Duplicate target paths 冲突，"
            "把文章卡在构建外）；请改用语义化小写连字符 slug"
        ]
    return []


def check_source_key(path: Path, data: dict, body: str) -> tuple[list[str], list[str]]:
    """校验 posts/tech 与 posts/video 文章的 source_key 身份锚点（自动发布去重保障）。

    返回 (fatal_list, warn_list)：
    - 有字段但格式非法（须 gh:/bv:/yt: 前缀）→ fatal（防错填）
    - tech 稿 source_key 与 github_repo 不一致 → fatal（防漂移）
    - 有锚点但缺 source_key（漏填）→ warn（存量文章多，先提醒不阻断；回填后升级 fatal）

    设计权衡：source_key 是 2026-08-06 新增契约，存量 ~900 篇文章尚未回填。
    若"漏填"即 fatal 会让全站 lint 崩、CI 阻断所有发布。故错填/漂移（确定是错误）
    fatal，漏填（只是没补齐）warn。新稿由写作 skill 直接带 source_key 落盘，
    回填完存量后把漏填也升级 fatal。
    """
    parts = path.parts
    in_tech = "posts" in parts and "tech" in parts
    in_video = "posts" in parts and "video" in parts
    if not (in_tech or in_video):
        return [], []

    raw = data.get("source_key")
    if raw:
        v = str(raw).strip().strip("\"'")
        if not SOURCE_KEY_RE.match(v):
            return [f"source_key 格式非法（须 gh:owner/repo 或 bv:/yt: 前缀）: {raw!r}"], []
        # tech 稿：source_key 应与 github_repo 一致（同源，防漂移）
        gh = str(data.get("github_repo", "") or "").strip().strip("\"'")
        if in_tech and gh:
            expect = f"gh:{gh}"
            if v != expect:
                return [
                    f"source_key 与 github_repo 不一致（应为 {expect!r}，实际 {raw!r}）"
                ], []
        return [], []

    # 无 source_key：有明确身份锚点则提醒漏填（warn，非 fatal）
    gh = str(data.get("github_repo", "") or "").strip().strip("\"'")
    if in_tech and gh:
        return [], [
            f"缺 source_key（应为 gh:{gh}，与 github_repo 同源）；漏填则自动发布去重判定失灵"
        ]
    if in_video:
        m = BODY_BVID_RE.search(body or "")
        if m:
            return [], [
                f"正文含 {m.group(0)} 但缺 source_key（应为 bv:{m.group(0)}）；漏填则自动发布去重判定失灵"
            ]
    return [], []


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

    fence, fm, body = split

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

    # 致命 #3：posts/tech 的 github_repo 身份字段（格式错填 / 正文有 repo 却漏填）
    for msg in check_github_repo(path, data, body):
        report.add_fatal(msg)

    # 致命 #4：slug:index 全站构建毒药（所有 posts 文章）
    for msg in check_slug_not_index(path, data):
        report.add_fatal(msg)

    # 致命 #5：categories 白名单（所有 posts 文章，防再写错分类不上首页）
    for msg in check_categories_whitelist(path, data):
        report.add_fatal(msg)

    # 致命 #6 / 软警告：posts/tech 与 posts/video 的 source_key 身份锚点
    # （错填/漂移 fatal；漏填 warn——存量未回填，新稿由 skill 带齐落盘）
    sk_fatal, sk_warn = check_source_key(path, data, body)
    for msg in sk_fatal:
        report.add_fatal(msg)
    for msg in sk_warn:
        report.add_warn(msg)

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
        action="extend",
        nargs="+",
        default=[],
        help="显式指定要校验的文件；支持一次传多个，也支持重复传入（pre-commit 场景）",
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
