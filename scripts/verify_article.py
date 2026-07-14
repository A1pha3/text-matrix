#!/usr/bin/env python3
"""verify_article.py — 文章校验流水线（一手资料核对 + 启发式评分 + 构建）

把一次"据一手资料核对 → 只读评分 → 构建验证"的流程沉淀成一条命令。
源于对 Louis Kirsch ICLR 2026 演讲稿的核对：先用 pypdf 逐页提取幻灯片 PDF 做事实核对，
再跑 scripts/optimize-article-to-100.py 的评分（**只读，不写回、不生成副本**），
并额外诊断评分脚本那条"每个空行分隔块 <10 行"的假阴性，最后跑 frontmatter lint 与 Hugo 构建。

用法示例::

    # 1) 提取一手 PDF 正文（URL 或本地路径），供人工/LLM 逐页核对
    python scripts/verify_article.py --pdf https://example.com/slides.pdf --out /tmp/slides.txt

    # 2) 只读评分 + 超长块诊断（绝不改动文章、不生成 -optimized 副本）
    python scripts/verify_article.py --score content/posts/video/xxx.md

    # 3) 一条龙：评分 + frontmatter lint + Hugo 构建
    python scripts/verify_article.py --score content/posts/video/xxx.md --lint --build

环境变量::

    HUGO_BIN   Hugo 可执行文件路径（默认优先本仓库同级 ../hugo/hugo，回退 PATH 里的 hugo）
"""
from __future__ import annotations

import argparse
import importlib.util
import os
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCORER_PATH = REPO_ROOT / "scripts" / "optimize-article-to-100.py"
FRONTMATTER_LINT = REPO_ROOT / "scripts" / "frontmatter_lint.py"
DEFAULT_HUGO = REPO_ROOT.parent / "hugo" / "hugo"


