"""Карточки-вставки из схемы «Пульсации света» (pulsation-diagram.png).

Каждая карточка: название источника света и его условный график яркости.
Запуск:  python3 reels/2026-10-06_svet-i-son/make_cards.py
Результат: reels/2026-10-06_svet-i-son/cards/*.png (1000 px в ширину).
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
FONTS = HERE.parent / "fonts"
DIAGRAM = HERE / "pulsation-diagram.png"
OUT = HERE / "cards"

# Схема нарисована в координатах 1704×2000, файл — 2070×2430.
K = 2070 / 1704
WAVE_X = (650, 1640)
# (имя файла, заголовок, строка графика по вертикали в координатах схемы)
CARDS = [
    ("candle", "Свеча", (350, 512)),
    ("incandescent", "Лампа накаливания", (563, 725)),
    ("metal-halide", "Металлогалогенная", (775, 990)),
    ("halogen", "Галогенная", (990, 1150)),
    ("led", "LED-светильник", (1420, 1622)),
]
W = 1000
PAD = 36
BG = (247, 246, 242, 255)
INK = (33, 48, 61)
MUTED = (110, 116, 120)


def card(src, title, rows):
    y0, y1 = rows
    x0, x1 = WAVE_X
    wave = src.crop((int(x0 * K), int(y0 * K), int(x1 * K), int(y1 * K)))
    ww = W - 2 * PAD
    wave = wave.resize((ww, round(wave.height * ww / wave.width)), Image.LANCZOS)
    title_font = ImageFont.truetype(str(FONTS / "MontserratDEEV-Bold.ttf"), 50)
    note_font = ImageFont.truetype(str(FONTS / "MontserratDEEV-Regular.ttf"), 26)
    h = PAD + 60 + 14 + wave.height + 12 + 32 + PAD
    img = Image.new("RGBA", (W, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((0, 0, W - 1, h - 1), radius=28, fill=BG)
    d.text((PAD, PAD), title, font=title_font, fill=INK)
    img.alpha_composite(wave.convert("RGBA"), (PAD, PAD + 74))
    d.text((PAD, h - PAD - 30), "условная схема яркости во времени",
           font=note_font, fill=MUTED)
    return img


def main():
    OUT.mkdir(exist_ok=True)
    src = Image.open(DIAGRAM).convert("RGBA")
    for name, title, rows in CARDS:
        card(src, title, rows).save(OUT / f"{name}.png")
        print(OUT / f"{name}.png")


if __name__ == "__main__":
    main()
