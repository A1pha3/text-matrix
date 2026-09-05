---
title: "Spring AI 架构深读：从 ChatClient 流式 API 到 Advisors 拦截器，Java 圈为什么需要这套 AI 抽象"
date: "2026-09-05T16:00:00+08:00"
lastmod: "2026-09-05T16:00:00+08:00"
draft: false
categories: ["技术笔记"]
tags: ["spring-ai", "java", "spring-boot", "chatclient", "advisors", "mcp", "rag", "etl", "项目解读"]
description: "Spring Projects 9.4k stars Apache-2.0 项目 Spring AI 2.0.2-SNAPSHOT 主线深读。它不是又一个 LangChain 的 Java 复刻，是 Spring 生态把 portable + modular design 原则搬进 AI 域的工程实现。本文拆 5 个工程决策：ChatClient 流式 API（WebClient/RestClient 同款）、Advisors 拦截器链（Servlet Filter 思路）、Function/Supplier/Consumer 建模 ETL、VectorStore SQL-like 元数据过滤、MCP Java Annotations + Boot Starter 整合。每个决策挂具体代码入口或文档路径。"
slug: "spring-ai-application-framework-design"
band: "review"
gates: ["事实性", "去AI味", "观点依据"]
hiddenFromHomePage: false
github_repo: "spring-projects/spring-ai"
source_key: "gh:spring-projects/spring-ai"
---

