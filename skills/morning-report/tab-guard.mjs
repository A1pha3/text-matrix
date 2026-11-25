#!/usr/bin/env node
// tab-guard.mjs — 早报 CDP Chrome tab 守卫(2026-11-20 内存耗尽故障后新增)
//
// 背景: 早报采集/核验脚本逐条 PUT /json/new 开 tab,脚本中途失败/超时直接 process.exit,
//       tab 不关;跑几份早报后 Chrome tab 积压导致内存耗尽。本脚本是兜底巡检。
//
// 用法:
//   node skills/morning-report/tab-guard.mjs [选项]
//     --port <n>           CDP 端口,默认 9224(老 cdp-helper 走 9222 时手动传)
//     --max <n>            tab 数上限,超过则清空,默认 20
//     --restart-after <n>  累计"清空 tab"达到该次数后重启浏览器,默认 3
//     --check              只报告 tab 数与将采取的动作,不关闭/不重启/不写状态
//     --reset              清零累计计数后退出
//
// 行为:
//   1. GET /json/list 统计 type=page 的 tab 数
//   2. tab > max → 关闭全部 page tab(保留 1 个 about:blank 保活),计数 +1 落盘
//   3. 计数 >= restart-after → 用 ps 抓到的原启动命令行(含 --remote-debugging-port)
//      优雅退出并重启浏览器,等待 CDP 恢复后计数清零
//
// 退出码: 0=正常(含已清理/已重启); 1=错误; 3=CDP 端口不通(浏览器未开,非故障);
//         4=重启失败,需人工介入并向用户汇报

import http from 'http';
import { readFileSync, writeFileSync, renameSync, mkdirSync } from 'fs';
import { homedir } from 'os';
import { resolve, dirname } from 'path';
import { execSync, spawn } from 'child_process';

const argv = process.argv.slice(2);
const opt = (k, d) => { const i = argv.indexOf(k); return i >= 0 && argv[i + 1] !== undefined ? argv[i + 1] : d; };
const PORT = parseInt(opt('--port', '9224'), 10);
const MAX = parseInt(opt('--max', '20'), 10);
const RESTART_AFTER = parseInt(opt('--restart-after', '3'), 10);
const CHECK = argv.includes('--check');
const RESET = argv.includes('--reset');
const STATE = resolve(homedir(), '.openclaw/workspace/state/tab-guard-state.json');
const log = (...a) => console.error('[tab-guard]', ...a);
const sleep = ms => new Promise(r => setTimeout(r, ms));

// ---------- CDP HTTP ----------
function cdp(method, path, timeoutMs = 5000) {
  return new Promise((res, rej) => {
    const req = http.request({ hostname: '127.0.0.1', port: PORT, path, method, timeout: timeoutMs }, r => {
      let d = '';
      r.on('data', c => { d += c; });
      r.on('end', () => { try { res(JSON.parse(d)); } catch { res(d); } });
    });
    req.on('timeout', () => req.destroy(new Error('timeout')));
    req.on('error', rej);
    req.end();
  });
}
async function listPages() {
  const l = await cdp('GET', '/json/list');
  return (Array.isArray(l) ? l : []).filter(t => t.type === 'page');
}
async function closeTab(id) {
  try { return await cdp('PUT', `/json/close/${id}`); }        // Chrome 111+ 要求 PUT
  catch { try { return await cdp('GET', `/json/close/${id}`); } catch (e) { return 'ERR:' + e.message; } }
}
async function newBlank() {
  try { return await cdp('PUT', '/json/new?about%3Ablank'); }
  catch { return await cdp('GET', '/json/new?about%3Ablank'); }
}

// ---------- 状态 ----------
function loadState() {
  try { const s = JSON.parse(readFileSync(STATE, 'utf8')); return { closeCount: 0, history: [], ...s }; }
  catch { return { closeCount: 0, history: [] }; }
}
function saveState(s) {
  try { mkdirSync(dirname(STATE), { recursive: true }); } catch {}
  const tmp = STATE + '.tmp';
  writeFileSync(tmp, JSON.stringify(s, null, 1));
  renameSync(tmp, STATE);
}

