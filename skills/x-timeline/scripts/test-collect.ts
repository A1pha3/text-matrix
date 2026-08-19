#!/usr/bin/env bun
/**
 * collect-timeline.ts 核心解析逻辑单测
 * 运行：bun skills/x-timeline/scripts/test-collect.ts
 */
import { parseTwitterDate, parseGraphqlBody, parseDomItems, state } from './collect-timeline.ts';

let failures = 0;
const check = (name: string, cond: boolean, detail = '') => {
  if (cond) console.log(`  ✅ ${name}`);
  else { failures++; console.error(`  ❌ ${name}${detail ? ' — ' + detail : ''}`); }
};

// ---- T1: Twitter 时间解析（EEE MMM dd HH:mm:ss Z yyyy，非 ISO） ----
console.log('T1 时间解析');
check('UTC 时区', new Date(parseTwitterDate('Mon Aug 18 09:30:00 +0000 2026')!).toISOString() === '2026-08-18T09:30:00.000Z');
check('+0800 时区换算', new Date(parseTwitterDate('Mon Aug 18 09:30:00 +0800 2026')!).toISOString() === '2026-08-18T01:30:00.000Z');
check('非法输入返回 null', parseTwitterDate('not-a-date!!') === null);
check('ISO 兜底可解析', parseTwitterDate('2026-08-18T09:30:00Z') === Date.parse('2026-08-18T09:30:00Z'));

// ---- T2: GraphQL 解析（真实嵌套结构 mock） ----
console.log('T2 GraphQL 解析与双时间轴');

const tweetNode = (over: Record<string, unknown>) => ({ __typename: 'Tweet', core: { user_results: { result: { legacy: {} } } }, legacy: { entities: {} }, ...over });
const user = (screen_name: string, name: string) => ({ core: { user_results: { result: { legacy: { screen_name, name } } } } });

const mockPage = JSON.stringify({
  data: {
    home: {
      home_timeline: {
        instructions: [{
          type: 'TimelineAddEntries',
          entries: [
            { // ① 普通推文（含引用推：引用对象不得被当作独立条目）
              content: { itemContent: { tweet_results: { result: tweetNode({
                rest_id: '200',
                ...user('alice', 'Alice'),
                legacy: {
                  created_at: 'Mon Aug 18 06:00:00 +0000 2026',
                  full_text: 'my take on the market',
                  lang: 'en',
                  entities: { urls: [{ expanded_url: 'https://example.com/report' }] },
                },
                quoted_status_result: { result: tweetNode({
                  rest_id: '150',
                  ...user('bob', 'Bob'),
                  legacy: { created_at: 'Sun Aug 17 20:00:00 +0000 2026', full_text: 'quoted original', entities: {} },
                }) },
              }) } } },
            },
            { // ② 转推：外层入场时间新、原推时间旧 —— 双时间轴核心用例
              content: { itemContent: { tweet_results: { result: tweetNode({
                rest_id: '900',
                ...user('carol', 'Carol'),
                legacy: {
                  created_at: 'Mon Aug 18 05:00:00 +0000 2026', // 转推动作时间（入场时间）
                  full_text: 'RT @dave: old insight',
                },
                retweeted_status_result: { result: tweetNode({
                  rest_id: '100',
                  ...user('dave', 'Dave'),
                  legacy: { created_at: 'Sat Aug 15 00:00:00 +0000 2026', full_text: 'old insight', entities: {} },
                }) },
              }) } } },
            },
            { // ③ 墓碑条目
              content: { itemContent: { tweet_results: { result: { __typename: 'TweetTombstone', tombstone: { text: { text: 'unavailable' } } } } } },
            },
            { // ④ 广告条目
              content: { itemContent: { tweet_results: { result: tweetNode({
                rest_id: '300',
                ...user('brand', 'Brand'),
                promotedMetadata: { advertiser: 'brand' },
                legacy: { created_at: 'Mon Aug 18 04:00:00 +0000 2026', full_text: 'buy now', entities: {} },
              }) } } },
            },
          ],
        }],
      },
    },
  },
});

const parsed = parseGraphqlBody(mockPage);
const times = parsed.times;
check('顶层条目数 = 3（引用推不单独计数）', state.posts.size === 3, `实际 ${state.posts.size}`);
check('墓碑计数 = 1', state.tombstones === 1);
check('广告标记识别', state.posts.get('300')?.is_promoted === true);
check('入场时间列表不含引用推', times.length === 4 || times.length === 3, `times=${times.length}`);
check('无 cursor 的 mock 判定为穷尽页', parsed.hasBottomCursor === false);

