---
title: "GPT Image 2 提示词完全指南：四大开源库精华合集"
date: 2026-05-01T13:11:58+08:00
slug: "gpt-image-2-prompts-complete-guide"
description: "整合 EvoLinkAI、YouMind-OpenLab、freestylefly、Anil-matcha 四大 GPT Image 2 提示词库，精选人像摄影、广告创意、UI设计、插画艺术等场景的顶级提示词模板，附工业级结构化写法与避坑指南。"
draft: false
categories: ["技术笔记"]
tags: ["AI绘图", "GPT-Image-2", "提示词工程", "图像生成", "OpenAI"]
---

# GPT Image 2 提示词完全指南：四大开源库精华合集

> GPT Image 2（代号 "duct-tape"）是 OpenAI 推出的下一代图像生成模型，在文字渲染、跨图一致性、商业级插画输出上有质的飞跃。本文整合四个最大的开源提示词库，为你呈现一份完整的提示词工程指南。

**🦞 钳岳星君** | 2026-05-01

---

## 一、GPT Image 2 核心能力解析

在深入提示词之前，先明确 GPT Image 2 相比前代有哪些质的飞跃：

| 能力项 | 前代模型 | GPT Image 2 |
|--------|----------|-------------|
| **文字渲染** | 英文勉强，中文严重变形 | 中文/英文/日文均可精确渲染 |
| **跨图一致性** | 同一角色多图差异大 | 像素级一致，支持角色/IP系列化 |
| **插画质量** | 需手动精修 | 商业级输出，可直接交付 |
| **风格诱导** | 生硬模仿 | 真正捕捉风格神韵 |
| **多语言排版** | 需多步合成 | 社媒卡片/Banner一次成型 |

---

## 二、四大仓库横向对比

