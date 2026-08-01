#!/usr/bin/env python3

import importlib.util
import sys
import unittest
from pathlib import Path
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = Path(__file__).with_name("frontmatter_lint.py")
ARTICLE_PATH = REPO_ROOT / "content" / "posts" / "video" / "agent-technology-history-su-yu.md"


def load_module():
    spec = importlib.util.spec_from_file_location("frontmatter_lint", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class FrontmatterLintTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = load_module()

    def test_parse_args_accepts_multiple_targets_after_single_flag(self):
        argv = [
            "frontmatter_lint.py",
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

    def test_agent_technology_article_frontmatter_is_valid(self):
        report = self.module.lint_file(ARTICLE_PATH)

        self.assertEqual(report.fatal, [])


if __name__ == "__main__":
    unittest.main()