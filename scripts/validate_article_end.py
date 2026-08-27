from __future__ import annotations

import argparse
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from typing import Optional
from urllib.parse import urlsplit


VOID_ELEMENTS = {
    "area", "base", "br", "col", "embed", "hr", "img", "input", "link",
    "meta", "param", "source", "track", "wbr",
}


class ArticleEndParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.stack: list[tuple[str, bool, bool]] = []
        self.footer_depth = 0
        self.discussion_depth = 0
        self.footer_count = 0
        self.continuation_count = 0
        self.discussion_count = 0
        self.giscus_root_count = 0
        self.related_links: list[str] = []
        self.context_link_count = 0
        self.discussion_link_count = 0
        self.id_counts: dict[str, int] = {}
        self.errors: list[str] = []
        self.fixed_controls: dict[str, bool] = {}

    @staticmethod
    def attrs_map(attrs: list[tuple[str, Optional[str]]]) -> dict[str, str]:
        return {key: value or "" for key, value in attrs}

    def handle_starttag(self, tag: str, attrs: list[tuple[str, Optional[str]]]) -> None:
        data = self.attrs_map(attrs)
        classes = set(data.get("class", "").split())
        opens_footer = "data-article-end" in data
        opens_discussion = "post-discussion" in classes

        if opens_footer:
            self.footer_count += 1
            self.footer_depth += 1
        if opens_discussion:
            self.discussion_count += 1
            self.discussion_depth += 1

        element_id = data.get("id")
        if element_id:
            self.id_counts[element_id] = self.id_counts.get(element_id, 0) + 1

        if "post-continuation" in classes:
            self.continuation_count += 1
        if "data-giscus-root" in data:
            self.giscus_root_count += 1

        in_article_end = self.footer_depth > 0 or self.discussion_depth > 0
        if tag == "a" and in_article_end:
            href = data.get("href", "").strip()
            if not href:
                self.errors.append("文章结束区存在空 href")
            if href.lower().startswith("javascript:"):
                self.errors.append(f"文章结束区存在 JavaScript URL: {href}")
            if data.get("target") == "_blank":
                rel = set(data.get("rel", "").split())
                if not {"noopener", "noreferrer"}.issubset(rel):
                    self.errors.append(f"新窗口链接缺少 noopener noreferrer: {href}")
            if "post-context-link" in classes:
                self.context_link_count += 1
            if "post-discussion-link" in classes:
                self.discussion_link_count += 1
            if data.get("data-target-kind") == "related":
                self.related_links.append(href)

        if element_id in {"back-to-top", "view-comments"}:
            self.fixed_controls[element_id] = bool(data.get("aria-label", "").strip())

        if tag not in VOID_ELEMENTS:
            self.stack.append((tag, opens_footer, opens_discussion))

    def handle_endtag(self, tag: str) -> None:
        while self.stack:
            opened_tag, opened_footer, opened_discussion = self.stack.pop()
            if opened_footer:
                self.footer_depth -= 1
            if opened_discussion:
                self.discussion_depth -= 1
            if opened_tag == tag:
                break


def current_page_path(html_path: Path, public_root: Path) -> str:
    relative = html_path.relative_to(public_root)
    if relative.name == "index.html":
        return f"/{relative.parent.as_posix().strip('/')}/"
    return f"/{relative.as_posix().strip('/')}"


