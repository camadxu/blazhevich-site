"""Сборка сайта Blazhevich.

  python3 build.py                                   черновик: noindex, плашка «не опубликовано»
  python3 build.py --release --domain https://site   публичная версия: индексация, canonical,
                                                     Open Graph с полными адресами, sitemap.xml, robots.txt

Результат в папке site/: index.html — витрина (первый экран, вступление, разделы,
короткий вход в «Школу и традицию», лента новостей), страницы разделов works.html,
listen.html, biography.html, schools.html, about.html, досье moscow.html, leningrad.html,
us-schools.html и английские зеркала всех страниц в en/. Старые адреса разделов
(scores.html, en/scores.html, concertos.html, usa.html) остаются страницами-переадресациями.
Эту папку целиком загружают на хостинг.
Для зеркал (РФ и США) собирайте обе копии с одним --domain — адресом основного сайта.
С флагом --single-page дополнительно собирается artifact.html — вся русская версия одной
страницей (нужна только для предпросмотра в Claude, на сервер не загружается; шрифты берёт с Google Fonts).
"""
import argparse, atexit, datetime, hashlib, html, json, pathlib, re, shutil, time

ROOT = pathlib.Path(__file__).parent

# Кросс-платформенная детерминированность сборки: текстовые файлы всегда пишутся с LF,
# чтобы сборка на Windows была байт-в-байт равна сборке на Linux — это нужно для сверки
# с опубликованной версией и повторяемости проверок. По умолчанию write_text на Windows
# переводит \n в CRLF, из-за чего собранные файлы отличались от живого сайта.
import sys as _sys
if _sys.version_info >= (3, 10):
    _write_text_orig = pathlib.Path.write_text
    def _write_text_lf(self, data, *args, **kwargs):
        kwargs.setdefault('newline', '\n')
        return _write_text_orig(self, data, *args, **kwargs)
    pathlib.Path.write_text = _write_text_lf

SRC = ROOT / 'src'
ap = argparse.ArgumentParser()
ap.add_argument('--release', action='store_true')
ap.add_argument('--domain', default='')
ap.add_argument('--lastmod', default='', help='optional YYYY-MM-DD content revision date')
ap.add_argument('--news-dir', default='', help='папка с выпусками ленты (по умолчанию data/news)')
ap.add_argument('--single-page', action='store_true', help='дополнительно собрать artifact.html (предпросмотр)')
a = ap.parse_args()
DOM = a.domain.rstrip('/')
if a.release and not DOM:
    raise SystemExit('Для --release нужен --domain, например --domain https://blazhevich.ru')

CSS = (SRC / 'style.css').read_text()
JS = (SRC / 'script.js').read_text()
EXTRA_CSS = ""  # всё оформление в src/style.css
CSS = CSS + EXTRA_CSS
# Стили живут отдельным файлом с хэшем содержимого в имени: страницы не таскают стили при каждом
# переходе, а .deploy/htaccess кэширует такой файл навсегда (immutable). Инлайн остаётся только
# в artifact.html — он собирается одним файлом для предпросмотра вне сайта.
CSS_FILE = 'main.' + hashlib.sha256(CSS.encode('utf-8')).hexdigest()[:10] + '.css'
# Шрифтовой CSS тоже с хэшем: text/css кэшируется на сутки, а старые имена шрифтов после
# чистки дублей исчезают — версия в имени избавляет от 404 у тех, у кого старый CSS в кэше.
FONTS_CSS = (ROOT / 'assets' / 'fonts.css').read_text()
FONTS_FILE = 'fonts.' + hashlib.sha256(FONTS_CSS.encode('utf-8')).hexdigest()[:10] + '.css'
# Картинки кэшируются браузером на 30 дней (см. .deploy/htaccess), а имена у них постоянные.
# Версия от имён и содержимого assets даёт новый адрес при любой замене файла,
# в том числе когда новый файл имеет тот же размер.
_asset_hash = hashlib.sha256()
_assets = sorted(((q.relative_to(ROOT / 'assets').as_posix(), q)
                  for q in (ROOT / 'assets').rglob('*') if q.is_file()), key=lambda item: item[0])
for _asset_name, _asset in _assets:
    _asset_hash.update(_asset_name.encode('utf-8'))
    _asset_hash.update(b'\0')
    _asset_hash.update(_asset.read_bytes())
    _asset_hash.update(b'\0')
ASSET_VER = _asset_hash.hexdigest()[:8]
_ASSET_RE = re.compile(r'((?:\.\./)?assets/[A-Za-z0-9_./-]+\.(?:webp|png|jpg|jpeg|svg))(?=["\s,)\\])')
def asset_urls(html):
    """К адресам картинок добавляется ?v=<версия>, чтобы кэш не показывал старый снимок."""
    return _ASSET_RE.sub(lambda m: m.group(1) + '?v=' + ASSET_VER, html)

FONTS_GOOGLE = ('<link rel="preconnect" href="https://fonts.googleapis.com">\n'
                '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
                '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,500;0,600;1,500&family=Onest:wght@400;600&display=swap">')
FAVICON = ("<link rel=\"icon\" href=\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E%3Crect width='64' height='64' rx='14' fill='%23e8dbbf'/%3E%3Ctext x='32' y='46' text-anchor='middle' font-family='Georgia,serif' font-weight='600' font-size='40' fill='%232a2118'%3EB%3C/text%3E%3C/svg%3E\">")

def sec(name, lang='ru'):
    return (SRC / lang / f'{name}.html').read_text()

# ---------------- Русские страницы ----------------
# «Труды» собираются из src/ru/works.html (контентёр волны hub-pages). Пока файла нет,
# действует временный фолбэк волны: страница клеится из концертов и каталога нот.
WORKS_SECS = ['works'] if (SRC / 'ru' / 'works.html').exists() else ['concertos', 'scores']
PAGES = {  # файл: (секции, заголовок, описание)
    'index.html': (['hero'],
                   'Blazhevich — Владислав Блажевич: тромбон, ноты, история',
                   'Владислав Блажевич (1881–1942): ноты, записи, биография, 13 концертов для тромбона, школы тромбона и признание в США.'),
    'works.html': (WORKS_SECS, 'Труды Блажевича — концерты, школы, этюды',
                   '13 концертов для тромбона, «Школа игры», этюды и ансамбли: каталог трудов Владислава Блажевича со ссылками на ноты.'),
    'listen.html': (['listen'], 'Слушать Блажевича — записи и видео',
                    'Аудиозаписи и видео произведений Владислава Блажевича.'),
    'biography.html': (['biography'], 'Владислав Блажевич — биография: жизнь, оркестр, Вязьма',
                       'Биография Владислава Блажевича: детство на Смоленщине, Большой театр, Московская консерватория, Государственный духовой оркестр СССР и Вязьма.'),
    'schools.html': (['schools'], 'Школа и традиция — две школы русского тромбона',
                     'Московская и ленинградская школы тромбона и их досье: Москва, Петербург, американская линия.'),
    'about.html': (['about'], 'О проекте — Blazhevich',
                   'Источники, права на изображения и принципы работы сайта.'),
    'moscow.html': (['moscow'], 'Московская тромбоновая школа — Blazhevich',
                    'Московская школа тромбона: Витнебен, Борк, Блажевич, Щербинин и его ученики, гнесинская ветвь, ноты и записи.'),
    'leningrad.html': (['leningrad'], 'Ленинградская тромбоновая школа — Blazhevich',
                       'Петербургско-ленинградская школа тромбона: Тюрнер, Волков, Козлов, Венгловский, Квартет тромбонов филармонии, дискография.'),
    'us-schools.html': (['us-schools'], 'Американские школы тромбона — Blazhevich',
                        'Истмен и Ремингтон, Чикаго и Джейкобс, Curtis и Алесси, Northwestern: как устроены американские тромбоновые школы и чем они похожи на московскую и ленинградскую.'),
}
# реестр пяти разделов (порядок 01–05): меню шапки, витрина и пейджер; третья колонка — подпись в списке разделов
HUB_RU = [('works', 'Труды', 'Каталог: 13 концертов, школы, этюды и ансамбли — со ссылками на ноты'),
          ('listen', 'Слушать', 'Записи и видео: как его музыка звучит сегодня'),
          ('biography', 'Биография', 'Москва, Большой театр, консерватория — по документам и источникам'),
          ('schools', 'Школа и традиция', 'Две школы русского тромбона и досье: Москва, Петербург, Америка'),
          ('about', 'О проекте', 'Источники, права на изображения и принципы работы')]
