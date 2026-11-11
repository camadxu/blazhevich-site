"""Сцена для шапки досье «Московская тромбоновая школа»: консерватория вблизи,
Большой театр вдали, мощёная площадь в перспективе. Только Pillow; запускать вручную:
    python3 tools/scenes/moscow_scene.py
Результат: assets/scene-moscow.webp (+ -960 для телефонов)."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance, ImageChops
A = Path(__file__).resolve().parents[2] / 'assets'
W, H, HZ = 1920, 1150, 870            # холст и линия горизонта
SKY_T, SKY_B, FLOOR_B = (247, 241, 228), (240, 230, 210), (232, 219, 192)

def lerp(a, b, t): return tuple(round(x + (y - x) * t) for x, y in zip(a, b))

img = Image.new('RGBA', (W, H))
d = ImageDraw.Draw(img)
for y in range(H):                     # небо и площадь
    d.line([(0, y), (W, y)], fill=lerp(SKY_T, SKY_B, y / HZ) if y < HZ else lerp(SKY_B, FLOOR_B, (y - HZ) / (H - HZ)))

# плиты площади: лучи к точке схода у Большого театра + поперечные швы
VX = 470
floor = Image.new('RGBA', (W, H), (0, 0, 0, 0)); fd = ImageDraw.Draw(floor)
for i in range(-10, 13):
    fd.line([(VX, HZ), (VX + i * 420, H + 900)], fill=(168, 132, 58, 80), width=2)
y, step = HZ + 14, 9
while y < H:
    fd.line([(0, y), (W, y)], fill=(168, 132, 58, 55), width=2); step *= 1.45; y += step
fade = Image.linear_gradient('L').resize((W, H - HZ))          # швы проявляются к зрителю
m = Image.new('L', (W, H), 0); m.paste(fade, (0, HZ))
floor.putalpha(ImageChops.multiply(floor.getchannel('A'), m))
img = Image.alpha_composite(img, floor)

def place(name, width, x, base, alpha=1.0, haze=0.0, sharpen=False):
    global img
    b = Image.open(A / name).convert('RGBA')
    h = round(b.height * width / b.width)
    b = b.resize((width, h), Image.LANCZOS)
    if sharpen: b = b.filter(ImageFilter.UnsharpMask(radius=2, percent=90, threshold=2))
    if haze:   # воздушная перспектива: светлее и мягче
        rgb = Image.blend(b.convert('RGB'), Image.new('RGB', b.size, SKY_B), haze); rgb.putalpha(b.getchannel('A')); b = rgb
    if alpha < 1: b.putalpha(b.getchannel('A').point(lambda v: round(v * alpha)))
    layer = Image.new('RGBA', (W, H), (0, 0, 0, 0)); layer.paste(b, (x, base - h), b)
    img = Image.alpha_composite(img, layer)

# Большой театр — далеко, у точки схода
place('bolshoi-1905.webp', 360, VX - 180, HZ + 18, alpha=.85, haze=.3)
# Консерватория — близко, справа, крупно
place('conservatory-1940s.webp', 1320, 760, H - 20, sharpen=True)

img = img.convert('RGB')
img.save(A / 'scene-moscow.webp', 'WEBP', quality=84, method=6)
img.crop((300, 300, 1920, 1150)).resize((960, 504), Image.LANCZOS).save(A / 'scene-moscow-960.webp', 'WEBP', quality=82, method=6)
print('ok', img.size)
