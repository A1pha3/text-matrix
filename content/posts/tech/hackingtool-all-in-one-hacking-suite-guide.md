---
title: "HackingTool 拆解：215 个工具、21 个分类，和一个不许发明工具的 AI 层"
date: "2026-04-12T02:31:39+08:00"
lastmod: "2026-09-15T00:00:00+08:00"
slug: hackingtool-all-in-one-hacking-suite-guide
github_repo: "Z4nzu/hackingtool"
source_key: "gh:Z4nzu/hackingtool"
description: "HackingTool 在 2026 年完成两次重构（3 月 v2 结构重组、7 月 v3.0.0 AI 运营台），从数字菜单进化为带 AI 引导层的授权测试控制台：215 个工具、21 个分类、63 个标签，pipx 安装，支持 headless 编排。本文对照仓库核实其架构约束、安装路径与适用边界。"
draft: false
categories: ["技术笔记"]
tags: ["安全", "渗透测试", "AI Agent", "Python"]
---

# HackingTool 拆解：215 个工具、21 个分类，和一个不许发明工具的 AI 层

HackingTool 的价值从来不在工具本身——它集成的 Nmap、SQLMap、hashcat 全是独立维护的开源项目，绕过它直接用没有任何障碍。它替你做的是三件琐碎但耗时的事：把散落在各处的仓库收进一份可安装、可搜索的目录；给每个工具一条经过校验的安装路径；把你"想做什么"翻译成该用哪个工具、哪条命令。2026 年 7 月发布的 v3.0.0 把第三件事交给了一层带硬约束的 AI：模型只能从 63 个固定标签里做推荐，工具名永远由本地目录解析，模型无法发明一个不存在的工具，也无法看到工具的执行输出。

本文数据核验于 2026-09-15（GitHub API 与仓库 README、`docs/TOOLS.md`）。

> **授权边界**：HackingTool 面向授权安全测试——只对你拥有或获书面许可的系统使用。未授权入侵在大多数司法辖区属于犯罪行为。本文是项目解读，不构成任何攻击操作指导。

## 版本演进：两次重构改掉了什么

| 版本 | 时间 | 变化 | 证据 |
|------|------|------|------|
| v1.0 / v1.1.0 | 2020–2025 | 数字菜单启动器，`install.sh` 装依赖，约 9 个平铺模块 | git tag |
| v2.0.0 | 2026-03-15 | 结构重组：新工具、新 UI（PR #590） | 提交记录（此版本无 git tag） |
| v3.0.0 | 2026-07-26 | AI 运营台：215 个工具、AI 层、`/find` 发现、headless 编排 | git tag 与提交记录 |

网上大量教程（包括本文旧版）描述的是 v1 时代的形态：`install.sh` 装依赖、`python3 hackingtool.py` 启动、九个模块的数字菜单。这套流程在当前版本已经不成立——安装方式换成了 pipx，菜单换成了命令面板，模块数量从 9 个变成 21 个分类。照旧教程操作会在 Windows 支持这一步就碰壁：当前版本检测到 Windows 会直接提示并退出，而旧教程普遍写着"支持 WSL"。

## 仓库现状

| 指标 | 数值（2026-09-15） |
|------|------|
| Stars / Forks | 79,499 / 9,007 |
| 贡献者 | 36（GitHub 非匿名统计） |
| 提交数 | 340 |
| 许可证 | MIT |
| 语言构成 | Python 约 99%（按代码字节数），另有少量 Dockerfile、Shell、Makefile |
| 创建时间 | 2020-04-11 |
| 最新提交 | 2026-08-23（添加 context7.json） |
| 运行要求 | Python 3.10+；Linux 或 macOS（Kali、Parrot、Debian/Ubuntu、Arch 等） |

仓库创建于 2020 年，前五年靠"一键整合"积累人气，2023 年末到 2025 年的提交明显稀疏；2026 年两次密集重构之后，最新提交停在 8 月 23 日。项目活跃但不算高频迭代，选型时要注意后续维护节奏。

## 系统地图：一个控制台，四层分工

| 层 | 回答的问题 | 关键事实 |
|------|-----------|---------|
| 目录层（catalog） | 有哪些工具、怎么装 | 215 个活跃工具，21 个分类，63 个标签；另有 59 个已归档条目（上游停更或失效）默认隐藏 |
| 交互层 | 你怎么告诉它要什么 | 三类输入：`/` 命令、`@` 工具名或 `@tag:` 标签、其余按自然语言处理 |
| AI 层 | 该用哪个工具 | 可选、自带密钥（BYOK）；推荐结果只能是固定标签，由目录解析成工具 |
| 执行层 | 命令怎么跑 | 列表形式 `subprocess`（不经 shell）、下载钉版本并做 SHA-256 校验、不强制 sudo |

