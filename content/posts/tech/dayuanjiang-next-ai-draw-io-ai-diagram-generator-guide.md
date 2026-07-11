---
title: "Next AI Draw.io 深度拆解:33K stars 的「对话式画图」如何重塑架构图工具"
slug: dayuanjiang-next-ai-draw-io-ai-diagram-generator-guide
date: 2026-07-12T02:58:14+08:00
lastmod: 2026-07-12T02:58:14+08:00
draft: false
categories: ["技术笔记"]
tags: ["drawio", "nextjs", "llm", "diagram", "mcp", "ai-tool"]
description: "Next AI Draw.io 是 AI 对话生成 draw.io 图表的开源工具,33K+ stars。本文拆解它的 LLM 图表生成模式、MCP Server 集成、多 Provider 架构以及与传统 draw.io 的差异。"
---

# Next AI Draw.io 深度拆解:33K stars 的「对话式画图」如何重塑架构图工具

## 核心判断

Next AI Draw.io 是「AI 对话式生成 draw.io 图表」的代表项目,33K+ stars 来自一个具体需求:**用自然语言画架构图**——告诉 AI「画一个 RAG 架构图」,自动生成 draw.io 的 mxGraph XML。它的差异化是 **draw.io 的开放格式 + LLM 的自然语言理解**,既保留了 draw.io 的编辑能力,又让非设计师能用对话完成草图。

## 项目速览

