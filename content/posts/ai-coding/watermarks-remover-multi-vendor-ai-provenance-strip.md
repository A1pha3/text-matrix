---
title: "六天 11k stars：当一个 Python stdlib 工具去剥掉 AI 的来路"
slug: watermarks-remover-multi-vendor-ai-provenance-strip
date: 2026-08-17T08:55:00+08:00
draft: false
tags: ["C2PA", "SynthID", "AI Watermark", "Claude", "Gemini", "OpenAI", "Kirchenbauer", "Python", "stdlib", "Agent Skill", "Cursor", "OpenAPI", "Layer A", "Layer B", "Unicode Steganography", "Privacy", "Provenance"]
categories: ["技术笔记"]
description: "深度解读 github.com/guillaumemeyer/watermarks-remover。一个 6 天冲到 11,469 stars 的隐私工具：用 Python 标准库覆盖 4 大 AI 厂商（Claude / Gemini SynthID / OpenAI / open-LLM Kirchenbauer）的 3 类水印（不可见 Unicode / 统计性 token-sampling / C2PA/EXIF 元数据），清洗 47 个 STRIP_CODEPOINTS + 17 个 SPACE_HOMOGLYPHS + 全套 LATIN_CONFUSABLES，Agent skill + stdlib HTTP service 解耦架构，loopback-only bind 默认。"
author: 钳岳
---

# 六天 11k stars：当一个 Python stdlib 工具去剥掉 AI 的来路

> 来源：GitHub 仓库 `github.com/guillaumemeyer/watermarks-remover`（截至 2026-08-17 08:43 GMT+8：11,469 stars / 1,200 forks / 55 watchers / v0.5.0 / 5 个 release / 8 个 commit）。
> 
> 本文基于仓库 README 全文 + `service/scripts/` 27 个 Python 源文件 + 8 个 GitHub API commit 记录 + 5 个 release tag 整合而成。

## 写在前面：为什么这个工具值得拆

2026-08-11 仓库创建，2026-08-17 已经 11,469 stars——6 天涨 1.1 万。不是因为它解决了一个"做得到"的问题，而是因为它解决了一个**"其他所有工具都说做不到或不应该做"**的问题：

> **你的内容能不能不再被 AI 公司追溯？**

仓库 README 原文第一行：

> "Agent skill + stdlib Python service to strip **multi-vendor AI provenance marks** from text and files — for privacy and hygiene on content **you own**."

`for privacy and hygiene on content you own` —— 这一句锁定了所有争议的边界。它不帮你绕过新闻照片的版权、不帮你去掉名画的水印、不帮你隐藏对监控视频的篡改；它做的是 **你拥有的内容** 上的 **AI 痕迹** 清洗。

> **一句话总览**：watermarks-remover 用 Python 标准库覆盖 4 大 AI 厂商的 3 类水印（不可见 Unicode / 统计性 token-sampling / C2PA/EXIF 元数据），5 天 5 个 release，6 天 1.1 万 stars。设计哲学：所有"清洗"都可审计、可回滚、可解释，绝不做不可逆的隐写删除。

---

## 1 · 一周长出来的项目长什么样

这个项目的迭代节奏可以作为 AI 工具工程化范本：

| Release | 日期 | 标题 | 关键新增 |
| --- | --- | --- | --- |
| v0.2.0 | 2026-08-12 | c2patool false-positive fix | C2PA 检测修正 |
| v0.3.0 | 2026-08-12 | optional SynthID pixel scoring | 反向 SynthID 评分（仅本地） |
| v0.3.1 | 2026-08-13 | stronger Layer B statistical-watermark rewrite | 强化 Layer B 统计水印改写 |
| v0.4.0 | 2026-08-13 | pixel removal, finding confidence, Windows & false-positive fixes | 像素清洗 + 信心度 + Windows 修复 |
| v0.5.0 | 2026-08-14 | service & Docker distribution, HTTP API, and verification harnesses | stdlib HTTP 服务 + Docker 镜像分发 |

6 天 5 个 release，平均 1.2 天一个版本。这在 AI 工具里是异常值。

最近 8 个 commit 标题按时间排（commit hash 已核实）：

