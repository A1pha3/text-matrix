---
title: "ffmpeg-skill：把「让 Agent 剪视频」从猜 FFmpeg 参数，变成一份可校验的执行契约"
date: "2026-11-20T01:27:19+08:00"
slug: "kajisho5-ffmpeg-skill-verification-driven-video-editing"
description: "ffmpeg-skill 用 42 个本地 FFmpeg 工具、运行时派生的机器可读契约与逐操作验证，把编码 Agent 剪视频这件事从猜参数变成可测量闭环。本文拆解 SPEC 契约派生机制、十条设计铁律、probe-cut-check 工作流与能力探测的三态逻辑，并指出它不做决策的边界。"
draft: false
categories: ["技术笔记"]
tags: ["FFmpeg", "AI Agent", "视频处理", "MCP", "工具契约"]
github_repo: "kajisho5/ffmpeg-skill"
source_key: "gh:kajisho5/ffmpeg-skill"
---

## 核心判断

一个编码 Agent 被要求「把这段视频剪成 15 秒竖版，加字幕」，它的失败方式非常有规律：假设帧率是 30（实际是 29.97）、选了容器装不下的编码器（往 MP4 里塞 VP9）、对一个只需要流拷贝的文件做了全量重编码、然后报告「完成」——从头到尾没有打开过输出文件。

ffmpeg-skill 的判断是：这些错误不是模型能力问题，是**反馈回路缺失**。Agent 生成命令，命令返回 0，它就报告成功；中间没有任何一步强制它去看看产物到底长什么样。

这个项目的解法不是「写更好的 prompt」，而是三件事叠在一起：

1. **一个固定工作流**（probe → 尽量无损编辑 → check → verify），写进 SKILL.md，agent 每次都照做；
2. **42 个类型化工具**，参数是命名选项而不是 shell 字符串拼出来的 filter graph，工具自己负责构造 FFmpeg 命令；
3. **一份机器可读契约**，由工具自己的 argparse 解析器在运行时派生 —— 加一个 flag，契约和 MCP 工具定义自动跟着变，CI 负责挡住漂移。

第三点是这个项目真正值得学的东西。它的作者把这种模式命名为 **SPEC（Self-Producing Execution Contract）**，并且诚实地把它自己的论文《What Is Verification-Driven Coding?》评为「只部分符合自己定义的纪律」。

需要先划清一条边界：**这个 skill 不做决策**。哪一刀该切、这个成片能不能过审、什么算「有意思的高光」、字幕该写什么文字——这些都不在它职责内。它只负责执行与测量，作者把这称为「手」而非「脑」。

截至 2026 年 11 月 20 日，这个仓库有 8234 stars、767 forks，Python 为主，MIT 许可，2026 年 9 月创建，11 月 19 日仍在更新。CI 里测过 FFmpeg 6.1 / 7.1 / 8 / 9 四个版本。

## 系统地图：三层结构

```
SKILL.md            ← agent 每次会话加载：工作流、请求→脚本路由表、一行一个坑
   ↓ 按需读
references/*.md     ← 长文细节（flags.md / workflow.md / gotchas.md）
   ↓ 调用
scripts/*.py        ← 42 个工具，真正干活的地方
   ↓ 派生
scripts/_contract.py ← 运行时从 argparse 生成 input_schema
   ↓ 翻译
mcp/server.py       ← tools/list 由契约翻译而来，不自带 schema
```

这个分层有个实用后果：**SKILL.md 是两层的**。agent 每次会话都加载的那份只保留工作流、路由表和每个坑的一行提示；长文细节放进 `references/`，只在具体任务需要时才读。这是控制上下文开销的直接手段，不是文档洁癖。

## 核心机制：契约从哪来

这是整个项目最值得拆的部分。

工具的 `input_schema` —— 契约里必须与命令行 flag 一一对齐的那部分 —— **从不手工写在代码旁边**。它由运行时从唯一「必须对」的东西派生：**脚本自己的 argparse 解析器**。

具体做法在 `scripts/_contract.py` 的 `_capture_parser()`：它 import 每一个工具脚本，拦截其 `parse_args()` 调用，拿到活着的、完整构建好的 parser 对象 —— flag、类型、choices、默认值、required/positional、互斥组，全都在里面。`input_schema` 直接从这个对象构造。

