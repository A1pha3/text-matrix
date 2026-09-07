---
title: "jq 深度拆解：把 JSON 变成管道里的一道流"
date: "2026-04-11T00:25:00+08:00"
lastmod: "2026-09-07T00:00:00+08:00"
slug: "jq-command-line-json-processor-guide"
github_repo: "jqlang/jq"
description: "jq 用一门小型过滤器语言让 JSON 像 sed/awk 手下的文本一样在管道里流动。本文拆解它的流模型、过滤器语法、1.7/1.8 版本边界与模块系统，并给出从 curl 到 CSV 的完整任务链、真实报错排查清单与采用建议。"
categories: ["技术笔记"]
tags: ["JSON", "命令行工具", "Shell", "C语言"]
---

# jq 深度拆解：把 JSON 变成管道里的一道流

## 核心判断

jq 把 JSON 当流来过滤，而不是当文档来编程。官方 README 的自我定位是 "a lightweight and flexible command-line JSON processor akin to sed, awk, grep and friends"——sed、awk、grep 怎么处理文本，jq 就怎么处理 JSON。这句话里藏着它的全部设计：jq 程序不是脚本，而是一个过滤器（filter），对输入流里的每个值求值，结果连成输出流，继续喂给下一个命令。

任何脚本语言都能解析 JSON，jq 真正的贡献是把这件事压进 Unix 管道：一个零运行时依赖的单二进制（官方原话是 "written in portable C and has zero runtime dependencies"），加上一门只做变换的小语言。curl 拿回的响应、kubectl 输出的清单、服务里滚动的 JSON Lines 日志，都不必为此打开 Python——一行过滤器的事。

选型前需要知道两件事。第一，版本边界是真实的：`ascii_upcase` 全版本可用，而 `trim` 这批字符串函数是 1.8.0 才新增的，跑在旧版上会直接报 `not defined`。第二，2026 年 6 月发布的 1.8.2 是一次安全补丁版本，集中修复了一批 CVE——包括随机化哈希种子缓解哈希碰撞 DoS（CVE-2026-40164）、给 `contains` 和路径函数加深度上限防栈溢出（CVE-2026-40612、CVE-2026-33947）。长期躺在脚本里不动的 jq 值得升级一轮。

## 项目坐标

| 维度 | 数据 |
|------|------|
| 仓库 | jqlang/jq |
| Stars | 约 35.6 千（35,558） |
| Forks | 约 1.8 千 |
| 贡献者 | 约 230（GitHub 非匿名口径 228） |
| 提交数 | 约 1,940（master 分支） |
| 当前版本 | 1.8.2（2026-06-20） |
| 前两个版本 | 1.8.0（2025-06-01）、1.8.1（2025-07-01） |
| 仓库创建 | 2012-07-18 |
| 主语言 | C（约 79%，其余为 M4、Shell、Yacc 等） |
| License | 代码 MIT，文档 CC BY 3.0（见下方说明） |

Stars、Forks、贡献者与提交数取自 GitHub API，截至 2026-09-07。

License 有一处容易困惑的细节：仓库页面的 license 徽标显示 "Other" 而不是 MIT。原因是 COPYING 文件在 MIT 之外并入了 decNumber（ICU 许可）和 NetBSD `strptime()` 的署名条款，GitHub 无法把它识别为纯 MIT。项目自己的口径很明确：代码 MIT，文档 CC BY 3.0。

## 快速地图：过滤器、流、命令行选项

看 jq 要先分清三层，后文的每个语法点都落在这三层里：

| 层 | 管什么 | 代表 |
|----|--------|------|
| 过滤器语言 | 对每个输入值做变换的表达式 | `.name`、`.[]`、`map()`、`if` |
| 流模型 | 输入是值流，输出也是流 | 默认逐值输出；`-s` 吞成数组；`-n` 不读输入 |
| 命令行选项 | 输出格式、退出码、变量注入 | `-r`、`-c`、`-e`、`--arg` |

