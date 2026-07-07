#!/usr/bin/env python3
"""
文章优化脚本 - 使用 cn-doc-writer 和 humanizer 技能优化文章到满分100分
"""

import re
import sys
from pathlib import Path

def score_article(content):
    """根据 cn-doc-writer 五维评分标准评分"""
    score = {
        "结构性": 0,
        "准确性": 0,
        "可读性": 0,
        "教学性": 0,
        "实用性": 0
    }
    
    # 结构性 (20分)
    if "# " in content:  # 有标题
        score["结构性"] += 5
    if "## " in content:  # 有章节
        score["结构性"] += 5
    if "目录" in content or "toc" in content.lower():  # 有目录
        score["结构性"] += 5
    if len(re.findall(r'##+ ', content)) > 5:  # 逻辑递进
        score["结构性"] += 5
    
    # 准确性 (25分) - 简化检查
    if "```" in content:  # 有代码块
        score["准确性"] += 10
    if re.search(r'https?://', content):  # 有链接
        score["准确性"] += 5
    if "参考文献" in content or "参考" in content:
        score["准确性"] += 5
    score["准确性"] += 5  # 术语一致性默认给分
    
    # 可读性 (25分)
    if re.search(r'[\u4e00-\u9fa5]', content):  # 有中文
        score["可读性"] += 5
    # 检查中英文空格
    if re.search(r'[\u4e00-\u9fa5] [a-zA-Z]', content) or re.search(r'[a-zA-Z] [\u4e00-\u9fa5]', content):
        score["可读性"] += 5
    # 段落长度
    paragraphs = content.split('\n\n')
    if all(len(p.split('\n')) < 10 for p in paragraphs if p.strip()):
        score["可读性"] += 5
    # 自然表达 - 检查AI味道
    ai_patterns = ["值得注意的是", "不难发现", "从某种意义上说", "可以看出", "在此基础上"]
    if not any(p in content for p in ai_patterns):
        score["可读性"] += 5
    else:
        score["可读性"] += 3
    # 结构化表达 - 列表 / 表格 / 代码块是否被合理使用
    has_list = bool(re.search(r'^\s*[-*] ', content, re.MULTILINE))
    has_table = bool(re.search(r'^\|.+\|$', content, re.MULTILINE))
    has_code_block = "```" in content
    if sum([has_list, has_table, has_code_block]) >= 2:
        score["可读性"] += 5
    
    # 教学性 (20分)
    if "学习目标" in content or "目标" in content:
        score["教学性"] += 5
    if "为什么" in content or "原因" in content:
        score["教学性"] += 5
    if "练习" in content or "自测" in content:
        score["教学性"] += 5
    if "进阶" in content or "下一步" in content:
        score["教学性"] += 5
    
    # 实用性 (10分)
    if "示例" in content or "例子" in content:
        score["实用性"] += 4
    if "常见" in content or "FAQ" in content:
        score["实用性"] += 3
    if "错误" in content or "排查" in content:
        score["实用性"] += 3
    
    total = sum(score.values())
    return score, total

def humanize_text(content):
    """使用 humanizer 规则去除AI味道"""
    # 去除空泛的重要性表述
    replacements = [
        (r"具有重要意义", "很重要"),
        (r"具有重要价值", "很有用"),
        (r"体现了.*?的重要性", "说明它很重要"),
        (r"值得注意的是", ""),
        (r"不难发现", ""),
        (r"从某种意义上说", ""),
        (r"可以看出", ""),
        (r"在此基础上", ""),
        (r"进一步地", ""),
        (r"有必要指出", ""),
        (r"总体来看", ""),
    ]
    
    for pattern, replacement in replacements:
        content = re.sub(pattern, replacement, content)
    
    return content

def optimize_article(file_path):
    """优化文章到满分100分"""
    print(f"正在优化: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 评分
    score, total = score_article(content)
    print(f"初始评分: {total}/100")
    print(f"各维度得分: {score}")
    
    # 如果已经100分，直接返回
    if total >= 100:
        print("文章已达到满分，无需优化")
        return total
    
    # 优化：去除AI味道
    content = humanize_text(content)
    
    # 保存优化版本
    output_path = file_path.replace('.md', '-optimized.md')
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    # 重新评分
    new_score, new_total = score_article(content)
    print(f"优化后评分: {new_total}/100")
    print(f"各维度得分: {new_score}")
    
    return new_total

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python optimize-article-to-100.py <article.md>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    final_score = optimize_article(file_path)
    
    if final_score >= 100:
        print("✅ 文章已优化到满分100分")
    else:
        print(f"⚠️ 文章当前得分: {final_score}/100，需要进一步优化")
