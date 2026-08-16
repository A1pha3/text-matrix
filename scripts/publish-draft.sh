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
#   publish-draft.sh --key gh:owner/repo --score <三维分数> --grade <S|A|B>   ← 推荐：身份寻址，对形态免疫
#   publish-draft.sh <文章路径>            --score <三维分数> --grade <S|A|B>   （路径寻址，兼容保留）
#     --key <sk>       source_key 身份寻址（gh:/bv:/yt: 前缀），自动反查文章路径
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
target=""; score=""; grade=""; note=""; key=""; dry_run=0; no_push=0; force=0
target="${1:-}"; shift || true
# target 位置参数若以 -- 开头则说明调用方直接用了选项（如 --key），不吞
case "$target" in --*) set -- "$target" "$@"; target="";; esac
while [ $# -gt 0 ]; do
  case "$1" in
    --score) score="$2"; shift 2;;
    --grade) grade="$2"; shift 2;;
    --key) key="$2"; shift 2;;
    --note) note="$2"; shift 2;;
    --dry-run) dry_run=1; shift;;
    --no-push) no_push=1; shift;;
    --force) force=1; shift;;
    *) echo "未知参数: $1" >&2; exit 1;;
  esac
done

# ---- 定位文章文件 + 校验目录合法 ----
# 两种寻址方式：路径（target 位置参数）或身份（--key source_key 反查）。
# 身份寻址优先推荐：agent 只持有 source_key（发布唯一身份），路径由本脚本反查，
# 链路对形态免疫（normalize 拍平 / 未来迁移都不影响发布）。
if [ -z "$target" ] && [ -z "$key" ]; then
  echo "用法: $0 <文章路径> | --key <source_key> --score N --grade <S|A|B>" >&2; exit 1
fi
if [ -n "$key" ]; then
  # 白名单字符校验：key 将嵌入 grep 正则，必须拒绝正则元字符注入。
  # 合法形态：gh:owner/repo · bv:BVxxxx · yt:video_id（仅 ASCII 字母数字与 : / . _ -）。
  if ! echo "$key" | grep -qE '^[A-Za-z0-9._:/-]+$'; then
    echo "❌ --key 含非法字符（仅允许 A-Za-z0-9 . _ : / -）: $key" >&2; exit 3
  fi
  key_re="$(printf '%s' "$key" | sed 's/\./\\./g')"   # . 转义，精确匹配
  key_hits="$(grep -rlE "source_key:[[:space:]]*[\"']?${key_re}[\"']?[[:space:]]*$" "$REPO/content/posts" --include='*.md' 2>/dev/null || true)"
  # printf 必须 %s\n：command substitution 剥尾换行后 %s 不补，wc -l 数换行符会把单行误计为 0
  n_hits="$(printf '%s\n' "$key_hits" | sed '/^$/d' | wc -l | tr -d ' ')"
  case "$n_hits" in
    0) echo "❌ --key 未命中任何文章: $key" >&2; exit 2;;
    1) idx="$key_hits";;
    *) # 多命中=身份不唯一（数据异常）：发布动作宁拒勿错，交人工
       echo "❌ --key 命中 $n_hits 篇文章（source_key 应全局唯一），拒绝发布:" >&2
       printf '%s\n' "$key_hits" | sed 's/^/   /' >&2
       exit 6;;
  esac
  idx="$(cd "$(dirname "$idx")" && pwd)/$(basename "$idx")"
  echo "🔑 --key $key → ${idx#$REPO/}"
else
  # 解析成绝对路径（兼容相对路径：先按相对 REPO，再按相对 cwd）
  if [ -f "$target" ]; then idx="$target"; else idx="$target/index.md"; fi
  if [ ! -f "$idx" ]; then idx="$REPO/$target"; [ -f "$idx" ] || idx="$REPO/$target/index.md"; fi
  # 规范成绝对路径便于前缀匹配
  idx="$(cd "$(dirname "$idx")" && pwd)/$(basename "$idx")"
  [ -f "$idx" ] || { echo "❌ 找不到文章文件: $target（若已被 normalize 拍平成单文件，改用 --key 身份寻址）" >&2; exit 2; }
