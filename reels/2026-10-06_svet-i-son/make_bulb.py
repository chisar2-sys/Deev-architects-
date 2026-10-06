"""Лампочка для вставки «включил свет»: выключенная и горящая.

Запуск:  python3 reels/2026-10-06_svet-i-son/make_bulb.py
Результат: reels/2026-10-06_svet-i-son/cards/bulb-off.png, bulb-on.png (600×700).
"""
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

OUT = Path(__file__).resolve().parent / "cards"
W, H = 600, 700
CX, CY, R = 300, 300, 120     # стекло колбы
WARM = (255, 214, 140)


def bulb(lit):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    if lit:
        # мягкое тёплое свечение вокруг колбы
        y, x = np.mgrid[0:H, 0:W]
        d = np.hypot(x - CX, y - CY) / 290
        a = np.clip(1 - d, 0, 1) ** 2 * 235
        glow = np.zeros((H, W, 4), np.uint8)
        glow[..., :3] = WARM
        glow[..., 3] = a.astype(np.uint8)
        img.alpha_composite(Image.fromarray(glow, "RGBA"))
    d = ImageDraw.Draw(img)
    glass = (255, 246, 220, 255) if lit else (70, 74, 80, 200)
    edge = (255, 255, 255, 255) if lit else (200, 200, 200, 230)
    d.ellipse((CX - R, CY - R, CX + R, CY + R), fill=glass, outline=edge, width=6)
    # горлышко и цоколь
    d.polygon([(CX - 70, CY + 95), (CX + 70, CY + 95), (CX + 50, CY + 175),
               (CX - 50, CY + 175)], fill=glass, outline=edge)
    for i in range(4):
        y0 = CY + 180 + i * 26
        d.rounded_rectangle((CX - 52, y0, CX + 52, y0 + 20), radius=8,
                            fill=(150, 150, 150, 255) if not lit else (205, 200, 190, 255))
    d.ellipse((CX - 20, CY + 282, CX + 20, CY + 306), fill=(90, 90, 90, 255))
    # нить накала
    fil = (255, 160, 60, 255) if lit else (120, 120, 120, 255)
    d.line([(CX - 40, CY + 95), (CX - 40, CY + 10), (CX - 20, CY - 20), (CX, CY + 10),
            (CX + 20, CY - 20), (CX + 40, CY + 10), (CX + 40, CY + 95)],
           fill=fil, width=7, joint="curve")
    if lit:
        img = img.filter(ImageFilter.GaussianBlur(0.6))
    return img


def main():
    OUT.mkdir(exist_ok=True)
    bulb(False).save(OUT / "bulb-off.png")
    bulb(True).save(OUT / "bulb-on.png")
    print(OUT / "bulb-off.png", OUT / "bulb-on.png")


if __name__ == "__main__":
    main()
