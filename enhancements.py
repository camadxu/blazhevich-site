"""Reproducible editorial additions to v2. No network or server writes."""
from pathlib import Path
import re,html,json
ROOT=Path(__file__).parent
SOURCES=[('https://www.mosconsv.ru/ru/groups/11202','МГК: история кафедры','Moscow Conservatory: department history'),('https://www.mosconsv.ru/ru/person/9085','МГК: Виктор Баташёв','Moscow Conservatory: Viktor Batashev'),('https://tuba.org.ru/scherbinin.pdf','Очерк о Щербинине и учениках','Essay on Shcherbinin and his pupils'),('https://www.mosconsv.ru/ru/eventdet/124387','МГК: Блажевич — профессор','Moscow Conservatory: Blazhevich as professor')]
# Each paired row is a single bilingual editorial record.
PEOPLE=[
('blazhevich','Владислав Михайлович Блажевич','Vladislav Mikhailovich Blazhevich',[
('Даты','Dates','Преподавание в МГК: 1920–1942; смерть в 1942 подтверждена МГК.','Teaching at Moscow Conservatory: 1920–1942; death in 1942 stated by the Conservatory.',4),
('Обучение и педагог','Studies and teacher','1900–1905, Московская консерватория, класс Х. Борка.','1900–1905, Moscow Conservatory, class of H. Bork.',1),
('Деятельность и сочинения','Work and publications','Преподаватель тромбона и тубы; автор школ, концертных дуэтов и секвенций.','Teacher of trombone and tuba; author of methods, concert duets and sequences.',1),
('Ученики','Pupils','Владимир Щербинин, Борис Григорьев.','Vladimir Shcherbinin, Boris Grigoryev.',1)]),
('shcherbinin','Владимир Арнольдович Щербинин','Vladimir Arnoldovich Shcherbinin',[
('Даты','Dates','18 января 1896 — 5 июня 1963, по очерку.','18 January 1896 – 5 June 1963, according to the essay.',3),
('Обучение и педагог','Studies and teacher','Ученик Блажевича. Очерк различает версии окончания обучения: 1930 и экстерном 1947; объяснение расхождения не доказано.','Pupil of Blazhevich. The essay gives conflicting completion dates: 1930 and external graduation in 1947; the explanation is unconfirmed.',3),
('Деятельность','Work','По очерку: солист Большого театра в 1926–1944; преподаватель МГК.','According to the essay: Bolshoi Theatre soloist in 1926–1944; Moscow Conservatory teacher.',3),
('Ученики','Pupils','Баташёв — по официальной биографии МГК; другие связи показаны отдельно ниже.','Batashev, according to his official Conservatory biography; further connections appear below.',2)]),
('batashev','Виктор Борисович Баташёв','Viktor Borisovich Batashev',[
('Даты и написание','Dates and spelling','В очерке: 7 июня 1937; встречается написание «Баташов». Независимая сверка даты рождения не выполнена.','The essay gives 7 June 1937; the spelling Batashov also occurs. The birth date has not been independently corroborated.',3),
('Обучение и педагог','Studies and teacher','Училище 1956; Московская консерватория 1960, класс Щербинина.','Music college 1956; Moscow Conservatory 1960, class of Shcherbinin.',2),
('Работа и достижения','Work and awards','БСО 1959–2001; Женева 1958, I премия; Прага 1962, III премия. Преподавание с 1963 с перерывом; профессор с 1995.','Bolshoi Symphony Orchestra 1959–2001; Geneva 1958, first prize; Prague 1962, third prize. Teaching from 1963 with an interruption; professor from 1995.',2),
('Ученики и записи','Pupils and recordings','МГК называет Мажорина и Шарова; биография сообщает о записях в Фонде радио и на «Мелодии».','The Conservatory lists Mazhorin and Sharov; its biography mentions Radio Fund and Melodiya recordings.',2)]),
('turusin','Михаил Николаевич Турусин','Mikhail Nikolaevich Turusin',[
('Даты','Dates','1924 год рождения указан в воспроизведённом архивном заголовке очерка; оригинал дела не сверялся.','Birth year 1924 appears in an archival heading reproduced in the essay; the original file has not been checked.',3),
('Обучение и педагог','Studies and teacher','По биографическому приложению: училище 1944–1947; МГК 1947–1952, класс Щербинина.','According to the biographical appendix: college 1944–1947; Moscow Conservatory 1947–1952, class of Shcherbinin.',3),
('Работа','Work','По приложению: Большой театр 1948–1959 и 1963–1975; оркестр радио и телевидения 1960–1963.','According to the appendix: Bolshoi Theatre 1948–1959 and 1963–1975; Radio and Television Orchestra 1960–1963.',3),
('Педагогика и достижения','Teaching and awards','По приложению: МГК с 1965; I премии фестивалей в Будапеште 1949 и Берлине 1951.','According to the appendix: Moscow Conservatory from 1965; first prizes at the Budapest 1949 and Berlin 1951 festivals.',3)]),
('ladilov','Константин Михайлович Ладилов','Konstantin Mikhailovich Ladilov',[
('Даты','Dates','9 февраля 1927 — 13 февраля 1983, по биографическому приложению очерка.','9 February 1927 – 13 February 1983, according to the essay’s biographical appendix.',3),
('Обучение и педагог','Studies and teacher','По приложению: Горьковская консерватория 1952, класс Щербинина; аспирантура МГК 1956.','According to the appendix: Gorky Conservatory 1952, class of Shcherbinin; postgraduate studies at Moscow Conservatory completed in 1956.',3),
('Работа','Work','По приложению: солист Госоркестра СССР 1957–1983; преподавание в Гнесинском институте с 1964.','According to the appendix: USSR State Symphony Orchestra soloist 1957–1983; teaching at the Gnessin Institute from 1964.',3),
('Достижения','Awards','По приложению: I премия фестиваля в Бухаресте, 1953.','According to the appendix: first prize at the Bucharest festival, 1953.',3)])]
EDGES=[('Борк','Bork','Блажевич','Blazhevich',1),('Блажевич','Blazhevich','Щербинин','Shcherbinin',1),('Блажевич','Blazhevich','Григорьев','Grigoryev',1),('Щербинин','Shcherbinin','Баташёв','Batashev',2),('Щербинин','Shcherbinin','Ладилов','Ladilov',3),('Щербинин','Shcherbinin','Турусин','Turusin',3),('Щербинин','Shcherbinin','Миронов','Mironov',3),('Щербинин','Shcherbinin','Лебедев','Lebedev',1),('Григорьев','Grigoryev','Досадин','Dosadin',1),('Баташёв','Batashev','Мажорин','Mazhorin',2),('Баташёв','Batashev','Шаров','Sharov',2)]
def people_section(en=False):
 def ref(i):return f' <a href="#v3-source-{i}">[{i}]</a>'
 s='<section id="people-v3" class="block"><div class="wrap"><h2>'+('Teachers and pupils: biographical cards' if en else 'Педагоги и ученики: биографические карточки')+'</h2>'
 s+='<p>'+('The essay combines memoirs, biographies and archival reproductions. Its dates are attributed, not independently verified archival facts.' if en else 'Очерк объединяет воспоминания, биографии и воспроизведения архивных материалов. Его сведения приводятся с атрибуцией, а не как независимо проверенные архивные факты.')+'</p><div class="people-v3">'
 for slug,ru,eng,rows in PEOPLE:
  s+=f'<article class="person-v3" id="person-{slug}"><h3>{eng if en else ru}</h3><p>{ru if en else eng}</p><dl>'
  for lr,le,tr,te,i in rows:s+=f'<dt>{le if en else lr}</dt><dd>{te if en else tr}{ref(i)}</dd>'
  s+='<dt>'+('Additional fields' if en else 'Дополнительные сведения')+'</dt><dd>'+('Unlisted compositions, editions, pupils and individual recordings have not been verified in this update; this does not imply their absence.' if en else 'Не перечисленные здесь сочинения, редакции, ученики и отдельные записи в этом дополнении не проверены; это не означает их отсутствия.')+'</dd>'
  s+='<dt>'+('Images and verification' if en else 'Изображения и проверка')+'</dt><dd>'+('No new portrait published in this card. Source review: project research pass; archival facsimiles not verified. See the dated editorial report.' if en else 'Новый портрет в карточке не публикуется. Сверка — по текстам источников; архивные факсимиле не проверены. Дата редакционной проверки указана в отчёте проекта.')+'</dd></dl></article>'
 s+='</div><h3>'+('Teacher → pupil connections' if en else 'Связи «педагог → ученик»')+'</h3><ul class="lineage-v3">'
 for ar,ae,br,be,i in EDGES:
  status=('essay; independent check pending' if en else 'по очерку; независимая сверка впереди') if i==3 else ('institutional source' if en else 'источник учреждения')
  s+=f'<li class="{"provisional" if i==3 else "documented"}">{ae if en else ar} → {be if en else br} — {status}{ref(i)}</li>'
 s+='</ul><p>'+('These edges concern teaching relationships, not shared employment or private consultations. Dashed borders denote essay-only evidence.' if en else 'Рёбра обозначают обучение, а не совместную работу или частные консультации. Пунктир отмечает связи, приведённые только по очерку.')+'</p><h3>'+('Sources' if en else 'Источники карточек')+'</h3><ol>'
 for i,(url,ru,eng) in enumerate(SOURCES,1):s+=f'<li id="v3-source-{i}"><a href="{url}">{eng if en else ru}</a></li>'
 return s+'</ol></div></section>'
