+++
date = '2026-03-22T00:10:00+08:00'
draft = false
title = 'Hugo 新手多平台上线实战（GitHub Pages、Vercel、Cloudflare）'
+++

# Hugo 新手多平台上线实战（GitHub Pages、Vercel、Cloudflare）

## 文档目标

本文面向第一次接触 Hugo、GitHub Pages、Vercel、Cloudflare 的新手，目标是让你从零开始完成一次完整上线闭环：

- 在 Mac 上创建一个 Hugo 站点
- 将代码托管到 GitHub
- 同一个仓库分别部署到 GitHub Pages、Vercel、Cloudflare
- 验证三个线上地址都可访问
- 后续只要 `git push`，三个平台都会自动更新

## 学习成果标准

当你完成本文后，建议用下面 4 条判断自己是否真正掌握：

- 你能独立解释 `hugo server` 与 `hugo --gc --minify` 的使用场景
- 你能独立完成一次从本地改动到三平台同时更新的发布
- 你遇到 404、构建失败、样式丢失时能按排障清单定位问题
- 你能安全地做一次 `git revert` 回滚并恢复线上站点

## 执行原则（新手强烈建议）

- 一次只改一类内容：先改文档内容，再改配置，避免混合变更难排查
- 每完成一个平台就做一次访问验证，不要三个平台全部配置完才看结果
- 出现错误先看平台构建日志，再改代码；不要盲目反复 `git push`
- 所有命令在项目根目录执行，执行前先用 `pwd` 确认路径

## 你会得到什么

完成本文后，你将拥有：

- 一个本地 Hugo 项目
- 一个 GitHub 仓库（作为单一代码源）
- 三个可访问的网站地址：
  - `https://<github-username>.github.io/<repo-name>/`（GitHub Pages 项目站点）
  - `https://<vercel-project>.vercel.app/`
  - `https://<cloudflare-project>.pages.dev/`

## 快速导航

- 先看“变量约定”，避免照抄命令时改漏参数
- 再按步骤 0 -> 13 执行，不要跳步
- 每完成一个平台就先做一次访问验证，再继续下一个平台
- 最后一定执行“三端同时发布验证”，确保自动化链路可用

## 变量约定（先统一，再操作）

为了避免命令复制后出错，先把本文中的变量替换规则记住：

| 变量 | 示例值 | 含义 |
| --- | --- | --- |
| `<github-username>` | `alice` | 你的 GitHub 用户名 |
| `<repo-name>` | `my-hugo-multi-deploy` | 你的仓库名 |
| `<vercel-project>` | `my-hugo-multi-deploy` | Vercel 项目名 |
| `<cloudflare-project>` | `my-hugo-multi-deploy` | Cloudflare Pages 项目名 |

你也可以在终端临时定义变量，减少手改错误：

```bash
GITHUB_USERNAME="<github-username>"
REPO_NAME="my-hugo-multi-deploy"
```

说明：

- `<vercel-project>` 与 `<cloudflare-project>` 通常会出现在默认域名里，但有时平台会自动附加随机后缀
- 如果你看到的线上域名与示例不完全一致，以平台控制台显示的实际域名为准

## 先理解 4 个核心概念

在动手之前，先建立最小认知，后面的步骤会更顺畅。

- Hugo：静态网站生成器，把 Markdown 和模板编译成 `public/` 目录里的 HTML、CSS、JS
- GitHub：代码托管平台，你的 Hugo 源码放在这里
- GitHub Pages / Vercel / Cloudflare：托管平台，读取你的仓库并自动构建发布
- CI/CD：持续集成与持续部署；每次推送代码后，平台自动重新构建并上线

## 三个平台有什么差异（先看这张表）

| 平台 | 推荐用途 | 访问路径特点 | 配置重点 |
| --- | --- | --- | --- |
| GitHub Pages | 与仓库深度绑定，开源项目常用 | 项目站点通常带仓库子路径 | Actions 工作流与 `baseURL` |
| Vercel | 部署快、预览体验好 | 默认根域名访问 | 导入仓库时的构建参数 |
| Cloudflare Pages | 全球节点、边缘网络能力强 | 默认根域名访问 | Pages 项目构建参数 |