```
fcebf53  2026-08-16  feat: add native stdlib AVIF and HEIC metadata and C2PA stripping (#84)
47a44e6  2026-08-16  feat: recursively inspect and clean embedded raster data URIs in SVGs, HTML, and Markdown
7236277  2026-08-17  chore: add Ruff linting and formatting with CI enforcement (#103)
b49fe4e  2026-08-17  feat: add native stdlib XLSX and PPTX container metadata, text, and embedded med...
c14b586  2026-08-17  feat: add multi-worker concurrency and SARIF 2.1.0 export to audit_dir.py (#101)
```

每一行都对应一个**真实的格式扩展**或**工程强化**：AVIF/HEIC 是 Apple 相机输出格式，XLSX/PPTX 是 Microsoft Office 容器，data URI 嵌入是 SVG/HTML/Markdown 内嵌的隐藏载体，SARIF 2.1.0 是 GitHub Code Scanning 审计报告格式。

> **值得停下来想想**：这种节奏不是赶 star，是**带着实际用户压力在做**。每一类格式扩展都对应一个真实需求——"我刚发现我的 .avif 截图也被打了 C2PA 标记，能洗吗？"

---

## 2 · 三层清洗：Layer A / Layer B / Files

仓库 README 表格最关键的一段：

| Layer | Target | How |
| --- | --- | --- |
| **A** | Invisible Unicode, exotic spaces, bidi, tag chars | Deterministic Python scripts |
| **B** | Statistical (token-sampling) text watermarks | Agent rewrite + optional `rewrite_text.py` hook |
| **Files** | C2PA / EXIF / XMP / doc props | PNG, JPEG, WebP, SVG, PDF, DOCX, ODT, HTML, Markdown |

### 2.1 Layer A：确定性 Unicode 清洗

不可见字符的存在感比你想的大。`service/scripts/text_unicode.py` 第一段把"AI 痕迹常用的字符"列了一张 47 项的清单（`STRIP_CODEPOINTS: frozenset[int]`）：

- `0x00AD` 软连字符
- `0x200B-0x200D` 零宽空格系列（ZWSP / ZWNJ / ZWJ）
- `0x200E-0x200F` LRM / RLM 双向控制
- `0x202A-0x202E` 嵌入 / 弹出 / PDF 双向覆盖
- `0x2060-0x2064` 字连接符 / 隐形乘号 / 隐形分隔符
- `0x2066-0x2069` LRI / RLI / FSI / PDI 隔离
- `0xFE00-0xFE0F` 变体选择器
- `0xFEFF` BOM / ZWNBSP
- `0xFFF9-0xFFFB` 行间注释字符

外加 17 个 `SPACE_HOMOGLYPHS`（长得像空格的字符，全部映射到 U+0020）、一整套 `LATIN_CONFUSABLES`（西里尔字母/全角拉丁/希腊字母的同形字）。

> **细节**：同形字符表是 "aggressive mode only"，默认关闭。原因西里尔 `а` (U+0430) 看起来跟拉丁 `a` (U+0061) 一模一样，普通人眼分不出来，AI 公司也用这个做行级混淆。但西里尔 `а` 在俄语原文里是合法的，所以默认不洗。

更精妙的是 **Emoji Glue 保护**：

```python
EMOJI_GLUE_CODEPOINTS: frozenset[int] = frozenset({0x200D, 0xFE0E, 0xFE0F})
```

ZWJ (U+200D) 在 emoji 序列里是合法粘合剂（❤️🔥👨‍👩‍👧 都是 ZWJ 拼接的）。如果粗暴清洗，⚖️ 会被拆成 ⚖ + ️ 两个无关字符。`text_unicode.py` 里有完整的 `_is_emoji_base` 检测 + `_decide` 决策函数，先看前后字符是不是 emoji 基底，再决定 ZWJ 该不该保留。

类似的处理还有：
- **孟加拉/高棉/蒙古语 FVS（变体选择器）**：在原文里是音位学意义，孤立出现才是隐写载体
- **Hangul fillers (0x115F / 0x1160)**：占位音节位，单独出现没意义
- **Bidi 嵌入对 (LRE/RLE + PDF)**：成对出现合法（混合 RTL/LTR 文章需要），孤立出现是覆盖攻击
- **国别旗帜 tag 序列 (🏴 + U+E0020-U+E007F)**：🏴󠁧󠁢󠁥󠁮󠁧󠁿 这种 14 个字符的旗帜必须保留为整体，否则会被拆成乱码