- 仓库: [DayuanJiang/next-ai-draw-io](https://github.com/DayuanJiang/next-ai-draw-io)
- Stars / 语言: 33K+ / TypeScript (Next.js 16 + React 19)
- 主页: <https://next-ai-drawio.jiang.jp/>
- 定位: AI 驱动的图表生成工具(基于 draw.io)

## 为什么值得看

传统画架构图有三个痛点:

1. **手工对齐节点费时间**——一个 20 个节点的微服务图,手工排版 30 分钟起步。
2. **跨工具切换**——画图用 draw.io,写说明用 Markdown,贴到 Confluence 又要重新排版。
3. **复用困难**——之前的图是 SVG,下次要改架构又得重画。

Next AI Draw.io 用 LLM 直接生成 draw.io 的 mxGraph XML,完美解决前两个痛点,第三个通过「对话式修改」(「把这个节点改成虚线」)部分解决。

## 系统地图

```
┌──────────────────────────────────────────────────────────┐
│            Frontend (Next.js 16 + React 19)             │
│  ┌────────────────┐  ┌──────────────────┐               │
│  │  DrawIO UI     │  │ Chat Interface   │               │
│  │  (mxGraph)     │  │ (LLM prompt)     │               │
│  └────────────────┘  └──────────────────┘               │
├──────────────────────────────────────────────────────────┤
│            Server (Next.js API routes)                   │
│  ┌────────────────┐  ┌──────────────────┐               │
│  │ LLM Router     │  │ Diagram State    │               │
│  │ (multi-provider│  │ (history+restore)│               │
│  │  - Claude/GPT/ │  │                  │               │
│  │   Gemini/Doubao)│ │                  │               │
│  └────────────────┘  └──────────────────┘               │
├──────────────────────────────────────────────────────────┤
│            DrawIO Diagram Engine (mxGraph)               │
└──────────────────────────────────────────────────────────┘
```

## 关键机制

### 1. LLM 生成 mxGraph XML

核心 prompt 模式:让 LLM 直接输出 draw.io 的 mxGraph XML 格式,然后渲染到 draw.io 编辑器。

```xml
<mxfile>
  <diagram name="RAG Architecture">
    <mxGraphModel>
      <root>
        <mxCell id="0" />
        <mxCell id="1" parent="0" />
        <mxCell id="2" value="User Query" style="rounded=1;..." vertex="1" parent="1">
          <mxGeometry x="40" y="40" width="120" height="60" />
        </mxCell>
        <!-- ... -->
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>
```

LLM 的工作:

- 解析自然语言需求,识别节点(实体)和边(关系)
- 分配坐标(LLM 不擅长精确像素对齐,所以输出大致位置,由前端微调)
- 选择样式(rounded / filled / stroke / 颜色)

精度问题:LLM 输出的坐标经常需要前端重新排版(auto-layout),但**节点内容和关系的正确率**已经足以完成 80% 的工作。

### 2. 多 Provider LLM 架构

服务端支持多个 LLM Provider,管理员面板配置:

```ts
// 服务端多模型配置示意
{
  providers: {
    anthropic: { apiKey: '...', models: ['claude-opus-4-7', 'claude-sonnet-4-5'] },
    openai: { apiKey: '...', models: ['gpt-5', 'o3'] },
    google: { apiKey: '...', models: ['gemini-2.5-pro'] },
    doubao: { apiKey: '...', models: ['glm-4.7'] },
  }
}
```

用户在前端选模型,不同模型的输出风格不同——Claude 偏严谨,OpenAI 偏创意,Gemini 偏简洁。这给用户**模型对比**的机会,但也意味着**每次换模型都要重新校准 prompt**。

### 3. MCP Server 集成

2025 年起,项目加了 MCP Server 支持,可以在 Claude Desktop / Cursor / VS Code 里直接调用:

```json
{
  "mcpServers": {
    "drawio": {
      "command": "npx",
      "args": ["@next-ai-drawio/mcp-server@latest"]
    }
  }
}
```

这样在 Claude Desktop 里对话时,可以让 Claude 直接「帮我画一个 RAG 架构图到 draw.io」,图表自动同步到 Next AI Draw.io 服务,用户在浏览器里打开继续编辑。这是 **AI 工具从 UI 工具变成 Agent 工具**的关键演进。

### 4. AI Reasoning Display

支持显示 AI 的思考过程(OpenAI o1/o3, Gemini Thinking, Claude Extended Thinking):

- 用户能看到「AI 为什么这么画」
- 对错误的输出,可以反馈「你画错了 X,改成 Y」
- 对专业领域的图(医疗、法律),reasoning 暴露有助于信任审计

### 5. Diagram History + Restore

每次 AI 修改都保存一个版本,可以查看 / 恢复任意历史版本。这解决了 LLM 输出的「随机性」问题——AI 不小心把好图改坏了,可以一键回滚。

## 实战场景

**适合用 Next AI Draw.io**:

- **写技术博客**——配 1-2 张架构图,比 Visio / Figma 快 10 倍。
- **内部技术评审**——白板前快速生成候选方案。
- **客户提案**——客户说「想要个架构图」,对话生成后人工微调。
- **教学**——老师讲 RAG / Transformer 时,对话生成直观图示。

**不适合**:

- **复杂大型图表**(>50 节点)——LLM 容易混淆节点关系,需要分多次生成。
- **精确像素对齐的设计稿**——还是用 Figma / Sketch。
- **机密架构图**——LLM 看到 prompt 后,数据可能被 Provider 记录。

## 上手示例

```bash
# 在线试用
https://next-ai-drawio.jiang.jp/

# 本地启动
git clone https://github.com/DayuanJiang/next-ai-draw-io.git
cd next-ai-draw-io
npm install
npm run dev

# 部署到 Vercel
# (一行 vercel deploy)
vercel deploy

# 部署到 Cloudflare Workers
npm run deploy:cloudflare

# 配置 LLM Provider
# 在管理面板填入 Anthropic / OpenAI / Gemini API Key
```

## 适用边界

- **目标用户**:技术写作者、架构师、产品经理、内部技术评审组织者。
- **数据敏感性**:LLM Provider 会看到你的图内容,生产环境需评估。
- **本地化**:支持多语言界面(中/英/日),但 LLM prompt 默认英文。

## 总结

Next AI Draw.io 的真正价值是「**让 AI 直接生成可编辑的图表格式**」——不是 SVG 不是 PNG,而是 draw.io 的 mxGraph XML。这种「AI 生成 + 人类微调」的工作流,比纯 AI 生成(不可编辑)或纯手工画图(慢)都更高效。33K+ stars 反映了开发者社区对「**对话式画图**」这一新形态的认可。MCP Server 的加入让它从 UI 工具升级为 Agent 工具,这是 2026 年 AI 工具的标志性演进。

## 参考

- GitHub: <https://github.com/DayuanJiang/next-ai-draw-io>
- 在线试用: <https://next-ai-drawio.jiang.jp/>
- MCP Server: `@next-ai-drawio/mcp-server` on npm