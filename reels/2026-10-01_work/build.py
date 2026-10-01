"""Сборка Reels «Кварцит в ванной и на кухне».

Исходники (в reels/source/, в git не хранятся):
  IMG_4701.MOV         — селфи на складе камня (iCloud-ссылка из «Фото»);
  voiceover_01-10.m4a  — закадровый текст, записан отдельно, с дублями.
Визуализации проектов бюро: reels/2026-10-01_work/img/
  (1–3 — ванная и душевая, 4–6 — кухни).

Запуск:  python3 reels/2026-10-01_work/build.py
Результат: reels/2026-10-01_work/reels.mp4
"""
from pathlib import Path
import subprocess
import tempfile

import imageio_ffmpeg
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SOURCES = {
    "mov": ROOT / "source" / "IMG_4701.MOV",
    "vo": ROOT / "source" / "voiceover_01-10.m4a",
}
FONTS = ROOT / "fonts"
IMG = HERE / "img"
ASS = HERE / "subtitles.ass"
OUT = HERE / "reels.mp4"
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()

SPEED = 1.15   # ускорение всего ролика (видео и голос, без смены тона)
FPS = 30
VO_GAIN_DB = -4.0  # выравнивание закадра по громкости с голосом со склада
SIZE = (1080, 1920)
MIX = 0.30     # длительность перетекания между планами визуализаций, с

# Звуковая дорожка: (источник, начало, конец, планы).
# Планы None — собственное видео селфи; иначе — список (план, до какого
# времени источника), None во втором поле — до конца куска.
# Из селфи вырезаны «Да вы что», «там», «Ребята» и паузы; из закадра выбраны
# лучшие дубли, убраны «Да», «Ну хотя кому-то нравится…», «И радует вас».
# Кухня — на словах о кухне, ванная — на словах о душевой.
PIECES = [
    ("mov", 0.00, 1.12, None),     # «Камень в душевую?»
    ("mov", 1.75, 6.30, None),     # «Он же покроется плесенью… всё подряд»
    ("mov", 7.05, 7.76, None),     # «Масло,»
    ("mov", 7.92, 12.45, None),    # «жир, мыло… кто-то делает?»
    ("mov", 13.88, 14.60, None),   # «Это всё мифы»
    ("mov", 15.05, 22.10, None),   # «Можно на кухню… называется кварцит»
    ("mov", 22.10, 26.35, [("k2_wide", 24.20), ("b2_wide", None)]),  # «Я в своих проектах…»
    ("vo", 2.25, 3.42, [("k1_fronts", None)]),                       # «Почему именно кварцит?»
    ("vo", 7.45, 13.40, [("k1_pan", 9.40), ("k3_wide", 11.40), ("k3_top", None)]),
    ("vo", 13.75, 16.80, [("k2_counter", None)]),                        # «столешница не царапается»
    ("vo", 16.95, 20.50, [("k2_sink", 18.70), ("k3_sink", None)]),   # «Лимон, вино, уксус…»
    ("vo", 20.95, 23.73, [("k1_texture", None)]),                    # «В отличие от мрамора»
    ("vo", 26.40, 34.45, [("k3_column", 29.10), ("k2_portal", 31.80), ("k1_sink", None)]),
    ("vo", 92.45, 95.63, [("b2_wide", 94.00), ("b1_wide", None)]),   # «в душевой… без швов»
    ("vo", 95.95, 101.51, [("b2_tilt", 98.70), ("b1_wall", None)]),  # «слэбы большого размера»
    ("vo", 101.90, 104.02, [("b1_corner", None)]),                   # «стыки во внутренних углах»
    ("vo", 113.45, 117.36, [("b2_texture", 115.40), ("k1_texture2", None)]),  # «не всё… кварцит»
    ("vo", 119.20, 121.56, [("k2_stone", None)]),                    # «каждый слэб выбираю сам»
    ("vo", 122.10, 124.58, [("b2_floor", None)]),                    # «приезжаю на склад…»
    ("vo", 126.00, 127.96, [("k3_column2", None)]),                  # «ещё до покупки»
    ("vo", 143.70, 146.22, [("k3_final", 145.45), ("b3_final", None)]),  # «кухня и ванная»
    ("vo", 147.55, 153.05, [("b3_final", 149.30), ("k2_final", 151.30), ("b1_final", None)]),  # «через 10 лет…»
    ("mov", 39.40, 41.05, None),   # «А как это использовать?»
    ("mov", 41.65, 45.75, None),   # «Знаю я, архитектор Вячеслав Деев. Контакты…»
]

