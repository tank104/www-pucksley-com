"""The film and the pictures the website uses, made from the finished render and the puck's own screens.

  python film/web.py              makes whatever is missing
  python film/web.py --redo       makes everything again
  python film/web.py videos       only the film (also: captions, posters, stills, faces, icons)

What it writes, all under the site's public/ folder:

  videos/pucksley-<slug>.mp4          the film for the web: H.264, 1920x1080, 24 a second, under 50 MB
  videos/pucksley-<slug>-poster.jpg   1920x1080, the still shown before play
  videos/pucksley-<slug>-og.jpg       1200x630, the picture a shared link shows
  videos/pucksley-<slug>.vtt          what is said (and the few sounds that matter) as captions
  images/film/<name>-<width>.jpg      stills from the film, one for each moment of the day on the home page
  images/faces/<name>.webp            the puck's faces, as round pictures with clear corners
  og-image.jpg, favicon.svg, apple-touch-icon.png

The film is renders/pucksley-1080p-1.mp4 (blender/film_hd.sh). The faces are the simulator's pictures in
screens/ (drawn by NimbleHive/Pucksley's firmware/tools/sim). The captions' times are the voices' real
places in the mix, worked out the way blender/film_voice.py places them, from the lines it has already
spoken (blender/cache/voice): nothing is sent to a voice service.
"""
import hashlib
import os
import subprocess
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.dirname(HERE)
PUBLIC = os.path.join(SITE, 'public')
REDO = '--redo' in sys.argv
ONLY = [a for a in sys.argv[1:] if not a.startswith('--')]

# slug: (the finished film, video kbit/s, the poster's second)
FILMS = {
    'a-day': (os.path.join(HERE, 'renders', 'pucksley-1080p-1.mp4'), 4600, 52.6),
}
FILM = FILMS['a-day'][0]

# name: the second of the film it is taken from
STILLS = {
    'morning': 2.4,     # first sun on the bench, the house white and still
    'music': 15.0,      # the kitchen lit yellow, notes rising, the Home face on the puck
    'rooms': 25.6,      # the ensuite upstairs lit too
    'pasta': 31.0,      # down by the puck and the pot, the timer running
    'chime': 34.6,      # the pasta is ready; the television and the study's screen have come on
    'lamp': 43.5,       # after sunset: the TV off, the lamp on
    'heating': 52.6,    # terracotta under every floor
    'pc': 57.6,         # the study's screen gone dark
    'night': 63.0,      # everything off but the heating
}

# name: the simulator's picture in screens/. None of these shows the orange spark that the assistant's
# faces still draw (05-11, 24, 25, 27, 31, 35): it is close to Claude's own mark, and the film's script
# already asks for it to go (SCRIPT.md, "Still open"). Until the firmware replaces it, the site leaves
# those faces out.
FACES = {
    'playing': '32_film_home_playing.png',
    'home': '13_home_playing.png',
    'volume': '14_home_volume.png',
    'sonos': '15_controls_volume.png',
    'heating': '16_controls_heating.png',
    'lamp': '17_controls_lamp.png',
    'tv': '18_controls_action.png',
    'timer-new': '19_timer_new.png',
    'timer': '34_film_timer.png',
    'timer-running': '20_timer_running.png',
    'confirm': '22_confirm.png',
    'confirm-yes': '23_confirm_yes.png',
    'setup': '02_setup_portal.png',
    'setup-code': '04_setup_pending.png',
}
# The puck itself, from the film: its middle and half-width in the 1920 picture at that second, when its
# screen shows the Home face's two yellow bars.
PUCK_AT, PUCK = 15.0, (945, 806, 165)

# A few sounds belong in the captions too: the ones a deaf viewer would otherwise miss the point of.
SOUNDS = [
    (0.3, 2.3, '[Birds outside]'),
    (14.7, 16.2, '[Jazz plays, quietly]'),
    (16.4, 18.6, '[The puck is turned. The music grows]'),
    (32.0, 32.7, '[A chime]'),
    (39.7, 41.0, '[Crickets]'),
    (61.9, 64.0, '[The music stops. Only the heating stays on]'),
]
NAMES = {'Y': 'You', 'P': 'Pucksley'}


