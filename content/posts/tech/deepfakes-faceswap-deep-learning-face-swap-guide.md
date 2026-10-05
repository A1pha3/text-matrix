---
title: "FaceSwap：全球最大的开源深度换脸引擎"
date: 2026-08-01T02:54:21+08:00
lastmod: 2026-09-28
draft: false
categories: ["技术笔记"]
tags: ["FaceSwap", "深度学习", "换脸", "计算机视觉", "Python"]
description: "FaceSwap（deepfakes/faceswap）是 GitHub 上 star 数最高的开源换脸项目（57.5k+），完整的 Extract-Train-Convert 三步工作流，11 种模型架构，PyTorch 后端，支持 NVIDIA/AMD/Apple Silicon/CPU 四种运行方式，附带 GUI 和 CLI 双模式，伦理声明写进了 README 正文。"
slug: deepfakes-faceswap-deep-learning-face-swap-guide
github_repo: "deepfakes/faceswap"
source_key: "gh:deepfakes/faceswap"

---

## 一句话判断

FaceSwap 真正解决的问题，是把 2017 年还困在论文和碎片脚本里的换脸技术，收敛成一条普通人能跑通的 Extract → Train → Convert 流水线。"deepfakes"这个词的走红与它直接相关，而它给出的伦理约束——哪些事不做、支持问题去哪问——也和代码一样是项目的一部分。

## 项目概览

| 维度 | 数据 |
|------|------|
| 仓库 | deepfakes/faceswap |
| Stars / Forks | 57,557 / 13,465（2026-09-28 读数） |
| 语言 | Python（PyTorch） |
| 许可证 | GPL-3.0 |
| 建仓时间 | 2017-12-19 |
| 最近推送 | 2026-08-05 |
| 文档 | faceswap.readthedocs.io |
| 最新安装器 | v3.0.0（2025-12-21，覆盖 Windows/Linux/macOS） |

GitHub 上名字带 faceswap 的仓库里，它的 star 数遥遥领先——第二名 shaoanlu/faceswap-GAN 只有 3.4k。"全球最大"这个说法在开源换脸这个类目里站得住。

项目仍在维护，但节奏已经放缓：2026 年以来的提交以 bugfix 为主（比如锁定 `numpy<2.5` 修复图像元数据加载的 bug、修复 Villain 模型 lowmem 变体的构建问题），没有大的功能迭代。

## 它解决什么问题

README 的 Manifesto 一节其实写清了这段历史：换脸技术最早在学术界发表时被评价为突破性进展，但代码混乱、支离破碎，学术界之外几乎无人问津——直到有人把它整合成一套能直接运行的东西。Manifesto 原话是，它是"第一份任何人都能下载、运行并通过实验来学习的 AI 代码"，而在此之前这类技术"像黑魔法一样，只有能啃下晦涩论文的人才玩得转"。

这个定位延续到今天：FaceSwap 的价值不在于某个单点算法领先，而在于把"检测人脸 → 对齐裁剪 → 训练换脸模型 → 贴回原图"整条链路做成了带配置、带 GUI、带错误处理的可运行工程。想理解这类流水线怎么组织，它的代码库至今仍是最好的参考实现之一。

## 伦理立场：写在 README 正文里的红线

FaceSwap 用了整整一节 Manifesto 陈述伦理立场，四条红线原文如下（意译）：

- FaceSwap 不用于制作不当内容；
- FaceSwap 不用于未经同意的换脸，或意图掩盖换脸痕迹的使用；
- FaceSwap 不用于任何非法、不道德或可疑的目的；
- FaceSwap 的存在是为了实验和探索 AI 技术、社会或政治评论、电影制作，以及其他合乎伦理的正当用途。

对违反者，开发者的原话是"零容忍"（zero tolerance）。这条线不是装饰：Discord 社区与仓库一样明确要求 SFW（无不当内容），Manifesto 里开发者也写明了项目的发展方式——把滥用潜力压到最低，同时把学习、实验的价值放到最大。

