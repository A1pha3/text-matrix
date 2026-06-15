---
title: "Free-TV/IPTV：把 100+ 国家免费电视频道手工策展成一个 M3U playlist 的数据项目"
date: "2026-06-15T18:04:30+08:00"
slug: "free-tv-iptv-curated-free-tv-channels-m3u-playlist-guide"
description: "Free-TV/IPTV 是一个独立运营 5 年的 M3U 数据策展项目，把 DVB-S/T、YouTube Live 上的免费频道整理成一份统一 playlist。本文拆解它的策展哲学、目录组织、生成管线与跟 iptv-org 的取舍差异。"
draft: false
categories: ["技术笔记"]
tags: ["IPTV", "M3U", "数据策展", "FFmpeg", "Playlist"]
---

Free-TV/IPTV：把 100+ 国家免费电视频道手工策展成一个 M3U playlist 的数据项目

学习目标

- 看清 Free-TV/IPTV 这个仓库**不是软件工具**，而是一份长期人工维护的 M3U 数据集——理解这一点才不会被"克隆下来跑一下"的预期误导。
- 记住它的三条策展哲学：质量优先、只免费、只主流，并能用这些哲学解释为什么这个仓库只有几百个频道而不是几万。
- 读懂仓库的目录结构（`lists/*.md` + `playlist.m3u8`）与生成器 `make_playlist.py` 的关系，知道 PR 只能改 `.md`、不能直接改 `m3u8`。
- 区分它跟 iptv-org/iptv 的根本差别：Free-TV 走"几百个稳定频道"路线，iptv-org 走"几十万频道 + 自动失效检测"路线。
- 知道它的硬约束：无 SPDX License、只收录用户能证明"确实免费"的频道、依赖 IPTV 播放器（VLC/Kodi/IPTV Pro 等）。

---

## 1. 为什么写这篇文章

GitHub Trending 周榜最近又一次把 `Free-TV/IPTV` 顶上来——它是一个 2021 年 4 月创建、到现在 5 年多还在每天更新、Star 17k 的 IPTV 数据项目。仓库里**没有任何二进制、没有编译产物、没有 release**，只有一个 `playlist.m3u8` 文件夹 + 一堆 `lists/*.md` + 一个 Python 生成脚本。

这件事本身就值得专门写一篇：在一个"PR 几分钟就有人合并"的开发节奏里，一个**靠人手 PR 维护的纯数据仓库**为什么能稳定运行 5 年？它跟同领域的明星项目 `iptv-org/iptv`（122k stars）到底是什么关系，是竞品、子集、还是不同物种？

仓库当前状态（截至 2026-06-15）：

