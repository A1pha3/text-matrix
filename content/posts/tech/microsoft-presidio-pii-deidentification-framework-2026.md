---
title: "Presidio：企业 AI 数据合规的事实标准"
date: "2026-06-25T15:18:21+08:00"
slug: "microsoft-presidio-pii-deidentification-framework-2026"
github_repo: "microsoft/presidio"
source_key: "gh:microsoft/presidio"
description: "Presidio 把 PII 识别 + 编辑 + 反向识别做成可插拔框架，5 个模块（Analyzer / Anonymizer / Image Redactor / Structured / CLI）覆盖文本、图像、DICOM 与结构化数据。它不只是脱敏工具，是企业 AI 数据处理流水线的合规基础设施。本文拆开双层架构、103 个内置 recognizer、8+2 个 operator、DICOM 医学影像脱敏、与 LLM 协作时替身回路的真实工程约束，并给出 4 类团队的采用顺序。"
draft: false
categories: ["技术笔记"]
tags: ["Microsoft", "Hugging Face"]
hiddenFromHomePage: false
---

# Presidio：企业 AI 数据合规的事实标准

## §1 先给判断

如果一家公司在 2026 年还在用 LLM 处理用户数据，却**没有**用 Presidio 之类的工具在 prompt 出去之前把姓名、身份证号、信用卡号、SSN、电话号码去掉，那它要么没真跑过生产负载，要么把合规外包给了法务。

Presidio 不只是"一个 PII 编辑库"。它把 PII 检测、脱敏、反向脱敏做成可插拔框架——5 个子项目、103 个内置 recognizer 类（运行时由 YAML 注册表加载 96 个，默认启用 25 个）、10 个 operator（8 个 anonymize + 2 个 deanonymize），覆盖文本、图像、DICOM（Digital Imaging and Communications in Medicine，医学数字成像与通信标准）医学影像和结构化数据。放在 LLM 上游做去识别、下游做反向识别，让模型"看到的是替身"，用户"拿到的是真名"。

GitHub 上 10.8k stars、1.28k forks、MIT 协议、2018-05-04 创建，最新 release 是 2026-07-22 的 2.2.364。**这不是一个被放弃的旧库**。还有一件必须知道的事：项目已经完成从微软向社区组织 Data Privacy Stack 的移交（见 §13），仓库现在叫 `data-privacy-stack/presidio`。

这篇文章拆开 Presidio 的 5 个模块、双层架构（Analyzer 识别 + Anonymizer 编辑）、与 LLM 协作时替身回路的真实工程约束、DICOM 医学影像处理、recognizer 的可插拔机制，并给 4 类团队一个明确的采用顺序。

## §2 阅读路径

- **只想看结论**：§3 总览图 → §4 5 个模块 → §11 决策矩阵
- **想看核心架构**：§5 双层架构 → §6 Analyzer 与 recognizer → §7 Anonymizer 与 operator
- **想看 LLM 集成模式**：§7.3 反向识别的真实机制 → §8 替身回路与失败模式
- **想看工程边界**：§10 适用边界 → §11 决策矩阵
- **第一次读**：按顺序读，§3 + §7.3 + §11 是最值得细读的三节

## §3 系统地图：Presidio 在 AI 数据处理流水线里到底做什么

在展开细节之前，先把 Presidio 放在一个完整的 AI 数据处理流水线里看。

```
完整 AI 数据处理流水线
│
├── 数据入口
│   ├── 用户输入（chat / 表单 / 邮件 / 上传文件）
│   ├── 业务系统（CRM 工单 / 客服录音转写 / 病历 OCR）
│   └── 文档库（PDF / Word / 邮件归档 / 数据库导出）
│
├── Presidio 去识别层（这是本文焦点）
│   ├── presidio-analyzer
│   │   ├── 内置 recognizer：regex + checksum / NER / 各国证件规则
│   │   │   （default_recognizers.yaml 注册 96 个，默认启用 25 个）
│   │   ├── 自定义 recognizer 接口（pattern / NER / 规则等）
│   │   ├── NLP 引擎：spaCy（默认）/ Stanza / transformers
│   │   └── 输出：RecognizerResult 列表（entity_type / score / start / end）
│   │
│   ├── presidio-anonymizer
│   │   ├── 10 个内置 operator（replace / mask / redact / encrypt / hash / ...）
│   │   ├── 自定义 operator 接口
│   │   ├── 反向识别（deanonymize）：decrypt 等
│   │   └── 输出：EngineResult（text / items）
│   │
│   ├── presidio-image-redactor
│   │   ├── OCR（Tesseract，官方测试版本 v5.2.0）提取图像文字
│   │   ├── 文字送 presidio-analyzer 识别，再在原图上涂黑对应区域
│   │   ├── DICOM 医学影像：像素级文字处理（元数据不归它管）
│   │   └── 输出：去识别后图像
│   │
│   ├── presidio-structured
│   │   ├── 表格 / JSON 字段扫描
│   │   ├── 字段名 → PII 实体类型映射
│   │   └── 输出：脱敏后 DataFrame / dict
│   │
│   └── presidio-cli
│       └── 命令行工具（2.2.364 起支持 --threshold 覆盖置信度阈值）
│
├── LLM 处理层
│   ├── 主流模型（GPT / Claude / Gemini / 开源模型）
│   ├── 收到的是替身
│   └── 不接触真实 PII
│
└── 反向识别层
    ├── decrypt 路径（密文嵌在文本里，内置可逆）
    └── 应用层替身表（replace 型替身需自己维护映射，见 §8）
```

**关键边界**：Presidio 的工作是把"真实 PII"转换成"LLM 看得懂的替身 + 反向恢复手段"。LLM 处理过程中**不会接触真实 PII**——它看到的是 `My name is <PERSON_1> and my card is <CREDIT_CARD_1>`，回复给用户之前再把替身换回原值。

这个边界不是本文给 Presidio 的评价——它写在 README 第一段的警告里：**"Presidio can help identify sensitive/PII data in un/structured text. However, because it is using automated detection mechanisms, there is no guarantee that Presidio will find all sensitive information."**

翻译一下：Presidio 召回率很高但不完备，官方明确说**不保证找出全部敏感信息**。生产部署时它必须和别的合规层（人审 / 规则补充 / 业务白名单）一起用，**不能单独指望它**。

## §4 仓库拓扑：5 个子项目怎么拆

