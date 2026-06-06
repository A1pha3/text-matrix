+++
date = '2026-04-13T23:51:22+08:00'
draft = false
title = 'stb：C/C++ 单文件公共领域库全集'
slug = 'stb-c-single-file-public-domain-libraries'
description = 'stb 是 Sean Barrett 发起的单文件 C/C++ 公共领域库项目，包含 21 个精选库，零依赖零配置，支持图像加载、字体渲染、音频处理等场景。'
categories = ['技术笔记']
tags = ['C/C++', '开源', '工具', '库']
+++

# stb：C/C++单文件公共领域库全集

**stb** 是由 Sean T. Barrett（网名 nothings）发起的单文件公共领域库项目，包含 21 个精选 C/C++ 库，共 51,166 行代码。所有库均采用公共领域（Public Domain）或 MIT 双许可证，无任何归属要求，可任意使用再分发。

## 为什么选择 stb？

### 1. 零依赖、零配置

每个库都是单文件头文件，编译时只需：

```c
// 只需在一个 .c/.cpp 文件中定义实现宏
#define STB_IMAGE_IMPLEMENTATION
#include "stb_image.h"
```

无需cmake、无需下载多个文件、无需配置Include路径。Windows开发者的痛点在这里得到彻底解决。

### 2. 公共领域许可证

可任意使用、修改、再分发，无需：
- 注明出处
- 开源修改版本
- 支付任何费用

### 3. 51,166行代码覆盖21个领域

从图像加载到3D渲染，从音频解码到游戏开发，一个项目解决大部分基础需求。

## 图形图像（7个库）

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

**版本2.30 | 7,988行代码**

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

**版本1.16 | 1,724行代码**

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

**版本2.18b | 10,679行代码**

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

**版本1.26 | 5,079行代码**

### 其他图形库

| 库 | 版本 | 行数 | 功能 |
|----|------|------|------|
| stb_rect_pack.h | 1.01 | 623 | 2D矩形装箱打包 |
| stb_perlin.h | 0.5 | 428 | Perlin噪声生成 |

## 音频（2个库）

### stb_vorbis.c — Ogg Vorbis解码

```c
#define STB_VORBIS_INCLUDE_READ_WORST_ERROR
#define STB_VORBIS_CODEBOOK_SEARCH_NOFLOAT
#include "stb_vorbis.c"

stb_vorbis *v = stb_vorbis_open_filename("music.ogg", NULL, NULL);
stb_vorbis_info info = stb_vorbis_get_info(v);

float **output;
int samples = stb_vorbis_get_samples_float(v, info.channels, output);
```

**版本1.22 | 5,584行代码**

### stb_hexwave.h — 音频波形合成

```c
#define STB_HEXWAVE_IMPLEMENTATION
#include "stb_hexwave.h"

stbhw_context ctx;
stbhw_generate_begin(&ctx, 44100, STBHW_SQUARE);
stbhw_generate_squarewave(&ctx, 440.0, 0.5); // A4, 50%占空比
short *samples = stbhw_generate_end(&ctx, &num_samples);
```

**版本0.5 | 680行代码**

## 3D图形（3个库）

### stb_voxel_render.h — 体素渲染引擎

类似Minecraft的体素渲染系统：

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

**版本0.89 | 3,807行代码**

### stb_dxt.h — DXT纹理压缩

Fabian "ryg" Giesen编写的实时DXT压缩器：

```c
#define STB_DXT_IMPLEMENTATION
#include "stb_dxt.h"

stb CompressBlockDXT1(
    (uint8 *)rgba_pixels,
    block stride in bytes,
    result storage for 8 bytes
);
```

**版本1.12 | 719行代码**

### stb_easy_font.h — 简易位图字体

快速绘制帧率等信息：

```c
#define STB_EASY_FONT_IMPLEMENTATION
#include "stb_easy_font.h"

char buffer[100];
stb_easy_font_print(x, y, stb_sprintf(buffer, "FPS: %d", fps), NULL, &vertices);
```

**版本1.1 | 305行代码**

## 游戏开发（2个库）

### stb_tilemap_editor.h — 可嵌入瓦片地图编辑器

```c
#define STB_TILEMAP_EDITOR_IMPLEMENTATION
#include "stb_tilemap_editor.h"

stbte_tile_selection selection;
stbte_set_tile(...);
stbte_undo();
stbte_redo();
```

**版本0.42 | 4,187行代码**

### stb_herringbone_wang_tile.h — Herringbone Wang Tile生成器

**版本0.7 | 1,221行代码**

## 实用工具（2个库）

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

**版本0.67 | 1,895行代码**

### stb_sprintf.h — 快速字符串格式化

```c
#define STB_SPRINTF_IMPLEMENTATION
#include "stb_sprintf.h"

char buffer[100];
stbsp_sprintf(buffer, "%0.6f %s %d", 3.14159, "hello", 42);
stbsp_snprintf(buffer, 100, "%.2f", 2.71828f);
```

**版本1.10 | 1,906行代码**

## UI（1个库）

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

**版本1.14 | 1,429行代码**

## 其他库

| 库 | 版本 | 分类 | 行数 | 功能 |
|----|------|------|------|------|
| stb_c_lexer.h | 0.12 | parsing | 941 | C类语言词法分析 |
| stb_divide.h | 0.94 | math | 433 | 32位模数和欧几里得除法 |
| stb_connected_components.h | 0.96 | misc | 1,049 | 网格可达性计算 |
| stb_leakcheck.h | 0.6 | misc | 194 | 内存泄漏检查 |
| stb_include.h | 0.02 | misc | 295 | 递归#include支持 |

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
A: 文档详细且在README中有完整表格列出所有库的功能和代码行数。

**Q: 为什么是单文件设计？**
A: 避免Windows上部署库的痛苦，无需配置标准库目录，无需处理运行时冲突。

**Q: 支持哪些编译器？**
A: GCC、Clang、MSVC等主流编译器。由于使用MSVC 6作为开发环境，确保了良好的兼容性。

**Q: 为什么不用C99标准？**
A: 为兼容MSVC 6所以使用C89/C90标准编写。

**Q: 可以闭源项目中使用吗？**
A: 可以。公共领域或MIT许可证都允许闭源使用，无任何传染性。

## 总结

stb是C/C++开发者的瑞士军刀，核心优势：

| 特性 | 说明 |
|------|------|
| **零依赖** | 单文件头文件，无需外部库 |
| **零限制** | 公共领域许可证，随便用 |
| **覆盖广** | 21个库，51,166行代码 |
| **易部署** | 扔进项目即可编译 |
| **可移植** | GCC/Clang/MSVC全支持 |

无论是独立游戏开发者、嵌入式工程师还是Windows桌面应用开发者，stb都能提供可靠的基础工具集。
