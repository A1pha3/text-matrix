# Few-shot 示例与语气框架

> 本文件包含输出质量标准示例、反例和语气/调性框架。由 SKILL.md 按需加载。

---

## 语气/调性框架

根据受众类型选择对应语气（未指定时默认「企业内部」）：

| 受众类型 | 语气特征 | 示例表述 | 禁忌表述 |
|----------|----------|----------|----------|
| **开源社区** | 友好、鼓励、平等 | "恭喜你完成了第一步！" "欢迎提交 PR" | "必须按照规定..." |
| **企业内部** | 简洁、专业、结构化 | "按以下步骤配置..." "注意事项：" | "亲~" "小伙伴们" |
| **初学者教程** | 耐心、细致、引导 | "如果你还不熟悉 X，可以先..." | "这很简单" "显然" |
| **API 参考** | 精确、客观、无废话 | "返回值：string 类型" | "可能会返回..." "大概是..." |
| **技术博客** | 生动、有观点、有故事 | "我们踩过这个坑..." "经过测试发现..." | 过于口语化或夹带私货 |

---

## 正面示例

以下示例展示期望的输出质量标准，AI 必须达到或超越此水平。

### 示例 1：概念定义段落（标准模式 Level 2）

```markdown
## 📝 中间件（Middleware）

### 一句话定义
**中间件** 是请求到达路由处理函数之前（或响应返回之后）自动执行的函数链。

### 类比理解
> 💡 就像机场安检的多个关卡——每个旅客（请求）必须依次通过身份验证、
> 行李扫描、安全检查，全部通过后才能登机（到达目标路由）。
> 任何一个关卡失败，旅客都会被拦截。

### 为什么需要它
没有中间件时，每个路由都要重复编写认证、日志、错误处理等逻辑：

‌```python
# ❌ 无中间件：每个路由重复认证逻辑
@app.get("/users")
def get_users(token: str):
    if not verify_token(token):    # 重复！
        raise HTTPException(401)
    return db.get_users()

# ✅ 有中间件：认证逻辑集中处理
@app.middleware("http")
async def auth_middleware(request, call_next):
    verify_token(request.headers["Authorization"])
    return await call_next(request)
‌```
```

### 示例 2：翻译段落（translate-cn 输出）

```markdown
原文：
> Middleware functions have access to the request object, the response
> object, and the next middleware function. If the current middleware does
> not end the request-response cycle, it must call next().

译文：
> 中间件（Middleware）函数可以访问请求对象、响应对象和下一个中间件函数。
> 如果当前中间件没有结束请求-响应周期，就必须调用 `next()` 将控制权传递下去。
>
> 💡 **译注**：这是 Express.js 中间件的核心行为——每个中间件要么终结请求，
> 要么把请求传给下一个，否则客户端会一直挂起（hang）。
```

---

## 反例：不要这样输出

以下示例展示常见错误模式，AI **必须避免**：

````markdown
## ❌ 反例 1：术语不一致

第一段说"将应用打包到**容器**中"，第三段却写
"run the Container to start service"。
全文混用"代码仓库""存储库""仓库"三种译法，读者无法确定是否指同一概念。

→ **规则**：首次标注后全文统一，参照 terminology.json 单源

## ❌ 反例 2：只有 How，没有 Why

### 跨域配置

在 `app.py` 中添加以下代码：

```python
app.use(cors())
```

即可完成跨域配置。

→ **问题**：读者不知道什么是跨域、为什么需要处理、不处理会怎样。
→ **修复**：在代码前加一段"为什么需要 CORS"的解释。

## ❌ 反例 3：代码块缺少语言标记

```
npm install express
```

→ **问题**：无法语法高亮，读者分不清这是 shell 命令还是代码。
→ **修复**：添加 `bash` / `python` / `json` 等语言标记。

## ❌ 反例 4：中英文无空格 + 中文标点混乱

使用Docker部署,然后运行npm install安装依赖.

→ **问题**：Docker/npm 前后缺空格、逗号和句号用了半角。
→ **修复**：`使用 Docker 部署，然后运行 npm install 安装依赖。`
````

---

## 好文档 vs 差文档对比

````markdown
## ❌ 差文档示例

### 安装
运行 npm install 安装依赖。然后配置config.json文件，把apiKey填进去就行了。
接下来看下面的代码：
// ...省略...
如果报错了就检查一下配置。

## ✅ 好文档示例

### 安装（预计 5 分钟）

**前置条件**：Node.js 16+（运行 `node -v` 验证）

```bash
# 克隆项目并安装依赖
git clone https://github.com/example/project.git
cd project
npm install
```

### 配置

创建 `config.json`，填入你的 API Key：

```json
{
  "apiKey": "your-api-key-here",
  "baseUrl": "https://api.example.com/v1"
}
```

> 💡 **获取 API Key**：访问 [开发者后台](https://example.com/dashboard) → 「设置」→「API 密钥」

### ✅ 验证安装

```bash
npm run check
# 预期输出：✓ Configuration valid. Ready to go!
```

### ❓ 常见问题

**Q: 报错 `ENOENT: config.json not found`**
确认 `config.json` 在项目根目录下，而非 `src/` 目录中。
````
