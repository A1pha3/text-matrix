#!/usr/bin/env bun
/**
 * x-timeline 采集脚本（设计文档 v1.2 §3）
 *
 * 主路径：拦截 HomeLatestTimeline GraphQL 响应（窗口必然闭合）
 * 兜底路径：DOM 滚动解析（接受窗口未闭合）
 *
 * 双时间轴语义（v1.2）：收录与翻页边界一律按「入场时间」
 *   - 普通推：入场时间 = 发布时间
 *   - 转推：入场时间 = 转推动作时间（外层 created_at）
 *
 * 退出码：0 窗口闭合 | 3 窗口未闭合(有数据) | 2 需人工登录 | 4 风控/验证码 | 1 其他错误
 *
 * 用法：
 *   bun collect-timeline.ts --profile ./.chrome-profile --out .workbuddy/tmp/x-digest/raw-$(date +%F).json
 *   选项：--hours 24 | --port <复用已有CDP端口> | --chrome <路径> | --force-fallback | --help
 *
 * 零外部依赖：仅用 fetch + WebSocket（bun 内置；入口守卫依赖 bun 的 import.meta.main 语义）。
 * 只读脚本：全程不执行点赞/关注/发帖等任何写操作。
 */

import { spawn } from 'node:child_process';
import fs from 'node:fs';
import net from 'node:net';
import path from 'node:path';

// ============ 常量区（接口/结构变更时集中修复此处） ============

const CHROME_CANDIDATES = [
  '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
  '/Applications/Google Chrome Canary.app/Contents/MacOS/Google Chrome Canary',
  '/Applications/Chromium.app/Contents/MacOS/Chromium',
];
const HOME_URL = 'https://x.com/home';
const GRAPHQL_OP = 'HomeLatestTimeline'; // 「正在关注」Tab；For you 为 HomeTimeline
const LOGIN_URL_MARKERS = ['/i/flow/login', '/login'];
const CAPTCHA_URL_MARKERS = ['/account/', '/i/flow/challenge'];
const TAB_TEXT_RE = /正在关注|Following/i;
const WATCHDOG_MS = 10 * 60 * 1000; // 总时长看门狗 10 分钟
const MAX_SCROLLS = 120;
const EMPTY_STREAK_LIMIT = 3; // 连续空页上限
const DOM_FALLBACK_TRIGGER_MS = 45_000; // GraphQL 路径多久无响应则降级

// ============ 参数解析 ============

function parseArgs(): Record<string, string> & { flags: Set<string> } {
  const args = process.argv.slice(2);
  const opts: Record<string, string> = {};
  const flags = new Set<string>();
  for (let i = 0; i < args.length; i++) {
    const a = args[i];
    if (a === '--help' || a === '-h') flags.add('help');
    else if (a === '--force-fallback') flags.add('force-fallback');
    else if (a.startsWith('--')) opts[a.slice(2)] = args[++i] ?? '';
  }
  return Object.assign(opts, { flags });
}

const opts = parseArgs();
if (opts.flags.has('help')) {
  console.log('用法: bun collect-timeline.ts --profile <dir> --out <file> [--hours 24] [--port N] [--chrome <path>] [--force-fallback]');
  process.exit(0);
}

const PROFILE_DIR = path.resolve(opts.profile || '.chrome-profile');
const OUT_FILE = path.resolve(opts.out || `.workbuddy/tmp/x-digest/raw-${new Date().toISOString().slice(0, 10)}.json`);
const WINDOW_HOURS = Number(opts.hours || 24);
const WINDOW_END = Date.now();
const WINDOW_START = WINDOW_END - WINDOW_HOURS * 3600 * 1000;

const log = (msg: string) => console.error(`[x-digest] ${msg}`);

// ============ 采集状态 ============

interface Post {
  post_id: string;
  permalink: string;
  author_handle: string;
  author_name: string;
  is_retweet: boolean;
  retweeted_by: string | null;
  is_promoted: boolean;
  entry_created_at: string; // ISO，入场时间（窗口判定用）
  entry_time_reliable: boolean; // 入场时间是否可靠：GraphQL 恒真；DOM 兜底仅普通推为真、转推为假（原推时间≠入场时间）
  created_at: string; // ISO，原推发布时间（展示用）
  text: string;
  lang: string;
  in_reply_to_status_id: string | null;
  quoted_post: { post_id: string; permalink: string; author_handle: string; text: string } | null;
  media_summary: string[];
  link_cards: string[];
  counts: { likes: number; retweets: number };
}

