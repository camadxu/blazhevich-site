# BRASS-NEWS-SOURCES.md — источники для ежедневного новостного агента

Ресёрч от 16.11.2026 (валидация WebSearch/WebFetch, RSS проверены реальными запросами).
Назначение: конфиг мониторинга для «окна агента» — ежедневный дайджест по медным инструментам
(классика + джаз, RU + EN). Формат будущего конфига агента: source = {name, url, type: rss|scrape|search,
feed_url?, lang, instruments, genres}.

Правило архитектуры: **RSS-first** (бесплатно, безлимит) → scrape (Firecrawl, лимит) → site search
(Firecrawl/Tavily). Ключевые переносы доменов зашить в конфиг: `ita-web.org → trombone.net`,
`londonjazznews.com → ukjazznews.com`, `van-magazine.de → van-magazine.com`.

## A. Таблица по категориям

RSS ✓ = фид проверен реальным запросом (XML, свежие даты). «403 ботам» = фид/страница блокирует
автоматический доступ — брать через site search (Firecrawl/Tavily) или проверять в ридере.

### 1. Профессиональные ассоциации

| Источник | URL (раздел новостей) | RSS | Яз. | Покрытие | Свежесть | Примечания |
|---|---|---|---|---|---|---|
| ITA (trombone.net) | trombone.net/news | ✓ `https://trombone.net/feed` | EN | тромбон; конкурсы, назначения, фест | регулярные посты (последний 16.10.2026) | домен ita-web.org умер → trombone.net; бесплатно |
| ITG | trumpetguild.org/news | нет RSS | EN | труба, корнет, флюгельгорн | активен (09.11.2026) | пагинированный HTML; 256 страниц архива |
| IHS | hornsociety.org | WP-фид теоретически есть, сайт отдаёт 403 ботам | EN | валторна | активен (симпозиумы 2026/2027) | мониторить через site search; HornMatters практичнее |
| ITEA | iteaonline.org/category/news | WP `/feed` не проверен — сайт не отвечает >60 c | EN | туба, эуфониум | активен (окт–ноя 2026) | сайт крайне медленный; лучше site search + ретраи |
| 4barsrest | 4barsrest.com/news | ✓ `https://www.4barsrest.com/news/rss/news.xml` | EN | брасс-бэнды UK/EU | ежедневно (15–16.11.2026) | в фиде нет pubDate (только lastBuildDate); без пейволла |
| EBBA | ebba.eu.com/news | нет (403 ботам) | EN | европ. брасс-бэнды, EBBC | активен (2026–2028) | site search |

### 2. Классическая музыка

| Источник | URL | RSS | Яз. | Покрытие | Свежесть | Примечания |
|---|---|---|---|---|---|---|
| Slipped Disc | slippedisc.com | ✓ `https://slippedisc.com/feed` | EN | классика, люди, оркестры | ежедневно, неск. постов/день | лучший общий сигнал |
| The Strad | thestrad.com/news | нет RSS | EN | струнные+оркестр, классика | активен | JS-рендеринг; только site search; часть статей по подписке |
| Bachtrack | bachtrack.com/news | нет RSS | EN | классика/опера, концерты | активен (ноя 2026) | заголовки бесплатны; site search |
| Musical America | musicalamerica.com | нет RSS | EN | индустрия классики | активен (16.11.2026) | новости бесплатны; site search |
| Classical Music (Rhinegold) | classicalmusic.com | — | EN | классика | **ЗАКРЫТ** (март 2026) | в мёртвые |
| VAN Magazine | van-magazine.com | ✓ `https://van-magazine.com/feed` | EN/DE | классика, глубина, интервью | еженедельно (12.11.2026) | пейволл: 2 статьи/мес бесплатно |
| Gramophone | gramophone.co.uk/news | нет (403 ботам) | EN | классика, обзоры | активен | site search; частично пейволл |

### 3. Брасс-медиа

