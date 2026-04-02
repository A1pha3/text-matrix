#!/bin/sh
set -eu

if [ -n "${HUGO_BIN:-}" ]; then
  hugo_bin="$HUGO_BIN"
elif [ -x /Volumes/mini_matrix/github/a1pha3/web/hugo/hugo ]; then
  hugo_bin=/Volumes/mini_matrix/github/a1pha3/web/hugo/hugo
else
  hugo_bin=hugo
fi

exec "$hugo_bin" "$@"