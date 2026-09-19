---
title: "Next.js 深度拆解：React 全栈框架的事实标准"
slug: vercel-nextjs-react-fullstack-framework-guide
github_repo: "reactjs/rfcs"
source_key: "gh:reactjs/rfcs"
date: 2026-07-11T02:50:00+08:00
lastmod: 2026-09-18T09:00:00+08:00
draft: false
categories: ["技术笔记"]
tags: ["Next.js", "React"]
description: "Next.js 是 React 全栈框架的事实标准，渲染模型从 CSR/SSR/SSG/ISR 演进到 RSC 与 Cache Components。本文拆解其渲染模型演进、App Router 数据获取、部署路径，以及与 Remix/Astro/SvelteKit 的取舍。"
---

# Next.js 深度拆解：React 全栈框架的事实标准

## 核心判断

Next.js 之所以成为 React 全栈的事实标准，不是因为"React SSR 框架"——Remix、Astro、SvelteKit 都能做 SSR。它赢在**三件事的组合**：

1. **渲染模型并存演进**：CSR、SSR、SSG、ISR，再到 RSC 与 Cache Components——同一项目可混用
2. **App Router + Server Components**：让"哪些组件在服务端、哪些在客户端"成为代码级可声明的边界
3. **Vercel 平台深度集成**：从代码到边缘部署的"5 分钟部署"是它的护城河

App Router 在 13.4 转正、Server Components 稳定后，Next.js 早已不只是"React 框架"。到 Next.js 16（2025 年 10 月发布），Turbopack 成为默认打包器，Cache Components 进一步把"缓存哪些、流式补全哪些"也纳入代码级声明——它已经是一个覆盖渲染、数据获取、缓存、运行时（Node.js）与部署的 Web 应用运行时。

## 项目坐标

| 维度 | 数据 |
|------|------|
| 仓库 | vercel/next.js |
| Stars | 约 142k |
| 主语言 | JavaScript / TypeScript |
| License | MIT |
| 当前主版本 | 16.x（2025 年 10 月发布；Turbopack 为默认打包器，要求 Node.js 20.9+） |
| 部署平台 | Vercel（首选）、自托管 Node.js / Docker |

## 渲染模型演进

### 1. CSR（Client-Side Rendering）—— 传统 React

```jsx
function App() {
    const [user, setUser] = useState(null);
    useEffect(() => {
        fetch('/api/user').then(r => r.json()).then(setUser);
    }, []);
    return <div>{user?.name}</div>;
}
```

问题：

- SEO 极差（搜索引擎看不到内容）
- 首屏白屏（HTML 是空 shell）
- 服务端无法参与渲染

### 2. SSR（Server-Side Rendering）—— Next.js Pages Router

每个请求都在服务端渲染：

