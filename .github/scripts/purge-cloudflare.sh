#!/usr/bin/env bash
# Сброс кэша Cloudflare после публикации артефакт-ветки.
# Шаг необязательный: если секреты не заданы, скрипт выходит с кодом 0 и предупреждением.
#   нужны: CLOUDFLARE_API_TOKEN (Zone → Cache Purge), CLOUDFLARE_ZONE_ID
set -uo pipefail

if [ -z "${CF_API_TOKEN:-}" ] || [ -z "${CF_ZONE_ID:-}" ]; then
  echo "::notice::Секреты Cloudflare не заданы — сброс кэша пропущен"
  exit 0
fi

RESPONSE=$(mktemp)
CODE=$(curl -sS -o "$RESPONSE" -w '%{http_code}' \
  -X POST "https://api.cloudflare.com/client/v4/zones/${CF_ZONE_ID}/purge_cache" \
  -H "Authorization: Bearer ${CF_API_TOKEN}" \
  -H "Content-Type: application/json" \
  --data '{"purge_everything":true}') || CODE=000

if grep -q '"success":true' "$RESPONSE" 2>/dev/null; then
  echo "OK: кэш Cloudflare сброшен"
  exit 0
fi

# Деплой уже опубликован, поэтому не роняем сборку — только громкое предупреждение.
echo "::warning::Cloudflare не подтвердил сброс кэша (HTTP ${CODE})"
cat "$RESPONSE" 2>/dev/null || true
exit 0