有一个容易踩的计数差异：应用内标题栏显示 22 个分类、217 个工具，比官方目录多出的 1 个分类和 2 个条目是内置的更新与卸载菜单。写文档或做统计时以 `docs/TOOLS.md` 的 215/21 为准。

## AI 层的约束设计

这一层是 v3.0.0 最值得看的部分。把 LLM 接进安全工具台，最容易出事的三条路径是：模型幻觉出不存在的工具、模型读到工具输出后被带偏、敏感环境里的数据流出。HackingTool 的做法是给模型留很窄的位置：

**推荐链路：模型只出标签，目录出工具。** 你输入"crack a wifi handshake"这类自然语言（或 `/ai` 命令），模型允许返回的只有 63 个固定标签里的若干个，标签到工具的映射由本地目录完成。模型没有任何直接输出工具名或命令的通道——它推荐不存在的工具这件事在结构上不成立。没有配置模型时，一个标准库实现的关键词匹配器顶上，推荐照常工作，只是少了语义理解。

**`/goal`：模型只调用一次，工具输出不回传。** `/goal find live subdomains of example.com` 会生成一份逐步计划（每步带理由和安装提示），要求你确认对目标有测试授权，然后按步执行：`[y]` 运行、`[s]` 跳过、`[e]` 编辑、`[q]` 中止。规划调用只发生一次，扫描结果不会喂回模型。每个目标在 `~/.hackingtool/goals/` 下有带时间戳的工作区，存 `plan.json`、`run.log` 和每步原始输出——事后审计看文件，不靠回忆会话。

**`/find`：零模型调用的工具发现。** 先搜本地 215 个工具，没找到再走 GitHub 搜索 API，结果按可信度排序展示并标注"未经我们审核"。它是纯建议：发现的条目写入 `~/.hackingtool/found.yaml`，不带安装或运行命令，永远不能被执行。匿名可用（每分钟 10 次 GitHub 搜索），配一个无权限的 token 可以提到每分钟 30 次。超出范围的请求（干扰、DoS、大规模目标、恶意软件）在任何网络调用发出之前就被拒绝；防御与取证措辞的请求不受影响。

**密钥管理。** AI 层默认关闭。启用时按顺序探测：配置了 `ai_base_url` 加 API key 就走 OpenAI 兼容端点，否则尝试本地 Ollama，再否则所有功能降级为确定性的离线行为。API key 只写入 `~/.hackingtool/.env`（权限 600），不进 `config.json`，也不会被回显。`/config test` 会报告探测失败的真实原因。

这套设计的取舍也很清楚：模型不碰执行、不碰数据，换来的是它帮不上执行的忙——长任务的逐步推理、根据扫描结果调整策略，这些仍要操作者自己判断。对一个把"可控"放在"聪明"前面的工具来说，这个取舍说得通。

## 安装与快速上手

推荐用 pipx 装到独立环境：

```bash
git clone https://github.com/Z4nzu/hackingtool.git
cd hackingtool
pipx install .
hackingtool
```

没有 pipx 时，macOS 用 `brew install pipx && pipx ensurepath`，Debian/Ubuntu/Kali 用 `sudo apt install pipx && pipx ensurepath`（装完开新 shell 让 PATH 生效）。等价替代：`uv tool install .`，或传统 venv 加 `pip install .`。后续升级是 `git pull && pipx install . --force`，卸载是 `pipx uninstall hackingtool`。也可以直接跑官方 Docker 镜像 `docker run -it --rm hardikzinzu/hackingtool:latest`。注意 PyPI 和 `.deb` 渠道在 README 中仍处于注释状态，尚未发布——不要按旧教程 `pip install hackingtool`。

装完启动，输入分三类：`/` 开头是命令（`/search subdomain`、`/tags`、`/run <tool>`），`@` 开头是工具名或标签（`@nmap`、`@tag:osint`），其余文本按"我想做什么"处理。类别内按 `1–N` 选工具、`97` 一键安装未装的工具、`99` 返回；工具内 `1` 安装、`2` 运行、`c` 让它给出针对你目标的完整命令。非交互终端或没装 prompt_toolkit 时会退回经典数字菜单，可用 `hackingtool --classic` 强制。