| 子项目 | 角色 | 核心 API | 部署形态 |
|--------|------|----------|----------|
| **presidio-analyzer** | PII 识别 | `AnalyzerEngine.analyze()` | Python lib / HTTP 5002 |
| **presidio-anonymizer** | PII 编辑（10 个 operator）| `AnonymizerEngine.anonymize()` / `DeanonymizeEngine.deanonymize()` | Python lib / HTTP 5001 |
| **presidio-image-redactor** | 图像 PII | `ImageRedactorEngine` / `DicomImageRedactorEngine` | Python lib / HTTP 5003 |
| **presidio-structured** | 表格 / JSON PII | `StructuredEngine` | Python lib |
| **presidio-cli** | 命令行 | `presidio` | CLI |

仓库根目录把这些子项目作为独立 Python package 发布，每个都有自己的 `pyproject.toml` 和 `README`。根目录提供一个 `docker-compose.yml`，把 analyzer、anonymizer、image-redactor 三个服务和 Ollama 一起编排起来（2.2.363 起带 healthcheck），宿主端口分别是 5002 / 5001 / 5003。

**关键设计**：5 个子项目不是 5 个平行的独立服务，它们之间有明确的依赖关系。`presidio-image-redactor` 直接 import `presidio-analyzer` 来识别 OCR 出来的文字；`presidio-structured` 内部调用 analyzer 识别字段 PII 类型、anonymizer 执行编辑。**analyzer + anonymizer 是底座，其他三个是高层封装**。

这一点重要，因为它意味着自定义 recognizer 只需要写一次，text / image / structured 三个模块自动受益。

## §5 核心架构：双层 + 可插拔

Presidio 的核心是**双层架构 + 可插拔**：

```
输入文本
   │
   ▼
┌─────────────────────────────────┐
│  AnalyzerEngine（识别层）          │
│  ├── RecognizerRegistry          │
│  │   ├── 内置 recognizer（YAML 注册）│
│  │   └── 自定义 recognizer 接口   │
│  ├── NlpEngine（spaCy / Stanza / transformers）│
│  └── 上下文增强与分数处理           │
└─────────────────────────────────┘
   │ 输出：RecognizerResult 列表
   ▼
┌─────────────────────────────────┐
│  AnonymizerEngine（编辑层）        │
│  ├── OperatorsFactory            │
│  │   ├── 10 个内置 operator       │
│  │   └── 自定义 operator 接口      │
│  └── 实体类型 → operator 映射       │
└─────────────────────────────────┘
   │ 输出：EngineResult（text + items）
   ▼
脱敏文本 + 编辑记录（反向识别用）
```

### 5.1 Analyzer：识别层做了什么

`AnalyzerEngine.analyze()` 接受文本和语言，返回 `RecognizerResult` 列表。每个 recognizer 只负责检测**一类或几类** PII 实体：

```python
from presidio_analyzer import AnalyzerEngine

analyzer = AnalyzerEngine()
results = analyzer.analyze(
    text="My phone number is 212-555-5555",
    entities=["PHONE_NUMBER"],
    language='en'
)
# [RecognizerResult(entity_type='PHONE_NUMBER', start=19, end=31, score=0.75)]
```

`RecognizerResult` 含 4 个字段：`entity_type`（如 `PERSON` / `PHONE_NUMBER` / `CREDIT_CARD`）、`score`（0-1 置信度，0.75 = 0.4 的正则基础分 + 上下文词 "number" 的加分）、`start` / `end`（在原文中的位置）。

关键设计：**Analyzer 不修改原文**。它只告诉你"哪里有 PII、是什么类型、有多确定"。直接好处——你可以用同一份 Analyzer 输出对接不同的编辑策略（生产环境用 encrypt，调试环境用 replace），**不需要重新跑识别**。

### 5.2 Anonymizer：编辑层做了什么

`AnonymizerEngine.anonymize()` 接受**文本 + Analyzer 输出 + operator 映射**，返回脱敏后的文本：

```python
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import RecognizerResult, OperatorConfig

engine = AnonymizerEngine()
result = engine.anonymize(
    text="My name is Bond, James Bond",
    analyzer_results=[
        RecognizerResult(entity_type="PERSON", start=11, end=15, score=0.8),
        RecognizerResult(entity_type="PERSON", start=17, end=27, score=0.8),
    ],
    operators={"PERSON": OperatorConfig("replace", {"new_value": "BIP"})},
)
# result.text == "My name is BIP, BIP"
```

`EngineResult` 含两个字段：`text`（脱敏后文本）和 `items`（`OperatorResult` 列表，记录每个被编辑实体的位置 / 类型 / operator / **编辑后的文本值**）。注意 `items` 里存的是编辑后的值——对 `replace` 是替身、对 `encrypt` 是密文——**不是原值**。这个细节决定了反向识别怎么做，§7.3 展开。

### 5.3 双层架构的工程意义

把"识别"和"编辑"拆成两层不是过度设计，是为了三件事：

第一，**职责分离**——识别逻辑和编辑逻辑各自独立演化。2.2.362 加了 `HuggingFaceNerRecognizer`（PR #1834），它**只**改识别层，编辑层一个字符都不动；用户加自定义 operator 也只改编辑层，识别层不动。

第二，**复用最大化**——5 个模块里，image-redactor 和 structured 都在内部复用 analyzer + anonymizer。底层 recognizer 加一个，所有上层模块自动受益。这也是为什么 release notes 里 "GPU Device Control"（PR #1844）和 "fix broken links" 这类**不相关**的改动会出现在同一个版本——它们分散在 5 个模块的独立 PR 里。

第三，**测试隔离**——识别层的测试是"输入文本、断言识别出哪些实体"，编辑层的测试是"输入文本 + 识别结果 + operator、断言脱敏后文本"。两层的 fixture（测试样本）可以完全独立维护。

## §6 Analyzer 详解：内置 recognizer 与 NLP 引擎

`RecognizerRegistry` 的运行时清单由 `conf/default_recognizers.yaml` 注册：**96 个 recognizer 条目，25 个默认启用，71 个默认禁用**（禁用的绝大多数是 country-specific recognizer，需要显式开启或用国家过滤启用）；加上 NLP 引擎侧的 recognizer，`predefined_recognizers` 包一共导出 103 个类。按检测机制分几大类：