契约里其它字段来自一张手写表 `TOOL_META`，因为那些事实解析器表达不了：

| 字段 | 来源 | 含义 |
|---|---|---|
| `input_schema` | argparse 派生 | properties、types、enums、defaults、required、positional 顺序、互斥组 |
| `output_schema` | 手写 + 测量 | `--json` 输出什么：`status`、`output`、`commands`、`probe`、`output_identity`（写入文件的 `{size, mtime_ns}`） |
| `role` | `TOOL_META` | `analysis` / `analysis_and_execution` / `execution` / `verification` |
| `capabilities` | `TOOL_META` | 该工具始终需要、以及只在特定 flag 下需要的 FFmpeg 组件 |
| `supports_dry_run` 等 | **由测试测量** | 不是声明的，是测出来的 |

这个分工有讲究：**能被机器测出来的事实，就不要手写声明**。`supports_dry_run`、`supports_json`、`supports_json_brief` 三个字段是测试跑出来的结论，声明与实测不一致时 CI 会挂。

漂移的拦截有两道：

- **运行时**：加一个 flag 到 argparse，`input_schema` 和 MCP 工具定义自动跟着更新，没有第二个文件需要记得改。
- **CI**：`tests/test_contract.py` 每次运行都检查 `TOOL_META` 条目和文档页是否与代码实际行为一致；它**发现漂移，不修漂移**。

MCP 那一层同样不含 schema：`mcp/server.py` 的 `tools/list` 是从契约翻译过来的，工具名、顺序、`inputSchema` 都不可能与脚本漂移 —— 有测试保持两者字节一致。

## 契约里还剩什么

`contract --json` 输出大约 950 KB（`--tool cut` 单个工具约 60 KB），每个工具条目包含：

- `input_schema`：如上，派生而来
- `output_schema`：`--json` 打印的内容，含 `output_identity`（写入文件的 size 与 mtime_ns），这个字段在除 `probe` 外的每个工具上都有
- `role`：四种角色之一
- `capabilities`：需要的编码器、滤镜、bitstream filter
- `provides`：42 个工具各有一个跨仓库的 Capability id（`ffmpeg-skill.cut` 等），供 `AI-video-production-OS` 的 `CapabilityContract.provides` 消费

`doctor` 子命令则是环境侧的体检：读 `ffmpeg -encoders / -decoders / -filters / -bsfs`，报告本机构建里工具需要的组件（libx264、libass、zscale、loudnorm、xfade 等）是否齐备，在任务跑到 ffmpeg 内部才失败之前。

## 三态逻辑：unknown 不是 missing

能力探测里有一条很值得抄的规则：

> **Unknown is not missing.** 当某个 listing 读不出来（解析器不认识的布局、ffmpeg 非零退出），受影响的能力记为 `unknown` —— 绝不是 `missing`，也绝不静默记为 `available`。

这条规则的价值在于区分了三种完全不同的情况：

| 状态 | 含义 |
|---|---|
| `available` | 确认存在 |
| `missing` | 确认不存在 |
| `unknown` | **探测本身失败了** |

一个已安装的滤镜不该被报成缺失；一次失败的探测也不该被算作通过。第二种错误（探测失败当成通过）会直接导致任务在 ffmpeg 内部才炸，而第一种错误会导致明明装了的组件被误报。

同样地，`doctor` 自己的 introspection 调用（`-filters`/`-encoders`/`-bsfs`/`-version`）有 10 秒超时上限，理由写在代码注释里：这里挂起会静默冻结那个专门用来报告「机器坏没坏」的工具。而媒体处理脚本（`cut`、`fit` 等）**不设**这个上限 —— 一次合法的 `--accurate` 重编码长文件本来就可能很久。

## 工作流：八步

SKILL.md 给 agent 的顺序是固定的：