export const state = {
  posts: new Map<string, Post>(),
  tombstones: 0,
  promoted: 0,
  duplicates: 0,
  pages: 0,
  graphqlResponses: 0,
  path: opts.flags.has('force-fallback') ? 'dom' : 'graphql',
  window_closed: false,
  closed_reason: null as string | null, // window_reached | timeline_exhausted
  earliestEntryMs: Infinity,
};

const domSeenIds = new Set<string>(); // DOM 兜底：同一节点跨滚动持久存在，避免重复计数

function flushRaw(extra: Record<string, unknown> = {}) {
  fs.mkdirSync(path.dirname(OUT_FILE), { recursive: true });
  const tmp = OUT_FILE + '.tmp';
  const doc = {
    collected_at: new Date().toISOString(),
    window_start: new Date(WINDOW_START).toISOString(),
    window_end: new Date(WINDOW_END).toISOString(),
    path: state.path,
    window_closed: state.window_closed,
    closed_reason: state.closed_reason,
    stats: {
      pages: state.pages,
      tweets: state.posts.size,
      tombstones: state.tombstones,
      promoted: state.promoted,
      duplicates: state.duplicates,
    },
    posts: [...state.posts.values()],
    ...extra,
  };
  fs.writeFileSync(tmp, JSON.stringify(doc, null, 2));
  fs.renameSync(tmp, OUT_FILE); // 原子替换，崩溃不丢已采部分
}

// ============ Twitter 时间解析（EEE MMM dd HH:mm:ss Z yyyy，非 ISO） ============

const MONTHS: Record<string, number> = {
  Jan: 0, Feb: 1, Mar: 2, Apr: 3, May: 4, Jun: 5,
  Jul: 6, Aug: 7, Sep: 8, Oct: 9, Nov: 10, Dec: 11,
};

export function parseTwitterDate(s: string): number | null {
  // 形如 "Mon Aug 18 09:30:00 +0000 2026"
  const m = s.match(/^\w{3} (\w{3}) (\d{1,2}) (\d{2}):(\d{2}):(\d{2}) ([+-]\d{4}) (\d{4})$/);
  if (!m) {
    const t = Date.parse(s); // 兜底：ISO 或其他格式
    return Number.isNaN(t) ? null : t;
  }
  const [, mon, day, hh, mm, ss, tz, year] = m;
  const utcMs = Date.UTC(Number(year), MONTHS[mon] ?? 0, Number(day), Number(hh), Number(mm), Number(ss));
  const sign = tz[0] === '-' ? -1 : 1;
  const offMin = sign * (Number(tz.slice(1, 3)) * 60 + Number(tz.slice(3, 5)));
  return utcMs - offMin * 60 * 1000;
}

// ============ GraphQL 响应解析 ============

const isTweetNode = (n: any): boolean =>
  Boolean(n && typeof n === 'object' && typeof n.rest_id === 'string' &&
  n.legacy && typeof n.legacy.full_text === 'string' && n.core?.user_results);

function permalinkOf(handle: string, id: string) {
  return `https://x.com/${handle}/status/${id}`;
}

