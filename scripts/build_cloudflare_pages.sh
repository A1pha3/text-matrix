#!/bin/sh
set -eu

if [ -z "${CF_PAGES_URL:-}" ]; then
  echo 'CF_PAGES_URL is required' >&2
  exit 1
fi

python3 ./scripts/validate_site.py future-dates

# 环境判定：只有 main 分支才用 production（注入 GA/AdSense）。
# 预览分支（PR/其他 branch）必须用非 production 环境——gtag/adsense 模板都以
# hugo.Environment == "production" 为守卫，预览构建用 production 会把真实
# 测量 ID / Adsense 代码打进 pages.dev 预览页（2026-08-17 对抗审查 H1）
if [ "${CF_PAGES_BRANCH:-}" = "main" ]; then
  build_args="--gc --minify --environment production"
else
  build_args="--gc --minify --environment preview"
  build_args="$build_args --baseURL ${CF_PAGES_URL}/"
fi

# 提示：CF Pages 项目后台的构建命令会把本脚本作为 Build command；
# Hugo 二进制版本由项目设置 HUGO_VERSION 决定——为与本仓库 CI（0.161.1）
# 保持一致，请在 CF 项目设置里把 HUGO_VERSION 设为 0.161.1。

sh ./scripts/build_hugo.sh $build_args
sh ./scripts/run_pagefind.sh public
python3 ./scripts/validate_site.py expected-files --site-dir public --manifest ./scripts/expected-public-files.txt
python3 ./scripts/check_internal_links.py --site-dir public --base https://txtmix.com
