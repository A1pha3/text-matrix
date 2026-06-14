---
title: "Linux服务器安全加固实战指南：从SSH到防火墙的完整清单"
date: "2026-05-14T10:51:00+08:00"
slug: "linux-server-security-hardening-guide"
description: "How-To-Secure-A-Linux-Server是一份持续更新的开源安全加固指南，覆盖SSH双因素认证、sudo权限管理、UFW/iptables防火墙、Fail2Ban、CrowdSec入侵检测、Lynis安全审计、ClamAV病毒扫描等完整链路。适合运维工程师和DevSecOps实践者参考。"
draft: false
categories: ["技术笔记"]
tags: ["Linux", "安全加固", "SSH", "防火墙", "DevOps"]
---

# Linux 服务器安全加固实战指南：从 SSH 到防火墙的完整清单

**How-To-Secure-A-Linux-Server**（GitHub: imthenachoman/How-To-Secure-A-Linux-Server）是一份由社区共建的 Linux 服务器安全加固指南，涵盖从系统安装到日常运维的全链路安全措施。该项目在 GitHub 拥有 27,000+ Stars，内容持续更新，涵盖 SSH 加固、防火墙配置、入侵检测、安全审计等多个维度。

## 安全加固全景图

```
Linux 服务器安全加固
├── SSH 防护：密钥认证 + 2FA
├── 身份管理：sudo / PAM
├── 防火墙：UFW / iptables
├── 入侵检测：Fail2Ban / CrowdSec / PSAD
├── 安全审计：Lynis / OSSEC / Logwatch
├── 病毒扫描：ClamAV / Rkhunter
└── 网络安全：/proc 隔离 / TPROXY / NTP
```

## 第一层：SSH 加固

### 公私钥认证（禁用密码登录）

```bash
# 本地生成密钥对
ssh-keygen -t ed25519 -C "my-server-key"

# 上传公钥到服务器
ssh-copy-id -i ~/.ssh/id_ed25519.pub user@your-server-ip

# 服务端禁用密码登录
sudo vim /etc/ssh/sshd_config
```

```bash
# /etc/ssh/sshd_config 关键配置
PasswordAuthentication no
PubkeyAuthentication yes
PermitRootLogin no
MaxAuthTries 3
ClientAliveInterval 300
TCPKeepAlive yes
```

```bash
sudo systemctl restart sshd
```

### 限制 SSH 访问的 IP 段

```bash
# 仅允许特定 IP 访问 SSH（建议配合 VPN 或堡垒机）
AllowUsers user@10.0.0.0/8
AllowUsers user@192.168.1.0/24
```

### 2FA/MFA 认证

```bash
# 安装 Google Authenticator PAM 模块（Ubuntu/Debian）
sudo apt install libpam-google-authenticator

# 用户端配置（每个用户运行一次）
google-authenticator

# 服务端 /etc/pam.d/sshd 添加
auth required pam_google_authenticator.so

# /etc/ssh/sshd_config 启用
AuthenticationMethods publickey,keyboard-interactive
```

## 第二层：身份与权限管理

### 限制 sudo 权限

```bash
# 查看当前 sudo 组成员
getent group sudo

# 限制只有特定用户组可以使用 sudo
echo "%sudo ALL=(ALL) ALL" | sudo tee /etc/sudoers.d/sudo-group

# 为特定用户配置无密码 sudo（谨慎使用）
username ALL=(ALL) NOPASSWD: /usr/bin/apt, /usr/bin/systemctl
```

### 强密码策略（PAM）

```bash
# Ubuntu/Debian 安装 libpam-pwquality
sudo apt install libpam-pwquality

# /etc/security/pwquality.conf 配置
minlen = 14
dcredit = -1  # 至少一位数字
ucredit = -1  # 至少一位大写
lcredit = -1  # 至少一位小写
maxclassrepeat = 4  # 同一字符最多连续出现4次
```

### 自动化安全更新

```bash
# Ubuntu/Debian：配置无人值守升级
sudo apt install unattended-upgrades
sudo dpkg-reconfigure -plow unattended-upgrades
```

配置 `/etc/apt/apt.conf.d/50unattended-upgrades`：

```bash
Unattended-Upgrade::Mail "root@your-domain.com";
Unattended-Upgrade::AutomaticReboot "true";
Unattended-Upgrade::AutomaticRebootTime "03:00";
```

## 第三层：防火墙

### UFW（Uncomplicated Firewall）

```bash
# 安装并启用
sudo apt install ufw
sudo ufw enable

# 默认策略：拒绝入站，允许出站
sudo ufw default deny incoming
sudo ufw default allow outgoing

# 开放必要端口
sudo ufw allow 22/tcp comment 'SSH'
sudo ufw allow 80/tcp comment 'HTTP'
sudo ufw allow 443/tcp comment 'HTTPS'

# 限制 SSH 来源 IP（重要！）
sudo ufw allow from 10.0.0.0/8 to any port 22

# 查看规则
sudo ufw status verbose
```

