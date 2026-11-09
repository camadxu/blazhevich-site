#!/usr/bin/env bash
# Публикация собранного сайта в артефакт-ветку.
#   usage: publish-artifact.sh <ветка> <сообщение коммита>
# Корень артефакт-ветки = содержимое site/ + .htaccess из .deploy/htaccess.
# В ветки deploy/* не пушат вручную — их пишет только CI.
set -euo pipefail

BRANCH="${1:?нужно имя ветки}"
MSG="${2:?нужно сообщение коммита}"
SITE_DIR="$GITHUB_WORKSPACE/site"
HTACCESS="$GITHUB_WORKSPACE/.deploy/htaccess"
WT=/tmp/publish_worktree

test -f "$SITE_DIR/index.html" || { echo "ОШИБКА: site/index.html не найден — сначала сборка"; exit 1; }
test -f "$HTACCESS" || { echo "ОШИБКА: не найден $HTACCESS"; exit 1; }

REV=$(git -C "$GITHUB_WORKSPACE" rev-parse --short HEAD)
git -C "$GITHUB_WORKSPACE" config user.name "blazhevich-deploy-bot"
git -C "$GITHUB_WORKSPACE" config user.email "deploy-bot@blazhevich.tech"

git -C "$GITHUB_WORKSPACE" fetch --quiet origin "$BRANCH" 2>/dev/null || true

rm -rf "$WT"
if git -C "$GITHUB_WORKSPACE" ls-remote --exit-code --heads origin "$BRANCH" >/dev/null 2>&1; then
  git -C "$GITHUB_WORKSPACE" worktree add --quiet -B "$BRANCH" "$WT" "origin/$BRANCH"
else
  git -C "$GITHUB_WORKSPACE" worktree add --quiet --detach "$WT" HEAD
  git -C "$WT" checkout --quiet --orphan "$BRANCH"
  git -C "$WT" rm -rf --ignore-unmatch --quiet . >/dev/null 2>&1 || true
fi

find "$WT" -mindepth 1 -maxdepth 1 ! -name '.git' -exec rm -rf {} +
cp -a "$SITE_DIR"/. "$WT"/
cp "$HTACCESS" "$WT/.htaccess"

git -C "$WT" add -A
if git -C "$WT" diff --cached --quiet; then
  echo "Изменений нет — $BRANCH уже актуален (источник $REV)"
else
  git -C "$WT" commit --quiet -m "$MSG (из $REV)"
  git -C "$WT" push --quiet origin "HEAD:$BRANCH"
  echo "OK: $BRANCH обновлён (источник $REV)"
fi

git -C "$GITHUB_WORKSPACE" worktree remove --force "$WT" || true
