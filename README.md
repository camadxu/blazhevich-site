# Blazhevich — сайт о Владиславе Блажевиче

Статический сайт о тромбонисте и педагоге Владиславе Михайловиче Блажевиче (1881–1942).
Шесть русских страниц и одна английская. База данных, PHP, Node.js и серверное приложение не нужны.
Для размещения достаточно любого веб-сервера, который отдаёт статические файлы: nginx, Apache, Caddy или S3-подобное хранилище.

## Состав архива

```
blazhevich-site/
├── START_HERE.md        короткое задание для ИИ-агента: как запустить сайт
├── README.md            этот файл
├── HANDOFF.md           что сделано, ограничения, оставшиеся задачи, выполненные проверки
├── build.py             сборщик (только стандартная библиотека Python 3)
├── src/                 исходники
│   ├── style.css        все стили (встраиваются в каждую страницу)
│   ├── script.js        весь скрипт (встраивается в каждую страницу)
│   ├── ru/*.html        русские разделы: hero, scores, listen, explore, biography, usa, schools, concertos, about
│   └── en/page.html     английская страница целиком
├── assets/              изображения, шрифты (woff2), fonts.css, картинка-превью og-image.jpg
├── tools/check_site.py  проверка собранного сайта: файлы, ссылки, якоря, внешние ресурсы
└── site/                ГОТОВЫЙ ПУБЛИЧНЫЙ САЙТ для https://blazhevich.space (см. ниже)
    ├── index.html  biography.html  usa.html  schools.html  concertos.html  about.html
    ├── en/index.html
    └── assets/          копия папки assets
```

| Страница | Содержание |
|---|---|
| `index.html` | первый экран, поиск по нотам, записи, карточки разделов |
| `biography.html` | биография, хронология, расхождения источников |
| `usa.html` | Блажевич в Америке |
| `schools.html` | московская и петербургская школы тромбона, Яков Райхман |
| `concertos.html` | 13 концертов для тромбона |
| `about.html` | о проекте и список источников (сноски [1]–[11] со всех страниц ведут сюда) |
| `en/index.html` | английская версия одной страницей (раздела о школах в ней нет) |

## Требования

* Для сборки нужен Python 3.8 или новее, без сторонних пакетов. Проверено на Python 3.13.
* Для размещения нужен любой веб-сервер статических файлов. HTTPS настраивается на сервере.
* Все пути внутри сайта относительные. Сайт можно размещать в корне домена или во вложенной папке. Canonical и sitemap при этом строятся от адреса, переданного в `--domain`. Для вложенной папки указывайте её полный адрес, например `--domain https://example.com/blazhevich`.

## Сборка

Команды выполняются из корня распакованного архива, из папки, где лежит `build.py`.

Основной адрес сайта: **https://blazhevich.space**. Папка `site/` в архиве уже собрана этой командой:

```bash
python3 build.py --release --domain https://blazhevich.space
```

Черновик (без индексации, с плашкой «не опубликовано»), если нужен для проверки:

```bash
python3 build.py
```

Для другого адреса (например, при переезде) подставьте его в `--domain` без косой черты в конце.

Сборщик каждый раз удаляет и заново создаёт папку `site/`, копируя в неё `assets/`.
Проверка после сборки:

```bash
python3 tools/check_site.py
```

## Размещение

1. Папка `site/` уже собрана для https://blazhevich.space. Если вы меняли исходники, пересоберите её командой выше.
2. Запустите `python3 tools/check_site.py` и убедитесь, что выведено «Режим: ПУБЛИЧНЫЙ» и «Ошибок не найдено».
3. Скопируйте **содержимое** папки `site/` в корень документов сайта на сервере, например так:

   ```bash
   rsync -av --delete site/ user@server:/var/www/blazhevich/
   ```

   Папки `src/`, `tools/` и файлы `build.py`, `README.md`, `HANDOFF.md` на сервер не нужны.
4. На сервере включите отдачу `index.html` по умолчанию для каталога (чтобы адрес `/en/` открывал `en/index.html`), HTTPS и перенаправление с http на https.
5. Пример для nginx:

   ```nginx
   server {
       listen 443 ssl;
       server_name blazhevich.space;
       # ssl_certificate / ssl_certificate_key — по настройкам вашего сервера
       root /var/www/blazhevich;
       index index.html;
       location / { try_files $uri $uri/ =404; }
       location /assets/ { expires 30d; add_header Cache-Control "public"; }
   }
   server {   # www → основной адрес
       listen 443 ssl;
       server_name www.blazhevich.space;
       return 301 https://blazhevich.space$request_uri;
   }
   server {   # http → https
       listen 80;
       server_name blazhevich.space www.blazhevich.space;
       return 301 https://blazhevich.space$request_uri;
   }
   ```

6. Если сайт размещается зеркалами на двух серверах, загрузите на оба одинаковую сборку с одним и тем же `--domain`, адресом основного сайта.