## 平台配置速查表（部署时对照）

| 平台 | Git 提供方 | 生产分支 | 构建命令 | 输出目录 |
| --- | --- | --- | --- | --- |
| GitHub Pages | GitHub | `main` | `hugo --gc --minify --baseURL ".../"` | `public` |
| Vercel | GitHub | `main` | `hugo --gc --minify` | `public` |
| Cloudflare Pages | GitHub | `main` | `hugo --gc --minify` | `public` |

## 0. 前置准备清单

请确认你有以下账号：

- GitHub 账号
- Vercel 账号
- Cloudflare 账号

建议使用同一个邮箱注册，后续关联会更顺手。

## 1. 在 Mac 安装基础工具

### 1.1 安装 Homebrew（如果你还没安装）

在终端执行：

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

检查版本：

```bash
brew --version
```

### 1.2 安装 Git、Hugo（extended）、Node.js

```bash
brew install git hugo node
```

检查是否安装成功：

```bash
git --version
hugo version
node --version
npm --version
```

判定标准：

- 能看到版本号，说明工具可用
- `hugo version` 建议出现 `extended` 字样，兼容更多主题和资源处理场景

### 1.3 如果你在 Hugo 源码目录：先本地编译 Hugo 再创建站点

如果你当前就在 Hugo 源码目录（例如 `/Volumes/mini_matrix/github/a1pha3/hugo`），可以直接编译一个本地可执行文件来使用。

先进入源码目录并编译：

```bash
cd /Volumes/mini_matrix/github/a1pha3/hugo
go build -tags extended -o ./hugo
./hugo version
```

命令说明（`go build -tags extended -o ./hugo`）：

- `go build`：编译当前模块，生成可执行文件
- `-tags extended`：启用 `extended` 构建标签，编译出 Hugo Extended 版本（含 Sass/SCSS 等扩展能力）
- `-o ./hugo`：把输出文件名指定为当前目录下的 `hugo`

看到版本信息且包含 `extended`，说明编译成功。

接着使用这个二进制创建站点：

```bash
mkdir -p ~/Sites
cd ~/Sites
/Volumes/mini_matrix/github/a1pha3/hugo/hugo new site my-hugo-multi-deploy
cd my-hugo-multi-deploy
```

如果你希望后续直接使用 `hugo` 命令，可以临时加入 PATH：

```bash
export PATH="/Volumes/mini_matrix/github/a1pha3/hugo:$PATH"
hugo version
```

## 2. 创建 Hugo 项目

### 2.1 选择工作目录并新建站点

```bash
mkdir -p ~/Sites
cd ~/Sites
hugo new site my-hugo-multi-deploy
cd my-hugo-multi-deploy
```

### 2.2 初始化 Git 仓库

```bash
git init
git branch -M main
```

建议追加 `.gitignore`，避免把构建产物提交到仓库：

```bash
cat > .gitignore <<'EOF'
public/
resources/_gen/
.DS_Store
EOF
```

### 2.3 创建或安装主题（推荐先用现成主题）

你有两种方式：

- 创建新主题（适合想自己从零定制）：

```bash
hugo new theme mytheme
```

- 从主题站安装现成主题（适合先快速上线）：`https://themes.gohugo.io/`

下面给你一个可直接使用的安装示例（Ananke）：

```bash
git submodule add https://github.com/theNewDynamic/gohugo-theme-ananke.git themes/ananke
```

然后把 `hugo.toml` 替换为以下内容：

```toml
baseURL = "https://example.org/"
languageCode = "zh-cn"
title = "我的 Hugo 多平台站点"
theme = "ananke"
```

### 2.4 创建第一篇内容

```bash
hugo new content posts/hello-world.md
```

编辑 `content/posts/hello-world.md`，把内容改为：

```markdown
---
title: "Hello World"
date: 2026-03-21T10:00:00+08:00
draft: false
---

这是我的第一篇 Hugo 文章。  
如果你能在浏览器看到它，说明本地构建链路正常。
```