| 类型 | 量级 | 例子 | 说明 |
|------|------|------|------|
| **通用 Pattern recognizer（regex + checksum）** | 10 个左右 | `CreditCardRecognizer` / `CryptoRecognizer` / `IbanRecognizer` / `IpRecognizer` / `EmailRecognizer` / `PhoneRecognizer` / `UuidRecognizer` | 强模式 PII，多数带 checksum 或格式校验 |
| **Country-specific recognizer** | 约 75 个 | `UsSsnRecognizer` / `DeTaxIdRecognizer` / `CaSinRecognizer` / `SePersonnummerRecognizer` | 各国身份证 / 税号 / 护照 / 医疗卡，默认大多禁用 |
| **NER recognizer** | 若干 | `SpacyRecognizer` / `StanzaRecognizer` / `TransformersRecognizer` / `HuggingFaceNerRecognizer` | 人名 / 地名 / 组织名，随 NLP 引擎接入 |
| **第三方 / 云服务 recognizer** | 少量 | Azure AI Language、LangExtract（含 Ollama 本地模型）等 | 通过 recognizer 接口接入外部检测能力 |

### 6.1 Pattern recognizer 的核心是 checksum

`CreditCardRecognizer` 不只是用正则匹配 16 位数字，它**先**匹配卡组织前缀正则（Visa / Mastercard / Amex / Discover 各自的前缀），**再**用 Luhn 算法验证。一个典型的坑：13 位 Unix 毫秒时间戳（`1748503543012` 这种）长得像卡号，早期版本会误判——这个修复（PR #1609）落在 2025-07 的 2.2.359。

2026 年新加的国家 recognizer 沿着同一条路走：`CaSinRecognizer`（Canadian SIN，2.2.363）用 Luhn；`ZaIdNumberRecognizer`（South African ID，2.2.363）用 Luhn 加出生日期校验；`PhTinRecognizer`（Philippines TIN，2.2.363）用加权 modulo 11；`DeTaxIdRecognizer`（Germany Steueridentifikationsnummer）用 ISO 7064 Mod 11,10；`SePersonnummerRecognizer`（Sweden，2.2.363）用 Luhn 变体并支持 samordningsnummer（coordination numbers）。

**这套设计的工程含义**：Presidio 不会把"看起来像 SSN"的东西都识别成 SSN——有官方 checksum 算法的证件做二次验证，显著压误报。US SSN 是个例外，它没有官方 checksum，`UsSsnRecognizer` 靠格式正则 + 上下文词 + 已知测试号段黑名单（如 `987-65-4320` 到 `987-65-4329`）来控制质量。代价是维护成本——每个国家一份 recognizer、一份校验规则。微软和社区坚持做这件事，因为把"长得像"都报出来，生产环境的误报会先把运营压垮。

### 6.2 NER recognizer 的可换引擎

Presidio 通过 `NlpEngine` 接口支持多种 NLP 引擎，`NlpEngineProvider` 按配置加载：

| 引擎 | 模型 | 速度 | 精度 | 备注 |
|------|------|------|------|------|
| **spaCy** | `en_core_web_lg`（默认） | 快 | 中 | 默认引擎 |
| **Stanza** | Stanford 神经 NLP | 慢 | 高 | 适合学术场景 |
| **transformers** | 任意 HuggingFace NER 模型 | 中 | 视模型而定 | `TransformersRecognizer` 走此引擎 |

`HuggingFaceNerRecognizer`（PR #1834 by `ultramancode`，2026-02-13 merged，随 2.2.362 发布）值得单独说。它**不依赖** NlpEngine，直接用 `transformers` 库加载 HuggingFace 上的 NER 模型（如 `dslim/bert-base-NER`、`Davlan/distilbert-base-multilingual-cased-ner-hrl`）。这意味着：

- 多语言 NER 不再被 spaCy 的多语言模型质量绑死
- GLiNER 这类专用 NER 模型可以直接接进 Presidio（官方还给它加了 ONNX Runtime 后端，2.2.362）
- 在自己数据上 fine-tune 的 NER 模型也能直接接

配套地，2.2.362 还加了 `PRESIDIO_DEVICE` 环境变量（PR #1844 by `RonShakutai`）：接受任意合法的 PyTorch device 字符串（`cpu`、`cuda:0`、`cuda:1`……），多 GPU 机器上部署多实例时可以指定各自用哪张卡，不用改代码。

**2.2.362 的另一个工程加固**：`REGEX_TIMEOUT_SECONDS` 环境变量给正则执行加超时（默认 60 秒），防灾难性回溯把 worker 卡死。PII 检测是典型的大量正则跑不可信输入的场景，这个默认值给得很实在。

### 6.3 RecognizerRegistry 的过滤机制

`RecognizerRegistry.load_predefined_recognizers()` 支持三种控制：

| 控制维度 | 参数 | 说明 |
|----------|------|------|
| **语言** | `supported_languages=["en", "de"]` | 只加载支持指定语言的 recognizer |
| **国家** | `countries=["us", "uk"]`（2.2.363 正式发布） | 只加载指定国家的 country-specific recognizer |
| **实体类型** | `entities=["PERSON", "PHONE_NUMBER"]` | 调用 analyzer 时限制要识别的类型 |

`countries` 过滤（PR #2000，修复 issue #1328）解决的是真实问题：country-specific recognizer 数量已经涨到 70+，全量加载浪费内存和初始化时间。机制上有三条规则值得记住：

1. 传了 `countries` 就只加载匹配国家的 recognizer，其余跳过并打 `WARNING` 日志；
2. **locale-agnostic recognizer（通用 regex 类）和未打国家标签的自定义 recognizer 永远加载**，不受过滤影响——这是向后兼容的承诺；
3. 同样的过滤也能写在 `default_recognizers.yaml` 的 `supported_countries` 字段里，不用改代码。

`RecognizerRegistry.get_country_codes()` 可以查当前已注册的国家代码。

## §7 Anonymizer 详解：10 个 operator 与反向识别

`AnonymizerEngine` 按 `OperatorsFactory` 的实际注册清单提供 10 个用户可调用的 operator，按"是否可逆"分两组。

### 7.1 不可逆 / anonymize operator（8 个）

`OperatorsFactory.ANONYMIZERS` 注册 7 个必装 operator，外加 1 个可选的 AHDS：

| Operator | 作用 | 例子 |
|----------|------|------|
| `replace` | 替换为固定值 | `James Bond` → `<PERSON>` |
| `mask` | 部分遮蔽 | `4532-1234-5678-9010` → `4532-****-****-9010` |
| `redact` | 完全删除 | `James Bond` → (空字符串) |
| `hash` | 哈希（sha256 / sha512） | `James Bond` → `a3f5b8c9...` |
| `encrypt` | AES-CBC 加密 | `James Bond` → 密文 |
| `custom` | 用户函数 | 任意自定义逻辑 |
| `keep` | 不修改 | 原样保留 |
| `ahds_surrogate`（可选） | 调 Azure Health Data Services 生成医学替身 | 需装 `azure-health-deidentification` SDK 并配置 Azure 凭证 |