# Планы: файл, (центр x, центр y, высота кадра) в начале и в конце — в долях
# картинки; кадр всегда 9:16. Затем поворот перспективы в начале и в конце
# (имитация движения камеры) и блик света по камню на крупных планах.
B1, B2, B3 = "1_dush_ugol.jpg", "2_dush_front.jpg", "3_tumba.jpg"
K1, K2, K3 = "4_kuhnya_fasady.jpg", "5_kuhnya_portal.jpg", "6_kuhnya_ostrov.jpg"
SHOTS = {
    # кухни (горизонтальные кадры — панорама вбок и наезд)
    "k1_pan": (K1, (0.24, 0.50, 0.96), (0.50, 0.52, 0.90), -0.020, 0.020, False),
    "k1_fronts": (K1, (0.30, 0.74, 0.50), (0.36, 0.72, 0.42), 0.015, -0.010, True),
    "k1_texture": (K1, (0.58, 0.77, 0.44), (0.68, 0.75, 0.40), -0.015, 0.015, True),
    "k1_texture2": (K1, (0.80, 0.74, 0.42), (0.72, 0.76, 0.38), 0.015, -0.015, True),
    "k1_sink": (K1, (0.20, 0.60, 0.62), (0.28, 0.62, 0.52), -0.015, 0.015, False),
    "k2_wide": (K2, (0.62, 0.50, 0.96), (0.42, 0.50, 0.90), 0.020, -0.020, False),
    "k2_counter": (K2, (0.30, 0.76, 0.50), (0.48, 0.78, 0.44), -0.020, 0.010, True),
    "k2_sink": (K2, (0.84, 0.62, 0.56), (0.78, 0.60, 0.48), 0.015, -0.010, False),
    "k2_portal": (K2, (0.40, 0.42, 0.90), (0.50, 0.40, 0.76), -0.015, 0.015, False),
    "k2_stone": (K2, (0.17, 0.32, 0.46), (0.19, 0.38, 0.40), 0.010, -0.015, True),
    "k2_final": (K2, (0.50, 0.46, 0.74), (0.62, 0.50, 0.96), 0.000, 0.020, False),
    "k3_wide": (K3, (0.30, 0.52, 0.96), (0.58, 0.52, 0.92), -0.020, 0.015, False),
    "k3_top": (K3, (0.40, 0.62, 0.66), (0.48, 0.62, 0.48), 0.010, -0.015, True),
    "k3_sink": (K3, (0.70, 0.60, 0.52), (0.76, 0.61, 0.44), -0.010, 0.015, False),
    "k3_column": (K3, (0.86, 0.34, 0.50), (0.86, 0.42, 0.44), 0.015, -0.010, True),
    "k3_column2": (K3, (0.87, 0.48, 0.44), (0.86, 0.38, 0.40), -0.010, 0.015, True),
    "k3_final": (K3, (0.45, 0.55, 0.80), (0.40, 0.52, 0.96), 0.015, -0.010, False),
    # ванная и душевая (вертикальные кадры — наезд, подъём камеры)
    "b1_wide": (B1, (0.50, 0.50, 0.96), (0.52, 0.47, 0.84), 0.020, -0.010, False),
    "b1_wall": (B1, (0.79, 0.34, 0.42), (0.79, 0.40, 0.38), -0.015, 0.010, True),
    "b1_corner": (B1, (0.59, 0.56, 0.53), (0.59, 0.53, 0.44), 0.015, -0.015, True),
    "b1_final": (B1, (0.50, 0.47, 0.82), (0.50, 0.50, 0.96), -0.010, 0.015, False),
    "b2_wide": (B2, (0.50, 0.50, 0.96), (0.50, 0.50, 0.82), -0.020, 0.015, False),
    "b2_tilt": (B2, (0.49, 0.64, 0.55), (0.49, 0.40, 0.55), 0.010, -0.010, True),
    "b2_texture": (B2, (0.59, 0.39, 0.44), (0.56, 0.42, 0.37), -0.015, 0.010, True),
    "b2_floor": (B2, (0.42, 0.82, 0.38), (0.58, 0.80, 0.36), 0.015, -0.015, True),
    "b3_final": (B3, (0.45, 0.58, 0.80), (0.50, 0.50, 0.96), 0.015, -0.010, False),
}

