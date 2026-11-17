"""Lay the talking face's frames (face_capture.py: 25 a second, a folder a line) onto the film's own frames:
one picture a film frame, numbered as film.py numbers them, so the puck's glass can show it as a sequence.

  python face_frames.py --fps 24      → cache/face-seq-24/f0001.jpg and on

Each is cut to the puck's round glass, as the hub cuts them for the real puck. Between lines the picture is
the face at rest; the film does not show it then.
"""
import os
import sys

from PIL import Image, ImageDraw

import clock
import film_voice

HERE = os.path.dirname(os.path.abspath(__file__))
arg = lambda name, default: sys.argv[sys.argv.index('--' + name) + 1] if '--' + name in sys.argv else default
FPS = int(arg('fps', 24))
SRC, OUT = os.path.join(HERE, 'cache', 'face'), os.path.join(HERE, 'cache', f'face-seq-{FPS}')
os.makedirs(OUT, exist_ok=True)
mask = Image.new('L', (466, 466), 0)
ImageDraw.Draw(mask).ellipse((1, 1, 465, 465), fill=255)


def glass(path):
    im = Image.open(path).convert('RGB').resize((466, 466), Image.LANCZOS)
    im = im.point(lambda v: 0 if v < 10 else v)              # near-black to black: an AMOLED's black is off
    out = Image.new('RGB', (466, 466), (0, 0, 0))
    out.paste(im, (0, 0), mask)
    return out


lines = []                                                   # when each of the puck's lines starts, and its frames
for n, (t, who, text) in enumerate(film_voice.LINES):
    folder = os.path.join(SRC, str(n))
    if who == 'P' and os.path.isdir(folder):
        lines.append((t, sorted(os.path.join(folder, f) for f in os.listdir(folder))))
rest = glass(lines[0][1][0])
made = 0
for f in range(1, int(round(clock.END * FPS)) + 2):
    t = (f - 1) / FPS
    im = rest
    for start, frames in lines:
        if start <= t < start + len(frames) / 25 + 0.5:      # a little after the last word, the last frame holds
            im = glass(frames[min(len(frames) - 1, int((t - start) * 25))])
            made += 1
    im.save(os.path.join(OUT, f'f{f:04d}.jpg'), quality=92)
print(f'wrote {OUT}: {made} frames of the face talking, at {FPS} a second')
