#!/usr/bin/env python3
"""backfill_source_key.py — 给存量文章回填 source_key 身份锚点。

背景:source_key 是免审批自动发布管线的稳定身份锚点(2026-08-06 契约):
GitHub 稿记 gh:owner/repo、B 站视频稿记 bv:BV…。存量大批文章漏填,
发布去重/防漏判定只能退回 grep 正文碰运气。本脚本按 frontmatter_lint
的 check_source_key 同源规则一次性回填。

规则(与 lint 对齐,宁缺毋滥):
  - posts/tech : 有 github_repo 且无 source_key → source_key: "gh:{owner/repo}"
  - posts/video: 正文含首个 BV1xxxxxxxxx 且无 source_key → "bv:{bvid}"
  - 已有 source_key → 不动(不覆盖既有身份,防劣化)
  - github_repo 缺失/非法(格式/保留段/占位符) → 跳过,留给 lint 报告

插入位置:YAML 在 github_repo 行后(无则 slug 行后,再无则首行);
TOML 同构(source_key = "...")。幂等、原子写、保留 BOM。

用法:
  python3 backfill_source_key.py --dry-run    # 只统计 + 抽样,不改文件
  python3 backfill_source_key.py              # 实写
"""
from __future__ import annotations

import argparse
import os
import re
import tempfile
from collections import Counter
from pathlib import Path

CONTENT = Path(__file__).resolve().parent.parent / "content" / "posts"

# 与 frontmatter_lint.check_github_repo 同源的合法性判定
REPO_VALUE_RE = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9_-]*[A-Za-z0-9])?/[A-Za-z0-9._-]+$")
RESERVED_OWNERS = {
    "sponsors", "orgs", "users", "settings", "search", "topics", "trending",
    "explore", "notifications", "login", "signup", "features", "marketplace",
    "about", "pricing", "security",
}
PLACEHOLDERS = {
    "owner/repo", "user/repo", "username/repo", "account/repo", "org/repo",
    "your-name/your-repo", "namespace/repo", "example/repo",
}
# 与 frontmatter_lint.check_source_key 同源的视频锚点
BVID_RE = re.compile(r"\bBV1[A-Za-z0-9]{9}\b")

SOURCE_KEY_ANY_RE = re.compile(r"^source_key\s*[:=]", re.M)


def split_fm(text: str):
    """切分 frontmatter。

    返回 (bom, fence, fm, body, lines, close_idx),fm 不含 fence 行;
    无 frontmatter / fence 未闭合返回 None。
    """
    bom = "\ufeff" if text.startswith("\ufeff") else ""
    t = text[len(bom):]
    lines = t.split("\n")
    fence = lines[0].rstrip() if lines else ""
    if fence not in ("---", "+++"):
        return None
    for i, ln in enumerate(lines[1:], 1):
        if ln.rstrip() == fence:
            return bom, fence, "\n".join(lines[1:i]), "\n".join(lines[i + 1:]), lines, i
    return None


def write_atomic(path: Path, text: str) -> None:
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=f".{path.name}.", suffix=".tmp")
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


def process(path: Path, section: str, dry_run: bool):
    """返回 (status, key)。status: done / already / skip_no_fm / no_anchor / bad_github_repo / error。"""
    raw = path.read_text(encoding="utf-8")
    split = split_fm(raw)
    if split is None:
        return "skip_no_fm", None
    bom, fence, fm, body, lines, close_idx = split
    is_yaml = fence == "---"

    if SOURCE_KEY_ANY_RE.search(fm):
        return "already", None

    if section == "tech":
        gh_re = re.compile(r'^github_repo\s*[:=]\s*"?([^"\n]*?)"?\s*$', re.M)
        m = gh_re.search(fm)
        if not m:
            return "no_github_repo", None
        repo = m.group(1).strip().strip('"').strip("'").strip("/")
        owner = repo.split("/")[0].lower() if "/" in repo else ""
        if (
            not REPO_VALUE_RE.match(repo)
            or owner in RESERVED_OWNERS
            or repo.lower() in PLACEHOLDERS
        ):
            return "bad_github_repo", repo
        key = f"gh:{repo}"
    else:  # video
        m = BVID_RE.search(body)
        if not m:
            return "no_bvid", None
        key = f"bv:{m.group(0)}"

    line = f'source_key: "{key}"' if is_yaml else f'source_key = "{key}"'
    anchor_key = "github_repo" if section == "tech" else "slug"
    anchor_re = re.compile(rf"^{re.escape(anchor_key)}\s*[:=].*$", re.M)
    m2 = anchor_re.search(fm)
    if m2:
        new_fm = fm[: m2.end()] + "\n" + line + fm[m2.end():]
    else:
        new_fm = line + "\n" + fm

    # 重组:仅替换 frontmatter 行区间的 fm 部分,其余行原样;并自检新 fm 可解析出 source_key
    new_text = bom + "\n".join(lines[:1] + new_fm.split("\n") + lines[close_idx:])
    check = split_fm(new_text)
    if check is None or not SOURCE_KEY_ANY_RE.search(check[2]) or f'"{key}"' not in check[2]:
        return "error", key

    if not dry_run:
        write_atomic(path, new_text)
    return "done", key


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    stats: Counter = Counter()
    samples: list[tuple[str, str, str | None]] = []
    errors: list[str] = []
    for section in ("tech", "video"):
        for f in sorted((CONTENT / section).rglob("*.md")):
            try:
                status, key = process(f, section, args.dry_run)
            except Exception as exc:  # 单文件异常不中断整批
                status, key = "error", None
                errors.append(f"{f}: {exc}")
            stats[status] += 1
            if status == "done" and len(samples) < 12:
                samples.append((section, f.name, key))

    mode = "DRY-RUN(不改)" if args.dry_run else "已写入"
    print(f"=== {mode} | 目标 {stats.get('done', 0) + stats.get('already', 0) + stats.get('no_anchor', 0) + stats.get('skip_no_fm', 0) + stats.get('bad_github_repo', 0) + stats.get('error', 0)} 篇 ===")
    for k, v in stats.most_common():
        print(f"  {k:18s}: {v}")
    if samples:
        print("\n本次改动抽样:")
        for section, name, key in samples:
            print(f"  [{section:5s}] {str(key):40s} <- {name[:48]}")
    if errors:
        print("\n异常:")
        for e in errors[:10]:
            print(f"  ! {e}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
