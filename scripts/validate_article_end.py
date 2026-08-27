from __future__ import annotations

import argparse
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from typing import Optional
from urllib.parse import unquote, urlsplit


VOID_ELEMENTS = {
    "area", "base", "br", "col", "embed", "hr", "img", "input", "link",
    "meta", "param", "source", "track", "wbr",
}

# 设计 §1.3 已删除的结构；出现任一 class 即回归。
REMOVED_CLASSES = {
    "post-conversion", "post-related-grid", "post-related-card", "post-tags",
}


class ArticleEndParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        # 栈元素：(标签, 是否开启文章结束区, 是否开启评论区, 是否增加 aria-hidden 深度)
        self.stack: list[tuple[str, bool, bool, bool]] = []
        self.footer_depth = 0
        self.discussion_depth = 0
        self.hidden_depth = 0
        self.footer_count = 0
        self.continuation_count = 0
        self.discussion_count = 0
        self.giscus_root_count = 0
        self.related_links: list[str] = []
        self.internal_links: list[str] = []
        self.context_link_count = 0
        self.discussion_link_count = 0
        self.id_counts: dict[str, int] = {}
        self.errors: list[str] = []
        self.fixed_controls: dict[str, bool] = {}
        self.removed_class_hits: set[str] = set()
        # 当前正在收集可访问名称的链接（文章结束区内不嵌套链接）
        self.current_anchor: Optional[dict] = None

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

        self.removed_class_hits.update(classes & REMOVED_CLASSES)

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
            if href.startswith("/"):
                self.internal_links.append(href)
            if self.current_anchor is None:
                self.current_anchor = {
                    "href": href,
                    "named": bool(data.get("aria-label") or data.get("aria-labelledby")),
                    "text": [],
                }

        if element_id in {"back-to-top", "view-comments"}:
            self.fixed_controls[element_id] = bool(data.get("aria-label", "").strip())

        adds_hidden = (
            tag not in VOID_ELEMENTS
            and data.get("aria-hidden") == "true"
        )
        if adds_hidden:
            self.hidden_depth += 1
        if tag not in VOID_ELEMENTS:
            self.stack.append((tag, opens_footer, opens_discussion, adds_hidden))

    def handle_data(self, data: str) -> None:
        # aria-hidden 子树内的文本（如装饰箭头 →）不构成可访问名称
        if self.current_anchor is not None and self.hidden_depth == 0:
            text = data.strip()
            if text:
                self.current_anchor["text"].append(text)

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self.current_anchor is not None:
            anchor = self.current_anchor
            self.current_anchor = None
            if not anchor["named"] and not "".join(anchor["text"]).strip():
                self.errors.append(
                    f"文章结束区存在只有图标而没有可访问名称的链接: {anchor['href'] or '(空)'}"
                )
        while self.stack:
            opened_tag, opened_footer, opened_discussion, adds_hidden = self.stack.pop()
            if opened_footer:
                self.footer_depth -= 1
            if opened_discussion:
                self.discussion_depth -= 1
            if adds_hidden:
                self.hidden_depth -= 1
            if opened_tag == tag:
                break


def internal_link_exists(href: str, public_root: Path) -> bool:
    # //cdn.example.com/… 是协议相对外部 URL，不是站内链接。
    if href.startswith("//"):
        return True
    # HTML 中的中文路径是百分号编码的，磁盘目录是原始 Unicode，需先解码。
    path_part = unquote(urlsplit(href).path).strip("/")
    if not path_part:
        return (public_root / "index.html").exists()
    return (
        (public_root / path_part / "index.html").exists()
        or (public_root / path_part).is_file()
    )


def current_page_path(html_path: Path, public_root: Path) -> str:
    relative = html_path.relative_to(public_root)
    if relative.name == "index.html":
        return f"/{relative.parent.as_posix().strip('/')}/"
    return f"/{relative.as_posix().strip('/')}"


def validate_html(path: Path, public_root: Path) -> tuple[list[str], bool]:
    raw = path.read_text(encoding="utf-8")
    if "data-article-end" not in raw:
        return [], False

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
        href_path = unquote(urlsplit(href).path)
        if href_path.rstrip("/") == page_path.rstrip("/"):
            errors.append(f"相关推荐包含当前文章: {href}")

    # 主题、分类、系列与推荐目标都必须真实存在（无效链接直接阻断）
    for href in sorted(set(parser.internal_links)):
        if not internal_link_exists(href, public_root):
            errors.append(f"文章结束区链接目标不存在: {href}")

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

    for removed_class in sorted(parser.removed_class_hits):
        errors.append(f"仍存在已删除结构 .{removed_class}")

    return errors, True


def split_frontmatter(raw: str) -> Optional[str]:
    lines = raw.lstrip("\ufeff\n").splitlines()
    if not lines or lines[0].strip() not in {"---", "+++"}:
        return None
    delimiter = lines[0].strip()
    for index, line in enumerate(lines[1:], 1):
        if line.strip() == delimiter:
            return "\n".join(lines[1:index])
    return None


