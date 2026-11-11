"""Фон первого экрана: Московская консерватория (Большой зал), 1940-е, целиком, без растушёвки.
Полный кадр берётся из исходного файла коммита 99281c9 (там края были скрыты только альфа-каналом,
сами пиксели целы), переводится в ту же сепию, что и остальные снимки сайта.
    python3 tools/scenes/home_photo.py   → assets/conservatory-full.webp"""
import io, subprocess
from pathlib import Path
from PIL import Image, ImageOps, ImageFilter
ROOT = Path(__file__).resolve().parents[2]
raw = subprocess.run(['git', 'show', '99281c9:assets/conservatory-1940s.webp'], cwd=ROOT, capture_output=True, check=True).stdout
im = Image.open(io.BytesIO(raw)).convert('RGBA')
im.putalpha(255)
rgb = im.convert('RGB').crop((26, 52, 1080, 576))          # без рамки и рваного неба по верхнему краю
g = ImageOps.autocontrast(ImageOps.grayscale(rgb), cutoff=1)
out = ImageOps.colorize(g, black=(46, 34, 22), mid=(150, 122, 88), white=(246, 237, 216))
out = out.filter(ImageFilter.UnsharpMask(radius=1.2, percent=60, threshold=2))
out.save(ROOT / 'assets' / 'conservatory-full.webp', 'WEBP', quality=86, method=6)
print('ok', out.size)