def validate_html(path: Path, public_root: Path) -> list[str]:
    raw = path.read_text(encoding="utf-8")
    if "data-article-end" not in raw:
        return []

    parser = ArticleEndParser()
    parser.feed(raw)
    errors = list(parser.errors)

    if parser.footer_count != 1:
        errors.append(f"文章结束区数量应为 1，实际为 {parser.footer_count}")
    if parser.continuation_count != 1:
        errors.append(f"继续理解模块数量应为 1，实际为 {parser.continuation_count}")
    if not 0 <= len(parser.related_links) <= 3:
        errors.append(f"相关推荐数量应为 0～3，实际为 {len(parser.related_links)}")
    if len(parser.related_links) != len(set(parser.related_links)):
        errors.append("相关推荐包含重复 URL")
    if parser.context_link_count != 1:
        errors.append(f"上下文主入口数量应为 1，实际为 {parser.context_link_count}")

    page_path = current_page_path(path, public_root)
    for href in parser.related_links:
        href_path = urlsplit(href).path
        if href_path.rstrip("/").endswith(page_path.rstrip("/")):
            errors.append(f"相关推荐包含当前文章: {href}")

    if parser.discussion_count:
        if parser.discussion_count != 1:
            errors.append(f"评论区数量应为 1，实际为 {parser.discussion_count}")
        if parser.discussion_link_count != 1:
            errors.append(f"正文后讨论入口数量应为 1，实际为 {parser.discussion_link_count}")
        if parser.id_counts.get("discussion-title", 0) != 1:
            errors.append("评论开启时必须存在唯一的 #discussion-title")
        if parser.giscus_root_count != 1:
            errors.append(f"Giscus 根容器数量应为 1，实际为 {parser.giscus_root_count}")
    elif parser.discussion_link_count:
        errors.append("评论关闭时仍存在正文后讨论入口")

    for control_id in ("back-to-top", "view-comments"):
        if not parser.fixed_controls.get(control_id, False):
            errors.append(f"#{control_id} 缺少 aria-label")

    for removed_class in ("post-conversion", "post-related-grid", "post-related-card", "post-tags"):
        if f'class="{removed_class}' in raw or f" {removed_class}" in raw:
            errors.append(f"仍存在已删除结构 .{removed_class}")

    return errors


def validate_content(content_root: Path, topics_path: Path) -> list[str]:
    topic_text = topics_path.read_text(encoding="utf-8")
    allowed_topics = set(re.findall(r"^([a-z0-9][a-z0-9-]*):\s*$", topic_text, re.MULTILINE))
    errors: list[str] = []

    for path in sorted((content_root / "posts").rglob("*.md")):
        if path.name == "_index.md":
            continue
        raw = path.read_text(encoding="utf-8")
        lines = raw.lstrip("\ufeff\n").splitlines()
        if not lines or lines[0].strip() not in {"---", "+++"}:
            errors.append(f"{path}: 缺少可解析 Frontmatter")
            continue
        try:
            end = next(index for index, line in enumerate(lines[1:], 1) if line.strip() == lines[0].strip())
        except StopIteration:
            errors.append(f"{path}: Frontmatter 未闭合")
            continue
        frontmatter = "\n".join(lines[1:end])

        if not re.search(r"^categories\s*(?::|=)", frontmatter, re.MULTILINE):
            errors.append(f"{path}: 文章至少需要一个 categories 值")

        topic_match = re.search(r"^topics\s*(?::|=)\s*\[([^\]]*)\]", frontmatter, re.MULTILINE)
        topic_values = re.findall(r"['\"]([^'\"]+)['\"]", topic_match.group(1)) if topic_match else []
        yaml_topic_block = re.search(r"^topics:\s*\n((?:\s+-\s*[^\n]+\n?)+)", frontmatter, re.MULTILINE)
        if yaml_topic_block:
            topic_values.extend(
                value.strip().strip("'\"")
                for value in re.findall(r"^\s+-\s*([^\n]+)", yaml_topic_block.group(1), re.MULTILINE)
            )
        unknown = sorted(set(topic_values) - allowed_topics)
        if unknown:
            errors.append(f"{path}: topics 包含未登记值 {unknown}")

    return errors


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="校验文章结束区的内容契约与生成 HTML")
    parser.add_argument("site_dir", nargs="?", default="public")
    parser.add_argument("--content-root", default="content")
    parser.add_argument("--topics", default="data/topics.yaml")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    public_root = Path(args.site_dir).resolve()
    content_root = Path(args.content_root).resolve()
    topics_path = Path(args.topics).resolve()

    failures = validate_content(content_root, topics_path)
    checked_html = 0
    for path in sorted((public_root / "posts").rglob("index.html")):
        html_failures = validate_html(path, public_root)
        if "data-article-end" in path.read_text(encoding="utf-8"):
            checked_html += 1
        failures.extend(f"{path}: {message}" for message in html_failures)

    if failures:
        print("文章结束区校验失败:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print(f"文章结束区校验通过：内容契约有效，检查 {checked_html} 个文章页面")
    return 0


if __name__ == "__main__":
    sys.exit(main())
