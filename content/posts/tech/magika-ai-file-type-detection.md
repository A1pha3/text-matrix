---
title: "Magika 解读：Google 用几 MB 的专用模型替代 50 年的 magic bytes"
date: "2026-04-16T01:15:00+08:00"
lastmod: "2026-10-01T12:00:00+08:00"
slug: "magika-ai-file-type-detection"
github_repo: "google/magika"
source_key: "gh:google/magika"
description: "Magika 是 Google 开源的文件内容类型检测工具：一个几 MB 的专用深度学习模型，200+ 内容类型约 99% 平均精确率/召回率，单文件毫秒级推理，Gmail、Drive、Safe Browsing 每周数千亿样本在用。本文拆解其输入切分、双层标签与按类型阈值机制，并给出 CLI 与 Python API 的采用建议。"
draft: false
categories: ["技术笔记"]
tags: ["深度学习", "安全", "Google", "Python", "Rust", "开源"]
---

# Magika 解读：Google 用几 MB 的专用模型替代 50 年的 magic bytes

文件类型识别这活儿，`file` 命令背后的 libmagic 已经干了五十多年：拿文件开头几个字节去查魔数表。这套体系对 PNG、PDF 这类二进制格式一直够用，但在 text 文件上基本失灵——Python 脚本、JSON、YAML 的开头就是普通字符，没有魔数可查，把恶意脚本改个 `.jpg` 扩展名就能绕过大多数检查。

Magika 是 Google 对这个问题的解法：把文件类型识别当成一个分类任务，用一个几 MB 的专用深度学习模型（当前默认 standard_v3_3，ONNX 格式 3.2 MB）替代魔数表。官方口径是约 1 亿样本、200+ 内容类型上训练，测试集平均精确率/召回率约 99%，模型加载后单文件推理约 5 毫秒（单 CPU）。它不是实验室项目——Gmail、Drive、Safe Browsing 用它把文件路由到对应的安全与内容策略扫描器，每周处理数千亿样本。

2024 年 2 月开源，Apache-2.0 协议，截至 2026-10-01 有 18,687 个 star。仓库挂在 google 组织下，但 README 明确写着"这不是一个官方 Google 项目，不受 Google 支持"——评估依赖时值得知道这一句。

## 三层交付：CLI、绑定和那个 3 MB 的模型

Magika 的交付物分三层，先分清谁在哪个层，后面的机制才不会混：

| 层 | 形态 | 状态 |
| --- | --- | --- |
| 命令行工具 | Rust 写的 `magika` 二进制 | 已发布 1.x，`brew install magika`、`cargo install magika-cli`，或经 Python 包转发 |
| 语言绑定 | Python（PyPI `magika`）、JS/TS（npm `magika`）、Go（WIP） | Python 已稳定，npm 包官方标注实验性 |
| 模型核心 | ONNX 模型 + 各自的推理引擎 | Rust 核心用自带的 tract-runtime 分支，Python 1.x 用 onnxruntime |

一个容易搞错的点：`pipx install magika` 装的 Python 包在 v1.x 里也自带 `magika` 命令，但那是个转发层——平台 wheel 里带 Rust 二进制时直接执行，纯 Python wheel 上退化为 click 写的 Python 版客户端（源码注释自称 fallback）。两种装法拿到的命令行选项不完全一样，后面细说。

## 为什么 magic bytes 体系在 text 文件上失灵

魔数检测的逻辑是"看开头几个字节像不像已知格式"：`\x89PNG` 开头是 PNG，`\xff\xd8` 开头是 JPEG。二进制格式的魔数是规范强制的，所以准。

text 文件没有这个待遇。下面三种文件在字节层面都是 ASCII，魔数表无从下手：

```text
def hello():          # Python
{"name": "value"}     # JSON
function greet() {}   # JavaScript
```

于是扩展名成了唯一线索，而扩展名恰恰是最容易伪造的东西。Google 在官宣博文里的表述是：内部换用 Magika 后，对比被替换的旧手工规则系统准确率提升 50%，在 100 万文件、100+ 类型的基准上比现有工具好约 20%，文本类文件提升最明显。这些是 Google 自报的内部数字，论文发表在 ICSE 2025（Fratantonio 等 12 人），想追细节可以读论文 PDF。

