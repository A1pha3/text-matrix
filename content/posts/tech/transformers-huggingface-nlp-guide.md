---
title: "Hugging Face Transformers 深度指南：从 Pipeline 到生产部署"
date: "2026-04-06T22:19:00+08:00"
slug: "transformers-huggingface-nlp-guide"
description: "不止于 API 调用。本文深入 Transformers 的设计决策、Pipeline/AutoClass/Trainer 三条主线的工作机制、一个完整的微调任务流案例，以及模型量化、Flash Attention 等生产部署策略。最后给出不同场景的采用路线图。"
draft: false
categories: ["技术笔记"]
tags: ["Transformers", "Hugging Face", "NLP", "PyTorch", "大模型", "预训练模型"]
---

## 这篇文章解决什么问题

用了半年 Hugging Face Transformers 之后，我意识到大多数教程都在教你「怎么调 API」，但很少回答真正关键的问题：

- Pipeline、AutoModel、Trainer 这三条路径什么时候该用哪一条？
- `from_pretrained` 背后到底发生了什么——它怎么知道该加载 BERT 还是 GPT-2？
- 模型微调跑通了，但上生产时内存炸了、推理太慢、分词对不齐，怎么排查？

本文不会把 100 多个 AutoClass 名称全部列一遍。我们只讲三条主线和它们之间的边界：**快速推理线（Pipeline）→ 灵活控制线（AutoClass）→ 训练部署线（Trainer + 优化）**。读完你会有一个可以随时对照的决策地图。

## 先看地图：三条主线

在深入代码之前，先搞清楚 Transformers 把功能组织成了哪几条路径。它们不是「高级」和「低级」的关系，而是服务于不同阶段的工具链：

| 主线 | 入口 | 什么时候用 | 你失去的控制 |
|------|------|-----------|-------------|
| **快速推理** | `pipeline()` | 验证想法、原型、不想写预处理 | 无法自定义模型行为、无法微调 |
| **灵活控制** | `AutoModel` + `AutoTokenizer` | 需要拿到 hidden states、自定义 head、研究 | 需要自己处理输入输出 |
| **训练部署** | `Trainer` / 自定义循环 + 量化工具 | 微调、生产推理、多卡训练 | 需要理解训练超参和硬件 |

把这三条线记清楚，后面就不会在 `pipeline` 和 `AutoModel` 之间来回切换时搞混。

---

## 1. 装完就能用：环境与第一次推理

### 1.1 最小安装

Transformers 本身不捆绑深度学习框架——你决定用 PyTorch、TensorFlow 还是 JAX，然后它适配过去：

```bash
pip install transformers[torch]
```

如果你只用推理（不训练），这样装就够了。训练时才需要 `datasets`、`accelerate` 等额外依赖。

装完后跑一行验证：

```bash
python -c "import transformers; print(transformers.__version__)"
```

### 1.2 GPU 确认

```bash
python -c "import torch; print(f'CUDA: {torch.cuda.is_available()}, GPU: {torch.cuda.get_device_name(0)}')"
```

如果你的环境没有 GPU，Transformers 也能在 CPU 上跑——只是大模型会很慢。对于 7B 级别的模型，CPU 推理基本不可用，需要量化（见第 8 节）。

### 1.3 后端版本建议

| 后端 | 最低版本 | 推荐版本 |
|------|---------|---------|
| PyTorch | 1.11 | ≥ 2.0（`torch.compile` 可用） |
| TensorFlow | 2.4 | ≥ 2.15 |
| JAX/flax | 0.4.20 | ≥ 0.4.25 |

---

## 2. Pipeline：一行代码出结果的代价

### 2.1 它做了什么

```python
from transformers import pipeline

classifier = pipeline("sentiment-analysis")
result = classifier("I love using Hugging Face Transformers!")
# [{'label': 'POSITIVE', 'score': 0.9998}]
```

`pipeline()` 在背后帮你做了三件事——选模型、加载模型和分词器、跑完推理再把结果转成可读标签。拆开来看：

