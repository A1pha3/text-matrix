---
title: "PaddleOCR 深度解析：从 PP-OCRv5 到 PP-OCRv6、PaddleOCR-VL-1.6 与 HPD-Parsing，飞桨怎么把 OCR 工具链长成 LLM-ready 文档引擎"
date: "2026-06-07T15:03:00+08:00"
lastmod: "2026-09-29T11:30:00+08:00"
slug: "paddleocr-llm-ready-document-ai-engine"
github_repo: "PaddlePaddle/PaddleOCR"
source_key: "gh:PaddlePaddle/PaddleOCR"
description: "2026-06-07 GitHub Trending 当日榜 #17（81,072 stars / 单日 +433）。四个月后回看：2026 年上半年连发 3.4/3.5/3.6/3.7 四个大版本——PaddleOCR-VL-1.6（0.9B）在 OmniDocBench v1.6 拿到 96.33%，PP-OCRv6 以 34.5M 参数刷新场景 OCR，HPD-Parsing 主打高吞吐，被 Dify、RAGFlow、Cherry Studio 当作底座。截至 2026-09-29，stars 已到 90.4k。"
draft: false
categories: ["技术笔记"]
tags: ["OCR", "VLM", "RAG", "开源项目深拆"]
toc: true
---

## 这篇文章在回答什么

`PaddlePaddle/PaddleOCR` 在 2026-06-07 以 GitHub Trending 当日榜第 17 名出现时（81,072 stars / 单日 +433），早不是新面孔——仓库 2020 年 5 月创建，持续维护超过 5 年。每次大版本发布都会把它重新送回 trending，因为它踩中了 2025-2026 年工程侧最热的问题：**怎么把 PDF 和图片变成 LLM 能直接吃的数据**。

它真正的看点是迭代速度。仅 2026 年上半年就发了四个大版本：3.4.0 带来 PaddleOCR-VL-1.5，3.5.0 接入 Hugging Face 生态并发布浏览器 SDK，3.6.0 升级到 VL-1.6，3.7.0 发布场景 OCR 新旗舰 PP-OCRv6；7 月又补了主打吞吐的 HPD-Parsing。截至 2026-09-29，stars 已到 90.4k（GitHub API）。

整个仓库的身份，README 自己写得很直白：

> PaddleOCR converts PDF documents and images into structured, LLM-ready data (JSON/Markdown) with industry-leading accuracy. With 70k+ Stars and trusted by top-tier projects like Dify, RAGFlow, and Cherry Studio, PaddleOCR is the bedrock for building intelligent RAG and Agentic applications.

——"bedrock for RAG and Agentic applications"。它已经不是单纯的 OCR 工具，而是 RAG 数据预处理层。这篇文章回答三个问题：仓库里几条产品线各自解决什么；VL-1.6 的 96.33% 应该怎么读；真要接进自己的系统，该从哪条产线开始。

## 四条产品线：先看地图

PaddleOCR 仓库里跑着四条并行产线，分工不同，别混为一谈：

| 产线 | 形态 | 解决的问题 | 典型输出 |
|------|------|-----------|---------|
| **PP-OCRv6 / PP-OCRv5** | 判别式小模型 | 自然场景文字检测识别：证件、街景、书籍、工业元件 | 纯文本 + 坐标 |
| **PP-StructureV3** | 流水线版面解析 | 复杂 PDF / 图像转结构化数据，保留细粒度坐标 | Markdown / JSON + 表格 cell、文字坐标 |
| **PaddleOCR-VL 1.x** | 0.9B 生成式 VLM | 文档级理解：公式、图表、古籍、生僻字、印章 | Markdown / JSON |
| **HPD-Parsing** | 高吞吐 VLM | 大批量文档解析的吞吐瓶颈 | Markdown / JSON |

前一条是"场景 OCR"，后三条是"文档解析"。场景 OCR 只管把字认出来；文档解析要多答一层——这块是标题、那块是表格、阅读顺序是什么。选型时先分清自己要的是哪一层。

## 版本时间线：五个月四个大版本

