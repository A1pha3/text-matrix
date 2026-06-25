#!/usr/bin/env bash
# trending-dedup-check.sh - GitHub Trending repo 去重兜底检查
#
# 用途：trending 任务抓到一批 owner/repo 列表后，**动笔前**用本脚本判断每个 repo
#       是否已在 content/posts/tech/ 下写过文章。命中任意 1 重检查即视为"已写"。
#
# 为什么需要这个脚本（2026-06-16 6-13/6-16 写重 music-assistant 复盘）：
#   1. owner/repo 格式是 `music-assistant/server`（含 `/`），文件名 slug 是
#      `music-assistant-server-...`（含 `-`）。简单 grep `music-assistant/server`
#      找不到文件名 → 去重漏判。
#   2. 子代理只看 git log commit 标题，没在 content/posts/tech/ 做全量 grep 兜底。
#   3. 孤儿文件（写了没 commit）会让 git log 检查完全失效。
#
# 用法：
#   bash scripts/trending-dedup-check.sh <repo1> [<repo2> ...]
#   # 或 stdin：
#   cat trending-raw.json | jq -r '.daily[].full_name' | bash scripts/trending-dedup-check.sh
#
# 输出：
#   - exit 0：所有 repo 都没写过，可以动笔
#   - exit 1：有 repo 已写过，stdout 列出已写 repo + 命中文件
#   - exit 2：参数错误
#
# 3 重 grep 兜底（任一命中即视为已写）：
#   A. 按 owner 段模糊匹配 content/posts/tech/*.md（处理 `/` vs `-` 不匹配）
#   B. 按 owner-repo 拼接匹配（`owner-repo` 和 `owner/repo` 都试）
#   C. git log --grep 匹配 commit 标题（覆盖还没 commit 的孤儿文件 → 用文件系统兜底，
#      这一重主要是补 commit 标题差异）

set -euo pipefail

# 必须从仓库根目录跑
REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || true)"
if [[ -z "$REPO_ROOT" || ! -d "$REPO_ROOT/content/posts/tech" ]]; then
  echo "❌ 必须在 text-matrix 仓库根目录跑（找不到 content/posts/tech/）" >&2
  exit 2
fi
cd "$REPO_ROOT"