ACC = r"{\c&H9CC8E0&\b1}"   # тёплый песочный акцент
END = r"{\r}"
CUES = [
    ("mov", 0.00, 1.12, "Sub", "Камень в душевую?"),
    ("mov", 1.75, 4.20, "Sub", f"Он же покроется {ACC}плесенью{END}"),
    ("mov", 4.20, 6.30, "Sub", "будет впитывать всё подряд"),
    ("mov", 7.05, 9.40, "Sub", "Масло, жир, мыло…"),
    ("mov", 9.40, 11.35, "Sub", "Пятна будут непонятные"),
    ("mov", 11.35, 12.45, "Sub", "А ещё на кухне…"),
    ("mov", 13.88, 14.60, "Sub", f"Это всё {ACC}мифы{END}"),
    ("mov", 15.05, 17.80, "Sub", "Можно на кухню и в ванную"),
    ("mov", 17.80, 19.62, "Sub", f"постелить {ACC}натуральный камень{END}"),
    ("mov", 19.62, 21.25, "Sub", "И камень этот называется…"),
    ("mov", 21.25, 22.10, "Big", "КВАРЦИТ"),
    ("mov", 22.10, 26.35, "Sub", "Я в своих проектах\\Nиспользую этот камень"),
    ("vo", 2.25, 3.42, "Sub", "Почему именно кварцит?"),
    ("vo", 7.45, 10.95, "Sub", f"Это практически\\Nчистый {ACC}кварц{END}"),
    ("vo", 10.95, 13.40, "Sub", f"Он твёрже гранита\\Nи даже {ACC}стекла{END}"),
    ("vo", 13.75, 16.80, "Sub", f"Столешница\\Nне {ACC}царапается{END}"),
    ("vo", 16.95, 20.50, "Sub", f"{ACC}Лимон, вино, уксус{END}\\Nему не страшны"),
    ("vo", 20.95, 23.73, "Sub", "В отличие\\Nот того же мрамора"),
    ("vo", 26.40, 29.80, "Sub", "Для меня\\Nи для моих клиентов"),
    ("vo", 29.80, 34.45, "Sub", f"{ACC}пятна от вина{END} на мраморе\\Nне подходят"),
    ("vo", 92.45, 95.63, "Sub", f"В душевой я стараюсь\\Nсделать стены {ACC}без швов{END}"),
    ("vo", 95.95, 99.40, "Sub", f"Мы подберём {ACC}слэбы{END}\\N{ACC}большого размера{END}"),
    ("vo", 99.40, 101.51, "Sub", "чтобы пространство\\Nэто перекрыть"),
    ("vo", 101.90, 104.02, "Sub", f"Будут только стыки\\Nво {ACC}внутренних углах{END}"),
    ("vo", 113.45, 117.36, "Sub", "Не всё, что продают\\Nкак кварцит, им является"),
    ("vo", 119.20, 121.56, "Sub", f"Поэтому каждый слэб\\Nя {ACC}выбираю сам{END}"),
    ("vo", 122.10, 124.58, "Sub", "Приезжаю на склад\\Nи проверяю его"),
    ("vo", 126.00, 127.96, "Sub", "ещё до покупки"),
    ("vo", 143.70, 146.22, "Sub", "В итоге у моего клиента\\Nкухня и ванная"),
    ("vo", 147.55, 150.55, "Sub", f"которые через {ACC}10 лет{END}\\Nне меняются"),
    ("vo", 150.55, 153.05, "Sub", f"Выглядят как {ACC}при сдаче{END}"),
    ("mov", 39.40, 41.05, "Sub", "А как это использовать?"),
    ("mov", 41.65, 44.40, "Sub", f"Знаю я, {ACC}архитектор{END}\\NВячеслав Деев"),
    ("mov", 44.40, 45.75, "Sub", "Контакты — в описании профиля"),
]
# Хук — в координатах готового ролика до ускорения.
HOOK = (0.0, 3.6, "Hook", f"Камень в душевой —\\N{ACC}плесень и пятна?{END}")
TITLE = "КВАРЦИТ"            # постоянный заголовок сверху после первого названия камня
TITLE_FROM = ("mov", 21.25)
INSERT_LABEL = "визуализация проекта DEEV architects"
BRAND = "DEEV architects"
BRAND_FROM = ("mov", 41.65)