| 时间 | 版本 | 关键变化 |
|------|------|---------|
| 2025.05.20 | v3.0 | PP-OCRv5 发布：单模型支持简中、繁中、英、日、拼音五类文字和复杂手写体，整体识别精度较上一代提升 13 个百分点 |
| 2025.08.21 | v3.2.0 | 英文/泰语/希腊语专项识别模型（英文专项比通用主模型高 11 个百分点）；C++ 本地部署对齐 Python；CUDA 12 高性能推理；服务化部署全开源 |
| 2025.10.16 | v3.3.0 | PaddleOCR-VL 首发（NaViT 式动态分辨率视觉编码器 + ERNIE-4.5-0.3B，109 种语言）；PP-OCRv5 多语言识别模型（2M 参数，部分模型精度较上代提升 40% 以上） |
| 2026.01.29 | v3.4.0 | PaddleOCR-VL-1.5：OmniDocBench v1.5 上 94.5%，语言扩到 111 种，引入 PP-DocLayoutV3 版面算法 |
| 2026.04.21 | v3.5.0 | 20 个主模型支持 Transformers 推理后端；Word/Excel/PPT 转 Markdown；VL 系列、PP-StructureV3、PP-DocTranslation 支持导出 DOCX；官方浏览器推理 SDK PaddleOCR.js |
| 2026.05.28 | v3.6.0 | PaddleOCR-VL-1.6：OmniDocBench v1.6 上 96.33%；官方 Python / Go / TypeScript API SDK；多页 TIFF 支持 |
| 2026.06.11 | v3.7.0 | PP-OCRv6 发布：tiny / small / medium 三档，50 种语言统一模型 |
| 2026.07.22 | — | HPD-Parsing 发布：高吞吐文档解析 VLM，峰值 4,752 tokens/s |

（来源：仓库官方 update log 与 releases 页面。）

## PaddleOCR-VL-1.6 vs 1.5：一次没有架构变化的升级

VL-1.6 是这次 3.6.0 的主角。先看两代对比：

| 指标 | 1.5（2026.01.29） | 1.6（2026.05.28） |
|------|-------------------|-------------------|
| OmniDocBench | v1.5 上 94.5% | **v1.6 上 96.33%**，v1.5 与 Real5-OmniDocBench 亦刷新纪录 |
| 参数规模 | 0.9B | 0.9B（架构完全一致） |
| 语言覆盖 | 109 → 111 种（新增中国藏文、孟加拉文） | 延续 111 种 |
| 不规则版面 | PP-DocLayoutV3：倾斜、扭曲、扫描、光照、屏幕拍摄五类场景 | 复杂场景鲁棒性继续提升 |
| 能力增强 | 新增印章识别、Text Spotting；跨页表格合并、层级标题 | 表格、中文古籍、中文生僻字显著增强；印章、Spotting、图表继续提升 |
| 许可证 | Apache 2.0 | Apache 2.0 |

两代架构一模一样，升级只动了数据和训练：官方叫"区域感知数据优化框架"（从上一代模型的错误里找出薄弱区域，定向补数据、修监督信号）加"渐进式后训练"（精选数据 + 强化学习，分阶段推高成绩）。对生产环境的含义很直接：很多 RAG 系统跑的是 1.5，1.6 换权重即可，零适配成本。

架构本身是 NaViT 式动态分辨率视觉编码器 + ERNIE-4.5-0.3B 语言模型，合计 0.9B。这个量级意味着消费级 GPU 甚至边缘设备都能跑，是 VL 系列区别于动辄几十 B 参数通用 VLM 的立身之本。

## 96.33% 应该怎么读

benchmark 数字不能只复述。三个问题先问清：

1. **测的是什么。** OmniDocBench 是整页文档解析基准，端到端考察文本、表格、公式和阅读顺序的还原质量。注意别把基准版本号和模型版本号搞混：OmniDocBench 有 v1.5、v1.6 两个版本，PaddleOCR-VL 恰好也有 1.5、1.6 两代，纯属巧合。
2. **数字反映了什么。** 1.5 → 1.6 的提升来自数据和训练策略，不来自架构。换句话说，它证明的是"同样的 0.9B 架构，喂更好的数据能走多远"，这对资源受限团队是利好——你微调 1.5 的经验可以原样迁移。
3. **不能推出什么。** Real5-OmniDocBench 是飞桨团队自己提出的基准，专门测扫描伪影、倾斜、扭曲、屏幕拍摄、光照五类物理形变——自家模型在自家基准上领先，属于合理但需留一层的证据。96.33% 也是官方自报的端到端总分，你的版面类型、语言、扫描质量都可能让实际表现偏离这个均值。选型前用自己的样本跑一遍，比读任何榜单都可靠。

## 一份 PDF 进 RAG 知识库的四条路

把四条产线放进一个真实任务：手里有 200 页扫描版合同，要进 RAG 知识库。

```
PDF/图片进来，先问一个问题：
要不要保留版面结构（表格、标题层级、阅读顺序）？
 ├─ 不要，只要全文检索
 │    → PP-OCRv6：检测 + 识别，输出文本和坐标，成本最低
 └─ 要
      ├─ 需要 cell 级坐标做溯源引用
      │    → PP-StructureV3：表格 cell 坐标、文字坐标、阅读顺序最细
      ├─ 版面复杂或形变严重（公式、图表、古籍、印章、倾斜扫描）
      │    → PaddleOCR-VL-1.6：生成式还原为 Markdown/JSON
      └─ 日处理量大、延迟敏感
           → HPD-Parsing：分层并行解码，峰值 4,752 tokens/s
```

