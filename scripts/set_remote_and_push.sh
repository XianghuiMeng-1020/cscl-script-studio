#!/bin/bash
# 使用你提供的 Git 仓库 link 配置远程并推送。
# 用法：./scripts/set_remote_and_push.sh <你的仓库 URL>
# 或：  GIT_REMOTE_URL=<url> ./scripts/set_remote_and_push.sh
set -e
cd "$(dirname "$0")/.."
ROOT="$PWD"
URL="${1:-$GIT_REMOTE_URL}"
if [ -z "$URL" ]; then
  echo "用法: $0 <Git 仓库 URL>"
  echo "或:   GIT_REMOTE_URL=<url> $0"
  echo "示例: $0 https://github.com/你的用户名/cscl-script-generation.git"
  exit 1
fi
if ! git remote get-url origin 2>/dev/null; then
  git remote add origin "$URL"
  echo "已添加远程: origin -> $URL"
else
  echo "当前 origin: $(git remote get-url origin)"
  read -p "是否改为 $URL? [y/N] " -n 1 -r
  echo
  if [[ $REPLY =~ ^[Yy]$ ]]; then
    git remote set-url origin "$URL"
    echo "已更新 origin -> $URL"
  fi
fi
BRANCH=$(git branch --show-current)
echo "推送到 origin $BRANCH ..."
git push -u origin "$BRANCH"
echo "完成。请在 Cloudflare Dashboard 连接该仓库并部署。"
