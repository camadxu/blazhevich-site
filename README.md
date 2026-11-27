# Blazhevich — сайт о Владиславе Блажевиче

Статический сайт о тромбонисте и педагоге Владиславе Михайловиче Блажевиче (1881–1942).
Многостраничный: русская и английская версии. База данных, PHP, Node.js и серверное
приложение не нужны — сборка это Python 3 (только стандартная библиотека), размещение —
любой веб-сервер статических файлов.

Адрес сайта: **https://blazhevich.tech**. Тест: **https://test.blazhevich.tech**.

## Структура

```
blazhevich-site/
├── build.py             сборщик (только стандартная библиотека Python 3)
├── enhancements.py      пост-обработка сборки (перенос 404, служебные правки)
├── 404.html             страница 404 (входит в сборку)
├── maintenance.html     заглушка «сайт временно закрыт» для режима 503
├── AGENTS.md            правила для ИИ-агентов: читать перед любой правкой
├── README.md            этот файл
├── src/                 исходники страниц и стилей
│   ├── style.css        все стили сайта
│   ├── script.js        весь скрипт сайта
│   ├── ru/*.html        русские страницы: hero, biography, works, listen, schools, about,
│   │                    досье moscow, leningrad, us-schools
│   └── en/*.html        английские: page.html (каркас витрин), досье moscow, leningrad, us-schools
├── assets/              изображения, шрифты (woff2), fonts.css, og-*.jpg
├── data/                реестр трудов works.json и «Полка» shelf.json (схема — works.md); выпуски «Ленты» data/news/
├── files/               ноты (PDF) прямых ссылок — только файлы из реестра
├── tools/               проверки (check_site, test_v3, test_maintenance), генераторы
│                        изображений (scenes/, media/, photo_tone), news_agent.py
├── docs/                документация и исследования: DEPLOY, PLAN, LIBRARY, TROMBONIST-PHOTOS,
│                        docs/research/ — ресёрши (Ленинград, «Блажевич в мире», источники ленты)
├── .deploy/htaccess     шаблон .htaccess для деплой-веток (404, 503-режим, 301, кэш, заголовки)
├── .github/             workflows (deploy-test — авто на push в main; deploy-prod — вручную)
│                        и scripts/publish-artifact.sh
└── site/                результат сборки (в репозитории не хранится)
```

Страницы: `index.html` — витрина (первый экран, вступление, биография полосой,
полоса «Школа и традиция», лента);
`works.html`, `listen.html`, `schools.html`, `about.html` — разделы;
`moscow.html`, `leningrad.html`, `us-schools.html` — досье «Школа и традиция».
Английские зеркала — `en/…`. Старые адреса (`scores.html`, `concertos.html`, `usa.html`,
`biography.html`, а также `en/scores`, `en/concertos`, `en/usa`) — переадресации.

## Сборка

Из корня репозитория, где лежит `build.py`:

```bash
python3 build.py --release --domain https://blazhevich.tech --lastmod ГГГГ-ММ-ДД   # публичная
python3 build.py                                                                   # черновик: noindex + плашка
```

Проверки после сборки (все обязаны пройти):

```bash
python3 tools/check_site.py
python3 tools/test_v3.py      # с теми же --release/--domain/--lastmod или через BLZ_DOMAIN/BLZ_LASTMOD
python3 tools/test_maintenance.py
```

Сборка детерминированна: повторный запуск с теми же аргументами даёт байт-в-байт тот же
результат (в том числе на Windows — сборщик принудительно пишет LF). `--lastmod` — дата
содержательной редакции, не механическая дата.

Генераторы изображений (`tools/scenes/*_scene.py`, `tools/media/make_og.py`,
`tools/photo_tone.py`) для сборки не нужны: нужны Pillow/numpy, запускаются вручную,
результат коммитится в `assets/`.

## Деплой

CI сам собирает и проверяет сайт: push в `main` публикует ветку `deploy/test`
(черновая сборка для test.blazhevich.tech), прод `deploy/prod` — только ручной
workflow «ПРОДАКШЕН», который запускает владелец. Хостинг забирает артефакт-ветки
сам по read-only deploy-ключу. Порядок подключения GitHub + Hostinger: `docs/DEPLOY.md`.
Правила работы для агентов, запреты и история решений: `AGENTS.md`.
