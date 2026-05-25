---
title: "CLI-Anything：用AI将任何软件变成Agent-Native的命令行工具"
date: 2026-05-18
tags: ["AI Agent", "CLI", "开源", "香港大学", "工具生成"]
categories: ["工具"]
---

# CLI-Anything：用AI将任何软件变成Agent-Native的命令行工具

![CLI-Anything](assets/icon.png)

**CLI-Anything** 是香港大学 NLP 组（HKUDS）开源的项目，通过 7 阶段管道自动分析软件源代码，为任何有代码库的软件生成 Agent 可用的 CLI 接口。支持 OpenClaw、nanobot、Cursor、Claude Code 等主流 Agent 框架。已有 18 个专业软件 demos，2,269 个通过测试。

<!-- more -->

## 核心问题

当前软件面向人类用户设计，但 AI Agent 无法直接操控复杂软件（CAD、DAW、IDE、EDA、科学工具等）。CLI-Anything 通过生成标准化 CLI 来弥合这一 gap，让 Agent 能够以编程方式控制任何有代码库的软件。

## 技术架构：7 阶段管道

1. **环境感知** — 分析软件结构和依赖
2. **API 映射** — 识别可暴露的 CLI 命令
3. **参数验证** — 生成健壮的参数解析
4. **测试生成** — 端到端测试覆盖
5. **SKILL.md 生成** — Agent 技能发现元数据
6. **文档自动生成** — 使用指南和示例
7. **质量验证** — 多轮优化确保可用性

## CLI-Hub 生态

通过 `pip install cli-anything-hub` 安装的 CLI-Hub 可浏览、安装、管理社区贡献的 CLI：

```bash
pip install cli-anything-hub
cli-hub install <name>
```

Hub 支持 pip、npm、brew 等多种安装源，已收录大量公共 CLI。

## 支持的软件类型

已生成 harness 的软件类型：
- GIS/地图工具（QGIS）
- 分子建模（UniMol）
- 游戏引擎（Godot）
- 屏幕录制（Openscreen）
- 浏览器自动化（Safari）
- 知识管理（Obsidian）
- 云成本分析（CloudAnalyzer）
- 视频编辑（Kdenlive）
- ETH  staking（Eth2-Quickstart）
- 工作流自动化（n8n、Dify）

**即将支持**：CAD、DAW、IDE、EDA、科学工具

## 限制

- **需要强基础模型** — 依赖前沿模型（Claude Opus 4.6、GPT-5.4 等），弱模型可能生成不完整 CLI
- **依赖源代码** — 闭源编译二进制需反编译，效果下降
- **可能需要迭代 refinement** — 一次生成未必达到生产质量

## 链接

- GitHub: https://github.com/HKUDS/CLI-Anything
- CLI-Hub: https://hkuds.github.io/CLI-Anything/
- 文档: `cli-anything-plugin/HARNESS.md`（方法论 SOP）
- 中文文档: `README_CN.md`
- 日语文档: `README_JA.md`

> ⭐ 开源 Apache 2.0，欢迎贡献！