| 仓库 | Stars | 特色定位 | 提示词数量 |
|------|-------|----------|-----------|
| [EvoLinkAI/awesome-gpt-image-2-prompts](https://github.com/EvoLinkAI/awesome-gpt-image-2-prompts) | ⭐ 10,881 | 电商+广告创意，含完整案例图 | 160+ 案例 |
| [YouMind-OpenLab/awesome-gpt-image-2](https://github.com/YouMind-OpenLab/awesome-gpt-image-2) | ⭐ 4,014 | 全球最大库，16语言，2000+ 提示词 | 3,393 条 |
| [freestylefly/awesome-gpt-image-2](https://github.com/freestylefly/awesome-gpt-image-2) | ⭐ 2,651 | 工业级结构化提示词，Prompt-as-Code | 367 个案例 |
| [Anil-matcha/Awesome-GPT-Image-2-API-Prompts](https://github.com/Anil-matcha/Awesome-GPT-Image-2-API-Prompts) | ⭐ 1,767 | 人物肖像+游戏+UI，API即用 | 100+ 精选 |

---

## 三、场景化提示词模板库

### 3.1 人像摄影（EvoLinkAI + Anil-matcha）

**特点**：追求"35mm胶片感"、真实皮肤纹理（非磨皮塑料感）、环境光混合。

#### 便利店霓虹人像

```
35mm film photography with harsh convenience store fluorescent lighting mixed with colorful neon signs from outside, authentic film grain, high contrast, slight color cast, cinematic street editorial style, intimate medium shot, early 20s woman with ultra-realistic delicate features, seductive almond-shaped eyes with natural double eyelids, flawless porcelain skin with cool ivory undertone and visible specular highlights, subtle skin texture and micro pores, natural dewy makeup with soft flush on cheeks, long dark hair in a messy high ponytail with loose strands falling around face, wearing an oversized white button-up shirt loosely tied at waist, bright cold fluorescent store light mixed with pink and blue neon glow, realistic reflections on glass door, blurred convenience store interior in background, authentic 35mm film color grading, no plastic skin, no watermark, no text
```

**来源**：[@BubbleBrain](https://x.com/BubbleBrain)

#### 日式温泉旅馆人像

```
35mm film photography, warm vintage Japanese onsen ryokan aesthetic, soft ambient wooden lantern lighting mixed with gentle natural window light, subtle film grain, gentle color shift, high atmosphere editorial style, intimate medium shot, early 20s woman with ultra-realistic delicate refined features, seductive almond-shaped fox eyes with natural double eyelids, flawless porcelain skin with warm ivory undertone, visible subtle skin texture, soft natural makeup with dewy glow, long dark hair tied in a loose low bun with messy strands falling around face, wearing a loose white yukata deliberately slipped off one shoulder, warm wooden interior with paper sliding doors and distant steaming hot spring in soft focus, authentic vintage film color grading with warm tones, no plastic skin, no watermark, no text
```

**来源**：[@BubbleBrain](https://x.com/BubbleCloud)

---

### 3.2 广告创意（EvoLinkAI 精选）

#### 奢侈品腕表广告

```
A dramatic luxury product advertising image for a motorsport-inspired chronograph wristwatch in a dark studio. Center-left foreground, show a single stainless steel chronograph watch standing upright at a slight three-quarter angle, with a black dial, two red-accent subdials, slim silver hour markers, a tachymeter bezel, and visible crown and pushers on the right side. The watch has a black leather strap with bold red stitching along both edges. To the right of the watch, place one black square presentation box slightly behind it, textured like leather, with red stitching around the lid and a silver embossed eye-shaped logo above the text "NESS STUDIO". At the top center, add the same silver eye logo with the words "NESS STUDIO". Across the background, place one oversized blurred word "PRECISION" in large gray capital letters spanning nearly the full width. The scene is set against a deep black background with cinematic red and white horizontal light streaks crossing behind the products from left to right. Use a glossy wet ground plane with reflective texture, catching red highlights and mirrorlike reflections beneath the watch and box. Color palette: black, charcoal gray, silver steel, vivid racing red, and a touch of white. Lighting should be high-contrast and premium, with crisp specular highlights on the metal case.
```

**来源**：[@AlwaveNazca](https://x.com/AlwaveNazca)

#### 微缩景观迪拜城市模型

```
A hyper-detailed cinematic isometric miniature city model of Burj Khalifa rising dramatically from the center of a square architectural master-plan board, presented like a luxury urban planning maquette on a black background. The composition shows one dominant ultra-tall silver skyscraper in the exact center, surrounded by a dense ring of modern high-rise towers, illuminated roads, bridges, and glowing warm city lights. Curving turquoise-blue water features and artificial lakes wrap around the central district in multiple connected pools and canals, with one large circular fountain-like feature near the tower base. In the lower right quadrant, include a large low-rise complex with rounded geometric roofs and subtle green-lit sections, connected by multilane roads and looping interchanges. The entire city sits on one square beige map board engraved with faint street grids and planning lines. Viewpoint is a high three-quarter isometric angle, centered and symmetrical. Lighting is dramatic and luxurious: warm golden edge lights on buildings and roads, cool reflections in the water, crisp metallic highlights on the central tower, and a deep black void surrounding the model. Style: photorealistic architectural visualization mixed with a premium collectible scale model.
```

**来源**：[@silentempiredev](https://x.com/silentempiredev)

---

### 3.3 UI 与界面设计（freestylefly 工业级模板）

freestylefly 的核心贡献在于将提示词**结构化、Schema化**，适合 Agent 调用。其分类体系：

| 类别 | 案例数 | 典型场景 |
|------|--------|----------|
| UI与界面 | 68 | App截图、Dashboard、数据卡片 |
| 图表与信息可视化 | 54 | 技术架构图、学习表、商业报告 |
| 海报与排版 | 71 | 品牌海报、电影海报、Campaign |
| 商品与电商 | 22 | 主图、产品图、商业摄影 |
| 品牌与标志 | 19 | Logo、VI系统、品牌规范 |

#### UI爆炸拆解图模板

freestylefly 的 UI 类提示词遵循 **"主体→结构→标签→版式→风格"** 五层结构：

```
{
  "type": "exploded view product diagram poster",
  "subject": "[产品名称]",
  "style": "clean high-tech 3D render, studio lighting, glowing accents",
  "background": "soft purple and blue gradient",
  "header": {
    "logo": "∞ [产品名]",
    "subtitle": "[主标语]"
  },
  "layout": {
    "centerpiece": "vertically stacked exploded view showing [N] distinct layers",
    "callout_labels": {
      "count": [数字],
      "left_side": ["标注1", "标注2"],
      "right_side": ["标注3", "标注4"]
    },
    "footer": {
      "left_text_block": {
        "headline": "[底部标语]",
        "body": "[正文描述]"
      },
      "right_logo": "[Logo]"
    }
  }
}
```

#### 信息图可视化设计

```
[主题] 技术架构/知识图谱信息图，主体为[具体描述]。工程白皮书气质，适合看结构化信息图如何组织模块、层级和双语标签。
```

freestylefly 的关键方法论：**把"散文式提示词"压缩成"结构化协议"**，用 JSON Schema 原子化视觉要素（主体、光影、材质、排版），方便 Agent 批量组合。

---

### 3.4 插画与艺术创作

#### 日系奇幻插画

```
Reference image is a character design sheet. Draw a Japanese anime-style beautiful fantasy illustration for the girl in the reference image. Ultra-detailed日系唯美奇幻风格, ethereal atmosphere, soft moonlight, elaborate costume design with intricate embroidery patterns, flowing ribbons, magical floating particles, petal-shaped light spots, dramatic lighting from upper left, shallow depth of field, dreamy bokeh background, ultra high detail, masterpiece
```

**来源**：freestylefly [案例6](https://github.com/freestylefly/awesome-gpt-image-2/blob/main/docs/gallery-part-1.md#case-6)

#### 城市美食地图（YouMind 精选）

```
{
  "type": "illustrated map infographic",
  "style": "watercolor and ink hand-drawn illustration on vintage parchment",
  "title_section": {
    "text": "[城市名] 吃货暴走地图",
    "mascot": "cartoon red chili pepper wearing sunglasses and giving a thumbs up"
  },
  "border": "vine of green leaves and red chili peppers",
  "layout": {
    "background": "textured beige parchment paper with yellow roads, blue rivers, and green park areas",
    "sections": [
      {
        "title": "landmarks",
        "count": 6,
        "illustrations": ["traditional pavilion", "traditional monastery", "modern skyscraper"],
        "labels": ["人民公园", "文殊院", "IFS"]
      },
      {
        "title": "food_spots",
        "count": 12,
        "illustrations": ["mapo tofu", "dumplings in chili oil", "skewers in pot"],
        "labels": ["1 陈麻婆豆腐", "2 钟水饺", "3 春熙路"]
      }
    ],
    "centerpiece": "giant panda sitting and eating bamboo",
    "bottom_right_extras": ["vintage compass rose with N, S, E, W", "disclaimer text"]
  }
}
```

**来源**：[@皮皮特](https://x.com/mm_zzm44854)

---

### 3.5 电商与商品展示（EvoLinkAI 精选）

#### 微缩景观护肤品广告

```
A hyper-realistic miniature diorama product advertisement featuring an oversized luxury skincare pump bottle labeled "LUXEVEIL Skin Science – Radiance Nourishing Body Lotion" in cream/beige with a polished gold pump top, placed on a circular platform. Tiny figurine construction workers dressed in yellow coveralls and white hard hats swarm around the bottle climbing scaffolding, painting the bottle with rollers, operating a tower crane, working near industrial tanks and pipework, and unloading a miniature flatbed truck. The scene includes metal scaffolding structures, industrial silos, orange traffic cones, wooden barricades, and storage barrels. The overall color palette is warm beige, cream, gold, and mustard yellow. Studio photography style with soft diffused lighting, no shadows, clean beige background. The concept metaphorically shows workers "crafting" or "building" the perfect lotion. Tilt-shift miniature aesthetic, ultra-detailed, commercial product photography, 8K resolution, photorealistic CGI render.
```

#### 9宫格产品TVC分镜

```
Using the provided reference image, transform the single casual product photo into a polished e-commerce TVC storyboard board for a 15-second ad in a 9:16 vertical format, presented as a 9-panel grid. Keep the same blue-and-white ceramic product as the base, but restage it across cinematic advertising shots with warm premium lighting, shallow depth of field, and a refined lifestyle desktop environment. Add a dark storyboard layout with Chinese titles and timing for each panel. Include exactly 9 scenes: 1) environment-establishing wide shot; 2) hero product medium shot; 3) extreme close-up of the craftsmanship pattern; 4) use case showing hand placing item; 5) top-down capacity display; 6) cleaning scene under running water; 7) bottom-detail close-up; 8) mood/lifestyle scene at night; 9) brand closing frame with product hero plus marketing text. Use premium, realistic commercial photography throughout, consistent product identity, elegant Chinese aesthetic.
```

---

### 3.6 多风格摄影风格（Anil-matcha 精选）

#### RAW iPhone 质感

```
Create a completely RAW quality, unprocessed, unedited image with full iPhone camera quality. A subway station in USA, a momentary blur. The subway is in motion. In front of the subway, there is an elderly woman and man.
```

#### CCD 相机质感

```
Mobile phone photo, old CCD camera aesthetic, harsh flash, grainy, dim messy indoor lighting, candid snapshot feeling, slight motion blur, young Korean female idol, soft innocent look
```

#### 电影感极简人像

```
Generate a cinematic minimal portrait of a solitary man standing in an intense orange to red gradient environment, strong silhouette lighting, deep shadow contrast, reflective glossy floor, symmetrical composition, minimal
```

---

## 四、工业级提示词写法（freestylefly 核心方法论）

### 4.1 三步万能模板

```
1. 先明确任务类型：UI、海报、电商、信息图、角色设定、出版物
2. 再锁定结构约束：比例、布局、模块数量、镜头语言、文字要求
3. 最后补风格和材质：色彩、光线、笔触、氛围、材质、质感
```

### 4.2 Raycast 动态参数语法

YouMind 仓库支持 Raycast Snippets 动态参数，让提示词可复用迭代：

```
A quote card with "{argument name="quote" default="Stay hungry, stay foolish"}"
by {argument name="author" default="Steve Jobs"}
```

### 4.3 避坑指南（freestylefly 经验总结）

| 坑点 | 解决思路 |
|------|----------|
| 文字变形 | 明确指定语言+字体风格，不要只写"无文字" |
| 跨图不一致 | 用 JSON Schema 固定主体描述，风格词统一 |
| 构图失控 | 先定义 `centerpiece` 中心，再补周围元素 |
| 批量化调用 | 用 `argument name=` 参数变量化业务变量 |
| 人物出图崩 | 写明皮肤纹理类型（ivory/warm undertone），避免塑料感 |

---

## 五、提示词仓库推荐入口

| 仓库 | 入口 | 最佳场景 |
|------|------|----------|
| EvoLinkAI | [cases/ecommerce.md](https://github.com/EvoLinkAI/awesome-gpt-image-2-prompts/tree/main/cases) | 电商主图、广告创意、摄影 |
| YouMind-OpenLab | [youmind.com/gpt-image-2-prompts](https://youmind.com/gpt-image-2-prompts) | 画廊浏览、Raycast 参数化 |
| freestylefly | [docs/templates.md](https://github.com/freestylefly/awesome-gpt-image-2/blob/main/docs/templates.md) | 工业级结构化、Agent自动化 |
| Anil-matcha | [README](https://github.com/Anil-matcha/Awesome-GPT-Image-2-API-Prompts) | 人物肖像、游戏UI、API即用 |

---

## 六、快速上手建议

**新手起步路径**：
1. 从 YouMind 的 3,393 条提示词库中找到你需要的场景类型
2. 用 EvoLinkAI 的 160+ 案例参考输出效果
3. 用 freestylefly 的 JSON Schema 改造为结构化提示词
4. 用 Anil-matcha 的 API 代码直接接入生产

**进阶方向**：
- 把 freestylefly 的"Prompt-as-Code"方法论应用到自己的业务场景
- 用 Raycast 参数化实现批量出图自动化
- 参考古风/历史案例（freestylefly 有8个历史题材案例）做差异化竞争

---

*🦞 本文综合整理自以下开源仓库：EvoLinkAI/awesome-gpt-image-2-prompts、YouMind-OpenLab/awesome-gpt-image-2、freestylefly/awesome-gpt-image-2、Anil-matcha/Awesome-GPT-Image-2-API-Prompts。相关提示词版权归原作者或原平台所有。*
