---
title: "Babel：开源EDA工具链驱动的AI原生Chiplet设计流程"
date: 2026-05-22T20:20:00+08:00
slug: "babel-ai-native-chiplet-design-open-source-eda"
github_repo: "amoslee2026/Babel"
description: "Babel 是基于开源 EDA 工具链（Yosys/OpenSTA/Magic/Netgen）和 5-agent 流水线的 AI 原生 Chiplet 设计流程，通过 Claude Code 和 labeled issue 从 PRD 驱动到 GDSII，并用三层 Spec-Code 追溯体系让需求、代码、断言、约束保持一致。"
draft: false
categories: ["技术笔记"]
tags: ["AI Agent", "EDA", "芯片设计"]
---

# Babel：开源 EDA 工具链驱动的 AI 原生 Chiplet 设计流程

Babel 把 Claude Code 这类 AI coding agent 引入芯片设计流程，用 labeled issue 驱动 5 个 agent 串联走完 PRD 到 GDSII 的全流程。它复用 Yosys、OpenSTA、Magic、Netgen 等开源 EDA 工具，把"设计师 → RTL → 验证 → 综合 → PD"的人工接力改写成 agent 间的状态机 handoff。项目创建于 2026-05-22，到 2026 年 9 月初约 42 星，仍处于早期阶段，但已经沉淀出 v1.3 版本：除了 5-agent 流水线，还包含三层 Spec-Code 追溯体系、寄存器映射 pipeline 和提交质量门禁。

