# Anthropic官方知识工作者插件库：knowledge-work-plugins

> 有时，技术创新的火花不在实验室，而在真实工作流里。

## 📌 一句话概括

Anthropic 官方出品，面向知识工作者的 Claude 插件集合，覆盖研究分析、内容创作、数据处理等高频场景，开源免费，直接可用于 Claude Cowork。

## 🌟 核心亮点

- **官方背书**：Anthropic 亲儿子，不是第三方套壳，质量有保证
- **场景丰富**：涵盖网络搜索、文件处理、代码执行、思维导图等知识工作核心场景
- **Cowork 原生**：专为 Claude Cowork（桌面协作版）设计，即装即用
- **持续更新**：Anthropic 工程师维护，版本迭代快

## 🔬 功能实测

### 已收录插件一览

| 插件名 | 能力 | 适用场景 |
|--------|------|----------|
| Web Search | 实时联网搜索 | 竞品调研、新闻追踪 |
| File Tools | 本地文件读写执行 | 文档处理、数据分析 |
| Code Executor | Python/JS沙箱执行 | 原型验证、可视化 |
| Notion Sync | Notion 双向同步 | 知识库管理 |
| Miro Brainstorm | Miro 白板协作 | 头脑风暴、流程梳理 |

### 使用方法

```bash
# 安装全部插件（需 Claude CLI）
claude plugin install anthropics/knowledge-work-plugins

# 或单个安装
claude plugin install anthropics/knowledge-work-plugins --plugin web-search
```

安装后在 Claude Cowork 侧边栏「插件」选项卡中启用即可。

## 💡 对比同类产品

| 特性 | knowledge-work-plugins | 第三方插件合集 |
|------|----------------------|----------------|
| 官方支持 | ✅ | ❌ |
| Cowork 原生集成 | ✅ | ⚠️ 部分支持 |
| 更新频率 | 高（官方维护） | 不稳定 |
| 插件数量 | 8+ | 不等 |

## ⚠️ 注意事项

1. **需要 Claude Pro/Cowork 订阅**才能使用插件系统
2. 代码执行插件有 **5MB 输出限制**，大结果需导出文件
3. 部分插件（如 Miro）依赖 **第三方账号授权**

## 🔗 相关链接

- GitHub: https://github.com/anthropics/knowledge-work-plugins
- Anthropic 官网: https://claude.ai/cowork

---

*Tags: #Anthropic #Claude #插件 #知识工作 #Cowork*