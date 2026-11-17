"""The comparison sheet for ideas 1 and 2 together, in ../storyboards/mix-overview.jpg: three ways, a row
of three frames each, in film order, with what each frame is under it."""
import os

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
SB = os.path.join(HERE, '..', 'storyboards')
FONTS = os.path.join(HERE, '..', 'fonts')
MIX = [('A', 'zoomin', 'House, then into it', 'Open on the model. A room lights, and the camera goes in through its open front.',
        ('The house on the desk. You ask for music; the kitchen answers.', 'Into the card kitchen. There is a tiny puck on its table.', 'The card becomes the real bench, and the day carries on there.')),
       ('B', 'zoomout', 'Bench, then out of it', 'Live on the real bench all day. At the end, pull back: it was one room of the house.',
        ('The real kitchen. Breakfast, and the first question.', 'Pulling back at dinner time: the walls are card.', 'The whole house at night, a puck in a room, the heating on.')),
       ('C', 'together', 'The house on the bench', 'No cut. The model stands on the real bench; talk to the puck, watch the house.',
        ('Morning. The real things, the model among them, the puck listening.', 'Music: the model\'s kitchen lights up beside the real pot.', 'Night. The heating comes on in every room.'))]
font = lambda size, weight=800: ImageFont.truetype(os.path.join(FONTS, f'Nunito-w{weight}.ttf'), size)
CW, CH, PAD, LABEL, CAP = 800, 450, 14, 76, 44

im = Image.new('RGB', (PAD + 3 * (CW + PAD), PAD + len(MIX) * (LABEL + CH + CAP + PAD)), (24, 24, 26))
d = ImageDraw.Draw(im)
for r, (letter, key, title, what, caps) in enumerate(MIX):
    y = PAD + r * (LABEL + CH + CAP + PAD)
    d.text((PAD + 4, y + 12), f'{letter}  {title}', font=font(40, 900), fill=(245, 240, 232))
    d.text((PAD + 4 + d.textlength(f'{letter}  {title}', font=font(40, 900)) + 28, y + 26), what, font=font(25, 700), fill=(217, 119, 87))
    for i, cap in enumerate(caps):
        f = os.path.join(SB, f'mix-{letter.lower()}-{key}-{i + 1}.jpg')
        if os.path.exists(f):
            im.paste(Image.open(f).convert('RGB').resize((CW, CH), Image.LANCZOS), (PAD + i * (CW + PAD), y + LABEL))
        d.text((PAD + i * (CW + PAD) + 4, y + LABEL + CH + 8), f'{i + 1}  {cap}', font=font(23, 700), fill=(190, 186, 178))
im.save(os.path.join(SB, 'mix-overview.jpg'), quality=90)
print('wrote mix-overview.jpg', im.size)
