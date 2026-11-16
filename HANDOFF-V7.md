# Передача агенту: V7 и Cloudflare — состояние на 16.11.2026

Короткий документ для агента, который продолжит работу. Всё остальное — в `AGENTS.md` (правила) и `DEPLOY.md` (хостинг, шаг 8 про Cloudflare).

## 1. Где что лежит

| Что | Где |
|---|---|
| Рабочий репозиторий | `camadxu/blazhevich-site`, ветка `main` |
| Локальная копия | `D:\blazhevich-site` |
| Прод | https://blazhevich.tech — публикует **только владелец** вручную: Actions → «ПРОДАКШЕН: публикация deploy/prod» |
| Тест | https://test.blazhevich.tech — обновляется сам после push в `main`; черновик: `noindex,nofollow` + плашка «не опубликовано», это норма |
| Сборка | `build.py` из `src/`, только стандартная библиотека Python 3 |

## 2. Жёсткие правила

- Никаких доступов к хостингу: пароль Hostinger, FTP, SSH, hPanel на запись, полный доступ к аккаунту — не запрашивать и не использовать. Всё, что требует панели, делает владелец.
- Секретов в репозиторий не добавлять. Cloudflare-токен владелец кладёт сам в GitHub → Settings → Secrets (`CLOUDFLARE_API_TOKEN`, `CLOUDFLARE_ZONE_ID`).
- В ветки `deploy/*` не пушить — их пишет только CI.
- `site/` руками не править, только `src/`, `assets/`, сборщик.
- Факты — только из источников; сложность нот не выдумывать; бренд — **Blazhevich**.
- **Правки в `.github/workflows/*` этот токен GitHub не пропустит** (нет scope `workflow`). Логику деплоя менять через `.github/scripts/*.sh` — workflow их только вызывают.

## 3. Что сделано в V7 (все коммиты в `main`)

- `1fd4f59` — блок «Что сделало его таким»: плашка с двойной линейкой, рубрика, нумерация 01–05, сетка 2×2 + пятый тезис кодой. Затронуто 6 файлов разметки (ru/en, биография, Москва, Ленинград).
- `acd32c7` — печать (тёмные разделы печатаются тёмным по белому, кнопки контуром, таблицы не режутся, адреса источников), новая страница `404.html` (корень репозитория, `enhancements.py` её копирует), токены `--t-title-s/m/l`, `:active` для тач-экрана, запасной фокус без `:has()`, плашки изданий в таблице концертов отдельной строкой.
- `ff97980` — снято свечение `#listen h2` при печати.
- `af108d5` — «Школы»: персоны разделены линейкой, «Ученики» отдельным блоком, текст 15.5/1.55; отметки источников `.st` — курсивная ремарка вместо кнопки.
- `9fa6b89` — инфраструктура: `.deploy/htaccess` (LiteSpeed `CacheLookup off`, `Cache-Control` по типам, HSTS, `nosniff`, `Referrer-Policy`, `Permissions-Policy`, `frame-ancestors`), `.github/scripts/purge-cloudflare.sh` (вызывается из `publish-artifact.sh`, без секретов пропускается), `DEPLOY.md` шаг 8.
- `50e138d` — стили вынесены в `assets/main.<хэш>.css`: инлайн-`<style>` в страницах больше нет (главная 188 → 104 КБ), CSS кэшируется навсегда (`immutable` в `.htaccess`), `artifact.html` остался одностраничным.
- `bf11276` — DNS-таблица шага 8 переписана по живым IP Hostinger на 16.11.2026 (apex `92.113.23.53/.11`, test `92.113.23.68/.69`, AAAA `2a02:4780:45/43:…`), добавлены CNAME `autoconfig` и `autodiscover` — без них ломается автонастройка почтовых клиентов.
- `8c13fca` (ветка `library/scores-first-files`, в `main` не влита) — первые свои ноты в библиотеке сайта по заявке владельца от 16.11.2026: скан «Школы для раздвижного тромбона» (1936, 9,5 МБ) в `assets/library/scores/` и карточки концертов № 2 и № 5 со ссылками на публичную коллекцию Яндекс.Диска Папы; карточек в каталоге стало 12 (`test_v3.py` обновлён), правило путей `assets/` в EN-исходнике распространено на `href`. Сборка release 2026-11-16, check_site и test_v3 зелёные.

### Состояние веток и сайтов на 16.11.2026

| Ветка / сайт | Состояние |
|---|---|
| `main` | `bf11276`, всё нижеперечисленное влито |
| `deploy/test` | `0b1533b` — сборка из `50e138d`, 15.11 22:04 UTC |
| test.blazhevich.tech | отдаёт V7 и `assets/main.7637d6b20f.css`, `noindex` на месте |
| `deploy/prod` | **ветки нет** — workflow «ПРОДАКШЕН» ни разу не запускался |
| blazhevich.tech | заглушка Hostinger «Сайт готовится к запуску», не наш сайт |

Проверено на живом тесте 16.11.2026: страницы 200, заголовки на месте, шрифты `max-age=31536000, immutable`, картинки `max-age=2592000`, HTML `max-age=0`, `noindex` сохранён.

## 4. Что делать прямо сейчас

### 4.1 Ждём владельца (агент не может и не должен)

