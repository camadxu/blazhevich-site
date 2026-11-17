"""Единая обработка фотографий сайта: сепия-дуотон под архивные снимки Блажевича.

Палитра взята из эталона assets/blazhevich-1903.webp и из переменных style.css:
тени #2e1d0b, средние тона #6d573e, светá #eadfcb.

Правила:
  * оригиналы не изменяются и не удаляются — читаются из _originals/, результат пишется в assets/;
  * два формата кадра: портрет 4:5 (600×750) и снимок 3:2 (900×600);
  * кадрирование по центру с подъёмом к линии глаз (для портретов), без обрезки головы;
  * лёгкая S-кривая, зерно и виньетка — как у сканов того времени.

Запуск: python tools/photo_tone.py [--sheet]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from PIL import Image, ImageEnhance, ImageFilter, ImageOps

ROOT = Path(__file__).resolve().parent.parent
ORIG = ROOT / '_originals' / '2026-11-16'

# тени → средние → светá
STOPS = [(0.00, (0x1b, 0x12, 0x08)), (0.32, (0x43, 0x2e, 0x19)),
         (0.62, (0x7d, 0x67, 0x4c)), (1.00, (0xea, 0xdf, 0xcb))]

PORTRAIT = (600, 750)   # 4:5
PLATE = (900, 600)      # 3:2

# (исходник в _originals/2026-11-16, результат в assets/, формат, приоритет кадра по вертикали)
JOBS = [
    ('mail/trombonist-skobelev.webp', 'trombonist-skobelev.webp', PORTRAIT, 0.40, 'crop', 0.50),
    ('mail/trombonist-morozov.webp', 'trombonist-morozov.webp', PORTRAIT, 0.40, 'crop', 0.50),
    ('mail/trombonist-pachkaev.webp', 'trombonist-pachkaev.webp', PORTRAIT, 0.12, 'crop', 0.50),
    ('mail/trombonist-hersonsky.webp', 'trombonist-hersonsky.webp', PORTRAIT, 0.45, 'crop', 0.50),
    ('mail/raichman-portrait.webp', 'raichman-portrait.webp', PORTRAIT, 0.45, 'fit', 0.50),
    ('mail/hunsberger-usmc.webp', 'hunsberger-usmc.webp', PORTRAIT, 0.40, 'crop', 0.50),
    ('mail/edwards-trombone.webp', 'edwards-trombone.webp', PLATE, 0.42, 'crop', 0.50),
    # у этого скана медиана сидит в тенях, общий level() до него не достаёт — подъём задан отдельно
    ('mail/bso-trombones-1928.webp', 'bso-trombones-1928.webp', PLATE, 0.50, 'fit', 0.50, 0.72),
    ('mail/lindberg-960.webp', 'lindberg-960.webp', PORTRAIT, 0.40, 'crop', 0.50),
    # снимки школ США (загрузки из Wikimedia, исходники сохранены в _originals/wiki)
    ('wiki/eastman.webp', 'us-schools/eastman.webp', PLATE, 0.50, 'crop', 0.50),
    ('wiki/orchestra-hall.webp', 'us-schools/orchestra-hall.webp', PLATE, 0.50, 'crop', 0.50),
    ('wiki/curtis.webp', 'us-schools/curtis.webp', PLATE, 0.50, 'crop', 0.50),
    ('wiki/juilliard.webp', 'us-schools/juilliard.webp', PLATE, 0.50, 'crop', 0.50),
    ('wiki/kilbourn-hall.webp', 'us-schools/kilbourn-hall.webp', PLATE, 0.50, 'crop', 0.50),
    ('wiki/alessi.webp', 'us-schools/alessi.webp', PORTRAIT, 0.40, 'crop', 0.50),
    ('mail/trombone-trio.webp', 'us-schools/trombone-trio.webp', PLATE, 0.50, 'crop', 0.50),
    ('mail/eastman.webp', 'us-schools/eastman-choir.webp', (480, 480), 0.50, 'fit', 0.50),
]


def duotone(img: Image.Image) -> Image.Image:
    """Серый → тонированная по трём опорным цветам картинка."""
    g = ImageOps.grayscale(img)
    g = ImageOps.autocontrast(g, cutoff=(0.6, 0.4))
    # мягкая S-кривая
    g = g.point(lambda v: max(0, min(255, int(255 * (v / 255) ** 1.06 + 12 * (v / 255) * (1 - v / 255)))))

    lut = []
    for ch in range(3):
        vals = []
        for v in range(256):
            t = v / 255
            for i in range(len(STOPS) - 1):
                t0, c0 = STOPS[i]
                t1, c1 = STOPS[i + 1]
                if t0 <= t <= t1:
                    k = (t - t0) / (t1 - t0) if t1 > t0 else 0
                    a, b = c0[ch], c1[ch]
                    vals.append(int(round(a + (b - a) * k)))
                    break
            else:
                vals.append(STOPS[-1][1][ch])
        lut.extend(vals)
    out = Image.merge('RGB', [g, g, g]).point(lut)
    return out


def vignette(img: Image.Image, strength: float = 0.16) -> Image.Image:
    w, h = img.size
    mask = Image.new('L', (w, h), 0)
    px = mask.load()
    cx, cy = w / 2, h / 2
    maxd = (cx ** 2 + cy ** 2) ** 0.5
    for y in range(h):
        for x in range(w):
            d = (((x - cx) ** 2 + (y - cy) ** 2) ** 0.5) / maxd
            k = max(0.0, (d - 0.62) / 0.38)
            px[x, y] = int(255 * strength * (k ** 1.6))
    dark = Image.new('RGB', (w, h), STOPS[0][1])
    return Image.composite(dark, img, mask)


def grain(img: Image.Image, amount: float = 5.0) -> Image.Image:
    noise = Image.effect_noise(img.size, amount).convert('L').filter(ImageFilter.GaussianBlur(0.4))
    base = img.convert('L')
    mixed = Image.blend(base, Image.blend(base, noise, 0.5), 0.35)
    tinted = duotone(mixed)
    return Image.blend(img, tinted, 0.55)


def crop_to(img: Image.Image, size: tuple[int, int], anchor_y: float) -> Image.Image:
    tw, th = size
    target = tw / th
    w, h = img.size
    if w / h > target:                                    # шире — режем бока
        nw = int(round(h * target))
        x0 = (w - nw) // 2
        box = (x0, 0, x0 + nw, h)
    else:                                                 # выше — режем сверху/снизу по линии глаз
        nh = int(round(w / target))
        y0 = int(round((h - nh) * anchor_y))
        y0 = max(0, min(h - nh, y0))
        box = (0, y0, w, y0 + nh)
    return img.crop(box)


def fit_to(img: Image.Image, size: tuple[int, int]) -> Image.Image:
    """Вписать снимок целиком в кадр, поля — цветом бумаги сайта (допускается увеличение малых сканов)."""
    paper = Image.new('RGB', size, STOPS[-1][1])
    k = min(size[0] / img.width, size[1] / img.height)
    copy = img.resize((max(1, int(round(img.width * k))), max(1, int(round(img.height * k)))), Image.LANCZOS)
    paper.paste(copy, ((size[0] - copy.width) // 2, (size[1] - copy.height) // 2))
    return paper


def level(img: Image.Image, target: int = 138) -> Image.Image:
    """Подтянуть среднюю яркость к общей, не ломая намеренно тёмные кадры."""
    g = ImageOps.grayscale(img)
    hist = g.histogram()
    total = sum(hist)
    acc, median = 0, 128
    for v, n in enumerate(hist):
        acc += n
        if acc >= total / 2:
            median = v
            break
    gain = target / max(1, median)
    gain = max(0.88, min(1.16, gain))
    return ImageEnhance.Brightness(img).enhance(gain)


def process(src: Path, dst: Path, size: tuple[int, int], anchor_y: float, mode: str, anchor_x: float, lift: float = 1.0) -> tuple[int, int]:
    img = Image.open(src).convert('RGB')
    if mode == 'fit':
        img = fit_to(img, size)
    else:
        img = crop_to(img, size, anchor_y).resize(size, Image.LANCZOS)
    img = ImageEnhance.Contrast(duotone(img)).enhance(1.02)
    img = level(img)
    if lift != 1.0:                                   # подъём теней: гамма меньше единицы светлит низы
        table = [min(255, int(round(255 * (v / 255) ** lift))) for v in range(256)]
        img = img.point(table * 3)
    img = vignette(img)
    img = grain(img, 4.0)
    img = ImageEnhance.Sharpness(img).enhance(1.15)
    dst.parent.mkdir(parents=True, exist_ok=True)
    img.save(dst, 'WEBP', quality=88, method=6)
    return img.size


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--sheet', action='store_true', help='собрать контактный лист для просмотра')
    ap.add_argument('--only', default='', help='обработать только файлы, в имени которых есть подстрока')
    a = ap.parse_args()

    missing, done = [], []
    for job in JOBS:
        src_name, dst_name, size, anchor, mode, ax = job[:6]
        lift = job[6] if len(job) > 6 else 1.0
        if a.only and a.only not in dst_name:
            continue
        src = ORIG / src_name
        if not src.exists():
            missing.append(src_name)
            continue
        dst = ROOT / 'assets' / dst_name
        w, h = process(src, dst, size, anchor, mode, ax, lift)
        done.append((dst_name, w, h, dst.stat().st_size))

    for name, w, h, size in done:
        print(f'{name:38} {w}×{h}  {size // 1024} КБ')
    if missing:
        print('\nНЕТ ИСХОДНИКА:', ', '.join(missing), file=sys.stderr)

    if a.sheet:
        cols, cell = 4, 240
        rows = (len(done) + cols - 1) // cols
        sheet = Image.new('RGB', (cols * cell, rows * (cell + 18)), (232, 219, 191))
        for i, (name, _, _, _) in enumerate(done):
            im = Image.open(ROOT / 'assets' / name).convert('RGB')
            im.thumbnail((cell - 12, cell - 12))
            x = (i % cols) * cell + (cell - im.width) // 2
            y = (i // cols) * (cell + 18) + (cell - im.height) // 2
            sheet.paste(im, (x, y))
        sheet.save(ROOT / 'tmp_mail' / 'photo-sheet.png')
        print('контактный лист: tmp_mail/photo-sheet.png')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