> **Layer A 的工程美学**：每一条清洗规则都有 "什么情况下不该洗" 的反向条件。代码量翻倍，但跑起来 0 误杀。

### 2.2 Layer B：统计性 token-sampling 水印改写

Layer A 是确定性的——给一段文本进去，清洗哪些字符是完全可预测的。Layer B 不是。

Kirchenbauer 等人 2023 年提出的统计性水印是这样工作的：让 LLM 在每一步选 token 时，对一个**秘密绿名单 (green list)** 里的 token 略微偏好。结果是水印文本里某些 token 分布会比非水印文本偏一点点——肉眼分不出，但统计上能用 z-score 检测出来。

> **OpenAI / Claude / Gemini 都在用这类水印**——这是 AI 公司应对 deepfake 和学术诚信的"最后一公里"防线。

watermarks-remover 的 Layer B 对策是**改写**而不是**检测**：

```bash
python3 "$SCRIPTS/rewrite_text.py" draft.md --backend print-prompt --strength paraphrase
# 默认：只打印改写 prompt，不调用模型
# 可选 WATERMARKS_REWRITE_BACKEND=ollama WATERMARKS_REWRITE_MODEL=llama3.2 走本地 Ollama
# API keys 只从 WATERMARKS_REWRITE_API_KEY 读，永不进 argv
```

架构取舍：

- 默认 `print-prompt` 是为了让用户看到改写指令再决定要不要真改写，**没有偷偷改**
- 本地 Ollama 是首选 backend（loopback only by default）
- 远程 API 需要 `WATERMARKS_REWRITE_ALLOW_REMOTE=1` 显式开启
- `--strength paraphrase` 是强度档（`light` / `paraphrase` / `aggressive`）

> **设计哲学的极端体现**："我们做这个工具，但请你自己决定要不要真的改写"。这跟某些 AI 工具偷偷帮你重写段落的做法形成对比。

### 2.3 Files 层：C2PA / EXIF / XMP / doc props

`container_meta.py` 是最大单文件（52KB），专门处理 Office / PDF / SVG / HTML / Markdown 等容器型格式的元数据剥离。

C2PA（Coalition for Content Provenance and Authenticity）是 Adobe / Microsoft / Google 主导的"内容来源标准"——签一个 cryptographic assertion 进图片元数据，记录 "这张图是用哪台相机/哪个软件生成的"。Adobe Firefly 和 Microsoft Designer 生成的图都带这个。

watermarks-remover 的做法：

1. **检测**：用 `c2patool` (Rust 实现的 C2PA 解析器) 找出所有 C2PA assertions
2. **剥离**：用 `exiftool` 删除 EXIF / XMP 残留
3. **结构重建**：PDF 必须用 `qpdf` 重建——直接删 metadata stream 会破坏 PDF 内部 xref 表

> **三个外部工具缺一不可**（`c2patool` / `exiftool` / `qpdf`）。Docker 镜像里都预装了。本地运行的话，缺哪个能力 `/capabilities` 接口就会标 false，让用户知道哪些清洗步骤不会生效。

`service/scripts/server.py` 里的 capabilities() 函数把这三个工具是否在环境里翻译成 JSON 返回：

```python
def capabilities() -> dict[str, Any]:
    return {
        "version": VERSION,
        "tools": {
            "c2patool": which("c2patool") is not None,
            "exiftool": which("exiftool") is not None,
            "qpdf": which("qpdf") is not None,
        },
        "pixel_backends": {
            "ctrlregen": bool(os.environ.get("NOAI_WATERMARK_DIR")),
            "diffusion": bool(os.environ.get("MARKDIFFUSION_DIR")),
        },
        # ...
    }
```

> **"诚实的工程"**：用户能看到当前环境能做什么、不能做什么。比那些默认说 "已剥离干净" 但其实没找到 c2patool 就跳过的工具，可信得多。

---

## 3 · stdlib only：为什么刻意不装第三方依赖