不用大模型的原因很实际：Magika 要嵌入 Gmail 的附件扫描管线，每周数千亿样本意味着每一毫秒和每一 MB 内存都要算账。专用小模型在这个任务上反而更准——通用大模型没在这个数据分布上专门训过。这是个"小而专打败大而全"的典型场景。

## 一次检测的完整路径

用一个具体文件走一遍：攻击者把一个 Python 脚本改名为 `invoice.jpg` 上传。

**第一步，切字节。** Magika 不读整个文件。以当前默认模型 standard_v3_3 为例，Python 包内置的模型配置写死了输入切分：取文件开头 1024 字节和结尾 1024 字节（中段不读，`mid_size=0`），这决定了它的推理时间与文件大小基本无关——50 MB 的文件和 5 KB 的文件耗时几乎一样。

**第二步，特判。** 有些输入轮不到模型：空文件直接返回 `empty`；目录返回 `directory`；不开符号链接跟随（`--no-dereference`）时符号链接返回 `symlink`；小于 8 字节的文件（`min_file_size_for_dl=8`）用简单启发式判定为 `txt` 或 `unknown`。官网文档把这些归为"模型内部标签设为 undefined"的情形——Python API 里对应 `MagikaResult` 的 `dl` 与 `output` 双层标签，此时 `dl` 是 `undefined`。

**第三步，模型推理。** 开头结尾两段字节提特征后送入 ONNX 模型，输出在 215 个类型上的概率分布（模型原始输出空间，其中 `randombytes`/`randomtxt`/`undefined` 三个训练用标签不会对外出现）；工具层的可能输出是 216 项——模型的 212 个有效标签，加上 `empty`/`directory`/`symlink`/`unknown` 四个非模型判定。`invoice.jpg` 的两段字节全是 Python 语法，模型给出 `python` 标签、置信度 0.99。

**第四步，按类型阈值裁决。** 模型分数高不等于直接采纳。Magika 为每个内容类型单独设阈值——PDF 的预测置信度天然常年 99% 以上，一个 80% 的 PDF 预测就可疑；而 JavaScript 的预测经常就在 80% 出入，80% 反而很可靠。所以阈值不搞全局一刀切，而是随模型一起发布、在大验证集上调优。`python` 的分数过了阈值，最终输出就是 `python`；若没过，则降级为泛型标签——文本给 `txt`，二进制给 `unknown`。

这就是为什么结果对象里同时有 `dl` 和 `output` 两层：`dl` 是模型原始预测，`output` 是阈值裁决后的最终输出，二者不一致时 `overwrite_reason` 会说明覆盖原因。想看被覆盖的原始判断，CLI 的 `--format` 占位符里有个专门的 `%b`（model output if overruled）。

## 分数怎么用：三种预测模式

容忍度可以调。Magika 提供三种预测模式：

| 模式 | 行为 | 适用 |
| --- | --- | --- |
| `high-confidence` | 精确率优先，分数不过阈值就给泛型标签 | 上传过滤、安全场景，宁可误伤不可放过 |
| `medium-confidence` | 介于两者之间 | 一般用途 |
| `best-guess` | 无视分数直接返回模型最优预测 | 已知类型集合内的批量整理，召回优先 |

默认是 `high-confidence`——这是从源码核实的：Python API 的 `Magika.__init__` 与 Python 版 CLI 的 `--prediction-mode` 都默认 `HIGH_CONFIDENCE`（官方预测模式文档页只列了三种模式，没写默认值）。另有一个容易踩的坑：Rust 版 CLI 压根不暴露预测模式选项（v1.1.0 的选项表里没有），想在命令行换 `best-guess` 只能用 Python 包的 fallback 客户端（`-m/--prediction-mode`，另有 `--batch-size`）或直接走 Python API。

## CLI 与 Python API 实操

安装五条路（README 原文照录，均验活可用）：

```bash
pipx install magika                          # Python 包（内含/转发 Rust 二进制）
brew install magika                          # macOS / Linux
cargo install --locked magika-cli            # Rust 包
curl -LsSf https://securityresearch.google/magika/install.sh | sh
npm install magika                           # JS/TS 绑定（实验性）
```

CLI 的日常形态：