VL 产线内部也是两步：先用版面模型切分区域，再由 0.9B VLM 逐区域生成 Markdown / JSON；批量场景可以用官方 vLLM 推理服务加速。这和 PP-StructureV3 是并列的替代选择，不是前后串联——README 说得清楚：与 VL 系列不同，PP-StructureV3 提供更细粒度的坐标信息。精度、坐标粒度、吞吐，三者按需取舍。

## PP-OCRv6：34.5M 参数的场景 OCR 新旗舰

3.7.0 发布的 PP-OCRv6 值得单独一节。官方口径：

- **精度**：medium 档检测较 PP-OCRv5_server 提升 4.6 个百分点、识别提升 5.1 个百分点，官方称以此超越 Qwen3-VL-235B、GPT-5.5 等主流视觉语言大模型——在 OCR 这个窄任务上，34.5M 参数的专用模型打赢 235B 的通用 VLM，是"小模型 + 专任务"路线的又一次验证
- **语言**：单一模型统一覆盖中文、英文、日文及 46 种拉丁语系语言共 50 种（tiny 档 49 种），多语言文档不用再切模型
- **部署**：三档参数覆盖全场景——tiny 1.5M（端侧/移动）、small 7.7M、medium 34.5M（服务端）
- **速度**：medium 档 CPU OpenVINO 推理加速 5.2 倍，tiny 档在 Apple M4 上加速 6.1 倍，A100 上单次 0.13 秒
- **专项场景**：数码显示屏、点阵字符、轮胎印字、工业字符等传统 VLM 难覆盖的场景大幅增强

上一代 PP-OCRv5 的几个工程事实仍然成立，且常被误读：

1. **2M 参数的是 PP-OCRv5 多语言识别模型**（2025.10 随 v3.3.0 发布），覆盖拉丁、西里尔、阿拉伯、天城文等 109 种语言，部分模型精度较上代提升 40% 以上；而主力中文/英文识别模型没这么小——server 版存储体积 81MB，mobile 版 16MB（官方模型表）
2. **专项模型仍有存在价值**：英文专项模型在英文场景比通用主模型高 11 个百分点，泰语、希腊语专项分别做到 82.68%、89.28% 精度
3. **PP-OCRv5 整体精度较 v4 提升 13 个百分点**——是百分点不是百分比，这是官方 update log 的原文口径

## 3.5.0 之后，"全格式 ingestion"补齐

3.5.0 那次更新容易被当作小版本忽略，实际它补齐了文档入口的关键缺口：

- **Office 文档转 Markdown**：Word、Excel、PPT 直接进解析管线——PaddleOCR 从"图片 OCR"扩成"全文档格式 ingestion"的分水岭
- **DOCX 导出**：VL 系列、PP-StructureV3、PP-DocTranslation 的解析结果可导出 DOCX。RAG 不需要 DOCX，但"给人类审阅校对"需要
- **Transformers 后端**：20 个主模型接入 Hugging Face 生态，可在飞桨静态图、动态图、Transformers 三种推理后端间切换
- **PaddleOCR.js**：官方浏览器推理 SDK，PP-OCRv5 可以直接在浏览器里跑，零服务器成本

## 部署形态

README 强调多硬件支持：NVIDIA GPU、Intel CPU、昆仑芯 XPU 及各类 AI 加速器。生产端常见组合：

- **C++ 本地部署**：Linux + Windows，与 Python 端功能对齐、精度一致
- **高性能推理**：Paddle Inference 或 ONNX Runtime 后端，支持 CUDA 12；可再接 OpenVINO、TensorRT 加速
- **HTTP 服务化**：高稳定服务化方案全开源，Docker 镜像与 SDK 均可定制，任意语言客户端可调；3.6.0 起官方直接提供 Python / Go / TypeScript SDK
- **vLLM 推理服务**：VL 系列与 HPD-Parsing 可挂 vLLM 后端（官方镜像或 vLLM 官方 recipe）
- **浏览器端**：PaddleOCR.js 在浏览器直接运行 PP-OCRv5

## 生态定位：为什么 Dify / RAGFlow / Cherry Studio 都用它

README 的 "Awesome Projects" 部分直接列了：

