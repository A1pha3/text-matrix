#!/usr/bin/env bash
# morning-news-web3-dedup.sh - Web3 早报事件级去重兜底检查
#
# 用途：web3 早报采集到一批候选 URL 列表后，写稿前用本脚本判断每个 URL
#       是否已在过去 N 天的 web3 早报里出现过。命中即视为"已用"，必须：
#       1) 优先丢弃；或
#       2) 如果是持续更新型文章，必须 fetch 文章正文比对"last updated"时间，
#          只有 24h 内更新才保留 + 在摘要里明确标注"本文为 6-XX 同事件更新"
#
# 为什么需要这个脚本（2026-06-19 师父拍板 C 方案建立）：
#   1. CoinTelegraph / CoinDesk 大量"持续更新型"文章（同一 URL 内容持续被作者更新）
#      仅按 URL 去重会反复抓到同一事件
#   2. web3 早报 100% 单一来源（CoinTelegraph），无多源交叉验证
#   3. cron prompt 原本只有"24h 时间窗口"，缺"已用 URL 黑名单"约束
#   4. AI 写摘要时会用新时间副词包装旧事件，制造"新事件"假象
#
# 用法：
#   bash scripts/morning-news-web3-dedup.sh <url1> [<url2> ...]
#   # 或从 stdin：
#   cat candidates.txt | bash scripts/morning-news-web3-dedup.sh
#   # 或带选项：
#   bash scripts/morning-news-web3-dedup.sh --threshold 3 <url1> ...
#       # --threshold N: 跨天数超过 N 天视为严重复用（默认 3）
#       # --window N: 回溯 N 天扫描（默认 14）
#       # --json: 输出 JSON 格式供子代理消费
#
# 输出：
#   - exit 0: 所有 URL 都是新事件或轻微复用（< threshold 天）
#   - exit 1: 有 URL 严重复用（>= threshold 天），stdout 列出"已用" + 命中历史
#   - exit 2: 参数错误 / 路径错
#
# 双重 grep 兜底（任一命中即视为"已用"）：
#   A. state file ~/.openclaw/workspace/state/web3-event-fingerprint.json
#   B. content/posts/news/web3-morning-news-*.md 文件系统全量扫（处理 state 丢失）
#
# 师父铁律（2026-06-19 拍板）：
#   - 持续更新型文章 + 跨天数 >= 3 天 → 必须丢弃，除非 fetch 后确认 last-updated < 24h
#   - cron 子代理在动笔前必须跑本脚本，exit 1 时的 URL 必须从候选清单剔除

set -euo pipefail

# ---------- 参数解析 ----------
THRESHOLD=3
WINDOW=14
JSON_OUTPUT=false
TODAY=""  # 本轮要写的早报日期（YYYY-MM-DD），用于排除"自我命中"
URLS=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --threshold)
      THRESHOLD="$2"
      shift 2
      ;;
    --window)
      WINDOW="$2"
      shift 2
      ;;
    --today)
      TODAY="$2"
      shift 2
      ;;
    --json)
      JSON_OUTPUT=true
      shift
      ;;
    -h|--help)
      echo "用法: $0 [--threshold N] [--window N] [--today YYYY-MM-DD] [--json] <url1> [<url2> ...]" >&2
      echo "  --threshold N    跨天数 >= N 视为严重复用（默认 3）" >&2
      echo "  --window N       回溯 N 天扫描（默认 14）" >&2
      echo "  --today DATE     本轮要写的早报日期（YYYY-MM-DD），用于排除'自我命中'" >&2
      echo "  --json           输出 JSON 格式" >&2
      exit 0
      ;;
    *)
      URLS+=("$1")
      shift
      ;;
  esac
done

# 自动推断 today：取今天（北京时间）
if [[ -z "$TODAY" ]]; then
  TODAY=$(TZ=Asia/Shanghai date +%Y-%m-%d)
fi

