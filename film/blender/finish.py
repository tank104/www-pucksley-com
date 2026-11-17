"""The film finish, applied to a render: warm halation round the highlights, a gentle S-curve, a vignette
and grain that is stronger in the shadows. The recipe follows "The Fable of Clawd".

  python finish.py render.png out.jpg [seed]      # give each frame of a film its own seed, so the grain moves

film_join.py uses finish() directly, a whole film in one go.
"""
import sys

import numpy as np
from PIL import Image, ImageFilter


def finish(src, dst=None, seed=11, quality=93):
    """Finish the render at src. Saves it to dst if given; returns the picture."""
    a = np.asarray(Image.open(src).convert('RGB')).astype(np.float32) / 255
    h, w, _ = a.shape
    rng = np.random.default_rng(seed)

    # halation: what is brighter than 185/255 bleeds a warm glow
    lum = a @ np.array([0.2126, 0.7152, 0.0722], dtype=np.float32)
    hot = a * np.clip((lum - 185 / 255) / (1 - 185 / 255), 0, 1)[..., None]
    glow = np.asarray(Image.fromarray((hot * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(w * 0.012))).astype(np.float32) / 255
    glow = glow * np.array([1.0, 0.62, 0.36], dtype=np.float32) * 0.34
    a = 1 - (1 - a) * (1 - glow)

    # S-curve
    a = a + 0.14 * (a * a * (3 - 2 * a) - a)

    # vignette, 20% at the corners
    yy, xx = np.mgrid[0:h, 0:w]
    r2 = ((xx - w / 2) / (w / 2)) ** 2 + ((yy - h / 2) / (h / 2)) ** 2
    a = a * (1 - 0.2 * np.clip(r2 / 2, 0, 1) ** 1.2)[..., None]

    # grain, stronger in the shadows
    lum = a @ np.array([0.2126, 0.7152, 0.0722], dtype=np.float32)
    noise = rng.normal(0, 1, (h, w)).astype(np.float32)
    noise = 0.5 * noise + 0.125 * (np.roll(noise, 1, 0) + np.roll(noise, -1, 0) + np.roll(noise, 1, 1) + np.roll(noise, -1, 1))   # soften it a little
    noise = noise / noise.std()
    a = a + (noise * (0.016 - 0.009 * lum))[..., None]

    out = Image.fromarray((np.clip(a, 0, 1) * 255 + 0.5).astype(np.uint8))
    if dst:
        out.save(dst, quality=quality)
    return out


if __name__ == '__main__':
    finish(sys.argv[1], sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else 11)
    print('wrote', sys.argv[2])