### 2.5 本地预览

```bash
hugo server -D
```

打开浏览器访问 `http://localhost:1313/`。

确认点：

- 首页可打开
- 能进入文章页
- 修改文章后浏览器会热更新

按 `Ctrl + C` 停止服务。

### 2.6 本地生产构建冒烟检查

在接入云平台前，先确认生产构建没问题：

```bash
hugo --gc --minify
ls public
```

判定标准：

- `public/` 目录存在
- 能看到 `index.html`
- 没有构建报错

## 3. 创建 GitHub 远程仓库并首次推送

### 3.1 在 GitHub 创建仓库

在 GitHub 网页点击：

- 右上角 `+` -> **New repository**
- Repository name 填：`my-hugo-multi-deploy`
- 可选 Public 或 Private（新手建议先用 Public）
- 不勾选 `Add a README`
- 点击 **Create repository**

说明：

- 不是必须 Public
- 如果使用 Private，GitHub Pages 是否可用取决于你的账号套餐与仓库权限策略
- Public 通常配置最简单、排障成本最低

### 3.2 关联远程地址并推送

把下面命令中的 `<github-username>` 换成你的 GitHub 用户名：

```bash
git remote add origin https://github.com/<github-username>/my-hugo-multi-deploy.git
git config --global user.name "你的名字"
git config --global user.email "你的邮箱"
git add .
git commit -m "init hugo site"
git push -u origin main
```

到 GitHub 仓库页面刷新，能看到代码说明推送成功。

如果推送时提示认证失败：

- 你可能需要在 GitHub 网页生成 Personal Access Token（PAT）作为密码使用
- 或使用 GitHub Desktop / SSH Key 完成认证

PAT 建议最小权限：

- 只给当前仓库需要的最小读写权限
- 不要把 PAT 写进文档、截图或提交到 Git 仓库

## 4. 配置 GitHub Pages 自动部署

这一节完成后，GitHub 每次收到 `main` 分支推送都会自动发布。

### 4.0 关键策略：`baseURL` 怎样设才不踩坑

如果你暂时没有自定义域名，一个仓库同时部署到三个平台时，`baseURL` 不可能同时精准匹配 3 个线上域名。新手阶段建议用下面策略：

- `hugo.toml` 里保留一个临时值，例如 `https://example.org/`
- GitHub Pages 在工作流里用 `--baseURL` 覆盖，保证 GitHub 站点路径正确
- Vercel 与 Cloudflare 先保证可访问，后续若接入自定义域名，再统一 `baseURL`

为什么这么做：

- 先保证“能稳定发布”比“链接绝对完美”更重要
- 后续切自定义域名时，只需要改一次 `baseURL`

先确认你的仓库类型：

- 项目站点：仓库名不是 `<github-username>.github.io`，访问路径通常带 `/<repo-name>/`
- 用户站点：仓库名是 `<github-username>.github.io`，访问路径通常是根路径 `/`

本文默认按“项目站点”讲解。

如果你使用 GitHub 免费账户，建议仓库保持 Public，以避免 Pages 发布权限限制。

### 4.1 创建工作流文件

```bash
mkdir -p .github/workflows
```

创建 `.github/workflows/hugo.yaml`，写入：

```yaml
name: Deploy Hugo to GitHub Pages

on:
  push:
    branches:
      - main
  workflow_dispatch:

permissions:
  contents: read
  pages: write
  id-token: write

concurrency:
  group: pages
  cancel-in-progress: false

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4
        with:
          submodules: recursive
          fetch-depth: 0

      - name: Setup Hugo
        uses: peaceiris/actions-hugo@v3
        with:
          hugo-version: "0.156.0"
          extended: true

      - name: Setup Pages
        id: pages
        uses: actions/configure-pages@v5

      - name: Build
        run: |
          hugo \
            --gc \
            --minify \
            --baseURL "${{ steps.pages.outputs.base_url }}/"

      - name: Upload artifact
        uses: actions/upload-pages-artifact@v3
        with:
          path: ./public

  deploy:
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    runs-on: ubuntu-latest
    needs: build
    steps:
      - name: Deploy
        id: deployment
        uses: actions/deploy-pages@v4
```