1. **选模型**：任务名 `"sentiment-analysis"` 默认映射到 `distilbert-base-uncased-finetuned-sst-2-english`。你当然能换，但很多人不知道默认模型是什么就直接用了。
2. **加载**：它内部调了 `AutoModelForSequenceClassification.from_pretrained()` 和 `AutoTokenizer.from_pretrained()`——和你手动加载是一样的。
3. **预处理 + 推理 + 后处理**：原始文本 → token → 模型前向 → logits → softmax → label + score。每一步都有默认参数，改不动。

Pipeline 适合**验证想法**或者**快速出 demo**。但它的自动选择也可能坑你——比如 `pipeline("text-generation")` 默认用的是非常小的 GPT-2，生成质量可能跟你预期差很远。生产环境请明确指定 `model` 参数。

### 2.2 常用任务速查

```python
# 命名实体识别
ner = pipeline("ner", grouped_entities=True)
ner("Hugging Face is based in New York City.")
# → [{'entity_group': 'ORG', 'word': 'Hugging Face'},
#    {'entity_group': 'LOC', 'word': 'New York City'}]

# 问答
qa = pipeline("question-answering")
qa(question="Who developed Transformers?",
   context="Transformers is a library developed by Hugging Face.")
# → {'answer': 'Hugging Face', 'score': 0.9995}

# 摘要
summarizer = pipeline("summarization")
summarizer(article, max_length=50, min_length=20)

# 翻译（需要明确指定模型）
translator = pipeline("translation_en_to_fr", model="Helsinki-NLP/opus-mt-en-fr")
translator("Hugging Face Transformers is awesome!")

# 图像分类
classifier = pipeline("image-classification", model="google/vit-base-patch16-224")
classifier("cat.jpg")
```

### 2.3 一个容易踩的坑：Pipeline 不是线程安全的

如果你用 `ThreadPoolExecutor` 并行跑 pipeline，每个线程需要独立的 pipeline 实例：

```python
from concurrent.futures import ThreadPoolExecutor

def classify_batch(texts):
    # 每个线程创建自己的 pipeline
    classifier = pipeline("text-classification")
    results = []
    for text in texts:
        results.append(classifier(text))
    return results
```

原因是 pipeline 内部缓存的模型不在线程间共享。更好的做法是用 `device_map="auto"` 把模型加载到 GPU，然后一次处理一个 batch，而不是每个线程一个实例。

### 📝 练习 1：Pipeline 选型

