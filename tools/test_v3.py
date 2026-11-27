from pathlib import Path
from html.parser import HTMLParser
import re,json,subprocess,hashlib,os,sys
ROOT=Path(__file__).resolve().parents[1]
class Cards(HTMLParser):
 def __init__(self):super().__init__();self.cards=[];self.current=None
 def handle_starttag(self,t,a):
  d=dict(a)
  if t=='article' and 'data-instrument' in d:
   self.current={'dataset':{k[5:]:v for k,v in d.items() if k.startswith('data-')},'textContent':''};self.cards.append(self.current)
 def handle_data(self,s):
  if self.current is not None:self.current['textContent']+=s+' '
 def handle_endtag(self,t):
  if t=='article':self.current=None
results=[]
HUB=['works.html','listen.html','schools.html','about.html']  # биография — на витрине (index.html#biography)
for page in ['index.html','en/index.html']:
 s=(ROOT/'site'/page).read_text()
 # витрина: первый экран, биография во всю ширину + полоса «Школа и традиция»; карточек разделов и бокового меню больше нет
 assert 'hero-home.webp' in s and 'goznak-moscow' not in s
 assert 'class="hero-mark"' in s and 'popovertarget="menu"' in s
 assert 'class="block bio-band"' in s and 'class="block school-strip"' in s and 'class="dossiers-strip"' in s
 assert 'class="block home-sections"' not in s and 'class="section-list"' not in s
 assert 'class="block home-school"' not in s and 'class="school-entry-link"' not in s
 assert 'class="hub-cards"' not in s
 assert 'class="rail"' not in s and 'rail-edge' not in s
 # шапка стоит под hero и выезжает по прокрутке (класс on-hero, JS ставит past-hero)
 assert '<header id="top-bar" class="on-hero">' in s
 assert all(f'href="{p}"' in s for p in HUB)   # меню ведёт на страницы разделов
for page in [*HUB,'moscow.html','leningrad.html','us-schools.html']:
 for pre in ('','en/'):
  assert (ROOT/'site'/pre/page).exists(),'нет страницы '+pre+page
# биография живёт на витрине: факты и полный текст в полосе bio-band на обоих языках
_ix=(ROOT/'site'/'index.html').read_text();_ie=(ROOT/'site'/'en'/'index.html').read_text()
assert 'class="facts"' in _ix and 'id="ch-army"' in _ix and 'class="block bio-band"' in _ix
assert 'class="facts"' in _ie and 'State Wind Orchestra of the USSR' in _ie
# каталог живёт на «Трудах»: карточки без панели поиска и фильтров (убрана по просьбе владельца 13.11.2026)
# число карточек не зашито: каталог строится из данных; карточка без названия или подписи — брак
cards={}
for page in ['works.html','en/works.html']:
 s=(ROOT/'site'/page).read_text()
 p=Cards();p.feed(s)
 # полка «Концерты» старого каталога вливается в блок концертов — карточек 9 или 10
 assert p.cards and all(c['textContent'].strip() for c in p.cards),page+': пустая карточка'
 assert 'data-catalog-filter' not in s and 'id="search"' not in s and 'id="count"' not in s
 assert 'id="concertos"' in s
 cards[page]=len(p.cards)
 results.append({'page':page,'catalog_cards':len(p.cards),'filters':'removed'})
assert cards['works.html']==cards['en/works.html'],'RU и EN каталог расходятся по числу карточек'
# Своя запись снята из доступа (решение владельца 27.11.2026): плеера и файла в сборке нет.
for pg in ['listen.html','en/listen.html']:
 s=(ROOT/'site'/pg).read_text();assert '<audio' not in s and 'viktor-batashev-rimsky' not in s,pg
assert not list((ROOT/'files').glob('*.mp3')) and not list((ROOT/'site'/'files').glob('*.mp3'))
assert 'https://music.yandex.ru/iframe/album/42318197' in (ROOT/'site'/'listen.html').read_text()
assert 'https://www.caleblambertlowbrass.com/blazhevich-recording-project' in (ROOT/'site'/'en'/'listen.html').read_text()
results.append({'own_audio':'removed by owner decision 2026-11-27'})
# пейджер разделов: порядок пяти реальных страниц, без самоссылок
_w=(ROOT/'site'/'works.html').read_text();_a=(ROOT/'site'/'about.html').read_text()
assert 'class="pager' in _w and 'href="listen.html"' in _w and 'rel="prev"' not in _w
assert 'class="pager' in _a and 'href="schools.html"' in _a and 'rel="next"' not in _a
# биография — на витрине: пейджеры «Слушать» и «Школы» ведут на index.html#biography
assert 'href="index.html#biography"' in (ROOT/'site'/'listen.html').read_text()
assert 'href="index.html#biography"' in (ROOT/'site'/'schools.html').read_text()
_es=(ROOT/'site'/'en'/'schools.html').read_text();_ea=(ROOT/'site'/'en'/'about.html').read_text()
assert 'rel="next" href="about.html"' in _es and 'rel="next" href="schools.html"' not in _es
assert 'rel="prev" href="schools.html"' in _ea and 'rel="next"' not in _ea
# База = реестр data/works.json: в files/ лежат только файлы реестра, у каждого файла назван источник.
_wreg=json.loads((ROOT/'data'/'works.json').read_text(encoding='utf-8'))
_owned=set()
for w in _wreg:
 urls=[u for f in ('notes_url','parts_url','audio_url') for u in (w.get(f) if isinstance(w.get(f),list) else [w.get(f)]) if u]
 _owned|={u.removeprefix('files/') for u in urls if u.startswith('files/')}
 if urls:
  assert w.get('source_url')=='' or w['source_url'].startswith('http'),w['id']
  assert w.get('source_title'),(w['id'],'нет источника')
