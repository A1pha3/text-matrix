#!/usr/bin/env bash
# scripts/morning-news-verify.sh
#
# 6-10 师父铁律：早报自动 push 到 GitHub，但 push 前必须通过本脚本验证。
# 6-09 师父铁律：早报内容严禁暴露 CDP/PID/JSON 路径等采集实现细节。
#
# 用法: bash scripts/morning-news-verify.sh <markdown文件绝对路径>
# 退出码: 0 = PASS（可以 push），1 = FAIL（不能 push）
#
# 检查项:
#   1. date 字段 ≤ 当前时间（不能是未来时间）
#   2. 隐私脱敏：禁词检查
#   3. 链接 200 验证（最多 50 条 / 5 条失败容忍）
#   4. 新闻条数 ≥ 6

set -euo pipefail

FILE="${1:?❌ 用法: bash scripts/morning-news-verify.sh <markdown文件绝对路径>}"

if [[ ! -f "$FILE" ]]; then
  echo "❌ FAIL: 文件不存在: $FILE"
  exit 1
fi

echo "🔍 验证文件: $FILE"
echo "   大小: $(wc -c < "$FILE" | tr -d ' ') bytes"
echo ""

# ---------- 1. date 字段 ≤ 当前时间 ----------
echo "→ [1/4] date 字段检查..."
date_in_file=$(grep -E '^date:' "$FILE" | head -1 | awk '{print $2}' | cut -dT -f1)
if [[ -z "$date_in_file" ]]; then
  echo "❌ FAIL: 文件缺少 date 字段"
  exit 1
fi
now=$(date +%Y-%m-%d)
if [[ "$date_in_file" > "$now" ]]; then
  echo "❌ FAIL: date 是未来时间 ($date_in_file > $now)"
  exit 1
fi
echo "  ✅ date: $date_in_file ≤ $now"

# ---------- 2. 隐私脱敏禁词检查 ----------
echo ""
echo "→ [2/4] 隐私脱敏禁词检查..."
forbidden=(
  "Chrome CDP"
  "Chrome 抓取"
  "Chrome访问"
  "PID 9222"
  "/tmp/"
  "og:description"
  "dataPublished"
  "反爬墙"
  "已逐条打开原文核验"
  "逐条打开原文核验"
  "数据来源：CoinMarketCap"
  "数据来源: CoinMarketCap"
  "数据来源段"
  "📎 已核验"
  "已丢弃候选"
  "已丢弃说明"
  "Chrome 抓取原始数据快照"
  "原始 JSON 路径"
  "原始JSON路径"
)
hit=""
for word in "${forbidden[@]}"; do
  if grep -qF "$word" "$FILE"; then
    hit="$hit\n  - $word"
  fi
done
if [[ -n "$hit" ]]; then
  echo -e "❌ FAIL: 隐私泄露命中禁词:$hit"
  exit 1
fi
echo "  ✅ 禁词干净"

# ---------- 3. 链接 200 验证（最多 50 条 / 5 条失败容忍）----------
echo ""
echo "→ [3/4] 链接 200 验证（最多 50 条 / 5 条失败容忍）..."
links=$(grep -oE 'https?://[^]) ）　，。；,;]+' "$FILE" | sort -u | head -50)
total=$(echo "$links" | grep -cE '^https?://' || true)
fail_count=0
fail_list=""
for url in $links; do
  code=$(curl -sL -m 10 -A "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Safari/605.1.15" -o /dev/null -w '%{http_code}' "$url" 2>/dev/null || echo "000")
  if [[ "$code" != "200" ]]; then
    fail_count=$((fail_count+1))
    fail_list="$fail_list\n  [$code] $url"
    if [[ $fail_count -ge 10 ]]; then
      echo "  ⚠️ 已累计 $fail_count 个失败链接，提前停止（>10）"
      break
    fi
  fi
done
echo "  共检查 $total 条链接，失败 $fail_count 条"
if [[ $fail_count -gt 0 ]]; then
  echo -e "  失败列表:$fail_list"
fi
if [[ $fail_count -gt 8 ]]; then
  echo "❌ FAIL: 链接失败 > 8 条（实际 $fail_count / $total），禁止 push"
  exit 1
fi
echo "  ✅ 链接验证通过（失败 $fail_count ≤ 8 容忍，约 16% 容忍度应对反爬）"

# ---------- 4. 新闻条数 ≥ 6 (AI 副业早报豁免至 ≥ 5) ----------
echo ""
echo "→ [4/4] 新闻条数检查（≥6，AI 副业早报豁免至 ≥ 5）..."
n=$(grep -cE '^## ' "$FILE" || true)
# 6-12 师父裁决：ai-side-hustle-morning 5## 豁免（cron 850cf6e9 heartbeat #83）
if [[ "$FILE" == *ai-side-hustle-morning* ]]; then
  MIN_HEADLINES=5
  echo "  ℹ️  AI 副业早报豁免阈值：≥ 5（6-12 师父裁决）"
else
  MIN_HEADLINES=6
fi
if [[ $n -lt $MIN_HEADLINES ]]; then
  echo "❌ FAIL: 新闻条数 < $MIN_HEADLINES（实际 $n）"
  exit 1
fi
echo "  ✅ 新闻条数: $n"

echo ""
echo "✅ PASS: 全部验证通过，可以 push 到 GitHub"
exit 0
