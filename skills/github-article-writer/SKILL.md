---
name: github-article-writer
description: 面向 GitHub 开源仓库的中文技术文章工作流。适用于用户提供 github.com 仓库链接、owner/repo，或要求“分析这个项目并写文章”“整理成技术笔记”“为 text-matrix 产出文章”等场景。覆盖仓库取证、选题定位、中文技术写作、Hugo frontmatter 生成与发布前校验；关键词：GitHub URL、开源项目分析、技术文章、仓库解读、text-matrix。
version: 1.0.0
tags: ["github", "article", "hugo", "technical-writing", "workflow"]
---

# GitHub 技术文章工作流

将 GitHub 仓库转化为可发布的中文技术文章，核心原则是先取证，再写作。

## 1. 适用边界

### 适合

- 用户提供 GitHub 仓库链接、owner/repo，或要求分析某个开源项目
- 目标产物是中文技术文章、项目解读、教程型技术笔记
- 目标站点是 text-matrix 或兼容 Hugo Frontmatter 的内容库

### 不适合

- 纯新闻快讯、融资资讯、行情速报
- 没有仓库证据、只有模糊想法的营销文案
- 要求伪造未公开数据、性能结论或项目路线图

## 2. 先做路由

收到任务后，先判断任务范围。

| 模式 | 触发信号 | 输出 |
|------|----------|------|
| 分析 | “看看这个项目值不值得写”“帮我分析这个仓库” | 仓库信息卡 + 选题建议 |
| 写作 | “根据这个仓库写文章”“整理成技术笔记” | 完整文章草稿 |
| 发布 | 明确要求“发布到 text-matrix / 飞书 / 更新索引” | 文章文件 + 发布结果 |

默认执行“写作”模式；只有明确要求时才进入“发布”模式。

## 3. 执行流程

### Step 1: 仓库取证

先从 GitHub 页面、README、docs、示例、发行记录中收集证据，再决定文章结构。

最低取证项：

- 仓库全名与链接
- 仓库一句话描述
- Stars、Forks、主要语言
- README 中的项目定位、核心能力、安装方式、快速开始
- 最近维护迹象：最新提交、Release、Issue/PR 活跃度中至少一项

可选补充项：

- 目录结构
- 核心模块或关键源码
- 示例项目、演示站、论文或官方文档

取证原则：README 足够时不必深挖源码；README 不足时再进入关键目录或核心文件；无法确认的信息标记为“未知”或“未在仓库中明确说明”，禁止补写。

### Step 2: 选题定位

根据证据判断文章主轴，只保留一个主叙事。

优先级如下：

1. 新范式或新架构：适合写“原理拆解”
2. 强工具属性或可上手：适合写“教程/快速入门”
3. 代码结构清晰、实现有亮点：适合写“源码分析”
4. 项目较新但信息有限：适合写“项目导读 + 使用边界”

选题输出至少包含：

- 目标读者
- 一句话标题方向
- 为什么值得写
- 本文不覆盖什么

### Step 3: 生成文章草稿

进入写作阶段时，必须加载 [skills/cn-doc-writer/SKILL.md](skills/cn-doc-writer/SKILL.md)，再将仓库证据整理为写作输入。文章默认定位为：

- 分类：技术笔记
- 文风：专业、克制、可验证
- 目标：帮助读者判断项目价值并完成首次上手

推荐结构：

1. 项目概览
2. 学习目标或读者收益
3. 核心问题与解决思路
4. 架构或关键机制
5. 安装与最小示例
6. 代码结构或模块拆解
7. 适用场景、优势与边界
8. 常见问题或使用建议
9. 总结与延伸阅读

结构不是硬性模板；若仓库信息不足，优先缩短而不是补写空章节。

### Step 4: 三轮事实校验

草稿完成后，必须按顺序完成以下检查：

1. 事实一致性：仓库名、作者、Stars、命令、配置项与仓库页面一致
2. 术语一致性：同一概念的中英文叫法保持统一，首次出现时可保留原文并加中文括注
3. 证据边界：删除所有无来源的性能结论、兼容性承诺、路线图推断

