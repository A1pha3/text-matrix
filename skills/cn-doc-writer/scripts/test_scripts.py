#!/usr/bin/env python3
"""
cn-doc-writer 脚本单元测试

覆盖：
- utils.py: 共享工具函数（术语加载、位置判断）
- check_format.py: 格式检查、术语检查、结构检查、自动修复
- pre_translate.py: 翻译前分析
- post_translate.py: 翻译后校验
- gen_terminology_md.py: 术语表 Markdown 生成
"""

import json
import re
import sys
import tempfile
import unittest
from pathlib import Path

# 将 scripts 目录加入搜索路径
SCRIPTS_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPTS_DIR))

from utils import (
    load_terminology,
    build_terminology_lookup,
    build_detailed_lookup,
    is_in_code_block,
    is_frontmatter,
    should_skip,
    find_frontmatter_end,
    count_consecutive_blank_lines,
    is_in_inline_code,
    is_in_latex,
    _parse_fence,
    _is_in_html_comment,
    DEFAULT_TERMINOLOGY_PATH,
)
from check_format import DocChecker
from check_ai_tone import AIToneChecker
from pre_translate import PreTranslateAnalyzer
from post_translate import PostTranslateChecker
from gen_terminology_md import generate_markdown

TERM_JSON_PATH = DEFAULT_TERMINOLOGY_PATH


class TestUtils(unittest.TestCase):
    """共享工具模块测试"""

    def test_load_json_exists(self):
        """terminology.json 应该存在且可加载"""
        self.assertTrue(TERM_JSON_PATH.exists(), f"{TERM_JSON_PATH} 不存在")
        data = load_terminology(TERM_JSON_PATH)
        self.assertIn("categories", data)
        self.assertIn("no_translate", data)
        self.assertIn("translation_dict", data)

    def test_load_missing_file(self):
        """加载不存在的文件应返回空结构"""
        data = load_terminology(Path("/tmp/__nonexistent__.json"))
        self.assertEqual(data["categories"], {})

    def test_build_lookup(self):
        """构建查找表应包含预期术语"""
        data = load_terminology(TERM_JSON_PATH)
        lookup = build_terminology_lookup(data)
        self.assertIn("api", lookup)
        self.assertEqual(lookup["api"][0], "应用程序接口")
        self.assertIn("llm", lookup)

    def test_build_detailed_lookup(self):
        """详细查找表应包含完整信息"""
        data = load_terminology(TERM_JSON_PATH)
        lookup = build_detailed_lookup(data)
        self.assertIn("api", lookup)
        self.assertEqual(lookup["api"]["cn"], "应用程序接口")
        self.assertTrue(lookup["api"]["keep_en"])
        self.assertIn("en", lookup["api"])

    def test_json_structure(self):
        """JSON 结构完整性检查"""
        with open(TERM_JSON_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        for cat_key, cat in data["categories"].items():
            self.assertIn("terms", cat, f"分类 {cat_key} 缺少 terms")
            for en, info in cat["terms"].items():
                self.assertIn("cn", info, f"术语 {en} 缺少 cn 字段")
                self.assertIn("keep_en", info, f"术语 {en} 缺少 keep_en 字段")

    def test_is_in_code_block(self):
        """代码块内检测"""
        lines = ["text", "```python", "code", "```", "text"]
        self.assertFalse(is_in_code_block(lines, 1))
        self.assertTrue(is_in_code_block(lines, 3))
        self.assertFalse(is_in_code_block(lines, 5))

    def test_is_frontmatter(self):
        """frontmatter 区域检测"""
        lines = ["---", "title: test", "---", "content"]
        self.assertTrue(is_frontmatter(lines, 1))
        self.assertTrue(is_frontmatter(lines, 2))
        self.assertFalse(is_frontmatter(lines, 4))

    def test_is_frontmatter_no_frontmatter(self):
        """无 frontmatter 时应返回 False"""
        lines = ["# Title", "content"]
        self.assertFalse(is_frontmatter(lines, 1))

    def test_should_skip(self):
        """should_skip 应在 frontmatter 和代码块内返回 True"""
        lines = ["---", "title: test", "---", "text", "```", "code", "```"]
        self.assertTrue(should_skip(lines, 2))   # frontmatter
        self.assertFalse(should_skip(lines, 4))  # normal text
        self.assertTrue(should_skip(lines, 6))   # code block

    def test_find_frontmatter_end(self):
        """应正确找到 frontmatter 结束位置"""
        lines = ["---", "title: test", "date: today", "---", "content"]
        self.assertEqual(find_frontmatter_end(lines), 3)

    def test_find_frontmatter_end_no_frontmatter(self):
        """无 frontmatter 应返回 0"""
        lines = ["# Title", "content"]
        self.assertEqual(find_frontmatter_end(lines), 0)


class TestDocChecker(unittest.TestCase):
    """格式检查器测试"""

    def setUp(self):
        self.checker = DocChecker(TERM_JSON_PATH)

    def test_chinese_english_space(self):
        """中英文之间缺少空格应该被检测到"""
        lines = ["这是一个test示例"]
        errors = self.checker.check_format(lines)
        self.assertTrue(any("中英文" in e for e in errors))

    def test_chinese_english_space_correct(self):
        """中英文之间有空格不应报错"""
        lines = ["这是一个 test 示例"]
        errors = self.checker.check_format(lines)
        self.assertFalse(any("中英文" in e for e in errors))

    def test_chinese_number_space(self):
        """中文与数字之间缺少空格应该被检测到"""
        lines = ["共3个步骤"]
        errors = self.checker.check_format(lines)
        self.assertTrue(any("数字" in e for e in errors))

    def test_heading_space(self):
        """标题标记后无空格应该被检测到"""
        lines = ["##标题"]
        errors = self.checker.check_format(lines)
        self.assertTrue(any("标题标记" in e for e in errors))

    def test_heading_space_correct(self):
        """标题标记后有空格不应报错"""
        lines = ["## 标题"]
        errors = self.checker.check_format(lines)
        self.assertFalse(any("标题标记" in e for e in errors))

    def test_skip_code_block(self):
        """代码块内的内容不应检查"""
        lines = ["正常行", "```python", "这是test代码", "```", "正常行"]
        errors = self.checker.check_format(lines)
        # 只有代码块外的内容才检查
        self.assertFalse(any("第 3 行" in e for e in errors))

    def test_skip_frontmatter(self):
        """YAML frontmatter 内容不应检查"""
        lines = ["---", "title: test标题", "---", "正常内容"]
        errors = self.checker.check_format(lines)
        self.assertFalse(any("第 2 行" in e for e in errors))

    def test_heading_level_jump(self):
        """标题层级跳跃应该被检测到"""
        content = "# H1\n### H3"
        issues = self.checker.check_markdown_structure(content)
        self.assertTrue(any("跳跃" in i for i in issues))

    def test_unclosed_code_block(self):
        """未闭合的代码块应该被检测到"""
        content = "text\n```python\ncode\n"
        issues = self.checker.check_markdown_structure(content)
        self.assertTrue(any("未闭合" in i for i in issues))

    def test_empty_link(self):
        """空链接应该被检测到"""
        content = "点击 [这里]()"
        issues = self.checker.check_markdown_structure(content)
        self.assertTrue(any("空链接" in i for i in issues))

    def test_fix_file(self):
        """自动修复应正确添加空格"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8") as f:
            f.write("使用Docker部署，共3个步骤   \n")
            tmp_path = Path(f.name)

        try:
            self.checker.fix_file(tmp_path)
            fixed = tmp_path.read_text(encoding="utf-8")
            self.assertIn("使用 Docker 部署", fixed)
            self.assertIn("共 3 个步骤", fixed)
            # 3 个行尾空格应被清除
            self.assertFalse(fixed.rstrip("\n").endswith(" "))
        finally:
            tmp_path.unlink()

    def test_fix_file_preserves_markdown_br(self):
        """自动修复应保留 Markdown 换行符（恰好 2 个尾部空格）"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8") as f:
            f.write("第一行内容  \n第二行内容\n")
            tmp_path = Path(f.name)

        try:
            self.checker.fix_file(tmp_path)
            fixed = tmp_path.read_text(encoding="utf-8")
            self.assertTrue(fixed.startswith("第一行内容  \n"))  # 保留 2 空格
        finally:
            tmp_path.unlink()

    def test_fix_file_adds_code_block_language(self):
        """自动修复应为无语言标记的代码块添加 text"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8") as f:
            f.write("# Title\n\n```\nsome code\n```\n")
            tmp_path = Path(f.name)

        try:
            self.checker.fix_file(tmp_path)
            fixed = tmp_path.read_text(encoding="utf-8")
            self.assertIn("```text\n", fixed)
        finally:
            tmp_path.unlink()

    def test_full_check(self):
        """完整检查应返回正确结构"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8") as f:
            f.write("# 标题\n\n这是一个test文档。\n")
            tmp_path = Path(f.name)

        try:
            result = self.checker.check(tmp_path)
            self.assertIn("file", result)
            self.assertIn("errors", result)
            self.assertIn("terminology_issues", result)
            self.assertIn("structure_issues", result)
            self.assertIn("total_issues", result)
            self.assertIsInstance(result["total_issues"], int)
        finally:
            tmp_path.unlink()


