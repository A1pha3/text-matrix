---
title: "Nginx 1.31 安全修复与现代部署：30 岁反向代理的常青之道"
date: "2026-06-07T12:56:00+08:00"
slug: "nginx-1-31-security-and-modern-deployment"
github_repo: "nginx/nginx"
aliases:
  - "/posts/tech/nginx-1-31-security-and-modern-deployment/"
description: "Nginx 1.31.1 mainline 修复了 ngx_http_rewrite 模块的 buffer overflow 漏洞。本文解读这个 23 年历史项目的现代部署方式、与 Caddy/Traefik 的对比，以及在 AI Agent 网关场景的用法。"
draft: false
categories: ["技术笔记"]
tags: ["DevOps"]
---

# Nginx 1.31 安全修复与现代部署：30 岁反向代理的常青之道

2026 年 5 月 22 日，Nginx 发布 1.31.1 mainline 安全公告：ngx_http_rewrite 模块在处理特定 location + if 组合时存在 buffer overflow，攻击者通过精心构造的 URL 可触发。所有使用 rewrite 指令的服务器必须升级。

被 CVE 推上 trending 是 Nginx 的常态——它不像前端工具链那样有范式变化，但只要有安全公告，运维社区就会集体升级。

## 1.31.1 修复了什么

1.31.1 是一次纯安全修复版本：

- **CVE-2026-XXXX**：ngx_http_rewrite 模块的 buffer overflow。如果你的配置涉及 `if ($http_user_agent ~ ...) { rewrite ... }` 这类模式，属于高风险，立即升级。
- 修复了 stream 模块的少量内存泄漏。
- 升级 PCRE2 到 10.43，带来更好的 JIT 性能。

只用 `proxy_pass` 不带复杂 rewrite 的，风险低；用 `try_files` + `rewrite` 做 SPA 部署的，中风险；写 `if` 条件里套 rewrite 的，高风险，没有理由不升。

## 为什么 2026 年还在用 Nginx

在 K8s 主导的时代，Nginx 的位置看似被 Envoy、Istio、Traefik 抢了。但生产数据说明它依然不可替代：

| 场景 | 主流选择 | 原因 |
|------|----------|------|
| 传统 Web 服务器 | Nginx | 稳定、文档多、CDN 默认支持 |
| Kubernetes Ingress | Nginx Ingress Controller、Traefik、Envoy Gateway | K8s 生态强制 |
| API Gateway | Kong（基于 Nginx）、Tyk、Apigee | 需要商业特性 |
| Service Mesh 数据面 | Envoy | 必须支持 xDS |
| 边缘 / CDN | Nginx（部分 Cloudflare 节点） | 历史积累 |

Nginx 在 AI 时代的几个用途：

- **AI Agent 网关**：很多团队把 LLM API 代理、token 限速、计费用 Nginx + Lua（OpenResty）。比起 Kong 这种商业网关，Nginx + OpenResty 更轻、更可控，没有数据库依赖，配置可以纯文件进 git。
- **内网 LLM 推理服务入口**：vLLM、Ollama 的对外暴露层常用 Nginx 做 TLS 终止、限流、鉴权。
- **CDN 边缘节点**：Cloudflare、Fastly 部分节点仍基于 Nginx 魔改。

## 与 Caddy / Traefik 的对比

| 维度 | Nginx | Caddy | Traefik |
|------|-------|-------|---------|
| 配置方式 | 文本 + reload | Caddyfile / API | TOML / label / API |
| 自动 HTTPS | 需 certbot | 内置（Let's Encrypt） | 内置（ACME） |
| 配置热加载 | reload（短暂中断） | reload（无中断） | 无中断动态 |
| 性能 | 最高 | 中等 | 中等 |
| 学习曲线 | 中 | 低 | 低 |
| 生态 / 文档 | 极多 | 较少 | 较多 |

选型建议：个人或小团队直接上 Caddy，零运维；大流量生产环境 Nginx 仍然是性能天花板；K8s 微服务用 Traefik 或 Envoy Gateway；需要商业 API 网关功能就上 Kong。

## 上手与升级

升级到 1.31.1：

```bash
# Linux 包管理器
sudo apt update && sudo apt install nginx   # 1.31.1+
# 验证配置
sudo nginx -t
# 优雅 reload（不中断连接）
sudo nginx -s reload
```

容器场景：

```dockerfile
FROM nginx:1.31.1-alpine
COPY nginx.conf /etc/nginx/nginx.conf
COPY dist/ /usr/share/nginx/html/
```

K8s 场景（Ingress-NGINX 迁移到 Gateway API）：

```bash
kubectl set image deployment/ingress-nginx-controller \
  controller=registry.k8s.io/nginx-ingress-controller:v1.13.0
```

## 实践建议

1. **配置版本管理**：`nginx.conf` 永远进 git，禁止在生产裸跑 `nginx -s reload`。
2. **日志结构化**：access_log 用 json 格式，方便接 Loki/ELK。
3. **限流必开**：`limit_req_zone` + `limit_conn_zone`，防止被 LLM 客户端刷爆。
4. **TLS 1.3 默认**：1.25+ 已经默认，老版本需要 `ssl_protocols TLSv1.2 TLSv1.3`。
5. **动态 upstream**：用 `resolver` + `set $backend` 做服务发现，比硬编码 upstream 灵活。

## 参考资源

- 仓库：[github.com/nginx/nginx](https://github.com/nginx/nginx)
- 安全公告：[nginx.org/en/security_advisories.html](https://nginx.org/en/security_advisories.html)
- OpenResty（Lua 增强）：[openresty.org](https://openresty.org/)
- Ingress-NGINX 迁移指南：[kubernetes.github.io/ingress-nginx](https://kubernetes.github.io/ingress-nginx/)