function extractTweet(node: any, entryMs: number | null): Post | null {
  try {
    const outerCreatedAt = parseTwitterDate(node.legacy?.created_at ?? '');
    const rtResult = node.retweeted_status_result?.result ?? node.legacy?.retweeted_status_result?.result;
    const isRetweet = isTweetNode(rtResult);
    const orig = isRetweet ? rtResult : node;
    const user = orig.core?.user_results?.result?.legacy ?? {};
    const rtBy = isRetweet ? node.core?.user_results?.result?.legacy?.screen_name ?? null : null;
    const handle = user.screen_name ?? '';
    const restId = String(orig.rest_id);
    if (!handle || !restId) return null;

    const quoteResult = orig.quoted_status_result?.result ?? orig.legacy?.quoted_status_result?.result;
    let quoted: Post['quoted_post'] = null;
    if (isTweetNode(quoteResult)) {
      const qUser = quoteResult.core?.user_results?.result?.legacy ?? {};
      quoted = {
        post_id: String(quoteResult.rest_id),
        permalink: permalinkOf(qUser.screen_name ?? 'i', String(quoteResult.rest_id)),
        author_handle: qUser.screen_name ?? '',
        text: quoteResult.legacy?.full_text ?? '',
      };
    }

    const promoted = Boolean(node.promotedMetadata ?? orig.promotedMetadata);
    if (promoted) state.promoted++;

    return {
      post_id: restId,
      permalink: permalinkOf(handle, restId),
      author_handle: handle,
      author_name: user.name ?? handle,
      is_retweet: isRetweet === true,
      retweeted_by: rtBy,
      is_promoted: promoted,
      // 入场时间：转推取外层（转推动作时间），普通推取自身发布时间
      entry_created_at: new Date(entryMs ?? outerCreatedAt ?? Date.now()).toISOString(),
      entry_time_reliable: true, // GraphQL 路径有外层 created_at 作入场时间，双时间轴可靠
      created_at: new Date(parseTwitterDate(orig.legacy?.created_at ?? '') ?? outerCreatedAt ?? Date.now()).toISOString(),
      text: orig.legacy?.full_text ?? '',
      lang: orig.legacy?.lang ?? '',
      in_reply_to_status_id: orig.legacy?.in_reply_to_status_id_str ?? null,
      quoted_post: quoted,
      media_summary: (orig.legacy?.entities?.media ?? [])
        .map((md: any) => md?.ext_alt_text).filter((t: any) => typeof t === 'string' && t.length > 0),
      link_cards: (orig.legacy?.entities?.urls ?? [])
        .map((u: any) => u?.expanded_url).filter((u: any) => typeof u === 'string'),
      counts: { likes: orig.legacy?.favorite_count ?? 0, retweets: orig.legacy?.retweet_count ?? 0 },
    };
  } catch {
    return null;
  }
}

/**
 * 深度优先遍历响应 JSON，找到顶层推文节点即提取并停止下钻
 *（避免把引用推/转推内嵌对象误当作独立时间线条目）。
 * 返回本页顶层条目的入场时间列表与底部游标存在性（无底部游标 = 时间线穷尽）。
 */
export function parseGraphqlBody(body: string): { times: number[]; hasBottomCursor: boolean } {
  let json: any;
  try { json = JSON.parse(body); } catch { return { times: [], hasBottomCursor: true }; }
  const times: number[] = [];
  let hasBottomCursor = false;

  const walk = (n: any) => {
    if (!n || typeof n !== 'object') return;
    if (n.cursorType === 'Bottom') { hasBottomCursor = true; return; }
    if (n.__typename === 'TweetTombstone') { state.tombstones++; return; }
    if (isTweetNode(n)) {
      const entryMs = parseTwitterDate(n.legacy?.created_at ?? ''); // 外层 = 入场时间
      const post = extractTweet(n, entryMs);
      if (post) {
        if (state.posts.has(post.post_id)) state.duplicates++;
        else {
          state.posts.set(post.post_id, post);
          if (entryMs) {
            times.push(entryMs);
            state.earliestEntryMs = Math.min(state.earliestEntryMs, entryMs);
          }
        }
      }
      return; // 不下钻：内嵌的引用/转推对象随本条目一并提取
    }
    for (const k of Object.keys(n)) walk(n[k]);
  };

  walk(json);
  return { times, hasBottomCursor };
}

// ============ 最小 CDP 客户端（WebSocket，零依赖） ============

class Cdp {
  private ws!: WebSocket;
  private seq = 0;
  private pending = new Map<number, { resolve: (v: any) => void; reject: (e: Error) => void }>();
  private handlers = new Map<string, ((p: any) => void)[]>();

