import { readFileSync } from 'fs';
import { homedir } from 'os';
import { resolve } from 'path';
import http from 'http';
import net from 'net';
import { WebSocket } from 'ws';

const RUNTIME_DIR = resolve(homedir(), '.cache', 'cdp');

function sockPath(targetId) {
  return resolve(RUNTIME_DIR, `cdp-${targetId}.sock`);
}

async function connectSocket(sp) {
  return new Promise((resolve, reject) => {
    const conn = net.connect(sp);
    let buf = '';
    conn.on('data', chunk => { buf += chunk.toString(); });
    conn.on('end', () => {
      try { resolve(JSON.parse(buf)); } catch { resolve(null); }
    });
    conn.on('error', reject);
    setTimeout(() => reject(new Error('timeout')), 8000);
  });
}

async function sendCommand(conn, req) {
  return new Promise((resolve, reject) => {
    let buf = '';
    const cleanup = () => { conn.off('data', onData); conn.off('error', onError); };
    const onData = chunk => {
      buf += chunk.toString();
      const idx = buf.indexOf('\n');
      if (idx !== -1) {
        cleanup();
        try { resolve(JSON.parse(buf.slice(0, idx))); } catch { resolve(null); }
      }
    };
    const onError = e => { cleanup(); reject(e); };
    conn.on('data', onData);
    conn.on('error', onError);
    conn.write(JSON.stringify(req) + '\n');
    setTimeout(() => { cleanup(); reject(new Error('timeout')); }, 8000);
  });
}

async function cdpNav(targetId, url) {
  const sp = sockPath(targetId);
  try {
    const conn = await connectSocket(sp);
    const res = await sendCommand(conn, { id: 1, cmd: 'nav', args: [url] });
    return res;
  } catch(e) {
    // daemon doesn't exist, spawn it
  }
  const { existsSync, unlinkSync, mkdirSync } = await import('fs');
  try { mkdirSync(RUNTIME_DIR, { recursive: true, mode: 0o700 }); } catch {}
  try { unlinkSync(sp); } catch {}
  const { spawn } = await import('child_process');
  const child = spawn(process.execPath, [process.argv[1], '_daemon', targetId], { detached: true, stdio: 'ignore' });
  child.unref();
  await new Promise(r => setTimeout(r, 1500));
  const conn2 = await connectSocket(sp);
  const res2 = await sendCommand(conn2, { id: 1, cmd: 'nav', args: [url] });
  return res2;
}

async function getTargetList() {
  return new Promise((resolve, reject) => {
    http.get('http://127.0.0.1:9222/json/list', res => {
      let data = '';
      res.on('data', c => data += c);
      res.on('end', () => {
        try { resolve(JSON.parse(data)); } catch { resolve([]); }
      });
    }).on('error', () => resolve([]));
  });
}

async function sendWs(ws, req) {
  return new Promise((resolve, reject) => {
    const timeout = setTimeout(() => reject(new Error('timeout')), 15000);
    ws.on('message', msg => {
      clearTimeout(timeout);
      resolve(JSON.parse(msg.toString()));
    });
    ws.send(JSON.stringify(req));
  });
}

async function wsNav(targetId, url) {
  const targets = await getTargetList();
  const target = targets.find(t => t.id === targetId);
  if (!target) return { error: 'target not found' };
  return new Promise((resolve) => {
    const ws = new WebSocket(target.webSocketDebuggerUrl);
    ws.on('open', async () => {
      const res = await sendWs(ws, { id: 1, method: 'Page.navigate', params: { url } });
      await new Promise(r => setTimeout(r, 4000));
      ws.close();
      resolve(res);
    });
    ws.on('error', e => resolve({ error: e.message }));
  });
}

async function wsGetLinks(targetId) {
  const targets = await getTargetList();
  const target = targets.find(t => t.id === targetId);
  if (!target) return { error: 'target not found' };
  return new Promise((resolve) => {
    const ws = new WebSocket(target.webSocketDebuggerUrl);
    ws.on('open', async () => {
      const expr = `var links = []; var seen = {}; var as = document.querySelectorAll('a'); for (var i = 0; i < as.length; i++) { var a = as[i]; if (a.href.match(/\\/p\\/\\d+/) && a.textContent.trim().length > 10 && a.textContent.trim() !== '核心服务') { var url = a.href; if (!seen[url]) { seen[url] = true; var parent = a.closest('[class*=item], [class*=article], .info-flow-item, .article-item'); var timeEl = parent ? parent.querySelector('.time, [class*=time]') : null; var time = timeEl ? timeEl.textContent.trim() : ''; links.push({title: a.textContent.trim().substring(0,100), url: url, time: time}); } } } JSON.stringify(links.slice(0, 25))`;
      const res = await sendWs(ws, { id: 1, method: 'Runtime.evaluate', params: { expression: expr } });
      ws.close();
      resolve(res);
    });
    ws.on('error', e => resolve({ error: e.message }));
  });
}

async function wsGetText(targetId, expr) {
  const targets = await getTargetList();
  const target = targets.find(t => t.id === targetId);
  if (!target) return { error: 'target not found' };
  return new Promise((resolve) => {
    const ws = new WebSocket(target.webSocketDebuggerUrl);
    ws.on('open', async () => {
      const res = await sendWs(ws, { id: 1, method: 'Runtime.evaluate', params: { expression: expr } });
      ws.close();
      resolve(res);
    });
    ws.on('error', e => resolve({ error: e.message }));
  });
}

async function openNewTab(url = 'about:blank') {
  return new Promise((resolve, reject) => {
    const req = http.request({
      hostname: '127.0.0.1', port: 9222, path: '/json/new', method: 'GET'
    }, res => {
      let data = '';
      res.on('data', c => data += c);
      res.on('end', () => {
        try { resolve(JSON.parse(data)); } catch { resolve(null); }
      });
    });
    req.on('error', reject);
    req.end();
  });
}

export { cdpNav, getTargetList, sendWs, wsNav, wsGetLinks, wsGetText, openNewTab };