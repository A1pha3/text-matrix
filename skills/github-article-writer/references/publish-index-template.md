# Publish Index 更新模板

## 格式

```markdown
| **{项目名}** | {owner}/{repo} | {Stars} | {slug}.md | {commit hash} | {飞书文档ID} | {日期} |
```

## 示例

```markdown
| **Hyperagents** | facebookresearch/HyperAgents | 2k | hyperagents-self-referential-ai-agents-guide.md | db73004 | BhZAdE0obocpC5xSUp9cKQfsn4e | 2026-04-02 |
```

## 字段说明

| 字段 | 来源 |
|------|------|
| 项目名 | GitHub 仓库名或中文项目名 |
| owner/repo | GitHub 仓库完整路径 |
| Stars | GitHub 页面右上角数字 |
| slug.md | 文章文件名（content/posts/tech/ 下的文件名） |
| commit hash | `git commit` 后的 7 位 hash |
| 飞书文档ID | 创建飞书文档后返回的 document_id |
| 日期 | 格式 `YYYY-MM-DD` |

## 注意事项

1. **按 Stars 数量排序**：Stars 多的在上，少的在下
2. **同一项目多次发布**：只更新对应的行，不新增
3. **文件路径**：`~/.openclaw/workspace/GitHub/text-matrix/docs/memory/publish-index.md`
