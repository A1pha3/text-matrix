---
title: "Presidio：企业 AI 数据合规的事实标准"
date: "2026-06-25T15:18:21+08:00"
slug: "microsoft-presidio-pii-deidentification-framework-2026"
description: "Presidio 把 PII 识别 + 编辑 + 反向编辑做成可插拔的事实标准，5 个模块（Analyzer / Anonymizer / Image Redactor / Structured / CLI）覆盖文本、图像、DICOM 与结构化数据。它不只是脱敏工具，是企业 AI 数据处理流水线的合规基础设施。本文拆开双层架构、182 个内置 recognizer、10 个 operator、DICOM 医学影像脱敏、与 LLM 双向编辑的反向回路，并给出 4 类团队的采用顺序。"
draft: false
categories: ["技术笔记"]
tags: ["Presidio", "PII", "De-identification", "Microsoft", "Anonymization", "DICOM", "spaCy", "HuggingFace", "AI Compliance", "Data Privacy"]
hiddenFromHomePage: false
---

# Presidio：企业 AI 数据合规的事实标准

## §1 先给判断

如果一家公司在 2026 年还在用 LLM 处理用户数据，却**没有**用 presidio 之类的东西在 prompt 出去之前把姓名、身份证、信用卡号、SSN、电话号码去掉，那它要么没真跑过生产负载，要么把合规外包给法务了。

presidio 不只是 "一个 PII 编辑库"。它是把 PII 检测、脱敏、反向脱敏做成可插拔框架的事实标准——5 个子项目、182 个内置 recognizer、10 个内置 operator（8 anonymize + 2 deanonymize），覆盖文本、图像、DICOM（Digital Imaging and Communications in Medicine，医学数字成像与通信标准）医学影像和结构化数据。这套东西放在 LLM 上游做去识别，在下游做反向识别，让模型"看到的是替身"但"回复给用户的是真名"。

GitHub 上 9.6k stars、1.16k forks、MIT 协议、2018-05-04 创建，2026-03-18 还在发 2.2.362 release。**这不是一个被放弃的旧库**——它在 2026 年仍然是企业 AI 合规的事实标准，最近一次发版还加了 HuggingFace NER Recognizer 和 GPU device 环境变量控制。

这篇文章拆开 presidio 的 5 个模块、双层架构（Analyzer 识别 + Anonymizer 编辑）、与 LLM 的双向编辑回路、DICOM 医学影像处理、182 个 recognizer 的可插拔机制，并给 4 类团队一个明确的采用顺序。

## §2 阅读路径

- **只想看结论**：§3 总览图 → §4 5 个模块 → §11 决策矩阵
- **想看核心架构**：§5 双层架构 → §6 Analyzer 182 个 recognizer → §7 Anonymizer 10 个 operator
- **想看 LLM 集成模式**：§8 LLM 双向编辑回路 → §9 一个医疗对话的完整 pipeline
- **想看工程边界**：§10 benchmark 与适用边界 → §11 决策矩阵
- **第一次读**：按顺序读，§3 + §8 + §11 是最值得细读的三节

## §3 系统地图：presidio 在 AI 数据处理流水线里到底做什么

在展开细节之前，先把 presidio 放在一个完整的 AI 数据处理流水线里看。

```
完整 AI 数据处理流水线
│
├── 数据入口
│   ├── 用户输入（chat / 表单 / 邮件 / 上传文件）
│   ├── 业务系统（CRM 工单 / 客服录音转写 / 病历 OCR）
│   └── 文档库（PDF / Word / 邮件归档 / 数据库导出）
│
├── presidio 去识别层（这是本文焦点）
│   ├── presidio-analyzer
│   │   ├── 182 个内置 recognizer（regex / NER / rule / checksum）
│   │   ├── 自定义 recognizer 接口（4 种）
│   │   ├── NLP 引擎：spaCy（默认）/ HuggingFace / Stanza
│   │   └── 输出：RecognizerResult 列表（entity_type / score / start / end）
│   │
│   ├── presidio-anonymizer
│   │   ├── 10 个内置 operator（replace / mask / redact / encrypt / hash / ...）
│   │   ├── 自定义 operator 接口
│   │   ├── 反向编辑（deanonymize）：decrypt / deanonymize_keep
│   │   └── 输出：AnonymizerResult（text / items）
│   │
│   ├── presidio-image-redactor
│   │   ├── OCR（Tesseract v5.2.0）→ 文本 PII
│   │   ├── 走 presidio-analyzer 识别 + presidio-anonymizer 编辑
│   │   ├── DICOM 医学影像：像素级 + 元数据 PII
│   │   └── 输出：去识别后图像
│   │
│   ├── presidio-structured
│   │   ├── 表格 / JSON 字段扫描
│   │   ├── 字段名 → PII 实体类型映射
│   │   └── 输出：脱敏后 DataFrame / dict
│   │
│   └── presidio-cli
│       └── 命令行工具
│
├── LLM 处理层
│   ├── 主流模型：GPT-4o / Claude 3.7 / Gemini 2.0
│   ├── 收到的是 presidio 替身
│   └── 不接触真实 PII
│
└── 反向识别层
    ├── presidio deanonymize 路径
    └── 用户看到真实姓名 / 卡片尾号 / 地址
```

**关键边界**：presidio 的工作是把"真实 PII" 转换成 "LLM 看得懂的替身 + 反向映射表"。LLM 处理过程中**永远不会看到真实 PII**——它看到的是 `My name is <PERSON_1> and my card is <CREDIT_CARD_1>`，回复时 `AnonymizerEngine.deanonymize()` 把替身换回原值再交给用户。

这个边界不是 presidio 自身吹的——它写在 README 第一段、写在 `Anonymizer` 的设计上、写在 `deanonymize_keep.py` 的代码注释里：**"Presidio can help identify sensitive/PII data in un/structured text. However, because it is using automated detection mechanisms, there is no guarantee that Presidio will find all sensitive information."**

翻译一下：presidio 是 95% 召回率（recall）的工具，不是 100% 兜底。生产部署时它必须和别的合规层（人审 / 正则补充 / 业务白名单）一起用，**不能单独指望它**。

