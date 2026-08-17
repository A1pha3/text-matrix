#!/usr/bin/env python3
"""检查构建产物中的站内链接是否会 404。

用法:
    python3 scripts/check_internal_links.py [--site-dir public] [--base https://txtmix.com]

设计要点:
- 标签级解析: 只认真实 <a>/<img>/<link>/<script> 等标签里的 href/src，
  天然跳过 <pre><code> 里被转义的示例代码（&lt;a href=... 不会命中），
  避免把文章里的代码示例误报为断链。
- 覆盖三类来源: 渲染后的 HTML（含压缩后无引号属性）、sitemap.xml 的 <loc>、
  RSS/Atom/JSON feed 的 <link>/<guid> 与 href。
- /pagefind/ 前缀跳过: 其索引文件由 run_pagefind.sh 生成，且链接由 JS 运行时使用。
- 退出码: 发现断链返回 1（供 CI 卡点），否则 0。

已知边界: 相对链接按浏览器语义（相对页面 URL 目录）解析；Hugo 站点正文里的
相对 .md 链接几乎必然 404（.md 不会发布），本脚本会如实报出。
"""
from __future__ import annotations

import argparse
import re
import sys
import urllib.parse
from collections import defaultdict
from pathlib import Path

TAG_RE = re.compile(
    r"<(a|img|link|script|source|iframe|embed|video|audio|track|form|input|object|use)\b([^>]*)>",
    re.IGNORECASE,
)
ATTR_RE = re.compile(
    r"""(?:href|src|data-src|data-href|data-lazy-src|poster|action)\s*=\s*(?:"([^"]+)"|'([^']+)'|([^\s>]+))""",
    re.IGNORECASE,
)
SRCSET_RE = re.compile(
    r"""(?:data-)?srcset\s*=\s*(?:"([^"]+)"|'([^']+)'|([^\s>]+))""", re.IGNORECASE
)
SKIP_PREFIXES = (
    "http://", "https://", "//", "mailto:", "tel:", "javascript:",
    "data:", "#", "sms:", "ftp:", "about:",
)
SKIP_PATH_PREFIXES = ("/pagefind/",)
SCHEME_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.-]*:")


def first_group(m: re.Match) -> str | None:
    return next((g for g in m.groups() if g), None)