NAV_RU = [(i, t) for i, t, _ in HUB_RU]
# английские зеркала есть у всех страниц, кроме витрины (у неё — en/index.html)
EN_TWINS = {'works.html', 'listen.html', 'biography.html', 'schools.html', 'about.html',
            'moscow.html', 'leningrad.html', 'us-schools.html'}
# досье-подстраницы: крошка ведёт на родительский раздел, в меню подсвечен он же
PARENT_RU = {f: ('schools', 'Школа и традиция') for f in ('moscow.html', 'leningrad.html', 'us-schools.html')}
# английские досье: src/en/<имя>.html → en/<имя>.html (заголовок, описание)
EN_DOSSIERS = {
    'moscow.html': ('The Moscow trombone school — Blazhevich',
                    'The Moscow trombone school: Wittneben, Bork, Blazhevich, Shcherbinin and his pupils, the Gnesin branch, scores and recordings.'),
    'leningrad.html': ('The Leningrad trombone school — Blazhevich',
                       'The St. Petersburg–Leningrad trombone school: Türner, Volkov, Kozlov, Venglovsky, the Philharmonic Trombone Quartet, discography.'),
    'us-schools.html': ('American trombone schools — Blazhevich',
                        'Eastman and Remington, Chicago and Jacobs, Curtis and Alessi, New York and Northwestern: how American trombone schools are organised and how they compare with Moscow and Leningrad.'),
}
PAGE_OF_SECTION = {s: f for f, (ss, _, _) in PAGES.items() for s in ss}

def ids_in(html):
    return set(re.findall(r'\bid="([\w-]+)"', html))

def relink(html, page, id_page, old_map=None):
    """#id → нужная страница: якорь своей страницы остаётся, чужой становится page.html#id;
    старые якоря одностраничника (#scores, #usa, …) разводятся по словарю old."""
    here = ids_in(html)
    def fix(m):
        i = m.group(1)
        if i in here:
            return m.group(0)
        tgt = id_page.get(i)
        if tgt:
            if i == tgt[1] and tgt[0] != 'index.html':   # главная секция страницы → просто страница
                return f'href="{tgt[0]}"'
            return f'href="{tgt[0]}#{i}"'
        legacy = (old_map or {}).get(i)   # старые якоря одностраничника (#scores, #usa, …)
        return f'href="{legacy}"' if legacy else m.group(0)
    def fix_idx(m):
        pre, i = m.group(1), m.group(2)   # зашитые ссылки времён одностраничника: index.html#id и ../index.html#id
        if i in here:
            return f'href="{pre}#{i}"' if pre else m.group(0)
        tgt = id_page.get(i)
        if tgt:
            if i == tgt[1] and tgt[0] != 'index.html':
                return f'href="{pre}{tgt[0]}"'
            return f'href="{pre}{tgt[0]}#{i}"'
        legacy = (old_map or {}).get(i)
        return f'href="{pre}{legacy}"' if legacy else m.group(0)
    html = re.sub(r'href="#([\w-]+)"', fix, html)
    return re.sub(r'href="((?:\.\./)?)index\.html#([\w-]+)"', fix_idx, html)

DRAFT = '' if a.release else '<div class="draft">Предварительный просмотр · не опубликовано</div>\n'

def header(nav_html, lang_link, home, hero_page=False, skip_text='Перейти к содержимому'):
    bar_cls = ' class="on-hero"' if hero_page else ''   # витрина: шапка стоит под первым экраном
    return (f'<a class="skip" href="#main">{skip_text}</a>\n' + DRAFT
            + f'<header id="top-bar"{bar_cls}><div class="wrap bar">\n  <a href="{home}" class="brand" aria-label="Blazhevich — на главную">Blazhevich</a>\n'
            f'  <nav aria-label="Основная навигация">{nav_html}{lang_link}</nav>\n</div></header>\n')

# архивная виньетка в шапке раздела: декоративная (alt=""), источники снимков — в «О проекте»
VIGNETTE = {'works': 'v-conservatory-portico.webp', 'listen': 'v-bolshoi-colonnade.webp',
            'concertos': 'bolshoi-1905.webp', 'schools': 'conservatory-1940s.webp'}
# размеры файлов виньеток: с width/height браузер резервирует место до загрузки, вёрстка не прыгает
VIGNETTE_WH = {'v-conservatory-portico.webp': (420, 490), 'v-bolshoi-colonnade.webp': (470, 460),
               'conservatory-1940s.webp': (960, 600), 'bolshoi-1905.webp': (960, 600)}
def vignette(v, prefix=''):
    w, h = VIGNETTE_WH[v]
    return (f'<figure class="head-vignette" aria-hidden="true"><img src="{prefix}assets/{v}" alt="" '
            f'width="{w}" height="{h}" loading="lazy" decoding="async"></figure>')
# сцена во всю ширину с текстом поверх (assets/scene-*.webp делает tools/scenes/*.py)
SCENE = {'moscow', 'leningrad'}

def inner(h, crumb, href='index.html', prefix=''):
    """На внутренней странице заголовок секции становится h1 с «хлебной крошкой»."""
    sid = re.match(r'\s*<section id="([\w-]+)"', h)
    v = VIGNETTE.get(sid.group(1)) if sid else None
    fig = vignette(v, prefix) if v else ''
    cls = f' scene scene-{sid.group(1)}' if sid and sid.group(1) in SCENE else ''
    # url() во встроенном CSS считается от страницы: из папки en/ картинку сцены даём с префиксом
    sty = (f' style="--scene:url({prefix}assets/scene-{sid.group(1)}.webp);--scene-sm:url({prefix}assets/scene-{sid.group(1)}-960.webp)"'
           if cls and prefix else '')
    h = h.replace('<div class="section-head">',
                  f'<div class="section-head{cls}"{sty}><a class="crumb" href="{href}">← {crumb}</a>{fig}', 1)
    return re.sub(r'<h2>(.*?)</h2>', r'<h1 class="page-title">\1</h1>', h, count=1)

def deco(h, prefix=''):
    """Раздел на общей странице: заголовок остаётся h2, справа — архивная виньетка."""
    sid = re.match(r'\s*<section id="([\w-]+)"', h)
    v = VIGNETTE.get(sid.group(1)) if sid else None
    if not v:
        return h
    fig = vignette(v, prefix)
    return re.sub(r'(<div class="section-head"[^>]*>)', lambda m: m.group(1) + fig, h, count=1)

