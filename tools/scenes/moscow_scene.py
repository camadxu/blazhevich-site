"""Фон шапки досье «Московская тромбоновая школа» (по макету владельца, 12.11.2026):
кремовая бумага, едва заметные плиты площади внизу, Большой зал консерватории — крупно в правом нижнем углу.
Только Pillow; запускать вручную:  python3 tools/scenes/moscow_scene.py  → assets/scene-moscow.webp (+ -960)."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageChops, ImageFilter
A = Path(__file__).resolve().parents[2] / 'assets'
W, H, HZ = 1920, 1150, 900
TOP, BOT = (247, 241, 228), (238, 228, 206)

def lerp(a, b, t): return tuple(round(x + (y - x) * t) for x, y in zip(a, b))
img = Image.new('RGBA', (W, H)); d = ImageDraw.Draw(img)
for y in range(H): d.line([(0, y), (W, y)], fill=lerp(TOP, BOT, y / H))

# плиты площади: лучи к точке схода за зданием и поперечные швы, проявляются к зрителю
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

b = Image.open(A / 'conservatory-1940s.webp').convert('RGBA')
w = 1150; h = round(b.height * w / b.width)
b = b.resize((w, h), Image.LANCZOS).filter(ImageFilter.UnsharpMask(radius=1.6, percent=70, threshold=2))
layer = Image.new('RGBA', (W, H), (0, 0, 0, 0)); layer.paste(b, (W - w + 60, H - h + 40), b)
img = Image.alpha_composite(img, layer).convert('RGB')
img.save(A / 'scene-moscow.webp', 'WEBP', quality=84, method=6)
img.crop((640, 380, 1920, 1150)).resize((960, 578), Image.LANCZOS).save(A / 'scene-moscow-960.webp', 'WEBP', quality=82, method=6)
print('ok')
