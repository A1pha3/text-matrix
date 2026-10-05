---
title: "Next AI Draw.io：把 draw.io 的 XML 当作 LLM 的输出契约"
slug: dayuanjiang-next-ai-draw-io-ai-diagram-generator-guide
github_repo: "DayuanJiang/next-ai-draw-io"
source_key: "gh:DayuanJiang/next-ai-draw-io"
date: 2026-07-12T02:58:14+08:00
lastmod: 2026-10-03T00:00:00+08:00
draft: false
categories: ["技术笔记"]
tags: ["Next.js", "LLM", "draw.io", "MCP", "Electron"]
description: "36K stars 的 Next AI Draw.io 靠两个决定立足：让模型走 tool calling 输出 draw.io 原生 mxCell XML，生成结果直接可编辑；再用 MCP 把画图能力开放给 Claude Desktop 等外部 Agent。本文对照源码拆解其输出契约、多 Provider 配置与部署路径。"
---

# Next AI Draw.io：把 draw.io 的 XML 当作 LLM 的输出契约

AI 生成图表的工具不少，多数止步于输出一张图片。这个项目的思路不同：让模型生成 draw.io 的原生格式（mxCell XML），渲染在嵌入的 draw.io 编辑器里。图生出来就是可编辑的——拖动节点、改样式、导出文件，走的全是 draw.io 既有工作流。加上 MCP（Model Context Protocol）Server 之后，Claude Desktop、Cursor 这类外部 Agent 也能把图画进你的浏览器。

36,095 stars（2026-10-03 GitHub API 读数；文章发表时约 33K，2026-06-08 Wayback 快照为 31,563）大体说明了社区对这条路线的态度。下面按源码拆它的输出契约、模型配置和部署形态，结论先行：这个项目值得关注的不是「AI 画图」这个方向，而是它把「模型的输出格式」当成第一设计约束来处理的做派。

## 项目速览

