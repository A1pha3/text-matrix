---
title: "togatoga/karukan 深度拆解：基于 llama.cpp 的 Rust 神经假名汉字转换引擎，跨 Linux/macOS 的日语 IME 全栈方案"
date: "2026-07-01T21:03:00+08:00"
lastmod: "2026-07-01T21:03:00+08:00"
slug: "togatoga-karukan-neural-japanese-ime-architecture"
description: "Karukan 是一个用 Rust 写、基于 llama.cpp 推理 GPT-2 模型的神经假名汉字转换（Neural Kana-Kanji Conversion, NKCC）引擎，配合 fcitx5（Linux）和 Swift InputMethodKit（macOS）前端，提供跨平台日语输入体验。文章拆解其 5 个 crate 的分层、live conversion、context-aware 转换、用户转换学习、Sudachi 系统词典、Mozc 候选改写等核心机制。"
categories: ["技术笔记"]
tags: ["Karukan", "日语IME", "Rust", "llama.cpp", "fcitx5", "InputMethodKit", "NLP"]
draft: false
---

# togatoga/karukan 深度拆解：基于 llama.cpp 的 Rust 神经假名汉字转换引擎，跨 Linux/macOS 的日语 IME 全栈方案

## 读完能回答什么

- 神经假名汉字转换（Neural Kana-Kanji Conversion, NKCC）和传统 IME 的本质差异
- Karukan 的 5 个 crate 是怎么分层的——从 fcitx5 前端到 llama.cpp 推理
- 怎么用 GPT-2 模型做"假名 → 汉字"实时转换——live conversion 怎么工作
- Context-aware 转换：为什么 NKCC 比传统 IME 强
- 用户转换学习（learning）是怎么实现"用户习惯记忆"的
- Sudachi 系统词典的索引结构 + Mozc 候选改写器移植
- emoji 输入的两种 trigger 机制：假名读音 vs Slack 风 `:trigger`
- 怎么在自己的 Rust 项目里嵌入 Karukan 引擎做文本转换

## 目录

