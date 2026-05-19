---
title: "How-To-Secure-A-Linux-Server：GitHub 2.7万星服务器安全加固指南全文解读"
date: "2026-05-14T15:22:32+08:00"
slug: "how-to-secure-a-linux-server-security-guide"
description: "How-To-Secure-A-Linux-Server 是 GitHub 上最受欢迎的 Linux 服务器安全加固指南之一，涵盖 SSH 公私钥、2FA 认证、UFW 防火墙、Fail2Ban、CrowdSec 等主流工具，提供开箱即用的配置命令，适合运维工程师和站主参考。"
draft: false
categories: ["技术笔记"]
tags: ["Linux", "服务器安全", "SSH", "防火墙", "Fail2Ban", "CrowdSec", "UFW"]
---

# How-To-Secure-A-Linux-Server：GitHub 2.7万星服务器安全加固指南全文解读

## 项目概览

**How-To-Secure-A-Linux-Server**（https://github.com/imthenachoman/How-To-Secure-A-Linux-Server）是 GitHub 上一个持续维护的 Linux 服务器安全加固指南，截至 2026 年 5 月已积累 **27,226 Stars** 和 **1,780 Forks**，是同类安全类仓库中星标数最高的项目之一。

项目核心信息：

| 指标 | 数值 |
|------|------|
| Stars | 27,226 |
| Forks | 1,780 |
| 许可证 | CC-BY-SA-4.0 |
| 主要语言 | 无（纯文档） |
| 最后推送 | 2026-03-05 |
| 贡献者 | 开放协作 |

与很多浅尝辄止的安全教程不同，这个指南的定位是**"覆盖 Linux 服务器安全加固的方方面面"**，从 SSH 加固到防火墙、从入侵检测到日志审计，每个环节都有可直接复制粘贴的配置命令，适合需要将一台 Linux 机器打造成安全在线服务器的人。

---

## 为什么值得读

### 1. 覆盖面极广

大多数服务器安全指南只讲防火墙或只讲 SSH，而这个指南覆盖了完整的攻击面：

- **SSH 加固**：公私钥、AllowGroups、白名单、2FA/MFA
- **账户安全**：sudo/su 限制、安全密码策略、Panic/Fake 密码登录
- **网络防护**：UFW 防火墙、iptables + PSAD、Fail2Ban、CrowdSec
- **审计与检测**：AIDE 文件完整性、ClamAV 杀毒、Rkhunter rootkit 检测、OSSEC 入侵检测、Lynis 安全审计
- **系统加固**：FireJail 沙箱、/proc 隐藏、随机熵池优化、自动安全更新

### 2. 授人以渔，不只是授人以鱼

作者在 README 中明确说，这个指南不只是告诉你"做什么"，还希望你理解"为什么"。每配置一个安全措施，指南都会解释它防的是什么类型的攻击、为什么这个攻击值得关注。

### 3. 可直接复制使用的配置命令

每个章节都提供了可直接粘贴到终端的命令片段（echo、sed、awk、grep），不依赖任何特殊工具，也不需要手工编辑。对于希望快速完成加固的场景尤为实用。

### 4. 支持 Ansible 自动化

第三方贡献者 [moltenbit](https://github.com/moltenbit) 提供了 [Ansible Playbook 版本](https://github.com/moltenbit/How-To-Secure-A-Linux-Server-With-Ansible)，可以一键自动化执行整个指南的加固步骤。

---

## 核心章节解读

### SSH Server — 最关键的入口

SSH 是服务器最常被攻击的入口，大多数自动化攻击脚本第一轮就是爆破 SSH 密码。这个指南的 SSH 部分覆盖了：

**SSH 公私钥配置**
禁用密码登录，强制使用公私钥认证，是 SSH 安全的第一步。指南提供了完整的 sshd_config 加固配置，并教你创建一个专用的 SSH 用户组（AllowGroups），限制只有特定用户组的成员才能登录 SSH。

**移除短 Diffie-Hellman 密钥**
移除 SSH 服务端支持的短 DH 密钥组，防止被用于中间人攻击降级。

**2FA/MFA for SSH**
支持 Google Authenticator 或 FreeOTP 等 TOTP（基于时间的一次性密码）进行二次认证，兼顾安全与便利。

### The Basics — 账户与权限

**限制 sudo/su**
通过 sudoers 文件精细化授权，确保只有必要的人才有 root 权限。

**FireJail 沙箱**
用 FireJail 为不可信的应用程序创建轻量级沙箱，限制其文件系统、网络和进程权限。

**强制安全密码策略**
用 PAM（pam_pwquality）强制要求密码包含大小写、数字、特殊字符，并设置最小长度和历史记录。

### The Network — 防火墙与入侵检测

**UFW（Uncomplicated Firewall）**
Ubuntu/Debian 下最友好的 iptables 前端，一行命令搞定入站/出站策略。

**PSAD（Port Scan Attack Detector）**
监控 iptables 日志，自动识别端口扫描行为并动态封禁恶意 IP。

**Fail2Ban**
通过分析 SSH、Apache、Nginx 等服务的日志，自动封禁多次登录失败的 IP。

**CrowdSec**
 Fail2Ban 的开源继任者，支持协同防御——一个节点发现的攻击行为会同步到全球威胁情报网络。

### The Auditing — 安全审计工具

**Lynis**
由 CISOfy 开发的开源 Linux 安全审计工具，可对系统进行全面的安全检查并输出加固建议，得分可与 CIS Benchmark 对照。

**OSSEC**
主机入侵检测系统（HIDS），监控文件完整性、日志异常和 rootkit 行为。

**logwatch**
系统日志分析器，自动生成每日安全报告，适合不想手动巡检服务器的运维人员。

---

## 快速上手路径

以下是一个基于该指南的最精简加固路径，适合刚入手一台新 Linux 服务器的场景：

```bash
# 1. 创建普通用户并加入 sudo 组
useradd -m -s /bin/bash username
usermod -aG sudo username

# 2. 配置 SSH 公私钥登录（禁止密码登录）
# 3. 在 sshd_config 中限制 AllowGroups
# 4. 配置 UFW 防火墙（仅开放必要端口）
ufw default deny incoming
ufw allow ssh
ufw allow http
ufw allow https
ufw enable

# 5. 安装配置 Fail2Ban
# 6. 安装配置自动安全更新
```

完整的每一步骤请参考指南原文，链接在文章末尾。

---

## 适用场景与边界

**适合：**
- 首次将 Linux 服务器公开上线前的安全加固
- 作为运维参考手册，系统性了解服务器安全攻击面
- 用 Ansible 批量自动化加固多台服务器

**不适合：**
- 企业级专业运维环境（应直接参考 CIS Benchmark）
- 物理安全、容器安全、云安全专项场景（本指南聚焦单机服务器）

---

## 总结与延伸阅读

How-To-Secure-A-Linux-Server 是 Linux 服务器安全加固领域最好的开源指南之一。27,226 颗星标印证了其内容质量和实用价值。

指南最初由一位个人开发者维护，后来通过 GitHub 开放协作不断完善，如今已覆盖服务器安全的方方面面。对于任何需要将一台 Linux 服务器安全上线的人来说，这个项目值得收藏。

**延伸阅读：**
- 原文仓库：https://github.com/imthenachoman/How-To-Secure-A-Linux-Server
- Ansible 版本：https://github.com/moltenbit/How-To-Secure-A-Linux-Server-With-Ansible
- CIS Linux Benchmarks：https://www.cisecurity.org/cis-benchmarks/
- Lynis 官方文档：https://cisofy.com/lynis/