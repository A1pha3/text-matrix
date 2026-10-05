---
title: "stb 解读：21 个单文件 C 库，把接入成本压到接近零"
date: "2026-04-13T23:51:22+08:00"
lastmod: "2026-10-02T14:40:00+08:00"
slug: "stb-c-single-file-public-domain-libraries"
github_repo: "nothings/stb"
source_key: "gh:nothings/stb"
description: "stb 是 Sean Barrett 维护的 21 个单文件 C/C++ 公共领域库，51,166 行代码覆盖图像、字体、音频、容器。它解决的不是解码或渲染本身，而是『引入一个库』的流程成本：两次粘贴即可编译，公共领域许可无需署名。代价官方也直说：功能更少、更慢、内存更多。"
draft: false
categories: ["技术笔记"]
tags: ["C", "C++", "开源", "游戏开发"]
---

# stb 解读：21 个单文件 C 库，把接入成本压到接近零

libpng、FreeType、libvorbis 解码图像、渲染字体、解音频已经几十年，功能上没有空白留给 stb。它做的是另一件事：把『引入一个库』的成本压到接近零——库压成一个头文件，许可压到公共领域，接入只剩两次粘贴。代价 README 里写得毫不遮掩：stb 库可能功能更少、更慢、更耗内存；如果你已经在用等价库，"probably no good reason to switch"（大概率没有理由换）。

这句自评反而是理解它的钥匙：stb 的护城河不在代码质量，在集成成本。游戏行业、嵌入式、Windows 桌面——所有没有像样包管理器的地方——正是这口井打水的对象。项目由 Sean T. Barrett（GitHub ID nothings，stb 就是他姓名的缩写）2014 年 5 月创建，至今仍在维护（GitHub API 2026-10-02 读数：34,758 stars、8,095 forks、主语言 C、最近推送 2026-08-02）。21 个库中大多数出自他一人之手，例外在 README 里列得很清楚：stb_dxt 出自 Fabian "ryg" Giesen，原版 stb_image_resize 出自 Jorge L. "VinoBS" Rodriguez，stb_image_resize2 与 stb_sprintf 出自 Jeff Roberts。

## 21 个库总览

stb 不是"一个库"，是 21 个互相独立的单文件库，README 按 9 个类别列出，每个都标了版本和代码行数（含实现、头文件声明和文档注释三部分）。这张表本身就是选型目录：

| 库 | 版本 | 行数 | 用途 |
|----|------|------|------|
| stb_image.h | 2.30 | 7,988 | 从文件/内存解码 JPG、PNG、TGA、BMP、PSD、GIF、HDR、PIC |
| stb_image_write.h | 1.16 | 1,724 | 写出 PNG、BMP、TGA、JPEG、HDR |
| stb_image_resize2.h | 2.18b | 10,679 | 高质量图像缩放 |
| stb_truetype.h | 1.26 | 5,079 | 解析、解码并光栅化 TrueType 字体 |
| stb_rect_pack.h | 1.01 | 623 | 质量不错的简单 2D 矩形打包 |
| stb_perlin.h | 0.5 | 428 | Perlin 改进单纯形噪声，可换种子 |
| stb_vorbis.c | 1.22 | 5,584 | 从文件/内存解码 Ogg Vorbis，输出 float 或 16 位采样 |
| stb_hexwave.h | 0.5 | 680 | 抗锯齿（带限）数字音频振荡器 |
| stb_voxel_render.h | 0.89 | 3,807 | Minecraft 风格体素渲染"引擎" |
| stb_dxt.h | 1.12 | 719 | Fabian "ryg" Giesen 的实时 DXT 纹理压缩器 |
| stb_easy_font.h | 1.1 | 305 | 快速上手的位图字体，打印帧率等调试信息 |
| stb_tilemap_editor.h | 0.42 | 4,187 | 可嵌入游戏的瓦片地图编辑器 |
| stb_herringbone_wang_tile.h | 0.7 | 1,221 | herringbone Wang tile 地图生成器 |
| stb_ds.h | 0.67 | 1,895 | 类型安全的动态数组与哈希表，C/C++ 皆可编译 |
| stb_sprintf.h | 1.10 | 1,906 | 快速 sprintf/snprintf |
| stb_textedit.h | 1.14 | 1,429 | 文本编辑器内核，供从零实现编辑器的场景 |
| stb_c_lexer.h | 0.12 | 941 | 简化 C 类语言的词法分析器编写 |
| stb_divide.h | 0.94 | 433 | 更实用的 32 位除法与取模（截断/向下取整/欧几里得） |
| stb_connected_components.h | 0.96 | 1,049 | 在网格上增量计算可达性 |
| stb_leakcheck.h | 0.6 | 194 | 简陋但够用的 malloc/free 泄漏检查 |
| stb_include.h | 0.02 | 295 | 递归 #include 支持，主要为 GLSL |