1. [为什么又来了一个日语 IME](#为什么又来了一个日语-ime)
2. [定位与核心数字](#定位与核心数字)
3. [整体架构：5 个 crate 的分层](#整体架构5-个-crate-的分层)
4. [核心机制 1：GPT-2 神经假名汉字转换](#核心机制-1gpt-2-神经假名汉字转换)
5. [核心机制 2：用户转换学习](#核心机制-2用户转换学习)
6. [核心机制 3：系统词典与候选改写](#核心机制-3系统词典与候选改写)
7. [emoji 输入：双 trigger 机制](#emoji-输入双-trigger-机制)
8. [Linux 前端：fcitx5 addon + C FFI](#linux-前端fcitx5-addon--c-ffi)
9. [macOS 前端：Swift + InputMethodKit](#macos-前端swift--inputmethodkit)
10. [karukan-cli 工具链](#karukan-cli-工具链)
11. [典型问题与边界](#典型问题与边界)
12. [适用人群](#适用人群)
13. [场景问答（FAQ）](#场景问答faq)
14. [自测题](#自测题)
15. [练习](#练习)
16. [进阶路线](#进阶路线)
17. [总结](#总结)

---

如果你在 Linux/macOS 上做日语输入，你大概率在用：

- **macOS**——系统自带 IME（基于 Mozc 的某个旧 fork）
- **Linux**——fcitx5 + Mozc 或 fcitx5 + Anthy
- **Windows**——Google 日本語入力 或 Microsoft IME

**Mozc 是事实标准**——但它有几个被诟病的问题：
1. **C++ 维护负担重**——Mozc 主仓库 build system 复杂，issue 响应慢
2. **架构僵化**——十几年前的设计，新功能加不进去
3. **AI 集成弱**——纯 N-gram + CRF 模型，对长上下文理解差
4. **macOS 支持是"附带"**——Mozc 的 macOS 移植不是 Google 官方维护

而 **Neural IME 方向**（用 LLM 做 Kana-Kanji 转换）这两年有几个开源尝试：
- **Zenzai**（by Yasuaki Kudo）——基于 C++ 的 NKCC for fcitx5
- **llama.cpp + llama-cpp-python + custom IME frontend**（各家实现）

**Karukan 的差异点**：
1. **纯 Rust 引擎**——不依赖 Python 也不依赖 C++ 之外的复杂运行时
2. **跨平台前端完整实现**——fcitx5 (Linux) + Swift/InputMethodKit (macOS) 两条路都做
3. **完整工具链**——Sudachi 词典生成、字典 viewer、HTTP server、AJIMEE-Bench 自带
4. **多 crate 拆分**——引擎、前端、CLI 各自独立，可以单独嵌入

## 二、定位与核心数字

| 维度 | Karukan | 备注 |
|---|---|---|
| 仓库 | togatoga/karukan | 531 stars / 30 forks（截至 2026-07） |
| 主语言 | Rust（核心）+ Swift（macOS 前端） + C FFI | 多语言混合 |
| 运行时 | 纯 Rust + llama.cpp（动态链接） | 无 Python |
| 模型 | GPT-2（基于 llama.cpp 推理） | 体积小，本地可跑 |
| 词典 | SudachiDict 系统词典 | 业界标准 |
| 候选改写 | 从 Mozc 移植 | 包含"半角片假名"等 |
| emoji | 假名读音 + Slack 风 `:trigger` | 双 trigger |
| 许可证 | MIT OR Apache-2.0 | 双重许可 |
| 平台 | Linux（fcitx5） + macOS（InputMethodKit） | 两条路 |
| 工具 | 字典构建、HTTP server、AJIMEE-Bench | CLI 工具链 |

> **重要边界**：Karukan 不是一个"开箱即用的输入法官网下载"——它是一个**引擎 + 前端 + 工具链的完整开源实现**。终端用户需要自己编译、自己装模型。这对开发者和研究者友好，但对普通用户门槛偏高。

## 三、整体架构：5 个 crate 的分层

Karukan 的工程结构是教科书级的"crate 拆分"：

```
┌──────────────────────────────────────────────────────────────────┐
│  karukan-fcitx5    Linux IME 前端 — fcitx5 addon + C FFI           │
├──────────────────────────────────────────────────────────────────┤
│  karukan-macos     macOS IME 前端 — Swift + InputMethodKit         │
├──────────────────────────────────────────────────────────────────┤
│  karukan-im        共享 IME 引擎 — 状态机 + ローマ字変換 +         │
│                    karukan-imserver (macOS 用 JSON-RPC server)     │
├──────────────────────────────────────────────────────────────────┤
│  karukan-engine    核心库 — ローマ字→ひらがな + llama.cpp 神经     │
│                    假名汉字转换                                     │
├──────────────────────────────────────────────────────────────────┤
│  karukan-cli       CLI 工具 — 字典构建、Sudachi 字典生成、         │
│                    字典 viewer、AJIMEE-Bench、HTTP server           │
└──────────────────────────────────────────────────────────────────┘
```

### 3.1 各 crate 职责

| Crate | 职责 | 关键技术 |
|---|---|---|
| **karukan-engine** | 核心转换逻辑 | ローマ字→ひらがな 转换表 + llama.cpp 推理 |
| **karukan-im** | 共享 IME 引擎 | 状态机（composition/preedit/commit）+ JSON-RPC server |
| **karukan-fcitx5** | Linux 前端 | fcitx5 addon 协议 + C FFI |
| **karukan-macos** | macOS 前端 | Swift + InputMethodKit + 与 karukan-imserver 通信 |
| **karukan-cli** | 工具链 | 字典构建 + HTTP server + bench |

**关键设计**：macOS 前端**不直接调用 llama.cpp**——而是通过 JSON-RPC 调 `karukan-imserver`。这有两个好处：
1. macOS 前端是 Swift，**lama.cpp 是 C++ 库，混编很痛**——独立 server 隔离了语言边界
2. 多个 macOS app 可以共享同一个 karukan 引擎进程

### 3.2 数据流

```
用户键入 "k" "y" "o" "u"
   ↓
fcitx5 / InputMethodKit 捕获键事件
   ↓
karukan-im: 状态机更新 composition 字符串
   ↓
karukan-engine: ローマ字→ひらがな = "きょう"
   ↓
karukan-engine: llama.cpp 推理 NKCC = ["今日", "今日", "京", "教", ...]
   ↓
Mozc 候选改写器: "今日" → 添加 "きょう（今日）" + 半角片假名 "ｷｮｳ" 等相关候选
   ↓
UI 弹出候选列表
   ↓
用户选 "今日" → commit 到应用
```

## 四、核心机制 1：GPT-2 神经假名汉字转换

### 4.1 为什么是 GPT-2

Karukan 选择 GPT-2（小模型，几百万到几千万参数）而不是 Llama / Qwen 等大模型，核心原因：
1. **实时性**——输入法转换延迟必须 < 50ms（用户感知阈值），大模型推理做不到
2. **本地化**——隐私敏感用户不愿意把键入内容发到云端
3. **体积**——GPT-2 small 模型 FP16 约 500 MB，量化后 ~ 150 MB，llama.cpp 在 MacBook Air 上能跑

llama.cpp 提供了**纯 C++ 的 transformer 推理**——Karukan 通过 Rust FFI 绑定它，**避免了 Python onnxruntime / pytorch 的运行时依赖**。

### 4.2 NKCC 的 prompt 结构

神经 IME 的核心是把"假名 → 汉字候选"建模为"语言模型下一个 token 预测"：

```text
# 输入
context_before: 今日は
input: きょう
context_after: が良い天気です
# 输出（按概率排序）
candidates:
  - 今日   (0.62)
  - 強     (0.15)
  - 教     (0.08)
  - 京     (0.05)
  - ...
```

**注意 context_before / context_after**——这就是 **context-aware 转换**。传统 N-gram IME 只看输入字符串本身；NKCC 模型看**完整上下文**。

举例：
- 输入 "ashita"——传统 IME 不知道是"明日"还是"あした"（同音异字）
- 输入 "明日のashita"——Karukan 通过 context_after "明日" 直接锁定候选

### 4.3 Live Conversion（实时转换）

Karukan 的 live conversion（`Ctrl+Shift+L` 切换）是 NKCC 的**杀手特性**：

- **传统 IME**：用户输入假名 → 按 Space → 弹出候选 → 选
- **Live conversion**：用户输入假名时**实时显示转换结果**，Space 只是"确认当前选中的候选"

```text
输入: "konnichiwa"
  └─ 实时: こんにちは (konnichiwa)  ← 边输入边显示
  └─ 输入 "ha" → こんにちはは
  └─ 实时: こんにちはは (konnichiwa wa)  ← 上下文知道 "wa" 在这里是助词
```

**对用户的体感差异**：
- 传统 IME——每输入 4-6 字符需要按一次 Space
- Live conversion——**几乎不用按 Space**，只在需要切换候选时按

这是 Karukan 最被日文输入重度用户夸赞的特性。

## 五、核心机制 2：用户转换学习

NKCC 模型再强，也没法预测**某个具体用户的用词偏好**——比如一个程序员可能经常输入"バグ"（bug），但通用 GPT-2 不一定排第一。

Karukan 的**用户转换学习**机制：

### 5.1 候选优先排序

```text
1. 用户选过的候选 → 提到第一位
2. 输入前缀匹配的学习候选 → 显示在第二组（预测转换）
3. NKCC 模型的 top-k 候选 → 主列表
```

**举例**：
- 用户每次输入 "ぷろぐらむ" 都选 "プログラム"
- 5 次后 Karukan 在你刚输入 "ぷろ" 时就把 "プログラム" 列在预测区

### 5.2 预测转换（前缀匹配）

不只是"完全匹配后学习"，**输入到一半就开始推荐**：

```text
已学: ユーザー → 选了 5 次
输入: "ゆーざ" → 预测区显示 "ユーザー"
输入: "ゆーざー" → 预测区显示 "ユーザー"
```

### 5.3 学习数据存储

学习数据应该是本地 SQLite（推测，未在 README 明确写），每次 commit 候选时更新。用户数据完全本地，不上传。

## 六、核心机制 3：系统词典与候选改写

### 6.1 Sudachi 系统词典

Karukan 使用 **SudachiDict**（Works Applications 开发的日语形态素词典）作为系统词典：

- **覆盖面广**——SudachiDict 是日语最完整的开源词典之一
- **可索引**——Karukan 自己从 SudachiDict 源数据构建索引（karukan-cli 提供 `build-dict` 命令）

**为什么不用 NAIST-jdic / IPADIC**——这些传统词典分词粒度粗，NKCC 时代需要更细粒度的形态素。

### 6.2 Mozc 候选改写器（移植）

Karukan 把 Mozc 的 **candidate rewriter** 移植到 Rust。改写器的作用是**基于主候选生成"相关候选"**：

| 类型 | 例子 | 注释 |
|---|---|---|
| 半角片假名 | きょう → ｷｮｳ | "半角カタカナ" |
| 全角/半角切换 | abc → ＡＢＣ / abc | "全角" / "半角" |
| 大写/小写 | ＥＮＧ → eng | "小文字" |
| 数字变体 | 12 → 十二 / Ⅻ / ⑫ | "漢数字" / "ローマ数字" / "丸数字" |
| 进制 | 255 → 0xFF / 0b11111111 / 0377 | "16進数" / "2進数" / "8進数" |
| 符号 | けい → ㈱ | "記号" |

**这部分的实现质量决定 IME 的"工业感"**——Karukan 直接从 Mozc 移植，意味着这一块达到了 Mozc 同等水准。

## 七、emoji 输入：双 trigger 机制

### 7.1 假名读音

```text
输入: ぴえん → 🥺 (哭泣脸)
输入: きんにく → 💪 (肌肉)
输入: うっしっし → 🐛 (毛毛虫)
```

**支持范围**——常见日语 emoji 文化映射（ぴえん系、くあ系、动物叫声等）。这部分需要持续维护 emoji 数据库。

### 7.2 Slack 风格 trigger

```text
输入: :smile → 😄
输入: :halo → 😇
输入: :fire → 🔥
```

和 Slack / GitHub / Discord 的 `:emoji_code:` 兼容。

**两种机制并存**——给用户两种触发方式：日语用户习惯假名，国际用户习惯 `:trigger:`。

## 八、Linux 前端：fcitx5 addon + C FFI

### 8.1 fcitx5 addon 协议

fcitx5 是 Linux 上最主流的输入法框架，addon 需要实现：

```c
// 必需接口
FcitxInstance* create_instance();
void reload_config();        // 配置重载
void trigger_property();     // 属性切换
void process_key_event();    // 键事件处理
void commit_string();        // commit 字符串到应用
```

### 8.2 Karukan 怎么做

- `karukan-fcitx5` crate 实现 fcitx5 addon 接口
- 通过 **C FFI** 调用 `karukan-im` 共享引擎
- 引擎进程内启动 llama.cpp 推理（避免跨进程通信开销）

### 8.3 安装路径（典型 Ubuntu）

```bash
# 编译
cargo build --release -p karukan-fcitx5

# 复制到 fcitx5 addon 目录
cp target/release/libkarukan_fcitx5.so /usr/lib/x86_64-linux-gnu/fcitx5/

# 配置 fcitx5
mkdir -p ~/.config/fcitx5/conf
cat > ~/.config/fcitx5/conf/karukan.conf <<EOF
[Addon]
Name=karukan
EOF

# 重启 fcitx5
fcitx5 -r
```

## 九、macOS 前端：Swift + InputMethodKit

### 9.1 InputMethodKit

macOS 提供的官方 IME 开发框架，Swift / Objective-C 都能用。

### 9.2 Karukan 怎么做

- `karukan-macos` crate 是 Swift 包
- 不直接调 llama.cpp——通过 **JSON-RPC 调 `karukan-imserver`**
- 这种"前后端分离"设计避免了 Swift/C++ 混编的复杂度

### 9.3 通信协议

```json
// request
{
  "method": "convert",
  "params": {
    "context_before": "今日は",
    "input": "きょう",
    "context_after": "が"
  }
}

// response
{
  "result": {
    "candidates": [
      {"surface": "今日", "reading": "きょう", "score": 0.62},
      {"surface": "強", "reading": "きょう", "score": 0.15},
      ...
    ]
  }
}
```

## 十、karukan-cli 工具链

### 10.1 字典构建

```bash
# 从 SudachiDict 源数据构建系统字典
karukan-cli build-dict --input sudachidict/ --output dict.bin

# 查看字典内容
karukan-cli view-dict dict.bin --entry きょう
```

### 10.2 AJIMEE-Bench 自带评测

```bash
# 在标准 NKCC 评测集上跑分
karukan-cli bench --model karukan-gpt2.gguf --dataset ajimee-bench.json
```

### 10.3 HTTP server（debug 用）

```bash
# 启动 HTTP server，浏览器调试候选
karukan-cli serve --port 8080
# 访问 http://localhost:8080 输入假名看候选
```

## 十一、典型问题与边界

### 11.1 当前局限

- **模型只有 GPT-2**——和 Zenzai 用的 Llama 3 / Mistral 相比，精度上限较低
- **首启动慢**——首次从 Hugging Face 下载模型需要时间
- **macOS 配置复杂**——需要自己编译 karukan-imserver + 注册 Input Method
- **学习数据迁移**——没有跨设备同步（这是设计选择，隐私优先）
- **Windows 不支持**——只有 Linux (fcitx5) + macOS (InputMethodKit)

### 11.2 与其他日语 IME 的取舍

| 工具 | 优势 | 劣势 | 适合 |
|---|---|---|---|
| **Karukan** | Rust + GPT-2 + 完整工具链 | 需自编译 | 开发者 / 研究者 |
| **Zenzai** | 大模型 (Llama 3) NKCC | C++ 复杂 | 高精度用户 |
| **Mozc** | 工业级稳定 + 跨平台 | 不支持 NKCC | 普通用户 |
| **macOS 系统 IME** | 免配置 | 不支持 NKCC | macOS 普通用户 |
| **fcitx5-anthy** | 纯 CPU 轻量 | 老旧 / 精度差 | 极低配置机器 |

## 十二、适用人群

**强推荐**：
- **Rust 开发者**——想给自己的文本处理 pipeline 嵌入 NKCC 引擎（karukan-engine crate 独立可用）
- **日语 NLP 研究者**——研究 NKCC、live conversion、context-aware 转换
- **macOS 重度用户**——对系统自带 IME 不满意，又不想用付费日语输入法的
- **fcitx5 + AI 实验者**——想在 fcitx5 框架下跑通 NKCC

**谨慎采用**：
- **普通日语用户**——Mozc 仍是 2026 年的"省心"选择
- **需要 100% 准确率**——NKCC 永远不如手动选词，Karukan 在长难句上仍会出错
- **Windows 用户**——不支持

**不建议**：
- **企业生产环境**——Karukan 是个人项目，没有 SLA
- **离线场景但需要大模型**——GPT-2 在这种场景下精度不够

---

## 场景问答（FAQ）

**Q：Karukan 需要多大的内存？GPT-2 模型跑得动吗？**

GPT-2 small 模型 FP16 约 500 MB，量化后 ~150 MB。推理时需要额外内存存放上下文（取决于输入序列长度）。建议：macOS 上 8 GB 内存就够了（Apple Silicon 的 GPU 内存共享帮忙）；Linux 上建议 16 GB 内存（纯 CPU 推理）。

**Q：live conversion 的延迟真的能 < 50ms 吗？实测条件是什么？**

README 里提到的 < 50ms 是用户感知阈值，不是 GPT-2 推理延迟。实际流程：键入 → roma字转换（查表，< 1ms）→ GPT-2 推理（10-50ms，取决于硬件）→ 候选排序（< 1ms）。在 Apple Silicon (M1/M2/M3) 上，用 llama.cpp 的 Metal 加速，GPT-2 推理延迟约 10-30ms；在纯 CPU 上可能到 50-100ms。

**Q：用户转换学习的数据存在哪里？能导出或同步吗？**

推测是本地 SQLite（README 未明确写）。目前没有跨设备同步机制——这是设计选择，隐私优先。如果你需要在多台设备上共享学习数据，目前只能手动备份数据库文件。

**Q：Karukan 能用在 Fcitx5 之外的输入法框架吗？**

目前只支持 Fcitx5 (Linux) 和 InputMethodKit (macOS)。Windows 不支持，Wayland 用 XWayland 兼容模式。如果你需要其他框架（如 IBus），需要自己实现前端——karukan-engine crate 是独立的，可以嵌入。

**Q：Mozc 候选改写器移植完整吗？所有 Mozc 的改写规则都在吗？**

README 未明确说明完整度。但既然选择"移植"而不是"重写"，核心改写规则（半角片假名、全角/半角切换、大写/小写、数字变体、进制、符号）应该都覆盖了。如果你发现某个改写缺失，可以提 issue 或 PR。

---

## 自测题

读完这篇文章，试试回答下面 5 道题：

1. **Karukan 的 5 个 crate 中，哪个 crate 负责"ローマ字→ひらがな"转换？为什么 macOS 前端不直接调用 llama.cpp？**

   <details>
   <summary>点击查看参考答案</summary>
   
   - karukan-engine crate 负责"ローマ字→ひらがな"转换（查表）和 llama.cpp 推理 NKCC。
   - macOS 前端不直接调用 llama.cpp 是因为：llama.cpp 是 C++ 库，Swift/C++ 混编很痛；独立 JSON-RPC server (karukan-imserver) 隔离了语言边界，且多个 macOS app 可以共享同一个 karukan 引擎进程。
   </details>

2. **Context-aware 转换和传统 N-gram IME 的核心差异是什么？举一个具体例子。**

   <details>
   <summary>点击查看参考答案</summary>
   
   - 传统 N-gram IME 只看输入字符串本身；NKCC 模型看完整上下文（context_before 和 context_after）。
   - 具体例子：输入 "ashita"——传统 IME 不知道是"明日"还是"あした"（同音异字）；输入 "明日のashita"——Karukan 通过 context_after "明日" 直接锁定候选。
   </details>

3. **Live conversion 的用户体感差异是什么？为什么它能减少按键次数？**

   <details>
   <summary>点击查看参考答案</summary>
   
   - 传统 IME：用户输入假名 → 按 Space → 弹出候选 → 选
   - Live conversion：用户输入假名时实时显示转换结果，Space 只是"确认当前选中的候选"
   - 体感差异：传统 IME 每输入 4-6 字符需要按一次 Space；Live conversion 几乎不用按 Space，只在需要切换候选时按。
   </details>

4. **用户转换学习的三种机制是什么？各举一个例子。**

   <details>
   <summary>点击查看参考答案</summary>
   
   - 候选优先排序：用户选过的候选 → 提到第一位
   - 预测转换（前缀匹配）：输入到一半就开始推荐（如已学"ユーザー" → 输入"ゆーざ"时预测区显示）
   - 学习数据存储：每次 commit 候选时更新（推测是本地 SQLite）
   </details>

5. **Karukan 和 Mozc 的核心差异是什么？什么场景选 Karukan，什么场景选 Mozc？**

   <details>
   <summary>点击查看参考答案</summary>
   
   - 核心差异：Mozc 是 C++ N-gram + CRF 模型；Karukan 是 Rust + GPT-2 神经模型。Karukan 的 NKCC 对长上下文理解更强，但模型精度上限受 GPT-2 限制。
   - 选 Karukan：开发者/NLP 研究者、macOS 重度用户、想嵌入 NKCC 引擎到自己的产品
   - 选 Mozc：普通用户、需要 100% 准确率、Windows 用户
   </details>

---

## 练习

### 练习 1：编译 Karukan 并跑通 Linux (fcitx5) 前端

**任务**：在 Linux 上编译 Karukan 的 fcitx5 前端，并配置一个日语输入测试环境。

**步骤**：
1. 安装 Rust toolchain 和 fcitx5 开发库（`sudo apt install fcitx5 fcitx5-modules libfcitx5-dev` on Ubuntu）
2. `git clone https://github.com/togatoga/karukan`
3. `cargo build --release -p karukan-fcitx5`
4. 复制 `target/release/libkarukan_fcitx5.so` 到 fcitx5 addon 目录
5. 配置 fcitx5 添加 Karukan 作为输入法
6. 下载 GPT-2 模型（参考 README 的模型下载说明）
7. 测试输入：启动 fcitx5，切换到 Karukan，输入"こんにちは"

### 练习 2：在 macOS 上配置 Karukan 并测试 live conversion

**任务**：在 macOS 上编译 Karukan 的 macOS 前端，并测试 live conversion 特性。

**步骤**：
1. 安装 Xcode 和 Command Line Tools
2. `git clone https://github.com/togatoga/karukan`
3. 编译 karukan-imserver（`cargo build --release -p karukan-im`）
4. 编译 macOS 前端（参考 `karukan-macos` 目录的构建说明）
5. 注册 Karukan 为输入法（系统设置 → 键盘 → 输入法 → 添加）
6. 启用 live conversion（Ctrl+Shift+L 切换）
7. 测试：输入"きょうは"看是否实时转换为"今日は"

### 练习 3：用 karukan-cli 构建系统词典

**任务**：用 karukan-cli 从 SudachiDict 源数据构建系统词典。

**步骤**：
1. 下载 SudachiDict 源数据（参考 SudachiDict GitHub 的下载说明）
2. 运行 `karukan-cli build-dict --input sudachidict/ --output dict.bin`
3. 验证词典：`karukan-cli view-dict dict.bin --entry きょう`
4. 把构建好的词典配置到 Karukan（参考 README 的词典配置说明）

---

## 进阶路线

1. **入门**：在 Linux 或 macOS 上编译并跑通 Karukan，理解 5 个 crate 的分层架构
2. **应用**：在日常日语输入中用 Karukan 替代 Mozc，对比体感差异（尤其是 live conversion）
3. **定制**：配置用户转换学习，观察"预测转换"是否准确
4. **深入**：阅读 `karukan-engine` crate 的源码，理解"ローマ字→ひらがな"转换表和 llama.cpp 推理的集成
5. **扩展**：尝试为 Karukan 添加一个新的候选改写规则（参考 Mozc 候选改写器的实现）
6. **嵌入**：在自己的 Rust 项目里嵌入 karukan-engine crate，做文本转换（如 chatbot 候选、邮件自动补全）
7. **贡献**：找一个 good first issue，提交 PR——Karukan 是个人项目，社区贡献欢迎

---

## 十三、总结

Karukan 是 2026 年开源日语 IME 领域**最值得关注的"纯 Rust + 神经模型 + 跨平台"项目**：

1. **5 个 crate 的清晰分层**——engine / im / fcitx5 / macos / cli 各司其职，可独立嵌入
2. **GPT-2 + llama.cpp**——纯本地、纯 Rust、零 Python 运行时
3. **Live conversion**——边输入边转换，体感远胜传统 Space-then-select
4. **Context-aware NKCC**——模型看完整上下文，不是 N-gram
5. **用户学习 + 预测转换**——把"个人用词习惯"内化到模型之上
6. **Sudachi 词典 + Mozc 候选改写移植**——词典和改写器都达到工业级
7. **双 trigger emoji**——假名读音 + Slack `:trigger:` 兼容

它的**最大价值**不是"代替 Mozc"——而是**给开发者一套可嵌入的 Rust NKCC 引擎**。如果你的产品需要日语文本转换（chatbot 候选、邮件自动补全、笔记 app 智能输入），**karukan-engine crate 几乎是不二之选**。

对终端用户，Karukan 的"自编译"门槛让它在短期内不会成为主流；但对**想把 NKCC 嵌入自己产品的工程师**，它是一个**值得认真评估的开源起点**。

---

**仓库**：<https://github.com/togatoga/karukan>
**macOS 安装**：<https://github.com/togatoga/karukan/tree/main/karukan-macos>
**Linux (fcitx5) 安装**：<https://github.com/togatoga/karukan/tree/main/karukan-fcitx5>
**karukan-engine crate**（独立可用）：<https://github.com/togatoga/karukan/tree/main/karukan-engine>
**SudachiDict 源数据**：<https://github.com/WorksApplications/SudachiDict>
