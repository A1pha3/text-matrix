# 视频精读 Publish Index 更新模板

## 文件路径

`docs/memory/publish-index.md`

## 格式

视频精读文章使用以下格式（与其他技术文章一致）：

```markdown
| {slug} | {中文标题} | video | {YYYY-MM-DD} | {来源} | [文章](/posts/video/{slug}/) | [飞书](https://feishu.cn/docx/{document_id}) |
```

## 字段说明

| 字段 | 来源 |
|------|------|
| slug | 文件名（不含 .md），与 Frontmatter slug 一致 |
| 中文标题 | 与 Frontmatter title 一致 |
| video | 固定分类标识 |
| 日期 | 格式 `YYYY-MM-DD`，与文章发布日期一致 |
| 来源 | 频道名或平台链接（如 `YouTube @ChannelName`） |
| 文章链接 | `/posts/video/{slug}/` |
| 飞书链接 | 创建飞书文档后填入 `https://feishu.cn/docx/{id}` |

## 示例

```markdown
| claude-mythos-preview-security | Claude Mythos Preview安全研究揭秘 | video | 2026-04-09 | 微博@宝玉xp | [文章](/posts/video/claude-mythos-preview-security-vulnerabilities-analysis/) | [飞书](https://feishu.cn/docx/QW2idnFRQoFNorxWNICcdGC6nKh) |
```

## 注意事项

1. **发布前去重**：写入前先 `grep` 索引文件，确认 slug 不存在
2. **文件存放路径**：`content/posts/video/{slug}.md`
3. **飞书文档可选**：未创建飞书文档时留空，不填占位符
4. **按日期降序**：新文章插入在对应月份区域的顶部
