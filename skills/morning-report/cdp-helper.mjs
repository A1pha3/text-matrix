import { readFileSync } from 'fs';
import { homedir } from 'os';
import { resolve } from 'path';
import http from 'http';
import net from 'net';
import { WebSocket } from 'ws';
import { spawn } from 'child_process';

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
  
  const child = spawn(process.execPath, [process.argv[1], '_daemon', targetId], { detached: true, stdio: 'ignore' });
  child.unref();
  
  await new Promise(r => setTimeout(r, 1500));
  const conn2 = await connectSocket(sp);
  const res2 = await sendCommand(conn2, { id: 1, cmd: 'nav', args: [url] });
  return res2;
}

async function cdpEval(targetId, expr) {
  const sp = sockPath(targetId);
  const conn = await connectSocket(sp);
  const res = await sendCommand(conn, { id: 1, cmd: 'eval', args: [expr] });
  return res;
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

export { cdpNav, cdpEval, getTargetList, openNewTab, connectSocket, sendCommand };