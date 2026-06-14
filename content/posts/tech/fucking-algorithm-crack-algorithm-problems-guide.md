---
title: "fucking-algorithm：142k Stars 刷穿算法题完全指南"
date: "2026-04-06T22:25:00+08:00"
slug: "fucking-algorithm-crack-algorithm-problems-guide"
description: "全面介绍 142k Stars 的 fucking-algorithm 算法刷题笔记，涵盖学习路径、vscode-leetcode 插件、动态规划、回溯算法、二叉树、双指针等核心专题，以及多语言版本和面试技巧。"
draft: false
categories: ["技术笔记"]
tags: ["fucking-algorithm", "算法", "动态规划", "LeetCode", "vscode-leetcode", "刷题"]
---

## 学习目标

通过本文，你将全面掌握以下核心能力：

- 深入理解 fucking-algorithm 的项目定位、学习方法和核心特色
- 掌握算法学习的正确路径（先刷哪些题，再刷哪些题）
- 学会使用 vscode-leetcode VS Code 插件进行算法练习
- 掌握动态规划、链表、二叉树等核心数据结构
- 理解算法思维和刷题技巧
- 学会如何高效利用多语言版本的算法教程

---

## 1. 项目概述

### 1.1 是什么

**fucking-algorithm** 是一个知名的算法刷题笔记项目，帮助程序员高效掌握算法和数据结构。中文名"刷穿算法题"，英文标签"Crack Algorithm Problems"。

### 1.2 核心数据

| 指标 | 数值 |
|------|------|
| GitHub Stars | **142k** |
| GitHub Forks | **24.8k** |
| Contributors | **200** |
| Commits | **4,280** |
| 最新版本 | **v3.0** (2024-12-17) |
| License | **All Rights Reserved** |
| 语言 | **Markdown 100%** |

### 1.3 项目特色

| 特色 | 说明 |
|------|------|
| **先刷哪些题** | 学习路径清晰，不盲目刷题 |
| **多语言支持** | 简体中文、English、日语、韩语等 8+ 语言 |
| **VS Code 插件** | vscode-leetcode 插件支持 |
| **公众号** | labuladong 提供配套视频教程 |
| **实用技巧** | 涵盖面试高频题型和解题模板 |

### 1.4 创始人

**labuladong** 是创始人兼主要维护者，同时运营同名微信公众号，提供算法教学视频。

---

## 2. 学习路径

### 2.1 为什么刷题顺序很重要

很多人在 LeetCode 上刷题漫无目的，效率很低。这个项目的核心理念是：**先刷哪些题，再刷哪些题**，按照科学路径学习。

### 2.2 推荐学习顺序

**第一阶段：基础概念**

```bash
# 先掌握这些基础
1. 数组、链表、栈、队列
2. 哈希表
3. 树、二叉树
4. 图（了解即可）
```

**第二阶段：简单算法**

```bash
# 二分搜索
# 双指针
# 滑动窗口
# 排序
```

**第三阶段：高频题型**

```bash
# 动态规划（DP）
# 回溯算法
# 位运算
# BFS/DFS
```

**第四阶段：进阶内容**

```bash
# 链表二叉树高级技巧
# 数据结构设计
# 算法思维
```

### 2.3 刷题框架

**通用解题框架**：

```python
# 1. 明确函数定义
def dp(state1, state2, ...):
    # 2. 穷举所有选择
    for choice in choices:
        # 3. 做出选择
        new_state = transition(state, choice)
        # 4. 递归求解子问题
        result = dp(new_state1, new_state2, ...)
        # 5. 返回最优解
        return best(result, ...)
```

---

## 3. VS Code 插件

### 3.1 vscode-leetcode

VS Code 中的 LeetCode 插件，可以直接在 VS Code 中刷题、查看题解、提交代码。

**支持的编程语言**：

| 语言 | 支持状态 |
|------|----------|
| Python | ✅ 完整支持 |
| JavaScript/TypeScript | ✅ 完整支持 |
| Java | ✅ 完整支持 |
| C++ | ✅ 完整支持 |
| Go | ✅ 完整支持 |
| Rust | ✅ 完整支持 |
| 其他 | 🔧 部分支持 |

### 3.2 安装

```bash
# 在 VS Code 中搜索 "LeetCode"
# 或访问：https://marketplace.visualstudio.com/items?itemName=shengchen.vscode-leetcode
```

### 3.3 主要功能

