---
title: "frawk 解读：把 AWK 换成静态类型表示之后，快在哪里、又在哪里不成立"
date: "2026-05-11T09:00:00+08:00"
slug: "frawk-efficient-awk-language"
github_repo: "ezrosent/frawk"
source_key: "gh:ezrosent/frawk"
description: "带着仓库源码和一台 Apple Silicon 机器实测 ezrosent/frawk：核对它的 CSV 引号解析、SSA 与单向类型推导、记录级并行聚合语义，以及官方 benchmark 数字能支撑到哪一步。"
draft: false
lastmod: "2026-09-21T06:00:00+08:00"
categories: ["技术笔记"]
tags: ["Rust", "编译器", "AWK", "CSV", "性能分析"]
hiddenFromHomePage: true
---

frawk 常被介绍成"用 Rust 写的高性能 AWK"。这个说法把因果讲反了。

作者 Eli Rosenthal 在 `info/overview.md` 里给出的起点只有两件事：Awk 处理不好带引号转义的 CSV；在大数据文件上性能"sometimes-lackluster"。为了补上这两点，他换掉了 Awk 的运行时表示。标量不再是"字符串和数字并存"的双表示，而是编译期推导出的单一类型。

快是这笔交换的副产品。一批和 Awk 对不上的行为，也是。

下面回答三个问题：这笔交换具体换掉了什么；官方那份性能表格在什么条件下才读得通；到了 2026 年，哪些承诺已经和代码对不上。

## 目录