# 读参数（支持 stdin）
if [[ $# -gt 0 ]]; then
  REPOS=("$@")
else
  # 从 stdin 读
  REPOS=()
  while IFS= read -r line; do
    line=$(echo "$line" | tr -d '[:space:]')
    [[ -n "$line" ]] && REPOS+=("$line")
  done
fi

if [[ ${#REPOS[@]} -eq 0 ]]; then
  echo "用法: $0 <owner/repo> [<owner/repo> ...]" >&2
  echo "  或: cat trending.json | jq -r '.[].full_name' | $0" >&2
  exit 2
fi

echo "🔍 去重检查: ${#REPOS[@]} 个 repo vs content/posts/tech/ ($(ls content/posts/tech/*.md 2>/dev/null | wc -l | tr -d ' ') 个文件)"
echo ""

WRITTEN_REPOS=()
NEW_REPOS=()

for full in "${REPOS[@]}"; do
  # 解析 owner / repo
  if [[ "$full" != *"/"* ]]; then
    echo "⚠️  跳过非法格式: $full（需要 owner/repo）" >&2
    continue
  fi
  owner="${full%%/*}"
  repo="${full#*/}"

  # 标准化 owner/repo（小写）
  owner_lc=$(echo "$owner" | tr '[:upper:]' '[:lower:]')
  repo_lc=$(echo "$repo" | tr '[:upper:]' '[:lower:]')

  # 多种拼接形式
  owner_dash_repo="${owner_lc}-${repo_lc}"     # music-assistant-server
  owner_dash_repo_upperDashed="${owner}-${repo}" # 保留大小写

  hits=()

  # 重 A：对多段 owner（含 -）启用 basename 前缀匹配，处理 / vs - 路径差异
  # 例如 owner=music-assistant 时，匹配 music-assistant-server-*.md
  # 单段 owner（如 flutter/microsoft）不走 A 重，避免过杀
  # （flutter-* / microsoft-* 前缀会命中任何该 owner 下的文件，
  #  包含还未写的同 owner 新 repo → 过杀）
  # 6-25 fix: 原 A 重用 grep -liE 对内容匹配，会过杀含 owner 字符串的文章
  # （如 'microsoft' 命中 ace-step-ui 等含 'Microsoft' 字符串的文章）。
  # 现改为只对多段 owner 启用，且只在 basename 前缀匹配，不 grep 内容。
  hit_a=""
  if [[ "$owner_lc" == *-* ]]; then
    for f in content/posts/tech/*.md; do
      [[ -e "$f" ]] || continue
      base=$(basename "$f" .md)
      # 匹配 owner- 开头的 slug（slug 命名规律：owner-repo-description）
      # 用 tr 不用 ${base,,}（macOS 默认 bash 3.2 不支持）
      base_lc=$(echo "$base" | tr '[:upper:]' '[:lower:]')
      if [[ "$base_lc" == "${owner_lc}-"* ]]; then
        hit_a+="${f}"$'\n'
        # 收集到 3 个就停
        [[ $(printf '%s' "$hit_a" | grep -c .) -ge 3 ]] && break
      fi
    done
    hit_a=$(printf '%s' "$hit_a" | head -3 | grep -v '^$' || true)
    [[ -n "$hit_a" ]] && hits+=("A:multi-segment-owner-prefix")
  fi

  # 重 B：按 owner-repo 拼接形式匹配（同时试 - 和 /）
  hit_b1=$(grep -lF "$owner_dash_repo" content/posts/tech/*.md 2>/dev/null | head -3 || true)
  [[ -n "$hit_b1" ]] && hits+=("B1:dash-join")
  hit_b2=$(grep -lF "$owner_dash_repo_upperDashed" content/posts/tech/*.md 2>/dev/null | head -3 || true)
  [[ -n "$hit_b2" && "$hit_b2" != "$hit_b1" ]] && hits+=("B2:dash-join-cased")

  # 重 C：git log --grep commit 标题（覆盖极端情况）
  hit_c=$(git log --all --oneline --grep="${full}" 2>/dev/null | head -1 || true)
  [[ -n "$hit_c" ]] && hits+=("C:git-log-grep")

  # 重 D：对多段 owner（含 -）启用 commit 标题模糊匹配
  # 处理 6-13/6-14 那种 "LMCache + music-assistant" 模糊标题
  # 单段 owner 不走 D 重（flutter/microsoft 已写过 → git log 含 flutter/microsoft
  # 字符串 → 会过杀所有 owner/* 新 repo）
  hit_d=""
  if [[ "$owner_lc" == *-* ]]; then
    hit_d=$(git log --all --oneline --grep="$owner" 2>/dev/null | head -1 || true)
    [[ -n "$hit_d" ]] && hits+=("D:multi-segment-owner")
  fi

  if [[ ${#hits[@]} -gt 0 ]]; then
    WRITTEN_REPOS+=("$full")
    # 收集所有命中文件路径
    all_files=$(printf '%s\n' "$hit_a" "$hit_b1" "$hit_b2" | sort -u | grep -v '^$' || true)
    echo "  ✅ $full  → 已写过  [${hits[*]}]"
    if [[ -n "$all_files" ]]; then
      echo "$all_files" | sed 's|^|        |'
    fi
  else
    NEW_REPOS+=("$full")
    echo "  🆕 $full  → 未写过"
  fi
done

echo ""
echo "── 汇总 ──"
echo "  未写（可动笔）: ${#NEW_REPOS[@]}"
echo "  已写（跳过）:   ${#WRITTEN_REPOS[@]}"
if [[ ${#NEW_REPOS[@]} -gt 0 ]]; then
  echo ""
  echo "可写列表（去重后）："
  for r in "${NEW_REPOS[@]}"; do
    echo "  - $r"
  done
fi

# exit code：有已写的就 exit 1，让调用方决定是 warning 还是 error
if [[ ${#WRITTEN_REPOS[@]} -gt 0 ]]; then
  exit 1
fi
exit 0
