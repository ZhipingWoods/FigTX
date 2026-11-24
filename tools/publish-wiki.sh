#!/usr/bin/env bash
# 把 docs/wiki 发布到 GitHub Wiki（FigTX.wiki.git）
# 用法： ./tools/publish-wiki.sh
set -euo pipefail

REPO_SSH="${1:-git@github.com:ZhipingWoods/FigTX.wiki.git}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TMP="$(mktemp -d)"

echo "→ 克隆 wiki: $REPO_SSH"
git clone "$REPO_SSH" "$TMP/wiki"

# 文件名保持中文，GitHub Wiki 会直接用作页面标题
rsync -a --delete --exclude='.git' "$ROOT/docs/wiki/" "$TMP/wiki/"

cd "$TMP/wiki"
git add -A
if git diff --cached --quiet; then
  echo "→ 无变化"
else
  git -c user.name="ZhipingWoods" -c user.email="zhipingwoods@users.noreply.github.com" \
      commit -m "docs: 同步 wiki ($(date +%Y-%m-%d))"
  git push origin master 2>/dev/null || git push origin main
  echo "→ 已发布"
fi
rm -rf "$TMP"