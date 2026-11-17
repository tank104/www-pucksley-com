"""The Pucksley logos: four marks, each with the wordmark, drawn as plain SVG paths.

  python design/logo.py              # writes design/logos/*.svg, design/logos/sheet.html and src/lib/logo.ts

The wordmark is "Pucksley" set in Nunito Black, the typeface on the puck's own screen and on the film's
closing card (film/fonts, SIL Open Font License), turned into outlines here so the logo never depends on a
font being loaded. The kerning is the font's own (its GPOS pair adjustments).

The marks are all the puck seen from above: a black disc. What is lit on it is the puck's yellow
(COL_YELLOW in the firmware, 0xFFD60A), the colour the house turns when the music starts in the film.

  dial     the volume face: the arc that follows a turn of the puck
  eyes     the two pills of the Home face, read as a face: the puck as a character
  house    the whole house, lit, on the puck
  p        the p of the wordmark, its bowl lit like the puck's screen

Which one the site uses is CHOSEN below; src/components/Logo.astro draws it from src/lib/logo.ts.
"""
import math
import os

from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.dirname(HERE)
OUT = os.path.join(HERE, 'logos')
FONT = os.path.join(SITE, 'film', 'fonts', 'Nunito-w900.ttf')

CHOSEN = 'eyes'

# The colours. Night is the film's closing card (8, 8, 9); cream is its type (245, 242, 236).
INK = '#141416'
NIGHT = '#0B0B0D'
CREAM = '#F5F2EC'
YELLOW = '#FFD60A'
TRACK = '#3A3A3E'          # the unlit part of an arc, as on the puck (between COL_GREY2 and COL_GREY3)
RIM_DARK = '#2E2E33'       # the disc's edge on a dark ground, so the puck does not vanish into it

font = TTFont(FONT)
glyphs = font.getGlyphSet()
cmap = font.getBestCmap()
hmtx = font['hmtx']
CAP = font['OS/2'].sCapHeight            # 705 of 1000
XH = font['OS/2'].sxHeight               # 484


def kerning(left, right):
    """The font's own pair adjustment, in font units, from its GPOS 'kern' lookups."""
    gpos = font['GPOS'].table
    total = 0
    seen = set()
    for rec in gpos.FeatureList.FeatureRecord:
        if rec.FeatureTag != 'kern':
            continue
        for index in rec.Feature.LookupListIndex:
            if index in seen:
                continue
            seen.add(index)
            lookup = gpos.LookupList.Lookup[index]
            for sub in lookup.SubTable:
                if lookup.LookupType == 9:
                    sub = sub.ExtSubTable
                if getattr(sub, 'LookupType', 2) != 2 or left not in sub.Coverage.glyphs:
                    continue
                if sub.Format == 1:
                    pairs = sub.PairSet[sub.Coverage.glyphs.index(left)].PairValueRecord
                    hit = next((p for p in pairs if p.SecondGlyph == right), None)
                    if hit is not None and hit.Value1 is not None:
                        total += getattr(hit.Value1, 'XAdvance', 0) or 0
                        break
                else:
                    c1 = sub.ClassDef1.classDefs.get(left, 0)
                    c2 = sub.ClassDef2.classDefs.get(right, 0)
                    value = sub.Class1Record[c1].Class2Record[c2].Value1
                    if value is not None and getattr(value, 'XAdvance', 0):
                        total += value.XAdvance
                        break
    return total


def wordmark(text='Pucksley'):
    """The word as one SVG path in font units, the baseline at y = CAP (so the caps sit on y = 0), and its width."""
    pen = SVGPathPen(glyphs)
    x, prev = 0, None
    names = [cmap[ord(ch)] for ch in text]
    for name in names:
        if prev:
            x += kerning(prev, name)
        glyphs[name].draw(TransformPen(pen, (1, 0, 0, -1, x, CAP)))
        x += hmtx[name][0]
        prev = name
    # trim the left side bearing of the first letter and the right of the last, so the word sits flush
    lsb = hmtx[names[0]][1]
    last = names[-1]
    return pen.getCommands(), lsb, x - (hmtx[last][0] - glyph_xmax(last)) - lsb


def glyph_xmax(name):
    from fontTools.pens.boundsPen import BoundsPen
    b = BoundsPen(glyphs)
    glyphs[name].draw(b)
    return b.bounds[2]


