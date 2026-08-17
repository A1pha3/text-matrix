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

    # ---- 回归：2026-08-17 对抗审查发现的损坏场景 --------------------------

    def test_apply_on_empty_frontmatter_keeps_fields_inside_fences(self):
        # 空 frontmatter（---\n---）曾被 text.replace("", new_fm, 1) 把字段插到
        # 文件第 0 字符，frontmatter 整体失效、draft 闸门丢失
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            path = root / "posts/tech/empty-fm.md"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("---\n---\n# 正文标题\n\n内容。\n", encoding="utf-8")

            self.module.apply(path, root, dry_run=False)
            out = path.read_text(encoding="utf-8")

        self.assertTrue(out.startswith("---\n"))
        self.assertIn("\nslug : empty-fm\ncategories : [技术笔记]\n---\n", out)
        self.assertIn("# 正文标题", out)

    def test_body_starting_with_hr_is_not_treated_as_frontmatter(self):
        # 正文以 --- 水平线开头、无 frontmatter 的文件不得被注入字段
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            path = root / "posts/tech/hr-body.md"
            path.parent.mkdir(parents=True, exist_ok=True)
            original = "---\n\n一段导语。\n\n---\n\n# 标题\n"
            path.write_text(original, encoding="utf-8")

            result = self.module.apply(path, root, dry_run=False)
            out = path.read_text(encoding="utf-8")

        self.assertFalse(result.changed)
        self.assertEqual(out, original)

    def test_apply_preserves_body_and_trailing_newline(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            path = root / "posts/tech/plain.md"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(
                "---\ntitle: 正常\ndate: 2026-08-17\n---\n正文",
                encoding="utf-8",
            )

            self.module.apply(path, root, dry_run=False)
            out = path.read_text(encoding="utf-8")

        self.assertEqual(out.count("title: 正常"), 1)  # 旧内容不得翻倍
        self.assertTrue(out.startswith("---\ntitle: 正常"))
        self.assertTrue(out.endswith("正文"))  # 末尾无换行保持原样
        self.assertIn("---\n正文".replace("---\n正文", "\n---\n正文"), out)

    def test_bool_like_filename_gets_quoted_slug(self):
        # yes.md 不加引号会写出 slug: yes → YAML 解析为布尔 True
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            path = root / "posts/tech/yes.md"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("---\ntitle: t\n---\n正文\n", encoding="utf-8")

            self.module.apply(path, root, dry_run=False)
            out = path.read_text(encoding="utf-8")

        self.assertIn('slug : "yes"', out)

    def test_bom_file_is_handled(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            path = root / "posts/tech/bom.md"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(
                b"\xef\xbb\xbf---\ntitle: BOM\n---\n\xe6\xad\xa3\xe6\x96\x87\n"
            )

            result = self.module.apply(path, root, dry_run=False)
            out = path.read_text(encoding="utf-8")

        self.assertTrue(result.changed)
        self.assertIn("slug : bom", out)
        self.assertNotIn("﻿", out)  # BOM 已随重组清除


if __name__ == "__main__":
    unittest.main()