const rt = state.posts.get('100'); // 转推条目以原推 ID 收录
check('转推按原推 ID 收录', !!rt);
check('转推入场时间 = 外层转推动作时间', rt?.entry_created_at === '2026-08-18T05:00:00.000Z', rt?.entry_created_at);
check('转推内容时间 = 原推发布时间', rt?.created_at === '2026-08-15T00:00:00.000Z', rt?.created_at);
check('转推者标注', rt?.retweeted_by === 'carol' && rt?.is_retweet === true);
check('转推文本取原推全文', rt?.text === 'old insight');

const quote = state.posts.get('200');
check('引用推挂为字段而非独立条目', quote?.quoted_post?.post_id === '150' && !state.posts.has('150'));
check('外部链接提取', quote?.link_cards[0] === 'https://example.com/report');

// ---- T3: 跨页去重 ----
console.log('T3 跨页去重');
parseGraphqlBody(mockPage); // 同一页重复到达（X 跨页可能重复返回）
check('重复条目计数', state.duplicates === 3, `实际 ${state.duplicates}`);
check('条目总数不变', state.posts.size === 3);

// ---- T4: 翻页边界数据可用性 ----
console.log('T4 翻页边界');
const minEntry = Math.min(...times);
check('最早入场时间可判定（窗口闭合依据）', Number.isFinite(minEntry));
check('最早入场时间为转推动作时间而非原推时间', new Date(minEntry).toISOString() === '2026-08-18T04:00:00.000Z', new Date(minEntry).toISOString());

// ---- T5: 底部游标检测（时间线穷尽判定） ----
console.log('T5 底部游标检测');
const cursorPage = JSON.stringify({ data: { instructions: [{ entries: [
  { content: { entryType: 'TimelineTimelineCursor', cursorType: 'Bottom', value: 'cursor-abc' } },
] }] } });
check('含 Bottom cursor → 未穷尽', parseGraphqlBody(cursorPage).hasBottomCursor === true);
check('非法 JSON 不误判穷尽', parseGraphqlBody('{oops').hasBottomCursor === true);

// ---- T6: DOM 兜底解析与残留去重 ----
console.log('T6 DOM 兜底路径');
const domItems = [
  { id: '500', handle: 'eve', name: 'Eve', datetime: '2026-08-18T06:00:00.000Z', text: 'dom post', socialContext: '', tombstone: false, mediaAlts: [], links: ['https://example.com/a'] },
  { id: '501', handle: 'frank', name: 'Frank', datetime: '2026-08-18T05:00:00.000Z', text: '', socialContext: 'Carol 转推了', tombstone: false, mediaAlts: [], links: [] },
  { id: null, handle: null, name: '', datetime: '', text: '', socialContext: '', tombstone: true, mediaAlts: [], links: [] },
];
const before = { posts: state.posts.size, dups: state.duplicates, tombs: state.tombstones };
parseDomItems(domItems);
check('DOM 条目收录（转推标记识别）', state.posts.has('500') && state.posts.get('501')?.is_retweet === true);
check('DOM 墓碑计数', state.tombstones === before.tombs + 1);
parseDomItems(domItems); // 同一批节点跨滚动持久存在，重复提取不得计入 duplicates
check('DOM 残留重复提取不膨胀 duplicates', state.duplicates === before.dups, `实际 ${state.duplicates}，期望 ${before.dups}`);
check('DOM 条目总数不变', state.posts.size === before.posts + 2);

// ---- T7: DOM 双时间轴闭合游标（缺陷B回归：旧帖新转不得误判闭合） ----
console.log('T7 DOM 闭合判定只认普通推时间');
const boundaryItems = [
  { id: '600', handle: 'gina', name: 'Gina', datetime: '2026-08-18T07:00:00.000Z', text: 'fresh normal post', socialContext: '', tombstone: false, mediaAlts: [], links: [] },
  { id: '601', handle: 'hank', name: 'Hank', datetime: '2020-01-01T00:00:00.000Z', text: 'old post freshly reposted', socialContext: 'Ivan 转推了', tombstone: false, mediaAlts: [], links: [] },
];
const domRet = parseDomItems(boundaryItems);
check('返回结构含 added/closableTimes', typeof domRet.added === 'number' && Array.isArray(domRet.closableTimes));
check('本页新增计数含转推（2 条）', domRet.added === 2, `实际 ${domRet.added}`);
check('普通推入场时间进入闭合游标', domRet.closableTimes.includes(Date.parse('2026-08-18T07:00:00.000Z')));
check('转推原推旧时间不进入闭合游标（防旧帖新转误判闭合）', !domRet.closableTimes.includes(Date.parse('2020-01-01T00:00:00.000Z')));
check('转推标记入场时间不可靠', state.posts.get('601')?.entry_time_reliable === false);
check('普通推标记入场时间可靠', state.posts.get('600')?.entry_time_reliable === true);

console.log(failures === 0 ? '\n全部通过 ✅' : `\n${failures} 项失败 ❌`);
process.exit(failures === 0 ? 0 : 1);