// ---------- Chrome 进程定位与重启 ----------
function findChromeCmd() {
  // 找带 remote-debugging-port 的浏览器主进程(子进程带 --type=,排除)
  let out;
  try { out = execSync('ps -axo pid=,command=', { encoding: 'utf8' }); }
  catch (e) { return null; }
  for (const lineRaw of out.split('\n')) {
    const line = lineRaw.trim();
    if (!line.includes('remote-debugging-port')) continue;
    if (!/\.app\/Contents\/MacOS\//.test(line)) continue;
    if (line.includes('--type=')) continue;
    const m = line.match(/^(\d+)\s+(\/.*)$/);
    if (!m) continue;
    const pid = parseInt(m[1], 10);
    const cmd = m[2];
    const i = cmd.indexOf(' --');             // 二进制路径含空格,首个 " --" 前是二进制
    const bin = (i > 0 ? cmd.slice(0, i) : cmd).trim();
    const args = i > 0 ? cmd.slice(i + 1).trim().split(/\s+/) : [];
    return { pid, bin, args };
  }
  return null;
}
async function waitGone(pid, ms) {
  const deadline = Date.now() + ms;
  while (Date.now() < deadline) {
    try { process.kill(pid, 0); } catch { return true; }
    await sleep(500);
  }
  return false;
}
async function waitCdpUp(ms) {
  const deadline = Date.now() + ms;
  while (Date.now() < deadline) {
    try { await cdp('GET', '/json/version', 2000); return true; } catch {}
    await sleep(1000);
  }
  return false;
}
async function restartChrome(prev) {
  const found = prev || findChromeCmd();
  if (!found) return { ok: false, reason: 'no-cmd' };
  log(`重启浏览器: ${found.bin} ${found.args.join(' ')}`);
  // 1) 优雅退出: AppleScript quit(等同 Cmd+Q)→ SIGTERM → SIGKILL
  if (/Google Chrome/.test(found.bin)) {
    try { execSync(`osascript -e 'tell application "Google Chrome" to quit'`, { timeout: 8000 }); } catch {}
  }
  if (await waitGone(found.pid, 12000)) { log('已优雅退出'); }
  else {
    try { process.kill(found.pid, 'SIGTERM'); } catch {}
    if (await waitGone(found.pid, 10000)) { log('SIGTERM 后退出'); }
    else {
      log('优雅退出超时,升级 SIGKILL');
      try { process.kill(found.pid, 'SIGKILL'); } catch {}
      if (!(await waitGone(found.pid, 8000))) return { ok: false, reason: 'kill-failed' };
    }
  }
  await sleep(2000); // 等调试端口释放、崩溃标记清理
  // 2) 用原命令行重新拉起
  try {
    const child = spawn(found.bin, found.args, { detached: true, stdio: 'ignore' });
    child.unref();
  } catch (e) { return { ok: false, reason: 'spawn:' + e.message }; }
  // 3) 等 CDP 恢复
  if (!(await waitCdpUp(45000))) return { ok: false, reason: 'cdp-not-up' };
  return { ok: true };
}

// ---------- 主流程 ----------
(async () => {
  if (RESET) {
    saveState({ closeCount: 0, history: [] });
    console.log(JSON.stringify({ action: 'reset', closeCount: 0 }));
    log('计数已清零');
    return;
  }

  let pages;
  try { pages = await listPages(); }
  catch (e) {
    console.log(JSON.stringify({ port: PORT, error: 'cdp-unreachable', detail: e.message }));
    log(`CDP 127.0.0.1:${PORT} 连不上(浏览器未开?),非故障`);
    process.exit(3);
  }

  const tabs = pages.length;
  const st = loadState();
  const result = { ts: new Date().toISOString(), port: PORT, tabs, max: MAX, closeCount: st.closeCount, restartAfter: RESTART_AFTER, action: 'none' };

  if (tabs <= MAX) {
    log(`tab 数 ${tabs}/${MAX},正常`);
    console.log(JSON.stringify(result));
    return;
  }

  if (CHECK) {
    result.action = 'would-clear';
    log(`[check] tab 数 ${tabs} > ${MAX}:将关闭全部 page tab(累计已清空 ${st.closeCount} 次,满 ${RESTART_AFTER} 次后重启浏览器)`);
    console.log(JSON.stringify(result));
    return;
  }

  log(`tab 数 ${tabs} > ${MAX},关闭全部 page tab(保留 1 个 about:blank 保活)`);
  for (const p of pages) {
    const r = await closeTab(p.id);
    if (String(r).startsWith('ERR')) log('关闭失败', p.id, r);
  }
  await sleep(1000);
  try { await newBlank(); } catch (e) { log('开保活空白页失败(不影响)', e.message); }
  st.closeCount += 1;
  st.history.push({ ts: result.ts, tabs });
  if (st.history.length > 50) st.history = st.history.slice(-50);
  result.action = 'cleared';
  result.closeCount = st.closeCount;
  log(`已清空,累计清空 ${st.closeCount} 次`);

  if (st.closeCount >= RESTART_AFTER) {
    log(`累计清空 ${st.closeCount} 次 >= ${RESTART_AFTER},重启浏览器`);
    result.action = 'cleared+restarting';
    const r = await restartChrome();
    if (r.ok) {
      st.closeCount = 0;
      result.action = 'cleared+restarted';
      result.closeCount = 0;
      log('浏览器已重启,CDP 恢复,计数清零');
    } else {
      result.action = 'cleared+restart-failed';
      result.restartFailReason = r.reason;
      log(`重启失败(${r.reason}),计数保留,需人工介入`);
    }
  }
  saveState(st);
  console.log(JSON.stringify(result));
  if (result.action.includes('restart-failed')) process.exit(4);
})().catch(e => { console.error('FATAL', e); process.exit(1); });
