"""Сборка Reels «Кварцит в ванной и на кухне».

Исходники (в reels/source/, в git не хранятся):
  IMG_4701.MOV         — селфи на складе камня (iCloud-ссылка из «Фото»);
  voiceover_01-10.m4a  — закадровый текст, записан отдельно, с дублями.
Визуализации проекта бюро: reels/2026-10-01_work/img/.

Запуск:  python3 reels/2026-10-01_work/build.py
Результат: reels/2026-10-01_work/reels.mp4
"""
from pathlib import Path
import subprocess
import tempfile

import imageio_ffmpeg
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

# Звуковая дорожка: (источник, начало, конец, кадр).
# Кадр None — собственное видео селфи; иначе — план визуализации из SHOTS.
# Из селфи вырезаны «Да вы что», «там», «Ребята» и паузы; из закадра выбраны
# лучшие дубли, убраны «Да», «Ну хотя кому-то нравится…», «И радует вас».
PIECES = [
    ("mov", 0.00, 1.12, None),     # «Камень в душевую?»
    ("mov", 1.75, 6.30, None),     # «Он же покроется плесенью… всё подряд»
    ("mov", 7.05, 7.76, None),     # «Масло,»
    ("mov", 7.92, 12.45, None),    # «жир, мыло… кто-то делает?»
    ("mov", 13.88, 14.60, None),   # «Это всё мифы»
    ("mov", 15.05, 22.10, None),   # «Можно на кухню… называется кварцит»
    ("mov", 22.10, 26.35, "s1"),   # «Я в своих проектах использую этот камень»
    ("vo", 2.25, 3.42, "s2"),      # «Почему именно кварцит?»
    ("vo", 7.45, 13.40, "s2"),     # «Потому что… чистый кварц. Твёрже гранита и стекла»
    ("vo", 13.75, 16.80, "s3"),    # «Поэтому столешница не царапается на кухне»
    ("vo", 16.95, 20.50, "s3"),    # «Лимон, вино, уксус ему не страшны»
    ("vo", 20.95, 23.73, "s4"),    # «В отличие, допустим, от того же мрамора»
    ("vo", 26.40, 34.45, "s5"),    # «Для меня и моих клиентов пятнышки… не подходят»
    ("vo", 92.45, 95.63, "s6"),    # «И в душевой я стараюсь сделать стены без швов»
    ("vo", 95.95, 101.51, "s6"),   # «Мы подберём слэбы… перекрыть»
    ("vo", 101.90, 104.02, "s7"),  # «Только стыки во внутренних углах»
    ("vo", 113.45, 117.36, "s8"),  # «Не всё, что продают как кварцит, им является»
    ("vo", 119.20, 121.56, "s8"),  # «Поэтому каждый слэб я выбираю сам»
    ("vo", 122.10, 124.58, "s9"),  # «Приезжаю на склад и проверяю его»
    ("vo", 126.00, 127.96, "s9"),  # «Ещё до покупки и до заказа»
    ("vo", 143.70, 146.22, "s10"), # «В итоге у моего клиента кухня и ванная»
    ("vo", 147.55, 153.05, "s11"), # «которые через 10 лет… как при сдаче»
    ("mov", 39.40, 41.05, None),   # «А как это использовать?»
    ("mov", 41.65, 45.75, None),   # «Знаю я, архитектор Вячеслав Деев. Контакты…»
]