def home_sections(lang):
    """Тихий список разделов и короткий вход в «Школу» на витрине."""
    ru = lang == 'ru'
    if ru:
        heading = 'Разделы'
        rows = (('works.html', 'Труды', '13 концертов, школы, этюды, ансамбли'),
                ('listen.html', 'Слушать', 'записи и видео'),
                ('biography.html', 'Биография', 'жизнь, оркестр, Вязьма'),
                ('schools.html', 'Школа и традиция', 'Москва, Ленинград, Америка'),
                ('about.html', 'О проекте', 'источники и принципы'))
        school_heading = 'Школа и традиция'
        school_text = ('Тромбоновую школу России выучили Москва и Петербург — консерватория, Большой театр, '
                       'военные оркестры. После войны её подхватила Америка: ученики и внуки учеников играют '
                       'и преподают по обе стороны океана.')
        school_link = 'Школа и традиция →'
    else:
        heading = 'Sections'
        rows = (('works.html', 'Works', 'The 13 concertos, schools, studies, ensembles'),
                ('listen.html', 'Listen', 'Recordings and video'),
                ('biography.html', 'Biography', 'Life, the state orchestra, Vyazma'),
                ('schools.html', 'School & Tradition', 'Moscow, Leningrad, America'),
                ('about.html', 'About', 'Sources and principles'))
        school_heading = 'School & Tradition'
        school_text = ("Russia's trombone school was shaped by Moscow and Saint Petersburg — the conservatory, "
                       "the Bolshoi Theatre, the military orchestras. After the war, America carried it on: "
                       "Blazhevich's students and their students play and teach on both sides of the ocean.")
        school_link = 'School & Tradition →'
    items = ''.join(f'    <li><a href="{href}"><span class="section-name">{title}</span><span class="section-summary">{summary}</span></a></li>\n'
                    for href, title, summary in rows)
    return (f'<section class="block home-sections" aria-labelledby="home-sections-title"><div class="wrap">\n'
            f'  <div class="section-head"><h2 id="home-sections-title">{heading}</h2></div>\n'
            f'  <ul class="section-list">\n{items}  </ul>\n'
            f'</div></section>\n'
            f'<section class="block home-school" aria-labelledby="home-school-title"><div class="wrap">\n'
            f'  <div class="section-head"><h2 id="home-school-title">{school_heading}</h2><p>{school_text}</p></div>\n'
            f'  <a class="school-entry-link" href="schools.html">{school_link}</a>\n'
            f'</div></section>\n')

def pager(page_id, lang, prefix=''):
    """Пейджер разделельной страницы: ← предыдущий · все разделы · следующий → (порядок 01–05)."""
    ru = lang == 'ru'
    hub = HUB_RU if ru else EN_HUB
    idx = next((i for i, item in enumerate(hub) if item[0] == page_id), None)
    if idx is None:
        raise ValueError(f'Нет раздела {page_id!r} в хабе {lang}')
    T = ('Все разделы', 'Переход между разделами') if ru else ('All sections', 'Section navigation')
    links = ''
    if idx > 0:
        p = hub[idx - 1]
        links += f'<a class="pg-way" rel="prev" href="{prefix}{p[0]}.html">← {p[1]}</a>'
    links += f'<a class="pg-all" href="{prefix}index.html">{T[0]}</a>'
    if idx < len(hub) - 1:
        n_ = hub[idx + 1]
        links += f'<a class="pg-way" rel="next" href="{prefix}{n_[0]}.html">{n_[1]} →</a>'
    return f'<nav class="pager wrap" aria-label="{T[1]}">{links}</nav>\n'

# ---------------- База файлов (этап 1): реестр трудов и загрузки ----------------
FILES_BASE = ''   # адрес файлового сервера; пока пусто — пути files/… отдаются как есть
WORKS_REGISTRY_PATH = ROOT / 'data' / 'works.json'
WORKS_REGISTRY = json.loads(WORKS_REGISTRY_PATH.read_text(encoding='utf-8')) if WORKS_REGISTRY_PATH.exists() else []
WORK_TYPE = {'concert': ('Концерт', 'Concert'), 'school': ('Школа', 'School'), 'etudes': ('Этюды', 'Studies'),
             'ensemble': ('Ансамбль', 'Ensemble'), 'arrangement': ('Обработка', 'Arrangement')}

def validate_works(registry):
    """Реестр трудов не молча ломает страницу: битая запись падает сборкой с понятной ошибкой."""
    seen = set()
    for w in registry:
        wid = w.get('id', '')
        if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', wid):
            raise SystemExit(f'data/works.json: bad id {wid!r} (нужен латинский slug)')
        if wid in seen:
            raise SystemExit(f'data/works.json: дублируется id {wid!r}')
        seen.add(wid)
        if not w.get('title'):
            raise SystemExit(f'data/works.json: у записи {wid!r} нет title')
        if w.get('type') not in WORK_TYPE:
            raise SystemExit(f'data/works.json: у записи {wid!r} тип {w.get("type")!r} не из WORK_TYPE')
        for field in ('notes_url', 'parts_url', 'audio_url'):
            url = w.get(field)
            if not url:
                continue
            if isinstance(url, list):
                urls = url
            else:
                urls = [url]
            for u in urls:
                if not (ROOT / u).exists():
                    raise SystemExit(f'data/works.json: {wid!r} указывает на {field}={u!r}, файла нет')
        if any(w.get(f) for f in ('notes_url', 'parts_url', 'audio_url')) and not w.get('origin'):
            raise SystemExit(f'data/works.json: у записи {wid!r} есть файлы, но нет origin (откуда файл)')

validate_works(WORKS_REGISTRY)

def files_block(lang, prefix=''):
    """Блок «Файлы для скачивания» на странице «Труды»: рендерится из data/works.json."""
    rows = [w for w in WORKS_REGISTRY if w.get('notes_url') or w.get('audio_url')]
    if not rows:
        return ''
    ru = lang == 'ru'
    e = lambda t: html.escape(str(t), quote=True)
    T = (('Файлы для скачивания', 'Локальная база нот и аудио',
          'Файлы хранятся в собственной базе проекта и отдаются напрямую; записи появляются здесь по мере наполнения реестра.',
          'Партитура (PDF)', 'Аудио', 'Источник файла') if ru else
         ('Downloads', 'The local score and audio base',
          'The files live in the project’s own base and are served directly; entries appear here as the registry grows.',
          'Score (PDF)', 'Audio', 'File origin'))
    items = ''
    for w in rows:
        kind = WORK_TYPE.get(w.get('type'), ('', ''))[0 if ru else 1]
        title = w.get('title') if ru else (w.get('title_en') or w.get('title', ''))
        note = w.get('comment') if ru else (w.get('comment_en') or w.get('comment', ''))
        origin = w.get('origin') if ru else (w.get('origin_en') or w.get('origin', ''))
        year = f' <span class="tag">{e(w["year"])}</span>' if w.get('year') else ''
        links = ''
        if w.get('notes_url'):
            links += f'<a href="{e((FILES_BASE + w["notes_url"]) if FILES_BASE else (prefix + w["notes_url"]))}">{T[3]}</a>'
        if w.get('audio_url'):
            links += f'<a href="{e((FILES_BASE + w["audio_url"]) if FILES_BASE else (prefix + w["audio_url"]))}">{T[4]}</a>'
        items += (f'    <li class="file-row"><p class="file-name"><b>{e(title)}</b>'
                  + (f' <span class="tag">{e(kind)}</span>' if kind else '') + year + '</p>'
                  + (f'<p>{note}</p>' if note else '')
                  + (f'<p>{T[5]}: {e(origin)}</p>' if origin else '')
                  + (f'<p class="file-links">{links}</p>' if links else '') + '</li>\n')
    return ('<section id="files" class="block files-block" aria-labelledby="files-title"><div class="wrap">\n'
            f'  <div class="section-head"><h2 id="files-title">{T[0]}</h2><div class="eyebrow">{T[1]}</div><p>{T[2]}</p></div>\n'
            f'  <ul class="files-list">\n{items}  </ul>\n'
            '</div></section>\n')

def stub(target, title, lang):
    """Старый адрес раздела → раздел общей страницы."""
    return ('<!doctype html>\n'
            f'<html lang="{lang}">\n<head>\n<meta charset="utf-8">\n<meta name="robots" content="noindex,follow">\n'
            f'<meta http-equiv="refresh" content="0; url={target}">\n<title>{title}</title>\n</head>\n<body>\n'
            f'<p><a href="{target}">{title}</a></p>\n</body>\n</html>\n')

EN_WORDS = [('Перейти к содержимому', 'Skip to content'), ('Основная навигация', 'Main navigation'), ('на главную', 'home'),
            ('Предварительный просмотр · не опубликовано', 'Preview · not published')]
def en_words(html):
    for ru, en_ in EN_WORDS:
        html = html.replace(ru, en_)
    return html

