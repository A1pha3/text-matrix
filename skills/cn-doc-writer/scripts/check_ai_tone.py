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
- 采集过程细节泄漏（取证层内部记录混入正文）
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
        # 采集过程细节泄漏信号（2026-08-21 新增，源于视频精读文章把
        # B 站字幕接口抓取失败日志写成正文「来源声明」块的事故；
        # 同日对抗性审查重构：判别锚点是"失败叙事短语"而非蛇形标识符——
        # 后者在技术文章里是合法内容，单独出现只提示不阻断）
        self.collection_leak_phrases = [
            "抓取失败",
            "未登录用户不可达",
            "接口对未登录",
            "字幕列表为空",
            "逐字字幕抓取",
        ]
        self.snake_case_pattern = re.compile(r"[a-z][a-z0-9]*(?:_[a-z0-9]+)+")

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

    def _collect_collection_leaks(self, lines: List[str]) -> Dict:
        """检测取证过程内部细节泄漏进正文

        升级矩阵（判别锚点是失败叙事，不是标识符）：
        1. 失败叙事短语（"抓取失败""未登录用户不可达"等）描述的是
           "作者的采集动作"，几乎不可能成为读者向文章的正当主题，
           命中即阻断；不豁免行内代码（取证 JSON 恰在行内代码里），
           扫描一行内的全部出现位置；
        2. 蛇形命名 token（如 need_login_subtitle）在技术文章里是合法
           内容（函数名/配置项/数学下标），单独出现只提示不阻断，
           与失败短语共现时作为佐证计入同一阻断；
        3. 疑问句豁免：短疑问行（≤60 字符且以 ？/? 结尾，如
           "Q: 抓取失败怎么办？"）描述的是读者的故障场景而非作者的
           采集叙事，不阻断；长度上限防止长句伪装疑问行绕过。
        代码块、frontmatter、HTML 注释内的内容不参与检测。
        """
        snake_hits = []
        phrase_hits = []

        for line_number, line in enumerate(lines, 1):
            if should_skip(lines, line_number):
                continue
            for match in self.snake_case_pattern.finditer(line):
                if is_in_latex(line, match.start()):
                    continue
                snake_hits.append({"line": line_number, "token": match.group(0)})
            stripped = line.rstrip()
            # 剥掉行尾 Markdown 强调符（如 **Q: ...？**），再判疑问行
            cleaned_tail = stripped.rstrip("*_~ ")
            is_question_line = (
                cleaned_tail.endswith(("？", "?")) and len(stripped) <= 60
            )
            for phrase in self.collection_leak_phrases:
                start = 0
                while True:
                    idx = line.find(phrase, start)
                    if idx == -1:
                        break
                    if not is_question_line:
                        phrase_hits.append({"line": line_number, "phrase": phrase})
                    start = idx + len(phrase)

        return {"snake_hits": snake_hits, "phrase_hits": phrase_hits}

    def check_content(self, content: str) -> Dict:
        lines = content.split("\n")
        phrase_data = self._collect_phrase_hits(lines)
        heading_hits = self._collect_template_headings(lines)
        leak_data = self._collect_collection_leaks(lines)

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

        if leak_data["phrase_hits"]:
            phrases = sorted({hit["phrase"] for hit in leak_data["phrase_hits"]})
            corroboration = ""
            if leak_data["snake_hits"]:
                tokens = sorted({hit["token"] for hit in leak_data["snake_hits"]})
                corroboration = "，伴蛇形字段名佐证：" + "，".join(tokens[:4])
            issues.append(
                "正文混入采集过程细节（失败叙事描述）："
                + "，".join(phrases[:6])
                + corroboration
                + "；读者不关心抓取过程，只保留材料性质结论"
            )
        elif leak_data["snake_hits"]:
            tokens = sorted({hit["token"] for hit in leak_data["snake_hits"]})
            warnings.append(
                f"正文含 {len(tokens)} 个蛇形命名标识符（如 {tokens[0]}）；"
                "技术文章中通常合法，仅当伴随抓取失败类描述时才需按采集细节泄漏处理"
            )

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
                "collection_leak_hits": len(leak_data["snake_hits"]) + len(leak_data["phrase_hits"]),
            },
            "matches": phrase_data["matches"][:20],
            "template_headings": heading_hits[:20],
            "collection_leaks": {
                "snake_hits": leak_data["snake_hits"][:20],
                "phrase_hits": leak_data["phrase_hits"][:20],
            },
            "gate_effect": (
                "通过：脚本覆盖的高频信号未命中；完整门槛仍需对照 quality.md 去 AI 味门槛评估"
                if gate_passed
                else "未通过：按 quality.md 可读性门槛处理，总分不超过 89 且不得评 S"
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
        print(f"  - 采集细节泄漏: {summary.get('collection_leak_hits', 0)}")

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
    leaks = result.get("collection_leaks", {})
    leak_examples = leaks.get("snake_hits", [])[:4] + leaks.get("phrase_hits", [])[:4]
    if leak_examples:
        print("采集细节泄漏示例:")
        for hit in leak_examples:
            detail = hit.get("token") or hit.get("phrase")
            print(f"  - 第 {hit['line']} 行：{detail}")


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