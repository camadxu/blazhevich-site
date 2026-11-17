"""Единая обработка фотографий сайта: сепия-дуотон под архивные снимки Блажевича.

Палитра взята из эталона assets/blazhevich-1903.webp и из переменных style.css:
тени → средние → светá, опорные цвета в STOPS ниже.

Правила:
  * оригиналы не изменяются и не удаляются — читаются из _originals/, результат пишется
    в _incoming/retouch/ по умолчанию (публикация — только явным --out assets);
  * два формата кадра: портрет 4:5 (600×750) и снимок 3:2 (900×600);
  * кадрирование по центру с подъёмом к линии глаз (для портретов), без обрезки головы.

Порядок обработки (каждый шаг откатывается, если портит картинку):
  1. автообрезка бумажных полей — только однородные светлые полосы у края скана
     (яркость ≥ 225 и разброс ≤ 13), не больше 10 % с каждой стороны, детерминированно;
  2. подавление газетного растра — блюр до кадрирования, радиус по измеренному шагу
     сетки (автокорреляция остатка после медианы), лёгкий unsharp после масштаба;
  3. паспарту: если остаток бумаги срезать уже нельзя (лимит 10 %) или кадр не
     заполняется — ровное поле цвета старого картона, край снимка растворяется в нём;
  4. тон: средняя яркость самого снимка 105 (по файлу с паспарту — до 115), гамма
     подбирается по гистограмме, светá придерживаются, чтобы не пересветить;
  5. виньетка, зерно и слабый unsharp — лица без «пластика».

Запуск:
  python tools/photo_tone.py                  # кандидаты в _incoming/retouch/
  python tools/photo_tone.py --sheet          # + контактный лист до/после
  python tools/photo_tone.py --out assets     # публикация (решение владельца)
"""
from __future__ import annotations

import argparse
import random
import sys
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont, ImageOps, ImageStat

ROOT = Path(__file__).resolve().parent.parent
ORIG = ROOT / '_originals' / '2026-11-16'
DEFAULT_OUT = ROOT / '_incoming' / 'retouch'

# тени → средние → светá
STOPS = [(0.00, (0x1b, 0x12, 0x08)), (0.32, (0x43, 0x2e, 0x19)),
         (0.62, (0x7d, 0x67, 0x4c)), (1.00, (0xea, 0xdf, 0xcb))]

PORTRAIT = (600, 750)   # 4:5
PLATE = (900, 600)      # 3:2

# тон: все снимки в одной полосе средней яркости (по серому 0–255)
TARGET_MEAN = 105.0      # средняя яркость самого снимка
FILE_TARGET = 110.0      # средняя по файлу, когда есть паспарту
MEAN_BAND = (95.0, 115.0)

# бумага скана: почти белая и однородная
PAPER_MIN = 225.0
PAPER_FLAT = 13.0
MAX_CROP = 0.10         # не более 10 % размера с каждой стороны
MIN_CROP = 0.006        # мельче 0.6 % — это артефакт края, а не поле
MOUNT_T = 0.99          # паспарту = бумага сайта: край снимка растворяется в том же поле, что и рамка