两个容易踩的细节：`hash` 的 `salt` 参数如果手动指定，**必须至少 16 字节**，短了直接抛 `InvalidParamError`；不传 salt 则每个实体随机加盐——不可复现，拿哈希值做关联分析的部署要显式传 salt。`replace` 不给 `new_value` 时有默认行为：输出 `<{entity_type}>`（如 `<PERSON>`）。

### 7.2 可逆 / deanonymize operator（2 个）

`OperatorsFactory.DEANONYMIZERS` 注册的 2 个：

| Operator | 作用 | 说明 |
|----------|------|------|
| `decrypt` | 对称解密（`encrypt` 的反向） | 内置唯一自动可逆路径 |
| `deanonymize_keep` | 原样保留 | no-op，用于批量流程中放行不需要处理的实体 |

`AESCipher` 是 `Encrypt` / `Decrypt` 内部使用的工具类，不单独作为 operator 注册。

### 7.3 反向识别的真实机制

先纠正一个常见误解：`AnonymizerResult.items` **不是原值映射表**。读源码（`engine_base.py`）可以确认，`items` 里每个 `OperatorResult.text` 存的是**编辑后的文本**——`replace` 存替身、`encrypt` 存密文。原值没有存在结果里。

所以反向识别只有两条真实路径：

**路径一：encrypt / decrypt，内置自动可逆。** 密文嵌在文本里，`DeanonymizeEngine.deanonymize()` 按位置取出密文、用 key 解密：

```python
from presidio_anonymizer import DeanonymizeEngine
from presidio_anonymizer.entities import OperatorResult, OperatorConfig

deanonymizer = DeanonymizeEngine()
decrypted = deanonymizer.deanonymize(
    text="My name is S184CMt9Drj7QaKQ21JTrpYzghnboTF9pn/neN8JME0=",
    entities=[
        OperatorResult(start=11, end=55, entity_type="PERSON"),
    ],
    operators={"DEFAULT": OperatorConfig("decrypt", {"key": "WmZq4t7w!z%C&F)J"})},
)
# decrypted.text == "My name is Bond, James Bond"
```

但要清楚它的限制：`AESCipher` 用的是 **AES-CBC 加随机 IV**——同一个明文每次加密产生不同密文。这带来两个后果：加密是安全的（语义安全），但**同一个实体的多处出现不会得到同一个密文**。拿它做 LLM 替身，模型在不同轮次看到的是不同乱码，无法把它们关联为同一个人。encrypt 路径适合"一次性脱敏、事后授权恢复"的归档场景，不适合需要实体一致性的对话替身。

**路径二：replace 型替身，应用层自建映射表。** 替身稳定、短、可读（`<PERSON_1>`），但 Presidio 不保存原值——恢复靠应用层自己维护 原值 ↔ 替身 的映射，在 LLM 回复之后查表替换回去。这是生产上处理对话场景的主流做法，§8.1 给出完整骨架。

### 7.4 custom operator 的边界

`OperatorConfig("custom", {"lambda": lambda x: f"<REDACTED:{len(x)}>"})` 看似简单，有 3 个边界要注意。

