#!/usr/bin/env bash
# normalize-orphan-bundles.sh — content/posts 形态不变量执行器（2026-08-16 师父拍板）
#
# 不变量：content/posts/ 下不存在孤儿 bundle（目录里除 index.md 外无任何 git 追踪文件）。
#
# 第一性：单文件 <slug>.md 与 Page Bundle <slug>/index.md 在 Hugo 完全等价（URL 相同），
# 无资源的目录层是纯噪音。形态规则若靠写作契约维持，消费者是 N 个 agent，必然漂移
# （08-04 散文规则 → 08-06 矛盾条款覆盖 → 52 篇无图目录）。故形态不做契约、不做 lint 告警，
# 由本脚本在 pre-commit 自动拍平——formatter 模式：生成端随意，收敛端规范。
#
# 用法：
#   normalize-orphan-bundles.sh            只处理本次 staged 的 index.md（pre-commit 钩子用）
#   normalize-orphan-bundles.sh --all      全仓扫描拍平（存量治理）
#   normalize-orphan-bundles.sh --check    只报告不动作；发现孤儿 bundle 时 exit 1
set -euo pipefail

repo_root="$(git rev-parse --show-toplevel)"
cd "$repo_root"

mode="staged"
case "${1:-}" in
  --all)   mode=all;;
  --check) mode=check;;
  "")      ;;
  *) echo "用法: $0 [--all|--check]" >&2; exit 1;;
esac

# ---- 收集候选 index.md（git ls-files / diff 的 pathspec 对 ** 支持不稳，统一 grep 精确收尾）----
if [ "$mode" = "staged" ]; then
  candidates="$(git diff --cached --name-only --diff-filter=ACMR -- 'content/posts/' | grep -E '/index\.md$' || true)"
else
  candidates="$(git ls-files -- 'content/posts/' | grep -E '/index\.md$' || true)"
fi

[ -z "$candidates" ] && exit 0

orphans=""
while IFS= read -r idx; do
  d="$(dirname "$idx")"
  # 孤儿判定：该目录下被 git 追踪的文件恰好只有 index.md 一个
  # （git ls-files 看 index 区，staged 新文件可见；.DS_Store 等未追踪垃圾不影响判定）
  tracked="$(git ls-files -- "$d/")"
  [ "$tracked" = "$d/index.md" ] && orphans="$orphans$d"$'\n'
done <<< "$candidates"

orphans="$(printf '%s' "$orphans" | sed '/^$/d')"
[ -z "$orphans" ] && exit 0

if [ "$mode" = "check" ]; then
  echo "❌ 发现孤儿 bundle（目录里只有 index.md，应拍平为单文件）："
  printf '%s\n' "$orphans" | sed 's/^/   /'
  echo "   跑 scripts/normalize-orphan-bundles.sh --all 自动修复"
  exit 1
fi

count=0
while IFS= read -r d; do
  target="${d}.md"
  if [ -e "$target" ]; then
    echo "⚠️  撞名跳过（$target 已存在）: $d" >&2
    continue
  fi
  git mv "$d/index.md" "$target"
  # git mv 不管空目录；.DS_Store 是 macOS 垃圾可直接删，其余残留文件交人工
  rmdir "$d" 2>/dev/null \
    || { rm -f "$d/.DS_Store" && rmdir "$d" 2>/dev/null; } \
    || echo "⚠️  目录残留（含未追踪文件，请人工查看）: $d" >&2
  echo "✅ 拍平: $d/index.md → ${target}"
  count=$((count + 1))
done <<< "$orphans"

[ "$count" -gt 0 ] && echo "共拍平 $count 个孤儿 bundle"
exit 0