- [三条主线，别混成一个故事](#三条主线别混成一个故事)
- [CSV 那一行数据去了哪里](#csv-那一行数据去了哪里)
- [编译器管线与三种后端](#编译器管线与三种后端)
- [类型推导为什么不用统一算法](#类型推导为什么不用统一算法)
- [记录级并行与它的聚合语义](#记录级并行与它的聚合语义)
- [一条记录走完 frawk](#一条记录走完-frawk)
- [性能数字该怎么读](#性能数字该怎么读)
- [与邻近工具的分工](#与邻近工具的分工)
- [从 Awk 迁过来会撞上的十件事](#从-awk-迁过来会撞上的十件事)
- [常见故障与排查](#常见故障与排查)
- [谁该用，谁可以再等等](#谁该用谁可以再等等)
- [自测清单](#自测清单)
- [下一步读哪份代码](#下一步读哪份代码)
- [维护与复核指引](#维护与复核指引)
- [参考](#参考)

## 三条主线，别混成一个故事

读 frawk 最容易犯的错，是把"CSV 解析正确"和"跑得快"当成同一件事。它们在三份不同的代码里，失效条件也不同。

| 主线 | 解决什么 | 代码落在哪 | 独立于谁 |
|------|----------|------------|----------|
| 结构化解析 | 带引号、内嵌逗号的字段能被正确切成列 | `src/runtime/splitter/`（4 个文件，`batch.rs` 2406 行） | 与后端无关，解释器模式下同样生效 |
| 静态类型推导 | 消掉每次运算的字符串/数字分派 | `src/dom.rs`（SSA）+ `src/types.rs`（推导，1123 行） | 与解析无关，纯语言层 |
| 记录级并行 | 单个输入文件内部也能并行 | `src/harness.rs`（1578 行，负责分片与聚合） | 依赖前两条的边界：只对 CSV/TSV 等格式开放 |

第三条最容易被忽略，也最容易踩坑：它不是"多线程执行你的脚本"，而是一套会改写脚本语义的模型。后文单独讲。

## CSV 那一行数据去了哪里

标准 Awk 按记录分隔符切行、按字段分隔符切列，中间不认引号。`info/overview.md` 用的例子是一本书记名里带逗号：

```csv
Item,Quantity
Carrot,2
"The Deluge: The Great War, America and the Remaking of the Global Order, 1916-1931",3
Banana,4
```

把上面那四行存成 `books.csv`，`awk -F',' 'NR>1 { SUM+=$2 }'` 的结果就能当场对账。后面每条 frawk 命令都带 `-B interp`，原因见"常见故障与排查"：

```console
$ /usr/bin/awk -F, 'NR>1 { SUM+=$2 } END { print SUM }' books.csv
6
$ frawk -B interp -i csv 'NR>1 { SUM+=$2 } END { print SUM }' books.csv
9
```

9 是 2+3+4。差的 3 来自第三行：`-F,` 把书名从内部劈开，那行的 `$2` 落到 ` America and the Remaking of the Global Order` 上，转成数字是 0。作者的措辞是 "silently coerced to the number 0, thereby contributing nothing to the total"。少算，不报错。

frawk 用 `-i csv` 走一条完全不同的解析路径，`$0` 保留未转义的原始行，`$n` 给出反转义后的第 n 列：

```console
$ frawk -B interp -i csv '{ print NR "|" $0 "|" $1 "|" $2 }' books.csv
1|Item,Quantity|Item|Quantity
2|Carrot,2|Carrot|2
3|"The Deluge: The Great War, America and the Remaking of the Global Order, 1916-1931",3|The Deluge: The Great War, America and the Remaking of the Global Order, 1916-1931|3
4|Banana,4|Banana|4
```

这里有个反直觉的点值得单独记住：`-i csv` 模式下给列赋值不起作用。`$1 = "X"` 之后 `$0` 和 `$1` 都不变——`clap` 的帮助文本里那句 "Assigning to columns does nothing" 就是这件事。要改输出内容，得走 `-o csv` 由 `print` 重新转义。

作者给这条限制补了一句：他没法信任 Awk 去处理一个无法逐行人工核对字段的大 CSV。frawk 的解法不是加一个 CSV 开关，而是把 CSV/TSV 做成语言的一等输入格式。`-i` 与 `-F` 因此互斥，两条解析路径在实现上彻底分开。

## 编译器管线与三种后端

`info/overview.md` 把 frawk 的自我定位写成"a conventional compiler and interpreter"，并列出六步。对着仓库文件把这条链摊开是：

```text
源码
  → src/lexer.rs            手写词法分析（846 行）
  → src/parsing/            LALRPOP 语法文件生成 AST（syntax.lalrpop，488 行）
  → src/ast.rs              AST
  → src/cfg.rs              无类型控制流图（2017 行）
  → src/dom.rs              在 CFG 上做 SSA 转换
  → src/types.rs            给所有变量、数组键、数组值指派类型
  → src/compile.rs          产出带类型的 CFG 与字节码指令
  → src/interp.rs           解释执行
  → src/codegen/clif.rs     Cranelift JIT
  → src/codegen/llvm/       LLVM JIT
```

两处和"标准教学编译器"不一样，值得留意。第二行的解析器不是手写递归下降。`build.rs` 只有 8 行，作用是把 `src/parsing/` 下的 LALRPOP 语法编译成 LR 解析器，想改语法得动 `.lalrpop`。最后一步的三个后端**共用同一份运行时**：生成的代码只是调用运行时的 `extern "C"` 函数。作者在文档里直接写了这是取舍而非最优——把更多运行时内联进生成的代码会更快，但构建会变重。后文那次 Cranelift 崩溃，就出在这份运行时函数的登记表上。

后端选择是运行期参数，不是构建期参数：

| 后端 | 启用方式 | 定位 |
|------|----------|------|
| 字节码解释器 | `-B interp` | 官方文档写明用于小脚本和测试 |
| Cranelift JIT | 不带 `-B` 时的默认值 | 无需 LLVM，README 称对小脚本性能与 LLVM 相当 |
| LLVM JIT | `-B llvm`，且构建时要开 `llvm_backend` 特性 | 需要 LLVM 12；`--dump-llvm` 也只在启用该特性后存在 |

`-O` 的帮助文本声称 "Level `-1` forces bytecode interpretation"，这句在当前代码里不成立：`src/main.rs:713` 那个分派只看 `-B` 的值，`-O -1` 仍旧落进 Cranelift 分支，还把 `-1` 直接 `as usize` 转成优化级别。实测 `-O -1 '{s+=$1}END{print s}'` 与不带 `-O` 时同样崩溃，加上 `-B interp` 才正常。选后端请只认 `-B`。

README 对两者的说法是：Cranelift 后端在较小的脚本上提供与 LLVM 相当的性能，但 LLVM 的优化 "can sometimes deliver a substantial performance boost"。这是文档措辞，不是倍数。官方基准里确实有一项（Statistics）Cranelift 明显落后于 LLVM，其余各项两者很接近。

三个 `--dump-*` 参数是理解这套管线最省事的入口，也是我核对下面结论用的工具：

```bash
frawk --dump-cfg      '{ s += $1 } END { print s }'   # 无类型 SSA
frawk --dump-bytecode '{ s += $1 } END { print s }'   # 字节码
frawk --dump-llvm     '{ s += $1 } END { print s }'   # 需以 llvm_backend 构建
```

## 类型推导为什么不用统一算法

Awk 的标量同时挂着字符串和数字两种表示，靠使用场景选一个。这份灵活的成本是每次运算都要判断。frawk 的做法是编译期把每个标量定成 64 位有符号整数、双精度浮点或字符串三种之一；关联数组还能按"键全为整数""值仅为整数/浮点/字符串"特化，凑成 3 个标量类型加 6 个数组类型。内部另有 Null 类型表示未初始化变量，以及给 for-each 用的迭代器类型。

第一步是 SSA。`x = 1; x = "s"` 被拆成两个不同的槽位，`--dump-cfg` 能看到实际结果：

```text
4-1 = 1@int
0-4 = 4-1
4-2 = "s"
0-5 = 4-2
```

`4-1` 和 `4-2` 都是源码里的 `x`，整数与字符串各自独立，于是后续推导不需要处理"同一个变量两种类型"。带分支的地方由 phi 节点接住：

```text
7-1 = phi [←4:7-2, ←0:7-0]
```

作者给这一步开的书单是 Appel 的《Tiger Book》。SSA 构造那部分，他补了一句读的是该书之后发表的若干 Lengauer-Tarjan 替代方案。

第二步是赋类型。SSA 帮不上的地方是全局变量（只被主循环访问的除外）、数组的键和值，以及不同类型落进同一个 phi 节点的情形，比如 `x = y ? "z" : 3`。这里就要选算法了。经典的 Hindley-Milner 式推导靠等式约束，`x = y` 会把两个方向的类型信息互相倒进对方；作者认为这在 Awk 上代价太大：

```text
y = 3
x = "string"
x = y
```

按等式约束推，`y` 会被 `x` 污染成字符串，而程序里 `y` 只会取整数值。程序一大，"字符串会传染赋值两侧"会让数值变量越来越少。

frawk 于是把标量赋值的类型信息做成**单向流动**：`Integer` 与 `Float` 相遇近似成 `Float`，`String` 比一切都高。上面那段代码里，流向图的边是 `Integer→y`、`String→x`、`y→x`，结果 `x` 被放宽成字符串，而 `y` 保持整数。数组赋值反而是双向的——那正是统一约束在这个模型里的特例。作者把这个选择类比成静态分析里 Andersen 与 Steensgaard 两点分析的区别：单向更精确、双向更高效。代价也写得很直白：这套传播比统一算法慢，因为用不上 union-find；之所以能接受，是因为他写的 Awk 程序都很短。

对使用者来说，这套东西的意义在于它不要求任何类型标注，同时"不会给出 Awk 本身不会给出的类型错误"。真正会漏出来的地方是下面那十件事。

## 记录级并行与它的聚合语义

`-p r`（等价写法 `-pr`）按记录切分单个输入文件，`-p f` 则按文件切分多个输入。并行只对这么几类输入开放：CSV、TSV、只按空白切分的脚本，以及字段与记录分隔符都是单字节的脚本。

程序被拆成三段执行：

```awk
BEGIN { ... }        # 单线程；出现在主循环里的变量会被复制给各 worker
{ main loop }        # 多个 worker 并行；worker 数由 -j 指定上限，实际数量动态决定
PREPARE { ... }      # 每个 worker 读完自己那段输入后各自执行
END { ... }          # 单线程；主循环里出现的变量先聚合再交给它
```

隐式聚合是这套模型最值钱的部分，也是最深的一个坑。它的规则并不是一句"自动累加"：

- 整数和浮点标量求和；
- 字符串标量**任取一个非空 worker 的值**，不是拼接也不是最后一个；
- 数组按键值对做并集，键冲突时值再按上面的标量规则合并。

所以 `{ SUM += $1 } END { print SUM }` 和 `{ HIST[$1]++ } END { for (k in HIST) print k, HIST[k] }` 串行并行结果一致（浮点不满足结合律、数组遍历顺序未定义这两个常规例外除外）。而"求最大值"这种不是求和的操作，直接写会拿到某个 worker 的局部值。仓库文档给的修法有两层：先用 `PID`（每个 worker 一个唯一正整数，不保证连续）把结果写进数组，再在 `END` 里归约；或者用 `PREPARE` 块省掉在主循环里反复索引数组。

还有一条影响日常使用的限制，只在 `info/performance.md` 的批注里出现：**并行模式不保持输入的行顺序**。文档在 Select 和 Filter 两个基准上都专门标了这一点，并承认这使它与 tsv-utils 的比较不是同类比较。做行过滤时这很关键。

## 一条记录走完 frawk

把上面几条串起来，看一个真实脚本发生了什么。数据是 5 列的订单表，其中一行把地区写成了带逗号并加引号的 `"APAC, SEA"`：

```console
$ cat orders.csv
id,amount,date,region,status
1,5000,2026-01-15,EMV,APPROVED
2,300,2026-01-16,APAC,APPROVED
3,9000,2026-02-01,EMV,APPROVED
4,100,2026-02-03,EMV,PENDING
5,12000,2026-02-09,"APAC, SEA",APPROVED
```

脚本按"月份 × 地区"汇总金额超过 1000 且已批准的订单：

```awk
NR == 1 { next }
$5 == "APPROVED" && $2 + 0 > 1000 {
    month = substr($3, 1, 7)
    revenue[month, $4] += $2 + 0
}
END {
    for (key in revenue) {
        split(key, p, SUBSEP)
        print p[1], p[2], revenue[key]
    }
}
```

这条路径上依次发生四件事。`-i csv` 让第 5 行的地区保持成一个字段：换成 `-F,` 之后这一行多出第 6 个字段，`$4` 变成 `"APAC`、`$5` 变成 ` SEA"`，真正的 `APPROVED` 被推到 `$6`，于是 `$5 == "APPROVED"` 不再成立。`$2 + 0` 把金额显式转成数字，因为 frawk 里字符串比较恒为字典序。`revenue[month, $4]` 用 `SUBSEP` 拼复合键，`split(key, p, SUBSEP)` 再拆回来：这条经典写法 frawk 支持，`src/harness.rs` 里那个 `basic_subsep` 测试断言的正是它，虽然它不支持 gawk 的真多维数组。最后，`next` 出现在主循环里所以合法，挪进函数就会被 `src/cfg.rs` 拒掉。

把脚本存成 `revenue.awk`，串行和并行给出同样的三行：

```console
$ frawk -B interp -i csv -f revenue.awk orders.csv | sort
2026-01 EMV 5000
2026-02 APAC, SEA 12000
2026-02 EMV 9000
$ frawk -B interp -i csv -p r -f revenue.awk orders.csv | sort
2026-01 EMV 5000
2026-02 APAC, SEA 12000
2026-02 EMV 9000
```

同一份脚本换成 `-F,` 会怎样，值得单独看一眼：

```console
$ frawk -B interp -F, -f revenue.awk orders.csv | sort
2026-01 EMV 5000
2026-02 EMV 9000
$ /usr/bin/awk -F, -f revenue.awk orders.csv | sort
2026-01 EMV 5000
2026-02 EMV 9000
```

那笔 12000 的单子整个不见了，没有任何提示。这一对照也顺手说明了一件事：把 frawk 换成交错分隔符，它和系统自带的 Awk 犯的是同一个错——正确性来自 `-i csv` 这个模式，不来自实现语言。

用 `-H` 加 `FI` 可以省掉硬编码的列号，`$FI["amount"]` 等价于 `$2`。文档特别提到这个特性和投影下推分析（`src/pushdown.rs` 用来推断哪些列根本不需要解析）配合得很好：

```console
$ frawk -B interp -H -i csv '$FI["status"]=="APPROVED" { t += $FI["amount"] } END { print t }' orders.csv
26300
```

26300 = 5000 + 9000 + 12000，正确排除了 300 和未批准的那笔 100。

## 性能数字该怎么读

**先说测的是什么。** 官方 `info/performance.md` 的口径：每个配置取 5 次运行的最小墙钟时间，同时报 `time` 给出的用户态与系统态 CPU 时间；吞吐量的算法是"文件大小除以墙钟时间"。并行 frawk 的 worker 数是自适应的，所以 CPU 时间与墙钟时间的比值在各次运行间会浮动。

**两台机器都是 Intel。MacOS 那台是 2019 年末的 16 英寸 MacBook Pro，8 核 i9 @2.3GHz，睿频 4.8GHz。系统 macOS Big Sur 11.2.1。Linux 那台是 2016 年中的双路 Xeon 2620v4，16 核 @2.2GHz，64GB 内存，Ubuntu 18.04。作者自己提醒过，这两个标签代表整机配置而不是操作系统；同配置内的比较可信，跨配置的要谨慎。

**两份数据集。** UCI 的 HEPMASS `all_train.csv`，700 万行，CSV 与 TSV 均约 5.2GB；美国林务局的 `TREE_GRM_ESTN.csv`，3600 万行，CSV 8.9GB、TSV 7.9GB。

以下是 Ad-hoc 计算任务（对第一列做加权、取第 4/5 列较大值）在 **MacOS** 配置上的原表：

| 程序 | 格式 | 耗时（墙钟；括号内是用户 + 系统） | 吞吐量 |
|------|------|-----------------------------|--------|
| Python（csv 库） | CSV | 2m48.7s (2m47.4s + 1.3s) | 53.02 MB/s |
| Rust（csv crate） | CSV | 25.9s (24.8s + 1.1s) | 345.57 MB/s |
| frawk（Cranelift） | CSV | 19.9s (18.8s + 1.1s) | 450.13 MB/s |
| frawk（Cranelift，并行） | CSV | 4.9s (23.2s + 1.2s) | 1827.84 MB/s |
| frawk（LLVM） | CSV | 19.6s (18.5s + 1.1s) | 457.12 MB/s |
| frawk（LLVM，并行） | CSV | 4.9s (22.9s + 1.2s) | 1842.90 MB/s |

先纠正方法学里的一处笔误。文档写吞吐量的算法是 "wall time divided by input file size"，可照表内任一列反推，真实算法是文件大小除以墙钟。顺着这条还能推出文档没写明的事。53.02 MB/s 乘 168.7 秒约等于 8.9GB，所以 Ad-hoc 这一项跑的是 `TREE_GRM_ESTN`，不是 5.2GB 的 `all_train`。

这张表能读出的三件事，比"快 N 倍"有用。第一，这一项里**没有 gawk 和 mawk**。Awk 吃不下这个 CSV，作者拿 Python 和手写 Rust 当对照，所以"Awk 与 frawk 差 N 倍"这类说法不该引用它。第二，并行那两行的 CPU 时间约为墙钟的 5 倍，收益来自多核同时干活，不是单次执行变快。第三，Cranelift 与 LLVM 在这里只差 1.5%。

真正涉及 Awk 的比较在"Sum two columns"一项。`TREE_GRM_ESTN` 的 TSV 版本上：

| 程序 | MacOS | Linux |
|------|-------|-------|
| mawk | 42.0s，187.81 MB/s | 54.9s，143.74 MB/s |
| gawk | 14.0s，562.60 MB/s | 23.1s，341.23 MB/s |
| tsv-utils | 5.6s，1397.24 MB/s | 7.5s，1047.75 MB/s |
| frawk（LLVM，并行） | 3.4s，2332.73 MB/s | 8.1s，978.75 MB/s |

**这两列讲的是不同的故事。** MacOS 上 frawk 并行的墙钟比 tsv-utils 少 39%（3.4s 对 5.6s）；换到 Linux，frawk 并行（8.1s）反而略慢于 tsv-utils（7.5s）。作者的结论更保守：单核吞吐上 frawk 快过 mawk 和 gawk，但在两种配置下都慢于 tsv-utils。

"mawk 比 gawk 快"这句话同样找不到支撑。两者都参加的基准有五项。MacOS 上 gawk 赢了四项：Sum、Select、Filter、Group By Key。mawk 只在 Statistics 上勉强占先，1m12.6s 对 1m13.3s。换到 Linux，连这一项也归了 gawk（1m14.4s 对 1m23.3s）。

作者在前言里主动交代了三条保留，这是整份文档最有价值的部分，值得抄进自己的评估清单。他承认一定存在 frawk 比 Rust 甚至 C 更慢的程序。他说自己很难区分三类解释：语言实现的差距、程序质量的差距、以及某种语言天然让你能写得更省。于是他请读者从这些数字里 "draw at most modest conclusions"，也就是最多得出温和的结论。

基准里还有几处条件要看清。gawk 一律带 `-b` 关掉多字节支持，作者承认这对支持 UTF-8 的几个工具不公平，但这些任务没用到 UTF-8。frawk 在 TSV 上统一用 `-F'\t'` 而不是 `-itsv`。前者解析更简单，也更能利用"只读少数几列"的投影下推。他明确指出，这正是 tsv-utils 长期领先的主要原因之一。Group By Key 一项，frawk 与 gawk 单线程几乎并列，被 tsv-utils 明显拉开。

这些数字到 2026 年还算不算数？那两份 5.2GB 与 8.9GB 的数据集我复现不了，但在自己的机器上量一次是可以的。这一量，是把 x86 SIMD、LLVM 和 JIT 这三块地基全抽掉之后再看这笔交换剩多少。

### 一台 Apple Silicon 上的复现实验

环境：Mac mini（Apple M4，10 核），`rustc 1.97.1`，构建命令 `cargo build --release --no-default-features`，耗时 36.6 秒，产物 8.4 MiB，`--version` 报 `frawk 0.4.8`。三个"没有"各有各的来源。`src/runtime/splitter/batch.rs` 里的向量指令实现整段被 `#[cfg(target_arch = "x86_64")]` 限定，ARM 上走 `generic::Impl` 标量后备。本机没有 LLVM 12。至于 JIT，是下一节要讲的 Cranelift 故障逼着我退到最慢的字节码解释器。

数据用 Python 的 `csv` 模块按 RFC 4180 规则生成，300 万行、146.4MB。其中一半行的分类字段带逗号或引号（`grep -c '"'` 数得 1,498,227 行）。真值由同一个 `csv` 模块独立累加：**1499393.7153**。

每一行跑的都是同一句程序 `'NR>1 { s += $3 } END { print s }'`，只换分隔符和并行开关：

| 命令前缀 | 结果 | 耗时（3 次最小） | 吞吐 |
|----------|------|------------------|------|
| `/usr/bin/awk -F,` | 1.12498e+06（少算 374,413） | 2.61s | 56 MB/s |
| `frawk -B interp -F,` | 1124980.45（同一个错值） | 0.27s | 533 MB/s |
| `frawk -B interp -i csv` | **1499393.7153**，逐次完全一致 | 0.44s | 334 MB/s |
| `frawk -B interp -i csv -p r` | 1499392.88 到 1499393.70（8 次实测区间） | 0.28s | 528 MB/s |
| `frawk -B interp -i csv -p r -j 8` | 落在同一区间 | 0.30s | 486 MB/s |

那份 146.4MB 的数据由下面这段生成，`random.seed(42)` 固定了随机序列，所以任何人重跑都会得到同一份文件和同一个真值：

```python
import random, csv
random.seed(42)
cats = ['Alpha', 'Beta, Gamma', 'Del"tained', 'Epsilon']
with open('bench2.csv', 'w', newline='') as f:
    w = csv.writer(f)
    w.writerow(['id', 'cat', 'val1', 'val2', 'val3', 'name', 'flag'])
    for i in range(3_000_000):
        w.writerow([i, random.choice(cats), '%.4f' % random.random(),
                    '%.4f' % random.random(), i % 997,
                    'name%d' % (i % 5000), random.choice(['OK', 'NO'])])
```

累加真值就是把上面 `bench2.csv` 换成 `csv.reader` 逐行取 `row[2]` 求和，得到 1499393.7153。

四点读法。前两行是同一个错值，只是 Awk 按 `CONVFMT` 打成了 6 位有效数字；这说明字段错位与用哪家实现无关，正确性完全来自 `-i csv`。`-i csv` 相对 `-F,` 慢了 63%，这是转义解析实打实的开销。并行给了 1.57 倍，但 `-j` 从 2 加到 12 全部停在 0.27–0.29 秒。解释执行才是瓶颈，加 worker 已经推不动。这和官方文档说的"4 到 6 个 worker 后边际收益递减"是两件事，别混着引用。串行的 `-i csv` 每次都吐同一个 1499393.715300044，而并行八次跑出的尾数各不相同、极差 0.8 左右。这就是浮点加法不满足结合律的实测形态，作者把它列在并行等价性的常规例外里。并行给出的不是同一个数，而是一个足够近的数——用相等断言做回归的脚本会在这里翻车。

这台机器上最结实的结论只有一条：退化到标量解析加字节码解释之后，frawk 处理真实 CSV 仍比系统自带的 Awk 快 6 倍。而且它算对了，Awk 算错了。官方表格里 2GB/s 那一档，得靠 x86 向量指令、JIT 与多核三者同时到位。

## 与邻近工具的分工

作者对 frawk 的期待是"能在更多场合写 Awk 程序"，不是把 Awk 长成高级语言。他写明自己欣赏 Awk 很少越出一行脚本这个范围，也没打算用它写大程序。这条自我定位决定了下面的比较该怎么读。

| 工具 | 形态 | 引号 CSV | 编程模型 | 单核 TSV 表现 |
|------|------|----------|----------|----------------|
| frawk | 语言 + 命令行 | 原生（`-i csv`） | 完整，含自定义函数、并行 | 慢于 tsv-utils |
| xsv | 子命令集合 | 原生 | 固定菜单，非通用语言 | Select 5.3s、Statistics 32.8s（MacOS TSV） |
| tsv-utils | 子命令集合 | 需先 `csv2tsv` 转换 | 固定菜单 | 表内最快 |
| gawk | 语言 | 不处理 | 完整 + 大量扩展 | 快于 mawk |
| mawk | 语言 | 不处理 | 贴近"AWK 书"语义 | 效率取向 |

`csv2tsv` 那一步的代价，官方给的数字是 TREE_GRM_ESTN 28.7 秒、all_train 14.6 秒，比许多基准任务本身还长。所以"先转 TSV 再用 tsv-utils"在一次性查询上并不划算，这是 frawk 的定位空隙所在。反过来说，`info/performance.md` 里 Group By Key 一项 tsv-utils 单核拿到 1614 MB/s，frawk LLVM 只有 534 MB/s——固定聚合场景下没有悬念。

## 从 Awk 迁过来会撞上的十件事

下面每一条都是我在 HEAD（`d548b15`，2025-09-26）上跑出来的，对照实现是 macOS 自带的 `/usr/bin/awk`。

1. **`~` 与 `match()` 的返回值正好和 Awk 相反。** `("xxabc" ~ /abc/)` 在 frawk 里得到 **3**（匹配起始位置），Awk 得到 1；而 `match("xxabc", /abc/)` 在 frawk 里得到 **1**，Awk 得到 3。更要注意副作用：`RSTART`/`RLENGTH` 在 frawk 里跑完 `match()` 仍是 `0 -1`，Awk 给 `3 3`。`info/reference.md` 写的是 frawk 会设置这两个变量——文档与代码在这里不符。用来做真值判断没问题，凡是拿返回值和 1 比较、或者依赖 `RSTART` 的脚本都要改。
2. **`exit` 不再执行 `END`。** `{ if (NR>2) exit 3 } END { print "end-ran" }` 在 Awk 里打印 `end-ran` 并以 3 退出，在 frawk 里什么都不打印、退出码 3。这是靠 `END` 做收尾（刷新缓冲、打印汇总）的脚本最容易中的一次。
3. **内置函数与左括号之间不许有空格，而且失败是静默的。** `print length (s)` 不报语法错误，它被解析成"未初始化变量 `length` 与 `(s)` 拼接"，`s="abc"` 时输出 `abc`；`length(s)` 才输出 `3`。文档只说了不许有空格，没提失败是静默的。
4. **字符串之间的比较恒为字典序。** `("9" == "9.0")` 是 0，Awk 会先尝试把两边当数字再比。要数值比较就显式 `+0`：`("9" == "9.0"+0)` 得 1。作者的理由是 Awk 那套会让"相等的两个字符串在数组里落到不同键上"，而且很难显式选字典序。
5. **未初始化变量可能被打成整数。** `BEGIN{ if (0) { x=6 }; printf "[%s]", x }` 在 Awk 输出 `[]`，frawk 输出 `[0]`。这是文档自己承认的类型策略"漏进真实程序"的主要形态。
6. **`CONVFMT` 不参与浮点打印。** 默认用 `ryu` 做最短往返表示，`print 1/3` 得 `0.3333333333333333`，Awk 给 `0.333333`。要控精度只能 `printf`/`sprintf`。
7. **`-i csv` 与 `-F` 互斥**，同时给会直接被参数解析挡下（`--input-format <csv|tsv> cannot be used with --field-separator <FS>`）；`-i` 模式下给列赋值无效；`$0` 是未转义原文。
8. **正则用的是 Rust `regex` 语法**，与 POSIX ERE 相似但不相同。作者说想过自研引擎或做一层转换，只是没做。
9. **`next` 和 `nextfile` 只能在主循环里。** 放进函数会得到一条明确错误："frawk does not support `next` or `nextfile` from inside functions"（`src/cfg.rs`）。
10. **读写批处理比多数 Awk 实现激进。** 文档说这是为性能，反映"批处理脚本"的目标场景。副作用是把 frawk 接进需要即时逐行输出的管道时，会看到它不像 Awk 那样立刻吐字。

`info/overview.md` 还列了几条缺失项：gawk 的协程、真多维数组；32 位平台基本没戏，作者推测非 x86 的 64 位平台会明显更慢（这一条和我上面在 M4 上量到的标量后备路径正好对上）。反过来，这份清单也没说全：`gensub(/a/,"b","g","aaa")` 实跑得 `bbb`，而这个 gawk 扩展既不在"缺失"列表里，也不在 `info/reference.md` 的函数清单里。`src/builtins.rs` 里的 `FUNCTIONS` 表登记的内置函数是 38 个（`VARIABLES` 表另有 15 个内置变量），除 `join_fields`、`hex`、`int`、`escape_csv`、`rshiftl` 这些扩展位外，也包含 `gensub`。`print`、`printf`、`sprintf`、`getline`、`delete` 不在那张表里，它们是语法层面的关键字。位运算那组 `and`/`or`/`xor` 不像 gawk 那样可变参数，`and(1,2,3)` 会被 `src/builtins.rs` 直接拒掉。

## 常见故障与排查

**默认后端起不来。** 这是最需要先讲的一条。在这台 M4、`rustc 1.97.1`、无 LLVM 的构建上，凡是带主循环或 `END` 块的脚本都会立刻 panic，纯 `BEGIN` 的程序则正常：

```console
$ frawk -B cranelift 'END { print "e" }'
thread 'main' panicked at src/codegen/clif.rs:934:44:
no entry found for key
```

`clif.rs:934` 就是 `self.shared.external_funcs[&func]` 这次查找——生成的代码要调用一个没有登记在这张表里的运行时函数地址。跑仓库自带的测试能给出规模：单元目标 211 项里 33 项失败，而失败项**全部**是 `::cranelift` 参数化分支（该分支共 79 项），`bytecode` 分支 81 项零失败；三个集成目标合计 77 项（`misc` 16、`nawk_p` 59、`sort` 2）里失败 57 项，因为它们是起子进程调 `frawk` 二进制、默认走 Cranelift。换成 `-B interp`，上述所有失败全部消失。注意 `-O -1` 救不了：帮助文本说它"forces bytecode interpretation"，但 `src/main.rs:713` 只按 `-B` 分派后端，实测 `-O -1` 与不带 `-O` 一样崩。

最接近的在册记录是 issue #122（2025-09-11 提出，至今未关，诉求是把 Cranelift 从 0.93 升上去）。作者在其中指出：`codegen::intrinsics` 里那些 `pub(crate) unsafe extern "C"` 函数一旦被内联，注册时拿到的地址就和 `codegen::clif` 请求的地址不是同一个，`call_inst` 随即失败。这与上面那行的失败点吻合。#121 是它的邻居（Cranelift 下 `printf("%s")` 报"invalid type code"）。README 推荐的那条构建路线要 nightly 加 LLVM 12，我这里没有，所以无法判断换用 LLVM 后端是否绕得开这一条。能说的只有：只求能跑的话，`-B interp` 是当场可用的解。要复现官方吞吐，Cranelift 和 LLVM 两块都得先立起来。

**装不上 LLVM 12。** 依赖锁的是 `llvm-sys = "120"`。没有它，`-B llvm` 报 "compiled without LLVM support"，`--dump-llvm` 这个参数则根本不存在——不是值非法，而是无法识别。macOS 上 README 给的路线是 `brew install llvm@12`，原话还补了一句 "or similar seem to work"。我这台机器的 Homebrew 只装得到 llvm@21，这条路今天还好不好走，我没有验证。

**构建报特性错误。** 默认特性集含 `unstable`，需要 nightly。用 stable 就得去掉它，README 对此有明确说明。默认特性全集是 `use_jemalloc`、`allow_avx2`、`llvm_backend`、`unstable`；README 建议的无 LLVM 构建是 `--no-default-features --features use_jemalloc,allow_avx2,unstable`。另外 `allow_avx2` 注释里点了一句反直觉的话：AVX2 有时会让整个程序变慢，即使 CPU 支持——这是拉低频率的代价。

**并行结果和串行不一样。** 按顺序查三处：聚合的是不是字符串标量，它被任取一个而不是合并；脚本求的是不是 min、max、方差这类非求和量，这类要用 `PREPARE` 加 `PID` 显式归约；输出是否依赖行顺序，并行不保序。

**`-i csv` 下改了列没效果。** `$1 = "X"` 之后 `$0` 和 `$1` 都不变，脚本不报错也不警告。这是 `-i` 模式的设计：字段是解析出来的视图，不是可写存储。要改输出，改成 `print` 的参数并配 `-o csv`。

**Windows 与 32 位。** 作者没测过 Windows，但 README 记录它在关闭默认特性时能构建（issue #87）；`allow_avx2` 那条路径靠 `is_x86_feature_detected!` 在运行时探测 CPU 特性，非 x86 架构上整段不编译，32 位平台则被文档直接排除。

## 谁该用，谁可以再等等

适合的场景相当具体，四个条件：数据是 CSV 或 TSV；字段里可能有逗号和引号；逻辑是 Awk 擅长的那类过滤加聚合；你不想为它单独写一个 Rust 程序。四条同时满足时，frawk 基本是独一份的选择。

可以等的情况同样明确。已经在生产上跑的脚本别急着迁。凡是依赖 gawk 扩展（协程、真多维数组）的，或者依赖 `CONVFMT`、"`exit` 会先执行 `END`"这类 Awk 常规行为的，都要先按上面那十条逐条核对。只需要固定查询的，tsv-utils 和 xsv 的边际成本更低，frawk 得靠"转换那一步比整个任务还长"才赢。指望装上就复现 2GB/s 的，得先确认自己站在 x86 + LLVM + 可用 JIT 这三块地基上；Apple Silicon 用户目前处在最不利的位置。

如果要引入，我建议的顺序是四步。第一步，拿真实数据跑 `-i csv` 的正确性对照，用 Python 的 `csv` 或 `csvkit` 做独立真值，核对总量而不是抽样。第二步，锁定后端并固定 `-B` 参数，别让它随构建环境漂移。第三步，确认聚合语义等价之后再打开 `-p r`，并把"输出不保序"写进验收标准。性能留到最后再谈。

## 自测清单

不看文稿，回答这五个问题；答不上来的那一条就是回去重读的小节。

1. 一个字段里带逗号的 CSV，`-F,` 和 `-i csv` 给出的错误形态有什么不同？为什么换实现救不了前者？
2. `x = 1; x = "s"` 在 frawk 里靠什么被推成两个类型？哪一类变量 SSA 拆不动，拆不动之后怎么处理？
3. 并行模式下 `max` 为什么不自动正确？`PREPARE` 与 `PID` 各自补的是哪一段？
4. 官方 Ad-hoc 表里为什么没有 gawk 和 mawk？"Sum two columns"在两台机器上给出的结论差在哪？
5. 主循环脚本 panic 在 `clif.rs:934`，你的第一反应是换后端还是换编译器版本？依据是什么？

## 下一步读哪份代码

按性价比排序，都不需要跑起来：

- `info/types.md` 的 `### Information Flow`：一篇很短的"为什么不用统一算法"，配上那个 `y=3` 的三行例子。想理解 frawk 的类型策略，读这一节比读 `src/types.rs` 的 1123 行快得多。
- `info/overview.md` 的 `### What is new` 与 `### What is different`：迁移清单的第一手来源，但要用 `src/builtins.rs` 复核，因为它漏掉了 `gensub` 这类已经实现的 gawk 扩展。
- `info/parallelism.md` 的 `### Aggregations`：三条聚合规则，以及从"隐式够用"到"必须显式"的分界。
- `src/runtime/splitter/batch.rs` 文件头那行注释，加 `src/codegen/clif.rs` 的 `call_inst`：前者告诉你 CSV 解析是从 `geofflangdale/simdcsv` 那套两阶段思路改过来的（它不是依赖，没有 `simdcsv` 这个 crate），后者告诉你运行时函数按地址登记意味着什么。
- `info/performance.md` 开头的 Disclaimer 和 `-itsv` vs `-F'\t'` 两节：一份少见的、作者主动说明自己基准局限性的文档。

## 维护与复核指引

本文断言核实于 2026-09-21。代码对象是 `ezrosent/frawk` 的 `master` HEAD `d548b15`，提交于 2025-09-26。实测构建用 stable `rustc 1.97.1`，特性集是 `--no-default-features`。

需要重新核对的触发条件，按失效可能性排序：

| 断言 | 失效条件 | 复核命令 |
|------|----------|----------|
| Cranelift 后端故障 | 升级 Cranelift（issue #122 的诉求）或换 rustc 版本 | `cargo test --release --no-default-features 2>&1 \| grep 'test result'` |
| 最新版本与发布日期 | 一旦重新发版 | `curl -s -H 'User-Agent: check' https://crates.io/api/v1/crates/frawk/versions \| head -c 400` |
| 维护活跃度 | 有新提交 | `gh api 'repos/ezrosent/frawk/commits?per_page=3' --jq '.[].commit.author.date[:10]'` |
| 内置函数数量（38） | 函数表变动 | `sed -n '/FUNCTIONS<&/,/^);/p' src/builtins.rs \| grep -cE '^\s+\["'` |
| `~`/`match` 与 `exit`/`END` 行为 | 若与 Awk 对齐 | `frawk -B interp 'BEGIN{ print match("xxabc", /abc/), RSTART, RLENGTH }'` |
| SIMD 仅 x86-64 | 加入 ARM 向量实现 | `grep -n 'cfg(target_arch' src/runtime/splitter/batch.rs \| head` |

仓库的维护状态要用两个来源一起看，别只信 README。README 顶部有一条 2024 年的说明，作者是这么写的：过去一到两年，他投在 frawk 缺陷修复和新功能上的时间少了很多。别的 Awk 实现维护得更活跃。而且相比项目起步时，CSV 支持在 Awk 里已经常见得多。他承诺状态一变就更新这条说明。请注意这条说的是"别的实现更活跃"，不是他转去维护那些实现。把时间线摊开会看到另一面。2024-02-13 提交 "Add note to README" 之后是近 19 个月的静默。2025-09-23 到 09-26 一口气合进 5 个改动：修 `continue`、加环境变量支持、把 dev 构建的 `opt-level` 设成 1 来规避解释器段错误。此后至今再无新提交。仓库有 1317 星、42 个派生仓库、31 个未关闭 issue 加 4 个未关闭 PR。一个仍在零星接收修复、但没人对 Cranelift 与新版工具链负责的项目，是对读者最有用的一句话概括。

术语与口径上留两个提醒。AWK 的大小写问题仓库自己也混（`info/overview.md` 专门加了一句说作者在这个问题上不一致），本文统一用"Awk"指语言、"gawk/mawk/frawk"指实现。另一处是"方言"这个词。README 的说法是 "to a first approximation, it is an implementation of the AWK language"——近似实现，而不是同一个家族里的一个变体。这个区别在前面那十件事里会具体兑现。

## 参考

- [ezrosent/frawk](https://github.com/ezrosent/frawk) — README（安装、构建特性、2024 年维护状态说明）
- [frawk overview](https://github.com/ezrosent/frawk/blob/master/info/overview.md) — 动机、编译器结构、与 Awk 的差异清单
- [The Role of Types in frawk](https://github.com/ezrosent/frawk/blob/master/info/types.md) — SSA、单向 flows、与统一算法的取舍
- [Parallelism in frawk](https://github.com/ezrosent/frawk/blob/master/info/parallelism.md) — 三阶段模型、聚合规则、`PREPARE`
- [Performance](https://github.com/ezrosent/frawk/blob/master/info/performance.md) — 基准方法学、硬件与数据、各任务原表
- [Builtin Functions and Commands](https://github.com/ezrosent/frawk/blob/master/info/reference.md) — 内置函数清单
- [geofflangdale/simdcsv](https://github.com/geofflangdale/simdcsv) — 两阶段 CSV 解析思路的来源（frawk 移植了做法，未引这个 crate）
- [issue #122 Update cranelift](https://github.com/ezrosent/frawk/issues/122) 与 [issue #121](https://github.com/ezrosent/frawk/issues/121) — Cranelift 后端在册缺陷
- [issue #118](https://github.com/ezrosent/frawk/issues/118) — `rustc ≥ 1.77` 下解释器改字段分隔符导致段错误，2025-09-26 关闭
- [The AWK Programming Language](https://en.wikipedia.org/wiki/The_AWK_Programming_Language) 与 [Tiger Book](https://www.cs.princeton.edu/~appel/modern/ml/)（Appel《Modern Compiler Implementation in ML》）— frawk 文档自陈的两处参考
