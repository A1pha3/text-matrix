#!/usr/bin/env bash
# trending-dedup-check.sh — GitHub 趋势榜去重:精确字段查询(读 frontmatter github_repo)。
#
# 设计:每篇文章 frontmatter 的 github_repo: "owner/repo" 是结构化身份字段
#   (backfill_github_repo.py 回填历史 + github-article-writer 写新文时填入)。
# 去重 = 本轮 repo 列表与已写集合做精确字符串匹配(小写归一化)。
#
# 这取代了旧版 4 重 grep + owner 段特判(159 行):
#   / vs -、单段/多段 owner、孤儿文件、大小写、bitchat 误杀成 bitchat-android —— 全部消失,
#   因为现在是精确字符串匹配,这些根本不是问题。
#
# 用法:
#   bash trending-dedup-check.sh owner1/repo1 owner2/repo2 ...
#   jq -r '.repos[].full' .cache/github-trending/trending-raw.json | xargs bash trending-dedup-check.sh
#   cat repos.txt | bash trending-dedup-check.sh        # stdin
# 退出码:0=全部未写, 1=有已写, 2=不在 text-matrix 仓库或无参数
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"  # scripts/ 父目录即仓库根
TECH="$ROOT/content/posts/tech"
[ -d "$TECH" ] || { echo "❌ 找不到 $TECH — 请在 text-matrix 仓库内运行"; exit 2; }

# 统一入参:有命令行参数就用;否则从 stdin 读(每行一个 owner/repo)。
# 注意:stdin 必须在 bash 层读完再传给 python —— heredoc 会占用 python 的 stdin。
if [ $# -eq 0 ]; then
  args=()
  while IFS= read -r line; do
    line="${line//[[:space:]]/}"
    [ -n "$line" ] && args+=("$line")
  done
  set -- "${args[@]}"
fi
[ $# -gt 0 ] || { echo "用法: $0 owner1/repo1 ...  或 stdin 喂入 owner/repo 列表"; exit 2; }

python3 - "$TECH" "$@" <<'PY'
import re, sys
from pathlib import Path
tech, queries = Path(sys.argv[1]), sys.argv[2:]
# 收集已写 repo:frontmatter github_repo 字段(YAML `:` 与 TOML `=` 都认),小写归一化
val = re.compile(r'^github_repo\s*[:=]\s*"?([^\s"]+)', re.M)
written = set()
for f in tech.rglob('*.md'):  # rglob:含子目录(ai-agent/ tools/ page bundle),否则身份漏读→重复写
    for m in val.finditer(f.read_text(encoding='utf-8', errors='ignore')):
        written.add(m.group(1).lower().strip('/'))
old, new = [], []
for q in queries:
    (old if q.lower().strip('/') in written else new).append(q)
for q in old: print(f"  ✅ 已写: {q}")
for q in new:
    owner = q.split('/')[0].lower()
    sibs = sorted(w for w in written if w.split('/')[0] == owner)
    if sibs:
        tail = '…' if len(sibs) > 3 else ''
        print(f"  🆕 未写: {q}   ⚠️ 同 owner 已 {len(sibs)} 篇: {', '.join(sibs[:3])}{tail} — 写前确认不重叠")
    else:
        print(f"  🆕 未写: {q}")
print(f"\n已写 {len(old)} / 未写 {len(new)} / 共 {len(queries)}  |  已写库 {len(written)} 个 repo")
sys.exit(1 if old else 0)
PY
