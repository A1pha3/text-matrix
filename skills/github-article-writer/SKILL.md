---
name: github-article-writer
description: "面向 GitHub 开源仓库的中文技术文章工作流。只要用户输入任意 GitHub 仓库链接、仓库内页面链接、github.com URL 或 owner/repo，就应激活本 skill；如果消息里只有链接或链接加一句短指令，默认直接进入写作模式并产出中文技术文章。适用于“根据这个 GitHub 链接写文章”“分析这个 repo 并写成技术笔记”“把这个仓库整理成 Hugo 文章”等场景。覆盖仓库取证、文章形态路由、中文技术写作、Hugo frontmatter 生成与发布前校验，并支持架构分析 / benchmark 解读场景下的深度技术博客增强；关键词：GitHub URL、仓库链接、repo link、owner/repo、开源项目分析、技术文章、架构分析、benchmark 解读、text-matrix。"
version: 1.2.0
tags: ["github", "article", "hugo", "technical-writing", "workflow"]
---

# GitHub 技术文章工作流

将 GitHub 仓库转化为可发布的中文技术文章，核心原则是先取证，再写作。

## 0. 触发与默认动作

- 用户消息只要包含以下任一形式，就视为本 skill 的触发信号：`https://github.com/owner/repo`、`github.com/owner/repo`、`owner/repo`、仓库内 `tree`、`blob`、`issues`、`pull`、`releases`、`wiki` 等页面链接。
- 如果消息里只有 GitHub 链接，或只有 GitHub 链接加上“写文章”“整理成技术笔记”“写成 Hugo 文章”之类短指令，默认激活本 skill 并直接进入“写作”模式。
- 收到仓库内子页面链接时，先归一化为仓库根路径和 `owner/repo`，再继续取证与写作。
- 只有当用户明确要求“只分析不写”“只给摘要”“只做发布”时，才覆盖默认写作动作。
- 不要因为用户只给了链接就先追问题目、角度或受众；应先基于仓库证据完成首版可读草稿，再在必要时补充边界说明。

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

默认执行“写作”模式；如果输入只有 GitHub 链接，也直接进入“写作”模式；只有明确要求时才进入“发布”模式。

## 3. 执行流程

### Step 0: 去重兜底（trending 类任务强制，普通写作按需）

**触发条件**：用户给的是 GitHub Trending 抓取结果（owner/repo 列表），或子代理从 trending 榜单挑 repo 写文章。

**强制流程**：

1. 在动笔写任何一篇文章之前，**必须**先跑仓库根目录下的 `scripts/trending-dedup-check.sh`，传入本轮要写的 owner/repo 列表：
   ```bash
   cd ~/.openclaw/workspace/github/text-matrix
   bash scripts/trending-dedup-check.sh owner1/repo1 owner2/repo2 ...
   # 或从 trending JSON 喂入：
   jq -r '.repos[].full_name' .cache/github-trending/trending-raw.json | \
     bash scripts/trending-dedup-check.sh
   ```
2. 脚本返回 `exit 0`（全部未写）→ 正常进入 Step 1。
3. 脚本返回 `exit 1`（有已写）→ stdout 会列出"已写"的 repo + 命中文件路径，**必须**把这些 repo 从本轮写文章清单中**剔除**，只对脚本标记的"🆕 未写"列表动笔。
4. 脚本返回 `exit 2`（路径错）→ 立即停下来检查工作区是否在 text-matrix 仓库内，不要在错误目录里继续。

**4 重 grep 兜底原理**（`music-assistant/server` 漏判复盘，2026-06-16 23:20 师父拍板 + 6-25 单段 owner 过杀复盘，2026-06-25 16:02 师父拍板修复）：

