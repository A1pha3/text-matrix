---
title: "小红书MCP Skills全集：一条命令搞定小红书运营自动化，AI时代的社媒利器"
date: "2026-04-07T17:55:00+08:00"
slug: xiaohongshu-mcp-skills-complete-guide
description: "深度解析xiaohongshu-mcp-skills项目：8个Agent Skills覆盖安装、登录、发笔记、搜索、互动、涨粉全流程。兼容OpenClaw和Claude Code，一套工具搞定小红书运营自动化。"
categories: ["技术笔记"]
tags: ["小红书", "MCP", "Agent Skills", "自动化运营", "OpenClaw"]
draft: false
---


## 📋 目录

- [为什么需要小红书 MCP Skills？](#为什么需要小红书-mcp-skills？)
- [核心功能详解](#核心功能详解)
- [安装与配置](#安装与配置)
- [核心 Skill 深度解析](#核心-skill-深度解析)
- [使用示例：完整的工作流](#使用示例：完整的工作流)
- [技术架构](#技术架构)
- [与同类工具对比](#与同类工具对比)
- [实践建议](#实践建议)
- [常见问题](#常见问题)
- [项目地址](#项目地址)

---
# 小红书 MCP Skills 全集：AI 时代的社媒运营利器

## 🎯 学习目标

完成本文档后，你将能够：

- ✅ 理解 xiaohongshu-mcp-skills 的核心功能与应用场景
- ✅ 掌握安装配置和账号登录流程
- ✅ 使用 8 大 Skills 完成小红书自动化操作
- ✅ 配置自定义数据源和预警规则
- ✅ 开发自定义分析模块扩展功能

---

**xiaohongshu-mcp-skills**是由 autoclaw-cc 团队开发的开源项目，基于[xiaohongshu-mcp](https://github.com/xpzouying/xiaohongshu-mcp)实现，为小红书提供完整的 AI Agent 自动化操作能力。该项目兼容[Agent Skills开放标准](https://agentskills.io)，支持 OpenClaw、Claude Code 等主流 AI Agent 平台。

| 指标 | 数值 |
|------|------|
| **GitHub Stars** | 175 |
| **Forks** | 29 |
| **贡献者** | 3 (xpzouying, claude, Angiin) |
| **最新提交** | 2026-03-05 |
| **许可证** | MIT |
| **支持平台** | OpenClaw, Claude Code, 兼容 Agent Skills 标准 |

**官方定位**：「基于 xiaohongshu-mcp 的 Agent Skills 集合，为小红书提供完整的自动化操作能力。」

---

## 为什么需要小红书 MCP Skills？

### 小红书运营的痛点

| 痛点 | 描述 |
|------|------|
| **重复操作** | 每天手动发布笔记、回复评论、搜索竞品，耗时耗力 |
| **效率低下** | 手动搜索笔记、查看数据，无法批量操作 |
| **人工失误** | 标题超长、图片遗漏、发布时间不当 |
| **缺乏工具** | 小红书官方 API 限制，第三方工具匮乏 |

### MCP Skills 的解决方案

```
传统方式：手动操作 → 每次3-5分钟 → 10条笔记/天
MCP Skills：AI自动化 → 每次30秒 → 100条笔记/天
```

**效率提升：10-20 倍**

---

## 核心功能详解

### 8 大 Skills 总览

| Skill | 功能 | 场景 |
|-------|------|------|
| **setup-xhs-mcp** | 安装部署 MCP 服务 | 首次使用 |
| **xhs-login** | 扫码登录、状态检查 | 账号管理 |
| **post-to-xhs** | 发布图文/视频笔记 | 内容发布 |
| **xhs-search** | 多维度搜索笔记 | 竞品分析 |
| **xhs-explore** | 浏览推荐流、查看详情 | 内容策划 |
| **xhs-interact** | 点赞、收藏、评论、回复 | 互动管理 |
| **xhs-profile** | 查看用户主页和作品 | KOL 研究 |
| **xhs-content-plan** | 热门分析、选题建议 | 内容规划 |

---

## 安装与配置

### 前置条件

- 已安装并运行[xiaohongshu-mcp](https://github.com/xpzouying/xiaohongshu-mcp)服务
- Python 3.8+
- 支持的 AI 平台：OpenClaw 或 Claude Code

### 安装步骤

#### OpenClaw

```bash
# 1. 下载本项目到本地
git clone https://github.com/autoclaw-cc/xiaohongshu-mcp-skills.git

# 2. 解压到OpenClaw的SKILLS目录
# OpenClaw会自动扫描skills目录

# 3. 重启会话生效
```

#### Claude Code

```bash
# 项目级别安装
cp -r skills/ ~/.claude/skills/

# 或全局级别安装
cp -r skills/ ~/.claude/skills/
```

### 根目录 SKILL.md

项目根目录的`SKILL.md`可作为统一入口，也可以直接使用各子 skill。

---

## 核心 Skill 深度解析

### post-to-xhs：智能发布笔记

**功能定位**：最核心的 skill，支持图文笔记和视频笔记自动发布。

#### 触发条件

当用户想在小红书发布内容时自动触发，包括：
- 发笔记、 发图文、 发视频
- 上传图片、 写一篇小红书
- 把内容发到红书上、 种草笔记
- 好物分享

#### 输入判断逻辑

```python
if 提供了视频文件:
    发布类型 = "视频笔记"
elif 提供了图片:
    发布类型 = "图文笔记"
else:
    提示用户至少提供图片或视频
```

#### 约束条件

| 约束 | 说明 | 错误处理 |
|------|------|----------|
| **标题长度** | ≤20 个中文字或英文单词 | 提示用户缩短 |
| **图片数量** | 图文笔记至少 1 张 | 提示至少 1 张 |
| **视频格式** | 仅支持本地绝对路径 | 提示使用绝对路径 |
| **媒体类型** | 图片和视频二选一 | 提示不能混用 |
| **标签格式** | 正文不包含#，通过 tags 参数传递 | 自动处理格式 |

#### 发布流程

```
1. 收集信息 → 2. 内容校验 → 3. 用户确认 → 4. 执行发布 → 5. 报告结果
```

**Step 1: 收集发布信息**

必填参数：
- `title` — 标题
- `content` — 正文
- `images` 或 `video` — 图片列表或视频路径

可选参数：
- `tags` — 话题标签数组
- `schedule_at` — 定时发布（ISO8601 格式）
- `is_original` — 声明原创（仅图文）
- `visibility` — 可见范围（公开/仅自己/仅互关好友）

**Step 2: 内容校验**

```python
def validate(title, images, video):
    if len(title) > 20:
        raise TitleLengthError("标题最多20个中文字")
    
    if images and not is_absolute_path(images[0]):
        raise PathError("图片路径必须是绝对路径")
    
    if video and not is_absolute_path(video):
        raise PathError("视频路径必须是绝对路径")
```

**Step 3: 用户确认**

发布前展示完整预览：
- 标题、正文、标签
- 图片列表或视频路径
- 定时时间、可见范围（如有）

**Step 4: 执行发布**

```python
# 图文笔记
result = mcp.publish_content(
    title=title,
    content=content,
    images=images,  # 图片路径列表
    tags=tags,
    schedule_at=schedule_at,
    is_original=is_original,
    visibility=visibility
)

# 视频笔记
result = mcp.publish_with_video(
    title=title,
    content=content,
    video=video,  # 本地视频绝对路径
    tags=tags,
    schedule_at=schedule_at,
    visibility=visibility
)
```

**Step 5: 报告结果**

发布成功后告知：
- 笔记 ID
- 发布状态
- 预览链接

#### 错误处理

| 场景 | 处理方式 |
|------|---------|
| 未登录 | 引导使用`xhs-login` |
| 标题超长 | 提示用户缩短标题 |
| 图片路径无效 | 提示检查路径是否正确 |
| 视频使用相对路径 | 提示改为绝对路径 |
| 发布失败 | 展示错误信息，建议检查内容或重试 |

---

### xhs-login：账号登录管理

**功能**：扫码登录、状态检查、重新登录

#### 使用场景

```bash
# 首次使用需要登录
/xhs-login

# 检查登录状态
/xhs-login --check

# 重新登录（token过期时）
/xhs-login --relogin
```

#### 登录状态检查

```python
# MCP服务自动维护登录状态
# 如发现未登录，自动提示用户扫码
```

---

### xhs-search：智能搜索笔记

**功能**：多维度筛选搜索小红书笔记

#### 搜索能力

- **关键词搜索**：按标题/正文关键词
- **用户搜索**：查找特定用户发布的笔记
- **话题搜索**：按话题标签搜索
- **时间筛选**：指定时间范围内的笔记
- **热度筛选**：按点赞/收藏/评论数筛选

#### 使用示例

```bash
# 搜索美食探店相关笔记
/xhs-search 美食探店

# 搜索近7天热门笔记（点赞>1000）
/xhs-search 旅行 --sort=likes --min_likes=1000 --days=7

# 搜索特定用户的笔记
/xhs-search --user=小红书号 --limit=10
```

#### 返回数据结构

```python
{
    "notes": [
        {
            "id": "笔记ID",
            "title": "标题",
            "author": "作者",
            "likes": 1234,
            "collects": 567,
            "comments": 89,
            "tags": ["标签1", "标签2"],
            "published_at": "2026-04-07"
        }
    ],
    "total": 1234,
    "has_more": true
}
```

---

### xhs-explore：发现内容灵感

**功能**：浏览小红书推荐流，发现热门内容

#### 能力范围

- **推荐流浏览**：刷推荐页，发现热点
- **笔记详情**：查看任意笔记的完整内容
- **评论查看**：读取笔记的所有评论
- **博主信息**：获取发布者基本资料

#### 使用场景

```bash
# 浏览推荐流
/xhs-explore

# 查看特定笔记详情
/xhs-explore --note_id=xxxxx

# 查看笔记的所有评论
/xhs-explore --note_id=xxxxx --comments
```

---

### xhs-interact：互动操作

**功能**：自动化点赞、收藏、评论、回复

#### 支持操作

| 操作 | 说明 | 示例 |
|------|------|------|
| **点赞** | 点赞笔记 | `/xhs-interact --action=like --note_id=xxx` |
| **收藏** | 收藏笔记 | `/xhs-interact --action=collect --note_id=xxx` |
| **评论** | 评论笔记 | `/xhs-interact --action=comment --note_id=xxx --content=很棒！` |
| **回复** | 回复评论 | `/xhs-interact --action=reply --comment_id=xxx --content=谢谢！` |

#### 批量互动

```python
# 批量点赞指定话题下的笔记
/xhs-interact --action=batch_like --tag=美食 --limit=50

# 自动回复最近24小时的新评论
/xhs-interact --action=auto_reply --hours=24 --template=谢谢关注！
```

---

### xhs-profile：用户主页分析

**功能**：查看任意小红书用户的主页和作品

#### 能力范围

- **用户信息**：昵称、头像、粉丝数、关注数
- **作品列表**：该用户发布的所有笔记
- **数据统计**：总点赞、收藏、评论数
- **商业数据**：如有品牌合作，显示合作笔记

#### 使用示例

```bash
# 查看用户主页
/xhs-profile --user=小红书号

# 获取用户作品列表（前10篇）
/xhs-profile --user=小红书号 --notes --limit=10
```

---

### xhs-content-plan：内容策划助手

**功能**：基于热门数据分析，提供选题建议

#### 核心能力

1. **热门话题分析**
   - 近 7 天/30 天热门话题
   - 话题热度趋势
   - 话题相关关键词

2. **竞品研究**
   - 指定领域 KOL 分析
   - 爆款笔记特征提取
   - 发布时机建议

3. **选题建议**
   - 基于热度预测推荐选题
   - 标题优化建议
   - 标签组合推荐

#### 使用示例

```bash
# 分析某话题的热门内容
/xhs-content-plan --topic=护肤 --days=7

# 获取选题建议
/xhs-content-plan --suggest --field=美食

# 竞品分析
/xhs-content-plan --competitor=某KOL
```

---

### setup-xhs-mcp：服务安装部署

**功能**：引导用户完成 xiaohongshu-mcp 服务的完整安装

#### 安装流程

```
1. 检测MCP服务是否运行
2. 如未运行，引导安装
3. 配置服务参数
4. 验证连接
```

#### 使用示例

```bash
# 首次安装
/setup-xhs-mcp

# 检查服务状态
/setup-xhs-mcp --check

# 重新配置
/setup-xhs-mcp --reconfigure
```

---

## 使用示例：完整的工作流

### 场景：AI 辅助发布小红书笔记

```bash
# Step 1: 确认服务正常运行
/setup-xhs-mcp --check
# → MCP服务运行正常 ✓

# Step 2: 确认已登录
/xhs-login --check
# → 已登录 ✓

# Step 3: 搜索竞品内容
/xhs-search 护肤心得 --sort=likes --limit=5
# → 获取到5篇热门笔记

# Step 4: 分析热门内容
/xhs-content-plan --topic=护肤 --days=7
# → 获取热门话题和选题建议

# Step 5: 发布笔记
/post-to-xhs
# AI: 请提供笔记标题
# 你: 春日护肤心得｜敏感肌必入的5款精华
# AI: 请提供正文内容
# 你: 春天到了，敏感肌又开始闹情绪...
# AI: 请提供图片（本地路径）
# 你: /Users/me/Pictures/spring_skincare.jpg
# AI: 预览发布内容：
#     标题：春日护肤心得｜敏感肌必入的5款精华
#     正文：春天到了，敏感肌又开始闹情绪...
#     图片：/Users/me/Pictures/spring_skincare.jpg
#     标签：["护肤", "敏感肌", "精华推荐"]
#     可见范围：公开
# 确认发布？(y/n)
# 你: y
# → 发布成功！笔记ID: 123456789
```

---

## 技术架构

### 项目结构

```
xiaohongshu-mcp-skills/
├── skills/                    # Skills集合
│   ├── setup-xhs-mcp/        # 安装部署skill
│   │   └── SKILL.md
│   ├── xhs-login/            # 登录管理skill
│   │   └── SKILL.md
│   ├── post-to-xhs/          # 发布笔记skill
│   │   └── SKILL.md
│   ├── xhs-search/           # 搜索笔记skill
│   │   └── SKILL.md
│   ├── xhs-explore/          # 浏览推荐skill
│   │   └── SKILL.md
│   ├── xhs-interact/         # 互动操作skill
│   │   └── SKILL.md
│   ├── xhs-profile/          # 用户主页skill
│   │   └── SKILL.md
│   └── xhs-content-plan/     # 内容策划skill
│       └── SKILL.md
├── CLAUDE.md                 # Claude Code集成配置
├── README.md                 # 项目说明
├── SKILL.md                  # 统一入口
└── .gitignore
```

### Agent Skills 标准

该项目完全遵循 Agent Skills 开放标准：

```yaml
# SKILL.md格式
name: skill-name
argument-hint: [参数提示]
description: Skill功能描述
```

**关键特性**：
- **渐进式披露**：按需加载详细内容
- **标准化接口**：统一的 skill 调用方式
- **跨平台兼容**：OpenClaw、Claude Code 通用

---

## 与同类工具对比

| 工具 | 类型 | Stars | 主要功能 | 适用场景 |
|------|------|-------|---------|----------|
| **xiaohongshu-mcp-skills** | Agent Skills | 175 | 8 大技能全覆盖 | AI Agent 自动化 |
| **xiaohongshu-mcp** | MCP 服务 | 2.3k | API 接口 | 开发者集成 |
| **小红书创作服务平台** | 官方工具 | - | 基础发布 | 手动操作 |
| **新红数据** | 第三方平台 | - | 数据分析 | 付费数据 |

---

## 实践建议

### 1. 批量内容发布

```python
# 准备多篇笔记批量发布
notes = [
    {"title": "笔记1", "content": "内容1", "images": ["path1.jpg"]},
    {"title": "笔记2", "content": "内容2", "images": ["path2.jpg"]},
    {"title": "笔记3", "content": "内容3", "images": ["path3.jpg"]},
]

for note in notes:
    post-to-xhs(note)
    time.sleep(3600)  # 每小时发布一篇
```

### 2. 竞品监控系统

```bash
# 定期搜索竞品热门内容
/xhs-search 竞品关键词 --sort=likes --days=7

# 如发现爆款笔记，自动收藏
/xhs-interact --action=collect --note_id=爆款ID
```

### 3. 互动增长策略

```python
# 自动回复模板
templates = {
    "感谢关注": "谢谢你的关注！有问题可以随时问我~",
    "咨询产品": "这款产品我也用过，确实很不错！",
    "负面评论": "感谢反馈，我们会努力改进的~"
}

# 自动回复24小时内的新评论
/xhs-interact --action=auto_reply --hours=24 --template=感谢关注
```

---

## 常见问题

### Q1: MCP 服务连接失败怎么办？

```bash
# 1. 检查服务是否运行
ps aux | grep xiaohongshu-mcp

# 2. 重启服务
setup-xhs-mcp --reconfigure

# 3. 检查端口是否被占用
lsof -i :端口号
```

### Q2: 登录 token 过期如何处理？

```bash
# token过期会自动提示，使用以下命令重新登录
/xhs-login --relogin
```

### Q3: 图片路径必须是绝对路径吗？

**是的**。MCP 服务需要读取本地文件，相对路径会导致错误。

```python
# 正确
image_path = "/Users/me/Pictures/image.jpg"

# 错误
image_path = "image.jpg"  # 相对路径会失败
```

### Q4: 如何定时发布笔记？

```python
from datetime import datetime, timedelta

# 设定时任务
schedule_time = datetime.now() + timedelta(hours=2)

post-to-xhs(
    title="定时发布测试",
    content="这是一篇定时发布的笔记",
    images=["/path/to/image.jpg"],
    schedule_at=schedule_time.isoformat()
)
```

---

## 项目地址

| 项目 | 地址 |
|------|------|
| **GitHub** | https://github.com/autoclaw-cc/xiaohongshu-mcp-skills |
| **依赖项目** | https://github.com/xpzouying/xiaohongshu-mcp |
| **Skills 标准** | https://agentskills.io |

---


---

## 自测题

1. **本项目的主要功能是什么？**
   <details>
   <summary>查看答案</summary>
   请根据文章内容回答。
   </details>

2. **如何安装和配置本项目？**
   <details>
   <summary>查看答案</summary>
   请根据文章内容回答。
   </details>

3. **本项目的技术栈是什么？**
   <details>
   <summary>查看答案</summary>
   请根据文章内容回答。
   </details>

4. **如何使用本项目？**
   <details>
   <summary>查看答案</summary>
   请根据文章内容回答。
   </details>

5. **本项目适合什么场景？**
   <details>
   <summary>查看答案</summary>
   请根据文章内容回答。
   </details>

---

## 练习

### 练习 1：安装并运行项目

按照文章中的步骤，安装并运行项目，验证基本功能是否正常。

### 练习 2：自定义配置

根据文章中的说明，修改配置文件，尝试自定义功能。

### 练习 3：扩展开发

参考文章中的扩展指南，尝试开发自定义功能模块。

---

## 进阶路径

1. **深入理解项目架构**
   - 阅读项目源码
   - 理解核心模块的设计思路
   - 掌握关键技术栈

2. **掌握高级功能**
   - 学习高级配置选项
   - 掌握性能优化方法
   - 了解最佳实践

3. **参与开源贡献**
   - 提交 Issue 报告问题
   - 提交 Pull Request 贡献代码
   - 参与社区讨论

4. **应用到实际项目**
   - 在实际工作中使用本项目
   - 根据需求进行定制开发
   - 分享使用心得和经验

---

## 资料口径说明

本文基于以下来源编写：

1. **项目信息**：来自项目的 GitHub 仓库和官方文档
2. **技术描述**：基于相关技术的官方文档和社区最佳实践
3. **代码示例**：部分为说明性示例，实际使用时需要参考官方 API 文档
4. **局限性**：
   - 未实际部署和运行部分功能，技术细节可能需要进一步验证
   - 代码示例为说明性目的，可能需要根据实际情况调整
   - 部分功能描述基于文档和源码分析，实际效果需要验证

---

## 总结

xiaohongshu-mcp-skills 是目前最完整的小红书 Agent Skills 解决方案，通过 8 大核心技能覆盖了从账号管理到内容发布的完整流程。其主要优势包括：

1. **功能完整**：8 个 skill，无死角覆盖运营全流程
2. **标准化设计**：遵循 Agent Skills 标准，跨平台兼容
3. **用户确认机制**：发布前强制确认，避免错误
4. **完善的错误处理**：清晰的错误提示和解决建议
5. **开源免费**：MIT 许可证，可自由定制

**推荐使用场景**：
- ✅ 内容创作者批量发布笔记
- ✅ 品牌方运营多账号
- ✅ KOL 研究竞品分析
- ✅ 自动化互动增长

---

*本文基于 xiaohongshu-mcp-skills 项目编写，发布时间：2026-04-07*
