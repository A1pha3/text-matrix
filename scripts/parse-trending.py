#!/usr/bin/env python3
"""Parse GitHub trending HTML → repo 列表 JSON。

只提取 owner/repo（<h2><a href="/owner/repo"> 是 trending 页最稳的 DOM 锚点）。
stars / language / description **不在此抓** —— 写文章时 `gh repo view --json ...` 现取更准，
避免双源（此处正则脆弱，GitHub 改 stargazers DOM 就静默返 0 —— 8-03 Emily2040 stars=n/a 的根因）。

输入：--cache 目录下的 {dim}-raw.html（curl 抓的 trending 页）；默认 workspace cache
输出：stdout JSON {dim: [{owner, name, full, url, dimension}]}
用法：python3 parse-trending.py [--cache DIR] [daily|weekly|monthly ...]

设计：脚本入仓（text-matrix/scripts/，与 backfill_github_repo.py / trending-dedup-check.sh
同级，受版本控制），数据（raw HTML / 中间 JSON）留 cache（gitignore）。脚本与数据分离，
消除「唯一副本在 gitignore 的 workspace cache」的单点故障（2026-08-04 P0-1 修复）。
"""
import re
import json
import sys
import argparse
from pathlib import Path

ARTICLE_RE = re.compile(r'<article[^>]*class="[^"]*Box-row[^"]*"[^>]*>(.*?)</article>', re.DOTALL)
REPO_RE = re.compile(r'<h2[^>]*>.*?<a[^>]*href="/([^"/]+)/([^"/?]+)"', re.DOTALL)

# raw HTML 默认在 workspace 级 cache（cron 抓取后落地处）；可用 --cache 覆盖
DEFAULT_CACHE = Path.home() / ".openclaw" / "workspace" / ".cache" / "github-trending"


def parse(html, dim):
    repos = []
    for art in ARTICLE_RE.findall(html):
        m = REPO_RE.search(art)
        if not m:
            continue
        owner, name = m.group(1), m.group(2)
        repos.append({"owner": owner, "name": name, "full": f"{owner}/{name}",
                      "url": f"https://github.com/{owner}/{name}", "dimension": dim})
    return repos


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--cache", default=str(DEFAULT_CACHE),
                    help=f"raw HTML 所在目录（默认 {DEFAULT_CACHE}）")
    ap.add_argument("dims", nargs="*", default=["daily", "weekly", "monthly"],
                    help="维度，默认 daily weekly monthly")
    args = ap.parse_args()
    cache = Path(args.cache)
    out = {}
    for dim in args.dims:
        path = cache / f"{dim}-raw.html"
        if not path.exists():
            print(f"⚠️ 跳过 {dim}: {path} 不存在", file=sys.stderr)
            continue
        repos = parse(path.read_text(errors="ignore"), dim)
        out[dim] = repos
        print(f"{dim}: {len(repos)} repos", file=sys.stderr)
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