  constructor(private wsUrl: string) {}

  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      this.ws = new WebSocket(this.wsUrl);
      this.ws.onopen = () => resolve();
      this.ws.onerror = () => reject(new Error('CDP WebSocket 连接失败'));
      this.ws.onmessage = (ev) => {
        let msg: any;
        try { msg = JSON.parse(String(ev.data)); } catch { return; }
        if (msg.id && this.pending.has(msg.id)) {
          const p = this.pending.get(msg.id)!;
          this.pending.delete(msg.id);
          if (msg.error) p.reject(new Error(msg.error.message ?? 'CDP error'));
          else p.resolve(msg.result);
        } else if (msg.method) {
          for (const h of this.handlers.get(msg.method) ?? []) h(msg.params);
        }
      };
    });
  }

  send(method: string, params: any = {}): Promise<any> {
    const id = ++this.seq;
    return new Promise((resolve, reject) => {
      this.pending.set(id, { resolve, reject });
      this.ws.send(JSON.stringify({ id, method, params }));
    });
  }

  on(method: string, h: (p: any) => void) {
    if (!this.handlers.has(method)) this.handlers.set(method, []);
    this.handlers.get(method)!.push(h);
  }

  evaluate<T = any>(expression: string): Promise<T> {
    return this.send('Runtime.evaluate', { expression, returnByValue: true })
      .then((r) => r?.result?.value as T);
  }
}

// ============ Chrome 启动 / 复用 ============

function findChrome(override?: string): string | null {
  if (override && fs.existsSync(override)) return override;
  if (process.env.X_DIGEST_CHROME_PATH && fs.existsSync(process.env.X_DIGEST_CHROME_PATH)) {
    return process.env.X_DIGEST_CHROME_PATH;
  }
  for (const c of CHROME_CANDIDATES) if (fs.existsSync(c)) return c;
  return null;
}

function getFreePort(): Promise<number> {
  return new Promise((resolve, reject) => {
    const srv = net.createServer();
    srv.listen(0, '127.0.0.1', () => {
      const port = (srv.address() as net.AddressInfo).port;
      srv.close(() => resolve(port));
    });
    srv.on('error', reject);
  });
}

/** 复用已带 CDP 端口运行的实例（profile 目录的 DevToolsActivePort 文件） */
async function findExistingPort(profileDir: string): Promise<number | null> {
  try {
    const content = fs.readFileSync(path.join(profileDir, 'DevToolsActivePort'), 'utf8');
    const port = Number(content.split('\n')[0]);
    if (!port) return null;
    const res = await fetch(`http://127.0.0.1:${port}/json/version`, { signal: AbortSignal.timeout(2000) });
    return res.ok ? port : null;
  } catch {
    return null;
  }
}

async function launchChrome(profileDir: string, chromePath: string): Promise<number> {
  // 清理残留锁文件（上次异常退出会留下）
  for (const lock of ['SingletonLock', 'SingletonSocket', 'SingletonCookie']) {
    try { fs.rmSync(path.join(profileDir, lock), { force: true }); } catch { /* ignore */ }
  }
  const port = await getFreePort();
  const child = spawn(chromePath, [
    `--user-data-dir=${profileDir}`,
    `--remote-debugging-port=${port}`, // Chrome 默认仅绑定 127.0.0.1
    '--no-sandbox',
    '--disable-gpu',
    '--disable-blink-features=AutomationControlled',
    '--start-maximized',
    'about:blank', // 启动标签留空；采集标签由 newTab 建后先挂监听再导航，避免首屏 GraphQL 逃逸拦截
  ], { detached: true, stdio: 'ignore' });
  child.unref();
  // 等待 CDP 就绪
  for (let i = 0; i < 30; i++) {
    try {
      const res = await fetch(`http://127.0.0.1:${port}/json/version`, { signal: AbortSignal.timeout(1000) });
      if (res.ok) return port;
    } catch { /* retry */ }
    await new Promise((r) => setTimeout(r, 1000));
  }
  throw new Error('Chrome 启动后 CDP 端口未就绪（可能被同 profile 的既有实例抢占，请关闭后重试）');
}

