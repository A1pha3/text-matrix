+++
date = '2026-04-13T23:51:22+08:00'
draft = false
title = 'stb：C/C++ 单文件公共领域库全集'
slug = 'stb-c-single-file-public-domain-libraries'
description = 'stb 是 Sean Barrett 发起的单文件 C/C++ 公共领域库项目，包含 21 个精选库，零依赖零配置，支持图像加载、字体渲染、音频处理等场景。'
categories = ['技术笔记']
tags = ['C/C++', '开源', '工具', '库']
---

## 📋 学习目标

通过本文，您将掌握：

1. **理解 stb 的核心价值** — 了解单文件公共领域库的优势和使用场景
2. **掌握 stb 的安装与基本使用** — 学会如何在项目中集成 stb 库
3. **学会选择适合的 stb 库** — 根据需求选择图像、音频、3D 图形、游戏开发或实用工具库
4. **了解 stb 的许可证优势** — 明确公共领域许可证的使用自由度
5. **掌握 stb 的实际应用场景** — 独立游戏开发、嵌入式系统、跨平台项目

---

## 📑 目录

1. [为什么选择 stb？](#为什么选择-stb)
2. [图形图像（7 个库）](#图形图像7-个库)
3. [音频（2 个库）](#音频2-个库)
4. [3D 图形（3 个库）](#3d-图形3-个库)
5. [游戏开发（2 个库）](#游戏开发2-个库)
6. [实用工具（2 个库）](#实用工具2-个库)
7. [UI（1 个库）](#ui1-个库)
8. [其他库](#其他库)
9. [项目结构](#项目结构)
10. [FAQ](#faq)
11. [自测题](#自测题)
12. [练习](#练习)
13. [进阶路径](#进阶路径)
14. [资料口径说明](#资料口径说明)
15. [总结](#总结)

---

**stb** 是由 Sean T. Barrett（网名 nothings）发起的单文件公共领域库项目，包含 21 个精选 C/C++ 库，共 51,166 行代码。所有库均采用公共领域（Public Domain）或 MIT 双许可证，无任何归属要求，可任意使用再分发。

## 为什么选择 stb？

### 1. 零依赖、零配置

每个库都是单文件头文件，编译时只需：

```c
// 只需在一个 .c/.cpp 文件中定义实现宏
#define STB_IMAGE_IMPLEMENTATION
#include "stb_image.h"
```

无需 cmake、无需下载多个文件、无需配置 Include 路径。Windows 开发者的痛点在这里得到彻底解决。

### 2. 公共领域许可证

可任意使用、修改、再分发，无需：
- 注明出处
- 开源修改版本
- 支付任何费用

### 3. 51,166 行代码覆盖 21 个领域

从图像加载到 3D 渲染，从音频解码到游戏开发，一个项目解决大部分基础需求。

## 图形图像（7 个库）

### stb_image.h — 图像加载

支持格式：JPEG、PNG、TGA、BMP、PSD、GIF、HDR、PIC

```c
#define STB_IMAGE_IMPLEMENTATION
#include "stb_image.h"

// 加载图像
int width, height, channels;
stbi_uc *image = stbi_load("texture.png", &width, &height, &channels, 0);

// 加载HDR图像
float *hdr_data = stbi_loadf("scene.hdr", &w, &h, &comp, 0);

// 从内存加载
stbi_uc *img = stbi_load_from_memory(buffer, buffer_len, &w, &h, &c, 0);
```

**版本 2.30 | 7,988 行代码**

### stb_image_write.h — 图像保存

```c
#define STB_IMAGE_WRITE_IMPLEMENTATION
#include "stb_image_write.h"

// 保存为PNG
stbi_write_png("output.png", width, height, channels, image_data, stride);

// 保存为JPG（质量0-100）
stbi_write_jpg("output.jpg", width, height, channels, image_data, 90, 0);

// 保存为TGA
stbi_write_tga("output.tga", width, height, channels, image_data);

// 保存为BMP
stbi_write_bmp("output.bmp", width, height, channels, image_data);
```

**版本 1.16 | 1,724 行代码**

### stb_image_resize2.h — 图像缩放

支持高质量缩放算法：

```c
#define STB_IMAGE_RESIZE2_IMPLEMENTATION
#include "stb_image_resize2.h"

stbir_resize2d(
    output_pixels, output_w, output_h, output_stride_in_bytes,
    input_pixels, input_w, input_h, input_stride_in_bytes,
    stbir_dtype_uint8, STBIR_EDGE_CLAMP, STBIR_FILTER_CATMULLROM
);
```

**版本 2.18b | 10,679 行代码**

### stb_truetype.h — 字体解析

```c
#define STB_TRUETYPE_IMPLEMENTATION
#include "stb_truetype.h"

stbtt_fontinfo font;
stbtt_InitFont(&font, font_data, 0);

float scale = stbtt_ScaleForPixelHeight(&font, 48);
int baseline = ...;

// 获取字符位图
stbtt_GetCodepointBitmap(&font, scale, scale, 'A', &w, &h, &xoff, &yoff);
```

**版本 1.26 | 5,079 行代码**

### 其他图形库

| 库 | 版本 | 行数 | 功能 |
|----|------|------|------|
| stb_rect_pack.h | 1.01 | 623 | 2D 矩形装箱打包 |
| stb_perlin.h | 0.5 | 428 | Perlin 噪声生成 |

## 音频（2 个库）

### stb_vorbis.c — Ogg Vorbis 解码

```c
#define STB_VORBIS_INCLUDE_READ_WORST_ERROR
#define STB_VORBIS_CODEBOOK_SEARCH_NOFLOAT
#include "stb_vorbis.c"

stb_vorbis *v = stb_vorbis_open_filename("music.ogg", NULL, NULL);
stb_vorbis_info info = stb_vorbis_get_info(v);

float **output;
int samples = stb_vorbis_get_samples_float(v, info.channels, output);
```

**版本 1.22 | 5,584 行代码**

### stb_hexwave.h — 音频波形合成

```c
#define STB_HEXWAVE_IMPLEMENTATION
#include "stb_hexwave.h"

stbhw_context ctx;
stbhw_generate_begin(&ctx, 44100, STBHW_SQUARE);
stbhw_generate_squarewave(&ctx, 440.0, 0.5); // A4, 50%占空比
short *samples = stbhw_generate_end(&ctx, &num_samples);
```

**版本 0.5 | 680 行代码**

## 3D 图形（3 个库）

### stb_voxel_render.h — 体素渲染引擎

类似 Minecraft 的体素渲染系统：

```c
#define STB_VOXEL_RENDER_IMPLEMENTATION
#include "stb_voxel_render.h"

stbvox_mesh_queue q;
stbvox_init(&q, ...);

// 设置相机
stbvox_set_camera(&q, pos, look, up, 1.0, 3.0);

// 渲染批次
stbvox_build_meshes(&q);
stbvox_get_vertices(&q, &vertices, &num_vertices);
```

**版本 0.89 | 3,807 行代码**

### stb_dxt.h — DXT 纹理压缩

Fabian "ryg" Giesen 编写的实时 DXT 压缩器：

```c
#define STB_DXT_IMPLEMENTATION
#include "stb_dxt.h"

stb CompressBlockDXT1(
    (uint8 *)rgba_pixels,
    block stride in bytes,
    result storage for 8 bytes
);
```

**版本 1.12 | 719 行代码**

### stb_easy_font.h — 简易位图字体

快速绘制帧率等信息：

```c
#define STB_EASY_FONT_IMPLEMENTATION
#include "stb_easy_font.h"

char buffer[100];
stb_easy_font_print(x, y, stb_sprintf(buffer, "FPS: %d", fps), NULL, &vertices);
```

**版本 1.1 | 305 行代码**

## 游戏开发（2 个库）

### stb_tilemap_editor.h — 可嵌入瓦片地图编辑器

```c
#define STB_TILEMAP_EDITOR_IMPLEMENTATION
#include "stb_tilemap_editor.h"

stbte_tile_selection selection;
stbte_set_tile(...);
stbte_undo();
stbte_redo();
```

**版本 0.42 | 4,187 行代码**

### stb_herringbone_wang_tile.h — Herringbone Wang Tile 生成器

**版本 0.7 | 1,221 行代码**

## 实用工具（2 个库）

### stb_ds.h — 类型安全容器

```c
#define STB_DS_IMPLEMENTATION
#include "stb_ds.h"

// 动态数组
arrint a = NULL;
arrpush(a, 10);
arrpush(a, 20);

// 哈希表
hmint table = NULL;
hmput(table, "key", 42);
int val = hmget(table, "key");

// 字符串哈希表
stb_dt str_table = NULL;
hmput(str_table, "name", "Alice");
```

**版本 0.67 | 1,895 行代码**

### stb_sprintf.h — 快速字符串格式化

```c
#define STB_SPRINTF_IMPLEMENTATION
#include "stb_sprintf.h"

char buffer[100];
stbsp_sprintf(buffer, "%0.6f %s %d", 3.14159, "hello", 42);
stbsp_snprintf(buffer, 100, "%.2f", 2.71828f);
```

**版本 1.10 | 1,906 行代码**

## UI（1 个库）

### stb_textedit.h — 文本编辑器内核

为游戏等应用实现的文本编辑器：

```c
#define STB_TEXTEDIT_IMPLEMENTATION
#include "stb_textedit.h"

STB_TEXTEDIT_CHARSIZE  // 1 for char, 4 for uint32
struct my_editor { ... };
stb_textedit_initialize_state(&state, ...);
stb_textedit_key(...);
```

**版本 1.14 | 1,429 行代码**

## 其他库

| 库 | 版本 | 分类 | 行数 | 功能 |
|----|------|------|------|------|
| stb_c_lexer.h | 0.12 | parsing | 941 | C 类语言词法分析 |
| stb_divide.h | 0.94 | math | 433 | 32 位模数和欧几里得除法 |
| stb_connected_components.h | 0.96 | misc | 1,049 | 网格可达性计算 |
| stb_leakcheck.h | 0.6 | misc | 194 | 内存泄漏检查 |
| stb_include.h | 0.02 | misc | 295 | 递归#include 支持 |

## 项目结构

```
stb/
├── stb_image.h          # 图像加载
├── stb_image_write.h    # 图像保存
├── stb_image_resize2.h # 图像缩放
├── stb_truetype.h      # 字体解析
├── stb_vorbis.c       # Ogg解码
├── stb_hexwave.h       # 波形合成
├── stb_voxel_render.h # 体素渲染
├── stb_dxt.h          # DXT压缩
├── stb_easy_font.h     # 位图字体
├── stb_tilemap_editor.h # 瓦片编辑器
├── stb_ds.h           # 容器
├── stb_sprintf.h       # 字符串格式化
├── stb_textedit.h      # 文本编辑
├── stb_c_lexer.h       # 词法分析
├── stb_divide.h        # 数学
├── deprecated/         # 已废弃的库
├── tests/              # 测试
└── docs/               # 文档
```

## FAQ

**Q: 如何选择使用哪个库？**
A: 文档详细且在 README 中有完整表格列出所有库的功能和代码行数。

**Q: 为什么是单文件设计？**
A: 避免 Windows 上部署库的痛苦，无需配置标准库目录，无需处理运行时冲突。

**Q: 支持哪些编译器？**
A: GCC、Clang、MSVC 等主流编译器。由于使用 MSVC 6 作为开发环境，确保了良好的兼容性。

**Q: 为什么不用 C99 标准？**
A: 为兼容 MSVC 6 所以使用 C89/C90 标准编写。

**Q: 可以闭源项目中使用吗？**
A: 可以。公共领域或 MIT 许可证都允许闭源使用，无任何传染性。

---

## 📝 自测题

1. **stb 的核心优势是什么？**
   <details>
   <summary>查看答案</summary>
   零依赖、零配置、单文件头文件设计，公共领域许可证，21 个库覆盖多个领域。
   </details>

2. **stb 的许可证是什么？**
   <details>
   <summary>查看答案</summary>
   公共领域（Public Domain）或 MIT 双许可证，无任何归属要求，可任意使用再分发。
   </details>

3. **如何使用 stb_image.h 加载图像？**
   <details>
   <summary>查看答案</summary>
   在 .c/.cpp 文件中定义 STB_IMAGE_IMPLEMENTATION 宏，然后 #include "stb_image.h"，使用 stbi_load() 加载图像。
   </details>

4. **stb 支持哪些编译器？**
   <details>
   <summary>查看答案</summary>
   GCC、Clang、MSVC 等主流编译器。由于使用 MSVC 6 作为开发环境，确保了良好的兼容性。
   </details>

5. **stb 为什么使用 C89/C90 标准？**
   <details>
   <summary>查看答案</summary>
   为兼容 MSVC 6 所以使用 C89/C90 标准编写，确保广泛的编译器兼容性。
   </details>

---

## 💪 练习

### 练习 1：集成 stb_image.h 到你的项目

**任务**：在你的 C/C++ 项目中集成 stb_image.h，并加载一张图像。

**步骤**：
1. 下载 stb_image.h 并放到项目目录
2. 在 .c/.cpp 文件中定义宏并包含头文件：
   ```c
   #define STB_IMAGE_IMPLEMENTATION
   #include "stb_image.h"
   ```
3. 使用 stbi_load() 加载图像
4. 检查返回值并处理图像数据

**预期结果**：成功加载图像并获取宽度、高度、通道数信息。

---

### 练习 2：比较不同图像格式加载性能

**任务**：使用 stb_image.h 加载不同格式的图像（JPEG、PNG、BMP、HDR），并比较加载时间和内存占用。

**步骤**：
1. 准备相同内容的多种格式图像文件
2. 编写 benchmarks 代码，分别加载这些文件
3. 记录加载时间和内存占用
4. 分析哪种格式在你的使用场景下最高效

**预期结果**：了解不同格式的加载性能特点，为项目选择合适的图像格式。

---

### 练习 3：使用 stb 构建最小游戏引擎基础

**任务**：结合 stb_image.h（图像加载）、stb_truetype.h（字体渲染）、stb_voxel_render.h（体素渲染）构建一个最小游戏引擎基础。

**步骤**：
1. 使用 stb_image.h 加载纹理
2. 使用 stb_truetype.h 渲染字体
3. 使用 stb_voxel_render.h 渲染体素地形
4. 将它们集成到一个简单的游戏循环中

**预期结果**：构建一个具备基础图像、字体和 3D 渲染能力的游戏引擎原型。

---

## 🚀 进阶路径

1. **深入理解 C/C++ 单文件库设计** — 学习如何设计零依赖、易集成的单文件库
2. **掌握高级图像/音频处理** — 深入学习 stb 库的内部实现原理，了解图像压缩、音频解码等算法
3. **贡献到 stb 项目** — 为 stb 项目贡献代码、报告 Bug、完善文档
4. **构建自己的单文件库** — 基于 stb 的设计理念，为你的项目或社区创建单文件库
5. **研究公共领域许可证** — 了解公共领域许可证的法律含义，以及如何在项目中使用
6. **探索其他单文件库** — 研究其他优秀的单文件库（如 [miniaudio](https://miniaudio.com/)、[yocto-gl](https://github.com/g-truc/yocto-gl) 等）
7. **构建完整的 C/C++ 工具链** — 结合 stb 和其他工具，构建完整的 C/C++ 开发工具链

---

## 📊 资料口径说明

1. **信息来源与时效性**：本文基于 stb GitHub 仓库（https://github.com/nothings/stb）的公开信息编写，版本可能随时间变化，请以官方最新文档为准。
2. **功能验证情况**：文中提到的功能（如支持的图像格式、音频格式等）已根据官方文档确认，但未在所有编译器或平台上实际测试。
3. **代码示例说明**：文中提供的代码示例基于 stb 官方文档和常见使用场景，实际使用时请根据您的编译器和平台调整。
4. **许可证声明**：stb 使用公共领域许可证或 MIT 许可证，两者都允许闭源使用和无归属要求。实际使用时请查看具体库的许可证声明。
5. **编译器兼容性说明**：文中提到支持 GCC、Clang、MSVC 等主流编译器，但实际兼容性可能因版本而异。
6. **更新记录**：本文编写于 2026-04-13，基于当时的 stb 版本。如有功能变化或错误，请以官方文档为准。

---

## 总结

stb 是 C/C++开发者的瑞士军刀，核心优势：

| 特性 | 说明 |
|------|------|
| **零依赖** | 单文件头文件，无需外部库 |
| **零限制** | 公共领域许可证，随便用 |
| **覆盖广** | 21 个库，51,166 行代码 |
| **易部署** | 扔进项目即可编译 |
| **可移植** | GCC/Clang/MSVC 全支持 |

无论是独立游戏开发者、嵌入式工程师还是 Windows 桌面应用开发者，stb 都能提供可靠的基础工具集。