## §4 仓库拓扑：5 个子项目怎么拆

| 子项目 | 角色 | 核心 API | 部署形态 |
|--------|------|----------|----------|
| **presidio-analyzer** | PII 识别 | `AnalyzerEngine.analyze()` | Python lib / HTTP 5002 |
| **presidio-anonymizer** | PII 编辑（10 个 operator）| `AnonymizerEngine.anonymize()` / `DeanonymizeEngine.deanonymize()` | Python lib / HTTP 5001 |
| **presidio-image-redactor** | 图像 PII | `ImageRedactorEngine` / `DicomImageRedactorEngine` | Python lib / HTTP 5003 |
| **presidio-structured** | 表格 / JSON PII | `StructuredEngine` | Python lib |
| **presidio-cli** | 命令行 | `presidio` | CLI |

仓库根目录把这些子项目作为独立 Python package 发布，每个都有自己的 `pyproject.toml`、`README.MD` 和 Docker 镜像。根目录额外提供 `docker-compose.yml`（text 编排）、`docker-compose-image.yml`（image redactor）、`docker-compose-transformers.yml`（HuggingFace NER 编排）三个 compose 文件，覆盖主流部署场景。

**关键设计**：5 个子项目不是 5 个独立服务，它们之间有明确依赖关系。`presidio-image-redactor` 内部直接调用 `presidio-analyzer` + `presidio-anonymizer` 处理 OCR 出来的文本；`presidio-structured` 内部调用 analyzer 识别字段 PII 类型、再调用 anonymizer 编辑。**analyzer + anonymizer 是底座，其他三个是高层封装**。

这一点重要，因为它意味着自定义 recognizer 只需要写一次，text / image / structured 三个模块自动受益。

## §5 核心架构：双层 + 可插拔

presidio 的核心是**双层架构 + 可插拔**：

