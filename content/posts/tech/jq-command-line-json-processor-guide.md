---
title: "jq 完全指南：命令行 JSON 处理工具"
slug: "jq-command-line-json-processor-guide"
description: "深入解析jq——34.2k Stars的命令行JSON处理工具。零依赖纯C编写，sed/awk/grep般的便捷体验，轻松切片、过滤、映射、转换结构化数据。"
date: "2026-04-11T00:25:00+08:00"
categories: ["技术笔记"]
tags: ["JSON", "命令行", "数据处理", "C语言", "工具", "sed", "awk", "管道"]
---

# jq 完全指南：命令行 JSON 处理工具

## §1 学习目标

通过本文，您将掌握：

1. **理解jq的核心价值**：为什么JSON处理需要专门的命令行工具
2. **掌握全部过滤器**：选择、映射、转换、聚合
3. **熟练使用管道**：与shell命令的完美结合
4. **理解高级特性**：函数、模块、条件逻辑
5. **掌握实战技巧**：日志处理、API响应解析、配置文件操作

---

## §2 项目概述

### 2.1 什么是jq？

> jq is a lightweight and flexible command-line JSON processor akin to sed, awk, grep, and friends for JSON data.

| 项目 | 信息 |
|------|------|
| **Stars** | 34.2k ⭐ |
| **Forks** | 1.8k |
| **语言** | C 79.0%, M4 6.7%, Shell 5.3% |
| **许可证** | MIT |
| **最新版本** | jq 1.8.1 (2025-07-01) |
| **最新提交** | Apr 8, 2026 (2天前) |
| **Commits** | 1,897 |
| **贡献者** | 231 |

### 2.2 核心特点

**零运行时依赖**
- 纯C编写，无需任何外部库
- 下载即用，无环境配置烦恼

**类sed/awk/grep体验**
- 熟悉Unix哲学
- 管道友好
- 文本处理者的JSON利器

**轻量快速**
- 二进制文件极小
- 处理速度极快
- 适合脚本集成

### 2.3 与其他工具对比

| 工具 | 定位 | 学习曲线 |
|------|------|---------|
| **jq** | JSON专用 | 中等 |
| **yq** | YAML处理 | 简单 |
| **python -m json.tool** | Python内置 | 简单 |
| **sed/awk** | 通用文本 | 陡峭 |
| **Node.js** | 通用编程 | 陡峭 |

---

## §3 快速上手

### 3.1 安装

**macOS:**
```bash
brew install jq
```

**Ubuntu/Debian:**
```bash
sudo apt-get install jq
```

**Arch Linux:**
```bash
sudo pacman -S jq
```

**Docker:**
```bash
docker run --rm -i ghcr.io/jqlang/jq < input.json
```

**Windows:**
下载预编译二进制文件，加入PATH即可。

### 3.2 在线体验