### 4.2 在 GitHub 打开 Pages

仓库页面 -> **Settings** -> **Pages**：

- Source 选择 `GitHub Actions`

### 4.3 推送配置并观察 Actions

```bash
git add .github/workflows/hugo.yaml
git commit -m "add github pages workflow"
git push
```

到 GitHub 仓库 -> **Actions**，等待工作流变绿。

成功后访问：

`https://<github-username>.github.io/my-hugo-multi-deploy/`

如果你使用“用户站点仓库名”，访问地址通常是：

`https://<github-username>.github.io/`

如果你沿用了本文的变量，可直接替换成：

`https://<github-username>.github.io/<repo-name>/`

## 5. 配置 Vercel 自动部署

### 5.1 连接仓库

在 Vercel 控制台：

- 点击 **Add New...** -> **Project**
- 选择 GitHub 并授权
- 选中仓库 `my-hugo-multi-deploy`

### 5.2 设置构建参数

在导入项目页面设置：

- Framework Preset：`Hugo`
- Build Command：`hugo --gc --minify`
- Output Directory：`public`
- Install Command：留空（默认）

然后点击 **Deploy**。

如果导入页面没有自动识别 Hugo，可以手工改成：

- Framework Preset：`Other`
- Build Command：`hugo --gc --minify`
- Output Directory：`public`

### 5.3 首次发布验证

部署完成后，打开生成的 `*.vercel.app` 地址。

确认点：

- 首页可访问
- 文章页可访问
- 没有 404 样式错乱

建议再做一项检查：

- 打开页面源代码，确认 `meta` 或 canonical 链接没有明显错误域名

## 6. 配置 Cloudflare Pages 自动部署

### 6.1 创建 Pages 项目

在 Cloudflare 控制台：

- 进入 **Workers & Pages**
- 点击 **Create application**
- 选择 **Pages**
- 选择 **Connect to Git**
- 连接 GitHub 并授权仓库

### 6.2 设置构建参数

选择仓库 `my-hugo-multi-deploy` 后，设置：

- Production branch：`main`
- Framework preset：`Hugo`
- Build command：`hugo --gc --minify`
- Build output directory：`public`

点击 **Save and Deploy**。

如果 Cloudflare 没有自动识别 Hugo，手工填以上 2 个关键字段也可以正常部署。

### 6.3 首次发布验证

部署完成后，打开 `*.pages.dev` 地址，检查首页和文章页。

## 6.4 三平台发布前的 60 秒自检

每次准备推送前，先在本地执行：

```bash
hugo --gc --minify
git status
```

快速判断：

- `hugo` 无报错再推送
- `git status` 只包含你预期修改的文件

## 6.5 发布验证命令（可选但推荐）

完成部署后，你可以用 `curl` 快速验证三个地址都返回成功状态：

```bash
curl -I "https://<github-username>.github.io/<repo-name>/"
curl -I "https://<vercel-project>.vercel.app/"
curl -I "https://<cloudflare-project>.pages.dev/"
```

判定标准：

- 返回状态包含 `200` 或 `301/302`（跳转到最终 200 页面）
- 如果长期是 `404` 或 `5xx`，优先回到对应平台的 Deployments 日志排查

## 7. 一次改动，三端同时发布（验证自动化）

现在做一次最关键验证：确认三平台都自动更新。

### 7.1 修改文章

编辑 `content/posts/hello-world.md`，新增一行：

```markdown
这是一条用于验证三平台自动发布的更新内容。
```

### 7.2 提交并推送

```bash
git add .
git commit -m "test multi platform auto deploy"
git push
```

### 7.3 观察三个平台的构建状态

- GitHub：仓库 **Actions** 页面
- Vercel：项目 **Deployments** 页面
- Cloudflare：Pages 项目 **Deployments** 页面

都完成后，分别刷新三个 URL，确认都出现新内容。

## 8. 常见问题排查（新手高频）

### 8.1 GitHub Pages 是 404