# Metadata classifications use existing card descriptions, not invented score analysis.
META=[('method','single','mgk'),('method','single','mgk'),('duet','duo','mgk'),('exercise','single','mgk'),('method','single','classon'),('study','single','classon'),('study','single','classon'),('method','single','history'),('concerto','unspecified','recordings'),('study','single','imslp')]
LABELS={'genre': [('method','Школа','Method'),('duet','Дуэт','Duet'),('exercise','Упражнения','Exercises'),('study','Этюды','Studies'),('concerto','Концерты','Concertos')], 'ensemble':[('single','Один исполнитель: учебный материал','Single player: study material'),('duo','Два тромбона','Two trombones'),('unspecified','Состав сопровождения уточняется','Accompaniment not specified')], 'source':[('mgk','Московская консерватория','Moscow Conservatory'),('classon','classON','classON'),('history','История изданий','Edition history'),('recordings','Проект записей','Recording project'),('imslp','IMSLP','IMSLP')], 'difficulty':[('unrated','Не оценено по нотам','Not assessed from the score')]}
def apply():
 out=ROOT/'site'
 for path,en in [('scores.html',False),('en/scores.html',True)]:
  p=out/path;s=p.read_text();idx=[0]
  def attrs(m):
   j=idx[0];idx[0]+=1;g,e,so=META[j]
   return m.group(0)[:-1]+f' data-genre="{g}" data-ensemble="{e}" data-source="{so}" data-difficulty="unrated">'
  s=re.sub(r'<article class="card" data-instrument="[^"]+">',attrs,s);assert idx[0]==10
  controls='<div class="extra-tools-v3">'
  for key,opts in LABELS.items():
   title=({'genre':'Genre','ensemble':'Forces','source':'Source','difficulty':'Difficulty'} if en else {'genre':'Жанр','ensemble':'Состав','source':'Источник','difficulty':'Сложность'})[key]
   controls+=f'<label for="filter-{key}">{title}<select id="filter-{key}" data-catalog-filter="{key}"><option value="all">'+('All' if en else 'Все')+'</option>'
   controls+=''.join(f'<option value="{val}">{eng if en else ru}</option>' for val,ru,eng in opts)+'</select></label>'
  controls+='</div><p class="note">'+('Difficulty has not yet been assessed from scores. Proposed rubric: basic, intermediate, advanced — based on range, rhythm, endurance and clefs. No rating is assigned by title alone. Source filter describes the linked resource, not a verified publisher.' if en else 'Сложность пока не оценена по нотам. Предлагаемая шкала: базовая, средняя, высокая — по диапазону, ритму, выносливости и ключам. По одному названию оценка не назначается. Фильтр источника обозначает ресурс ссылки, а не проверенное издательство.')+'</p>'
  marker='  <p class="note count"';assert marker in s;s=s.replace(marker,controls+marker,1)
  # The hero carries no caption by the owner's choice; the portrait's AI origin and the photo credits live on the About page.
  p.write_text(s)
 # Карточки людей: на русском они повторяли бы московское досье, поэтому остаются только в английской версии.
 p=out/'en/schools.html';s=p.read_text();s=s.replace('</main>',people_section(True)+'</main>');p.write_text(s)
 # Styling additions inherit the existing palette and typography.
 css=''  # styles for these additions live in src/style.css
 for page in out.rglob('*.html'):
  text=page.read_text();page.write_text(text.replace('</head>',css+'</head>',1))
 # Standalone error page; activation on hosting requires verified server config.
 (out/'404.html').write_text('''<!doctype html><html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex"><title>Страница не найдена — Blazhevich</title><style>body{max-width:48rem;margin:10vh auto;padding:24px;background:#f4eee1;color:#2a2118;font:18px/1.6 system-ui}a{color:#24426b}</style></head><body><main><h1>Страница не найдена / Page not found</h1><p>Проверьте адрес или вернитесь к каталогу.</p><a href="/">Главная / Home</a> · <a href="/scores.html">Ноты / Scores</a> · <a href="/en/">English</a></main></body></html>''')
if __name__=='__main__':apply()