| 项 | 值 |
| --- | --- |
| 仓库 | [DayuanJiang/next-ai-draw-io](https://github.com/DayuanJiang/next-ai-draw-io)，2025-03-23 创建 |
| Stars / Forks | 36,095 / 3,851（2026-10-03 读数） |
| 许可 | Apache-2.0 |
| 技术栈 | TypeScript；Next.js 16（^16.0.7）+ React 19（^19.1.2）+ Vercel AI SDK（`ai` ^6.0.1）+ react-drawio ^1.0.3 |
| 形态 | Web 应用（自托管/在线 demo）、Electron 桌面应用（Windows/macOS/Linux）、MCP Server（独立 npm 包） |
| 在线 demo | <https://next-ai-drawio.jiang.jp/>（307 重定向到 `/en/`，正常） |
| 界面语言 | 英/简中/繁中/日四种（`lib/i18n/config.ts` 的 locales，路由形如 `/[lang]/`） |

## 系统地图

```
浏览器
├─ Next.js 前端（React 19）
│   ├─ react-drawio：内嵌 draw.io 编辑器（embed.diagrams.net）
│   └─ 聊天面板：展示推理过程与工具调用
│        ↑ XML 经 display_diagram / edit_diagram 工具回传渲染
Next.js API 路由（服务端）
├─ /api/chat：streamText + tools，AI SDK 统一各 Provider 协议
├─ 多 Provider 路由：AWS Bedrock（默认）/OpenAI/Anthropic/Google 等 16 个
└─ /admin 管理面板：模型、访问码、配额、可观测性
外部通道
└─ MCP Server（@next-ai-drawio/mcp-server）
     内嵌 HTTP server，直连浏览器实时预览
```

三条主线值得分开看：Web 端的「对话改图」、服务端的「多模型接入」、MCP 的「外部 Agent 接入」。三者共享同一套 XML 表示，机制却各不相同。

## 关键机制

### 1. 输出契约：tool calling 下的 mxCell 片段

`app/api/chat/route.ts` 用 Vercel AI SDK 的 `streamText` 发起请求，注册了两个工具：

- `display_diagram`：新建或整体重画。模型只传 mxCell 元素，wrapper 标签（`<mxfile>`、`<mxGraphModel>`、`<root>`）和 id 为 0/1 的根单元格由应用自动补齐；
- `edit_diagram`：增量修改。按 cell ID 执行 update/add/delete 三种操作，delete 会自动级联删除子节点和关联连线。

工具的 description 里写死了验证规则，违反即拒绝：只生成 mxCell、不带根单元格、所有 mxCell 保持平级、id 从 2 起且唯一、每个 mxCell 带合法 parent、转义特殊字符。模型面对的不是「随便写 XML」的自由任务，而是有 schema 约束的 tool call。这道护栏不改变模型能力本身——模型过小时连工具调用都未必稳定，边界见后文排查一节。

服务端还有一层容错：`jsonrepair` 修复模型输出的畸形 JSON。代码里还预留了 DynamoDB 配额管理与 token 记账（demo 站在用），不配置即不启用。

两个官方推荐的样式技巧也写在工具描述里：边样式加 `flowAnimation=1` 可得流动动画连线；AWS 架构图使用 AWS 2025 图标。

### 2. 多 Provider：一个环境变量到一套 JSON 的三档配置

支持的 Provider 共 16 个（README 清单）：AWS Bedrock（默认）、OpenAI、Anthropic、Google AI、Google Vertex AI、Azure OpenAI、Ollama、OpenRouter、AIHubMix、DeepSeek、SiliconFlow、ModelScope、SGLang、Vercel AI Gateway、ByteDance Doubao、Atlas Cloud。除 AWS Bedrock 和 OpenRouter 外，都支持自定义 endpoint。

配置分三档，全部来自 `env.example` 与 `docs/en/ai-providers.md`：

```bash
# 第一档：单模型。AI_PROVIDER 选平台，AI_MODEL 必填
AI_PROVIDER=bedrock          # 默认值即 bedrock
AI_MODEL=global.anthropic.claude-sonnet-4-5-20250929-v1:0

# 第二档：单平台多模型，逗号分隔；第一个是默认，其余进前端模型选择器
AI_MODEL=doubao-seed-1-8-251215,doubao-seed-1-6-flash,doubao-seed-1-6-pro
```

第三档是跨平台多模型，用 `AI_MODELS_CONFIG` 环境变量（JSON 字符串）或项目根的 `ai-models.json` 文件：

```json
{
  "providers": [
    { "name": "OpenAI Production", "provider": "openai",
      "models": ["gpt-4o", "gpt-4o-mini"], "default": true },
    { "name": "Custom DeepSeek", "provider": "deepseek",
      "models": ["deepseek-chat"],
      "apiKeyEnv": "MY_DEEPSEEK_KEY", "baseUrlEnv": "MY_DEEPSEEK_URL" }
  ]
}
```

注意 API key 的传递方式：配置里写的是**环境变量的名字**（`apiKeyEnv`），不是密钥本身，密钥仍留在环境变量里。模型管理也可以不走手改配置——设好 `ADMIN_PASSWORD` 后访问 `/admin`，在网页面板里管理模型、访问码、功能开关、配额与可观测性。

选模型这件事，README 给的口径很具体：这个任务要求模型擅长「长文本 + 严格格式约束」，官方点名推荐 Claude Sonnet 4.5、GPT-5.1、Gemini 3 Pro、DeepSeek V3.2/R1；画云架构图优先选 claude 系，理由是它的训练数据见过大量带 AWS/Azure/GCP 图标的 draw.io 图。另一个常被忽略的参数是 `MAX_OUTPUT_TOKENS`（默认 64000）：推理内容和图 XML 共享这份配额，thinking 模型可能把配额花光还没开始画工具调用，低于模型自身上限时会自动按实际上限重试。

顺带澄清一个容易误读的点：README 里「demo 站现在使用 glm-4.7」出现在 ByteDance Doubao 的赞助致谢里——豆包以 Coding Plan 形式赞助了 demo 站的 API 用量，glm-4.7 是该赞助下 demo 站实际挂载的模型，不是「Doubao Provider 的专属模型」。在 ARK 平台注册还能拿到 50 万免费 tokens。

### 3. MCP Server：把画图能力交给外部 Agent

MCP 支持的独立包 `@next-ai-drawio/mcp-server` 于 2025-12-17 首发到 npm（当前 latest 0.2.3），仓库内对应 `packages/mcp-server/`。接入 Claude Code 只需一行：

```bash
claude mcp add drawio -- npx @next-ai-drawio/mcp-server@latest
```

Claude Desktop、Cursor、VS Code 的配置同构（`command: npx` + 包名），逐字照抄 README 即可。这个包自包含一个 HTTP server，无外部依赖；画出的图实时出现在浏览器里。

它暴露 10 个工具：`start_session`、`create_new_diagram`、`load_diagram`、`edit_diagram`、`get_diagram`、`export_diagram`，加上多页管理的 `list_pages`、`add_page`、`rename_page`、`delete_page`——draw.io 文档本身支持多页（一个文件里多个绘图页），后四个工具对应页级操作。导出支持 `.drawio`（XML）、`.png`、`.svg` 三种格式；png/svg 指定页导出时会把该页单页投影临时载入浏览器截图再恢复，用户会看到约 1-2 秒的标签页闪动。

`edit_diagram` 的并发保护是个精巧的设计（`packages/mcp-server/src/edit-gate.ts`）：早期版本用 30 秒墙钟超时，结果慢而正确的客户端被误杀（issue #885），后来改成内容比对——服务端记录模型上次见到的 XML（`lastSeenXml`），编辑前比对当前状态是否仍然一致。比对是结构级的（页集合、页名、每个页的 cell 树），因为 draw.io 回推状态时会改变属性顺序、空白和视口属性，这些不算用户编辑；字节相等只作为快速路径。模型没见过有人动过图，编辑放行；否则返回 stale 拒绝。

### 4. 其余能力一览

README 的 Features 还有几项值得点名：上传图片让 AI 复刻增强；上传 PDF/文本文件提取内容生成图；AI Reasoning Display（o1/o3、Gemini、Claude 等支持思考的模型可展开推理过程）；Diagram History 记录每次 AI 修改前的版本，可查看和回滚——这是对「AI 把好图改坏了」的直接兜底。

## 一次对话的完整流转

以浏览器里画一张「带鉴权的 RAG 架构图」为例：

1. 用户在聊天面板输入需求，前端 POST 到 `/api/chat`；
2. 服务端按当前 Provider 组装请求，`streamText` 携带 `display_diagram`/`edit_diagram` 两个工具定义发出；模型的思考内容（若支持）先流式回传到界面上；
3. 模型发起 `display_diagram` 调用，参数是符合验证规则的 mxCell 片段；服务端校验、自动补 wrapper 与根单元格，经 AI SDK 的客户端工具通道回传浏览器；
4. react-drawio 把 XML 渲染进嵌入的 draw.io 编辑器，用户此刻已经可以手动拖拽微调；
5. 用户追问「把向量库换成虚线框」，模型改走 `edit_diagram`，按 cell ID 发 update 操作，只传变更的单元格；
6. 每次修改前的状态自动进 Diagram History，改坏了从历史面板一键回滚；
7. 满意后导出 PNG 或 `.drawio` 文件，后者可直接在 draw.io 桌面版继续编辑。

MCP 通道的差别只在 1-3 步：需求来自 Claude Desktop 的对话，工具调用走本地 MCP server 的 HTTP server，渲染与导出仍落在同一浏览器会话里。

## 上手路径

```bash
# 在线 demo：开箱即用，配额受限
#   聊天面板设置里填自己的 API Key（BYOK，自带密钥）可绕过用量限制
#   官方说明：Key 只存浏览器本地，不上传服务器

# 本地开发（Node 环境就绪后）
git clone https://github.com/DayuanJiang/next-ai-draw-io
cd next-ai-draw-io
npm install
cp env.example .env.local   # 至少配置 AI_PROVIDER 与 AI_MODEL
npm run dev                 # Turbopack，http://localhost:6002

# 桌面应用：Releases 页下载 Windows/macOS/Linux 安装包（Electron 打包）

# Docker：见 docs/en/docker.md（可搭配 jgraph/drawio 镜像自托管渲染端）
```

部署三条路，按场景选：腾讯 EdgeOne Pages 有一键 Deploy 按钮，走它还附赠 DeepSeek 模型的每日免费额度；Vercel 同样一键（记得在面板配好环境变量）；Cloudflare Workers 用仓库自带的 `npm run deploy` 脚本（基于 opennextjs-cloudflare，本地可先 `npm run preview` 验证）。

## 排查与边界

官方 FAQ 里的四类高频问题，都是部署后第一小时内会撞上的：

- **PDF 导出无响应**：Web 版导出 PDF 依赖外部服务 `convert.diagrams.net`，在 iframe 里跑不通（issue #539/#125）。先导 PNG 再打印成 PDF。
- **内网访问不到 embed.diagrams.net**：渲染端默认连 draw.io 官方嵌入服务。内网要自建 jgraph/drawio 容器，且 `NEXT_PUBLIC_DRAWIO_BASE_URL` 是**构建期**变量，运行时设置无效，必须在 docker compose 的 build args 里传入（issue #295/#317）。
- **自托管小模型只输出思考不画图**：两个原因——模型太小（官方建议 32B+，小模型难以正确跟随 tool calling 指令），或推理服务没开工具调用（vLLM 需加 `--enable-auto-tool-choice --tool-call-parser hermes`，issue #269/#75）。
- **上传图片报 No Image Provided**：见 FAQ 第 4 条，多与请求体/Provider 对图像输入的支持有关。

能力边界同样来自官方口径：模型侧，生成质量与模型能力强相关，弱模型连工具调用都未必稳定；格式侧，它的强项是架构图、流程图这类结构化图形，像素级设计稿不是 draw.io 的领地；数据侧，图的内容会发送给所选的 LLM Provider，机密架构图要么自托管模型，要么选有数据协议保障的企业通道（如 Bedrock/Vertex）。

## 采用建议

- **现在就可以用**：经常画架构图/流程图的技术写作者与评审组织者。demo 站加 BYOK 零成本试一周，合适再自托管。
- **自托管优先**：图里有业务敏感信息的团队。Apache-2.0 允许商用与内网部署，Docker/EdgeOne/Vercel/Cloudflare 四条部署路径里选熟悉的；模型走 Bedrock 或 Vertex 这类有数据治理承诺的通道。
- **可以观望**：想在生产文档流水线里全自动出图的团队——当前产品的定位仍是「对话式辅助画图」，批量结构化生成需要自己在 MCP 工具之上封装。
- **不适用**：需要精确版式的设计交付（用 Figma/Sketch）、完全离线且无法自建 drawio 渲染端的内网（渲染依赖处理干净前体验打折，见 offline-deployment 文档）。

## 结尾

这个项目对输出契约的处理方式——模型面对的是带 schema 的工具调用和写进 description 的验证规则，而不是一块自由发挥的画布；生成结果是 draw.io 的原生 XML，人类的后续编辑、历史回滚、文件导出全部落在成熟格式上——比「AI 会画图」这个标签本身更值得设计者细看。MCP 的加入把同一套契约开放给了外部 Agent，Web 应用与 Agent 工具共享一条渲染管线。对正在设计「LLM 生成结构化内容」类产品的团队来说，「工具 schema 即质量护栏」这套做法可以直接抄。

## 参考

- 仓库：<https://github.com/DayuanJiang/next-ai-draw-io>（Apache-2.0）
- 在线 demo：<https://next-ai-drawio.jiang.jp/>
- MCP Server：npm 包 [`@next-ai-drawio/mcp-server`](https://www.npmjs.com/package/@next-ai-drawio/mcp-server)，仓库内 `packages/mcp-server/`
- 部署与排查文档：仓库 `docs/en/`（ai-providers、admin-panel、docker、cloudflare-deploy、offline-deployment、FAQ）