| 步 | 动作 | 关键点 |
|---|---|---|
| 0 | **环境，仅在失败时** | 遇到 `kind: missing_tool` 或 ffmpeg 报错才跑 `doctor`；**绝不作为第一步**，`contract --json` 是给规划器用的 |
| 1 | **Probe 你要依据的东西** | 从实测的时长、fps、分辨率、色彩、音频布局决策，不靠文件名和假设 |
| 2 | **优先无损** | 不需要重编码时不做重编码 |
| 3 | **先 `--dry-run --json` 规划，再执行** | 信任 `--json` 里的数字，不信摘要行 |
| 4 | **串联** | 色彩 → 剪切 → 拼接 → 静音 → 适配 → 字幕/叠加 → 同步 → 音频 → 响度 → 导出；一次交付请求 = 一个 `render.py --template`，三步以上 = 一个 `render.py` project |
| 5 | **Check** | `check.py OUTPUT --platform X --expect-identity S:M`，`S:M` 来自写入方的 `output_identity` |
| 6 | **Verify** | 依据写入方的 `--json` probe 或 `probe.py`：退出码 0 且数字符合要求，否则就是失败 |
| 7 | **保留原件** | 绝不覆盖源文件；`--overwrite` 只用于本次任务的产物或用户明确要求替换的 |
| 8 | **Look** | 任何画面变更后跑 `look.py OUTPUT --tiles 3x2`，看 PNG，在 `Look:` 行里指名那张图；没有视觉能力就说「未检查像素」 |

第 4 步的 `--plan FILE` 机制值得一提：dry run 可以存成 plan，带输入的指纹，`render.py FILE` 之后执行它，**输入变了就拒绝执行**（`render` 和 `verify` 拒绝这个 flag）。这让「先规划后执行」从口头约定变成了有约束的流程。

## 安全约束

README 用三条独立的规则保护源文件：

- **目标与声明的输入相同时拒绝**。不会因为算错了路径就把源文件当输出覆盖。
- **直接编辑需要 `--overwrite`**。覆盖已存在的输出必须显式同意。
- **A `--watch` 的 batch 任务可以替换它上一轮交付过的未变更文件**。这是唯一一条自动覆盖路径，因为它自己知道那个文件是它的产物。

`-y` 在 dry-run 命令里生效，但**只在工具完成目标检查之后**才起作用。

## 十条设计铁律

README 有一节明确写着「这些是 skill 文件给 agent 的规则，代码负责强制执行」。其中最见功力的几条：

**不靠 shell 字符串。** 每个操作是一个带类型化参数的脚本。**没有任何东西经过 shell**，调用方也不能提交 filter graph。

**能力探测先行。** 在任务于 ffmpeg 内部失败之前就知道缺什么。

**验证在执行之后。** 输出被 probe，与目标规格对照，画面变了还要看一眼 contact sheet。

**报告只有一个标签。** 完成是 `Done:`，失败或拒绝是 `Failed:`，部分完成是 `Done:` 加上 `Notes:` 里点明缺口 —— 不存在第三种标签比如 `Done (partially):`。这条规则的作用是消除「部分完成」这个模糊地带的措辞弹性。

**保持原件。** 没有工具会覆盖自己的输入。输出是新文件，命名 `<input>_<operation>.<ext>`，除非另有指示；有一个测试在每次运行后对所有输入做哈希校验。

## 边界：它明确不做什么

README 里有一整节叫「这个 skill 做什么、不决定什么」，把边界写得很清楚：

- **哪一刀该切**、这个交付物能不能过审、什么让一段高光变得「有意思」、字幕该写什么文字 —— 这些属于人、调用方 agent 或另一个 skill。用户的口播文本是**按原样烧录**的，绝不被改写去凑长度。
- **`look.py` 只渲染 PNG**，不检测人脸、产品、主体，也不判断画面里「有意思的部分」。需要保留画面特定区域时，是多模态 agent 看那张 PNG 之后选锚点；非视觉调用方（脚本、没有眼睛看 sheet 的 CLI 用户）必须自己给出这个决定，默认是居中裁切。
- **`scenes.py --highlights` 按测得的代理指标排序**（`--rank-by audio` 或 `--rank-by duration`），不是按内容判断「最好」。
- **`cropdetect.py` 只报告**运动质心，由调用方选裁切框，没有自动重构图。
- **`redact.py` 不找人脸**，框是你给的；`delogo` 是边缘混合，不是 inpainting。