```jsx
export async function getServerSideProps(ctx) {
    const res = await fetch(`https://api.example.com/users/${ctx.params.id}`);
    const user = await res.json();
    return { props: { user } };
}
```

适合：登录后内容、个性化页面。

### 3. SSG（Static Site Generation）—— 预渲染

构建时生成静态 HTML：

```jsx
export async function getStaticPaths() {
    const res = await fetch('https://api.example.com/posts');
    const posts = await res.json();
    return { paths: posts.map(p => ({ params: { id: p.id } })), fallback: false };
}
```

适合：博客、文档、营销页。

### 4. ISR（Incremental Static Regeneration）—— 静态但可增量更新

```jsx
export async function getStaticProps() {
    const res = await fetch('https://api.example.com/posts');
    return {
        props: { posts: await res.json() },
        revalidate: 60  // 60s 后重新生成
    };
}
```

适合：电商商品页、新闻列表——静态性能 + 内容更新。

### 5. RSC（React Server Components）—— App Router 的核心

服务端组件默认——不发送 JS 到浏览器：

```jsx
// app/posts/page.tsx
async function PostsPage() {
    const posts = await db.posts.findMany();  // 直接查数据库
    return <PostList posts={posts} />;
}
```

客户端组件只在你需要交互时：

```jsx
'use client';
function LikeButton({ postId }) {
    const [liked, setLiked] = useState(false);
    return <button onClick={() => setLiked(!liked)}>{liked ? '已点赞' : '点赞'}</button>;
}
```

RSC 的好处：

- **包体积大幅减小**：服务端组件不发到浏览器
- **直接访问数据源**：可以查数据库、调内部 API，不需要 public API
- **减少客户端 JS 执行**：浏览器只水合（hydrate）必要的部分
- **流式渲染**：服务端组件可以分块流式发送到浏览器（`<Suspense>` 边界）

### 6. Cache Components + PPR（Next.js 16 的当前路径）

Next.js 16 把"渲染模型"又推进一步：新增 `use cache` 指令与 Cache Components。规则和以前正好相反——**缓存完全显式**，页面、布局、路由里未标记的代码默认都在请求期执行；你用 `use cache` 把愿意缓存的页面、组件或函数显式标出来，编译器自动生成缓存键。缓存模型从"默认缓存、逐处关闭"改成了"默认动态、逐处开启"。

```tsx
// next.config.ts
const nextConfig = { cacheComponents: true };
export default nextConfig;
```

开启后，Partial Prerendering（PPR）成为 App Router 的默认行为：构建期预渲染出静态 HTML shell 立即下发，未缓存的动态部分（如个性化内容）再按需流式补全——静态的性能和动态的灵活性不再二选一。细粒度控制靠一组 API：`cacheLife` 定缓存寿命、`cacheTag` 打标签，`revalidateTag` 按标签失效（16 起要求带 `cacheLife` profile 作为第二个参数）；Server Actions 里另有 `updateTag`，写入后立刻回读新数据，用户刷新表单就能看到自己的修改。

这一套机制有明确的边界：替代了 15 的 `experimental.ppr` / `experimental.dynamicIO` 开关；只支持 Node.js runtime，Edge 路由要迁移；作为交换，客户端导航改用 React 的 `<Activity>` 保持组件状态，返回上一页时表单内容、展开状态都还在。

## App Router vs Pages Router

Next.js 13.4 起 App Router 稳定，新版 create-next-app 默认使用（`app/` 目录）。Pages Router（`pages/` 目录）仍兼容。

| 维度 | App Router | Pages Router |
|------|-----------|--------------|
| 路由方式 | 文件夹即路由 | 文件即路由 |
| 默认渲染 | Server Component | Client Component |
| 数据获取 | async 组件函数 | getServerSideProps / getStaticProps |
| 布局 | 嵌套 layout.tsx | 单层 _app.tsx |
| Loading/Error | loading.tsx / error.tsx | 手动 |
| Streaming | 原生支持 | 有限 |
| 请求拦截 | proxy.ts（16 起替代 middleware.ts，框架级，与路由器选择无关） | 同左 |
| 学习曲线 | 较高（要理解 Server vs Client） | 较低 |

**新项目应该用 App Router**。Pages Router 进入维护期。

## 一个 App Router 示例

```text
app/
├── layout.tsx          # 根布局
├── page.tsx            # 首页（Server Component）
├── posts/
│   ├── page.tsx        # 列表
│   └── [id]/
│       └── page.tsx    # 详情
├── api/
│   └── webhook/
│       └── route.ts    # API 路由
└── components/
    └── LikeButton.tsx  # Client Component
```

```tsx
// app/posts/[id]/page.tsx
import { LikeButton } from '@/components/LikeButton';
import { db } from '@/lib/db';
import { notFound } from 'next/navigation';

export default async function PostPage({ params }: { params: Promise<{ id: string }> }) {
    const { id } = await params;
    const post = await db.posts.findUnique({ where: { id } });
    if (!post) notFound();
    
    return (
        <article>
            <h1>{post.title}</h1>
            <p>{post.content}</p>
            <LikeButton postId={post.id} />
        </article>
    );
}
```

```tsx
// app/components/LikeButton.tsx
'use client';
import { useState } from 'react';