def letter_p():
    """The lowercase p, scaled to sit in a 48 box, and the circle that fills its bowl's counter."""
    from fontTools.pens.boundsPen import BoundsPen
    rec = RecordingPen()
    glyphs['p'].draw(rec)
    b = BoundsPen(glyphs)
    glyphs['p'].draw(b)
    x0, y0, x1, y1 = b.bounds
    # split into contours, find the counter: the contour whose box sits inside another's
    contours, cur = [], []
    for op, args in rec.value:
        cur.append((op, args))
        if op in ('closePath', 'endPath'):
            contours.append(cur)
            cur = []
    boxes = []
    for c in contours:
        pts = [p for _, args in c for p in args]
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        boxes.append((min(xs), min(ys), max(xs), max(ys)))
    inner = min(boxes, key=lambda bb: (bb[2] - bb[0]) * (bb[3] - bb[1]))
    s = 40 / (y1 - y0)                     # the p is 40 tall in the 48 box
    w = (x1 - x0) * s
    ox, oy = (48 - w) / 2 - x0 * s, 4 + y1 * s
    pen = SVGPathPen(glyphs)
    glyphs['p'].draw(TransformPen(pen, (s, 0, 0, -s, ox, oy)))
    cx = ox + (inner[0] + inner[2]) / 2 * s
    cy = oy - (inner[1] + inner[3]) / 2 * s
    r = min(inner[2] - inner[0], inner[3] - inner[1]) / 2 * s
    return pen.getCommands(), cx, cy, r


def arc(cx, cy, r, a0, a1):
    """An SVG arc path from angle a0 to a1 (degrees, clockwise from 3 o'clock, as SVG's y runs down)."""
    p = lambda a: (cx + r * math.cos(math.radians(a)), cy + r * math.sin(math.radians(a)))
    (x0, y0), (x1, y1) = p(a0), p(a1)
    large = 1 if (a1 - a0) % 360 > 180 else 0
    return f'M{x0:.3f} {y0:.3f}A{r} {r} 0 {large} 1 {x1:.3f} {y1:.3f}'


def disc(on):
    """The puck from above, in a 48 box."""
    if on == 'dark':
        return f'<circle cx="24" cy="24" r="22.6" fill="{INK}" stroke="{RIM_DARK}" stroke-width="1.6"/>'
    return f'<circle cx="24" cy="24" r="23.4" fill="{INK}"/>'


def mark(kind, on='light'):
    """The inner SVG of a mark, in a 48 x 48 box."""
    if kind == 'dial':
        return (disc(on)
                + f'<path d="{arc(24, 24, 14.6, 135, 405)}" fill="none" stroke="{TRACK}" stroke-width="5.2" stroke-linecap="round"/>'
                + f'<path d="{arc(24, 24, 14.6, 135, 330)}" fill="none" stroke="{YELLOW}" stroke-width="5.2" stroke-linecap="round"/>')
    if kind == 'eyes':
        return (disc(on)
                + f'<rect x="14.4" y="14.5" width="6.6" height="15.5" rx="3.3" fill="{YELLOW}"/>'
                + f'<rect x="27" y="14.5" width="6.6" height="15.5" rx="3.3" fill="{YELLOW}"/>')
    if kind == 'house':
        house = 'M24 11.6 35.2 21.4V34.2a1.6 1.6 0 0 1-1.6 1.6H14.4a1.6 1.6 0 0 1-1.6-1.6V21.4Z'
        return (disc(on)
                + f'<path d="{house}" fill="{YELLOW}" stroke="{YELLOW}" stroke-width="2" stroke-linejoin="round"/>'
                + f'<rect x="21" y="26.6" width="6" height="9.2" rx="1.2" fill="{INK}"/>')
    if kind == 'p':
        d, cx, cy, r = letter_p()
        fill = CREAM if on == 'dark' else INK
        return f'<path d="{d}" fill="{fill}"/><circle cx="{cx:.3f}" cy="{cy:.3f}" r="{r * 1.02:.3f}" fill="{YELLOW}"/>'
    raise ValueError(kind)


KINDS = {
    'dial': ('Dial', 'The volume face: the arc a turn of the puck draws. It says the one thing no other assistant does: you turn it.'),
    'eyes': ('Eyes', "The two pills of the Home face, read as a face. Pucksley as a character, which the name already is."),
    'house': ('House', 'The whole house, lit, on the puck: the film in one picture.'),
    'p': ('p', "The p of the wordmark with its bowl lit like the puck's screen. Typographic; needs no picture of the puck."),
}


def svg(width, height, body, title):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width:g} {height:g}" width="{width:g}" height="{height:g}" '
            f'role="img" aria-label="{title}"><title>{title}</title>{body}</svg>\n')


WORD, LSB, WORD_W = wordmark()
# The lockup: the mark as tall as the word's cap height plus its descender's worth (so it reads as a peer of
# the word, not a bullet), the gap a third of the mark.
MARK_H = CAP * 1.42
GAP = MARK_H * 0.30
LOCK_W = MARK_H + GAP + WORD_W
LOCK_H = MARK_H
WORD_Y = (MARK_H - CAP) / 2 - 2        # caps centred on the mark (y-descenders hang below, as type does)


def lockup(kind, on):
    word_fill = CREAM if on == 'dark' else INK
    s = MARK_H / 48
    body = (f'<g transform="scale({s:.4f})">{mark(kind, on)}</g>'
            f'<path transform="translate({MARK_H + GAP - LSB:.2f} {WORD_Y:.2f})" d="{WORD}" fill="{word_fill}"/>')
    return body


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(text)


