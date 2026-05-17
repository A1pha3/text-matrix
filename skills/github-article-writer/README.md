# github-article-writer

> 面向 GitHub 开源仓库的中文技术文章 Skill — v1.2.0

## 功能概述

将 GitHub 仓库、仓库内页面链接或 owner/repo 转化为可发布的中文技术文章。核心原则是先取证，再判断文章形态，再进入写作。

这个 skill 不把所有仓库都写成同一种“项目介绍 + 安装 + 总结”模板，而是先根据仓库证据判断更适合写成项目导读、快速上手、原理拆解、源码分析还是实验性评估。

## 新增能力：文章形态路由

- 在选题阶段强制判断文章主形态，避免一个仓库同时被写成教程、架构分析和源码分析的混合体。
- 当仓库呈现多子系统、并行机制、benchmark、trade-off 等结构性信号时，优先进入“原理拆解 / 架构分析”。
- 将“核心判断、目标读者、证据集合、不覆盖什么”作为正文前的最小决策骨架。

## 新增能力：分析型文章增强

- 当文章落到架构分析、benchmark 解读或系统评测时，自动转调 cn-doc-writer 的 deep-dive 规则。
- 强制要求开头先给判断，前 20% 给系统地图，并至少补一个任务流案例。
- benchmark 段必须解释“测什么、反映哪部分系统、不能推出什么”。
- 结尾要求给采用顺序、适用边界或决策建议，而不是停在泛化总结。

## 三种模式

| 模式 | 用途 |
| ------ | ------ |
| `分析` | 输出仓库信息卡、选题方向和证据不足项 |
| `写作` | 产出完整中文技术文章与 Hugo Frontmatter |
| `发布` | 在明确要求时落库到目标仓库并汇报发布结果 |

## 文件结构

```text
github-article-writer/
├── SKILL.md                           # 核心工作流
├── skill.json                         # Skill 元数据
├── README.md                          # 本文件
├── CHANGELOG.md                       # 版本变更记录
└── references/
    ├── article-shapes.md              # 仓库证据到文章形态的路由规则
    ├── frontmatter-template.md        # Hugo Frontmatter 提醒
    └── publish-index-template.md      # 发布索引模板
```

## 工作流概览

```text
1. 识别 GitHub 链接 / owner-repo
2. 仓库取证：README、docs、示例、目录、维护迹象
3. 判断文章形态：导读 / 上手 / 架构 / 源码 / 实验评估
4. 调用 cn-doc-writer 生成正文
5. 调用 hugo-writer 生成 Frontmatter
6. 用户明确要求时再执行发布
```

## 与其他 Skill 的关系

| 能力 | 依赖 |
| ------ | ------ |
| 中文技术写作 | `../cn-doc-writer/SKILL.md` |
| 架构分析增强 | `../cn-doc-writer/references/blog-deep-dive.md` |
| Hugo Frontmatter | `../hugo-writer/SKILL.md` |

github-article-writer 负责“仓库取证 + 文章形态路由 + 写作任务编排”，不重复维护 cn-doc-writer 已经沉淀好的中文技术写作规则。

## 适用场景

- 根据 GitHub 仓库写技术文章、项目解读、Hugo 博文。
- 分析开源项目的架构、源码、benchmark 或工程边界。
- 把仓库资料整理成可发布的中文技术笔记。

## 不适用场景

- 纯新闻快讯、融资资讯、行情速报。
- 没有仓库证据、只有营销诉求的文案。
- 需要伪造未公开路线图、性能结论或维护状态的场景。

## 更新日志

完整历史见 [CHANGELOG.md](CHANGELOG.md)。

| 版本 | 变更 |
| ------ | ------ |
| v1.2.0 | 新增文章形态路由 `references/article-shapes.md`；主 SKILL 接入架构分析 / benchmark 解读的 deep-dive 分支；补齐 README、skill.json、CHANGELOG 元数据，统一仓库版与安装版结构。 |
| v1.1.0 | 建立 GitHub 仓库取证、中文技术写作、Hugo Frontmatter 与发布模式的基础工作流。 |

## 许可证

内部使用。
