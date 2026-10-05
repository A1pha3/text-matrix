---
title: "awesome-design-systems：163 个设计系统的资产开放度地图"
date: "2026-04-12T02:31:39+08:00"
lastmod: "2026-09-28T10:00:00+08:00"
slug: awesome-design-systems-complete-curated-guide
github_repo: "alexpate/awesome-design-systems"
source_key: "gh:alexpate/awesome-design-systems"
description: "alexpate/awesome-design-systems 用四个标签（组件、语言规范、设计文件、源码）给 163 个设计系统做资产标注：96% 附带组件，42% 给出 Voice & Tone 文案规范，73% 公开源码但官方提醒开源不等于可用。本文拆解清单的真实结构、统计口径与一次选型的完整走法。"
draft: false
categories: ["技术笔记"]
tags: ["设计系统", "组件库", "前端"]
---

# awesome-design-systems：163 个设计系统的资产开放度地图

## 先说结论

[awesome-design-systems](https://github.com/alexpate/awesome-design-systems) 的独特之处不在"收录全"——163 个条目算不上全网最全——而在它记录资产的方式。每个条目用四个标签标注这个设计系统开放了什么：组件（Components）、语言规范（Voice & Tone）、设计文件（Designers Kit）、源码（Source code）。多数组件库清单只关心第一项，这份清单把"文案怎么写"与"代码怎么写"并排放在同一张表里。

所以它适合回答的问题不是"我该装哪个组件库"，而是两个更靠前的问题：一个成熟的设计系统由哪几类资产组成？各家把资产开放到了什么程度？带着这两个问题去读那张 163 行的大表，比按需检索更有收获。

## 快速信息卡

| 项目 | 信息 |
|------|------|
| **仓库地址** | [alexpate/awesome-design-systems](https://github.com/alexpate/awesome-design-systems) |
| **Stars** | 26,036 |
| **Forks** | 1,666 |
| **许可证** | Unlicense（公共领域贡献） |
| **条目数** | 163 个设计系统 |
| **形态** | 单页 README 索引，仓库不含代码 |
| **最后推送** | 2026-04-28 |
| **数据核实日** | 2026-09-28 |

## 这份清单长什么样

仓库的全部内容就是一份 README：一张按字母排序的大表，每行一个设计系统，四列标签用 👍 标注该项资产是否存在。README 开头先给了一个工作定义：

> A design system is a collection of documentation on principles and best practices, that helps guide a team to build digital products. They are often embodied in UI libraries and pattern libraries, but can extend to include guides on other areas such as 'Voice and Tone'.

也就是说，清单视角下的"设计系统"不只是组件：组件库（UI library）、模式库（pattern library）和文案规范都是它的组成部分。这直接解释了四个标签的取法：

| 标签 | 官方定义 | 对应资产 |
|------|---------|---------|
| **Components** | 含代码化的模式与示例 | 可直接使用的组件库 |
| **Voice & Tone** | 语言使用方式的指引 | 文案与语气规范 |
| **Designers Kit** | 提供 Sketch / Photoshop / Figma 等设计文件 | 设计侧工作包 |
| **Source code** | 公开可查的源码 | 源码仓库入口 |

表尾的 Notes 有两条容易被忽略、却最值得读的声明：

1. **标记开源不等于开放使用**——官方原话是 "Projects marked as open source may not always be open to use. Always check the license of these projects before using them."。全表只有 Foyer Design System 一个条目用 🔒 标注了源码不公开，其余 119 个给出源码链接的条目仍需逐个核对许可证。
2. **三种"库"是三样东西**——官方承认 design systems、UI libraries、pattern libraries 经常被混用，而这份清单三者都收。读到某一行觉得"这也算设计系统？"时，答案就在这句声明里。

源码列的图标也有含义：猫（octocat）指向 GitHub，太空入侵者指向 Bitbucket，外星人脸指向 GitLab。同一列三种图标，读的时候别只认 GitHub。

## 四个标签切开的设计资产

把 163 行按四列统计（2026-09-28 读数），分布并不均匀：

| 标签 | 条目数 | 占比 | 读法 |
|------|-------|------|------|
| Components | 158 | 96% | 组件几乎是默认资产，没有它的 5 条全是纯规范 |
| Source code | 119 | 73% | 多数有源码，但"开源"与"可用"之间隔着许可证 |
| Designers Kit | 75 | 46% | 约一半把设计文件打包给设计侧 |
| Voice & Tone | 70 | 42% | 语言规范是最容易被忽略的一类资产 |

两组对照值得展开。

**第一组：没有 Components 的 5 个条目。** Mailchimp Content Styleguide、Monzo Tone of Voice、Duolingo、Finland Toolbox、Apple Developer Design Guidelines——前三个是纯文案规范，一个组件都没有。它们的存在说明 Voice & Tone 不是设计系统的附属装饰，而是可以独立成文的一类资产。内容型产品（邮件服务、银行、教育）比工具型产品更需要它。

**第二组：四个标签全勾的 31 个条目（约 19%）。** 这些是资产最完整的"全家桶"系统，挑几个代表：

| 系统 | 出品方 | 定位 |
|------|--------|------|
| IBM Carbon | IBM | 企业级后台，规范约束强 |
| Google Material Design | Google | 跨平台设计语言 |
| Adobe Spectrum | Adobe | 创意工具场景 |
| Salesforce Lightning | Salesforce | 企业应用与表单 |
| Shopify Polaris | Shopify | 电商商家工具 |
| Fluent UI | Microsoft | 跨平台设计体系 |
| AWS Cloudscape | AWS | 云控制台 |
| U.S. Web Design Standards | 美国政府 | 政务站点无障碍合规 |
| Alibaba Ant Design | 阿里巴巴 | 中后台组件体系 |
| Atlassian Design System | Atlassian | 协作工具 |

与全家桶相对的另一端是"两格条目"：Chakra UI、Mantine、shadcn/ui、Radix 这类社区组件库通常只有 Components 和 Source code 两格——它们本身就不试图成为完整设计系统，没有文案规范和设计文件很正常。用标签密度判断一个条目的定位，比看知名度更准。

另一个显眼板块是政务系统：GOV.UK、美国 USWDS、法国 DSFR、新加坡 SGDS、韩国 KRDS、加拿大 Aurora、意大利 DESIGNERS.IT 都在列。政务条目的共同特征是强调无障碍与合规，做面向公众的服务类站点时，这一板块比商业系统更值得先看。

## 一次选型怎么走

以"给中后台项目选设计系统"为例，这张表的完整用法如下。

**第 1 步：按出品方背景粗筛。** 企业后台场景先看出品方产品形态相近的条目——IBM Carbon、Salesforce Lightning、AWS Cloudscape、Microsoft Fluent 都是背靠自家庞大后台产品长出来的系统，表格里的定位一栏（链接名）基本能看出背景。

**第 2 步：查四标签。** 比如 IBM Carbon 那一行四个标签全勾：组件、文案规范、设计文件、源码都在。这意味着团队接入的不只是组件包，还有现成的文案指引和 Figma 库，设计与内容的协作成本都会低一些。

**第 3 步：点进源码列核对许可证与框架。** 官方 Notes 的提醒在这一步落地：源码公开不代表可以商用。同时注意清单本身不标注框架支持——Carbon 的组件官方主发 React 与 Web Components 版本，你的技术栈是否覆盖，要进各系统官网确认，这一步清单替代不了。

**第 4 步：只需要组件库时，看两格条目。** 如果团队已有自己的规范，只想找组件实现，Chakra UI、Mantine、shadcn/ui、Radix 这些两格条目比全家桶更合适——后者会把整套设计语言一起带进来，样式覆盖反而成为负担。

**走不通的场景也要认。** Vue 项目在这张表里没有专门分区：Element Plus、Vuetify、Naive UI、PrimeVue 都不在清单内（唯一沾边的 Vue Design System 是一个教学项目）。这份清单的筛选天然偏向"完整设计系统"而非"框架组件库"，这不是缺陷，是定位。

## 清单没覆盖的生态

清单只收"设计系统"条目，下面几类常用资源都不在收录范围内。做选型时需要在清单之外补课，这里按类给出当前入口（数据为 2026-09-28 读数）。

**React 组件库**：清单里的 Chakra UI、Mantine、shadcn/ui、Radix 之外，还有两个常被混淆的空白点。Material UI 不在清单内，它对 Material Design 的实现是 MUI 团队的独立实现（官方原话 "our independent implementation of Google's Material Design system"），并非 Google 官方交付，也没有完成 Material 3 规格；Headless UI 也不在清单内，它是 Tailwind 团队的无样式组件库，通常与 Tailwind 搭配。

**Vue 组件库**：清单完全缺席的领域，主流选择及其当前热度：

| 组件库 | 框架 | Stars | 定位 |
|--------|------|-------|------|
| Element | Vue 2 | 54,045 | 饿了么出品，Vue 2 时代主流，仅维护 |
| Vuetify | Vue 3 | 41,042 | Material Design 实现 |
| Element Plus | Vue 3 | 27,792 | Element 的 Vue 3 续作，中文文档友好 |
| Ant Design Vue | Vue 3 | 21,671 | Ant Design 的 Vue 移植 |
| Naive UI | Vue 3 | 18,563 | TypeScript 友好，主题灵活 |
| PrimeVue | Vue 3 | 14,458 | 跨框架 Prime 体系的 Vue 版 |

Element 与 Element Plus 是两个独立项目：Element 只覆盖 Vue 2，新项目直接选 Element Plus。

**设计令牌工具**：把颜色、间距、字号抽象成命名变量，一处定义、多端产出的工具链。清单不收，但它是自建设计系统的地基。代表是 Amazon 的 Style Dictionary（口号 "Style once, use everywhere."，已发布 4.0）与 Salesforce 的 Theo，格式层面 W3C 的 Design Tokens Community Group 也在推进交换格式草案。一个最小的令牌定义长这样：

```json
{
  "color": {
    "primary": { "value": "#1890ff" }
  },
  "spacing": {
    "sm": { "value": "8px" },
    "md": { "value": "16px" }
  }
}
```

Style Dictionary 读入令牌后按平台配置输出。一份可运行的最小配置（`config.json`）：

```json
{
  "source": ["tokens/**/*.json"],
  "platforms": {
    "css": {
      "transformGroup": "css",
      "buildPath": "build/css/",
      "files": [
        { "destination": "variables.css", "format": "css/variables" }
      ]
    }
  }
}
```

在项目根目录执行 `style-dictionary build`，即可得到 `build/css/variables.css`。改主色时只改令牌定义，Web、iOS、Android 的产物在各自平台的构建里同步更新。

**图标与字体**：清单同样不收。当前主流图标库的规模（按各自仓库实测）：Tabler 超过 6,000 个图标；Lucide 官方口径 1,600+（它是 Feather Icons 的社区延续）；Phosphor 单一权重下 1,000 个图标、共 6 种权重风格；Heroicons 是 Tailwind 官方出品，outline 风格 324 个；Feather 本体 287 个，仓库最近一次推送已停在 2025 年 3 月。字体方向 Inter、IBM Plex、JetBrains Mono 是技术产品文档的常见组合。

**移动端组件库**：一份时效提醒——搜到的移动端选型文章若还在推荐 NativeBase，注意它已被官方标记弃用（README 顶部即 "⛔️ DEPRECATED"），官方建议新项目改用其后续项目 gluestack-ui。

## 自建系统前的几个硬约束

如果读完全景决定自建，下面几条约束决定了系统上线后的维护成本，与选哪家的组件无关。

**令牌先于组件。** 令牌是单一数据源，所有组件从令牌取值。先写组件再补令牌的顺序，会把硬编码颜色散进几十个文件，回头调整视觉时逐个替换的成本远高于先行定义。

**命名一致性。** 相同语义的 prop 在所有组件里用同一个词：变体统一叫 `variant`，状态统一叫 `status`。混用 `type`、`state`、`mode` 会让使用方每接一个组件都要重新查文档：

```jsx
// 一致的命名
<Button variant="primary" size="medium" />
<Input status="error" />

// 不一致，应避免
<Button type="primary" />
<Input state="error" />
```

**可访问性按 WCAG 2.2 对齐。** WCAG 2.2 已于 2023 年 10 月成为 W3C 正式推荐标准，取代 2.1 成为当前对齐基准。键盘可达、焦点可见、对比度达标是组件层就要解决的问题，后补的成本极高。CSS 变量配合 `data-theme` 属性是主题切换的常见实现：

```css
:root {
  --color-primary: #1890ff;
  --bg-primary: #ffffff;
}

[data-theme="dark"] {
  --color-primary: #1890ff; /* 品牌色也可在暗色下单独调整，视设计而定 */
  --bg-primary: #141414;
}
```

```javascript
document.documentElement.setAttribute('data-theme', 'dark');
```

**性能上抓三条。** 组件库的包体优化主要靠 ESM 模块与 `sideEffects: false` 让 Tree Shaking 生效；首屏体积靠 `React.lazy()` 按需拆分；CSS-in-JS 选零运行时方案（如 Vanilla Extract），把样式计算留在编译期。

**版本管理走 SemVer。** `major.minor.patch` 分别对应破坏性变更、向后兼容的新功能、问题修复。破坏性变更必须升 major，并在 CHANGELOG 里写清迁移路径——组件库的消费方通常不止一个项目，升级路径含糊会直接阻塞下游。

**文档与第一个组件同时上线。** Storybook 在写第一个组件时就接入，`npx storybook@latest init` 一条命令完成初始化。组件库没有文档等于没有，补文档的最好时机是组件还只有一个的时候。

## 常见问题与故障排查

**Q1：直接 `npm install` awesome-design-systems 为什么不行？**
它是一份 README 索引，不是包。按清单找到目标系统的源码链接，再去对应仓库安装。

**Q2：设计系统、组件库、模式库有什么区别？**
README Notes 的说法：三者是不同的东西，但经常被混用，这份清单三者都收。落到标签上：组件库是 Components 一列的产物，完整设计系统通常四列都占。小团队先引组件库完全够用，多条产品线要统一视觉语言时再谈设计系统。

**Q3：选了 Radix UI 这类 Headless 库，为什么还要写大量样式？**
Headless 库只提供行为与无障碍能力，样式完全交给使用方。清单里 Radix、shadcn/ui 都只有 Components 和 Source code 两格，这正是它们的定位。项目周期短、设计资源少时，选自带样式的成品库更划算。

**Q4：设计令牌到底解决什么问题？**
主色、间距、字号需要全局调整时，改一处令牌定义，各平台产物在构建时同步更新。没有令牌，就要在几百个组件文件里逐个替换硬编码值。

**Q5：主题切换用 CSS 变量还是 Sass 变量？**
CSS 变量（自定义属性）。Sass 变量在编译时固定，运行时改不了；CSS 变量可以被 JavaScript 动态修改，配合 `data-theme` 属性切换即可实现暗色模式。

## 自测题

1. **四个标签分别对应哪类资产？清单里连 Components 标签都没有的 5 个条目是什么类型？**
   > Components 对应组件代码，Voice & Tone 对应文案规范，Designers Kit 对应设计文件，Source code 对应源码入口。没有 Components 的 5 条（Mailchimp、Monzo、Duolingo、Finland Toolbox、Apple Developer Design Guidelines）是纯规范类条目，其中三个是纯文案规范。

2. **"源码列给了 GitHub 链接"是否等于"可以在产品里自由使用"？**
   > 不等于。官方 Notes 明确提醒标记开源的项目未必开放使用，接入前必须逐个核对许可证；全表只有 Foyer 一条用 🔒 显式标出源码不公开，其余 119 个源码链接同样要查许可证。

3. **想给 Vue 项目找组件库，这份清单合适吗？**
   > 不合适。清单没有 Vue 组件库分区，Element Plus、Vuetify、Naive UI、PrimeVue 均不在收录范围内，需要到清单之外补课。

4. **全家桶条目（四标签全勾）在 163 条中占多少？与两格条目分别适合什么场景？**
   > 31 条，约 19%。全家桶适合从零建立完整设计语言、且设计与内容团队需要统一协作的场景；两格条目（如 Chakra UI、Radix）适合已有规范、只要组件实现的团队。

5. **自建设计系统时，为什么令牌要先行于组件？**
   > 令牌是单一数据源，组件从令牌取值。顺序颠倒会把硬编码值散进各组件，全局视觉调整时替换成本成倍增加。

## 进阶路径

**先用起来（本周可做）**：从中后台、政务、电商三类场景各挑一个全家桶条目（如 Carbon、USWDS、Polaris），点进官网通读其 Principles 与 Token 文档，感受完整设计系统的资产构成。

**再对照（下一步）**：把清单里同类型的 3-4 个系统按四标签、许可证、框架支持做成内部对照表，作为团队选型的第一步产出。政务项目优先看无障碍合规条款。

**自建时（长期）**：先用 Style Dictionary 把令牌管道搭起来，跑通 CSS 单端输出后再扩 iOS / Android；组件从 Button、Input 等高频原语起步，Storybook 从第一个组件就跟着走。

## 数据时效与来源

- awesome-design-systems 仓库数据（Stars 26,036、Forks 1,666、许可证 Unlicense、最后推送 2026-04-28）与 README 结构、163 条条目及四标签统计，均核对于 2026-09-28 的 GitHub API 与仓库 master 分支 README；开源项目数据会持续变化，使用时以仓库实际显示为准。
- Vue 组件库与图标库数据取自各项目 GitHub 仓库当日读数；NativeBase 弃用状态、Material UI 对 Material Design 的实现口径、Style Dictionary 4.0，分别取自各官方 README 原文。
- 最新条目与分类以[上游 README](https://github.com/alexpate/awesome-design-systems) 为准。

---

仓库地址：<https://github.com/alexpate/awesome-design-systems>