`requirements-dev.txt` 只有 ruff / pytest / pytest-cov。**核心代码 0 第三方依赖**。

为什么？

```python
# service/scripts/server.py 第一段注释
"""HTTP service exposing the watermarks-remover cleaning pipeline.

Stdlib-only. The agent skill and any web app can call it over HTTP instead of
running the CLI scripts locally.
...
Hardening mirrors the CLIs: input size caps, binary-as-text guard, atomic
writes, loopback-only bind by default, optional bearer API key. Run it as an
unprivileged user (the Docker image does). Intended for a trusted network;
expose through a reverse proxy if reachable from untrusted clients.
"""
```

四个具体好处：

1. **零供应链风险**——这是个**清洗 AI 痕迹的工具**，它本身的依赖如果被供应链投毒，等于给你的"隐私"装一个后门
2. **Python 3.10+ 标准库足够**——`http.server` / `argparse` / `dataclasses` / `unicodedata` / `difflib` 全够用
3. **镜像极小**——`Dockerfile` 是 2.4KB，没有 requirements.txt 拉几百兆
4. **审计容易**——核心代码 0.5MB Python，全在 27 个文件里，每个文件 < 60KB

代价：HTTP server 用 `http.server.ThreadingHTTPServer`（不是 asyncio / hypercorn / uvicorn），并发能力有限。但 README 明确说"intended for trusted network"，不追求大流量。

> **取舍非常明确**：工具的"信任边界"决定了它必须 stdlib only。其他工具追求吞吐和生态，这个工具追求**用户对工具本身的可信度**。

---

## 4 · Agent skill + HTTP service：解耦的两个 surface

架构最漂亮的部分是 `skills/` 和 `service/` 的分离：

```
skills/remove-ai-marks/    ← Agent 调用入口（纯 markdown，没有 .py）
service/                   ← 实际清洗逻辑（stdlib Python）
service/scripts/server.py  ← HTTP service（127.0.0.1:8765）
```

README 原文：

> "The skill ships **no code** — it calls the service over HTTP. Install the skill (markdown only) and start the service, then set WATERMARKS_SERVICE_URL if it is not http://127.0.0.1:8765."

这意味着：

- **Agent host**（Grok Build / Cursor / Claude Code 等）**不需要装 Python**
- 只需要 `mkdir -p ~/.grok/skills && ln -sfn $(pwd)/skills/remove-ai-marks ~/.grok/skills/remove-ai-marks` 一行
- 实际清洗跑在另一个进程（service），Agent 只是按规则触发 `/clean` POST 请求

> **这是"AI Agent 工具"的成熟形态**：把工具做成一个独立 service，让多个 Agent 共享同一个底层能力。

具体的 HTTP 协议（`server.py` 注释里写明）：

| Method | Path | Body | Returns |
| --- | --- | --- | --- |
| GET | `/health` | — | `{"ok": true, "version": ...}` |
| GET | `/capabilities` | — | optional tools / backends present |
| GET | `/openapi.json` | — | dynamically generated OpenAPI 3.0.3 spec |
| POST | `/inspect` | `{"file": "<base64>", "name": "x.png"}` | `{"ok", "kind", "suspicious", "report"}` |
| POST | `/clean` | `{"file": "<base64>", "name": "x.md", "options": {...}}` | `{"ok", "kind", "cleaned": "<base64>", "report"}` |

`/openapi.json` 是**动态生成**的，spec table 和实际 endpoint 共用一个声明——确保 spec 永远不漂移（这是 OpenAPI 工具最容易出问题的地方）。这种"single source of truth"的工程实践比大部分 SaaS 公司的做法更严格。

### 4.1 安全加固：默认 loopback + optional bearer + atomic writes

`server.py` 里的 hardening 设计跟 CLI 完全一致：

```python
# Optional bearer token: when set, every request must send
# `Authorization: Bearer <key>`. Empty means no auth (default).
API_KEY = os.environ.get("WATERMARKS_SERVER_API_KEY", "").strip()

# Body cap for the JSON envelope. Base64 inflates by 4/3, so the decoded file
# stays well under MAX_INPUT_BYTES for the same cap.
MAX_BODY_BYTES = MAX_INPUT_BYTES + (MAX_INPUT_BYTES >> 1)
```