def site_footer(lang):
    """Подвал: имя и годы, разделы, досье школ, язык. Ссылки с адресом страницы — подвал общий для витрины, разделов и досье."""
    ru = lang == 'ru'
    nav = NAV_RU if ru else [(i, t) for i, t, _ in EN_HUB]

    def nav_href(i):
        pages = PAGES if ru else EN_PAGES
        if f'{i}.html' in pages:                 # настоящая страница раздела
            return f'{i}.html'
        return f'index.html#{i}'

    secs = ''.join(f'<li><a href="{nav_href(i)}">{t}</a></li>' for i, t in nav)
    T = (dict(who='Владислав Блажевич', about='Тромбонист, педагог, композитор. Независимый проект о его жизни, нотах и школе.',
              s='Разделы', d='Школы тромбона', m='Московская тромбоновая школа', l='Ленинградская тромбоновая школа', u='Американские школы',
              o='Язык', other='<a href="en/index.html" hreflang="en" lang="en">English version</a>',
              fine='Источники и права на изображения указаны в разделе <a href="about.html">«О проекте»</a>.', top='Наверх', nav='Подвал')
         if ru else
         dict(who='Vladislav Blazhevich', about='Trombonist, teacher, composer. An independent project about his life, scores and school.',
              s='Sections', d='Trombone schools', m='The Moscow trombone school', l='The Leningrad trombone school', u='American schools',
              o='Language', other='<a href="../index.html" hreflang="ru" lang="ru">Русская версия</a>',
              fine='Sources and image credits are listed under <a href="about.html">About</a>.', top='Back to top', nav='Footer'))
    return ('<footer><div class="wrap foot">\n'
            f'  <div class="foot-id"><a href="index.html" class="brand">Blazhevich</a><p class="foot-name">{T["who"]} <span>1881–1942</span></p><p>{T["about"]}</p></div>\n'
            f'  <div class="foot-col" role="navigation" aria-label="{T["nav"]}"><h2>{T["s"]}</h2><ul class="foot-secs">{secs}</ul></div>\n'
            f'  <div class="foot-col"><h2>{T["d"]}</h2><ul><li><a href="moscow.html">{T["m"]}</a></li><li><a href="leningrad.html">{T["l"]}</a></li><li><a href="us-schools.html">{T["u"]}</a></li></ul>'
            f'<h2>{T["o"]}</h2><ul><li>{T["other"]}</li></ul></div>\n'
            f'  <p class="foot-fine">{T["fine"]}</p>\n'
            '</div></footer>\n')

# ---- типографика русских страниц ----
_NB = ' '
_SHORT = re.compile(r'(?<![\w-])(в|во|к|ко|с|со|о|об|у|и|а|на|по|из|за|от|до|не|ни|но) (?=\S)', re.I)
def typo(html):
    """Неразрывные пробелы в русском тексте: после коротких предлогов и союзов, после №, между инициалами,
    перед тире и между числом и словом «год/лет» — чтобы строка не кончалась на «в», «и», «№» или «1905». Теги не трогаются."""
    def fix(t):
        t = t.replace('№ ', '№' + _NB)
        t = re.sub(r'(?<![А-Яа-яЁё])([А-ЯЁ]\.) (?=[А-ЯЁ])', r'\1' + _NB, t)
        t = re.sub(r'(\d) (год[а-я]{0,2}|лет|г\.|гг\.)(?![а-яё])', r'\1' + _NB + r'\2', t)
        t = _SHORT.sub(lambda m: m.group(1) + _NB, t)
        return t.replace(' —', _NB + '—')
    return ''.join(x if x.startswith('<') else fix(x) for x in re.split(r'(<[^>]+>)', html))

FOOTER_RU = lambda: site_footer('ru')
FOOTER_EN = lambda: site_footer('en')

# ---------------- JSON-LD: разметка для поисковиков (только в публичной сборке, адреса абсолютные) ----------------
PERSON_SAME_AS = ['https://ru.wikipedia.org/wiki/Блажевич,_Владислав_Михайлович',
                  'https://en.wikipedia.org/wiki/Vladislav_Blazhevich',
                  'https://imslp.org/wiki/Category:Blazhevich,_Vladislav']
CRUMBS = {  # страница: цепочка «хлебных крошек» (подпись, адрес от корня сайта)
    'moscow.html': [('Главная', ''), ('Школа и традиция', 'schools.html'), ('Московская тромбоновая школа', 'moscow.html')],
    'leningrad.html': [('Главная', ''), ('Школа и традиция', 'schools.html'), ('Ленинградская тромбоновая школа', 'leningrad.html')],
    'us-schools.html': [('Главная', ''), ('Школа и традиция', 'schools.html'), ('Американские школы тромбона', 'us-schools.html')],
    'en/moscow.html': [('Home', 'en/'), ('The school and its lineage', 'en/schools.html'), ('The Moscow trombone school', 'en/moscow.html')],
    'en/leningrad.html': [('Home', 'en/'), ('The school and its lineage', 'en/schools.html'), ('The Leningrad trombone school', 'en/leningrad.html')],
    'en/us-schools.html': [('Home', 'en/'), ('The school and its lineage', 'en/schools.html'), ('American trombone schools', 'en/us-schools.html')],
}
_plain = lambda t: re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', t)).strip()

def concerto_rows(lang):
    """Номер, тональность и дата каждого концерта — из таблицы раздела «Труды», чтобы разметка не расходилась с текстом."""
    if lang == 'ru':
        src = ''.join(sec(s) for s in PAGES['works.html'][0])
    else:
        src = ''.join(en_secs[s] for s in EN_PAGES['works.html'][0])
    body = re.search(r'<table class="conc">.*?<tbody>(.*?)</tbody>', src, re.S).group(1)
    return [tuple(_plain(c) for c in re.findall(r'<td>(.*?)</td>', r, re.S)[:3]) for r in re.findall(r'<tr>(.*?)</tr>', body, re.S)]

def jsonld(path, lang, url, title, desc):
    ru = lang == 'ru'
    person = {'@type': 'Person', '@id': f'{DOM}/#blazhevich',
              'name': 'Владислав Блажевич' if ru else 'Vladislav Blazhevich',
              'alternateName': ['Vladislav Blazhevich', 'Владислав Михайлович Блажевич'] if ru
                               else ['Владислав Блажевич', 'Владислав Михайлович Блажевич'],
              'birthDate': '1881-08-15', 'deathDate': '1942-04-10',
              'jobTitle': 'Тромбонист, педагог, композитор' if ru else 'Trombonist, teacher, composer',
              'sameAs': PERSON_SAME_AS}
    g = []
    if path in ('index.html', 'en/index.html'):
        g.append({'@type': 'WebSite', '@id': f'{DOM}/#website', 'url': f'{DOM}/', 'name': 'Blazhevich',
                  'inLanguage': ['ru', 'en'], 'about': {'@id': person['@id']}})
        g.append(person)
    else:
        wp = {'@type': 'WebPage', '@id': f'{url}#page', 'url': url, 'name': title, 'description': desc,
              'inLanguage': lang, 'isPartOf': {'@id': f'{DOM}/#website'}}
        if path.startswith('news/'):   # лента — новости медных, а не страница о Блажевиче
            g.append(wp)
        else:
            g += [{**wp, 'about': {'@id': person['@id']}}, person]
    if path in ('works.html', 'en/works.html'):   # список концертов живёт на странице «Трудов»
        items = []
        for n, key, date in concerto_rows(lang):
            c = {'@type': 'MusicComposition', '@id': f'{url}#concerto-{n}',
                 'name': f'Концерт № {n} для тромбона' if ru else f'Trombone Concerto No. {n}',
                 'composer': {'@id': person['@id']}, 'url': f'{url}#concertos'}
            if key != '—':
                c['musicalKey'] = key
            if re.fullmatch(r'\d{4}', date):   # спорные даты («1926 или 1930-е») в разметку не идут
                c['dateCreated'] = date
            items.append({'@type': 'ListItem', 'position': int(n), 'item': c})
        g.append({'@type': 'ItemList', '@id': f'{url}#concertos-list',
                  'name': '13 концертов для тромбона' if ru else 'The 13 trombone concertos',
                  'numberOfItems': len(items), 'itemListElement': items})
    if path in CRUMBS:
        g.append({'@type': 'BreadcrumbList', 'itemListElement': [
            {'@type': 'ListItem', 'position': i, 'name': n_, 'item': f'{DOM}/{u}'} for i, (n_, u) in enumerate(CRUMBS[path], 1)]})
    data = json.dumps({'@context': 'https://schema.org', '@graph': g}, ensure_ascii=False, separators=(',', ':'))
    return '<script type="application/ld+json">' + data.replace('</', '<\\/') + '</script>'