| 功能 | 说明 |
|------|------|
| **刷题模式** | 在 VS Code 中查看题目、编写代码、提交 |
| **题解** | 查看高票回答和讨论 |
| **测试** | 本地测试用例 |
| **竞赛** | 参与 LeetCode 周赛/双周赛 |
| **收藏** | 收藏感兴趣的题目 |

### 3.4 使用技巧

```bash
# 1. 登录 LeetCode 账号
# Ctrl+Shift+P → LeetCode: Sign In

# 2. 切换题目列表
# Ctrl+Shift+P → LeetCode: Switch Solution Language

# 3. 提交代码
# Ctrl+Enter 提交

# 4. 查看题解
# Ctrl+Shift+S 查看高票回答
```

---

## 4. 核心算法专题

### 4.1 动态规划（DP）

**动态规划核心四要素**：

```python
# 1. 状态定义
#    dp[i] 表示...

# 2. 状态转移方程
#    dp[i] = dp[i-1] + dp[i-2]

# 3. 初始化
#    dp[0] = 1, dp[1] = 1

# 4. 遍历顺序
#    从前到后遍历
```

**经典问题**：

| 问题 | 难度 | 标签 |
|------|------|------|
| 爬楼梯 | 简单 | 斐波那契 |
| 编辑距离 | 困难 | 字符串 DP |
| 最长公共子序列 | 中等 | 序列 DP |
| 背包问题 | 中等/困难 | 背包 DP |

### 4.2 回溯算法

**回溯算法框架**：

```python
def backtrack(path, choices):
    if is_end_condition(path):
        result.add(path)
        return

    for choice in choices:
        # 做选择
        path.add(choice)
        # 递归
        backtrack(path, remaining_choices)
        # 撤销选择
        path.remove(choice)
```

**经典问题**：

| 问题 | 难度 | 说明 |
|------|------|------|
| 全排列 | 中等 | 回溯 + 剪枝 |
| N 皇后 | 困难 | 二维回溯 |
| 子集 | 中等 | 收集所有叶子节点 |
| 组合总和 | 中等 | 去重技巧 |

### 4.3 二叉树

**二叉树遍历框架**：

```python
def traverse(root):
    if not root:
        return

    # 前序位置（在访问左右子节点之前）
    traverse(root.left)

    # 中序位置（在访问左右子节点之间）
    traverse(root.right)

    # 后序位置（在访问左右子节点之后）
```

**经典问题**：

| 问题 | 难度 | 说明 |
|------|------|------|
| 二叉树最大深度 | 简单 | 递归/DFS |
| 二叉树最近公共祖先 | 中等 | 后序遍历 |
| 二叉树展开链表 | 中等 | 改造成链表 |
| 验证二叉搜索树 | 中等 | BST 特性 |

### 4.4 双指针

**双指针技巧**：

```python
# 1. 对撞双指针（左右指针向中间移动）
def two_pointers_opposite(arr):
    left, right = 0, len(arr) - 1
    while left < right:
        if condition(arr[left], arr[right]):
            return result
        left += 1
        right -= 1

# 2. 快慢指针（fast 和 slow 指针）
def fast_slow_pointer(head):
    slow = fast = head
    while fast and fast.next:
        slow = slow.next
        fast = fast.next.next
    return slow  # 中点
```

**经典问题**：

| 问题 | 难度 | 说明 |
|------|------|------|
| 有序数组两数之和 | 简单 | 对撞双指针 |
| 环形链表 | 简单 | 快慢指针 |
| 滑动窗口 | 中等/困难 | 变长窗口 |

### 4.5 BFS 和 DFS

**BFS 框架**：

```python
from collections import deque

def bfs(graph, start):
    visited = set()
    queue = deque([start])

    while queue:
        node = queue.popleft()
        if node in visited:
            continue
        visited.add(node)

        for neighbor in graph[node]:
            if neighbor not in visited:
                queue.append(neighbor)
```

**DFS 框架**：

```python
def dfs(node, visited):
    if node in visited:
        return
    visited.add(node)

    for neighbor in node.neighbors:
        dfs(neighbor, visited)
```

---

## 5. 多语言版本

### 5.1 支持的语言

fucking-algorithm 提供以下语言版本：

| 语言 | 网站 |
|------|------|
| **简体中文** | labuladong.github.io |
| **English** | en.labuladong.com |
| **Español** | es.labuladong.com |
| **日本語** | ja.labuladong.com |
| **한국어** | kr.labuladong.com |
| **Português** | pt.labuladong.com |
| **Français** | fr.labuladong.com |
| **Русский** | ru.labuladong.com |
| **اردو** | ud.labuladong.com |