- **A 重 - owner 段 basename 前缀匹配**（仅**多段 owner** 启用）：`music-assistant` → 命中 `music-assistant-server-*.md`（处理 `/` vs `-` 不匹配）；只在 basename 前缀匹配，不 grep 内容。单段 owner（flutter/microsoft）不启用，避免 `flutter-*.md` / `microsoft-*.md` 前缀过杀同 owner 未写的新 repo。
- **B 重 - owner-repo 拼接形式**：同时试 `music-assistant-server` 和大小写保留版，grep 文件内容
- **C 重 - git log --grep**：按 `owner/repo` 查 commit 标题
- **D 重 - git log --grep owner 段**（仅**多段 owner** 启用）：补"模糊 commit 标题"（如 `LMCache + music-assistant`）。单段 owner 不启用，避免 git log 含 owner 字符串后过杀所有 owner/* 新 repo。

任一命中即视为"已写过"，从本轮清单剔除。

**6-25 修复历史**（2026-06-25 16:02）：原 A 重用 `grep -liE` 对文件内容匹配，单段 owner（如 `microsoft`）会过杀任何含 "Microsoft" 字符串的文章（如 `ace-step-ui-ai-music-generation-guide.md`），单段 owner（如 `flutter`）会过杀任何含 "Flutter" 字符串的文章（如 `flutter-skill-claude-code-gaokao-volunteer-guide.md`）。修复后 A 重只在**多段 owner**（含 `-` 的 owner，如 `music-assistant`）时启用，且只在 basename 前缀匹配，不 grep 内容。15:00 cron 47 个 trending repo 回归测试验证：修复前 47 个全判定已写（14 个过杀），修复后正确识别 33 个已写 + 14 个真未写。

**历史教训**（2026-06-16 复盘）：6-13 trending daily 15:00 写过 `music-assistant/server`（`unified-music-hub-guide.md`），6-16 trending daily+weekly 15:00 **又**把它当"新 repo"写了一遍（`media-orchestration-guide.md`）。根因：6-16 子代理只查 git log，没在 `content/posts/tech/` 做全量 grep 兜底；`/` vs `-` 不匹配让 owner/repo grep 漏判。本 Step + 脚本彻底封死此类问题。

**历史教训**（2026-06-25 复盘）：15:00 cron 抓 47 个 trending repo，dedup-check 全部判定"已写"（exit 1）。人工精确复核发现 3 个高价值过杀（microsoft/presidio / microsoft/Webwright / flutter/flutter）+ 11 个真未写。根因：A 重 grep 内容匹配 owner 字符串（microsoft/flutter 等单段 owner 过杀），D 重 git log --grep owner 字符串（单段 owner 过杀）。修复方案：方案 2.1（A 重 + D 重都只在多段 owner 启用）。详见 `~/.openclaw/workspace/docs/anomaly-decisions/trending-dedup-check-A-owner-segment-overkill-fix-2026-06-25.md` 呈报稿。

### Step 1: 仓库取证

先从 GitHub 页面、README、docs、示例、发行记录中收集证据，再决定文章结构。**如果是 trending 类任务**，取证前先确认 `scripts/trending-dedup-check.sh` 已经跑过且本 repo 在"未写"列表里。

如果用户提供的是仓库内子页面链接，先提取并记录：

- 原始链接
- 归一化后的仓库根链接
- 对应的 `owner/repo`

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

### Step 2: 选题定位与文章形态

根据证据判断文章主轴，只保留一个主叙事。执行本步骤时，必须加载 [references/article-shapes.md](references/article-shapes.md)。

优先级如下：

1. 新范式或新架构：适合写“原理拆解”
2. 强工具属性或可上手：适合写“教程/快速入门”
3. 代码结构清晰、实现有亮点：适合写“源码分析”
4. 项目较新但信息有限：适合写“项目导读 + 使用边界”

选题输出至少包含：

- 文章形态
- 目标读者
- 一句话标题方向
- 为什么值得写
- 本文不覆盖什么

如果仓库更像“多子系统 + 并行机制 + benchmark + 适用边界”的组合，不要硬写成教程，优先进入“原理拆解 / 架构分析”。

### Step 3: 生成文章草稿

进入写作阶段时，必须加载 [../cn-doc-writer/SKILL.md](../cn-doc-writer/SKILL.md)，并先依据 [references/article-shapes.md](references/article-shapes.md) 确定正文形态，再将仓库证据整理为写作输入。文章默认定位为：

- 分类：技术笔记
- 文风：专业、克制、可验证
- 目标：帮助读者判断项目价值并完成首次上手

推荐结构按文章形态调整：

- **项目导读**：项目概览 → 为什么值得看 → 核心能力 → 适用边界 → 阅读路径
- **快速上手**：项目概览 → 安装 → 最小示例 → 常见坑点 → 适用边界
- **原理拆解 / 架构分析**：核心判断 → 系统地图 → 边界拆分 → 关键机制 → 任务流案例 → benchmark 解读 → 采用建议
- **源码分析**：项目定位 → 模块切分 → 关键调用链 → 设计取舍 → 适用边界
- **实验性评估**：项目定位 → 为什么值得观察 → 已验证信号 → 风险与未知项 → 适用人群

结构不是硬性模板；若仓库信息不足，优先缩短而不是补写空章节。

当文章形态是“原理拆解 / 架构分析”，或正文高度依赖 benchmark、系统分层、并行机制时，必须额外加载 [../cn-doc-writer/references/blog-deep-dive.md](../cn-doc-writer/references/blog-deep-dive.md)。

### Step 4: 三轮事实校验

草稿完成后，必须按顺序完成以下检查：

1. 事实一致性：仓库名、作者、Stars、命令、配置项与仓库页面一致
2. 术语一致性：同一概念的中英文叫法保持统一，首次出现时可保留原文并加中文括注
3. 证据边界：删除所有无来源的性能结论、兼容性承诺、路线图推断
4. 形态一致性：正文是否真的围绕所选文章形态展开，而不是重新滑回通用模板

如果文章形态是“原理拆解 / 架构分析”，还必须额外检查：

- 开头是否先给判断，而不是先报 Stars、Forks 或安装命令
- 前 20% 是否给出系统地图、对照表或明确总览段
- 是否至少有一个请求 / 任务流案例
- benchmark 是否解释了“测什么、不能推出什么”
- 结尾是否给出采用顺序、适用边界或决策建议

任意一轮失败都要先修正，再进入 Frontmatter 或发布阶段。

### Step 5: 生成 Hugo Frontmatter

生成 Frontmatter 前，必须加载以下文件：

- [../hugo-writer/SKILL.md](../hugo-writer/SKILL.md)
- [references/frontmatter-template.md](references/frontmatter-template.md)

Frontmatter 约束：categories 必须是 ["技术笔记"]；tags 保持 2-5 个精准名词；date 必须使用生成当下的北京时间且格式完整；description 必须是 50-100 字纯文本摘要。

除非用户明确要求只输出大纲，否则写作模式默认产物应是“完整文章 + 合法 Frontmatter”。

### Step 6: 发布与落库

只有在用户明确要求发布时，才执行本步骤。

发布前必须确认：

- 文章文件路径
- 当前工作区是否就是目标仓库
- 用户是否要求同步飞书
- 用户是否要求更新发布索引

如果需要更新发布索引，按需加载 [references/publish-index-template.md](references/publish-index-template.md)。

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
- 先判断文章形态，再写正文；不要默认所有仓库都用同一套文章模板
- 只基于 GitHub 页面、README、文档、示例、源码等可验证材料写作
- 信息不足时收缩文章范围，而不是扩写空洞章节
- 默认输出中文
- 默认保留英文术语，并在首次出现时加中文括注
- 发布前完成三轮事实校验
- 多子系统、并行机制、benchmark 密集的仓库，优先按“原理拆解 / 架构分析”处理
- **trending 类任务必须在动笔前跑 `scripts/trending-dedup-check.sh` 去重；脚本返回 exit 1 时只能写"未写"列表里的 repo，脚本标记的"已写"必须从本轮清单剔除**

### 禁止

- 禁止伪造 Stars、Forks、License、维护状态、路线图、Benchmark
- 禁止把 README 中没有的命令写成“官方推荐命令”
- 禁止把 README 的 feature list 直接扩写成文章主体
- 禁止把不同 benchmark 或不同时间尺度的指标混成同一条能力结论
- 禁止架构分析文章开头只堆 Stars、版本号、安装命令，而不给核心判断
- 禁止在未获明确指令时执行 git push、创建飞书文档、更新索引
- 禁止依赖固定机器路径；始终以当前工作区或用户指定路径为准
- 禁止为了凑结构补写“最佳实践”“FAQ”“性能优化”之类空章节
- **禁止 trending 类任务未跑 `scripts/trending-dedup-check.sh` 就动笔写文章**（2026-06-16 复盘：music-assistant/server 6-13/6-16 写重 2 篇的根因）

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
| 文章形态路由 | [references/article-shapes.md](references/article-shapes.md) |
| 中文技术写作 | [../cn-doc-writer/SKILL.md](../cn-doc-writer/SKILL.md) |
| 分析型深度增强 | [../cn-doc-writer/references/blog-deep-dive.md](../cn-doc-writer/references/blog-deep-dive.md) |
| Hugo Frontmatter 生成 | [../hugo-writer/SKILL.md](../hugo-writer/SKILL.md) |
| Frontmatter 字段提醒 | [references/frontmatter-template.md](references/frontmatter-template.md) |
| 发布索引格式 | [references/publish-index-template.md](references/publish-index-template.md) |

## 8. 输出前自检

- 本文的每个关键判断是否都能回溯到仓库证据
- 所选文章形态是否正确，且正文没有滑回通用项目介绍模板
- 标题、摘要、正文是否围绕同一个主叙事
- 安装命令、配置项、代码示例是否来自可验证材料
- 是否错误进入了发布模式
- Frontmatter 是否符合 Hugo 站点规范
