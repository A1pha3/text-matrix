#!/usr/bin/env python3
"""validate_article_end.py 的负向/回归测试：证明断言真的能拦截违规。"""

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT_PATH = Path(__file__).with_name("validate_article_end.py")


def load_module():
    spec = importlib.util.spec_from_file_location("validate_article_end", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


MODULE = load_module()

# 与生成页面同构的最小合法文章结束区
VALID_PAGE = """<!DOCTYPE html><html><body>
<footer class="post-footer" data-article-end>
  <div class="post-end-meta">
    <a class="post-end-context" href="/topic/">主题</a>
    <a class="post-discussion-link" href="#discussion-title">参与讨论</a>
    <button class="post-share" type="button" hidden>分享</button>
  </div>
  <section class="post-continuation">
    <a class="post-context-link" href="/topic/">查看全部文章</a>
    <ul>
      <li><a data-target-kind="related" href="/posts/other/">推荐标题<span aria-hidden="true">→</span></a></li>
    </ul>
  </section>
  <nav class="post-series"><a href="/posts/prev-article/">系列上一篇</a></nav>
</footer>
<section id="comments" class="post-discussion">
  <h2 id="discussion-title">参与讨论</h2>
  <div data-giscus-root></div>
</section>
<a id="back-to-top" aria-label="回到顶部" href="#"></a>
<a id="view-comments" aria-label="查看评论" href="#discussion-title"></a>
</body></html>"""


class ValidateArticleEndTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.public = Path(self._tmp.name)
        for rel in ("posts/current", "posts/other", "posts/prev-article", "topic"):
            target = self.public / rel
            target.mkdir(parents=True, exist_ok=True)
            (target / "index.html").write_text("<html></html>", encoding="utf-8")
        self.page = self.public / "posts" / "current" / "index.html"

    def tearDown(self):
        self._tmp.cleanup()

    def run_html(self, html: str) -> list[str]:
        self.page.write_text(html, encoding="utf-8")
        errors, checked = MODULE.validate_html(self.page, self.public)
        self.assertTrue(checked)
        return errors

    # ---------- 生成 HTML 断言 ----------

    def test_valid_page_passes(self):
        self.assertEqual(self.run_html(VALID_PAGE), [])

    def test_icon_only_link_without_accessible_name_is_blocked(self):
        html = VALID_PAGE.replace(
            'data-target-kind="related" href="/posts/other/">推荐标题',
            'data-target-kind="related" href="/posts/other/"><i class="fas fa-arrow-right"></i>',
        )
        errors = self.run_html(html)
        self.assertTrue(any("可访问名称" in e for e in errors), errors)

    def test_aria_hidden_text_is_not_an_accessible_name(self):
        html = VALID_PAGE.replace(">推荐标题<", "><span aria-hidden='true'>装饰文字</span><")
        errors = self.run_html(html)
        self.assertTrue(any("可访问名称" in e for e in errors), errors)

    def test_missing_internal_target_is_blocked(self):
        html = VALID_PAGE.replace("/posts/other/", "/posts/ghost/")
        errors = self.run_html(html)
        self.assertTrue(any("链接目标不存在" in e for e in errors), errors)

    def test_percent_encoded_chinese_target_is_resolved(self):
        encoded = "/categories/%E6%8A%80%E6%9C%AF%E7%AC%94%E8%AE%B0/"
        (self.public / "categories" / "技术笔记").mkdir(parents=True)
        (self.public / "categories" / "技术笔记" / "index.html").write_text("<html></html>")
        html = VALID_PAGE.replace("/posts/other/", encoded)
        errors = self.run_html(html)
        self.assertFalse(any("链接目标不存在" in e for e in errors), errors)

    def test_fourth_related_item_is_blocked(self):
        item = '<li><a data-target-kind="related" href="/posts/other/">推荐标题<span aria-hidden="true">→</span></a></li>'
        html = VALID_PAGE.replace(item, item * 4)
        self.assertIn(item * 4, html)
        errors = self.run_html(html)
        self.assertTrue(any("0～3" in e for e in errors), errors)

    def test_self_reference_in_related_is_blocked(self):
        html = VALID_PAGE.replace("/posts/other/", "/posts/current/")
        errors = self.run_html(html)
        self.assertTrue(any("包含当前文章" in e for e in errors), errors)

    def test_removed_structure_class_is_blocked(self):
        html = VALID_PAGE.replace(
            '<section class="post-continuation">',
            '<div class="legacy post-tags x">标签</div><section class="post-continuation">',
        )
        errors = self.run_html(html)
        self.assertTrue(any("post-tags" in e for e in errors), errors)

    def test_discussion_enabled_requires_unique_title(self):
        html = VALID_PAGE.replace('<h2 id="discussion-title">', "<h2>")
        errors = self.run_html(html)
        self.assertTrue(any("discussion-title" in e for e in errors), errors)

    # ---------- 内容契约断言 ----------

    def write_content(self, relative: str, frontmatter: str) -> Path:
        path = self.public / "content" / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"---\n{frontmatter}\n---\n\n正文\n", encoding="utf-8")
        return path

    def run_content(self, files: dict[str, str], topics: str = "ai-agent:\n  title: T\n  url: /t/\n") -> list[str]:
        content_root = self.public / "content"
        for relative, frontmatter in files.items():
            self.write_content(relative, frontmatter)
        topics_path = self.public / "topics.yaml"
        topics_path.write_text(topics, encoding="utf-8")
        return MODULE.validate_content(content_root, topics_path, self.public)

    def test_missing_categories_is_blocked(self):
        errors = self.run_content({"posts/a.md": "title: A"})
        self.assertTrue(any("categories" in e for e in errors), errors)

    def test_unknown_topic_is_blocked_including_unquoted_inline(self):
        errors = self.run_content({
            "posts/a.md": 'categories: ["技术笔记"]\ntopics: ["ghost-topic"]',
            "posts/b.md": "categories: ['技术笔记']\ntopics: [ghost-inline]",
        })
        self.assertTrue(any("a.md" in e and "ghost-topic" in e for e in errors), errors)
        self.assertTrue(any("b.md" in e and "ghost-inline" in e for e in errors), errors)

    def test_related_posts_violations_are_blocked(self):
        errors = self.run_content({
            "posts/a.md": 'categories: ["技术笔记"]\nrelatedPosts:\n  - /posts/ghost/\n',
            "posts/b.md": 'categories: ["技术笔记"]\nrelatedPosts:\n  - /posts/b/\n',
            "posts/c.md": 'categories: ["技术笔记"]\nrelatedPosts:\n  - /posts/d/\n  - /posts/d/\n',
            "posts/d.md": "categories: ['技术笔记']\nrecommend: false",
        })
        self.assertTrue(any("a.md" in e and "不存在" in e for e in errors), errors)
        self.assertTrue(any("b.md" in e and "自身" in e for e in errors), errors)
        self.assertTrue(any("c.md" in e and "重复" in e for e in errors), errors)
        self.assertTrue(any("c.md" in e and "recommend: false" in e for e in errors), errors)

    def test_alias_reference_resolves_via_built_site(self):
        # aliases 路径在内容树解析不到，但构建产物里有重定向页，不应误报。
        alias_dir = self.public / "posts" / "old-name"
        alias_dir.mkdir(parents=True, exist_ok=True)
        (alias_dir / "index.html").write_text("<html></html>", encoding="utf-8")
        errors = self.run_content({
            "posts/a.md": 'categories: ["技术笔记"]\nnext: /posts/old-name/',
            "posts/b.md": 'categories: ["技术笔记"]\nrelatedPosts:\n  - /posts/old-name/',
        })
        self.assertFalse(any("不存在" in e for e in errors), errors)

    def test_quoted_and_commented_scalar_values_are_parsed(self):
        errors = self.run_content({
            "posts/a.md": 'categories: ["技术笔记"]\nprev: "/posts/ghost/"',
            "posts/b.md": 'categories: ["技术笔记"]\nnext: /posts/ghost/ # 行内注释',
        })
        self.assertTrue(any("a.md" in e and "不存在" in e and '"' not in e.split()[-1] for e in errors), errors)
        self.assertTrue(any("b.md" in e and "不存在" in e and "注释" not in e for e in errors), errors)

    def test_series_violations_are_blocked(self):
        errors = self.run_content({
            "posts/a.md": 'categories: ["技术笔记"]\nprev: /posts/ghost/',
            "posts/b.md": 'categories: ["技术笔记"]\nnext: /posts/b/',
            "posts/c.md": 'categories: ["技术笔记"]\nprev: /posts/a/\nnext: /posts/a/',
        })
        self.assertTrue(any("a.md" in e and "prev" in e and "不存在" in e for e in errors), errors)
        self.assertTrue(any("b.md" in e and "next" in e and "自身" in e for e in errors), errors)
        self.assertTrue(any("c.md" in e and "同一页面" in e for e in errors), errors)

    def test_valid_content_passes(self):
        errors = self.run_content({
            "posts/a.md": 'categories: ["技术笔记"]\ntopics: ["ai-agent"]\nrelatedPosts:\n  - /posts/b/\nnext: /posts/b/',
            "posts/b.md": 'categories: ["技术笔记"]\nprev: /posts/a/',
        })
        self.assertEqual(errors, [])


if __name__ == "__main__":
    unittest.main()