过滤器是 jq 程序的正式名称：读入一个值流，对其中每个值求值一次，把所有结果按顺序写成输出流。这个定义解释了 jq 大部分"怪异"行为——为什么 `.[]` 的输出不止一行，为什么 `map(f)` 等价于 `[.[] | f]`，为什么两个配置文件可以直接作为两个输入文档喂给 jq。理解了流，语法就只剩查表。

## 快速上手

```bash
# macOS
brew install jq

# Ubuntu/Debian
sudo apt-get install jq

# Arch Linux
sudo pacman -S jq
```

Windows 从 [GitHub Releases](https://github.com/jqlang/jq/releases) 下载预编译二进制；1.8.2 起官方构建覆盖了 Windows arm64，Docker 镜像补齐了 arm/v7。发布产物自 1.8.0 起带有 provenance attestation，安全敏感的场景可以用 `gh attestation verify --repo jqlang/jq <文件>` 校验来源。

Docker 场景用官方镜像 `ghcr.io/jqlang/jq`。注意镜像的入口就是 jq 本身，过滤器作为容器参数传入，`-i` 让它接管 stdin：

```bash
docker run --rm -i ghcr.io/jqlang/jq:latest '.version' < package.json
```

什么都不想装的话，浏览器打开官方练习场 [play.jqlang.org](https://play.jqlang.org) 就能试。

装好后先确认版本，本文标注"1.8+"的函数在 1.7.1 上会报 `not defined`：

```bash
jq --version
# 例如 jq-1.8.2

# 第一个命令：解析并按默认缩进重新打印，也就是最常见的"格式化"
echo '{"name":"张三","age":30}' | jq '.'
# {
#   "name": "张三",
#   "age": 30
# }
```

## 过滤器基础：路径、切片与展开

| 过滤器 | 说明 | 示例 |
|--------|------|------|
| `.key` | 访问对象属性 | `jq '.name'` |
| `.a.b` | 嵌套访问 | `jq '.user.name'` |
| `.["key"]` | 括号形式，键里有特殊字符时用 | `jq '.["my key"]'` |
| `.[0]` | 数组索引 | `jq '.[0]'` |
| `.[-1]` | 最后一个元素 | `jq '.[-1]'` |
| `.[a:b]` | 数组或字符串切片 | `jq '.[0:3]'` |
| `.[]` | 展开为数组或对象的值流 | `jq '.[]'` |

```bash
# 嵌套访问
echo '{"address":{"city":"北京"}}' | jq '.address.city'
# "北京"

# 数组索引与倒数索引
echo '["a","b","c"]' | jq '.[0], .[-1]'
# "a"
# "c"

# 切片对字符串同样有效
echo '"abc1234def"' | jq '.[0:7]'
# "abc1234"
```

对象操作的三件套是 `keys`、`to_entries` 和 `del`：

```bash
# keys 返回排序后的键；keys_unsorted 保留原始顺序
echo '{"b":1,"a":2}' | jq 'keys'
# ["a", "b"]

# 键值对拆开，常用于遍历
echo '{"a":1,"b":2}' | jq 'to_entries'
# [{"key":"a","value":1},{"key":"b","value":2}]

# 删除键
echo '{"a":1,"b":2}' | jq 'del(.a)'
# {"b":2}
```

## 流模型：为什么输出常常不止一行

这是 jq 和"另一个 JSON 库"的分界线。默认模式下，jq 对输入流中的每个 JSON 文档各跑一遍过滤器，输出所有结果。两行日志喂进去，就出来两行结果：

```bash
printf '{"lvl":"INFO","n":1}\n{"lvl":"ERROR","n":2}\n' | jq -c 'select(.lvl=="ERROR")'
# {"lvl":"ERROR","n":2}
```

这正好是 JSON Lines 日志的形状——jq 天然逐文档处理，不需要先拼接成大数组。

`.[]` 是流思想的核心：它把数组（或对象的值）拆散成流。`map(f)` 只是把流重新收拢的语法糖，`[.[] | f]` 和它完全等价：

```bash
echo '["a","b","c"]' | jq '.[]'
# "a"
# "b"
# "c"

echo '[1,2,3]' | jq 'map(. * 2)'
# [2, 4, 6]
```

跨文档聚合才需要 `-s`（slurp）：把整个输入吞成一个数组，过滤器只跑一次。合并两份配置靠的就是它——`*` 在对象上是递归深合并，嵌套字段会逐层融合而不是整体覆盖：

```bash
jq -s '.[0] * .[1]' base.json override.json

# 深合并的行为：同名字段逐层融合
echo '{"a":{"x":1},"b":1}' | jq '. * {"a":{"y":2}}'
# {"a":{"x":1,"y":2},"b":1}
```

`-n` 走另一个极端：不读任何输入，过滤器只用 `null` 跑一次。算数、从零构造 JSON 都用它：

```bash
jq -n '1 + 2 * 3'
# 7
```

## 运算、条件与内置函数

```bash
# 算术与比较
echo '5' | jq '. + 3'        # 8
echo '7' | jq '. % 3'        # 1
echo '5' | jq '. > 3'        # true

# 条件：if 必须以 end 收尾，elif 中接
echo '7' | jq 'if . < 3 then "小" elif . < 7 then "中" else "大" end'
# "大"

# 布尔组合
echo '5' | jq 'if . > 3 and . < 10 then "在范围内" else "超出范围" end'
# "在范围内"
```

字符串函数里有一个高频陷阱：jq 没有 `upcase` 和 `downcase`，只有 ASCII 范围的 `ascii_upcase` / `ascii_downcase`。写成 `upcase` 会直接报 `not defined`：

```bash
echo '"hello"' | jq 'ascii_upcase'
# "HELLO"

# 去首尾空白：trim / ltrim / rtrim / trimstr，均为 1.8+ 新增
echo '"  hello  "' | jq 'trim'          # 1.8+
# "hello"
```

数值与数组函数没有版本坑，各版本一致：

```bash
echo '3.14159' | jq 'floor, ceil'    # 3 与 4
echo '3.6' | jq 'round'              # 4

echo '[3,1,2]' | jq 'sort'           # [1,2,3]
echo '[1,1,2,2,3]' | jq 'unique'     # [1,2,3]
echo '[1,2,3]' | jq 'reverse'        # [3,2,1]
echo '[[1,2],[3,4]]' | jq 'flatten'  # [1,2,3,4]
echo '[1,2,3]' | jq 'contains([2])'  # true

# 按字段排序、按字段分组（group_by 的结果按分组键排好序）
echo '[{"n":"b"},{"n":"a"}]' | jq 'sort_by(.n)'
# [{"n":"a"},{"n":"b"}]

echo '[{"type":"a","v":1},{"type":"b","v":2},{"type":"a","v":3}]' | jq 'group_by(.type)'
# [[{"type":"a","v":1},{"type":"a","v":3}],[{"type":"b","v":2}]]

# 存在性判断
echo '[true,false,true]' | jq 'any'   # true
echo '[true,false,false]' | jq 'all'  # false
```

`select` 负责筛选，它是流模型里"过滤"二字的直接实现——不满足条件的值直接从输出流里消失：

```bash
echo '[1,2,3,4,5]' | jq 'map(select(. > 2))'
# [3, 4, 5]

echo '[{"name":"A"},{"name":"B"}]' | jq '.[] | select(.name == "A")'
# {"name":"A"}
```

## 一次真实任务：从 GitHub API 到 CSV

把前面的东西串起来：拉取 jq 仓库最近的提交，清洗成人能读的清单，再落成 CSV。以下输出全部来自 2026-09-07 的真实请求。

第一步，拿数据、看结构。拿到陌生 JSON 先 `length` 或 `keys` 摸形状，比直接盯原始文本快得多：

```bash
curl -s 'https://api.github.com/repos/jqlang/jq/commits?per_page=5' -o commits.json
jq 'length' commits.json
# 5
```

第二步，提取字段。`.[]` 拆开提交数组，对每个提交构造一个小对象，外层 `[]` 把流收回数组；`.[0:7]` 截短 SHA，`split("\n")[0]` 取提交信息首行（完整 message 常带多段正文）：

```bash
jq '[.[] | {sha: .sha[0:7], author: .commit.author.name, date: .commit.author.date}]' commits.json
# [
#   {
#     "sha": "9d241e2",
#     "author": "dependabot[bot]",
#     "date": "2026-09-01T06:30:46Z"
#   },
#   {
#     "sha": "8bce8b6",
#     "author": "dependabot[bot]",
#     "date": "2026-09-01T06:24:58Z"
#   },
#   ... 共 5 条
# ]
```

第三步，清洗。机器人的依赖升级提交通常不值得人看，`select` 过滤后只剩三个真人提交：

```bash
jq -r '.[] | select(.commit.author.name | startswith("dependabot") | not)
      | [.sha[0:7], .commit.author.name] | @tsv' commits.json
# 41b8edf	Anna Rift
# 17b4118	Thomas Klausner
# fbee8f4	august
```

第四步，落 CSV。`@csv` 把数组转成 CSV 行：字符串自动加引号，数字原样输出。`-r` 去掉外层引号，输出即可直接重定向进 `.csv` 文件：

```bash
jq -r '.[] | [.sha[0:7], .commit.author.date, .commit.author.name,
      (.commit.message | split("\n")[0])] | @csv' commits.json
# "9d241e2","2026-09-01T06:30:46Z","dependabot[bot]","build(deps): bump markdown from 3.10.2 to 3.10.3 in /docs (#3622)"
# "8bce8b6","2026-09-01T06:24:58Z","dependabot[bot]","build(deps): bump lxml from 6.1.1 to 6.1.2 in /docs (#3621)"
# "41b8edf","2026-08-23T15:06:16Z","Anna Rift","Fix a handful of typos (#3605)"
# "17b4118","2026-08-23T15:03:21Z","Thomas Klausner","Fix strftime-related functions on NetBSD. (#3579)"
# "fbee8f4","2026-08-23T15:01:54Z","august","Reject raw NUL bytes in the parser instead of silently truncating tokens (#3606)"
```

同一份数据还可以按时间倒序取前几条——`sort_by`、`reverse`、切片三个原语的组合拳：

```bash
jq -r '[.[] | {sha: .sha[0:7], date: .commit.author.date}]
      | sort_by(.date) | reverse | .[0:3][] | [.sha, .date] | @tsv' commits.json
# 9d241e2	2026-09-01T06:30:46Z
# 8bce8b6	2026-09-01T06:24:58Z
# 41b8edf	2026-08-23T15:06:16Z
```

## 命令行选项：脚本集成的接口面

| 选项 | 说明 |
|------|------|
| `-r` | 字符串结果按原始文本输出（去引号），对接 shell 的标配 |
| `-c` | 紧凑输出，一行一个值 |
| `-s` | 把整个输入吞成一个数组再过滤 |
| `-n` | 不读输入，用 null 跑一次过滤器 |
| `-e` | 按最后一个输出值设置退出码（语义见下） |
| `-f file` | 从文件读取过滤器，复杂逻辑别塞进单引号 |
| `-S` | 输出时对对象键排序 |
| `-M` | 强制单色输出 |
| `--arg name v` | 注入字符串变量，过滤器里用 `$name` 引用 |
| `--argjson name v` | 注入 JSON 变量 |

`-e` 是 jq 进 CI 脚本的钥匙。退出码规则：最后一个输出既不是 `false` 也不是 `null` 时为 0；是 `false` 或 `null` 时为 1；整个运行没有产生任何输出时为 4。常规错误不经 `-e` 就是另外两档：2 是用法或系统错误，3 是过滤器编译错误。

```bash
# 配置开关检查：enabled 为 false 或缺失时走 else 分支
if jq -e '.features.new_ui' config.json > /dev/null; then
  echo "new UI enabled"
fi
```

变量注入让过滤器可以接收外部输入，不用字符串拼接——拼接是过滤器注入漏洞的入口：

```bash
NAME="张三"
echo '{}' | jq --arg name "$NAME" '.name = $name'
# {"name":"张三"}

echo '{}' | jq --argjson cfg '{"port":8080}' '.config = $cfg'
# {"config":{"port":8080}}
```

## 进阶：def、模块与正则

过滤器语言支持自定义函数，包括递归。阶乘一行写完：

```bash
echo '5' | jq 'def fact: if . <= 1 then 1 else . * (. - 1 | fact) end; fact'
# 120
```

反复使用的过滤器应该沉淀成模块。把定义写进 `~/.jq/lib/mylib.jq`：

```jq
def double: . * 2;
def add_tax(rate): . * (1 + rate);
```

引用方式有两种。`include` 把定义并进当前作用域，直接按名字调用；`import ... as m` 加命名空间，用 `m::double` 引用，避免重名冲突：

```bash
jq -L '~/.jq/lib' 'include "mylib"; double' <<< '21'
# 42
jq -L '~/.jq/lib' 'include "mylib"; add_tax(0.06)' <<< '100'
# 106
jq -L '~/.jq/lib' 'import "mylib" as m; m::double' <<< '21'
# 42
```

搜索路径有一条实测出来的规矩：默认搜索路径包含 `~/.jq` 这一层，但不包含它的子目录——放在 `~/.jq/lib` 里的模块必须用 `-L` 显式加上；`-L` 参数开头的 `~` 和 `$ORIGIN`（jq 可执行文件所在目录）会按手册规则替换，所以上面 `-L '~/.jq/lib'` 的写法有效。1.8.0 还给 `-L` 补了长选项形式 `--library-path`。作为参照，如果只是偶尔复用，直接把 `.jq` 文件平铺在 `~/.jq/` 下，连 `-L` 都不用写。

正则方面，jq 的 `test`、`match`、`gsub`、`capture` 建在 Oniguruma 库上，语法是 "Perl NG"（带命名分组的 Perl 风格）——手册原话。前三个函数覆盖日常需求：

```bash
# 匹配判断
echo '"hello world"' | jq 'test("^hello")'
# true

# 替换
echo '"hello world"' | jq 'gsub("world"; "jq")'
# "hello jq"

# 全局提取：match 返回对象流，"g" 标志开启全局，取 .string 字段
echo '"item123price456"' | jq '[match("[0-9]+"; "g")] | map(.string)'
# ["123", "456"]
```

还想往深走，方向是 `reduce` 和 `foreach` 两个迭代器——它们让过滤器语言拥有折叠和带状态循环的能力。顺带一提，1.8.0 曾改动过它们的状态变量语义，又因性能回退在 1.8.1 撤销，这段反复本身说明官方对兼容性的在意程度。

## 常见问题与排查

**`jq: error: upcase/0 is not defined`** —— jq 没有这个函数，用 `ascii_upcase` / `ascii_downcase`（只转换 a-z 与 A-Z）。同理 `trim`、`ltrim`、`rtrim`、`trimstr` 都是 1.8+ 才有，旧版先升级或用 `gsub("^\\s+|\\s+$"; "")` 替代。

**`jq: error (at <stdin>:1): Cannot index string with string "name"`** —— 过滤器假设输入是对象，实际来的是字符串。先用 `jq 'type'` 看输入类型；上游不可控时用 `select(type == "object")` 防御性过滤。

**`jq: error: module not found: mylib`** —— 模块搜索路径没对上。默认只搜 `~/.jq` 这一层，子目录不算数；用 `-L` 把模块目录显式加进搜索路径。

**`parse error: Invalid numeric literal`** —— 输入根本不是 JSON。最常见两种成因：curl 少了 `-sL`，跟着重定向落到了 HTML 登录页；或者日志文件里混进了非 JSON 行。逐文档处理时，坏行会让 jq 在那一行报错退出，先定位坏行再决定跳过策略。

**过滤器里的单引号和 shell 打架** —— 过滤器整体用单引号包，内部字符串用双引号，多数情况够用；真需要单引号嵌套时别和 shell 较劲，把过滤器存成 `.jq` 文件用 `-f` 加载，还顺便可维护。

**大文件把内存吃满了** —— jq 把整个 JSON 文档解析进内存再处理，内存占用与文件大小同量级。超大文件先分片或抽样；顺带知道一个上限：CVE-2024-23337 修复后（1.8.0 起），单个数组或对象最多 536,870,912（2^29）个元素。

**脚本里 jq "成功"了但字段是空的** —— jq 对缺失字段返回 `null` 且退出码为 0，静默吞掉问题。脚本化时配 `-e` 用退出码说话，或在过滤器里对关键路径用 `// error("missing")` 显式失败。

## 与其他工具的分工

需要处理 YAML 时会撞上两个同名的 yq，分工不同：[mikefarah/yq](https://github.com/mikefarah/yq) 是 Go 写的独立实现，用 jq 风格语法处理 YAML、JSON、INI、XML、CSV 等（官方说明"尚不支持 jq 的全部能力"）；[kislyuk/yq](https://github.com/kislyuk/yq) 则是 jq 的包装器，把 YAML/XML/TOML 转成 JSON 后交给 jq 处理，pip 安装、依赖 jq 本尊。纯 JSON 场景没有理由绕道 yq；YAML 场景按团队语言偏好二选一。

| 任务 | 首选 |
|------|------|
| curl 响应提字段、调试 API | jq |
| JSON Lines 日志过滤与统计 | jq + sort/uniq |
| YAML/XML 配置处理 | yq（两个实现按需选） |
| 只是想美化看看 | `python -m json.tool`（只做格式化，不能提取变换） |
| 多文件、带校验的固定流程 | Python 等脚本语言 |

界线画在复杂度上：过滤器超过几十行、需要 schema 校验或错误恢复逻辑时，jq 的单表达式风格就开始透支可读性，这时候是脚本语言的主场。

## 适用边界与采用顺序

jq 的主场：shell 管道里的 JSON 手术——curl 后处理、CI 脚本断言、日志抽样统计、配置读取。这些场景的共同点是"一次性、组合式、在管道里"，正是单二进制零依赖的用武之地。

可以缓一缓的场景：超大规模 ETL（内存模型不合适）、需要严格 schema 校验的入口（jq 是查询语言，校验交给 jsonschema 类工具）、以及团队里没人愿意维护长过滤器的地方。

上手顺序按依赖关系排：

1. `jq '.'` 调试 curl，感受格式化与流输出
2. 路径访问、切片、`.[]` 展开——覆盖八成日常
3. `select`、`map`、`sort_by`、`group_by`，开始做数据手术
4. `-r`、`-c`、`--arg`、`-e`，把过滤器嵌进脚本
5. `def` 与模块，沉淀团队自己的过滤器库

## 总评

jq 的交易结构很简单：学一门只有几十个原语的小语言，换回在管道里处理任意 JSON 的能力。14 年过去，它靠"单二进制、零依赖、一次学会到处能用"守住了位置——2026 年的 1.8.x 线补上了安全欠账、理顺了版本号、给发布产物加了 attestation，项目没有任何老龄化的迹象。只要 shell 还在，JSON 的 sed 就是它。

## 参考资源

- 仓库：[https://github.com/jqlang/jq](https://github.com/jqlang/jq)
- 官方文档：[https://jqlang.org/](https://jqlang.org/)（手册 [https://jqlang.org/manual/](https://jqlang.org/manual/)、教程 [https://jqlang.org/tutorial/](https://jqlang.org/tutorial/)）
- 在线练习：[https://play.jqlang.org](https://play.jqlang.org)
- 发布页（含各平台预编译二进制）：[https://github.com/jqlang/jq/releases](https://github.com/jqlang/jq/releases)
- 问答社区：[https://stackoverflow.com/questions/tagged/jq](https://stackoverflow.com/questions/tagged/jq)
- Discord：[https://discord.gg/yg6yjNmgAC](https://discord.gg/yg6yjNmgAC)
- Wiki（跨平台编译等进阶话题）：[https://github.com/jqlang/jq/wiki](https://github.com/jqlang/jq/wiki)

版本与生态数据截至 2026-09-07：Stars、Forks、贡献者与提交数取自 GitHub API；版本号、发布日期与 CVE 内容出自 GitHub Releases 原文；函数版本边界（`ascii_upcase` 全版本、`trim` 系 1.8+、`upcase` 不存在）经 jq 1.7.1/1.8.0 源码 `builtin.c` 与 `builtin.jq` 交叉验证，文中示例与输出在 jq 1.7.1 与 1.8.2 下实测。查最新版本看 GitHub Releases 页。
