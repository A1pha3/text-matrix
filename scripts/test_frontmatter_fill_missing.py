#!/usr/bin/env python3

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


SCRIPT_PATH = Path(__file__).with_name("frontmatter_fill_missing.py")


def load_module():
    spec = importlib.util.spec_from_file_location("frontmatter_fill_missing", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class FrontmatterFillMissingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = load_module()

    def test_parse_args_accepts_multiple_targets_after_single_flag(self):
        argv = [
            "frontmatter_fill_missing.py",
            "--root",
            "content",
            "--target",
            "content/posts/a.md",
            "content/posts/b.md",
        ]

        with mock.patch.object(sys, "argv", argv):
            args = self.module.parse_args()

        self.assertEqual(args.root, "content")
        self.assertEqual(
            args.target,
            ["content/posts/a.md", "content/posts/b.md"],
        )

    def test_render_fm_uses_toml_assignment_for_toml_frontmatter(self):
        fm = "title = 'Example'\ndate = '2026-08-01T00:00:00+08:00'\n"

        rendered = self.module.render_fm(
            "+++",
            fm,
            {"slug": "example-slug", "categories": ["技术笔记"]},
        )

        self.assertIn("slug = 'example-slug'", rendered)
        self.assertIn("categories = ['技术笔记']", rendered)
        self.assertNotIn("slug:", rendered)
        self.assertNotIn("categories:", rendered)

    @staticmethod
    def _write_article(root: Path, rel: str) -> Path:
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            "---\ntitle: 某文章\ndate: 2026-08-17\ndescription: x\n"
            "tags: [a]\ncategories: [技术笔记]\ndraft: true\n---\n正文\n",
            encoding="utf-8",
        )
        return path

    def test_bundle_index_md_derives_slug_from_parent_dir(self):
        # Page Bundle 的文件名恒为 index.md——slug 必须取父目录名;
        # 取文件名会注入 slug: index(lint 判 fatal 的构建毒药,2026-08-17 审查实证)
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            path = self._write_article(root, "posts/tech/my-awesome-tool/index.md")
            (path.parent / "cover.png").write_bytes(b"fake")

            result = self.module.fill_one(path, root)

        self.assertEqual(result.added.get("slug"), "my-awesome-tool")

    def test_single_file_still_derives_slug_from_filename(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            path = self._write_article(root, "posts/tech/other-tool.md")

            result = self.module.fill_one(path, root)

        self.assertEqual(result.added.get("slug"), "other-tool")

    def test_bundle_with_non_kebab_parent_dir_skips_slug(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            path = self._write_article(root, "posts/tech/中文目录/index.md")

            result = self.module.fill_one(path, root)

        self.assertNotIn("slug", result.added)


if __name__ == "__main__":
    unittest.main()