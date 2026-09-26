---
title: "Spring AI 架构深读：从 ChatClient 流式 API 到 Advisors 拦截器，Java 圈为什么需要这套 AI 抽象"
date: "2026-09-05T16:00:00+08:00"
lastmod: "2026-09-19T00:00:00+08:00"
draft: false
categories: ["技术笔记"]
tags: ["spring-ai", "java", "spring-boot", "chatclient", "advisors", "mcp", "rag", "etl", "项目解读"]
description: "Spring AI 2.0（最新发布 2.0.1，main 已进入 2.1.0-SNAPSHOT）主线深读。README 把项目目标写成两件事：把 Spring 生态的 portability 与 modular design 用到 AI 域，用强类型数据结构和 API 做应用构件。本文按这个口径拆五个工程决策——ChatClient 链式 API 的 builder 注入规则、Advisor 链的栈式 order 与工具调用循环的内外之分、ETL 复用 Supplier/Function/Consumer、VectorStore 的 SQL-like 过滤 DSL 与它的算子边界、MCP 的五个 starter 与一次 Maven 坐标迁移。全部断言按 2026-09-19 的仓库 HEAD、分支 pom、Maven Central 与文档原文核对。"
slug: "spring-ai-application-framework-design"
band: "review"
gates: ["事实性", "去AI味", "观点依据"]
hiddenFromHomePage: false
github_repo: "spring-projects/spring-ai"
source_key: "gh:spring-projects/spring-ai"
---

