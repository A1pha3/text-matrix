+++
date = '2026-05-22T15:54:25+08:00'
draft = false
title = 'The-Book-of-Secret-Knowledge：程序员技术手册合集'
slug = 'the-book-of-secret-knowledge-developer-swiss-army-knife'
description = 'trimstray/the-book-of-secret-knowledge 是一个精心整理的技术知识合集，收录各类技术手册、速查表、CLI 工具和 hacks，适合技术人员日常参考。'
categories = ['技术笔记']
tags = ['DevOps', '工具', '教程', 'Linux']
+++

# The-Book-of-Secret-Knowledge：程序员技术手册合集

## 一、项目概览

**GitHub:** [trimstray/the-book-of-secret-knowledge](https://github.com/trimstray/the-book-of-secret-knowledge)

这是一个技术知识合集，收录了各类技术手册、速查表、博客、hacks、单行命令、CLI/Web 工具。

## 二、内容结构

### 系统与网络

| 分类 | 内容示例 |
|------|----------|
| **Linux 命令** | 系统管理、网络配置、性能监控 |
| **网络安全** | 端口扫描、流量分析、渗透测试命令 |
| **容器编排** | Docker/K8s 常用命令速查 |
| **云服务** | AWS/GCP/Azure CLI 备忘 |

### 🛠️ 开发工具

| 分类 | 内容示例 |
|------|----------|
| **Git** | 常用操作、冲突解决、钩子配置 |
| **Shell** | Bash/Zsh 高级技巧与单行命令 |
| **编辑器** | Vim/Emacs/VSCode 快捷键速查 |
| **调试** | GDB/pdb/strace 实战命令 |

### 🔐 安全与渗透

- **Nmap 扫描技巧** - 全面端口发现与服务识别
- **Metasploit 框架** - 漏洞利用与后渗透
- **Burp Suite** - Web 安全测试配置
- **Wireshark** - 流量抓包与协议分析

### ☁️ 云原生

- Kubernetes 故障排查指南
- Terraform 模块化实践建议
- Prometheus+Grafana 监控体系

## 三、亮点特色

### 1. 实用导向
每个条目侧重可直接执行的命令和配置：

```bash
# 快速检查服务器对外开放端口
nmap -sT -F target-host

# Docker清理未使用资源
docker system prune -af

# Git强制更新远程覆盖
git fetch --all && git reset --hard origin/main
```

### 2. 结构化整理
所有内容按主题分类，配备清晰的目录索引：

```
├── README.md              # 总索引
├── _tools/               # CLI工具分类
├── _networking/          # 网络工具与命令
├── _programming/          # 编程语言参考
└── _system/              # 系统管理
```

### 3. 持续更新
社区贡献者持续更新，保持内容的时效性。

## 四、快速使用

```bash
# 克隆仓库
git clone https://github.com/trimstray/the-book-of-secret-knowledge.git

# 查看某个分类的内容
cat the-book-of-secret-knowledge/_networking/README.md

# 搜索特定命令
grep -r "nmap" . --include="*.md"
```

## 五、适用人群

- 🟢 **初学者** - 建立技术知识框架
- 🟡 **中级工程师** - 速查常用命令
- 🔴 **高级/运维** - 故障排查参考手册

## 六、总结

The-Book-of-Secret-Knowledge 的价值在于系统性：把散落在互联网各处的技术碎片整理成册。无论是紧急故障排查还是系统性学习，都可以当作参考手册。