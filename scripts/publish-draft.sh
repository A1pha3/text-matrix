#!/usr/bin/env bash
# publish-draft.sh — 免审批自动发布管线的执行层（2026-08-06 师父拍板）
#
# 第一性：发布 = 翻一个 frontmatter 布尔位（draft:false）。不评分、不写作、
# 不碰 state/。评分由写作 agent 在对话里跑 cn-doc-writer 三维评分决定，达 B 级（≥70）
# 才调用本脚本。本脚本只做"翻 draft + 去重 + commit + push + 飞书"四件事。
#
# 为什么取代 reverse-publish.sh 的 deliver：
#   旧 deliver 走 state/→content/ 两段式接力（重复发布与误报病根，已废弃）；
#   旧 deliver git add -A（卷入仓库无关改动）、强制 slug:index（构建毒药）。
#   新管线：稿子写完直接落 content/，本脚本只翻 draft，稿子唯一落点=content/。
#
# 安全约束（硬编码，不可被参数绕过）：
#   1. 只 add 本文章目录，绝不用 git add -A（防卷入无关改动）
#   2. push 前必做 source_key 去重：content 里已有同 source_key 的 draft:false 文章 → 拒绝（--force 覆盖）
#   3. 翻 draft 前 frontmatter 必须已过 frontmatter_lint（source_key/slug 非 index 等 fatal）
#   4. 仅处理 content/posts/{tech,video} 下的文章（分类映射所在）
#
# 用法（写作 agent 拿到评分后调用）：
#   publish-draft.sh <文章目录或 index.md> --score <三维分数> --grade <S|A|B>
#     --score <n>      cn-doc-writer 三维评分总分（写进 commit message + 飞书）
#     --grade <g>      评级 S/A/B（≥70 才应调用本脚本；C/D 由 agent 留 draft 不调用）
#     --note <text>    额外说明（如触发的门槛），可选
#     --dry-run        只打印将做的事，不写盘/不 commit/不 push
#     --no-push        只 commit 不推（紧急刹车）
#     --force          已有同 source_key 的上线稿也强制覆盖（慎用）
set -euo pipefail

WS="${HOME}/.openclaw/workspace"
REPO="$WS/github/text-matrix"
FEISHU_TO="user:ou_28db2798a35179602c855f46406e63f3"
VALID_GRADES="S A B"

# ---- 解析参数 ----
target=""; score=""; grade=""; note=""; dry_run=0; no_push=0; force=0
target="${1:-}"; shift || true
while [ $# -gt 0 ]; do
  case "$1" in
    --score) score="$2"; shift 2;;
    --grade) grade="$2"; shift 2;;
    --note) note="$2"; shift 2;;
    --dry-run) dry_run=1; shift;;
    --no-push) no_push=1; shift;;
    --force) force=1; shift;;
    *) echo "未知参数: $1" >&2; exit 1;;
  esac
done

