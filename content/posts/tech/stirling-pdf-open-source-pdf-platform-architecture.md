---
title: "Stirling-PDF 架构拆解：开源边界划在构建脚本里，AI Engine 却不归 MIT"
date: 2026-06-22T20:59:00+08:00
lastmod: "2026-09-20T14:20:00+08:00"
slug: "stirling-pdf-open-source-pdf-platform-architecture"
github_repo: "Stirling-Tools/Stirling-PDF"
source_key: "gh:Stirling-Tools/Stirling-PDF"
categories: ["技术笔记"]
tags: ["PDF", "Java", "FastAPI", "Monorepo", "架构分析"]
description: "对照 Stirling-Tools/Stirling-PDF main 分支提交 d6784b3 拆解这个 9.2 万星的 PDF 平台：开源与商业的分界线画在 Gradle flavor 和前端源码分层里，而不只是 LICENSE 文件里；Python AI Document Engine 走的是需要订阅的 User License；三种语言的类型由 Java 的一份 OpenAPI 规范生成，并有 CI 检查挡住漂移。"
draft: false
---

> **目标读者**：在选型上把 Stirling-PDF 当作「那个开源 PDF 工具」来评估的团队负责人；想参考多语言单仓库（monorepo）分层做法的后端与前端架构师；打算给已有 Java 服务接一层 Python 智能体服务的工程师。
> **核心问题**：它现在到底还是不是一个开源 PDF 工具箱，以及那条商业线与 AI 线是怎么切分的。
> **事实边界**：本文核对的是 `Stirling-Tools/Stirling-PDF` 的 `main` 分支提交 `d6784b3`（2026-09-18）、GitHub API（应用程序接口）在 2026-09-20 的读数，以及仓库内的 `LICENSE`、`README.md`、`ADDING_TOOLS.md`、`DATABASE.md`（数据库备份说明）、`docker/README.md`、`engine/.env`、`engine/src/stirling/documents/README.md`、八份 `.taskfiles/*.yml` 与前端的 `frontend/package.json`。目录与文件计数取自提交树，行内代码是从源文件摘出的原文（注释有删节处会标明）。发布版能力与 `main` 的差异没有逐项复核，涉及处会写明。

## 一句话判断

Stirling-PDF 已经不是一个「带网页界面的 Java PDF 工具」，但把它称作一个平台，前提是先看清两条切分线。

第一条是商业线。根 `LICENSE` 是 MIT，后面挂着一串目录例外；Python 的 AI Document Engine 正在这串例外里，它自带的 `engine/LICENSE` 是一份商业许可，生产使用需要有效的 User License 订阅。所以「完全开源」只对 `app/core` 和 `frontend/editor/src/core`（Java 后端与前端编辑器的核心目录）这些位置成立，对 `engine/` 不成立。

第二条是契约线。Java 后端导出 OpenAPI 规范，TypeScript 类型和 Python 模型都从这一份规范生成，并且两边各带一条会失败的检查任务。这条线决定了三模块为什么能各写各的，而不会在半年内散成三套互不相认的字段名。

两条线看完，选型问题的答案就分开了：自托管做 PDF 批处理，它仍然是这个赛道里最完整的开源选项；把 AI 文档理解算进成本，要算的是订阅，不是硬件。支撑这两条线跑动的还有第三条——五十多个工具是怎么长到 105 个端点而不互相踩脚的，这一条不决定价格，只决定维护成本。

## 项目坐标（2026-09-20 核对）