部分工具需要额外的语言运行时，核心应用本身不需要：

| 依赖 | 版本 | 涉及工具 |
|------|------|---------|
| Go | 1.21+ | nuclei、ffuf、amass、httpx、katana、dalfox、gobuster、subfinder |
| Ruby | 任意 | haiti、evil-winrm |
| tmux | 任意 | 后台面板（`/run <tool> … &`、`/panes`、`/attach`） |
| Docker | 任意 | Mythic、MobSF（可选） |

长扫描不该占着控制台——tmux 装好后，`/run nmap -sV -oA scan 10.0.0.5 &` 会把任务放进后台面板，`/panes` 列出、`/attach` 查看（`Ctrl-b` `d` 退回）、`/kill <label>` 终止。没装 tmux 就内联运行；`/config background_runner off` 可整体关闭。

## 任务流案例：一次授权的子域名侦察

假设你要对 example.com 做授权测试的侦察阶段，从零到产出走一遍：

```text
$ hackingtool
/goal find live subdomains of example.com
```

系统生成计划草稿：Subfinder 做被动枚举、httpx 探活、必要时 Amass 补充——每步带选择理由和安装提示。确认授权后逐步执行，每步输出落到 `~/.hackingtool/goals/<时间戳>/`。中途想改参数，按 `[e]` 编辑当前步；想先看别的，`/run httpx … &` 丢进后台面板再 `/attach` 回来看。

同样的流程在 CI 或报告流水线里可以用 headless 模式跑，不需要交互界面：

```bash
hackingtool --engagement acme --targets example.com --pipeline recon
hackingtool --engagement acme --report      # 确定性 Markdown 报告
hackingtool --engagement acme --ai-summary  # 可选：让 AI 摘要真实发现
```

headless 模式把各工具的输出归一成一份 `findings.json`，范围外的目标在执行前就被标记并记录。`--ai-summary` 和 `--ai-report` 是可选项，且 AI 只允许总结已经存在的发现——报告的正文永远来自工具的真实输出，不来自模型生成。

这个案例里能看到四层的配合：目录层提供 Subfinder/httpx 的安装路径，AI 层把它们从你的意图里"选"出来，执行层保证命令不经 shell、输出可审计，交互层用后台面板让长任务不阻塞。熟练之后你可能直接 `@subfinder` 跳过 AI 层——这恰好说明 AI 层是入口加速器，不是必经之路。

## 工具目录怎么读

21 个分类的规模分布很不均匀，工程投入也看得出来：

| 分类 | 工具数 | 代表 |
|------|--------|------|
| 信息收集 | 26 | Nmap、Amass、Subfinder、theHarvester、RustScan、SpiderFoot、TruffleHog |
| Web 攻击 | 23 | Nuclei、ffuf、OWASP ZAP、mitmproxy、WPScan、Nikto、Katana |
| 无线攻击 | 17 | aircrack-ng、Wifite、Bettercap、Airgeddon、Kismet、hcxdumptool |
| 后渗透 | 15 | pwncat-cs、Sliver、PEASS-ng、Ligolo-ng、Evil-WinRM、LaZagne |
| 钓鱼攻击 | 13 | Setoolkit、SocialFish、HiddenEye、Evilginx3、GoPhish |
| 取证 | 12 | Volatility 3、Wireshark、Autopsy、Binwalk、ExifTool |
| 逆向工程 | 10 | Ghidra、Radare2、jadx、apktool、Frida（移动类） |
| Active Directory | 10 | BloodHound、NetExec、Impacket、Responder、Certipy |
| 隐写术 | 10 | zsteg、Stegseek、outguess、stego-toolkit |
| 其余 12 类 | 4–10 | SQL 注入（SQLMap、Ghauri）、密码破解（hashcat、John、hydra）、云安全（Prowler、Pacu、Trivy）、移动安全（MobSF、Frida）、DDoS、RAT、XSS、Payload、漏洞框架、匿名、字典、其他 |

目录的编辑痕迹能反映行业重心：v1 时代的"社交媒体爆破"（Facebook/Instagram 账号爆破类工具）在 v3 目录里已经消失；取而代之的是一整套 AD 工具链、云安全审计（Prowler、ScoutSuite、Checkov）、DFIR 取证（Volatility 3、Eric Zimmerman 工具集）和大量 projectdiscovery 系的现代 Go 工具。钓鱼分类里甚至收了 GoPhish（钓鱼演练平台）和 MITRE ATT&CK T1566 参考——红队视角之外，蓝队做钓鱼演练也能直接用。