- 仓库：[Free-TV/IPTV](https://github.com/Free-TV/IPTV)
- Stars / Forks：约 17,099 / 2,547
- 主语言：Python（仅 `make_playlist.py` 一个脚本）
- License：仓库未声明 SPDX（README 也未明示），按 README 内容定位为公开数据集合
- Topics：`help-wanted`、`looking-for-contributors`
- 创建时间：2021-04-13
- 收录国家：100+（USA、CA、GB、AU、CN、HK、JP、KR、DE、FR、RU、BR、IN……）

注意：仓库没有 `LICENSE` 文件、也没有 SPDX 标识。使用前需要自行评估"无明确许可证 = 默认保留权利"这条默认规则的影响——下文第 5 节会展开。

---

## 2. 核心判断：这不是软件，是数据策展

很多人第一次看到这个仓库会问："克隆下来怎么跑？"答案是**不需要跑任何东西**。仓库的最终产物是：

```
https://raw.githubusercontent.com/Free-TV/IPTV/master/playlist.m3u8
```

把这一行粘进 VLC、Kodi、IPTV Pro、TiviMate、OTT Navigator 等任何支持 M3U 的播放器，就能直接拿到一份覆盖 100+ 国家、几百个频道的直播源列表。

这跟同领域的 iptv-org/iptv 在形态上非常像（同样是 M3U playlist + 同样的播放器兼容矩阵），但内部组织完全不同。下表是关键差异：

| 维度 | Free-TV/IPTV | iptv-org/iptv |
|------|--------------|---------------|
| 规模 | 几百个频道 | 几万到十几万个频道 |
| 收录策略 | 人工策展（PR 评审质量） | 自动抓取 + 用户提交 |
| 数据形态 | `lists/*.md`（人类可读） + `playlist.m3u8`（生成产物） | `streams/*.m3u`（机器可读） + 外部 `iptv-org/database` |
| EPG（电子节目单） | 不提供 | 由 `iptv-org/epg` 单独维护 |
| 失效处理 | 手工把失效频道移到 Invalid 分类、`[x]` 标记 | 自动化 cron 定期探测 |
| 频道元数据库 | 无独立数据库 | `iptv-org/database`（独立仓库，1.4k stars） |
| License | 无 SPDX | The Unlicense（公有领域） |

**结论**：两个项目不是替代关系，是不同物种。Free-TV 的目标是"给我一份稳定能看的清单"，iptv-org 的目标是"尽可能多地收录公开流并提供 API"。

---

## 3. 系统地图：仓库结构与生成管线

Free-TV 的仓库布局极简，但每一处都跟"数据策展"这个定位对齐：

```
Free-TV/IPTV/
├── playlist.m3u8              ← 最终播放列表（生成产物，不要 PR）
├── lists/                     ← 各国/语种的手工策展清单
│   ├── usa.md
│   ├── china.md
│   ├── japan.md
│   ├── germany.md
│   └── ... (100+ 国家)
├── make_playlist.py           ← 从 lists/*.md 生成 playlist.m3u8
└── README.md
```

### 3.1 `lists/*.md`：人类可读的策展层

每个 `lists/<country>.md` 是一个 Markdown 表格，列是这个频道的元数据。README 给出了清晰的列约定（基于仓库中实际表格示例）：

- **Channel**：频道名（带国旗 emoji 或图标）
- **URL**：流地址，但前面有状态前缀：
  - `[>]` 表示有效流，**会被收入最终 playlist.m3u8**
  - `[x]` 表示失效或暂时不可用，**留在表格但不进 playlist**
  - 无前缀的 URL 在 README 规则下不会被收入
- **画质标记**（追加在频道名后）：
  - `Ⓢ` = SD（标清）
  - `Ⓖ` = GeoIP 限制（部分国家能看、部分国家不能）
  - `Ⓨ` = YouTube Live 来源

举个例子（基于仓库真实片段抽象出的格式）：

```markdown
| Channel | url | HD/SD | Notes |
|---|---|---|---|
| CNN | [>](https://cnn.example.com/live.m3u8) | HD | |
| Local News | [x]() | | 失效流，保留待恢复 |
| YouTube Music Live | [>](https://youtube.com/watch?v=...) | Ⓨ | YouTube 来源 |
```

这种设计的好处：

1. **PR reviewer 看得懂**：一个 PR 上来就是表格的 +/- 行 diff，不需要懂 M3U 格式。
2. **状态可逆**：流失效了，把 `[>]` 改成 `[x]`，不需要删频道元数据；恢复时改回去就行。
3. **错误被编码在文本里**：`Ⓢ`/`Ⓖ`/`Ⓨ` 这些 unicode 字符就是机器可读的状态标记，不依赖额外元数据。

### 3.2 `make_playlist.py`：唯一的代码

整个仓库**只有这一个 Python 脚本**，职责单一：

1. 遍历 `lists/*.md` 下所有 `<country>.md`。
2. 用 markdown 解析器读出每个表格行。
3. 把状态是 `[>]` 的频道条目转换成 M3U `#EXTINF` + 流地址格式。
4. 把所有国家的条目合并、按规则排序，输出 `playlist.m3u8`。

这个脚本本身不抓取、不检测、不更新——它只是把"人工维护的 markdown"编译成"播放器能吃的 M3U"。所有"频道当前还能不能看"的知识都在 `lists/*.md` 里，由维护者和 PR 贡献者手动维护。

### 3.3 `playlist.m3u8`：只读产物

README 明确写了：**不要在 PR 里修改 `playlist.m3u8` 文件本身**。它是 `make_playlist.py` 运行后的产物，由仓库维护者定期（或 CI 自动）重新生成。提交改 playlist 的 PR 会被直接 close。

这条规则的存在说明一件事：仓库把"事实（频道元数据）"和"视图（M3U 播放列表）"明确分层。事实由 PR 改、视图由脚本生成——这是非常经典的数据-视图分离模式。

---

## 4. 策展哲学：为什么只有几百个频道

Free-TV 的 README 把策展哲学写得很硬，三条铁律：

> **Quality over quantity** — Less channels is better. All channels should work well. As much as possible in HD, not SD. Only one URL per channel.
>
> **Only free channels** — No paid channels. Only channels officially provided for free (DVB-S、DVB-T、analog 等)。
>
> **Only mainstream channels** — No adult, no particular religion, no particular political party, no channels made for a country and funded by a different country。

这三条翻译成技术决策就是：

- **频道数量天花板**被刻意压低。README 自己写"The less channels we support the better"——这种声明在开源数据项目里非常少见。
- **PR 评审要做的事实核查**包括："你能证明这个频道确实是免费的吗？"——这个证明要写到 PR 描述里。
- **失效流不删元数据**，只标记 `[x]`——确保频道历史信息可追溯、恢复成本低。

直接结果是：这个仓库收录的频道总数长期保持在几百个量级，而 iptv-org/iptv 的 streams 数量是 8-10 万级别。**前者是"能看的"，后者是"可能能看的"**。

---

## 5. 硬约束与适用边界

### 5.1 许可证状态

仓库根目录**没有 LICENSE 文件**，README 也没有声明 SPDX。这在 GitHub 上的默认含义是"All rights reserved"——其他人在没有明确授权的情况下不能直接 fork 后改 license 再发布。

实际使用层面：

- **个人看直播**：playlist URL 是公开的，拿去播放器里用没有法律风险（这是流地址本身的事，跟仓库 License 无关）。
- **基于这份 playlist 做衍生作品**：需要谨慎。最稳妥的做法是联系维护者或在 issue 里问清楚。
- **要规避 License 不明确的风险**：用 iptv-org/iptv（Unlicense / 公有领域）反而更省心。

### 5.2 频道流的有效期

playlist 里的频道流地址**大部分是第三方服务器提供的**（电视台自有 CDN、YouTube Live、Dailymotion Live 等）。这些地址会随时间失效，可能几周、几个月、几年。

Free-TV 处理失效的方式是**人工**——PR 把失效频道移到 Invalid 分类、`[x]` 标记。这意味着：

- 任何时刻打开 playlist 都会有一部分频道是失效的；
- 但失败模式是"少数频道放不出来"，不是"整个 playlist 失效"；
- 持续维护（PR 提交 + reviewer 合并）是这个仓库能用的前提。

### 5.3 地域限制

很多免费频道使用 GeoIP 限制——同一个频道流在美国能看、在欧洲不能看。Free-TV 在表格里用 `Ⓖ` 标记这些频道，PR 时会要求贡献者说明流在哪些国家能用。

这意味着 playlist **不是地域无关的资源**——打开播放器看到一堆频道但很多打不开是正常现象。

### 5.4 没有 EPG、没有 Logo 库、没有 API

Free-TV 不提供：

- EPG（Electronic Program Guide，节目单）—— 需要自己找；
- 频道 Logo 数据库—— 部分频道行里附了 imgur 图标，但不是统一库；
- 查询 API—— playlist 是静态文件，没有元数据查询能力。

如果需要这些，要去找 iptv-org 的 epg / database / api 三个仓库（合计 2k+ stars），或者自建。

---

## 6. 使用方式：3 步上手

仓库最终交付物就是一行 URL，使用流程极简：

### 步骤 1：选一个支持 M3U 的播放器

主流选项：

- **桌面**：VLC（跨平台，免费）、Kodi + PVR IPTV Simple Client（跨平台，免费）
- **移动**：IPTV Pro（Android）、TiviMate（Android，付费但口碑好）、OTT Navigator（Android）、iPlayTV（iOS）
- **智能电视/盒子**：TiviMate（Android TV）、IPTV Smarters

### 步骤 2：导入 playlist URL

```
https://raw.githubusercontent.com/Free-TV/IPTV/master/playlist.m3u8
```

在播放器的"M3U URL"或"Add playlist"位置粘贴这行。播放器会拉取 M3U 文件、解析 `#EXTINF` 条目、显示出频道列表。

### 步骤 3：分类浏览

M3U 文件里频道按国家分组（group-title）。展开你所在的国家分组，挑一个频道点开。**如果某个频道打不开**——大概率是 GeoIP 限制或者流已失效。换另一个频道看就行。

### 可选：用 `make_playlist.py` 自定义输出

如果想把所有频道 dump 到本地，自己跑：

```bash
git clone https://github.com/Free-TV/IPTV.git
cd Free-TV/IPTV
python3 make_playlist.py
# 输出 playlist.m3u8
```

不过这个脚本不带参数——要定制（比如只输出某个国家、只输出 HD 频道）需要改源码。

---

## 7. 怎么参与贡献

仓库 README 把贡献规则写得很清楚，关键点：

1. **不要改 `playlist.m3u8` 文件**。这是生成产物，改它的 PR 会被 close。
2. **只改 `lists/*.md`**。所有频道元数据都在这里。
3. **添加频道**要在 PR 描述里证明"这个频道确实是免费的"。例如贴出电视台官网的"Free to air"声明。
4. **删除频道**要证明"这个频道现在只有付费订阅能看"。注意 README 明确说"公共税收资助的电视（无论叫 TV License 还是其他名字）不构成付费订阅"——这条规则避免误删公共服务频道。
5. **失效频道不要删**，移到 Invalid 分类、把 `[>]` 改成 `[x]`。
6. **issue 只用来提 bug 和 feature request**。添加/编辑/删除频道要走 PR，不要发 issue。

对贡献者来说，这意味着**修改的最小颗粒度是一个 Markdown 表格行**——非常友好，不需要懂任何 M3U 知识。

---

## 8. 适用人群与不适用人群

### 适合

- **想有一份"打开就能看"的全球免费电视清单**的人。装个 VLC、粘一行 URL、就能看。
- **研究者 / 数据分析师**：想看"100+ 国家公开流媒体地址是怎么组织的"——`lists/*.md` 是个很干净的样本。
- **想为开源数据项目做贡献**但不想写代码的人：贡献方式就是改 Markdown 表格，门槛极低。
- **需要规避自动失效检测失效**的人：iptv-org 的自动 cron 偶尔会误杀有效流，Free-TV 的人工评审更稳。

### 不适合

- **想要 EPG 节目单**——Free-TV 不提供，需要用 iptv-org 的 epg 仓库或第三方服务。
- **想要几万个频道**——Free-TV 的定位就是"几百个稳定的"，不想要的话用 iptv-org。
- **想做商业二次分发**——仓库 License 不明确，商业场景需要谨慎。
- **完全不想自己处理失效频道**——playlist 里总是有失效项，靠手动跳过去。

---

## 9. 总结

`Free-TV/IPTV` 不是一个软件项目，**它是一个用 Markdown 表格 + Python 生成脚本长期人工维护的 M3U 数据集**。5 年的稳定运行说明这种"数据-视图分离 + 人工策展 + 严格 PR 规则"的模式在小规模数据项目上完全可行。

它的真正价值不在 playlist 本身，而在三件事：

1. **策展哲学的样板**：质量优先、只免费、只主流——这三条铁律比一万个频道都重要。
2. **数据-视图分离的最小化实现**：`lists/*.md`（事实）+ `make_playlist.py`（视图）+ `playlist.m3u8`（产物），三件套互不重叠。
3. **贡献门槛低到只有 Markdown**：PR reviewer 看的是表格 diff，不是代码。

如果你想参与一个**低代码、低冲突、长期维护**的开源数据项目，Free-TV/IPTV 是个值得 clone 下来看一眼的样本。如果你只想要一个能用的 M3U playlist——粘那行 URL 进 VLC 就行。

---

## 参考链接

- 仓库主页：[Free-TV/IPTV](https://github.com/Free-TV/IPTV)
- 直接使用的 playlist：[playlist.m3u8](https://raw.githubusercontent.com/Free-TV/IPTV/master/playlist.m3u8)
- 同领域参考：[iptv-org/iptv](https://github.com/iptv-org/iptv)（大规模、Unlicense、有 EPG 和数据库）
- 播放器参考：[VLC](https://www.videolan.org/)、[Kodi](https://kodi.tv/)、[TiviMate](https://tivimate.com/)