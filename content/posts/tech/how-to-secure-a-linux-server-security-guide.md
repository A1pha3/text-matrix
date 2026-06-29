---
title: "How-To-Secure-A-Linux-Server：持续演进的中文版Linux服务器安全加固指南"
date: "2026-05-14T16:12:00+08:00"
slug: "how-to-secure-a-linux-server-security-guide"
description: "How-To-Secure-A-Linux-Server是由imthenachoman维护的开源安全指南，星数27,245，涵盖SSH加固、sudo/su限制、防火墙配置（UFW/iptables）、入侵检测（Fail2Ban/CrowdSec/OSSEC）、文件完整性监控、病毒扫描等Linux服务器安全全栈知识，配有Ansible自动化脚本。"
draft: false
categories: ["技术笔记"]
tags: ["Linux", "服务器安全", "SSH", "防火墙", "Fail2Ban", "安全加固"]
---

# How-To-Secure-A-Linux-Server：持续演进的中文版 Linux 服务器安全加固指南

## 项目概览

**How-To-Secure-A-Linux-Server** 是由 imthenachoman 在 GitHub 上维护的一个持续演进的开源安全指南，项目星数 **27,245**，Forks 1,782，定位是「一个正在成长中的 Linux 服务器安全加固指南，同时希望读者能学到一点安全知识和安全意识」。

项目的核心思路是：安全相关的信息散落在互联网上数百篇文章里，没有人有时问去逐一查阅。imthenachoman 在搭建自己的 Debian 服务器时记录了一系列笔记，最终整理成了这份综合指南。README 明确说：**「我从未找到一个涵盖所有内容的指南——这就是我的尝试。」**

## 学习目标

读完本文后，你可以：

1. **理解指南定位**：明白 How-To-Secure-A-Linux-Server 核心思路，判断它是否适合你的场景
2. **掌握安全模块**：了解 SSH 加固、防火墙配置、入侵检测、文件完整性监控等核心模块
3. **评估适用性**：判断该指南是否匹配你的服务器环境和安全需求
4. **规划学习路径**：基于指南内容制定适合你的 Linux 服务器安全加固计划
5. **结合 CIS Benchmarks**：理解本指南与 CIS Benchmarks 的关系，规划后续深入学习

## 目录

1. [项目概览](#项目概览)
2. [指南覆盖内容](#指南覆盖内容)
   - [SSH 服务器加固](#ssh-服务器加固)
   - [基础安全措施](#基础安全措施)
   - [网络安全](#网络安全)
   - [审计与监控](#审计与监控)
   - [Ansible 自动化](#ansible-自动化)
3. [指南特点](#指南特点)
   - [面向人群](#面向人群)
   - [实用优先](#实用优先)
   - [分布无关](#分布无关)
4. [与 CIS Benchmarks 的关系](#与-cis-benchmarks-的关系)
5. [待办事项（To Do）](#待办事项to-do)
6. [适用场景](#适用场景)
7. [自测题](#自测题)
8. [进阶路径](#进阶路径)
9. [资料口径说明](#资料口径说明)

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

## 自测题

1. **How-To-Secure-A-Linux-Server 的核心定位是什么？**
   <details>
   <summary>查看答案</summary>
   一个正在成长中的 Linux 服务器安全加固指南，旨在将散落在互联网上的安全信息整合在一起，为读者提供平易的入门路径。
   </details>

2. **在修改 SSH 配置前，为什么需要确保留有备用登录方式？**
   <details>
   <summary>查看答案</summary>
   因为错误的 SSH 配置可能导致你被锁在服务器外面，无法远程登录。备用登录方式（如控制台访问、另一个 SSH 端口）可以在配置出错时提供恢复途径。
   </details>

3. **本指南与 CIS Benchmarks 的关系是什么？**
   <details>
   <summary>查看答案</summary>
   README 建议读者先过一遍本指南，再看 CIS Benchmarks。本指南提供更平易的入门路径，而 CIS Benchmarks 是行业公认的最权威、最全面的 Linux 安全基准。
   </details>

4. **指南的"实用优先"特点体现在哪些方面？**
   <details>
   <summary>查看答案</summary>
   每个步骤都提供可直接复制粘贴的代码片段；使用基础命令（echo、cat、sed、awk、grep）；涉及文件修改前都会备份原始文件；不能用脚本自动化的部分提供手动编辑指南。
   </details>

5. **指南目前尚未覆盖的内容包括哪些？（列举3个）**
   <details>
   <summary>查看答案</summary>
   Fail2Ban 自定义 Jails、MAC（强制访问控制）与 Linux 安全模块（SELinux/AppArmor）、磁盘加密、日志远程存储/备份等。
   </details>

## 进阶路径

1. **完成本指南的所有步骤**：按照指南逐一实施安全加固措施，理解每个步骤的原理
2. **研究 CIS Benchmarks**：在完成本指南后，深入研究 CIS Benchmarks 以获取更全面的安全基准
3. **学习 Ansible 自动化**：使用 Ansible Playbook 版本实现安全配置的自动化批量部署
4. **深入特定安全工具**：选择指南中提到的某个工具（如 Fail2Ban、CrowdSec、OSSEC）进行深入学习
5. **实践安全审计**：使用 Lynis 等工具定期审计你的服务器安全状态

## 资料口径说明

本文基于 How-To-Secure-A-Linux-Server 项目的 GitHub README（最后更新：2026-05-14）。由于该指南是持续演进的开源项目，以下内容可能随时间变化：

1. **覆盖内容**：指南的覆盖内容基于 README 中的目录和描述，实际指南可能已扩展
2. **待办事项**：README 列出的待办事项可能已完成或调整，请以最新版本为准
3. **适用场景**：指南的适用场景基于 README 的描述，实际适用性可能因你的环境而异
4. **工具版本**：指南中提到的工具（如 Fail2Ban、CrowdSec）可能有新版本，配置方式可能不同
5. **安全实践**：安全最佳实践持续演进，建议结合最新的安全公告和 CIS Benchmarks 进行配置

---

**延伸阅读**：[GitHub 仓库](https://github.com/imthenachoman/How-To-Secure-A-Linux-Server) · [Ansible 自动化版本](https://github.com/moltenbit/How-To-Secure-A-Linux-Server-With-Ansible) · [CIS Linux Benchmarks](https://www.cisecurity.org/cis-benchmarks/)