**第一个**（issue [#2024](https://github.com/data-privacy-stack/presidio/issues/2024)，已修复）：早期版本的 `validate()` 会用 dummy 值 `"PII"` 调用用户 lambda 一次。如果 lambda 是**有状态**的（比如内部维护 token 计数），这次 dummy 调用会污染状态。修复后的 `validate()` 只检查 callable，不再调用 lambda，返回类型检查移到 `operate()` 的真实数据调用上。

**第二个**：lambda 接收原文本片段、**必须返回 `str`**，返回其他类型会抛 `InvalidParamError`。需要携带更多元信息时，用闭包把状态放在 lambda 外面（§8.1 就是这么做的）。

**第三个**：`replace` 的替身是固定值——所有 `PERSON` 实体都会变成同一个 `new_value`。想要 `<PERSON_1>`、`<PERSON_2>` 这种带编号的替身，得用 `custom` operator 自己维护计数器，Presidio 内置没有这个机制。

## §8 LLM 集成模式：替身回路

Presidio 在 LLM 系统里的标准位置是"上游去识别 + 下游反向识别"。这一节把 §3 的总览图落成一个可运行的骨架，并把容易翻车的地方说透。

### 8.1 一个医疗对话助手的完整回路

场景：医院部署 AI 助手，医生用自然语言查询病历。LLM 不能直接看到病历原文（HIPAA 合规），但答案要能指名道姓——"患者张三的最近一次血压"。

直接用中文跑 Presidio 需要先给 analyzer 配中文 NLP 模型（如 spaCy 的 `zh_core_web_md`）并补中文 recognizer；下面用英文文本演示默认安装（`en_core_web_lg`）就能跑通的最小路径，机制完全相同。

```python
import re

from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig

analyzer = AnalyzerEngine()      # 默认加载 spaCy en_core_web_lg
anonymizer = AnonymizerEngine()

# 替身表：应用层自己维护。同一原值永远映射到同一替身；
# 生命周期 = session 生命周期，跨进程要持久化到 Redis / 数据库。
surrogate_map = {}               # (entity_type, 原值) -> 替身

def stable_surrogate(entity_type: str):
    def anonymize(original: str) -> str:
        key = (entity_type, original)
        if key not in surrogate_map:
            surrogate_map[key] = f"<{entity_type}_{len(surrogate_map) + 1}>"
        return surrogate_map[key]
    return anonymize

# 1. 病历入库前去识别
record = "Patient James Bond was admitted for hypertension on March 7, 1990."
anonymized = anonymizer.anonymize(
    text=record,
    analyzer_results=analyzer.analyze(text=record, language="en"),
    operators={
        "PERSON": OperatorConfig("custom", {"lambda": stable_surrogate("PERSON")}),
        "DATE_TIME": OperatorConfig("keep"),
    },
)
# anonymized.text == "Patient <PERSON_1> was admitted for hypertension on March 7, 1990."

# 2. 医生提问同样去识别。替身表共享，"James Bond" 拿到的仍是 <PERSON_1>，
#    LLM 才能把问题和病历对上
query = "What is James Bond's latest blood pressure?"
query_anonymized = anonymizer.anonymize(
    text=query,
    analyzer_results=analyzer.analyze(text=query, language="en"),
    operators={"PERSON": OperatorConfig("custom", {"lambda": stable_surrogate("PERSON")})},
)
# query_anonymized.text == "What is <PERSON_1>'s latest blood pressure?"

# 3. 病历 + 问题一起送 LLM（替身一致），LLM 只见替身
# llm_output 形如 "<PERSON_1>'s latest blood pressure was 140/90 mmHg."

# 4. 反向：应用层查表把替身换回原值
def deanonymize_surrogates(text: str) -> str:
    def restore(match: re.Match) -> str:
        for (_, original), token in surrogate_map.items():
            if token == match.group():
                return original
        return match.group()
    return re.sub(r"<[A-Z_]+_\d+>", restore, text)

# deanonymize_surrogates(llm_output)
# == "James Bond's latest blood pressure was 140/90 mmHg."
```

**关键工程点**：

1. **替身表必须跨阶段、跨轮次共享**——同一个"张三"在病历和提问里必须得到同一个替身，否则 LLM 无法建立关联。表的生命周期等于 session 生命周期，重启即失效，要持久化。
2. **query 端也要去识别**——医生问"患者张三"，不去识别的话真名直接进了 LLM 上下文，模型回复里可能原样引用"张三"，整个回路就漏了。
3. **反向不需要重新跑 NER**——替身是规则生成的固定 token，用正则精确定位再查表即可；在 LLM 输出上重跑 analyzer 既慢又不可靠。
4. **为什么不用内置的 encrypt/decrypt 做对话替身**——CBC 随机 IV 让同一人名每次产生不同密文（§7.3），破坏实体一致性。decrypt 路径留给归档恢复。

### 8.2 与 LLM guardrail 的集成

Presidio 是 guardrail 的"输入清洗层"，但**不是** guardrail 本身。一个完整 LLM guardrail 通常含 5 层：

```
LLM guardrail 5 层
│
├── 1. 输入清洗：Presidio 去识别（PII 替换 / 掩码）
├── 2. 提示词注入检测：rebuff / prompt-guard / lakera
├── 3. 内容审核：OpenAI moderation / 自定义分类器
├── 4. 输出清洗：替身换回真名（Presidio + 应用层替身表）
└── 5. 审计日志：记录所有 PII 检测 + operator 选择
```

Presidio 占第 1 和第 4 层。它不解决提示词注入、不解决内容审核、不解决越狱。**试图让 Presidio 兼任所有 5 层的项目会失败**——它的设计目标就是"识别 + 编辑 PII"，不超出这个范围。

### 8.3 失败模式

匿名化 LLM 系统的 3 个常见失败模式：

**替身不一致**——一个 session 里 anonymize 阶段生成了 `<PERSON_1>`，session 重启后替身表丢了，新一轮给同一个张三生成了 `<PERSON_5>`。用户看到 "你之前问的 <PERSON_1> 信息是 X，今天 <PERSON_5> 信息是 Y"，两个不同替身指同一个人。修复：替身表持久化到 session store。

**LLM 改写替身**——LLM 收到 `<PERSON_1>` 后，回复时可能改成 `<患者 1>` 或 `the patient` 或 `Patient-001`。反向阶段按固定 token 查表就会漏。修复：在 system prompt 里明确"必须原样使用 `<PERSON_1>` 格式"；或者反向之前用 fuzzy match 找回被改写的替身。

**替身冲突**——病历里有两个同名患者（父子都叫 James Bond），都识别成 `PERSON`。按"实体类型 + 原值"做 key 的替身表会给两个同名的人生成**同一个**替身，LLM 回复时就分不清哪个是哪个。修复：key 里加入下文区分（病历 ID + 人名），或用 `<PATIENT_FATHER_1>` / `<PATIENT_SON_1>` 这种带上下文前缀的替身。

## §9 DICOM 与多模态：医学影像的 PII 处理

Presidio 的 image redactor 不只是"OCR 文字 + 识别"——它对 DICOM 医学影像有专门的处理路径，也有明确的边界。

### 9.1 标准图像 PII 路径

`ImageRedactorEngine` 处理普通图像（PNG / JPG）的 pipeline：

1. **OCR**：Tesseract 提取图像中的文字（官方文档注明 "For best performance, please use the most up-to-date version of Tesseract OCR. Presidio was tested with **v5.2.0**"；另支持接入 Azure Document Intelligence 作为 OCR 引擎）
2. **识别**：OCR 文本送 `presidio-analyzer`（复用底座，零额外配置）
3. **涂黑**：按识别结果的坐标在原图上画出遮盖矩形（fill 可选 `contrast` 或 `background`）

**关键设计**：image redactor 不自己实现识别逻辑——它**直接 import analyzer**。你在 analyzer 层加的 recognizer，image redactor 自动支持。注意图像路径不经过 anonymizer 的文本 operator：图像的"编辑"是按坐标涂黑，不是文本替换。

### 9.2 DICOM 医学影像路径

`DicomImageRedactorEngine` 处理 DICOM 影像（CT / MRI / X-ray）：

1. **像素级 OCR**：从 DICOM 影像的**像素**里提取文字（与普通图像 OCR 相同）
2. **涂黑像素文字**：在像素上遮盖
3. **元数据不归它管**：DICOM 文件 header 里有大量 PII（patient name、patient ID、study date、institution name、referring physician）——这部分**不能靠涂黑**完成

官方文档在 `DicomImageRedactorEngine` 的说明里写得非常直白：

> "This class only redacts pixel data and does not scrub text PII which may exist in the DICOM metadata. We highly recommend using the DICOM image redactor engine to redact text from images BEFORE scrubbing metadata PII."

**重要顺序**：先做图像去识别（`DicomImageRedactorEngine`），**再做** metadata scrub（用 `pydicom` 之类的库改 DICOM header）。Presidio 自己不做 metadata scrub——DICOM 的 tag 集合是标准化的大字典，业务相关性强，通用框架不适合硬编码。

医疗 AI 项目的常见错误：用 `DicomImageRedactorEngine` 处理了像素就以为 PII 去干净了，结果 DICOM header 里还留着 patient name、study date——放射科系统读取时直接暴露。**这是 HIPAA 合规的真实风险**。

### 9.3 DICOM 的生产部署建议

| 步骤 | 工具 | 责任 |
|------|------|------|
| 1. DICOM 接收 | PACS / DICOM router | 医院 IT |
| 2. 像素去识别 | `DicomImageRedactorEngine` | Presidio |
| 3. **metadata scrub** | `pydicom` 自定义脚本 | 医院 IT（Presidio 之外） |
| 4. 加密 + 访问日志 | 存储系统 | 医院 IT |
| 5. 训练用数据集导出 | 上面的完整 pipeline | ML 团队 |

元数据 scrub 有一个借力的写法：`pydicom` 把 header 转成 dict 后，可以喂给 `presidio-structured` 的 `StructuredEngine` 做字段级脱敏。但要清楚 presidio-structured 的定位——它是面向 DataFrame / dict 的通用表格脱敏引擎，靠"字段名 → PII 实体类型"的映射工作；**DICOM header 转 dict、再配一份字段映射，是应用层的组装工作**，Presidio 不内置 DICOM 元数据支持。

## §10 benchmark 与适用边界

Presidio 的 README 第一段有一个关键警告：

> "Presidio can help identify sensitive/PII data in un/structured text. However, because it is using automated detection mechanisms, there is no guarantee that Presidio will find all sensitive information. Consequently, additional systems and protections should be employed."

这一节解释怎么评估它、边界在哪。

### 10.1 Presidio 没有"官方 benchmark"

Presidio 不是 ML 模型，它是规则 + 模型的混合系统，官方没有发布统一的精度基准。评估它要按"召回率 / 误报率"的工程指标来，而且结论高度依赖场景：

- **英文 + 标准 PII**（人名、SSN、信用卡、电话）：checksum 和上下文增强压得住误报，表现最好
- **非标准 PII**（拼写变体、罕见格式的 ID）：regex 和 NER 都会漏，召回率明显下降
- **多语言**（中文 / 日文 / 阿拉伯文）：取决于 NER 模型质量，中文需要自配模型和 recognizer
- **OCR 文本**（来自图像）：Tesseract 的错误率叠加 Presidio 的错误率，**双重损耗**

**工程含义**：英文 + 标准 PII 的表现**不直接迁移**到中文 / OCR 场景——中文项目通常要自己跑一轮标注集实测，OCR 场景还要再打折扣。这不是 Presidio "变差了"，是叠加误差。把它接进生产前的标准动作是：用自己业务的样本建一个小评测集（官方有 evaluation 框架和 `presidio-research` 可用），量出自己场景的召回率。

### 10.2 适用边界

| 场景 | 适合 Presidio | 不适合 Presidio |
|------|---------------|-----------------|
| LLM 上游去识别 | ✅ 主流 PII 覆盖好 | ❌ 不能当 100% 兜底 |
| 用户上传文件 PII 扫描 | ✅ 文本 / 图像 / 结构化都支持 | ❌ 复杂嵌套 PII（如 PDF 嵌套图像）漏识别 |
| 客服录音 / 视频转写 | ✅ 转写后文本走 Presidio | ❌ 转写阶段就丢的 PII 救不回来 |
| 医疗 DICOM | ✅ 像素处理 | ❌ 元数据 scrub 必须自己写 |
| 金融交易 | ✅ 信用卡 / 账号 / IBAN | ❌ 业务相关敏感字段（如内部账户 ID）必须自定义 recognizer |
| 法律文书 | ⚠️ 实测为准 | ❌ 复杂法律术语误报风险高 |
| 中文 / 阿拉伯文 | ⚠️ 依赖 NER 模型质量 | ❌ 没有高质量 NER 模型时表现差 |
| 100% 兜底 | ❌ README 原话：no guarantee | ❌ 不能用 Presidio 当唯一合规层 |

### 10.3 Presidio 不是银弹

把这件事说清楚：**Presidio 的工程价值是把 PII 暴露风险压到很低的水平，不是消除风险**。任何宣称"用 Presidio 就 HIPAA 合规 / GDPR 合规"的说法都站不住脚。

合规的真实工程栈：

```
完整 PII 合规栈
│
├── Presidio：检测 + 编辑（自动层主力）
├── 业务白名单：已知安全的输入 / 输出路径
├── 人审环节：低置信度 PII 的人工确认
├── 业务自检：业务相关敏感字段（Presidio 不认识）
├── 加密 / 访问控制：即使 Presidio 漏了，访问也受限
└── 审计 + 监控：发现 Presidio 漏判的反馈环
```

Presidio 是这个栈的"自动层"，不是"全部"。

## §11 决策矩阵：哪些团队先上 Presidio，怎么和 LLM 集成

### 11.1 4 类团队的采用顺序

| 团队类型 | 建议阶段 | 集成方式 | 复杂度 |
|----------|----------|----------|--------|
| **已经用 LLM 处理用户数据但没去识别** | **立刻上** | analyzer + anonymizer 串在 LLM 上游 | 低（pip install presidio-analyzer presidio-anonymizer） |
| **在做医疗 AI / 法律 AI / 金融 AI** | 上 Presidio + 业务白名单 | Presidio + 自定义 recognizer + DICOM / 业务字段 mapping | 中（要写 custom recognizer） |
| **在做客服 / 文档处理 / 内部知识库** | 上 Presidio | analyzer + 定期 batch 扫描文档库 | 低 |
| **只用 LLM 跑内部研发 / 论文分析** | **不上** | 数据本来就不含 PII | n/a |

**第一类**（已经在 LLM 上跑用户数据但没去识别）**是 Presidio 最高优先级的目标用户**。这一类团队的工程风险是直接的——一次 LLM 日志泄露、一次 prompt cache 暴露，就可能违反 GDPR / HIPAA / 个人信息保护法。Presidio 是 1-2 天能集成的合规层，ROI 极高。

**第二类**（医疗 / 法律 / 金融）必须上 Presidio + 业务白名单 + 人审环节。**业务白名单**是 Presidio 之外的层——例如医疗 AI 项目除了 Presidio 检测的 SSN / 姓名，还有"特殊病种标记"（如 HIV 阳性标记）这类业务字段，Presidio 不认识。

**第三类**（客服 / 文档处理）适合**离线批量**用 Presidio——每天扫一次客服工单库，标记含 PII 的工单，自动脱敏存档。比"每个请求实时过 Presidio"成本低很多。

**第四类**（纯内部研发）**不上**。Presidio 是处理 PII 的工具，数据里没有 PII 就别浪费算力。

### 11.2 集成模式的复杂度梯度

| 集成模式 | 复杂度 | 适用场景 | 注意事项 |
|----------|--------|----------|----------|
| **离线 batch 扫描** | 低 | 文档库 / 工单库定期脱敏 | Presidio HTTP 服务 + cron |
| **LLM 上游去识别（单向）** | 中 | LLM 输入清洗（不需要恢复真名） | anonymize 一次即可 |
| **LLM 双向替身回路** | 高 | LLM 回复要把替身换回真名 | §8.1 的替身表 + §8.3 的失败模式都要处理 |
| **图像 / DICOM pipeline** | 高 | 医疗 / 法律文档处理 | §9.2 的 metadata scrub 必须自己写 |
| **结构化数据脱敏** | 中 | 数据库导出 / 备份 | presidio-structured + 字段映射 |

**复杂度建议**：先上"离线 batch 扫描"（低复杂度、立竿见影），再上"LLM 上游去识别（单向）"（中复杂度、覆盖大多数用例），最后才考虑"LLM 双向替身回路"或"DICOM pipeline"（高复杂度、需要专门工程化）。

不要**直接**上"双向替身回路"——替身表持久化、跨 session 一致性、LLM 改写替身、同名冲突 4 个坑没踩过的话，会出现"用户看到的名字对不上"这种严重 UX 问题。

## §12 与同类工具的对比

Presidio 在 PII 编辑领域的事实标准地位来自**完整度**，不是单点性能。和同类工具的对比：

| 工具 | 文本 | 图像 | 结构化 | DICOM | NLP 引擎 | 自定义 recognizer | License |
|------|------|------|--------|-------|----------|-------------------|---------|
| **Presidio** | ✅ | ✅ | ✅ | ✅ | spaCy / Stanza / transformers | ✅ 多种接口 | MIT |
| **scrubadub** | ✅ | ❌ | ❌ | ❌ | spaCy | ✅ regex | MIT |
| **faker** | ❌（生成假数据）| ❌ | ❌ | ❌ | n/a | ❌ | MIT |
| **AWS Comprehend PII** | ✅ | ❌ | ❌ | ❌ | 闭源 | ❌ | 商业 |
| **GCP DLP** | ✅ | ✅ | ✅ | ❌ | 闭源 | ✅（有限） | 商业 |

**Presidio 的不可替代点**：

1. **DICOM 像素处理**——在主流开源 PII 工具里很少见
2. **HuggingFace NER 直接推理**——2.2.362 起多语言 NER 不再被 spaCy 绑死
3. **多模态共用同一套底座**——text / image / structured 共用同一套 recognizer + operator
4. **MIT 协议**——商业部署零授权成本

**Presidio 不擅长的**：

1. **超大规模吞吐**——内部是 Python + spaCy，单实例吞吐不如商业 DLP API
2. **黑盒语义识别**——商业 DLP 用更大的模型做语义级识别，Presidio 主要是规则 + 轻量 NER
3. **托管服务**——Presidio 是自部署，AWS / GCP 用户更愿意用托管服务

## §13 项目状态：微软 → Data Privacy Stack

文章写作时（2026-06）这还是一个进行中的公告；现在（2026-09）移交已经落地。README 顶部第一行就是迁移提示，2.2.363/2.2.364 完成了实际的搬迁：

- **仓库**：`microsoft/presidio` → `data-privacy-stack/presidio`（GitHub 旧地址 301 重定向）
- **文档站**：迁到 presidio.dataprivacystack.org（data-privacy-stack.github.io）
- **容器镜像**：从 Microsoft Container Registry 迁到 `ghcr.io/data-privacy-stack`
- **法务身份**：LICENSE 版权行从 "Microsoft Corporation" 改为 "Presidio Contributors"，联系邮箱改为 presidio@dataprivacystack.org

**这件事的工程意义**：

1. **路线图不再由微软单方面决定**——演进由 Data Privacy Stack 社区组织接手，release 节奏由社区 PR 推动（2.2.362 到 2.2.364 之间明显加快，社区贡献者占比很高）
2. **企业采用的风险敞口变化**——"微软维护"的隐性背书没了，换成了社区组织的 governance。好在迁移不是断崖：代码库、文档、发布流水线连续，CHANGELOG 里能看到迁移是有条不紊的批量 PR
3. **贡献通道更开放**——2026 年的 release notes 里新 recognizer 几乎全部来自社区贡献者（DE、SE、CA、ZA、PH、TR、ES 等国家模块），这个趋势在社区化之后只会更强

**给企业的具体建议**：

- 如果是**新建**项目：Presidio 仍然是功能最全的开源 PII 框架，把"社区治理"纳入常规供应商风险评估即可，不必恐慌
- 如果是**已有**项目：继续用，关注 release 节奏变化，fallback 计划里保证业务白名单层的可移植性
- 如果是**严肃医疗 / 金融**项目：Presidio + 业务白名单 + 商业 DLP 兜底，不要把 Presidio 当单一依赖

## §14 启示：5 条工程经验

读完 Presidio 的代码、文档和 release notes，5 条对 AI 工程团队可复用的经验。

### 14.1 拆分检测与编辑是 PII 系统的底层结构

Presidio 的双层架构（Analyzer 识别 + Anonymizer 编辑）不是过度设计，是 PII 系统的**最小可工作单元**。任何 PII 编辑库都不可避免有这两层——区别只在命名和接口清晰度。

**反模式**：把识别和编辑揉在一个函数里，函数直接返回脱敏后的文本——没法在生产环境和调试环境用不同的编辑策略（生产 encrypt、调试 replace），没法复用识别结果做日志分析。

**正路**：识别返回结构化结果（`RecognizerResult` 列表），编辑接收结构化结果 + 文本 + operator 配置。**两个步骤独立演化、独立测试**。

**什么时候该拆**：所有"先识别后处理"的场景——PII 编辑、内容审核、敏感字段标记、告警去重。

### 14.2 checksum 是降低误报的关键

Presidio 的 country-specific recognizer 里，凡是有官方校验算法的证件都做了 checksum 验证：CA SIN 走 Luhn、ZA ID 走 Luhn + 出生日期、PH TIN 走 modulo 11、DE Tax ID 走 ISO 7064。US SSN 没有官方 checksum，就用格式 + 上下文 + 测试号段黑名单补位。**这是 Presidio 控制误报的核心手段**——光靠 regex，"长得像"的字符串全会中招；加校验后误报被压到可运营的水平。

**反模式**：一个 regex 匹配所有看起来像 ID 的字符串 → 把 `1234567890123`（13 位数字）当 SSN，结果是误报灾难。

**正路**：regex 候选 → checksum 验证 → 上下文词加权 → 输出。

**什么时候该用**：所有"有官方标准格式"的数据——身份证、信用卡、税号、银行账号、IBAN、ISBN。各国标准格式有现成 checksum 算法，**不要用通用 regex 凑合**。

### 14.3 LLM 替身回路的关键是替身表，不是工具本身

Presidio 的内置可逆能力只有 encrypt/decrypt，而且 CBC 随机 IV 决定它给不了实体一致性。真正让对话替身回路 work 的，是应用层那张**原值 ↔ 替身**的映射表——它决定了同一实体能否跨轮次保持同一替身。

**反模式**：每次 deanonymize 都重新生成替身 → 同一个张三在 session 1 是 `<PERSON_1>`、在 session 2 是 `<PERSON_5>`，用户看到两个替身指同一个人。

**正路**：anonymize 阶段把替身表存进 session store（Redis / 数据库），反向阶段查同一张表。**替身表的生命周期 = session 生命周期**。

**什么时候该持久化**：所有 multi-turn 对话、所有跨 session 引用、所有人审环节。

### 14.4 多模态共用同一套底座

Presidio 的 image redactor **直接 import** analyzer。analyzer 加一个 recognizer，image redactor 自动支持。

**反模式**：每个模态（text / image / structured / audio）实现一套独立的 PII 检测 → 新加一个 recognizer 要改 4 个地方，漏改一处就是漏识别。

**正路**：模态层只做"提取文本"（OCR / speech-to-text / 字段名映射），文本层共用同一套 recognizer + operator。

**什么时候该共用**：所有 PII 编辑系统。Presidio 的实现就是 reference architecture。

### 14.5 自动检测不是 100% 兜底

Presidio README 自己的警告：

> "there is no guarantee that Presidio will find all sensitive information. Consequently, additional systems and protections should be employed."

这条警告**应该**出现在所有 PII 编辑工具的 README 里——但大多数工具把这条警告藏在小字。

**反模式**：宣传"PII 100% 检测" → 用户拿单一工具当合规层 → 漏判的那一小部分直接变成事故。

**正路**：Presidio + 业务白名单 + 人审环节 + 加密 + 审计监控，**多层叠加**才是合规的完整答案。

**什么时候必须叠加**：所有"违规会出事故"的场景——医疗、法律、金融、儿童产品。**Presidio 是必要条件，不是充分条件**。

## §15 给读者的下一步建议

读完 Presidio 的代码和文档，给三类读者一个直接的下一步建议。

**如果你是 LLM 应用开发者，现在要处理用户数据**：

1. 第一步：`pip install presidio`（2.2.362 起有官方元包，同时装上 analyzer 和 anonymizer），跑通 §8.1 的替身回路
2. 第二步：把 anonymize 串到 LLM 上游，**暂时不做反向**（单向模式）
3. 第三步：上线 1 周后，**审计 100 条 LLM 交互**——Presidio 漏判的有多少、误判的有多少
4. 第四步：根据审计结果补自定义 recognizer / 业务白名单
5. 第五步：上线 1 个月后，加替身表反向回路

**如果你是医疗 / 金融 / 法律 AI 项目负责人**：

1. 第一步：评估业务相关敏感字段（Presidio 不认识的字段）——列清单
2. 第二步：为每个业务字段写 custom recognizer（文档有多种接口）
3. 第三步：设计"Presidio + 业务白名单 + 人审"3 层 pipeline
4. 第四步：DICOM 项目按 §9.3 的 5 步走完（特别是 metadata scrub 不要忘）
5. 第五步：HIPAA / GDPR / 个保法合规审计——Presidio 是必要条件不是充分条件

**如果你是研究 LLM 安全 / 数据隐私的学者**：

1. 第一步：读 `presidio_analyzer/recognizer_registry/` 和 `presidio_anonymizer/operators/`——看它怎么把规则和模型组合
2. 第二步：用 presidio-research 测 Presidio 在你关心的多语言 / 多场景下的召回率
3. 第三步：把 Presidio 当 baseline，对比你的新方法
4. 第四步：关注 `HuggingFaceNerRecognizer` 之后的演进——多语言 NER 是 2026 的热点
5. 第五步：参与社区治理——项目已经移交 Data Privacy Stack，贡献通道在打开

### 自测：5 条经验对照

1. 你的 PII 系统里，识别和编辑是分两层还是糊在一个函数里？
2. 你的 ID 字段识别是 regex 候选 + checksum 验证，还是只看正则？
3. 你的 LLM 替身回路里，替身表是持久化到 session store，还是每次重新生成？
4. 你的多模态 PII 系统（text / image / structured）共用同一套底座，还是各写一套？
5. 你的 PII 系统在自己业务样本上实测的召回率是多少？漏判部分靠什么层兜底？

如果任何一道题的答案是"糊" / "只看正则" / "每次重新生成" / "各写一套" / "我没测过"，对应的那节值得回头细读。

---

**参考来源**：

- GitHub 仓库：github.com/data-privacy-stack/presidio（原 microsoft/presidio，2026-09 核实：10.8k stars / 1.28k forks / MIT）
- 项目首页：presidio.dataprivacystack.org（文档站，data-privacy-stack.github.io/presidio）
- 关键文档：`docs/analyzer/index.md`、`docs/anonymizer/index.md`、`docs/image-redactor/index.md`、presidio-structured `README.md`
- Release（GitHub Releases 页核实）：2.2.359（2025-07-06，CreditCard 13 位时间戳修复 #1609）、2.2.361（2026-02-12）、2.2.362（2026-03-18：HuggingFaceNerRecognizer #1834、PRESIDIO_DEVICE #1844、REGEX_TIMEOUT_SECONDS、presidio 元包）、2.2.363（2026-06-28：countries 过滤 #2000、品牌与仓库迁移、CA/SE/PH/ZA/DE/TR/ES recognizer）、2.2.364（2026-07-22：CLI --threshold、License 更新）
- 持续演进：CHANGELOG unreleased 段（UuidRecognizer、BatchDeanonymizeEngine、NoOpNlpEngine、ZA/PH 系列 recognizer 扩充、custom operator #2024 修复）
- 项目治理：README 迁移公告与 docs/project_transition.md（微软 → Data Privacy Stack）
- 内部设计：5 个子项目；`default_recognizers.yaml` 注册 96 个 recognizer（25 个默认启用）；`predefined_recognizers` 包 103 个类；`OperatorsFactory` 注册 8 个 anonymize + 2 个 deanonymize operator