每个工具带固定标签（如 `osint`、`subdomain-enum`、`git-secrets`），`/tags` 列出全部 63 个标签及计数，`@tag:<名称>` 直接筛选。想加工具不用写 Python：大多数工具只是 `src/hackingtool/catalog/` 下的一个 YAML 条目，PR 跑 `make check`（lint + 测试 + 目录校验）通过即可。

## 适用边界与采用建议

**适合用**：

- 搞不清"这类任务该用哪个工具"的安全新手——推荐链路和 PortSwigger Labs、HackTricks 等学习资源集成在目录里，起点友好
- 需要在干净环境快速凑齐一套授权测试工具箱的人——pipx 安装不动系统 Python，SHA-256 校验过的下载路径比满屏 `curl | bash` 可信
- 想把侦察流程塞进脚本或 CI 的团队——headless 模式输出 `findings.json`，比解析各工具各自的日志格式省事

**不适合**：

- 已经有成熟工具链的红队/渗透团队——Sliver、BloodHound、Nuclei 这些工具你们都在直接用，多一层菜单只添麻烦；这个项目对你们的增量价值主要在 headless 编排和目录校验上
- 期望"AI 自动渗透"的人——模型不出命令、不看输出、不替你决策，复杂的攻击链规划仍然靠人
- Windows 原生环境——不支持，且没有折中方案，只能上 Linux/macOS 或虚拟机

**采用顺序**：先在 Kali/Parrot 虚拟机里 pipx 装一份，浏览 `/tags` 熟悉目录结构；跑一次 `/goal` 感受计划-确认-执行的节奏，重点看它对授权确认的强制程度；最后把 headless 模式接进你现有的报告流程，`findings.json` 的格式决定这一步的成本。生产环境的重型需求（C2、大规模 AD 域测试）仍然直接用 Mythic、BloodHound 本体。

## 法律与授权

未授权的渗透测试在大多数国家是犯罪行为。使用 HackingTool 及其集成的任何工具前，确认三件事：书面授权覆盖目标资产与测试时间窗、测试行为符合当地法律、发现的问题按约定的披露流程处理。项目自身的 SECURITY.md 定义了漏洞披露与发布校验政策。

## 资源链接

| 资源 | 链接 |
|------|------|
| GitHub | <https://github.com/Z4nzu/hackingtool> |
| 工具目录 | <https://github.com/Z4nzu/hackingtool/blob/master/docs/TOOLS.md> |
| 使用手册 | <https://github.com/Z4nzu/hackingtool/blob/master/docs/HOW-TO-USE.md> |
| 操作手册（AI 层规则） | `src/hackingtool/skill/OPERATOR.md`（应用内 `/skill` 查看） |
| 安全政策 | <https://github.com/Z4nzu/hackingtool/blob/master/SECURITY.md> |
| Docker 镜像 | `hardikzinzu/hackingtool:latest` |

## 自测题

1. **v3.0.0 里模型在推荐链路中扮演什么角色？为什么它无法推荐一个不存在的工具？**
   模型只允许返回 63 个固定标签中的若干个，标签到工具的映射由本地目录（`src/hackingtool/catalog/`）解析完成，模型输出里没有工具名和命令的位置。

2. **`/goal` 为什么只在规划阶段调用一次模型、且工具输出不回传？**
   防止工具输出污染模型上下文（诱导后续步骤偏离计划），也避免敏感扫描数据流出到模型端点。每步执行由人确认，产物落 `~/.hackingtool/goals/` 供审计。

3. **`/find` 发现的 GitHub 工具为什么"永远不能被执行"？**
   保存到 `~/.hackingtool/found.yaml` 的条目只含标题、标签、描述和链接，没有安装或运行命令字段——建议与执行在数据结构上被分开。

4. **当前版本对 Windows 的支持状态如何？与旧教程的说法有什么出入？**
   不支持，检测到 Windows 会提示并退出。旧教程（描述 v1 时代）普遍写"支持 WSL"，已过时。

5. **为什么说 HackingTool 对成熟红队团队的增量价值有限？他们可能用它做什么？**
   目录里的工具他们本来就在直接用，控制台反而是多余一层；有价值的部分是 headless 编排（归一化 `findings.json`）和经过校验的安装路径（新环境快速拉起）。

---

_仓库数据（Stars、贡献者、提交数、许可证）核验于 2026-09-15，来自 GitHub API；功能描述对照同日 master 分支的 README 与 `docs/TOOLS.md`。_
