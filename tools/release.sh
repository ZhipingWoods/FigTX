#!/usr/bin/env bash
# 一键打 tag 并推送（触发 CI 三平台构建 + Release）
# 用法： ./tools/release.sh 0.1.0
set -euo pipefail

VERSION="${1:-}"
if [[ -z "$VERSION" ]]; then
  echo "用法: $0 <version>  例如：$0 0.1.0"
  exit 1
fi

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

# 同步 package.json 版本号
node -e "const fs=require('fs');const p=JSON.parse(fs.readFileSync('package.json'));p.version='$VERSION';fs.writeFileSync('package.json',JSON.stringify(p,null,2)+'\n')"
git add package.json
git commit -m "chore(release): v$VERSION" || true

git tag -a "v$VERSION" -m "FigTX v$VERSION"
git push origin HEAD
git push origin "v$VERSION"

echo "→ 已推送 v$VERSION，CI 正在构建三平台安装包"
echo "   查看进度: https://github.com/ZhipingWoods/FigTX/actions"