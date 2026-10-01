---
title: "TileLang：用 100 行 Python 写出接近手调 CUDA 的 GPU Kernel——多后端 Kernel DSL 的设计解剖"
date: "2026-10-02T03:23:27+08:00"
lastmod: "2026-10-02T03:23:27+08:00"
draft: false
slug: "tile-ai-tilelang-gpu-kernel-dsl"
github_repo: "tile-ai/tilelang"
source_key: "gh:tile-ai/tilelang"
description: "TileLang 是构建在 TVM 之上的 Pythonic GPU/CPU/NPU kernel 领域语言：用 T.copy/T.gemm 这类 tile 级原语描述分块计算，编译器负责 pipeline、warp specialization、TMA 等底层优化，从 CUDA/ROCm/Metal 到华为昇腾 950 一个语言全覆盖，DeepSeek MLA 等生产级 kernel 已在仓库里。"
categories: ["技术笔记"]
tags: ["GPU", "编译器", "高性能计算", "Python"]
---

## 本文导读

读完本文你将能够：

- 说清 TileLang 在 Triton / CUDA C++ / TVM 之间的生态位：为什么「tile 级抽象 + 显式循环」是写高性能 kernel 的甜点区
- 理解它的编译管线：Python 原语如何经过 TIRX IR 落到 CUDA/ROCm/Metal/昇腾等多个后端
- 看懂一个分块矩阵乘的最小示例，以及 autotuning 如何替代手动调参
- 判断自己的场景（推理引擎、注意力变体、国产加速卡）值不值得押注它

## 问题：写 GPU Kernel 的三个不可兼得

高性能 GPU kernel 开发长期处在三角困境里：

- **CUDA C++**：性能天花板最高，但开发效率极低——一个 FlashAttention 级别的实现动辄数千行，shared memory swizzle、pipeline 深度、warp 编排全靠人肉，且锁死 NVIDIA。
- **Triton**：易用性大幅提升，但抽象层级偏「块级匿名函数」，对 pipeline、内存层级（SMEM/TMEM/寄存器）的控制力有限，切到 AMD/国产卡仍要重写。
- **TVM 等自动调度器**：自动化程度高，但对 SOTA kernel（稀疏注意力、block-scaled MMA 这类）的搜索空间表达能力不够。

TileLang（Python 编写，tile-ai 组织出品）的选择是在 Python 语法里提供 **tile 级原语**：你仍然显式写循环结构（这是性能可预期的关键），但操作的单位是分块（tile）而不是单个线程，内存层级搬运（`T.copy`）、矩阵乘（`T.gemm`）、归约（`T.reduce`）都是一等公民。编译器基于 TVM 基础设施，负责把这些原语降级到具体硬件——包括 software pipeline、warp specialization、TMA 异步拷贝这类过去必须手写的优化。

一句话概括它的卖点：**用约百行 Python 表达原本数千行 CUDA 的算法结构，同时保留对性能关键决策的显式控制**。仓库里的证据是 DeepSeek 的 MLA 解码 kernel——在 H100 上用紧凑的 TileLang 实现达到了接近手写 CUTLASS 的性能，且同一份代码有 AMD MI300X 移植版本。

## 语言核心：tile 级原语一览

写一个分块 GEMM，感受一下抽象层级：

```python
import tilelang
import tilelang.language as T

@T.prim_func
def matmul(A: T.Tensor((M, K), "float16"),
           B: T.Tensor((K, N), "float16"),
           C: T.Tensor((M, N), "float16")):
    # 为每一级内存显式分配缓冲
    A_shared = T.alloc_shared((128, 128), "float16")   # SMEM
    B_shared = T.alloc_shared((128, 128), "float16")
    C_local  = T.alloc_fragment((128, 128), "float32") # 寄存器 accum

    # 循环结构由你决定——这是与全自动调度的分界线
    for i, j, k in T.Parallel(M // 128, N // 128, K // 128, "SSR"):
        T.copy(A[i*128:(i+1)*128, k*128:(k+1)*128], A_shared)
        T.copy(B[k*128:(k+1)*128, j*128:(j+1)*128], B_shared)
        T.gemm(A_shared, B_shared, C_local, policy=T.GemmWarpPolicy.Full)
    T.copy(C_local, C)
```

几个关键点：

- **`T.alloc_shared` / `T.alloc_fragment`**：内存层级（shared memory / 寄存器片段）是显式声明的。你知道每份数据住在哪，编译器不会给你意外。
- **`T.Parallel(..., "SSR")`**：标注循环的并行语义（S=sequential, R=reduction），编译器据此决定 grid/block 映射。
- **`T.gemm`**：自动映射到当前硬件的矩阵指令——NVIDIA 上是 WMMA/MMA/TCGEN5，AMD 是 WMMA/MFMA，Apple 上是 simdgroup/cooperative tensor，昇腾上是其 SIMD/SIMT 通道。
- **`T.copy`**：在新架构上会自动升级为 TMA 异步传输（包括 swizzled layout 的任意布局 TMA），老架构退化为 cp.async/普通拷贝。