作者把这套关系说得非常清楚：这个仓库是「手」，决定砍哪一刀是「脑」的活，且「脑」坐在它前面而不是里面。依赖是单向的 —— 生态里的其它仓库读它的 `contract --json`、工具的 `--json` 输出和 `doctor`，它不调用它们。

## 生态里的位置

| 你想做什么 | 用哪个 |
|---|---|
| 现在就剪 / 拼 / 测量 / 导出一个文件 | **这个仓库**，独立使用 |
| 决定剪切点、审批交付物、规划整场剪辑 | `video-production-agent` / `AI-video-production-OS` |
| 在一个工作区里搭类型化剪辑图，不写裸 ffmpeg | `video-editing-skill` / `audio-production-skill` |
| 把 Remotion 动效叠到真实录屏上 | `remotion-ffmpeg-skill`（其 composition 从本仓库的 `probe.py`、`silence.py`、`scenes.py` 取长度、fps、帧、静音、场景切换、音频峰值和节拍） |

独立使用只需要 PATH 上有 `ffmpeg` 和 `python3`。不需要云、不需要 API key、不需要 Python 第三方依赖。

## 采用顺序

1. **先装再读**：`npx ffmpeg-skill setup` 一条命令完成 0–2 步（装 skill、装 FFmpeg、跑 `doctor`），它返回 `doctor` 的退出状态。注意它需要 Node 16+ 和 Python 3.10+，且两个都不由它安装。
2. **先看契约再动手**：`npx ffmpeg-skill contract --json | head -40`。这是给规划器读的东西，也是理解 42 个工具边界最快的方式。
3. **拿一个真实小文件走一遍完整八步**，重点看第 8 步的 `look.py` 输出 —— 那是整个方法论的落点，也是最容易被跳过的步骤。
4. **再读 `references/workflow.md` 的「ask/assume」段**。这套工具对「没指定就问」和「没指定就按惯例选并说明」划了界，agent 必须知道边界在哪，否则要么过度提问要么默默瞎猜。
5. **需要自动字幕再装本地语音引擎**（Parakeet 或 whisper 系）。`caption.py --transcribe` 和 `silence.py --transcribe` 在没有引擎时会**打印安装行而不是猜**，两者都接受你已有的转录文本。引擎在你机器上跑，音频不上传。

## 排查：按现象定位

| 现象 | 先查这里 |
|---|---|
| `kind: missing_tool` | 先跑 `scripts/_contract.py doctor`（第 0 步，仅在失败时），看是哪个 FFmpeg 组件缺失 |
| 提示符说组件「缺失」但你明明装了 | 看 `doctor` 输出里的能力是不是 `unknown` —— 探测失败会被如实标为 unknown，不会谎报 missing |
| 画面被裁掉了关键内容 | `fit.py --fit crop --crop-x/--crop-y` 或 `cropdetect.py --motion-centre`，但**锚点得由你或视觉 agent 定**，默认是居中裁切 |
| 剪辑点落在换气或字尾上 | `silence.py` 会报告每个切点的电平并警告；用 `--margin-lead` / `--margin-tail` 或 `--sentence-min-silence` 调整 |
| 导出后时长不对 | `check.py` 的 `basis: guidance` WARN（时长、大小）是平台上传上限，以表格当前值为准；用 `--expect-identity S:M` 比对写入方的 `output_identity` |
| `render.py` 拒绝执行 plan | 输入文件的指纹变了（`size` 或 `mtime_ns`），重新 dry run 生成 plan |
| 报告不知道该不该写 `Look:` | 只有画面变了才需要；音频-only 任务写 `Look: not needed`；没有视觉能力就写「未检查像素」，别假装看过 |

## 参考

- 仓库：<https://github.com/kajisho5/ffmpeg-skill>
- 站点：<https://kajisho5.github.io/ffmpeg-skill/>
- 契约字段参考：<https://github.com/kajisho5/ffmpeg-skill/blob/main/docs/contract.md>
- 位置论文：Kajiyama, S. (2026). *What Is Verification-Driven Coding? — A Discipline for Not Trusting Generation.* Zenodo. <https://doi.org/10.5281/zenodo.23720216>
- npm：<https://www.npmjs.com/package/ffmpeg-skill>
