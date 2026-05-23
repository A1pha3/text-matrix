# Agent Governance Toolkit: 为AI Agent打造的安全护盾，覆盖OWASP Agentic Top 10

**🏷️ 分类：** AI安全 · Agent治理  
**⭐ Stars：** 1,840  
**🔗 地址：** https://github.com/microsoft/agent-governance-toolkit  
**🌐 官网：** https://github.com/microsoft/agent-governance-toolkit

**一句话总结：** 微软出品的AI Agent治理工具包，提供策略执行、零信任身份验证、隔离执行环境、可靠性工程四大护盾，**系统性覆盖OWASP Agentic Top 10全部10类安全风险**。

---

## 🎯 这个工具解决什么问题？

AI Agent带来了全新的安全威胁面：工具滥用、数据泄露、提示词注入、越权操作……OWASP为此专门发布了"Agentic Top 10"安全风险清单。Agent Governance Toolkit 是业界首个**系统性对应OWASP Agentic Top 10全部风险**的治理框架，让企业安心部署Agent。

---

## ⚡ 核心能力

### 1. 策略执行引擎
基于OPA/Rego编写Agent行为策略，发现违规立即拦截

### 2. 零信任身份验证
每次工具调用都验证身份，支持OAuth 2.0、MCP身份协议

### 3. 隔离执行沙箱
危险的代码执行在独立沙箱中运行，不影响主系统

### 4. 可靠性工程
熔断、重试、超时、限流，防止Agent行为失控

### 5. 可观测性
完整的操作审计日志，满足合规要求

---

## 📦 安装

```bash
pip install agent-governance-toolkit
# 或
git clone https://github.com/microsoft/agent-governance-toolkit
cd agent-governance-toolkit && pip install -e .
```

---

## 🚀 快速上手

### 集成到Agent
```python
from agent_governance import GovernanceShield

shield = GovernanceShield(
    policies="policies/",
    sandbox=True,
    zero_trust=True
)

agent = MyAgent(governance_shield=shield)
agent.run(user_request)
```

### 定义策略
```rego
# policies/tool_access.rego
package agent_governance

default allow_tool_call = false

allow_tool_call {
    input.tool == "execute_code"
    input.user_role == "developer"
}
```

---

## 🛡️ 覆盖的OWASP Agentic Top 10

| 风险 | 防护方式 |
|------|----------|
| 1. 提示词注入 | 输入验证 + 隔离解析 |
| 2. 工具滥用 | 白名单 + 策略引擎 |
| 3. 数据泄露 | 输出过滤 + DLP集成 |
| 4. 权限泛滥 | 最小权限 + 零信任 |
| 5. 依赖供应链 | SBOM扫描 + 签名验证 |
| 6. 沙盒逃逸 | 强隔离沙箱 |
| 7. 过度信任 | 审计日志 + 人工审核点 |
| 8. 模型投毒 | 输入验证 + 对比检测 |
| 9. 状态混淆 | 会话隔离 + 上下文签名 |
| 10. 链路追踪缺失 | 完整链路可见性 |

---

## 💡 适用场景

| 场景 | 说明 |
|------|------|
| 企业Agent部署 | 满足安全合规要求 |
| 高风险工具调用 | 代码执行、数据库操作等 |
| 多Agent协作 | 跨Agent权限隔离 |
| 合规审计 | SOC2 / ISO 27001合规 |

---

## ⚠️ 注意事项

- 策略编写需要一定的安全基础
- 沙箱模式会引入一定性能开销
- 部分功能需要企业Azure订阅

---

**相关工具：** [Superpowers](superpowers-agentic-development-methodology) · [Claude Plugins Official](chrome-devtools-mcp-ai-coding-agents-chrome-devtools) · [aidlc-workflows](aidlc-workflows-ai-driven-lifecycle-automation)