| 指标 | 数值 |
|------|------|
| GitHub | [amoslee2026/Babel](https://github.com/amoslee2026/Babel) |
| ⭐ Stars | 42 |
| 🍴 Forks | 9 |
| 📜 License | GPL-3.0 |
| 💻 主要语言 | Verilog（含 SystemVerilog） |
| 🏷️ 当前版本 | v1.3 |

## 系统架构

Babel 的分层设计分三层。上层是 agent 编排层，用 Claude Code 的 slash command 和 labeled issue 驱动；中层是 skill 层，把 EDA 工具调用、质量检查、流程生成、质量门控封装成可复用 skill；下层是开源 EDA 工具层，Yosys/OpenSTA/Magic 等工具直接执行综合、时序分析、物理设计。

```
用户需求 → [bba-architect] → bba-guru-rtl → bba-guru-verification → bba-guru-synthesis → bba-guru-pd → signoff
              ↑_________________________*-needs-fix 回流__________________________|
```

三层之间通过文件系统解耦：skill 封装 agent 对 EDA 工具的调用，skill 之间不共享状态，状态只通过文件系统中的设计产物和 `.handoff/` 目录里的 labeled issue 传递。单个 agent 出错时不会牵连其他 agent，可以单独重试。

### Agent 与工具对照

| Agent | 主要 skill | 调用的 EDA 工具 |
|-------|-----------|----------------|
| `bba-architect` | `/bb-spec-review` | 无（纯文档生成） |
| `bba-guru-rtl` | `/bb-rtl-coder`, `/bb-check-lint`, `/bb-check-cdc` | verible |
| `bba-guru-verification` | `/bb-generate-tb`, `/bb-create-verif-plan` | verilator |
| `bba-guru-synthesis` | `/bb-create-sdc`, `/bb-invoke-yosys`, `/bb-invoke-opensta` | Yosys, ABC, OpenSTA |
| `bba-guru-pd` | `/bb-create-floorplan`, `/bb-invoke-magic`, `/bb-invoke-qrouter`, `/bb-invoke-klayout`, `/bb-invoke-netgen` | Magic, QRouter, KLayout, Netgen |

## Agent 流水线机制

### 为什么用 issue handoff

芯片设计流程是多阶段接力：架构师交付 MAS（微架构规范）后，RTL 工程师才能开始编码；RTL 通过 lint 后，验证工程师才能跑仿真。Babel 把这种接力关系映射成 GitHub issue 的 label 状态机，每个 agent 监听自己负责的 label，处理完后打上下一个 label。

选 issue handoff 而不是函数调用或消息队列，是因为：

- issue 自带评论、附件、关联 PR，能承载设计产物的元数据
- label 状态机对人类可读，设计师可以随时介入修改 label 强制回流
- agent 间不共享内存状态，issue 充当持久化的消息队列，崩溃后可恢复

### 5 个 Agent 的职责

| Agent | 触发 label | 输入 | 输出 | 质量门控 |
|-------|-----------|------|------|---------|
| `bba-architect` | 新设计想法 / `arch-needs-fix` | 用户需求 | PRD → arch_spec → MAS | `/bb-spec-review` 对抗评审 |
| `bba-guru-rtl` | `ready-for-rtl` / `rtl-needs-fix` | MAS | lint-clean SystemVerilog | `/bb-gate-rtl-quality` |
| `bba-guru-verification` | `ready-for-verification` | RTL | 100% 覆盖率报告 | `/bb-gate-test-quality` |
| `bba-guru-synthesis` | `ready-for-synth` / `synth-needs-fix` | RTL + SDC | timing-closed 网表 | `/bb-gate-synth-quality` |
| `bba-guru-pd` | `ready-for-pd` / `pd-rework` | 网表 | GDSII + DRC/LVS 通过 | `/bb-gate-pd-quality` |

### Issue Label 状态机

正向流转 label：`ready-for-rtl` → `ready-for-verification` → `ready-for-synth` → `ready-for-pd` → `signoff`

回流 label（带 `-needs-fix` 或 `-rework` 后缀）：`arch-needs-fix`、`rtl-needs-fix`、`synth-needs-fix`、`pd-rework`、`escalate-user`

### 迭代限制

每个 agent 有单阶段迭代限制和全局限制，防止 agent 在无法收敛的问题上死循环：

| Agent | 单阶段限制 | 全局限制 |
|-------|-----------|----------|
| architect | — | 10 |
| rtl | lint 3 次 | 10 |
| verification | coverage 8 次 | 10 |
| synthesis | timing 6 次 | 10 |
| pd | total 8 次（DRC 3 / LVS 2 / STA 3） | 10 |

超限自动触发 `escalate-user`，停止并等待用户决策。Babel 承认 AI agent 在硬件设计上无法 100% 自主收敛——把"何时放弃"做成可观察的 label，避免 agent 在死循环中耗尽配额。

## Skill 体系

Skill 是 agent 调用 EDA 工具和执行质量检查的封装单元，按用途分六类，合计 35+ 个。前四类是流水线主力，后两类支撑工程运维。

### EDA 工具 Skill

| Skill | 调用工具 | 用途 |
|-------|---------|------|
| `/bb-invoke-yosys` | Yosys | 并行综合（LLM 驱动 5-Phase） |
| `/bb-invoke-verilator` | Verilator | 仿真 + 覆盖率收集 |
| `/bb-invoke-opensta` | OpenSTA | 静态时序分析 |
| `/bb-invoke-magic` | Magic | Placement + DRC |
| `/bb-invoke-netgen` | Netgen | LVS 网表比对 |
| `/bb-invoke-qrouter` | QRouter | 详细布线 |
| `/bb-invoke-klayout` | KLayout | GDSII 导出/验证 |
| `/bb-invoke-abc` | ABC | 逻辑优化 |

### 质量检查 Skill

| Skill | 用途 |
|-------|------|
| `/bb-check-lint` | verible lint（含修复迭代） |
| `/bb-check-cdc` | CDC + RDC 检查 |
| `/bb-spec-review` | MAS 对抗评审 |
| `/bb-code-review` | RTL 代码审查 |

### 流程生成 Skill

| Skill | 用途 |
|-------|------|
| `/bb-rtl-coder` | MAS → SV 代码生成 |
| `/bb-create-sdc` | MAS → SDC 约束 |
| `/bb-generate-tb` | 测试平台生成 |
| `/bb-create-verif-plan` | 验证计划 |
| `/bb-create-floorplan` | Floorplan TCL |

### 质量门控 Skill

| Skill | 用途 |
|-------|------|
| `/bb-gate-rtl-quality` | RTL 交付检查 |
| `/bb-gate-test-quality` | 验证交付检查 |
| `/bb-gate-synth-quality` | 综合交付检查 |
| `/bb-gate-pd-quality` | PD 交付检查 |

### 辅助工具 Skill

| Skill | 用途 |
|-------|------|
| `/bb-find-module-deps` | 模块依赖拓扑排序 |
| `/bb-trace-signal-path` | 信号路径追踪 |
| `/bb-collect-coverage` | 覆盖率数据收集 |
| `/bb-search-protocol` / `/bb-search-cbb` | 协议/CBB 复用搜索 |

### 问题管理 Skill

| Skill | 用途 |
|-------|------|
| `/bb-create-issue` / `/bb-list-issues` / `/bb-close-issue` | Issue 协议：查看状态、触发阶段、关闭 issue |

质量门控 skill 是 agent 间 handoff 的守门员：上一个 agent 的产物必须通过对应门控，才会打上 `ready-for-*` label 触发下一个 agent。

## 设计产物目录结构

Babel 把每个设计的所有产物放在 `designs/<name>/` 下，目录结构反映流水线阶段：

```
designs/<name>/
├── idea/parsed_idea.json       # 解析后的设计需求
├── PRD.md                      # 产品需求文档
├── arch_spec/                  # 架构文档、数据流、工作流
├── mas/mas.json                # 微架构规范 (schema-valid)
├── rtl/                        # SystemVerilog 源码
├── tb/                         # 测试平台
├── verif/                      # 验证计划与测试用例
├── sim_results/                # 仿真结果
├── coverage.json               # 覆盖率数据
├── test_report.json            # 验证报告
├── constraints/*.sdc           # 时序约束
├── synth_parallel/             # 并行综合结果
├── synth_report.json           # 综合报告
├── pd/                         # Floorplan/Placement/Routing
├── pd_report.json              # PD 交付报告
├── gdsii/                      # 最终布局
├── .handoff/                   # 状态机持久化层
└── ADR/                        # 架构决策记录
```

`.handoff/` 目录是状态机的持久化层：`ready-for-*.md` 记录每个 handoff 的上下文，`fix_iter.json` 和 `global_fix_iter.json` 跟踪迭代次数。agent 崩溃重启后，从这两个文件恢复状态。

## 任务流案例：AI 推理处理器如何流过系统

假设用户想设计一个主频 1GHz、能运行主流大模型的 AI 推理处理器，使用 ASAP7 PDK：

1. **需求解析**：用户在 Claude Code 中描述需求，`/bba-architect` 被触发。agent 把自然语言需求解析成 `idea/parsed_idea.json`，生成 `PRD.md`，暂停等待用户确认。

2. **架构设计**：用户确认 PRD 后，agent 生成 `arch_spec/` 下的架构文档，再生成 `mas/mas.json`（schema-valid 的微架构规范）。`/bb-spec-review` 做对抗评审，通过后打 `ready-for-rtl` label。

3. **RTL 生成**：`/bba-guru-rtl` 监听到 `ready-for-rtl`，读 MAS，用 `/bb-rtl-coder` 生成 SystemVerilog，用 `/bb-check-lint` 跑 verible lint。lint 失败则自动修复，最多 3 次；通过后用 `/bb-check-cdc` 检查跨时钟域。`/bb-gate-rtl-quality` 门控通过后打 `ready-for-verification`。

4. **验证**：`/bba-guru-verification` 生成测试平台和验证计划，用 verilator 跑仿真，收集覆盖率。覆盖率不达标则补充测试用例，最多 8 次。100% 覆盖率后打 `ready-for-synth`。

5. **综合**：`/bba-guru-synthesis` 用 `/bb-create-sdc` 生成时序约束，用 `/bb-invoke-yosys` 做并行综合（LLM 驱动 5-Phase），用 `/bb-invoke-opensta` 做静态时序分析。timing 不收敛则调整约束或 RTL，最多 6 次。Timing closed 后打 `ready-for-pd`。

6. **物理设计**：`/bba-guru-pd` 用 `/bb-create-floorplan` 生成 floorplan TCL，用 `/bb-invoke-magic` 做 placement + DRC，用 `/bb-invoke-qrouter` 布线，用 `/bb-invoke-netgen` 做 LVS，用 `/bb-invoke-klayout` 导出 GDSII。DRC/LVS/STA 任一失败则返工，最多 8 次。全部通过后打 `signoff`。

7. **用户审核**：`signoff` label 触发用户审核 GDSII。用户可强制打 `*-needs-fix` label 回流到任意阶段。

agent 间没有共享内存或直接调用，状态只通过文件系统和 issue label 传递。单个 agent 失败时可以单独重试，不必回滚整条流水线。

## Spec-Code 追溯体系

流水线解决的是"接力"，追溯体系解决的是"一致"。多阶段接力跑下来，最怕需求和实现脱节：PRD 里写的要求，到 RTL 里没实现；MAS 里定义的寄存器，到验证里测错了位宽。Babel 从 v1.2 起引入三层追溯模型，把需求、代码、断言、约束绑在一起。

### 三层追溯模型

| 层 | 位置 | 标签 |
|----|------|------|
| Layer 1 | RTL 文件头 | `@requirement` / `@spec_ref` / `@spec_hash` |
| Layer 2 | 内嵌 SVA 断言 | `@verifies` / `@constraint` |
| Layer 3 | SDC 约束 | `@requirement` / `@spec_ref` / `@constraint` |

第一层声明"这段 RTL 实现哪个需求、对应规范的哪个条目、内容哈希是多少"；第二层把断言和具体需求挂钩，验证是否通过都能反查需求；第三层让时序约束也带上需求来源。三层互相交叉引用，任何一层改动，哈希或引用关系都会暴露不一致。

### REQ_ID 编码规范

跨阶段传播靠统一的 REQ_ID。从 PRD 到 ARCH 到 MAS 到 RTL 到 TB 到 SDC，同一个需求始终使用同一编号，脚本据此生成跨阶段的追溯矩阵：

| 前缀 | 含义 | 示例 |
|------|------|------|
| `REQ-M##-R###` | 模块寄存器需求 | REQ-M00-R001 |
| `REQ-M##-F###` | 模块功能需求 | REQ-M12-F001 |
| `REQ-NFR-F##` | 非功能需求（时序等） | REQ-NFR-F001 |
| `REQ-SYS-##` | 系统级需求 | REQ-SYS-001 |

### 寄存器映射 Pipeline

寄存器是最容易"定义一套、实现一套"的地方。Babel 让每个模块只有一个事实来源 `spec/MAS/<module>/regmap.md`，用脚本生成三种产物：Markdown/CMSIS-SVD 文档、SystemVerilog 断言（覆盖 reset/RO/W1C/reserved/addr 五类行为）、注入 RTL 文件头的 SHA256 spec hash。改寄存器定义时只改一处，文档、断言、哈希一起更新，天然保持一致。

README 给出示例设计各模块的规模：

| 模块 | 寄存器数 | SVA Properties | Spec Hash |
|------|---------|---------------|-----------|
| M00_SystolicArray | 4 | 22 | sha256:40d48df8c266 |
| M01_DataflowController | 10 | 52 | sha256:91d2b1405f45 |
| M02_SRAM | 3 | 18 | sha256:66d1bba70afc |
| M03_DRAMController | 4 | 20 | sha256:081931ff9be5 |
| M04_SystemBus | 7 | 36 | sha256:0e08e60cc0ad |
| M05_PowerManager | 3 | 20 | sha256:b04a03e91656 |
| M06_ClockManager | 3 | 20 | sha256:eefa1152b74a |
| M07_ResetManager | 3 | 20 | sha256:1fd07a37ec6a |

### 变更传播与提交门禁

追溯体系还要防止"改了上游忘了下游"。Babel 用 git hook 检测上游 artifact 的变更，把下游标记为 stale，提醒重跑对应 agent。`git commit` 前自动跑质量门禁：RTL lint、REQ_ID 唯一性、`@spec_hash` 一致性。三道检查全过才允许提交，避免把不一致的状态写进历史。

这套机制用文件落地：`scripts/` 下集中了 `generate_regmap_doc.py`、`generate_regmap_assertions.py`、`compute_spec_hash.py`、`babel_traceability.py`、`allocate_req_id.py`、`check_req_uniqueness.py`，分别负责文档生成、断言生成、哈希注入、追溯矩阵、编号分配与唯一性校验。

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
| Verilator | latest | Verilog 仿真 |
| verible | latest | SV lint |

Babel 通过 shell 调用这些工具，不修改工具本身。版本号来自项目 README，实际可用版本以各工具官方发布为准。

## PDK：ASAP7

Babel 的示例设计跑在 ASAP7 上——亚利桑那州立大学开源的预测性 7nm 工艺设计套件，位于 `libs/asap7/`：

| Library | 描述 |
|---------|------|
| asap7sc6t_26 | 6-track 标准单元库 |
| asap7sc7p5t_27 | 7.5-track 标准单元库 (r27) |
| asap7sc7p5t_28 | 7.5-track 标准单元库 (r28) |
| asap7_sram | SRAM 模型 |

选 ASAP7 而非真实工艺，是因为它开源、可免费使用、文档齐全，适合验证流程本身。它不代表先进工艺的真实时序行为，Babel 的结果是流程验证，不是流片签核。

## 快速开始

```bash
# 设置 EDA 工具环境
source ~/wrk/eda_opensources/eda_env.sh

# 在 Claude Code 中描述设计需求
claude-code

# 描述设计需求
> 设计一个 AI 推理处理器 主频 1GHz，能运行主流大模型，使用 ASAP7 PDK

# 或显式触发 architect
> /bba-architect

# 触发 RTL 生成
> /bba-guru-rtl
```

`>` 开头的行是 Claude Code 的输入提示符，`/bba-*` 是 slash command。agent 会在每个质量门控点暂停，等待用户确认或自动打 label 继续。

## 学习教程

Babel 在 `tutorial/` 下提供面向电子工程毕业生的 16 章教程，覆盖 AI 原生芯片设计全流程，适合从零走一遍：

| Part | 章节 | 主题 |
|------|------|------|
| I. 范式与准备 | 01-04 | AI 原生范式、前置知识、用 Claude Code 学习、人机协作模式 |
| II. 规范驱动设计 | 05-07 | PRD、架构设计、微架构规范 (MAS) |
| III. AI 实现流程 | 08-11 | RTL 生成、验证闭环、逻辑综合、物理设计 |
| IV-V. 工具与实战 | 12-16 | EDA 工具链、NPU 实战走读、调试、术语表、延伸阅读 |

前半部分是概念铺垫，后半部分直接进 NPU 实战走读，与上文"任务流案例"互相印证。

## 采用建议

### 适合的场景

- **教学和原型验证**：Babel 把完整芯片设计流程串成可复现的 agent 流水线，适合用来理解从 PRD 到 GDSII 的每个阶段产出什么、检查什么。
- **开源 EDA 工具链练手**：想在真实设计任务中熟悉 Yosys/OpenSTA/Magic 时，Babel 提供了现成的调用封装和质量门控。
- **AI agent 流程编排参考**：issue handoff + labeled state machine 的模式可以迁移到其他多阶段接力场景。

### 需要注意的风险

- **项目成熟度**：项目创建于 2026-05-22，到 2026 年 9 月初约 42 星，仍处于早期阶段。skill 封装、迭代限制、质量门控的具体实现可能随版本变化。
- **AI agent 的收敛性**：迭代限制承认 agent 无法 100% 自主收敛。复杂设计（如大规模 SoC、模拟混合信号）很可能频繁触发 `escalate-user`，需要设计师深度介入。
- **开源 EDA 工具的能力边界**：Yosys/OpenSTA/Magic 在先进工艺节点的支持有限，Babel 目前示例使用 ASAP7 PDK（7nm 教学工艺），不代表能直接用于流片。
- **Claude Code 依赖**：整个流程依赖 Claude Code 的 agent 能力，使用前需要确认 Claude Code 订阅和 API 配额。

### 采用顺序

1. 先在 ASAP7 PDK 上跑通一个简单设计（如计数器、FIFO），熟悉 agent 流水线和 issue handoff 机制
2. 用 `/bb-spec-review` 和 `/bb-code-review` 等质量检查 skill 单独评审现有 RTL，理解 skill 封装
3. 尝试中等复杂度设计（如简单 RISC-V 核心），观察哪些阶段容易触发回流
4. 评估是否把 issue handoff 模式迁移到自己的设计流程中，与现有 EDA 工具链集成

Babel 复用开源 EDA 工具，把精力放在流程编排和质量门控上，把 agent 间协作、迭代收敛、状态持久化落成可观察的 label 和文件，设计师随时可以介入、回流或审计。

---

*相关链接：[GitHub](https://github.com/amoslee2026/Babel) | 依赖工具：Yosys、OpenSTA、Magic、Netgen、QRouter、KLayout*