---
title: "DNSGen 读码笔记：八个变形器、两条版本线，和一处会让候选全部作废的种子写法"
date: "2026-04-14T22:20:00+08:00"
lastmod: "2026-09-21T22:40:00+08:00"
slug: "dnsgen-dns-permutation"
github_repo: "AlephNullSK/dnsgen"
source_key: "gh:AlephNullSK/dnsgen"
description: "逐条核对 AlephNullSK/dnsgen：master 上的 2.0.3 与 PyPI 上的 1.0.4 是两套不同的变形器组合；八个变形器里只有一个读词表，-l 在 2.0 已不影响输出；拿顶级域当种子时产出的候选全部带非法标签。结论都附可重跑的命令与本机实跑输出。"
draft: false
categories: ["技术笔记"]
tags: ["安全", "BugBounty", "DNS", "渗透测试"]
---

> **目标读者**：已经在用 Findomain 或 subfinder 收子域名、想把"变形生成"这一环接进流水线，或者干脆想自己写一个的人。你不需要读过 dnsgen 的源码，但需要知道子域名枚举大致有哪几步。
>
> **本文口径**：核对对象是 `AlephNullSK/dnsgen` 的 `master` 分支 HEAD `7c98e7e`（最后一次提交 2025-01-03），以及 PyPI 上的 `dnsgen 1.0.4`。文件行数、参数行为、候选条数全部来自本机实跑：macOS arm64、Python 3.11.16，两个版本各装一份独立虚拟环境。所有"某参数有没有用"的判断都用输出内容的哈希或条数比对定案，不靠读文档推。星标数与推送时间是 2026-09-21 的快照。

## 目录

