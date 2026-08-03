import { execSync, spawn } from 'node:child_process';
import path from 'node:path';
import process from 'node:process';
import { fileURLToPath } from 'node:url';

import {
  CdpConnection,
  findChromeExecutable as findChromeExecutableBase,
  findExistingChromeDebugPort as findExistingChromeDebugPortBase,
  getFreePort as getFreePortBase,
  resolveSharedChromeProfileDir,
  sleep,
  waitForChromeDebugPort,
  type PlatformCandidates,
} from 'baoyu-chrome-cdp';

export { CdpConnection, sleep, waitForChromeDebugPort };

export const CHROME_CANDIDATES: PlatformCandidates = {
  darwin: [
    '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    '/Applications/Google Chrome Canary.app/Contents/MacOS/Google Chrome Canary',
    '/Applications/Chromium.app/Contents/MacOS/Chromium',
  ],
  win32: [
    'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
    'C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe',
  ],
  default: [
    '/usr/bin/google-chrome',
    '/usr/bin/chromium',
    '/usr/bin/chromium-browser',
  ],
};

export function findChromeExecutable(chromePathOverride?: string): string | undefined {
  if (chromePathOverride?.trim()) return chromePathOverride.trim();
  return findChromeExecutableBase({
    candidates: CHROME_CANDIDATES,
    envNames: ['ZHIHU_BROWSER_CHROME_PATH', 'BAOYU_BROWSER_CHROME_PATH'],
  });
}

export async function findExistingChromeDebugPort(profileDir: string): Promise<number | null> {
  return await findExistingChromeDebugPortBase({ profileDir });
}

export function killChromeByProfile(profileDir: string): void {
  try {
    const result = execSync('ps aux', { encoding: 'utf-8', timeout: 5_000 });
    for (const line of result.split('\n')) {
      if (!line.includes(profileDir) || !line.includes('--remote-debugging-port=')) continue;
      const pid = line.trim().split(/\s+/)[1];
      if (pid) {
        try { process.kill(Number(pid), 'SIGTERM'); } catch {}
      }
    }
  } catch {}
}

export function getDefaultProfileDir(): string {
  return resolveSharedChromeProfileDir({
    envNames: ['BAOYU_CHROME_PROFILE_DIR', 'ZHIHU_CHROME_PROFILE_DIR'],
  });
}

export async function getFreePort(): Promise<number> {
  return await getFreePortBase('ZHIHU_BROWSER_DEBUG_PORT');
}

/**
 * 启动 Chrome（沙箱友好版，独立生命周期）。
 * - 沙箱内必须 --no-sandbox --disable-gpu，否则 Chrome 直接崩
 * - 先清 profile 的 SingletonLock/Socket/Cookie，否则二次启动失败
 * - 用 spawn + detached + unref：Chrome 生命周期独立于脚本进程，脚本退出后 Chrome 继续存活
 */
export async function launchChrome(url: string, profileDir: string, chromePathOverride?: string): Promise<number> {
  const chromePath = findChromeExecutable(chromePathOverride);
  if (!chromePath) throw new Error('Chrome not found. Set ZHIHU_BROWSER_CHROME_PATH env var.');

  // 清理残留锁文件（上次异常退出会留下）
  for (const lock of ['SingletonLock', 'SingletonSocket', 'SingletonCookie']) {
    try { execSync(`rm -f "${profileDir}/${lock}"`); } catch {}
  }

  const port = await getFreePort();
  console.log(`[chrome-utils] Launching Chrome (profile: ${profileDir})`);

  const args = [
    `--user-data-dir=${profileDir}`,
    `--remote-debugging-port=${port}`,
    '--no-sandbox',
    '--disable-gpu',
    '--disable-blink-features=AutomationControlled',
    '--start-maximized',
    url,
  ];

  const child = spawn(chromePath, args, {
    detached: true,
    stdio: 'ignore',
    env: process.env,
  });
  child.unref();

  return port;
}

export function getScriptDir(): string {
  return path.dirname(fileURLToPath(import.meta.url));
}