export function LikeButton({ postId }: { postId: string }) {
    const [liked, setLiked] = useState(false);
    return <button onClick={() => setLiked(!liked)}>{liked ? '已点赞' : '点赞'}</button>;
}
```

```tsx
// app/api/webhook/route.ts
export async function POST(req: Request) {
    const body = await req.json();
    // 处理 webhook
    return Response.json({ ok: true });
}
```

## 一次请求的完整路径

把上面的例子串起来，看一次 `/posts/123` 请求从头到尾经历了什么：

**构建期**。Turbopack 打包整个应用；`/posts/[id]` 里的 `PostPage` 是 Server Component，查数据库取文章正文这一步没有被 `use cache` 标记，构建器不会预生成这条路由，留到请求期执行。

**请求到达**。用户访问 `/posts/123`，Node.js 服务端执行 `PostPage`：`await params` 拿到路由参数，`db.posts.findUnique` 直接查库——这一步发生在服务端，数据库连接串不会进浏览器。React 把组件树渲染成 HTML，遇到 `<LikeButton>` 这种 Client Component 时只发一个占位标记和一小段 JS。

**流式下发**。如果页面上还有取数较慢的部分（比如相关文章推荐），包在 `<Suspense>` 里，HTML shell 先行返回，慢的部分后到先补；用户先看到标题和正文，推荐列表稍后浮现。

**水合**。浏览器加载 JS bundle，只对 `<LikeButton>` 水合——点赞按钮可交互，页面其余部分不背 JS 逻辑。

**用户提交表单**。在 `/posts/new` 写新文章点提交，`<form action={createPost}>` 直达服务端函数，`createPost` 写库后调 `revalidatePath('/posts')`，把列表页的缓存标脏；下一个访问 `/posts` 的用户立刻看到新文章。整条链路没有手写 API 调用，也没有全页刷新。

## 数据获取策略

App Router 推荐几种数据获取模式：

### 1. Server Component 直接 fetch

```tsx
import { cookies } from 'next/headers';

async function UserPage() {
    const cookieStore = await cookies();          // Next.js 15+ 为异步
    const user = await fetch('https://api.example.com/me', {
        headers: { cookie: cookieStore.get('token')?.value ?? '' },
        cache: 'no-store'
    }).then(r => r.json());
    return <div>{user.name}</div>;
}
```

### 2. Server Actions（服务端操作）

```tsx
// app/actions.ts
'use server';
import { revalidatePath } from 'next/cache';

export async function createPost(formData: FormData) {
    const title = formData.get('title') as string;
    await db.posts.create({ data: { title } });
    revalidatePath('/posts');  // 刷新 /posts 的缓存
}
```

```tsx
// app/posts/new/page.tsx
import { createPost } from '@/app/actions';
export default function NewPost() {
    return (
        <form action={createPost}>
            <input name="title" />
            <button type="submit">Create</button>
        </form>
    );
}
```

Server Actions 让"表单提交到服务端函数"成为一等公民——不需要单独写 API 路由。

### 3. Route Handlers（API 端点）

如果要给外部系统（移动 App、第三方）暴露 HTTP API：

```tsx
// app/api/posts/route.ts
export async function GET() {
    const posts = await db.posts.findMany();
    return Response.json(posts);
}
```

## 部署选项

| 平台 | 优势 | 限制 |
|------|------|------|
| **Vercel** | 零配置、全球边缘、自动 HTTPS、ISR/RSC 原生支持 | 商业锁定、价格 |
| **自托管 Node.js** | 完全控制 | 需要自己配负载均衡、CDN |
| **Docker** | 跨云一致 | 同样要配 CDN |
| **Cloudflare Pages + Workers** | 边缘运行时 | 部分 Node.js API 不可用 |
| **AWS Amplify** | AWS 集成 | 配置较复杂 |

> **缓存能力依赖 Node.js runtime**：Cache Components 明确要求 Node.js runtime，官方建议迁移掉声明 `runtime = 'edge'` 的路由；16 起的 `proxy.ts`（原 `middleware.ts`）同样跑在 Node.js 上。往 Cloudflare Workers 这类纯 Edge 环境部署前，先确认目标平台对这些能力的适配情况。

## 与 Remix / Astro / SvelteKit 的取舍

| 维度 | Next.js | Remix | Astro | SvelteKit |
|------|---------|-------|-------|-----------|
| 学习曲线 | 中（要理解 RSC） | 中 | 低 | 低 |
| 渲染模型 | 多模型混用 | SSR-first | 静态/Island | 多模型 |
| 数据获取 | Server Component + Server Actions | loader/action | 多源 | load function |
| 路由 | 文件夹 | 文件夹 | 文件夹 | 文件夹 |
| 性能 | 中（hydration 开销） | 中 | 极高（少 JS） | 极高（少 JS） |
| 生态 | 巨大 | 中 | 中 | 中 |
| Vercel 集成 | 原生 | 需适配 | 适配 | 适配 |

**决策建议**：

- **大团队 + 复杂业务 + React 生态** → Next.js
- **Web 标准优先 + 渐进增强** → Remix
- **内容站 + 极致性能 + 少 JS** → Astro
- **不想用 React + 喜欢简洁** → SvelteKit

补充一个时效信息：Remix 2 的框架能力（loader/action、文件约定路由、Vite 集成）已并入 React Router v7（2024 年 11 月发布）；Remix 团队随后另起 Remix 3，改走 Web 标准原语路线，2026 年 8 月已到 RC。今天在 React 语境里选 Remix，实际落地的是 React Router 框架模式。

## 实战起步建议

1. **新项目**：用 App Router + TypeScript
2. **数据访问**：Server Component 直查（不绕道 API）
3. **交互**：仅在需要时用 Client Component（`'use client'` 边界尽量小）
4. **表单**：优先用 Server Actions（而不是手写 fetch）
5. **缓存**：15 及以前先理解缓存层级（Request Memoization → Data Cache → Full Route Cache → Router Cache）；16 开了 Cache Components 后换成显式模型——`use cache` 标记、`cacheLife` 定寿命、`cacheTag` 打标签，失效走 `revalidateTag` / `updateTag`
6. **部署**：Vercel 一键起步；后期要自托管用 `next start`

## 常见坑

### 1. Client / Server 边界混乱

```tsx
'use client';
async function MyComponent() {  // 报错：Client Component 不能是 async 函数
    const data = await fetch('https://api.example.com/data');
}
```

### 2. 误把 secrets 暴露给客户端

```tsx
// Server Component 里
const apiKey = process.env.SECRET_API_KEY;
fetch(`https://api.example.com?key=${apiKey}`);  // OK：在服务端执行