assert {p.name for p in (ROOT/'files').iterdir() if p.is_file()}==_owned,'в files/ есть файл вне реестра'
assert {p.name for p in (ROOT/'site'/'files').iterdir()}==_owned
assert 'blazhevich-valse-de-concert-partitur.pdf' in _owned   # первая запись реестра остаётся
# ручные списки «Скачать ноты» и «Другие ноты» убраны: файлы показываются блоком реестра
for pg in ['works.html','en/works.html']:
 s=(ROOT/'site'/pg).read_text()
 assert 'id="files"' in s and 'id="catalog"' in s and 'id="concertos"' in s,pg
assert not any(t in _w for t in ('Скачать ноты','Другие ноты')) and not any(t in (ROOT/'site'/'en'/'works.html').read_text() for t in ('Download scores','More scores'))
# источник файла — строкой со ссылкой, RU и EN
assert 'Источник файла' in _w and 'href="https://imslp.org/' in _w and 'File origin' in (ROOT/'site'/'en'/'works.html').read_text()
# ссылки на свои PDF стоят в строках концертов № 2 и № 5 таблицы
for n,fn in ((2,'blazhevich-concerto-2-piano-1933.pdf'),(5,'blazhevich-concerto-5-piano-1930.pdf')):
 row=re.search(r'<tr><td>%d</td>.*?</tr>'%n,_w,re.S).group(0);assert 'files/'+fn in row,('концерт',n)
# «Полка тромбониста»: страница из data/shelf.json на обоих языках, вход с «Трудов», в sitemap
_shelf=json.loads((ROOT/'data'/'shelf.json').read_text(encoding='utf-8'))
for pg,label in (('shelf.html','Полка тромбониста'),('en/shelf.html','Trombonist’s shelf')):
 s=(ROOT/'site'/pg).read_text()
 assert label in s and 'rel="canonical"' in s and 'hreflang="en"' in s,pg
 for it in _shelf:
  if it.get('url') or it.get('file'):   # карточка без издания и ссылки на «Полке» не показывается
   assert ('shelf-'+it['id']) in s,pg+' нет записи '+it['id']
assert 'href="shelf.html"' in _w and 'href="shelf.html"' in (ROOT/'site'/'en'/'works.html').read_text()
# чужие файлы — только ссылками: их адреса есть на «Полке», файлов в сборке нет
for u in ('https://imslp.org/wiki/70_Tuba_Studies_(Blazhevich,_Vladislav)','https://imslp.org/wiki/Concert_Duets_for_Trombone_(Blazhevich,_Vladislav)','https://imslp.org/wiki/Concert_Sketch_No.5_(Blazhevich,_Vladislav)'):
 assert u in (ROOT/'site'/'shelf.html').read_text(),u
# og:image с alt на всех индексируемых страницах; у разделов и досье — своя картинка семейства og-*.jpg
for pg in ['index.html',*HUB,'moscow.html','leningrad.html','us-schools.html','en/index.html',*['en/'+p for p in HUB],'en/moscow.html','en/leningrad.html','en/us-schools.html']:
 _s=(ROOT/'site'/pg).read_text()
 assert 'property="og:image" content=' in _s and 'og:image:alt' in _s,pg
for pg,img in [('works.html','og-works.jpg'),('moscow.html','og-moscow.jpg'),('us-schools.html','og-us-schools.jpg')]:
 for pre in ('','en/'):assert img in (ROOT/'site'/pre/pg).read_text(),pre+pg