async function newTab(port: number, url: string): Promise<string> {
  const target = `http://127.0.0.1:${port}/json/new?${encodeURIComponent(url)}`;
  // Chrome 冷启动时 DevTools HTTP 服务就绪晚于 /json/version 探测，需重试容忍竞态
  for (let i = 0; i < 5; i++) {
    try {
      let res = await fetch(target, { method: 'PUT', signal: AbortSignal.timeout(5000) }).catch(() => null);
      if (!res || !res.ok) res = await fetch(target, { signal: AbortSignal.timeout(5000) });
      const tab = (await res.json()) as { webSocketDebuggerUrl?: string };
      if (tab.webSocketDebuggerUrl) return tab.webSocketDebuggerUrl;
    } catch { /* 重试 */ }
    await new Promise((r) => setTimeout(r, 2000));
  }
  throw new Error('无法创建新标签页（Chrome DevTools HTTP 服务持续无响应）');
}

// ============ 登录态 / 风控检查 ============

async function checkPageStatus(cdp: Cdp): Promise<'ok' | 'login' | 'captcha' | 'loading'> {
  const href = await cdp.evaluate<string>('location.href').catch(() => '');
  if (!href || href === 'about:blank' || !href.startsWith('https://x.com')) return 'loading';
  if (LOGIN_URL_MARKERS.some((m) => href.includes(m))) return 'login';
  if (CAPTCHA_URL_MARKERS.some((m) => href.includes(m))) return 'captcha';
  const hasLoginForm = await cdp.evaluate<boolean>(
    `Boolean(document.querySelector('input[autocomplete="username"]'))`,
  ).catch(() => false);
  if (hasLoginForm) return 'login';
  // 未登录时 x.com/home 可能不跳转、只展示登录/注册墙（无 username 输入框），需额外识别
  const loggedOut = await cdp.evaluate<boolean>(`(() => {
    const hasTimeline = Boolean(document.querySelector('article[data-testid="tweet"]'));
    const hasLoginEntry = Boolean(document.querySelector('a[href="/login"], a[href="/i/flow/signup"], [data-testid="loginButton"]'));
    return hasLoginEntry && !hasTimeline;
  })()`).catch(() => false);
  return loggedOut ? 'login' : 'ok';
}

async function clickFollowingTab(cdp: Cdp): Promise<boolean> {
  return cdp.evaluate<boolean>(`(() => {
    const re = ${TAB_TEXT_RE};
    const els = [...document.querySelectorAll('nav[role="navigation"] a[role="link"], [role="tab"], a[href="/home"], header a, [data-testid="TopNavBar"] a')];
    // 只匹配自身文本短小的元素，避免误中父容器（其 textContent 会同时含两个 Tab 名）
    const hit = els.find((el) => {
      const t = (el.textContent || '').trim();
      return t.length <= 20 && (re.test(el.getAttribute('aria-label') || '') || re.test(t));
    });
    if (hit) { hit.click(); return true; }
    return false;
  })()`).catch(() => false);
}

function verifyFollowingTab(cdp: Cdp): Promise<boolean> {
  return cdp.evaluate<boolean>(`(() => {
    const re = ${TAB_TEXT_RE};
    return [...document.querySelectorAll('[aria-selected="true"]')]
      .some((el) => (el.textContent || '').trim().length <= 20 && re.test(el.textContent || el.getAttribute('aria-label') || ''));
  })()`).catch(() => false);
}

/** 采集页面 Tab 导航结构快照，用于中止时排查选择器失配 */
function dumpTabDebug(cdp: Cdp): Promise<any> {
  return cdp.evaluate(`(() => {
    const pick = (el) => ({ tag: el.tagName, role: el.getAttribute('role'), label: el.getAttribute('aria-label'), selected: el.getAttribute('aria-selected'), text: (el.textContent || '').trim().slice(0, 40) });
    return {
      href: location.href,
      tabs: [...document.querySelectorAll('[role="tab"]')].map(pick),
      homeLinks: [...document.querySelectorAll('a[href="/home"]')].map(pick),
      navLinks: [...document.querySelectorAll('nav a[role="link"]')].map(pick).slice(0, 12),
    };
  })()`).catch((e) => ({ error: String(e) }));
}