# ---------------- «Лента»: ежедневный дайджест новостей медных (PLAN.md, этап «Лента») ----------------
# Выпуски лежат в data/news/ГГГГ-ММ-ДД.json, их пишет tools/news_agent.py. Пока выпусков нет,
# сборка ничего не добавляет: ни панели на главной, ни /news/, ни feed.xml.
NEWS_DIR = pathlib.Path(a.news_dir) if a.news_dir else ROOT / 'data' / 'news'
NEWS_MAX, NEWS_PANEL, NEWS_ARCHIVE, NEWS_FEED = 15, 5, 90, 50
NEWS_INSTR = {'trombone': 'тромбон', 'trumpet': 'труба', 'horn': 'валторна', 'tuba': 'туба', 'euphonium': 'эуфониум',
              'cornet': 'корнет', 'flugelhorn': 'флюгельгорн', 'brass-band': 'брасс-бэнд'}
NEWS_KIND = {'competition': 'конкурс', 'vacancy': 'вакансия', 'premiere': 'премьера', 'appointment': 'назначение',
             'obituary': 'память', 'festival': 'фестиваль', 'album': 'альбом', 'masterclass': 'мастер-класс'}
_MONTHS = 'января февраля марта апреля мая июня июля августа сентября октября ноября декабря'.split()
_esc = lambda t: html.escape(str(t), quote=True)
_weburl = lambda u: isinstance(u, str) and re.match(r'https?://[^\s"<>]+$', u) is not None

def ru_date(iso):
    d = datetime.date.fromisoformat(iso)
    return f'{d.day} {_MONTHS[d.month - 1]} {d.year}'

def load_news():
    """Выпуски от нового к старому. Позиция без заголовка, ссылки на первоисточник или даты публикации в выпуск не идёт."""
    out = []
    for f in sorted(NEWS_DIR.glob('[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9].json'), reverse=True)[:NEWS_ARCHIVE]:
        d = json.loads(f.read_text(encoding='utf-8'))
        datetime.date.fromisoformat(f.stem)
        items = [i for i in d.get('items', []) if i.get('title') and _weburl(i.get('url')) and i.get('published')]
        items.sort(key=lambda i: i['published'], reverse=True)          # свежие выше…
        items.sort(key=lambda i: float(i.get('score', 0)), reverse=True)   # …но главный порядок — по оценке (сортировка устойчивая)
        if items:
            out.append({'release': f.stem, 'items': items[:NEWS_MAX]})
    return out

def news_card(i):
    tags = [NEWS_INSTR[t] for t in i.get('instruments', []) if t in NEWS_INSTR] + [NEWS_KIND[t] for t in i.get('kinds', []) if t in NEWS_KIND]
    lang = '' if i.get('lang', 'ru') == 'ru' else f' lang="{_esc(i["lang"])}"'
    more = ''.join(f'<a href="{_esc(c["url"])}" rel="noopener">{_esc(c.get("source", "ещё источник"))}</a>'
                   for c in i.get('cluster', []) if _weburl(c.get('url')))
    return (f'<li class="news-item" data-agent-instruments="{_esc(" ".join(i.get("instruments", [])))}">'
            f'<p class="news-meta"><span class="news-source">{_esc(i.get("source", ""))}</span><time datetime="{_esc(i["published"])}">{ru_date(i["published"])}</time></p>'
            f'<h3{lang}><a href="{_esc(i["url"])}" rel="noopener">{_esc(i["title"])}</a></h3>'
            + (f'<p class="news-sum">{_esc(i["summary"])}</p>' if i.get('summary') else '')
            + (f'<p class="news-tags">{"".join(f"<span>{t}</span>" for t in tags)}</p>' if tags else '')
            + (f'<p class="news-more">Об этом же: {more}</p>' if more else '') + '</li>')

def news_chips(items):
    """Чипы фильтра по инструментам — только те, что есть в выпуске. Без JavaScript скрыты (фильтровать нечем)."""
    have = [k for k in NEWS_INSTR if any(k in i.get('instruments', []) for i in items)]
    if len(have) < 2:
        return ''
    return ('<p class="news-chips" data-agent-chips hidden><button type="button" data-agent-filter="" aria-pressed="true">Все</button>'
            + ''.join(f'<button type="button" data-agent-filter="{k}" aria-pressed="false">{NEWS_INSTR[k]}</button>' for k in have) + '</p>')

def news_panel(issue):
    """Панель на главной: первые пять позиций свежего выпуска (остальные в разметке, скрыты — для фильтра)."""
    return ('<section id="news" class="block news-panel" aria-labelledby="news-title"><div class="wrap">\n'
            '  <div class="section-head"><h2 id="news-title">Лента</h2>'
            f'<div class="eyebrow">Новости медных духовых · выпуск от <time datetime="{issue["release"]}">{ru_date(issue["release"])}</time></div>'
            '<p>Конкурсы, назначения, премьеры и записи: что произошло у тромбонистов, трубачей, валторнистов и тубистов. Каждая заметка ведёт на первоисточник.</p></div>\n'
            + news_chips(issue['items'])
            + f'<ol class="news-list" data-agent-list data-agent-release="{issue["release"]}" data-agent-limit="{NEWS_PANEL}">'
            + ''.join(news_card(i) for i in issue['items']) + '</ol>\n'
            '  <p class="news-foot"><a class="btn btn-ghost" href="news/">Весь выпуск и архив</a><a href="feed.xml">RSS</a></p>\n'
            '</div></section>\n')

def news_page(issue, issues, permalink):
    """Страница выпуска: /news/ (свежий, с архивом по дням) и /news/ГГГГ-ММ-ДД.html (постоянный адрес)."""
    cur = ' aria-current="page"'   # вне f-string-выражения: бэкслеш внутри выражения валиден только с Python 3.12
    arch = ''.join(f'<li><a href="{i["release"]}.html"{cur if permalink and i is issue else ""}>'
                   f'<time datetime="{i["release"]}">{ru_date(i["release"])}</time></a><span>{len(i["items"])}</span></li>' for i in issues)
    return ('<section id="news" class="block news-page"><div class="wrap">\n'
            '  <div class="section-head"><a class="crumb" href="../index.html">← Главная</a>'
            f'<h1 class="page-title">Лента</h1><div class="eyebrow">Выпуск от <time datetime="{issue["release"]}">{ru_date(issue["release"])}</time></div>'
            '<p>Ежедневный дайджест новостей медных духовых. Заметки ведут на первоисточники; пересказ не заменяет оригинал.</p></div>\n'
            + news_chips(issue['items'])
            + f'<ol class="news-list" data-agent-list data-agent-release="{issue["release"]}">' + ''.join(news_card(i) for i in issue['items']) + '</ol>\n'
            + f'  <div class="news-archive"><h2>Архив по дням</h2><ol>{arch}</ol><p class="note"><a href="../feed.xml">RSS-лента</a></p></div>\n'
            '</div></section>\n')

def news_feed(issues):
    """RSS 2.0: последние позиции ленты. Адрес канала — домен публичной сборки (в черновике — основной домен проекта)."""
    from xml.sax.saxutils import escape
    from email.utils import format_datetime
    base = DOM or 'https://blazhevich.tech'
    rfc = lambda iso: format_datetime(datetime.datetime.fromisoformat(iso + 'T00:00:00+00:00'))
    rows = [(i, s['release']) for s in issues for i in s['items']][:NEWS_FEED]
    items = ''.join(
        f'  <item><title>{escape(i["title"])}</title><link>{escape(i["url"])}</link><guid isPermaLink="false">{escape(i.get("id") or i["url"])}</guid>'
        f'<pubDate>{rfc(i["published"])}</pubDate><source url="{escape(base)}/news/{rel}.html">{escape(i.get("source", ""))}</source>'
        + (f'<description>{escape(i["summary"])}</description>' if i.get('summary') else '') + '</item>\n' for i, rel in rows)
    return ('<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">\n<channel>\n'
            f'  <title>Blazhevich — Лента: новости медных духовых</title>\n  <link>{base}/news/</link>\n'
            '  <description>Ежедневный дайджест: тромбон, труба, валторна, туба, брасс-бэнды. Ссылки на первоисточники.</description>\n'
            f'  <language>ru</language>\n  <lastBuildDate>{rfc(issues[0]["release"])}</lastBuildDate>\n'
            f'  <atom:link href="{base}/feed.xml" rel="self" type="application/rss+xml"/>\n{items}</channel>\n</rss>\n')

