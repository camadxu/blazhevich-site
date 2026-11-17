# Задание для ИИ-агента: запустить сайт blazhevich.space

Статический сайт о Владиславе Блажевиче (7 страниц: 6 русских и английская). База данных, PHP и Node.js не нужны.
Подробности: `README.md` (устройство, сборка, nginx) и `HANDOFF.md` (что сделано, ограничения, проверки).

## Что уже готово

Папка `site/` — **готовый публичный сайт для https://blazhevich.space**. Его можно загружать на сервер как есть.
Проверить, что он цел:

```bash
python3 tools/check_site.py
```

Ожидаемый результат: «Страниц: 7 из 7», «Режим: ПУБЛИЧНЫЙ», «canonical: https://blazhevich.space/», «Ошибок не найдено».

## Шаги запуска

1. Загрузить **содержимое** папки `site/` в корень документов сайта на сервере (например, `/var/www/blazhevich/`).
   В корне должны оказаться `index.html`, `biography.html`, `usa.html`, `schools.html`, `concertos.html`, `about.html`,
   папки `en/` и `assets/`, файлы `sitemap.xml` и `robots.txt`.
   Папки `src/`, `tools/` и файлы `build.py`, `*.md` на сервер **не** загружать.
2. Настроить веб-сервер (пример nginx — в `README.md`, раздел «Размещение»):
   * отдавать `index.html` для каталога (чтобы `https://blazhevich.space/en/` открывал `en/index.html`);
   * включить HTTPS для `blazhevich.space`;
   * постоянные перенаправления (301): `http://` → `https://blazhevich.space`, `www.blazhevich.space` → `https://blazhevich.space`.
3. Проверить после запуска:
   * открываются `https://blazhevich.space/`, `/biography.html`, `/usa.html`, `/schools.html`, `/concertos.html`, `/about.html`, `/en/`;
   * `https://blazhevich.space/robots.txt` и `/sitemap.xml` отдаются;
   * картинка `https://blazhevich.space/assets/og-image.jpg` открывается (превью в Telegram);
   * на главной работает поиск по нотам (например, «туба» — 4 карточки).
4. По желанию владельца: добавить сайт в Яндекс Вебмастер и Google Search Console, указать `https://blazhevich.space/sitemap.xml`.

## Ограничения для агента

* Домен и DNS подключает владелец. Ничего не покупать и не менять DNS без отдельного поручения.
* Тексты, источники и оформление не менять без поручения владельца.
* Секретов и паролей в проекте нет; доступы к серверу запрашивать у владельца.

## Если нужно пересобрать (например, после правки текста)

Нужен Python 3.8+ без дополнительных пакетов. Из этой папки:

```bash
python3 build.py --release --domain https://blazhevich.space
python3 tools/check_site.py
```

Тексты лежат в `src/ru/*.html` и `src/en/page.html`, стили в `src/style.css`, скрипт в `src/script.js`.