/** 确认当前处于「正在关注」：失败则重试点击一次；仍失败则中止（宁可失败，不可误采推荐流） */
async function ensureFollowingTab(cdp: Cdp): Promise<void> {
  if (await verifyFollowingTab(cdp)) return;
  await clickFollowingTab(cdp);
  await sleep(2000);
  if (await verifyFollowingTab(cdp)) return;
  const debug = await dumpTabDebug(cdp);
  log('无法确认当前处于「正在关注」Tab，为避免误采「For you」推荐流，中止采集（DOM 快照已写入 raw JSON）');
  flushRaw({ abort_reason: 'following_tab_unverified', tab_debug: debug });
  process.exit(1);
}

// ============ DOM 兜底路径解析 ============

/**
 * DOM 兜底解析。返回 {added, closableTimes}：
 * - added：本页新增条目数（含转推），用于空页判定；
 * - closableTimes：仅「普通推」的入场时间（DOM 上 time[datetime] 对普通推 = 入场时间、单调递减，
 *   可作可靠翻页游标）。转推的 datetime 是原推时间（≠入场时间），绝不参与窗口闭合判定，
 *   否则「旧帖新转」会误触发闭合、漏采其后全部新帖（设计文档 §3.3 双时间轴硬性规则）。
 */
export function parseDomItems(items: any[]): { added: number; closableTimes: number[] } {
  const closableTimes: number[] = [];
  let added = 0;
  for (const it of items ?? []) {
    try {
      if (it.tombstone) { state.tombstones++; continue; }
      const t = Date.parse(it.datetime ?? '');
      if (Number.isNaN(t) || !it.id || !it.handle) continue;
      if (domSeenIds.has(it.id)) continue; // DOM 残留的重复提取，不计入跨页重复
      domSeenIds.add(it.id);
      if (state.posts.has(it.id)) { state.duplicates++; continue; }
      const socialText: string = it.socialContext ?? '';
      const isRetweet = /转推了|reposted/i.test(socialText);
      state.posts.set(it.id, {
        post_id: it.id,
        permalink: `https://x.com/${it.handle}/status/${it.id}`,
        author_handle: it.handle,
        author_name: it.name || it.handle,
        is_retweet: isRetweet,
        retweeted_by: null, // DOM 兜底无法可靠区分转推者，留空
        is_promoted: /推广|Ad$/i.test(socialText),
        // 兜底路径限制：time[datetime] 是原推时间；转推入场时间不可得，标记 entry_time_reliable=false
        entry_created_at: new Date(t).toISOString(),
        entry_time_reliable: !isRetweet,
        created_at: new Date(t).toISOString(),
        text: it.text ?? '',
        lang: '',
        in_reply_to_status_id: null,
        quoted_post: null,
        media_summary: (it.mediaAlts ?? []).filter(Boolean),
        link_cards: (it.links ?? []).filter(Boolean),
        counts: { likes: 0, retweets: 0 },
      });
      added++;
      if (!isRetweet) {
        // 仅普通推的入场时间可靠，用于闭合判定与「最早入场时间」统计
        closableTimes.push(t);
        state.earliestEntryMs = Math.min(state.earliestEntryMs, t);
      }
    } catch { /* 跳过损坏条目 */ }
  }
  return { added, closableTimes };
}

const DOM_EXTRACT_JS = `(() => {
  const out = [];
  for (const a of document.querySelectorAll('article[data-testid="tweet"]')) {
    const timeEl = a.querySelector('time[datetime]');
    const linkEl = [...a.querySelectorAll('a[href*="/status/"]')]
      .find((l) => /\\/status\\/\\d+$/.test(l.getAttribute('href') || ''));
    const id = linkEl ? (linkEl.getAttribute('href').match(/status\\/(\\d+)/) || [])[1] : null;
    const handle = linkEl ? (linkEl.getAttribute('href').match(/^\\/([^/]+)\\//) || [])[1] : null;
    const textEl = a.querySelector('[data-testid="tweetText"]');
    const socialEl = a.querySelector('[data-testid="socialContext"]');
    const unavailable = /unavailable|已不可用|已被删除/i.test(a.textContent || '');
    out.push({
      id, handle,
      name: a.querySelector('[data-testid="User-Name"]')?.textContent?.split('@')[0]?.trim() || '',
      datetime: timeEl?.getAttribute('datetime') || '',
      text: textEl?.textContent || '',
      socialContext: socialEl?.textContent || '',
      tombstone: unavailable || (!id && !textEl),
      mediaAlts: [...a.querySelectorAll('img[alt]')].map((i) => i.alt).slice(0, 4),
      links: [...a.querySelectorAll('a[href^="http"]:not([href*="x.com"]):not([href*="twitter.com"])')]
        .map((l) => l.href).slice(0, 4),
    });
  }
  return out;
})()`;

