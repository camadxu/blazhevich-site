"""Фон первого экрана: консерватория слева и Большой театр справа — крупно, за портретом,
от верха окна до линии горизонта (площадь рисует CSS). Только Pillow; запускать вручную:
    python3 tools/scenes/home_scene.py   → assets/scene-home.webp"""
from pathlib import Path
from PIL import Image, ImageFilter
A = Path(__file__).resolve().parents[2] / 'assets'
W, H = 2400, 800                        # низ холста = линия горизонта
img = Image.new('RGBA', (W, H), (0, 0, 0, 0))

def place(name, width, x, sharpen=True):
    global img
    b = Image.open(A / name).convert('RGBA')
    h = round(b.height * width / b.width)
    b = b.resize((width, h), Image.LANCZOS)
    if sharpen: b = b.filter(ImageFilter.UnsharpMask(radius=1.6, percent=70, threshold=2))
    layer = Image.new('RGBA', (W, H), (0, 0, 0, 0)); layer.paste(b, (x, H - h + round(h * .085)), b)
    img = Image.alpha_composite(img, layer)

place('conservatory-1940s.webp', 1380, 40)     # стоит у левого края площади
place('bolshoi-1905.webp', 1380, 980)          # напротив, справа; края сходятся за фигурой
img.save(A / 'scene-home.webp', 'WEBP', quality=84, method=6)
print('ok', img.size)