你的任务是做一个中文新闻分类器。打开 Python 终端，用 `pipeline("text-classification")` 试一条中文新闻标题，观察默认模型的表现。然后去 [huggingface.co/models](https://huggingface.co/models) 搜一个中文文本分类模型，用 `model=` 参数指定它，对比两次结果。

---

## 3. AutoClass：`from_pretrained` 背后发生了什么

Pipeline 把模型选择和加载藏起来了。当你需要更多控制——比如拿 hidden states 做特征提取、在模型上加自定义分类头——就该用 AutoClass。

### 3.1 自动推断是怎么工作的

```python
from transformers import AutoModel, AutoTokenizer

model = AutoModel.from_pretrained("bert-base-uncased")
tokenizer = AutoTokenizer.from_pretrained("bert-base-uncased")
```

`from_pretrained("bert-base-uncased")` 的实际流程：

1. 去 Hugging Face Hub 拉取 `config.json`。
2. 读 `config.json` 里的 `"architectures": ["BertModel"]`。
3. 把 `BertModel` 映射到 `AutoModel` 注册表里对应的类。
4. 用这个类加载 `pytorch_model.bin`（或 `model.safetensors`）。

所以 `AutoModel` 不是一个万能模型——它只是一个**路由器**。它的价值在于：你不用记住 200 多个模型各自的类名，只要知道 checkpoint 名字就行。

### 3.2 什么时候用哪个 AutoClass

| 你要做的事 | 用这个 |
|-----------|--------|
| 拿最后一层 hidden states | `AutoModel` |
| 文本分类（输出 label） | `AutoModelForSequenceClassification` |
| 命名实体识别 | `AutoModelForTokenClassification` |
| 问答 | `AutoModelForQuestionAnswering` |
| 文本生成（GPT 类） | `AutoModelForCausalLM` |
| 填空（BERT 类） | `AutoModelForMaskedLM` |
| 翻译/摘要（T5 类） | `AutoModelForSeq2SeqLM` |

每个 AutoClass 返回的模型 head 不同。比如 `AutoModelForSequenceClassification` 会在预训练 backbone 上自动加一个线性分类头，输出维度等于你的类别数。如果你用 `AutoModel` 做分类，需要自己写这个 head。

### 3.3 一个常见错误

```python
# ❌ 错误：用 AutoModel 做分类，输出是 hidden states 不是 logits
model = AutoModel.from_pretrained("bert-base-uncased")
outputs = model(**inputs)
# outputs.last_hidden_state 是 (batch, seq_len, 768)，不是分类结果

# ✅ 正确：用 AutoModelForSequenceClassification
model = AutoModelForSequenceClassification.from_pretrained(
    "bert-base-uncased", num_labels=2
)
outputs = model(**inputs)
# outputs.logits 才是 (batch, 2)，可以对它做 softmax
```

### 📝 练习 2：AutoModel 输出探索

加载 `bert-base-uncased` 的 `AutoModel`，输入 "Hello, world!"，打印 `last_hidden_state.shape` 和 `pooler_output.shape`。然后用同样的模型名加载 `AutoModelForSequenceClassification`（设置 `num_labels=3`），观察这次输出的 logits 维度是多少。思考：分类头加在了哪里？

---

## 4. 分词器不是「切词」那么简单

很多教程把 Tokenizer 讲成「把文本切成 token 的工具」，但它在 Transformers 里的角色远不止切词。

### 4.1 它实际做的四件事

```python
tokenizer = AutoTokenizer.from_pretrained("bert-base-uncased")
encoded = tokenizer("Hello, world!")
# {'input_ids': [101, 7592, 1010, 2088, 102],
#  'token_type_ids': [0, 0, 0, 0, 0],
#  'attention_mask': [1, 1, 1, 1, 1]}
```

每一步：

1. **分词**：把 "Hello, world!" 拆成 `["Hello", ",", "world", "!"]`。不同模型用不同算法——BERT 用 WordPiece，GPT-2 用 BPE，T5 用 SentencePiece。
2. **映射到 ID**：每个 token 查词汇表变成整数。`7592` 就是 "hello" 在 BERT 词汇表里的编号。
3. **加特殊 token**：BERT 需要 `[CLS]`（101）开头、`[SEP]`（102）结尾。GPT-2 不需要。这取决于模型。
4. **生成 attention mask**：标记哪些位置是真实 token（1）、哪些是 padding（0）。

### 4.2 为什么不同模型用不同分词算法

| 算法 | 代表模型 | 核心思路 | 适合场景 |
|------|---------|---------|---------|
| WordPiece | BERT | 按词边界切，常见词完整保留，罕见词拆成子词 | 英文为主 |
| BPE | GPT-2, RoBERTa | 从字节级开始，高频组合合并 | 多语言、代码 |
| SentencePiece | T5, XLNet | 把空格也当字符，语言无关 | 中文、日文等 |

如果你在中文场景用 BERT 的分词器处理「南京市长江大桥」，结果取决于分词器训练时见过的数据——这直接影响下游任务效果。这就是为什么微调时一定要用对应的分词器，不能混用。

### 4.3 编码时的重要参数

```python
# 批量编码
tokenizer(
    ["Hello world", "Transformers is great"],
    padding=True,        # 短句补零到最长
    truncation=True,     # 超长截断
    max_length=128,      # 最大长度
    return_tensors="pt"  # 返回 PyTorch tensor
)
```

两个容易忽视的细节：
- `padding="max_length"` 会把所有句子 padding 到 `max_length`，而不是 batch 内最长。GPU 推理时这能避免动态形状重编译。
- `return_offsets_mapping=True` 能让你把 token 映射回原文字符位置。做 NER 标注对齐时必须用它。

### 📝 练习 3：对比分词器

用 `bert-base-uncased`（WordPiece）和 `gpt2`（BPE）两个分词器，分别对 "Transformers is awesome!" 进行编码。比较两个分词器产出的 `input_ids` 长度和具体 token。你发现了什么差异？为什么？

---

## 5. 微调：一个完整的 SST-2 情感分类任务

这是篇幅最长的一节，也是微调真正发生的地方。我们不走「贴一段代码就跑」的路线，而是把每一步的决策和备选方案讲清楚。

### 5.1 微调到底在做什么

预训练模型在 BooksCorpus 和 Wikipedia 上学会了通用语言知识。微调在这个基础上，用你的任务数据把通用知识「拧」到特定任务上。

和从头训练的区别：预训练花了数千 GPU 小时在几十 TB 数据上；微调通常只用几 MB 数据、几分钟到几小时就能在一个 GPU 上跑完。你在借用一个已经知道「语言是什么」的模型，只教它「你关心什么」。

### 5.2 数据准备

```python
from datasets import load_dataset

dataset = load_dataset("glue", "sst2")
# train: 67,349 条 / validation: 872 条
# 每条: {'sentence': "...", 'label': 0/1}
```

SST-2 是斯坦福情感二分类数据集：句子 → 正面（1）或负面（0）。选它是因为模型小、训练快、结果直观——适合验证流程。

### 5.3 分词

```python
from transformers import AutoTokenizer

tokenizer = AutoTokenizer.from_pretrained("distilbert-base-uncased")

def tokenize_fn(examples):
    return tokenizer(
        examples["sentence"],
        truncation=True,
        padding="max_length",
        max_length=128
    )

tokenized = dataset.map(tokenize_fn, batched=True)
```

为什么用 `distilbert` 而不是 `bert`？DistilBERT 是 BERT 的知识蒸馏版，参数量少 40%，推理快 60%，在这个简单任务上精度几乎一样。如果你在 Colab 免费 GPU 上跑，这个选择能省一半时间。

### 5.4 Trainer：封装好的训练循环

```python
from transformers import (
    AutoModelForSequenceClassification,
    Trainer,
    TrainingArguments
)

model = AutoModelForSequenceClassification.from_pretrained(
    "distilbert-base-uncased", num_labels=2
)

training_args = TrainingArguments(
    output_dir="./results",
    num_train_epochs=3,
    per_device_train_batch_size=16,
    per_device_eval_batch_size=64,
    evaluation_strategy="epoch",      # 每个 epoch 评估一次
    save_strategy="epoch",            # 每个 epoch 保存一次
    load_best_model_at_end=True,      # 训练完加载最佳 checkpoint
    metric_for_best_model="accuracy", # 用 accuracy 判断最佳
    logging_dir="./logs",
    logging_steps=100,
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized["train"],
    eval_dataset=tokenized["validation"],
)

trainer.train()
```

几个参数值得展开说：
- `evaluation_strategy="epoch"`：每个 epoch 结束时在验证集上跑评估。如果你是大型数据集（比如训练要几天），改成 `"steps"` 配合 `eval_steps=500` 可以减少开销。
- `load_best_model_at_end=True`：训练过程中可能出现过拟合——第 3 个 epoch 的验证 loss 反而比第 2 个高。这个参数保证最终加载的是验证集上表现最好的 checkpoint，而不是最后一个。

### 5.5 什么时候不用 Trainer

Trainer 封装得很好，但有三种情况你应该自己写训练循环：

1. **需要自定义 loss**：比如多任务学习，loss 是两个任务的加权和，Trainer 不方便注入。
2. **需要梯度操作**：梯度裁剪策略和 Trainer 默认的不一样，或者要做对抗训练。
3. **需要精细控制 logging**：Trainer 的 logging 粒度是 `steps`，但你需要记录每个 batch 的梯度范数。

自己写训练循环也不复杂：

```python
import torch
from torch.utils.data import DataLoader
from transformers import get_linear_schedule_with_warmup

model = AutoModelForSequenceClassification.from_pretrained(
    "distilbert-base-uncased", num_labels=2
)
optimizer = torch.optim.AdamW(model.parameters(), lr=2e-5)

# 学习率预热：前 10% 步线性增长，之后线性衰减
total_steps = len(train_loader) * 3
scheduler = get_linear_schedule_with_warmup(
    optimizer,
    num_warmup_steps=int(0.1 * total_steps),
    num_training_steps=total_steps
)

for epoch in range(3):
    model.train()
    for batch in train_loader:
        # 只传模型需要的 key
        inputs = {k: v for k, v in batch.items()
                  if k in ["input_ids", "attention_mask", "labels"]}
        outputs = model(**inputs)
        loss = outputs.loss
        loss.backward()
        optimizer.step()
        scheduler.step()
        optimizer.zero_grad()
```

### 5.6 一个完整的任务流：从数据到部署

这里用一个完整案例串起上面所有概念。假设你要做一个情感分析 API：

```text
[原始文本] → Tokenizer → [input_ids] → Model → [logits] → softmax → [label, score]
    ↑                                                                    │
    └── 训练阶段：SST-2 数据集 → 微调 DistilBERT → 保存 checkpoint ──────┘
```

具体步骤：

```python
# 1. 微调并保存
model.save_pretrained("./my_sentiment_model")
tokenizer.save_pretrained("./my_sentiment_model")

# 2. 加载并推理
model = AutoModelForSequenceClassification.from_pretrained("./my_sentiment_model")
tokenizer = AutoTokenizer.from_pretrained("./my_sentiment_model")

# 3. 封装成服务
from fastapi import FastAPI
import torch

app = FastAPI()

@app.post("/predict")
def predict(text: str):
    inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=128)
    with torch.no_grad():
        logits = model(**inputs).logits
    probs = torch.softmax(logits, dim=-1)
    label_id = torch.argmax(probs, dim=-1).item()
    return {
        "text": text,
        "label": "POSITIVE" if label_id == 1 else "NEGATIVE",
        "confidence": probs[0][label_id].item()
    }
```

### 📝 练习 4：调参实验

在 Colab 上复制这个微调流程，做三组实验：
1. `num_train_epochs=1` → 记录验证集 accuracy
2. `num_train_epochs=3` → 记录验证集 accuracy
3. `num_train_epochs=5` → 记录验证集 accuracy

画出 epoch-accuracy 曲线。哪个 epoch 后 accuracy 不再明显提升？这告诉你「过拟合出现在什么时候」。

---

## 6. 多模态：同一套 API，不同类型的数据

Transformers 的强大之处在于它把文本、音频、图像统一到了同一套 `pipeline()` / `AutoModel` 接口下。你不需要学三套 API。

```python
# 语音识别
asr = pipeline("automatic-speech-recognition", model="openai/whisper-base")
asr("meeting.wav")

# 图像分割
segmenter = pipeline("image-segmentation", model="facebook/detr-resnet-50-panoptic")
segmenter("photo.jpg")

# 视觉问答
vqa = pipeline("vqa", model="dandelin/vilt-b32-finetuned-vqa")
vqa(image="chart.png", question="What is the trend?")
```

但要注意：多模态模型通常比纯文本模型大得多。Whisper-base 有 74M 参数，在 CPU 上转录 1 分钟音频需要约 30 秒。如果做实时语音识别，至少需要一块 GPU。

---

## 7. 生产部署：量化、Flash Attention 和 ONNX

模型跑通了不算完。生产环境里你面对的是延迟预算、显存限制和并发压力。

### 7.1 量化：用精度换显存

对于 7B 级别的模型，全精度（float32）加载需要约 28 GB 显存，一张消费级 GPU（24 GB）根本装不下。4-bit 量化可以把显存压到约 6 GB：

```python
from transformers import AutoModelForCausalLM, BitsAndBytesConfig
import torch

quant_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_compute_dtype=torch.float16,
    bnb_4bit_use_double_quant=True,  # 二次量化，进一步压缩
)

model = AutoModelForCausalLM.from_pretrained(
    "meta-llama/Llama-2-7b-hf",
    quantization_config=quant_config,
    device_map="auto"
)
```

**量化前先想清楚**：4-bit 量化会让模型在数学推理、代码生成等精度敏感任务上有可感知的退化。如果任务是情感分类或摘要，影响通常很小；如果是数学题或 SQL 生成，建议用 8-bit 或直接上更大的 GPU。

### 7.2 Flash Attention：用算法换速度

标准 attention 的时间和显存复杂度是 O(n²)。Flash Attention 通过分块计算和 IO 优化，把显存降到 O(n)，速度提升 2-4 倍，而且**数学结果完全等价**（不是近似）：

```python
model = AutoModelForCausalLM.from_pretrained(
    "meta-llama/Llama-2-7b-hf",
    attn_implementation="flash_attention_2",
    torch_dtype=torch.float16,
    device_map="auto"
)
```

前提：需要 `flash-attn` 包，且 GPU 架构 ≥ Ampere（A100、A6000、RTX 3090/4090 系列）。V100 和 T4 不支持。

### 7.3 ONNX：跨平台和低延迟

ONNX Runtime 把 PyTorch 模型转成中间表示，在 CPU 上跑可以拿到 2-3 倍的推理加速，适合边缘部署：

```python
from optimum.onnxruntime import ORTModelForSequenceClassification

model = ORTModelForSequenceClassification.from_pretrained(
    "distilbert-base-uncased-finetuned-sst-2-english", export=True
)
model.save_pretrained("./optimized_model")
```

| 优化手段 | 显存节省 | 推理加速 | 精度损失 | 适用场景 |
|---------|---------|---------|---------|---------|
| 4-bit 量化 | ~75% | 不明显 | 可感知 | LLM 推理、资源受限 |
| 8-bit 量化 | ~50% | 不明显 | 几乎无 | 精度敏感任务 |
| Flash Attention | ~50% (长序列) | 2-4x | 无 | 长文本、训练 |
| ONNX Runtime | 取决于模型 | CPU 2-3x | 无 | 边缘部署、CPU |

**怎么读这个表——以及不要被它误导**：

这些数字是我在自己的 A6000（48 GB）上用 Llama-2-7B 和 DistilBERT 测的，batch size=1，序列长度 512。换一个模型、换一块卡、换个 batch size，数字会变。

具体来说：

- 「显存节省 75%」测的是模型权重的加载大小，**不是**推理时的峰值显存。2-bit 量化后 KV cache 可能反而成为显存瓶颈——尤其是在长序列推理时。如果你发现量化后显存没省那么多，先检查 KV cache 的占用。
- 「推理加速 2-4x」来自 Flash Attention 在长序列（>2048 tokens）上的表现。短序列（<128 tokens）下加速不到 1.5x，甚至因为 kernel launch overhead 比标准实现还慢一丝。
- ONNX Runtime 的「CPU 2-3x」在 ARM 架构（Apple Silicon、树莓派）上不一定成立，因为 ONNX 的 ARM 优化不如 x86 成熟。

简单说：这张表告诉你**方向**（量化省显存，Flash Attention 加速长序列），但数字本身不能直接用于容量规划。在你自己的硬件上用你自己的模型跑一轮，拿真实数字。用 `torch.cuda.max_memory_allocated()` 和 `time.perf_counter()` 就够了，不需要复杂的 benchmark 工具。

### 📝 练习 5：量化对比

如果你有 GPU 环境，加载 `meta-llama/Llama-2-7b-hf`（或一个更小的替代如 `microsoft/phi-2`），分别用 float16 和 4-bit 加载，用 `torch.cuda.memory_allocated()` 记录显存占用差异。然后用同一个 prompt 跑推理，比较输出质量。

---

## 8. Transformers 生态：什么时候用哪个组件

Transformers 本身只是 Hugging Face 生态的核心，周围还有一圈配套工具：

| 库 | 解决的问题 | 什么时候引入 |
|---|-----------|-------------|
| **Datasets** | 数据加载、预处理、缓存 | 微调开始时就引入 |
| **Tokenizers** | 比 Transformers 自带的分词器更快的分词 | 大规模预处理（百万级样本） |
| **PEFT** | LoRA/QLoRA 等参数高效微调 | 全量微调显存不够时 |
| **Accelerate** | 多 GPU / TPU 训练 abstract | 单卡变多卡时 |
| **Optimum** | ONNX、Intel、Habana 等硬件优化 | 部署到非 NVIDIA 硬件时 |
| **Evaluate** | 统一的评估指标（BLEU/ROUGE 等） | 需要评估生成质量时 |
| **Diffusers** | 图像/视频生成 | 做 AIGC 时 |

实际项目里，你大概率是按这个顺序引入的：

1. 原型 → 只用 `transformers` 的 `pipeline()`
2. 微调 → 加 `datasets` + `Trainer`
3. 显存不够 → 加 `peft` 做 LoRA
4. 多卡 → 加 `accelerate`
5. 部署 → 加 `optimum` 做 ONNX 导出或量化

不用一开始就全装上。很多人在第一步就把所有库 `pip install` 一遍，最后真正用到的只有两三个。

---

## 9. 常见问题排查

### 9.1 CUDA Out of Memory

原因通常是 batch size 太大或模型超出了显存：

```python
# 方案 1：减小 batch size
training_args = TrainingArguments(per_device_train_batch_size=4)

# 方案 2：梯度检查点（用时间换显存）
model.gradient_checkpointing_enable()

# 方案 3：清理碎片
import torch
torch.cuda.empty_cache()
```

根本解决办法是量化（第 7 节），或者在 `TrainingArguments` 里加 `fp16=True` 做混合精度训练。

### 9.2 分词对不齐

NER 任务中，分词后的 token 需要映射回原文的字符位置：

```python
encoded = tokenizer("Hello world!", return_offsets_mapping=True)
# offset_mapping: [(0, 0), (0, 5), (5, 6), (6, 11), (11, 12), (0, 0)]
#                   [CLS]    Hello      ,      world      !      [SEP]

start, end = encoded["offset_mapping"][1]  # position 1 = "Hello"
print(f"Token 'Hello' spans characters {start} to {end}")
```

这里要注意两个特殊 token 的 offset 都是 `(0, 0)`——在代码里需要对它们做过滤。

### 9.3 模型下载慢

Hugging Face Hub 的 CDN 在某些网络下很慢：

```bash
# 方案 1：用镜像
export HF_ENDPOINT=https://hf-mirror.com

# 方案 2：先下载再加载
from huggingface_hub import snapshot_download
snapshot_download("bert-base-uncased")

# 方案 3：用国内模型源
# ModelScope（魔搭社区）提供了大部分主流模型的镜像
```

---

## 10. 采用路线图

不同起点的人应该走不同的路，这里给出三条：

### 🚀 如果你想快速上手（1 小时内）

1. 读第 1-2 节，装上环境，跑通 `pipeline()` 的 3 个任务
2. 把情感分析的例子换成你的数据，看能不能用
3. 不要碰微调，不要碰量化

### 🔧 如果你想应用到自己的任务（1 天）

1. 完整读第 3-5 节，理解 AutoClass 和微调流程
2. 在 Colab 上跑通 SST-2 微调（练习 4）
3. 替换成你自己的数据集，调整 `num_labels` 和训练参数
4. 把模型保存下来，写一个最简单的 API 服务

### 🏭 如果你要部署到生产（1 周）

1. 读第 7 节，理解量化、Flash Attention、ONNX 的适用边界
2. 在你的实际硬件上跑 benchmark——不要用别人的数字做容量规划
3. 做 A/B 测试：量化后的模型输出质量能否接受
4. 考虑用 TGI（Text Generation Inference）或 vLLM 做 LLM 推理服务

### ⛔ 哪些场景不该用 Transformers

- **纯规则匹配的文本分类**：正则表达式或 scikit-learn 的 TF-IDF + 逻辑回归更快、更省钱。
- **实时性要求极高（<10ms）的场景**：即使是 DistilBERT，单次推理也需要 10-50ms。考虑 ONNX 导出或用更轻量的模型。
- **数据量极小（<100 条）的微调**：模型学不到有效模式，不如用 few-shot prompting + LLM API。

---

## 自测清单

读完本文后，你应该能回答以下问题：

- [ ] `pipeline("sentiment-analysis")` 内部自动完成了哪三个步骤？
- [ ] `AutoModel` 和 `AutoModelForSequenceClassification` 的区别是什么？
- [ ] 什么时候用 Trainer，什么时候该自己写训练循环？
- [ ] BERT 的 WordPiece 和 GPT-2 的 BPE 分词算法，核心区别在哪？
- [ ] 4-bit 量化省了显存，但以什么为代价？
- [ ] Flash Attention 能在 V100 上跑吗？为什么？
- [ ] 你的场景适合本文三条采用路线中的哪一条？

---

## 进一步阅读

- [Hugging Face NLP Course](https://huggingface.co/learn/nlp-course) — 官方免费课程，从零开始，有配套练习
- [Transformers 官方文档](https://huggingface.co/docs/transformers) — API 参考，遇到参数问题先查这里
- [PEFT 文档](https://huggingface.co/docs/peft) — LoRA/QLoRA 微调指南
- [Text Generation Inference](https://github.com/huggingface/text-generation-inference) — 生产级 LLM 推理服务
- [ModelScope](https://modelscope.cn) — 国内模型下载替代方案
