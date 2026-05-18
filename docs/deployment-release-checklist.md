# Text Matrix 发布检查清单

这份清单用于把 `text-matrix` 的发布流程固定下来，减少“本地正常、线上缺页”这类问题再次出现。

## 当前发布链路

- `GitHub Pages`：通过 [/.github/workflows/hugo.yml](/Volumes/mini_matrix/github/a1pha3/web/text-matrix/.github/workflows/hugo.yml) 构建与部署
- `Cloudflare Pages`：通过 `npm run build:cloudflare-pages` 构建
- Hugo 产物目录：`public/`

## 已接入的自动校验

### 1. 未来发布时间校验

命令：

```bash
npm run validate:future-dates
```

作用：

- 拦截 `draft = false` 但 `date` 晚于当前时间的页面
- 避免 Hugo 在生产构建中静默排除这些页面

### 2. 关键产物校验

命令：

```bash
npm run validate:release-assets
```

作用：

- 检查首页、关于页、搜索页
- 检查 3 个专题页
- 检查分类/标签关键入口
- 检查 Pagefind 前端资源

清单位于 [scripts/expected-public-files.txt](/Volumes/mini_matrix/github/a1pha3/web/text-matrix/scripts/expected-public-files.txt)。

## 本地发布前检查

依次执行：

```bash
npm run validate:future-dates
npm run build
npm run validate:release-assets
```

如果本地是为了验证 Cloudflare Pages 的正式构建路径，执行：

```bash
CF_PAGES_URL=https://txtmix.com CF_PAGES_BRANCH=main npm run build:cloudflare-pages
```

## Cloudflare Pages 配置要求

- Production branch: `main`
- Build command: `npm run build:cloudflare-pages`
- Build output directory: `public`

如果后续新增专题页、核心栏目页或新的搜索静态资源，需要同步更新：

- [scripts/expected-public-files.txt](/Volumes/mini_matrix/github/a1pha3/web/text-matrix/scripts/expected-public-files.txt)

## 上线后人工验收

至少手动检查这些路径：

- `/`
- `/about/`
- `/search/`
- `/ai-agent/`
- `/coding-agent/`
- `/open-source-ai-tools/`
- `/categories/`
- `/tags/`

重点确认：

- 首页是否为当前专题型结构
- 专题页是否不是 404
- 搜索页是否能加载 Pagefind 资源
- 文章页文末 CTA 与继续阅读是否存在
