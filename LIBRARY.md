# Своя база нот и записей (заготовка, 15.11.2026)

Решение владельца: сайт опирается в первую очередь на собственную базу нот и записей, внешние источники идут рядом как дополнительные ссылки. Файлов пока нет: владелец положит их позже, когда появится сервер для хранения. Вёрстка уже готова их принять. Чужие файлы без решения владельца не размещать.

## Куда класть

- `assets/library/scores/` — ноты (PDF);
- `assets/library/audio/` — записи (MP3 или M4A);
- `assets/library/video/` — видео (MP4) и кадр-заставка (WebP).

Имена латиницей, без пробелов: `school-in-clefs-1939.pdf`, `concerto-02-lambert-2020.mp3`. Если файлы будут лежать на отдельном сервере, вместо `assets/library/...` ставится полный адрес; тогда `tools/check_site.py` нужно научить пропускать этот домен.

## Ноты: карточка в `src/ru/scores.html` и `src/en/page.html`

Первой строкой низа карточки идёт свой файл, второй, мельче, внешний источник:

```html
<a class="card-file" href="assets/library/scores/school-in-clefs-1939.pdf">Открыть ноты (PDF)</a>
<a href="https://…">История изданий</a>
```

Знак «↗» у внешней ссылки ставит CSS. Карточки лежат на полках (`.shelf`): школы, этюды и упражнения, ансамбли, концерты; у каждой полки свой оттенок бумаги.

## Записи: строка в `src/ru/listen.html` и `src/en/page.html`

Внутри `.record-body` перед списком ссылок:

```html
<audio controls preload="none" src="assets/library/audio/concerto-02-lambert-2020.mp3"></audio>
```

Слева в `.record-head` стоят исполнитель, школа и год. `preload="none"`: файл не качается, пока посетитель не нажал «играть».

## Видео: подраздел «Видео» в «Слушать»

```html
<li><video controls preload="none" poster="assets/library/video/batashev-1972.webp" src="assets/library/video/batashev-1972.mp4"></video>
    <a href="https://www.youtube.com/…"><b>Название</b><span>Исполнитель, год · <span class="ext">YouTube</span></span></a></li>
```

YouTube и другие площадки остаются обычными ссылками рядом. Встроенные плееры YouTube не ставить: в России он не открывается.
