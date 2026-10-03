"""Generate the Arcalume icon set: icon.png/.ico/.icns and the store tile images.

The mark is a ring (the arc) around a light source over a document fold. Replace
packaging/icons/icon.png with a designer's icon and run with --from-png to
regenerate every other size. Needs Pillow.
"""
import os
import sys

from PIL import Image, ImageDraw

BG, PANEL, ACCENT, LIGHT = (11, 15, 20), (18, 24, 33), (92, 184, 255), (255, 211, 92)
OUT = os.path.join(os.path.dirname(__file__), "icons")
# MSIX (Microsoft Store) tiles; Mac App Store needs the 1024 px icon.png itself.
STORE_TILES = {"StoreLogo.png": (50, 50), "Square44x44Logo.png": (44, 44), "Square150x150Logo.png": (150, 150),
               "Wide310x150Logo.png": (310, 150), "LargeTile.png": (310, 310), "SplashScreen.png": (620, 300)}


def draw(size=1024):
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, size - 1, size - 1), radius=size // 5, fill=BG)
    c, s = size / 2, size
    # page
    d.rounded_rectangle((c - s * .22, c - s * .28, c + s * .22, c + s * .30), radius=s // 40, fill=PANEL, outline=ACCENT, width=s // 48)
    for i, w in enumerate((.30, .30, .22, .30, .18)):
        y = c - s * .12 + i * s * .075
        d.rounded_rectangle((c - s * .15, y, c - s * .15 + s * w, y + s * .03), radius=s // 100, fill=ACCENT)
    # arc of light
    d.arc((c - s * .40, c - s * .40, c + s * .40, c + s * .40), start=200, end=340, fill=LIGHT, width=s // 22)
    d.ellipse((c + s * .12, c - s * .36, c + s * .26, c - s * .22), fill=LIGHT)
    return im


def tiles(im):
    out = os.path.join(OUT, "store")
    os.makedirs(out, exist_ok=True)
    for name, (w, h) in STORE_TILES.items():
        side = min(w, h)
        canvas = Image.new("RGBA", (w, h), BG + (255,))
        icon = im.resize((side, side), Image.LANCZOS)
        canvas.alpha_composite(icon, ((w - side) // 2, (h - side) // 2))
        canvas.save(os.path.join(out, name))


def main():
    os.makedirs(OUT, exist_ok=True)
    png = os.path.join(OUT, "icon.png")
    im = Image.open(png).convert("RGBA") if "--from-png" in sys.argv else draw()
    im.save(png)
    im.save(os.path.join(OUT, "icon.ico"), sizes=[(s, s) for s in (16, 24, 32, 48, 64, 128, 256)])
    im.save(os.path.join(OUT, "icon.icns"))
    tiles(im)


if __name__ == "__main__":
    main()
