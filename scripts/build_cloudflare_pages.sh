#!/bin/sh
set -eu

if [ -z "${CF_PAGES_URL:-}" ]; then
  echo 'CF_PAGES_URL is required' >&2
  exit 1
fi

python3 ./scripts/validate_site.py future-dates
python3 ./scripts/validate_hugo_template_compatibility.py

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

# Hugo 版本自钉：CF Pages 内置 hugo 由后台 HUGO_VERSION 决定，未配置时可能过旧；
# 模板同时只使用跨版本稳定 API，避免单点版本差异中断全站渲染。
# 不依赖控制台配置：版本不匹配时自行下载与 CI 一致的 extended 版，经 HUGO_BIN 构建。
required_hugo="0.161.1"
if [ "$(uname -s)" = "Linux" ]; then
  current_hugo="$(hugo version 2>/dev/null | sed -n 's/.*v\([0-9][0-9.]*\).*/\1/p' | head -1)"
  if [ "$current_hugo" != "$required_hugo" ]; then
    hugo_dir="${HOME}/.cache/hugo-pin/hugo_extended_${required_hugo}"
    if [ ! -x "${hugo_dir}/hugo" ]; then
      echo "Hugo 版本不匹配（当前：${current_hugo:-未安装}），下载 v${required_hugo}…"
      mkdir -p "$hugo_dir"
      curl -fsSL "https://github.com/gohugoio/hugo/releases/download/v${required_hugo}/hugo_extended_${required_hugo}_Linux-64bit.tar.gz" \
        | tar -xz -C "$hugo_dir" hugo
    fi
    export HUGO_BIN="${hugo_dir}/hugo"
  fi
fi

sh ./scripts/build_hugo.sh $build_args
sh ./scripts/run_pagefind.sh public
python3 ./scripts/validate_site.py expected-files --site-dir public --manifest ./scripts/expected-public-files.txt
python3 ./scripts/validate_article_end.py public
python3 ./scripts/check_internal_links.py --site-dir public --base https://txtmix.com
