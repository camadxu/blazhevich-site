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

## Обычный цикл изменений

1. Агент вносит изменения, гоняет проверки, пушит в `main`.
2. CI автоматически обновляет test.blazhevich.tech.
3. Вы смотрите тест-сайт.
4. Всё хорошо → Actions → «ПРОДАКШЕН» → Run workflow → blazhevich.tech обновлён.

## Откат

- Тест: `git revert <коммит>` и push в `main` — тест-сайт вернётся автоматически.
- Прод: повторный запуск workflow «ПРОДАКШЕН» на нужном коммите (или revert + запуск).
- Крайний случай: вернуть файлы из ZIP-бэкапа через File Manager.

## Если в тарифе нет инструмента Git

Скажите агенту — переключим деплой на GitHub Actions + FTP, где FTP-пароль вводится только в GitHub Secrets вашим руками (агенты его не видят и не запрашивают).
