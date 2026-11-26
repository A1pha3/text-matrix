#!/usr/bin/env python3
"""trending-daily-filter.py — daily 榜候选筛选（2026-11-26 对抗审查新增）。

背景：trending cron 原来只抓 weekly + monthly（daily 被判"波动大、昀花多"跳过），
但 weekly/monthly 榜更新慢，候选池枯竭——11-25 实测 29 个候选里 28 个早已写过，
每天增量只有 0-1 篇。daily 榜能补上"当天新冒出来"的项目，是三个维度里唯一带
时效性的渠道。

问题：daily 榜混着两类东西——
  ① 天天霸榜的老面孔（nginx/firecrawl 常年霸位）→ 写过一次就没必要再写，
     它们的机会在 weekly/monthly 渠道，挤占 daily 名额没有价值；
  ② 真正的昀花（刚被 star 收藏、无人 fork、无主线）→ 写不出深度文章。

策略：daily 渠道只收"最近才出现"的硬项目（老面孔抑制 + 硬门槛兜底）。
weekly/monthly 两个维度原样透传，去重由 trending-dedup-check.sh 统一负责。

用法：
  python3 scripts/trending-daily-filter.py --cache=<cache_dir> <parsed.json>
    <parsed.json> = parse-trending.py 的输出（{"daily":[...],"weekly":[...],...}）
    stdout = 过滤后的同结构 JSON；stderr = 人类可读诊断

  --cache 目录里维护 daily-seen.json（本地状态，不进 GitHub），
  记录每个 repo 在 daily 榜的出现历史，用于"连续出现天数"判定。
"""

import argparse
import json
import subprocess
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

# 硬门槛：宽松兜底即可，真正的减法靠"老面孔抑制"。
# 取值参考 2026-11-26 daily 榜实测（最低 stars=12749 / forks=2125），
# 纯昀花项目通常 stars < 500 且 forks 极少，两条门槛足以兜住。
MIN_STARS = 1000
MIN_FORKS = 50
ACTIVE_WITHIN_DAYS = 90
# 连续在榜多少天算"老面孔"，不再占用 daily 名额（其机会走 weekly/monthly）。
STALE_DAYS = 3


def gh_repo_meta(full):
    """取单个 repo 元数据；失败返回 None（不因单个失败中断整批）。"""
    try:
        out = subprocess.run(
            ["gh", "api", f"repos/{full}",
             "-q", "[.stargazers_count, .forks_count, .archived, .pushed_at, (.description // \"\"), (.created_at // \"\")] | @tsv"],
            capture_output=True, text=True, timeout=25)
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return None
    if out.returncode != 0:
        return None
    parts = out.stdout.strip().split("\t")
    if len(parts) < 6:
        return None
    try:
        return {
            "stars": int(parts[0] or 0),
            "forks": int(parts[1] or 0),
            "archived": parts[2] == "true",
            "pushed_at": parts[3],
            "description": parts[4],
            "created_at": parts[5],
        }
    except ValueError:
        return None


def load_seen(path):
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def save_seen(path, seen):
    path.write_text(json.dumps(seen, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--cache", required=True, help="raw HTML / 状态文件所在目录")
    ap.add_argument("parsed", help="parse-trending.py 的输出 JSON 文件（- 表示 stdin）")
    ap.add_argument("--min-stars", type=int, default=MIN_STARS)
    ap.add_argument("--min-forks", type=int, default=MIN_FORKS)
    ap.add_argument("--active-days", type=int, default=ACTIVE_WITHIN_DAYS)
    ap.add_argument("--stale-days", type=int, default=STALE_DAYS)
    args = ap.parse_args()

    raw = sys.stdin.read() if args.parsed == "-" else Path(args.parsed).read_text(encoding="utf-8")
    data = json.loads(raw)

    cache = Path(args.cache)
    seen_path = cache / "daily-seen.json"
    seen = load_seen(seen_path)
    today = date.today()
    cutoff = (today - timedelta(days=args.active_days)).isoformat()

    daily = data.get("daily") or []
    kept, dropped = [], []
    for repo in daily:
        full = repo.get("full")
        if not full:
            continue
        meta = gh_repo_meta(full)
        if meta is None:
            # 查不到元数据：保守丢弃（写文章需要 gh repo view 的元数据，查不到说明 repo 异常）
            dropped.append((full, "元数据查询失败（gh api 报错/超时）"))
            continue

        rec = seen.get(full)
        if rec:
            last = rec.get("last")
            if last == today.isoformat():
                days = rec.get("days", 1)
            else:
                days = rec.get("days", 1) + 1
        else:
            days = 1
        seen[full] = {"first": (rec or {}).get("first", today.isoformat()),
                      "last": today.isoformat(), "days": days}

        if meta["archived"]:
            dropped.append((full, "已归档"))
            continue
        if meta["stars"] < args.min_stars:
            dropped.append((full, f"stars {meta['stars']} < {args.min_stars}（疑似昙花）"))
            continue
        if meta["forks"] < args.min_forks:
            dropped.append((full, f"forks {meta['forks']} < {args.min_forks}（只收藏不用）"))
            continue
        if not (meta["pushed_at"] or "")[:10] >= cutoff:
            dropped.append((full, f"{(meta['pushed_at'] or '?')[:10]} 无近期提交（不活跃）"))
            continue
        if not (meta["description"] or "").strip():
            dropped.append((full, "无 description（判断不出技术主线）"))
            continue
        if days >= args.stale_days:
            dropped.append((full, f"连续 {days} 天在 daily 榜（老面孔，走 weekly/monthly 渠道）"))
            continue

        item = dict(repo)
        item["stars"] = meta["stars"]
        item["forks"] = meta["forks"]
        item["daily_days"] = days
        item["first_seen"] = seen[full]["first"]
        kept.append(item)

    save_seen(seen_path, seen)

    data["daily"] = kept
    print(json.dumps(data, ensure_ascii=False, indent=2))

    print(f"\n📊 daily 榜筛选：{len(daily)} → {len(kept)} 通过"
          f"（门槛 stars≥{args.min_stars} / forks≥{args.min_forks} / "
          f"{args.active_days}天内活跃 / 非归档 / 有 description / 连续上榜<{args.stale_days}天）",
          file=sys.stderr)
    for item in kept:
        tag = "🆕 首现" if item["daily_days"] == 1 else f"第{item['daily_days']}天"
        print(f"  ✅ {item['full']:<45} ⭐{item['stars']:<7} 🍴{item['forks']:<6} [{tag}]",
              file=sys.stderr)
    for full, why in dropped:
        print(f"  ⏭️  {full:<45} {why}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