def _load_scorer():
    """从 optimize-article-to-100.py 借用 score_article，避免重复实现评分逻辑。"""
    spec = importlib.util.spec_from_file_location("_scorer", SCORER_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"无法加载评分脚本: {SCORER_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def extract_pdf(src: str, out: str | None) -> int:
    """把 PDF（URL 或本地路径）逐页提取成纯文本，供事实核对。"""
    try:
        from pypdf import PdfReader
    except ImportError:
        print("需要 pypdf：pip install pypdf（或 uv run --with pypdf ...）", file=sys.stderr)
        return 2

    local = src
    if src.startswith(("http://", "https://")):
        local = str(Path(out).with_suffix(".pdf")) if out else "/tmp/_verify_article.pdf"
        # 用 curl 断点续传，规避部分服务器对大 PDF 的连接截断
        for attempt in range(8):
            rc = subprocess.run(
                ["curl", "-fsSL", "-C", "-", "--retry", "5", "-A", "Mozilla/5.0", "-o", local, src]
            ).returncode
            if rc == 0:
                break
            print(f"下载重试 {attempt + 1} …（已有 {Path(local).stat().st_size if Path(local).exists() else 0} 字节）")
        if not Path(local).exists() or Path(local).stat().st_size == 0:
            print(f"下载失败: {src}", file=sys.stderr)
            return 1

    reader = PdfReader(local)
    chunks: list[str] = [f"PAGES {len(reader.pages)}"]
    for i, page in enumerate(reader.pages):
        text = (page.extract_text() or "").strip()
        if text:
            chunks.append(f"--- PAGE {i + 1} ---\n{text}")
    result = "\n".join(chunks)
    if out:
        Path(out).write_text(result, encoding="utf-8")
        print(f"已写出 {len(reader.pages)} 页文本 → {out}")
    else:
        print(result)
    return 0


def score_article(path: Path) -> int:
    """只读评分 + 超长块诊断。不写回文件、不生成副本。"""
    scorer = _load_scorer()
    content = path.read_text(encoding="utf-8")
    dims, total = scorer.score_article(content)
    print(f"== 评分: {path.name} ==")
    for name, value in dims.items():
        print(f"  {name}: {value}")
    print(f"  总分: {total}/100")

    # 诊断评分脚本"可读性"那条 all-or-nothing 规则：任一空行分隔块 >=10 行就扣 5 分
    big = []
    for block in content.split("\n\n"):
        if not block.strip():
            continue
        lines = block.split("\n")
        if len(lines) >= 10:
            big.append((len(lines), lines[0][:48]))
    if big:
        print("  ⚠️ 超长块(>=10 行，会扣可读性 5 分):")
        for n, head in big:
            print(f"     {n} 行 | {head}")
    else:
        print("  ✓ 无超长块")
    return 0 if total >= 100 else 1


def _score_one(scorer, path: Path) -> tuple[int, int]:
    """返回 (总分, 超长块数量)，供批量模式汇总。"""
    content = path.read_text(encoding="utf-8")
    _, total = scorer.score_article(content)
    big = sum(
        1 for b in content.split("\n\n") if b.strip() and len(b.split("\n")) >= 10
    )
    return total, big


def score_all(root: str) -> int:
    """批量扫描目录下所有 .md 文章评分，按分数升序汇总（问题优先）。"""
    scorer = _load_scorer()
    base = (REPO_ROOT / root) if not Path(root).is_absolute() else Path(root)
    files = sorted(p for p in base.rglob("*.md") if p.name != "_index.md")
    if not files:
        print(f"未找到文章: {base}")
        return 1
    rows = []
    for path in files:
        try:
            total, big = _score_one(scorer, path)
        except Exception as exc:  # 单篇失败不阻断整批
            print(f"  跳过 {path}: {exc}", file=sys.stderr)
            continue
        rows.append((total, big, path))
    rows.sort(key=lambda r: (r[0], -r[1]))  # 低分在前
    print(f"== 批量评分: {base} （共 {len(rows)} 篇，按分数升序）==")
    below = 0
    for total, big, path in rows:
        flag = "" if total >= 100 else "  ← 未满分"
        blk = f" [超长块x{big}]" if big else ""
        rel = path.relative_to(REPO_ROOT) if path.is_relative_to(REPO_ROOT) else path
        print(f"  {total:3d}/100{blk}  {rel}{flag}")
        if total < 100:
            below += 1
    print(f"-- 未满分 {below} 篇 / 共 {len(rows)} 篇 --")
    return 0 if below == 0 else 1


def run_lint(path: Path | None) -> int:
    """调用仓库的 frontmatter_lint.py。"""
    cmd = [sys.executable, str(FRONTMATTER_LINT)]
    cmd += ["--target", str(path)] if path else ["--root", "content"]
    print(f"== frontmatter lint: {' '.join(cmd[2:])} ==")
    return subprocess.run(cmd, cwd=REPO_ROOT).returncode


def run_build() -> int:
    """跑 Hugo 构建（默认用本仓库同级 ../hugo/hugo）。"""
    hugo = os.environ.get("HUGO_BIN") or (str(DEFAULT_HUGO) if DEFAULT_HUGO.exists() else shutil.which("hugo"))
    if not hugo:
        print("找不到 hugo 可执行文件，可用 HUGO_BIN 指定。", file=sys.stderr)
        return 2
    print(f"== Hugo 构建: {hugo} ==")
    return subprocess.run([hugo, "--gc", "--logLevel", "warn"], cwd=REPO_ROOT).returncode


def main() -> int:
    parser = argparse.ArgumentParser(description="文章校验流水线：一手资料核对 + 只读评分 + 构建")
    parser.add_argument("--pdf", help="一手 PDF 的 URL 或本地路径，逐页提取正文供事实核对")
    parser.add_argument("--out", help="配合 --pdf：把提取文本写到该文件（默认打印到 stdout）")
    parser.add_argument("--score", metavar="ARTICLE.md", help="对文章做只读评分 + 超长块诊断")
    parser.add_argument("--score-all", nargs="?", const="content/posts", metavar="DIR",
                        help="批量扫描目录下所有 .md 文章评分（默认 content/posts）")
    parser.add_argument("--lint", nargs="?", const="", metavar="ARTICLE.md",
                        help="跑 frontmatter lint（给路径则只校验该文件，否则校验 content 全量）")
    parser.add_argument("--build", action="store_true", help="跑 Hugo 构建验证")
    args = parser.parse_args()

    if not any([args.pdf, args.score, args.score_all, args.lint is not None, args.build]):
        parser.print_help()
        return 0

    worst = 0
    if args.pdf:
        worst = max(worst, extract_pdf(args.pdf, args.out))
    if args.score:
        worst = max(worst, score_article(Path(args.score)))
    if args.score_all:
        worst = max(worst, score_all(args.score_all))
    if args.lint is not None:
        worst = max(worst, run_lint(Path(args.lint) if args.lint else None))
    if args.build:
        worst = max(worst, run_build())
    return worst


if __name__ == "__main__":
    sys.exit(main())
