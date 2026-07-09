# pre-commit 钩子说明（即使冗余也要文档化）

**最后更新**：2026-07-09 17:35 GMT+8
**目的**：解释为什么 cron payload 中的 pre-commit 段是冗余可删除的（参考铁律外移决策）

---

## 当前状态

- ✅ **仓库级 `.git/config` 已激活**：`core.hooksPath=.githooks`
- ✅ **commit 5e0da6b7 验证**：commit 输出包含 `[frontmatter-lint] scanned 1 files, fatal=0, warn=0`
- ✅ **cron payload 中的"git config core.hooksPath .githooks"是冗余防御**（已删除）

---

## 钩子功能

`text-matrix/.githooks/pre-commit`：

```bash
#!/bin/sh
# frontmatter lint - 检查 commit 中所有 *.md 文件的 frontmatter
# 拦截：date 未来时间 / categories 错误 / tags 缺失等
```

**触发时机**：每次 `git commit` 前自动执行

**失败处理**：
- fatal > 0 → commit 中止
- warn > 0 → 警告但不中止

---

## 已激活的 cron（7-06 11:39 师父批准）

- ✅ trending 3 个：`0045a8a5` 15:00 → `4a4f8bc3` 凌晨 3 点（合并后 1 个）
- ✅ 早报 4 个：`878d492b` AI新闻 / `27e08237` 经济财经 / `28270175` Web3 / `abd75bdf` AI副业
- ✅ 健康检查 `850cf6e9`（无 commit 操作，无需）

---

## 历史踩坑

- 2026-06-28 `0321327` 6-28 docs batch：Lint frontmatter fail
- 2026-06-30 `0ce3a92` glm-rush 首发：Lint frontmatter fail
- 触发：6-30 15:49 师父飞书 message `om_x100b6b031e66dc80b2f6c0626a82a92` 拍板铁律

**根因**：仓库内任何 `git commit` 必须走 pre-commit 钩子，仓库级 + cron payload 显式双层激活

---

## 异常决策文档

`~/.openclaw/workspace/docs/anomaly-decisions/122.1-mit-6s184-fix-and-trending-precommit-2026-06-30.md`

---

## 7-09 铁律外移

- cron payload 中的"git config core.hooksPath .githooks"步骤已删除
- 删除原因：仓库级 `.git/config` 已生效，cron payload 步骤是冗余防御
- 删除字符：414 × 4 cron = **1656 chars**
- 删除时间：2026-07-09 17:35
- 备案：`state/cron-backups/iron-law-externalization-20260709-1731/`

**记忆来源**：2026-07-09 17:31 师父飞书批准全部 6 步外移 `om_x100b6bc2e9c568a0b4cd454ede2c417`