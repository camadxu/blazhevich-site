"""Лента жизни (биография) и схема-карта (В США): генерирует HTML/SVG-фрагменты и вставляет их в исходники
между маркерами <!-- lifeline --> … <!-- /lifeline --> и <!-- routemap --> … <!-- /routemap -->.
Только стандартная библиотека. Запуск вручную:  python3 tools/media/make_fragments.py
Все даты и места взяты из текста разделов «Биография» и «В США»; координаты городов — географические."""
import re, pathlib
ROOT = pathlib.Path(__file__).resolve().parents[2]
Y0, Y1 = 1881, 1942

# (дорожка, начало, конец, якорь главы, RU, EN)
SPANS = [
    (0, 1881, 1893, 'ch-childhood', 'Смоленщина', 'Smolensk region'),
    (0, 1893, 1900, 'ch-army', 'Военные оркестры', 'Army bands'),
    (1, 1900, 1905, 'ch-conservatory', 'Консерватория', 'Conservatory'),
    (0, 1905, 1928, 'ch-bolshoi', 'Большой театр', 'Bolshoi Theatre'),
    (1, 1920, 1942, 'ch-teacher', 'Профессор консерватории', 'Conservatory professor'),
    (2, 1922, 1932, 'ch-bolshoi', 'Персимфанс', 'Persimfans'),
    (3, 1937, 1939, 'ch-conductor', 'Гос. духовой оркестр СССР', 'USSR State Wind Band'),
]
MARKS = [(1881, 'рождение', 'born'), (1900, 'класс Борка', 'Bork’s class'), (1925, 'школа в ключах', 'Clef Studies'),
         (1942, 'Москва, 10 апреля', 'Moscow, 10 April')]

def pct(y): return round((y - Y0) / (Y1 - Y0) * 100, 2)

def lifeline(en):
    t = 'A life in years' if en else 'Жизнь по годам'
    out = [f'<figure class="lifeline reveal" aria-label="{t}">', f'<figcaption>{t} · 1881–1942</figcaption>', '<div class="ll-scroll" tabindex="0"><div class="ll-track">']
    for lane, a, b, anchor, ru, en_ in SPANS:
        label = en_ if en else ru
        style = f'style="--a:{pct(a)}%;--w:{round(pct(b) - pct(a), 2)}%;--lane:{lane}"'
        inner = f'<b>{label}</b><i>{a}–{b}</i>'
        cls = 'll-span' + (' ll-short' if b - a <= 5 else '') + (' ll-left' if a > 1930 else '')
        out.append(f'<span class="{cls}" {style}>{inner}</span>' if en else f'<a class="{cls}" href="#{anchor}" {style}>{inner}</a>')
    out.append('<div class="ll-axis" aria-hidden="true">' + ''.join(f'<span style="--a:{pct(y)}%">{y}</span>' for y in range(1890, 1941, 10)) + '</div>')
    out.append('<div class="ll-marks">' + ''.join(f'<span style="--a:{pct(y)}%"><b>{y}</b> {e if en else r}</span>' for y, r, e in MARKS) + '</div>')
    out.append('</div></div></figure>')
    return '\n  '.join(out)

# ---------- карта ----------
def ov(lon, lat): return round((lon + 90) / 135 * 640, 1), round(30 + (65 - lat) / 40 * 410, 1)
def ins(lon, lat): return round(680 + (lon - 26) / 14 * 310, 1), round(60 + (61 - lat) / 9 * 360, 1)
C = {'boston': (-71.06, 42.36), 'tally': (-84.28, 30.44), 'moscow': (37.62, 55.75), 'spb': (30.31, 59.94),
     'smolensk': (32.05, 54.78), 'vitebsk': (30.2, 55.19)}

def arc(p, q, lift):
    (x1, y1), (x2, y2) = p, q
    return f'M{x1} {y1} Q{(x1 + x2) / 2} {min(y1, y2) - lift} {x2} {y2}'

