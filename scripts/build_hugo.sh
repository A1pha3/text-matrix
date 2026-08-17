#!/bin/sh
set -eu

# 用显式指定的 hugo 二进制（HUGO_BIN），否则 PATH 里的 hugo。
# 曾硬编码另一台机器的 /Volumes/.../hugo：本机挂载该盘时会用到错误版本（2026-08-17 对抗审查）。
if [ -n "${HUGO_BIN:-}" ]; then
  hugo_bin="$HUGO_BIN"
else
  hugo_bin=hugo
fi

exec "$hugo_bin" "$@"