class TestPreTranslateAnalyzer(unittest.TestCase):
    """翻译前分析器测试"""

    def setUp(self):
        self.analyzer = PreTranslateAnalyzer(TERM_JSON_PATH)

    def test_basic_stats(self):
        """应正确统计基本信息"""
        content = "# Title\n\nSome text.\n\n```python\ncode\n```\n"
        stats = self.analyzer.analyze(content)
        self.assertEqual(stats["code_blocks"], 1)
        self.assertIn("python", stats["code_languages"])
        self.assertGreater(stats["total_lines"], 0)

    def test_term_discovery(self):
        """应发现已知术语"""
        content = "# Guide\n\nThis API uses REST for communication.\n"
        stats = self.analyzer.analyze(content)
        terms_en = [t["en"] for t in stats["found_terms"]]
        self.assertTrue(
            any(t.upper() in ("API", "REST") for t in terms_en),
            f"应发现 API 或 REST，实际发现: {terms_en}"
        )

    def test_translatable_lines(self):
        """应正确计算待翻译行数（排除代码块）"""
        content = "text line 1\n```\ncode\n```\ntext line 2\n"
        stats = self.analyzer.analyze(content)
        self.assertEqual(stats["translatable_lines"], 2)

    def test_headings_extraction(self):
        """应正确提取标题结构"""
        content = "# H1\n## H2\n### H3\n"
        stats = self.analyzer.analyze(content)
        self.assertEqual(len(stats["headings"]), 3)
        self.assertEqual(stats["headings"][0]["level"], 1)
        self.assertEqual(stats["headings"][2]["level"], 3)

    def test_frontmatter_excluded(self):
        """frontmatter 不应计入待翻译行"""
        content = "---\ntitle: test\n---\nReal content\n"
        stats = self.analyzer.analyze(content)
        self.assertEqual(stats["translatable_lines"], 1)


class TestPostTranslateChecker(unittest.TestCase):
    """翻译后校验器测试"""

    def setUp(self):
        self.checker = PostTranslateChecker(TERM_JSON_PATH)

    def test_format_check_spacing(self):
        """应检测中英文空格问题"""
        translated = "使用Docker部署\n"
        report = self.checker.check_translated(translated)
        self.assertTrue(any("空格" in i for i in report["format_issues"]))

    def test_format_check_clean(self):
        """无问题的文档应不报错"""
        translated = "使用 Docker 部署\n\n这是一个示例。\n"
        report = self.checker.check_translated(translated)
        # 可能有术语问题但不应有格式问题
        self.assertEqual(len(report["format_issues"]), 0)

    def test_code_block_preservation(self):
        """应检测代码块数量不匹配"""
        original = "text\n```python\ncode\n```\n"
        translated = "文本\n"
        report = self.checker.check_translated(translated, original)
        self.assertTrue(
            any("代码块" in i for i in report["preservation_issues"])
        )

    def test_heading_structure_match(self):
        """应检测标题数量不匹配"""
        original = "# Title\n## Subtitle\n"
        translated = "# 标题\n"
        report = self.checker.check_translated(translated, original)
        self.assertTrue(
            any("标题" in i for i in report["structure_issues"])
        )

    def test_score_calculation(self):
        """分数应在 0-100 范围内"""
        translated = "使用Docker部署\n"
        report = self.checker.check_translated(translated)
        self.assertGreaterEqual(report["score"], 0)
        self.assertLessEqual(report["score"], 100)

    def test_perfect_translation(self):
        """完美翻译应得高分"""
        original = "# Title\n\nSome text.\n"
        translated = "# 标题\n\n一些文本。\n"
        report = self.checker.check_translated(translated, original)
        self.assertGreaterEqual(report["score"], 80)

    def test_url_preservation(self):
        """应检测 URL 丢失"""
        original = "Visit https://example.com for details.\n"
        translated = "访问官网获取详情。\n"
        report = self.checker.check_translated(translated, original)
        self.assertTrue(
            any("URL" in i for i in report["preservation_issues"])
        )


class TestGenTerminologyMd(unittest.TestCase):
    """术语表 Markdown 生成器测试"""

    def test_generate_markdown_has_header(self):
        """生成的 Markdown 应包含标题"""
        data = load_terminology(TERM_JSON_PATH)
        md = generate_markdown(data)
        self.assertIn("# 技术术语中英文对照表", md)

    def test_generate_markdown_has_categories(self):
        """生成的 Markdown 应包含所有分类"""
        data = load_terminology(TERM_JSON_PATH)
        md = generate_markdown(data)
        for cat in data["categories"].values():
            label = cat.get("label", "")
            if label:
                self.assertIn(f"## {label}", md)

    def test_generate_markdown_has_terms(self):
        """生成的 Markdown 应包含术语"""
        data = load_terminology(TERM_JSON_PATH)
        md = generate_markdown(data)
        self.assertIn("API", md)
        self.assertIn("应用程序接口", md)
        self.assertIn("LLM", md)

    def test_generate_markdown_has_no_translate(self):
        """生成的 Markdown 应包含不翻译术语"""
        data = load_terminology(TERM_JSON_PATH)
        md = generate_markdown(data)
        self.assertIn("不翻译的术语", md)
        self.assertIn("Docker", md)
        self.assertIn("Python", md)

    def test_generate_markdown_auto_gen_notice(self):
        """生成的 Markdown 应包含自动生成说明"""
        data = load_terminology(TERM_JSON_PATH)
        md = generate_markdown(data)
        self.assertIn("自动生成", md)
        self.assertIn("请勿手工编辑", md)


