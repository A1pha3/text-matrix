---
title: "Mebus/cupp：交互式生成社工密码字典的开源工具"
date: "2026-06-30T21:10:22+08:00"
slug: "mebus-cupp-password-profiler-guide"
description: "CUPP（Common User Passwords Profiler）是一款基于目标个人信息的交互式密码字典生成工具，6k Stars、Python、GPL-3.0，可用于合法渗透测试与取证调查，本文讲解其原理、快速上手、命令行选项、配置项与合规边界。"
draft: false
categories: ["技术笔记"]
tags: ["CUPP", "密码学", "渗透测试", "Python", "安全工具"]
---

# Mebus/cupp：交互式生成社工密码字典的开源工具

## 这篇文章解决什么问题

在做授权渗透测试或取证调查时，最常见的弱密码往往不是 `123456` 这种通用字典能覆盖的，而是基于目标个人信息的"社工字典"——`Alice2024!`、`Zhang@1990`、`Wang_iphone` 这类组合。通用字典命中率低，但手工拼这种字典既耗时又容易遗漏。CUPP（Common User Passwords Profiler）就是为这个场景设计的：跑一次交互式问答，工具根据目标姓名、生日、宠物、配偶、爱好等个人信息，自动拼接出高命中率的候选密码清单。

读完后你能：

1. 知道 CUPP 适合什么场景，不适合什么场景
2. 跑通交互式生成、社工字典再加工、下载大字典三种用法
3. 通过 `cupp.cfg` 自定义生成规则，理解拼接策略的边界
4. 把 CUPP 接到你已有的字典生成或 hashcat 工作流里

## 项目基本事实