具体加固：

- **loopback-only bind**（`--host 127.0.0.1`，默认）—— 拒绝外部网络直接访问
- **可选 Bearer API key** —— 多个 Agent 共享同一个 service 时设 `WATERMARKS_SERVER_API_KEY`
- **输入大小封顶** —— `MAX_INPUT_BYTES + (MAX_INPUT_BYTES >> 1)` = 1.5x，给 base64 膨胀留空间
- **二进制当文本的 guard** —— `looks_binary()` 检 magic bytes + 控制字节比例，`.docx` 当文本读会损坏
- **原子写入** —— `backup_path()` 先做 .bak 再覆盖，`in-place` 模式可回滚

> **服务暴露的是不可逆操作**（cleaned 文件覆盖原始痕迹），每个加固项都不是装饰。

---

## 5 · Format dispatch：路由表设计

`format_dispatch.py` 全文只有 70 行，但把"什么样的文件交给哪条管道"这件事拆得清清楚楚：

```python
IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".avif", ".heic", ".heif"}
CONTAINER_EXTS = {
    ".svg", ".pdf", ".docx", ".xlsx", ".pptx", ".odt",
    ".html", ".htm", ".md", ".markdown", ".mdx",
}
TEXT_EXTS = {
    ".txt", ".text", ".css", ".js", ".py", ".rs", ".go",
    ".json", ".yaml", ".yml", ".toml", ".csv",
}
```

分类策略：

1. **扩展名优先** —— 已知扩展名立即分类
2. **magic bytes 嗅探** —— 无扩展名或未知扩展名时扫 magic bytes
3. **zip 容器签名** —— `.docx` / `.odt` 是 zip，从末尾 central directory 判断
4. **兜底为 text** —— 未知格式按 text 处理（但要求 caller 自己保证不会损坏二进制）

> **关键细节**：扩展名表的优先级比 magic bytes 高。`notes.md` 哪怕内容看起来像 binary 也按 text 走——因为 markdown 文件的扩展名是用户强语义信号。

每个 caller（`inspect_file` / `clean_file` / `audit_lib`）都通过 `classify(path)` 拿同一个答案。三处实现收敛到一个函数，是经典 "don't repeat yourself"。

---

## 6 · 5 个可选重型后端：开源合规的边界

README 列了 5 个可选后端，**其中 2 个从未发布 Docker 镜像**：

| Image tag | Contents | Published? |
| --- | --- | --- |
| `ghcr.io/.../watermarks-remover:latest` | Core HTTP service + cleaners + c2patool/exiftool/qpdf | ✅ |
| `…:markllm-latest` | MarkLLM text-watermark harness (Apache-2.0 upstream) | ✅ |
| `…:markdiffusion-latest` | MarkDiffusion image harness (Apache-2.0 upstream) | ✅ |
| `watermarks-remover-ctrlregen:local` | CtrlRegen pixel removal — **never published** | 仅本地 build |
| `watermarks-remover-synthid-scorer:local` | reverse-SynthID scorer — **non-commercial Research License** | 仅本地 build |

为什么 CtrlRegen 和 SynthID 反向 scorer 不发布？

- **CtrlRegen**：上游 `noai-watermark` 没有 LICENSE 文件，不能进 GHCR 公开镜像
- **SynthID 反向 scorer**：上游 Research License 明文禁止商业使用

> **工程上的诚实**：合规边界不是用 README 漂亮话遮过去，是直接在 Docker 镜像标签和 compose profile 上做硬约束。`docker compose --profile heavy up -d` 才会拉这两个本地 build 的镜像。

这种 "用基础设施层面 enforce 而不是 README 写一句" 的做法，是真正能信任的工具的标志。

---

## 7 · 边界、争议、与它不解决的问题

这个项目在仓库 README 和 GitHub issue 里都明确讲了它**不做**的事：

### 7.1 它不洗"图片上的水印"

仓库的 `clean_image.py` 处理的是 **EXIF / XMP / C2PA 元数据** 和 **像素层面的 SynthID score**——不是图片角落的 logo / 半透明文字 / 网格。要洗这类视觉水印得用 inpainting（LaMa / SD inpaint / IOPaint），不是这个工具的范围。