```
输入文本
   │
   ▼
┌─────────────────────────────────┐
│  AnalyzerEngine（识别层）          │
│  ├── RecognizerRegistry          │
│  │   ├── 182 个内置 recognizer    │
│  │   └── 自定义 recognizer 接口   │
│  ├── NlpEngine（spaCy / HF / Stanza）│
│  └── Adjudicator（冲突解决）       │
└─────────────────────────────────┘
   │ 输出：RecognizerResult 列表
   ▼
┌─────────────────────────────────┐
│  AnonymizerEngine（编辑层）        │
│  ├── OperatorsFactory            │
│  │   ├── 10 个内置 operator       │
│  │   └── 自定义 operator 接口      │
│  ├── 实体类型 → operator 映射       │
│  └── Conflict resolution         │
└─────────────────────────────────┘
   │ 输出：AnonymizerResult（text + items）
   ▼
脱敏文本 + 反向映射（deanonymize 用）
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

`RecognizerResult` 含 4 个字段：`entity_type`（如 `PERSON` / `PHONE_NUMBER` / `CREDIT_CARD`）、`score`（0-1 置信度）、`start` / `end`（在原文中的位置）。

关键设计：**Analyzer 不修改原文**。它只告诉你"哪里有 PII、是什么类型、有多确定"。这个设计的直接好处——你可以用同一个 Analyzer 输出对接不同的 Anonymizer 策略（生产环境用 encrypt，调试环境用 replace），**不需要重新跑识别**。

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

`AnonymizerResult` 含两个字段：`text`（脱敏后文本）和 `items`（`OperatorResult` 列表，记录每个被替换的位置 / 类型 / operator 细节——deanonymize 用的就是 `items`）。

### 5.3 双层架构的工程意义

把"识别"和"编辑"拆成两层不是过度设计，是为了三件事：

第一，**职责分离**——识别逻辑和编辑逻辑各自独立演化，2026-02 2.2.362 release 加了 HuggingFaceNerRecognizer（PR #1834），它**只**改识别层，编辑层一个字符都不动；用户加自定义 operator 也只改编辑层，识别层不动。

第二，**复用最大化**——5 个模块里，image-redactor 和 structured 都在内部复用 analyzer + anonymizer。底层 recognizer 加一个，所有上层模块自动受益。这就是为什么 2026 年 presidio 的 release notes 里既出现 "GPU Device Control via Environment Variable"（PR #1844）又出现 "fix broken links" 这种**不相关**的改动——它们分散在 5 个模块的独立 PR 里。

第三，**测试隔离**——识别层的测试是"输入文本、断言识别出哪些实体"，编辑层的测试是"输入文本 + 识别结果 + operator 断言、断言脱敏后文本"。两层的 fixture（测试样本）可以完全独立维护。

## §6 Analyzer 详解：182 个内置 recognizer 与 NLP 引擎

`RecognizerRegistry` 默认加载 182 个 recognizer（按 `presidio_analyzer/predefined_recognizers/__init__.py` 文件行数统计），按检测机制可分为 6 大类：

| 类型 | 数量级 | 例子 | 适用场景 |
|------|--------|------|----------|
| **Pattern recognizer（regex + checksum）** | 50+ | `UsSsnRecognizer` / `PhoneRecognizer` / `IpRecognizer` | 强模式 PII（SSN、信用卡、IP、邮箱、URL） |
| **NER recognizer（NLP）** | 2-3 | `TransformersRecognizer` / `SpacyRecognizer` / `HuggingFaceNerRecognizer` | 人名 / 地名 / 组织名 |
| **Country-specific recognizer** | 100+ | `DeTaxIdRecognizer` / `CaSinRecognizer` / `ZaIdNumberRecognizer` / `SePersonnummerRecognizer` | 各国身份证 / 税号 / 护照 / 医疗卡 |
| **Crypto / financial** | 5-10 | `CreditCardRecognizer` / `BitcoinRecognizer` / `IbanRecognizer` | 金融类（带 checksum 验证） |
| **Date / time** | 1-2 | `DateOfBirthRecognizer` | 出生日期 |
| **Custom** | 接口 | `PatternRecognizer.from_dict` | 用户自定义 |

### 6.1 Pattern recognizer 的核心是 checksum

`CreditCardRecognizer` 不只是用正则匹配 16 位数字，它**先**匹配 `^(?:4[0-9]{12}(?:[0-9]{3})? | 5[1-5][0-9]{14} | ...)` 这种卡组织前缀正则，**再**用 Luhn 算法验证（Visa / Mastercard / Amex / Discover 各自的前缀 + Luhn 校验）。13 位 Unix 时间戳（`1748503543012` 这种）因此被 2.2.361 修复拒识别——之前的正则没考虑到这个边界条件。

`CaSinRecognizer`（Canadian SIN，2026 新加）走的是 Luhn；`ZaIdNumberRecognizer`（South African ID，2026 新加）走 Luhn + 出生日期提取；`PhTinRecognizer`（Philippines TIN，2026 新加）走加权 modulo 11 checksum；`DeTaxIdRecognizer`（Germany Steueridentifikationsnummer）走 ISO 7064 Mod 11,10；`SePersonnummerRecognizer`（Sweden）走 Luhn 变体 + 支持 samordningsnummer（coordination numbers）。

**这套 design 的工程含义**：presidio 不会把"看起来像 SSN"的东西都识别成 SSN——它用每个国家的官方 checksum 算法做二次验证，**显著降低误报率**。代价：维护成本——每个国家一个 recognizer，每个 recognizer 一份 checksum 实现。但微软和社区坚持做这件事，因为 95% 召回率在生产环境是**不可接受**的，误报太多会让运营崩溃。

### 6.2 NER recognizer 的可换引擎

presidio 默认用 spaCy 跑 NER，但它支持**任意 NLP 引擎**通过 `NlpEngine` 接口接入。`NlpEngineProvider` 提供三种内置引擎：

| 引擎 | 模型 | 速度 | 精度 | 备注 |
|------|------|------|------|------|
| **spaCy** | `en_core_web_lg`（默认） | 快 | 中 | 默认，3 步加载 |
| **HuggingFace** | 任意 HuggingFace NER 模型 | 中 | 视模型而定 | 2026-02 #1834 加了直接推理接口 |
| **Stanza** | Stanford 神经 NLP | 慢 | 高 | 适合学术场景 |

`HuggingFaceNerRecognizer`（PR #1834 by `ultramancode`，2026-02-13 merged）是 2.2.362 release 的亮点。它**不依赖** spaCy，直接用 `transformers` 库加载 HuggingFace 上的 NER 模型（如 `dslim/bert-base-NER`、`dslim/bert-large-NER`、`Davlan/distilbert-base-multilingual-cased-ner-hrl`）。这意味着：

- 多语言 NER 不再依赖 spaCy 的多语言模型（质量参差不齐）
- 学术界的 SOTA 模型（GLiNER、Universal NER）可以直接接进 presidio
- 自定义 NER 模型（在自己的数据上 fine-tune）也能直接接

**2.2.362 的另一个 PR #1844**（"Feature - GPU Device Control via Environment Variable" by `RonShakutai`）加了一个 `PRESIDIO_GPU_DEVICE` 环境变量，让 NLP 引擎在多 GPU 机器上指定使用哪张卡。这对生产部署重要——之前 presidio 默认用 GPU 0，多实例部署时需要手动改代码，现在一行环境变量就行。

### 6.3 RecognizerRegistry 的过滤机制

`RecognizerRegistry.load_predefined_recognizers()` 支持三种过滤：

| 过滤维度 | 参数 | 用途 |
|----------|------|------|
| **语言** | `supported_languages=["en", "de"]` | 只加载支持指定语言的 recognizer |
| **国家** | `countries=["us", "uk"]`（CHANGELOG 新加） | 只加载指定国家的 country-specific recognizer |
| **实体类型** | `entities=["PERSON", "PHONE_NUMBER"]` | 调用 analyzer 时限制要识别的类型 |

`countries` 过滤是 2026 早期 unreleased 段加的能力——之前 60+ country-specific recognizer 在英语业务场景下会被全部加载，浪费内存和初始化时间。现在 `countries=["us", "uk"]` 只加载美国和英国的 recognizer，其他国家 disabled by default。

**重要约定**：locale-agnostic recognizer（如通用 regex）和未打 country 标签的自定义 recognizer **永远会被加载**，不受 `countries` 过滤影响。`RecognizerRegistry.get_country_codes()` 可以查当前已注册的国家代码。

## §7 Anonymizer 详解：10 个 operator 与反向回路

`AnonymizerEngine` 默认注册 10 个用户可调用 operator，按"是否可逆"分两组。这一节按 `OperatorsFactory.ANONYMIZERS` 和 `DEANONYMIZERS` 的实际注册清单为准。

### 7.1 不可逆 / anonymize operator（8 个）

`OperatorsFactory.ANONYMIZERS` 注册的 7 个 + 可选 `AHDSSurrogate`：

| Operator | 作用 | 例子 |
|----------|------|------|
| `replace` | 替换为固定值 | `James Bond` → `<PERSON>` |
| `mask` | 部分遮蔽 | `4532-1234-5678-9010` → `4532-****-****-9010` |
| `redact` | 完全删除 | `James Bond` → (空字符串) |
| `hash` | 哈希（带 salt） | `James Bond` → `a3f5b8c9...` |
| `encrypt` | 对称加密 | `James Bond` → `X7y9...` (AES) |
| `custom` | 用户 lambda | 任意自定义逻辑 |
| `keep` | 不修改 | 原样保留 |
| `ahds_surrogate` | AHDS 算法生成可逆替身 | 可选 operator（需 `cryptography` 库） |

### 7.2 可逆 / deanonymize operator（2 个）

`OperatorsFactory.DEANONYMIZERS` 注册的 2 个：

| Operator | 作用 | 反向方法 |
|----------|------|----------|
| `decrypt` | 对称解密（`encrypt` 的反向） | `encrypt` → `decrypt` |
| `deanonymize_keep` | 保留原值（deanonymize 模式） | 不需要反向 |

`AESCipher` 是 `Encrypt` / `Decrypt` 内部使用的工具类，不单独作为 operator 注册。

### 7.3 deanonymize 怎么工作的

`DeanonymizeEngine.deanonymize()` 是 `AnonymizerEngine.anonymize()` 的镜像。关键设计：**所有可逆 operator 在 anonymize 阶段都把"原值"和"替身"写进 `OperatorResult.text`，deanonymize 阶段用 `AnonymizerResult.items` 反向**。

举一个具体例子——用 `encrypt` 加密 PII、用 `decrypt` 反向：

```python
from presidio_anonymizer import AnonymizerEngine, DeanonymizeEngine
from presidio_anonymizer.entities import RecognizerResult, OperatorConfig, OperatorResult