fi
case "$idx" in
  "$REPO"/content/posts/tech/*) section=tech;;
  "$REPO"/content/posts/video/*) section=video;;
  *) echo "❌ 目标不在 content/posts/tech 或 content/posts/video 下（不支持）: $idx" >&2; exit 2;;
esac
rel="${idx#$REPO/}"

# ---- 读 frontmatter 关键字段（source_key / title / draft / slug）----
# 同时读 HEAD 里的已提交版本：上线判定必须以 HEAD 为准——工作区的 draft:false
# 可能是上次 commit 失败的残留（翻 draft 在前、commit 在后），读工作区会把
# "上次失败"误判成"已上线"，exit 5 自锁拒绝恢复（2026-08-17 实证）。
head_tmp="$(mktemp -t publish-draft-head)"
git -C "$REPO" show "HEAD:$rel" > "$head_tmp" 2>/dev/null || true  # 新稿无 HEAD 版本 → 空文件
meta="$(python3 - "$idx" "$head_tmp" <<'PY'
import re, sys, json

def split_fm(c):
    m = re.match(r'^---\n(.*?)\n---\n', c, re.DOTALL)
    return (m.group(1), True) if m else ('', False)

def field(fm, n):
    mm = re.search(r'^' + n + r'\s*:\s*(.*?)\s*$', fm, re.MULTILINE)
    v = mm.group(1).strip() if mm else ''
    return v.strip("\"'")

fm, has_fm = split_fm(open(sys.argv[1]).read())
hfm, _ = split_fm(open(sys.argv[2]).read())
print(json.dumps({
    'source_key': field(fm, 'source_key'),
    'title': field(fm, 'title'),
    'draft': field(fm, 'draft'),
    'slug': field(fm, 'slug'),
    'head_draft': field(hfm, 'draft') if hfm else '',
    'has_fm': has_fm,
}, ensure_ascii=False))
PY
)"
rm -f "$head_tmp"
sk="$(echo "$meta" | python3 -c "import json,sys;print(json.load(sys.stdin)['source_key'])")"
title="$(echo "$meta" | python3 -c "import json,sys;print(json.load(sys.stdin)['title'])")"
draft_now="$(echo "$meta" | python3 -c "import json,sys;print(json.load(sys.stdin)['draft'])")"
head_draft="$(echo "$meta" | python3 -c "import json,sys;print(json.load(sys.stdin)['head_draft'])")"

# ---- 硬约束：HEAD 已是 draft:false（已提交上线态）则拒绝重发，防幂等破坏 ----
if [ "$head_draft" = "false" ] && [ "$force" != 1 ]; then
  echo "❌ 该文章已提交为 draft:false（上线态），不应重复发布：${rel}" >&2
  echo "   如需重新发布（如内容大改后重上），加 --force。" >&2
  exit 5
fi
# 工作区 false 但 HEAD 不是 = 上次 commit 失败的残留：翻 draft 幂等，继续完成即可
if [ "$draft_now" = "false" ] && [ "$head_draft" != "false" ]; then
  echo "ℹ️  工作区已是 draft:false（上次发布中断的残留，未提交），继续完成发布"
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
if [ "$force" != 1 ]; then
  # grep frontmatter 里的 source_key 行（排除当前文件自身）
  # 注意 BSD grep(macOS)ERE 不支持 \s、\$ 非行尾锚点：用 [[:space:]] 与裸 $
  # （此处曾因 \s 退化为可选 s 永不匹配空格，致去重保护长期静默失效，2026-08-16 修复）
  sk_re="$(printf '%s' "$sk" | sed 's/\./\\./g')"
  dup_list="$(grep -rlE "^source_key:[[:space:]]*[\"']?${sk_re}[\"']?[[:space:]]*$" "$REPO/content/posts" 2>/dev/null \
        | grep -v "^${idx}$" || true)"
  if [ -n "$dup_list" ]; then
    # 只拦截已上线（draft:false）的重复——同 key 草稿（draft:true）提示后放行
    dup_live=""
    while IFS= read -r f; do
      d="$(grep -m1 -E '^draft:' "$f" | sed 's/^draft:[[:space:]]*//;s/[[:space:]]*$//')"
      if [ "$d" = "false" ]; then dup_live="$f"; break; fi
    done <<< "$dup_list"
    if [ -n "$dup_live" ]; then
      echo "❌ 已存在同 source_key 的上线稿：${dup_live#$REPO/}" >&2
      echo "   source_key=$sk 是发布去重命脉。如确认要覆盖，加 --force（会翻旧稿 draft:true 撤下后重发）。" >&2
      exit 4
    fi
    echo "⚠️  存在同 source_key 的未上线草稿（放行，建议人工清理）：" >&2
    printf '%s\n' "$dup_list" | sed "s|^${REPO}/|   |" >&2
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
# 先备份原文件字节：commit 失败时必须回滚，否则残留的 draft:false 会把
# 工作区留在"已翻未提交"的中间态（旧版在此状态下重跑会误判已上线，见上）。
bak="$(mktemp -t publish-draft-bak)"
cp "$idx" "$bak"
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
if ! ( cd "$REPO" && git add "$rel" && git commit -m "$msg" -q ); then
  cp "$bak" "$idx"                    # 恢复进入脚本时的文件字节
  git -C "$REPO" reset -q HEAD -- "$rel" 2>/dev/null || true  # 撤回本次暂存（不碰工作区）
  rm -f "$bak"
  echo "❌ commit 失败（多为 pre-commit 的 lint/形态检查未过）。" >&2
  echo "   已回滚 draft 翻转与暂存区，文件保持进入脚本时的状态；修复后可直接重跑。" >&2
  exit 7
fi
rm -f "$bak"
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
# 展示路径：bundle 显示目录（去 index.md 尾巴），单文件原样显示
case "$rel" in */index.md) display="${rel%/*}/";; *) display="$rel";; esac
openclaw message send --channel feishu -t "$FEISHU_TO" -m "🎬 自动发布 · $(date +%H:%M)
• 《${title}》→ ${display}
• 评级 ${grade}（${score:-?}/100），cn-doc-writer 三维过闸自动上线
• source_key ${sk}，${status}
• 无需操作 ✅ 不满意可撤回：把 draft 翻回 true（commit ${hash_short}）" >/dev/null 2>&1 || true
echo "📤 已飞书报告"
