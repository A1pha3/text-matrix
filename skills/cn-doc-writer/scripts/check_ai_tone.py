#!/usr/bin/env python3
"""
中文技术文档 AI 味门槛检查工具

目标：
- 将高频“AI 味”信号转成可执行的启发式检查
- 作为 quality.md 中“去 AI 味门槛”的本地脚本补充
- 默认给出提示和门槛状态；使用 --strict 时可作为阻断性检查

当前覆盖的高频信号：
- 生成式转场堆叠
- 过强作者在场感
- 教学控制句过密
- 模板化标题标签重复出现
"""

import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Dict, List

from utils import should_skip, is_in_inline_code, is_in_latex


class AIToneChecker:
    """AI 味门槛检查器"""

    def __init__(self):
        self.pattern_groups = {
            "生成式转场": [
                "更准确地说",
                "换句话说",
                "最重要的是",
                "这里必须明确",
                "本文将",
                "需要注意的是",
                "值得注意的是",
                "简单来说",
            ],
            "教学控制句": [
                "如果你只想",
                "读到这里",
                "你应该已经",
                "不妨",
                "不用担心",
                "一步一步带你",
            ],
            "作者在场感": [
                "我认为",
                "我更愿意",
                "我倾向于",
                "我会",
                "我宁愿",
            ],
        }
        self.template_headings = {
            "学习目标",
            "阅读指引",
            "自测问题",
            "进阶路径",
            "目标读者",
            "前置知识",
            "预计阅读时间",
        }

    def _collect_phrase_hits(self, lines: List[str]) -> Dict:
        counts = Counter()
        category_counts = Counter()
        matches = []

        for line_number, line in enumerate(lines, 1):
            if should_skip(lines, line_number):
                continue
            for category, phrases in self.pattern_groups.items():
                for phrase in phrases:
                    start = 0
                    while True:
                        idx = line.find(phrase, start)
                        if idx == -1:
                            break
                        if not is_in_inline_code(line, idx) and not is_in_latex(line, idx):
                            counts[phrase] += 1
                            category_counts[category] += 1
                            matches.append({
                                "line": line_number,
                                "category": category,
                                "phrase": phrase,
                            })
                        start = idx + len(phrase)

        return {
            "counts": counts,
            "category_counts": category_counts,
            "matches": matches,
        }

    def _collect_template_headings(self, lines: List[str]) -> List[Dict]:
        hits = []
        for line_number, line in enumerate(lines, 1):
            if should_skip(lines, line_number):
                continue
            match = re.match(r"^(#{1,6})\s+(.+?)\s*$", line.strip())
            if not match:
                continue
            heading = match.group(2)
            normalized = re.sub(r"^[§\d\s\.、\-（）()]+", "", heading).strip()
            if normalized in self.template_headings:
                hits.append({
                    "line": line_number,
                    "heading": normalized,
                })
        return hits

    def check_content(self, content: str) -> Dict:
        lines = content.split("\n")
        phrase_data = self._collect_phrase_hits(lines)
        heading_hits = self._collect_template_headings(lines)

        issues = []
        warnings = []

        repeated_transitions = {
            phrase: count
            for phrase, count in phrase_data["counts"].items()
            if phrase in self.pattern_groups["生成式转场"] and count >= 2
        }
        if repeated_transitions:
            details = "，".join(
                f"{phrase} × {count}" for phrase, count in sorted(repeated_transitions.items())
            )
            issues.append(f"生成式转场有重复堆叠：{details}")

        if phrase_data["category_counts"]["生成式转场"] >= 4:
            issues.append(
                f"生成式转场累计 {phrase_data['category_counts']['生成式转场']} 次，正文可能存在明显模板腔"
            )

        author_hits = phrase_data["category_counts"]["作者在场感"]
        if author_hits >= 2:
            issues.append(f"作者在场感短文内出现 {author_hits} 次，非评论文建议收敛")
        elif author_hits == 1:
            warnings.append("检测到 1 处作者在场感表达，建议确认是否确有必要")

        teaching_hits = phrase_data["category_counts"]["教学控制句"]
        if teaching_hits >= 3:
            issues.append(f"教学控制句出现 {teaching_hits} 次，可能打断正文推进")
        elif teaching_hits == 2:
            warnings.append("教学控制句出现 2 次，建议检查是否过度干预阅读节奏")

        if len(heading_hits) >= 2:
            issue_headings = "，".join(hit["heading"] for hit in heading_hits[:4])
            issues.append(f"检测到 {len(heading_hits)} 个模板化标题标签：{issue_headings}")

        gate_passed = len(issues) == 0

        return {
            "gate_passed": gate_passed,
            "issues": issues,
            "warnings": warnings,
            "summary": {
                "total_phrase_hits": sum(phrase_data["counts"].values()),
                "transition_hits": phrase_data["category_counts"]["生成式转场"],
                "teaching_control_hits": teaching_hits,
                "author_presence_hits": author_hits,
                "template_heading_hits": len(heading_hits),
            },
            "matches": phrase_data["matches"][:20],
            "template_headings": heading_hits[:20],
            "gate_effect": (
                "通过：可继续参与 A / S / 100 分评估"
                if gate_passed
                else "未通过：建议按 quality.md 将可读性封顶 20/25，总分不超过 89"
            ),
        }

    def check(self, file_path: Path) -> Dict:
        try:
            content = file_path.read_text(encoding="utf-8")
        except Exception as exc:
            return {
                "file": str(file_path),
                "gate_passed": False,
                "issues": [f"无法读取文件: {exc}"],
                "warnings": [],
                "summary": {},
                "matches": [],
                "template_headings": [],
                "gate_effect": "未通过：文件不可读",
            }

        result = self.check_content(content)
        result["file"] = str(file_path)
        return result


