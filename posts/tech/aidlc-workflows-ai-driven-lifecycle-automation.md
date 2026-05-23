# aidlc-workflows: AI驱动开发周期的自适应工作流引擎

**🏷️ 分类：** AI编程 · 开发流程  
**⭐ Stars：** 2,375  
**🔗 地址：** https://github.com/awslabs/aidlc-workflows  
**🌐 官网：** -

**一句话总结：** AWS Labs出品的AI驱动生命周期工作流系统，为AI编码Agent提供自适应导航规则，让Agent能自主驾驭复杂项目的开发全流程。

---

## 🎯 这个工具解决什么问题？

AI编码Agent（如Devin、Cursor Agent）在处理**跨文件、跨模块**的复杂任务时常常迷路——不知道先改什么、后改什么，遇到依赖关系就卡住。aidlc-workflows 为AI Agent提供**结构化的生命周期导航**，让Agent在代码生成、测试、部署各阶段都有明确指引。

---

## ⚡ 核心特性

### 1. 自适应工作流引擎
根据项目特征自动调整工作流步骤，而非一刀切

### 2. AI友好的生命周期阶段
预定义：需求理解 → 代码生成 → 测试验证 → 部署上线，每个阶段都有Agent可执行的checklist

### 3. 项目上下文感知
能理解项目架构、依赖关系、代码风格指南，生成符合项目规范的代码

### 4. AWS深度集成
与AWS CodePipeline、CodeBuild等原生集成，AI生成的代码直接可部署

### 5. 可观测性
每个工作流步骤都可追踪，方便调试Agent行为

---

## 📦 安装

```bash
pip install aidlc-workflows
# 或
git clone https://github.com/awslabs/aidlc-workflows
cd aidlc-workflows && pip install -e .
```

---

## 🚀 快速上手

```yaml
# aidlc-workflow.yaml
name: full-stack-app
stages:
  - understand_requirements
  - generate_code
  - write_tests
  - deploy
rules:
  # AI Agent遵循的决策规则
  cross_file_deps: warn
  test_coverage_min: 80%
```

```bash
aidlc run full-stack-app
```

---

## 💡 适用场景

| 场景 | 说明 |
|------|------|
| AI代码审查 | 结构化审查流程，减少遗漏 |
| 复杂项目重构 | Agent遵循阶段指引，降低破坏风险 |
| CI/CD优化 | AI自动调整流水线配置 |
| 技术债务管理 | 系统化识别和消除技术债务 |

---

**相关工具：** [Superpowers](superpowers-agentic-development-methodology) · [Claude Plugins Official](chrome-devtools-mcp-ai-coding-agents-chrome-devtools) · [CodeGraph](colbymchenry-codegraph-semantic-code-knowledge-graph-guide)