# Планы визуализаций: файл, (центр x, центр y, ширина кадра) в начале и в конце.
# Координаты — в пикселях исходника 1440×2560; кадр 9:16. Медленный наезд/отъезд.
SHOTS = {
    "s1": ("1_dush_ugol.jpg", (720, 1280, 1440), (720, 1200, 1250)),    # душевая целиком
    "s2": ("3_tumba.jpg", (720, 1280, 1440), (600, 1480, 1060)),        # тумба, столешница
    "s3": ("3_tumba.jpg", (560, 1640, 820), (600, 1700, 700)),          # столешница, раковина
    "s4": ("1_dush_ugol.jpg", (1140, 900, 600), (1140, 1000, 560)),     # стена из кварцита
    "s5": ("2_dush_front.jpg", (700, 1200, 820), (700, 1150, 680)),     # рисунок камня
    "s6": ("2_dush_front.jpg", (720, 1280, 1440), (720, 1300, 1180)),   # душевая без швов
    "s7": ("1_dush_ugol.jpg", (845, 1400, 760), (845, 1350, 640)),      # внутренний угол
    "s8": ("2_dush_front.jpg", (850, 1000, 640), (800, 1050, 540)),     # слэб крупно
    "s9": ("3_tumba.jpg", (330, 560, 620), (350, 600, 540)),            # слэб крупно
    "s10": ("3_tumba.jpg", (600, 1480, 1060), (720, 1280, 1440)),       # результат: ванная
    "s11": ("1_dush_ugol.jpg", (720, 1200, 1200), (720, 1280, 1440)),   # результат: душевая
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
    """Видеоряд: подряд идущие куски с одним планом склеиваются в один план."""
    items = []
    for src, a, b, shot in PIECES:
        if shot is None:
            items.append(("mov", a, b))
        elif items and items[-1][0] == "shot" and items[-1][1] == shot:
            items[-1] = ("shot", shot, items[-1][2] + (b - a))
        else:
            items.append(("shot", shot, b - a))
    return items


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
Style: Label,Montserrat DEEV Regular,30,&H00FFFFFF,&H00FFFFFF,&H00000000,&H64000000,0,0,0,0,100,100,3,0,1,2,2,8,100,140,420,1
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
    # подпись «визуализация» на всё время планов из рендеров
    pos = 0.0
    for kind, x, y in video_items():
        d = (y - x) if kind == "mov" else y
        if kind == "shot":
            lines.append(
                f"Dialogue: 1,{ts(pos / SPEED)},{ts((pos + d) / SPEED)},Label,,0,0,0,,"
                f"{INSERT_LABEL}"
            )
        pos += d
    s, _ = out_span(BRAND_FROM[0], BRAND_FROM[1], BRAND_FROM[1] + 0.5)
    lines.append(f"Dialogue: 1,{ts(s)},{ts(total)},Brand,,0,0,0,,{fade}{BRAND}")
    ASS.write_text(header + "\n".join(lines) + "\n", encoding="utf-8")


def render_shot(name, start, end, dur, path):
    """План из неподвижной визуализации: плавный наезд по кадру 9:16."""
    img = Image.open(IMG / name).convert("RGB")
    W, H = img.size
    n = max(1, round(dur * FPS))
    proc = subprocess.Popen(
        [FFMPEG, "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
         "-s", "1080x1920", "-r", str(FPS), "-i", "-",
         "-c:v", "libx264", "-crf", "12", "-preset", "fast",
         "-pix_fmt", "yuv420p", str(path)],
        stdin=subprocess.PIPE,
    )
    for i in range(n):
        k = i / max(1, n - 1)
        k = k * k * (3 - 2 * k)  # плавный старт и остановка
        cx, cy, w = (s + (e - s) * k for s, e in zip(start, end))
        h = w * 16 / 9
        x0 = min(max(cx - w / 2, 0), W - w)
        y0 = min(max(cy - h / 2, 0), H - h)
        frame = img.resize((1080, 1920), Image.LANCZOS, box=(x0, y0, x0 + w, y0 + h))
        proc.stdin.write(frame.tobytes())
    proc.stdin.close()
    proc.wait()


def build():
    write_ass()
    tmp = Path(tempfile.mkdtemp())
    items = video_items()
    shot_files = []
    for kind, x, y in items:
        if kind == "shot":
            name, start, end = SHOTS[x]
            path = tmp / f"{x}_{len(shot_files)}.mp4"
            render_shot(name, start, end, y, path)
            shot_files.append(path)

    inputs = ["-i", str(SOURCES["mov"]), "-i", str(SOURCES["vo"])]
    for p in shot_files:
        inputs += ["-i", str(p)]

    parts, vlabels, alabels = [], [], []
    shot_idx = 2
    for i, (kind, x, y) in enumerate(items):
        if kind == "mov":
            parts.append(
                f"[0:v]trim={x}:{y},setpts=PTS-STARTPTS,fps={FPS},"
                f"scale=1080:1920:flags=lanczos,setsar=1[v{i}]"
            )
        else:
            parts.append(f"[{shot_idx}:v]setpts=PTS-STARTPTS,fps={FPS},setsar=1[v{i}]")
            shot_idx += 1
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
    print(OUT)


if __name__ == "__main__":
    build()