```bash
% magika -r ./tests_data/basic | head
asm/code.asm: Assembly (code)
batch/simple.bat: DOS batch file (code)
c/code.c: C source (code)
csv/magika_test.csv: CSV document (code)
dockerfile/Dockerfile: Dockerfile (code)
docx/doc.docx: Microsoft Word 2007+ document (document)
eml/sample.eml: RFC 822 mail (text)
empty/empty_file: Empty file (inode)
```

完整选项：`-r` 递归目录、`--no-dereference` 不跟随符号链接、`-s/--output-score` 附带分数、`-i/--mime-type`、`-l/--label`、`--json`/`--jsonl`、`--format` 自定义格式（占位符 `%p` 路径、`%l` 标签、`%d` 描述、`%g` 分组、`%m` MIME、`%e` 扩展名、`%s`/`%S` 分数（小数/百分比）、`%b` 被覆盖时的模型原始输出、`%%` 字面百分号）。

`--json` 的输出结构值得看一眼，双层标签在这里是显式的：

```json
[
  {
    "path": "code.py",
    "result": {
      "status": "ok",
      "value": {
        "dl":     { "label": "python", "mime_type": "text/x-python", "group": "code", "is_text": true, "description": "Python source", "extensions": ["py", "pyi"] },
        "output": { "label": "python", "mime_type": "text/x-python", "group": "code", "is_text": true, "description": "Python source", "extensions": ["py", "pyi"] },
        "score": 0.996999979019165
      }
    }
  }
]
```

Python API 三件套：`identify_bytes` 检测内存字节，`identify_path`/`identify_paths` 检测文件（后者批量），`identify_stream` 检测已打开的二进制流（要求可 seek，Magika 会在流里前后跳，用完帮你跳回原位）：

```python
from magika import Magika

m = Magika()
res = m.identify_bytes(b'function log(msg) {console.log(msg);}')
print(res.output.label)   # javascript
print(res.score)          # 0-1 之间的置信分数
```

错误处理与直觉不同：`identify_path` 遇到不存在的文件**不抛异常**，返回一个 `status=FILE_NOT_FOUND_ERROR` 的结果对象，用 `res.ok` 或 `res.status` 判断（源码里注释明说这是 StatusOr 风格，`identify_bytes` 甚至不存在返回错误的代码路径）。正确的防御写法是：

```python
res = m.identify_path(path)
if not res.ok:
    print(res.status)     # FILE_NOT_FOUND_ERROR / PERMISSION_ERROR
else:
    print(res.output.label)
```

对依赖细节敏感的读者：Python 1.x 包的运行时依赖只有 `click` 和 `onnxruntime`（按 Python 版本钉了最低版）；Rust CLI 依赖 clap、colored、crossbeam-channel、serde、anyhow。仓库 main 分支正在开发 Python 2.0：改用 PyO3 直接绑定 Rust 核心，`pyproject.toml` 的 `dependencies` 已清空，即未来 Python 包不再拉 onnxruntime——截至本文复核（2026-10-01）尚未发布，生产环境仍按 1.x 口径评估。

## 模型演进与那些数字该怎么读

Magika 的模型以 `standard_vN` 系列迭代，资产仓库里的 CHANGELOG 记得很清楚：

| 模型 | 时间 | 类型数 | 平均准确率 | 单次推理 |
| --- | --- | --- | --- | --- |
| standard_v1 | 2024 开源时 | ~100 | 99%+ | ~2.6ms |
| standard_v2_1 | 2024 | 200+ | ~99% | ~6.2ms（另有 fast_v2_1：快约 4 倍，98.5%） |
| standard_v3_0 | — | 216 | ~99% | ~2ms |
| standard_v3_1 | — | 216 | ~99% | ~2ms |
| standard_v3_2 | 2025-03 | 216 | ~99% | ~2ms |
| standard_v3_3（当前默认） | 2025-04-11 | 216 | ~99% | ~2ms |

读这批数字有三个前提。

**测的是什么。** "~99%"是 Google 自己测试集上的平均精确率与召回率，自报口径、无独立复现。推理速度是官方在 AMD Ryzen 9 7950X 上"单次调用内 100 次推理取平均"的口径；README 里那个"约 5ms"是更保守的表述（且注明是模型加载后的开销）。两个数字都对，基准不同。

