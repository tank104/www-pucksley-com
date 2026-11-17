"""Draw the printed pieces the sets use into blender/cache/cut: bench labels, plugin cards, a cutting mat
and a phone's screen. Plain Python with Pillow (Blender's own Python has no Pillow, so this runs first).

  python film/blender/pieces.py
"""
import math
import os

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
CUT = os.path.join(HERE, 'cache', 'cut')
FONTS = os.path.join(HERE, '..', 'fonts')
os.makedirs(CUT, exist_ok=True)

INK, PAPER = (28, 28, 30), (244, 241, 234)
YELLOW, TERRACOTTA, GREEN, BLUE, GREY = (255, 214, 10), (217, 119, 87), (48, 209, 88), (90, 150, 230), (150, 150, 154)


def font(size, weight=800):
    return ImageFont.truetype(os.path.join(FONTS, f'Nunito-w{weight}.ttf'), size)


def centred(d, xy, s, f, fill):
    d.text(xy, s, font=f, fill=fill, anchor='mm')


# ---- bench labels: what each part is, as a small card on a wire
LABELS = {'screen': ('Round touch screen', '466 × 466 AMOLED'), 'board': ('ESP32-S3', 'Wi-Fi · Bluetooth'), 'mics': ('Two microphones', 'hears you across the room'),
          'motion': ('Motion sensor', 'turn it · lift it'), 'speaker': ('Speaker', 'answers out loud'), 'battery': ('Battery', 'no cable needed'),
          'case': ('Aluminium case', '49 mm across'), 'hub': ('The hub', 'runs at home, on a NAS or PC')}
for key, (big, small) in LABELS.items():
    im = Image.new('RGB', (720, 300), PAPER)
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, 719, 14), fill=TERRACOTTA)
    centred(d, (360, 128), big, font(66, 900), INK)
    centred(d, (360, 218), small, font(40, 700), (110, 108, 104))
    im.save(os.path.join(CUT, f'label-{key}.png'))


