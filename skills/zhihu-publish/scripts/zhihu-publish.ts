import fs from 'node:fs';
import path from 'node:path';
import { marked } from 'marked';
import {
  CdpConnection,
  findChromeExecutable,
  findExistingChromeDebugPort,
  getDefaultProfileDir,
  launchChrome,
  sleep,
  waitForChromeDebugPort,
} from './chrome-utils.js';

const ZHIHU_WRITE_URL = 'https://zhuanlan.zhihu.com/write';
const TITLE_MAX = 100;

interface PublishOptions {
  markdownPath: string;
  title?: string;
  debugPort?: number;
  profileDir?: string;
  chromePath?: string;
  dryRun?: boolean;
  keepAlive?: boolean;
  screenshotPath?: string;
  json?: boolean;
}

// ---------- markdown -> 干净 HTML 片段（marked + 兜底） ----------
function mdToHtml(markdown: string): string {
  // 预处理：mermaid 代码块打标，避免被 marked 转义后丢失（知乎不支持 mermaid，保留为代码块并标注）
  const mermaidBlocks: string[] = [];
  const prepped = markdown.replace(/```mermaid\s*\n([\s\S]*?)```/g, (_m, code: string) => {
    const idx = mermaidBlocks.length;
    mermaidBlocks.push(code.trim());
    return `> 📊 **Mermaid 图 ${idx + 1}**（知乎暂不支持渲染，源码见下方代码块）\n\n\`\`\`\n${code.trim()}\n\`\`\``;
  });

  // marked GFM 渲染（表格、嵌套列表、引用、代码块均支持）
  const html = marked.parse(prepped, {
    gfm: true,
    breaks: false,
  }) as string;

  // 兜底清理：marked 可能输出 <hr> 等，保留；去掉外层 <p> 包裹的冗余
  return html
    .replace(/<h1>/g, '<h2>').replace(/<\/h1>/g, '</h2>') // 正文 h1 降级为 h2，避免与文章标题重复
    // <details>/<summary> 折叠块 → 稳定的答案块（知乎编辑器不支持折叠标签）
    .replace(/<details>[\s\S]*?<summary>([\s\S]*?)<\/summary>([\s\S]*?)<\/details>/g,
      (_m, summary: string, inner: string) => `<blockquote><p><strong>${summary.replace(/<[^>]*>/g, '').trim()}</strong></p>${inner.replace(/<\/?p>/g, '').trim()}</blockquote>`)
    .trim();
}