def out_span(src, a, b):
    """Пересечение интервала источника с фрагментами → интервал в ролике."""
    pos, start, end = 0.0, None, None
    for s, sa, sb, _ in PIECES:
        if s == src:
            lo, hi = max(a, sa), min(b, sb)
            if lo < hi:
                if start is None:
                    start = pos + lo - sa
                end = pos + hi - sa
        pos += sb - sa
    if start is None:
        raise ValueError((src, a, b))
    return start / SPEED, end / SPEED


def video_items():
    """Видеоряд: ('mov', a, b) или ('block', [(план, длительность), …]).

    Подряд идущие куски с визуализациями собираются в один блок, внутри
    которого планы перетекают друг в друга.
    """
    items = []
    for src, a, b, shots in PIECES:
        if shots is None:
            items.append(("mov", a, b))
            continue
        if not (items and items[-1][0] == "block"):
            items.append(("block", []))
        t = a
        for shot, until in shots:
            until = b if until is None else until
            block = items[-1][1]
            if block and block[-1][0] == shot:   # план продолжается в следующем куске
                block[-1] = (shot, block[-1][1] + until - t)
            else:
                block.append((shot, until - t))
            t = until
    return items


def item_duration(item):
    return item[2] - item[1] if item[0] == "mov" else sum(d for _, d in item[1])


def ts(t):
    h, t = divmod(t, 3600)
    m, s = divmod(t, 60)
    return f"{int(h)}:{int(m):02d}:{s:05.2f}"


def write_ass():
    total = sum(b - a for _, a, b, _ in PIECES) / SPEED
    # Безопасная зона Reels 1080×1920: сверху ~250 px и снизу ~420 px занимает
    # интерфейс, справа ~140 px — кнопки. Субтитры опущены до уровня груди
    # (низ текста ≈ y 1520), чтобы не закрывать лицо в селфи.
    header = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Sub,Montserrat DEEV SemiBold,58,&H00FFFFFF,&H00FFFFFF,&H20000000,&H50000000,0,0,0,0,100,100,0,0,1,5,3,2,110,170,400,1
Style: Big,Montserrat DEEV Bold,96,&H009CC8E0,&H00FFFFFF,&H20000000,&H50000000,1,0,0,0,100,100,8,0,1,5,3,2,110,170,400,1
Style: Hook,Montserrat DEEV Bold,76,&H00FFFFFF,&H00FFFFFF,&H00000000,&H64000000,1,0,0,0,100,100,0,0,1,3,3,8,100,140,330,1
Style: Title,Montserrat DEEV Bold,104,&H009CC8E0,&H00FFFFFF,&H20000000,&H50000000,1,0,0,0,100,100,14,0,1,4,3,8,100,140,280,1
Style: Label,Montserrat DEEV Regular,30,&H00FFFFFF,&H00FFFFFF,&H20000000,&H64000000,0,0,0,0,100,100,3,0,1,2,2,8,100,140,420,1
Style: Brand,Montserrat DEEV SemiBold,40,&H00FFFFFF,&H00FFFFFF,&H00000000,&H64000000,0,0,0,0,100,100,6,0,1,2,2,8,100,140,420,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    fade = r"{\fad(120,120)}"
    lines = []
    s, e, style, text = HOOK
    lines.append(f"Dialogue: 1,{ts(s / SPEED)},{ts(e / SPEED)},{style},,0,0,0,,{fade}{text}")
    for src, a, b, style, text in CUES:
        s, e = out_span(src, a, b)
        lines.append(f"Dialogue: 0,{ts(s)},{ts(e)},{style},,0,0,0,,{fade}{text}")
    s, _ = out_span(TITLE_FROM[0], TITLE_FROM[1], TITLE_FROM[1] + 0.5)
    lines.append(f"Dialogue: 1,{ts(s)},{ts(total)},Title,,0,0,0,,{fade}{TITLE}")
    # подпись «визуализация» на всё время блоков из рендеров
    pos = 0.0
    for item in video_items():
        d = item_duration(item)
        if item[0] == "block":
            lines.append(
                f"Dialogue: 1,{ts(pos / SPEED)},{ts((pos + d) / SPEED)},Label,,0,0,0,,"
                f"{fade}{INSERT_LABEL}"
            )
        pos += d
    s, _ = out_span(BRAND_FROM[0], BRAND_FROM[1], BRAND_FROM[1] + 0.5)
    lines.append(f"Dialogue: 1,{ts(s)},{ts(total)},Brand,,0,0,0,,{fade}{BRAND}")
    ASS.write_text(header + "\n".join(lines) + "\n", encoding="utf-8")


