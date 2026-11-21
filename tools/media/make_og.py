"""OG-картинки под страницы (PLAN §5.5): cover-crop 1200x630 из готовых ассетов.
Мелкие виньетки не апскейлятся — ставятся карточкой на бумагу --paper:#e8dbbf.
Результат коммитится: CI этот скрипт не зовёт. Запуск вручную:
  python3 tools/media/make_og.py   (нужен Pillow)
"""
import pathlib
from PIL import Image, ImageEnhance

ROOT = pathlib.Path(__file__).resolve().parents[2]
W, H = 1200, 630
PAPER = (232, 219, 191)          # --paper:#e8dbbf

# страница -> (исходник, способ: cover | card, контраст, якорь кропа top|center|bottom, пре-кроп-бокс;
# выцветшим виньеткам — усиление контраста, иначе в ленте соцсетей карточка выглядит пустой бумагой;
# у сцен-шапок здание стоит в правом нижнем углу всей композиции — вырезаем район здания координатами
# вставки из tools/scenes/*_scene.py, иначе og — почти пустая бумага)
SRC = {
    'works':      ('assets/v-conservatory-portico.webp', 'card', 1.6, 'center', None),
    'listen':     ('assets/v-bolshoi-colonnade.webp', 'card', 1.6, 'center', None),
    'schools':    ('assets/conservatory-1940s.webp', 'cover', 1.0, 'center', None),
    'about':      ('assets/bolshoi-1905.webp', 'cover', 1.0, 'center', None),
    'moscow':     ('assets/scene-moscow.webp', 'cover', 1.0, 'bottom', (790, 400, 1920, 1150)),
    'leningrad':  ('assets/scene-leningrad.webp', 'cover', 1.0, 'bottom', (1050, 500, 1920, 1120)),
    'us-schools': ('assets/us-schools/eastman.webp', 'cover', 1.0, 'center', None),
}

def cover(im, anchor):
    s = max(W / im.width, H / im.height)
    im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
    x = (im.width - W) // 2
    y = {'top': 0, 'center': (im.height - H) // 2, 'bottom': im.height - H}[anchor]
    return im.crop((x, y, x + W, y + H))

def card(im):
    """Виньетка или портрет на бумаге, без апскейла: вписать по высоте, не крупнее 100%."""
    s = min(H / im.height, 1.0)
    im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
    if im.mode == 'RGBA':
        im.putalpha(im.getchannel('A').point(lambda a: a))   # сохранён альфа-канал для paste
    out = Image.new('RGB', (W, H), PAPER)
    out.paste(im, ((W - im.width) // 2, (H - im.height) // 2), im if im.mode == 'RGBA' else None)
    return out

for page, (src, how, k, anchor, box) in SRC.items():
    im = Image.open(ROOT / src)
    if box:
        im = im.crop(box)
    out = cover(im.convert('RGB'), anchor) if how == 'cover' else card(im.convert('RGBA'))
    if k != 1.0:
        out = ImageEnhance.Contrast(out).enhance(k)
    dst = ROOT / 'assets' / f'og-{page}.jpg'
    out.save(dst, 'JPEG', quality=85, optimize=True)
    print(f'{dst.relative_to(ROOT)}: {dst.stat().st_size // 1024}KB')
