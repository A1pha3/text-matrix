---
title: "Babel：开源EDA工具链驱动的AI原生Chiplet设计流程"
date: 2026-05-22T20:20:00+08:00
slug: "babel-ai-native-chiplet-design-open-source-eda"
description: "Babel是amoslee2026开源的AI原生Chiplet设计流程，基于开源EDA工具链（Yosys/OpenSTA/Magic/Netgen等）和5-agent流水线架构，通过Claude Code实现从PRD到GDSII的全流程自动化。"
draft: false
categories: ["技术笔记"]
tags: ["Chiplet", "EDA", "开源工具链", "AI Agent", "芯片设计"]
---

# Babel：开源EDA工具链驱动的AI原生Chiplet设计流程

Babel 是一个 AI 原生 Chiplet 设计流程，基于开源 EDA 工具链，用 5-agent 流水线处理从产品需求到 GDSII 的完整设计。2026-05-22创建，20星。

## 核心判断

Babel 的核心创新不是 EDA 工具本身（Yosys/Magic 这些都是成熟工具），而是把 AI coding agent（Claude Code）引入芯片设计流程：让 agent 以 issue handoff 的方式协作，每个 agent 专注特定设计阶段，用 labeled issue 做状态机驱动。这本质上是把"设计师 → RTL → 验证 → 综合 → PD"的人工流程 AI 化。

## Agent 流水线架构

```
用户需求 → [bba-architect] → bba-guru-rtl → bba-guru-verification → bba-guru-synthesis → bba-guru-pd → signoff
              ↑_________________________*-needs-fix 回流__________________________|
```

| Agent | 触发方式 | 职责 |
|-------|----------|------|
| `/bba-architect` | 新设计想法 / `arch-needs-fix` | PRD → arch_spec → MAS，架构设计流程负责人 |
| `/bba-guru-rtl` | `ready-for-rtl` / `rtl-needs-fix` | MAS → lint-clean SystemVerilog，RTL生成专家 |
| `/bba-guru-verification` | `ready-for-verification` | 100% 覆盖率验证，验证专家 |
| `/bba-guru-synthesis` | `ready-for-synth` / `synth-needs-fix` | SDC + CDC + 并行综合 → timing closure |
| `/bba-guru-pd` | `ready-for-pd` / `pd-rework` | Floorplan → Place → Route → DRC/LVS → GDSII |

## Issue Handoff 协议

Agent 间通过 labeled issue 协作：

| Label | 含义 |
|-------|------|
| `ready-for-rtl` | MAS 完成，等待 RTL 生成 |
| `ready-for-verification` | RTL lint-clean，等待验证 |
| `ready-for-synth` | 100% 覆盖率通过，等待综合 |
| `ready-for-pd` | Timing closed，等待物理设计 |
| `signoff` | GDSII 完成，用户审核 |
| `arch-needs-fix` | MAS 问题，回流 architect |
| `rtl-needs-fix` | RTL 问题，回流 rtl guru |
| `synth-needs-fix` | 综合问题，回流 synthesis guru |
| `escalate-user` | 超出迭代限制，需用户决策 |

## 迭代限制

| Agent | 单阶段迭代限制 | 全局限制 |
|-------|----------------|----------|
| architect | — | 10 |
| rtl | lint 3 次 | 10 |
| verification | coverage 8 次 | 10 |
| synthesis | timing 6 次 | 10 |
| pd | total 8 次 (DRC 3 / LVS 2 / STA 3) | 10 |

超限自动触发 `escalate-user`，停止并等待用户决策。

## Skill 体系