NEWS = load_news()

# OG-картинки под страницы: файл делает tools/media/make_og.py, результат коммитится.
# Страницы без своей картинки (витрина, лента) и EN-зеркала берут общую или картинку своей RU-страницы.
OG_DEFAULT = ('og-image.jpg', 'Владислав Блажевич с тромбоном перед Большим залом консерватории и Большим театром',
              'Vladislav Blazhevich with his trombone in front of the Great Hall of the Moscow Conservatory and the Bolshoi Theatre')
OG = {
    'works.html':      ('og-works.jpg', 'Большой зал Московской консерватории, архивная виньетка сайта', 'The Great Hall of the Moscow Conservatory, the site’s archival vignette'),
    'listen.html':     ('og-listen.jpg', 'Колоннада Большого театра, архивная виньетка сайта', 'The colonnade of the Bolshoi Theatre, the site’s archival vignette'),
    'schools.html':    ('og-schools.jpg', 'Московская консерватория, 1940-е годы', 'The Moscow Conservatory in the 1940s'),
    'about.html':      ('og-about.jpg', 'Большой театр, 1905 год', 'The Bolshoi Theatre, 1905'),
    'moscow.html':     ('og-moscow.jpg', 'Большой зал Московской консерватории', 'The Great Hall of the Moscow Conservatory'),
    'leningrad.html':  ('og-leningrad.jpg', 'Здание Петербургской консерватории на Театральной площади', 'The St. Petersburg Conservatory on Theatre Square'),
    'us-schools.html': ('og-us-schools.jpg', 'Истменская школа музыки в Рочестере', 'The Eastman School of Music in Rochester'),
}

def head(title, desc, path, lang, prefix, fonts):
    url = f'{DOM}/{path}'.replace('/index.html', '/') if DOM else ''
    og_file, alt_ru, alt_en = OG.get(path.removeprefix('en/'), OG_DEFAULT)
    alt = alt_ru if lang == 'ru' else alt_en
    img = f'{DOM}/assets/{og_file}' if DOM else f'{prefix}assets/{og_file}'
    m = [f'<title>{title}</title>',
         f'<meta name="description" content="{desc}">',
         f'<meta name="robots" content="{"index,follow" if a.release else "noindex,nofollow"}">',
         '<meta name="theme-color" content="#e8dbbf">', FAVICON,
         f'<link rel="apple-touch-icon" href="{prefix}assets/apple-touch-icon.png">',
         '<meta property="og:type" content="website">',
         f'<meta property="og:locale" content="{"ru_RU" if lang == "ru" else "en_US"}">',
         '<meta property="og:site_name" content="Blazhevich">',
         f'<meta property="og:title" content="{title}">',
         f'<meta property="og:description" content="{desc}">',
         f'<meta property="og:image" content="{img}">',
         f'<meta property="og:image:alt" content="{alt}">',
         '<meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">',
         '<meta name="twitter:card" content="summary_large_image">',
         f'<meta name="twitter:image" content="{img}">',
         f'<meta name="twitter:image:alt" content="{alt}">']
    if DOM:
        m += [f'<link rel="canonical" href="{url}">', f'<meta property="og:url" content="{url}">']
        if path in ('index.html', 'en/index.html'):   # языковые пары: общая страница и два досье
            m += [f'<link rel="alternate" hreflang="ru" href="{DOM}/">',
                  f'<link rel="alternate" hreflang="en" href="{DOM}/en/">',
                  f'<link rel="alternate" hreflang="x-default" href="{DOM}/">']
        elif path.removeprefix('en/') in EN_TWINS:   # раздел или досье с английским зеркалом
            f_ = path.removeprefix('en/')
            m += [f'<link rel="alternate" hreflang="ru" href="{DOM}/{f_}">',
                  f'<link rel="alternate" hreflang="en" href="{DOM}/en/{f_}">',
                  f'<link rel="alternate" hreflang="x-default" href="{DOM}/{f_}">']
        elif lang == 'ru':   # страница только по-русски (например, «Школы США»): ссылка на себя
            m += [f'<link rel="alternate" hreflang="ru" href="{url}">',
                  f'<link rel="alternate" hreflang="x-default" href="{url}">']
        m.append(jsonld(path, lang, url, title, desc))
    if path in ('index.html', 'en/index.html'):   # снимок первого экрана браузер начинает качать сразу, не дожидаясь разбора встроенных стилей
        hs = ', '.join(f'{prefix}assets/hero-home-{w}.avif {w}w' for w in (960, 1440, 2880))   # те же srcset и sizes, что у <source> в hero
        m.append(f'<link rel="preload" as="image" type="image/avif" imagesrcset="{hs}" '
                 'imagesizes="(max-aspect-ratio: 2880/1568) 184vh, 100vw" fetchpriority="high">')
        # шрифт надписи BLAZHEVICH на первом экране: без preload браузер узнаёт о нём только после разбора fonts.css
        m.append(f'<link rel="preload" as="font" type="font/woff2" href="{prefix}assets/fonts/cormorant-garamond-500-normal-latin.woff2" crossorigin>')
    if NEWS and lang == 'ru':   # автообнаружение RSS ленты
        m.append(f'<link rel="alternate" type="application/rss+xml" title="Blazhevich — Лента" href="{prefix}feed.xml">')
    m.append(fonts)
    return '\n'.join(m)

def page(lang, title, desc, path, prefix, body, fonts, footer):
    if lang == 'ru':
        body, footer = typo(body), typo(footer)
    html = ('<!doctype html>\n'
            f'<html lang="{lang}">\n<head>\n<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">\n'
            + head(title, desc, path, lang, prefix, fonts)
            + f'\n<link rel="stylesheet" href="{prefix}assets/{CSS_FILE}">\n</head>\n<body>\n{body}{footer}<script>\n{JS}</script>\n</body>\n</html>\n')
    return asset_urls(html)


def clean_out(path, tries=5):
    """Очистка site/. На Windows свежие файлы иногда заняты антивирусом или индексатором — повторяем."""
    for i in range(tries):
        shutil.rmtree(path, ignore_errors=True)
        if not path.exists():
            return
        time.sleep(0.3 * (i + 1))
    raise SystemExit(f'Не удалось очистить {path}: файлы заняты другим процессом, закройте просмотр и повторите')

def sync_locked_out(source, target):
    """Windows не переименовывает каталог, открытый локальным предпросмотром; синхронизируем его содержимое."""
    source_files = {p.relative_to(source) for p in source.rglob('*') if p.is_file()}
    for old in sorted((p for p in target.rglob('*') if p.is_file()), key=lambda p: len(p.parts), reverse=True):
        if old.relative_to(target) not in source_files:
            old.unlink()
    for src in sorted((p for p in source.rglob('*') if p.is_file()), key=lambda p: p.as_posix()):
        dst = target / src.relative_to(source)
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
    for old in sorted((p for p in target.rglob('*') if p.is_dir()), key=lambda p: len(p.parts), reverse=True):
        if not any(old.iterdir()):
            old.rmdir()


FINAL_OUT = ROOT / 'site'
STAGE_ROOT = ROOT / 'site.next'
PREVIOUS_OUT = ROOT / 'site.previous'
OUT = STAGE_ROOT / 'site'