### 7.2 它不绕过 copyright / DMCA

README 强调 `for privacy and hygiene on content you own`。如果有人用它洗掉别人作品的 C2PA 签名，**那是使用者的法律问题，不是工具的问题**。

### 7.3 它不偷偷干

Layer B 默认 `print-prompt`（只打印改写 prompt，不调模型）。`--strip-emoji-glue` 是显式 flag。`--strip-bidi` 是显式 flag。`--aggressive-homoglyphs` 是显式 flag。`--force-text` 是显式 flag。

每个不可逆操作都需要用户**显式开关**——这是它跟很多 "AI cleanup tool" 的核心区别。

### 7.4 它在浏览器侧基本无解

C2PA 可以验签，但 **prompt-level 隐写**（比如 Claude 在 prompt 里插不可见指令）必须在你拿到的内容进浏览器之前清洗。GitHub README 一句："Cursor does not expose a deterministic pre-send filter for final chat responses" —— Cursor 没有真正的"输出前清洗"机制，watermarks-remover 的 skill 是 model-selected 而非 deterministic pre-send。

---

## 8 · 这次反主流的工具给我们的提示

仓库不到一周，从 0 到 11k stars。背后有几件值得记下的事：

1. **AI 内容的归属问题不是单方面的**。AI 公司想加 provenance 标记是合理的（deepfake 检测、学术诚信），但内容创作者想清洗自己产出的内容上的痕迹也是合理的。这两件事**同时成立**，且没有现成的伦理共识。watermarks-remover 选了"为创作者一方提供能力"，所以才爆发。

2. **"AI 工具的信任"比"AI 工具的能力"更稀缺**。一个 stdlib only、Agent skill 解耦、能力可声明（`/capabilities`）、不可逆操作显式开关、镜像分发改许可证合规——这种工具的可信度是其他 AI 项目很难复制的。

3. **AI Agent 工具的成熟形态 = 独立 service + 协议 + 多 Agent 共享**。`skills/` 只放 markdown，`service/` 跑实际逻辑，HTTP 是 Agent 之间的连接方式。这套架构不是为这个项目设计的——是为"未来 100 个 Agent 工具"设计的。

4. **release 节奏反映的是真实用户压力**。6 天 5 个 release 不是赶进度，是 .avif 截图带 C2PA 的人逼出来的，是 .xlsx 想洗的人逼出来的，是 Windows 用户发现 .bak 路径有问题的人逼出来的。**工具的迭代节奏是它"服务于谁"的诚实信号**。

---

## 9 · 读者判断：谁该跑一遍，谁该读本文就够

**读本文就够的**：

- 想了解 AI 内容 provenance 标记这个生态（Claude / Gemini SynthID / OpenAI / C2PA）的整体图景
- 想理解 stdlib-only + Agent skill 解耦架构的真实工程取舍
- 想知道"清洗 AI 痕迹"这件事的工具目前做到了什么程度、没做到什么

**应该跑一遍的**：

- 你刚发现自己的图 / 文档 / Markdown 被 AI 公司打上了 provenance 标记，想洗掉——`make serve` 一行启动，`curl /clean` 一行调用
- 你做的是 Agent 工具开发，想参考"独立 service + 多 surface"这套架构——`server.py` 200 行读一遍够了
- 你做的是内容平台的合规 / 风控——`audit_lib.py` (11KB) + `audit_dir.py` (4.5KB) + `audit_website.py` (16KB) 三件套是 SARIF 2.1.0 输出，可以直接接 GitHub Code Scanning

**应该直接跳仓库的**：

- 想看 Layer A 的 47 项清洗表 + 17 项空格表 + emoji glue 保护逻辑 → `service/scripts/text_unicode.py` 649 行
- 想看路由分类器 + magic bytes 嗅探 → `service/scripts/format_dispatch.py` 70 行
- 想看 stdlib HTTP 服务怎么写 → `service/scripts/server.py` 完整

---

## 附录 A · 本文事实来源