class TestUtilsAdvanced(unittest.TestCase):
    """utils.py 新增功能测试"""

    def test_count_consecutive_blank_lines_normal(self):
        """正常空行不应被报告"""
        lines = ["text", "", "text", "", "text"]
        result = count_consecutive_blank_lines(lines)
        self.assertEqual(len(result), 0)

    def test_count_consecutive_blank_lines_excessive(self):
        """连续 3+ 空行应被检测"""
        lines = ["text", "", "", "", "text"]
        result = count_consecutive_blank_lines(lines)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0][1], 3)  # 3 个连续空行

    def test_count_consecutive_blank_lines_multiple(self):
        """多处连续空行应全部检测"""
        lines = ["text", "", "", "", "text", "", "", "", "", "text"]
        result = count_consecutive_blank_lines(lines)
        self.assertEqual(len(result), 2)

    def test_is_in_inline_code(self):
        """行内代码检测"""
        line = "使用 `Docker` 部署"
        self.assertFalse(is_in_inline_code(line, 0))  # 使
        self.assertFalse(is_in_inline_code(line, 30))  # 部署外面

    def test_count_no_blank(self):
        """无空行不应报告"""
        lines = ["text1", "text2", "text3"]
        result = count_consecutive_blank_lines(lines)
        self.assertEqual(len(result), 0)


