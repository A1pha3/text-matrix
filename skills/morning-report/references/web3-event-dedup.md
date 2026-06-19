# Web3 早报事件级去重指引（2026-06-19 师父拍板 C 方案）

## 为什么需要这一步

2026-06-19 师父审查 web3 早报时发现 3 条"几天前的旧闻"：

| URL 末段 | 跨天数 | 严重度 |
|----------|--------|--------|
| `fg-nexus-offloads-additional-178m-ether-as-treasury-losses-top-100m` | **14 天**（6-05 → 6-19） | 🔴 极重 |
| `bitmine-boosts-ethereum-treasury-to-554m-eth-nearing-5-supply-target` | **5 天**（6-14 → 6-19） | 🟠 重 |
| `strategy-michael-saylor-1587-btc-buy-100-million` | **3 天**（6-16 → 6-19） | 🟠 重 |

**根因**：
1. CoinTelegraph 大量"持续更新型"文章（同一 URL slug 内容被作者持续更新，不生成新 URL）
2. web3 早报 100% 单一来源（CoinTelegraph），无多源交叉验证
3. cron prompt 只有"24h 时间窗口"约束，缺"已用 URL 黑名单"约束
4. AI 写摘要时把同一事件用新时间副词包装，制造"新事件"假象

## 解决方案：C 方案（事件级去重）

### 双层去重机制

**A. state file**（本地，不入 GitHub）
- 路径：`~/.openclaw/workspace/state/web3-event-fingerprint.json`
- 135 个 event，4 个持续更新型（截至 2026-06-19）
- 由 web3 早报生成器每次跑完后自动更新

**B. 文件系统兜底**
- 扫 `content/posts/news/web3-morning-news-*.md` 全部历史早报
- 自动排除"今天"（避免自我命中）
- 双保险：state 丢失时仍可工作

### 3 重判定

| 重数 | 检查项 | 命中即视为已用 |
|------|--------|--------------|
| A 重 | state file 命中 | ✅ |
| B 重 | 文件系统历史早报命中 | ✅ |
| C 重 | 持续更新型 + 跨 ≥ 3 天 | 🔴 强制丢弃 |

### 执行流程

```bash
# 1. 采集候选 URL
URLS=(
  "https://cointelegraph.com/news/xxx-1"
  "https://cointelegraph.com/news/yyy-2"
  ...
)

# 2. 跑去重脚本（强约束，exit 0 才能进 step 3）
cd ~/.openclaw/workspace/github/text-matrix
bash scripts/morning-news-web3-dedup.sh --threshold 3 --window 14 "${URLS[@]}"

# 3. exit 0: 全部新事件 / 轻微复用，继续
#    exit 1: 有严重复用 URL，剔除后继续（"✅ 新事件"清单是允许列表）
#    exit 2: 路径错（不在仓库根目录）
```

### JSON 模式（子代理推荐）

```bash
bash scripts/morning-news-web3-dedup.sh --json "${URLS[@]}" > /tmp/dedup-result.json
# 用 jq 提取"可写清单"
jq -r '.results[] | select(.status == "new") | .url' /tmp/dedup-result.json
```

### state file 更新

每次 web3 早报生成后，**必须**更新 state：

```python
# 伪代码（实际由 collect-*.mjs 完成）
import json
from pathlib import Path
state_path = Path.home() / ".openclaw/workspace/state/web3-event-fingerprint.json"
state = json.loads(state_path.read_text())
# 把今天每条新闻的 URL 加入 state
for url, title, summary in today_news:
    slug = url_to_slug(url)
    state["events"][slug] = {
        "url": url,
        "slug": slug,
        "first_seen": today,
        "last_seen": today,
        "seen_count": state.get(slug, {}).get("seen_count", 0) + 1,
        "seen_dates": sorted(set(state.get(slug, {}).get("seen_dates", []) + [today])),
        "is_continuously_updated": ...,
        ...
    }
state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2))
```

## 持续更新型文章的特殊处理

**判断标准**：
- state file 中 `is_continuously_updated=true`
- 跨 ≥ 3 天再次出现在候选清单

**3 种处理方式**（按优先级）：

1. **直接丢弃**（最常见，6-19 三条都属此类）
2. **保留但摘要必须明确标注**：
   - 标题前缀加"【同事件更新·6-19】"
   - 摘要里写"本文为 CoinTelegraph 持续更新型报道，前次见于 6-XX 早报"
3. **多源交叉验证**（仅当同一事件在 CoinDesk / Decrypt 有独立报道时）

**默认走 1，2/3 需用户显式批准**。

## 横向对比：4 份早报的去重策略

| 早报 | 去重 | 理由 |
|------|------|------|
| AI 新闻 | URL 级（轻） | 多来源（36kr/qbitai/HN/TechCrunch/36kr），天然分散 |
| 经济财经 | URL 级（轻） | 主用 wallstreetcn + 行情，单事件单 URL |
| AI 副业 | URL 级（轻） | 多来源（reddit/v2ex/indiehackers） |
| **Web3** | **事件级（重）+ 持续更新型标记** | **单一来源 + 大量 live-update 文章** |

## 紧急补做（6-19 早报）

如果师父要求"立即修复 6-19 早报里的 3 条旧闻"：

```bash
# 1. 跑 dedup 脚本识别
cd ~/.openclaw/workspace/github/text-matrix
bash scripts/morning-news-web3-dedup.sh --threshold 3 --window 14 \
  https://cointelegraph.com/news/fg-nexus-offloads-additional-178m-ether-as-treasury-losses-top-100m \
  https://cointelegraph.com/news/bitmine-boosts-ethereum-treasury-to-554m-eth-nearing-5-supply-target \
  https://cointelegraph.com/news/strategy-michael-saylor-1587-btc-buy-100-million

# 2. 从 6-19 早报删除这 3 条 + 补 1-2 条全新事件
# 3. 重新 commit + push
```

## 验证与回滚

**验证 dedup 脚本有效**：
```bash
# 测试：6-19 早报 11 条 URL 应识别 3 条严重复用
bash scripts/morning-news-web3-dedup.sh \
  $(grep -oE 'https://cointelegraph.com/[^)]+' content/posts/news/web3-morning-news-2026-06-19.md | sort -u)
# 期望：exit 0 + 3 条严重复用提示
```

**回滚**：删除 state file + 删除 dedup 脚本（git revert commit）即可。

## 记忆来源

- 2026-06-19 10:12 师父飞书 message `om_x100b6c7e144374a4b2ecba680b40b9b`："徒儿，我发现web3早报中，有些 新闻消息是好几天前的，这个问题你查一下原因"
- 2026-06-19 10:23 师父飞书 message `om_x100b6c7ece4678a4b3bee5d58efd67f`："直接上C方案"
- 2026-06-16 16:03 trending-dedup-check.sh 模板（github-article-writer 已验证可行）
