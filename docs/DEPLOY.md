# Подключение GitHub + Hostinger — чек-лист владельца

Схема: **ИИ-агент → приватный GitHub-репозиторий → test.blazhevich.tech → ваша проверка → blazhevich.tech**

Пароли Hostinger, FTP, SSH и файловый менеджер агентам не передаются вообще. Хостинг сам забирает код из репозитория по deploy-ключу «только чтение» — его добавляете вы лично. GitHub Secrets не нужны вовсе.

Что уже сделано агентом локально (C:\Users\IAI\Documents\ZAI):
- Репозиторий с исходниками сайта (та же версия, что сейчас на blazhevich.tech — сверено байт-в-байт).
- CI: push в `main` → автосборка → проверка → публикация ветки `deploy/test`; публикация прода — отдельный ручной workflow → ветка `deploy/prod`.
- AGENTS.md — правила работы агентов (включая ваши запреты по доступам).

---

## Шаг 1. Создать приватный репозиторий (≈2 минуты)

1. Откройте https://github.com/new
2. Repository name: например `blazhevich-site` (любое).
3. Вид: **Private**.
4. Ничего не инициализировать (без README, .gitignore, лицензии) — репозиторий уже подготовлен и будет запушен целиком.
5. Скопируйте HTTPS-адрес вида `https://github.com/<ваш-логин>/blazhevich-site.git` и сообщите его агенту — агент сам добавит remote и выполнит push.

При первом push на вашем экране откроется окно входа GitHub (Git Credential Manager). Это ваш личный вход — агент пароли не видит и в них не попадает.

Вариант «сделать самому»:
```powershell
cd C:\Users\IAI\Documents\ZAI
git remote add origin https://github.com/<ваш-логин>/blazhevich-site.git
git push -u origin main
```

## Шаг 2. Разрешить Actions запись в репозиторий (один раз)

GitHub → репозиторий → **Settings → Actions → General → Workflow permissions** → выбрать **Read and write permissions** → Save.
Это нужно, чтобы CI мог обновлять ветки `deploy/test` и `deploy/prod`.

## Шаг 3. Дождаться первого запуска CI

Вкладка **Actions** → workflow «Тест: сборка и публикация deploy/test» должен завершиться зелёным. После этого в репозитории появится ветка **`deploy/test`** — корень этой ветки и есть готовый сайт.

## Шаг 4. hPanel: подключить Git для test.blazhevich.tech

1. hPanel → **Websites** → `test.blazhevich.tech` → **Manage** → в левом меню найти **Git**.
2. Create a New Repository:
   - Git repository: HTTPS-адрес вашего репозитория (`https://github.com/<логин>/blazhevich-site.git`);
   - Branch: **`deploy/test`**;
   - Installation path: папка поддомена (обычно `domains/test.blazhevich.tech/public_html`).
3. Репозиторий приватный, поэтому hPanel предложит подтвердить доступ — следуйте подсказке интерфейса (если показан публичный SSH-ключ: GitHub → репозиторий → **Settings → Deploy keys → Add deploy key**, вставить ключ, галку write access НЕ ставить).
4. Нажмите **Deploy** (первая публикация — вручную).

## Шаг 5. Вебхук автодеплоя для теста

1. hPanel → ваш Git-репозиторий → кнопка **Auto-Deployment** → скопировать Webhook URL.
2. GitHub → репозиторий → **Settings → Webhooks → Add webhook**: вставить URL, событие — **push**, остальное по умолчанию.
3. Проверка: внесите любое изменение в `main` → через минуту test.blazhevich.tech должен обновиться.

## Шаг 6. Проверить тестовый сайт

Откройте https://test.blazhevich.tech — ожидаемо: тёмная версия сайта **с плашкой «Предварительный просмотр · не опубликовано»** и запретом индексации. Так и задумано: тест-сайт никогда не индексируется.

## Шаг 7. Подключить основной сайт blazhevich.tech (когда тест устроит)