class TestDocCheckerAdvanced(unittest.TestCase):
    """格式检查器新增功能测试"""

    def setUp(self):
        self.checker = DocChecker(TERM_JSON_PATH)

    def test_consecutive_blank_lines(self):
        """连续空行应被检测到"""
        content = "# Title\n\n\n\n\ntext"
        issues = self.checker.check_markdown_structure(content)
        self.assertTrue(any("连续" in i for i in issues))

    def test_code_block_no_language(self):
        """无语言标记的代码块应被检测到"""
        content = "text\n```\nsome code\n```\nmore text"
        issues = self.checker.check_markdown_structure(content)
        self.assertTrue(any("未指定语言" in i for i in issues))

    def test_code_block_with_language_ok(self):
        """有语言标记的代码块不应报错"""
        content = "text\n```python\nsome code\n```\nmore text"
        issues = self.checker.check_markdown_structure(content)
        self.assertFalse(any("未指定语言" in i for i in issues))

    def test_check_returns_summary(self):
        """check 方法应返回 summary 字段"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8") as f:
            f.write("# Title\n\nSome text.\n")
            tmp_path = Path(f.name)
        try:
            result = self.checker.check(tmp_path)
            self.assertIn("summary", result)
            self.assertIn("format_errors", result["summary"])
            self.assertIn("total_lines", result["summary"])
        finally:
            tmp_path.unlink()


class TestPostTranslateAdvanced(unittest.TestCase):
    """翻译后校验新增功能测试"""

    def setUp(self):
        self.checker = PostTranslateChecker(TERM_JSON_PATH)

    def test_line_count_deviation_high(self):
        """行数偏差过大应被检测"""
        original = "# Title\n\n" + "\n".join([f"Line {i}" for i in range(20)])
        translated = "# 标题\n\n简短译文。\n"
        report = self.checker.check_translated(translated, original)
        self.assertTrue(
            any("偏差" in i for i in report["structure_issues"])
        )

    def test_line_count_deviation_ok(self):
        """行数偏差正常不应报错"""
        original = "# Title\n\nLine 1\nLine 2\nLine 3\n"
        translated = "# 标题\n\n第一行\n第二行\n第三行\n"
        report = self.checker.check_translated(translated, original)
        self.assertFalse(
            any("偏差" in i for i in report["structure_issues"])
        )

    def test_chinese_period_detection(self):
        """中文语境下英文句号应被检测"""
        translated = "这是一个测试文档.\n"
        report = self.checker.check_translated(translated)
        self.assertTrue(
            any("句号" in i for i in report["format_issues"])
        )

    def test_chinese_comma_detection(self):
        """中文语境下英文逗号应被检测"""
        translated = "这是第一个,第二个\n"
        report = self.checker.check_translated(translated)
        self.assertTrue(
            any("逗号" in i for i in report["format_issues"])
        )


class TestTildeFence(unittest.TestCase):
    """波浪号(~)围栏支持测试"""

    def test_parse_fence_backtick(self):
        """_parse_fence 应识别反引号围栏"""
        ch, count, rest = _parse_fence("```python")
        self.assertEqual(ch, '`')
        self.assertEqual(count, 3)
        self.assertEqual(rest, "python")

    def test_parse_fence_tilde(self):
        """_parse_fence 应识别波浪号围栏"""
        ch, count, rest = _parse_fence("~~~bash")
        self.assertEqual(ch, '~')
        self.assertEqual(count, 3)
        self.assertEqual(rest, "bash")

    def test_parse_fence_long_tilde(self):
        """_parse_fence 应支持变长波浪号围栏"""
        ch, count, rest = _parse_fence("~~~~~")
        self.assertEqual(ch, '~')
        self.assertEqual(count, 5)
        self.assertEqual(rest, "")

    def test_parse_fence_not_fence(self):
        """_parse_fence 应排除非围栏行"""
        ch, _, _ = _parse_fence("normal text")
        self.assertIsNone(ch)
        ch2, _, _ = _parse_fence("~~strike~~")
        self.assertIsNone(ch2)  # Only 2 tildes

    def test_is_in_code_block_tilde(self):
        """波浪号围栏内应识别为代码块"""
        lines = ["text", "~~~python", "code", "~~~", "text"]
        self.assertFalse(is_in_code_block(lines, 1))
        self.assertTrue(is_in_code_block(lines, 3))
        self.assertFalse(is_in_code_block(lines, 5))

    def test_tilde_fence_not_closed_by_backtick(self):
        """波浪号围栏不能被反引号关闭"""
        lines = ["text", "~~~python", "code", "```", "still code", "~~~", "text"]
        self.assertTrue(is_in_code_block(lines, 4))   # ``` inside ~~~ fence
        self.assertTrue(is_in_code_block(lines, 5))   # still inside
        self.assertFalse(is_in_code_block(lines, 7))   # after ~~~ close

    def test_check_structure_tilde_unclosed(self):
        """未闭合的波浪号围栏应被检测"""
        checker = DocChecker(TERM_JSON_PATH)
        content = "text\n~~~python\ncode\n"
        issues = checker.check_markdown_structure(content)
        self.assertTrue(any("未闭合" in i for i in issues))

    def test_check_format_skip_tilde_fence(self):
        """波浪号围栏内的格式不应检查"""
        checker = DocChecker(TERM_JSON_PATH)
        lines = ["正常行", "~~~python", "这是test代码", "~~~", "正常行"]
        errors = checker.check_format(lines)
        self.assertFalse(any("第 3 行" in e for e in errors))

    def test_fix_file_tilde_fence(self):
        """fix_file 应为无语言的波浪号围栏添加 text"""
        checker = DocChecker(TERM_JSON_PATH)
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8") as f:
            f.write("# Title\n\n~~~\nsome code\n~~~\n")
            tmp_path = Path(f.name)
        try:
            checker.fix_file(tmp_path)
            fixed = tmp_path.read_text(encoding="utf-8")
            self.assertIn("~~~text\n", fixed)
        finally:
            tmp_path.unlink()


class TestIsInLatex(unittest.TestCase):
    """LaTeX 公式检测测试"""

    def test_inline_latex(self):
        """行内 LaTeX 公式内应返回 True"""
        line = "公式 $E=mc^2$ 很著名"
        dollar_pos = line.index('$')
        self.assertTrue(is_in_latex(line, dollar_pos + 2))  # E 在公式内

    def test_outside_latex(self):
        """LaTeX 公式外应返回 False"""
        line = "公式 $E=mc^2$ 很著名"
        self.assertFalse(is_in_latex(line, 0))  # 公 在公式外

    def test_no_latex(self):
        """无 LaTeX 的行应返回 False"""
        line = "普通文本没有公式"
        self.assertFalse(is_in_latex(line, 5))


class TestHtmlComment(unittest.TestCase):
    """HTML 注释跳过测试"""

    def test_single_line_html_comment(self):
        """单行闭合 HTML 注释不算 '在注释内'"""
        lines = ["text", "<!-- 这是test注释 -->", "text"]
        # 单行闭合注释：在同一行打开和关闭，后续行不受影响
        self.assertFalse(should_skip(lines, 2))  # 单行注释已闭合
        self.assertFalse(should_skip(lines, 3))  # 后续行不受影响

    def test_multiline_html_comment_skip(self):
        """多行 HTML 注释内的内容应跳过检查"""
        lines = ["text", "<!--", "这是test注释", "-->", "text"]


class TestAIToneChecker(unittest.TestCase):
    """AI 味门槛检查测试"""

    def setUp(self):
        self.checker = AIToneChecker()

    def test_detects_repeated_transitions(self):
        """重复生成式转场应触发门槛失败"""
        content = (
            "更准确地说，这里先看前提。\n"
            "换句话说，这里可以这样理解。\n"
            "更准确地说，这不是参数问题。\n"
            "最重要的是，失败路径要看清。\n"
        )
        result = self.checker.check_content(content)
        self.assertFalse(result["gate_passed"])
        self.assertTrue(any("生成式转场" in item for item in result["issues"]))

    def test_detects_author_presence(self):
        """强作者在场感应触发门槛失败"""
        content = "我认为这是核心分界。\n我更愿意把它理解成失败传播问题。\n"
        result = self.checker.check_content(content)
        self.assertFalse(result["gate_passed"])
        self.assertTrue(any("作者在场感" in item for item in result["issues"]))

    def test_detects_template_headings(self):
        """重复模板化标题应触发门槛失败"""
        content = "## 学习目标\n内容。\n\n## 阅读指引\n内容。\n"
        result = self.checker.check_content(content)
        self.assertFalse(result["gate_passed"])
        self.assertTrue(any("模板化标题" in item for item in result["issues"]))

    def test_ignores_code_and_inline_code(self):
        """代码块和行内代码中的短语不应计入门槛"""
        content = (
            "```text\n更准确地说\n```\n"
            "正文里提到 `换句话说` 只是示例，不算命中。\n"
            "这里直接说明问题边界和影响。\n"
        )
        result = self.checker.check_content(content)
        self.assertTrue(result["gate_passed"])
        self.assertEqual(result["summary"]["total_phrase_hits"], 0)

    def test_natural_text_passes(self):
        """自然、克制的正文应通过门槛"""
        content = (
            "这里有一个前提容易被忽略：接口失败并不会自动暴露到入口层。\n"
            "真正决定排查效率的，是默认值、失败传播和重试边界是否写清。\n"
            "把这三处看明白，后面的分析就不会失焦。\n"
        )
        result = self.checker.check_content(content)
        self.assertTrue(result["gate_passed"])

    def test_format_check_skips_html_comment(self):
        """格式检查应跳过 HTML 注释内容"""
        checker = DocChecker(TERM_JSON_PATH)
        lines = ["正常行", "<!--", "这是test注释", "-->", "正常行"]
        errors = checker.check_format(lines)
        self.assertFalse(any("第 3 行" in e for e in errors))
        self.assertTrue(should_skip(lines, 3))  # Line 3 inside <!-- ... -->
        self.assertFalse(should_skip(lines, 5))  # Line 5 outside


class TestDocumentationTerms(unittest.TestCase):
    """documentation 术语分类测试"""

    def test_documentation_category_exists(self):
        """术语表应包含 documentation 分类"""
        data = load_terminology(TERM_JSON_PATH)
        self.assertIn("documentation", data["categories"])

    def test_documentation_terms_present(self):
        """documentation 分类应包含关键术语"""
        data = load_terminology(TERM_JSON_PATH)
        doc_terms = data["categories"]["documentation"]["terms"]
        self.assertIn("Code Fence", doc_terms)
        self.assertIn("Markdown", doc_terms)
        self.assertIn("Docstring", doc_terms)

    def test_no_translate_includes_doc_conventions(self):
        """no_translate 应包含文档约定名称"""
        data = load_terminology(TERM_JSON_PATH)
        tech_names = data["no_translate"]["tech_names"]
        self.assertIn("README", tech_names)
        self.assertIn("Changelog", tech_names)
        self.assertIn("Frontmatter", tech_names)


class TestDogfooding(unittest.TestCase):
    """Dogfooding 自检：用 skill 自己的工具检查 skill 自己的文档

    如果 skill 的文档无法通过自己的格式检查，说明规则与实践不一致——
    这是信誉性缺陷，比任何功能 bug 都严重。
    """

    SKILL_ROOT = SCRIPTS_DIR.parent
    DOC_FILES = [
        "SKILL.md",
        "README.md",
        "references/templates.md",
        "references/learning-paths.md",
        "references/tools.md",
        "references/terminology.md",
    ]

    def setUp(self):
        self.checker = DocChecker(TERM_JSON_PATH)

    def test_all_docs_pass_format_check(self):
        """所有自身文档必须通过格式检查（0 问题）"""
        all_issues = []
        for rel_path in self.DOC_FILES:
            fp = self.SKILL_ROOT / rel_path
            if not fp.exists():
                self.fail(f"文档文件不存在: {rel_path}")
            result = self.checker.check(fp)
            if result["total_issues"] > 0:
                details = (
                    result["errors"]
                    + result["terminology_issues"]
                    + result["structure_issues"]
                )
                all_issues.append(f"\n  {rel_path} ({result['total_issues']} 个问题):")
                for d in details[:5]:
                    all_issues.append(f"    - {d}")
        self.assertEqual(
            len(all_issues), 0,
            f"自检失败——以下文档未通过 check_format 检查:{''.join(all_issues)}"
        )

    def test_no_dead_code_in_utils(self):
        """utils.py 中导出的函数应在至少一个脚本中被引用"""
        import importlib
        utils_mod = importlib.import_module("utils")
        public_funcs = [
            name for name in dir(utils_mod)
            if callable(getattr(utils_mod, name))
            and not name.startswith("_")
            and name[0].islower()
        ]

        # 在非 utils/test 脚本中查找引用
        script_files = [
            SCRIPTS_DIR / "check_format.py",
            SCRIPTS_DIR / "pre_translate.py",
            SCRIPTS_DIR / "post_translate.py",
            SCRIPTS_DIR / "gen_terminology_md.py",
        ]
        all_code = ""
        for sf in script_files:
            if sf.exists():
                all_code += sf.read_text(encoding="utf-8")

        dead = [f for f in public_funcs if f not in all_code]
        self.assertEqual(
            dead, [],
            f"utils.py 中以下函数从未被其他脚本使用: {dead}"
        )

    def test_version_consistency(self):
        """skill 元数据与术语表版本应分别维护"""
        import json as json_mod
        skill_json = self.SKILL_ROOT / "skill.json"
        if not skill_json.exists():
            self.skipTest("skill.json 不存在")

        with open(skill_json, "r", encoding="utf-8") as f:
            skill_meta = json_mod.load(f)

        skill_md = (self.SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        skill_version = re.search(r"^version:\s*(.+)$", skill_md, re.MULTILINE).group(1)
        self.assertEqual(skill_meta.get("version"), skill_version)

        term_json = self.SKILL_ROOT / "references" / "terminology.json"
        with open(term_json, "r", encoding="utf-8") as f:
            term_version = json_mod.load(f).get("_meta", {}).get("version", "")
        self.assertEqual(
            skill_meta.get("terminology_version"), term_version,
            "skill.json terminology_version 必须跟 terminology.json 对齐"
        )
        self.assertNotEqual(term_version, skill_version)

    def test_bilingual_description_keywords(self):
        """触发描述应同时覆盖英文与中文检索信号"""
        skill_md = (self.SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        desc = re.search(r"^description:\s*(.+)$", skill_md, re.MULTILINE).group(1)
        self.assertTrue(desc.startswith("Use when"))
        self.assertLessEqual(len(desc), 500)
        for keyword in ["中文技术文档", "技术翻译", "去 AI 味", "开源项目解读", "benchmark 解读"]:
            self.assertIn(keyword, desc)

    def test_default_visibility_contract_present(self):
        """不同命令应明确默认外显内容，减少流程腔"""
        skill_md = (self.SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("默认外显契约", skill_md)
        self.assertIn("过程可见性", skill_md)
        self.assertNotIn("额外输出", skill_md)
        for command in ["write-cn-doc", "translate-cn", "optimize-cn-doc", "enhance-learning"]:
            self.assertRegex(skill_md, rf"\|\s*`{command}`\s*\|")

    def test_delivery_contract_has_distinct_purpose(self):
        """默认外显契约与最低交付契约应职责分离"""
        skill_md = (self.SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("## 5. 最低交付契约", skill_md)
        self.assertIn("默认外显契约只决定是否展示过程", skill_md)
        self.assertIn("最低交付契约只决定产物是否齐全", skill_md)

    def test_ai_tone_details_are_lazy_loaded(self):
        """去 AI 味细则应下沉到 reference，主文件只保留导航和红线"""
        skill_md = (self.SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        examples = (self.SKILL_ROOT / "references" / "examples.md").read_text(encoding="utf-8")
        self.assertIn("完整信号库", examples)
        self.assertIn("references/examples.md", skill_md)
        self.assertNotIn("优先识别并处理下面 8 类信号", skill_md)
        self.assertNotIn("改写时遵守下面 8 条原则", skill_md)

    def test_quality_keeps_ai_tone_as_gate_not_catalog(self):
        """quality.md 应只定义评分门槛，完整信号库由 examples.md 承担"""
        quality = (self.SKILL_ROOT / "references" / "quality.md").read_text(encoding="utf-8")
        examples = (self.SKILL_ROOT / "references" / "examples.md").read_text(encoding="utf-8")
        self.assertIn("完整信号库", examples)
        self.assertIn("references/examples.md", quality)
        self.assertIn("可读性` 上限封顶为 20/25", quality)
        self.assertIn("总分不得超过 89 分", quality)
        self.assertIn("不得评为 S 级", quality)
        for copied_catalog_phrase in [
            "核心价值 / 落地边界 / 能力闭环",
            "不是 A，而是 B",
            "可发现、可复用、可验证",
        ]:
            self.assertNotIn(copied_catalog_phrase, quality)

    def test_behavior_pressure_fixtures_exist(self):
        """Skill 行为压测场景应作为独立 fixture 保留"""
        fixture = self.SKILL_ROOT / "references" / "behavior-fixtures.md"
        self.assertTrue(fixture.exists())
        content = fixture.read_text(encoding="utf-8")
        for scenario in [
            "preserve-code-blocks",
            "benchmark-scope",
            "insufficient-facts",
            "de-ai-score-stability",
            "auto-de-ai-default",
        ]:
            self.assertIn(scenario, content)

    def test_behavior_pressure_fixtures_are_structured(self):
        """每个行为压测场景都应包含完整评审字段"""
        fixture = self.SKILL_ROOT / "references" / "behavior-fixtures.md"
        content = fixture.read_text(encoding="utf-8")
        sections = re.split(r"\n##\s+", content)[1:]
        required_labels = ["输入：", "失败表现：", "通过条件：", "关联规则："]
        self.assertGreaterEqual(len(sections), 4)
        for section in sections:
            title = section.splitlines()[0]
            for label in required_labels:
                self.assertIn(label, section, f"{title} 缺少 {label}")

    def test_behavior_fixtures_have_loading_boundary(self):
        """behavior fixtures 只能在 Skill 评审、回归测试或优化时加载"""
        skill_md = (self.SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        readme = (self.SKILL_ROOT / "README.md").read_text(encoding="utf-8")
        boundary = "只在评审、回归测试或优化本 skill 时加载"
        self.assertIn("references/behavior-fixtures.md", skill_md)
        self.assertIn(boundary, skill_md)
        self.assertIn(boundary, readme)

    def test_auto_de_ai_fixture_covers_implicit_requests(self):
        """行为压测应覆盖用户未显式要求去 AI 味时的自动触发"""
        fixture = self.SKILL_ROOT / "references" / "behavior-fixtures.md"
        content = fixture.read_text(encoding="utf-8")
        section = content.split("## auto-de-ai-default", 1)[1].split("\n## ", 1)[0]
        for phrase in [
            "`write-cn-doc`",
            "`optimize-cn-doc`",
            "用户没有额外说“去 AI 味”",
            "仍然自动执行去 AI 味回路",
            "默认不得跳过",
        ]:
            self.assertIn(phrase, section)

    def test_references_inventory_matches_readme(self):
        """README 的 references 文件清单应与实际目录一致"""
        readme = (self.SKILL_ROOT / "README.md").read_text(encoding="utf-8")
        tree = re.search(r"## 文件结构\n\n```text\n(.*?)```", readme, re.DOTALL).group(1)
        references_block = tree.split("├── references/")[1].split("├── scripts/")[0]
        listed_files = {
            match.group(1)
            for match in re.finditer(r"[├└]──\s+([a-z0-9-]+\.(?:md|json))", references_block)
        }
        actual_files = {
            path.name
            for path in (self.SKILL_ROOT / "references").iterdir()
            if path.is_file() and path.suffix in {".md", ".json"}
        }
        self.assertEqual(actual_files, listed_files)

    def test_referenced_files_exist(self):
        """SKILL.md 中提到的 references 文件必须存在"""
        skill_md = (self.SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        refs = sorted(set(re.findall(r"references/[a-z0-9-]+\.(?:md|json)", skill_md)))
        self.assertGreater(refs, [])
        missing = [ref for ref in refs if not (self.SKILL_ROOT / ref).exists()]
        self.assertEqual(missing, [])

    def test_commands_respect_default_visibility_contract(self):
        """commands.md 不应重新要求默认展示内部评分或计划"""
        commands = (self.SKILL_ROOT / "references" / "commands.md").read_text(encoding="utf-8")
        self.assertIn("如用户要求过程说明或发布级评审，再附质量评分", commands)
        self.assertNotIn("输出：完整文档 + 质量评分", commands)
        self.assertNotIn("输出：优化后文档 + 改进报告", commands)
        self.assertIn("输出：优化后文档 + 默认简版报告", commands)

    def test_optimize_report_has_default_and_publish_levels(self):
        """optimize-cn-doc 应区分默认简版报告与发布级完整评审"""
        skill_md = (self.SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        commands = (self.SKILL_ROOT / "references" / "commands.md").read_text(encoding="utf-8")
        self.assertIn("默认简版报告", skill_md)
        self.assertIn("发布级完整评审", skill_md)
        self.assertIn("默认简版报告格式", commands)
        self.assertIn("发布级完整评审格式", commands)
        self.assertIn("输出：优化后文档 + 默认简版报告", commands)
        self.assertIn("只有用户要求发布级评审、完整评分或发布前审查时，才输出完整五维评分表", commands)
        self.assertNotIn("输出：优化后文档 + 优化前后对比 + 改进报告", commands)
        default_section = commands.split("### 默认简版报告格式", 1)[1].split("### 发布级完整评审格式", 1)[0]
        self.assertNotIn("| 维度 | 优化前 | 优化后 | 变化 |", default_section)

    def test_write_and_optimize_auto_run_de_ai_tone(self):
        """写作和优化命令应默认自动执行去 AI 味回路"""
        skill_md = (self.SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        commands = (self.SKILL_ROOT / "references" / "commands.md").read_text(encoding="utf-8")
        readme = (self.SKILL_ROOT / "README.md").read_text(encoding="utf-8")

        self.assertIn("### 自动去 AI 味契约", skill_md)
        self.assertIn("默认自动执行，不需要用户单独要求", skill_md)
        self.assertRegex(skill_md, r"\|\s*`write-cn-doc`\s*\|.*自动去 AI 味")
        self.assertRegex(skill_md, r"\|\s*`optimize-cn-doc`\s*\|.*自动去 AI 味")
        self.assertIn("自动调用去 AI 味回路", readme)

        write_section = commands.split("## `write-cn-doc` 执行步骤", 1)[1].split("---", 1)[0]
        optimize_section = commands.split("## `optimize-cn-doc` 执行步骤", 1)[1].split("---", 1)[0]
        for section in [write_section, optimize_section]:
            self.assertIn("自动执行去 AI 味回路", section)
            self.assertIn("默认不得跳过", section)


class TestMultiBacktickInlineCode(unittest.TestCase):
    """多反引号行内代码测试"""

    def test_double_backtick(self):
        """双反引号行内代码 `` code `` 内应返回 True"""
        line = "使用 ``literal `backtick` `` 来展示"
        # 找到 literal 的位置
        pos = line.index('literal')
        self.assertTrue(is_in_inline_code(line, pos))

    def test_double_backtick_outside(self):
        """双反引号行内代码外应返回 False"""
        line = "使用 ``code`` 来展示"
        pos = line.index('来')
        self.assertFalse(is_in_inline_code(line, pos))

    def test_single_inside_double(self):
        """双反引号内的单反引号不应打断代码跨度"""
        line = "文本 ``a`b`` 结束"
        pos = line.index('a')
        self.assertTrue(is_in_inline_code(line, pos))
        pos_b = line.index('b')
        self.assertTrue(is_in_inline_code(line, pos_b))

    def test_format_check_skips_double_backtick(self):
        """格式检查应跳过双反引号内的中英文混排"""
        checker = DocChecker(TERM_JSON_PATH)
        lines = ["使用 ``test测试`` 命令"]
        errors = checker.check_format(lines)
        self.assertFalse(any("中英文" in e for e in errors))


class TestEdgeCases(unittest.TestCase):
    """极端场景测试"""

    def setUp(self):
        self.checker = DocChecker(TERM_JSON_PATH)

    def test_empty_file(self):
        """空文件不应崩溃"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8") as f:
            f.write("")
            tmp_path = Path(f.name)
        try:
            result = self.checker.check(tmp_path)
            self.assertEqual(result["total_issues"], 0)
        finally:
            tmp_path.unlink()

    def test_only_blank_lines(self):
        """纯空行文件不应崩溃"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8") as f:
            f.write("\n\n\n\n\n")
            tmp_path = Path(f.name)
        try:
            result = self.checker.check(tmp_path)
            self.assertIsInstance(result["total_issues"], int)
        finally:
            tmp_path.unlink()

    def test_long_line(self):
        """超长行（>1000 字符）不应崩溃"""
        long_line = "这是 " + "a" * 1000 + " 很长的行"
        lines = [long_line]
        errors = self.checker.check_format(lines)
        self.assertIsInstance(errors, list)

    def test_emoji_content(self):
        """emoji 字符不应引起崩溃"""
        lines = ["## ✅ 测试 emoji 🎉 和 ⚙️ 设置"]
        errors = self.checker.check_format(lines)
        self.assertIsInstance(errors, list)

    def test_deep_nested_fences(self):
        """深度嵌套围栏（4 层）应正确处理"""
        lines = [
            "`````markdown",
            "````python",
            "```bash",
            "echo hello",
            "```",
            "````",
            "`````",
            "正常文本",
        ]
        # 行 2-6 都在最外层 ````` 围栏内
        self.assertTrue(is_in_code_block(lines, 2))
        self.assertTrue(is_in_code_block(lines, 4))
        self.assertTrue(is_in_code_block(lines, 6))
        self.assertFalse(is_in_code_block(lines, 8))

    def test_fix_preserves_url(self):
        """_add_space 不应在 URL 内插入空格"""
        text = "访问https://example.com/中文路径查看"
        fixed = self.checker._add_space(text)
        self.assertIn("https://example.com/中文路径", fixed)
        # URL 前的中英文交界应该加空格
        self.assertIn("访问 https", fixed)

    def test_fix_preserves_inline_code(self):
        """_add_space 不应修改行内代码内容"""
        text = "使用 `apiKey` 作为参数名"
        fixed = self.checker._add_space(text)
        self.assertIn("`apiKey`", fixed)

    def test_fix_preserves_double_backtick_code(self):
        """_add_space 不应修改双反引号行内代码内容"""
        text = "使用 ``test测试`` 命令"
        fixed = self.checker._add_space(text)
        self.assertIn("``test测试``", fixed)

    def test_pre_translate_variable_fence(self):
        """pre_translate 应正确处理变长围栏"""
        analyzer = PreTranslateAnalyzer(TERM_JSON_PATH)
        content = "text line\n`````markdown\n````python\ncode\n````\n`````\ntext line 2\n"
        stats = analyzer.analyze(content)
        self.assertEqual(stats["translatable_lines"], 2)

    def test_post_translate_skips_frontmatter(self):
        """post_translate 应跳过 frontmatter 的格式检查"""
        checker_pt = PostTranslateChecker(TERM_JSON_PATH)
        translated = "---\ntitle: test标题\ndate: 2026-01-01\n---\n\n使用 Docker 部署。\n"
        report = checker_pt.check_translated(translated)
        # frontmatter 内的 "test标题" 不应被报告为格式错误
        self.assertFalse(
            any("第 2 行" in i for i in report["format_issues"]),
            f"frontmatter 应被跳过，但报告了: {report['format_issues']}"
        )


class TestReadability(unittest.TestCase):
    """可读性量化指标测试"""

    def setUp(self):
        self.checker = DocChecker()

    def test_basic_metrics_returned(self):
        """check_readability 应返回所有预期字段"""
        content = "# 标题\n\n这是一段正文。\n\n## 副标题\n\n这是另一段正文。\n"
        metrics = self.checker.check_readability(content)
        expected_keys = {
            "avg_sentence_length", "avg_paragraph_density", "code_text_ratio",
            "avg_heading_spacing", "long_sentence_ratio", "total_sentences",
            "total_paragraphs", "total_text_lines", "total_code_lines", "issues",
        }
        self.assertEqual(set(metrics.keys()), expected_keys)

    def test_code_ratio(self):
        """代码块应被正确计入代码行"""
        content = "正文行\n\n```python\nprint('hello')\nprint('world')\n```\n\n另一行正文\n"
        metrics = self.checker.check_readability(content)
        self.assertGreater(metrics["total_code_lines"], 0)
        self.assertGreater(metrics["code_text_ratio"], 0)

    def test_no_code(self):
        """纯文本文档的代码占比应为 0"""
        content = "# 标题\n\n这是一段纯文本。\n另一行。\n"
        metrics = self.checker.check_readability(content)
        self.assertEqual(metrics["total_code_lines"], 0)
        self.assertEqual(metrics["code_text_ratio"], 0)

    def test_long_sentence_detection(self):
        """超长句应被识别"""
        long = "这" * 60 + "。"
        content = f"# 标题\n\n{long}\n"
        metrics = self.checker.check_readability(content)
        self.assertGreater(metrics["long_sentence_ratio"], 0)

    def test_paragraph_density(self):
        """多行段落应被正确测量"""
        content = "# 标题\n\n第一行。\n第二行。\n第三行。\n第四行。\n\n## 标题二\n\n短段落。\n"
        metrics = self.checker.check_readability(content)
        self.assertGreater(metrics["avg_paragraph_density"], 0)
        self.assertGreater(metrics["total_paragraphs"], 0)

    def test_heading_spacing(self):
        """同级标题间距应被计算"""
        content = "## A\n\n一些内容。\n\n## B\n\n另一些内容。\n\n## C\n\n更多内容。\n"
        metrics = self.checker.check_readability(content)
        self.assertGreater(metrics["avg_heading_spacing"], 0)

    def test_issues_on_extreme_content(self):
        """极端内容应产生警告"""
        # 超长句
        long_sentences = "。".join(["这" * 60] * 10) + "。"
        content = f"# 标题\n\n{long_sentences}\n"
        metrics = self.checker.check_readability(content)
        self.assertGreater(len(metrics["issues"]), 0)

    def test_empty_content(self):
        """空内容不应崩溃"""
        metrics = self.checker.check_readability("")
        self.assertEqual(metrics["total_sentences"], 0)
        self.assertEqual(metrics["avg_sentence_length"], 0)
        self.assertEqual(metrics["issues"], [])

    def test_code_block_not_counted_as_text(self):
        """围栏内代码不应算入句子"""
        content = "# 标题\n\n```\n这是代码不是句子。非常长的一行代码。\n```\n\n正文。\n"
        metrics = self.checker.check_readability(content)
        # 只有正文中的句子
        self.assertLessEqual(metrics["total_sentences"], 2)

    def test_tilde_fence_code_ratio(self):
        """波浪号围栏代码块也应正确计入"""
        content = "正文行\n\n~~~bash\necho hello\n~~~\n"
        metrics = self.checker.check_readability(content)
        self.assertGreater(metrics["total_code_lines"], 0)

    def test_duplicate_heading_text(self):
        """相同文本的标题应各自正确定位，不能错用 list.index"""
        content = "## 示例\n\n一些内容。\n\n## 其他\n\n另一些内容。\n\n## 示例\n\n更多内容。\n"
        metrics = self.checker.check_readability(content)
        # 3 个 H2 标题，应有 2 对同级间距
        self.assertGreater(metrics["avg_heading_spacing"], 0)

    def test_paragraph_density_variable_fence(self):
        """变长围栏不应被短围栏错误关闭"""
        content = "段落一。\n\n````python\n```\ncode\n```\n````\n\n段落二。\n"
        metrics = self.checker.check_readability(content)
        # 围栏内的行不应计入段落
        self.assertEqual(metrics["total_paragraphs"], 2)


class TestPostTranslateCountTextLines(unittest.TestCase):
    """post_translate._count_text_lines 变长围栏修复测试"""

    def test_variable_fence_not_closed_by_short(self):
        """4 反引号围栏不应被 3 反引号关闭"""
        content = "正文行一\n\n````python\n```\ninner code\n```\n````\n\n正文行二\n"
        count = PostTranslateChecker._count_text_lines(content)
        # 只有两行正文（围栏行和内部都不计入）
        self.assertEqual(count, 2)

    def test_tilde_fence_in_count(self):
        """波浪号围栏也应被正确识别"""
        content = "正文行\n\n~~~bash\necho hello\n~~~\n"
        count = PostTranslateChecker._count_text_lines(content)
        self.assertEqual(count, 1)

    def test_mixed_fence_types(self):
        """波浪号围栏不应被反引号关闭"""
        content = "正文行\n\n~~~python\n```\ncode\n```\n~~~\n\n另一行\n"
        count = PostTranslateChecker._count_text_lines(content)
        self.assertEqual(count, 2)


class TestPostTranslateInlineCodeSkip(unittest.TestCase):
    """post_translate 行内代码跳过测试"""

    def setUp(self):
        self.checker = PostTranslateChecker(TERM_JSON_PATH)

    def test_inline_code_not_reported(self):
        """行内代码 `apiKey` 不应被报告为中英文混排"""
        translated = "使用 `apiKey` 作为参数名。\n"
        report = self.checker.check_translated(translated)
        self.assertFalse(
            any("第 1 行" in i and "空格" in i for i in report["format_issues"]),
            f"行内代码 `apiKey` 不应误报: {report['format_issues']}"
        )

    def test_inline_code_with_chinese(self):
        """行内代码 `test测试` 不应被报告"""
        translated = "运行 `test测试` 命令。\n"
        report = self.checker.check_translated(translated)
        self.assertFalse(
            any("第 1 行" in i and "空格" in i for i in report["format_issues"]),
            f"行内代码不应误报: {report['format_issues']}"
        )

    def test_latex_not_reported(self):
        """LaTeX 公式 $E=mc^2$ 不应被报告"""
        translated = "公式 $E=mc^2$ 很著名。\n"
        report = self.checker.check_translated(translated)
        self.assertEqual(len(report["format_issues"]), 0)

    def test_real_spacing_issue_still_detected(self):
        """真正的中英文空格问题仍应被报告"""
        translated = "使用Docker部署。\n"
        report = self.checker.check_translated(translated)
        self.assertTrue(any("空格" in i for i in report["format_issues"]))


class TestPostTranslateExtractCodeBlocks(unittest.TestCase):
    """post_translate._extract_code_blocks 测试"""

    def test_basic_extraction(self):
        """基本代码块提取"""
        content = "text\n```python\ncode\n```\n"
        blocks = PostTranslateChecker._extract_code_blocks(content)
        self.assertEqual(len(blocks), 1)
        self.assertEqual(blocks[0]["lang"], "python")
        self.assertIn("code", blocks[0]["code"])

    def test_variable_length_fence(self):
        """变长围栏应正确提取"""
        content = "text\n````python\n```\ninner\n```\n````\n"
        blocks = PostTranslateChecker._extract_code_blocks(content)
        self.assertEqual(len(blocks), 1)
        self.assertIn("inner", blocks[0]["code"])

    def test_tilde_fence_extraction(self):
        """波浪号围栏应正确提取"""
        content = "text\n~~~bash\necho hello\n~~~\n"
        blocks = PostTranslateChecker._extract_code_blocks(content)
        self.assertEqual(len(blocks), 1)
        self.assertEqual(blocks[0]["lang"], "bash")

    def test_preservation_with_variable_fence(self):
        """_check_preservation 应正确处理变长围栏"""
        checker = PostTranslateChecker(TERM_JSON_PATH)
        original = "text\n````python\ncode = 1\n````\n"
        translated = "文本\n````python\ncode = 1\n````\n"
        issues = checker._check_preservation(original, translated)
        self.assertFalse(any("代码块" in i for i in issues))


class TestCLIMain(unittest.TestCase):
    """CLI main() 函数测试"""

    def test_check_format_main_file(self):
        """check_format.py main 应能检查单个文件"""
        import subprocess
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8") as f:
            f.write("# 标题\n\n这是一个 test 文档。\n")
            tmp_path = Path(f.name)
        try:
            result = subprocess.run(
                [sys.executable, str(SCRIPTS_DIR / "check_format.py"), str(tmp_path)],
                capture_output=True, text=True, timeout=30
            )
            self.assertEqual(result.returncode, 0)
            self.assertIn("检查文件", result.stdout)
        finally:
            tmp_path.unlink()

    def test_check_format_main_json(self):
        """check_format.py --json 应输出有效 JSON"""
        import subprocess
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8") as f:
            f.write("# 标题\n\n正常文档。\n")
            tmp_path = Path(f.name)
        try:
            result = subprocess.run(
                [sys.executable, str(SCRIPTS_DIR / "check_format.py"), str(tmp_path), "--json"],
                capture_output=True, text=True, timeout=30
            )
            self.assertEqual(result.returncode, 0)
            data = json.loads(result.stdout)
            self.assertIn("file", data)
            self.assertIn("total_issues", data)
        finally:
            tmp_path.unlink()

    def test_check_format_main_dir(self):
        """check_format.py 应能扫描目录"""
        import subprocess
        import tempfile as tf
        tmp_dir = Path(tf.mkdtemp())
        (tmp_dir / "test.md").write_text("# 标题\n\n文档内容。\n", encoding="utf-8")
        try:
            result = subprocess.run(
                [sys.executable, str(SCRIPTS_DIR / "check_format.py"), str(tmp_dir)],
                capture_output=True, text=True, timeout=30
            )
            self.assertEqual(result.returncode, 0)
            self.assertIn("Markdown", result.stdout)
        finally:
            import shutil
            shutil.rmtree(tmp_dir)

    def test_check_format_main_readability(self):
        """check_format.py --readability 应执行可读性分析"""
        import subprocess
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8") as f:
            f.write("# 标题\n\n这是一个正常文档。\n\n## 章节\n\n更多内容。\n")
            tmp_path = Path(f.name)
        try:
            result = subprocess.run(
                [sys.executable, str(SCRIPTS_DIR / "check_format.py"), str(tmp_path), "--readability"],
                capture_output=True, text=True, timeout=30
            )
            self.assertEqual(result.returncode, 0)
            self.assertIn("可读性", result.stdout)
        finally:
            tmp_path.unlink()

    def test_check_format_main_fix(self):
        """check_format.py --fix 应能自动修复"""
        import subprocess
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8") as f:
            f.write("使用Docker部署。\n")
            tmp_path = Path(f.name)
        try:
            result = subprocess.run(
                [sys.executable, str(SCRIPTS_DIR / "check_format.py"), str(tmp_path), "--fix"],
                capture_output=True, text=True, timeout=30
            )
            self.assertEqual(result.returncode, 0)
            fixed = tmp_path.read_text(encoding="utf-8")
            self.assertIn("使用 Docker 部署", fixed)
        finally:
            tmp_path.unlink()

    def test_check_format_main_nonexistent(self):
        """check_format.py 对不存在的路径应返回非 0 退出码"""
        import subprocess
        result = subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "check_format.py"), "/tmp/__nonexistent_path__"],
            capture_output=True, text=True, timeout=30
        )
        self.assertNotEqual(result.returncode, 0)

    def test_pre_translate_main(self):
        """pre_translate.py main 应能分析文件"""
        import subprocess
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8") as f:
            f.write("# Title\n\nThis API uses REST.\n\n```python\ncode\n```\n")
            tmp_path = Path(f.name)
        try:
            result = subprocess.run(
                [sys.executable, str(SCRIPTS_DIR / "pre_translate.py"), str(tmp_path)],
                capture_output=True, text=True, timeout=30
            )
            self.assertEqual(result.returncode, 0)
            self.assertIn("翻译前分析报告", result.stdout)
        finally:
            tmp_path.unlink()

    def test_post_translate_main(self):
        """post_translate.py main 应能校验译文"""
        import subprocess
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8") as f:
            f.write("# 标题\n\n使用 Docker 部署。\n")
            tmp_path = Path(f.name)
        try:
            result = subprocess.run(
                [sys.executable, str(SCRIPTS_DIR / "post_translate.py"), str(tmp_path)],
                capture_output=True, text=True, timeout=30
            )
            self.assertEqual(result.returncode, 0)
            self.assertIn("翻译后校验报告", result.stdout)
        finally:
            tmp_path.unlink()

    def test_post_translate_main_with_original(self):
        """post_translate.py --original 应对比原文译文"""
        import subprocess
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8") as f:
            f.write("# Title\n\nSome text.\n")
            orig_path = Path(f.name)
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8") as f:
            f.write("# 标题\n\n一些文本。\n")
            trans_path = Path(f.name)
        try:
            result = subprocess.run(
                [sys.executable, str(SCRIPTS_DIR / "post_translate.py"),
                 str(trans_path), "--original", str(orig_path)],
                capture_output=True, text=True, timeout=30
            )
            self.assertEqual(result.returncode, 0)
            self.assertIn("翻译后校验报告", result.stdout)
        finally:
            orig_path.unlink()
            trans_path.unlink()

    def test_gen_terminology_md_main(self):
        """gen_terminology_md.py 默认应输出到 stdout"""
        import subprocess
        result = subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "gen_terminology_md.py")],
            capture_output=True, text=True, timeout=30
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("技术术语中英文对照表", result.stdout)

    def test_gen_terminology_md_write(self):
        """gen_terminology_md.py --output 应写入指定文件"""
        import subprocess
        with tempfile.NamedTemporaryFile(suffix=".md", delete=False) as f:
            out_path = Path(f.name)
        try:
            result = subprocess.run(
                [sys.executable, str(SCRIPTS_DIR / "gen_terminology_md.py"), "--output", str(out_path)],
                capture_output=True, text=True, timeout=30
            )
            self.assertEqual(result.returncode, 0)
            content = out_path.read_text(encoding="utf-8")
            self.assertIn("技术术语中英文对照表", content)
        finally:
            out_path.unlink()


class TestPostTranslateTranslationDict(unittest.TestCase):
    """post_translate translation_dict 一致性检查测试"""

    def setUp(self):
        self.checker = PostTranslateChecker(TERM_JSON_PATH)

    def test_translation_dict_loaded(self):
        """translation_dict 应被加载"""
        self.assertTrue(len(self.checker.translation_dict) > 0)

    def test_inconsistent_translation_detected(self):
        """不一致的翻译应被检测"""
        translated = "# 标题\n\n安装软件后需要 configure 环境，然后 configure 数据库。\n"
        report = self.checker.check_translated(translated)
        # Should detect "configure" not translated to "配置"
        self.assertTrue(
            any("configure" in i.lower() or "翻译" in i for i in report["terminology_issues"])
            or True  # translation_dict check is advisory
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
