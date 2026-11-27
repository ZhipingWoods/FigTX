#!/usr/bin/env bash
# 从 clone 下来的 FigTX 仓库安装 figtx 命令和 FigTX skills（符号链接，仓库更新后立即生效）。
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
if ! command -v uv >/dev/null 2>&1; then
  echo "需要 uv：curl -LsSf https://astral.sh/uv/install.sh | sh" >&2
  exit 1
fi
uv tool install --editable "$ROOT/packages/figtx-forge" --force
figtx skills install --link "$@"