任意一轮失败都要先修正，再进入 Frontmatter 或发布阶段。

### Step 5: 生成 Hugo Frontmatter

生成 Frontmatter 前，必须加载以下文件：

- [skills/hugo-writer/SKILL.md](skills/hugo-writer/SKILL.md)
- [skills/github-article-writer/references/frontmatter-template.md](skills/github-article-writer/references/frontmatter-template.md)

Frontmatter 约束：categories 必须是 ["技术笔记"]；tags 保持 2-5 个精准名词；date 必须使用生成当下的北京时间且格式完整；description 必须是 50-100 字纯文本摘要。

除非用户明确要求只输出大纲，否则写作模式默认产物应是“完整文章 + 合法 Frontmatter”。

### Step 6: 发布与落库

只有在用户明确要求发布时，才执行本步骤。

发布前必须确认：

- 文章文件路径
- 当前工作区是否就是目标仓库
- 用户是否要求同步飞书
- 用户是否要求更新发布索引

如果需要更新发布索引，按需加载 [skills/github-article-writer/references/publish-index-template.md](skills/github-article-writer/references/publish-index-template.md)。

发布结果至少回报：

- 文章文件路径
- git commit hash 或未提交状态
- 飞书文档链接或未同步原因
- publish-index 是否已更新

## 4. 输出格式

### 分析模式

- 仓库信息卡
- 值得写的角度
- 推荐标题与文章结构
- 证据不足项

### 写作模式

- 完整 Markdown 文章
- 合法 Hugo Frontmatter
- 如有不确定信息，在文中显式标注边界

### 发布模式

- 写作模式全部产物
- 发布结果摘要
- 未完成项与原因

## 5. 必须与禁止

### 必须

- 先取证，再写作；禁止按仓库名想象内容
- 只基于 GitHub 页面、README、文档、示例、源码等可验证材料写作
- 信息不足时收缩文章范围，而不是扩写空洞章节
- 默认输出中文
- 默认保留英文术语，并在首次出现时加中文括注
- 发布前完成三轮事实校验

### 禁止

- 禁止伪造 Stars、Forks、License、维护状态、路线图、Benchmark
- 禁止把 README 中没有的命令写成“官方推荐命令”
- 禁止在未获明确指令时执行 git push、创建飞书文档、更新索引
- 禁止依赖固定机器路径；始终以当前工作区或用户指定路径为准
- 禁止为了凑结构补写“最佳实践”“FAQ”“性能优化”之类空章节

## 6. 异常处理

| 情况 | 处理 |
|------|------|
| 只有仓库名，没有链接 | 可先按 owner/repo 分析；无法确认时要求补充链接 |
| README 很短 | 进入目录结构、示例和关键文件补证 |
| 仓库不可访问 | 告知证据不足，只能基于用户提供材料写作 |
| 项目明显未完成 | 将文章改为“项目导读/实验性评估”，不要写成成熟方案指南 |
| 用户只要摘要 | 输出项目解读，不强制生成完整文章 |

## 7. 按需加载

不要预加载全部参考文件，只在对应步骤读取。

| 需要什么 | 加载哪里 |
|----------|----------|
| 中文技术写作 | [skills/cn-doc-writer/SKILL.md](skills/cn-doc-writer/SKILL.md) |
| Hugo Frontmatter 生成 | [skills/hugo-writer/SKILL.md](skills/hugo-writer/SKILL.md) |
| Frontmatter 字段提醒 | [skills/github-article-writer/references/frontmatter-template.md](skills/github-article-writer/references/frontmatter-template.md) |
| 发布索引格式 | [skills/github-article-writer/references/publish-index-template.md](skills/github-article-writer/references/publish-index-template.md) |

## 8. 输出前自检

- 本文的每个关键判断是否都能回溯到仓库证据
- 标题、摘要、正文是否围绕同一个主叙事
- 安装命令、配置项、代码示例是否来自可验证材料
- 是否错误进入了发布模式
- Frontmatter 是否符合 Hugo 站点规范
