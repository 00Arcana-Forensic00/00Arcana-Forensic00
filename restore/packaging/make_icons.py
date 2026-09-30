"""Generate the app icon set (icon.png, icon.ico, icon.icns) in the design-system colours.

A placeholder mark (hexagon + keyhole); replace packaging/icons/icon.png with an official
icon and re-run to regenerate the .ico/.icns. Needs Pillow.
"""
import math
import os
import sys

from PIL import Image, ImageDraw

BG, PANEL, ACCENT = (11, 15, 20), (18, 24, 33), (79, 176, 255)
OUT = os.path.join(os.path.dirname(__file__), "icons")


def hexagon(cx, cy, r):
    return [(cx + r * math.cos(math.radians(60 * i - 90)), cy + r * math.sin(math.radians(60 * i - 90))) for i in range(6)]


def draw(size=1024):
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, size - 1, size - 1), radius=size // 5, fill=BG)
    c = size / 2
    d.polygon(hexagon(c, c, size * 0.40), fill=PANEL, outline=ACCENT, width=size // 28)
    d.polygon(hexagon(c, c, size * 0.29), outline=ACCENT, width=size // 64)
    d.ellipse((c - size * 0.085, c - size * 0.15, c + size * 0.085, c + size * 0.02), fill=ACCENT)
    d.polygon([(c - size * 0.04, c), (c + size * 0.04, c), (c + size * 0.065, c + size * 0.17), (c - size * 0.065, c + size * 0.17)], fill=ACCENT)
    return im


def main():
    os.makedirs(OUT, exist_ok=True)
    png = os.path.join(OUT, "icon.png")
    im = Image.open(png).convert("RGBA") if "--from-png" in sys.argv else draw()
    im.save(png)
    im.save(os.path.join(OUT, "icon.ico"), sizes=[(s, s) for s in (16, 24, 32, 48, 64, 128, 256)])
    im.save(os.path.join(OUT, "icon.icns"))


if __name__ == "__main__":
    main()