def extract_list_values(frontmatter: str, field: str) -> list[str]:
    values: list[str] = []
    block = re.search(rf"^{field}:\s*\n((?:\s+-\s*[^\n]+\n?)+)", frontmatter, re.MULTILINE)
    if block:
        values.extend(
            value.strip().strip("'\"")
            for value in re.findall(r"^\s+-\s*([^\n]+)", block.group(1), re.MULTILINE)
        )
    inline = re.search(rf"^{field}\s*(?::|=)\s*\[([^\]]*)\]", frontmatter, re.MULTILINE)
    if inline:
        values.extend(
            item.strip().strip("'\"")
            for item in inline.group(1).split(",")
            if item.strip()
        )
    return [value for value in values if value]


def extract_scalar_value(frontmatter: str, field: str) -> Optional[str]:
    # 值可带单/双引号，也可带 YAML 行内注释；只禁止换行。
    match = re.search(rf"^{field}\s*(?::|=)\s*([^\n]+)$", frontmatter, re.MULTILINE)
    if not match:
        return None
    value = re.sub(r"\s+#.*$", "", match.group(1)).strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "'\"":
        value = value[1:-1]
    return value or None


def page_rel_path(path: Path, content_root: Path) -> str:
    """content/posts/tech/foo/index.md -> /posts/tech/foo/"""
    relative = path.relative_to(content_root)
    parts = list(relative.parts)
    if parts[-1] in {"index.md", "_index.md"}:
        parts = parts[:-1]
    else:
        parts[-1] = relative.stem
    return "/" + "/".join(parts) + "/"


def resolve_content_file(content_root: Path, ref: str) -> Optional[Path]:
    rel = ref.strip().strip("/")
    if not rel or "://" in rel or rel.startswith("//"):
        return None
    for candidate in (
        content_root / rel / "index.md",
        content_root / f"{rel}.md",
        content_root / rel / "_index.md",
    ):
        if candidate.exists():
            return candidate
    return None


def has_recommend_false(target: Path) -> bool:
    frontmatter = split_frontmatter(target.read_text(encoding="utf-8")) or ""
    return bool(re.search(r"^recommend\s*:\s*false\s*$", frontmatter, re.MULTILINE))


def validate_content(content_root: Path, topics_path: Path, public_root: Optional[Path] = None) -> list[str]:
    topic_text = topics_path.read_text(encoding="utf-8")
    allowed_topics = set(re.findall(r"^([a-z0-9][a-z0-9-]*):\s*$", topic_text, re.MULTILINE))
    errors: list[str] = []

    for path in sorted((content_root / "posts").rglob("*.md")):
        if path.name == "_index.md":
            continue
        raw = path.read_text(encoding="utf-8")
        frontmatter = split_frontmatter(raw)
        if frontmatter is None:
            errors.append(f"{path}: 缺少可解析或未闭合的 Frontmatter")
            continue

        if not re.search(r"^categories\s*(?::|=)", frontmatter, re.MULTILINE):
            errors.append(f"{path}: 文章至少需要一个 categories 值")

        unknown = sorted(set(extract_list_values(frontmatter, "topics")) - allowed_topics)
        if unknown:
            errors.append(f"{path}: topics 包含未登记值 {unknown}")

        self_path = page_rel_path(path, content_root)

        related_refs = extract_list_values(frontmatter, "relatedPosts")
        for ref in related_refs:
            target = resolve_content_file(content_root, ref)
            if target is None:
                # 内容树解析不到时可能是 aliases 路径：Hugo 构建产物里有对应重定向页，
                # 交给生成 HTML 层判定存在性，避免与 GetPage 语义不一致的误报。
                if not (public_root and internal_link_exists(ref, public_root)):
                    errors.append(f"{path}: relatedPosts 指向不存在页面 {ref}")
            else:
                if page_rel_path(target, content_root) == self_path:
                    errors.append(f"{path}: relatedPosts 指向自身 {ref}")
                if has_recommend_false(target):
                    errors.append(f"{path}: relatedPosts 指向 recommend: false 页面 {ref}")
        if len(related_refs) != len(set(related_refs)):
            errors.append(f"{path}: relatedPosts 包含重复路径")
        if self_path in related_refs:
            errors.append(f"{path}: relatedPosts 指向自身 {self_path}")

        prev = extract_scalar_value(frontmatter, "prev")
        next_ = extract_scalar_value(frontmatter, "next")
        for field, ref in (("prev", prev), ("next", next_)):
            if ref is None:
                continue
            target = resolve_content_file(content_root, ref)
            if target is None:
                if not (public_root and internal_link_exists(ref, public_root)):
                    errors.append(f"{path}: {field} 指向不存在页面 {ref}")
            elif page_rel_path(target, content_root) == self_path:
                errors.append(f"{path}: {field} 指向自身 {ref}")
            if ref == self_path:
                errors.append(f"{path}: {field} 指向自身 {ref}")
        if prev is not None and prev == next_:
            errors.append(f"{path}: prev 与 next 指向同一页面 {prev}")

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

    failures = validate_content(content_root, topics_path, public_root)
    checked_html = 0
    for path in sorted((public_root / "posts").rglob("index.html")):
        html_failures, checked = validate_html(path, public_root)
        if checked:
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
