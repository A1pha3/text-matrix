---
title: "apache/ossie 拆解：一份关死扩展口的语义模型规范，和它还没解决的表达式问题"
date: 2026-07-17T02:58:00+08:00
lastmod: 2026-09-21T11:05:00+08:00
draft: false
categories: ["技术笔记"]
tags: ["Apache", "语义层", "数据建模", "BI", "dbt", "规范"]
description: "Apache Ossie（前身 Open Semantic Interchange）进孵化才三个月，main 上的 0.2.0.dev0 已经把顶层文档形状改掉：semantic_model 数组不再合法。读完整个仓库并把校验器与 Pydantic 参考模型各跑一遍之后，能确认的东西比 README 能告诉你的多得多——包括 10 个方言里只有 4 个真被校验、14 个转换器没有一个上了 PyPI、以及四份互相不一致的 vendor 清单。"
slug: "apache-ossie-semantic-model-interchange-spec-guide"
github_repo: "apache/ossie"
source_key: "gh:apache/ossie"
author: text-matrix
---

Ossie 要解决的事情很窄：让「营收」这个指标在 dbt、Snowflake、Tableau、GoodData 之间搬运时，有一份大家都能读写的定义。它的做法不是做工具，而是定格式——一份模式（schema）文件加一份 YAML 实例，配一批把各家格式往这个格式上折算的转换器。

我的判断有三层。第一层，这份规范真正的取舍在**关死未知字段**：`ossie-schema.json` 每一层都写着 `additionalProperties: false`，厂商私有信息只能走 `custom_extensions` 这一个口子进来，代价是任何未经协商的字段都会直接让文档校验失败。第二层，它现在**还没有把自己的口径说统一**：方言枚举 10 个、其中只有 4 个能被语法校验；vendor 知名清单在四处各写了一份、两两不一致；仓库那份主页文稿还停留在 5 个方言。第三层，规范本体只有 5 个文件，真正的工程量全在转换器那一侧，而**转换器一个都装不到**——今天要用只能克隆仓库。

下面每条结论都标了出处：文件加行号、仓库原文，或者本文的实跑输出。凡是本机跑不了的（Go 命令行工具、各家云端服务），显式写成未验证。

## 项目坐标

| 项 | 值 | 来源 |
|------|------|------|
| 定位 | Apache 孵化项目（podling），前身 Open Semantic Interchange | `README.md`、`DISCLAIMER` |
| 进入孵化 | 2026-06-22 | incubator.apache.org/projects/ossie.html（2026-09-21 取） |
| 规范版本 | main 上 `0.2.0.dev0`（未发布）；文档口径的最新发布是 0.1.1（2025-12-11） | `core-spec/spec.md` 版本历史、`docs/` 那份主页文稿 |
| Git 标签 | 只有 `osi-0.1.1-rc1` 一个，GitHub Releases 列表为空 | `git ls-remote --tags`、releases 接口 |
| 许可证 | Apache-2.0 | 仓库元数据与 `LICENSE` |
| 星标 / 复刻 /  Watchers | 2160 / 280 / 57 | GitHub 应用程序接口（API），2026-09-21 取 |
| 未关闭条目 | 136 条 = 57 个议题（issue）+ 79 个拉取请求，另有 20 个已关闭议题 | 检索接口按类型分列 |
| 提交与贡献者 | 288 次提交、52 名贡献者，最早一条提交 2025-10-07 还在写 OSI | 提交历史分页 |
| 讨论区 | 已开启，94 条讨论 | 仓库接口计数 |

一句提醒：`open_issues_count` 这个字段是议题和拉取请求的合计，按它判断「积压了多少问题」会高估一倍以上。

## 目录