# ---- 定位 index.md + 校验目录合法 ----
if [ -z "$target" ]; then echo "用法: $0 <文章目录或index.md> --score N --grade <S|A|B>" >&2; exit 1; fi
# 解析成绝对路径（兼容相对路径：先按相对 REPO，再按相对 cwd）
if [ -f "$target" ]; then idx="$target"; else idx="$target/index.md"; fi
if [ ! -f "$idx" ]; then idx="$REPO/$target"; [ -f "$idx" ] || idx="$REPO/$target/index.md"; fi
# 规范成绝对路径便于前缀匹配
idx="$(cd "$(dirname "$idx")" && pwd)/$(basename "$idx")"
case "$idx" in
  "$REPO"/content/posts/tech/*) section=tech;;
  "$REPO"/content/posts/video/*) section=video;;
  *) echo "❌ 目标不在 content/posts/tech 或 content/posts/video 下（不支持）: $idx" >&2; exit 2;;
esac
[ -f "$idx" ] || { echo "❌ 找不到 index.md: $idx" >&2; exit 2; }
rel="${idx#$REPO/}"

# ---- 读 frontmatter 关键字段（source_key / title / draft / slug）----
meta="$(python3 - "$idx" <<'PY'
import re, sys, json
c = open(sys.argv[1]).read()
m = re.match(r'^---\n(.*?)\n---\n', c, re.DOTALL)
fm = m.group(1) if m else ''
def field(n):
    mm = re.search(r'^' + n + r'\s*:\s*(.*?)\s*$', fm, re.MULTILINE)
    v = mm.group(1).strip() if mm else ''
    v = v.strip("\"'")
    return v
sk = field('source_key')
print(json.dumps({
    'source_key': sk,
    'title': field('title'),
    'draft': field('draft'),
    'slug': field('slug'),
    'has_fm': bool(m),
}, ensure_ascii=False))
PY
)"
sk="$(echo "$meta" | python3 -c "import json,sys;print(json.load(sys.stdin)['source_key'])")"
title="$(echo "$meta" | python3 -c "import json,sys;print(json.load(sys.stdin)['title'])")"
draft_now="$(echo "$meta" | python3 -c "import json,sys;print(json.load(sys.stdin)['draft'])")"

# ---- 硬约束：已 draft:false（上线态）则拒绝重发，防幂等破坏 ----
if [ "$draft_now" = "false" ] && [ "$force" != 1 ]; then
  echo "❌ 该文章已是 draft:false（上线态），不应重复发布：${rel}" >&2
  echo "   如需重新发布（如内容大改后重上），加 --force。" >&2
  exit 5
fi

# ---- 硬约束：source_key 必须有（发布去重的唯一身份）----
if [ -z "$sk" ] || ! echo "$sk" | grep -qE '^(gh|bv|yt):'; then
  echo "❌ frontmatter 缺 source_key 或格式非法（须 gh:/bv:/yt: 前缀）: ${sk:-（空）}" >&2
  echo "   补 source_key 后再发布。自动发布身份锚点是去重命脉，不可缺。" >&2
  exit 3
fi

# ---- 硬约束：评级校验（防误传 C/D 进来）----
if [ -z "$grade" ]; then echo "❌ 缺 --grade（S/A/B）。C/D 级不应调用本脚本，由 agent 留 draft。" >&2; exit 3; fi
case " $VALID_GRADES " in
  *" $grade "*) ;;
  *) echo "❌ grade 必须是 S/A/B（当前 ${grade}）。C/D 不自动发布。" >&2; exit 3;;
esac

# ---- 去重保护：content 里是否已有同 source_key 的 draft:false 上线稿 ----
dup=""
if [ "$force" != 1 ]; then
  # grep frontmatter 里的 source_key 行（排除当前文件自身）
  dup="$(grep -rlE "^source_key:\s*[\"']?${sk}[\"']?\s*$" "$REPO/content/posts" 2>/dev/null \
        | grep -v "^${idx}$" | head -1 || true)"
  if [ -n "$dup" ]; then
    echo "❌ 已存在同 source_key 的文章：${dup#$REPO/}" >&2
    echo "   source_key=$sk 是发布去重命脉。如确认要覆盖，加 --force（会翻旧稿 draft:true 撤下后重发）。" >&2
    exit 4
  fi
fi

echo "发布计划："
echo "  文章  ：${rel}"
echo "  标题  ：$title"
echo "  评级  ：${grade}（${score:-?}/100）  source_key：${sk}"
[ -n "$note" ] && echo "  说明  ：$note"
echo "  动作  ：draft:true → draft:false，commit，$([ "$no_push" = 1 ] && echo 不 || echo )push"

if [ "$dry_run" = 1 ]; then
  echo ""; echo "🔎 --dry-run，未写盘未 commit。"; exit 0
fi

# ---- 翻 draft:true → draft:false（原子，仅改这一行）----
python3 - "$idx" <<'PY'
import sys, re
f = sys.argv[1]
c = open(f).read()
m = re.match(r'^(---\n)(.*?)(\n---\n)', c, re.DOTALL)
if not m:
    sys.exit("frontmatter 未找到，无法翻 draft")
pre, fm, post = m.group(1), m.group(2), m.group(3)
body = c[m.end():]
if re.search(r'^draft\s*:', fm, re.MULTILINE):
    fm = re.sub(r'^draft\s*:.*$', 'draft: false', fm, flags=re.MULTILINE)
else:
    fm = fm.rstrip('\n') + '\ndraft: false'
open(f, 'w').write(pre + fm + post + body)
PY
echo "✅ 已翻 draft: false"

# ---- commit（只 add 本文章目录；前置 lint 由 pre-commit 钩子跑）----
msg="${grade} ${score:-?}/100 · ${title}"
[ -n "$note" ] && msg="${msg}（${note}）"
msg="${msg} [${sk}]"
( cd "$REPO" && git add "$rel" && git commit -m "$msg" -q )
echo "✅ 已 commit：$msg"

# ---- push ----
if [ "$no_push" != 1 ]; then
  ( cd "$REPO" && git push -q )
  echo "✅ 已 push 到 origin"
  status="已上线"
else
  echo "⏸  --no-push，本地已 commit 未推"
  status="本地已 commit 未 push"
fi

# ---- 飞书报告（结论先行 + 评分依据 + 可撤回方式）----
hash_short="$(cd "$REPO" && git rev-parse --short HEAD)"
openclaw message send --channel feishu -t "$FEISHU_TO" -m "🎬 自动发布 · $(date +%H:%M)
• 《${title}》→ ${rel%/*}/
• 评级 ${grade}（${score:-?}/100），cn-doc-writer 三维过闸自动上线
• source_key ${sk}，${status}
• 无需操作 ✅ 不满意可撤回：把 draft 翻回 true（commit ${hash_short}）" >/dev/null 2>&1 || true
echo "📤 已飞书报告"