// ---------- 主流程 ----------
async function publishToZhihu(options: PublishOptions): Promise<void> {
  const {
    markdownPath,
    debugPort: cliPort,
    profileDir = getDefaultProfileDir(),
    chromePath,
    dryRun = false,
    keepAlive = true,
    screenshotPath,
    json = false,
  } = options;

  if (!fs.existsSync(markdownPath)) throw new Error(`File not found: ${markdownPath}`);

  // 解析 frontmatter 与正文
  const raw = fs.readFileSync(markdownPath, 'utf-8');
  let fmTitle = '';
  let description = '';
  let body = raw;
  const fmMatch = raw.match(/^---\r?\n([\s\S]*?)\r?\n---\r?\n/);
  if (fmMatch) {
    const fm = fmMatch[1]!;
    fmTitle = fm.match(/^title:\s*["']?(.+?)["']?\s*$/m)?.[1] ?? '';
    description = fm.match(/^description:\s*["']?(.+?)["']?\s*$/m)?.[1] ?? '';
    body = raw.slice(fmMatch[0].length);
  }

  const h1Match = body.match(/^#\s+(.+)$/m);
  if (!fmTitle && h1Match) fmTitle = h1Match[1]!.trim();

  const title = (options.title || fmTitle || path.basename(markdownPath, '.md')).trim();
  const truncatedTitle = title.length > TITLE_MAX ? title.slice(0, TITLE_MAX) : title;
  if (title.length > TITLE_MAX && !json) {
    console.warn(`[zhihu] Title exceeds ${TITLE_MAX} chars (${title.length}), truncated to ${TITLE_MAX}. Use --title to override.`);
  }

  const htmlContent = mdToHtml(body);

  // 统计期望值，供粘贴后校验
  const expect = {
    textLen: htmlContent.replace(/<[^>]*>/g, '').length,
    h2: (htmlContent.match(/<h2>/g) || []).length,
    h3: (htmlContent.match(/<h3>/g) || []).length,
    tables: (htmlContent.match(/<table>/g) || []).length,
    pres: (htmlContent.match(/<pre>/g) || []).length,
  };

  const outHtml = process.env.ZHIHU_OUT_HTML || '/tmp/zhihu-article-content.html';
  fs.writeFileSync(outHtml, htmlContent, 'utf-8');

  if (!json) {
    console.log(`[zhihu] HTML saved: ${outHtml} (${htmlContent.length} chars)`);
    console.log(`[zhihu] Title (${truncatedTitle.length}/${TITLE_MAX}): ${truncatedTitle}`);
    if (description) console.log(`[zhihu] Description: ${description.slice(0, 80)}...`);
    console.log(`[zhihu] Expected: ${expect.textLen} chars | h2=${expect.h2} h3=${expect.h3} tables=${expect.tables} codeBlocks=${expect.pres}`);
  }

  if (dryRun) {
    if (json) {
      console.log(JSON.stringify({ ok: true, dryRun: true, title: truncatedTitle, expect }));
    } else {
      console.log('[zhihu] DRY RUN - not touching browser');
    }
    return;
  }

  // ---------- Chrome 生命周期自管 ----------
  let port: number;
  let launchedByUs = false;
  const existingPort = cliPort || await findExistingChromeDebugPort(profileDir);

  if (existingPort) {
    try {
      const ver = await fetch(`http://127.0.0.1:${existingPort}/json/version`).then((r) => r.json());
      if (ver.webSocketDebuggerUrl) {
        port = existingPort;
        if (!json) console.log(`[zhihu] Reusing Chrome on port ${port}`);
      } else throw new Error('no ws');
    } catch {
      if (cliPort) throw new Error(`Chrome on port ${cliPort} is not reachable. Start it with --no-sandbox or let the script launch one.`);
      port = await launchChrome(ZHIHU_WRITE_URL, profileDir, chromePath);
      launchedByUs = true;
    }
  } else {
    port = await launchChrome(ZHIHU_WRITE_URL, profileDir, chromePath);
    launchedByUs = true;
  }

  if (launchedByUs && !json) console.log(`[zhihu] Launched Chrome on port ${port}`);

  // 等待调试端口就绪（spawn 是异步的）
  const wsUrl = await waitForChromeDebugPort(port, 30_000);
  const cdp = await CdpConnection.connect(wsUrl, 30_000, { defaultTimeoutMs: 60_000 });

  const result: Record<string, unknown> = { ok: false };
  let screenshotSaved = false;

  try {
    const targets = await cdp.send<{ targetInfos: Array<{ targetId: string; url: string; type: string }> }>('Target.getTargets');
    let page = targets.targetInfos.find((t) => t.type === 'page' && t.url.includes('zhihu.com'));
    if (!page) {
      const { targetId } = await cdp.send<{ targetId: string }>('Target.createTarget', { url: ZHIHU_WRITE_URL });
      page = { targetId, url: ZHIHU_WRITE_URL, type: 'page' };
    }
    const { sessionId } = await cdp.send<{ sessionId: string }>('Target.attachToTarget', { targetId: page.targetId, flatten: true });
    await cdp.send('Target.activateTarget', { targetId: page.targetId });
    await cdp.send('Page.enable', {}, { sessionId });
    await cdp.send('Runtime.enable', {}, { sessionId });

    await cdp.send('Page.navigate', { url: ZHIHU_WRITE_URL }, { sessionId });

    // 等待编辑器（带登录态检测）
    const waitForEditor = async (timeoutMs = 30_000): Promise<'ok' | 'login' | 'timeout'> => {
      const start = Date.now();
      while (Date.now() - start < timeoutMs) {
        const r = await cdp.send<{ result: { value: string } }>('Runtime.evaluate', {
          expression: `(() => {
            const titleEl = document.querySelector('textarea[placeholder*="标题"]');
            const editor = document.querySelector('.public-DraftEditor-content');
            if (titleEl && editor) return 'ok';
            if (location.href.includes('signin') || /登录|扫码/.test(document.body.innerText.slice(0, 300))) return 'login';
            return 'loading';
          })()`,
          returnByValue: true,
        }, { sessionId });
        if (r.result.value === 'ok' || r.result.value === 'login') return r.result.value as 'ok' | 'login';
        await sleep(1000);
      }
      return 'timeout';
    };

    if (!json) console.log('[zhihu] Waiting for editor...');
    const editorState = await waitForEditor();
    if (editorState === 'login') throw new Error('Zhihu login required. Log in once in the browser window, then re-run.');
    if (editorState === 'timeout') throw new Error('Zhihu editor not found after 30s. Check network or Zhihu layout change.');

    // 幂等：清空已有正文（用真实键盘事件 Draft 才能响应）
    await cdp.send('Runtime.evaluate', {
      expression: `(() => {
        const editor = document.querySelector('.public-DraftEditor-content');
        if (editor) editor.focus();
      })()`,
    }, { sessionId });
    await sleep(300);

    const hasContent = await cdp.send<{ result: { value: boolean } }>('Runtime.evaluate', {
      expression: `(() => {
        const e = document.querySelector('.public-DraftEditor-content');
        if (!e) return false;
        return (e.innerText.replace(/\\s/g, '').length > 0);
      })()`,
      returnByValue: true,
    }, { sessionId });

    if (hasContent.result.value) {
      if (!json) console.log('[zhihu] Editor has existing content, clearing via Ctrl+A + Backspace...');
      // 真实键盘事件：Ctrl+A（modifiers=2），Backspace
      await cdp.send('Input.dispatchKeyEvent', { type: 'keyDown', modifiers: 2, key: 'a', code: 'KeyA', windowsVirtualKeyCode: 65 }, { sessionId });
      await cdp.send('Input.dispatchKeyEvent', { type: 'keyUp', modifiers: 2, key: 'a', code: 'KeyA', windowsVirtualKeyCode: 65 }, { sessionId });
      await sleep(150);
      await cdp.send('Input.dispatchKeyEvent', { type: 'keyDown', key: 'Backspace', code: 'Backspace', windowsVirtualKeyCode: 8 }, { sessionId });
      await cdp.send('Input.dispatchKeyEvent', { type: 'keyUp', key: 'Backspace', code: 'Backspace', windowsVirtualKeyCode: 8 }, { sessionId });
      await sleep(600);
    }

    // 填标题（Input.insertText 保证真实输入事件）
    await cdp.send('Runtime.evaluate', {
      expression: `(() => {
        const el = document.querySelector('textarea[placeholder*="标题"]');
        if (el) el.focus();
      })()`,
    }, { sessionId });
    await sleep(200);
    await cdp.send('Input.insertText', { text: truncatedTitle }, { sessionId });
    await sleep(600);

    const titleCheck = await cdp.send<{ result: { value: string } }>('Runtime.evaluate', {
      expression: `document.querySelector('textarea[placeholder*="标题"]')?.value || ''`,
      returnByValue: true,
    }, { sessionId });
    const actualTitle = titleCheck.result.value;
    if (actualTitle !== truncatedTitle) {
      // 重试一次标题
      await cdp.send('Runtime.evaluate', {
        expression: `(() => { const el = document.querySelector('textarea[placeholder*="标题"]'); if (el) { el.focus(); el.value = ${JSON.stringify(truncatedTitle)}; el.dispatchEvent(new Event('input', { bubbles: true })); } })()`,
      }, { sessionId });
      await sleep(400);
    }
    if (!json) console.log(`[zhihu] Title in editor (${actualTitle.length} chars)`);
    result.title = actualTitle;

    // 粘贴正文（带一次自动重试）
    const pasteBody = async (): Promise<{ textLen: number; blocks: number; tables: number; pres: number }> => {
      await cdp.send('Runtime.evaluate', {
        expression: `(() => {
          const editor = document.querySelector('.public-DraftEditor-content');
          if (!editor) return false;
          editor.focus(); editor.click();
          return true;
        })()`,
      }, { sessionId });
      await sleep(400);

      const pasted = await cdp.send<{ result: { value: string } }>('Runtime.evaluate', {
        expression: `(() => {
          const editor = document.querySelector('.public-DraftEditor-content');
          if (!editor) return 'no_editor';
          editor.focus();
          const html = ${JSON.stringify(htmlContent)};
          const plain = ${JSON.stringify(htmlContent.replace(/<[^>]*>/g, '\n').replace(/\n{3,}/g, '\n\n'))};
          const dt = new DataTransfer();
          dt.setData('text/html', html);
          dt.setData('text/plain', plain);
          const ev = new ClipboardEvent('paste', { bubbles: true, cancelable: true, clipboardData: dt });
          editor.dispatchEvent(ev);
          return 'dispatched';
        })()`,
        returnByValue: true,
      }, { sessionId });
      await sleep(4000);

      const chk = await cdp.send<{ result: { value: { textLen: number; blocks: number; tables: number; pres: number } } }>('Runtime.evaluate', {
        expression: `(() => {
          const editor = document.querySelector('.public-DraftEditor-content');
          if (!editor) return { textLen: 0, blocks: 0, tables: 0, pres: 0 };
          return {
            textLen: editor.innerText.length,
            blocks: editor.querySelectorAll('[data-block]').length,
            tables: editor.querySelectorAll('table').length,
            pres: editor.querySelectorAll('pre').length,
          };
        })()`,
        returnByValue: true,
      }, { sessionId });
      return chk.result.value;
    };

    let content = await pasteBody();

    // 校验：block 数严重不足 → 重试一次（知乎编辑器偶尔吞粘贴）
    const minBlocks = Math.max(20, Math.floor(expect.textLen / 120));
    if (content.blocks < minBlocks && content.textLen < expect.textLen * 0.5) {
      if (!json) console.warn(`[zhihu] Paste looks incomplete (${content.blocks} blocks < ${minBlocks}), retrying...`);
      await cdp.send('Runtime.evaluate', {
        expression: `(() => { const e = document.querySelector('.public-DraftEditor-content'); if (e) e.innerText = ''; })()`,
      }, { sessionId });
      await sleep(500);
      content = await pasteBody();
    }

    result.content = content;
    result.ok = content.blocks >= Math.min(minBlocks, 20) || content.textLen >= 2000;

    if (!json) {
      console.log(`[zhihu] Editor content: ${content.textLen} chars, ${content.blocks} blocks, ${content.tables} tables, ${content.pres} code blocks`);
      if (!result.ok) console.warn('[zhihu] Content may be incomplete — please verify in browser.');
    }

    // 截图（可选，供 agent 视觉验证）
    if (screenshotPath) {
      try {
        const shot = await cdp.send<{ data: string }>('Page.captureScreenshot', { format: 'png' }, { sessionId });
        fs.writeFileSync(screenshotPath, Buffer.from(shot.data, 'base64'));
        screenshotSaved = true;
        if (!json) console.log(`[zhihu] Screenshot saved: ${screenshotPath}`);
      } catch (e) {
        if (!json) console.warn(`[zhihu] Screenshot failed: ${e instanceof Error ? e.message : String(e)}`);
      }
    }

    if (!json) {
      console.log('[zhihu] Article composed. Please review in the browser and publish manually.');
      console.log('[zhihu] Browser remains open for manual review.');
    }

  } finally {
    cdp.close();
    if (launchedByUs && !keepAlive) {
      // 由脚本启动且用户要求关闭时，才关闭
      const { killChromeByProfile } = await import('./chrome-utils.js');
      killChromeByProfile(profileDir);
    }
  }

  if (json) {
    console.log(JSON.stringify({
      ...result,
      title: result.title,
      htmlPath: outHtml,
      screenshot: screenshotSaved ? screenshotPath : null,
    }));
  }
}

// ---------- CLI ----------
const args = process.argv.slice(2);
let markdownPath: string | undefined;
let cliPort: number | undefined;
let dryRun = false;
let keepAlive = true;
let screenshotPath: string | undefined;
let json = false;
let titleOverride: string | undefined;

for (let i = 0; i < args.length; i++) {
  const arg = args[i]!;
  if (arg === '--port' && args[i + 1]) cliPort = Number(args[++i]);
  else if (arg === '--title' && args[i + 1]) titleOverride = args[++i];
  else if (arg === '--screenshot' && args[i + 1]) screenshotPath = args[++i];
  else if (arg === '--dry-run') dryRun = true;
  else if (arg === '--no-keep-alive') keepAlive = false;
  else if (arg === '--json') json = true;
  else if (!arg.startsWith('-')) markdownPath = arg;
}

if (!markdownPath || args.includes('--help') || args.includes('-h')) {
  console.log(`Publish Markdown article to Zhihu (semi-auto, user clicks final 发布)

Usage:
  npx -y bun zhihu-publish.ts <markdown_file> [options]

Options:
  --port <port>       Chrome debug port (default: auto-detect or auto-launch)
  --title <text>      Override title (default: frontmatter title or first # heading)
  --screenshot <path> Save a PNG screenshot after filling (for visual verification)
  --dry-run           Only convert markdown → HTML, don't touch browser
  --json              Machine-readable JSON output on stdout
  --no-keep-alive     Close the Chrome instance this script launched (keep-alive by default)
  --help              Show this help

Env:
  ZHIHU_OUT_HTML       Output path for converted HTML (default /tmp/zhihu-article-content.html)
  ZHIHU_BROWSER_CHROME_PATH  Chrome executable path override
`);
  process.exit(args.includes('--help') || args.includes('-h') ? 0 : 1);
}

await publishToZhihu({
  markdownPath,
  title: titleOverride,
  debugPort: cliPort,
  dryRun,
  keepAlive,
  screenshotPath,
  json,
}).catch((err) => {
  if (json) console.log(JSON.stringify({ ok: false, error: err instanceof Error ? err.message : String(err) }));
  else console.error(`Error: ${err instanceof Error ? err.message : String(err)}`);
  process.exit(1);
});