# 从 stdin 读
if [[ ${#URLS[@]} -eq 0 ]]; then
  while IFS= read -r line; do
    line=$(echo "$line" | tr -d '[:space:]')
    [[ -n "$line" ]] && URLS+=("$line")
  done
fi

if [[ ${#URLS[@]} -eq 0 ]]; then
  echo "❌ 用法: $0 [--threshold N] [--window N] [--json] <url1> [<url2> ...]" >&2
  echo "   或: cat candidates.txt | $0" >&2
  exit 2
fi

# ---------- 路径检查 ----------
REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || true)"
if [[ -z "$REPO_ROOT" || ! -d "$REPO_ROOT/content/posts/news" ]]; then
  echo "❌ 必须在 text-matrix 仓库根目录跑（找不到 content/posts/news/）" >&2
  exit 2
fi
cd "$REPO_ROOT"

STATE_FILE="$HOME/.openclaw/workspace/state/web3-event-fingerprint.json"
if [[ ! -f "$STATE_FILE" ]]; then
  echo "⚠️  警告: state file 不存在: $STATE_FILE" >&2
  echo "    仅做文件系统兜底（重 B），未命中 state 但命中文件系统仍会标记" >&2
  HAS_STATE=false
else
  HAS_STATE=true
fi

# ---------- 工具函数 ----------
# 从 URL 提取 slug
url_to_slug() {
  local url="$1"
  # 取 /news/<slug>/ 或 /<year>/<month>/<day>/<slug> 的末段
  if [[ "$url" =~ /news/([^/?#]+) ]]; then
    echo "${BASH_REMATCH[1]}"
  elif [[ "$url" =~ /[0-9]{4}/[0-9]{2}/[0-9]{2}/([^/?#]+) ]]; then
    echo "${BASH_REMATCH[1]}"
  else
    # 取末段
    echo "${url##*/}" | sed 's/[?#].*//'
  fi
}

# 从 state file 查 slug → event info
state_lookup() {
  local slug="$1"
  if [[ "$HAS_STATE" != "true" ]]; then
    return 1
  fi
  python3 -c "
import json, sys
with open('$STATE_FILE') as f:
    state = json.load(f)
ev = state.get('events', {}).get('$slug')
if ev:
    print(json.dumps(ev, ensure_ascii=False))
else:
    sys.exit(1)
" 2>/dev/null
}

# 文件系统全量扫（按 slug 在所有 web3 早报里搜，排除"自我命中"）
fs_lookup() {
  local slug="$1"
  local news_dir="$REPO_ROOT/content/posts/news"
  # 按 slug 模糊匹配（排除今天 + 排除本轮要写的文件）
  local hits
  hits=$(grep -lF "$slug" "$news_dir"/web3-morning-news-*.md 2>/dev/null \
    | grep -v "web3-morning-news-${TODAY}\.md" \
    | grep -v "web3-morning-news-$(date +%Y-%m-%d)\.md" \
    | sort -u || true)
  if [[ -n "$hits" ]]; then
    echo "$hits"
  else
    return 1
  fi
}

# ---------- 主逻辑 ----------
NEW_URLS=()
SEVERE_REUSE=()
MILD_REUSE=()

JSON_RESULTS=()

for url in "${URLS[@]}"; do
  url=$(echo "$url" | tr -d '[:space:]')
  [[ -z "$url" ]] && continue
  slug=$(url_to_slug "$url")
  
  state_hit=""
  fs_hits=""
  matched_files=()
  span=0
  is_continuously_updated=false
  first_seen=""
  last_seen=""
  entity=""
  has_history=false  # 是否在历史（非今天）早报里出现过
  
  # 重 A: state file
  if [[ "$HAS_STATE" == "true" ]]; then
    if state_hit=$(state_lookup "$slug" 2>/dev/null); then
      span=$(echo "$state_hit" | python3 -c "import json,sys; print(json.load(sys.stdin).get('span_days', 0))" 2>/dev/null || echo 0)
      is_continuously_updated=$(echo "$state_hit" | python3 -c "import json,sys; print(json.load(sys.stdin).get('is_continuously_updated', False))" 2>/dev/null || echo "False")
      first_seen=$(echo "$state_hit" | python3 -c "import json,sys; print(json.load(sys.stdin).get('first_seen', ''))" 2>/dev/null || echo "")
      last_seen=$(echo "$state_hit" | python3 -c "import json,sys; print(json.load(sys.stdin).get('last_seen', ''))" 2>/dev/null || echo "")
      entity=$(echo "$state_hit" | python3 -c "import json,sys; print(json.load(sys.stdin).get('entity', ''))" 2>/dev/null || echo "")
    fi
  fi
  
  # 重 B: 文件系统兜底（取日期列表）
  if fs_hits=$(fs_lookup "$slug" 2>/dev/null); then
    has_history=true
    while IFS= read -r f; do
      matched_files+=("$f")
    done <<< "$fs_hits"
  fi
  
  # 如果 state 没命中但 fs 命中了 → 用 fs 的日期算 span
  if [[ -z "$state_hit" && ${#matched_files[@]} -gt 0 ]]; then
    fs_dates=$(for f in "${matched_files[@]}"; do
      basename "$f" | grep -oE '2026-06-[0-9]{2}' || true
    done | sort -u)
    if [[ -n "$fs_dates" ]]; then
      first_seen=$(echo "$fs_dates" | head -1)
      last_seen=$(echo "$fs_dates" | tail -1)
      if [[ -n "$first_seen" && -n "$last_seen" ]]; then
        first_ts=$(date -j -f "%Y-%m-%d" "$first_seen" +%s 2>/dev/null || echo 0)
        last_ts=$(date -j -f "%Y-%m-%d" "$last_seen" +%s 2>/dev/null || echo 0)
        if [[ "$first_ts" -gt 0 && "$last_ts" -gt 0 ]]; then
          span=$(( (last_ts - first_ts) / 86400 ))
        fi
      fi
    fi
  fi
  
  # 判定
  hit_a=$([ -n "$state_hit" ] && echo "yes" || echo "no")
  hit_b=$([ "$has_history" == "true" ] && echo "yes" || echo "no")
  
  if [[ "$hit_a" == "yes" || "$hit_b" == "yes" ]]; then
    # 命中历史（非自我命中）
    # 边界：seen_count == 1 且 last_seen == TODAY → 本轮首次出现，视为新事件
    if [[ "$span" -eq 0 && "$last_seen" == "$TODAY" ]]; then
      # 转移到 NEW_URLS（不视为复用）
      NEW_URLS+=("$url")
      if [[ "$JSON_OUTPUT" == "true" ]]; then
        json_line=$(python3 - "$url" "$slug" "$span" "$is_continuously_updated" "$first_seen" "$last_seen" "$entity" "$hit_a" "$hit_b" << 'PYEOF'
import json, sys
url, slug, span, is_cont, first_seen, last_seen, entity, hit_a, hit_b = sys.argv[1:]
print(json.dumps({
  'url': url,
  'slug': slug,
  'status': 'new',
  'span_days': int(span),
  'is_continuously_updated': is_cont == 'True',
  'first_seen': first_seen,
  'last_seen': last_seen,
  'entity': entity,
  'matched_files': [],
  'hit_state': hit_a,
  'hit_fs': hit_b
}, ensure_ascii=False))
PYEOF
)
        JSON_RESULTS+=("$json_line")
      else
        echo "  ✅ 新事件 $slug"
        echo "     URL: $url"
      fi
      continue
    fi
    
    # 真正复用
    severity=$([ "$span" -ge "$THRESHOLD" ] && echo "severe" || echo "mild")
    if [[ "$severity" == "severe" ]]; then
      SEVERE_REUSE+=("$url")
    else
      MILD_REUSE+=("$url")
    fi
    
    if [[ "$JSON_OUTPUT" == "true" ]]; then
      # 用 here-doc 生成 JSON 行（避免 bash 转义问题）
      matched_files_json=$(printf '%s\n' "${matched_files[@]}" | python3 -c 'import json,sys; print(json.dumps([l.strip() for l in sys.stdin if l.strip()]))')
      json_line=$(python3 - "$url" "$slug" "$severity" "$span" "$is_continuously_updated" "$first_seen" "$last_seen" "$entity" "$hit_a" "$hit_b" "$matched_files_json" << 'PYEOF'
import json, sys
url, slug, severity, span, is_cont, first_seen, last_seen, entity, hit_a, hit_b, matched = sys.argv[1:]
print(json.dumps({
  'url': url,
  'slug': slug,
  'status': f'reused_{severity}',
  'span_days': int(span),
  'is_continuously_updated': is_cont == 'True',
  'first_seen': first_seen,
  'last_seen': last_seen,
  'entity': entity,
  'matched_files': json.loads(matched),
  'hit_state': hit_a,
  'hit_fs': hit_b
}, ensure_ascii=False))
PYEOF
)
      JSON_RESULTS+=("$json_line")
    else
      icon=$([ "$span" -ge 7 ] && echo "🔴" || ([ "$span" -ge 3 ] && echo "🟠" || echo "🟡"))
      cont_tag=$([ "$is_continuously_updated" == "True" ] && echo "[持续更新型]" || echo "")
      echo "  $icon 复用 $slug (跨 ${span} 天) $cont_tag"
      echo "     URL: $url"
      if [[ -n "$entity" ]]; then
        echo "     主体: $entity"
      fi
      echo "     首次: $first_seen → 最近: $last_seen"
      if [[ ${#matched_files[@]} -gt 0 ]]; then
        echo "     命中文件:"
        for f in "${matched_files[@]}"; do
          echo "       - $(basename "$f")"
        done
      fi
    fi
  else
    NEW_URLS+=("$url")
    if [[ "$JSON_OUTPUT" == "true" ]]; then
      json_line=$(python3 - "$url" "$slug" << 'PYEOF'
import json, sys
url, slug = sys.argv[1:]
print(json.dumps({
  'url': url,
  'slug': slug,
  'status': 'new',
  'span_days': 0,
  'is_continuously_updated': False,
  'first_seen': '',
  'last_seen': '',
  'entity': '',
  'matched_files': [],
  'hit_state': 'no',
  'hit_fs': 'no'
}, ensure_ascii=False))
PYEOF
)
      JSON_RESULTS+=("$json_line")
    else
      echo "  ✅ 新事件 $slug"
      echo "     URL: $url"
    fi
  fi
done

# ---------- 汇总 ----------
if [[ "$JSON_OUTPUT" == "true" ]]; then
  # 写临时文件，Python 读入
  TMP_JSON=$(mktemp)
  for line in "${JSON_RESULTS[@]}"; do
    echo "$line" >> "$TMP_JSON"
  done
  python3 - "$THRESHOLD" "$WINDOW" "$TMP_JSON" << 'PYEOF'
import json, sys
threshold, window, tmp_path = sys.argv[1], sys.argv[2], sys.argv[3]
results = []
with open(tmp_path) as f:
    for line in f:
        line = line.strip()
        if line:
            results.append(json.loads(line))
summary = {
  'total': len(results),
  'new': sum(1 for r in results if r['status'] == 'new'),
  'mild_reuse': sum(1 for r in results if r['status'] == 'reused_mild'),
  'severe_reuse': sum(1 for r in results if r['status'] == 'reused_severe'),
  'threshold_days': int(threshold),
  'window_days': int(window),
  'results': results
}
print(json.dumps(summary, ensure_ascii=False, indent=2))
PYEOF
  rm -f "$TMP_JSON"
else
  echo ""
  echo "── 汇总 ──"
  echo "  ✅ 新事件: ${#NEW_URLS[@]}"
  echo "  🟡 轻微复用 (< ${THRESHOLD} 天): ${#MILD_REUSE[@]}"
  echo "  🟠🔴 严重复用 (>= ${THRESHOLD} 天): ${#SEVERE_REUSE[@]}"
  
  if [[ ${#NEW_URLS[@]} -gt 0 ]]; then
    echo ""
    echo "可写清单（去重后）:"
    for u in "${NEW_URLS[@]}"; do
      echo "  - $u"
    done
  fi
  
  if [[ ${#SEVERE_REUSE[@]} -gt 0 ]]; then
    echo ""
    echo "⚠️  严重复用 URL（必须丢弃，6-19 师父铁律 C 方案）:"
    for u in "${SEVERE_REUSE[@]}"; do
      echo "  - $u"
    done
  fi
fi

# exit code
if [[ ${#SEVERE_REUSE[@]} -gt 0 ]]; then
  exit 1
fi
exit 0
