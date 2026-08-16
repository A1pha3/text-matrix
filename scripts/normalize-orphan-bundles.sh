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
  # 孤儿判定（双重，缺一不可）：
  # 1. git 追踪层：该目录下被追踪的文件恰好只有 index.md
  #    （git ls-files 看 index 区，staged 新文件可见）
  # 2. 物理层：目录内容 ⊆ {index.md, .DS_Store}——防 untracked 资源被 stranded
  #    （agent 已生成图片但尚未 git add 时拍平，图会被丢在失去 index.md 的空目录里）
  # 已知限制：git ls-files 默认 core.quotePath，非 ASCII 文件名会 false negative
  # （该拍不拍）——方向安全，且 slug 由 lint 强制 kebab-case ASCII，实际不触发。
  tracked="$(git ls-files -- "$d/")"
  if [ "$tracked" = "$d/index.md" ]; then
    physical="$(ls -A "$d" | grep -vE '^(\.DS_Store|index\.md)$' || true)"
    if [ -z "$physical" ]; then
      orphans="$orphans$d"$'\n'
    elif [ "$mode" != "staged" ]; then
      echo "ℹ️  跳过（含未追踪文件，非纯孤儿）: $d → $physical" >&2
    fi
  fi
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
  # 撞名必须 fatal 而非跳过：双形态同 slug 共存 = Hugo Duplicate target paths
  # （全站页面互相覆盖，slug:index 事故同族）。拦下 commit 强制人工合并，
  # 已拍平的不回滚（脚本幂等，处理后重跑即可）。
  if [ -e "$target" ] || git ls-files --error-unmatch "$target" >/dev/null 2>&1; then
    echo "❌ 撞名：$target 已存在，拒绝拍平 $d" >&2
    echo "   两形态同 slug 共存会导致 Hugo Duplicate target paths（页面互相覆盖）。" >&2
    echo "   请人工把 $d/index.md 的内容合并进 ${target}、删除该目录后重新提交。" >&2
    exit 1
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