合计 21 个库、51,166 行 C 代码。README 顶部单独列了 5 个"Noteworthy"：image、image_write、image_resize2、truetype、ds——后面几节就按这个优先级拆。

## 单文件是怎么工作的

### 两次粘贴的接入流程

每个库默认只是普通头文件，声明函数但不产生任何代码。你选定一个不常编辑的 .c/.cpp 文件，定义实现宏，让实现代码只在这一处实例化：

```c
// 全项目恰好一个文件里做这两步，其余文件正常 #include 即可
#define STB_IMAGE_IMPLEMENTATION
#include "stb_image.h"
```

每个库的实现宏名字都写在文件开头第一屏。不需要构建系统配置，不需要链接选项，没有安装步骤。编译器方面，GCC、Clang、MSVC 都能用——作者自己拿 MSVC 6（1998 年的 IDE）当日常开发环境，README 给的理由很个人化："它的人体工学比后来的 MSVC 版本对我更好"，所以代码停留在 C89/C90，顺手兼容了一大批老编译器。

### 为什么坚持单文件

README 把动机讲得很具体，两条都指向 Windows：一是 Windows 没有标准库目录，部署库远比 Unix 世界痛苦；二是 Windows 常见的运行时库版本冲突——库 A 用一版 CRT 编译、库 B 用另一版，链接时就打架。头文件形式让代码直接编进你的项目，绕开了这两件事。至于为什么是一个文件而不是"头文件 + 实现文件"两个，README 的原话值得引：10 个文件变 9 个无所谓，2 个文件变 1 个是质变——你不用打包、不用记得附件要发两个。

### 公共领域 + MIT：许可上的例外自由

每个源文件里都有显式的双许可声明，你选其一：公共领域（README 原话："you can do anything you want with them. You have no legal obligation to do anything else, although I appreciate attribution"——做任何用途，无任何法律义务，作者只是感谢署名）；或者给不认可公共领域概念的律师们准备的 MIT。公共领域这一侧有个实务上的好处：你把 stb 包进自己的库再发布时，可以按自己库的许可随意再授权——MIT 没有这个自由度。

## Noteworthy 五库逐个看

### stb_image：9 种格式换一次 `stbi_load`

```c
int w, h, n;
unsigned char *pixels = stbi_load("texture.png", &w, &h, &n, 0);
if (!pixels) {
    fprintf(stderr, "decode failed: %s\n", stbi_failure_reason());
    // ...
}
stbi_image_free(pixels);
```

支持 JPEG（基线 + 渐进）、PNG（1/2/4/8/16 位每通道）、TGA、BMP、PSD、GIF、HDR、PIC、PNM，可从文件、内存或 I/O 回调解码；x86/x64 上有 SSE2、ARM 上有 NEON 加速。`req_comp` 参数传 1–4 可以强制输出通道数，传 0 则按文件原样。

边界都写在头文件注释里：JPEG 不支持 12 bpc 和算术编码；BMP 不支持 1bpp 和 RLE；PSD 只给合成视图，不带额外通道；GIF 的 `n` 恒报 4。SIMD 在 GCC 下有个结构性限制：stb_image 要么编译加 `-msse2` 全程用 SIMD，要么完全不用，不做运行时 CPU 检测——README 解释过原因，GCC 没有在单文件库内做双路径运行时选择的官方途径，多年踩坑后作者放弃了。

还有一个方向性决定：stb_image 不再增加新格式。随着使用量增长，安全比功能覆盖重要，多一种格式就多一片需要加固的解析代码。选型时别指望它读 WebP 或 AVIF。

### stb_image_write：五个写盘函数

```c
stbi_write_png("out.png", w, h, n, pixels, 0);        // stride 传 0 按紧凑布局算
stbi_write_jpg("out.jpg", w, h, n, pixels, 90);       // quality 1-100
stbi_write_hdr("out.hdr", w, h, n, (const float*)data); // float 数据写 Radiance HDR
```

