#!/bin/sh
set -eu

site_dir="${1:-public}"
script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
repo_root=$(CDPATH= cd -- "$script_dir/.." && pwd)
workspace_python="$repo_root/.conda/bin/python"

if [ -n "${PAGEFIND_BIN:-}" ]; then
  exec "$PAGEFIND_BIN" --site "$site_dir"
fi

if [ -x "$workspace_python" ]; then
  if "$workspace_python" -c 'import pagefind' >/dev/null 2>&1; then
    exec "$workspace_python" -m pagefind --site "$site_dir"
  fi
fi

if command -v python3 >/dev/null 2>&1; then
  if python3 -c 'import pagefind' >/dev/null 2>&1; then
    exec python3 -m pagefind --site "$site_dir"
  fi
fi

if command -v npx >/dev/null 2>&1; then
  if npx -y pagefind --site "$site_dir"; then
    exit 0
  fi
fi

echo "Pagefind runner is unavailable on this machine." >&2
echo "If you are on macOS arm64, install the Python wrapper and retry:" >&2
echo "python3 -m pip install 'pagefind[extended]'" >&2
exit 1