另一个容易踩的坑是支持渠道。README 写得很直接：不要把通用使用问题发到 GitHub Issues——这类 issue "很可能被直接删除，不予回复"（liable to be deleted without response）。问题应该去 [Discord](https://discord.gg/FC54sYg) 或 [论坛](https://faceswap.dev/forum)。

## 系统地图：一条流水线，四个入口

FaceSwap 的全部功能围绕一张人脸交换流水线展开，对外暴露四个入口：

| 入口 | 干什么 | 关键产物 |
|------|--------|----------|
| `faceswap.py extract` | 从照片/视频里检测、对齐、裁出人脸 | 人脸集 + `alignments.json` |
| `faceswap.py train` | 用 A、B 两组人脸训练换脸模型 | `models/` 下的模型文件 |
| `faceswap.py convert` | 用模型把换好的脸贴回原始素材 | 换脸后的图片/视频帧 |
| `faceswap.py gui` | 图形界面，覆盖以上全部操作 | tkinter 实现 |

流水线之外还有一套 `tools.py` 工具箱（详见后文），以及三个首次运行后自动生成的配置文件：`config/extract.ini`、`config/train.ini`、`config/convert.ini`——所有插件的参数都在这里调，不用背命令行参数。

## 一次完整任务流：把 Trump 换成 Cage

官方 USAGE.md 用 Trump/Nic Cage 的示例走完了全流程，这里按它的口径串一遍：

**1. 备料。** 准备两组素材，比如 `src/trump` 和 `src/cage` 两个目录，各放一个人的人脸照片或视频。官方建议每人收集 500 到 5000 张脸，角度、表情、光照越丰富越好；视频是比图片搜索更好的素材来源，但不要逐帧全取——相邻帧太相似，浪费训练。

**2. 提取人脸。**

```bash
python faceswap.py extract -i ~/faceswap/src/trump -o ~/faceswap/faces/trump
```

这一步会检测人脸、定位特征点、裁成统一尺寸输出，同时在输入目录生成 `alignments.json`——记录每张脸的位置和特征点，后续训练和转换都要用它。注意提取不完美：会误检多张脸，也不认识"这是不是你要的人"，所以官方反复强调 **训练前务必人工过一遍数据**，数据质量直接决定换脸质量。

**3. 训练模型。**

```bash
python faceswap.py train -A ~/faceswap/faces/trump -B ~/faceswap/faces/cage -m ~/faceswap/trump_cage_model/ -p
```

`-A`/`-B` 指定两组人脸，`-m` 指定模型输出目录，`-p` 打开实时预览窗口。训练是最耗时的一步，官方给的量级是 GPU 上 12 到 48 小时，CPU 上以周计。模型每 100 次迭代左右自动存档，随时可以停、随时可以接着练——只要指向同样的目录。另一个容易被忽略的机制：每次保存迭代时如果整体 loss 下降了（模型变好了），会额外备份一份；模型损坏时进模型目录去掉 `.bk` 后缀就能回滚。

**4. 转换素材。**

```bash
python faceswap.py convert -i ~/faceswap/src/trump/ -o ~/faceswap/converted/ -m ~/faceswap/trump_cage_model/
```

对要被换脸的目标视频，先对它跑一遍 extract 生成 `alignments.json`，转换进程靠这个文件知道每帧的脸在哪。转换前建议清理对齐文件里的假阳性和对齐失败的条目，否则会直接影响成片质量——`tools.py` 里有专门的工具做这件事。

**5. 善后。** 视频素材用 `tools.py effmpeg` 在视频和帧序列之间转换（或手动用 ffmpeg），把换好的帧合成回视频。

## 技术架构：插件化的每一步

流水线的每个环节都是插件式设计，按类目放在 `plugins/` 下：

- **训练模型（11 种）**：original、dfaker、dfl_h128、dfl_sae、dlight、iae、lightweight、phaze_a、realface、unbalanced、villain。README 演示用的两个模型都出自这份名单——Emma Stone/Scarlett Johansson 的演示用 Phaze-A，Jennifer Lawrence/Steve Buscemi 用 Villain。
- **人脸检测（4 种）**：cv2_dnn、mtcnn、s3fd、retinaface。
- **特征点对齐**：FAN、HRNet 等。README 致谢部分提到 FAN 对齐器和 MTCNN 检测器都是核心开发者 torzdf 实现。
- **遮罩（5 种）**：bisenet_fp、custom、unet_dfl、vgg_clear、vgg_obstructed，负责把脸从背景里干净地抠出来。
- **转换后处理**：颜色校正（avg_color、match_hist、color_transfer、manual_balance、seamless_clone 五种）、遮罩混合、缩放与锐化。

模型网络本身的损失函数集中在 `lib/model/losses/`，除了常规重建损失，还有感知损失（LPIPS）、FocalFrequencyLoss、GeneralizedLoss、GradientLoss、LaplacianPyramidLoss 等——想研究换脸模型"像不像"是怎么量化的，这个目录是入口。

**底层是 PyTorch**。requirements 按硬件分文件：NVIDIA 走 CUDA 13.0（torch 2.9+，RTX 20 系起；GTX 7-10 系另有 CUDA 11/12 的依赖文件），AMD 走 ROCm 6.0-6.4（INSTALL.md 还提示 ROCm 也支持 WSL2），Apple Silicon 走 Metal（官方标注实验性），CPU 有单独的依赖文件。四种 backend（nvidia/apple_silicon/rocm/cpu）在安装时选定。

多 GPU 是训练选项，不是默认行为：`-d/--distributed` 在 nvidia 和 rocm 后端上启用分布式训练，`-X/--exclude-gpus` 可以把指定 GPU 排除在外。

## 工程化：长期主义的部分

能让一个 2017 年的项目活到今天的不只是模型，还有这些基建：

- **断点续训**：模型自动定期保存，训练可随时中断恢复；
- **训练可视化**：`-p` 实时预览换脸效果，TensorBoard 日志记录 loss 曲线，GUI 的分析页可以直接回看历史训练数据；`-x/--timelapse-input-A` 还能定时把固定素材的换脸效果存成延时记录，观察模型成长过程；
- **工具箱（7 件）**：`alignments`（对齐文件增删改查）、`effmpeg`（视频转帧）、`manual`（人工修对齐的 GUI 编辑器）、`mask`（给已提取的人脸补遮罩）、`model`（模型操作）、`preview`（调转换参数的实时预览）、`sort`（人脸集排序清洗）；
- **贡献秩序**：模型讨论引到独立的 faceswap-model 仓库进行，主仓库专注工程。

## 环境要求与安装

官方优先推荐 [releases 页](https://github.com/deepfakes/faceswap/releases)的安装器，Windows/Linux/macOS 三平台都有，最新版 v3.0.0。手动安装走 Anaconda：克隆仓库后按硬件执行对应的 `requirements/*.txt`。几点硬要求值得提前知道：

- 训练"几乎必须"在桌面级或服务器级 GPU 上跑——INSTALL.md 原话是 CPU 训练可能要数周，GPU 只要数小时；
- NVIDIA GPU 要求 CUDA Compute Capability 3.5 以上；
- AMD 显卡的支持范围是"较新的型号"，经 Linux 下的 ROCm；
- GUI 依赖 tkinter，Conda 环境里需要单独装。

## 适用边界与采用顺序

**适合**：

- 学习人脸检测、对齐、图像生成整条流水线的工程实现——这是它最不可替代的价值；
- 有合法授权的影视/VFX 换脸、艺术创作与社会评论；
- 想要一个伦理边界清晰、社区治理成熟的开源项目作为深度学习工程范本。

**不适合**：

- 未经同意的换脸——写在 README 红线里，也写在多数地区的法律里；
- 实时换脸：FaceSwap 是离线批处理流水线，训练以小时/天计，没有实时模式；
- 无 GPU 的机器上追求速度：CPU 能跑，但训练以周计。

**如果决定上手**，顺序很简单：从 releases 装安装器 → 用 `extract` 提两组人脸并人工清洗 → 挑一个模型用 `train -p` 开预览练起 → 满意后 `convert` 出结果 → 有空再读 `lib/model/losses/` 和某个模型插件的源码。想读代码，从 `plugins/train/model/original.py` 入手比较平滑——它直接继承所有模型共用的 `_base` 结构。

## 结尾判断

FaceSwap 不是当下效果最好的换脸工具——新一代方法在效率和保真度上都有超越者。它真正的护城河是八年积累下来的工程完整性：插件化流水线、四种硬件后端、完善的断点恢复和可视化、以及一条从 2017 年写到今天的伦理边界。对研究者，它是理解人脸交换全链路的参考实现；对工程者，它是一个"如何把研究代码做成可靠工具"的长期样本；对普通用户，装个安装器就能跑通第一次换脸。这三个角色里，它都还有位置。

## 参考来源与口径说明

- 仓库数据（stars/forks/许可证/建仓与推送时间）：GitHub API，2026-09-28 读数；
- 工作流命令、目录约定、伦理声明、支持渠道：master 分支 README.md 与 USAGE.md；
- 硬件要求、安装路径、ROCm/Apple Silicon 支持范围：master 分支 INSTALL.md；
- 插件清单、损失函数、多 GPU 参数、TensorBoard 日志：master 分支源码（`plugins/`、`lib/model/losses/`、`lib/cli/args_train.py` 等）；
- 安装器版本：GitHub Releases（v3.0.0，2025-12-21）；
- 训练时长、人脸数量建议为官方文档给出的量级参考，实际效果取决于素材与硬件；
- 本文以 2026-09-28 的 master 分支快照为口径，插件与参数以实际仓库为准。