PNG、BMP、TGA、JPEG、HDR 五种，返回 int 表示成败；也有 `*_to_func` 变体把输出接到回调而非文件。头文件自己承认定位：为源码紧凑和简单设计，不追求文件大小或运行性能——PNG 输出比优化过的实现大 20–50%（可用自定义 zlib 压缩钩子缓解）。

### stb_image_resize2：Jeff Roberts 重写的缩放器

2.18b 版的 10,679 行是全项目最大的单库，出自 Jeff Roberts 之手（替代 Jorge L. Rodriguez 的原版 stb_image_resize，原版已归入仓库 deprecated/ 目录）。简单路径四个函数覆盖常见情形：

```c
#define STB_IMAGE_RESIZE2_IMPLEMENTATION
#include "stb_image_resize2.h"

// sRGB 空间 8 位缩放：输入在前，输出在后，stride 传 0 表示连续内存
stbir_resize_uint8_srgb(in,  in_w,  in_h,  0,
                        out, out_w, out_h, 0, STBIR_RGBA);
```

`STBIR_RGBA` 这类像素布局参数要与实际通道数一致（`STBIR_1CHANNEL`/`STBIR_RGB`/`STBIR_RGBA` 等）；另有线性色彩空间的 `stbir_resize_uint8_linear`、float 版 `stbir_resize_float_linear` 和通用入口 `stbir_resize`。滤波器有默认值：上采样 Catmull-Rom、下采样 Mitchell-Netrevalli，要换走 `stbir_resize_init` + `stbir_set_filters` 的高级接口，那里还能配置边缘模式、子区域和像素回调。

### stb_truetype：三步取出一个字形位图

```c
stbtt_fontinfo font;
stbtt_InitFont(&font, ttf_data, 0);                     // offset 0 = 普通 .ttf

float scale = stbtt_ScaleForPixelHeight(&font, 48.0f);  // 换算像素高度比例

int bw, bh, ox, oy;
unsigned char *bitmap = stbtt_GetCodepointBitmap(
    &font, scale, scale, 'A', &bw, &bh, &ox, &oy);      // 8 位抗锯齿位图
```

它解析、解码并光栅化 TrueType 字体，全流程无堆分配器配置、无外部依赖。配 stb_rect_pack 可以打字形图集：rect_pack 的 `stbrp_init_target` 建上下文、`stbrp_pack_rects` 装箱，再把每个字形的位图拷进去——这是它最常见的搭档用法。

### stb_ds：C 语言里缺的那对容器

```c
#define STB_DS_IMPLEMENTATION
#include "stb_ds.h"

// 动态数组：指针即数组，NULL 即空
int *arr = NULL;
arrput(arr, 10);
arrput(arr, 20);
printf("%d %d\n", arrlen(arr), arr[1]);   // 2 20
arrfree(arr);

// 哈希表：结构体里必须有 key（和 value）字段
struct { int key; char *value; } *map = NULL;
hmput(map, 42, "hello");
char *v = hmget(map, 42);                 // "hello"
hmfree(map);
```

宏直接作用在你的指针上，类型安全来自宏展开，不是 `void*`。键类型是结构体字段类型（整数、指针都行），字符串键走 `sh` 系列（`shput`/`shget`）配合 `sh_new_strdup` 或 `sh_new_arena` 自动管理键内存。两个值得知道的默认行为：增长用 realloc，返回值/新指针必须写回你的变量——宏会改写传入的指针；哈希默认用较弱的 SipHash 变体（性能考量），64 位平台上定义 `STBDS_SIPHASH_2_4` 可换成合规的 SipHash-2-4，代价是 4–8 字节键的插入慢约 20%。

## 一次完整任务流：读入、缩放、写出

三个 Noteworthy 库串一个真实任务——把输入图缩小一半并存成两种格式。整个程序零外部依赖，一个文件即可编译：

