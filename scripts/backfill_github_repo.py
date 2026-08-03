#!/usr/bin/env python3
"""backfill_github_repo.py — 给 content/posts/tech 文章 frontmatter 回填 github_repo 字段。

背景:repo 身份以前散落在 slug 前缀(大小写丢失)+ 正文"来源"行,导致 dedup 要 4 重 grep
+ 5 次历史修复。本脚本把 repo 提为结构化 frontmatter 字段 github_repo: "owner/repo"
(大小写保留),让 dedup 退化为一次精确查询。

支持两种 Hugo frontmatter:
  - YAML (---): github_repo: "owner/repo"     (7 月至今主力)
  - TOML (+++): github_repo = "owner/repo"     (5 月早期文章)

提取策略(宁缺毋滥 —— 漏判可发现可补救,错值污染 dedup 数据隐性不可信):
  - 只从正文 github.com/owner/repo 提取(大小写保留),strip .git / 子路径
  - 边界用负向 lookahead(停在任何非 repo 合法字符前: > ）、（ / 空格 行尾)
  - 跳过字面占位符(owner/repo 等)与 GitHub 保留路径段(sponsors/settings/trending…)
  - 正文无 github.com 链接 → 跳过(非 repo 文章 / 历史文章缺链接,不猜)

清洗:已有 github_repo 但 owner 是保留路径段的(早期未过滤误填),删字段重新提取。
插入位置:YAML 在 slug 行后;TOML 在首行。幂等。

用法:
  python3 backfill_github_repo.py --dry-run    # 只统计 + 抽样,不改文件
  python3 backfill_github_repo.py              # 实写
"""
import re, argparse
from pathlib import Path
from collections import Counter

TECH = Path(__file__).resolve().parent.parent / "content" / "posts" / "tech"

REPO_RE = re.compile(
    r'github\.com/([A-Za-z0-9](?:[A-Za-z0-9_-]*[A-Za-z0-9])?)/([A-Za-z0-9._-]+?)(?![A-Za-z0-9._-])'
)
FM_YAML = re.compile(r'^---\n(.*?)\n---\n', re.S)
FM_TOML = re.compile(r'^\+\+\+\n(.*?)\n\+\+\+\n', re.S)
EXISTING_RE = re.compile(r'^github_repo\s*[:=]\s*"?([^"\s]+)"?', re.M)
PLACEHOLDERS = {'owner/repo', 'user/repo', 'username/repo', 'account/repo',
                'org/repo', 'your-name/your-repo', 'namespace/repo', 'example/repo'}
RESERVED_OWNERS = {'sponsors', 'orgs', 'users', 'settings', 'search', 'topics',
                   'trending', 'explore', 'notifications', 'login', 'signup',
                   'features', 'marketplace', 'about', 'pricing', 'security'}


def extract_repo(text):
    """正文 → owner/repo(大小写保留),strip .git。跳过占位符与 GitHub 保留路径段。"""
    for m in REPO_RE.finditer(text):
        owner, repo = m.group(1), m.group(2)
        repo = re.sub(r'\.git$', '', repo)
        if len(owner) < 2 or len(repo) < 2:
            continue
        if owner.lower() in RESERVED_OWNERS:
            continue
        full = f"{owner}/{repo}"
        if full.lower() in PLACEHOLDERS:
            continue
        return full
    return None


def process(f, dry_run):
    raw = f.read_text(encoding='utf-8')
    m = FM_YAML.match(raw)
    fmt = 'yaml'
    if not m:
        m = FM_TOML.match(raw)
        fmt = 'toml'
    if not m:
        return ('skip_no_fm', None)
    fm, body = m.group(1), raw[m.end():]

    cleaned = False
    existing = EXISTING_RE.search(fm)
    if existing:
        owner = existing.group(1).split('/')[0].lower().strip('/')
        if owner not in RESERVED_OWNERS:
            return ('already', None)
        fm = re.sub(r'^github_repo\s*[:=].*$\n', '', fm, flags=re.M)  # 清洗误填
        cleaned = True

    repo = extract_repo(raw)
    if repo:
        line = (f'github_repo = "{repo}"\n' if fmt == 'toml' else f'github_repo: "{repo}"\n')
        if fmt == 'yaml':
            new_fm = re.sub(r'(^slug:.*$\n)', rf'\1{line}', fm, count=1, flags=re.M)
            if new_fm == fm:
                new_fm = line + fm
        else:
            new_fm = line + fm
    else:
        new_fm = fm  # 无 repo(可能刚清洗掉误填)

    if not repo and not cleaned:  # 没清洗且无 repo → 真 no_repo, 不写入
        return ('no_repo', None)
    if not dry_run:
        sep = '+++' if fmt == 'toml' else '---'
        f.write_text(f'{sep}\n{new_fm}\n{sep}\n{body}', encoding='utf-8')
    return ('cleaned' if cleaned else 'done', repo)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dry-run', action='store_true')
    args = ap.parse_args()
    files = sorted(TECH.rglob('*.md'))  # rglob:含子目录(ai-agent/ tools/ page bundle 等)
    stats = Counter(); samples = []
    for f in files:
        status, repo = process(f, args.dry_run)
        stats[status] += 1
        if status in ('done', 'cleaned') and len(samples) < 12:
            samples.append((f.name, repo, status))
    mode = 'DRY-RUN(不改)' if args.dry_run else '已写入'
    print(f"=== {mode} | 总 {len(files)} 篇 ===")
    for k, v in stats.most_common():
        print(f"  {k:14s}: {v}")
    if samples:
        print("\n本次改动抽样:")
        for name, repo, status in samples:
            print(f"  [{status:7s}] {(repo or '(清洗后无repo)'):36s} <- {name[:44]}")


if __name__ == '__main__':
    main()