| Источник | URL | RSS | Яз. | Покрытие | Свежесть | Примечания |
|---|---|---|---|---|---|---|
| Last Row Music | lastrowmusic.com | ✓ `https://lastrowmusic.com/feed` | EN | все меди: вакансии, назначения, новые произведения | ежедневно | лучший специализированный агрегатор |
| HornMatters | hornmatters.com | ✓ `https://hornmatters.com/feed` | EN | валторна | нерегулярно, живой (07.11.2026) | блог John Ericson |
| TromboneChat | trombonechat.com | phpBB `/feed.php` — 403 ботам | EN | тромбон-форум | активен (ноябрь 2026) | 289k постов; site search (разделы Musicians, Performance) |
| TrumpetHerald | trumpetherald.com | `/feed.php` — 403 ботам | EN | труба-форум | активен | site search |
| The Brass Herald | thebrassherald.com | нет | EN | все меди | **STALE: последний выпуск 2019** | в мёртвые |
| euphonium.com | euphonium.com | — | EN | — | магазин нот (Shopify) | как новостной источник непригоден |
| IBEW | ibew.org.uk | нет | EN | брасс-бэнды | живой, но исторический блог | не новостной; референс |

### 4. Джаз

| Источник | URL | RSS | Яз. | Покрытие | Свежесть | Примечания |
|---|---|---|---|---|---|---|
| DownBeat | downbeat.com/news | нет RSS | EN | джаз | пачки ~еженедельно (10.11.2026) | бесплатно; site search |
| Jazzwise | jazzwise.com/news | нет (403 ботам) | EN | джаз UK | активен | site search |
| JazzTimes | jazztimes.com | `/feed` — 403 ботам | EN | джаз | возрождён 12.2024, активен | site search |
| UK Jazz News (экс-LondonJazz News) | ukjazznews.com | ✓ `https://ukjazznews.com/feed` | EN | джаз UK/мир | ежедневно (16.11.2026) | londonjazznews.com заморожен 10.2024, редирект |
| All About Jazz | allaboutjazz.com/news | каталог: allaboutjazz.com/jazz-rss-feeds | EN | джаз | активен | общий news-фид через каталог |
| The Jazz Line | news.jazzline.com | `/feed` заморожен (05.2024) | EN | джаз | STALE | в мёртвые |
| NPR Jazz | npr.org/music/genres/jazz | фид не найден (feeds.npr.org/10306 — 404) | EN | джаз | редакция сокращена (2023) | живее NPR Music на YouTube (UC4eYXhJI4-7wSWc8UNRwD4A) |
| Jazz.ru («Полный Джаз») | jazz.ru | ✓ `https://www.jazz.ru/feed/` | RU | джаз RU+мир | ежедневно/через день (16.11.2026) | без пейволла |
| Jazz-Квадрат | jazzquad.ru | `jazzquad.ru/sitemap.pl?act=RSS` | RU | джаз | нерегулярно (последний 16.11.2026) | наследник печатного «Джаз-Квадрата» |
| JazzPeople | jazzpeople.ru | нет RSS | RU | джаз СПб/Мск | активен (13.11.2026) | site search |

### 5. Русскоязычные

| Источник | URL | RSS | Яз. | Покрытие | Свежесть | Примечания |
|---|---|---|---|---|---|---|
| Музыкальное обозрение | muzobozrenie.ru | нет RSS | RU | классика РФ, конкурсы, фестивали | ежедневно (16.11.2026) | бесплатное; site search |
| ТАСС (Культура) | tass.ru/kultura | ✓ `https://tass.ru/rss/v2.xml` (общий поток, фильтровать) | RU | общие новости, вкл. культуру | реальное время | фильтр «духовой|тромбон|труба|валторна|оркестр» на стороне агента |
| РБК Стиль (Культура) | style.rbc.ru | RSS удалены (404) | RU | культура | активен | только site search |
| МГК им. Чайковского | mosconsv.ru «Новости» | нет RSS | RU | консерватория, концерты | активен (13.11.2026) | |
| СПбГК | conservatory.ru/news | нет RSS | RU | консерватория, конкурсы | активен (ноя 2026) | есть трубачьи конкурсы (им. Вурма) |
| Духовое общество им. Халилова | dukhovik.ru/novosti | нет RSS | RU | духовые оркестры, фестивали, все меди | еженедельно (15.11.2026) | лучший RU-ресурс про духовую сцену |
| Гос. духовой оркестр России | kremlinorchestra.ru (переименован в Гос. Кремлёвский оркестр) | нет | RU | духовой оркестр | непроверено | уточнить при интеграции |

### 6. Агрегаторы / соцсети / подкасты