def _print_result(result: Dict):
    print(f"\n检查文件: {result['file']}")
    print(f"门槛状态: {'通过' if result['gate_passed'] else '未通过'}")
    print(f"门槛说明: {result['gate_effect']}")

    summary = result.get("summary", {})
    if summary:
        print("统计:")
        print(f"  - 生成式转场: {summary.get('transition_hits', 0)}")
        print(f"  - 教学控制句: {summary.get('teaching_control_hits', 0)}")
        print(f"  - 作者在场感: {summary.get('author_presence_hits', 0)}")
        print(f"  - 模板化标题: {summary.get('template_heading_hits', 0)}")

    if result["issues"]:
        print("问题:")
        for item in result["issues"]:
            print(f"  - {item}")
    if result["warnings"]:
        print("提示:")
        for item in result["warnings"]:
            print(f"  - {item}")
    if result["matches"]:
        print("命中示例:")
        for hit in result["matches"][:8]:
            print(
                f"  - 第 {hit['line']} 行 [{hit['category']}]：{hit['phrase']}"
            )


def main():
    if len(sys.argv) < 2:
        print("用法: python check_ai_tone.py <文件或目录> [--json] [--strict]")
        sys.exit(1)

    target = Path(sys.argv[1])
    json_output = "--json" in sys.argv
    strict = "--strict" in sys.argv
    checker = AIToneChecker()

    if target.is_file():
        result = checker.check(target)
        if json_output:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            _print_result(result)
        if strict and not result["gate_passed"]:
            sys.exit(2)
        return

    if target.is_dir():
        files = sorted(
            path for path in target.rglob("*")
            if path.suffix in (".md", ".txt", ".rst", ".adoc")
        )
        results = [checker.check(path) for path in files]
        failed = [item for item in results if not item["gate_passed"]]

        if json_output:
            print(json.dumps({
                "total_files": len(results),
                "failed_files": len(failed),
                "files": results,
            }, ensure_ascii=False, indent=2))
        else:
            print(f"找到 {len(results)} 个文件")
            print(f"未通过门槛: {len(failed)} 个")
            for result in failed[:20]:
                _print_result(result)

        if strict and failed:
            sys.exit(2)
        return

    if json_output:
        print(json.dumps({"error": f"路径不存在: {target}"}, ensure_ascii=False))
    else:
        print(f"路径不存在: {target}")
    sys.exit(1)


if __name__ == "__main__":
    main()