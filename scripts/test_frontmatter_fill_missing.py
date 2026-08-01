#!/usr/bin/env python3

import importlib.util
import sys
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


if __name__ == "__main__":
    unittest.main()