# (исходник в _originals/2026-11-16, результат, формат, приоритет кадра по вертикали)
JOBS = [
    ('mail/trombonist-skobelev.webp', 'trombonist-skobelev.webp', PORTRAIT, 0.40, 'crop', 0.50),
    ('mail/trombonist-morozov.webp', 'trombonist-morozov.webp', PORTRAIT, 0.40, 'crop', 0.50),
    ('mail/trombonist-pachkaev.webp', 'trombonist-pachkaev.webp', PORTRAIT, 0.12, 'crop', 0.50),
    ('mail/trombonist-hersonsky.webp', 'trombonist-hersonsky.webp', PORTRAIT, 0.45, 'crop', 0.50),
    ('mail/raichman-portrait.webp', 'raichman-portrait.webp', PORTRAIT, 0.45, 'fit', 0.50),
    ('mail/hunsberger-usmc.webp', 'hunsberger-usmc.webp', PORTRAIT, 0.40, 'crop', 0.50),
    ('mail/edwards-trombone.webp', 'edwards-trombone.webp', PLATE, 0.42, 'crop', 0.50),
    ('mail/bso-trombones-1928.webp', 'bso-trombones-1928.webp', PLATE, 0.50, 'fit', 0.50),
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


# --- палитра ----------------------------------------------------------------

def _sepia(v: int) -> tuple[int, int, int]:
    t = v / 255
    for i in range(len(STOPS) - 1):
        t0, c0 = STOPS[i]
        t1, c1 = STOPS[i + 1]
        if t0 <= t <= t1:
            k = (t - t0) / (t1 - t0) if t1 > t0 else 0.0
            return tuple(int(round(a + (b - a) * k)) for a, b in zip(c0, c1))
    return STOPS[-1][1]


SEPIA = [_sepia(v) for v in range(256)]
LUMA = tuple(0.299 * r + 0.587 * g + 0.114 * b for r, g, b in SEPIA)
MOUNT = SEPIA[int(round(MOUNT_T * 255))]


# --- 1. бумажные поля -------------------------------------------------------

def _edge_line(g: Image.Image, side: str, i: int) -> tuple[float, float]:
    w, h = g.size
    box = {'L': (i, 0, i + 1, h), 'R': (w - 1 - i, 0, w - i, h),
           'T': (0, i, w, i + 1), 'B': (0, h - 1 - i, w, h - i)}[side]
    st = ImageStat.Stat(g.crop(box))
    return st.mean[0], st.stddev[0]


def paper_runs(g: Image.Image, cap: float = MAX_CROP) -> dict[str, int]:
    """Ширина однородной светлой полосы у каждого края, в пикселях (не больше cap)."""
    w, h = g.size
    out: dict[str, int] = {}
    for side, dim in (('L', w), ('R', w), ('T', h), ('B', h)):
        limit = max(1, int(round(dim * cap)))
        minrun = max(4, int(round(dim * MIN_CROP)))
        run = 0
        for i in range(limit):
            mean, dev = _edge_line(g, side, i)
            if mean >= PAPER_MIN and dev <= PAPER_FLAT:
                run = i + 1
            else:
                break
        out[side] = run if run >= minrun else 0
    return out


def autocrop(img: Image.Image) -> tuple[Image.Image, dict[str, int]]:
    """Срезать только однородные светлые поля: лица и головы дают разброс и не режутся."""
    runs = paper_runs(ImageOps.grayscale(img))
    if not any(runs.values()):
        return img, {}
    box = (runs['L'], runs['T'], img.width - runs['R'], img.height - runs['B'])
    if box[2] - box[0] < img.width * 0.55 or box[3] - box[1] < img.height * 0.55:
        return img, {}
    return img.crop(box), runs


# --- 2. растр ---------------------------------------------------------------

def screen_pitch(g: Image.Image, lags=(2, 3, 4, 5, 6), threshold: float = 0.30) -> tuple[float, int]:
    """Периодичность растровой сетки: (отклик 0..1, шаг в пикселях).

    Газетный растр даёт регулярный узор — остаток после медианы коррелирует сам с собой
    на шаге сетки. Фотографическая фактура такой корреляции не даёт.
    """
    res = ImageChops.subtract(g, g.filter(ImageFilter.MedianFilter(3)), 1, 128)
    w, h = res.size
    px = res.load()
    step_y = max(1, h // 120)
    best, best_lag = 0.0, 0
    for lag in lags:
        num = den = 0.0
        for y in range(0, h, step_y):
            for x in range(0, w - lag, 3):
                a = px[x, y] - 128
                num += a * (px[x + lag, y] - 128)
                den += a * a
        r = num / den if den else 0.0
        if r > best:
            best, best_lag = r, lag
    return (best, best_lag) if best >= threshold else (0.0, 0)


def suppress_screen(img: Image.Image) -> tuple[Image.Image, tuple[float, int, float]]:
    """Размытие до кадрирования: точки растра усредняются в тон, фактура остаётся."""
    found, lag = screen_pitch(ImageOps.grayscale(img))
    if found:
        radius = 1.6 if lag >= 4 else 1.25          # шаг сетки крупный → мягче
    else:
        radius = 0.6                                # только шум скана
    return img.filter(ImageFilter.GaussianBlur(radius)), (found, lag, radius)


# --- кадр -------------------------------------------------------------------

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


def fit_geometry(gray: Image.Image, size: tuple[int, int]) -> tuple[Image.Image, dict[str, int]]:
    """Снимок целиком без полей: масштаб по меньшей стороне и остатки под паспарту."""
    k = min(size[0] / gray.width, size[1] / gray.height)
    copy = gray.resize((max(1, int(round(gray.width * k))), max(1, int(round(gray.height * k)))), Image.LANCZOS)
    x0, y0 = (size[0] - copy.width) // 2, (size[1] - copy.height) // 2
    bands = {'L': x0, 'R': size[0] - copy.width - x0, 'T': y0, 'B': size[1] - copy.height - y0}
    return copy, bands


def place_on_mount(img: Image.Image, size: tuple[int, int], bands: dict[str, int]) -> Image.Image:
    """Посадить снимок на паспарту цвета старого картона (тон задан палитрой)."""
    canvas = Image.new('RGB', size, MOUNT)
    canvas.paste(img, (bands.get('L', 0), bands.get('T', 0)))
    return canvas


# --- 3. тон -----------------------------------------------------------------

def _contrast_for(gamma: float) -> float:
    """Чем сильнее подъём теней, тем нужнее S-кривая: иначе кадр уходит в туман."""
    return min(0.72, 0.30 + max(0.0, 0.90 - gamma) * 0.55)


def tone_lut(gamma: float, contrast: float | None = None, knee: float = 0.55, hold: float = 0.75) -> list[int]:
    """Кривая тона: гамма тянет средние тона, светá придерживаются, S держит контраст."""
    contrast = _contrast_for(gamma) if contrast is None else contrast
    lut = []
    for v in range(256):
        x = v / 255
        y = x ** gamma
        if x > knee:                                  # у света возвращаем линейность
            wgt = ((x - knee) / (1 - knee)) ** 1.5 * hold
            y = (1 - wgt) * y + wgt * x
        y -= contrast * y * (1 - y) * (1 - 2 * y)     # мягкая S-кривая
        lut.append(min(255, max(0, int(round(255 * y)))))
    for i in range(1, 256):                           # страховка: кривая не должна ломаться
        if lut[i] < lut[i - 1]:
            lut[i] = lut[i - 1]
    return lut


def mean_with(gray: Image.Image, lut: list[int]) -> float:
    hist = gray.histogram()
    total = sum(hist)
    acc = 0.0
    for v, n in enumerate(hist):
        if n:
            acc += n * LUMA[lut[v]]
    return acc / total


def solve_gamma(gray: Image.Image, target: float, lo: float = 0.28, hi: float = 1.6, steps: int = 14) -> float:
    """Гамма, при которой средняя яркость (в палитре сепии) равна target."""
    for _ in range(steps):
        mid = (lo + hi) / 2
        if mean_with(gray, tone_lut(mid)) > target:
            lo = mid                                  # светлее нужного → гамму больше
        else:
            hi = mid
    return (lo + hi) / 2


def tint(gray: Image.Image, gamma: float) -> Image.Image:
    curve = tone_lut(gamma)
    chans = [[SEPIA[curve[v]][ch] for v in range(256)] for ch in range(3)]
    return Image.merge('RGB', [gray.point(c) for c in chans])


# --- 4. печать: виньетка, край, зерно ---------------------------------------

def vignette(img: Image.Image, strength: float = 0.17, onset: float = 0.62, step: int = 4) -> Image.Image:
    w, h = img.size
    sw, sh = max(1, w // step), max(1, h // step)
    mask = Image.new('L', (sw, sh), 0)
    px = mask.load()
    cx, cy = (sw - 1) / 2, (sh - 1) / 2
    maxd = (cx * cx + cy * cy) ** 0.5 or 1.0
    for y in range(sh):
        for x in range(sw):
            d = (((x - cx) ** 2 + (y - cy) ** 2) ** 0.5) / maxd
            k = max(0.0, (d - onset) / (1 - onset))
            px[x, y] = int(255 * strength * (k ** 1.6))
    mask = mask.resize((w, h), Image.BILINEAR)
    return Image.composite(Image.new('RGB', (w, h), STOPS[0][1]), img, mask)


def edge_dissolve(img: Image.Image, spec: dict[str, tuple[int, int, float, tuple[int, int, int]]],
                  power: float = 1.4) -> Image.Image:
    """Растворение края: рваный край уходит в бумагу, стык с паспарту — в картон.

    spec: сторона → (полная ширина, ширина ровной части, сила 0..1, цвет).
    """
    w, h = img.size
    if not spec:
        return img

    def ramp(length: int, total: int, flat: int, a: float) -> list[int]:
        if total <= 0 or a <= 0:
            return [0] * length
        tail = max(1, total - flat)
        out = []
        for i in range(length):
            k = 1.0 if i <= flat else max(0.0, 1 - (i - flat) / tail)
            out.append(int(255 * a * (k ** power)))
        return out

    cols = [0] * w
    for i, v in enumerate(ramp(w, *spec.get('L', (0, 0, 0.0))[:3])):
        cols[i] = max(cols[i], v)
    for i, v in enumerate(ramp(w, *spec.get('R', (0, 0, 0.0))[:3])):
        cols[w - 1 - i] = max(cols[w - 1 - i], v)
    rows = [0] * h
    for i, v in enumerate(ramp(h, *spec.get('T', (0, 0, 0.0))[:3])):
        rows[i] = max(rows[i], v)
    for i, v in enumerate(ramp(h, *spec.get('B', (0, 0, 0.0))[:3])):
        rows[h - 1 - i] = max(rows[h - 1 - i], v)

    cmask = Image.frombytes('L', (w, 1), bytes(cols)).resize((w, h), Image.NEAREST)
    rmask = Image.frombytes('L', (1, h), bytes(rows)).resize((w, h), Image.NEAREST)
    out = img
    for side in 'LRTB':
        if side not in spec:
            continue
        span = spec[side][0]
        band = {'L': (0, 0, span, h), 'R': (w - span, 0, w, h),
                'T': (0, 0, w, span), 'B': (0, h - span, w, h)}[side]
        mask = ImageChops.lighter(cmask, rmask).crop(band)
        out.paste(Image.new('RGB', (band[2] - band[0], band[3] - band[1]), spec[side][3]), band[:2], mask)
    return out


_GRAIN = None
_GRAIN_SIGMA = 8.0


def _grain_tile() -> Image.Image:
    """Зерно из фиксированного генератора: результат воспроизводим от запуска к запуску."""
    global _GRAIN
    if _GRAIN is None:
        side = 512
        rnd = random.Random(20261116)
        buf = bytes(min(255, max(0, int(round(128 + rnd.gauss(0, _GRAIN_SIGMA)))))
                    for _ in range(side * side))
        _GRAIN = Image.frombytes('L', (side, side), buf)
    return _GRAIN


def grain(img: Image.Image, amount: float = 3.6) -> Image.Image:
    tile = _grain_tile()
    w, h = img.size
    canvas = Image.new('L', (w, h))
    ox, oy = (w * 7) % tile.width, (h * 13) % tile.height
    for y in range(-oy, h, tile.height):
        for x in range(-ox, w, tile.width):
            canvas.paste(tile, (x, y))
    if amount != _GRAIN_SIGMA:
        k = amount / _GRAIN_SIGMA
        canvas = canvas.point([min(255, max(0, int(round(128 + (v - 128) * k)))) for v in range(256)])
    return ImageChops.add(img, Image.merge('RGB', [canvas, canvas, canvas]), 1, -128)


# --- сборка кадра -----------------------------------------------------------

def mount_border(size: tuple[int, int], residual: dict[str, float]) -> int:
    """Ровная рамка паспарту: накрывает остаток бумаги, который нельзя срезать (лимит 10 %)."""
    worst = max(residual.values()) if residual else 0.0
    if worst < 0.04:                     # тоньше 4 % накрывается растворением края
        return 0
    dims = {'L': size[0], 'R': size[0], 'T': size[1], 'B': size[1]}
    return max(int(round(residual.get(s, 0.0) * dims[s])) for s in 'LRTB')


def dissolve_spec(size: tuple[int, int], residual: dict[str, float], margin: dict[str, int],
                  mounted: bool) -> dict[str, tuple[int, int, float, tuple[int, int, int]]]:
    """Где и насколько растворять край: стык с паспарту — в картон, остаток бумаги — в бумагу."""
    dims = {'L': size[0], 'R': size[0], 'T': size[1], 'B': size[1]}
    spec: dict[str, tuple[int, int, float, tuple[int, int, int]]] = {}
    for side in 'LRTB':
        side_margin = margin.get(side, 0)
        frac = residual.get(side, 0.0)
        dim = dims[side]
        if side_margin > 0:
            spec[side] = (side_margin + int(round(0.050 * dim)), side_margin, 1.0, MOUNT)
        elif frac > 0.004:
            if mounted:
                spec[side] = (int(round((frac + 0.030) * dim)), 0, 1.0, MOUNT)
            else:
                spec[side] = (int(round((frac + 0.020) * dim)), 0, 0.55, STOPS[-1][1])
    return spec


def mount_colour(photo_mean: float, share: float, target_file: float) -> tuple[int, int, int]:
    """Паспарту всегда бумажное: на сайте снимок лежит на таком же поле, шва не видно."""
    return MOUNT


def compose(gray: Image.Image, gamma: float, size: tuple[int, int],
            spec: dict[str, tuple[int, int, float, tuple[int, int, int]]],
            margin: dict[str, int], sharp: tuple[float, int] = (1.1, 62)) -> Image.Image:
    img = tint(gray, gamma)
    img = vignette(img)                       # винетка — только внутри снимка, паспарту остаётся ровным
    if any(margin.values()):
        img = place_on_mount(img, size, margin)
    img = edge_dissolve(img, spec)
    img = grain(img, 3.6)
    return img.filter(ImageFilter.UnsharpMask(radius=sharp[0], percent=sharp[1], threshold=3))


def luma_mean(img: Image.Image) -> float:
    return ImageStat.Stat(img.convert('L')).mean[0]


def process(src: Path, dst: Path, size: tuple[int, int], anchor_y: float, mode: str,
            anchor_x: float, target: float = TARGET_MEAN) -> dict:
    img = Image.open(src).convert('RGB')
    img, cropped = autocrop(img)

    # остаток бумаги после обрезки — им задаётся ширина мягкого края
    left = ImageOps.grayscale(img)
    residual = {}
    runs = paper_runs(left, cap=0.25)
    for side, dim in (('L', img.width), ('R', img.width), ('T', img.height), ('B', img.height)):
        residual[side] = runs[side] / dim

    scale = min(size[0] / img.width, size[1] / img.height)
    img, screen = suppress_screen(img)
    gray = ImageOps.autocontrast(ImageOps.grayscale(img), cutoff=(0.5, 0.5))

    border = mount_border(size, residual)
    area = (size[0] - 2 * border, size[1] - 2 * border)
    if mode == 'fit':
        gray, bands = fit_geometry(gray, area)
    else:
        gray = crop_to(gray, area, anchor_y).resize(area, Image.LANCZOS)
        bands = {}

    margin = {side: border + bands.get(side, 0) for side in 'LRTB'}
    box = (margin['L'], margin['T'], size[0] - margin['R'], size[1] - margin['B'])
    share = (box[2] - box[0]) * (box[3] - box[1]) / (size[0] * size[1])
    mounted = any(margin.values())
    spec = dissolve_spec(size, residual, margin, mounted=mounted)

    # сильно увеличенные сканы теряют резкость — unsharp им чуть сильнее, но без грязи
    sharp = (2.0, 70) if scale >= 1.5 else (1.1, 62)

    gamma = solve_gamma(gray, target)
    out = compose(gray, gamma, size, spec, margin, sharp)
    if mounted:                              # тон паспарту — из фактической доли поля
        photo_mean = luma_mean(out.crop(box))
        colour = mount_colour(photo_mean, share, FILE_TARGET)
        spec = dissolve_spec(size, residual, margin, mounted=mounted)
        spec = {k: (v[0], v[1], v[2], colour) for k, v in spec.items()}
        out = compose(gray, gamma, size, spec, margin, sharp)
    for _ in range(2):                       # виньетка и растворение края съедают яркость
        mean = luma_mean(out.crop(box))
        if abs(mean - target) <= 1.5:
            break
        gamma = solve_gamma(gray, target + (target - mean))
        out = compose(gray, gamma, size, spec, margin, sharp)

    dst.parent.mkdir(parents=True, exist_ok=True)
    out.save(dst, 'WEBP', quality=88, method=6)
    return {'size': out.size, 'gamma': gamma, 'crop': cropped, 'screen': screen,
            'margin': margin, 'residual': residual, 'scale': scale, 'mean': mean}


# --- отчёт ------------------------------------------------------------------

def metrics(path: Path) -> dict | None:
    if not path.exists():
        return None
    g = Image.open(path).convert('L')
    hist = g.histogram()
    total = sum(hist)
    mean = sum(v * n for v, n in enumerate(hist)) / total
    dark = sum(n for v, n in enumerate(hist) if v < 40) / total
    return {'size': g.size, 'mean': mean, 'dark': dark * 100}


def font(size: int = 13) -> ImageFont.ImageFont:
    for name in ('segoeui.ttf', 'arial.ttf', 'tahoma.ttf'):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def contact_sheet(rows: list[dict], before_dir: Path, after_dir: Path, dst: Path) -> tuple[int, int]:
    cw, ch = 420, 340
    gutter = 26
    f, fb = font(13), font(14)
    sheet = Image.new('RGB', (cw * 2 + gutter * 3, (ch + 34) * len(rows) + gutter), (26, 24, 21))
    d = ImageDraw.Draw(sheet)
    for i, row in enumerate(rows):
        y0 = gutter + i * (ch + 34)
        for j, (label, base) in enumerate((('до', before_dir), ('после', after_dir))):
            x0 = gutter + j * (cw + gutter)
            path = base / row['name']
            d.text((x0, y0 - 18), label, font=fb, fill=(214, 186, 138))
            if not path.exists():
                d.rectangle((x0, y0, x0 + cw, y0 + ch), outline=(80, 70, 58))
                d.text((x0 + 8, y0 + 8), 'нет файла', font=f, fill=(150, 130, 100))
                continue
            im = Image.open(path).convert('RGB')
            im.thumbnail((cw, ch))
            sheet.paste(im, (x0 + (cw - im.width) // 2, y0 + (ch - im.height) // 2))
        d.text((gutter, y0 + ch + 4), row['caption'], font=f, fill=(226, 214, 190))
    dst.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(dst)
    return sheet.size


def write_report(rows: list[dict], dst: Path, target: float) -> None:
    lines = ['# Тон и растр: кандидаты ретуши', '',
             f'Цель: средняя яркость самого снимка {target:.0f} (полоса {MEAN_BAND[0]:.0f}–{MEAN_BAND[1]:.0f} по серому). '
             '«До» — файл, лежащий сейчас в `assets/`, «после» — файл из `_incoming/retouch/`.', '',
             '| Файл | Размер | Средняя «до» | Средняя «после» | <40 «до», % | <40 «после», % | Обрезка | Растр | Поля |',
             '|---|---|---|---|---|---|---|---|---|']
    for r in rows:
        b, a = r['before'], r['after']
        crop = {k: v for k, v in (r.get('crop') or {}).items() if v}
        crop_s = ', '.join(f'{k} {v}' for k, v in crop.items()) if crop else '—'
        screen = r.get('screen') or (0.0, 0, 0.0)
        screen_s = f'{screen[0]:.2f} (шаг {screen[1]}), блюр {screen[2]:.2f}' if screen[0] else 'не найден'
        margin = {k: v for k, v in (r.get('margin') or {}).items() if v}
        margin_s = f'паспарту {max(margin.values())} px' if margin else '—'
        if not margin:
            res = {k: v for k, v in (r.get('residual') or {}).items() if v > 0.004}
            if res:
                margin_s = 'смягчён край: ' + ', '.join(f'{k} {v * 100:.0f} %' for k, v in res.items())
        bm = f'{b["mean"]:.1f}' if b else 'нет файла'
        bd = f'{b["dark"]:.1f}' if b else '—'
        lines.append(f'| `{r["name"]}` | {a["size"][0]}×{a["size"][1]} | {bm} | {a["mean"]:.1f} | '
                     f'{bd} | {a["dark"]:.1f} | {crop_s} | {screen_s} | {margin_s} |')

    means = [r['after']['mean'] for r in rows]
    out = [r for r in rows if r['after']['mean'] < MEAN_BAND[0] or r['after']['mean'] > MEAN_BAND[1]]
    was = [r['before']['mean'] for r in rows if r['before']]
    lines += ['', f'Итог: средняя по всем «после» — {sum(means) / len(means):.1f}, '
                  f'разброс {min(means):.1f}–{max(means):.1f}'
                  + (f'; до правки разброс был {min(was):.1f}–{max(was):.1f}.' if was else '.'), '']
    lines.append('Все снимки в полосе 95–115.' if not out else
                 'Вне полосы: ' + ', '.join(f'`{r["name"]}` ({r["after"]["mean"]:.1f})' for r in out) + '.')

    notes = []
    for r in rows:
        res = {k: v for k, v in (r.get('residual') or {}).items() if v > 0.004}
        if res and not any((r.get('margin') or {}).values()):
            notes.append(f'`{r["name"]}`: остаток бумаги '
                         + ', '.join(f'{k} {v * 100:.0f} %' for k, v in res.items())
                         + ' — срезать нельзя (лимит 10 %), край только смягчён.')
        if r.get('scale', 1) >= 2:
            notes.append(f'`{r["name"]}`: исходник мелкий, увеличение ×{r["scale"]:.1f} — мягкость ограничена сканом.')
    if any(r['name'].startswith('lindberg') for r in rows):
        notes.append('`lindberg-960.webp`: записи в `assets/` и упоминаний в `src/` нет — старая запись JOBS, '
                     'кандидат собран только для полноты.')
    notes.append('`raichman-portrait.webp`: растр с шагом 4 px на исходнике 428 px — сетка снята, но '
                 'крупные пятна тона на лице остаются из скана (это уже не растр, а дефект печати).')
    notes.append('`bso-trombones-1928.webp`: исходник 442×322, рамка 900×600 — детали лиц ограничены сканом.')
    lines += ['', '## Что осталось', ''] + [f'- {n}' for n in notes]
    dst.write_text('\n'.join(lines) + '\n', encoding='utf-8', newline='\n')


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', default=str(DEFAULT_OUT), help='куда писать результаты (по умолчанию _incoming/retouch)')
    ap.add_argument('--asset-dir', default=str(ROOT / 'assets'), help='откуда брать «до» для метрик')
    ap.add_argument('--sheet', action='store_true', help='собрать контактный лист до/после')
    ap.add_argument('--only', default='', help='обработать только файлы, в имени которых есть подстрока')
    a = ap.parse_args()

    out_dir = Path(a.out)
    if not out_dir.is_absolute():
        out_dir = ROOT / out_dir
    asset_dir = Path(a.asset_dir)

    rows, missing = [], []
    for job in JOBS:
        src_name, dst_name, size, anchor, mode, ax = job
        if a.only and a.only not in dst_name:
            continue
        src = ORIG / src_name
        if not src.exists():
            missing.append(src_name)
            continue
        dst = out_dir / dst_name
        info = process(src, dst, size, anchor, mode, ax)
        after = metrics(dst)
        before = None if dst.resolve() == (asset_dir / dst_name).resolve() else metrics(asset_dir / dst_name)
        rows.append({'name': dst_name, 'after': after, 'before': before,
                     'crop': info['crop'], 'screen': info['screen'], 'gamma': info['gamma'],
                     'margin': info['margin'], 'residual': info['residual'], 'scale': info['scale']})

        bits = [f'{dst_name:34} {after["size"][0]}×{after["size"][1]}']
        bits.append(f'средняя {after["mean"]:5.1f}')
        if before:
            bits.append(f'было {before["mean"]:5.1f}')
        if info['crop']:
            bits.append('обрезка ' + ','.join(f'{k}{v}' for k, v in sorted(info['crop'].items())))
        if info['screen'][0]:
            bits.append(f'растр {info["screen"][2]:.2f}')
        print('  '.join(bits))

    if missing:
        print('\nНЕТ ИСХОДНИКА: ' + ', '.join(missing), file=sys.stderr)

    report = ROOT / '_incoming' / 'retouch' / 'report.md'   # отчёт не публикуется вместе с сайтом
    write_report(rows, report, TARGET_MEAN)
    print(f'\nотчёт: {report.relative_to(ROOT)}')

    for r in rows:
        r['caption'] = (f'{r["name"]} · средняя {r["after"]["mean"]:.0f}'
                        + (f' (было {r["before"]["mean"]:.0f})' if r['before'] else '')
                        + f' · <40 {r["after"]["dark"]:.0f}%'
                        + (f' (было {r["before"]["dark"]:.0f}%)' if r['before'] else ''))
    if a.sheet:
        sheet = out_dir / 'sheet.png'
        size = contact_sheet(rows, asset_dir, out_dir, sheet)
        print(f'контактный лист: {sheet.relative_to(ROOT)} {size[0]}×{size[1]}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