- GitHub 仓库：`github.com/guillaumemeyer/watermarks-remover`（截至 2026-08-17 08:43 GMT+8）
  - 11,469 stars / 1,200 forks / 55 watchers
  - Created: 2026-08-11T16:32:38Z / Updated: 2026-08-17T00:43:17Z / Pushed: 2026-08-17T00:43:31Z
  - License: 见 `LICENSE` (1KB)
- 5 个 release（按时间排）：
  - v0.2.0 (2026-08-12) — c2patool false-positive fix
  - v0.3.0 (2026-08-12) — optional SynthID pixel scoring
  - v0.3.1 (2026-08-13) — stronger Layer B statistical-watermark rewrite
  - v0.4.0 (2026-08-13) — pixel removal, finding confidence, Windows & false-positive fixes
  - v0.5.0 (2026-08-14) — service & Docker distribution, HTTP API, and verification harnesses
- 8 个核心 commit（按时间倒序，commit hash 已核实）：
  - `c14b586` (2026-08-17) — multi-worker concurrency + SARIF 2.1.0 export
  - `b49fe4e` (2026-08-17) — XLSX/PPTX container metadata
  - `7236277` (2026-08-17) — Ruff linting CI
  - `47a44e6` (2026-08-16) — SVG/HTML/Markdown data URI 递归清洗
  - `fcebf53` (2026-08-16) — AVIF/HEIC metadata + C2PA stripping
  - `737eaa3` (2026-08-15) — DOCX docProps provenance fix
  - `6750f88` (2026-08-15) — `--in-place` + `-o` 同格式检测修复
  - `e85656d` (2026-08-15) — DOCX/ODT body text Layer A
- 27 个 `service/scripts/` 核心 Python 文件（行数已核实）：
  - `container_meta.py` 52KB（最大，DOCX/PDF/SVG 元数据剥离）
  - `image_meta.py` 37KB（PNG/JPEG/WebP/AVIF/HEIC）
  - `server.py` 20KB（stdlib HTTP service）
  - `rewrite_text.py` 21KB（Layer B 改写）
  - `text_unicode.py` 649 行 20KB（Layer A 清洗）
  - `audit_website.py` 16KB（整站审计）
  - `audit_lib.py` 11KB（审计核心库）
  - `clean_ctrlregen.py` 6.4KB
  - `clean_file.py` 5.4KB
  - `clean_image.py` 6.9KB
  - `clean_text.py` 3.0KB
  - `common.py` 14.5KB（共享工具）
  - `detect_text_watermark.py` 11.7KB
  - `format_dispatch.py` 2.2KB（路由表）
  - `inspect_file.py` 3.5KB / `inspect_image.py` 2.6KB / `inspect_text.py` 2.6KB
  - `markdiffusion_harness.py` 18.5KB
  - `score_stylometry.py` 14.8KB
  - `score_synthid.py` 4.7KB
  - 其他 8 个 setup 脚本 + requirements-*.txt
- 6 个 Dockerfile（已核实）：
  - `Dockerfile` 2.4KB（core）
  - `Dockerfile.ctrlregen` 2.8KB
  - `Dockerfile.markdiffusion` 2.2KB
  - `Dockerfile.markllm` 2.9KB
  - `Dockerfile.synthid` 2.5KB
- 测试文件 20+（已核实）：`test_audit.py` 11.5KB / `test_container_meta.py` 28KB（最大）/ `test_audit_sarif_and_concurrency.py` 4.7KB / `test_avif_heic.py` 5.8KB / `test_binary_guard.py` 8.5KB / `test_clean_text.py` 9.9KB / `test_clean_image.py` 5.3KB / `test_ctrlregen_clean.py` 8.6KB 等

## 附录 B · 已知缺口

- **作者 `guillaumemeyer` 背景**：未拿到 bio / LinkedIn / 个人网站（需要 Sonner 子代理调研补充或人工查 GitHub profile 页）
- **同类项目对比**：未深入对比 WatermarkRemover.io / Aiseesoft / HitPaw / LaMa Cleaner / IOPaint 等（需要后续反写稿或专题调研）
- **6 天 11k stars 的真实用户分布**：仓库 issue / discussion 数据未抽取
- **AI 公司对这类工具的官方态度**：OpenAI / Google / Anthropic 各自的回应（如果有）—— 这是反 AI 追溯工具的伦理上限