class LinkChecker:
    def __init__(self, site_dir: Path, base: str):
        self.site_dir = site_dir
        self.base = base.rstrip("/")
        self.broken: dict[str, set[str]] = defaultdict(set)
        self.checked = 0

    def resolve(self, site_path: str) -> bool:
        path = site_path.split("#", 1)[0].split("?", 1)[0]
        if not path:
            return True
        decoded = urllib.parse.unquote(path).lstrip("/")
        if any(decoded.startswith(p.rstrip("/")) for p in SKIP_PATH_PREFIXES if p != "/"):
            return True
        if not decoded:  # 裸 "/" 即首页
            return True
        p = self.site_dir / decoded
        try:
            if p.is_file() or (p.is_dir() and (p / "index.html").is_file()):
                return True
            return (self.site_dir / (decoded + ".html")).is_file()
        except OSError:  # 超长路径等文件系统异常，视为可疑
            return False

    def record(self, url: str, source: str) -> None:
        """url 已归一化为站内绝对路径（/xxx 或去掉 base 后的形式）。"""
        self.checked += 1
        if not self.resolve(url):
            self.broken[url].add(source)

    def normalize(self, u: str) -> str | None:
        """返回站内绝对路径；外部链接返回 None。"""
        u = u.strip()
        if u.startswith(self.base + "/"):
            return u[len(self.base):]
        if u.startswith("http://") or u.startswith("https://") or u.startswith("//"):
            return None
        if SCHEME_RE.match(u) or any(u.lower().startswith(p) for p in SKIP_PREFIXES):
            return None
        if u.startswith("/"):
            return u
        return None  # 相对链接由调用方按源目录处理

    def check_html(self, f: Path) -> None:
        text = f.read_text(encoding="utf-8", errors="replace")
        source = "/" + str(f.relative_to(self.site_dir))
        candidates: list[str] = []
        for tm in TAG_RE.finditer(text):
            attrs = tm.group(2)
            for am in ATTR_RE.finditer(attrs):
                u = first_group(am)
                if u:
                    candidates.append(u)
            sm = SRCSET_RE.search(attrs)
            if sm:
                v = first_group(sm) or ""
                candidates.extend(c.strip().split(" ")[0] for c in v.split(",") if c.strip())
        for u in candidates:
            u = u.strip()
            abs_path = self.normalize(u)
            if abs_path is not None:
                self.record(abs_path, source)
            elif not any(u.lower().startswith(p) for p in SKIP_PREFIXES) and not SCHEME_RE.match(u):
                # 相对链接：按浏览器语义解析到源页面目录
                if any(c.isspace() for c in u):
                    continue
                path = u.split("#", 1)[0].split("?", 1)[0]
                if not path:
                    continue
                self.checked += 1
                try:
                    tp = f.parent / urllib.parse.unquote(path)
                    ok = (
                        tp.is_file()
                        or (tp.is_dir() and (tp / "index.html").is_file())
                        or (self.site_dir.parent / tp.with_suffix(".html")).is_file()
                        or Path(str(tp) + ".html").is_file()
                    )
                except OSError:
                    ok = True  # 无法判定时不阻塞
                if not ok:
                    self.broken[u].add(source)

    def check_sitemap(self) -> None:
        sm = self.site_dir / "sitemap.xml"
        if not sm.is_file():
            return
        for u in re.findall(r"<loc>([^<]+)</loc>", sm.read_text(encoding="utf-8", errors="replace")):
            if u.startswith(self.base + "/"):
                self.record(u[len(self.base):], "/sitemap.xml")

    def check_feeds(self) -> None:
        feeds = [p for p in self.site_dir.rglob("*.xml") if p.name != "sitemap.xml"]
        feeds += self.site_dir.rglob("*.json")
        for f in feeds:
            try:
                text = f.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            source = "/" + str(f.relative_to(self.site_dir))
            urls = re.findall(r"<link>(?:<!\[CDATA\[)?([^<\]]+)(?:\]\]>)?</link>", text)
            urls += re.findall(r"<guid[^>]*>(?:<!\[CDATA\[)?([^<\]]+)(?:\]\]>)?</guid>", text)
            urls += re.findall(r'href="(https?://[^"\s]+)"', text)
            urls += re.findall(r'"url"\s*:\s*"(https?://[^"\s]+)"', text)
            for u in urls:
                if u.startswith(self.base + "/"):
                    self.record(u[len(self.base):], source)

    def run(self) -> int:
        html_files = sorted(self.site_dir.rglob("*.html"))
        for f in html_files:
            self.check_html(f)
        self.check_sitemap()
        self.check_feeds()
        return len(html_files)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--site-dir", default="public")
    parser.add_argument("--base", default="https://txtmix.com")
    args = parser.parse_args()

    site_dir = Path(args.site_dir)
    if not site_dir.is_dir():
        print(f"错误: 站点目录不存在: {site_dir}", file=sys.stderr)
        return 2

    checker = LinkChecker(site_dir, args.base)
    n_html = checker.run()

    print(f"扫描 {n_html} 个 HTML + sitemap + feeds，共校验 {checker.checked} 条站内链接")
    if not checker.broken:
        print("✅ 站内链接全部有效")
        return 0

    occurrences = sum(len(v) for v in checker.broken.values())
    print(f"\n❌ 发现 {len(checker.broken)} 个断链目标（{occurrences} 处引用）:\n")
    for target in sorted(checker.broken):
        sources = sorted(checker.broken[target])
        print(f"404: {target}")
        for s in sources[:3]:
            print(f"     from {s}")
        if len(sources) > 3:
            print(f"     ... 另有 {len(sources) - 3} 个页面引用")
    return 1


if __name__ == "__main__":
    sys.exit(main())
