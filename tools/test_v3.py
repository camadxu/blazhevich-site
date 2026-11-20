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
HUB=['works.html','listen.html','biography.html','schools.html','about.html']
for page in ['index.html','en/index.html']:
 s=(ROOT/'site'/page).read_text()
 # витрина: первый экран, карточки пяти разделов, полоса досье; бокового меню одностраничника больше нет
 assert 'hero-home.webp' in s and 'goznak-moscow' not in s
 assert 'class="hero-mark"' in s and 'popovertarget="menu"' in s
 assert 'class="hub-cards"' in s and 'class="dossiers-strip"' in s
 assert 'class="rail"' not in s and 'rail-edge' not in s
 # шапка стоит под hero и выезжает по прокрутке (класс on-hero, JS ставит past-hero)
 assert '<header id="top-bar" class="on-hero">' in s
 assert all(f'href="{p}"' in s for p in HUB)
for page in [*HUB,'moscow.html','leningrad.html','us-schools.html']:
 for pre in ('','en/'):
  assert (ROOT/'site'/pre/page).exists(),'нет страницы '+pre+page
# каталог живёт на «Трудах»: карточки без панели поиска и фильтров (убрана по просьбе владельца 13.11.2026)
for page in ['works.html','en/works.html']:
 s=(ROOT/'site'/page).read_text()
 p=Cards();p.feed(s)
 # полка «Концерты» старого каталога вливается в блок концертов — карточек 9 или 10
 assert 9<=len(p.cards)<=10,page+': карточек '+str(len(p.cards))
 assert 'data-catalog-filter' not in s and 'id="search"' not in s and 'id="count"' not in s
 assert 'id="concertos"' in s
 results.append({'page':page,'catalog_cards':len(p.cards),'filters':'removed'})
# пейджер разделов: на «Трудах» — центр и «Слушать →», в «О проекте» — «← Школа и традиция» без «след»
_w=(ROOT/'site'/'works.html').read_text();_a=(ROOT/'site'/'about.html').read_text()
assert 'class="pager' in _w and 'href="listen.html"' in _w and 'rel="prev"' not in _w
assert 'class="pager' in _a and 'href="schools.html"' in _a and 'rel="next"' not in _a
# блок «Файлы для скачивания» рендерится из реестра data/works.json (засеян партитурой Вальс-концерта)
assert 'id="files"' in _w and 'blazhevich-valse-de-concert-partitur.pdf' in _w
assert 'id="files"' in (ROOT/'site'/'en'/'works.html').read_text()
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
 for k,tgt in (('scores.html','works.html'),('concertos.html','works.html#concertos'),('usa.html','us-schools.html')):
  _s=(ROOT/'site'/pre/k).read_text();assert f'url={tgt}' in _s,pre+k
# EN-досье: кнопка RU парной версии на месте; автограф — только в московском
assert all('hreflang="ru"' in (ROOT/'site'/pg).read_text() for pg in ['en/moscow.html','en/leningrad.html'])
assert 'autograph-1903' in (ROOT/'site'/'en'/'moscow.html').read_text() and 'autograph-1903' not in (ROOT/'site'/'en'/'leningrad.html').read_text()
# п. 5.0 и 5.2–5.3 PLAN.md: контейнеры страниц сбалансированы; JSON-LD и x-default есть на индексируемых страницах публичной сборки
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
report={'tests':results,'repeat_build_identical':True,'file_count':len(before),'content_pages':18,'error_page':True,'browser_test':'NOT RUN','live_publication':'NOT PERFORMED'}
(ROOT/'TEST-RESULTS.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps(report,ensure_ascii=False))