| 类别 | Skill | 用途 |
|------|-------|------|
| **EDA 工具** | `/bb-invoke-yosys` | 并行综合 (LLM驱动5-Phase) |
| | `/bb-invoke-verilator` | 仿真 + 覆盖率收集 |
| | `/bb-invoke-opensta` | 静态时序分析 |
| | `/bb-invoke-magic` | Placement + DRC |
| | `/bb-invoke-netgen` | LVS 网表比对 |
| | `/bb-invoke-qrouter` | 详细布线 |
| | `/bb-invoke-klayout` | GDSII 导出/验证 |
| | `/bb-invoke-abc` | 逻辑优化 |
| **质量检查** | `/bb-check-lint` | verible lint (含修复迭代) |
| | `/bb-check-cdc` | CDC + RDC 检查 |
| | `/bb-spec-review` | MAS 对抗评审 |
| | `/bb-code-review` | RTL 代码审查 |
| **流程生成** | `/bb-rtl-coder` | MAS → SV 代码生成 |
| | `/bb-create-sdc` | MAS → SDC 约束 |
| | `/bb-generate-tb` | 测试平台生成 |
| | `/bb-create-verif-plan` | 验证计划 |
| | `/bb-create-floorplan` | Floorplan TCL |
| **质量门控** | `/bb-gate-rtl-quality` | RTL 交付检查 |
| | `/bb-gate-test-quality` | 验证交付检查 |
| | `/bb-gate-synth-quality` | 综合交付检查 |
| | `/bb-gate-pd-quality` | PD 交付检查 |

## 设计产物目录结构

```
designs/<name>/
├── idea/
│   └── parsed_idea.json      # 解析后的设计需求
├── PRD.md                    # 产品需求文档
├── arch_spec/
│   ├── arch_doc.md           # 架构文档
│   ├── data_flow.md          # 数据流
│   └── workflow.md           # 工作流
├── mas/
│   ├── mas.json              # 微架构规范 (schema-valid)
│   ├── fsm/                  # FSM 定义
│   ├── datapath/             # 数据通路
│   └── verif_plan_seed.md    # 验证计划种子
├── rtl/
│   ├── *.sv                  # SystemVerilog 源码
│   ├── file_list.f           # 拓扑排序文件列表
│   └── rtl_artifact.json     # RTL 交付产物
├── tb/
│   ├── *.sv / *.py           # 测试平台 / cocotb
├── verif/
│   ├── verification_plan.md  # 完整验证计划
│   └── test_cases.md         # 测试用例列表
├── sim_results/
│   ├── *.log / *.vcd         # 仿真结果
├── coverage.json             # 覆盖率数据
├── test_report.json          # 验证报告
├── constraints/
│   └ *.sdc                   # 时序约束
├── synth_parallel/
│   ├── synthesis_summary.json # 并行综合结果
│   └ <module>/netlist.v      # 网表
├── synth_report.json         # 综合报告
├── pd/
│   ├── floorplan.def         # Floorplan
│   ├── placed.def / routed.def
│   ├── drc_report.txt / lvs_report.txt
│   └── timing_signoff.json   # Post-PD STA
├── gdsii/
│   └ *.gds                   # 最终布局
├── pd_report.json            # PD 交付报告
├── .handoff/
│   ├── ready-for-*.md        # 各阶段 handoff
│   ├── fix_iter.json         # 修复迭代计数
│   └── global_fix_iter.json  # 全局计数
└── ADR/
    └ *.md                    # 架构决策记录
```

## 技术栈

| 工具 | 版本 | 用途 |
|------|------|------|
| Yosys | 0.35 | RTL 综合 |
| ABC | latest | 逻辑优化 |
| OpenSTA | 2.2.0 | 静态时序分析 |
| Magic | 8.3.641 | Layout/DRC/LVS |
| Netgen | 1.5 | LVS 网表比对 |
| QRouter | 1.4 | 详细布线 |
| KLayout | 0.30.8 | GDSII 查看/DRC |

## 快速开始

```bash
# 1. 在 Claude Code 中描述设计需求
claude-code

# 2. 描述设计需求
> 设计一个 AI 推理处理器 主频1Ghz，能运行主流大模型，使用 ASAP7 PDK

# 3. 或显式触发 architect
> /bba-architect

# 4. architect 依次生成 PRD → arch_spec → MAS
#    每阶段完成后暂停，等待用户确认

# 5. 确认后继续，直到 ready-for-rtl 开启

# 6. 触发 RTL 生成
> /bba-guru-rtl

# 7. 依次触发后续阶段...
```

## 环境设置

```bash
source ~/wrk/eda_opensources/eda_env.sh
```

## 结论

Babel 把 Claude Code agent 引入芯片设计流程，用 labeled issue 做状态机，每个阶段有明确的质量门控和迭代限制。它的价值在于把 AI coding agent 的能力迁移到硬件设计领域，而不是重新发明 EDA 工具。