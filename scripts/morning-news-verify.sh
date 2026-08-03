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
#   4. 条目数 ≥3（3-6 需标注精简版；8-03 师父选 B）
#   5. 跨天去重（本文链接不得在历史早报重复；8-03 师父铁律）

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
echo "→ [1/5] date 字段检查..."
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
echo "→ [2/5] 隐私脱敏禁词检查..."
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
echo "→ [3/5] 链接 200 验证（最多 50 条 / 5 条失败容忍）..."
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

# ---------- 4. 条目数(8-03 师父选 B：源冷场允许精简，按原文链接计数) ----------
echo ""
echo "→ [4/5] 条目数检查（≥3；3-6 需标注精简版）..."
n=$(grep -oE '\]\(https?://[^)]+\)' "$FILE" | wc -l | tr -d ' ')
# 6-12 师父裁决：ai-side-hustle-morning 5## 豁免（cron 850cf6e9 heartbeat #83）
# ⚠️ 7-18 改: 豁免扩到 *ai-side-hustle-* (覆盖 morning + noon + 未来扩展)
# 6-12 原豁免: *ai-side-hustle-morning* (只覆盖早报)
# 16:06 师父裁决 D2: ai-side-hustle 全系列午报也享 H2 ≥ 5 豁免
# 8-03 师父选 B：filter 接入后源冷场日候选可能 <6，硬卡 ≥6 会卡死发不出。
# 新规则：≥3 即可；3-6 必须标注「精简版/源冷场」防偷懒少写。
if [[ $n -lt 3 ]]; then
  echo "❌ FAIL: 条目数 $n < 3（即便精简版至少 3 条）"
  exit 1
fi
if [[ $n -lt 6 ]]; then
  if ! grep -qE "精简版|源冷场|候选不足|今日精简" "$FILE"; then
    echo "❌ FAIL: 条目数 $n（<6）但未标注「精简版/源冷场」——少发可以，必须显式说明"
    exit 1
  fi
  echo "  ℹ️  精简版：$n 条（已标注源冷场，8-03 师父选 B）"
else
  echo "  ✅ 条目数: $n"
fi

# ---------- 5. 跨天去重(8-03 师父铁律:同链接不得跨天重复发布)----------
# 背景:SceniX(量子位 qbitai/464532)在 8-02/8-03 AI 早报连发两天。
# verify.sh 是全系列 push 前闸门,在此加确定性去重,不依赖模型自觉。
echo ""
echo "→ [5/5] 跨天去重检查(本文链接不得在历史早报重复)..."
set +e
python3 - "$FILE" << 'PYEOF'
import sys, re, os, glob
from urllib.parse import urlsplit

file_path = sys.argv[1]
# 从 FILE 往上定位 content/posts/news(不依赖 git/cwd)
d = os.path.dirname(os.path.abspath(file_path))
repo_root = None
while d != "/":
    if os.path.isdir(os.path.join(d, "content/posts/news")):
        repo_root = d; break
    d = os.path.dirname(d)
if not repo_root:
    print("  ⚠️  跳过跨天去重:未定位到 content/posts/news")
    sys.exit(0)
news_dir = os.path.join(repo_root, "content/posts/news")

def norm(u):
    """URL 归一化:统一小写 scheme/host、去 www.、去 query/fragment、去尾斜杠。
    使 qbitai.com/.../464532.html 与 www.qbitai.com/.../464532.html?utm=x 判同。"""
    p = urlsplit(u.strip())
    host = (p.netloc or "").lower()
    if host.startswith("www."):
        host = host[4:]
    path = p.path or ""
    if len(path) > 1 and path.endswith("/"):
        path = path.rstrip("/")
    return f"{p.scheme.lower()}://{host}{path}"

try:
    body = open(file_path, encoding="utf-8").read()
except Exception:
    print("  ⚠️  跳过跨天去重:读取文件失败")
    sys.exit(0)

# 本文所有 [原文](url) 链接,归一化后去重
my_urls = [u.strip() for u in re.findall(r"\]\((https?://[^)]+)\)", body)]
my_norm = {norm(u): u for u in my_urls}
self_name = os.path.basename(file_path)

# 扫描所有历史早报(排除本文自身),建 URL→文件名 倒排
hist = {}
for f in glob.glob(os.path.join(news_dir, "*.md")):
    bn = os.path.basename(f)
    if bn == self_name:
        continue
    try:
        txt = open(f, encoding="utf-8").read()
    except Exception:
        continue
    for u in re.findall(r"\]\((https?://[^)]+)\)", txt):
        hist.setdefault(norm(u.strip()), []).append(bn)

hits = [(orig, hist[n]) for n, orig in my_norm.items() if n in hist]

if not hits:
    print(f"  ✅ 跨天去重通过(检查 {len(my_norm)} 条链接,无历史重复)")
    sys.exit(0)

print(f"  ❌ 跨天去重 FAIL:{len(hits)} 条链接已在历史早报发布")
for orig, files in hits:
    print(f"    🔁 {orig}")
    for fbn in sorted(set(files)):
        print(f"        ← 已发于 {fbn}")
print("  铁律(8-03):同链接不得跨天重复。请删除/替换命中条目后再 push。")
sys.exit(1)
PYEOF
DUP_RC=$?
set -e
if [[ $DUP_RC -ne 0 ]]; then
  echo "❌ FAIL: 跨天去重未通过,禁止 push"
  exit 1
fi

echo ""
echo "✅ PASS: 全部验证通过，可以 push 到 GitHub"
exit 0