| Источник | URL | RSS | Яз. | Покрытие | Свежесть | Примечания |
|---|---|---|---|---|---|---|
| Reddit r/trombone | reddit.com/r/trombone | ✓ `https://www.reddit.com/r/trombone/.rss` (Atom) | EN | тромбон | реальное время (16.11.2026) | |
| Reddit r/trumpet, r/horn, r/Tuba | reddit.com/r/{trumpet,horn,Tuba} | ✓ шаблон `https://www.reddit.com/r/<sub>/.rss` | EN | труба/валторна/туба | реальное время | |
| YouTube | `https://www.youtube.com/feeds/videos.xml?channel_id=<UC…>` | фид по channel_id | — | @CanadianBrass, @MnozilBrass, NPR Music | — | получить channel_id один раз, вписать в конфиг |
| The Brass Junkies | andrewhitz.com/pedal-note-media | фид подкаста | EN | все меди, интервью | пауза 2025; Season 3 — весна 2026 | не «ежедневный» источник |
| 4BR Podcast / That's Not Banding | 4barsrest.com/news | через RSS 4barsrest | EN | брасс-бэнды | активны (ноя 2026) | |

## B. TOP-15 для ежедневного агента

1. **Slipped Disc** — RSS `slippedisc.com/feed` — общеклассика, много брасса, ежедневно
2. **4barsrest** — RSS — брасс-бэнды ежедневно
3. **Last Row Music** — RSS — все меди, назначения/вакансии ежедневно
4. **ITA (trombone.net)** — RSS — ядро тромбонного мира
5. **ITG** trumpetguild.org/news — scrape ~2 раза/нед — ядро трубачей
6. **HornMatters** — RSS — валторна
7. **UK Jazz News** — RSS — джаз ежедневно
8. **VAN Magazine** — RSS — глубокая классика (пейволл 2/мес)
9. **Jazz.ru** — RSS — RU-джаз
10. **Музыкальное обозрение** — scrape muzobozrenie.ru — RU-классика ежедневно
11. **ТАСС** — RSS `tass.ru/rss/v2.xml` + фильтр инструментов
12. **dukhovik.ru/novosti** — scrape еженедельно — RU-духовая сцена
13. **Reddit r/trumpet + r/trombone + r/horn + r/Tuba** — RSS — сообщества
14. **DownBeat** — scrape downbeat.com/news еженедельно — джаз
15. **ITEA** — scrape iteaonline.org/category/news (медленный сайт — ретраи) — туба/эуфониум

Резерв: Bachtrack, jazzquad.ru, All About Jazz, TromboneChat.

## C. Черновик поисковых запросов (общие сайты → брасс-новости)

EN:
1. `"trombone" OR "trumpet" OR "tuba" OR "euphonium" OR "horn" news 2026`
2. `trombone OR tuba OR euphonium competition winner result`
3. `"brass band" championship results section`
4. `principal trumpet OR principal trombone appointment OR audition announced`
5. `new trombone concerto OR trumpet concerto OR horn concerto premiere`
6. `brass band OR trombone OR tuba obituary tribute died`
7. `jazz trumpeter OR trombonist new album interview`

RU:
8. `валторна OR тромбон OR туба OR труба концерт новость`
9. `духовой оркестр конкурс результаты фестиваль`
10. `солист туба OR тромбон OR валторна победитель международный конкурс`
11. `трубач джаз альбом премия интервью`
12. `премьера сочинение духовой оркестр корнет флюгельгорн`

## D. Мёртвые / не поддающиеся проверке (2026)

- **Classical Music (classicalmusic.com)** — закрыт в марте 2026.
- **The Jazz Line** — лента заморожена с мая 2024.
- **TubaNews (tubanews.com)** — сайт не отвечает; не индексируется.
- **The Brass Herald** — последний выпуск май 2019.
- **Brass Musician magazine (brassmusician.com)** — TLS сломан, недоступен.
- **«Джаз-Квадрат» (Минск, печатный)** — закрыт ~2009; наследник jazzquad.ru (в таблице).
- **трубач.рф** — не индексируется.
- **Musical Cosmos** — не существует.
- **NPR Jazz** — редакция сокращена 2023; профильного RSS нет.
- **ITA ita-web.org** — домен мёртв, замещён trombone.net.
- **IHS/ITEA/JazzTimes/Jazzwise/Gramophone/EBBA/TrumpetHerald/TromboneChat** — RSS не проверить
  из этой среды (403 ботам / таймауты): для агента надёжнее site search (Firecrawl/Tavily).