1. **Резервная копия:** hPanel → File Manager → папка `domains/blazhevich.tech/public_html` → скачать всё в ZIP. Если в папке есть скрытый `.htaccess` — пришлите его содержимое агенту, чтобы правила не потерялись.
2. Очистить `public_html` (Git-деплой должен начинаться с пустой папки).
3. hPanel → `blazhevich.tech` → Manage → Git → Create a New Repository: тот же репозиторий, ветка **`deploy/prod`**, путь `domains/blazhevich.tech/public_html`. Добавить deploy-ключ, как в шаге 4.
4. Ветка `deploy/prod` появится после первого запуска: GitHub → **Actions → «ПРОДАКШЕН: публикация deploy/prod» → Run workflow** (можно указать дату для sitemap, можно оставить пустой).
5. После появления ветки нажать **Deploy** в hPanel — или добавить второй webhook (Auto-Deployment) для автопубликации. Рекомендация: оставьте прод ручным (кнопка Deploy) — тогда сайт обновляется только когда вы сами нажимаете кнопку.

## Шаг 8. Cloudflare перед хостингом (по желанию, но решает проблему кэша)

Зачем: LiteSpeed на Hostinger держит HTML в своём кэше и после деплоя отдаёт старую страницу (тест-сайт так два дня показывал удалённый раздел). Cloudflare даёт один край на весь домен, честные заголовки кэша и мгновенный сброс при публикации. Все действия с панелями — ваши: агент не запрашивает доступы и не меняет DNS.

### Что нужно сделать вам

1. **Добавить домен.** dash.cloudflare.com → Add a site → `blazhevich.tech` → план Free. Cloudflare покажет две NS-записи вида `xxx.ns.cloudflare.com`.
2. **Перенести записи в Cloudflare** (DNS → Records), пока они ещё отвечают на старом DNS. Без этого шага отвалится почта:

   | Тип | Имя | Значение | Прокси |
   |---|---|---|---|
   | A | `@` | `92.113.23.53` | оранжевое облако |
   | A | `@` | `92.113.23.11` | оранжевое облако |
   | AAAA | `@` | `2a02:4780:45:d103:3536:4d52:44ed:2d4f` | оранжевое облако |
   | AAAA | `@` | `2a02:4780:43:bafa:4f69:f22e:5c26:4435` | оранжевое облако |
   | CNAME | `www` | `www.blazhevich.tech.cdn.hstgr.net` | **серое** (иначе два CDN друг на друге) |
   | A | `test` | `92.113.23.68` | оранжевое облако |
   | A | `test` | `92.113.23.69` | оранжевое облако |
   | MX | `@` | `mx1.hostinger.com` (5), `mx2.hostinger.com` (10) | — |
   | CNAME | `hostingermail-a._domainkey` | `hostingermail-a.dkim.mail.hostinger.com` | серое |
   | CNAME | `hostingermail-b._domainkey` | `hostingermail-b.dkim.mail.hostinger.com` | серое |
   | CNAME | `autoconfig` | `autoconfig.mail.hostinger.com` | серое |
   | CNAME | `autodiscover` | `autodiscover.mail.hostinger.com` | серое |
   | TXT | `@` | `v=spf1 include:_spf.mail.hostinger.com ~all` | — |
   | TXT | `_dmarc` | `v=DMARC1; p=none` | — |

   Значения сняты с живого DNS 16.11.2026: Hostinger мигрировал серверы, старые адреса
   из ранних ревизий этого файла (`2.57.91.x`, `88.222.222.x`, `2a02:4780:84:…`) уже не отвечают.
   Перед переносом сверьте ещё раз: `nslookup blazhevich.tech`, `nslookup test.blazhevich.tech`,
   `nslookup -type=mx blazhevich.tech` — и перенесите то, что вернёт DNS, а не старую таблицу.

