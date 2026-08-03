---
name: zhihu-publish
description: |
  Publish Markdown articles to Zhihu (知乎专栏/文章) via real Chrome CDP. Converts markdown to clean HTML via marked, launches its own Chrome (no manual setup), fills title and body into the Draft.js editor — but never clicks the final 发布 button; the user reviews and publishes manually. Use when user asks to "发布到知乎", "发知乎文章", "publish to Zhihu", "知乎发布".
  依赖: bun/npx + Google Chrome（自动启动，沙箱内带 --no-sandbox）、marked。
agent_created: true
version: 2.0.0
metadata:
  openclaw:
    requires:
      anyBins:
        - bun
        - npx
---

# Publish to Zhihu (知乎文章发布)

Compose an article on `zhuanlan.zhihu.com/write` via Chrome CDP. The script auto-launches Chrome (or reuses a running one), fills title + body, and leaves the browser open for you to review and click 发布.

## Quick start

```bash
# One command, no setup. Browser opens automatically.
npx -y bun {baseDir}/scripts/zhihu-publish.ts path/to/article.md

# Preview the HTML conversion without touching the browser
npx -y bun {baseDir}/scripts/zhihu-publish.ts path/to/article.md --dry-run

# Save a screenshot for visual verification
npx -y bun {baseDir}/scripts/zhihu-publish.ts path/to/article.md --screenshot /tmp/preview.png

# Machine-readable output for agent automation
npx -y bun {baseDir}/scripts/zhihu-publish.ts path/to/article.md --json
```

## Options

| Flag | Effect |
|------|--------|
| `--port <port>` | Connect to an existing Chrome on this debug port (skip auto-launch) |
| `--title <text>` | Override title (default: YAML frontmatter title or first `# heading`) |
| `--screenshot <path>` | Save a PNG of the filled editor (lets agent "see" the result) |
| `--dry-run` | Only convert markdown → HTML; don't touch browser |
| `--json` | Single-line JSON summary on stdout (for agent automation) |
| `--no-keep-alive` | Close the Chrome instance this script launched |

Env: `ZHIHU_OUT_HTML` (default `/tmp/zhihu-article-content.html`), `ZHIHU_BROWSER_CHROME_PATH`.

## What the script does

1. Parse markdown → clean HTML via `marked` (GFM: tables, nested lists, code blocks, images all supported).
2. **Mermaid blocks** are preserved as code blocks with a labelled note ("知乎暂不支持渲染，源码见下方代码块") — Zhihu has no native mermaid renderer, and we don't auto-upload PNGs (would require brittle file-input upload flow).
3. **`<details>/<summary>`** blocks are flattened into blockquotes ("答案: ...") — Zhihu's Draft.js editor strips unknown tags, so we convert proactively.
4. Auto-launch Chrome (or reuse an existing one on `--port`) with `--no-sandbox --disable-gpu`; clean profile locks first.
5. Navigate to `zhuanlan.zhihu.com/write`, wait for editor, **log in once** if prompted.
6. **Idempotent**: if the editor already has content (rerun case), clear via real Ctrl+A + Backspace key events (Draft.js responds to real keyboard, not `execCommand`).
7. Fill title (CDP `Input.insertText` for real input events) and paste body via synthesized `ClipboardEvent('paste')` with `DataTransfer`.
8. **Verify**: compare blocks/tables/code-blocks to expected counts; if severely under-target, retry paste once.
9. Optional screenshot for visual confirmation.
10. Browser stays open — you click 发布.

## Troubleshooting

| Symptom | Cause / Fix |
|---------|-------------|
| `Zhihu login required` error | Log in once in the browser window, then re-run |
| `editor not found after 30s` | Zhihu layout changed — update selectors in `zhihu-publish.ts` (`textarea[placeholder*="标题"]`, `.public-DraftEditor-content`) |
| `Paste looks incomplete` warning + retry | Known issue on first paste — retry path fills it; verify with screenshot |
| Chrome fails to launch in WorkBuddy sandbox | The script already uses `--no-sandbox --disable-gpu` and cleans locks; if still failing, ensure `~/Library/Application Support/baoyu-skills/chrome-profile` is writable |
| Tables or details look wrong in editor | Re-check the saved HTML at `/tmp/zhihu-article-content.html`; tables and details should be flat HTML |

## Pairing

Works on any Hugo-style markdown with YAML frontmatter (`title`, `description` honored). For text-matrix posts, source is `content/posts/tech/*.md` — no preprocessing needed.