def main():
    for kind, (name, _) in KINDS.items():
        write(os.path.join(OUT, f'pucksley-{kind}-mark.svg'), svg(48, 48, mark(kind), f'Pucksley mark: {name}'))
        write(os.path.join(OUT, f'pucksley-{kind}-mark-dark.svg'), svg(48, 48, mark(kind, 'dark'), f'Pucksley mark: {name}, on dark'))
        for on in ('light', 'dark'):
            write(os.path.join(OUT, f'pucksley-{kind}-lockup-{on}.svg'),
                  svg(LOCK_W, LOCK_H + CAP * 0.30, lockup(kind, on), 'Pucksley'))
        # the app icon: the mark on a night square, square to the edges (phones round the corners themselves)
        write(os.path.join(OUT, f'pucksley-{kind}-icon.svg'),
              svg(48, 48, f'<rect width="48" height="48" fill="{NIGHT}"/><g transform="translate(6 6) scale(0.75)">{mark(kind, "dark")}</g>',
                  'Pucksley'))
    write(os.path.join(OUT, 'pucksley-wordmark.svg'),
          svg(WORD_W, CAP * 1.30, f'<path transform="translate({-LSB} 0)" d="{WORD}" fill="{INK}"/>', 'Pucksley'))

    # the review sheet: every mark, on both grounds, at the sizes it will be seen
    cards = []
    for kind, (name, why) in KINDS.items():
        chosen = ' <em>on the site now</em>' if kind == CHOSEN else ''
        lock = lambda on: f'<svg viewBox="0 0 {LOCK_W:g} {LOCK_H + CAP * 0.3:g}" class="lock">{lockup(kind, on)}</svg>'
        small = ''.join(f'<svg viewBox="0 0 48 48" width="{px}" height="{px}">{mark(kind)}</svg>' for px in (96, 48, 32, 16))
        cards.append(f'''
<section class="card">
  <h2>{name}{chosen}</h2>
  <p>{why}</p>
  <div class="row light">{lock('light')}</div>
  <div class="row dark">{lock('dark')}</div>
  <div class="row light sizes">{small}<svg viewBox="0 0 48 48" width="96" height="96"><rect width="48" height="48" rx="10.5" fill="{NIGHT}"/><g transform="translate(6 6) scale(0.75)">{mark(kind, 'dark')}</g></svg></div>
</section>''')
    write(os.path.join(OUT, 'sheet.html'), f'''<!doctype html>
<meta charset="utf-8"><title>Pucksley logos</title>
<style>
  body {{ margin: 0; padding: 40px; background: #E9E4DA; font: 16px/1.5 system-ui, sans-serif; color: {INK}; }}
  h1 {{ margin: 0 0 24px; font-size: 28px; }}
  .grid {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 24px; }}
  .card {{ background: #fff; border-radius: 16px; padding: 24px; }}
  .card h2 {{ margin: 0 0 4px; font-size: 20px; }} .card h2 em {{ font: 600 12px system-ui; color: #8a6d00; background: #FFF3B0; padding: 2px 8px; border-radius: 99px; vertical-align: middle; }}
  .card p {{ margin: 0 0 16px; color: #555; }}
  .row {{ display: flex; align-items: center; gap: 20px; padding: 28px; border-radius: 10px; margin-top: 10px; }}
  .light {{ background: {CREAM}; }} .dark {{ background: {NIGHT}; }}
  .lock {{ height: 64px; width: auto; }}
</style>
<h1>Pucksley: four marks</h1>
<div class="grid">{''.join(cards)}</div>
''')

    # what the site draws: the chosen mark and the word, as data for Logo.astro
    write(os.path.join(SITE, 'src', 'lib', 'logo.ts'), f'''// Made by design/logo.py: do not edit by hand. Change the drawing there and run it again.
// The chosen mark ("{CHOSEN}") in a 48 x 48 box, on a light and on a dark ground, and the wordmark
// "Pucksley" in Nunito Black as outlines, with the numbers that lock them up side by side.

export const MARK = {{
  light: {mark(CHOSEN, 'light')!r},
  dark: {mark(CHOSEN, 'dark')!r},
}};

export const WORDMARK = {{
  d: {WORD!r},
  /** where the path starts (the first letter's side bearing), its width and cap height, in font units */
  lsb: {LSB},
  width: {WORD_W:.1f},
  cap: {CAP},
}};

export const LOCKUP = {{ markHeight: {MARK_H:.1f}, gap: {GAP:.1f}, width: {LOCK_W:.1f}, height: {LOCK_H + CAP * 0.30:.1f}, wordY: {WORD_Y:.1f} }};

export const COLOURS = {{ ink: '{INK}', night: '{NIGHT}', cream: '{CREAM}', yellow: '{YELLOW}' }};
''')
    print('wrote design/logos/*.svg, design/logos/sheet.html, src/lib/logo.ts')


if __name__ == '__main__':
    main()