# ---- plugin cards: one a plugin, a coloured band with a plain sign and the name under it
def sign(d, kind, cx, cy, s, c):
    w = max(6, s // 9)
    if kind == 'speaker':
        d.rounded_rectangle((cx - s * 0.5, cy - s * 0.8, cx + s * 0.5, cy + s * 0.8), radius=s * 0.14, outline=c, width=w)
        d.ellipse((cx - s * 0.28, cy - 0.02 * s, cx + s * 0.28, cy + s * 0.54), outline=c, width=w)
        d.ellipse((cx - s * 0.1, cy - s * 0.56, cx + s * 0.1, cy - s * 0.36), fill=c)
    elif kind == 'note':
        d.ellipse((cx - s * 0.55, cy + s * 0.25, cx - s * 0.05, cy + s * 0.7), fill=c)
        d.ellipse((cx + s * 0.15, cy + s * 0.05, cx + s * 0.65, cy + s * 0.5), fill=c)
        d.line((cx - s * 0.1, cy + s * 0.45, cx - s * 0.1, cy - s * 0.6, cx + s * 0.6, cy - s * 0.8, cx + s * 0.6, cy + s * 0.28), fill=c, width=w, joint='curve')
    elif kind == 'tv':
        d.rounded_rectangle((cx - s * 0.85, cy - s * 0.6, cx + s * 0.85, cy + s * 0.4), radius=s * 0.1, outline=c, width=w)
        d.line((cx - s * 0.4, cy + s * 0.68, cx + s * 0.4, cy + s * 0.68), fill=c, width=w)
    elif kind == 'plug':
        d.rounded_rectangle((cx - s * 0.45, cy - s * 0.2, cx + s * 0.45, cy + s * 0.45), radius=s * 0.16, outline=c, width=w)
        d.line((cx - s * 0.2, cy - s * 0.2, cx - s * 0.2, cy - s * 0.7), fill=c, width=w)
        d.line((cx + s * 0.2, cy - s * 0.2, cx + s * 0.2, cy - s * 0.7), fill=c, width=w)
        d.line((cx, cy + s * 0.45, cx, cy + s * 0.85), fill=c, width=w)
    elif kind == 'heat':
        for k in (-0.5, 0, 0.5):
            pts = [(cx + s * k + s * 0.14 * math.sin(t / 6 * math.pi * 2), cy - s * 0.7 + s * 1.4 * t / 24) for t in range(25)]
            d.line(pts, fill=c, width=w, joint='curve')
    elif kind == 'sun':
        d.ellipse((cx - s * 0.36, cy - s * 0.36, cx + s * 0.36, cy + s * 0.36), outline=c, width=w)
        for k in range(8):
            a = k * math.pi / 4
            d.line((cx + s * 0.56 * math.cos(a), cy + s * 0.56 * math.sin(a), cx + s * 0.82 * math.cos(a), cy + s * 0.82 * math.sin(a)), fill=c, width=w)
    elif kind == 'clock':
        d.ellipse((cx - s * 0.72, cy - s * 0.72, cx + s * 0.72, cy + s * 0.72), outline=c, width=w)
        d.line((cx, cy - s * 0.42, cx, cy, cx + s * 0.32, cy + s * 0.2), fill=c, width=w, joint='curve')
    elif kind == 'pc':
        d.rounded_rectangle((cx - s * 0.8, cy - s * 0.62, cx + s * 0.8, cy + s * 0.3), radius=s * 0.08, outline=c, width=w)
        d.line((cx, cy + s * 0.3, cx, cy + s * 0.62), fill=c, width=w)
        d.line((cx - s * 0.36, cy + s * 0.66, cx + s * 0.36, cy + s * 0.66), fill=c, width=w)
    elif kind == 'list':
        for k in (-0.45, 0, 0.45):
            d.ellipse((cx - s * 0.7, cy + s * k - s * 0.09, cx - s * 0.52, cy + s * k + s * 0.09), fill=c)
            d.line((cx - s * 0.3, cy + s * k, cx + s * 0.7, cy + s * k), fill=c, width=w)
    elif kind == 'plus':
        d.line((cx - s * 0.5, cy, cx + s * 0.5, cy), fill=c, width=w)
        d.line((cx, cy - s * 0.5, cx, cy + s * 0.5), fill=c, width=w)


PLUGINS = [('sonos', 'Sonos', 'speaker', YELLOW), ('spotify', 'Spotify', 'note', GREEN), ('tv', 'TV', 'tv', BLUE), ('plugs', 'Lamps & plugs', 'plug', YELLOW),
           ('heating', 'Heating', 'heat', TERRACOTTA), ('weather', 'Weather', 'sun', BLUE), ('timers', 'Timers', 'clock', YELLOW), ('pc', 'This PC', 'pc', GREY),
           ('lists', 'Lists & memory', 'list', GREEN)]
for key, name, kind, colour in PLUGINS:
    im = Image.new('RGB', (600, 840), PAPER)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((36, 36, 564, 560), radius=40, fill=(22, 22, 24))
    sign(d, kind, 300, 298, 150, colour)
    centred(d, (300, 668), name, font(70 if len(name) < 9 else 54, 900), INK)
    centred(d, (300, 760), 'PLUGIN', font(30, 800), (150, 146, 140))
    im.save(os.path.join(CUT, f'plugin-{key}.png'))

im = Image.new('RGB', (600, 840), PAPER)                    # the one that is still to be written
d = ImageDraw.Draw(im)
for i in range(0, 1960, 44):                                # a dashed outline, walked round the rectangle
    for a, b in ((i, i + 24),):
        for t0, t1 in ((a, b),):
            def pt(t):
                t %= 1960
                if t < 528:
                    return 36 + t, 36
                if t < 980:
                    return 564, 36 + (t - 528) * 524 / 452
                if t < 1508:
                    return 564 - (t - 980), 560
                return 36, 560 - (t - 1508) * 524 / 452
            d.line((*pt(t0), *pt(t1)), fill=(150, 146, 140), width=8)
sign(d, 'plus', 300, 298, 130, TERRACOTTA)
centred(d, (300, 668), 'Yours', font(70, 900), INK)
centred(d, (300, 760), 'ONE C# CLASS', font(30, 800), (150, 146, 140))
im.save(os.path.join(CUT, 'plugin-yours.png'))

# ---- a cutting mat
W, H = 2400, 1700
im = Image.new('RGB', (W, H), (38, 92, 74))
d = ImageDraw.Draw(im)
for x in range(100, W - 99, 20):
    d.line((x, 100, x, H - 100), fill=(64, 124, 102) if (x - 100) % 100 else (128, 180, 156), width=2 if (x - 100) % 100 else 4)
for y in range(100, H - 99, 20):
    d.line((100, y, W - 100, y), fill=(64, 124, 102) if (y - 100) % 100 else (128, 180, 156), width=2 if (y - 100) % 100 else 4)
for k, x in enumerate(range(100, W - 99, 100)):
    centred(d, (x, 60), str(k), font(30, 700), (150, 200, 176))
im.save(os.path.join(CUT, 'mat.png'))

# ---- a phone's screen: rows of apps, all grey
im = Image.new('RGB', (540, 1120), (30, 30, 32))
d = ImageDraw.Draw(im)
for r in range(6):
    for c in range(4):
        x, y = 54 + c * 120, 120 + r * 150
        g = 70 + (r * 4 + c) * 37 % 60
        d.rounded_rectangle((x, y, x + 84, y + 84), radius=20, fill=(g, g, g + 2))
im.save(os.path.join(CUT, 'phone.png'))

print('wrote', len(os.listdir(CUT)), 'pieces to', CUT)