除了这三件套，原语面还覆盖 `T.reduce`（层级/warp 级归约）、`T.tma_copy`（显式 TMA）、`T.gemm_sp`（2:4 结构稀疏）、`T.copy_cluster`（SM 间 multicast）、scan 算子、以及直接内嵌 CUDA 源码的逃生舱（`T.CUDASourceCodeKernel`）。表达能力对标的是 CUTLASS 级 kernel，不是玩具。

## 编译管线与多后端：TileLang-X 的架构赌注

TileLang 正在演进为多后端编译器（官方称 **TileLang-X**），核心是一个模块化的后端抽象：

| 后端 | Target | 状态 | 备注 |
|------|--------|------|------|
| NVIDIA CUDA | `cuda` | **Primary** | SM70 → SM120 全覆盖，TMA/WGMMA/TMEM 需对应架构 |
| AMD ROCm/HIP | `hip` | Supported | CDNA/RDNA，CI 跑 MI300X；gfx950 支持 MXFP4 |
| 华为昇腾 950 | `ascend` | Supported | 2026-09 新增，原生代码生成 + 自动调度同步 |
| Apple Metal | `metal` | Supported | M 系芯片，M5 支持 cooperative tensor GEMM |
| LLVM CPU | `llvm` | Experimental | CPU 也能跑同一语言写的 kernel |
| CuTe DSL / WebGPU | — | Experimental | CUTLASS CuTe 路线 / Web 运行时 |
| 昇腾 A2/A3、MetaX、摩尔线程、海光、TANG | — | Ecosystem | 独立仓库适配，走 MLIR/厂商栈 |

这个矩阵说明一件事：**国产加速卡生态已经把它当成了「一次编写、各家适配」的统一入口**——摩尔线程 MUSA、海光 DCU、MetaX、昆仑芯系的 TANG 都有官方或社区适配仓库。对被供应链不确定性困扰的团队，这是比单卡性能更现实的吸引力。

编译流程：Python 原语 → TVM 的 TIRX IR（2026-05 完成迁移）→ 各后端 CodeGen（2026-06 起收敛到 backend registry 统一调度）。配套工程设施在同期的密集迭代中逐步补齐：带 Python 源位置的编译诊断、逐 pass 的 IR 变化追踪（IR Lower Trace）、pass 可视化、pass 级计时、编译产物跨主机缓存——这些「编译器开发体验」工具的完备度，是判断 DSL 项目能否被生产采用的可靠信号。

## 调参：从人肉到 autotuning

显式循环结构留出了 autotuning 的空间：block 尺度、pipeline 阶数等参数可以作为搜索空间交给 `@tilelang.autotune`，2026-05 起支持流水线并行编译 + 多 GPU 并行基准测试。配套的 TileLang Puzzles（十个递进难度的交互式练习）适合作为上手路径；TileLang LSP 则提供 buffer 形状/dtype/scope 的 inlay hint 和精确诊断，把「DSL 写起来盲」的抱怨堵回去。

## 谁该认真看它

1. **推理/训练引擎开发者**：注意力变体（FlashAttention、线性注意力、DeepSeek 稀疏 MLA、扩散语言模型的 block-causal attention）在 examples/ 里有大量可抄的生产级实现，且天然多卡厂移植。
2. **国产加速卡上的算法团队**：昇腾/MUSA/海光等生态适配意味着你不需要为每家硬件维护一份 C++ 分支。
3. **编译器方向的研究者**：tile 级 DSL + 多后端 registry 是一个干净的实验平台，Z3 符号推理已集成进 TVM 算术分析器。

需要留意的：项目节奏快、API 仍在活跃演进（v0.1.13 明确移除了若干遗留 API，升级要读兼容性说明）；DeepWiki 上有社区维护的知识库可作补充文档。

## 写在最后

GPU kernel 开发的「民主化」讲了多年，Triton 证明了 Python 级抽象可以触达大部分场景，但 SOTA kernel（稀疏注意力、block-scaled 低精度 MMA、跨 SM 协作）仍然掌握在少数 CUDA 专家手里。TileLang 的路线是用**显式的 tile 级原语 + 显式的内存层级声明**换性能可预期性，再用多后端编译解决可移植性——两头都要。从仓库里 DeepSeek MLA、Blackwell TMEM、昇腾 950 这些跟随最前沿硬件的落地速度看，这条路线目前是跑通了的。

项目信息：[tile-ai/tilelang](https://github.com/tile-ai/tilelang)（Python · 8k+ stars），`pip install tilelang` 即装，文档在 [tilelang.com](https://tilelang.com/)，配套 [TileLang Puzzles](https://github.com/tile-ai/tilelang-puzzles) 与 [TileLang LSP](https://github.com/tile-ai/tilelang-lsp)。
