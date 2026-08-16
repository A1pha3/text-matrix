#!/usr/bin/env python3

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


SCRIPT_PATH = Path(__file__).with_name("frontmatter_autofill.py")


def load_module():
    spec = importlib.util.spec_from_file_location("frontmatter_autofill", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class FrontmatterAutofillTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = load_module()

    @staticmethod
    def _make_root(td: str) -> Path:
        root = Path(td)
        (root / "posts/tech").mkdir(parents=True)
        return root

    def test_no_frontmatter_file_gets_draft_true_by_default(self):
        # 发布安全模型:draft 布尔位是唯一闸门,自动补全必须默认不上线——
        # 无 frontmatter 的文件可能是未审半成品,draft=false 会绕过评分闸直达线上
        # (2026-08-17 对抗审查:与钩子 git add 联级可静默发版)
        with tempfile.TemporaryDirectory() as td:
            root = self._make_root(td)
            f = root / "posts/tech/some-article.md"
            f.write_text("# 标题\n正文\n", encoding="utf-8")

            result = self.module.run(root=root, dry_run=False, recursive=True)

            content = f.read_text(encoding="utf-8")
        self.assertEqual(result.changed, 1)
        self.assertIn("draft = true", content)
        self.assertNotIn("draft = false", content)

    def test_live_flag_opts_into_draft_false_for_legacy_backfill(self):
        with tempfile.TemporaryDirectory() as td:
            root = self._make_root(td)
            f = root / "posts/tech/legacy-article.md"
            f.write_text("# 老文章\n正文\n", encoding="utf-8")

            self.module.run(root=root, dry_run=False, recursive=True, live=True)

            content = f.read_text(encoding="utf-8")
        self.assertIn("draft = false", content)

    def test_bundle_index_md_is_not_skipped(self):
        # 回归:08-16 前误跳 index.md 导致 52 篇 bundle 期文章漏补字段
        with tempfile.TemporaryDirectory() as td:
            root = self._make_root(td)
            d = root / "posts/tech/my-bundle"
            d.mkdir()
            f = d / "index.md"
            f.write_text("# 标题\n正文\n", encoding="utf-8")

            result = self.module.run(root=root, dry_run=False, recursive=True)

        self.assertEqual(result.changed, 1)

    def test_section_index_md_is_skipped(self):
        with tempfile.TemporaryDirectory() as td:
            root = self._make_root(td)
            f = root / "posts/tech/_index.md"
            original = "# 栏目\n"
            f.write_text(original, encoding="utf-8")

            result = self.module.run(root=root, dry_run=False, recursive=True)

            after = f.read_text(encoding="utf-8")
        self.assertEqual(result.changed, 0)
        self.assertEqual(after, original)

    def test_target_limits_scope_to_listed_files(self):
        # 钩子是收敛端:只应碰本次提交的文件,全量回填留给手动 --root 跑
        with tempfile.TemporaryDirectory() as td:
            root = self._make_root(td)
            staged = root / "posts/tech/staged.md"
            stray = root / "posts/tech/stray.md"
            staged.write_text("# 暂存的\n", encoding="utf-8")
            stray.write_text("# 无关的\n", encoding="utf-8")

            result = self.module.run(
                root=root, dry_run=False, recursive=True, targets=[staged]
            )

            staged_after = staged.read_text(encoding="utf-8")
            stray_after = stray.read_text(encoding="utf-8")
        self.assertEqual(result.changed, 1)
        self.assertIn("+++", staged_after)
        self.assertNotIn("+++", stray_after)

    def test_parse_args_accepts_target_and_live(self):
        argv = [
            "frontmatter_autofill.py",
            "--root",
            "content",
            "--target",
            "content/posts/a.md",
            "content/posts/b.md",
            "--live",
        ]

        with mock.patch.object(sys, "argv", argv):
            args = self.module.parse_args()

        self.assertEqual(args.target, ["content/posts/a.md", "content/posts/b.md"])
        self.assertTrue(args.live)


if __name__ == "__main__":
    unittest.main()