访问 [play.jqlang.org](https://play.jqlang.org) 即可在浏览器中试用jq！

### 3.3 第一个命令

```bash
# 基本语法
jq '.' input.json

# 管道输入
cat input.json | jq '.'
echo '{"name":"张三","age":30}' | jq '.'
```

---

## §4 过滤器详解

### 4.1 基础过滤器

| 过滤器 | 说明 | 示例 |
|--------|------|------|
| `.key` | 访问对象属性 | `jq '.name'` |
| `.[]` | 展开数组 | `jq '.[]'` |
| `.a.b` | 嵌套访问 | `jq '.user.name'` |
| `.[0]` | 数组索引 | `jq '.[0]'` |
| `.[-1]` | 最后一个元素 | `jq '.[-1]'` |

**示例数据：**
```json
{
  "name": "张三",
  "age": 30,
  "skills": ["Python", "Go", "Rust"],
  "address": {
    "city": "北京",
    "district": "朝阳区"
  }
}
```

```bash
# 访问姓名
echo '{"name":"张三"}' | jq '.name'
# 输出: "张三"

# 访问城市
echo '{"address":{"city":"北京"}}' | jq '.address.city'
# 输出: "北京"

# 访问数组元素
echo '["a","b","c"]' | jq '.[0]'
# 输出: "a"
```

### 4.2 数组操作

```bash
# 展开数组
echo '["a","b","c"]' | jq '.[]'
# 输出:
# "a"
# "b"
# "c"

# 数组切片
echo '[1,2,3,4,5]' | jq '.[0:3]'
# 输出: [1, 2, 3]

# 数组长度
echo '[1,2,3]' | jq 'length'
# 输出: 3

# 数组包含
echo '[1,2,3]' | jq 'contains([2])'
# 输出: true
```

### 4.3 对象操作

```bash
# 获取所有键
echo '{"a":1,"b":2}' | jq 'keys'
# 输出: ["a", "b"]

# 获取所有值
echo '{"a":1,"b":2}' | jq 'values'
# 输出: [1, 2]

# 获取键值对
echo '{"a":1,"b":2}' | jq 'to_entries'
# 输出: [{"key":"a","value":1},{"key":"b","value":2}]

# 对象合并
echo '{"a":1}' | jq '. + {"b":2}'
# 输出: {"a":1,"b":2}

# 删除键
echo '{"a":1,"b":2}' | jq 'del(.a)'
# 输出: {"b":2}
```

---

## §5 高级特性

### 5.1 管道组合

```bash
# 链式调用
echo '{"user":{"name":"张三","age":30}}' | jq '.user.name'
# 输出: "张三"

# 嵌套访问
echo '{"users":[{"name":"A"},{"name":"B"}]}' | jq '.users[].name'
# 输出:
# "A"
# "B"
```

### 5.2 运算符

```bash
# 算术运算
echo '5' | jq '. + 3'      # 加法: 8
echo '10' | jq '. - 4'      # 减法: 6
echo '6' | jq '. * 7'       # 乘法: 42
echo '10' | jq '. / 2'      # 除法: 5
echo '7' | jq '. % 3'       # 取模: 1

# 比较运算
echo '5' | jq '5 > 3'       # true
echo '5' | jq '5 >= 5'      # true
echo '"abc"' | jq '"abc" == "abc"'  # true
```

### 5.3 条件判断

```bash
# if-then-else
echo '5' | jq 'if . > 3 then "大" else "小" end'
# 输出: "大"

# 多条件
echo '7' | jq 'if . < 3 then "小" elif . < 7 then "中" else "大" end'
# 输出: "大"

# and/or/not
echo '5' | jq 'if . > 3 and . < 10 then "在范围内" else "超出范围" end'
# 输出: "在范围内"
```

### 5.4 内置函数

```bash
# 字符串函数
echo '"hello"' | jq 'upcase'
# 输出: "HELLO"

echo '"  hello  "' | jq 'trim'
# 输出: "hello"

echo '"hello"' | jq 'split("")'
# 输出: ["h", "e", "l", "l", "o"]

# 数值函数
echo '3.14159' | jq 'floor'    # 3
echo '3.14159' | jq 'ceil'     # 4
echo '3.6' | jq 'round'         # 4

# 数组函数
echo '[1,2,3]' | jq 'sort'      # [1,2,3]
echo '[3,1,2]' | jq 'sort'       # [1,2,3]
echo '[1,2,3]' | jq 'reverse'     # [3,2,1]
echo '[1,2,3]' | jq 'unique'     # [1,2,3]
echo '[1,1,2,2,3]' | jq 'unique'  # [1,2,3]

# 对象函数
echo '{"b":2,"a":1}' | jq 'sort_by(.a)'
# 输出: [{"a":1,"b":2}]
echo '[{"n":"b"},{"n":"a"}]' | jq 'sort_by(.n)'
# 输出: [{"n":"a"},{"n":"b"}]
```

### 5.5 高级过滤

```bash
# select - 条件筛选
echo '[1,2,3,4,5]' | jq 'map(select(. > 2))'
# 输出: [3, 4, 5]

# map - 批量转换
echo '[1,2,3]' | jq 'map(. * 2)'
# 输出: [2, 4, 6]

# flatten - 扁平化
echo '[[1,2],[3,4]]' | jq 'flatten'
# 输出: [1, 2, 3, 4]

# group_by - 分组
echo '[{"type":"a","v":1},{"type":"b","v":2},{"type":"a","v":3}]' | jq 'group_by(.type)'
# 输出: [[{"type":"a","v":1},{"type":"a","v":3}],[{"type":"b","v":2}]]

# any/all - 逻辑判断
echo '[true,false,true]' | jq 'any'  # true
echo '[true,false,false]' | jq 'all'  # false
```

---

## §6 实战技巧

### 6.1 API响应解析

```bash
# GitHub API响应
curl -s https://api.github.com/repos/jqlang/jq | jq '{stars: .stargazers_count, forks: .forks_count, name: .full_name}'

# 提取多个字段
curl -s 'https://httpbin.org/json' | jq '.slideshow.slides[] | {title: .title, type: .type}'
```

### 6.2 日志处理

```bash
# 解析JSON日志
cat app.log | jq -r '.timestamp + " " + .level + " " + .message'

# 过滤错误级别
cat app.log | jq -c 'select(.level == "ERROR")'

# 统计每种级别数量
cat app.log | jq -r '.level' | sort | uniq -c
```

### 6.3 配置文件操作

```bash
# 读取配置值
cat config.json | jq '.database.host'

# 修改配置值（不修改原文件）
cat config.json | jq '.port = 8080'

# 合并配置
jq -s '.[0] * .[1]' base.json override.json
```

### 6.4 数据转换

```bash
# CSV转JSON
cat data.csv | tail -n +2 | while IFS=',' read -r name age city; do
  echo "{\"name\":\"$name\",\"age\":\"$age\",\"city\":\"$city\"}"
done | jq -s '.'

# JSON转CSV
jq -r '.[] | [.name, .age, .city] | @csv' data.json

# JSON转TSV
jq -r '.[] | [.name, .age] | @tsv' data.json
```

### 6.5 管道组合

```bash
# 复杂数据处理
curl -s https://api.github.com/repos/jqlang/jq/commits | \
  jq '[.[] | {message: .commit.message, author: .commit.author.name, date: .commit.author.date}]' | \
  jq 'sort_by(.date) | reverse | .[0:5]'
```

---

## §7 命令行选项

| 选项 | 说明 |
|------|------|
| `-c` | 紧凑输出（单行） |
| `-r` | 原始输出（无引号） |
| `-n` | null输入模式 |
| `-f` | 从文件读取过滤程序 |
| `-e` | 根据输出设置退出码 |
| `-M` | 单色输出 |
| `-S` | 对象键排序 |
| `--arg` | 传入Shell变量 |
| `--argjson` | 传入JSON值 |

```bash
# 紧凑JSON输出
echo '{"a":1,"b":2}' | jq -c '.'
# 输出: {"a":1,"b":2}

# 原始字符串输出
echo '"hello"' | jq -r '.'
# 输出: hello

# 传入变量
NAME="张三"
echo '{}' | jq --arg name "$NAME" '.name = $name'
# 输出: {"name":"张三"}

# 读取过滤程序文件
echo '{"test":true}' | jq -f filter.jq
```

---

## §8 高级用法

### 8.1 自定义函数

```bash
# 在过滤程序中定义函数
echo '5' | jq 'def is_even: . % 2 == 0; is_even'
# 输出: false

# 递归函数
echo '5' | jq 'def fact: if . <= 1 then 1 else . * (. - 1 | fact) end; fact'
# 输出: 120
```

### 8.2 模块系统

```bash
# 使用模块
jq -L '~/.jq/lib' 'include "mylib"; myfunc'

# 导入远程模块 (需要网络)
jq -s 'import "stdlib" as std; std::round(.temperature)'
```

### 8.3 正则表达式

```bash
# 正则匹配
echo '"hello world"' | jq 'test("^hello")'
# 输出: true

# 正则替换
echo '"hello world"' | jq 'gsub("world"; "jq")'
# 输出: "hello jq"

# 正则提取
echo '"item123price456"' | jq '[match("[0-9]+"; "g")] | map(.string)'
# 输出: ["123", "456"]
```

---

## §9 与其他工具对比

### 9.1 jq vs yq

| 特性 | jq | yq |
|------|-----|-----|
| **处理对象** | JSON | YAML |
| **性能** | 更快 | 中等 |
| **语法** | 过滤器 | YAML原生 |
| **学习曲线** | 中等 | 简单 |

### 9.2 jq vs Python

```bash
# jq (一行命令)
echo '{"name":"张三"}' | jq '.name'

# Python (需要多行)
python3 -c "import json,sys; print(json.load(sys.stdin)['name'])"
```

---

## §10 总结

### 10.1 核心价值

1. **轻量快速**：纯C编写，零依赖
2. **管道友好**：Unix哲学，Shell无缝集成
3. **功能强大**：完整的JSON处理能力
4. **学习曲线平缓**：类sed/awk体验

### 10.2 常用场景

| 场景 | 常用命令 |
|------|---------|
| **API调试** | `curl -s API_URL \| jq '.'` |
| **日志分析** | `cat log.json \| jq 'select(.level=="ERROR")'` |
| **配置读取** | `cat config.json \| jq '.key'` |
| **数据转换** | `jq -s '.[0] * .[1]'` |
| **格式化输出** | `jq '.' file.json` |

### 10.3 学习资源

- 官方文档：jqlang.org
- 在线练习：play.jqlang.org
- Stack Overflow：jq tag
- GitHub Wiki：高级话题

---

*🦞 本文由钳岳星君基于 [jqlang/jq](https://github.com/jqlang/jq) 项目撰写，MIT许可证。*
