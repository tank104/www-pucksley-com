"""The comparison sheet for the five ideas, in ../storyboards:
  ideas-overview.jpg     every idea, a row of three frames each, with its name and what it is
  idea-N-name.jpg        one idea's three frames side by side"""
import os

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
SB = os.path.join(HERE, '..', 'storyboards')
FONTS = os.path.join(HERE, '..', 'fonts')
IDEAS = [('1', 'house', 'One puck, the whole house', 'A white card model of the house. Ask, and the room answers in light.'),
         ('2', 'bench', 'A day on the bench', 'The real kitchen at true size, breakfast to bedtime, told by the light.'),
         ('3', 'remotes', 'The last remote', 'Every grey controller in the house, in one domino run that ends at the puck.'),
         ('4', 'apart', 'Taken apart', 'For makers: what is inside, the plugins round it, the hub it talks to.'),
         ('5', 'rings', 'Turn it', 'A black studio. The ring on the screen stands behind it, as big as the room.')]
font = lambda size, weight=800: ImageFont.truetype(os.path.join(FONTS, f'Nunito-w{weight}.ttf'), size)
CW, CH, PAD, LABEL = 800, 450, 14, 76


def frames(num, key):
    files = [os.path.join(SB, f'idea-{num}-{key}-{s}.jpg') for s in ('wide', 'day', 'night')]
    return [Image.open(f).convert('RGB') for f in files] if all(os.path.exists(f) for f in files) else None


rows = [(i, frames(i[0], i[1])) for i in IDEAS]
rows = [(i, ims) for i, ims in rows if ims]
im = Image.new('RGB', (PAD + 3 * (CW + PAD), PAD + len(rows) * (LABEL + CH + PAD)), (24, 24, 26))
d = ImageDraw.Draw(im)
for r, ((num, key, title, what), ims) in enumerate(rows):
    y = PAD + r * (LABEL + CH + PAD)
    d.text((PAD + 4, y + 12), f'{num}  {title}', font=font(40, 900), fill=(245, 240, 232))
    d.text((PAD + 4 + d.textlength(f'{num}  {title}', font=font(40, 900)) + 28, y + 26), what, font=font(25, 700), fill=(217, 119, 87))
    for i, fr in enumerate(ims):
        im.paste(fr.resize((CW, CH), Image.LANCZOS), (PAD + i * (CW + PAD), y + LABEL))
    strip = Image.new('RGB', (ims[0].width * 3, ims[0].height))
    for i, fr in enumerate(ims):
        strip.paste(fr, (i * fr.width, 0))
    strip.resize((2880, 540), Image.LANCZOS).save(os.path.join(SB, f'idea-{num}-{key}.jpg'), quality=90)
im.save(os.path.join(SB, 'ideas-overview.jpg'), quality=88)
print('wrote ideas-overview.jpg', im.size)