1. Cloudflare → Add a site → `blazhevich.tech`, план Free.
2. Перенести записи **по таблице из `DEPLOY.md` § Шаг 8** (она обновлена 16.11 по живым IP и включает `autoconfig`/`autodiscover`): A/AAAA apex, A `test`, CNAME `www` (серое облако), **MX ×2, SPF, DKIM ×2, DMARC** — без них умрёт почта на Hostinger.
3. Заменить NS у регистратора.
4. SSL/TLS → **Full (strict)**; Always Use HTTPS — вкл; Rocket Loader — не включать.
5. Cache Rules: «Bypass cache» для HTML, Edge TTL 1 месяц для `/assets/*`.
6. Секреты в GitHub для сброса кэша.

### 4.2 Что проверить агенту после переключения NS

```bash
curl -sI https://blazhevich.tech/ | grep -iE 'cache-control|cf-cache-status|strict-transport|server'
curl -sI https://blazhevich.tech/assets/hero-home.webp | grep -iE 'cache-control|cf-cache-status'
```

Ожидаемо: HTML — `cf-cache-status: DYNAMIC`, `cache-control: max-age=0`; картинка — со второго запроса `HIT`, `max-age=2592000`. Проверить: нет петли редиректов (`curl -IL`), тест остаётся `noindex`, 404 отдаёт `/404.html`, письма на домен ходят (MX не проксированы).

### 4.3 Запуск прода (делает владелец)

1. Actions → «ПРОДАКШЕН: публикация deploy/prod» → Run workflow. Первый запуск создаёт ветку `deploy/prod`.
2. hPanel → `blazhevich.tech` → Manage → Git: репозиторий, ветка `deploy/prod`, путь `domains/blazhevich.tech/public_html`, deploy-ключ.
3. Deploy в hPanel. После этого `blazhevich.tech` перестаёт быть заглушкой.

**До публикации:** Git-деплой **заменит `.htaccess` в `public_html`** на файл из репозитория. Если владелец добавлял туда свои правила — их нужно прислать и объединить заранее, иначе они потеряются.

**После публикации агенту:**

```bash
curl -sI https://blazhevich.tech/ | grep -iE 'cache-control|strict-transport|x-content-type'
curl -sI https://blazhevich.tech/404.html | head -1
curl -s https://blazhevich.tech/robots.txt
```

Ожидаемо: те же заголовки, что на тесте; 404 отдаётся; в `robots.txt` нет `noindex`,`Disallow`; в HTML есть `canonical` на `https://blazhevich.tech/`.

## 5. Обычный цикл

```powershell
cd D:\blazhevich-site
python build.py --release --domain https://blazhevich.tech --lastmod 2026-11-16
python tools\check_site.py          # 464 ссылки, 0 ошибок
$env:BLZ_DOMAIN='https://blazhevich.tech'; $env:BLZ_LASTMOD='2026-11-16'
python tools\test_v3.py             # repeat_build_identical: true
python build.py                     # черновик для теста
git add src assets ... ; git commit ; git push origin main
```

`--lastmod` — дата содержательной редакции, а не «сегодня». Сборка детерминированна (LF), `site/` и `TEST-RESULTS.json` в игноре.

## 6. Ловушки

- **Кэш хостинга.** LiteSpeed кэшировал HTML и отдавал страницу двухдневной давности. Теперь `CacheLookup off`, но при проверке теста всё равно открывать с `?cachebust=<метка>` или Ctrl+F5.
- **Новые файлы.** `V6-RESTORED-STYLE.md`, `assets/hero-home-restored.png` и `.zwork/` — рабочий мусор, не коммитить. `site/assets/hero-home-restored.png` в деплой не попадает (файл не в git), это нормально.
- **Nested `<section>`.** Если пишешь инструмент, который вырезает секцию из HTML, не режь регэкспом по первому `</section>` — внутри есть вложенные (`#about`).
- **Кэш ассетов.** Картинки кэшируются на 30 дней; заменяя файл, менять имя или добавлять `?v=2` в `src`.
- **`python` в этом окружении** — изолированный Python 3.13, папка скрипта не в `sys.path`; `build.py` это обходит сам.
- **`.htaccess` на проде.** Git-деплой заменяет файл целиком; пользовательские правила из `public_html` надо перенести в `.deploy/htaccess` до публикации.
- **Токен без scope `workflow`** — правки `.github/workflows/*` пуш не пройдёт. Логику деплоя менять только в `.github/scripts/*.sh`.

## 7. Что делать дальше по приоритету

1. **AVIF + `srcset`.** `hero-home.webp` 222 КБ на первый экран, снимки глав 100–115 КБ — AVIF даёт примерно вдвое меньше. (CSS в отдельный файл уже сделано — `50e138d`.)
2. **Поиск по нотам.** Убран 13.11, но `AGENTS.md` всё ещё его обещает — либо вернуть, либо поправить документацию.
3. **Микротипографика:** неразрывные пробелы после предлогов и перед тире, `text-wrap:pretty` для лидов.
4. **Биография:** в главах без снимка справа пустует ~320 px (третья колонка сетки). Решение за владельцем: оставить как печатное поле или центрировать пару «годы + текст».

## 8. Откат

- Любой шаг: `git revert <коммит>` + push в `main` → тест пересоберётся за 1–2 минуты.
- Прод: повторный запуск workflow «ПРОДАКШЕН» на нужном коммите.
- Если `.htaccess` уронит сайт в 500: `git revert 9fa6b89` и push; проверить `curl -sI https://test.blazhevich.tech/`.
