# 技术术语中英文对照表

> 本文件由 `scripts/gen_terminology_md.py` 从 `terminology.json` 自动生成。
> **请勿手工编辑**，修改请编辑 `terminology.json` 后重新生成。

## 通用术语

| 英文 | 中文 | 说明 |
|-----|------|------|
| API | API / 应用程序接口 | Application Programming Interface |
| SDK | SDK / 软件开发包 | Software Development Kit |
| CLI | CLI / 命令行工具 | Command Line Interface |
| GUI | GUI / 图形用户界面 | Graphical User Interface |
| IDE | IDE / 集成开发环境 | Integrated Development Environment |
| ORM | ORM / 对象关系映射 | Object-Relational Mapping |
| MVC | MVC / 模型-视图-控制器 | Model-View-Controller |
| REST | REST / 表述性状态转移 | Representational State Transfer |
| CRUD | CRUD / 增删改查 | Create, Read, Update, Delete |
| CI/CD | CI/CD / 持续集成/持续部署 | Continuous Integration/Deployment |

## Web 开发

| 英文 | 中文 | 说明 |
|-----|------|------|
| Frontend | 前端 |  |
| Backend | 后端 |  |
| Fullstack | 全栈 |  |
| Middleware | 中间件 |  |
| Authentication | 身份认证 |  |
| Authorization | 授权 |  |
| CORS | CORS / 跨域资源共享 | Cross-Origin Resource Sharing |
| SEO | SEO / 搜索引擎优化 | Search Engine Optimization |
| SSR | SSR / 服务器端渲染 | Server-Side Rendering |
| CSR | CSR / 客户端渲染 | Client-Side Rendering |
| WebSocket | WebSocket / WebSocket | 全双工通信协议 |
| WebAssembly | WebAssembly / WebAssembly | 又作「WASM」 |
| PWA | PWA / 渐进式 Web 应用 | Progressive Web App |
| SPA | SPA / 单页应用 | Single Page Application |
| ISR | ISR / 增量静态再生 | Incremental Static Regeneration |
| Edge Computing | 边缘计算 |  |
| Webhook | Webhook / Webhook | HTTP 回调通知机制 |
| CDN | CDN / 内容分发网络 | Content Delivery Network |

## 数据和存储

| 英文 | 中文 | 说明 |
|-----|------|------|
| Database | 数据库 |  |
| Cache | 缓存 |  |
| Query | 查询 |  |
| Index | 索引 |  |
| Schema | Schema / 模式 |  |
| Migration | 迁移 |  |
| Transaction | 事务 |  |
| ACID | ACID / 原子性一致性隔离性持久性 | Atomicity, Consistency, Isolation, Durability |
| Partition | 分区 |  |
| Sharding | 分片 |  |

## 代码和工程

| 英文 | 中文 | 说明 |
|-----|------|------|
| Repository | 仓库 / 存储库 |  |
| Branch | 分支 |  |
| Merge | 合并 |  |
| Rebase | 变基 |  |
| Commit | 提交 |  |
| Push | 推送 |  |
| Pull | 拉取 |  |
| Clone | 克隆 |  |
| Fork | 派生 |  |
| Pull Request | Pull Request / 拉取请求 | 又作「PR」 |
| Code Review | 代码审查 |  |
| Refactoring | 重构 |  |
| Tech Debt | 技术债务 |  |
| Semantic Versioning | 语义化版本 / SemVer |  |
| Monorepo | Monorepo / 单仓库 | 所有项目在同一仓库管理 |

## 性能和架构

| 英文 | 中文 | 说明 |
|-----|------|------|
| Latency | 延迟 |  |
| Throughput | 吞吐量 |  |
| Scalability | 可扩展性 |  |
| Availability | 可用性 |  |
| Reliability | 可靠性 |  |
| Concurrency | 并发性 |  |
| Parallelism | 并行性 |  |
| Load Balancing | 负载均衡 |  |
| Microservices | 微服务 |  |
| Monolithic | 单体 |  |
| Circuit Breaker | 熔断器 | 服务降级保护模式 |
| Rate Limiting | 限流 |  |
| Failover | 故障转移 |  |
| Disaster Recovery | 灾难恢复 / 容灾 |  |
| Blue-green Deployment | 蓝绿部署 |  |
| Canary Release | 灰度发布 / 金丝雀发布 |  |
| Rolling Update | 滚动更新 |  |
| Idempotent | 幂等 |  |

## AI 和机器学习