- **Dify**（agentic workflow 平台）
- **RAGFlow**（deep document understanding 的 RAG 引擎）
- **Pathway**（Python ETL / 流式 RAG）
- **MinerU**（多类型文档转 Markdown）
- **Umi-OCR**（开源离线 OCR）
- **Cherry Studio**（多 LLM 桌面客户端）
- **Haystack**（deepset 的 LLM 编排框架）
- **OmniParser**（微软的 GUI Agent 屏幕解析）
- **QAnything**（网易有道的问答系统）

中文 RAG / Agent 生态里，它已经是事实上的数据预处理层。原因有四：

1. **Apache 2.0 + 中文社区主导**：商业友好，国内项目几乎无授权成本
2. **语言覆盖全**：整体 100+ 种语言，简繁、日韩、俄、阿拉伯、印地、泰卢固、泰米尔都有专门支持
3. **部署门槛低**：VL 系列只有 0.9B，PP-OCRv6 tiny 档 1.5M，消费级 GPU 甚至手机都能跑
4. **输出即 LLM-ready**：Markdown / JSON 出来不需要二次处理就能进 RAG pipeline

README 还点了一句 "LLM Data Flywheel"——完整的高质量数据集构建管线。也就是说它不仅能给你的 RAG 供数据，还能给你的微调供数据：用 PaddleOCR-VL 批量标注文档，再拿这些数据造你自己的解析模型。

## 采用建议

按场景给个落地顺序：

- **做中文 RAG / Agent，今天就要选**：直接从 PP-StructureV3 或 PaddleOCR-VL-1.6 起步。要 cell 级坐标做引用溯源选前者，版面复杂（公式、图表、古籍、印章）或扫描件形变重选后者。两者输出格式一致，可以先用小样本各自跑一遍再定
- **只要文本抽取（日志、截图、街景）**：PP-OCRv6 一条产线就够，tiny 档 1.5M 参数连手机都放得下
- **每天几万份文档的批处理**：先测 HPD-Parsing 的吞吐是否命中你的规模，再考虑常规 VL 管线 + vLLM
- **做古籍数字化 / 历史档案**：生僻字 + 古籍能力是 1.6 相对其他开源方案的差异化点
- **已有系统在跑 VL-1.5**：升 1.6 零适配成本，建议直接升；从 PP-StructureV3 迁到 VL 则要重新验证坐标相关的下游逻辑
- **浏览器端离线 OCR**：PaddleOCR.js 是目前唯一官方浏览器方案，适合隐私敏感、不想起服务的场景

不必急着用的场景也说一下：如果你的文档全是干净的原生 PDF（非扫描件），开源世界还有 MinerU、Marker 等专门做 PDF→Markdown 的工具，解析质量可能更对口，PaddleOCR 的优势集中在"图片 + 扫描件 + 多语言"这块硬骨头上。

## 引用

学术或工业项目引用，官方 README 建议引 PaddleOCR 3.0 与 PaddleOCR-VL；VL-1.6 有独立技术报告：

```bibtex
@misc{cui2026paddleocrvl16expandingfrontierdocument,
      title={PaddleOCR-VL-1.6: Expanding the Frontier of Document Parsing with Under-Optimized Region Refinement and Progressive Post-Training},
      author={Zelun Zhang and Hongen Liu and Suyin Liang and Yubo Zhang and Yiqing Xiang and Jiaxuan Liu and Ting Sun and Manhui Lin and Yue Zhang and Changda Zhou and Tingquan Gao and Cheng Cui and Yi Liu and Dianhai Yu and Yanjun Ma},
      year={2026},
      eprint={2606.03264},
      archivePrefix={arXiv},
      primaryClass={cs.CV},
      url={https://arxiv.org/abs/2606.03264}
}
```

## 参考

- 仓库：[github.com/PaddlePaddle/PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR)
- 模型：[HuggingFace PaddleOCR-VL-1.6](https://huggingface.co/PaddlePaddle/PaddleOCR-VL-1.6) / [PaddleOCR-VL-1.5](https://huggingface.co/PaddlePaddle/PaddleOCR-VL-1.5)
- 官网：[paddleocr.com](https://www.paddleocr.com)
- 论文：[VL-1.6 技术报告（arXiv 2606.03264）](https://arxiv.org/abs/2606.03264) / [PaddleOCR-VL 论文（arXiv 2510.14528）](https://arxiv.org/abs/2510.14528) / [PaddleOCR 3.0 技术报告（arXiv 2507.05595）](https://arxiv.org/abs/2507.05595)
- 版本历史：[官方 update log](https://github.com/PaddlePaddle/PaddleOCR/blob/main/docs/update/update.md)
- HPD-Parsing 使用文档：[paddleocr.ai](https://www.paddleocr.ai/latest/en/version3.x/pipeline_usage/HPD-Parsing.html)
- 关联生态：Dify、RAGFlow、Pathway、MinerU、Umi-OCR、Cherry Studio
