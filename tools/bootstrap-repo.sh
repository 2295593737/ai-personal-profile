#!/usr/bin/env bash
# 一次性把本地档案推到 GitHub。
# 用法：
#   GH_TOKEN=ghp_xxx bash tools/bootstrap-repo.sh
# 可选环境变量：
#   OWNER  默认 2295593737
#   REPO   默认 ai-personal-profile
# 说明：脚本可重复执行；仓库已存在时只做推送，不会重复创建。

set -euo pipefail

OWNER="${OWNER:-2295593737}"
REPO="${REPO:-ai-personal-profile}"
API="https://api.github.com"

if [ -z "${GH_TOKEN:-}" ]; then
  echo "缺少 GH_TOKEN。请先设置一个有 repo 权限的令牌：GH_TOKEN=xxx bash tools/bootstrap-repo.sh" >&2
  exit 1
fi

auth=(-H "Authorization: Bearer ${GH_TOKEN}" -H "Accept: application/vnd.github+json" -H "X-GitHub-Api-Version: 2022-11-28")

echo "==> 检查仓库 ${OWNER}/${REPO}"
code=$(curl -s -o /dev/null -w "%{http_code}" "${auth[@]}" "${API}/repos/${OWNER}/${REPO}")

if [ "$code" = "404" ]; then
  echo "==> 创建公开仓库"
  curl -sS -X POST "${auth[@]}" "${API}/user/repos" \
    -d "{\"name\":\"${REPO}\",\"description\":\"Cross-AI personal profile\",\"private\":false,\"auto_init\":false}" \
    -o /dev/null -w "HTTP %{http_code}\n"
elif [ "$code" = "200" ]; then
  echo "==> 仓库已存在，跳过创建"
else
  echo "==> 意外的响应码 ${code}，请检查令牌权限" >&2
  exit 1
fi

echo "==> 初始化本地 Git"
cd "$(dirname "$0")/.."
git init -b main >/dev/null 2>&1 || git init >/dev/null
git symbolic-ref -q HEAD >/dev/null 2>&1 || true

git remote remove origin >/dev/null 2>&1 || true
git remote add origin "https://github.com/${OWNER}/${REPO}.git"

git add -A
if ! git diff --cached --quiet; then
  git -c user.name="${GIT_NAME:-$OWNER}" -c user.email="${GIT_EMAIL:-${OWNER}@users.noreply.github.com}" \
    commit -m "docs: 初始化跨 AI 个人档案结构" || true
fi

echo "==> 推送"
git -c credential.helper= \
    -c "http.https://github.com/.extraheader=Authorization: Bearer ${GH_TOKEN}" \
    push -u origin main

echo "==> 完成：https://github.com/${OWNER}/${REPO}"