3. **Заменить NS у регистратора** на выданные Cloudflare. До этого момента всё работает по-старому.
4. **SSL/TLS → Overview → Full (strict).** Режим Flexible даёт петлю редиректов, Off — ломает HTTPS.
5. **SSL/TLS → Edge Certificates:** Always Use HTTPS — вкл, HSTS — можно не дублировать (он уже в `.htaccess`).
6. **Speed → Optimization:** Brotli — вкл; Rocket Loader — **не включать** (переставляет наши скрипты).
7. **Кэш (правила).** Caching → Cache Rules, два правила: сверху — обход кэша для HTML, ниже — месяц для ассетов:
   - правило 1, «Bypass cache»: `(http.request.uri.path eq "/") or ends_with(http.request.uri.path, ".html") or ends_with(http.request.uri.path, "/")`;
   - правило 2, «Edge TTL → Override origin → 1 month», Browser TTL → Respect origin: `starts_with(http.request.uri.path, "/assets/")`.
   Итог: HTML всегда с источника, ассеты — с края; `Cache-Control` для них уже отдаёт `.htaccess`.
8. **Секреты для сброса кэша (по желанию).** Мой профиль → API Tokens → Create Token → шаблон «Purge cache» на зону `blazhevich.tech`. В GitHub → Settings → Secrets → Actions добавить `CLOUDFLARE_API_TOKEN` и `CLOUDFLARE_ZONE_ID` (Zone ID виден на странице домена). Пока секретов нет, шаг «Сброс кэша Cloudflare» в workflow просто пишет notice и пропускается.

### Что уже сделано в репозитории

- `.deploy/htaccess`: `CacheLookup off` для LiteSpeed, `Cache-Control` по типам файлов (HTML — `no-cache`, шрифты — год с `immutable`, картинки — месяц), HSTS, `nosniff`, `Referrer-Policy`, `Permissions-Policy`, `frame-ancestors`. Все директивы внутри `<IfModule>` — если модуль выключен, сайт не падает.
- `.github/scripts/purge-cloudflare.sh` — сброс кэша после публикации; его вызывает `publish-artifact.sh`, то есть работает и для теста, и для прода. Без секретов шаг пропускается.

### Как проверить

```
curl -sI https://test.blazhevich.tech/ | findstr /i "cache-control cf-cache strict-transport"
curl -sI https://test.blazhevich.tech/assets/hero-home.webp | findstr /i "cache-control cf-cache"
```

Ожидаемо: у HTML `cache-control: no-cache` и `cf-cache-status: DYNAMIC`; у картинки `max-age=2592000` и `cf-cache-status: HIT` после второго запроса. На тесте должен остаться `noindex,nofollow` и плашка «не опубликовано».

### Чего не делать

- Не проксировать MX и DKIM — почта перестанет ходить.
- Не ставить `Flexible` SSL и не включать «Under Attack Mode» на постоянку.
- Не включать кэш HTML на краю: без сброса при деплое вернётся та же проблема, только на другом уровне.

## Обычный цикл изменений

1. Агент вносит изменения, гоняет проверки, пушит в `main`.
2. CI автоматически обновляет test.blazhevich.tech.
3. Вы смотрите тест-сайт.
4. Всё хорошо → Actions → «ПРОДАКШЕН» → Run workflow → blazhevich.tech обновлён.

## Закрыть / открыть сайт (заглушка «временно недоступен»)

- Закрыт: коммит, где в `.deploy/htaccess` есть блок «режим „сайт временно закрыт“» (503 на всё + `maintenance.html`). Попасть на прод и тест — той же кнопкой «ПРОДАКШЕН» / автоматом на тесте.
- Открыть: `git revert` этого коммита в `main`, push — тест откроется сам, прод — кнопкой «ПРОДАКШЕН».
- Текст заглушки правится в `maintenance.html` в корне репозитория (в сборку кладёт build.py).

## Откат

- Тест: `git revert <коммит>` и push в `main` — тест-сайт вернётся автоматически.
- Прод: повторный запуск workflow «ПРОДАКШЕН» на нужном коммите (или revert + запуск).
- Крайний случай: вернуть файлы из ZIP-бэкапа через File Manager.

## Если в тарифе нет инструмента Git

Скажите агенту — переключим деплой на GitHub Actions + FTP, где FTP-пароль вводится только в GitHub Secrets вашим руками (агенты его не видят и не запрашивают).