# Если предыдущий процесс оборвался ровно во время подмены, возвращаем последний
# рабочий артефакт. В остальных случаях staging и старый backup безопасно убираются.
if not FINAL_OUT.exists() and PREVIOUS_OUT.exists():
    PREVIOUS_OUT.replace(FINAL_OUT)
clean_out(STAGE_ROOT)
clean_out(PREVIOUS_OUT)
atexit.register(clean_out, STAGE_ROOT)
(OUT / 'en').mkdir(parents=True)
shutil.copytree(ROOT / 'assets', OUT / 'assets')
(OUT / 'assets' / CSS_FILE).write_text(CSS)
(OUT / 'assets' / FONTS_FILE).write_text(FONTS_CSS)
# статические файлы для прямых ссылок (ноты и т.п.): files/ → site/files/ как есть, без обработки
if (ROOT / 'files').is_dir():
    shutil.copytree(ROOT / 'files', OUT / 'files')

# карта «id → (страница, главная секция страницы)»
id_page = {}
for f, (ss, _, _) in PAGES.items():
    for s_ in ss:
        for i in ids_in(sec(s_)):
            id_page[i] = (f, s_)
# старые якоря одностраничника: куда теперь ведёт каждый раздел (ссылки из контента и стабы).
# «В США» переехала в досье us-schools.html; якорь #usa появляется вместе с главой.
OLD_RU = {'scores': 'works.html', 'concertos': 'works.html#concertos', 'listen': 'listen.html',
          'biography': 'biography.html', 'schools': 'schools.html', 'about': 'about.html',
          'usa': 'us-schools.html#usa' if 'usa' in id_page else 'us-schools.html'}
STUB_TITLE_RU = {'scores': 'Ноты', 'concertos': 'Концерты', 'usa': 'В США'}

nav = ''.join(f'<a href="{i}.html">{t}</a>' for i, t in NAV_RU)
HUB_N = {f'{i}.html': n for n, (i, _, _) in enumerate(HUB_RU)}   # номер страницы в порядке разделов 01–05
for f, (ss, title, desc) in PAGES.items():
    par = PARENT_RU.get(f)
    en_href = 'en/index.html' if f == 'index.html' else f'en/{f}'
    if f == 'index.html':   # витрина: первый экран, вступление, разделы, вход в «Школу», лента
        hdr = header(nav, '<a class="lang" href="en/index.html" hreflang="en" lang="en">EN</a>', 'index.html', hero_page=True)
        hero = sec('hero')
        # Шапка — banner-landmark перед main; CSS оставляет её fixed/sticky и показывает после hero.
        body = (hdr + '<button class="fab" type="button" popovertarget="menu">Меню</button>\n'
                + '<main id="main">\n' + hero + home_sections('ru')
                + (news_panel(NEWS[0]) if NEWS else '') + '</main>\n')
        footer = FOOTER_RU()
    else:
        crumb = (par[1], f'{par[0]}.html') if par else ('Разделы', 'index.html')
        body = header(nav, f'<a class="lang" href="{en_href}" hreflang="en" lang="en">EN</a>', 'index.html') \
            + '<main id="main">\n' + inner(sec(ss[0]), crumb[0], crumb[1]) + ''.join(sec(s_) for s_ in ss[1:]) \
            + (files_block('ru') if f == 'works.html' else '') \
            + (pager(f[:-5], 'ru') if f in HUB_N else '') + '</main>\n'
        footer = FOOTER_RU()
    body = relink(body, f, id_page, OLD_RU)
    key = (par[0] if par else f[:-5]) + '.html'   # какой пункт меню подсвечен
    # точная страница — aria-current="page"; досье подсвечивает свой раздел — aria-current="true"
    cur = 'aria-current="true"' if par else 'aria-current="page"'
    for pat in (f'<a href="#{key[:-5]}">', f'<a href="{key}">'):
        if pat in body:
            body = body.replace(pat, pat[:-1] + f' class="active" {cur}>', 1)
            break
    (OUT / f).write_text(page('ru', title, desc, f, '', body,
                              f'<link rel="stylesheet" href="assets/{FONTS_FILE}">', footer))
if NEWS:   # «Лента»: свежий выпуск с архивом, постоянные адреса выпусков, RSS и снимок для живого обновления
    (OUT / 'news').mkdir()
    nav_news = ''.join('<a href="../' + (f'{i}.html' if f'{i}.html' in PAGES else f'index.html#{i}') + f'">{t}</a>' for i, t in NAV_RU) \
        + '<a href="index.html" class="active">Лента</a>'
    news_footer = re.sub(r'href="(?!https?:|#|mailto:)', 'href="../', FOOTER_RU())
    for n_, issue in enumerate([NEWS[0]] + NEWS):
        permalink = n_ > 0
        f = f'news/{issue["release"]}.html' if permalink else 'news/index.html'
        title = (f'Лента: выпуск от {ru_date(issue["release"])} — Blazhevich' if permalink else 'Лента — новости медных инструментов — Blazhevich')
        desc = f'Новости медных духовых, выпуск от {ru_date(issue["release"])}: ' + '; '.join(i['title'] for i in issue['items'][:3])
        body = header(nav_news, '<a class="lang" href="../en/index.html" hreflang="en" lang="en">EN</a>', '../index.html') \
            + '<main id="main">\n' + news_page(issue, NEWS, permalink) + '</main>\n'
        (OUT / f).write_text(page('ru', _esc(title), _esc(desc[:300]), f, '../', body,
                                  f'<link rel="stylesheet" href="../assets/{FONTS_FILE}">', news_footer))
    (OUT / 'feed.xml').write_text(news_feed(NEWS))
    (OUT / 'news' / 'today.json').write_text(json.dumps(NEWS[0], ensure_ascii=False, separators=(',', ':')) + '\n')

for k, tgt in OLD_RU.items():   # старые адреса разделов одностраничника
    if f'{k}.html' in PAGES:    # настоящий раздел — не переадресация
        continue
    (OUT / f'{k}.html').write_text(stub(tgt, f'{STUB_TITLE_RU[k]} — Blazhevich', 'ru'))

# ---------------- Английские страницы: один исходник, по странице на раздел ----------------
en = re.sub(r'(src="|srcset="|, )assets/', r'\1../assets/', sec('page', 'en'))  # пути к картинкам из папки en/
en_secs = {re.match(r'<section id="([\w-]+)"', p).group(1): p for p in re.split(r'(?=<section id=")', en) if p.strip()}
# «Труды» по-английски — одна секция works (контентёр волны hub-pages); пока её нет, склейка концертов и каталога
EN_WORKS_SECS = ['works'] if 'works' in en_secs else ['concertos', 'scores']
EN_PAGES = {  # файл en/<имя>: (секции, заголовок, описание)
    'works.html': (EN_WORKS_SECS, 'Works by Vladislav Blazhevich — Blazhevich',
                   'The catalogue: 13 trombone concertos, method books, studies and ensembles — with links to the scores.'),
    'listen.html': (['listen'], 'Listen to Blazhevich — Blazhevich', 'Recordings and video: how his music sounds today.'),
    'biography.html': (['biography'], 'Vladislav Blazhevich — biography: life, the State Wind Orchestra, Vyazma',
                       'The life of Vladislav Blazhevich: Smolensk, the Bolshoi Theatre, the Moscow Conservatory, the State Wind Orchestra and the musicians lost near Vyazma.'),
    'schools.html': (['schools'], 'The Moscow and St Petersburg trombone schools — Blazhevich', 'Two Russian trombone schools and the dossiers: Moscow, St Petersburg, America.'),
    'about.html': (['about'], 'About the project — Blazhevich', 'Sources, image credits and how this project works.'),
}
EN_HUB = [('works', 'Works', 'The catalogue: 13 concertos, schools, studies and ensembles — with links to the scores'),
          ('listen', 'Listen', 'Recordings and video: how his music sounds today'),
          ('biography', 'Biography', 'Moscow, the Bolshoi, the Conservatory — by documents and sources'),
          ('schools', 'The school and its lineage', 'Two Russian trombone schools and the dossiers: Moscow, St Petersburg, America'),
          ('about', 'About', 'Sources, image credits and how this project works')]