// ============ 主流程 ============

const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms));
const humanDelay = () => sleep(2000 + Math.random() * 3000); // 2–5 秒拟人化间隔

async function main() {
  const startedAt = Date.now();

  // 1. 取得 CDP 端口（复用 > 指定 > 新启动）
  let port = opts.port ? Number(opts.port) : await findExistingPort(PROFILE_DIR);
  if (!port) {
    const chrome = findChrome(opts.chrome);
    if (!chrome) throw new Error('未找到 Chrome，请用 --chrome 指定路径或设置 X_DIGEST_CHROME_PATH');
    port = await launchChrome(PROFILE_DIR, chrome);
  }
  log(`CDP 端口：${port}`);

  // 2. 新建空白标签并连接 CDP（先不导航，避免首屏 GraphQL 早于监听发出）
  const wsUrl = await newTab(port, 'about:blank');
  const cdp = new Cdp(wsUrl);
  await cdp.connect();
  await cdp.send('Page.enable');
  await cdp.send('Network.enable', { maxTotalBufferSize: 100 * 1024 * 1024 });

  // 3. GraphQL 响应拦截（必须先挂监听、再导航到 home，否则漏首屏 HomeLatestTimeline 响应）
  const pendingBodies: Promise<void>[] = [];
  let lastResponseAt = Date.now();
  cdp.on('Network.responseReceived', (p) => {
    const url: string = p?.response?.url ?? '';
    if (!url.includes('/i/api/graphql/') || !url.includes(GRAPHQL_OP)) return;
    if (p.response.status === 401 || p.response.status === 403) {
      log('接口返回 401/403：登录态失效或风控，停止采集');
      state.window_closed = false;
      flushRaw({ abort_reason: 'auth_lost_or_rate_limited' });
      process.exit(p.response.status === 403 ? 4 : 2);
    }
    pendingBodies.push(
      cdp.send('Network.getResponseBody', { requestId: p.requestId })
        .then((r) => {
          const body = r.base64Encoded ? Buffer.from(r.body, 'base64').toString() : r.body;
          const { times, hasBottomCursor } = parseGraphqlBody(body);
          state.graphqlResponses++;
          state.pages++;
          lastResponseAt = Date.now();
          if (times.length > 0 && Math.min(...times) <= WINDOW_START) {
            state.window_closed = true;
            state.closed_reason = 'window_reached';
          } else if (times.length > 0 && !hasBottomCursor) {
            state.window_closed = true; // 时间线已穷尽（无底部游标），等价窗口闭合
            state.closed_reason = 'timeline_exhausted';
          }
          flushRaw();
        })
        .catch(() => { /* 响应体不可读，忽略 */ }),
    );
  });

  // 监听就绪后再导航到 home，确保首屏 HomeLatestTimeline 响应不被漏拦（GraphQL 竞态修复）
  await cdp.send('Page.navigate', { url: HOME_URL });

  // 4. 登录态检查（轮询至多 30 秒，避免冷启动加载慢导致误判）
  let status: 'ok' | 'login' | 'captcha' | 'loading' = 'loading';
  for (let i = 0; i < 15; i++) {
    await sleep(2000);
    status = await checkPageStatus(cdp);
    if (status !== 'loading') break;
  }
  if (status === 'loading') {
    log('页面 30 秒内未完成加载，请检查网络后重试');
    process.exit(1);
  }
  if (status === 'login') {
    log('未登录：Chrome 窗口已保持打开，请手动登录 X 后重新运行（skill 绝不自动输入凭据）');
    process.exit(2);
  }
  if (status === 'captcha') {
    log('检测到验证码/异常验证页：请在浏览器窗口人工处理后重新运行');
    process.exit(4);
  }

  // 5. 切「正在关注」Tab
  const useFallback = opts.flags.has('force-fallback');
  const clicked = await clickFollowingTab(cdp);
  log(clicked ? '已点击切换「正在关注」Tab' : '未找到「正在关注」Tab 元素（可能已处于该 Tab）');
  await sleep(3000);
  if (useFallback) await ensureFollowingTab(cdp); // 兜底模式必须确认在「正在关注」，避免误采推荐流

  // 6. 翻页采集循环
  let scrolls = 0;
  let emptyStreak = 0;
  let fallbackEngaged = useFallback;

  while (Date.now() - startedAt < WATCHDOG_MS && scrolls < MAX_SCROLLS) {
    if (state.window_closed) break;
    await humanDelay();
    await pendingBodies.splice(0).reduce((c, p) => c.then(() => p), Promise.resolve());

    // GraphQL 路径长时间无响应 → 降级 DOM 兜底
    if (!fallbackEngaged && state.graphqlResponses === 0 && Date.now() - startedAt > DOM_FALLBACK_TRIGGER_MS) {
      log('GraphQL 拦截持续无响应，降级 DOM 滚动兜底路径');
      await ensureFollowingTab(cdp); // 降级前必须确认 Tab，避免静默采集「For you」
      fallbackEngaged = true;
      state.path = 'dom';
    }

    if (fallbackEngaged) {
      const items = await cdp.evaluate<any[]>(DOM_EXTRACT_JS).catch(() => []);
      const { added, closableTimes } = parseDomItems(items);
      state.pages++;
      flushRaw();
      if (added > 0) {
        emptyStreak = 0;
        // 仅用普通推的可靠入场时间判定闭合；转推原推时间不参与，避免「旧帖新转」误判闭合
        if (closableTimes.length > 0 && Math.min(...closableTimes) <= WINDOW_START) {
          state.window_closed = true;
          state.closed_reason = 'window_reached';
          break;
        }
      } else if (++emptyStreak >= EMPTY_STREAK_LIMIT) {
        log('连续空页，停止采集（窗口未闭合）');
        break;
      }
    } else if (state.graphqlResponses > 0 && lastResponseAt < Date.now() - 30_000) {
      // 拦截路径曾有响应但已 30s 无新数据且窗口未闭合，视为疑似限流
      if (++emptyStreak >= EMPTY_STREAK_LIMIT) {
        log('疑似限流：连续无新数据，停止采集（窗口未闭合）');
        break;
      }
    } else {
      emptyStreak = 0;
    }

    // 滚动一次驱动下一页加载（只读操作）
    await cdp.evaluate('window.scrollTo(0, document.body.scrollHeight)').catch(() => {});
    scrolls++;
  }

  // 7. 收尾：截图存证 + 汇总
  let screenshot: string | null = null;
  try {
    const shotDir = path.dirname(OUT_FILE);
    const shotPath = path.join(shotDir, `evidence-${new Date().toISOString().slice(0, 10)}.png`);
    const r = await cdp.send('Page.captureScreenshot', { format: 'png' });
    fs.writeFileSync(shotPath, Buffer.from(r.data, 'base64'));
    screenshot = shotPath;
  } catch { /* 截图失败不阻塞 */ }

  flushRaw({ screenshot });

  const summary = {
    path: state.path,
    window_closed: state.window_closed,
    closed_reason: state.closed_reason,
    tweets: state.posts.size,
    tombstones: state.tombstones,
    promoted: state.promoted,
    duplicates: state.duplicates,
    earliest_entry: state.earliestEntryMs === Infinity ? null : new Date(state.earliestEntryMs).toISOString(),
    elapsed_seconds: Math.round((Date.now() - startedAt) / 1000),
    out: OUT_FILE,
  };
  console.log(JSON.stringify(summary, null, 2));
  process.exit(state.window_closed ? 0 : 3);
}

if (import.meta.main) {
  main().catch((err) => {
    log(`错误：${err?.message ?? err}`);
    try { flushRaw({ abort_reason: String(err?.message ?? err) }); } catch { /* ignore */ }
    process.exit(1);
  });
}
