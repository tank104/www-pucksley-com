"""Make the film from its frames: give every frame the film finish, fade the last of the shot into the
closing card, and put the sound on.

  python film_join.py                                   → ../renders/pucksley-low-cut-1.mp4
  python film_join.py --src film-hd --fps 24 --crf 15 --out ../renders/pucksley-1080p-1.mp4
  options: --no-sound

Frames come from cache/<src>/f0001.png and on (film.py); finished ones go to cache/<src>-fin. The sound is
cache/film-mix.wav (film_voice.py). Every time is clock.py's.
"""
import os
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

import clock
from finish import finish

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(HERE, '..', 'fonts')
arg = lambda name, default: sys.argv[sys.argv.index('--' + name) + 1] if '--' + name in sys.argv else default
SRC = arg('src', 'film')
FPS = int(arg('fps', 12))
OUT = os.path.abspath(os.path.join(HERE, arg('out', '../renders/pucksley-low-cut-1.mp4')))
src, dst = os.path.join(HERE, 'cache', SRC), os.path.join(HERE, 'cache', SRC + '-fin')
os.makedirs(dst, exist_ok=True)
os.makedirs(os.path.dirname(OUT), exist_ok=True)

last = int(round(clock.END * FPS)) + 1
missing = [f for f in range(1, last + 1) if not os.path.exists(os.path.join(src, f'f{f:04d}.png'))]
if missing:
    raise SystemExit(f'{len(missing)} of {last} frames are not rendered yet (the first is {missing[0]})')
w, h = Image.open(os.path.join(src, 'f0001.png')).size


def card():
    """The closing card: the name, and the one line that says what it is."""
    im = Image.new('RGB', (w, h), (8, 8, 9))
    d = ImageDraw.Draw(im)
    font = lambda size, weight: ImageFont.truetype(os.path.join(FONTS, f'Nunito-w{weight}.ttf'), int(size * h / 1080))
    d.text((w / 2, h * 0.46), 'Pucksley', font=font(150, 900), fill=(245, 242, 236), anchor='mm')
    d.text((w / 2, h * 0.6), 'A voice assistant you can hold.', font=font(46, 700), fill=(217, 119, 87), anchor='mm')
    return im


end = card()
fade = int(round(clock.FADE * FPS))
for f in range(1, last + 1):
    out = os.path.join(dst, f'f{f:04d}.jpg')
    im = finish(os.path.join(src, f'f{f:04d}.png'), seed=f)
    if f > last - fade:                                      # the shot goes into the card
        u = (f - (last - fade)) / fade
        im = Image.blend(im, end, u * u * (3 - 2 * u))
    im.save(out, quality=95)
for f in range(last + 1, last + int(round(clock.CARD * FPS)) + 1):
    end.save(os.path.join(dst, f'f{f:04d}.jpg'), quality=95)

sound = os.path.join(HERE, 'cache', 'film-mix.wav')
cmd = ['ffmpeg', '-v', 'error', '-y', '-framerate', str(FPS), '-i', os.path.join(dst, 'f%04d.jpg')]
if '--no-sound' not in sys.argv and os.path.exists(sound):
    cmd += ['-i', sound, '-c:a', 'aac', '-b:a', '256k', '-shortest']
cmd += ['-c:v', 'libx264', '-crf', arg('crf', '18'), '-preset', 'slow', '-pix_fmt', 'yuv420p', '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709', '-movflags', '+faststart', OUT]
subprocess.run(cmd, check=True)
print('wrote', OUT)