| 字段 | 值 |
|------|------|
| 仓库 | [`Stirling-Tools/Stirling-PDF`](https://github.com/Stirling-Tools/Stirling-PDF)，默认分支 `main`，最近推送 2026-09-19 |
| 核对提交 | `d6784b3`（2026-09-18），提交树 8,078 个路径 |
| 最近 release | `v2.14.3`（2026-08-06，"lots of bug fixes"） |
| 建仓 | 2023-01-27（早期归 `Frooodle` 所有） |
| 主语言 | Java、TypeScript，字节数只差七万 |
| Stars / Forks | 92,583 / 8,987 |
| 开放议题 | 628（`open_issues_count` 同时计入 issue 与拉取请求（pull request），未拆分） |
| License | 根目录 MIT；`app/proprietary/`（企业特性）、`app/saas/`（软件即服务形态）、`engine/` 及前端七个子目录各挂自己的许可 |
| 部署 | 单一容器镜像、分离前后端容器、桌面客户端、私有 API |

用 `GET /repos/.../compare/v2.14.3...d6784b3` 一比：`main` 领先 699 个提交、落后 19 个，状态 `diverged`。最新 release 里有 19 个提交没回到 `main`，`main` 上又多出 699 个。读这份仓库时，凡是「某个能力现在能不能用到」的判断，都要回到 tag 那一侧再确认一次。

## 把它拆成三条线看

前面那两条线之外还有第三条。仓库里同时存在三条线，各有自己的决定因素：商业线由许可目录与构建 flavor 决定，受版本发布影响；契约线由那份 OpenAPI 生成链决定，只要生成规则不动就基本稳定；工具线是端点与工具目录的持续累积，几乎每天都在变。三条线的交叉点不多：proprietary 侧确实消费 `SwaggerDoc.json`，因为 `@ToolIO` 与 `resourceWeight` 的取值会进规范；反过来，engine 不读许可证，前端也不从规范里生成类型之外的东西。先把三条线分开，再合起来看：

| 线 | 位置 | 它在解决什么 | 什么时候会咬你 |
|------|------|------|------|
| 商业线 | 根 `LICENSE` 的目录例外、`settings.gradle` 的 flavor、`frontend/editor/src/` 的分层 | 决定哪些代码能免费用、哪些要订阅 | Gradle 默认 flavor 是 proprietary，出厂 compose 却在运行时关掉附加特性 |
| 契约线 | Java 导出的 `SwaggerDoc.json`、`task frontend:tool-models`、`task engine:tool-models` | 决定 Java 加一个参数之后前端和 AI 层会不会立刻知道 | 它不在 `task check` 里，要单独跑 `task tool-models:check` 或等 CI |
| 工具线 | `controller/api/` 下 70 个 Controller、`hooks/tools/` 下 48 个目录、`shared/` 下 21 个共享文件 | 决定 105 个端点怎么长出来而不互相踩踏 | 教程文档落后于实现，新工具会照着旧写法写 |

下面按商业线、契约线、工具线的顺序走。engine 放在工具线之后，因为它是这三条线共同的新增消费者。

## 商业线：切分写在许可目录、构建 flavor 和运行时开关里

`settings.gradle` 提供三种 flavor：`core`、`proprietary`、`saas`，可由 `STIRLING_FLAVOR` 选择，也可以直接给 `DISABLE_ADDITIONAL_FEATURES` 和 `ENABLE_SAAS` 两个布尔值。三者的展开关系写得很直白：

```groovy
include 'stirling-pdf', 'common', 'proprietary'

project(':stirling-pdf').projectDir = file('app/core')
project(':common'      ).projectDir = file('app/common')
project(':proprietary' ).projectDir = file('app/proprietary')

if (enableSaas) {
    include 'saas'
    project(':saas').projectDir = file('app/saas')
}
```

这段里有两件事值得停一下。第一，Gradle 设置阶段无条件 `include` 了 `:proprietary`，它只是不被打进产物；第二，`ENABLE_SAAS=true` 且 `DISABLE_ADDITIONAL_FEATURES=true` 会直接抛 `GradleException`，注释写的是 SaaS 构建站在 proprietary 之上，不能单独存在。

真正把边界落到产物上的是 `app/core/build.gradle`：

```groovy
if (!gradle.ext.disableAdditional) {
    implementation project(':proprietary')
}
if (gradle.ext.enableSaas) {
    implementation project(':saas')
}
```

也就是说，以 `core` flavor 构建的产物确实不含 proprietary 的类，这一层不是靠运行时开关糊出来的。

AI 引擎的调用桥在 proprietary 侧：服务层 `app/proprietary/src/main/java/stirling/software/proprietary/service/` 下的 `AiEngineClient.java`、`AiEngineConfigSync.java`、`AiEngineEndpointResolver.java`，控制器 `controller/api/AiEngineController.java`，外加 `model/api/ai/` 下的进度模型。Java 侧那个「连接 AI Engine」的能力，因此不在 MIT 覆盖的目录里，`app/core` 下一个 `AiEngine*` 文件都搜不到。

四个 Gradle 子项目的体量（提交树文件数）：`app/core` 1,273、`app/proprietary` 1,140（其中 1,119 个是 `.java`）、`app/common` 376、`app/saas` 322。proprietary 与 core 几乎等大，这条边界的分量不轻。

前端用同一套思路，只是靠目录分层：`frontend/editor/src/` 下并列 `core`、`proprietary`、`saas`、`desktop`、`cloud`、`portal`、`portal-saas`、`prototypes` 八个入口，根 `LICENSE` 的例外列表逐个点名了其中七个。构建时选哪一层由优先级决定，`app/core/build.gradle` 的注释写明了顺序：`-PprototypesMode` 高于 `-PfrontendMode`，再高于 `enableSaas`、`disableAdditional`，兜底是 `proprietary`。

许可证侧的落点也一并说清：`app/proprietary/LICENSE`、`app/saas/LICENSE`、`engine/LICENSE` 是同一份「Stirling PDF User License」（`engine/LICENSE` 与 `app/proprietary/LICENSE` 逐字节相同，`app/saas/` 那份只差第 9 与第 48 行的引号字形），正文里那句约束是——生产使用、规模化使用或用于业务关键流程，需要有效的 User License 订阅；免费使用限于内部试用、评估与最小范围使用，且不得用于面向客户或商业场景。GitHub 侧把整个仓库标成 `Other`，就是这组混合许可的结果。

## 契约线：一份 OpenAPI 规范，三种语言消费

这是整个 monorepo 里最值得抄的一件事。

Java 后端导出 `SwaggerDoc.json`（由 `task backend:swagger` 生成，仓库里不提交该文件）。前端和 engine 各自跑一条代码生成任务，输入都是它：

```yaml
# .taskfiles/frontend.yml
tool-models:
  desc: "Generate tool API types from the Java OpenAPI spec"
  deps: [install, ":backend:swagger"]
  cmds:
    - npx tsx editor/scripts/generate-tool-api-types.mts --spec ../SwaggerDoc.json \
        --output editor/src/core/types/toolApiTypes.ts --io-output editor/src/core/types/toolIO.ts
```

```yaml
# .taskfiles/engine.yml
tool-models:
  desc: "Generate tool_models.py from Java OpenAPI spec (SwaggerDoc.json)"
  deps: [install, ":backend:swagger"]
  cmds:
    - uv run --locked --group engine --group engine-dev python scripts/generate_tool_models.py \
        --spec ../SwaggerDoc.json --output src/stirling/models/tool_models.py \
        --io-output src/stirling/models/tool_io.py
```

两边都配了 `tool-models:check`：engine 侧把同一个脚本换成 `--check` 跑，frontend 侧直接 `git diff --exit-code` 生成的两个文件。任何一条 CI 通过前都必须先重新生成，字段漂移不会靠人眼发现。

生成物的规模可以量出来。`editor/src/core/types/toolApiTypes.ts` 有 1,866 行，文件头三行注释写着「AUTO-GENERATED FILE. DO NOT EDIT」并指出规范来源。其中 `export const TOOL_ENDPOINTS` 列出 **105** 个端点；请求模型 107 个：88 个写成 `export interface`，19 个是 `export type X = Record<string, never>`（只收文件、没有参数的那批端点）。文件里另有 `ToolEndpoint`（105 条路径的联合类型）与 `ToolApiRequest`（`ToolApiParams[ToolEndpoint]` 的索引访问类型）两个类型，它们不是请求模型。按路径第三段分组：

| 分组 | 端点数 |
|------|------|
| `convert` | 29 |
| `misc` | 27 |
| `general` | 20 |
| `security` | 18 |
| `filter` | 6 |
| `integration` | 3 |
| `ai` | 1 |
| `form` | 1 |

这个类型系统还带运行时护栏：`isToolEndpoint()` 拿生成的端点清单构造一个 `Set` 做成员判断，让任意字符串收窄到 `ToolEndpoint` 类型，而不是靠 `as` 强转。engine 侧同样消费这份产物——`services/operation_shortlist.py` 从 `stirling.models` 导入 `OPERATIONS` 目录，把每个端点的模型描述和字段说明拼成检索文本，按嵌入相似度对请求排序。

## 工具线：70 个 Controller 与 48 个前端工具目录

### 后端按业务域切片

`app/core/src/main/java/stirling/software/SPDF/controller/` 下共 94 个 Java 文件，其中 74 个以 `Controller.java` 结尾：`api/` 递归 70 个，`web/` 4 个。`api/` 顶层是 21 个 Controller 加 6 个子目录（`converters`、`filters`、`form`、`misc`、`pipeline`、`security`），子目录里再放 49 个。

命名并不统一：`converters/` 下九个以 `Controller.java` 结尾，另外九个文件叫 `ConvertEmlToPDF.java`、`ConvertPdfJsonExceptionHandler.java` 这样按方向或职责命名的类。所以「数 Controller 文件」会得到比实际少的答案，端点数量才是要盯的指标（上一节的 105）。

端点本身是自描述的。`MergeController` 类上是另一个元注解 `@GeneralApi`，它把 `@RestController`、`@RequestMapping("/api/v1/general")` 与 OpenAPI 的 `@Tag` 折叠成一处声明；方法注解只补上剩余的 `/merge-pdfs`（合并）：

```java
    @AutoJobPostMapping(
            consumes = MediaType.MULTIPART_FORM_DATA_VALUE,
            value = "/merge-pdfs",
            resourceWeight = ResourceWeight.MEDIUM_WEIGHT)
    @StandardPdfResponse
    @ToolIO(produces = ToolFormat.PDF, arity = ToolArity.MISO)
```

`@AutoJobPostMapping` 定义在 `app/common`，把 `@RequestMapping(method = POST)` 与 `consumes` 的默认值折叠起来，另外挂出 `timeout`、`retryCount`（指数退避）、`trackProgress`、`queueable`、`resourceWeight` 五个属性，其中 `resourceWeight` 的默认值是 `Integer.MIN_VALUE` 这个哨兵值，用来区分「没声明」和「声明为 0」。注解注释写着：除特别说明外，这些属性只在异步执行时生效，而异步与否由客户端在请求上带 `?async=true` 决定。工具端点因此同时是作业端点：走不走队列由调用方在请求上决定，超时、重试与进度追踪是声明出来的，不是每个工具各自实现一遍。

`@ToolIO` 上的 `arity` 是另一个值得注意的设计。`ToolArity` 只有 `SISO / SIMO / MISO / MIMO` 四个值，读作单/多输入、单/多输出；枚举的注释专门解释了 ZIP 的位置——多输出端点把结果打包成一个 zip 返回、由调用方拆开，所以 `split-pages` 记作 `produces = PDF, arity = SIMO`，而不是发明一个叫 ZIP-of-PDF 的格式；只有交付物本身就是归档的端点才声明 `ToolFormat.ZIP` 并用单输出的 arity。一条注释挡住了一个容易长歪的枚举分支。

`GeneralApi.java` 的注释里还带着 `@Tag` 的分组描述，`General` 那一组写的是「页级 PDF 编辑：拆分、合并、旋转、裁边、重排、缩放」。类上挂哪个分组注解，OpenAPI 文档里就长成哪一节，前端的分类不是前端自己定的。合并的实现也值得一看：`MergeController` 直接 import `stirling.software.jpdfium.PdfMerge`，走 JPDFium 原生库。这解释了桌面端那份平台矩阵为什么是一等约束——原生库没有对应平台的产物，工具在那个平台上就跑不起来。

`controller/web/` 下的四个 Controller 职责各异：

- `ReactRoutingController` —— 单页应用（SPA）的路由转发，机制见下
- `MetricsController` —— 注入 Micrometer 的 `MeterRegistry`，12 个 `@GetMapping`：`/status`、`/health`、`/uptime`（正常运行时间）、`/wau`，加上 `/load`、`/load/unique`、`/load/all`、`/load/all/unique` 与 `/requests` 的同族四条，整组受 `applicationProperties.getMetrics().isEnabled()` 控制
- `RobotsController` —— 按 `system.googlevisibility` 动态返回 allow-all 或 disallow-all 的 `robots.txt`，用于内部部署不被索引
- `SignatureImageController` —— 挂在 `/api/v1/general` 下取已保存的签名图

`MetricsController` 上只有一个 `@InfoApi`。它是 `app/common` 下的元注解，把 `@RestController`、`@RequestMapping("/api/v1/info")` 和 OpenAPI 的 `@Tag(name = "Info")` 折叠成一处声明，所以上面那组端点的完整路径是 `/api/v1/info/status` 这样——容器健康检查打的就是它。观测出口的分层也值得记一句：`spring-boot-starter-actuator` 在根 `build.gradle` 的 `subprojects` 块里对所有子项目生效，而 `micrometer-registry-prometheus` 只在 `app/proprietary/build.gradle` 里以 `api` 声明。以 `core` flavor 构建时，Prometheus 抓取格式随着 proprietary 一起被排除，留下的只有 `MetricsController` 这组 JSON 端点。

同目录还有 `UploadLimitService.java`，名字里没有 Controller，它是服务不是控制器。

`ReactRoutingController` 值得一说，因为它是三个前端分层共用的入口。它的 `servePrerenderedOrIndex()` 把请求解析成预渲染页或索引页：先给 `/` 与 `/index.html` 一个显式处理器——若 SaaS 落地页存在，只替换根页，其余入口照常；再给 `/auth/callback`、`/share/{token}`（分享令牌）、`/mobile-scanner`、`/mobile-sign`、`/auth/callback/tauri` 各一条映射。剩下的靠两条正则路径变量处理，前缀里排除了 `api`、`static`、`pipeline`、`pdfjs`、`vendor`、`assets`、`locales` 等一长串保留段。

问题在于 Spring 的路径变量不跨越 `/`，正则只能覆盖一段和两段的路径，于是 `/processor/pipelines/new` 这类深链直连会 404。仓库的解决办法是再注册一个 `RouterFunctionMapping` Bean 做兜底，并把它排在 `LOWEST_PRECEDENCE - 2`——注释解释了为什么不能是一个裸 Bean：`RouterFunctionMapping` 默认 order 为 `-1`，在注解控制器之前，会把所有不在排除列表里的后端路由（`/actuator`、`/v1/api-docs`、`/error`）挡掉。兜底只能放在注解控制器之后、资源链之前这一个位置上。

桌面模式在这个类里也有痕迹：`isDesktopMode()` 读系统属性 `STIRLING_PDF_TAURI_MODE`。

### 前端：复杂度没有消失，只是搬进了 shared/

`ADDING_TOOLS.md`（293 行）给新工具规定的落点是三个位置：

```text
frontend/editor/src/hooks/tools/[toolName]/
  ├── use[ToolName]Parameters.ts     # Parameter definitions and validation
  └── use[ToolName]Operation.ts      # Tool operation logic using useToolOperation

frontend/editor/src/components/tools/[toolName]/
  └── [ToolName]Settings.tsx         # Settings UI component (if needed)

frontend/editor/src/tools/
  └── [ToolName].tsx                 # Main tool component
```

实际路径要再深一层：这些文件都在 `frontend/editor/src/core/` 下面，文档省略了 `core`。注册也不是自动的，新工具还要改 `core/data/useTranslatedToolRegistry.tsx`。这个文件 1,580 行，`useTranslatedToolCatalog()` 在里面先展开一个 `allTools: ToolRegistry`，把 `proprietaryTools` 与 `prototypeTools` 两组注册表并进同一个对象（注释说明原型工具只在 `prototypes` 构建里非空），再逐项声明图标、名称、组件、分类、`maxFiles`、`endpoints`、`operationConfig` 与可选的设置组件。开源侧新增一个工具，落点就是这张清单里的一处展开。

`core/hooks/tools/` 下是 48 个工具目录共 150 个文件，平均每个工具三个文件；`merge`（合并）是四个（`useMergeOperation.ts`、`useMergeParameters.ts` 各带一个测试），`split` 是三个。目录之外还有 `shared/` 与 3 个平铺的钩子（hook）文件。「加工具 = 加文件」这句话大致成立，代价在另一侧：`shared/` 是 21 个文件、4,394 行，其中 `useToolOperation.ts` 单文件 917 行、33 条 import，`toolOperationTypes.ts` 401 行，`toolAutomation.ts` 550 行。抽象没有把复杂度消掉，它把复杂度从 48 个调用点收敛到 21 个共享文件里。这是同一件事的两面，只讲前面一半会误导打算照抄的人。

三个共享 Hook 的名字是准确的：`useBaseTool.ts`（217 行）、`useToolOperation.ts`、`useBaseParameters.ts`（57 行），加上 `components/tools/shared/createToolFlow.tsx`（207 行）。`useBaseTool` 的返回契约能看出它到底管了多少事：

```typescript
interface BaseToolReturn<TParams, TParamsHook extends BaseParametersHook<TParams>> {
  selectedFiles: StirlingFile[];
  params: TParamsHook;
  operation: ToolOperationHook<TParams>;
  endpointEnabled: boolean | null;
  endpointLoading: boolean;
  handleExecute: () => Promise<void>;
  handleThumbnailClick: (file: File) => void;
  handleSettingsReset: () => void;
  handleUndo: () => Promise<void>;
  hasFiles: boolean;
  hasResults: boolean;
  settingsCollapsed: boolean;
}
```

`endpointEnabled` 说明每个端点可以被单独关停，这对应企业部署里「只开放部分工具」的诉求；`handleUndo` 说明结果页带回退，不是单向提交。

配置文件的样子，以 `merge` 的真实实现为准（注释有删节）：

```typescript
const ENDPOINT = "/api/v1/general/merge-pdfs" satisfies ToolEndpoint;

export const mergeToApiParams = (parameters: MergeParameters): MergeApiParams => ({
  // The UI owns file ordering, so the backend is always told to keep it.
  sortType: "orderProvided",
  removeCertSign: parameters.removeDigitalSignature ?? false,
  generateToc: parameters.generateTableOfContents ?? false,
});

export const mergeOperationConfig = defineMultiFileTool({
  buildFormData,
  toApiParams: mergeToApiParams,
  fromApiParams: mergeFromApiParams,
  operationType: "merge",
  endpoint: ENDPOINT,
  filePrefix: "merged_",
  defaultParameters,
});
```

三个细节：`satisfies ToolEndpoint` 让端点字符串必须命中生成清单，写错路径在类型阶段就失败；`toApiParams` / `fromApiParams` 成对存在，UI 参数与后端字段之间是双向映射，这让自动化流程能从一次真实请求里还原出参数；`sortType` 恒为 `orderProvided`，注释给出的理由是文件顺序由 UI 掌管。

这里有一个对读者更有用的发现：`ADDING_TOOLS.md` 写的还是 `toolType: ToolType.singleFile` 加一个裸对象 config，也没有 `toApiParams` / `fromApiParams`；文档末尾自己承认「部分现有工具（比如 AddPassword、Compress）使用手动管理 hook 的旧模式」。仓库文档描述的是上一代写法，`merge` 用的是 `defineMultiFileTool`。照文档抄会写出能跑但落后的代码，落笔前应以 `merge`、`split` 这类已迁移工具的实际文件为准。

## `engine/`：一个许可在先的 Python 服务

`engine/pyproject.toml` 的 `[project]` 段里 `version = "0.1.0"`，而 `dependencies = []` 是空的——所有依赖挂在 `[dependency-groups]` 下，配合 `[tool.uv]` 的 `default-groups = []`，安装必须显式点名分组。它的 Dockerfile 里就是这一句：`uv sync --frozen --no-dev --no-install-project --group engine`。`task engine:install` 同理，漏掉 `--group engine` 就装不到运行依赖。

`requires-python = ">=3.13,<3.14"`，上界也钉住了。`engine` 组的实际内容：

```toml
engine = [
    "cryptography>=50.0.0",
    "fastapi>=0.141.1",
    "opentelemetry-sdk>=1.39.1",
    "pgvector>=0.5.0",
    "posthog>=7.38.3",
    "psycopg[binary,pool]>=3.3.4",
    "pydantic>=2.13.5",
    # <2 cap: 1.99.0 patches CVE-2026-46678; 2.0 is an untested major migration.
    # Explicit extras: the `pydantic-ai` meta-package pulls all 20 providers (~230MB).
    # No `voyageai` extra either; stirling.documents.voyage speaks its API directly.
    "pydantic-ai-slim[anthropic,openai]>=1.107.2,<2.0.0",
    "pydantic-settings>=2.15.0",
    "python-dotenv>=1.2.3",
    "sqlite-vec>=0.1.9",
    "uvicorn>=0.52.3",
]
```

三条注释是这个依赖表里最有价值的部分：`pydantic-ai` 元包会拉进全部 20 家 provider 约 230 MB，所以只装 slim 加显式 extras；`<2.0.0` 的上界是为了一个 CVE 补丁版本；Voyage 不用官方 extra，因为 `stirling.documents.voyage` 自己讲那套接口。除 `engine` 外还有五个非运行时组：`engine-dev`（`datamodel-code-generator[ruff]==0.64.0`、`pyright`、`pytest`、`ruff`、`anyio`、`referencing`）、`cucumber`（`behave` 加 `pdf2image`、`reportlab` 等测试夹具）、`tools`（仓库脚本与 CI 共用，含 `openai`、`weasyprint`、`deep-translator`）、`updater-signatures`（只有 `cryptography`，用于校验发布签名），以及把工具版本钉死供提交前检查用的 `pre-commit` 组。`ruff==0.15.5` 同时出现在 `engine-dev` 和 `pre-commit` 里，两处各自生效，改一处不会带动另一处。

代码结构是 src layout，`engine/src/stirling/` 下七个子包加一个负责日志记录的 `logging.py`，按 Python 文件数看：

| 子包 | `.py` 文件数 | 内容 |
|------|------|------|
| `agents/` | 35 | pydantic-ai 智能体与共享推理骨架 |
| `api/` | 19 | FastAPI 应用、中间件、鉴权与 `routes/` |
| `contracts/` | 19 | 请求与响应的数据契约 |
| `documents/` | 9 | 分块、嵌入、两种向量库与检索增强生成（RAG）能力 |
| `services/` | 7 | 运行时、进度、语言、操作排序 |
| `models/` | 5 | 含生成物 `tool_models.py`、`tool_io.py` |
| `config/` | 3 | `AppSettings` 与配置缓存 |

`agents/` 里能看到这个服务真正的用途不是聊天。它的子模块按「审文件」的动作划分，而不是按问答划分：

- `contradiction/` —— 前后矛盾检测，含 `detector.py`、`intent.py` 与一个 `validators/ledger.py`
- `ledger/` —— 台账核对，`validators/` 下分 `arithmetic.py`、`figures.py`、`formula.py` 与 `_parsing.py`
- `pdf_comment/`、`pdf_create/`、`pdf_review.py`、`pdf_questions.py` —— 批注、生成、审阅与问答四类能力
- `document_classifier.py`、`orchestrator.py` —— 先分类再调度
- `shared/` —— `chunked_mapper.py`、`chunked_reasoner.py`、`whole_doc_reader.py`，即分片与整本两种读取骨架

算术、图表、公式三类校验器并列出现，这是「审文件」而不是「问文件」的证据。

`documents/README.md` 是仓库里对 RAG 层最完整的一手说明：一个 `collection`（以文件 id 命名）下同时存两种表示——用于检索的向量分块，和按页序保留、用于整本阅读的原文；`ingest()` 一次写入两者，`delete_collection()` 一次删掉两者。给智能体加检索只需要把 `runtime.rag_capability` 的 `instructions` 和 `toolset` 传给 `Agent`，智能体就自动获得一个 `search_knowledge` 工具；`collections=[...]` 可以把检索限定到某几个桶。`sqlite-vec` 与 `pgvector` 两个后端实现同一个 `DocumentStore` 接口。README 末尾的端点表列了两条，`routes/documents.py`（`prefix="/api/v1/documents"`）实际注册三条：`POST` 空路径做替换式写入、`DELETE /by-id/{document_id}` 与 `DELETE /by-owner`。文档里既没有 `by-id` 这一段，也漏了按属主清理的那条。

`engine/.env` 是提交的，里面是全部默认值（键名取自原文）：嵌入模型 `STIRLING_RAG_EMBEDDING_MODEL=voyageai:voyage-4`，分块 `512` / 重叠 `64` / `TOP_K=20`，单次运行内 `search_knowledge` 上限 `STIRLING_RAG_MAX_SEARCHES=5`（超限后工具从 toolset 里移除，逼模型用已取到的内容作答）；`STIRLING_PLANNER_SHORTLIST_SIZE=20`，注释的理由是完整目录会撑爆本地模型的上下文，设 `0` 关闭排序；分块推理器每片 `16000` 字符、并发 `10`、单片超时 `60` 秒、笔记预算 `250000` 字符；模型侧 `STIRLING_MODEL_MAX_CONCURRENCY=32` 是进程级共享上限。每请求的分片并发乘上并发请求数都要落在这条线内，这就是注释给出的解释。

两处对不上，值得记下来：`documents/README.md` 的配置片段写 `STIRLING_RAG_TOP_K=5`，同仓库的 `.env` 是 `20`；根 `README.md` 里「50+ PDF 工具」是产品口径，与生成清单的 105 个端点、`convert` 组下 29 个转换方向都不是同一个数——三个数字量的是三件事。

### 边界：哪些还是空的

`ExecutionPlanningAgent` 是空的：

```python
    async def next_action(self, request: AgentExecutionRequest) -> NextExecutionAction:
        return CannotContinueExecutionAction(
            reason=f"Execution planning is not implemented yet for step {request.current_step_index}."
        )
```

`contracts/` 里有 `AgentExecutionRequest`、`NextExecutionAction` 这一整套类型，`api/routes/execution.py` 也有路由，但规划器无条件返回「不能继续」。所以「agent 自动串起多个 PDF 工具」这条链路目前是接口先就位、实现未到位，读代码时别把类型定义当成已有能力。

`0.1.0` 加上 `execution` 未实现，engine 的位置就是它写的样子：一个能读文档、能检索、能出审查意见的服务，不是一个能自动编排工具序列的服务。

## 一次任务如何流过这套结构

**上传两份合同、合并、下载。** 浏览器里的 `merge` 工具从 `useTranslatedToolRegistry.tsx` 取到自己的条目，`useBaseTool('merge', useMergeParameters, useMergeOperation, props)` 把参数、文件与端点可用性这三类状态收进一个统一的返回值，工具组件自己不再持有状态属性；用户点执行，`useToolOperation` 走 `defineMultiFileTool` 的 `buildFormData`，把 `mergeToApiParams` 的结果和 `clientFileIds` 一起塞进 `FormData`，`fetch` 到 `/api/v1/general/merge-pdfs`。Spring 侧 `MergeController` 接住，交给 PDF 处理服务，产物回传，结果页显示缩略图并留下 `handleUndo`。整条链上没有一处需要新写的胶水代码，因为端点和字段名两边都来自同一份生成类型。

**问一份已索引文档「第 12 条违约责任和附件里的金额有没有冲突」。** 这条请求最终落在 engine 自己的路由上，而不是 Java 那 105 个工具端点上，例如 `POST /api/v1/pdf/questions`（`APIRouter(prefix="/api/v1/pdf/questions")` 在 `routes/pdf_questions.py` 里声明）。engine 的 `AppRuntime` 取出该文档的 `collection`，`RagCapability` 提供 `search_knowledge`，`whole_doc_reader` 或 `chunked_reasoner` 按页数决定走整本读还是分片读；`contradiction` 与 `ledger` 那组校验器负责把「金额对不上」变成可复核的判断，而不是模型的一段话。模型并发受 `STIRLING_MODEL_MAX_CONCURRENCY=32` 约束，检索次数受 `STIRLING_RAG_MAX_SEARCHES=5` 约束，两个上限都会在结果里留下痕迹。

**这条链的前提是 Java 先把它接通。** 部署时的顺序是：起 engine（`task engine:dev`，默认 5001），再起 Java 并给出 `AIENGINE_URL` 与 `AIENGINE_ENABLED=true`。Java 侧由 `AiEngineConfigSync` 把管理端配置的模型推给 engine 的 `POST /api/v1/config`，它的类注释写明「启动时与每次保存之后各推一次，非阻塞、尽力而为」，内部是 `MAX_ATTEMPTS = 5`、间隔 3 秒；关闭它的是 Java 侧的 `aiEngine.pushConfigToEngine`，engine 侧对应 `STIRLING_ALLOW_CONFIG_PUSH=false`，用于让环境成为唯一真源。`STIRLING_REQUIRE_USER_ID` 默认 `false`（自托管没有用户身份），多租户部署必须置 `true`。

## 数字怎么读

GitHub 的语言统计量的是各语言源文件的字节数，不做归属拆分。当前的读数：

| 语言 | 字节数 |
|------|------|
| Java | 17,883,678 |
| TypeScript | 17,810,639 |
| Python | 1,420,712 |
| CSS | 920,882 |
| Shell | 288,664 |
| JavaScript | 246,038 |
| Gherkin | 201,435 |
| Rust | 188,162 |
| HTML | 110,140 |
| Dockerfile | 56,333 |

三个读法上的提醒。Java 与 TypeScript 只差约 7.3 万字节，但这个「几乎相等」里含 1,866 行自动生成的 `toolApiTypes.ts` 与 `core/generated/docsManifest.json`，不能读成「前端手写量等于后端」。Python 那 140 万字节主体在 `engine/`，但仓库脚本与 CI 里用到的 Python 也记在同一行——`pyproject.toml` 的 `tools` 组注释写明它是「repository scripts and CI workflows」共用的工具库。反过来，`app/proprietary` 的 1,140 个文件是记在 Java 名下的，把 Java 字节数当成开源后端的规模会高估。

剩下两行也有归属：Gherkin 20 万字节说明行为驱动测试是这个仓库的一等公民，`.taskfiles/cucumber.yml` 指向 `testing/cucumber`，engine 的 `cucumber` 依赖组里装的是 `behave`。Rust 那 18 万字节则是 Tauri 桌面壳，`frontend/editor/src-tauri/` 下 `Cargo.toml`、`build.rs`、`capabilities/default.json` 齐全。

仓库里能直接对上口径的计数，比字节数好用得多：

| 口径 | 数值 | 来源 |
|------|------|------|
| 前端可见端点 | 105 | `toolApiTypes.ts` 的 `TOOL_ENDPOINTS` |
| 生成的请求模型 | 107（88 interface + 19 类型别名） | 同文件 |
| `*Controller.java` | 74（api 70 + web 4） | 提交树 |
| 前端工具目录 | 48 | `core/hooks/tools/` |
| 共享机制文件 | 21 / 4,394 行 | `core/hooks/tools/shared/` |
| 支持界面语言 | 41 | `core/i18n/languages.ts` 的 `supportedLanguages` |
| 界面语言（官方口径） | 40+ | `README.md` |
| PDF 工具（官方口径） | 50+ | `README.md` |

`languages.ts` 里还有两条容易被跳过的规定：`rtlLanguages = ["ar-AR", "fa-IR"]` 驱动 `document.dir`，语言选择优先级是一个有数值大小的枚举，`Fallback < Browser < ServerDefault < User`——用户显式选过的语言不被浏览器探测覆盖。

## 构建与部署：Task 是唯一的入口

顶层 `Taskfile.yml` 用 `includes` 引入 8 个子任务文件：`backend`、`frontend`、`engine`、`docker`、`desktop`、`e2e`、`cucumber`（指向 `testing/cucumber`）、`pre-commit`。它同时是开发环境的编排器和跨平台的抽象层。

`task dev` 只起两个进程（后端与编辑器）。`vars` 里按 `OS` 挑的是脚本名——`find-free-port.ps1` 还是 `find-free-port.sh`——而调用点固定传入 `8080 5173` 两个首选端口；脚本的语义是逐个参数判断，空闲就用该端口、被占则在 20000-49999 里另取一个，并保证同一次输出互不重复。前端拿到 `BACKEND_URL=http://localhost:<实际端口>`。三个进程的版本是 `task dev:all`，它转发到内部任务 `dev:_all`，那里才加 `engine:dev`，端口表是 `8080 5173 5001`，并给后端注入 `AIENGINE_URL` 与 `AIENGINE_ENABLED=true`。`task dev:portal` 的描述直接写着「the portal is an admin route at /portal」，附带 `SECURITY_ENABLELOGIN=true`；`task dev:saas` 只是把 `dev:_all` 的前后端换成 `saas`，端口表仍是三端口那一套；真正把两套实例并起来的是 `linked:dev` 与 `linked:staging`，它们走内部任务 `linked:_all`，端口表扩到 `8081 5174 8080 5173`。

这类文件里最有信息量的是为跨平台写的注释。`linked:_ready` 那个探测四个端口是否就绪的等待循环里，两行说明分别指出：不能用 `-o /dev/null`，因为 Windows 的 `curl.exe` 会把它当成真实路径并以 23 退出；以及 `sleep` 是二进制不是内建命令、Windows 上没有，所以那里按 `OS` 换成 `Start-Sleep`。写跨平台脚本时值得回来抄这两处判断。

桌面端 `.taskfiles/desktop.yml` 里有三条硬约束，每条都带原因：

- `REQUIRED_JAVA = "25"`，注释要求与 `build.gradle` 的 `modernJavaVersion` 同步，理由是应用 JAR 按此编译，装了更旧的运行时会以 `UnsupportedClassVersionError` 启动失败，并有 `jlink:verify` 把关
- `JLINK_MODULES` 里显式包含 `jdk.dynalink`，因为 VeraPDF 做 PDF/A 校验要用这个命名空间下的类，缺了会在 `get-info-on-pdf` 与 `verify-pdf` 运行到一半时抛 `NoClassDefFoundError: jdk/dynalink/Namespace`
- `JPDFIUM_PLATFORMS` 按 `{{OS}}-{{ARCH}}` 映射，`windows-arm64` 映射到 `none`，注释写明还没有发布对应的 JPDFium 原生库；`frontend/package.json` 里没有任何 Electron 依赖，桌面侧是 `@tauri-apps/api` 加 `dialog`、`fs`、`http`、`notification`、`shell` 五个官方插件，构建工具是 `@tauri-apps/cli`（命令行工具）

Docker 侧有三档镜像：`ultra-lite`、标准、`fat`，`docker/README.md` 给出各档内存建议 2 G / 4 G / 6 G。默认那档走 `docker/embedded/Dockerfile`——Java 与前端打进同一镜像（`-PbuildWithFrontend=true`），构建阶段是 `gradle:9.7.1-jdk25` 且 `ARG STIRLING_FLAVOR=proprietary`，用 Spring Boot layertools 把依赖拆成层以复用缓存，并把一个表单检测模型烘进 `/opt/stirling/preinstalled-models`。但 `docker/compose/docker-compose.yml` 在运行时显式设了 `DISABLE_ADDITIONAL_FEATURES: "true"`。镜像按 proprietary 构建、实例却被要求关掉附加特性，这两个默认值不是一回事。出厂那台容器到底开放了哪些能力，取决于这个变量的实际值，而不是仓库的默认 flavor——查这一层的时候别只看 `settings.gradle`。engine 有独立的 `docker/engine/Dockerfile`，两段式构建、基础镜像按 sha256 摘要钉死；标准 compose 里只有 `stirling-pdf` 一个服务，健康检查打 `/api/v1/info/status`，`docker:up`、`up:fat`、`up:ultra-lite` 各自指向一个 compose 文件。

一处文档滞后：`docker/README.md` 的目录结构块只列了 `backend/`、`frontend/`、`compose/` 三项，实际 `docker/` 下有七个子目录，另四个是 `base/`、`embedded/`、`engine/`、`unoserver/`。同理，提交树的 8,078 个路径里没有 Helm 用的 `Chart.yaml`，`helm` 这个词一次都没出现（含 `chart` 的 11 个路径全是 React 图表组件），`README.md` 对 Kubernetes 只给了一句「见文档站」。这两项若要在部署方案里依赖，得先去文档站确认，不要按本仓库推断。

## 排查：六类会真实遇到的故障

按现象分，不是按模块分。这六类是这类平台部署里最常见的故障形状，且前五条在仓库里都能查到作者写下的原因，第六条属于许可与文档口径。

1. **`task engine:install` 之后 `import fastapi` 失败。** 十有八九是依赖组没被选中：`[tool.uv]` 的 `default-groups = []` 使 `uv sync` 不带任何组，必须 `--group engine`，跑测试再加 `--group engine-dev`。
2. **桌面版启动即 `UnsupportedClassVersionError`，或 `verify-pdf` 跑到一半崩。** 前者是捆绑 JRE 低于 25，检查 `jlink:verify` 是否被跳过；后者是 `jdk.dynalink` 没进 `JLINK_MODULES`。两个原因都在 `desktop.yml` 的注释里，属于「模块裁剪把可选依赖剪掉了」这一类。
3. **`/processor/pipelines/new` 直连 404，但从首页点进去正常。** 深链兜底依赖那个 `LOWEST_PRECEDENCE - 2` 的 `RouterFunctionMapping`。如果为了简化把它改成一个裸 `RouterFunction` Bean，order 回到默认的 `-1`，症状会反转：深链正常，而 `/actuator`、`/error` 这类后端路由被 SPA 吞掉。
4. **AI 功能「偶尔卡住不返回」，engine 日志里有一行 Request 却没有对应 Response。** `services/runtime.py` 把 Anthropic 的 httpx 连接池 keepalive 关掉了，原因写得很具体：Cloudflare 前置会静默关闭空闲连接，复用旧连接时请求体被丢进黑洞，一直挂到分片推理自己的超时才醒。代价是每次多约 150 ms 握手。诊断同类问题时把 `STIRLING_HTTP_DEBUG=true` 打开，用有没有成对的 Request / Response 行判断卡在哪一层。
5. **升级依赖时撞上用户数据库读不出来。** `app/proprietary/build.gradle` 里那一行 `runtimeOnly 'com.h2database:h2:2.3.232'` 后面跟着一条禁止升级的注释：2.4.x 换了文件格式，会让已有用户库打不开。这是升级类 PR 最容易被漏掉的一条约束，也是一次性故障里最贵的一种。
6. **功能在 `main` 上见过，装出来没有。** 先分清读的是仓库还是发布物：`main` 领先 `v2.14.3` 共 699 个提交，`engine/` 又在商业许可目录下。想确认某个能力在自己的实例里到底有没有，顺序是：先查它在不在 `app/core` 或 `core/` 分层里，再查 `DISABLE_ADDITIONAL_FEATURES` 的实际取值，最后才看版本。

## 适用边界

- **当作 PDF 阅读器**：不行。它没有翻页、批注、笔记这一层界面，做的是修改、转换与提取。
- **当作文档管理系统**：不行。没有版本控制与协作评论，权限侧只有单点登录（SSO）与审计。
- **当作全开源栈**：要看 flavor 与运行时开关。Gradle 的默认 flavor 含商业许可代码，`engine/` 与 `app/proprietary/`、`app/saas/` 生产使用都需要订阅；以 `core` flavor 构建的产物不含 proprietary 模块，也就没有 AI Engine 的调用桥。出厂 compose 把 `DISABLE_ADDITIONAL_FEATURES` 设为 `true`，镜像本身却按 proprietary 构建，两层要分开确认。
- **当作可用的 AI 编排**：目前只有文档问答与审查这一半，`ExecutionPlanningAgent` 尚返回未实现。
- **Windows ARM64 桌面**：官方桌面构建在该平台映射到 `none`，缺 JPDFium 原生库。

## 五个自测问题

答不出来的，说明下面那节还没读进去。

1. 同一份 `SwaggerDoc.json` 被谁消费两次，两边各生成什么文件？
2. `tool-models:check` 与 `tool-models` 的区别是什么，为什么它需要 `git diff --exit-code`？
3. 以 `core` flavor 构建时，`AiEngineClient` 会不会进入产物？依据在哪一行？
4. `engine` 的 `STIRLING_RAG_MAX_SEARCHES` 和 `STIRLING_MODEL_MAX_CONCURRENCY` 各自限制的是什么行为？
5. 「48 个工具目录 150 个文件」和「21 个共享文件 4,394 行」合起来说明了一件什么事？

## 下一步读什么

给三个不同的进入目的，各一条路径：

- 想知道某个工具的全部实现：从 `TOOL_ENDPOINTS` 里那条路径出发，搜到 `controller/api/` 下对应 Controller，再看它注入的服务；不要从 `ADDING_TOOLS.md` 出发，那里的示例代码是上一代。
- 想抄三模块契约的做法：只读 `.taskfiles/frontend.yml` 与 `.taskfiles/engine.yml` 的 `tool-models` 与 `tool-models:check` 四个任务，加 `scripts/generate_tool_models.py`（506 行）和 `editor/scripts/generate-tool-api-types.mts`（582 行）两个生成脚本。任务定义三十来行，剩下的一千行全是怎么把接口模式（schema）折叠成可用类型这件事本身。
- 想看 agent 怎么包住 RAG：`engine/src/stirling/documents/README.md` 是最短的一手入口，接着读 `documents/rag_capability.py` 与 `agents/shared/chunked_reasoner.py`，比读任何二手解读都快。

## 维护指引

复核这条链需要五步命令，全部只依赖公开接口。

```bash
# 1. 只要提交树，不要文件内容
git clone --depth 1 --filter=blob:none --no-checkout \
  https://github.com/Stirling-Tools/Stirling-PDF && cd Stirling-PDF
git show HEAD:settings.gradle                    # flavor 边界
git show HEAD:app/core/build.gradle | sed -n '10,20p'   # proprietary 是否进产物
git show HEAD:engine/LICENSE | head -12          # 许可，不是 MIT
git ls-tree --name-only HEAD frontend/editor/src/core/hooks/tools/ \
  | grep -v '\.ts$' | grep -v '/shared$' | wc -l  # 48 个工具目录
```

端点与模型两个数字要从生成文件里取：`git show HEAD:frontend/editor/src/core/types/toolApiTypes.ts` 落到本地后，数 `TOOL_ENDPOINTS` 数组里的字符串项得 105，`^export interface`（88）加 `^export type … = Record<string, never>`（19）得请求模型数 107。单独数任一项都会得到偏小或偏大的中间值，而 `^export type` 一共 21 行、含两个非模型的类型定义，按它数会多数两个。

本文的读数在三种情况下需要重算：`main` 上出现新的 `v2.x` tag（发布线与仓库线的差距消失）、`settings.gradle` 改掉无条件 `include ':proprietary'`、或 `SwaggerDoc.json` 不再是前后端类型的唯一输入。语言字节数与 Stars 每次复核都会变，但这两项不构成结论，只用于说明量级。

## 参考

- 仓库：<https://github.com/Stirling-Tools/Stirling-PDF>（`main` @ `d6784b3`）
- 贡献与工具接入指南：仓库根 `ADDING_TOOLS.md`、`CONTRIBUTING.md`、`DeveloperGuide.md`
- 数据库备份：`DATABASE.md`（自动备份由 `system.databaseBackup.cron` 控制，默认每日零点；管理动作触发手动导出；可经 Web 或 API 上传 SQL 恢复）
- 引擎内文档：`engine/src/stirling/documents/README.md`（RAG 层与两种后端）
- 部署：`docker/README.md` 与 `docker/compose/`，文档站 <https://docs.stirlingpdf.com>
- 读数来源：GitHub API 的 `repos` 与 `languages` 两个端点，2026-09-20