Spring AI 的常见介绍是「LangChain 的 Java 复刻」。[README.md](https://github.com/spring-projects/spring-ai/blob/main/README.md) 第 5 行写的是另一回事：

> Its goal is to apply Spring ecosystem design principles, such as portability and modular design, to the AI domain and promote using strongly-typed data structures and APIs as the building blocks of an application.

这两句划的是不同的责任边界。「复刻」意味着跟着各家的接口形状走；「可移植 + 模块化」要求它自己决定抽象放在哪一层、把哪一侧的变化挡住。仓库文档里还有一句配套话：项目「不是这些项目的直接移植」（概览与特性索引页 [index.adoc](https://github.com/spring-projects/spring-ai/blob/main/spring-ai-docs/src/main/antora/modules/ROOT/pages/index.adoc) 原文 `Spring AI is not a direct port of those projects`）。

本文按这个判断读 2.0：五个抽象各自的入口在哪、它们分别挡住了什么，以及 2.0 把「谁负责工具调用循环」从模型层挪到拦截层这件事在源码里留下的证据。三条线值得带着读：这套抽象的成本落在谁的代码里、哪些 1.x 写法到 2.0 已经编译不过、一个团队从哪一层开始接最省事。

术语先约好：本文说大语言模型（LLM）指远端的推理服务，说提示词（prompt）指发给它的消息集合，说检索增强生成（RAG）指「先查资料再让模型作答」这条链路；应用程序接口（API）与建造者模式（builder）按 Spring 文档原名混用，不逐处译成中文。

## 目录

- [1. 系统地图：一次调用会经过哪五层](#1-系统地图一次调用会经过哪五层)
- [2. 版本口径：main、2.0.x、1.1.x 各自配哪个 Spring Boot](#2-版本口径main20x11x-各自配哪个-spring-boot)
- [3. 决策一：ChatClient 的链式 API，代价藏在 builder 的注入规则里](#3-决策一chatclient-的链式-api代价藏在-builder-的注入规则里)
- [4. 决策二：Advisor 链是栈，order 决定「看不看得到每一轮工具调用」](#4-决策二advisor-链是栈order-决定看不看得到每一轮工具调用)
- [5. 决策三：ETL 用语言内建类型建模](#5-决策三etl-用语言内建类型建模)
- [6. 决策四：VectorStore 与 SQL-like 过滤 DSL 的算子边界](#6-决策四vectorstore-与-sql-like-过滤-dsl-的算子边界)
- [7. 决策五：MCP 的五个 starter、一个协议属性和一次坐标迁移](#7-决策五mcp-的五个-starter一个协议属性和一次坐标迁移)
- [8. 一次请求的流转：带两轮工具调用的问答](#8-一次请求的流转带两轮工具调用的问答)
- [9. 常见错误与排查](#9-常见错误与排查)
- [10. 五道自测题](#10-五道自测题)
- [11. 采用建议](#11-采用建议)
- [12. 这套抽象真正换来什么](#12-这套抽象真正换来什么)
- [13. 下一步读哪份代码](#13-下一步读哪份代码)
- [14. 参考资料与核查方法](#14-参考资料与核查方法)

---

## 1. 系统地图：一次调用会经过哪五层

| 层 | 入口类型 | 所在模块 | 这层替你挡住什么 |
| --- | --- | --- | --- |
| 应用 | `ChatClient` | `spring-ai-client-chat` | 链式调用形状、advisor 装配、可观测性 |
| 编排 | `CallAdvisor` / `StreamAdvisor` | 同上，包 `...chat.client.advisor.api` | 记忆、检索、工具循环、日志的顺序与组合 |
| 模型 | `ChatModel` 及各 provider 实现 | `models/` 下 15 个模型模块 | 请求体差异、流式协议差异 |
| 数据 | `VectorStore` / `VectorStoreRetriever` | `spring-ai-vector-store`、`vector-stores/` | 查询语法、元数据过滤、建库与批量写入 |
| 文档 | `DocumentReader` / `DocumentTransformer` / `DocumentWriter` | `spring-ai-commons`、`document-readers/` | 解析与切分，写入目标可换 |

一次调用走过的路：

```text
你的代码
  ChatClient.prompt().user(...).call().content()
      │
      ├─ ChatClientRequest（未展开的 Prompt + 空的 advisor 上下文）
      ▼
   Advisor 链（按 getOrder() 从小到大排；顺序决定谁看得见什么）
      ├─ 记忆 advisor：进循环前读历史，出循环后写回
      ├─ ToolCallingAdvisor：驱动工具调用循环（2.0 新增的落点）
      ├─ 检索 advisor：把命中文档拼进提示词
      ▼
   ChatModel.call(Prompt) ──► 远端模型
      ▲                            │
      └──── ToolResponseMessage ◄──┘  工具调用由 ToolCallingManager 执行
```

五个决策分别落在这张图的不同层，把它们串起来的是同一件事：**编排权在 2.0 归到了 advisor 链**。先从版本口径开始，因为跨版本的写法差异直接决定后面四节能不能照抄。

## 2. 版本口径：main、2.0.x、1.1.x 各自配哪个 Spring Boot

三条分支的 `pom.xml` 我逐条读过（2026-09-19），发布序列取自 Maven Central 的 `spring-ai-bom` 元数据与 GitHub Releases：

| 线 | 仓库里的版本 | `spring-boot.version` | 发布状态 |
| --- | --- | --- | --- |
| `main` | `2.1.0-SNAPSHOT` | `4.2.0-SNAPSHOT` | 未发布，Maven Central 上无 2.1.x |
| `2.0.x` | `2.0.2-SNAPSHOT` | `4.1.2-SNAPSHOT` | 维护线 |
| 最新发布 | `2.0.1`（2026-08-21） | `4.1.1`（tag `v2.0.1` 的 pom） | 生产可用 |
| `2.0.0` | 已发布，GA 2026-06-12 | `4.1.0` | 从 1.1.x 升级的主断点 |
| `1.1.x` | `1.1.9-SNAPSHOT` | `3.5.15` | 最后发布 `1.1.8`（2026-06-12） |
| `1.0.x` | 分支仍在 | — | 最后发布 `1.0.9`（同日） |

三行的 Boot 版本互不重叠（3.5 / 4.1 / 4.2）。我把它读成 1.1.x 还在发补丁的原因：跨的是 Spring Boot 大版本，不是特性偏好——这一句是本文的判断，文档只给出兼容表。如果你的应用还在 Boot 3.5，可选空间只有 1.1.x，本文第 4 节里「2.0 才有的编排能力」一条都拿不到。

仓库元数据一并记下，方便日后复核：Apache-2.0，创建于 2023-06-27，9,463 stars、2,919 forks（GitHub API，2026-09-19）。star 数只说明关注人数，本文不用它支撑任何技术结论。

## 3. 决策一：ChatClient 的链式 API，代价藏在 builder 的注入规则里

[chatclient.adoc](https://github.com/spring-projects/spring-ai/blob/main/spring-ai-docs/src/main/antora/modules/ROOT/pages/api/chatclient.adoc) 开篇：

> The `ChatClient` offers a fluent API for communicating with an AI Model. It supports both a synchronous and streaming programming model.

index.adoc 把形状来源说得更直接：`idiomatically similar to the WebClient and RestClient APIs`。文档给的最小示例是：

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

链式调用本身没有讨论价值，有意思的是它背后那条作用域规则。文档原话：`Spring AI provides Spring Boot autoconfiguration, creating a prototype ChatClient.Builder bean`，并补了一句 `a new instance is created for each injection point`——每个注入点拿到一个新 builder，所以同一份自动配置可以给两个 bean 配出两套默认参数：

```java
@Configuration
class ChatClientConfig {

    @Bean
    ChatClient defaultChatClient(ChatClient.Builder builder) {
        return builder.build();
    }

    @Bean
    ChatClient customChatClient(ChatClient.Builder builder) {
        return builder.defaultSystem("You are a helpful assistant.").build();
    }
}
```

这套设计的价格在文档下一段写着，而且和多数人的直觉相反：

> When working with multiple AI models, you might be tempted to define separate `ChatClient` beans by using `ChatClient.create(chatModel)` or `ChatClient.builder(chatModel)`. However, doing so bypasses the auto-configured `ChatClient.Builder`, which means observability and `ChatClientBuilderCustomizer` beans are ignored.

也就是说，多 provider 场景下用 `ChatClient.create(...)` 省掉的那一步，代价是可观测性和所有 `ChatClientBuilderCustomizer` bean 静默失效。文档给的替代入口是注入 `ChatClientBuilderConfigurer`（包名 `org.springframework.ai.model.chat.client.autoconfigure`），由它去补齐 customizer 与观测装配；上下文里同时存在多个 `ChatModel` bean 时，再按文档建议显式标 `@Primary`，或者自己定义一个 `ChatClient.Builder` bean 覆盖自动配置。

为什么把这层做成链式而不是让业务直接面对模型客户端？Java 侧的约束很具体：一个 Spring Boot 应用里，用哪家模型、重试走什么策略、指标发给谁，都是配置期决定的事，不该渗进业务方法签名。链式 builder + prototype 注入点正好把这三件事留在装配期。

## 4. 决策二：Advisor 链是栈，order 决定「看不看得到每一轮工具调用」

[advisors.adoc](https://github.com/spring-projects/spring-ai/blob/main/spring-ai-docs/src/main/antora/modules/ROOT/pages/api/advisors.adoc) 的第一句：

> The Spring AI Advisors API provides a flexible and powerful way to intercept, modify, and enhance AI-driven interactions in your Spring applications.

接口在 `org.springframework.ai.chat.client.advisor.api` 包下，与源码逐字一致：

```java
public interface Advisor extends Ordered {
    String getName();
}

public interface CallAdvisor extends Advisor {
    ChatClientResponse adviseCall(
        ChatClientRequest chatClientRequest, CallAdvisorChain callAdvisorChain);
}

public interface StreamAdvisor extends Advisor {
    Flux<ChatClientResponse> adviseStream(
        ChatClientRequest chatClientRequest, StreamAdvisorChain streamAdvisorChain);
}
```

请求侧与响应侧共用一个 order，语义是栈：

> An advisor with the highest precedence (lowest order value) is added to the top of the stack. It will be the first to process the request as the stack unwinds. It will be the last to process the response as the stack rewinds.

`Ordered` 是 Spring 自己的接口，复用它的学习成本为零。但 2.0 里 order 的真正信息量不在「谁先跑」，而在**某个 advisor 是在工具调用循环的里面还是外面**。

### 4.1 三个默认值构成一条硬边界

| advisor | 默认 order | 相对工具循环的位置 |
| --- | --- | --- |
| 记忆类（`MessageChatMemoryAdvisor`、`VectorStoreChatMemoryAdvisor`） | `Ordered.HIGHEST_PRECEDENCE + 200` | 外 |
| `ToolCallingAdvisor` | `Ordered.HIGHEST_PRECEDENCE + 300` | 循环本身 |
| `QuestionAnswerAdvisor` / `RetrievalAugmentationAdvisor` / `SimpleLoggerAdvisor` / `SafeGuardAdvisor` | `0` | 内 |
| `ChatModelCallAdvisor` / `ChatModelStreamAdvisor`（框架注入的末位） | `Ordered.LOWEST_PRECEDENCE` | 最内，交给模型 |

数字来自源码：常量 `DEFAULT_CHAT_MEMORY_PRECEDENCE_ORDER` 定义在 `Advisor` 接口里，值为 `HIGHEST_PRECEDENCE + 200`；`ToolCallingAdvisor.DEFAULT_ORDER` 是 `HIGHEST_PRECEDENCE + 300`，它上方那段字段注释直接写明这个差值的目的：让默认位置的记忆 advisor 落在循环外，不参与每次工具调用迭代。`HIGHEST_PRECEDENCE` 是 `Integer.MIN_VALUE`，所以 +200 < +300 < 0 < 末位。

这个边界是 2.0 才立起来的。upgrade-notes 的对应条目写着：`DEFAULT_CHAT_MEMORY_PRECEDENCE_ORDER` 从 `HIGHEST_PRECEDENCE + 1000` 改成 `+200`，给的理由翻过来是：这是正确的默认值，因为多数存储实现不支持那类消息。

### 4.2 为什么要挪：一次被删掉的选项

1.x 的工具循环长在每个 `ChatModel` 内部。[tools.adoc](https://github.com/spring-projects/spring-ai/blob/main/spring-ai-docs/src/main/antora/modules/ROOT/pages/api/tools.adoc) 把 2.0 的做法说成链上的一个可组合组件（composable component）：

> Spring AI 2.0 makes the tool calling loop a first-class, composable component of the `ChatClient`'s advisor chain.

同页的 NOTE 更硬：`This architecture replaces the per-ChatModel tool execution loops of Spring AI 1.x`。搬家留下的编译期痕迹都在 upgrade-notes 上：

- `internalToolExecutionEnabled` 从 `ToolCallingChatOptions` 和所有 provider 的 options 类里移除，配套属性 `spring.ai.<provider>.chat.internal-tool-execution-enabled` 一起删掉，原先每个模型自带的内部执行在所有 `ChatModel` 实现中都不存在了。
- `ToolExecutionEligibilityPredicate` 被删，替代物是挂在 advisor 上的 `ToolExecutionEligibilityChecker`（一个 `Function<ChatResponse, Boolean>`，默认判断 `chatResponse != null && chatResponse.hasToolCalls()`），provider 特有的 stop reason 逻辑现在有地方接了。
- `ToolCallAdvisor` 标注 `@Deprecated`（since 2.0.0），由 `ToolCallingAdvisor` 取代；两个类同时还在代码树里，读源码时别混。

最能说明「为什么非挪不可」的是 `streamToolCallResponses` 这个选项被整条删除的理由。文档的 Why 小节原话是：开启它之后，工具调用请求的中间块会往下游流，而配对回传给模型的 `ToolResponseMessage` 不会流；下游任何记忆 advisor 会收到一段「只有请求、没有结果」的历史，「损坏的会话历史」就是这么造出来的。文档接着写：不破坏 `ChatClientResponse` 就修不好，于是整个选项删除。

这是一个只在「循环属于模型内部」时才会出现的缺陷形状——循环进了 advisor 链，请求与结果的成对性才成为可被同一层保证的不变式。

### 4.3 自动注册的三行代码

带工具调用时你不需要手写 `ToolCallingAdvisor`。`DefaultChatClient.Builder.autoRegisterToolCallingAdvisor()`（`spring-ai-client-chat`）里能读到全部逻辑：

```java
boolean hasDownstreamMemoryAdvisor = this.advisors.stream()
    .anyMatch(a -> a instanceof MemoryAdvisor && a.getOrder() > configuredOrder);

this.advisors.add(this.toolCallingAdvisorBuilder.copy()
    .conversationHistoryEnabled(!hasDownstreamMemoryAdvisor)
    .build());
```

也就是说，只要链上存在 order 大于工具 advisor 的记忆 advisor（即落在循环内），框架就自动关掉 `ToolCallingAdvisor` 自己的会话历史，避免重复写入；同一方法开头还会读 `ChatClientAttributes.TOOL_CALLING_ADVISOR_AUTO_REGISTER` 这个开关，全局等价物是配置项 `spring.ai.chat.client.tool-calling.enabled`（默认 `true`）。旁边的 `validateSingleToolAdvisor()` 则规定链上只能有一个实现了 `ToolAdvisor` 的 advisor，多注册直接抛错并列出名字与 order。

### 4.4 想进循环，先查存储后端

把记忆 advisor 放到循环内（`order` 大于 +300），模型下一轮就能看到此前所有工具调用的完整往返。tools.adoc 的 Backend Compatibility 小节给了正向名单：截至 2.0，内置实现里只有 `InMemoryChatMemoryRepository`、`RedisChatMemoryRepository`、`Neo4jChatMemoryRepository` 认得完整消息集。反面写在 chat-memory.adoc：`JdbcChatMemoryRepository`、`CassandraChatMemoryRepository`、`MongoChatMemoryRepository` 三处各挂一个 WARNING，说含工具调用的助手消息与 `ToolResponseMessage` **在保存时被静默过滤**，检索结果里不会出现——注意是静默，不是抛错。两个文档都没提 Cosmos DB 落在哪一侧。社区项目 `spring-ai-session` 在 chat-memory.adoc 的三处 WARNING 里被点名推荐，upgrade-notes 进一步说它任意存储都能在循环内用，并计划在 2.1 取代 `ChatMemory`。

顺带记一条读源码会撞上的噪音。`ToolCallingAdvisor` 里 `advisorOrder` 字段上方的注释写着「set the order close to `Ordered.LOWEST_PRECEDENCE` to ensure an advisor is executed first in the chain」，与 advisors.adoc 的结论正好相反。以文档为准，注释是复制时写反了。

## 5. 决策三：ETL 用语言内建类型建模

[etl-pipeline.adoc](https://github.com/spring-projects/spring-ai/blob/main/spring-ai-docs/src/main/antora/modules/ROOT/pages/api/etl-pipeline.adoc) 把三个阶段映射到三个 JDK 函数式接口，定义在 `spring-ai-commons` 的 `org.springframework.ai.document` 包，与源码一致：

```java
public interface DocumentReader extends Supplier<List<Document>> {
    default List<Document> read() { return get(); }
}

public interface DocumentTransformer extends Function<List<Document>, List<Document>> {
    default List<Document> transform(List<Document> transform) { return apply(transform); }
}

public interface DocumentWriter extends Consumer<List<Document>> {
    default void write(List<Document> documents) { accept(documents); }
}
```

三个 `default` 方法只是给领域语法的壳，`get/apply/accept` 才是契约本体。文档里的两行链路写法：

```java
vectorStore.accept(tokenTextSplitter.apply(pdfReader.get()));
vectorStore.write(tokenTextSplitter.split(pdfReader.read()));
```

真实实现清单（按目录数）：读取侧是 `document-readers/` 下四个模块——jsoup、Markdown、pdf、tika，加上 `spring-ai-commons` 里的 `JsonReader` 与 `TextReader`；PDF 那个模块给了两个 reader，`PagePdfDocumentReader`（按页）与 `ParagraphPdfDocumentReader`（按段落，依赖 PDF 结构解析）；切分侧 `TokenTextSplitter` 继承 `TextSplitter`；写入侧除了 `VectorStore`，还有一个 `FileDocumentWriter`。

注意 `VectorStore extends DocumentWriter, VectorStoreRetriever`：Load 阶段与向量库是同一个接口，不需要适配器类。这是「用现成契约而不是发明契约」能落地的原因。

`Document` 本身：文本 + 元数据 + 可选媒体。元数据是 `Map<String, Object>`，键名常量集中在 `DocumentMetadata`；控制它怎么进提示词的是枚举 `MetadataMode`，四个值 `ALL` / `EMBED` / `INFERENCE`（推理时）/ `NONE`——写入时想要过滤用的字段，未必想原样发给模型，这一层就是留给这个落差的。

文档在 `== DocumentReaders` 一节开头挂了个 WARNING，值得抄进自家规范：

> Most `DocumentReader` and `DocumentWriter` implementations described below are constructed using a `Resource` or resource pattern and internally use a `DefaultResourceLoader` or variation of it to access storage. Care should be taken not to construct such instances using directly user supplied URLs, as there are security implications to this.

抽象给的是可替换性，服务端请求伪造（SSRF）风险留给调用方——这条边界 Spring 没有替你收走。

## 6. 决策四：VectorStore 与 SQL-like 过滤 DSL 的算子边界

### 6.1 接口与默认值

`VectorStoreRetriever` 是只读侧的函数式接口，只有一个 `similaritySearch(SearchRequest)`；`VectorStore` 继承它再加 `add(List<Document>)`、`delete(List<String>)`、`delete(Filter.Expression)` 和 `<T> Optional<T> getNativeClient()`。`add` 会替你算向量。自己提供向量的写入口 `upsert(List<EmbeddedDocument>)` 只在 `main`（2.1.0-SNAPSHOT）上，2.0.x 分支的接口里没有它，且它的默认实现直接抛 `UnsupportedOperationException`，文档写明各家存储自行启用——按 2.0.1 写代码时不要照抄。`SearchRequest` 的两个常量：`DEFAULT_TOP_K = 4`、`SIMILARITY_THRESHOLD_ACCEPT_ALL = 0.0`，即不显式设阈值就是全收。

### 6.2 「多少家」这件事有三种口径

介绍 Spring AI 时常见的一句是「支持 21+ 个向量库」。这个数字对齐三份清单会得到三个结果：

| 口径 | 数量 | 说明 |
| --- | --- | --- |
| 文档 `vectordbs.adoc` 实现清单 | 18 家 + `SimpleVectorStore` | 清单本身落后于模块树，缺 Couchbase、Coherence、Bedrock Knowledgebase |
| 仓库 `vector-stores/` 目录 | 22 个模块 | 其中 `spring-ai-redis-semantic-cache` 不是向量库实现，它给的是语义缓存（semantic cache）的 `SemanticCache` 与 `SemanticCacheAdvisor`，故 21 |
| 仓库 `starters/` 目录 | 21 个 `spring-ai-starter-vector-store-*` | 与模块不一一对应：Coherence 有模块无 starter，AWS OpenSearch 单列一个 starter |

vendor 侧的 `*FilterExpressionConverter` 也是 21 个（24 个同名文件去掉接口、`Abstract` 与调试用的 `Print` 实现）。数字相同只是巧合：Coherence 有 converter 却没 starter，`-opensearch` 与 `-aws-opensearch` 两个 starter 共用同一个 OpenSearch converter。`SimpleVectorStore` 在文档里挂着 WARNING：只用于测试，不要上生产。Azure Cosmos DB 那一行是外部模块，由 Azure 团队维护，不在本仓库。写文章或做选型时先说清口径，再报数字。

### 6.3 算子清单：两个来源交叉核对

过滤表达式的可信来源是语法文件和 AST 枚举，不是叙述性文档。`Filters.g4`（ANTLR）与 `Filter.ExpressionType` 一致支持：

```text
==  !=  >  >=  <  <=
AND | and | &&      OR | or | ||      NOT | not
IN | in             NIN | nin | NOT IN
IS NULL | is null   IS NOT NULL | is not null
```

`ExpressionType` 的值是 `AND, OR, EQ, NE, GT, GTE, LT, LTE, IN, NIN, NOT, ISNULL, ISNOTNULL`，**没有 LIKE**——模糊匹配在跨 vendor 抽象层不存在，需要它就得走各家原生能力。文档正文里的例子只有三条：

```text
"country == 'BG'"
"genre == 'drama' && year >= 2020"
"genre in ['comedy', 'documentary', 'drama']"
```

构造侧两种写法等价：字符串走 `FilterExpressionTextParser`，或者 `FilterExpressionBuilder` 造 `Filter.Expression` 抽象语法树，再由各 vendor 的 converter 翻成自家查询语言。运行时可换条件——`QuestionAnswerAdvisor.FILTER_EXPRESSION` 与 `VectorStoreDocumentRetriever.FILTER_EXPRESSION` 都是为此准备的上下文键：

```java
String content = this.chatClient.prompt()
    .user("Please answer my question XYZ")
    .advisors(a -> a.param(QuestionAnswerAdvisor.FILTER_EXPRESSION, "type == 'Spring'"))
    .call()
    .content();
```

多租户共享一张索引正是这个键的主用途，文档为此单列了一节 Partitioning a Shared Index，示例形态是 `group == '<groupId>'` 与等价的 `b.eq("group", groupId)`。要按时间窗口或权限裁剪，走同一入口。

至于为什么是字符串 DSL 而不是强类型 Criteria API：元数据键集合按文档来源而定，编译期强类型没有对象可绑。这是我的判断，不是文档结论；文档只称它是「一种新颖的 SQL-like 元数据过滤 API」。

## 7. 决策五：MCP 的五个 starter、一个协议属性和一次坐标迁移

模型上下文协议（MCP, Model Context Protocol）标准化模型与外部工具、资源的交互方式。Java 侧的协议实现是 MCP Java 软件开发包（SDK），分三层：客户端与服务端、会话、传输。Spring AI 在其上加两件东西：Boot starter 与注解。

### 7.1 starter 数量与传输选择

[mcp-overview.adoc](https://github.com/spring-projects/spring-ai/blob/main/spring-ai-docs/src/main/antora/modules/ROOT/pages/api/mcp/mcp-overview.adoc) 列出的 starter 是 5 个：

| starter | 角色 | 传输 |
| --- | --- | --- |
| `spring-ai-starter-mcp-client` | 客户端 | STDIO、Servlet-based Streamable-HTTP、Stateless Streamable-HTTP、SSE |
| `spring-ai-starter-mcp-client-webflux` | 客户端 | WebFlux 的 SSE / Streamable-HTTP / Stateless |
| `spring-ai-starter-mcp-server` | 服务端 | STDIO（`spring.ai.mcp.server.stdio=true`） |
| `spring-ai-starter-mcp-server-webmvc` | 服务端 | SSE / Streamable-HTTP / Stateless |
| `spring-ai-starter-mcp-server-webflux` | 服务端 | SSE / Streamable-HTTP / Stateless |

容易搞错的一点：HTTP 侧三种传输**不换 starter，换属性**。同一个 `spring-ai-starter-mcp-server-webmvc` 分别配 `spring.ai.mcp.server.protocol=SSE`（或留空）、`=STREAMABLE`、`=STATELESS` 就是三个服务器形态，WebFlux 侧同理。starter 划分的是运行模型（阻塞 servlet / 响应式 / STDIO 进程），不是协议版本。

自动配置模块确实是 6 个（根 `pom.xml` 的 `<modules>` 里可数）：

```text
auto-configurations/mcp/spring-ai-autoconfigure-mcp-client-common
auto-configurations/mcp/spring-ai-autoconfigure-mcp-client-httpclient
auto-configurations/mcp/spring-ai-autoconfigure-mcp-client-webflux
auto-configurations/mcp/spring-ai-autoconfigure-mcp-server-common
auto-configurations/mcp/spring-ai-autoconfigure-mcp-server-webflux
auto-configurations/mcp/spring-ai-autoconfigure-mcp-server-webmvc
```

「common + 各 flavor」是 Spring Boot 自动配置的常规切法：common 管连接与序列化属性，三个 flavor 管各自传输的 bean。

### 7.2 注解层

注解模块在 2.0 已经进了本仓库：`mcp/mcp-annotations`，包名 `org.springframework.ai.mcp.annotation`。按 annotations-overview 页的清单，服务端四个：`@McpTool`、`@McpResource`、`@McpPrompt`、`@McpComplete`；客户端七个：`@McpLogging`、`@McpSampling`、`@McpElicitation`、`@McpProgress`，外加 `@McpToolListChanged`、`@McpResourceListChanged`、`@McpPromptListChanged` 三个列表变更通知。

特殊参数一侧两页文档并不一致：mcp-overview 列的是 `McpSyncServerExchange`、`McpAsyncServerExchange`、`McpTransportContext`、`McpMeta`，annotations-overview 列的是 `McpSyncRequestContext`、`McpAsyncRequestContext`、`McpTransportContext`、`@McpProgressToken`、`McpMeta`、`MetaProvider`，并说明 exchange 只是 request context 上的一个 getter、且在无状态模式下取到 `null`。以 annotations-overview 为准。

服务端示例按文档写法（可直接编译，参数描述与必填都由注解给出）：

```java
@Component
public class CalculatorTools {

    @McpTool(name = "add", description = "Add two numbers together")
    public int add(
            @McpToolParam(description = "First number", required = true) int a,
            @McpToolParam(description = "Second number", required = true) int b) {
        return a + b;
    }
}
```

`@McpTool` 的属性：`name` 与 `description` 默认取方法名，`title` 面向 UI 展示，`generateOutputSchema` 默认 `false`，打开后为非 primitive 的返回值生成 JSON 输出模式（schema）。另有 `annotations` 与 `metaProvider` 两个属性。

`@McpTool` 与 Spring AI 自己的 `@Tool` 作用在不同协议层：`@Tool` 声明给 `ChatClient` 调用的本地工具，`@McpTool` 声明给 MCP 客户端的工具。2.0.1 把 `@McpTool` 的异常处理改成与 `@Tool` 对齐（upgrade-notes 条目 *MCP Tool Exception Handling Now Mirrors `@Tool`*）。两者语义相近，实现各自演进。

### 7.3 一次 Maven 坐标迁移

2.0 的破坏性变更里有一条容易漏。Spring 自己的 MCP 传输实现 `mcp-spring-webflux` 与 `mcp-spring-webmvc` 不再由 MCP Java SDK 发布，而是搬进 Spring AI，group id 从 `io.modelcontextprotocol.sdk` 变成 `org.springframework.ai`。直接引过这两个坐标的项目要改依赖与 import；走 `spring-ai-bom` 或 starter 的项目不用写版本，感知不到这件事。

## 8. 一次请求的流转：带两轮工具调用的问答

把前四节串起来。设链上有三个 advisor：默认 order 的记忆 advisor、默认 order 的检索 advisor，以及自动注册的工具 advisor。用户问「我们公司的报销上限是多少，帮我查一下今天的汇率」。

```text
1  ChatClient.prompt().user(...).call()
   DefaultChatClient 造出 ChatClientRequest（未展开 Prompt + 空上下文）
2  自动注册阶段（构建时）：链上没有别的 ToolAdvisor，也没有 order>+300 的记忆 advisor
   → ToolCallingAdvisor 以 +300 追加，内部会话历史保持开启
3  请求方向，order 从小到大：
   +200 记忆 advisor ── 读该 conversationId 的历史一次，拼进消息
   +300 工具 advisor  ── 循环入口
        0 检索 advisor ── 第 1 次相似度搜索，文档拼进用户消息
        LOWEST ChatModelCallAdvisor ── ChatModel.call()
        模型要求调用 lookup_rate(...) → ToolCallingManager 执行 → 回到本层再来一次
        0 检索 advisor ── 第 2 次相似度搜索（它真的又跑了一遍）
        模型给出无工具调用的回答 → 退出循环
4  响应方向，order 从大到小：
   检索 advisor（可改写响应）→ 工具 advisor → 记忆 advisor 只写回最终一问一答
```

从这张图能直接读出三件事，都能在源码或文档里对上：

1. **检索成本按迭代次数放大。** 依据是 tools.adoc 那句 `ToolCallingAdvisor is a recursive advisor — it re-enters the downstream advisor chain on each iteration of the loop`。检索 advisor 默认 order 是 `0`，大于 +300，即位于被重入的那段链里，所以模型每多要一次工具结果，它就多跑一次相似度搜索。要让它只跑一次，得把它的 order 设到工具 advisor 之前。动手前先用 `AdvisorObservationConvention` 打点，数清一次请求里检索被调了几次，再决定要不要动。
2. **工具往返默认不进长期存储。** 记忆 advisor 在 +200，只看到最终的用户消息与助手消息，中间的 `ToolResponseMessage` 不落库。
3. **同一份链上必须恰好一个 `ToolAdvisor`。** tools.adoc 的原话是 `DefaultChatClient enforces that exactly one ToolAdvisor is present in the chain`，源码 `validateSingleToolAdvisor()` 在数量大于 1 时抛错并列出名字与 order。想自己接管循环，先关掉自动注册（`spring.ai.chat.client.tool-calling.enabled=false` 或调用级 `AdvisorParams.toolCallingAdvisorAutoRegister(false)`）。

流式调用还有一条不变式：`adviseStream` 返回的是 `Flux<ChatClientResponse>`，工具调用参数可能散在多个块里，`ToolCallingAdvisor` 内部用 `ChatClientMessageAggregator` 聚合后再判断是否有工具调用——这就是 4.2 里那个选项被删掉的场景的正面解法。

## 9. 常见错误与排查

按现象查，右列是本文核实过的依据位置。

| 现象 | 先看什么 | 依据 |
| --- | --- | --- |
| 启动即失败，`ChatModel` 注入歧义 | 多个模型 bean 时显式 `@Primary`，或自定义 `ChatClient.Builder` | chatclient.adoc 多模型一节 |
| 指标/链路里看不到 ChatClient 与 advisor | 是否用了 `ChatClient.create(...)`——它绕过自动配置 builder | 同上，`observability ... are ignored` |
| 升级到 2.0 后编译不过 | `.internalToolExecutionEnabled(...)`、`ToolExecutionEligibilityPredicate`、`.streamToolCallResponses(...)` 三项已移除 | upgrade-notes 2.0.0 |
| 记忆里没有工具往返，也没有任何报错 | 存储是否支持完整消息集。JDBC / Cassandra / MongoDB 三家在保存时静默过滤掉工具消息，2.0 只有 InMemory / Redis / Neo4j 认 | chat-memory.adoc 三处 WARNING + tools.adoc Backend Compatibility |
| 手动建的 `ToolCallingAdvisor` 会重复写历史 | `.disableInternalConversationHistory()`；自动注册时框架已代劳 | DefaultChatClient 源码 + tools.adoc |
| 构建链时抛错，消息里列出两个 advisor 的名字与 order | 链上只能有一个 `ToolAdvisor`：删掉自定义的那个，或关掉自动注册 | `validateSingleToolAdvisor()` |
| 过滤表达式解析失败 | 是否写了 `like`（不支持）；字符串值必须带引号；`NIN` / `IS NOT NULL` 的大小写形式 | `Filters.g4` + `Filter.ExpressionType` |
| 会话窗口莫名变空 | `maxMessages` 小于一个完整回合时，非系统消息可能全被驱逐 | chat-memory.adoc 回合边界驱逐一节 |
| Redis 记忆存储库配置不生效 | 2.0.1 起前缀是 `spring.ai.chat.memory.repository.redis.*`，旧前缀靠委托存活 | upgrade-notes 2.0.1 |
| 工具太多，提示词膨胀 | `ToolSearchToolCallingAdvisor`，索引类型 `regex`（默认）/ `lucene` / `vector` | upgrade-notes 2.0.0 |
| 生产用了 `SimpleVectorStore` | 文档明确它只用于测试 | vectordbs.adoc WARNING |

一个默认值值得单独记：`spring.ai.retry` 下的 `maxAttempts` 默认是 10，退避初始 2 秒、倍数 5、上限 3 分钟。重试在模型层由 `RetryTemplate` 负责，不是链上的 advisor。想把重试挂进 advisor 链得自己实现，并且先想清楚它与工具循环谁在外层。

## 10. 五道自测题

1. 应用里有 `OpenAiChatModel` 与 `AnthropicChatModel` 两个 bean，你想为两家各配一个 `ChatClient`，同时保住指标与自定义 customizer。该注入什么？
2. 一次请求触发三轮工具调用，默认配置下相似度搜索跑了几次、历史里落下几条消息？说清 order 依据。
3. `country == 'UK' && name like '%redis%'` 这条过滤表达式会发生什么？换 `IS NOT NULL` 呢？
4. 需要保留完整工具往返给下一轮对话，改动清单是什么（提示：至少三处）。
5. 应用还在 Spring Boot 3.5。能不能上 Spring AI 2.0？依据是什么？

答案依次在第 3 节、第 8 节的流转图、第 6.3 节、第 4.4 节、第 2 节。每答完一题，顺手在本文列出的文档或源码位置复核一次。

## 11. 采用建议

按团队现状给顺序，不是按功能强弱。

- **Boot 3.5 的存量应用**：留在 1.1.x。第 2 节的版本口径是硬约束，2.0 那条线要连 Spring Boot 一起升，编排能力再香也不能当升级理由。
- **新起的应用，单一 provider、单轮调用、无检索无工具**：这套抽象暂时用不上。直接用 provider 的 SDK 更薄；引 `spring-ai-starter-model-*` 只为省一个 HTTP 客户端，收益抵不上多一层概念。
- **要接多家模型（做降级、A/B 或按用户选择）**：从第 3 节的 builder 规则起步。`ChatClient.Builder` 用满 prototype 语义，`ChatClientBuilderConfigurer` 走自定义路径，别用 `ChatClient.create(...)`。
- **要做 RAG**：先只上 `QuestionAnswerAdvisor`，把阈值、`topK`、过滤键三件事定下来（第 6 节）。需要改写查询再换 `RetrievalAugmentationAdvisor`。它的可插接位有六个：查询转换、查询扩展、检索、合并、后处理、查询增强，文档称这套设计受 arXiv:2407.21059 *Modular RAG* 启发。另有一条明确提醒，用查询转换时把构建器的温度调到 0.0 左右。
- **向量库选型**：以已跑着的数据栈优先，PostgreSQL 就用 pgvector，已有 Elasticsearch/Redis 就复用。21 个 starter 的意义是「以后能换」，不是「现在要挑最好的」。
- **MCP**：只做消费方就 `spring-ai-starter-mcp-client`；提供服务按容器类型选 `server-webmvc` 或 `server-webflux`，STDIO 进程用 `server`，HTTP 传输靠 `spring.ai.mcp.server.protocol` 切。已经在用 `mcp-spring-*` 的项目先做第 7.3 节的坐标迁移。

## 12. 这套抽象真正换来什么

五层各自的入口都在仓库里能数出来，它们共同的方向是：把「每个模型自己解释一遍」的事情，收成一个应用侧可测试的位置。

2.0 那批改动把这件事说得很具体。工具循环从每个 `ChatModel` 内部搬进 advisor 链之后，才可能出现「记忆 advisor 在循环内外两种语义」这种可讨论的设计，也才可能把 `streamToolCallResponses` 这种会损坏历史的选项整体删掉。抽象层没有消灭复杂度，只是换了位置。order 与工具循环的相对位置、`maxMessages` 与回合边界、元数据算子与 vendor 差异都还在，原本散在各家 provider 里的处理，现在收进你自己的应用配置一次。

判断标准也跟着变。要不要引入 Spring AI，看的不是它接了多少家模型，而是三件可核对的事：你的 Spring Boot 版本上不上得去（第 2 节）、你愿不愿意把复杂度收进 advisor 顺序（第 4 节）、你要不要跨 vendor 换向量库（第 6 节）。三件都否，用不上。三件都是，它挡住的正是你自己写会写散的那部分。

三处未定，别按今天的形状押长期：`ChatMemory` 计划在 2.1 被 `spring-ai-session` 取代（upgrade-notes 原话，2.1 尚未发布）；main 的 upgrade-notes 已为 2.1 列出消息分块（`MessagePart`）改造；MCP 的传输种类还在动。涉及这三处的接口，留薄一点。

## 13. 下一步读哪份代码

按这个顺序读，每一处都能验证本文的一个判断。路径相对仓库根目录，`main` 分支。

| 读什么 | 看哪一行 | 验证本文哪句 |
| --- | --- | --- |
| `spring-ai-client-chat/.../chat/client/DefaultChatClient.java` | `autoRegisterToolCallingAdvisor()`、`validateSingleToolAdvisor()` | 4.3 的自动注册与单工具 advisor 约束 |
| 同模块 `.../advisor/api/Advisor.java` | `DEFAULT_CHAT_MEMORY_PRECEDENCE_ORDER` 常量 | 4.1 那条 +200 边界 |
| 同模块 `.../advisor/ToolCallingAdvisor.java` | `DEFAULT_ORDER`、类注释、`ToolExecutionEligibilityChecker` 字段 | 4.1 与 4.2，以及 4.4 末尾那条注释噪音 |
| `spring-ai-commons/.../document/` | 三个 ETL 接口、`MetadataMode`、`DocumentMetadata` | 第 5 节的类型契约与元数据落差 |
| `spring-ai-rag/.../rag/advisor/RetrievalAugmentationAdvisor.java` | 构造器里那六个字段 | 第 11 节 RAG 一行的可插接位 |
| `spring-ai-vector-store/.../vectorstore/filter/Filter.java` 与同模块 `antlr4/.../Filters.g4` | `ExpressionType` 枚举、词法规则 | 6.3 的算子边界（含没有 `like`） |
| `mcp/mcp-annotations/.../mcp/annotation/` | 注解类清单 | 7.2 的服务端 / 客户端分类 |
| `spring-ai-docs/.../pages/upgrade-notes.adoc` | 2.0.0 与 2.0.1 两节 | 第 9 节排查表里那三行编译错误 |

核对方法上，这份仓库用 `git ls-tree` 与 `git show HEAD:<path>` 看结构最省力，浅克隆就够，不必拉全量历史。

## 14. 参考资料与核查方法

仓库与文档：

- 仓库：[spring-projects/spring-ai](https://github.com/spring-projects/spring-ai)（Apache-2.0）
- 概览与设计原则：[README.md](https://github.com/spring-projects/spring-ai/blob/main/README.md)、[index.adoc](https://github.com/spring-projects/spring-ai/blob/main/spring-ai-docs/src/main/antora/modules/ROOT/pages/index.adoc)
- 核心抽象：[chatclient.adoc](https://github.com/spring-projects/spring-ai/blob/main/spring-ai-docs/src/main/antora/modules/ROOT/pages/api/chatclient.adoc)、[advisors.adoc](https://github.com/spring-projects/spring-ai/blob/main/spring-ai-docs/src/main/antora/modules/ROOT/pages/api/advisors.adoc)、[tools.adoc](https://github.com/spring-projects/spring-ai/blob/main/spring-ai-docs/src/main/antora/modules/ROOT/pages/api/tools.adoc)、[etl-pipeline.adoc](https://github.com/spring-projects/spring-ai/blob/main/spring-ai-docs/src/main/antora/modules/ROOT/pages/api/etl-pipeline.adoc)、[retrieval-augmented-generation.adoc](https://github.com/spring-projects/spring-ai/blob/main/spring-ai-docs/src/main/antora/modules/ROOT/pages/api/retrieval-augmented-generation.adoc)、[chat-memory.adoc](https://github.com/spring-projects/spring-ai/blob/main/spring-ai-docs/src/main/antora/modules/ROOT/pages/api/chat-memory.adoc)
- 向量库与过滤：[vectordbs.adoc](https://github.com/spring-projects/spring-ai/blob/main/spring-ai-docs/src/main/antora/modules/ROOT/pages/api/vectordbs.adoc)、语法文件 [Filters.g4](https://github.com/spring-projects/spring-ai/blob/main/spring-ai-vector-store/src/main/antlr4/org/springframework/ai/vectorstore/filter/antlr4/Filters.g4)
- MCP：[mcp-overview.adoc](https://github.com/spring-projects/spring-ai/blob/main/spring-ai-docs/src/main/antora/modules/ROOT/pages/api/mcp/mcp-overview.adoc)、[mcp-annotations-server.adoc](https://github.com/spring-projects/spring-ai/blob/main/spring-ai-docs/src/main/antora/modules/ROOT/pages/api/mcp/mcp-annotations-server.adoc)、[mcp-annotations-overview.adoc](https://github.com/spring-projects/spring-ai/blob/main/spring-ai-docs/src/main/antora/modules/ROOT/pages/api/mcp/mcp-annotations-overview.adoc)
- 跨版本变更：[upgrade-notes.adoc](https://github.com/spring-projects/spring-ai/blob/main/spring-ai-docs/src/main/antora/modules/ROOT/pages/upgrade-notes.adoc)
- 关键源码：`spring-ai-client-chat/src/main/java/org/springframework/ai/chat/client/DefaultChatClient.java`、`.../advisor/ToolCallingAdvisor.java`、`.../advisor/api/Advisor.java`、`spring-ai-commons/src/main/java/org/springframework/ai/document/`（三个 ETL 接口与 `MetadataMode`）、`spring-ai-vector-store/src/main/java/org/springframework/ai/vectorstore/filter/Filter.java`

核查方式与失效条件：

- 事实核对时间 2026-09-19。`main` 用 blobless 克隆（`--filter=blob:none --no-checkout`）读提交树，`git ls-tree` 数模块、`git show HEAD:<path>` 取文档与源码原文；`2.0.x` / `1.1.x` 各做一次单分支浅克隆，除读 pom 外还抽核了 tools.adoc 与 chat-memory.adoc 在 2.0.x 上确有同一段落；文中凡只在 `main` 成立的东西都单独标了版本，目前只有 6.1 的 `upsert` 一条。已发布版本的 pom 走 `raw.githubusercontent.com/.../v<tag>/pom.xml`；发布序列与日期来自 Maven Central 的 `spring-ai-bom/maven-metadata.xml` 和 GitHub Releases API；stars 与许可证来自 GitHub API。
- 三类数字最易过期，复用时先重跑第 6.2 节与第 7.1 节的目录计数：向量库模块与 starter 清单、MCP starter 与注解清单。
- 第 4 节那条 order 边界（+200 / +300）是 2.0 的设计决定，若 2.1 真用 `spring-ai-session` 替换 `ChatMemory`，4.4 与第 9 节对应两行要整段重写。
