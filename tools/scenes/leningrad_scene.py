"""Фон шапки досье «Ленинградская тромбоновая школа» — в пару к moscow_scene.py:
кремовая бумага, плиты площади внизу, здание Петербургской консерватории на Театральной площади
(архивный снимок, прислал владелец 12.11.2026) — крупно в правом нижнем углу, в той же сепии.
Только Pillow и numpy; запускать вручную:  python3 tools/scenes/leningrad_scene.py
→ assets/scene-leningrad.webp (+ -960)."""
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageChops, ImageFilter
A = Path(__file__).resolve().parents[2] / 'assets'
W, H, HZ = 1920, 1150, 900
TOP, BOT = (247, 241, 228), (238, 228, 206)

def lerp(a, b, t): return tuple(round(x + (y - x) * t) for x, y in zip(a, b))
img = Image.new('RGBA', (W, H)); d = ImageDraw.Draw(img)
for y in range(H): d.line([(0, y), (W, y)], fill=lerp(TOP, BOT, y / H))

VX = 1300
floor = Image.new('RGBA', (W, H), (0, 0, 0, 0)); fd = ImageDraw.Draw(floor)
for i in range(-14, 10):
    fd.line([(VX, HZ), (VX + i * 330, H + 700)], fill=(168, 132, 58, 60), width=2)
y, step = HZ + 12, 8
while y < H:
    fd.line([(0, y), (W, y)], fill=(168, 132, 58, 50), width=2); step *= 1.45; y += step
m = Image.new('L', (W, H), 0); m.paste(Image.linear_gradient('L').resize((W, H - HZ)), (0, HZ))
floor.putalpha(ImageChops.multiply(floor.getchannel('A'), m))
img = Image.alpha_composite(img, floor)

# снимок: отрезаем пустое небо и рамку, сепия как у московского снимка (тёмное ~ (70,54,38), светлое — бумага)
src = Image.open(A / 'leningrad-conservatory.webp').convert('L').crop((0, 110, 1280, 850))
w = 1080; h = round(src.height * w / src.width)
src = src.resize((w, h), Image.LANCZOS).filter(ImageFilter.UnsharpMask(radius=1.4, percent=60, threshold=2))
g = np.asarray(src).astype(float) / 255
g = np.clip((g - 0.06) / 0.88, 0, 1) ** 0.9
stops = np.array([[62, 47, 33], [150, 132, 108], [242, 234, 216]], float)
t = g[..., None]
rgb = np.where(t < .5, stops[0] + (stops[1] - stops[0]) * (t / .5), stops[1] + (stops[2] - stops[1]) * ((t - .5) / .5))
# края растворяются в бумаге: слева и сверху мягко, справа и снизу чуть-чуть
yy, xx = np.mgrid[0:h, 0:w] / np.array([h, w])[:, None, None]
def ramp(v, a, b): return np.clip((v - a) / (b - a), 0, 1)
al = ramp(xx, 0.0, 0.28) * ramp(yy, 0.0, 0.24) * (1 - ramp(xx, 0.96, 1.0) * .6) * (1 - ramp(yy, 0.86, 1.0))
al = al ** 1.2
# небо светлое — уводим его в прозрачность, чтобы не было серого прямоугольника
al *= 1 - np.clip((g - 0.80) / 0.15, 0, 1) * (1 - ramp(yy, 0.25, 0.5))
b = Image.fromarray(np.dstack([rgb, al[..., None] * 255]).astype(np.uint8), 'RGBA')
b = b.filter(ImageFilter.GaussianBlur(0.3))
layer = Image.new('RGBA', (W, H), (0, 0, 0, 0)); layer.paste(b, (W - w + 30, H - h + 20), b)
img = Image.alpha_composite(img, layer).convert('RGB')
img.save(A / 'scene-leningrad.webp', 'WEBP', quality=84, method=6)
img.crop((640, 380, 1920, 1150)).resize((960, 578), Image.LANCZOS).save(A / 'scene-leningrad-960.webp', 'WEBP', quality=82, method=6)
print('ok')