def want(path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    return REDO or not os.path.exists(path)


def run(cmd, cwd=None):
    subprocess.run(cmd, check=True, cwd=cwd)


def frame(at, width=1920):
    """The film's picture at this second."""
    tmp = os.path.join(HERE, 'renders', f'.web-frame-{at}.png')
    run(['ffmpeg', '-v', 'error', '-y', '-ss', str(at), '-i', FILM, '-frames:v', '1', tmp])
    im = Image.open(tmp).convert('RGB')
    im.load()
    os.remove(tmp)
    return im if width == im.width else im.resize((width, width * 9 // 16), Image.LANCZOS)


def videos():
    for slug, (src, kbit, _) in FILMS.items():
        dst = os.path.join(PUBLIC, 'videos', f'pucksley-{slug}.mp4')
        if want(dst):
            log = os.path.join(HERE, 'renders', f'.web-{slug}')
            rate = ['-c:v', 'libx264', '-preset', 'slow', '-tune', 'film', '-b:v', f'{kbit}k', '-maxrate', f'{kbit * 14 // 10}k',
                    '-bufsize', f'{kbit * 2}k', '-pix_fmt', 'yuv420p', '-passlogfile', log]
            run(['ffmpeg', '-v', 'error', '-y', '-i', src, '-an', *rate, '-pass', '1', '-f', 'null', '-'])
            run(['ffmpeg', '-v', 'error', '-y', '-i', src, *rate, '-pass', '2', '-colorspace', 'bt709', '-color_primaries', 'bt709',
                 '-color_trc', 'bt709', '-c:a', 'aac', '-b:a', '160k', '-ar', '48000', '-movflags', '+faststart', dst + '.part.mp4'])
            os.replace(dst + '.part.mp4', dst)
            for f in os.listdir(os.path.dirname(log)):
                if f.startswith(f'.web-{slug}'):
                    os.remove(os.path.join(os.path.dirname(log), f))
        print(f'{os.path.basename(dst)}  {os.path.getsize(dst) / 1e6:.1f} MB')


def lines():
    """Every spoken line with where it really starts and ends in the film, placed as film_voice.py places them."""
    sys.path.insert(0, os.path.join(HERE, 'blender'))
    import film_voice as fv
    out, free = [], 0.0
    for t, who, text in fv.LINES:
        path = os.path.join(fv.OUT, f'{who}-{hashlib.md5(((fv.YOU if who == "Y" else fv.PUCK) + "|" + text).encode()).hexdigest()[:10]}.wav')
        if not os.path.exists(path):
            raise SystemExit(f'{text!r} has not been spoken yet (run blender/film_voice.py first)')
        a = fv.load(path)
        start = max(t, free + 0.25)
        free = start + len(a) / fv.SR
        out.append((start, free, who, text))
    return out


def stamp(s):
    return f'{int(s // 3600):02d}:{int(s % 3600 // 60):02d}:{s % 60:06.3f}'


def captions():
    dst = os.path.join(PUBLIC, 'videos', 'pucksley-a-day.vtt')
    said = lines()
    if want(dst):
        cues = [(a, b, f'<v {NAMES[who]}>{text}') for a, b, who, text in said] + list(SOUNDS)
        cues.sort()
        text = ['WEBVTT', '']
        for i, (a, b, words) in enumerate(cues):
            nxt = cues[i + 1][0] if i + 1 < len(cues) else 68.0
            end = min(max(b + 0.4, a + 1.4), nxt - 0.05) if nxt > a + 0.5 else b
            text += [f'{stamp(a)} --> {stamp(end)}', words, '']
        with open(dst, 'w', encoding='utf-8', newline='\n') as f:
            f.write('\n'.join(text))
    for a, b, who, text in said:
        print(f'{a:5.1f} {b:5.1f}  {who}  {text}')


def share(im):
    """1920x1080 -> 1200x630, cut from the middle."""
    im = im.resize((1200, 675), Image.LANCZOS)
    return im.crop((0, 22, 1200, 652))


def posters():
    for slug, (_, _, at) in FILMS.items():
        poster = os.path.join(PUBLIC, 'videos', f'pucksley-{slug}-poster.jpg')
        og = os.path.join(PUBLIC, 'videos', f'pucksley-{slug}-og.jpg')
        site_og = os.path.join(PUBLIC, 'og-image.jpg')
        if want(poster) or want(og) or want(site_og):
            im = frame(at)
            im.save(poster, quality=86, optimize=True, progressive=True)
            share(im).save(og, quality=86, optimize=True, progressive=True)
            share(im).save(site_og, quality=86, optimize=True, progressive=True)
        print(os.path.basename(poster), os.path.getsize(poster) // 1000, 'KB')


def stills():
    for name, at in STILLS.items():
        dsts = {w: os.path.join(PUBLIC, 'images', 'film', f'{name}-{w}.jpg') for w in (1280, 640)}
        if any(want(d) for d in dsts.values()):
            im = frame(at)
            for w, d in dsts.items():
                im.resize((w, w * 9 // 16), Image.LANCZOS).save(d, quality=82, optimize=True, progressive=True)
        print(f'film/{name}', os.path.getsize(dsts[1280]) // 1000, 'KB')


def round_webp(im, dst):
    """A square picture as a round one, its corners clear, at 360 pixels."""
    k = 4
    mask = Image.new('L', (im.width * k, im.height * k), 0)
    ImageDraw.Draw(mask).ellipse((k, k, im.width * k - k, im.height * k - k), fill=255)
    im.putalpha(mask.resize(im.size, Image.LANCZOS))
    im.resize((360, 360), Image.LANCZOS).save(dst, quality=90, method=6)


def faces():
    """Each face as a round picture; and the puck itself, cut from the film, for "tap it and talk"."""
    for name, src in FACES.items():
        dst = os.path.join(PUBLIC, 'images', 'faces', f'{name}.webp')
        if want(dst):
            round_webp(Image.open(os.path.join(HERE, 'screens', src)).convert('RGB'), dst)
        print(f'faces/{name}', os.path.getsize(dst) // 1000, 'KB')
    dst = os.path.join(PUBLIC, 'images', 'faces', 'puck.webp')
    if want(dst):
        x, y, r = PUCK
        round_webp(frame(PUCK_AT).crop((x - r, y - r, x + r, y + r)), dst)
    print('faces/puck', os.path.getsize(dst) // 1000, 'KB')


def icons():
    """The favicon is the chosen mark (design/logo.py); the phone's icon is the mark on night, as a PNG."""
    sys.path.insert(0, os.path.join(SITE, 'design'))
    import logo
    svg = os.path.join(PUBLIC, 'favicon.svg')
    if want(svg):
        with open(os.path.join(SITE, 'design', 'logos', f'pucksley-{logo.CHOSEN}-mark.svg'), encoding='utf-8') as f:
            text = f.read().replace(' width="48" height="48"', '')
        with open(svg, 'w', encoding='utf-8', newline='\n') as f:
            f.write(text)
    touch = os.path.join(PUBLIC, 'apple-touch-icon.png')
    if want(touch):
        icon = os.path.join(SITE, 'design', 'logos', f'pucksley-{logo.CHOSEN}-icon.svg').replace('\\', '/')
        script = (
            "const { chromium } = require('playwright-core');"
            "(async () => { const b = await chromium.launch({ channel: 'chrome' });"
            "const p = await b.newPage({ viewport: { width: 180, height: 180 } });"
            f"await p.setContent(`<style>body{{margin:0}}svg{{display:block;width:180px;height:180px}}</style>${{require('fs').readFileSync('{icon}', 'utf8')}}`);"
            f"await p.screenshot({{ path: '{touch.replace(chr(92), '/')}' }}); await b.close(); }})();")
        run(['node', '-e', script], cwd=SITE)          # playwright-core is in the site's devDependencies
    print('favicon.svg, apple-touch-icon.png')


if __name__ == '__main__':
    for step in (videos, captions, posters, stills, faces, icons):
        if not ONLY or step.__name__ in ONLY:
            step()