- [一句话判断](#一句话判断)
- [项目坐标](#项目坐标)
- [先分清两条版本线](#先分清两条版本线)
- [八个变形器各自读什么](#八个变形器各自读什么)
- [三个开关各自管到哪](#三个开关各自管到哪)
- [种子形状决定候选质量](#种子形状决定候选质量)
- [输出去哪儿](#输出去哪儿)
- [一次任务怎么流过整条流水线](#一次任务怎么流过整条流水线)
- [候选量与耗时测的是什么](#候选量与耗时测的是什么)
- [与 altdns 怎么分工](#与-altdns-怎么分工)
- [跑不通时的几类现象](#跑不通时的几类现象)
- [谁该用谁不必用](#谁该用谁不必用)
- [五道自测题](#五道自测题)
- [下一步读什么](#下一步读什么)
- [参考资料](#参考资料)
- [复核口径与失效条件](#复核口径与失效条件)

## 一句话判断

dnsgen 值得读的地方不是"八种变形技术"，而是它把"变形生成"这个环节压到了一个数据类和八个注册函数里。`dnsgen/dnsgen.py` 全文 361 行，八个函数各自往一个列表上追加字符串，没有解析、没有并发、没有网络。读完你能拿到一个具体答案——子域名变形的候选量到底由什么决定。

要用它，得先对准三件文档没讲清的事。第一，`pip install dnsgen` 装到的是 2020 年的 1.0.4，而 README 描述的是仓库里的 2.0.3，两者注册的变形器完全不同。第二，2.0.3 的八个变形器里只有一个读词表，`-l` 这个参数对输出已经没有任何影响。第三，种子列表里如果混进顶级域（`example.com` 这种），它产出的候选百分之百带非法标签，而且不报错。

这三件事都不影响"读懂它"，但每一条都会影响"抄命令"。本文按这个顺序展开：先讲清版本线和八个变形器的分工，再给实测的开关作用域与种子陷阱，最后是流水线和取舍。

## 项目坐标

| 项 | 值 | 怎么来的 |
|------|------|------|
| 仓库 | `AlephNullSK/dnsgen`，旧地址 `ProjectAnte/dnsgen` 会重定向过来 | 查一次仓库的应用程序接口（API）：`gh api repos/ProjectAnte/dnsgen` 返回 `full_name: AlephNullSK/dnsgen` |
| 语言 / 许可证 | Python / MIT | 仓库 `LICENSE` |
| 星标 / 派生仓库 / 未关闭议题 | 1,080 / 131 / 14 | 同一次接口查询，2026-09-21 快照 |
| 分支与历史 | `master`，23 个提交，作者集中在 Patrik Hudak，最早提交 2019-09-24 | `git rev-list --count HEAD`、`git log --format='%an %ad'` |
| 最后一次提交 | 2025-01-03，内容是一次代码检查（静态分析），提交说明只写了 `Linting` 一个词 | `git log -1` |
| 标签 | 只有 `v1.0.0`、`v1.0.1`、`v1.0.4`，没有 2.x | `git tag` |
| PyPI 最新版 | 1.0.4，2020-03-04 上传 | `https://pypi.org/pypi/dnsgen/json` |
| 仓库内版本号 | `2.0.3`（`pyproject.toml`） | 未发布、未打标签 |
| 运行依赖 | `click>=8.1.8`、`rich>=13.9.4`、`tldextract>=5.1.3` | `pyproject.toml` |
| Python 要求 | 仓库 `requires-python = ">=3.9"`；PyPI 1.0.4 的元数据写 `>=3.6.0` | 两份元数据 |
| 代码规模 | `dnsgen.py`（库核心）361 行、`cli.py`（命令行工具）176 行、`__init__.py` 93 行、`words.txt` 380 行 | `wc -l` |
| 自带测试 | 21 个用例，在源码目录里全部通过 | `python -m pytest -q` |
| README 指向的 `CONTRIBUTING.md` 与 `docs/` | 仓库里都不存在 | `git ls-files` |

一个容易被略过的事实：README 里那句"Original concept by Aleph Null s.r.o."和 PyPI 上的作者名 `Patrik Hudak` 是同一条线。这个仓库不是谁派生出来的副本，它就是原项目本身，只是换了两次组织名（ProjectAnte → AlephNullSK），而 PyPI 账号停在 2020 年。

## 先分清两条版本线

1.0.4 和 2.0.3 不是"功能多一点少一点"的关系，是两套变形器：

| 维度 | PyPI 1.0.4（2020-03） | 仓库 master 2.0.3（2025-01） |
|------|------|------|
| 变形器数量 | 6 个 | 8 个 |
| 变形器名单 | `insert_word_every_index`、`increase_num_found`、`decrease_num_found`、`prepend_word_every_index`、`append_word_every_index`、`replace_word_with_word` | 见下一节表，含环境、区域、云服务、微服务、内部工具五类硬编码模式 |
| 快速模式跑哪几个 | 3 个（增数、减数、词替换） | 2 个（改数字、加端口） |
| `-l/--wordlen` | 有效：`generate()` 里会把从种子提取的词并进词典 | 无效：`extract_custom_words()` 还在，但没有任何地方调用它 |
| 词表注释行 | 不过滤，`# 开头` 会被当成一个词 | 过滤，`create_generator()` 显式剔除 `#` 行与空行 |
| 顶级域切分 | `[p for p in parts if p]` 会丢掉空片段 | 不过滤，空片段留在列表里（见「种子形状」一节） |
| `-o/--output`、`-v/--verbose` | 没有 | 有 |
| 日志 | 不写日志 | 往 stdout 写 4 行日志与进度符 |
| 安装后可用性 | `pip install dnsgen` 直接可用 | 从源码构建的 wheel 里 `dnsgen` 命令起不来 |

最后一行需要单独说清楚，因为它会决定你怎么跑 2.0.3。`pyproject.toml` 里这两段：

```toml
[tool.hatch.build.targets.wheel]
only-include = ["dnsgen/"]

[tool.hatch.build.targets.wheel.sources]
"dnsgen" = ""
```

`sources` 把 `dnsgen/` 目录映射到 wheel 根，于是构建出来的包里没有 `dnsgen/` 这一层：`dnsgen.py`、`cli.py`、`__init__.py`、`words.txt` 四个文件平铺在 `site-packages` 顶层。`RECORD` 里能直接看到这一点。后果是入口点 `dnsgen = "dnsgen.cli:main"` 找不到模块：

```console
$ dnsgen --help
ModuleNotFoundError: No module named 'dnsgen.cli'; 'dnsgen' is not a package
```

`from dnsgen import DomainGenerator` 反而能成功（命中的是顶层那个 `dnsgen.py`），`from dnsgen import generate` 失败（那个函数写在被平铺出去的 `__init__.py` 里）。所以本机验证 2.0.3 用的是源码目录加 `PYTHONPATH`：

```bash
git clone https://github.com/AlephNullSK/dnsgen && cd dnsgen
uv venv --python 3.11 /tmp/dnv && uv pip install --python /tmp/dnv/bin/python .
PYTHONPATH=$PWD /tmp/dnv/bin/python -m dnsgen.cli --help
```

这么跑出来的一切就是 2.0.3 的真实行为，只是它不走那个坏掉的入口脚本。

## 八个变形器各自读什么

`create_generator()` 里用 `@generator.register_permutator()` 注册了八个函数。八个函数的分工差异只有一处，就是**语料从哪来**：只有一个用词表，其余七个各自带一份硬编码的小列表。

下面是本机对单个种子 `api.example.com` 逐个函数调用的结果（词表用默认的 `dnsgen/words.txt`，实际词数 342，分 20 个注释组）：

| 注册顺序 | 函数 | 词从哪来 | 读词表 | 进快速模式 | 该种子产出条数 |
|------|------|------|------|------|------|
| 1 | `insert_word_every_index` | 词表 × 域名层级数 | 是 | 否 | 684 |
| 2 | `modify_numbers` | 种子里的数字 | 否 | 是 | 0 |
| 3 | `environment_prefix` | `dev/staging/uat/prod/test` | 否 | 否 | 5 |
| 4 | `cloud_provider_additions` | 5 个云词 × 5 个服务词 | 否 | 否 | 25 |
| 5 | `region_prefixes` | 8 个区域名 | 否 | 否 | 8 |
| 6 | `microservice_patterns` | 6 个服务名 × 4 个后缀 | 否 | 否 | 24 |
| 7 | `internal_tooling` | 7 个工具名 × 3 个前缀 × 2 种顺序 | 否 | 否 | 42 |
| 8 | `common_ports` | 6 个端口 × 2 种写法 | 否 | 是 | 12 |

八个函数合计吐出 800 条，CLI 用一个 `set()` 去重、`sorted()` 排序后剩 747 条。也就是说：**747 条里有 684 条来自第一个函数，词表决定 92% 的产出**；剩下 7 个函数加起来只有 116 条（有数字的种子另算）。这个比例决定了后面几节的所有取舍。

几个具体行为，都实测过：

- `insert_word_every_index` 的循环是 `for i in range(len(parts))`，所以插入位置数 = 层级数（含根域那一段）。`api.example.com` 切两段 → 342 × 2 = 684；`a.b.api.example.com` 切四段 → 1368。词表越长产出线性放大，别的七个函数纹丝不动。
- `modify_numbers` 不是"±1"。它对每个匹配到的数字串做 `+1..+3` 和 `-1..-3`，负数跳过，`zfill` 保持原宽度。单独调用这个函数跑 `api2.example.com`，产出是 `api0 / api1 / api3 / api4 / api5` 五条。匹配用的是 `\d{1,3}`，超过三位的数字串只能吃到前缀。
- `internal_tooling` 两种顺序都产：`internal.jenkins.example.com` 和 `jenkins.internal.example.com` 都在输出里。但裸的 `jenkins.example.com` 一个也拿不到——八个函数没有一个会丢掉种子里已有的标签，输出层级永远不少于输入（实测单种子 747 条里，层级少于种子的是 0 条）。想直接枚举 `jenkins.example.com` 这类两层名字，得靠字典，不是靠变形。
- `common_ports` 每个端口产两条：`8080.api.example.com` 和 `port-8080.api.example.com`。
- README 的 "Word Affixing" 一节声称会产出 `devapi.example.com`、`api-dev.example.com`。**2.0.3 里没有对应的函数**，这两类字符串在 747 条输出里一条都没有（`prepend_word_every_index` 和 `append_word_every_index` 是 1.0.4 的实现）。同理，README 给 `cloud_provider_additions` 举的例子是 `example.com → api-aws.example.com`，而真实输出是 `api-aws..example.com`，原因见下一节。

## 三个开关各自管到哪

`--help` 给的东西很规整，实际作用域差很多。下表最后一列是判据——两种跑法比对输出哈希或条数。

| 开关 | 声称 | 2.0.3 实测 | 1.0.4 实测 | 判据 |
|------|------|------|------|------|
| `-w PATH` | 自定义词表 | 整表**替换**默认词表，且只对第一个函数有效 | 替换，且注释行会被当词 | 默认词表下 `canary` 出现在 4 条里；换成两词的表后 `canary` 归零、自定义词出现 8 次 |
| `-l N` | 从域名提取词的最小长度 | 对输出零影响 | 有效 | `-l 2` 与 `-l 100` 输出哈希相同；1.0.4 同一种子 `-l 2` 得 1175 条、`-l 90` 得 1002 条 |
| `-f` | 快速模式，产出更少 | 只跑改数字与端口两类，词表完全不参与 | 词表截到前 10 行，跑三个函数 | `-f` 与 `-f -w custom.txt` 输出哈希相同 |
| `-o PATH` | 写文件 | 有效，且文件里没有日志 | 选项不存在 | `dnsgen -o out.txt`：`wc -l` 1495，`grep -c INFO` 0 |
| `-v` | 详细日志 | 无可见变化 | 选项不存在 | 加与不加都是同样 4 行 |

`-l` 的失效不是猜测。`DomainGenerator.generate()` 收了 `wordlen` 参数，函数体里除了文档字符串再没有第二处引用它；`extract_custom_words()` 原样留在类上，只有 `tests/test_dnsgen.py` 在调。1.0.4 的模块级 `generate()` 里有这么一行，2.0.3 搬走类的时候把它丢了：

```python
WORDS = list(set(WORDS).union(extract_custom_words(domains, wordlen)))
```

1.0.4 README 里那句 "Custom words are extracted per execution" 说的就是这行代码。2.0 README 里的 "Intelligent word extraction from existing domains" 也只由它支撑，而在 2.0.3 上它不再发生。于是 2.0.3 的定位反而更单纯：**它是一个纯模式展开器，唯一可调的语料是词表，而词表只喂给一个函数。**

`-f` 值得单独说一句。既然只有一个函数读词表，快速模式又恰好不含这个函数，那 `-f` 的真实含义是"放弃所有词表驱动的候选，只保留数字变体和端口变体"。对无数字的种子，一个种子 12 条。想要"少产一点但仍然覆盖各语义词"的效果，`-f` 给不了。

## 种子形状决定候选质量

dnsgen 不做域名合法性校验，切分完全交给 `tldextract`。2.0.3 的切分函数：

```python
ext: ExtractResult = tldextract.extract(domain.lower())
parts: DomainPartsType = ext.subdomain.split(".") + [ext.registered_domain]
```

问题出在 `"".split(".")` 得到的是 `[""]` 而不是 `[]`。种子只有一层根域时，`parts` 变成 `['', 'example.com']`，而 2.0.3 没有 1.0.4 那句 `[p for p in parts if p]`。空片段会一路参与 `join`，产出带空标签的名字。

本机对三种种子的全部产出做了分类（2.0.3，默认词表）：

| 种子 | 候选条数 | 含 `..` | 以 `.` 开头 | 合法 hostname |
|------|------|------|------|------|
| `example.com` | 748 | 379 | 369 | **0** |
| `api.example.com` | 747 | 0 | 0 | 747 |
| `a.b.example.com` | 1075 | 0 | 0 | 1075 |

379 条含 `..`、369 条以 `.` 开头，两种形态正好覆盖全部 748 条，合法 hostname 为 0。这类种子交进去，massdns 只会白跑一趟，而且工具不会给你任何提示。

同一批种子在 1.0.4 上：`example.com` 得 167 条，全部合法；`api.example.com` 得 1002 条。

非域名输入也是同样的静默行为。喂 `localhost`、`not a domain` 进去，`registered_domain` 为空，产出形如 `.acme.`、`.admin.gitlab.` 的字符串，748 条，一条不报。反过来说，`API.Example.COM` 会被 `lower()` 正常处理，`api.example.com.`（带尾点）和 `https://api.example.com/path` 也都能进——只是后者会拆出 `.https.` 这种垃圾标签。

实践上三条就够用：

1. 种子列表里只留至少带一层子域的名字。用 `grep -E '^[^.]+(\.[^.]+){2,}$'` 先筛一遍。
2. 只有 apex 时别指望它，那部分交给字典暴力枚举更划算。
3. 生成后再过一道形状过滤，`grep -E '^[A-Za-z0-9._-]+$'` 这一条式子同时能去掉 2.0.3 的日志行。

还有一点：不校验标签长度。喂一个 70 字符标签的种子，输出里那 70 字符标签原样保留（DNS 单个标签上限 63）。常规种子碰不到这个，但批量拼接时值得防一手。

## 输出去哪儿

`cli.py` 用 `logging.basicConfig(handlers=[RichHandler(...)])` 配置日志记录，而 `RichHandler` 默认写 stdout。于是这几行进了标准输出而不是 stderr：

```console
[09/21/26 04:43:03] INFO     Read 2 domains from input file           cli.py:161
                    INFO     Generator initialized successfully        cli.py:46
⠋ Generating domain variations...
                    INFO     Generated 1495 unique domain variations  cli.py:171
```

后果很实际：README 里 `dnsgen hosts.txt > wordlist.txt` 和 `cat domains.txt | dnsgen - | massdns ...` 两条命令，产出的流里都混着这 4 行。`2>/dev/null` 摘不掉它们，因为本来就没走 stderr。实测两个种子 `wc -l` 得 1499，域名 1495。

绕开的办法按干净程度排：

```bash
# 1. 最省事：用 -o 落文件，文件里只有域名
dnsgen -o mutated.txt seeds.txt 2>/dev/null

# 2. 必须走管道时，按字符集滤掉日志与进度符
PYTHONPATH=$PWD python -m dnsgen.cli seeds.txt 2>/dev/null \
  | grep -E '^[A-Za-z0-9._-]+$' \
  | massdns -r resolvers.txt -t A -o S -w resolved.txt

# 3. 换回 PyPI 的 1.0.4：它不写日志，管道天然干净
dnsgen seeds.txt | massdns -r resolvers.txt -t A -o S -w resolved.txt
```

1.0.4 的代价是没有 `-o`，也只能用 stdout。`-` 表示读标准输入这点两版都支持（`click.File` 的约定），`cat seeds.txt | dnsgen -` 可用。顺带说一句，这个 2020 年的包并不腐：本机 Python 3.11 加 tldextract 5.3.2 下开箱能跑。

## 一次任务怎么流过整条流水线

这条链路的中间那步是 2026-09-21 在本机实跑的，目标用文档里常见的 `example.com`，规模刻意小，为的是每一步的输入输出都能对上号。两头两条命令没有在本机执行——这两个工具本机没装——参数取自各自仓库：Findomain 的 `src/cli.rs`，massdns `README.md` 里的 help 段。

第一步，被动收集。Findomain 是 Rust 写的收集器（GPL-3.0，3,794 星标，最近推送 2026-09-17）。`-t` 指定目标，`-u` 指定输出文件名。这里有个常见踩点：`-o` 在 Findomain 里是布尔开关，含义是"按目标名自动起文件名"，在它后面直接跟文件名是错的。

```bash
findomain -t example.com -u passive.txt --resolved
```

第二步，变形。把上一步的产物原样喂进去，种子必须已经带子域层级：

```bash
wc -l passive.txt                       # 上一步的产物，每行一个已知子域名
grep -E '^[^.]+(\.[^.]+){2,}$' passive.txt > seeds.txt
PYTHONPATH=$PWD python -m dnsgen.cli -o mutated.txt seeds.txt 2>/dev/null
```

第三步，解析。massdns 是 C 写的批量解析器（GPL-3.0，3,645 星标），`-t A` 是默认值，`-o S` 要简单文本格式，`-w` 指定输出文件。

```bash
massdns -r resolvers.txt -t A -o S -w resolved.txt mutated.txt
```

中间那步跳过会怎样？被动收集里最大的一路是证书透明度日志，`staging.api.example.com`、`grafana.internal.example.com` 这种没上过公网证书的名字不会出现在那批结果里。本机一个种子 `api.example.com` 展开成 747 条，两个种子 1495 条；下一节那张表给出的是 50 个种子的规模。这条流水线的宽度由种子数与域名层级数一起决定，第二步进去多少条，第三步就要付多少网络往返。

流水线里真正需要人判断的是两件事，工具都不替你做：

- **泛解析**。目标如果配了 `*.example.com`，所有候选都会解析成功，变形命中变成全命中。开跑前先 dig 一个不可能存在的名字，有答复就先别信这批结果。
- **验收口径**。"候选条数"不是成果，解析后去掉泛解析才是。变形环节唯一可靠的量化指标是"这一步多出来多少条待查名字"。

## 候选量与耗时测的是什么

同一份 50 行的种子（每行两级子域，形如 `svc01.internal.example.com`），四种跑法各测五次取最好值：

| 跑法 | 候选条数 | 命令墙钟 | 扣掉导入后的净展开 |
|------|------|------|------|
| 2.0.3 默认 | 53,758 | 272 ms | 约 172 ms |
| 2.0.3 `-f` | 658 | 143 ms | 约 43 ms |
| 1.0.4 默认 | 100,447 | 358 ms | 约 272 ms |
| 1.0.4 `-f` | 797 | 103 ms | 约 17 ms |

第三列是进程从启动到退出的时间，第四列减掉的是一个固定开销：光 `import dnsgen.cli` 就要 100 ms（2.0.3）或 86 ms（1.0.4），大头在 tldextract 加载公后缀列表，Python 解释器本身只占 15 ms。两列并排看就清楚了，快速模式那 143 ms 里六成是启动，真正展开只用了 43 ms。

这组数字测的是单机纯字符串展开：不含网络、不含解析、不写临时文件。从它能推出两件事——候选量由"种子数 × 层级数 × 词表长度"三个因子相乘决定；以及 1.0.4 在这批输入上展开得更宽，它的六个函数里有四个由词表驱动，其中 `prepend_word_every_index` 与 `append_word_every_index` 各自还要再乘上带连字符与不带连字符两种拼法。

从它推不出端到端耗时。生成阶段是百毫秒级，整条流水线的时间压在解析那一步，而解析走网络，本文没有测。两个版本之间不到 100 ms 的差值，放进任何真实的 massdns 跑批里都看不见，所以别用这张表下"1.0.4 比 2.0.3 慢"的结论：条数不同，比时间没有意义。真要比较，得比"同样解析 N 条候选，谁多命中几个真实子域"，那需要真实目标和真实解析。

要控量，能动的只有词表规模和种子形状这两样，换实现解决不了这件事。

## 与 altdns 怎么分工

同类工具里最常被拿来做对照的是 altdns（`infosec-au/altdns`，Apache-2.0，2,509 星标，最近推送 2025-01-09）。先纠正一个流传相当广的说法：**它是 Python，不是 Go**。PyPI 包名 `py-altdns`，`setup.py` 里版本号 1.0.2，作者 Shubham Shah，全部实现是一个 13,816 字节的 `altdns/__main__.py`。"编译二进制部署"这个卖点不存在。

真正的差别在结构和职责边界上：

| 维度 | dnsgen 2.0.3 | altdns 1.0.2 |
|------|------|------|
| 语言 / 体积 | Python，三个 `.py` 文件共 630 行 | Python，单文件 13,816 字节 |
| 变形模式 | 词表插入 + 五类硬编码语义模式（环境、云、区域、微服务、内部工具）+ 数字 + 端口 | 词表插入、连字符拼接、词与词拼接，数字后缀要加 `-n` 才跑 |
| 词表处理 | 过滤 `#` 与空行，342 词分 20 组 | `readlines()` 直接读，自带词表 232 行且以数字开头 |
| 输入扫描 | 每个种子一次遍历，八个函数在其上叠加 | 每个函数各自重读整个输入文件 |
| 是否解析 | 不解析 | 内置多线程解析（dnspython），`-r` 开启，`-t` 控线程数，`-d` 指定 DNS 服务器 |
| 去重 | CLI 层 `set()` + 排序 | 生成后走 `remove_duplicates`，可选 `-e` 去掉已存在的 |
| 输出 | stdout 或 `-o` | 必须 `-o` 指定中间文件 |

dnsgen 的语义模式是 altdns 没有的：后者所有候选都由"词表 × 层级"这一维展开，你要 `us-east` 或 `grafana` 就得自己写进词表。dnsgen 把这批词硬编码进了函数体——好处是开箱就有方向性，坏处是你改不了，除非动源码（而那只有 361 行，改起来不算过分）。

altdns 的"自带解析"在大规模场景确实省一件事，代价是它的解析走 dnspython，吞吐和 massdns 不在一个量级；而 dnsgen 天生就是把解析外包给 massdns 的分工。把 dnsgen 归成"简单版"、把 altdns 归成"性能版"的流传分法，方向恰好是反的：把解析外包给 massdns 的那条路才是吞吐上限更高的那条。

## 跑不通时的几类现象

这一节按现象排查。最常见的是前两类，它们由版本引起，与配置无关；剩下的几类是种子形状或词表用错了，工具一声不响，只能从输出条数和形态反推。错误信号都在条数里，不在退出码里。

**现象 1：`dnsgen --help` 直接报 `ModuleNotFoundError: No module named 'dnsgen.cli'`。**
你装的是从源码构建的 2.0.3 wheel，模块被平铺到了 `site-packages` 顶层。换成 `PYTHONPATH=$PWD python -m dnsgen.cli`，或者干脆用 PyPI 的 1.0.4。

**现象 2：命令行跑通了，但产出和 README 描述的变形对不上。**
先看 `dnsgen --help` 里有没有 `-o`。有就是 2.0.3，没有就是 1.0.4。2.0 的 README 里混着几条只有 1.0.4 才产的变形例子，`devapi.example.com`、`api-dev.example.com` 都在其中。

**现象 3：换了自定义词表，条数几乎没变。**
先看是不是同时带了 `-f`——快速模式不跑词表插入，词表在这个组合下完全不参与。没带 `-f` 的话，检查你的词表规模：默认 342 词时词表贡献占产出的九成以上，换成几十词的表条数一定掉，不掉说明你比对的两个跑法之间还有别的差异。

**现象 4：结果里出现 `#`、空标签或整行注释。**
`#` 说明你在用 1.0.4，它的词表读取不过滤注释行。空标签（`dev..example.com`、`.admin.example.com`）说明种子队列里混进了 apex 或非域名行，回到"种子形状"那节的三条过滤。

**现象 5：变形结果为 0。**
1.0.4 的 `-f` 在 apex 种子上就是这个行为——快速注册表里那三个函数都不处理"没有子域层级"的输入。

**现象 6：接 massdns 之后慢。**
massdns 里 `-c` 是 `--resolve-count`（每个名字重试次数，默认 50），不是并发数，调它只会让每个名字多问几遍。真正的旋钮是 `--processes`（进程数，默认 1）和 `-s/--hashmap-size`（同时在飞的查询数，默认 10000）。另外 massdns **没有 `--timeout` 这个选项**，超时相关的参数是 `-i/--interval`（同一名字两次查询的间隔毫秒数）。解析器列表可以从 <https://public-dns.info/nameservers.txt> 取，取完先测可用性再上量。

**现象 7：Findomain 输出文件没生成。**
`-o` 是布尔，要指定文件名用 `-u/--unique-output`。顺带一提 Findomain 自己有 `--permutations` 和 `--permutations-wordlist`：把每个已知标签和词表的词用 `-`、`.`、无连接符三种方式前后拼一遍，再补 trailing 数字递增到 9，且不会返回已知名字或 apex。它跑的是"连接符 × 位置"这一维，和 dnsgen 的语义模式不重叠，两者不是替代关系。

## 谁该用谁不必用

值得用的场景：

- 你已经有一份带子域的种子（CT 日志、被动源、历史扫描都行），想让候选覆盖到环境名、区域名、内部工具名这几类语义模式，又不想自己维护三份词表。
- 你在写自己的枚举脚本，需要一个能整仓读完的参考实现。八个函数、361 行、无网络，改起来没有心理负担。
- 流水线里已经有 massdns，只缺生成这一环。

不必用的场景：

- 只有 apex、手上没有任何已知子域。2.0.3 在这种情况下产 0 条合法候选，1.0.4 产的那 167 条也只覆盖词表插入一维。这时候先去做字典暴力枚举更划算。
- 想要"从目标的命名习惯里自动学词"。这个能力在 1.0.4 里是有效的，在 2.0.3 里是断的；要它就得回退版本，或者把 `extract_custom_words()` 重新接回 `generate()`——两行代码的事，但那是你自己在维护的分支。
- 指望它替你解析或去重。它两样都不做。

如果只能记一条采用顺序：先用被动源拿到一批**带子域**的种子，用默认词表跑 2.0.3 的全模式，`-o` 落文件，再交给 massdns。词表和 `-f` 是控制量的手段，不是提升命中的手段。

## 五道自测题

1. 同一个仓库，为什么 `dnsgen -o out.txt` 会报"没有这个选项"？
2. 八个变形器里哪个读词表？由此能推出 `-f` 的实际语义是什么？
3. 为什么 `-l` 在 2.0.3 上不影响输出，在 1.0.4 上影响？
4. 种子列表里混进 `example.com` 会怎样？怎么防？
5. 想加速整条枚举流水线，`-c 200` 这种改法对吗？正确的旋钮是什么？

答案都在正文里，这里只给定位：一是版本，PyPI 停在 1.0.4；二是第一个函数，`-f` 恰好把它排除在外，所以快速模式等价于"只改数字和加端口"；三是 2.0.3 搬类时丢了 `WORDS = list(set(WORDS).union(extract_custom_words(...)))` 这一行；四是 748 条候选全部非法且不报错，靠"只保留至少两层点分片"过滤；五是不对，`-c` 是每个名字的重试次数，该动的是 `--processes` 和 `-s`。

## 下一步读什么

按这个顺序读，每步都能边读边跑：

1. `dnsgen/dnsgen.py` 的 `create_generator()`：八个函数全在里面，注意每个函数怎么取 `parts[:-1]`、又怎么 `insert(0, ...)`。这是本文那张表的出处。
2. `partiate_domain()` 与 `tldextract`：一个 `"".split(".")` 的边界情况，代价是 apex 种子 748 条全废，值得对照 1.0.4 的同名函数看它多出来的那行 `[p for p in parts if p]`。
3. `dnsgen/cli.py` 的 `write_output()`：为什么 `-o` 比 shell 重定向干净，答案在 `logging.basicConfig` 那几行。
4. `tests/test_dnsgen.py`：21 个用例都在断言什么，尤其 `test_fast_mode_generation` 只断言"条数更少"而不关心少了什么——这解释了为什么快速模式的语义漂移没人拦住。
5. `git show v1.0.4:dnsgen/dnsgen.py`：模块级 `generate()` 那不到 30 行，是"从目标命名习惯学词"这个思路的最小实现。
6. 想看完带解析的版本，读 `altdns/__main__.py`：四个生成函数各自重读输入文件的写法，和它的数据结构放在一起看更有收获。

## 参考资料

- 仓库：<https://github.com/AlephNullSK/dnsgen>（`master`，HEAD `7c98e7e`，MIT）
- 旧地址：<https://github.com/ProjectAnte/dnsgen>（重定向到上面）
- PyPI 元数据：<https://pypi.org/pypi/dnsgen/json>（latest 1.0.4，2020-03-04）
- 1.0.4 的 README（变形器名单与"输入可用 `-`"的说明）：`git show v1.0.4:README.md`
- altdns：<https://github.com/infosec-au/altdns>（Python，Apache-2.0）
- massdns：<https://github.com/blechschmidt/massdns>（C，GPL-3.0），参数表来自其 `README.md` 的 help 段
- Findomain：<https://github.com/Findomain/Findomain>（Rust，GPL-3.0），内置变形见 `src/permutations.rs`
- 解析器列表：<https://public-dns.info/nameservers.txt>
- 证书透明度查询：<https://crt.sh>
- 原始方法论文章（作者博客）：<https://0xpatrik.com/subdomain-enumeration-2019/>

## 复核口径与失效条件

本文的每条断言都能在下面这段里重跑出来。需要两个虚拟环境，一份装 PyPI 的 1.0.4，一份从源码装 2.0.3：

```bash
git clone https://github.com/AlephNullSK/dnsgen && cd dnsgen
git log -1 --format='%h %ci'          # 期望 7c98e7e，2025-01-03
git tag                               # v1.0.0 v1.0.1 v1.0.4，没有 2.x
grep -n 'version' pyproject.toml | head -1     # 2.0.3
grep -n 'sources' -A1 pyproject.toml | head -4 # "dnsgen" = ""

uv venv --python 3.11 /tmp/dnv && uv pip install --python /tmp/dnv/bin/python . pytest
uv venv --python 3.11 /tmp/dnv1 && uv pip install --python /tmp/dnv1/bin/python "dnsgen==1.0.4"
/tmp/dnv/bin/dnsgen --help            # 预期 ModuleNotFoundError: No module named 'dnsgen.cli'
PYTHONPATH=$PWD /tmp/dnv/bin/python -m pytest -q   # 21 passed
```

变形条数、去重数与非法标签分类来自同一个探针：把仓库根目录放进 `PYTHONPATH`，`create_generator()` 之后逐个调用 `generator.permutators` 里的函数计长度，再和 `len(set(generator.generate([seed])))` 对账。开关作用域的判据是输出哈希比对：

```bash
printf 'api.example.com\n' > s1.txt; printf 'example.com\n' > apex.txt
printf 'onlyword\nsecondword\n' > custom.txt
V() { PYTHONPATH=$PWD /tmp/dnv/bin/python -m dnsgen.cli "$@" 2>/dev/null | grep -E '^[A-Za-z0-9._-]+$'; }
V s1.txt | wc -l                              # 747
V -f s1.txt | wc -l                           # 12
V -l 2 s1.txt | cksum; V -l 100 s1.txt | cksum        # 两个值相同
V -f -w custom.txt s1.txt | cksum; V -f s1.txt | cksum  # 两个值相同
V apex.txt | grep -c '\.\.'                   # 379，且合法 hostname 为 0
```

四个位置最可能随上游变化，重看本文时先查它们：PyPI 是否补上 2.x（一旦补上，"两条版本线"一节的对照表要重写）；`generate()` 是否重新调用 `extract_custom_words()`（那 `-l` 就恢复有效）；`partiate_domain()` 是否加上空片段过滤（那 apex 种子不再产废候选）；`logging` handler 是否改到 stderr（那 `-o` 的必要性下降）。星标数、派生仓库数和最近推送时间只是 2026-09-21 的快照，不作为论据使用。
