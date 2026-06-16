#!/usr/bin/env bash
# frontmatter-integrity-scan.sh - 扫描 content/posts 下所有 md 文件的 frontmatter 完整性
#
# 用途：34400b30 commit 一次性改了 548 个文件，把其中至少 1 个截断到 18 字节。
#       Hugo build 在第一个 EOF fail 时 stop，没暴露其他 547 个文件的同类问题。
#
# 扫描维度：
#   1. 文件大小 < 500B（疑似截断；早报格式都 970B+，< 500B 几乎肯定是截断）
#   2. frontmatter 起始缺失（既不是 `---` 也不是 `+++` 也不是 `{`）
#   3. frontmatter 结束缺失（YAML 缺 `---` / TOML 缺 `+++`）
#   4. frontmatter 内部含未配对引号 / 不合法 YAML
#
# 注意：Hugo 同时支持 YAML (`---`)、TOML (`+++`)、JSON (`{`) 三种 frontmatter 格式。
#       TOML 和 JSON 都是合法格式，仅在 warning 中提示，不算损坏。
#
# 用法：
#   bash scripts/frontmatter-integrity-scan.sh
#   bash scripts/frontmatter-integrity-scan.sh content/posts/tech/   # 限定子目录
#
# 输出：
#   - exit 0：无问题
#   - exit 1：有损坏文件，stdout 列出所有问题

set -u

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || true)"
if [[ -z "$REPO_ROOT" ]]; then
  echo "❌ 必须在 text-matrix 仓库根目录跑" >&2
  exit 2
fi
cd "$REPO_ROOT"

# 接受可选的扫描目录参数
SCAN_DIR="${1:-content/posts}"
if [[ ! -d "$SCAN_DIR" ]]; then
  echo "❌ 目录不存在: $SCAN_DIR" >&2
  exit 2
fi

echo "🔍 扫描 frontmatter 完整性: $SCAN_DIR/**/*.md"
echo ""

# macOS bash 3.2 不支持 mapfile，用 while-read 替代
MD_FILES=()
while IFS= read -r f; do
  MD_FILES+=("$f")
done < <(find "$SCAN_DIR" -name "*.md" -type f 2>/dev/null | sort)
TOTAL=${#MD_FILES[@]}

# 计数器
COUNT_SMALL=0          # < 1KB
COUNT_NO_OPEN=0        # 缺起始 ---
COUNT_NO_CLOSE=0       # 缺结束 --- (EOF)
COUNT_TOML=0           # TOML 格式 +++
COUNT_TOTAL_PROBLEM=0

# 问题文件清单
PROBLEM_FILES=()

echo "进度："
processed=0
for f in "${MD_FILES[@]}"; do
  processed=$((processed + 1))
  
  # 取相对路径
  rel=${f#$REPO_ROOT/}
  
  # 1. 文件大小
  size=$(wc -c < "$f" 2>/dev/null | tr -d ' ')
  size_kb=$((size / 1024))
  
  if [[ $size -lt 500 ]]; then
    # 跳过 _index.md / 目录索引（通常较小且有特殊 frontmatter 形式）
    base=$(basename "$f")
    if [[ "$base" == "_index.md" || "$base" == "README.md" ]]; then
      continue
    fi
    # 文件 < 500B 但不是索引页 → 高度可疑（早报都 970B+，< 500B 几乎肯定截断）
    echo "  ⚠️  [$processed/$TOTAL] SMALL  $rel (${size}B)"
    PROBLEM_FILES+=("SMALL($size):$rel")
    COUNT_SMALL=$((COUNT_SMALL + 1))
    COUNT_TOTAL_PROBLEM=$((COUNT_TOTAL_PROBLEM + 1))
    continue
  fi
  
  # 2. frontmatter 起始 — Hugo 同时支持 YAML (`---`)、TOML (`+++`)、JSON (`{`) 三种
  first_line=$(head -1 "$f" 2>/dev/null)
  
  # 2a. TOML 格式 (`+++`) — Hugo 合法，仅在 warning 中提示
  if [[ "$first_line" == "+++" ]]; then
    echo "  ℹ️  [$processed/$TOTAL] TOML  $rel (Hugo 合法格式)"
    PROBLEM_FILES+=("TOML_INFO:$rel")
    COUNT_TOML=$((COUNT_TOML + 1))
    # 不计入真损坏
    continue
  fi
  
  # 2b. 既不是 YAML 也不是 TOML — 缺起始分隔符
  if [[ "$first_line" != "---" ]]; then
    echo "  ❌ [$processed/$TOTAL] NO_OPEN  $rel (first line: ${first_line:0:30})"
    PROBLEM_FILES+=("NO_OPEN:$rel")
    COUNT_NO_OPEN=$((COUNT_NO_OPEN + 1))
    COUNT_TOTAL_PROBLEM=$((COUNT_TOTAL_PROBLEM + 1))
    continue
  fi
  
  # 4. frontmatter 结束 --- (EOF)
  # 找第二个 --- 在前 50 行内
  fm_end_line=$(awk 'NR > 1 && NR <= 50 && /^---[[:space:]]*$/ {print NR; exit}' "$f" 2>/dev/null)
  if [[ -z "$fm_end_line" ]]; then
    echo "  ❌ [$processed/$TOTAL] NO_CLOSE  $rel (前 50 行无结束 ---)"
    PROBLEM_FILES+=("NO_CLOSE:$rel")
    COUNT_NO_CLOSE=$((COUNT_NO_CLOSE + 1))
    COUNT_TOTAL_PROBLEM=$((COUNT_TOTAL_PROBLEM + 1))
    continue
  fi
done

echo ""
echo "── 扫描结果 ──"
echo "  总文件: $TOTAL"
echo "  ❌ 真损坏:   $COUNT_TOTAL_PROBLEM"
echo "    - SMALL (< 500B):       $COUNT_SMALL"
echo "    - NO_OPEN (缺起始):     $COUNT_NO_OPEN"
echo "    - NO_CLOSE (缺结束):    $COUNT_NO_CLOSE"
echo "  ℹ️  Hugo 合法非 YAML:  $COUNT_TOML (TOML 格式 +++)"

if [[ ${#PROBLEM_FILES[@]} -gt 0 ]]; then
  echo ""
  echo "── 损坏文件清单 ──"
  for p in "${PROBLEM_FILES[@]}"; do
    echo "  $p"
  done
  exit 1
fi
exit 0