# sitemap: адреса считаются, а не зашиты — 18 основных страниц (вместе с «Полкой»), индекс ленты и по адресу на выпуск
_sm=(ROOT/'site'/'sitemap.xml').read_text()
_urls=re.findall(r'<loc>([^<]+)</loc>',_sm)
_news=[p for p in (ROOT/'data'/'news').glob('*.json') if p.stem[:4].isdigit()]
assert len(_urls)==18+(1 if _news else 0)+len(_news) and len(set(_urls))==len(_urls),f'sitemap: {len(_urls)} адресов'
assert 'biography.html' not in _sm
# hreflang в sitemap повторяет языковые пары из <head> тех же страниц (ru, en, x-default)
_dom=os.environ.get('BLZ_DOMAIN','https://blazhevich.tech').rstrip('/')
_blocks=dict(zip(_urls,[b for b in _sm.split('<url>')[1:]]))   # _sm делится перед каждым <url>
for _u in _urls:
 _rel=_u[len(_dom):].lstrip('/')
 _head=(ROOT/'site'/(_rel+'index.html' if _rel.endswith('/') else _rel or 'index.html')).read_text()
 _alt=dict(re.findall(r'<link rel="alternate" hreflang="([^"]+)" href="([^"]+)"',_head))
 _smalt=dict(re.findall(r'<xhtml:link rel="alternate" hreflang="([^"]+)" href="([^"]+)"',_blocks[_u]))
 assert _smalt==_alt,(_u,_smalt,_alt)
assert 'xmlns:xhtml="http://www.w3.org/1999/xhtml"' in _sm.split('<url>')[0]
# Карточки людей: на русском они повторяли бы московское досье, поэтому остаются только в английских «Трудах».
s=(ROOT/'site'/'en'/'works.html').read_text()
assert all('id="person-'+n+'"' in s for n in ['blazhevich','shcherbinin','batashev','turusin','ladilov'])
assert s.count('id="v3-source-')==4
assert s.count('class="provisional"')==3
# Происхождение портрета (ИИ) и источники фото указаны на странице «О проекте» и в английской версии.
assert 'созданное с помощью ИИ' in (ROOT/'site'/'about.html').read_text().replace('\u00a0',' ')  # сборщик ставит неразрывные пробелы
assert 'AI-generated' in (ROOT/'site'/'en'/'about.html').read_text()
# биография Райхмана живёт в досье американской линии, а не на витрине
assert (ROOT/'site'/'index.html').read_text().count('id="raichman"')==0
assert (ROOT/'site'/'us-schools.html').read_text().count('id="raichman"')==1
# стабы старых адресов одностраничника (у «В США» якорь появляется вместе с главой в досье)
for pre in ('','en/'):
 for k,tgt in (('scores.html','works.html'),('concertos.html','works.html#concertos'),('usa.html','us-schools.html'),('biography.html','index.html#biography')):
  _s=(ROOT/'site'/pre/k).read_text();assert f'url={tgt}' in _s,pre+k
# EN-досье: кнопка RU парной версии на месте; автограф — только в московском
assert all('hreflang="ru"' in (ROOT/'site'/pg).read_text() for pg in ['en/moscow.html','en/leningrad.html'])
assert 'autograph-1903' in (ROOT/'site'/'en'/'moscow.html').read_text() and 'autograph-1903' not in (ROOT/'site'/'en'/'leningrad.html').read_text()
# п. 5.0 и 5.2–5.3 docs/PLAN.md: контейнеры страниц сбалансированы; JSON-LD и x-default есть на индексируемых страницах публичной сборки
for pg in ['index.html',*HUB,'moscow.html','leningrad.html','us-schools.html','en/index.html',*['en/'+p for p in HUB],'en/moscow.html','en/leningrad.html','en/us-schools.html']:
 s=(ROOT/'site'/pg).read_text();assert s.count('<div')==s.count('</div>'),pg
 if 'rel="canonical"' in s:assert 'application/ld+json' in s and 'hreflang="x-default"' in s,pg
# страница ошибки входит в сборку и ведёт на разделы многостраничника
_e=(ROOT/'site'/'404.html').read_text();assert 'noindex' in _e and '/works.html' in _e and '/about.html' in _e
def digest():return {str(p.relative_to(ROOT/'site')):hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'site').rglob('*') if p.is_file()}
# Аргументы пересборки берутся из окружения, чтобы проверку можно было запускать
# сразу после сборки с теми же параметрами (по умолчанию — параметры релиза v3).
_lastmod=os.environ.get('BLZ_LASTMOD','2026-11-09');_domain=os.environ.get('BLZ_DOMAIN','https://blazhevich.tech')
before=digest();subprocess.run([sys.executable,'build.py','--release','--domain',_domain,'--lastmod',_lastmod],cwd=ROOT,check=True);assert before==digest()
report={'tests':results,'repeat_build_identical':True,'file_count':len(before),'content_pages':16,'error_page':True,'browser_test':'NOT RUN','live_publication':'NOT PERFORMED'}
(ROOT/'TEST-RESULTS.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps(report,ensure_ascii=False))