EN_STUB_TITLE = {'scores': 'Scores', 'concertos': 'Concertos', 'usa': 'In America'}
need = {s_ for ss, _, _ in EN_PAGES.values() for s_ in ss}
if need - set(en_secs):
    raise SystemExit(f'В src/en/page.html нет секций: {", ".join(sorted(need - set(en_secs)))}')
id_page_en = {}
for f_, (ss_, _, _) in EN_PAGES.items():
    for s_ in ss_:
        for i in ids_in(en_secs[s_]):
            id_page_en[i] = (f_, s_)
for f_ in EN_DOSSIERS:   # идентификаторы досье (m-bork, raichman, …) тоже разводятся по страницам
    for i in ids_in(sec(f_[:-5], 'en')):
        id_page_en.setdefault(i, (f_, f_[:-5]))
if 'usa' in en_secs:   # глава ждёт переноса в en/us-schools.html: её якоря пока ведут на досье американских школ
    for i in ids_in(en_secs['usa']):
        id_page_en.setdefault(i, ('us-schools.html', i))
OLD_EN = {'scores': 'works.html', 'concertos': 'works.html#concertos', 'listen': 'listen.html',
          'biography': 'biography.html', 'schools': 'schools.html', 'about': 'about.html',
          'usa': 'us-schools.html#usa' if 'usa' in id_page_en else 'us-schools.html'}
nav_en = ''.join(f'<a href="{i}.html">{t}</a>' for i, t, _ in EN_HUB)
FONTS_EN = f'<link rel="stylesheet" href="../assets/{FONTS_FILE}">'
hdr_en = header(nav_en, '<a class="lang" href="../index.html" hreflang="ru" lang="ru">RU</a>', 'index.html',
                hero_page=True, skip_text='Skip to content')
hero = en_secs['hero']
body = (hdr_en + '<button class="fab" type="button" popovertarget="menu">Menu</button>\n'
        + '<main id="main">\n' + hero + home_sections('en') + '</main>\n')
(OUT / 'en' / 'index.html').write_text(page(
    'en', 'Vladislav Blazhevich — trombone: life, concertos, Clef Studies',
    'Vladislav Blazhevich (1881–1942): biography, the 13 trombone concertos, Clef Studies and other method books, how his music reached America.',
    'en/index.html', '../', en_words(relink(body, 'index.html', id_page_en, OLD_EN)), FONTS_EN, FOOTER_EN()))
for f_, (ss_, title, desc) in EN_PAGES.items():   # страницы разделов
    body = (header(nav_en, f'<a class="lang" href="../{f_}" hreflang="ru" lang="ru">RU</a>', 'index.html', skip_text='Skip to content')
            + '<main id="main">\n' + inner(en_secs[ss_[0]], 'Sections', 'index.html', '../')
            + ''.join(en_secs[s_] for s_ in ss_[1:])
            + (files_block('en', '../') if f_ == 'works.html' else '')
            + pager(f_[:-5], 'en') + '</main>\n')
    body = relink(body, f_, id_page_en, OLD_EN)
    for pat in (f'<a href="#{f_[:-5]}">', f'<a href="{f_}">'):
        if pat in body:
            body = body.replace(pat, pat[:-1] + ' class="active" aria-current="page">', 1)
            break
    (OUT / 'en' / f_).write_text(page('en', title, desc, f'en/{f_}', '../', en_words(body), FONTS_EN, FOOTER_EN()))
for k, tgt in OLD_EN.items():   # старые адреса английских разделов
    if f'{k}.html' in EN_PAGES:
        continue
    (OUT / 'en' / f'{k}.html').write_text(stub(tgt, f'{EN_STUB_TITLE[k]} — Blazhevich', 'en'))
nav_en_dossier = nav_en.replace('<a href="schools.html">', '<a href="schools.html" class="active" aria-current="true">', 1)
for f, (title, desc) in EN_DOSSIERS.items():
    src = re.sub(r'(src="|srcset="|, )assets/', r'\1../assets/', sec(f[:-5], 'en'))
    body = (header(nav_en_dossier, f'<a class="lang" href="../{f}" hreflang="ru" lang="ru">RU</a>', 'index.html', skip_text='Skip to content')
            + '<main id="main">\n' + inner(src, 'The school and its lineage', 'schools.html', '../') + '</main>\n')
    body = relink(body, f, id_page_en, OLD_EN)
    (OUT / 'en' / f).write_text(page('en', title, desc, f'en/{f}', '../', en_words(body), FONTS_EN, FOOTER_EN()))

if a.release:
    today = datetime.date.fromisoformat(a.lastmod).isoformat() if a.lastmod else datetime.date.today().isoformat()
    urls = [''] + [f for f in PAGES if f != 'index.html'] + ['en/'] + [f'en/{f}' for f in (*EN_PAGES, *EN_DOSSIERS)]
    (OUT / 'sitemap.xml').write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + ''.join(f'  <url><loc>{DOM}/{u}</loc><lastmod>{today}</lastmod></url>\n' for u in urls)
        + (f'  <url><loc>{DOM}/news/</loc><lastmod>{NEWS[0]["release"]}</lastmod></url>\n' if NEWS else '')
        + ''.join(f'  <url><loc>{DOM}/news/{i["release"]}.html</loc><lastmod>{i["release"]}</lastmod></url>\n' for i in NEWS) + '</urlset>\n')
    (OUT / 'robots.txt').write_text(f'User-agent: *\nAllow: /\nContent-Signal: search=yes, ai-train=no\n\nSitemap: {DOM}/sitemap.xml\n')

# ---------------- Одностраничная версия для предпросмотра на claude.ai ----------------
one = ''.join(deco(sec(s_)) for s_ in WORKS_SECS + ['listen', 'biography', 'schools', 'about'])
nav = ''.join(f'<a href="#{i}">{t}</a>' for i, t, _ in HUB_RU)
art = ('<title>Blazhevich</title>\n<meta name="claude:viewport-fit-sides" content="cover">\n'
       '<meta name="robots" content="noindex,nofollow">\n<meta name="theme-color" content="#e8dbbf">\n' + FAVICON + '\n' + FONTS_GOOGLE
       + f'\n<style>\n{CSS}</style>\n\n'
       + header(nav, '', f'#{PAGES["works.html"][0][0]}')
       + f'<main id="main">\n{one}</main>\n'
       + '<footer><div class="wrap foot"><a href="#scores" class="brand">Blazhevich</a><span>Владислав Блажевич · Vladislav Blazhevich</span></div></footer>\n'
       + f'<script>\n{JS}</script>\n')
if a.single_page:
    (ROOT / 'artifact.html').write_text(art)
shutil.copy2(ROOT / '404.html', STAGE_ROOT / '404.html')
try:
    import enhancements as _enhancements
except ModuleNotFoundError:
    # Изолированные сборки Python (python313._pth, например встроенный Python в приложениях)
    # не добавляют папку скрипта в sys.path — добавляем её явно и повторяем импорт.
    import sys
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
    import enhancements as _enhancements
_enhancements_root = _enhancements.ROOT
try:
    _enhancements.ROOT = STAGE_ROOT
    _enhancements.apply()
finally:
    _enhancements.ROOT = _enhancements_root

# Подмена начинается только после полной генерации и enhancements.apply(). Если Windows
# держит сам каталог открытым предпросмотром, обновляем его содержимое из готового staging.
if FINAL_OUT.exists():
    try:
        FINAL_OUT.replace(PREVIOUS_OUT)
    except PermissionError:
        sync_locked_out(OUT, FINAL_OUT)
    else:
        try:
            OUT.replace(FINAL_OUT)
        except BaseException:
            if PREVIOUS_OUT.exists() and not FINAL_OUT.exists():
                PREVIOUS_OUT.replace(FINAL_OUT)
            raise
else:
    OUT.replace(FINAL_OUT)
clean_out(PREVIOUS_OUT)
clean_out(STAGE_ROOT)
print('Собрано в site:', 'ПУБЛИЧНАЯ версия для ' + DOM if a.release else 'черновик')
