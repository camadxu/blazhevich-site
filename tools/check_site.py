"""Проверка собранного сайта без внешних зависимостей (только Python 3 из коробки).

  python3 tools/check_site.py            проверяет папку site/
  python3 tools/check_site.py путь/к/site

Что проверяется:
  • все страницы на месте: витрина, пять разделов, три досье — на обоих языках;
  • каждая внутренняя ссылка (href/src/srcset и url() в fonts.css) ведёт на существующий файл,
    а ссылка с #якорем — на существующий id в целевой странице;
  • нет повторяющихся id на странице, у каждой страницы ровно один <h1>;
  • JSON-LD на всех HTML-страницах валиден, локальные hreflang-ссылки взаимны;
  • ни одна страница не загружает внешние ресурсы (скрипты, стили, картинки, шрифты с http/https);
  • витрина: список разделов и короткий вход в «Школу» на месте, меню ведёт на разделы, бокового меню (rail) нет;
  • переадресации со старых адресов (scores, concertos, usa) ведут на существующие страницы;
  • страница 404 собрана и ведёт на разделы;
  • состояние публикации: robots, плашка черновика, canonical, sitemap.xml, robots.txt.
Внешние ссылки (<a href="https://…">) только перечисляются; их доступность не проверяется.
Код выхода 1 — если найдены ошибки.
"""
import json, pathlib, re, sys
from html.parser import HTMLParser
from urllib.parse import unquote, urlsplit

SITE = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else pathlib.Path(__file__).resolve().parent.parent / 'site').resolve()
# Сайт — витрина index.html, пять разделов и три досье на каждом языке; старые адреса — переадресации
HUB = ['works.html', 'listen.html', 'biography.html', 'schools.html', 'about.html']
PAGES = ['index.html', *HUB, 'moscow.html', 'leningrad.html', 'us-schools.html',
         'en/index.html', *[f'en/{p}' for p in HUB], 'en/moscow.html', 'en/leningrad.html', 'en/us-schools.html']
# старый адрес → (страница, обязательный якорь; '?' = якорь optional, пока глава переносится)
STUBS = (('scores.html', 'works.html', ''), ('concertos.html', 'works.html', 'concertos'), ('usa.html', 'us-schools.html', '?'))
errors, external = [], set()

class P(HTMLParser):
    def __init__(self):
        super().__init__(); self.refs = []; self.ids = []; self.h1 = 0; self.res = []
        self.alternates = []; self.json_ld = []; self._json_ld = None
    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        if 'id' in d: self.ids.append(d['id'])
        if tag == 'h1': self.h1 += 1
        for k in ('href', 'src'):
            if k in d and d[k]:
                self.refs.append((tag, k, d[k], d.get('rel')))
        if 'srcset' in d:
            for part in d['srcset'].split(','):
                self.refs.append((tag, 'srcset', part.strip().split(' ')[0], None))
        if tag == 'link' and d.get('hreflang') and 'alternate' in (d.get('rel') or '').split():
            self.alternates.append((d['hreflang'], d.get('href', '')))
        if tag == 'script' and (d.get('type') or '').lower() == 'application/ld+json':
            self._json_ld = []
    def handle_data(self, data):
        if self._json_ld is not None:
            self._json_ld.append(data)
    def handle_endtag(self, tag):
        if tag == 'script' and self._json_ld is not None:
            self.json_ld.append(''.join(self._json_ld))
            self._json_ld = None

parsed = {}
for pg in PAGES:
    f = SITE / pg
    if not f.exists():
        errors.append(f'нет страницы {pg}'); continue
    p = P(); p.feed(f.read_text(encoding='utf-8')); parsed[pg] = p
    dup = {i for i in p.ids if p.ids.count(i) > 1}
    if dup: errors.append(f'{pg}: повторяющиеся id {sorted(dup)}')
    if p.h1 != 1: errors.append(f'{pg}: <h1> встречается {p.h1} раз')

# JSON-LD проверяется у всех HTML-файлов, включая ленту, редиректы и 404.
for f in sorted(SITE.rglob('*.html')):
    pg = f.relative_to(SITE).as_posix()
    p = parsed.get(pg)
    if p is None:
        p = P(); p.feed(f.read_text(encoding='utf-8')); parsed[pg] = p
    for n, payload in enumerate(p.json_ld, 1):
        try:
            json.loads(payload)
        except json.JSONDecodeError as exc:
            errors.append(f'{pg}: невалидный JSON-LD #{n}: {exc.msg} (строка {exc.lineno}, столбец {exc.colno})')

def local_html(source, href):
    """Возвращает локальный HTML-путь для absolute/root-relative/relative URL."""
    u = urlsplit(href)
    raw = unquote(u.path)
    if u.scheme or u.netloc or raw.startswith('/'):
        target = SITE / raw.lstrip('/')
    else:
        target = (SITE / source).parent / raw
    if not raw or raw.endswith('/'):
        target /= 'index.html'
    target = target.resolve()
    try:
        rel = target.relative_to(SITE).as_posix()
    except ValueError:
        return None
    return rel if target.is_file() and target.suffix.lower() == '.html' else None

# Каждая локальная hreflang-ссылка должна быть взаимной: B ссылается обратно на A.
alternate_targets = {}
for pg, p in parsed.items():
    alternate_targets[pg] = [(lang, href, local_html(pg, href)) for lang, href in p.alternates]
for pg, links in alternate_targets.items():
    for lang, href, target in links:
        if target is None:
            continue
        if not any(back == pg for _, _, back in alternate_targets.get(target, [])):
            errors.append(f'{pg}: hreflang="{lang}" ведёт на {target}, но {target} не ссылается обратно на {pg}')