### iptables + PSAD（入侵检测）

```bash
# 安装 PSAD
sudo apt install psad

# /etc/psad/psad.conf 配置
EMAIL_ADDRESSES     your-email@example.com;
HOSTNAME            your-server;
IPT_SYSLOG_FILE     /var/log/syslog;
```

PSAD 会分析 iptables 日志，自动 ban 可疑 IP。

### Fail2Ban（应用层入侵检测）

```bash
sudo apt install fail2ban
sudo systemctl enable fail2ban

# /etc/fail2ban/jail.local
[DEFAULT]
bantime  = 3600
findtime  = 600
maxretry = 5

[sshd]
enabled  = true
port     = 22
filter   = sshd
logpath  = /var/log/auth.log
maxretry = 3

[nginx-http-auth]
enabled  = true
port     = 80,443
```

### CrowdSec（社区驱动的入侵检测）

```bash
# 安装
curl -s https://packagecloud.io/install/repositories/crowdsec/crowdsec/script.deb.sh | sudo bash
sudo apt install crowdsec crowdsec-firewall-bouncer-iptables

# 注册场景（自动下载防御规则）
sudo cscli scenarios list
sudo cscli scenarios enable crowdsecurity/http-crawlers
sudo cscli collections install crowdsecurity/linux
```

## 第四层：安全审计

### Lynis（系统安全审计）

```bash
sudo apt install lynis
sudo lynis audit system
```

Lynis 会输出一份完整的安全审计报告，包含建议修复项：

```
[+] System Tools
-----------
  - Scanning for tools...
  - [WARNING] Missing tool: auditd (audit subsystem)
  - [WARNING] Missing tool: chkrootkit
  - [INFO] Present tool: iptables
```

### OSSEC（主机入侵检测）

```bash
# OSSEC 架构
┌──────────────┐    ┌──────────────┐
│  OSSEC Agent  │───▶│ OSSEC Server  │
│  (被监控主机)  │    │  (分析告警)   │
└──────────────┘    └──────────────┘
```

```bash
# 服务端安装
sudo apt install ossec-hids

# 监控配置（/var/ossec/etc/ossec.conf）
<localfile>
  <log_format>syslog</log_format>
  <location>/var/log/auth.log</location>
</localfile>
```

### Logwatch（日志分析报告）

```bash
sudo apt install logwatch

# 生成每日报告邮件
sudo logwatch --output mail --service all --range 'today'
```

## 第五层：特洛伊与病毒检测

### ClamAV 扫描

```bash
sudo apt install clamav clamav-daemon
sudo systemctl stop clamav-freshclam
sudo freshclam  # 更新病毒库（首次较慢）

# 扫描指定目录
sudo clamscan -r /home -i --remove
# -r: 递归  -i: 只显示感染文件  --remove: 删除感染文件
```

### Rkhunter（Rootkit 检测）

```bash
sudo apt install rkhunter
sudo rkhunter --update
sudo rkhunter --check
```

## /proc 隔离（防止信息泄露）

```bash
# 隐藏 PID（防止窥探进程）
sudo sysctl kernel.pid_max=99999

# 禁止查看其他用户进程
sudo sysctl kernel.yama.ptrace_scope=2

# /etc/sysctl.conf 永久配置
kernel.yama.ptrace_scope = 2
kernel.pid_max = 99999
fs.suid_dumpable = 0
```

## 快速部署清单

```bash
# 一键安全加固（Ubuntu 22.04）
sudo apt update && sudo apt install -y \
  unattended-upgrades ufw fail2ban lynis clamav rkhunter logwatch

# 启用防火墙
sudo ufw default deny incoming && \
sudo ufw default allow outgoing && \
sudo ufw allow OpenSSH && \
sudo ufw enable

# 限制 SSH 来源
sudo ufw allow from YOUR_IP/32 to any port 22

# 启动 fail2ban
sudo systemctl enable fail2ban && sudo systemctl start fail2ban
```

## 总结

Linux 服务器安全是一个**分层防御**的过程，从网络层（防火墙）、传输层（SSH 加密）、应用层（入侵检测）到系统层（PAM、特权管理），每一层都有对应的加固手段。本指南覆盖了生产环境中最实用的链路，适合作为运维工程师的**安全加固 Checklist**。

Ansible 自动化版本：[moltenbit/How-To-Secure-A-Linux-Server-With-Ansible](https://github.com/moltenbit/How-To-Secure-A-Linux-Server-With-Ansible)