// ❌ 把 apiKey 传给 Client Component
return <ClientComp apiKey={apiKey} />;  // 会泄露
```

### 3. 别沿用旧的缓存默认值

Next.js 15 起改了默认值：`fetch` 默认不再缓存（此前默认 `force-cache`）。需要缓存时显式声明——要实时数据用 `cache: 'no-store'`，要定期刷新用 `next: { revalidate: 60 }`，或接入 16 的 `use cache` / `revalidateTag` / `updateTag` 做细粒度控制。跨大版本升级先看 release notes。

### 4. Streaming 边界

`<Suspense>` 包裹的部分会流式发送到浏览器，但 Suspense 边界外的部分仍要等所有内容准备好——要合理设计边界。

### 5. 从 15 升 16 的破坏性变更

官方提供升级 codemod（`npx @next/codemod@canary upgrade latest`），但动手前先心里有数：

- Node.js 最低 20.9，Node.js 18 被放弃
- `middleware.ts` 改名 `proxy.ts`，导出函数改为 `proxy`；旧文件名仍可用但已废弃，未来版本移除
- `next lint` 命令移除，`next build` 不再自动跑 lint，直接用 ESLint 或 Biome
- AMP 支持移除
- `params`、`searchParams`、`cookies()`、`headers()` 的同步访问移除，必须 `await`——正文示例均已按新写法
- `revalidateTag` 单参数形式废弃，第二个参数要带 `cacheLife` profile

## 何时用 / 何时不用

**适合**：

- React 全栈应用 + SEO 要求
- 内部业务系统（dashboard、CRM、ERP）
- 营销站 + 博客 + 文档
- 大型团队的标准化框架

**不适合**：

- 单页工具（用 Vite + React SPA）
- 极致静态站（用 Astro 性能更好）
- 不用 React 的项目

## 参考资源

- 官方文档：[https://nextjs.org/docs](https://nextjs.org/docs)
- App Router 教程：[https://nextjs.org/learn](https://nextjs.org/learn)
- Next.js 16 发布公告：[https://nextjs.org/blog/next-16](https://nextjs.org/blog/next-16)
- Cache Components 配置：[https://nextjs.org/docs/app/api-reference/config/next-config-js/cacheComponents](https://nextjs.org/docs/app/api-reference/config/next-config-js/cacheComponents)
- Server Components RFC：[https://github.com/reactjs/rfcs/blob/main/text/0188-server-components.md](https://github.com/reactjs/rfcs/blob/main/text/0188-server-components.md)
- 《Real-World Next.js》（Michele Riva 著）