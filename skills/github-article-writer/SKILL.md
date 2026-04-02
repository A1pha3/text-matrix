---
name: github-article-writer
description: "当收到GitHub仓库链接时，自动分析仓库信息并撰写顶级技术文档。使用方法：发送GitHub URL给AI，AI会自动：(1)抓取仓库信息，(2)使用cn-doc-writer写文章（三遍自检），(3)用hugo-writer检查格式，(4)发布到飞书和text-matrix，(5)更新publish-index.md。触发词：收到github.com链接、帮忙写文章、分析这个项目。"
---

# GitHub 文章自动写作 Skill

当收到 GitHub 仓库链接时，自动完成从信息抓取到发布的完整流程。

## 工作流程

```
GitHub URL → 抓取信息 → cn-doc-writer写文章 → hugo-writer检查 → 发布飞书+GitHub → 更新索引
```

## Step 1: 抓取 GitHub 仓库信息

使用浏览器打开 GitHub 页面，抓取以下信息：

**必抓信息**：
- 仓库全名（如 `facebookresearch/HyperAgents`）
- Stars / Forks / Watchers 数量
- 最新提交日期
- README 内容（核心！）
- 仓库描述

**可选信息**：
- 目录结构
- 主要源文件内容
- 示例代码

**抓取命令**：
```bash
# 打开仓库首页
browser.open(url="https://github.com/{owner}/{repo}")

# 等待加载后截图获取信息
browser.snapshot()
```

## Step 2: 使用 cn-doc-writer 写文章

### 2.1 文章定位

技术文档（而非行业快讯），分类为 `["技术笔记"]`

### 2.2 文章结构（10-15章）

```
# {项目名}：一句话描述

## 学习目标
学完本文后掌握的核心技能（6条左右）

## 一、项目概述
- 基本信息表格（Stars/Forks/License/语言等）
- 项目定位和核心功能
- 解决的问题

## 二、核心概念与原理
- 核心技术点解析
- 架构设计
- 工作原理

## 三、深入分析
- 核心算法（如适用）
- 代码结构
- 关键技术细节

## 四、安装与配置
- 环境要求
- 安装命令
- 基础配置

## 五、快速入门
- 最小可用示例
- Hello World 示例

## 六、使用详解
- 主要功能的使用方法
- 常用命令
- 参数说明

## 七、开发扩展
- API 接口
- 自定义开发
- 插件扩展

## 八、最佳实践
- 生产环境注意事项
- 性能优化
- 安全考虑

## 九、FAQ
常见问题解答（5-8条）

## 十、总结
核心要点回顾、生态现状、未来展望

## 相关链接
| 资源 | 地址 |
```

### 2.3 自检三遍

**第一遍：事实准确性**
- [ ] Stars/Forks/License 等数字与 GitHub 页面一致
- [ ] README 描述与实际功能一致
- [ ] 无臆造的命令或参数
- [ ] 代码示例为真实语法（非占位符）

**第二遍：术语一致性**
- [ ] 英文术语首次出现时附中文解释
- [ ] 全文档同一术语使用一致
- [ ] 无拼写错误

**第三遍：格式合规**
- [ ] frontmatter 格式正确
- [ ] categories: ["技术笔记"]
- [ ] tags: 2-5 个精准名词
- [ ] slug: 小写英文连字符
- [ ] description: 50-100 字

## Step 3: hugo-writer 检查格式

### frontmatter 模板

```yaml
---
title: "{项目名}：{一句话描述}"
date: {当前系统时间，格式：YYYY-MM-DDTHH:MM:SS+08:00}
slug: "{小写英文连字符}"
description: "{50-100字的摘要}"
draft: false
categories: ["技术笔记"]
tags: ["标签1", "标签2", ...]
---
```

**日期必须是当前系统时间**，使用北京时间 `+08:00`。

## Step 4: 发布

### 4.1 GitHub (text-matrix)

```bash
cd ~/.openclaw/workspace/GitHub/text-matrix

# 添加文件
git add content/posts/tech/{slug}.md

# 提交（commit message 以 emoji 开头）
git commit -m "📝 {中文标题}"

# 推送（如果失败，执行 git pull --rebase 再 push）
git push
```

### 4.2 飞书文档

```bash
# 1. 创建文档
feishu_doc(action=create, title="{文章标题}")

# 2. 写入内容（分批 append）
feishu_doc(action=append, doc_token="{文档ID}", content="{markdown内容}")

# 3. 获取返回的文档 URL 备用
```

### 4.3 更新发布索引

编辑 `~/.openclaw/workspace/memory/publish-index.md`，添加一行：

```markdown
| **{项目名}** | {owner}/{repo} | {Stars} | {slug}.md | {commit hash} | {飞书文档ID} | {日期} |
```

## Step 5: 完成后汇报

向用户报告：
- GitHub commit hash
- 飞书文档链接
- 文章核心内容概述

## 参考信息

### 常用数据源

| 源 | 用途 |
|-----|------|
| 36kr | AI 新闻 |
| 量子位 | AI 产品 |
| FT中文网 | 金融财经 |
| V2EX | 副业机会 |

### 发布索引位置

`~/.openclaw/workspace/memory/publish-index.md`

### cn-doc-writer 位置

`~/.openclaw/workspace/skills/cn-doc-writer/SKILL.md`

### hugo-writer 位置

`~/.openclaw/workspace/github/text-matrix/skills/hugo-writer/SKILL.md`

## 注意事项

1. **禁止臆造**：所有信息必须来自 GitHub 页面或 README，不可臆造
2. **链接必须可点击**：飞书文档中使用 `[文字](完整URL)` 格式
3. **图片处理**：飞书不支持本地图片，使用在线图片 URL
4. **代码示例**：如无法确认准确性，标注为"概念性代码"或"基于推断"
5. **Git push 验证**：推送后必须确认成功，失败则 `git pull --rebase` 再推