优先检查：

- 仓库 Settings -> Pages 的 Source 是否是 `GitHub Actions`
- 工作流是否成功（Actions 是否绿色）
- 访问 URL 是否包含仓库名路径：`/<repo-name>/`

### 8.2 Vercel 构建失败，提示找不到 Hugo

优先检查：

- Framework Preset 是否选了 `Hugo`
- Build Command 是否为 `hugo --gc --minify`
- 仓库根目录是否就是 Hugo 项目根目录

### 8.3 Cloudflare Pages 构建失败

优先检查：

- Build output directory 是否是 `public`
- Production branch 是否是 `main`
- Hugo 内容是否至少包含一篇 `draft: false` 的文章

### 8.4 本地预览正常，线上样式丢失

优先检查：

- `baseURL` 配置与平台路径是否匹配
- 浏览器是否命中过期缓存（强制刷新）
- 主题子模块是否正确拉取（`git submodule` 是否存在）

### 8.5 `git push` 被拒绝（non-fast-forward）

优先执行：

```bash
git pull --rebase origin main
git push
```

如果你不理解冲突内容，不要强推，先解决冲突再推送。

### 8.6 子模块相关报错（主题拉取失败）

执行：

```bash
git submodule update --init --recursive
```

如果是网络问题，重试即可；如果是私有仓库权限问题，需要先保证你有访问权限。

### 8.7 协作者拉取后页面样式缺失

如果你把主题作为子模块，协作者克隆仓库后需要执行：

```bash
git clone --recurse-submodules https://github.com/<github-username>/<repo-name>.git
```

已经 clone 但没拉子模块时执行：

```bash
git submodule update --init --recursive
```

## 9. 回滚与恢复（上线必备）

当你推送后发现页面异常，可以用最小回滚法快速恢复：

```bash
git log --oneline -n 5
git revert <问题提交的commit-id>
git push
```

说明：

- `revert` 会生成一个“反向提交”，不会破坏历史
- 三个平台会自动部署回滚后的版本

## 10. 推荐目录结构（完成后对照）

你的项目至少应包含：

```text
my-hugo-multi-deploy/
├── .github/
│   └── workflows/
│       └── hugo.yaml
├── content/
├── themes/
│   └── ananke/
├── hugo.toml
└── ...
```

## 11. 你的后续日常动作

上线完成后，你的日常流程可以固定为：

1. 本地写内容：`hugo server -D`
1. 提交代码：`git add . && git commit -m "xxx" && git push`
1. 等待三平台自动构建完成
1. 验证线上页面

这套流程跑通后，你已经具备静态站点多平台发布的完整基础能力。

## 12. 新手执行清单（最终验收）

完成全部步骤后，请逐项打勾：

- [ ] 本地 `hugo server -D` 可预览
- [ ] GitHub 仓库可看到 Hugo 源码
- [ ] GitHub Actions 部署成功且页面可访问
- [ ] Vercel 部署成功且页面可访问
- [ ] Cloudflare Pages 部署成功且页面可访问
- [ ] 修改一篇文章后，三平台都自动更新
- [ ] 我能根据日志定位一次失败原因，而不是只靠重试

## 13. 可选进阶：绑定自定义域名

如果你后续要把三个平台统一成自己的域名，可以按这个顺序做：

1. 先在一个平台完成自定义域名绑定并验证成功
1. 再决定是否把其余两个平台作为备份发布目标
1. 最后把 `hugo.toml` 的 `baseURL` 改成你的正式域名并重新部署

建议：

- 不要在三个平台同时绑定同一个生产域名，以免 DNS 与证书排障复杂度陡增
- 新手阶段优先使用平台默认域名完成流程，等流程稳定后再切正式域名

## 14. 已知边界说明（避免误解）

本文目标是“先跑通多平台自动部署流程”，因此有两个刻意取舍：

- 你会同时得到 3 个可访问地址，但 SEO 主域名建议只保留 1 个，其余用于预览或备份
- 在未统一自定义域名前，Vercel 与 Cloudflare 的 canonical 可能不是最终生产域名，这是预期现象