def perspective_coeffs(dst, src):
    """Коэффициенты PIL PERSPECTIVE: точки кадра dst → точки картинки src."""
    m, v = [], []
    for (x, y), (u, w) in zip(dst, src):
        m.append([x, y, 1, 0, 0, 0, -u * x, -u * y]); v.append(u)
        m.append([0, 0, 0, x, y, 1, -w * x, -w * y]); v.append(w)
    return np.linalg.solve(np.array(m, float), np.array(v, float)).tolist()


class Shot:
    """План из неподвижной визуализации: движение камеры по кадру 9:16."""

    def __init__(self, name):
        file, self.a, self.b, self.yaw0, self.yaw1, self.sheen = SHOTS[name]
        img = Image.open(IMG / file).convert("RGB")
        # уменьшаем картинку один раз так, чтобы кадр был ≈ 1:1 к выходу
        h_px = min(self.a[2], self.b[2]) * img.height
        k = min(1.0, SIZE[1] * 1.15 / h_px)
        if k < 1.0:
            img = img.resize((round(img.width * k), round(img.height * k)), Image.LANCZOS)
        self.img = img

    def frame(self, u):
        """u ∈ [0, 1] — положение внутри плана (с плавным стартом и остановкой)."""
        e = u * u * (3 - 2 * u)
        W, H = self.img.size
        cx, cy, hf = (p + (q - p) * e for p, q in zip(self.a, self.b))
        yaw = self.yaw0 + (self.yaw1 - self.yaw0) * e
        h = hf * H
        w = h * 9 / 16
        if w > W:
            w, h = W, W * 16 / 9
        x0, y0 = cx * W - w / 2, cy * H - h / 2
        # поворот перспективы: одна сторона кадра чуть выше, другая ниже
        dy = yaw * h
        quad = [(x0, y0 + dy), (x0 + w, y0 - dy), (x0 + w, y0 + h + dy), (x0, y0 + h - dy)]
        # вписываем четырёхугольник в картинку без чёрных краёв
        xs, ys = [p[0] for p in quad], [p[1] for p in quad]
        s = min(1.0, W / (max(xs) - min(xs)), H / (max(ys) - min(ys)))
        mx, my = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
        quad = [(mx + (x - mx) * s, my + (y - my) * s) for x, y in quad]
        xs, ys = [p[0] for p in quad], [p[1] for p in quad]
        sx = -min(xs) if min(xs) < 0 else (W - max(xs) if max(xs) > W else 0)
        sy = -min(ys) if min(ys) < 0 else (H - max(ys) if max(ys) > H else 0)
        quad = [(x + sx, y + sy) for x, y in quad]
        dst = [(0, 0), (SIZE[0], 0), (SIZE[0], SIZE[1]), (0, SIZE[1])]
        out = self.img.transform(SIZE, Image.PERSPECTIVE,
                                 perspective_coeffs(dst, quad), Image.BICUBIC)
        arr = np.asarray(out, dtype=np.float32)
        if self.sheen:
            arr = arr + 38.0 * sheen_mask(e)[..., None] * (1 - arr / 255.0)
        return arr


_GRID = None


def sheen_mask(e):
    """Мягкая диагональная полоса света, проходящая по камню за время плана."""
    global _GRID
    if _GRID is None:
        yy, xx = np.mgrid[0:SIZE[1], 0:SIZE[0]].astype(np.float32)
        _GRID = (xx * 0.8 + yy * 0.45) / (SIZE[0] * 0.8 + SIZE[1] * 0.45)
    p = -0.25 + 1.5 * e
    return np.exp(-((_GRID - p) / 0.11) ** 2)


def render_block(shots, path):
    """Блок визуализаций с перетеканием планов (MIX секунд) и движением камеры."""
    bounds, t = [], 0.0
    for name, d in shots:
        bounds.append((name, t, t + d))
        t += d
    n = round(t * FPS)
    cache = {}
    proc = subprocess.Popen(
        [FFMPEG, "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
         "-s", f"{SIZE[0]}x{SIZE[1]}", "-r", str(FPS), "-i", "-",
         "-c:v", "libx264", "-crf", "12", "-preset", "fast",
         "-pix_fmt", "yuv420p", str(path)],
        stdin=subprocess.PIPE,
    )
    half = MIX / 2
    for i in range(n):
        tt = (i + 0.5) / FPS
        layers = []
        for k, (name, s, e) in enumerate(bounds):
            lo = s - (half if k > 0 else 0)
            hi = e + (half if k < len(bounds) - 1 else 0)
            if lo <= tt < hi:
                if name not in cache:
                    cache[name] = Shot(name)
                u = (tt - lo) / (hi - lo)
                wgt = 1.0
                if k > 0 and tt < s + half:
                    wgt = (tt - (s - half)) / MIX
                if k < len(bounds) - 1 and tt > e - half:
                    wgt = min(wgt, ((e + half) - tt) / MIX)
                layers.append((wgt, cache[name].frame(u)))
        total = sum(w for w, _ in layers)
        frame = sum(w * f for w, f in layers) / total
        proc.stdin.write(np.clip(frame, 0, 255).astype(np.uint8).tobytes())
    proc.stdin.close()
    proc.wait()