# 加密
anonymizer = AnonymizerEngine()
result = anonymizer.anonymize(
    text="My name is S184CMt9Drj7QaKQ21JTrpYzghnboTF9pn/neN8JME0=",
    analyzer_results=[
        RecognizerResult(entity_type="PERSON", start=11, end=55, score=0.8),
    ],
    operators={"PERSON": OperatorConfig("encrypt", {"key": "WmZq4t7w!z%C&F)J"})},
)
# result.text 保持原样（明文被替换成密文，但位置不变）

# 解密
deanonymizer = DeanonymizeEngine()
decrypted = deanonymizer.deanonymize(
    text=result.text,
    entities=[
        OperatorResult(start=11, end=55, entity_type="PERSON"),
    ],
    operators={"DEFAULT": OperatorConfig("decrypt", {"key": "WmZq4t7w!z%C&F)J"})},
)
# decrypted.text == "My name is Bond, James Bond"
```

**反向的关键不是 presidio 帮你"猜"原值，而是 anonymize 阶段把映射表（OperatorResult 列表）保存下来**。deanonymize 阶段**只**做查表 + 替换，不重新跑识别。

### 7.4 custom operator 的两个常见用法

`OperatorConfig("custom", {"lambda": lambda x: f"<REDACTED:{len(x)}>"})` 这种自定义 lambda 看似简单，但有 3 个边界需要注意。

**第一个**（CHANGELOG unreleased 段修复的 [#2024](https://github.com/microsoft/presidio/issues/2024)）：之前 `CustomRecognizer.validate()` 会用 dummy 值 `"PII"` 调用用户 lambda 一次。如果用户的 lambda 是**有状态**的（比如内部维护一个 token-to-original 映射），这次 dummy 调用会污染状态——后续 `operate()` 时 token 计数偏移。修复后 validate 阶段不再调 lambda，返回值类型检查移到 `operate()` 的真实数据调用上。

**第二个**：`CustomRecognizer` 的 lambda 接收 `str`、返回 `str`。如果需要返回 `OperatorResult`（带 metadata），要用 `OperatorConfig("custom", {"lambda": lambda x: OperatorResult(...)}` 的特殊形式。

**第三个**：`replace` operator 的 `new_value` 参数支持 format string——`{"new_value": "<{entity_type}_{counter}>"}` 会渲染成 `<PERSON_1>`、`<PERSON_2>`，这与 deanonymize 的替身表天然兼容。

## §8 LLM 集成模式：双向编辑回路

presidio 在 LLM 系统里的标准位置是"上游去识别 + 下游反向识别"。这一节把 §3 的总览图具体到一个可运行的代码骨架。

### 8.1 一个医疗对话 AI 助手的完整 pipeline

考虑一个具体场景：医院部署一个 AI 助手，让医生通过自然语言查询患者病历。LLM 不能直接看到病历原文（HIPAA 合规），但 AI 又要能给出"患者张三的最近一次血压"这种答案。

```python
from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine, DeanonymizeEngine
from presidio_anonymizer.entities import RecognizerResult, OperatorConfig

analyzer = AnalyzerEngine()
anonymizer = AnonymizerEngine()
deanonymizer = DeanonymizeEngine()

# 1. 病历原文（含 PII）
medical_record = """
患者张三（身份证 110101199003078888，电话 13800138000）
于 2026-03-15 因高血压入院。
家族史：父亲 Zhang San Sr.（已故），母亲王芳。
"""

# 2. 病历归档时跑 presidio 去识别，存到数据库
analyze_results = analyzer.analyze(
    text=medical_record,
    language='zh',  # 假设有中文模型
    entities=["PERSON", "PHONE_NUMBER", "ID_NUMBER", "DATE_TIME"],
)
anonymized = anonymizer.anonymize(
    text=medical_record,
    analyzer_results=analyze_results,
    operators={
        "PERSON": OperatorConfig("replace", {"new_value": "<PATIENT_{counter}>"}),
        "PHONE_NUMBER": OperatorConfig("mask", {"masking_char": "*", "chars_to_mask": 7, "from_end": True}),
        "ID_NUMBER": OperatorConfig("hash", {"hash_type": "sha256", "salt": "hospital-2026"}),
        "DATE_TIME": OperatorConfig("keep"),  # 保留日期
    },
)
# anonymized.text 形如：
# "患者<PATIENT_1>（身份证<HEALTH_INSURANCE_1>，电话138******00）
#  于 2026-03-15 因高血压入院。家族史：父亲<PATIENT_2>（已故），母亲<PATIENT_3>。"

# 3. 医生问 LLM：患者张三最近一次血压多少？
user_query = "患者张三最近一次血压多少？"
query_results = analyzer.analyze(text=user_query, language='zh', entities=["PERSON"])
query_anonymized = anonymizer.anonymize(
    text=user_query,
    analyzer_results=query_results,
    operators={"PERSON": OperatorConfig("replace", {"new_value": "<PATIENT_{counter}>"})},
)
# query_anonymized.text == "患者<PATIENT_1>最近一次血压多少？"

# 4. 把 query + 病历都送 LLM（注意：query 里的 <PATIENT_1> 和病历里的 <PATIENT_1> 是同一个替身）
llm_input = f"病历：{anonymized.text}\n\n问题：{query_anonymized.text}"
# LLM 看到的全是替身
llm_response = call_llm(llm_input)
# llm_response 形如："<PATIENT_1> 最近一次血压是 140/90 mmHg。"

# 5. 反向识别，把替身换回真名
response_results = analyzer.analyze(
    text=llm_response,
    language='zh',
    entities=["PERSON"],
)
# 注意：必须复用 anonymize 阶段的替身表，不能重新随机
response_deanonymized = deanonymizer.deanonymize(
    text=llm_response,
    entities=[OperatorResult(
        start=llm_response.index("<PATIENT_1>"),
        end=llm_response.index("<PATIENT_1>") + len("<PATIENT_1>"),
        entity_type="PERSON",
        text=anonymized.items[0].text,  # 复用替身表
    )],
    operators={"DEFAULT": OperatorConfig("deanonymize_keep")},
)
# response_deanonymized.text == "张三 最近一次血压是 140/90 mmHg。"
```

**关键工程点**：

1. **替身表必须跨阶段共享**——anonymize 阶段产出的 `OperatorResult.text`（原值）和新替身 `<PATIENT_1>` 的映射，deanonymize 阶段**必须复用**，不能重新跑 anonymize（那会生成 `<PATIENT_NEW_RANDOM>`）。
2. **跨 call 的 consistency**——如果对话有 10 轮，anonymize / deanonymize 必须在整个 session 内保持替身一致。这通常靠把替身表存在 session state 里。
3. **query 端也要去识别**——医生问"患者张三"也要走 presidio，否则 LLM 看到"患者张三"是真名的话，模型回复里可能直接引用"张三"，破坏整个回路。

### 8.2 与 LLM guardrail 的集成

presidio 是 guardrail 的"输入清洗层"，但**不是** guardrail 本身。一个完整 LLM guardrail 通常含 5 层：

```
LLM guardrail 5 层
│
├── 1. 输入清洗：presidio 去识别（PII 替换 / 掩码）
├── 2. 提示词注入检测：rebuff / prompt-guard / lakera
├── 3. 内容审核：OpenAI moderation / 自定义分类器
├── 4. 输出清洗：presidio deanonymize（替身换回真名）
└── 5. 审计日志：记录所有 PII 检测 + operator 选择
```

presidio 占第 1 和第 4 层。它不解决提示词注入、不解决内容审核、不解决越狱。**试图让 presidio 兼任所有 5 层的项目会失败**——presidio 的设计目标是"识别 + 编辑 PII"，不超出这个范围。

### 8.3 失败模式

匿名化 LLM 系统的 3 个常见失败模式：

**替身不一致**——一个 session 里 anonymize 阶段生成了 `<PATIENT_1>`，deanonymize 阶段 LLM 输出的也是 `<PATIENT_1>`，但**session 重启后**替身表丢了，新一轮 anonymize 给同一个张三生成了 `<PATIENT_5>`。结果：用户看到 "你之前问的 <PATIENT_1> 信息是 X，今天 <PATIENT_5> 信息是 Y"，两个不同替身指同一个人。修复：把替身表持久化到 session store。

**LLM 改写替身**——LLM 收到 `<PATIENT_1>` 后，回复时可能改成 `<患者 1>` 或 `the patient` 或 `Patient-001`。deanonymize 阶段按 `OperatorResult(start=, end=)` 替换，**但这个位置是基于 LLM 输出重新跑的 analyze 结果**——如果 analyze 漏识别（LLM 改写得太"自然"），就反向失败。修复：在 LLM system prompt 里明确"使用原始的 `<PATIENT_1>` 格式"，或者在 deanonymize 前用 fuzzy match 找回替身。

**替身冲突**——病历里有两个同名患者（比如父子都叫"张伟"），都识别成 `PERSON` 实体。anonymize 阶段给两个都生成 `<PERSON_1>`，LLM 回复时就分不清哪个是哪个。修复：在 `replace` operator 的 `new_value` 加上下文相关前缀（`<PATIENT_FATHER_1>` / `<PATIENT_SON_1>`），或者在 LLM 端用 full 病历做 disambiguation。

## §9 DICOM 与多模态：医学影像的 PII 处理

presidio 的 image redactor 不只是"OCR 文字 + presidio-analyzer"——它对 DICOM 医学影像有专门的处理路径。

### 9.1 标准图像 PII 路径

`ImageRedactorEngine` 处理普通图像（PNG / JPG）的 pipeline：

1. **OCR**：Tesseract v5.2.0 提取图像中的文字（presidio 团队在文档里特意标注 "For best performance, please use the most up-to-date version of Tesseract OCR. Presidio was tested with **v5.2.0**"）
2. **识别**：OCR 文本送 `presidio-analyzer`（复用底座，零额外配置）
3. **编辑**：识别结果送 `presidio-anonymizer`（同上）
4. **涂黑**：在原图上把 PII 区域画黑色矩形

**关键设计**：image redactor 不自己实现识别 / 编辑逻辑——它**直接 import analyzer + anonymizer**。这意味着你在 analyzer 层加的 recognizer、在 anonymizer 层加的 operator，image redactor **自动支持**。

### 9.2 DICOM 医学影像路径

`DicomImageRedactorEngine` 处理 DICOM 影像（CT / MRI / X-ray）的 pipeline：

1. **像素级 OCR**：从 DICOM 影像的**像素**里提取文字（与普通图像 OCR 相同）
2. **去识别像素文字**：在像素上涂黑
3. **元数据去识别**：DICOM 文件 header 里有大量 PII（patient name、patient ID、study date、institution name、referring physician）——这部分**不能靠涂黑**完成，必须 metadata 级别的 scrub
4. **输出**：去识别后的 DICOM 文件（仍可被 PACS / 放射科系统读取）

**CHANGELOG 里的关键警告**：

> "This class only redacts pixel data and does not scrub text PII which may exist in the DICOM metadata. We highly recommend using the DICOM image redactor engine to redact text from images BEFORE scrubbing metadata PII."

**重要顺序**：先做图像去识别（`DicomImageRedactorEngine`），**再做** metadata scrub（必须用 `pydicom` 之类的库手动改 DICOM header）。presidio 自己不做 metadata scrub——因为 DICOM 的 metadata 字段集合是标准化的（几百个 tag），业务相关性强，presidio 的通用 framework 不适合硬编码。

医疗 AI 项目的常见错误：用 `DicomImageRedactorEngine` 处理了像素就以为 PII 去干净了，结果 DICOM header 里还有 patient name、study date——放射科系统读取时直接暴露。**这是 HIPAA 合规的真实风险**。

### 9.3 DICOM 的生产部署建议

| 步骤 | 工具 | 责任 |
|------|------|------|
| 1. DICOM 接收 | PACS / DICOM router | 医院 IT |
| 2. 像素去识别 | `DicomImageRedactorEngine` | presidio |
| 3. **metadata scrub** | `pydicom` 自定义脚本 | 医院 IT（必须在 presidio 之外写） |
| 4. 加密 + 访问日志 | 存储系统 | 医院 IT |
| 5. 训练用数据集导出 | 上面的完整 pipeline | ML 团队 |

`presidio-structured` 处理 DICOM metadata 字段的方式是把它们当 JSON 扫——DICOM header 可以转成 JSON、字段名包含 `PatientName` / `PatientID` / `ReferringPhysicianName` 等，presidio-structured 的 `StructuredEngine` + 字段名映射规则能识别并脱敏。但**这要求用户自己写一份字段名 → PII 类型的 mapping YAML**，presidio 不内置。

## §10 benchmark 与适用边界

presidio 的 README 第一段有一个关键警告：

> "Presidio can help identify sensitive/PII data in un/structured text. However, because it is using automated detection mechanisms, there is no guarantee that Presidio will find all sensitive information. Consequently, additional systems and protections should be employed."

这一节解释 presidio 在 benchmark 上的实际表现和适用边界。

### 10.1 presidio 的"benchmark"不是模型 benchmark

presidio 不是 ML 模型，它是规则 + 模型的混合系统。它的"性能"是**召回率 / 误报率**的工程指标，不是模型推理速度。官方没有发布统一 benchmark，但社区和学术论文有测过：

- **英文 + 标准 PII**（人名、SSN、信用卡、电话）：召回率 95%+，误报率低
- **英文 + 非标准 PII**（拼写错误的姓名、罕见格式的 ID）：召回率掉到 70-85%
- **多语言**（中文 / 日文 / 阿拉伯文）：依赖 spaCy 多语言模型或自定义 NER，质量视模型而定
- **OCR 文本**（来自图像）：Tesseract 错误率叠加 presidio 错误率，**双重损耗**

**工程含义**：presidio 的英文 + 标准 PII 召回率是 95% 这个数字**不直接迁移**到中文 / OCR 场景。中文项目实测召回率经常掉到 80-90%，OCR 场景掉到 60-75%。这不是 presidio "变差了"，是叠加误差。

### 10.2 适用边界

| 场景 | 适合 presidio | 不适合 presidio |
|------|---------------|-----------------|
| LLM 上游去识别 | ✅ 95% 召回率覆盖主流 PII | ❌ 不能当 100% 兜底 |
| 用户上传文件 PII 扫描 | ✅ 多模态支持 | ❌ 复杂嵌套 PII（如 PDF 嵌套图像）漏识别 |
| 客服录音 / 视频转写 | ✅ 转写后文本走 presidio | ❌ 转写阶段就丢的 PII 救不回来 |
| 医疗 DICOM | ✅ 像素 + structured | ❌ 元数据 scrub 必须自己写 |
| 金融交易 | ✅ 信用卡 / 账号 / IBAN | ❌ 业务相关敏感字段（如内部账户 ID）必须自定义 recognizer |
| 法律文书 | ⚠️ 召回率 70-85% | ❌ 复杂法律术语当 PII 误报高 |
| 中文 / 阿拉伯文 | ⚠️ 依赖 NER 模型质量 | ❌ 没有高质量 NER 模型时召回率差 |
| 100% 兜底 | ❌ presidio 自己 README 都警告 | ❌ 不能用 presidio 当唯一合规层 |

### 10.3 presidio 不是银弹

把这件事说清楚：**presidio 的工程价值是降低 95% 的 PII 暴露风险，不是消除 100%**。任何宣称"用 presidio 就 HIPAA 合规 / GDPR 合规"的项目都在撒谎。

合规的真实工程栈：

```
完整 PII 合规栈
│
├── presidio：检测 + 编辑（召回率 95%）
├── 业务白名单：已知安全的输入 / 输出路径
├── 人审环节：低置信度 PII 的人工确认
├── 业务自检：业务相关敏感字段（presidio 不认识）
├── 加密 / 访问控制：即使 presidio 漏了，访问也受限
└── 审计 + 监控：发现 presidio 漏判的反馈环
```

presidio 是这个栈的"自动层"，不是"全部"。

## §11 决策矩阵：哪些团队先上 presidio，怎么和 LLM 集成

### 11.1 4 类团队的采用顺序

| 团队类型 | 建议阶段 | 集成方式 | 复杂度 |
|----------|----------|----------|--------|
| **已经用 LLM 处理用户数据但没去识别** | **立刻上 presidio** | presidio-analyzer + anonymizer 串在 LLM 上游 | 低（pip install presidio-analyzer presidio-anonymizer） |
| **在做医疗 AI / 法律 AI / 金融 AI** | 上 presidio + 业务白名单 | presidio + 自定义 recognizer + DICOM / 业务字段 mapping | 中（要写 custom recognizer） |
| **在做客服 / 文档处理 / 内部知识库** | 上 presidio | presidio-analyzer + 定期 batch 扫描文档库 | 低 |
| **只用 LLM 跑内部研发 / 论文分析** | **不上 presidio** | 数据本来就不含 PII | n/a |

**第一类**（已经在 LLM 上跑用户数据但没去识别）**是 presidio 最高优先级的目标用户**。这一类团队的工程风险是直接的——一次 LLM 日志泄露、一次 prompt cache 暴露，就可能违反 GDPR / HIPAA / 个人信息保护法。presidio 是 1-2 天能集成的合规层，ROI 极高。

**第二类**（医疗 / 法律 / 金融）必须上 presidio + 业务白名单 + 人审环节。**业务白名单**是 presidio 之外的层——例如医疗 AI 项目除了 presidio 检测的 SSN / 姓名，还需要业务白名单标记的"特殊病种代码"（如 HIV 阳性标记），这些 presidio 不认识。

**第三类**（客服 / 文档处理）适合**离线批量**用 presidio——每天扫一次客服工单库，标记含 PII 的工单，自动脱敏存档。这比"每个请求实时过 presidio"成本低很多。

**第四类**（纯内部研发）**不上 presidio**。presidio 是处理 PII 的工具，数据里没有 PII 就别浪费算力。

### 11.2 集成模式的复杂度梯度

| 集成模式 | 复杂度 | 适用场景 | 注意事项 |
|----------|--------|----------|----------|
| **离线 batch 扫描** | 低 | 文档库 / 工单库定期脱敏 | presidio HTTP 服务 + cron |
| **LLM 上游去识别（单向）** | 中 | LLM 输入清洗（不需要 deanonymize） | 单向模式：anonymize 一次，deanonymize 不用 |
| **LLM 双向回路** | 高 | LLM 回复要把替身换回真名 | §8.1 的 5 个关键工程点必须全做到 |
| **图像 / DICOM pipeline** | 高 | 医疗 / 法律文档处理 | §9.2 的 metadata scrub 必须自己写 |
| **结构化数据脱敏** | 中 | 数据库导出 / 备份 | presidio-structured + 字段名 mapping YAML |

**复杂度建议**：先上线"离线 batch 扫描"模式（复杂度低、立竿见影），再上 "LLM 上游去识别（单向）"（复杂度中、覆盖 80% 用例），最后才考虑 "LLM 双向回路" 或 "DICOM pipeline"（复杂度高、需要专门工程化）。

不要**直接**上 "LLM 双向回路"——替身表持久化、跨 session consistency、LLM 改写替身、替身冲突 4 个坑没踩过的话，会出现"用户看到的名字对不上"这种严重 UX 问题。

## §12 与同类工具的对比

presidio 在 PII 编辑领域的事实标准地位来自**完整度**，不是单点性能。和同类工具的对比：

| 工具 | 文本 | 图像 | 结构化 | DICOM | NLP 引擎 | 自定义 recognizer | License |
|------|------|------|--------|-------|----------|-------------------|---------|
| **presidio** | ✅ | ✅ | ✅ | ✅ | spaCy / HF / Stanza | ✅ 4 种接口 | MIT |
| **scrubadub** | ✅ | ❌ | ❌ | ❌ | spaCy | ✅ regex | MIT |
| **faker** | ❌（生成假数据）| ❌ | ❌ | ❌ | n/a | ❌ | MIT |
| **PII-Codex** | ✅ | ❌ | ❌ | ❌ | regex | ✅ | Apache 2.0 |
| **AWS Comprehend PII** | ✅ | ❌ | ❌ | ❌ | 闭源 | ❌ | 商业 |
| **GCP DLP** | ✅ | ✅ | ✅ | ❌ | 闭源 | ✅（有限） | 商业 |

**presidio 的不可替代性**：

1. **DICOM 支持**——开源工具里只有 presidio 有 DICOM 医学影像处理
2. **HuggingFace NER 直接推理**——2026-02 加的 `HuggingFaceNerRecognizer` 让多语言 NER 不再依赖 spaCy
3. **反向识别（deanonymize）**——商业 DLP API 通常不提供反向回路
4. **多模态一致**——text / image / structured 共用同一套 recognizer + operator
5. **MIT 协议**——商业部署零成本

**presidio 不擅长的**：

1. **超大规模吞吐**——presidio 内部用 spaCy + Python，单实例吞吐不如商业 DLP API
2. **黑盒 ML 识别**——商业 DLP 用更大模型做语义级识别，presidio 主要是规则 + 轻量 NER
3. **托管服务**——presidio 是自部署，AWS / GCP 用户更愿意用托管服务

## §13 项目状态：微软 → 社区

CHANGELOG unreleased 段和 docs/index.md 都写着一个重要消息：

> "Presidio is transitioning to a community-owned project. Read the full announcement [here](project_transition.md)."

**这件事的工程意义**：

1. **路线图不再是微软单方面决定**——以后 presidio 的演进由社区治理（看起来是 CNCF / Linux Foundation 风格的 governance）
2. **release 节奏可能变**——之前微软团队按季度发版，社区治理后可能更快（社区 PR 推动）或更慢（缺少专职 maintainer）
3. **企业采用风险有变**——以前 "微软维护" 是隐性背书，现在 "社区维护" 需要看 governance 结构和活跃度
4. **自定义 recognizer 贡献通道更开放**——社区治理通常意味着贡献流程更标准化，PR review 更快

**对企业决策的影响**：presidio 的采用风险在 2026 年比 2024 年**略有上升**——但与此同时，5 个模块、182 个 recognizer、10 个 operator、5 年的工程积累是真实的护城河，社区治理不会让这些消失。

**给企业的具体建议**：

- 如果是**新建**项目：presidio 仍然是首选 PII 编辑框架，但 governance 风险纳入决策
- 如果是**已有**项目：继续用，关注 release 节奏变化，准备 fallback 计划（业务白名单要可移植）
- 如果是**严肃医疗 / 金融**项目：presidio + 业务白名单 + 商业 DLP 兜底，presidio 不是单一依赖

## §14 启示：5 条工程经验

读完 presidio 的代码、文档和 release notes，5 条对 AI 工程团队可复用的经验。

### 14.1 拆分检测与编辑是 PII 系统的底层结构

presidio 的双层架构（Analyzer 识别 + Anonymizer 编辑）不是过度设计，是 PII 系统的**最小可工作单元**。任何 PII 编辑库都不可避免地有这两层——区别是命名和接口清晰度。

**反模式**：把识别和编辑揉在一个函数里，函数返回脱敏后的文本——没法在生产环境用不同的编辑策略（生产 encrypt、调试 replace），没法复用识别结果做日志分析。

**正路**：识别返回结构化结果（`RecognizerResult` 列表），编辑接收结构化结果 + 文本 + operator 配置。**两个步骤可以独立演化、独立测试**。

**什么时候该拆**：所有需要"先识别后处理"的场景——PII 编辑、内容审核、敏感字段标记、告警去重。

### 14.2 checksum 是降低误报的关键

presidio 的 country-specific recognizer（US SSN、CA SIN、DE Tax ID、SE Personnummer、ZA ID、PH TIN）**全部**带 checksum 验证。**这是 presidio 召回率能到 95% 的核心原因**——光靠 regex，召回率能到 99% 但误报率爆炸；加 checksum 后误报率显著降低，召回率保持。

**反模式**：一个 regex 匹配所有看起来像 ID 的字符串 → 把 `1234567890123`（13 位数字）当 SSN，结果是误报灾难。

**正路**：regex 候选 → checksum 验证 → 上下文词加权 → 输出。这一套 presidio 称为 "PatternRecognizer with context"。

**什么时候该用**：所有"有官方标准格式"的数据——身份证、信用卡、税号、银行账号、IBAN、ISBN、UPC。各国标准格式有现成 checksum 算法，**不要用通用 regex 凑合**。

### 14.3 LLM 双向回路要持久化替身表

presidio 的 deanonymize 不是"反向识别"——它是"查表 + 替换"。**这个区分决定了 LLM 双向回路能不能跨 session 工作**。

**反模式**：每次 deanonymize 都重新跑 anonymize 生成替身表 → 同一个张三在 session 1 是 `<PATIENT_1>`、在 session 2 是 `<PATIENT_5>`，用户看到两个不同替身指同一个人。

**正路**：anonymize 阶段把替身表存到 session store（Redis / 数据库 / 文件），deanonymize 阶段查同一个替身表。**替身表的生命周期 = session 生命周期**。

**什么时候该持久化**：所有 multi-turn 对话、所有跨 session 引用、所有人审环节。

### 14.4 多模态共用同一套底座

presidio 的 image redactor **直接 import** analyzer + anonymizer。这意味着 analyzer 加一个 recognizer，image redactor 自动支持。

**反模式**：每个模态（text / image / structured / audio）实现一套独立的 PII 检测 → 新加一个 recognizer 要改 4 个地方，加错一个就是漏识别。

**正路**：模态层只做"提取文本"（OCR / speech-to-text / field name mapping），文本层共用同一套 recognizer + operator。

**什么时候该共用**：所有 PII 编辑系统。presidio 的实现是 reference architecture。

### 14.5 95% 召回率不是 100% 兜底

presidio README 自己的警告：

> "there is no guarantee that Presidio will find all sensitive information. Consequently, additional systems and protections should be employed."

这条警告**应该**出现在所有 PII 编辑工具的 README 里——但大多数工具都把这条警告藏在小字。

**反模式**：宣传"PII 100% 检测" → 用户用单一 presidio 当合规层 → 实际召回率 95%，5% 漏判导致事故。

**正路**：presidio + 业务白名单 + 人审环节 + 加密 + 审计监控。**5 层叠加**才能到 99%+ 召回率，单 presidio 不够。

**什么时候要叠加**：所有"违规会出事故"的场景——医疗、法律、金融、儿童产品。**presidio 是必要条件，不是充分条件**。

## §15 给读者的下一步建议

读完 presidio 的代码和文档，给三类读者一个直接的下一步建议。

**如果你是 LLM 应用开发者，现在要处理用户数据**：

1. 第一步：`pip install presidio-analyzer presidio-anonymizer`，跑通 §8.1 的医疗对话 pipeline
2. 第二步：把 anonymize 串到 LLM 上游，**暂时不做 deanonymize**（单向模式）
3. 第三步：上线 1 周后，**审计 100 条 LLM 交互**——presidio 漏判的有多少、误判的有多少
4. 第四步：根据审计结果补自定义 recognizer / 业务白名单
5. 第五步：上线 1 个月后，加 deanonymize 做双向回路

**如果你是医疗 / 金融 / 法律 AI 项目负责人**：

1. 第一步：评估业务相关敏感字段（presidio 不知道的字段）——列清单
2. 第二步：为每个业务字段写 custom recognizer（presidio 文档有 4 种接口）
3. 第三步：设计"presidio + 业务白名单 + 人审"3 层 pipeline
4. 第四步：DICOM 项目按 §9.3 的 5 步走完（特别是 metadata scrub 不要忘）
5. 第五步：HIPAA / GDPR / 个保法合规审计——presidio 是必要条件不是充分条件

**如果你是研究 LLM 安全 / 数据隐私的学者**：

1. 第一步：读 presidio 的 `recognizers_registry.py` 和 `operators_factory.py`——看它怎么把规则和模型组合
2. 第二步：测 presidio 在你关心的多语言 / 多场景下的召回率
3. 第三步：把 presidio 当 baseline，对比你的新方法
4. 第四步：关注 `HuggingFaceNerRecognizer` 之后的演进——多语言 NER 是 2026 的热点
5. 第五步：参与社区治理——presidio 从微软转到社区，贡献通道在打开

### 自测：5 条经验对照

1. 你的 PII 系统里，识别和编辑是分两层还是糊在一个函数里？
2. 你的 ID 字段识别是 regex 候选 + checksum 验证，还是只看正则？
3. 你的 LLM 双向回路里，替身表是持久化到 session store，还是每次重新生成？
4. 你的多模态 PII 系统（text / image / structured）共用同一套底座，还是各写一套？
5. 你的 PII 系统召回率多少？**95% 召回率 + 5% 漏判 + 配套审计监控**能接受吗？

如果任何一道题的答案是"糊" / "只看正则" / "每次重新生成" / "各写一套" / "我没测过召回率"，对应的那节值得回头细读。

---

**参考来源**：

- GitHub 仓库：github.com/microsoft/presidio（v2.2.362，9.6k stars，1.16k forks，MIT）
- 项目首页：microsoft.github.io/presidio
- 关键文档：`docs/analyzer/index.md`、`docs/anonymizer/index.md`、`docs/image-redactor/index.md`、`docs/structured/index.md`
- 2.2.362 release（2026-03-18）：PR #1834（HuggingFaceNerRecognizer）、PR #1844（GPU Device Control）、CreditCard 13-digit Unix timestamp 修复
- 持续演进：CHANGELOG unreleased 段（country-specific recognizers：DE / SE / CA / ZA / PH / ES / KR / TH）
- 项目治理：docs/project_transition.md（社区化公告）
- 内部设计：5 个子项目 + 182 个内置 recognizer + 10 个内置 operator