### 5.2 如何选择语言版本

```bash
# 如果英文阅读有困难，可以选择中文版
# 学习算法后，再用英文版复习

# 推荐学习顺序：
# 1. 中文版打基础
# 2. 英文版深入理解
# 3. 其他语言版扩展
```

---

## 6. 配套资源

### 6.1 微信公众号

**labuladong** 公众号提供：

| 资源 | 说明 |
|------|------|
| **视频教程** | 配套算法视频讲解 |
| **每日一题** | 每天一道算法题 |
| **面试技巧** | 互联网大厂面试经验 |
| **源码解析** | 框架源码分析 |

### 6.2 LeetCode 题目分类

```bash
# 按照知识点分类练习
# 1. 数组 → 2. 字符串 → 3. 链表
# 4. 哈希表 → 5. 栈和队列 → 6. 二叉树
# 7. 图论 → 8. 动态规划 → 9. 回溯
# 10. 位运算
```

### 6.3 面试高频题型

```bash
# TOP 10 高频面试题
# 1. LRU 缓存 - 设计类
# 2. 两数之和 - 简单
# 3. 合并两个有序链表 - 中等
# 4. 括号生成 - 中等
# 5. 全排列 - 中等
# 6. 二叉树最近公共祖先 - 中等
# 7. 岛屿数量 - 中等
# 8. 滑动窗口最大值 - 困难
# 9. 合并 K 个有序链表 - 困难
# 10. 接雨水 - 困难
```

---

## 7. 学习方法

### 7.1 正确刷题流程

```bash
# 1. 读懂题目
#    - 输入输出是什么？
#    - 边界条件有哪些？
#    - 时间空间复杂度要求？

# 2. 分析思路
#    - 暴力解法是什么？
#    - 能否优化？（找重复子问题）

# 3. 写代码
#    - 先写框架
#    - 再填细节

# 4. 测试验证
#    - 正常case
#    - 边界case
#    - 性能测试
```

### 7.2 面试技巧

```bash
# 1. Clarify
#    - 提问明确需求
#    - 确认边界条件

# 2. Plan
#    - 说出思路
#    - 分析复杂度

# 3. Code
#    - 边说边写
#    - 代码规范

# 4. Verify
#    - 跑测试用例
#    - 分析边界情况
```

### 7.3 常见错误

| 错误 | 正确做法 |
|------|----------|
| 直接看答案 | 先思考，实在不会再看 |
| 只看不练 | 每道题都要自己写 |
| 不复习 | 定期回顾已刷题目 |
| 死记硬背 | 理解算法思想 |

---

## 8. 常见问题

### 8.1 刷题顺序

**问题**：应该按顺序刷还是随机刷？

**答案**：按照项目推荐的学习路径刷题效率最高。不要按题号顺序刷，那是随机顺序。

### 8.2 需要刷多少题

**问题**：LeetCode 刷多少题够用？

**答案**：

| 目标 | 推荐数量 |
|------|----------|
| 通过面试 | 100-200 题 |
| 大厂 offer | 200-300 题 |
| 算法竞赛 | 300+ 题 |

### 8.3 遗忘怎么办

**问题**：刷过的题忘记了怎么办？

**答案**：

1. 定期复习（隔 1 天、3 天、7 天）
2. 总结题型模板
3. 写博客记录学习心得

---

## 9. 总结

**fucking-algorithm** 是算法学习的优秀资源：

| 优势 | 说明 |
|------|------|
| **学习路径清晰** | 不盲目刷题 |
| **多语言支持** | 8+ 语言版本 |
| **配套插件** | VS Code LeetCode 插件 |
| **面试高频** | 涵盖主流面试题 |

**适用人群**：

- 准备互联网算法面试的求职者
- 想系统学习算法的开发者
- 参加算法竞赛的选手

**学习建议**：

1. 按照项目推荐路径刷题
2. 每道题都要自己写代码
3. 定期复习总结
4. 利用多语言版本加深理解

**官方资源**：

- GitHub：https://github.com/labuladong/fucking-algorithm
- 英文版：https://github.com/labuladong/labuladong.github.io
- VS Code 插件：https://marketplace.visualstudio.com/items?itemName=shengchen.vscode-leetcode
- 微信公众号：labuladong