def build():
    write_ass()
    tmp = Path(tempfile.mkdtemp())
    items = video_items()
    blocks = []
    for item in items:
        if item[0] == "block":
            path = tmp / f"block_{len(blocks)}.mp4"
            render_block(item[1], path)
            blocks.append(path)

    inputs = ["-i", str(SOURCES["mov"]), "-i", str(SOURCES["vo"])]
    for p in blocks:
        inputs += ["-i", str(p)]

    parts, vlabels, alabels = [], [], []
    block_idx = 2
    for i, item in enumerate(items):
        if item[0] == "mov":
            parts.append(
                f"[0:v]trim={item[1]}:{item[2]},setpts=PTS-STARTPTS,fps={FPS},"
                f"scale=1080:1920:flags=lanczos,setsar=1[v{i}]"
            )
        else:
            parts.append(f"[{block_idx}:v]setpts=PTS-STARTPTS,fps={FPS},setsar=1[v{i}]")
            block_idx += 1
        vlabels.append(f"[v{i}]")
    for i, (src, a, b, _) in enumerate(PIECES):
        d = b - a
        stream = "[0:a:0]" if src == "mov" else "[1:a:0]"
        extra = (
            "aformat=channel_layouts=mono,aresample=48000,"
            + (f"highpass=f=80,volume={VO_GAIN_DB}dB," if src == "vo" else "")
        )
        # короткие фейды на стыках убирают щелчки звука
        parts.append(
            f"{stream}atrim={a}:{b},asetpts=PTS-STARTPTS,{extra}"
            f"afade=t=in:d=0.03,afade=t=out:st={d - 0.05:.3f}:d=0.05[a{i}]"
        )
        alabels.append(f"[a{i}]")
    parts.append(f"{''.join(vlabels)}concat=n={len(vlabels)}:v=1:a=0[vc]")
    parts.append(f"{''.join(alabels)}concat=n={len(alabels)}:v=0:a=1[ac]")
    ass = str(ASS).replace(":", r"\:")
    fonts = str(FONTS).replace(":", r"\:")
    parts.append(
        f"[vc]setpts=PTS/{SPEED},fps={FPS},"
        f"subtitles='{ass}':fontsdir='{fonts}',format=yuv420p[vout]"
    )
    parts.append(
        f"[ac]atempo={SPEED},loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000[aout]"
    )
    cmd = [
        FFMPEG, "-y", "-v", "error", *inputs,
        "-filter_complex", ";".join(parts),
        "-map", "[vout]", "-map", "[aout]",
        "-c:v", "libx264", "-preset", "slow", "-crf", "19",
        "-profile:v", "high", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k",
        "-movflags", "+faststart", "-shortest",
        str(OUT),
    ]
    subprocess.run(cmd, check=True)
    normalize_audio()
    print(OUT)


def normalize_audio():
    """Второй проход loudnorm по измерениям первого: точно −14 LUFS, видео без перекодирования."""
    import json
    probe = subprocess.run(
        [FFMPEG, "-hide_banner", "-i", str(OUT), "-af",
         "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"],
        capture_output=True, text=True,
    ).stderr
    m = json.loads(probe[probe.rindex("{"):probe.rindex("}") + 1])
    tmp = OUT.with_suffix(".tmp.mp4")
    subprocess.run(
        [FFMPEG, "-y", "-v", "error", "-i", str(OUT), "-c:v", "copy", "-af",
         "loudnorm=I=-14:TP=-1.5:LRA=11:linear=true"
         f":measured_I={m['input_i']}:measured_TP={m['input_tp']}"
         f":measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}"
         f":offset={m['target_offset']},aresample=48000",
         "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(tmp)],
        check=True,
    )
    tmp.replace(OUT)


if __name__ == "__main__":
    build()