| 指标 | 数值 |
|---|---|
| 仓库 | [Mebus/cupp](https://github.com/Mebus/cupp) |
| Stars / Forks | 6.0k / 2.0k |
| 语言 | Python（Python 3） |
| License | GPL-3.0 |
| 默认分支 | master |
| 状态 | 仍在维护（最近提交活跃） |

CUPP 不是一个密码破解工具，也不接入 hashcat、John the Ripper 这类密码攻击工具。它只做一件事：根据用户提供的信息生成候选密码清单，输出文本文件，由你决定下一步是手工测试还是接给爆破工具。

## 核心能力

### 交互式问答生成（`-i`）

最常见的用法。运行 `python3 cupp.py -i`，工具会按顺序问：名字、姓氏、昵称、生日、配偶姓名、配偶昵称、孩子的名字、宠物名、公司名、关键字等。每一项都可以直接回车跳过。回答完之后，CUPP 按内置的拼接规则生成一份 `.txt` 字典文件，文件名通常是 `<firstname>.txt`。

默认生成逻辑会覆盖三类组合：

- 名字、姓氏、昵称及其反向、缩写
- 数字后缀（生日、年份、常见数字）
- 特殊字符与 leet 替换（a→@、s→$、i→1、o→0）

例如下面这段问答之后：

```
> First Name: alice
> Surname: smith
> Nickname: ali
> Birthdate (DD/MM/YYYY): 15/03/1990
> Partner's name: bob
> Partner's nickname: bobby
> Partner's birthdate: 22/07/1991
> Child's name: charlie
> Pet's name: max
> Company name: acme
```

CUPP 输出的字典会包含类似这样的组合：`alice1990`、`Smith@1990`、`al1c3`、`alice_bob`、`CharlieMax!`、`Acme1990!`、`bobsmith15` 等数百到数千条。覆盖范围是"个人信息 + 常见变换"，并不是穷举。

### 已有字典再加工（`-w`）

```bash
python3 cupp.py -w existing.txt
```

传入一份已有字典，CUPP 在每行基础上追加数字、特殊字符、leet 变换，输出到 `existing.txt.cupp`。这条命令本质上是"字典扩展器"，适合你手上已经有一份基础字典，想加入社工变体时使用。

### 大字典下载（`-l`）

```bash
python3 cupp.py -l
```

下载经过 Alecto 项目（Phenoelit + CIRT 合并净化版）的用户名/密码字典。这条命令只在你需要一份规模更大的纯字典时才用，跟社工模式无关。

### Alecto 解析（`-a`）

```bash
python3 cupp.py -a
```

直接解析 Alecto DB 的默认用户名/密码，跳过下载步骤。适合已经下载过 Alecto 字典的离线场景。

## 配置项

CUPP 的行为通过 `cupp.cfg` 控制。默认配置里几个常被改的关键项：

| 配置项 | 默认值 | 作用 |
|---|---|---|
| `years` | `1990,1991,...,2026` | 拼接时使用的年份集合 |
| `chars` | `!,@,#,$,%,^,&,*,?,_,.,+,=,-` | 拼接时使用的特殊字符集合 |
| `numfrom` / `numto` | `0` / `100` | 拼接数字后缀的范围 |
| `leet` | `a->@, i->1, o->0, ...` | leet 替换规则 |

调整 `years` 是最高频的自定义：如果你调查的目标是 1990 年前后出生的职场人，把 `years` 限定在 1985–2000 之间能显著减少无效候选。`numfrom`/`numto` 默认 0–100，对应常见数字后缀（生日日、月、年龄尾数），但在某些场景下需要扩大到 1000+（如手机尾号后 4 位）。

## 合规边界与使用限制

**CUPP 只能用于合法场景**：

- 授权渗透测试（在书面授权范围内，针对已知目标生成字典）
- 取证调查（配合司法或合规调查）
- 教育与研究（在自己可控的环境里评估密码强度）
- 个人安全自检（对自己使用的密码做"如果被社工攻击会不会命中"的评估）

**绝对不适用**：

- 针对未授权目标的密码爆破
- 大规模账号枚举攻击
- 任何违反当地法律和计算机滥用法规的使用

工具本身没有任何内置"目标锁定"机制，输出文件是纯文本，不会主动调用任何攻击接口。但工具生成出来的字典一旦被用于未授权测试，所有的法律后果由使用者承担。GPL-3.0 也明确不提供任何担保。

## 接到更大的工作流

CUPP 输出的是标准字典文本，最容易接的就是 hashcat 和 John the Ripper：

```bash
# 生成字典
python3 cupp.py -i
# 假设输出 alice.txt
# 接 hashcat
hashcat -m 0 hashes.txt alice.txt
# 接 John
john --wordlist=alice.txt hashes.txt
```

也可以把 CUPP 的输出当成 Hydra 的用户名/密码文件源，做在线服务弱密码扫描。注意：在线扫描同样需要明确的书面授权。

## 适用与不适用

**适用**：

- 渗透测试开局阶段，需要一份针对目标的社工字典
- 红队演练中演示"基于公开信息的密码攻击"路径
- 给安全意识培训提供具体案例（让员工看到自己的密码组合模式能被自动生成）

**不适用**：

- 没有具体目标的"通用扫描"——CUPP 的价值在于社工维度，没有目标等于退化成普通字典生成器
- 已有完整 hashcat 规则集的场景——规则集已经覆盖大部分变换，CUPP 的拼接价值有限
- 需要 GPU 加速的纯 hash 爆破——CUPP 只生成字典，不参与 hash 计算

## 阅读路径建议

1. 第一次跑：先在自己环境里跑一次 `python3 cupp.py -i`，看看默认配置下的输出格式
2. 调整 `cupp.cfg` 的 `years` 和 `numto`，适配目标画像
3. 用 `-w` 把已有字典扩成社工变体
4. 把输出接进 hashcat 或 Hydra，注意只在授权范围内使用
5. 跑完之后清理本地生成的 `.txt` 文件——这些文件本身就是高敏感度的字典内容

仓库本身只有 2207 KB，单文件脚本，Python 3 即可运行，不需要额外依赖。直接 clone：

```bash
git clone https://github.com/Mebus/cupp.git
cd cupp
python3 cupp.py -i
```

读完后你应能在 10 分钟内跑出第一份针对具体目标的社工字典，剩下要做的是把它接到你已有的爆破或审计工作流里。