- [项目坐标](#项目坐标)
- [核查方法](#核查方法)
- [仓库实际长什么样](#仓库实际长什么样)
- [三份规格别混成一份](#三份规格别混成一份)
- [最要紧的变化：顶层文档形状改了](#最要紧的变化顶层文档形状改了)
- [关死的字段与唯一的扩展口](#关死的字段与唯一的扩展口)
- [类型与角色：datatype 和 is_time 是两件事](#类型与角色datatype-和-is_time-是两件事)
- [10 个方言，能校验的只有 4 个](#10-个方言能校验的只有-4-个)
- [ai_context 在五层上，键名本身还在投票](#ai_context-在五层上键名本身还在投票)
- [14 个转换器各自对接的是什么实物](#14-个转换器各自对接的是什么实物)
- [一次真实任务：把旧模型迁到 0.2.0.dev0 并跑通校验](#一次真实任务把旧模型迁到-020dev0-并跑通校验)
- [BI 工具真正会生成的那些 SQL](#bi-工具真正会生成的那些-sql)
- [它不替代谁](#它不替代谁)
- [治理、发布与版本承诺](#治理发布与版本承诺)
- [常见误区](#常见误区)
- [该不该用，从哪儿开始用](#该不该用从哪儿开始用)
- [五道自测题](#五道自测题)
- [出错时先看哪几处](#出错时先看哪几处)
- [下一步读什么](#下一步读什么)
- [维护指引与事实边界](#维护指引与事实边界)
- [参考资料](#参考资料)

## 核查方法

这篇不是照着 README 复述出来的。第一步是浅克隆到本地（提交 `df81044`，2026-09-20），把关键目录逐文件读完，包括 `core-spec/` 全部内容、`converters/README.md`、`validation/`、本体规格，以及 `python/src/ossie/models.py`。

第二步是装依赖并把校验器真的跑起来。依赖版本照 `validation/validate.py` 头部声明取，本机用 uv 建环境：

```bash
git clone --depth 50 https://github.com/apache/ossie.git
cd ossie
uv venv --python 3.11 .venv
uv pip install --python .venv/bin/python \
  "jsonschema>=4.26.0" "pyyaml>=6.0.3" "sqlglot>=30.12.0"
.venv/bin/python validation/validate.py examples/tpcds_semantic_model.yaml
```

实测装到的版本是 4.26.0、6.0.3、30.18.0；最后一行输出 `Validation PASSED: tpcds_semantic_model.yaml`，退出码 0。这一步必须先过，否则后面所有失败输出都可能来自坏环境而不是坏文档。

第三步是拿构造出来的输入做差分：同一份文件既喂给 `validate.py`，也喂给 Pydantic 参考模型（把 `python/src` 放进模块搜索路径后调 `OssieDocument.model_validate`）。两个校验器给出不同结论的地方，就是本文最有信息量的地方。

## 仓库实际长什么样

```text
core-spec/     5 个文件   spec.md, spec.yaml, ossie-schema.json,
                          expression_language.md, img/
converters/  290 个文件   14 个厂商目录 + README.md
validation/    3 个文件   validate.py, test_validate.py, tests/
python/        6 个文件   Pydantic v2 模型，转换器的公共底座
cli/          20 个文件   Go 写的 ossie 命令行工具
ontology/      2 个文件   ontology.md + ontology.json
examples/      2 个文件   tpcds_semantic_model.yaml, flights.yaml
bi-sql-examples/ 7 个文件 目前只有 tableau/ 一个子目录
docs/          2 个文件   index.md, working_groups.md
compliance/    1 个文件   只有一句占位说明
ROADMAP.md / CONTRIBUTING.md / DISCLAIMER / NOTICE / LICENSE 在仓库根
.github/workflows/        16 个：14 个转换器 + cli + validation
```

全文 366 个受版本控制的文件，转换器占了 290 个。「规范薄、转换层厚」不是修辞，是一个可以直接算出来的比例。

顺带纠正一处容易踩空的路径：路线图在仓库根的 `ROADMAP.md`，不在 `docs/` 下；`docs/` 里只有项目主页文稿和工作组清单两篇。

## 三份规格别混成一份

读者最容易搞错的一点是：以为 `core-spec/` 目录里躺着的是一份规格。实际上是三份，成熟度各不相同。

| 规格 | 载体 | 状态 | 现在能依赖吗 |
|------|------|------|--------------|
| 核心元数据规范 | `spec.md` + `ossie-schema.json` + `spec.yaml` | 顶部写着 DRAFT，`0.2.0.dev0` | 枚举与字段可用，文档形状正在变 |
| 表达式语言 | `expression_language.md`（806 行） | 文首 `Current Status: Proposed Final` | 只是提案，未并入核心枚举 |
| 本体层 | `ontology/ontology.md` + `ontology.json` | 同样标 `0.2.0.dev0` | 另一套根键，不吃核心模式 |

表达式语言那份提案值得单独说。它定义了 Ossie 实现「MUST 支持」的 SQL 子集，并且要新增一个方言 `Ossie_SQL_2026`、在未指定方言时把它当默认值（第 54–55 行）。把这个方言名在全仓搜一遍，命中只有提案自己的两行（第 54、55 行），而且文中写作转义形式 `Ossie\_SQL\_2026`，照原样字符串去搜会一个都搜不到。方言枚举、`ossie-schema.json`、Pydantic 模型里都没有它。所以「Ossie 有一套可移植表达式语言」这句话，**现在只能成立到文档层面**。

提案本身也划了范围：Ossie 有本体层与逻辑层两处需要表达式语言，这份只管逻辑层，本体层留作另案。

## 最要紧的变化：顶层文档形状改了

`0.2.0.dev0` 的版本历史只记了一条变更，措辞是 `Breaking`：每个独立文档在根级直接放一个模型，`semantic_model` 数组被移除。动手的是提交 #383（2026-09-16，标题 `Define one semantic model per document without a wrapper`），紧随其后的 #397 又把根级的 `dialects` 与 `vendors` 从模式里删掉。规范原文的例子是新形状：

```yaml
version: 0.2.0.dev0
name: sales_analytics
description: Sales and customer analytics model
ai_context:
  instructions: "Use this model for sales analysis and customer insights"
datasets:
  - name: orders
    source: sales.public.orders
relationships: []
metrics: []
custom_extensions:
  - vendor_name: DBT
    data: '{"project_name": "tpcds_analytics", "models_path": "models/semantic"}'
```

旧的写法是这样的：

```yaml
semantic_model:
  - name: sales_analytics
    datasets:
      - name: orders
        source: sales.public.orders
```

拿这份旧形文档去跑校验器，得到四条报错，退出码 1：

```text
Validation FAILED with 4 error(s):

  [Schema] (root): 'version' is a required property
  [Schema] (root): 'name' is a required property
  [Schema] (root): 'datasets' is a required property
  [Schema] (root): Additional properties are not allowed ('semantic_model' was unexpected)
```

这四条其实是同一个原因的两面：根级现在要求 `version`、`name` 和一个非空的 `datasets`（`ossie-schema.json:35`），而 `semantic_model` 这个键已不在允许列表里。迁移规则写在 `spec.md` 的「Migrating earlier document shapes」一节：把模型属性平移到根级、删掉 `semantic_model`、补上 `version`；根级的 `dialects` 与 `vendors` 声明要去掉，逐表达式的方言信息保留；多个模型就拆成多个文档、逐个校验；并且明确要求「不要静默只取第一个模型，也不要覆盖文件」。这几条都很新鲜：#383 与 #397 落在 2026-09-15 至 16，而 main 上最新那条提交（`df81044`，#291）走的是另一条路：加一个脚本，从 `ossie-schema.json` 反向生成 `spec.yaml` 里的枚举，好让这两份机器可读文件不再各说各话。

这个变更的波及面不是文档级的。转换器公共文档 `converters/README.md` 开头就规定转换器一律使用扁平格式、旧形必须先迁移；Snowflake 转换器自述「拒绝 `semantic_model` 包装」；Python 包那一侧也写着同样的话：「The former `semantic_model` wrapper is rejected.」（`python/README.md:28`）。三处独立表述加一次实跑，可以定案。

有一点要留余地：`$defs/SemanticModel` 这个定义还在。规范正文说它描述的是「不含独立文档元数据的模型内容」，供本体文档内嵌使用；这个定义在模式里的自述仍是 "Top-level container…"（顶层容器）那句，没跟着改。也就是说 `semantic_model` 作为**属性名**在本层文档里依然存在，只是不再作为**独立文档的外壳**。

## 关死的字段与唯一的扩展口

`ossie-schema.json` 在 10 处写了 `additionalProperties: false`：根对象、`$defs/SemanticModel`，以及 `Dataset`、`Field`、`Metric`、`Relationship`、`Dimension`、`Expression`、`DialectExpression`、`CustomExtension` 这八个定义。唯一例外是 `ai_context` 的对象形态，那里是 `additionalProperties: true`。

这个选择的直接后果是：往模型里塞一个没协商过的字段，文档就无效。实测根级加一个 `owner: data-team`：

```text
[Schema] (root): Additional properties are not allowed ('owner' was unexpected)
```

厂商私有信息于是只有 `custom_extensions` 一条路。它的结构很小：`vendor_name`（自由字符串）加 `data`（一个 **JSON 字符串**，不是对象），两个键都必填。

```yaml
custom_extensions:
  - vendor_name: SNOWFLAKE
    data: '{"warehouse": "ANALYTICS_WH", "database": "PROD", "schema": "PUBLIC"}'
```

`vendor_name` 不需要向任何人注册，规范文档里给的是一份「知名例子」清单。麻烦在于这份清单有四个版本，彼此不一致：

| 出处 | 条数 | 独有条目 |
|------|------|----------|
| `core-spec/spec.md` 的 Vendor Names 表 | 10 | `HONEYDEW` |
| `ossie-schema.json` 的 `Vendor.examples` | 8 | 无 `HONEYDEW`、无 `SIGMA` |
| `python/src/ossie/models.py` 的 `OssieVendor` | 9 | `SEMANTIDO`（且无 `POWER_BI`、`HONEYDEW`） |
| `converters/README.md` 的 Supported Vendors | 8 | `OMNI`、`NVIDIA_GSF` |

四份清单的并集有 13 个名字。只出现在一处的有四个：`HONEYDEW` 在规范正文，`SEMANTIDO` 在 Python 模型，`OMNI` 与 `NVIDIA_GSF` 在转换器文档；剩下九个里也只有 `DATABRICKS`、`DBT`、`SALESFORCE`、`SNOWFLAKE`、`WISDOM` 五个是四处全名的。还有第五处镜像：`core-spec/spec.yaml` 的注释里抄着与模式同一份 8 项清单，而那份是脚本从 `ossie-schema.json` 生成的。另外 `OssieVendor` 这个枚举其实没被字段引用——`OssieCustomExtension.vendor_name` 的类型就是 `str`，枚举只起文档作用。

这不算缺陷，更像是「不做中心注册表」这个决定的自然结果，但它意味着写转换器时不能假设双方对 vendor 名有共识。规范文档里连自己的示例都没完全统一：`spec.md` 的 Databricks 扩展示例写的是 `vendor_name: Databricks`，而同一份文档那张「知名例子」表列的是 `DATABRICKS`——表只是示例，模式里也明写任何字符串都收，所以这不算违规，是命名还没收口。

## 类型与角色：datatype 和 is_time 是两件事

`0.2.0.dev0` 引入了 `DataType` 枚举，10 个值：`String`、`Integer`、`Decimal`、`Float`、`Boolean`、`Date`、`Time`、`DateTime`、`DateTimeTz`、`Opaque`。它只回答「这个值是什么类型」；「该不该被当成时间维度」由 `dimension.is_time` 回答。规范的表格给了六种常见组合，其中两行是这样：日历日期 `d_date` 给 `Date` 且省略 `is_time` → 算时间维度；审计用的 `created_at` 给 `DateTime` 但显式写 `is_time: false` → 不算。默认规则是：`is_time` 未显式设置时，若 `datatype` 属于四个时间类型则默认 `true`，否则 `false`；显式值永远优先。

参考实现多了一条前提，而且这条前提在规范正文里没有对应句子。`OssieField.is_time_dimension()` 的函数体（`python/src/ossie/models.py:147-151`）是这样：

```python
        if self.dimension is None:
            return False
        if self.dimension.is_time is not None:
            return self.dimension.is_time
        return self.datatype in _TEMPORAL_DATA_TYPES
```

它的文档字符串（docstring）把这条前提挑明了：「A field must have dimension metadata to be a dimension.」——要先有 `dimension` 块，才谈得上时间维度。

也就是说，一个字段如果只写了 `datatype: Date`、整个 `dimension` 块都没写，那么 `dimension is None` 这一支会先返回 `False`，根本走不到「由类型推默认角色」。构造一份这样的文档实测：`jsonschema` 判它有效（合法，因为它没要求 `dimension` 存在），而 `OssieField.is_time_dimension()` 返回 `False`。规范表格里那一行「`is_time` omitted → time dimension」在参考实现里并不自动成立——差别就出在「`is_time` 省略」和「`dimension` 省略」不是一回事。对写转换器的人来说，结论是可操作的两条：要么显式写 `dimension.is_time`，要么就别指望从 `datatype` 推出角色。

顺带一个可以复用的读码点：`_TEMPORAL_DATA_TYPES` 是一个 `frozenset`，只含 `Date`、`Time`、`DateTime`、`DateTimeTz` 四个成员，和文档里的措辞逐字对应。

## 10 个方言，能校验的只有 4 个

方言枚举现在是 10 个，`spec.md`、`ossie-schema.json` 和 `models.py` 三处一致：`ANSI_SQL`、`SNOWFLAKE`、`MDX`、`TABLEAU`、`DATABRICKS`、`MAQL`、`BIGQUERY`、`SIGMA`、`THOUGHTSPOT`、`DAX`。这十个不是一次定下来的：`THOUGHTSPOT` 由提交 #351（2026-09-02）加入枚举，`SIGMA` 由 #297（2026-09-08）随 Sigma 转换器加入，`DAX` 更早——本文能取到的最早提交里它已经在枚举中了。

而校验器只把它认识的方言交给 sqlglot 做语法检查：

```python
DIALECT_MAP = {
    "ANSI_SQL": None,  # sqlglot default
    "SNOWFLAKE": "snowflake",
    "DATABRICKS": "databricks",
    "BIGQUERY": "bigquery",
    "MDX": None,  # Not supported by sqlglot, skip validation
    "TABLEAU": None,  # Not supported by sqlglot, skip validation
    "MAQL": None,  # Not supported by sqlglot, skip validation
    "SIGMA": None,  # Sigma's spreadsheet-style formula language, not SQL; skip validation
    "THOUGHTSPOT": None,  # Not supported by sqlglot, skip validation
    "DAX": None,  # Not supported by sqlglot, skip validation
}

SKIP_SQL_VALIDATION = {"MDX", "TABLEAU", "MAQL", "SIGMA", "THOUGHTSPOT", "DAX"}
```

于是「模式（schema）能过校验」和「表达式能解析」是两件事。实测：一条 `MDX` 表达式写成 `THIS IS NOT ANY LANGUAGE ([Measures].[X`、一条 `DAX` 写成 `SUMX(,,,(`，文档照样 `Validation PASSED`、退出码 0；同样一段垃圾放到 `BIGQUERY` 上就会报 SQL 解析错误。6/10 的方言拿不到任何语法反馈。

同一份文档里还有一个更省事的历史遗留：主页文稿在两处（规范概览与技术问答）列出的方言仍只有 5 个，`ANSI_SQL`、`SNOWFLAKE`、`DATABRICKS`、`MDX`、`TABLEAU`。读主页文稿会低估枚举的实际宽度，以 `spec.md` 和 `ossie-schema.json` 为准。上一节说到的同步脚本也只覆盖 `ossie-schema.json` 到 `spec.yaml` 这一条边，管不到规范正文。

转换器侧的方言选择规则是明确写下来的：优先目标平台的方言，回落 `ANSI_SQL`，两者都没有就报警告或错误。这条规则也解释了为什么允许一个字段挂多份方言表达式。

## ai_context 在五层上，键名本身还在投票

`ai_context` 出现在模型、数据集、字段、关系、指标五层，可以是裸字符串，也可以是带 `instructions`、`synonyms`、`examples` 三个推荐键的对象。仓库自带的 TPC-DS 例子内计数（用 Pydantic 解析后统计所得）：模型层 1、数据集 5、字段 25、指标 8、关系 4——五层全部用上了。

这个设计常被解读成「Ossie 把大语言模型（LLM）当一等消费者」。更准的说法是：形状定了，语义没定。`ROADMAP.md` 把 **AI-Native Semantic Layer 列在 Future Efforts**，不在当前工作组那一节。动机写的是「对结构化语义上下文与可落地的查询生成有需求」，交付项分三条：标准化 AI 上下文元数据、经验证的查询定义、控制哪些内容暴露给模型的机制。它下面挂着的第一条社区讨论标题就是「不要规定 AI Context 这个键名」；另有「加一个跳过上下文的关键字」和「把 verified_queries 变成规范元素」两条。

把「形状定了、语义没定」说到能用的层面：`ai_context` 的键名本身还在讨论中，而控制暴露面的机制还停在提案分组里。转换器怎么处理它则是具体行为：Microsoft 转换器把 Ossie 的 `ai_context` 存进一个叫 `OssieAIContext` 的注解；转换器公共文档规定，目标平台原生不支持时，导入侧要把它塞进 `vendor_name: COMMON` 的扩展里以免丢信息。

## 14 个转换器各自对接的是什么实物

`converters/` 下 14 个厂商目录。12 个是 Python 包，Polaris 与 Salesforce 是 Java（各有 `pom.xml`）。Python 侧包名统一走 `apache-ossie-*`，只有 Omni 那个叫 `ossie-omni`；两个 Java 坐标是 `ossie-polaris-converter` 与 `ossie-salesforce-converter`，版本 `0.1.0-SNAPSHOT`。版本号也不齐：10 个 Python 包跟着规范写 `0.2.0.dev0`，nvidia 是 `0.1.0.dev0`，ontology 是 `0.1.0`。

| 目录 | 对接的实物 | 方向 |
|------|------------|------|
| dbt | `semantic_manifest.json`（dbt 产物） | 双向，导入侧明确「有损」 |
| databricks | metric view 定义 | 双向，离线 |
| snowflake | Cortex Analyst 语义模型 YAML | **仅导出** |
| microsoft | 语义模型 `model.bim` JSON / TMDL 文档 | 双向，导入侧两种输入都收 |
| gooddata | 声明式 LDM JSON | 双向 |
| salesforce | Salesforce 语义模型 JSON | 双向（Java） |
| polaris | 经 Iceberg 表目录接口读写元数据 | 双向（Java，含 Importer/Exporter） |
| sigma | Sigma 数据模型 spec JSON | 双向，反解析共享一套中间表示 |
| omni | Omni 语义模型 | 双向 |
| honeydew | Honeydew 工作区目录 | 双向 |
| wisdom | WisdomAI 域定义 | 双向 |
| nvidia | GSF（Generative Semantic Fabric）独立 YAML | 双向，带原文回执 |
| orionbelt | OBML（OrionBelt Markup Language） | 双向 |
| ontology | Palantir 本体 / 本体规范 YAML | 三个单向：入 Ossie 两个、出 spec 一个 |

三点值得单独讲。

**「双向」不是设计口号，是有算术理由的。** 公共文档的说法是：N 个厂商两两互转需要 `N*(N-1)` 个转换器，以 Ossie 为中心则每个厂商各写一个导入、一个导出即可，且与其他厂商的互通顺带得到。这个论证也自带一个边界：前提是每个厂商真的把两个方向都写出来。Snowflake 目录目前只有导出的实现，所以它现在是「只出不进」的一条辐条。

**导出侧的成熟度是自己承认的。** Snowflake 转换器 README 写着「正在积极开发……未经所有边界情况的充分测试，生产环境谨慎使用」；它的类型映射表覆盖 9 个 `datatype`，`Opaque` 因没有可移植对应物而省略 `data_type` 并输出警告。dbt 方向更明确：`semantic_manifest.json` → Ossie 被标为有损，每一处信息丢失都记成一个 `ConverterIssue` 返回。NVIDIA 那条路数不同：从 GSF 转进来时把原始文档整份存进 `NVIDIA_GSF` 扩展里，因此 GSF → Ossie → GSF 能回去；手写 Ossie 文件没有这个扩展，走同一方向就没有这层保险。读这几段的意义在于：**能不能安全往返，答案按厂商各不相同**，不能按「双向」两个字概括。

**一个都装不到。** 仓内声明的 13 个 Python 包名（12 个转换器加公共底座 `apache-ossie`），再加上裸名 `ossie`，一共 14 个在 PyPI 的包元数据接口上全部返回 404（2026-09-21 逐个查过）。这件事转换器自己也写在配置里：dbt 转换器依赖 `apache-ossie>=0.2.0.dev0`，紧接着就是一段注释，说明该包尚未发布、先用 `[tool.uv.sources]` 从仓内 `../../python` 以可编辑方式解析，并留了「等它发布后删掉这段」。

唯一看似例外的是 orionbelt：它的 README 说正源在上游独立仓库的 `packages/ossie-orionbelt`，并从那里发布到 PyPI。上游确实发了包（`orionbelt-semantic-layer`，2.30.0，累计 74 个发布），但把它的 wheel 解出来数一遍，177 个条目里和 ossie 相关的有 0 个；换成源码发行物，那个子包仍叫 `packages/osi-orionbelt`、模块名 `osi_orionbelt`、文件是 `osi_to_obml.py` 与 `obml_to_osi.py`——停在改名之前的命名上。所以「上游已发布」说的是 OrionBelt 这个产品，不是 Ossie 转换器。结论不变：要跑转换器只能克隆仓库，进对应目录 `uv sync`，再走它自己注册的命令（dbt 那个是 `ossie-dbt`）。

## 一次真实任务：把旧模型迁到 0.2.0.dev0 并跑通校验

假设你手上有一份 OSI 时代导出的模型，形状还是 `semantic_model` 数组，现在要用它给两家 BI 工具做口径对账。整个流程走下来是这样，命令与输出都是本文实跑。

第一步，先按旧形状喂校验器，确认问题在文档而不是环境。四条根级报错，退出码 1（上面已给）。

第二步，按迁移规则把模型属性平移到根级，补 `version`：

```yaml
version: 0.2.0.dev0
name: revenue_model
datasets:
  - name: orders
    source: analytics.orders
    primary_key: [order_id]
    fields:
      - name: recognized_revenue
        expression:
          dialects:
            - dialect: ANSI_SQL
              expression: recognized_revenue
metrics:
  - name: revenue
    expression:
      dialects:
        - dialect: ANSI_SQL
          expression: SUM(orders.recognized_revenue)
```

注意指标的形状：只有 `name` + `expression`（外加可选的 `description`、`datatype`、`ai_context`、`custom_extensions`）。**Ossie 没有 `type: simple` / `type_params` 这一套**，那是 dbt 的指标结构，转换器读的就是它（`converters/dbt/src/ossie_dbt/msi_to_ossie.py` 里出现 `metric.type_params.expr`、`metric_aggregation_params`、`cumulative_type_params`、`numerator`/`denominator`）。把带这两个键的指标拿去校验，报错很直白：

```text
[Schema] metrics -> 0: 'expression' is a required property
[Schema] metrics -> 0: Additional properties are not allowed ('type', 'type_params' were unexpected)
```

第三步，跑通之后再做一件真正省事的事：把同一份模型转成两家的形式，比较差异。这一步本文**未验证**，因为需要 Snowflake 与 dbt 的真实项目输入，仓库里没有对应的可运行样本；能验证的是离线那半段——转换器的入口和参数格式在各目录 README 里。

第四步，用关系把两张表连起来时，注意校验器对 `to_columns` 的处理。它只要求两侧列数相等，不等就报：

```text
[Arity] Relationship 'o_c' in model 'm': from_columns (1) and to_columns (2) must have the same number of columns
```

而 `to_columns` 没有覆盖目标数据集任何已声明的键时，它给的是**警告**，文档仍然通过、退出码仍是 0。规范正文把 `to_columns` 描述成「主键或唯一键列」，校验器却按「能保住多对一语义」来判，代码注释也写明了理由：覆盖即视为足够，而且 `primary_key` 与 `unique_keys` 本身是可选的，可能压根没声明。这是一处强度差，别把「校验通过」读成「关系语义正确」。

## BI 工具真正会生成的那些 SQL

`bi-sql-examples/` 是仓库里最有教学价值、也最容易被跳过的一个目录：只有 `tableau/` 一个子目录，四段 SQL 加一份 `setup.sql`。README 说清了目的：**收录 BI 工具在「指标定义在工具之外」时真正生成的 SQL**，再拿这些查询形状去检验 Ossie 能不能安全覆盖复杂情况。四个例子分别是 top-N 过滤、两级 LOD 聚合、集合（sets）、多表连接与关系。里面用了一个 `MEASURE()` 函数读指标，README 特意声明那只是示意：任何方案都要求 BI 工具提供某种查询指标的函数。

这份材料旁边摆着表达式语言提案里的两样东西，正好组成「难在哪」的完整答案。

一样是不支持清单：表达式里不许出现 `SELECT`/`FROM`/`JOIN`、`GROUP BY`（由粒度控制）、`WHERE`（改用 filter 属性）、子查询、CTE、`UNION`/`INTERSECT`/`EXCEPT`、DDL、DML。另一样是可分解性分档，它决定一个指标能不能在更粗的粒度上二次汇总：

| 类别 | 函数 |
|------|------|
| Distributive | SUM, COUNT, MIN, MAX |
| Algebraic | AVG, STDDEV, VARIANCE |
| Holistic | MEDIAN, PERCENTILE, COUNT DISTINCT |
| Sketch-based | APPROX_COUNT_DISTINCT, APPROX_PERCENTILE |

核心聚合表里 `COUNT(DISTINCT expr)` 标的就是 Holistic。这两样合起来能推出一条判断，虽然仓库里没有哪一句话直接这么写：**眼下能跨工具搬得放心的，是可分解性为 distributive 或 algebraic 的那类指标表达式。**推理链是三段：表达式语言把 `GROUP BY` 与 `WHERE` 挡在表达式之外，汇总责任交给消费端；`COUNT(DISTINCT ...)`、`MEDIAN`、`PERCENTILE` 被标成 holistic，意味着换粒度时不能拿已汇总的结果再算一次；而 Tableau 那份两级聚合样本恰好演示了工具端就是这么发查询的。规范文档对多阶段聚合只留了一个外部链接，它称之为 Analytical Context Extension；仓库里没有对应的可执行定义。这也是这条判断的边界：不是「Ossie 不支持」，而是**它现在只把分类写下来，把复算规则留给实现**。表达式语言的函数分档也能佐证成熟度：在剔除代码块后统计标题里的档位标记，`(REQUIRED)` 23 个小节、`(RECOMMENDED)` 4 个、`(EXPERIMENTAL)` 2 个。

## 它不替代谁

项目主页的问答里给了坐标。它把已有的标准分成三类：数据格式（Parquet、Arrow）、查询接口（ODBC、JDBC）、目录元数据（Hive Metastore、OpenMetadata）。Ossie 管的是其上的语义层——业务含义、指标定义、关系——并且明确说自己是互补而非替代。

这句话在这份仓库里能找到实现级的支撑，不必靠类比。`converters/ontology` 处理的是本体层（概念、关系、业务规则），`ontology/ontology.md` 把概念分成 `EntityType` 与 `ValueType` 两类，内置 8 个概念（`Any`、`Boolean`、`Date`、`DateTime`、`Decimal`、`Float`、`Integer`、`String`），关系的重数只允许 `ManyToOne` 与 `OneToOne` 两种；映射侧再把逻辑层的字段接回概念对象（`object_mappings` 用 SQL 表达式，或 `referent_mappings` 经标识关系找实体）。仓库自带的第二个例子 `examples/flights.yaml`（1111 行）走的正是这一层：它根级除 `version`、`name`、`description` 外还带 `ontology`、`ontology_mappings`、`requires` 三个键，用核心模式校验会失败（缺 `datasets`，外加这三个未知键），换 `--schema ontology/ontology.json` 才通过。

同一份文件在一套模式下无效、在另一套下有效——这就是「核心规范与本体规范是两份规格」最直观的证据。

## 治理、发布与版本承诺

孵化时间线在 Apache 的 podling 状态页上逐项打了日期：06-22 进孵化，06-23 申请 DNS，06-26 邮件列表、仓库迁移与议题跟踪一并就位，06-29 导师订阅完成。冠军与四位导师里，JB Onofré 既在导师名单里，也出现在贡献者前列。页面公开列出 14 位提交者，其中至少四位能在表达式语言提案的署名里对上：Will Pugh、Khushboo Bhatia、Quigley Malcolm，以及写成「Kurt, Relational AI」的那位。那份署名还覆盖 Malloy、Atscale、Salesforce、dbt Labs、Databricks、Cube、ThoughtSpot、Lightdash、Starburst、Denodo 与 The ASF。

规范变更走 ASF 投票：在 `dev@ossie.apache.org` 发提案并开一个说明动机与影响的拉取请求，讨论期最短 7 天，然后开 `[VOTE]`；`-1` 必须附技术理由且只能通过解决该理由来化解；**通过需要至少 3 个约束性 `+1` 且无否决**。孵化期的发布还要 Incubator PMC 批。提交者需要签 ICLA。这些条件解释了为什么「一家厂商推个字段进来」在这个项目里走不通——不是因为模式关得严，而是因为改模式要过投票。

版本策略这处要读细。主页文稿写的是遵循语义化版本，其中「小版本 = 向后兼容地新增，已有有效模型仍然有效」。而 `spec.md` 的版本历史把 `semantic_model` 数组移除记在 `0.2.0.dev0` 上并标注 `Breaking`。两者对不上；但主版本号是 0，语义化版本本身对 0.x 段就允许以小版本承载破坏性变更，所以这更像承诺措辞还没赶上现实，而不是流程被破坏。配套的还有两条：破坏性变更要在变更日志显式标记、给迁移指南、尽量走弃用期；`custom_extensions` 被明令排除在核心兼容承诺之外，但规范保证它在往返转换中**一定被保留**，哪怕中转工具读不懂。

发布现状值得单独提醒：仓库只有一个标签 `osi-0.1.1-rc1`（连标签前缀都还是 OSI 时代的），GitHub Releases 列表是空的，`version` 在模式里被钉成常量 `"0.2.0.dev0"`。补语义化版本与 Git 发布的请求是议题 #102，它已在 2026-05-20 关闭，标题里引用的还是旧文件 `core-spec/osi-schema.json`。严格讲，规范正文所称「最新已发布 0.1.1」只到文档口径为止——能钉住的产物只有那个 rc 标签。把标签里的模式取出来与 main 对一遍，破坏性变更的分量就清楚了：

```text
                0.1.1 标签的模式             main 的 0.2.0.dev0
根级必填      version, semantic_model    version, name, datasets
方言枚举      6 个                       10 个
DataType      没有这个定义               10 个值
```

顺带一句：主页文稿列的 5 个方言比 0.1.1 正式版还少一个（缺 `MAQL`），可见那份清单不是照某个已发布版本抄出来的。

旧名的残留不止链接：Slack 邀请在 `docs/working_groups.md` 与主页文稿里两处都还指向 `opensemanticx`，而 README 的入口已经是 `apache-ossie`。工作组共四个，负责人分别是指标语言与关系（Will Pugh）、目录（Shubham Bhargav，Atlan）、本体（Kurt，RelationalAI）、金融服务通用语义（John Heisler，Snowflake）。`ROADMAP.md` 的「当前工作组」一节只列了前三项。

## 常见误区

按现象分，最常见的三类。

**校验报「Additional properties are not allowed」。** 这一句总是指向同一类原因：你动了根级或某层的未知字段。这份模式在每一层都关着，唯一合法的携带信息位置是 `custom_extensions`。先看报错路径：`(root)` 还是 `datasets -> 0 -> ...`，位置决定了你放错了哪一层。

**关系语义过了校验，但 join 方向是错的。** 上一节那条 `[Reference] Warning` 就是这种情形：列数对齐了、覆盖没保证。把「退出码 0」当成语义正确，会在这种地方翻车。

**同一个字段在两个校验器里结论不一样。** 这是本文实测到的、最容易让人误判工具坏了的一处。同一份输入：

| 输入 | JSON Schema 校验器 | Pydantic 参考模型 |
|------|--------------------|-------------------|
| `version: "9.9.9"` | 失败（模式要求常量 `0.2.0.dev0`） | 通过（那里只是默认值） |
| 根级多个 `owner` | 失败 | 失败（`extra="forbid"`） |
| 数据集层多个未知键 | 失败 | **通过** |
| `primary_key` 写成字符串 | 失败 | 失败 |

根因是能读出来的：`OssieDocument` 单独声明了 `model_config = ConfigDict(frozen=True, extra="forbid")`，其余模型类都只有 `frozen=True`（个别另加 `extra="allow"` 或 `populate_by_name=True`，但都没有 `forbid`），于是 Pydantic 默认的「忽略未知字段」在嵌套层生效。`version` 那行同理，`version: str = "0.2.0.dev0"` 是缺省值不是约束。**要判合规就以 `validate.py` 为准；Pydantic 那边不报错，不等于文档有效。**

## 该不该用，从哪儿开始用

按阶段给顺序，不按热情给。

1. **只有一家 BI 或语义层工具**：现在没有跨工具搬运需求，Ossie 对你只有「多一套要维护的模式」这一层成本。可以先只读表达式语言提案，那部分对「一个指标表达式到底能写多复杂」有独立参考价值。
2. **两家以上工具、口径已经开始打架**：可以试点，但要按本文列出的现实条件做——只处理可分解性为 distributive/algebraic 的指标；从一个数据集开始；把转换器版本钉到具体提交；并且假设至少有一个方向是有损的，用 `ConverterIssue`（dbt 侧）或扩展回存（NVIDIA 侧）去看损失落在哪。
3. **要给智能体（agent）接业务口径**：`ai_context` 的形状可用，但别把「规范里有这个字段」当成「语义已定」。它还在被讨论、控制暴露面的机制还在未来事项里。真要接，先把口径来源固定，再指望这个字段。
4. **在做目录（catalog）集成**：这条路线在项目里是当前的工作组之一，交付项写着与 Polaris 这类目录的集成模式、独立语义服务与注册表、以及模型的发现、版本化与访问控制——都还没落地。有实际需求值得参与，没需求就别按「已有目录集成」来排期。
5. **想给自家产品做导入导出**：这是投入产出最清楚的一条。`converters/README.md` 给了九步实现清单和一张边界情况处理表（缺厂商方言回落 `ANSI_SQL` 并记警告、复合主键、跨数据集指标的引用解析、未知 vendor 的扩展要保留不得丢弃），公共模型类型可以从 `python/` 直接复用（转换器就是这么依赖它的），工作流文件也有 14 份转换器的现成样板可照抄。

不建议现在做的事只有一件：**把它当发布中的标准去对外承诺兼容性**。仓库没有正式产物可钉，模式里的版本是个开发常量。

## 五道自测题

1. 一份根键只有 `semantic_model` 数组的文档，在当前 main 上会报几条错误、为什么？
2. `custom_extensions` 里能不能放一个 JSON 对象？为什么？
3. 一个字段写了 `datatype: Date`、没有 `dimension` 块，它算不算时间维度？两个校验器各怎么说？
4. 指望 `validate.py` 抓出 MDX 表达式的语法错误，可行吗？
5. 你声称「A 工具与 B 工具已经通过 Ossie 互通」，需要满足的前提是什么？

答案依次落在：形状变更与四条根级错误；不能（`data` 的类型是字符串，扩展本体也关着）；参考实现判不算而模式判合法；不可行（`MDX` 在跳过集合里，语法只能由工具侧自己负责）；两个方向的转换器都得存在，而 Snowflake 那一条目前只有导出。

## 出错时先看哪几处

| 症状 | 先看 | 依据位置 |
|------|------|----------|
| 根级三条 required 加一条 unexpected | 文档是否还是旧数组形状 | `core-spec/spec.md` 迁移一节 |
| `Additional properties are not allowed` | 报错路径指向的层级 | `ossie-schema.json` 的 10 处 `additionalProperties: false` |
| `'TEXT' is not one of [...]` | 用了数据库物理类型名 | `$defs/DataType` 枚举 10 值 |
| `[Arity] ... must have the same number` | `from_columns`/`to_columns` 长度 | `validate_relationship_column_arity()` |
| `[Reference] Warning ... does not cover` | 目标数据集的键声明 | `validate_references()`，注意它是警告 |
| `[SQL] ... Invalid expression` | 该方言是否真被送去解析 | `SKIP_SQL_VALIDATION` 里那 6 个不在检查范围 |
| `Error: Invalid YAML: found duplicate key` | YAML 里重复的键 | `UniqueKeyLoader` |
| 装不上转换器 | 它不在 PyPI | 各目录 README 的 `uv sync` 路径 |

## 下一步读什么

顺序读比按目录扫省事：

1. `core-spec/spec.md` 第 26–158 行，Goals、Enumerations、Semantic Model 三节连着读，把 10 个方言与 10 个类型先记住。
2. `ossie-schema.json` 从 `$defs/SemanticModel` 倒着往上读，比读文档更能看清哪些字段是必填的。
3. `validation/validate.py` 的五个检查项（`validate_schema` 一直到 `validate_sql`，外加一个逐表达式辅助函数）——规范正文与工具行为的差异全在这里。
4. `converters/README.md` 后半段的「Handling Edge Cases」表与 Round-Trip 一节，准备写转换器前必读。
5. `core-spec/expression_language.md` 的不支持清单与可分解性表，判断某个指标能不能安全搬。
6. `bi-sql-examples/tableau/` 四段 SQL，看真实 BI 查询长什么样。
7. `ROADMAP.md` 与主页文稿的兼容策略一节，判断哪些能力属于「已写下来」而非「已能用」。

## 维护指引与事实边界

- **本文事实的核查时间**：2026-09-21，对应提交 `df81044`（2026-09-20，提交信息 `Automate enum sync for spec files`）。仓库仍活跃，但不是每天有提交：以 2026-08-24 起的四个星期为窗口，共 47 次提交、分布在 21 个自然日。`0.2.0.dev0` 期间任何字段名、枚举、退出码都可能变；重读时先用 `git log -1` 对提交号。
- **需要最先复核的三条**：方言枚举（本次 10）、顶层必填键集合（`version`/`name`/`datasets`）、以及 PyPI 是否仍无发布。这三条最容易变，而且一变就会牵连文中多处结论。
- **一条实测到的经验**：那份刚合进来的同步脚本，在 main 上跑 `python3 scripts/generate-spec-types.py --check` 现在是失败的（退出码 1）。它想删掉 `spec.yaml` 里 `SIGMA` 与 `DAX` 两条注释，因为脚本自带的那份说明字典里没有这两个值；而 `spec.md` 的方言表里两处说明都写得好好的。同一份枚举此时由四处手工维护——模式、规范正文、`spec.yaml` 的注释、以及脚本里的字典——而且这个脚本还没接进任何工作流。规范正文与机器模式的一致性能被自动化，跨文件的一致性还得人盯着。
- **本文未验证的事项**：Go 命令行工具（本机无 Go 工具链，`ossie validate`/`convert`/`plugin` 的子命令与参数只来自 `cli/cmd/*.go` 的源码文本）；各转换器的实际转换输出；任何需要 Snowflake / dbt / Tableau / Polaris 真实项目输入的往返实验；`incubator.apache.org` 之外的 ASF 内部投票记录；讨论区各议题的当前共识程度（只引用了议题标题与所在分组）。
- **可复算的入口**：`python validation/validate.py <file>`（退出码 0/1）、`--schema ontology/ontology.json` 换模式、`PYTHONPATH=python/src` 直接 `import ossie.models`。统计类数字（文件数、目录数、例子内的层计数）都可用 `git ls-tree -r --name-only HEAD -- <dir>` 与一次 Pydantic 解析复现。

## 参考资料

- [apache/ossie 仓库](https://github.com/apache/ossie) — 提交 `df81044`
- [核心元数据规范 core-spec/spec.md](https://github.com/apache/ossie/blob/main/core-spec/spec.md) — 顶层形状、枚举、迁移规则
- [机器可读模式 ossie-schema.json](https://github.com/apache/ossie/blob/main/core-spec/ossie-schema.json) — 必填键与逐层 `additionalProperties`
- [表达式语言提案 core-spec/expression_language.md](https://github.com/apache/ossie/blob/main/core-spec/expression_language.md) — 子集、函数分档、可分解性
- [转换器公共指南 converters/README.md](https://github.com/apache/ossie/blob/main/converters/README.md) — hub-and-spoke、边界情况、往返保真
- [校验器 validation/validate.py](https://github.com/apache/ossie/blob/main/validation/validate.py) — 五层检查与方言映射
- [主页文稿（仓库 docs 目录的索引页）](https://github.com/apache/ossie/blob/main/docs/index.md) — 治理、投票、兼容策略、采用四阶段
- [路线图 ROADMAP.md](https://github.com/apache/ossie/blob/main/ROADMAP.md) — 当前与未来工作组、社区讨论索引
- [Apache Ossie 孵化状态页](https://incubator.apache.org/projects/ossie.html) — 进孵化日期、导师、提交者名单
- [官方站点 ossie.apache.org](https://ossie.apache.org/) — 会议与工作组安排