> **关于这篇文章。** Spring AI 是 [spring-projects](https://github.com/spring-projects) 下的官方 AI 集成项目（9.4k stars / Apache-2.0），2023-06 创立。最新 main 是 Spring AI 2.0.2-SNAPSHOT（配 Spring Boot 4.x），1.1.x 分支配 Spring Boot 3.5.x。它的核心目标不是"做 AI"，而是**把 Spring 生态的 portable + modular design 原则搬进 AI 域**——让 Java 开发者能用熟悉的 Spring 抽象调用 LLM、构建 RAG、整合 vector database、连接 MCP 服务器。
>
> 仓库：[github.com/spring-projects/spring-ai](https://github.com/spring-projects/spring-ai) · 架构文档：[docs.spring.io/spring-ai/reference/](https://docs.spring.io/spring-ai/reference/)

## 为什么挑这 5 个决策

Spring AI 一眼看去像"LangChain 的 Java 复刻"——多 provider 适配、vector store、RAG、tool calling、agent loop，似乎每个 LangChain / LlamaIndex 的特性在 Spring AI 都能找到对应物。但读 [concepts.adoc](https://github.com/spring-projects/spring-ai/blob/main/spring-ai-docs/src/main/antora/modules/ROOT/pages/concepts.adoc)、[chatclient.adoc](https://github.com/spring-projects/spring-ai/blob/main/spring-ai-docs/src/main/antora/modules/ROOT/pages/api/chatclient.adoc)、[advisors.adoc](https://github.com/spring-projects/spring-ai/blob/main/spring-ai-docs/src/main/antora/modules/ROOT/pages/api/advisors.adoc) 三份核心文档会发现，它的差异化在 5 个具体的工程决策：

1. **ChatClient Fluent API** —— 把 LLM 调用流式化，沿用 WebClient / RestClient 的 ergonomics 设计
2. **Advisors 拦截器链** —— 把 Servlet Filter 的设计思路搬到 AI 调用，Ordered 控制顺序 + advisor context 共享状态
3. **ETL Pipeline 用 Java 函数式接口建模** —— `Supplier` / `Function` / `Consumer` 自然映射 Extract / Transform / Load 三阶段
4. **VectorStore SQL-like 元数据过滤** —— 21+ vector store 统一 `FilterExpression`，屏蔽 vendor 差异
5. **MCP Java Annotations + Boot Starter** —— 把 Anthropic MCP（Model Context Protocol）做成 Spring 生态原生集成

下面逐个拆。

---

## 决策一：ChatClient 流式 API——WebClient / RestClient 的 AI 版本

Spring 生态做 HTTP 客户端有两个标杆：`RestClient`（同步、流式 API）和 `WebClient`（响应式）。它们共同的设计原则是**把一个多步骤操作装进一条可读的链式调用**。Spring AI 把这个设计搬到了 LLM 调用里：[chatclient.adoc](https://github.com/spring-projects/spring-ai/blob/main/spring-ai-docs/src/main/antora/modules/ROOT/pages/api/chatclient.adoc) 开篇写：

> The `ChatClient` offers a fluent API for communicating with an AI Model. It supports both a synchronous and streaming programming model.

最简使用看起来确实像 RestClient：

```java
@RestController
class MyController {

    private final ChatClient chatClient;

    public MyController(ChatClient.Builder chatClientBuilder) {
        this.chatClient = chatClientBuilder.build();
    }

    @GetMapping("/ai")
    String generation(String userInput) {
        return this.chatClient.prompt()
            .user(userInput)
            .call()
            .content();
    }
}
```

但 Spring AI 2.0 把这套 API 推得更远——把 tool calling loop、advisor chain、memory、observability 都装进 `ChatClient` 这一层，不再暴露底层 `ChatModel` 的细节。[tools.adoc](https://github.com/spring-projects/spring-ai/blob/main/spring-ai-docs/src/main/antora/modules/ROOT/pages/api/tools.adoc) 写：

> Spring AI 2.0 makes the tool calling loop a first-class, composable component of the `ChatClient`'s advisor chain. ... This architecture replaces the per-`ChatModel` tool execution loops of Spring AI 1.x.

这条**意味着**：

- 1.x 里"调 LLM"是直接对 `ChatModel.call()`；tool execution 是 `ChatModel` 自己的逻辑
- 2.0 里"调 LLM + tool calling + memory + observability + retry"全部由 ChatClient 上的 Advisor Chain 编排；`ChatModel` 退到"纯粹接收 prompt、返回 response"的原子层

为什么这么设计？因为 Java 生态的诉求和 Python 生态不同。Python 开发者习惯直接对 `openai.OpenAI()` client 写 prompt、解析 response——这种"裸调 LLM"模式在 Python 圈是惯用的。Java 圈不一样：Spring Boot 应用层强调 portable、可配置、可观察——你不可能让业务方代码知道"现在用的是 OpenAI 还是 Anthropic"、"retry 策略是 Spring Retry 还是 Resilience4j"、"metrics 是 Micrometer 还是 OpenTelemetry"。

ChatClient Fluent API 把这些 cross-cutting concerns 全压到 builder 层，业务代码只看 `.prompt().user().call().content()`——这是 Spring 的标准做法。

具体到 [ChatClient 的 builder 实现](https://github.com/spring-projects/spring-ai/tree/main/spring-ai-client-chat)，它依赖一个 prototype-scoped `ChatClient.Builder` bean。`@Primary` 的 ChatModel 被自动注入 builder；其他 ChatModel（多 provider 场景）需要单独注册 builder bean。这个设计有工程判断在里头：

- prototype-scoped 保证每个 `@Bean` 注入点是独立的 builder 实例，避免共享状态污染
- `ChatClientBuilderConfigurer` bean 让自定义 Builder 时仍能 apply 所有 `ChatClientBuilderCustomizer`——这是 Spring 自身的扩展点模式（`*Customizer` 链）

代价是：多 ChatModel 场景下必须显式标记 `@Primary` 或手动 create `ChatClient.Builder`，否则依赖注入歧义。Spring AI 选择接受这个复杂度，换来单 ChatModel 场景的极简 API。

---

## 决策二：Advisors 拦截器链——Servlet Filter 思路搬到 AI 调用

如果 ChatClient Fluent API 是 RestClient 的复刻，那 Advisors 就是 Servlet Filter 的复刻——这是 Spring 生态最经典的拦截器模式。[advisors.adoc](https://github.com/spring-projects/spring-ai/blob/main/spring-ai-docs/src/main/antora/modules/ROOT/pages/api/advisors.adoc) 开篇：

> The Spring AI Advisors API provides a flexible and powerful way to intercept, modify, and enhance AI-driven interactions in your Spring applications. By leveraging the Advisors API, developers can create more sophisticated, reusable, and maintainable AI components.

核心接口是三个：

```java
public interface CallAdvisor extends Advisor {
    ChatClientResponse adviseCall(
        ChatClientRequest chatClientRequest,
        CallAdvisorChain callAdvisorChain);
}

public interface StreamAdvisor extends Advisor {
    Flux<ChatClientResponse> adviseStream(
        ChatClientRequest chatClientRequest,
        StreamAdvisorChain streamAdvisorChain);
}
```

工作流程在 [advisors-flow.jpg](https://github.com/spring-projects/spring-ai/blob/main/spring-ai-docs/src/main/antora/modules/ROOT/pages/api/advisors.adoc) 里画得很清楚：

1. `ChatClient` 构造一个 `ChatClientRequest`（含 unsealed Prompt）+ 空 advisor context
2. advisor chain 按 `Ordered.getOrder()` 顺序处理 request（**order 低的先处理 request，order 低的最后处理 response**——栈式语义）
3. 最后一个 advisor（框架注入）把 request 送到 `ChatModel`
4. response 反向流回 chain，每个 advisor 可以修改 response
5. 最终 `ChatClientResponse` 返回给 caller

栈式语义来自 `Ordered` 接口的复用。文档里专门用 [NOTE](https://github.com/spring-projects/spring-ai/blob/main/spring-ai-docs/src/main/antora/modules/ROOT/pages/api/advisors.adoc) 强调：

> The seeming contradiction between order and execution sequence is due to the stack-like nature of the advisor chain: An advisor with the highest precedence (lowest order value) is added to the top of the stack. It will be the first to process the request as the stack unwinds. It will be the last to process the response as the stack rewinds.

这是 Spring `Ordered` 的标准语义——复用让 Java 开发者零学习成本就理解 advisor order。文档还给了具体场景的判断：

> Set the order close to `Ordered.HIGHEST_PRECEDENCE` to ensure an advisor is executed first in the chain (first for request processing, last for response processing).

这个栈式语义的工程价值在哪？**它让 advisor 的"在哪一侧（request / response）生效"可以通过 order 控制**。比如：

- 一个 logging advisor（`HIGHEST_PRECEDENCE`）会在 request 阶段第一时间记录，但 response 阶段最后拿到完整响应——这对 logging 很有用，能记录"完整链路"
- 一个 retry advisor（`LOWEST_PRECEDENCE`）会在 request 阶段最后才执行（保留前面的所有 advisor 改过的内容），response 阶段第一时间拿到响应（决定是否 retry）——这是 retry 的正确位置

如果用普通 list 顺序处理（不是 stack），retry 就要面对"前面 advisor 的修改是否要 replay"的复杂问题——栈式语义一次性解决。

Advisor Chain 内置一个上下文对象 `advise-context`，用于跨 advisor 共享状态。比如 `QuestionAnswerAdvisor` 在 request 阶段把检索到的 documents 放进 context，下一个 `LoggingAdvisor` 就能在 response 阶段读到"这次请求用了哪几个文档"。

这跟 Servlet Filter 的 `FilterChain` 设计几乎一样——Spring 生态一贯的设计模式。

---

## 决策三：ETL Pipeline 用 Java 函数式接口建模——`Supplier` / `Function` / `Consumer` 自然映射 Extract / Transform / Load

[etl-pipeline.adoc](https://github.com/spring-projects/spring-ai/blob/main/spring-ai-docs/src/main/antora/modules/ROOT/pages/api/etl-pipeline.adoc) 把 ETL 三阶段映射成三个 Java 内置函数式接口：

```java
public interface DocumentReader extends Supplier<List<Document>> {
    default List<Document> read() { return get(); }
}

public interface DocumentTransformer extends Function<List<Document>, List<Document>> {
    default List<Document> transform(List<Document> docs) { return apply(docs); }
}

public interface DocumentWriter extends Consumer<List<Document>> {
    default void write(List<Document> docs) { accept(docs); }
}
```

Extract 阶段（`DocumentReader`）是**数据源**——产出一批 `Document`。Spring AI 内置 PDF / JSON / Markdown / Text 等 reader，每个 reader实现 `Supplier<List<Document>>` 接口。Transform 阶段（`DocumentTransformer`）是**数据变换**——比如 `TokenTextSplitter` 把长文档按 token 切成小段（保留段落语义边界）。Load 阶段（`DocumentWriter`）是**写入目标**——`VectorStore` 实现 `Consumer<List<Document>>`，把 documents 写入 vector store。

链式调用极简：

```java
vectorStore.write(tokenTextSplitter.split(pdfReader.read()));
```

或者 function-style 写法（同样语义）：

```java
vectorStore.accept(tokenTextSplitter.apply(pdfReader.get()));
```

为什么用 Java 函数式接口建模？两个判断：

- **类型即文档**——`Supplier` / `Function` / `Consumer` 在 Java 圈是基础类型，开发者一看就知道"读 / 转换 / 写"三件事的输入输出契约
- **Java 标准库天然支持组合**——`Supplier.compose(Function)`、`Function.andThen(Function)`、`Consumer.andThen(Consumer)` 这些标准库方法直接可用

这种"用语言内建类型建模业务概念"的做法是 Spring 一贯风格——它不发明新的"DocumentReader 接口就能读文档"，而是用 `Supplier` 这个 Java 圈所有人都认识的契约。同样，`PagePdfDocumentReader` 实现 `Supplier<List<Document>>` 而不是实现一个 Spring 自定义的 `DocumentReader` 接口，意思就是"这就是一个数据源，没什么特别的"。

`Document` 类本身也体现这个思路：包含 text + metadata + 可选的 media（image/audio/video）。`Metadata` 是 `Map<String, Object>`，所有 vector store / reader / writer 都通过 metadata 而非专门类型交互——这也是 Spring "用 Map 而不是专类型做灵活 metadata"的一贯做法。

---

## 决策四：VectorStore SQL-like 元数据过滤——21+ vector store 统一抽象

Vector store 是 RAG 的命门——但每家 vector database（Milvus / Pinecone / Weaviate / Qdrant / Chroma / pgvector / Elasticsearch / Cassandra ...）都有自己的 metadata filter 语法。如果 Spring AI 不做这层抽象，每个 provider 的 metadata filter API 都不通用，跨 vendor 切换就是噩梦。

Spring AI 的解法是定义一个 **SQL-like 的 `FilterExpression` 抽象**，然后每个 vector store adapter 自己实现从 `FilterExpression` 到自家 DSL 的转换。[vectordbs.adoc](https://github.com/spring-projects/spring-ai/blob/main/spring-ai-docs/src/main/antora/modules/ROOT/pages/api/vectordbs.adoc) 里给了一组 example：

```
country == 'UK' && year > 2020
genre in ['科幻', '动作'] && rating >= 4.5
status == 'ACTIVE' && (priority > 5 || owner == 'admin')
```

这套 SQL-like DSL 设计得相当通用——支持 `==` / `!=` / `>` / `>=` / `<` / `<=` / `in` / `nin` / `like` / `and` / `or` / `not`。底层通过 `FilterExpressionBuilder` 解析成 `Filter.Expression` AST 树，再由各 vector store adapter 翻译成自家 query language。

具体 RAG 集成在 [retrieval-augmented-generation.adoc](https://github.com/spring-projects/spring-ai/blob/main/spring-ai-docs/src/main/antora/modules/ROOT/pages/api/retrieval-augmented-generation.adoc)——`QuestionAnswerAdvisor` 是 RAG 的开箱即用实现：

```java
ChatResponse response = ChatClient.builder(chatModel)
        .build().prompt()
        .advisors(QuestionAnswerAdvisor.builder(vectorStore).build())
        .user(userText)
        .call()
        .chatResponse();
```

`QuestionAnswerAdvisor` 在 advisor chain 里做两件事：

- 把 user text 做 embedding 相似度搜索
- 把 top-K documents append 到 user text 后面，形成 augmented prompt
- 让 ChatModel 在 augmented context 下生成 answer

`FILTER_EXPRESSION` 是 advisor context 里的一个参数，运行时可以动态修改过滤表达式：

```java
String content = this.chatClient.prompt()
    .user("Please answer my question XYZ")
    .advisors(a -> a.param(QuestionAnswerAdvisor.FILTER_EXPRESSION, "type == 'Spring'"))
    .call()
    .content();
```

这意味着同一个 ChatClient builder 可以服务多个用户，每个用户携带不同的 filter——按 tenant 隔离、按时间窗口隔离、按权限隔离都能做。

`RetrievalAugmentationAdvisor` 是更复杂的版本：支持 module 化 RAG flows（DocumentRetriever / QueryAugmenter / DocumentJoiner / ResponsePostprocessor），允许自定义每个环节。

这套 SQL-like DSL + adapter 的设计判断：**SQL-like 而不是 Java method-chaining**——理由是 metadata filter 表达"的关系运算"用文本形式更紧凑（`country == 'UK' && year > 2020` 比 `eq(field("country"), "UK").and(gt(field("year"), 2020))` 更易读）；**SQL-like 而不是 JPA-style Criteria API**——因为 metadata filter 的数据 schema 是动态的（每个 Document 的 metadata keys 不固定），强类型 Criteria API 不合适。

---

## 决策五：MCP Java Annotations + Boot Starter——把 Anthropic MCP 做成 Spring 原生集成

[MCP（Model Context Protocol）](https://modelcontextprotocol.org/) 是 Anthropic 2024 年发布的开放协议，标准化 AI 模型与外部工具/资源的交互。Java 圈对 MCP 的支持来自 [MCP Java SDK](https://modelcontextprotocol.io/sdk/java/mcp-overview)，它提供 Client / Server / Session / Transport 四层抽象。

Spring AI 不重复造轮子——它直接复用 MCP Java SDK，但加上 Spring 风格的两层包装：

1. **Spring Boot Starters** ——把 MCP transport 配置变成 Spring Boot auto-configuration
2. **MCP Java Annotations** ——声明式定义 `@McpTool` / `@McpResource` / `@McpPrompt` 等注解，简化 MCP 服务器开发

[Spring AI MCP overview](https://github.com/spring-projects/spring-ai/blob/main/spring-ai-docs/src/main/antora/modules/ROOT/pages/api/mcp/mcp-overview.adoc) 列了 6 个 starter：

| Starter | Transport |
| --- | --- |
| `spring-ai-starter-mcp-client` | Core client + STDIO + Servlet SSE + Streamable-HTTP |
| `spring-ai-starter-mcp-client-webflux` | WebFlux SSE / Streamable-HTTP |
| `spring-ai-starter-mcp-server` | STDIO server |
| `spring-ai-starter-mcp-server-webmvc` | WebMVC SSE / Streamable-HTTP / Stateless |
| `spring-ai-starter-mcp-server-webflux` | WebFlux SSE / Streamable-HTTP / Stateless |

6 个 starter 覆盖 client + server × {httpclient, webflux, webmvc} × {SSE, Streamable-HTTP} + STDIO server。pom 里能看到 6 个 auto-configuration module：

```
auto-configurations/mcp/spring-ai-autoconfigure-mcp-client-common
auto-configurations/mcp/spring-ai-autoconfigure-mcp-client-httpclient
auto-configurations/mcp/spring-ai-autoconfigure-mcp-client-webflux
auto-configurations/mcp/spring-ai-autoconfigure-mcp-server-common
auto-configurations/mcp/spring-ai-autoconfigure-mcp-server-webflux
auto-configurations/mcp/spring-ai-autoconfigure-mcp-server-webmvc
```

`common` 提供基础配置（连接池、超时、序列化），`httpclient` / `webflux` / `webmvc` 提供 transport-specific 集成。这种"common + flavor"的 module 拆分是 Spring Boot auto-configuration 的标准做法。

更激进的是 [MCP Annotations](https://github.com/spring-projects/spring-ai/blob/main/spring-ai-docs/src/main/antora/modules/ROOT/pages/api/mcp/mcp-annotations-server.adoc)：

```java
@Component
public class WeatherTools {

    @McpTool(description = "Get the current weather for a given city")
    public String getWeather(@McpToolParam(description = "City name") String city) {
        return weatherService.fetch(city);
    }
}
```

`@McpTool` / `@McpResource` / `@McpPrompt` 是 server 端注解；`@McpLogging` / `@McpSampling` / `@McpElicitation` / `@McpProgress` 是 client 端注解。这种"声明式 MCP 集成"是 Spring 生态的标准思路——对照 Spring Data JPA 的 `@Query` / Spring Web 的 `@GetMapping`，都是"注解 + auto-configuration + 元数据扫描"三件套。

`@McpTool` 和 Spring AI 自己的 `@Tool`（在 tools.adoc）有概念重叠但目的不同：Spring AI 的 `@Tool` 是给 ChatClient 用的工具调用声明；`@McpTool` 是给 MCP 服务器用的协议级声明。两者在"自动生成 JSON schema / 参数描述 / 返回值转换"这些细节上有相似实现，但作用在不同协议层。

MCP integration 的工程判断：

- **不复造 MCP SDK**——直接复用 Java SDK，避免维护协议级代码
- **多 transport starter**——SSE / Streamable-HTTP / STDIO 各有应用场景，Spring Boot 一键切换
- **注解 + auto-config 风格**——降低 MCP 服务器/客户端的 boilerplate，让 Spring 开发者用熟悉的方式定义 MCP endpoints

代价是 6 个 starter 增加了入门时的选择成本——但 README 里 7 6 个 starter 矩阵直接列出 transport 支持关系，选择路径清晰。

---

## 这 5 个决策之外

spring-ai-rag 里有几个值得讲的细节：

**RAG 模块化设计**——`RetrievalAugmentationAdvisor.builder()` 接受四个 component：

- `DocumentRetriever`（从 vector store 检索）
- `QueryAugmenter`（增强 query，比如改写、加 contextual 信息）
- `DocumentJoiner`（合并多源 documents）
- `ResponsePostprocessor`（后处理 response，比如引用追踪）

这种"Advisor pattern + module composition"是经典的设计——对照 LangChain 的 LCEL 和 LlamaIndex 的 Query Engine，Spring AI 的做法更接近 Onyx / Pipeline Bags 的工程风格：每个 module 有清晰的输入输出契约。

**Chat Memory 5 个 backend**——`spring-ai-autoconfigure-model-chat-memory-repository-{cassandra, jdbc, mongodb, neo4j, redis}` 5 个持久化 backend。Redis 和 Neo4j 是较常见的内存后端选择；Cassandra 和 MongoDB 适合需要持久化对话历史的场景；JDBC 让 MySQL/PostgreSQL 也能用。配置粒度到 backend，ChatClient 不感知。

**Document Reader Resource-based 安全**——`etl-pipeline.adoc` 顶部明确写：

> Care should be taken not to construct such instances using directly user supplied URLs, as there are security implications to this.

这是 Spring 一贯的安全提示——`Resource` 抽象让路径解析更安全，但 user-controlled URLs 仍然是 SSRF 风险。这种"提供抽象但不替你规避风险"的写法，把安全责任明确交给调用方，是工程上负责任的做法。

**VectorStoreChatMemoryAdvisor**——把 Chat Memory 存进 Vector Store 而非专门的 Memory backend。这让"对话历史"也能走相似度检索——比如保留 100 条对话历史，query 时只检索 top-K 相关历史。RAG 不只用于文档，还用于对话上下文管理。

---

## 写给想用 Spring AI 做生产级 AI 应用的 Java 团队

读完这 5 个决策，几个能立刻用得上的判断：

**判断 1：直接用 ChatClient，不要绕过它去用 ChatModel**。1.x 风格的"裸调 ChatModel + 自己实现 tool execution loop"在 2.0 已经不再推荐——2.0 把所有 cross-cutting concerns 都收敛到 ChatClient 层的 Advisor Chain 上。你绕过 ChatClient，就等于放弃了 observability、retry、memory、tool loop 全部内置能力。

**判断 2：Advisor 的 order 决定它在 chain 中的位置**——栈式语义让 order 既控制 request 处理顺序又控制 response 处理顺序。Logging advisor 用 `HIGHEST_PRECEDENCE`（request 阶段第一时间记录，response 阶段最后拿到完整结果）；Retry advisor 用 `LOWEST_PRECEDENCE`（response 阶段第一时间决定是否 retry）；RAG / Memory / Tool Calling 中间层 advisor 用中间 order。

**判断 3：VectorStore 选型时优先考虑"已存在的数据栈"**。Spring AI 21+ adapter 让你能选 Milvus / Pinecone / Weaviate / pgvector 等，但真正驱动选择的是"你生产环境里已经跑着什么"。如果已有 PostgreSQL，pgvector 是最低运维成本的选项；如果已有 Elasticsearch 集群，把它当 vector store 也是合理选择。Spring AI 抽象让你不会 vendor-lock-in。

**判断 4：MCP integration 现在还分 6 个 starter**——是因为 MCP 协议本身还在演进（Streamable-HTTP 是 2024 年新加的）。Spring AI 用 starter-per-transport 而不是单一 starter，是为了快速跟进协议演进而不破坏现有用户。等 MCP 协议稳定后，可能会收敛。但今天选哪个 starter，要看你的部署环境：传统 servlet 容器选 `server-webmvc`，响应式 WebFlux 选 `server-webflux`，stdio 进程间通信选 `server`。

**判断 5：不要在 Spring AI 里硬塞"业务架构"**——它的 Advisor Chain 是为 AI 交互设计的，不是为通用业务拦截器设计的。cross-cutting concerns 里和 AI 无关的部分（日志、安全、retry）应该用 Spring 自己的 filter / interceptor / Spring Retry / Spring Security 等。混淆两者的边界会让 advisor chain 变成"大杂烩"，失去 clarity。

---

## 这个项目真正讲的是什么

把 5 个决策摆在一起看，Spring AI 不是又一个 LangChain 的 Java 复刻——它是**把 Spring 生态二十年的设计哲学搬到 AI 域**：

- **ChatClient 沿用 WebClient/RestClient**——Java 圈的 HTTP 客户端心智模型被搬到 LLM 调用
- **Advisor 沿用 Servlet Filter**——Java 圈的拦截器模式被搬到 AI 调用 chain
- **ETL Pipeline 沿用 Supplier/Function/Consumer**——Java 圈的基础类型被用来建模业务概念
- **VectorStore SQL-like DSL**——SQL 圈的可读性被搬到 metadata filter
- **MCP Boot Starter + Annotations**——Spring Boot auto-configuration 模式被用来集成 MCP 协议

每一层都是"把已成熟的 Java 生态设计搬到 AI 域"，而不是"发明新的 Java 生态设计"。这正是 Spring AI 的定位——**Java/Spring 圈不需要"另一套 AI 框架"，需要的是"在熟悉的 Spring 抽象里调 AI"**。

读 Spring AI 的代码不是学 AI——是学**怎么用 Java 圈成熟的工程模式包装未成熟的 AI 协议**。当 MCP、vector store、tool calling 协议还在快速演进时，Spring 风格的"封装 + auto-config + 注解"模式给 Java 团队提供了一个稳定的对接层——AI 协议再变，业务代码不改。

22> Spring AI 9.4k stars 不是一个"Java 圈也能做 AI"的项目。它的价值在**让 Java/Spring 团队不需要放弃二十年积累的工程实践就能进入 AI 域**。这是 Spring 一贯的哲学——**好的框架不是让你学新东西，是让你用熟悉的东西做新事情**。

> 出处：
> - 仓库：[github.com/spring-projects/spring-ai](https://github.com/spring-projects/spring-ai)
> - 核心文档：[concepts.adoc](https://github.com/spring-projects/spring-ai/blob/main/spring-ai-docs/src/main/antora/modules/ROOT/pages/concepts.adoc) · [chatclient.adoc](https://github.com/spring-projects/spring-ai/blob/main/spring-ai-docs/src/main/antora/modules/ROOT/pages/api/chatclient.adoc) · [advisors.adoc](https://github.com/spring-projects/spring-ai/blob/main/spring-ai-docs/src/main/antora/modules/ROOT/pages/api/advisors.adoc) · [etl-pipeline.adoc](https://github.com/spring-projects/spring-ai/blob/main/spring-ai-docs/src/main/antora/modules/ROOT/pages/api/etl-pipeline.adoc) · [retrieval-augmented-generation.adoc](https://github.com/spring-projects/spring-ai/blob/main/spring-ai-docs/src/main/antora/modules/ROOT/pages/api/retrieval-augmented-generation.adoc) · [tools.adoc](https://github.com/spring-projects/spring-ai/blob/main/spring-ai-docs/src/main/antora/modules/ROOT/pages/api/tools.adoc) · [mcp/mcp-overview.adoc](https://github.com/spring-projects/spring-ai/blob/main/spring-ai-docs/src/main/antora/modules/ROOT/pages/api/mcp/mcp-overview.adoc)
>
> 作者：钳岳 · 2026-09-05