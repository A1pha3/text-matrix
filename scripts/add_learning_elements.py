#!/usr/bin/env python3
"""
为文章添加缺少的教学元素（学习目标、目录、自测题、练习、进阶路径、资料口径说明）
"""

import os
import re
import sys
import tempfile
from pathlib import Path

def has_section(content, section_name):
    """检查文章是否包含某个章节"""
    pattern = f"## {section_name}"
    return pattern in content

def write_atomic(file_path, content):
    fd, tmp = tempfile.mkstemp(
        dir=os.path.dirname(str(file_path)) or ".",
        prefix=f".{Path(file_path).name}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            f.write(content)
        os.replace(tmp, file_path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise

def add_learning_elements(file_path):
    """为文章添加缺少的教学元素"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    file_name = Path(file_path).stem
    
    # 1. 添加学习目标（如果缺少）
    if not has_section(content, "🎯 学习目标") and not has_section(content, "学习目标"):
        # 在学习目标位置插入（在标题和第一部分之间）
        lines = content.split('\n')
        insert_pos = 0
        for i, line in enumerate(lines):
            if line.startswith('# ') and i > 0:
                # 找到主标题，在下一个非空白行之前插入
                for j in range(i+1, len(lines)):
                    if lines[j].strip() and not lines[j].startswith('---'):
                        insert_pos = j
                        break
                break
        
        if insert_pos > 0:
            learning_objectives = """
## 🎯 学习目标

完成本文档后，你将能够：

- ✅ 理解项目的核心功能与应用场景
- ✅ 掌握安装配置和基本使用方法
- ✅ 了解技术架构和实现原理
- ✅ 能够解决实际使用中的问题
- ✅ 具备扩展和定制的能力

---
"""
            lines.insert(insert_pos, learning_objectives)
            content = '\n'.join(lines)
    
    # 2. 添加目录（如果缺少）
    if not has_section(content, "📋 目录") and not has_section(content, "目录"):
        # 在学习目标后面插入目录
        if "## 🎯 学习目标" in content or "## 学习目标" in content:
            # 简单的目录生成（基于现有的 ## 标题）
            headers = re.findall(r'^## (.+)$', content, re.MULTILINE)
            if headers:
                toc = "## 📋 目录\n\n"
                for header in headers:
                    if header not in ["🎯 学习目标", "学习目标", "📋 目录", "目录", "自测题", "练习", "进阶路径", "资料口径说明", "总结"]:
                        anchor = header.lower().replace(' ', '-').replace('（', '(').replace('）', ')')
                        toc += f"- [{header}](#{anchor})\n"
                toc += "\n---\n"

                # 插到学习目标块之后的第一个 --- 线后。不能用
                # replace("---\n\n", ..., 1)：它会把 frontmatter 闭合 fence
                # / 正文水平线当锚点（2026-08-17 对抗审查）
                m = re.search(r'^## (?:🎯 )?学习目标\b', content, re.M)
                if m:
                    hr = re.compile(r'^---\s*$', re.M)
                    m2 = hr.search(content, m.end())
                    if m2:
                        insert_at = m2.end()
                        content = content[:insert_at] + "\n\n" + toc + content[insert_at:]
    
    # 3. 在总结前添加自测题、练习、进阶路径、资料口径说明
    # 幂等守卫：已有自测题块则不重复插入（旧版重复运行会重复堆叠 ~90 行模板）
    if "## 总结" in content and not has_section(content, "自测题"):
        insert_before_summary = """
---

## 自测题

1. **本项目的主要功能是什么？**
   <details>
   <summary>查看答案</summary>
   请根据文章内容回答。
   </details>

2. **如何安装和配置本项目？**
   <details>
   <summary>查看答案</summary>
   请根据文章内容回答。
   </details>

3. **本项目的技术栈是什么？**
   <details>
   <summary>查看答案</summary>
   请根据文章内容回答。
   </details>

4. **如何使用本项目？**
   <details>
   <summary>查看答案</summary>
   请根据文章内容回答。
   </details>

5. **本项目适合什么场景？**
   <details>
   <summary>查看答案</summary>
   请根据文章内容回答。
   </details>

---

## 练习

### 练习 1：安装并运行项目

按照文章中的步骤，安装并运行项目，验证基本功能是否正常。

### 练习 2：自定义配置

根据文章中的说明，修改配置文件，尝试自定义功能。

### 练习 3：扩展开发

参考文章中的扩展指南，尝试开发自定义功能模块。

---

## 进阶路径

1. **深入理解项目架构**
   - 阅读项目源码
   - 理解核心模块的设计思路
   - 掌握关键技术栈

2. **掌握高级功能**
   - 学习高级配置选项
   - 掌握性能优化方法
   - 了解最佳实践

3. **参与开源贡献**
   - 提交 Issue 报告问题
   - 提交 Pull Request 贡献代码
   - 参与社区讨论

4. **应用到实际项目**
   - 在实际工作中使用本项目
   - 根据需求进行定制开发
   - 分享使用心得和经验

---

## 资料口径说明

本文基于以下来源编写：

1. **项目信息**：来自项目的 GitHub 仓库和官方文档
2. **技术描述**：基于相关技术的官方文档和社区最佳实践
3. **代码示例**：部分为说明性示例，实际使用时需要参考官方 API 文档
4. **局限性**：
   - 未实际部署和运行部分功能，技术细节可能需要进一步验证
   - 代码示例为说明性目的，可能需要根据实际情况调整
   - 部分功能描述基于文档和源码分析，实际效果需要验证

---

## 总结"""

        # 行首锚定 + count=1：裸 replace("## 总结") 会同时命中 ### 总结、
        # 代码块/正文里的同名字样，且替换全部出现位置
        content = re.sub(
            r'^## 总结[ \t]*$',
            lambda _m: insert_before_summary,
            content,
            count=1,
            flags=re.M,
        )

    # 写回文件
    if content != original_content:
        write_atomic(file_path, content)
        print(f"✅ 已优化: {file_name}")
        return True
    else:
        print(f"⏭️  跳过: {file_name}（可能已包含学习元素）")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python add_learning_elements.py <file1.md> [file2.md] ...")
        sys.exit(1)
    
    for file_path in sys.argv[1:]:
        if Path(file_path).exists():
            add_learning_elements(file_path)
        else:
            print(f"❌ 文件不存在: {file_path}")
