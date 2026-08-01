---
title: "k-skill：把韩国本地生活琐事打包给编码代理的技能合集"
date: 2026-08-02T02:59:48+08:00
slug: "NomaDamas-k-skill-korean-life-skill-bundle"
description: "NomaDamas/k-skill 是一个面向编码代理的韩国生活场景技能合集，覆盖 SRT/KTX 订票、KBO/로또、当근/KakaoT/政府24/Hometax 等高频本地操作，通过 skills 协议接入 Claude Code、Codex、OpenCode 等代理。"
draft: false
categories: ["技术笔记"]
tags: ["Agent Skills", "Claude Code", "Codex", "韩国本地服务", "生活自动化"]
---

## 一句话判断

`k-skill` 不是一个新的代理运行时，而是一组**严格按照 Agent Skills 开放标准**打包的韩国本地生活技能模块：每个技能对应一个公开接口（如 SRT 订票、서울 지하철 도착정보、KakaoT Mac 아카이브 검색），由 `npx skills add` 一行命令安装到本地代理，让编码代理在不写额外集成代码的前提下顺手处理韩国用户的真实生活需求。

## 项目定位

仓库（`NomaDamas/k-skill`）自我定位是一份"给韩国人准备的 AI 代理技能合集"，覆盖场景包括：

- 出行：SRT/KTX/고속버스/시외버스 订票，자연휴양림 빈 객실，서울 실시간 혼잡도，따릉이 대여소
- 本地检索：서울 지하철 도착정보，지하철 분실물，한국 대중교통 길찾기，KakaoMap
- 通讯与数据：KakaoT Mac 아카이브 검색，GeekNews RSS/Atom
- 生活与环境：한국 날씨，미세먼지，한강 수위
- 法律与行政：한국 법령 검색，등기부등본 자동화，건축물대장，법인등기 컨설팅，지급명령 신청 보조
- 企业合规：국세청 사업자등록，체납 명단，금융위 기업기본정보，부정당제재업체，K-Startup 통합공고
- 公共与采购：나라장터 발주계획，국방전자조달 공고，인허가 영업상태，지방선거 후보자，공무국외출장 보고서

仓库 README 里出现的"한국인이면 깃허브 스타 눌러줍시다"不是营销话术，而是把"哪些技能值得长期维护"这件事直接交给本地用户决定。

## 安装与运行路径

```bash
# 安装所有技能
npx --yes skills add NomaDamas/k-skill --all -g

# 按需安装
npx --yes skills add NomaDamas/k-skill --skill srt-booking -g
```

要求只有两条：Node.js ≥ 18 与可用的 `npx`。Claude Code 用户也可以走 `claude plugin marketplace` 安装。

仓库明确说明：**代理不得在未经用户同意时调用 `gh repo star NomaDamas/k-skill`**。这条限制写得很死，是因为技能集合自身会影响代理在 GitHub 平台上的行为，所有写入型操作必须由人显式触发。

## 技能协议与代理集成

技能按"用户登录"维度分三档，README 表格里写得很清楚：

| 类别 | 含义 |
|------|------|
| 필요 | 用户自己必须持有登录态或密钥（如 SRT/KTX 实名购票、IROS 수동 로그인 + TouchEn、법원 전자소송 로그인 + 인증 + 결제 + 제출） |
| 불필요 | 公共/匿名接口即可调用（如 서울 실시간 혼잡도、한강 수위、국세청 무인증 공개 검색、LOCALDATA） |
| 선택사항 | 代理运营者持有官方密钥时功能更丰富，否则 fallback 到 hosted fallback（如 CODEF BYOK 自动收集时启用 korean-jangbu-for 增强路径） |

`k-skill-proxy` 是整个合集的统一前置代理层：本地技能不直接调用任何受限 API，而是把 HTTP 请求发到 proxy，由 proxy 持有运营者密钥。这意味着：

1. 本地代理不需要为每个技能各自配置 API key
2. 用户侧的密钥集合收敛到 0，只剩"需要自己登录"的强场景
3. hosted fallback 与本地直连两套路径可以共存

## 一个真实任务流：晚上 9 点代理帮订 SRT

把 SRT 订票当成任务流样本，验证一下技能组合是怎么在代理里被串起来的。

1. 用户用自然语言提需求："明早 7 点去釜山，最好靠窗有插座。"
2. 代理首先激活 `korean-transit-route` 与 `ktx-booking` 做可行性探测，调用 `korean-transit-route` 获得出发-到达路径预估
3. 探测到 7 点 KTX 紧张后，激活 `srt-booking` 走 SRT 余票查询；用户登录态已就位
4. 锁定 06:55 SRT，靠窗+插座确认（`ktx-booking` 提供 좌석번호·콘센트 좌석 확인）
5. 调用 `kakao-map` 反查出发地→SRT 역的最短汽车路径
6. 出票成功后由 `seoul-subway-arrival` 给出现场换乘到达时间

整条链路没有引入新的 agent runtime，只是在已有代理（Claude Code/Codex/OpenCode/OpenClaw）外加了一层标准化的 skill 描述文件 + proxy。

## 适用边界与不适用边界

**适用**：

- 已经在用 Claude Code / Codex / OpenCode 这类编码代理的韩国本地开发者
- 团队需要把"对外公共服务 + 对内强身份操作"两种场景在同一代理里分清楚

**不适用**：

- 非韩国用户（绝大多数技能强绑定 한국 공공데이터 + IROS/법원/국세청 接口）
- 完全不允许将任何凭据托管到 `k-skill-proxy` 的人（"필요"档的技能必须自己登录，等价于放弃自动化）
- 期待"全自动无人值守"的人：법원 전자소송、등기부등본 등 强合规场景里 README 反复强调 handoff 给浏览器的人手动作

## 与同类项目的差异

"代理技能合集"赛道最近半年变拥挤（`emilkowalski/skills`、`earthtojake/text-to-cad`、`virgiliojr94/book-to-skill` 等都跑进 trending），但 `k-skill` 的差异化在两处：

1. **不是教代理怎么写代码，而是教代理怎么用本地公共服务** —— 技能描述里几乎找不到"代码生成"语义，全部围绕"查询/提交/缴费"展开
2. **三档登录分级被显式编码进技能元数据** —— 这与一般 `skills add` 命令只关心"装不装得上"完全不同，让代理调度时直接知道哪些动作必须 handoff

如果只看一个仓库就能立刻意识到"Agent Skills 不只是给设计师和工程师用的"，`NomaDamas/k-skill` 就是那一记重击。