```c
/* resize_tool.c — 唯一需要定义实现宏的翻译单元 */
#define STB_IMAGE_IMPLEMENTATION
#define STB_IMAGE_RESIZE2_IMPLEMENTATION
#define STB_IMAGE_WRITE_IMPLEMENTATION
#include "stb_image.h"
#include "stb_image_resize2.h"
#include "stb_image_write.h"
#include <stdio.h>
#include <stdlib.h>

int main(int argc, char **argv) {
    if (argc < 2) { fprintf(stderr, "usage: %s in.png\n", argv[0]); return 1; }

    int w, h, n;
    unsigned char *pixels = stbi_load(argv[1], &w, &h, &n, 0);
    if (!pixels) {
        fprintf(stderr, "decode failed: %s\n", stbi_failure_reason());
        return 1;
    }

    int out_w = w / 2, out_h = h / 2;
    unsigned char *small = malloc((size_t)out_w * out_h * n);
    if (!small) { stbi_image_free(pixels); return 1; }

    /* 像素布局要与通道数匹配，否则缩放会读越界；stbi_load 的 n 范围是 1-4 */
    stbir_pixel_layout layout = (n == 1) ? STBIR_1CHANNEL
                              : (n == 2) ? STBIR_2CHANNEL
                              : (n == 3) ? STBIR_RGB
                              : STBIR_RGBA;
    stbir_resize_uint8_srgb(pixels, w, h, 0, small, out_w, out_h, 0, layout);

    stbi_write_png("out.png", out_w, out_h, n, small, 0);
    stbi_write_jpg("out.jpg", out_w, out_h, n, small, 90);

    stbi_image_free(pixels);
    free(small);
    return 0;
}
```

```sh
gcc resize_tool.c -o resize_tool && ./resize_tool photo.png
# x86 上可加 -msse2 启用 stb_image 的 SIMD 路径
```

同样的组合逻辑在游戏工具链里随处可见：stb_image 读图块，stb_rect_pack 装箱，stb_image_write 输出图集。每个环节都是独立小函数，胶水代码自己写——这正是 stb 的哲学：给你零件，不给你框架。

## 安全与维护的现实

README 顶部有一条加粗警告，值得原样转述：这个项目在公开的 GitHub Issue 和 PR 里讨论安全相关漏洞，而安全修复可能需要相当长时间才能实现或合并；如果这给你的项目带来不可接受的风险，就不要使用 stb 库。选型时把这条当作一票否决项来对待：解析不可信输入（用户上传的图片等）的联网服务，风险自担或另选；离线工具、游戏资源加载这类输入可控的场景，暴露面小得多。

维护节奏也要有预期：21 个库基本一人维护，CONTRIBUTING.md 自述"ended up supporting a lot of libraries"（最后背上了好多库），所以处理得比较慢，许多 issue 挂了很久。优先级排序是崩溃 > stb_image 的安全问题 > 一般 bug > 其他库的安全问题 > 警告 > 新特性。另外这个项目明确拒绝 AI 生成内容——仓库根目录的 .NO_AI 标记和 CONTRIBUTING.md 写明不接受 LLM 生成的代码、文档、issue 和 PR，提交前连 AI 自动补全都要求关掉。

## 什么时候用，什么时候别用

README 里有一段少见的诚实自评，选型判断应该从这里出发：stb 库的优势只有易集成、易使用、易发布；它们可能功能更少、更慢、更耗内存；"如果你已经在用一个等价库，大概率没有理由换"。

值得引入的信号：

- 项目没有包管理器可用：游戏客户端、嵌入式、Windows 桌面工具、教学代码。没有 vcpkg/Conan 环境时，stb 的接入成本无可替代。
- 原型期要快：今天就能跑起来比长期最优重要，工具函数先用 stb 顶着。
- 许可负担要清零：发行渠道审核严格、法务不想审署名条款时，公共领域是最省事的答案。

不该用的信号：

- 已有等价成熟库在跑：换库收益是负的，官方自己都这么说。
- 需要极限性能或完整特性：如 stb_image_write 的 PNG 压缩、stb_image 的格式覆盖，专业实现都更强。
- 解析不可信输入的联网服务：把 README 顶部的安全警告读三遍再决定。

渐进路径也简单：从 stb_image 开始，一次只引入一个库，跑顺了再考虑下一个；需要容器时 stb_ds 是第二顺位，它的 realloc 语义要花十分钟适应。想自己写一个单文件库，仓库 docs/stb_howto.txt 是作者的经验总结；为什么坚持公共领域，docs/why_public_domain.md 给了完整论证。

## 结尾

stb 证明了一件事：在一个"库"的常规竞争维度（性能、功能、正确性）之外，还有一条叫接入成本的赛道，而这条赛道上几乎没有对手。21 个库、51,166 行代码、一个人维护十二年，被引擎、模拟器、独立游戏和无数工具默默打包——这个结果本身就是论据。单文件 + 公共领域的组合后来也成了流派，r-lyeh/single_file_libs 维护着一份同类单文件库列表（README 里的原始链接 nothings/single_file_libs 会重定向过去）；stb 自己则更新换底层库——stb_image_resize2、stb_sprintf 都是后来者重写——但"两次粘贴就能用"这个接口承诺，十二年没变过。