| 英文 | 中文 | 说明 |
|-----|------|------|
| LLM | LLM / 大语言模型 | Large Language Model |
| Agent | 智能体 / 代理 |  |
| Prompt | 提示词 |  |
| Token | Token / 词元 |  |
| Fine-tuning | 微调 |  |
| Embedding | 嵌入向量 |  |
| RAG | RAG / 检索增强生成 | Retrieval-Augmented Generation |
| Context Window | 上下文窗口 |  |
| Temperature | 温度 |  |
| Hallucination | 幻觉 |  |
| RLHF | RLHF / 基于人类反馈的强化学习 | Reinforcement Learning from Human Feedback |
| CoT | CoT / 思维链 | Chain of Thought |
| MoE | MoE / 混合专家模型 | Mixture of Experts |
| Inference | 推理 |  |
| Training | 训练 |  |
| Pre-training | 预训练 |  |
| Alignment | 对齐 |  |
| Tokenizer | 分词器 |  |
| Attention | 注意力机制 |  |
| Transformer | Transformer / Transformer 架构 |  |
| Multimodal | 多模态 |  |
| LoRA | LoRA / 低秩适配 | Low-Rank Adaptation |
| Quantization | 量化 |  |
| Distillation | 蒸馏 | 知识蒸馏 |

## DevOps 和云原生

| 英文 | 中文 | 说明 |
|-----|------|------|
| Container | 容器 |  |
| Image | 镜像 |  |
| Volume | 数据卷 |  |
| Pod | Pod / Pod | Kubernetes 最小部署单元 |
| Node | 节点 |  |
| Cluster | 集群 |  |
| Ingress | 入口 |  |
| Service | 服务 |  |
| Deployment | 部署 |  |
| StatefulSet | StatefulSet / 有状态部署 |  |
| Namespace | 命名空间 |  |
| ConfigMap | ConfigMap / 配置映射 |  |
| Helm | Helm / Helm | Kubernetes 包管理工具 |
| DaemonSet | DaemonSet / 守护进程集 |  |
| CronJob | CronJob / 定时任务 |  |
| Service Mesh | 服务网格 |  |
| Sidecar | 边车 | 代理容器模式 |
| GitOps | GitOps / GitOps | 以 Git 为核心的运维模式 |
| Infrastructure as Code | 基础设施即代码 / IaC |  |

## 安全

| 英文 | 中文 | 说明 |
|-----|------|------|
| Encryption | 加密 |  |
| Decryption | 解密 |  |
| Hash | 哈希 / 散列 |  |
| Salt | 盐值 |  |
| Token | 令牌 |  |
| Certificate | 证书 |  |
| Vulnerability | 漏洞 |  |
| XSS | XSS / 跨站脚本攻击 | Cross-Site Scripting |
| CSRF | CSRF / 跨站请求伪造 | Cross-Site Request Forgery |
| SQL Injection | SQL 注入 |  |
| Firewall | 防火墙 |  |
| Sandbox | 沙箱 |  |
| Zero Trust | 零信任 | 零信任安全架构 |
| mTLS | mTLS / 双向 TLS 认证 | Mutual TLS |
| WAF | WAF / Web 应用防火墙 | Web Application Firewall |
| DDoS | DDoS / 分布式拒绝服务攻击 | Distributed Denial of Service |
| Penetration Testing | 渗透测试 |  |
| RBAC | RBAC / 基于角色的访问控制 | Role-Based Access Control |
| SSO | SSO / 单点登录 | Single Sign-On |
| MFA | MFA / 多因素认证 | Multi-Factor Authentication，又作「2FA」 |

## 测试

| 英文 | 中文 | 说明 |
|-----|------|------|
| Unit Test | 单元测试 |  |
| Integration Test | 集成测试 |  |
| End-to-End Test | 端到端测试 / E2E 测试 |  |
| Mock | 模拟 |  |
| Stub | 桩 |  |
| Fixture | 测试夹具 |  |
| Coverage | 覆盖率 |  |
| Assertion | 断言 |  |
| Regression | 回归 |  |
| Snapshot Test | 快照测试 |  |
| TDD | TDD / 测试驱动开发 | Test-Driven Development |
| BDD | BDD / 行为驱动开发 | Behavior-Driven Development |

## 前端框架和工具

| 英文 | 中文 | 说明 |
|-----|------|------|
| Component | 组件 |  |
| Props | Props / 属性 | React/Vue 组件属性 |
| State | 状态 |  |
| Hook | 钩子 |  |
| Lifecycle | 生命周期 |  |
| Virtual DOM | 虚拟 DOM |  |
| Hydration | 水合 | SSR 后客户端激活 |
| Bundler | 打包工具 |  |
| Transpiler | 转译器 |  |
| Tree Shaking | 摇树优化 | 移除未使用代码 |
| Hot Module Replacement | 热模块替换 / HMR |  |
| Responsive Design | 响应式设计 |  |

## 文档和写作

