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
    <button class="post-share" type="button" data-share hidden>分享</button>
    <a class="post-social" href="https://service.weibo.com/share/share.php?url=x&amp;title=t" target="_blank" rel="noopener noreferrer" data-event="article_share" data-target-kind="weibo">微博</a>
    <a class="post-social" href="https://x.com/intent/tweet?url=x&amp;text=t" target="_blank" rel="noopener noreferrer" data-event="article_share" data-target-kind="x">X</a>
  </div>
  <nav class="post-continuation" aria-label="后续阅读">
    <a class="post-recommendation-link" data-target-kind="related" href="/posts/other/">
      <span class="post-recommendation-reason">同主题</span>
      <span class="post-recommendation-title">推荐标题</span>
      <span aria-hidden="true">→</span>
    </a>
    <a class="post-context-link" href="/topic/">查看全部文章</a>
  </nav>
</footer>
<section id="comments" class="post-discussion">
  <h2 id="discussion-title">参与讨论</h2>
  <div data-giscus-root data-light-theme="light" data-dark-theme="dark"></div>
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
            '<span class="post-recommendation-reason">同主题</span>\n      <span class="post-recommendation-title">推荐标题</span>',
            '<span class="post-recommendation-title"><i class="fas fa-arrow-right"></i></span>',
        )
        errors = self.run_html(html)
        self.assertTrue(any("可访问名称" in e for e in errors), errors)

    def test_aria_hidden_text_is_not_an_accessible_name(self):
        html = VALID_PAGE.replace(
            '<span class="post-recommendation-reason">同主题</span>\n      <span class="post-recommendation-title">推荐标题</span>',
            '<span aria-hidden="true">装饰文字</span>',
        )
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

    def test_second_recommendation_is_blocked(self):
        item = """    <a class="post-recommendation-link" data-target-kind="related" href="/posts/other/">
      <span class="post-recommendation-reason">同主题</span>
      <span class="post-recommendation-title">推荐标题</span>
      <span aria-hidden="true">→</span>
    </a>"""
        html = VALID_PAGE.replace(item, item * 2)
        self.assertIn(item * 2, html)
        errors = self.run_html(html)
        self.assertTrue(any("0～1" in e for e in errors), errors)

    def test_self_reference_in_related_is_blocked(self):
        html = VALID_PAGE.replace("/posts/other/", "/posts/current/")
        errors = self.run_html(html)
        self.assertTrue(any("包含当前文章" in e for e in errors), errors)

    def test_removed_structure_class_is_blocked(self):
        html = VALID_PAGE.replace(
            '<nav class="post-continuation" aria-label="后续阅读">',
            '<div class="legacy post-tags x">标签</div><nav class="post-continuation" aria-label="后续阅读">',
        )
        errors = self.run_html(html)
        self.assertTrue(any("post-tags" in e for e in errors), errors)

    def test_recommendation_requires_valid_kind_and_reason(self):
        html = VALID_PAGE.replace('data-target-kind="related"', 'data-target-kind="category"')
        html = html.replace('<span class="post-recommendation-reason">同主题</span>', "")
        errors = self.run_html(html)
        self.assertTrue(any("来源标签无效" in e for e in errors), errors)
        self.assertTrue(any("准确来源标签" in e for e in errors), errors)

    def test_visible_continuation_title_is_blocked(self):
        html = VALID_PAGE.replace(
            '<nav class="post-continuation" aria-label="后续阅读">',
            '<nav class="post-continuation" aria-label="后续阅读"><h2 id="post-continuation-title">继续理解</h2>',
        )
        errors = self.run_html(html)
        self.assertTrue(any("继续理解" in e for e in errors), errors)

    def test_both_static_share_targets_are_required(self):
        html = VALID_PAGE.replace(
            '<a class="post-social" href="https://x.com/intent/tweet?url=x&amp;text=t" target="_blank" rel="noopener noreferrer" data-event="article_share" data-target-kind="x">X</a>',
            "",
        )
        errors = self.run_html(html)
        self.assertTrue(any("微博和 X" in e for e in errors), errors)

    def test_static_share_target_structure_is_validated(self):
        html = VALID_PAGE.replace(
            "https://x.com/intent/tweet?url=x&amp;text=t",
            "https://x.com/share?url=x&amp;text=t",
        )
        errors = self.run_html(html)
        self.assertTrue(any("x 分享链接结构无效" in e for e in errors), errors)

    def test_discussion_enabled_requires_unique_title(self):
        html = VALID_PAGE.replace('<h2 id="discussion-title">', "<h2>")
        errors = self.run_html(html)
        self.assertTrue(any("discussion-title" in e for e in errors), errors)

    def test_giscus_requires_supported_light_and_dark_themes(self):
        html = VALID_PAGE.replace('data-light-theme="light"', 'data-light-theme="github-light"')
        errors = self.run_html(html)
        self.assertTrue(any("内置 light/dark" in e for e in errors), errors)

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