**数字变化反映什么。** v2_1 把类型数翻倍但推理慢了一倍多，v3_0 又拉回 2ms——这是模型结构优化，不是数据问题。v3_1 引入 CutMix 和"随机片段选择"增广，专攻短文本；v3_2 用合成 CSV 数据集修一个具体回归（issue #983）；v3_3 最有意思的增量是理顺了 JavaScript 和 TypeScript 的数据配比后，TypeScript 准确率从 85% 提到 95%——易混淆的同类类型才是这类模型的真正短板。

**不能推出什么。** 99% 是全体类型平均，不代表每个类型都 99%；v3_3 之前 TypeScript 就只有 85%。也不能拿"比现有工具好 20%"直接当成对某个具体工具的胜率——那是 1M 文件基准上的总体口径，且是 v1 时代的数据。选型时最稳的做法还是拿自己的样本集跑一遍：CLI 一条 `magika -r ./samples --jsonl` 就能出全量结果。

## 生产环境里的 Magika

Google 内部的用法是把 Gmail、Drive、Safe Browsing 的文件按类型路由到对应的安全与内容策略扫描器，README 的口径是每周处理数千亿样本。官宣博文补充了两个效果数字：接入后恶意文档扫描器多覆盖 11% 的文件，未识别文件占比降到 3%。

外部集成有两家可查证：VirusTotal 把 Magika 用作 Code Insight 的预过滤器（扫描结果里会带 Magika 的类型判断），恶意软件情报平台 abuse.ch 的样本库同样在用。

多语言绑定的成熟度差异很大，选型前对齐一下：Python（PyPI `magika`，最新 1.0.3，2026-05 发布）最稳；Rust CLI（crates.io `magika-cli`，最新 1.1.0，2026-04）与 Homebrew 分发同步；npm 包 1.0.0 官方自述实验性——官网那个纯浏览器本地推理的 web demo 就是它驱动的，能力够用但 API 可能变；Go 绑定 WIP，还没到能用的时候。

## 采用建议

**适合先上的场景**：上传过滤与网关扫描（text 文件伪装是 libmagic 的盲区，这正是 Magika 增益最大的地方）、CI 里拦截不该出现的可执行文件、数据管道里按真实类型分拣文件。检查可执行文件时注意 label 空间：Windows PE 是 `pebin`、Linux 是 `elf`、macOS 是 `macho`——label 集合以所用模型的 README 为准（216 项全列在 `assets/models/standard_v3_3/README.md`），别凭直觉写 `exe`、`dll` 这类不存在的标签。

**装法怎么选**：CI 和服务器上直接装 Rust 二进制（brew/cargo/安装脚本），无运行时依赖；Python 程序内嵌用 `pip install magika`，代价是拉 onnxruntime（约几十 MB）；前端或浏览器场景用 npm 包并接受实验性标注；等 Python 2.0（PyO3 零依赖）发布后再评估一次 Python 侧的依赖成本。

**别指望它做的事**：输出空间固定 216 类，认不出就老老实实返回 `txt` 或 `unknown`，没有开放集能力；模型训练代码未开源（README 只承诺"客户端与绑定已开源，更多即将到来"），想加自定义类型只能等官方发新模型——好在节奏不慢，standard 系列从 2024 年开源时的 v1 到 2025 年 4 月的 v3_3 已迭代六代。另外再强调一次仓库 README 的自我定位：这不是官方 Google 项目，没有 Google 的支持承诺，生产依赖前把这条计入风险。

## 相关资源

| 资源 | 链接 |
| --- | --- |
| GitHub 仓库 | <https://github.com/google/magika> |
| 官网（Core Concepts 文档） | <https://securityresearch.google/magika/> |
| 研究论文与引用（ICSE 2025） | <https://securityresearch.google/magika/additional-resources/research-papers-and-citation/> |
| 论文 PDF 直链 | <https://securityresearch.google/magika/2025_icse_magika.pdf> |
| 官方开源官宣博文（2024-02） | <https://opensource.googleblog.com/2024/02/magika-ai-powered-fast-and-efficient-file-type-identification.html> |
| 浏览器内 Web Demo | <https://securityresearch.google/magika/demo/magika-demo/> |
| PyPI | <https://pypi.org/project/magika/> |
| npm | <https://www.npmjs.com/package/magika> |
| crates.io | <https://crates.io/crates/magika-cli> |

---

**🦞 作者：钳岳星君 | 来源：GitHub google/magika**