| 英文 | 中文 | 说明 |
|-----|------|------|
| Code Fence | 代码围栏 | Markdown 中用 ``` 或 ~~~ 包裹代码的语法 |
| Linting | 代码检查 / 静态分析 |  |
| Snippet | 代码片段 |  |
| Boilerplate | 模板代码 | 可复用的标准化代码骨架 |
| Docstring | 文档字符串 | 函数/类内嵌的文档注释 |
| Markdown | Markdown / Markdown | 轻量级标记语言 |
| Style Guide | 风格指南 |  |
| Glossary | 术语表 |  |
| Annotation | 注解 / 标注 |  |

## 云计算

| 英文 | 中文 | 说明 |
|-----|------|------|
| IaaS | IaaS / 基础设施即服务 | Infrastructure as a Service |
| PaaS | PaaS / 平台即服务 | Platform as a Service |
| SaaS | SaaS / 软件即服务 | Software as a Service |
| FaaS | FaaS / 函数即服务 | Function as a Service |
| Serverless | 无服务器 |  |
| Region | 区域 | 云服务商的地理区域 |
| Availability Zone | 可用区 / AZ |  |
| VPC | VPC / 虚拟私有云 | Virtual Private Cloud |
| Auto Scaling | 自动伸缩 |  |
| Multi-tenant | 多租户 |  |
| Object Storage | 对象存储 |  |
| Elasticity | 弹性 |  |

## 设计模式和架构

| 英文 | 中文 | 说明 |
|-----|------|------|
| Singleton | 单例模式 |  |
| Factory | 工厂模式 |  |
| Observer | 观察者模式 |  |
| Strategy | 策略模式 |  |
| Adapter | 适配器模式 |  |
| Proxy Pattern | 代理模式 |  |
| Facade | 外观模式 |  |
| Builder | 建造者模式 |  |
| Dependency Injection | 依赖注入 / DI |  |
| Inversion of Control | 控制反转 / IoC |  |
| Event-driven | 事件驱动 |  |
| Pub/Sub | 发布/订阅 | 发布-订阅模式 |
| CQRS | CQRS / 命令查询职责分离 | Command Query Responsibility Segregation |
| Event Sourcing | 事件溯源 |  |
| Domain-driven Design | 领域驱动设计 / DDD |  |

## 可观测性

| 英文 | 中文 | 说明 |
|-----|------|------|
| Logging | 日志记录 |  |
| Metrics | 指标 |  |
| Tracing | 链路追踪 |  |
| Alert | 告警 |  |
| Dashboard | 仪表盘 |  |
| SLA | SLA / 服务等级协议 | Service Level Agreement |
| SLO | SLO / 服务等级目标 | Service Level Objective |
| SLI | SLI / 服务等级指标 | Service Level Indicator |
| APM | APM / 应用性能管理 | Application Performance Management |
| Uptime | 正常运行时间 |  |
| MTTR | MTTR / 平均恢复时间 | Mean Time to Recovery |
| MTTF | MTTF / 平均无故障时间 | Mean Time to Failure |

## 网络

| 英文 | 中文 | 说明 |
|-----|------|------|
| Gateway | 网关 |  |
| Proxy | 代理 |  |
| Reverse Proxy | 反向代理 |  |
| Subnet | 子网 |  |
| VPN | VPN / 虚拟专用网络 | Virtual Private Network |
| NAT | NAT / 网络地址转换 | Network Address Translation |
| Bandwidth | 带宽 |  |
| Socket | 套接字 |  |
| Router | 路由器 |  |
| Packet | 数据包 |  |

## 不翻译的术语

以下术语通常保持英文，不翻译：

**技术名称**：
- Git, Docker, Kubernetes, Python, JavaScript, TypeScript, Go, Rust, React, Vue, Angular, Next.js, Nuxt.js, Svelte, Node.js, Deno, Bun, Django, Flask, FastAPI, Spring, Redis, PostgreSQL, MongoDB, MySQL, SQLite, Nginx, Linux, macOS, Windows, Webpack, Vite, esbuild, Playwright, Cypress, Jest, Vitest, pytest, README, Changelog, Frontmatter, Terraform, Ansible, Prometheus, Grafana, Elasticsearch, Kafka, RabbitMQ, Istio, Envoy, ArgoCD, GitHub, GitLab, Bitbucket, Vercel, Netlify, Cloudflare, Tailwind CSS, Storybook, Figma, Swagger, OpenAPI

**协议和标准**：
- HTTP, HTTPS, TCP, UDP, JSON, XML, YAML, TOML, CSV, SSL, TLS, OAuth, JWT, GraphQL, gRPC, WebSocket, SSH, FTP, SMTP, DNS, QUIC, HTTP/2, HTTP/3, AMQP, MQTT, Protobuf

**代码概念**：
- class, function, method, variable, constant, parameter, loop, recursion, closure, async, await, promise, callback, interface, abstract, enum, struct, trait, generic, decorator, middleware, iterator, generator

**单位和度量**：
- KB, MB, GB, TB, PB, ms, s, min, Hz, GHz, QPS, TPS, RPS, fps, px, rem, em, vw, vh
