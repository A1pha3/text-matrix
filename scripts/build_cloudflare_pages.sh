#!/bin/sh
set -eu

if [ -z "${CF_PAGES_URL:-}" ]; then
  echo 'CF_PAGES_URL is required' >&2
  exit 1
fi

build_args="--gc --minify --environment production"

if [ "${CF_PAGES_BRANCH:-}" != "main" ]; then
  build_args="$build_args --baseURL ${CF_PAGES_URL}/"
fi

sh ./scripts/build_hugo.sh $build_args
sh ./scripts/run_pagefind.sh public