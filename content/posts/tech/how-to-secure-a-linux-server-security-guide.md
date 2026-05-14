---
title: "How-To-Secure-A-Linux-Server：持续演进的中文版Linux服务器安全加固指南"
date: "2026-05-14T16:12:00+08:00"
slug: "how-to-secure-a-linux-server-security-guide"
description: "How-To-Secure-A-Linux-Server是由imthenachoman维护的开源安全指南，星数27,245，涵盖SSH加固、sudo/su限制、防火墙配置（UFW/iptables）、入侵检测（Fail2Ban/CrowdSec/OSSEC）、文件完整性监控、病毒扫描等Linux服务器安全全栈知识，配有Ansible自动化脚本。"
draft: false
categories: ["技术笔记"]
tags: ["Linux", "服务器安全", "SSH", "防火墙", "Fail2Ban", "安全加固"]
---

# How-To-Secure-A-Linux-Server：持续演进的中文版Linux服务器安全加固指南

## 项目概览

**How-To-Secure-A-Linux-Server** 是由 imthenachoman 在 GitHub 上维护的一个持续演进的开源安全指南，项目星数 **27,245**，Forks 1,782，定位是「一个正在成长中的 Linux 服务器安全加固指南，同时希望读者能学到一点安全知识和安全意识」。

项目的核心思路是：安全相关的信息散落在互联网上数百篇文章里，没有人有时问去逐一查阅。imthenachoman 在搭建自己的 Debian 服务器时记录了一系列笔记，最终整理成了这份综合指南。README 明确说：**「我从未找到一个涵盖所有内容的指南——这就是我的尝试。」**

## 指南覆盖内容

### SSH 服务器加固

- SSH 公私钥认证创建与管理
- 创建专用 SSH 群组（AllowGroups）限制登录
- 安全配置 `/etc/ssh/sshd_config`
- 移除短 Diffie-Hellman 密钥
- **SSH 双因素认证（2FA/MFA）**

关键提示：在修改 SSH 配置前，务必确保留有备用登录方式，否则可能把自己锁在外面。

### 基础安全措施

- **限制 sudo 使用者**：通过 `/etc/sudoers` 配置精确的权限控制
- **限制 su 使用者**：仅允许特定用户组使用 `su` 命令
- **使用 FireJail 沙箱运行应用**：进程级隔离
- **NTP 客户端配置**：确保时间同步，利于日志分析和取证
- **安全 /proc**：防止信息泄露
- **强制安全密码策略**：PAM 模块强制密码复杂度
- **自动安全更新与告警**： unattended-upgrades 配置
- **添加应急备用密码登录系统**：panic button 机制

### 网络安全

- **UFW（Uncomplicated Firewall）**：简化的 iptables 前端
- **iptables + PSAD**：入侵检测与防御
- **Fail2Ban**：应用层入侵检测与防御
- **CrowdSec**：新一代协同防御框架

### 审计与监控

- **AIDE**：文件/文件夹完整性监控
- **ClamAV**：病毒扫描
- **Rkhunter / chkrootkit**：Rootkit 检测
- **logwatch**：系统日志分析与报告
- **ss**：查看服务器监听的端口
- **Lynis**：Linux 安全审计工具
- **OSSEC**：主机入侵检测系统（HIDS）

### Ansible 自动化

[moltenbit](https://github.com/moltenbit) 提供了本指南的 Ansible Playbook 版本——[How To Secure A Linux Server With Ansible](https://github.com/moltenbit/How-To-Secure-A-Linux-Server-With-Ansible)，可实现安全配置的自动化批量部署。

## 指南特点

### 面向人群

指南明确说明：

- **针对场景**：家庭 Linux 服务器（但不排除大型/专业环境适用）
- **不涉及**：Linux 基础安装、系统使用教学、物理安全
- **不承诺**：涵盖安全的方方面面（安全是个太大的话题）

### 实用优先

- 每个步骤都提供**可直接复制粘贴的代码片段**
- 代码片段使用 `echo`、`cat`、`sed`、`awk`、`grep` 等基础命令
- 涉及文件修改前都会备份原始文件
- 不能用脚本自动化的部分，提供手动编辑指南

### 分布无关

指南尽可能保持 Linux 发行版 agnostic，但特别提到了：

- 参考 [CIS benchmarks](https://www.cisecurity.org/cis-benchmarks/) 获取各发行版的详细指南
- 参考各发行版官方文档

## 与 CIS benchmarks 的关系

README 建议读者先过一遍本指南，**然后**再看 CIS benchmarks。这样 CIS 的建议会覆盖本指南的内容，而本指南提供了更平易的入门路径。CIR benchmarks 本身是行业公认的最权威、最全面的 Linux 安全基准。

## 待办事项（To Do）

指南的 README 明确列出了尚未覆盖的内容：

- Fail2Ban 自定义 Jails
- MAC（强制访问控制）与 Linux 安全模块（LSM）
  - SELinux
  - AppArmor
- 磁盘加密
- Rkhunter 和 chrootkit（已在目录中出现但标记为 WIP）
- 日志远程存储/备份
- CIS-CAT 评估工具
- debsums 包完整性验证

## 适用场景

- 刚刚接触 Linux 服务器运维的开发者
- 需要系统化安全加固指南的运维工程师
- 想用 Ansible 批量部署安全配置的团队
- 需要抵御 SSH 暴力破解和 DDoS 的服务器管理员

---

**延伸阅读**：[GitHub 仓库](https://github.com/imthenachoman/How-To-Secure-A-Linux-Server) · [Ansible 自动化版本](https://github.com/moltenbit/How-To-Secure-A-Linux-Server-With-Ansible) · [CIS Linux Benchmarks](https://www.cisecurity.org/cis-benchmarks/)