def routemap(en):
    L = (lambda ru, e: e) if en else (lambda ru, e: ru)
    title = L('Схема: как ноты Блажевича попали в Америку', 'Chart: how Blazhevich’s music reached America')
    desc = L('Блажевич приехал из Смоленской губернии в Москву в 1900 году. Яков Райхман родился в Витебске, учился в Петербурге, играл в Москве и в 1926 году увёз ноты Блажевича в Бостон. В 1974 году Виктор Венгловский переслал из Ленинграда во Флориду все 13 концертов.',
             'Blazhevich came from Smolensk province to Moscow in 1900. Jacob Raichman was born in Vitebsk, studied in St. Petersburg, played in Moscow and in 1926 took Blazhevich’s music to Boston. In 1974 Victor Venglovsky sent all 13 concertos from Leningrad to Florida.')
    s = [f'<figure class="routemap reveal"><svg viewBox="0 0 1000 470" role="img" aria-labelledby="rm-t rm-d"><title id="rm-t">{title}</title><desc id="rm-d">{desc}</desc>']
    # сетка обзорной карты
    g = []
    for lon in range(-90, 46, 15):
        x = ov(lon, 0)[0]; g.append(f'<path d="M{x} 30V440"/>')
    for lat in range(25, 66, 10):
        y = ov(0, lat)[1]; g.append(f'<path d="M0 {y}H640"/>')
    s.append('<g class="rm-grid">' + ''.join(g) + '</g>')
    s.append('<rect class="rm-frame" x="0.5" y="30" width="639.5" height="410"/><rect class="rm-frame" x="680" y="60" width="310" height="360"/>')
    for lon in range(26, 41, 2):
        x = ins(lon, 0)[0]; s.append(f'<path class="rm-grid" d="M{x} 60V420"/>')
    for lat in range(53, 61, 2):
        y = ins(0, lat)[1]; s.append(f'<path class="rm-grid" d="M680 {y}H990"/>')
    s.append(f'<text class="rm-sea" x="330" y="330" text-anchor="middle">{L("Атлантический океан", "Atlantic Ocean")}</text>')
    s.append(f'<text class="rm-land" x="60" y="200">{L("Северная Америка", "North America")}</text>')
    s.append(f'<text class="rm-land" x="500" y="205">{L("Европа", "Europe")}</text>')
    s.append(f'<text class="rm-land" x="835" y="52" text-anchor="middle">{L("Россия, крупнее", "Russia, enlarged")}</text>')
    mo, sp, bo, ta = ov(*C['moscow']), ov(*C['spb']), ov(*C['boston']), ov(*C['tally'])
    # рамка-указатель области врезки
    a, b = ov(26, 61), ov(40, 52)
    s.append(f'<rect class="rm-inset" x="{a[0]}" y="{a[1]}" width="{round(b[0]-a[0],1)}" height="{round(b[1]-a[1],1)}"/><path class="rm-inset" d="M{b[0]} {a[1]}L680 60M{b[0]} {b[1]}L680 420"/>')
    s.append(f'<path class="rm-route" d="{arc(mo, bo, 110)}"/><path class="rm-route rm-route-2" d="{arc(sp, ta, 30)}"/>')
    s.append(f'<text class="rm-note" x="330" y="74" text-anchor="middle">{L("1926 · Райхман увозит ноты в Бостон", "1926 · Raichman takes the music to Boston")}</text>')
    s.append(f'<text class="rm-note" x="300" y="246" text-anchor="middle">{L("1974 · Венгловский: все 13 концертов", "1974 · Venglovsky: all 13 concertos")}</text>')
    def dot(p, label, dx=10, dy=4, anchor='start', key=False):
        return (f'<circle class="rm-dot{" rm-key" if key else ""}" cx="{p[0]}" cy="{p[1]}" r="{6 if key else 4.5}"/>'
                f'<text class="rm-city" x="{p[0] + dx}" y="{p[1] + dy}" text-anchor="{anchor}">{label}</text>')
    s.append(dot(bo, L('Бостон', 'Boston'), 10, 24, key=True))
    s.append(f'<text class="rm-sub" x="{bo[0] + 10}" y="{bo[1] + 41}">{L("«Clef Studies», 1948", "Clef Studies, 1948")}</text>')
    s.append(dot(ta, L('Таллахасси, Флорида', 'Tallahassee, Florida'), 12, 5))
    s.append(f'<circle class="rm-dot" cx="{mo[0]}" cy="{mo[1]}" r="3.5"/><circle class="rm-dot" cx="{sp[0]}" cy="{sp[1]}" r="3.5"/>')
    # врезка
    M, S, SM, V = ins(*C['moscow']), ins(*C['spb']), ins(*C['smolensk']), ins(*C['vitebsk'])
    s.append(f'<path class="rm-route" d="M{SM[0]} {SM[1]}L{M[0]} {M[1]}"/>')
    s.append(f'<path class="rm-route rm-route-2" d="M{V[0]} {V[1]}L{S[0]} {S[1]}L{M[0]} {M[1]}"/>')
    s.append(dot(M, L('Москва', 'Moscow'), 6, 26, 'middle', key=True))
    s.append(dot(S, L('Петербург', 'St. Petersburg'), 12, 5))
    s.append(dot(SM, L('Трегубовка, Смоленск', 'Tregubovka, Smolensk'), 4, 24))
    s.append(dot(V, L('Витебск', 'Vitebsk'), -10, -8, 'end'))
    s.append(f'<text class="rm-sub" x="{(SM[0] + M[0]) / 2 - 30}" y="{(SM[1] + M[1]) / 2 - 14}" text-anchor="middle">{L("Блажевич, 1900", "Blazhevich, 1900")}</text>')
    s.append(f'<text class="rm-sub" x="{S[0] + 12}" y="{S[1] + 22}">{L("Райхман, выпуск 1911", "Raichman, class of 1911")}</text>')
    s.append('</svg>')
    s.append(f'<figcaption>{L("Схема, а не точная карта: города стоят по своим координатам, берега не показаны. Сплошная линия — путь Блажевича и его нот, пунктир — путь Райхмана и посылка Венгловского.", "A chart rather than an exact map: the cities sit at their true coordinates, coastlines are not drawn. Solid line: the path of Blazhevich and his music; dashed: Raichman’s path and Venglovsky’s parcel.")}</figcaption></figure>')
    return '\n  '.join(s)

def put(path, name, html, before):
    """Вставить/обновить фрагмент между маркерами; при первой вставке — перед строкой `before`."""
    s = path.read_text(); block = f'<!-- {name} -->\n  {html}\n  <!-- /{name} -->'
    if f'<!-- {name} -->' in s:
        s = re.sub(rf'<!-- {name} -->.*?<!-- /{name} -->', lambda m: block, s, count=1, flags=re.S)
    else:
        assert s.count(before) == 1, (path, before)
        s = s.replace(before, block + '\n' + before, 1)
    path.write_text(s)

if __name__ == '__main__':
    put(ROOT / 'src/ru/biography.html', 'lifeline', lifeline(False), '  <div class="chapters">')
    put(ROOT / 'src/ru/usa.html', 'routemap', routemap(False), '  <div class="usa-grid">')
    put(ROOT / 'src/en/page.html', 'lifeline', lifeline(True), '  <div class="chapters">')
    put(ROOT / 'src/en/page.html', 'routemap', routemap(True), '  <div class="usa-grid">')
    print('ok')