def ids_of(path):
    rel = path.relative_to(SITE).as_posix()
    if rel not in parsed:
        q = P(); q.feed(path.read_text(encoding='utf-8')); parsed[rel] = q
    return set(parsed[rel].ids)

checked = 0
for pg, p in list(parsed.items()):
    if pg not in PAGES: continue
    base = (SITE / pg).parent
    for tag, attr, url, rel in p.refs:
        if url.startswith(('http://', 'https://')):
            if tag == 'a': external.add(re.sub(r'^https?://([^/]+).*', r'\1', url))
            elif not (tag == 'link' and rel in ('canonical', 'alternate')) and not (tag == 'meta'):
                errors.append(f'{pg}: внешний ресурс <{tag} {attr}> {url}')
            continue
        if url.startswith(('data:', 'mailto:', 'tel:')): continue
        path, _, frag = url.partition('#')
        path = path.split('?', 1)[0]
        target = (base / path).resolve() if path else (SITE / pg)
        checked += 1
        if path.endswith('/'): target = target / 'index.html'
        if not target.exists():
            errors.append(f'{pg}: битая ссылка {url}'); continue
        if frag and target.suffix == '.html' and frag not in ids_of(target):
            errors.append(f'{pg}: нет якоря #{frag} в {target.relative_to(SITE)}')

# витрина: список разделов + короткий вход в «Школу»; меню ведёт на страницы разделов; старые крупные блоки убраны
if 'index.html' in parsed:
    s = (SITE / 'index.html').read_text(encoding='utf-8')
    for p_ in HUB:
        if f'href="{p_}"' not in s: errors.append(f'index.html: меню не ведёт на {p_}')
    if 'class="rail"' in s or 'rail-edge' in s: errors.append('index.html: осталось боковое меню rail')
    if any(marker in s for marker in ('class="block bio-band"', 'class="block school-strip"', 'class="dossiers-strip"')):
        errors.append('index.html: остались прежние блоки биографии или досье')
    if 'class="block home-sections"' not in s or 'class="section-list reveal"' not in s:
        errors.append('index.html: нет списка разделов')
    if 'class="block home-school"' not in s or 'class="school-entry-link"' not in s:
        errors.append('index.html: нет короткого входа в «Школу»')

# переадресации со старых адресов ведут на существующую страницу (и якорь, если он указан)
for pre in ('', 'en/'):
    for k, base_, frag in STUBS:
        f = SITE / f'{pre}{k}'
        if not f.exists():
            errors.append(f'нет переадресации {pre}{k}'); continue
        m = re.search(r'url=([^"]+)"', f.read_text(encoding='utf-8'))
        tgt, _, got = (m.group(1) if m else '').partition('#')
        if not m or tgt != base_ or not (f.parent / tgt).exists():
            errors.append(f'{pre}{k}: переадресация ведёт не туда ({m.group(1) if m else "нет"})'); continue
        if got and got not in ids_of(f.parent / tgt):
            errors.append(f'{pre}{k}: нет якоря #{got} в {tgt}')
        if frag != '?' and got != frag:
            errors.append(f'{pre}{k}: ожидался адрес {base_}#{frag}, получено #{got}')
        checked += 1

# страница 404 входит в сборку (копирует её enhancements.py из 404.html в корне репозитория)
f404 = SITE / '404.html'
if not f404.exists():
    errors.append('нет 404.html')
else:
    t = f404.read_text(encoding='utf-8')
    if 'noindex' not in t: errors.append('404.html: нет noindex')
    for p_ in ('/works.html', '/about.html'):
        if f'href="{p_}"' not in t: errors.append(f'404.html: нет ссылки {p_}')

# sitemap.xml (публичная сборка) не должен перечислять переадресации с noindex
sm = SITE / 'sitemap.xml'
if sm.exists():
    for loc in re.findall(r'<loc>[^<]*/([^/<]*\.html)</loc>', sm.read_text(encoding='utf-8')):
        f = SITE / loc
        if f.exists() and 'noindex' in f.read_text(encoding='utf-8')[:600]:
            errors.append(f'sitemap.xml: в списке переадресация {loc}')

css = SITE / 'assets' / 'fonts.css'
if css.exists():
    for u in re.findall(r'url\(([^)]+)\)', css.read_text()):
        checked += 1
        if not (css.parent / u.strip('\'"')).exists(): errors.append(f'fonts.css: нет файла {u}')
else:
    errors.append('нет assets/fonts.css')

idx = (SITE / 'index.html').read_text(encoding='utf-8') if (SITE / 'index.html').exists() else ''
robots = re.search(r'<meta name="robots" content="([^"]+)"', idx)
canon = re.search(r'<link rel="canonical" href="([^"]+)"', idx)
print(f'Папка: {SITE}')
print(f'Страниц: {sum(1 for p in PAGES if (SITE / p).exists())} из {len(PAGES)}; проверено локальных ссылок и путей: {checked}')
print('Режим:', 'ПУБЛИЧНЫЙ' if robots and robots.group(1).startswith('index') else 'ЧЕРНОВИК (noindex)',
      '| плашка черновика:', 'есть' if 'class="draft"' in idx else 'нет',
      '| canonical:', canon.group(1) if canon else 'нет',
      '| sitemap.xml:', 'есть' if (SITE / 'sitemap.xml').exists() else 'нет',
      '| robots.txt:', 'есть' if (SITE / 'robots.txt').exists() else 'нет')
print('Внешние сайты в ссылках (не проверялись на доступность):', ', '.join(sorted(external)))
if errors:
    print('\nОШИБКИ:'); [print(' -', e) for e in errors]; sys.exit(1)
print('Ошибок не найдено.')
