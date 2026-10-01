"""Сборка Reels «Кварцит в ванной и на кухне» (предварительная).

Исходник: iCloud-ссылка из «Фото» → IMG_4701.MOV (скачивается в reels/source/).
Запуск:  python3 reels/2026-10-01_work/build.py
Результат: reels/2026-10-01_work/reels.mp4
"""
from pathlib import Path
import subprocess

import imageio_ffmpeg

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SOURCE = ROOT / "source" / "IMG_4701.MOV"
FONTS = ROOT / "fonts"
ASS = HERE / "subtitles.ass"
OUT = HERE / "reels.mp4"

SPEED = 1.15  # ускорение всего ролика (видео и голос, без смены тона)

# Фрагменты исходника (секунды). Вырезаны обращения к зрителю
# («Да вы что», «Ребята»), слово-паразит «там» и длинные паузы.
SEGMENTS = [
    (0.00, 1.12),    # «Камень в душевую?»
    (1.75, 6.30),    # «Он же покроется плесенью… всё подряд»
    (7.05, 7.76),    # «Масло,»
    (7.92, 12.45),   # «жир, мыло… кто-то делает?»
    (13.88, 14.60),  # «Это всё мифы»
    (15.05, 39.15),  # «Можно на кухню… называется кварцит… воплотить в жизнь»
    (39.40, 41.05),  # «А как это использовать?»
    (41.65, 45.75),  # «Знаю я, архитектор Вячеслав Деев. Контакты…»
]

ACC = r"{\c&H9CC8E0&\b1}"   # тёплый песочный акцент
END = r"{\r}"
CUES = [
    (0.00, 1.12, "Sub", "Камень в душевую?"),
    (1.75, 4.20, "Sub", f"Он же покроется {ACC}плесенью{END}"),
    (4.20, 6.30, "Sub", "будет впитывать всё подряд"),
    (7.05, 9.40, "Sub", "Масло, жир, мыло…"),
    (9.40, 11.35, "Sub", "Пятна будут непонятные"),
    (11.35, 12.45, "Sub", "А ещё на кухне…"),
    (13.88, 14.60, "Sub", f"Это всё {ACC}мифы{END}"),
    (15.05, 17.80, "Sub", "Можно на кухню и в ванную"),
    (17.80, 19.62, "Sub", f"постелить {ACC}натуральный камень{END}"),
    (19.62, 21.25, "Sub", "И камень этот называется…"),
    (21.25, 22.10, "Big", "КВАРЦИТ"),
    (22.10, 26.35, "Sub", "Я в своих проектах\\Nиспользую этот камень"),
    (26.35, 31.20, "Sub", f"Очень большая\\Nи интересная {ACC}палитра{END}"),
    (31.20, 33.90, "Sub", "рисунка, цвета, фактуры"),
    (33.90, 35.55, "Sub", "Просто нереально"),
    (35.55, 39.15, "Sub", "Практически любое желание —\\Nвоплотить в жизнь"),
    (39.40, 41.05, "Sub", "А как это использовать?"),
    (41.65, 44.40, "Sub", f"Знаю я, {ACC}архитектор{END}\\NВячеслав Деев"),
    (44.40, 45.75, "Sub", "Контакты — в описании профиля"),
]
# Надписи в координатах готового ролика (до ускорения).
HOOK = (0.0, 3.6, "Hook", f"Камень в душевой —\\N{ACC}плесень и пятна?{END}")
BRAND = "DEEV architects"
BRAND_FROM = 41.65  # время исходника


def out_span(a, b):
    """Пересечение интервала исходника с фрагментами → интервал в ролике."""
    pos, start, end = 0.0, None, None
    for sa, sb in SEGMENTS:
        lo, hi = max(a, sa), min(b, sb)
        if lo < hi:
            if start is None:
                start = pos + lo - sa
            end = pos + hi - sa
        pos += sb - sa
    return start / SPEED, end / SPEED


def ts(t):
    h, t = divmod(t, 3600)
    m, s = divmod(t, 60)
    return f"{int(h)}:{int(m):02d}:{s:05.2f}"


def write_ass():
    total = sum(b - a for a, b in SEGMENTS) / SPEED
    # Безопасная зона Reels 1080×1920: сверху ~250 px и снизу ~420 px занимает
    # интерфейс, справа ~140 px — кнопки. Субтитры стоят в одной стабильной зоне.
    header = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Sub,Montserrat DEEV SemiBold,62,&H00FFFFFF,&H00FFFFFF,&H20000000,&H50000000,0,0,0,0,100,100,0,0,1,5,3,2,120,160,470,1
Style: Big,Montserrat DEEV Bold,96,&H009CC8E0,&H00FFFFFF,&H20000000,&H50000000,1,0,0,0,100,100,8,0,1,5,3,2,120,160,470,1
Style: Hook,Montserrat DEEV Bold,76,&H00FFFFFF,&H00FFFFFF,&H00000000,&H64000000,1,0,0,0,100,100,0,0,1,3,3,8,100,140,330,1
Style: Brand,Montserrat DEEV SemiBold,40,&H00FFFFFF,&H00FFFFFF,&H00000000,&H64000000,0,0,0,0,100,100,6,0,1,2,2,8,100,140,270,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    fade = r"{\fad(120,120)}"
    lines = []
    s, e, style, text = HOOK
    lines.append(f"Dialogue: 1,{ts(s / SPEED)},{ts(e / SPEED)},{style},,0,0,0,,{fade}{text}")
    for a, b, style, text in CUES:
        s, e = out_span(a, b)
        lines.append(f"Dialogue: 0,{ts(s)},{ts(e)},{style},,0,0,0,,{fade}{text}")
    s, _ = out_span(BRAND_FROM, SEGMENTS[-1][1])
    lines.append(f"Dialogue: 1,{ts(s)},{ts(total)},Brand,,0,0,0,,{fade}{BRAND}")
    ASS.write_text(header + "\n".join(lines) + "\n", encoding="utf-8")


def build():
    write_ass()
    parts, labels = [], []
    for i, (a, b) in enumerate(SEGMENTS):
        d = b - a
        parts.append(f"[0:v]trim={a}:{b},setpts=PTS-STARTPTS[v{i}]")
        # короткие фейды на стыках убирают щелчки звука
        parts.append(
            f"[0:a:0]atrim={a}:{b},asetpts=PTS-STARTPTS,"
            f"afade=t=in:d=0.04,afade=t=out:st={d - 0.05:.3f}:d=0.05[a{i}]"
        )
        labels.append(f"[v{i}][a{i}]")
    n = len(SEGMENTS)
    parts.append(f"{''.join(labels)}concat=n={n}:v=1:a=1[vc][ac]")
    ass = str(ASS).replace(":", r"\:")
    fonts = str(FONTS).replace(":", r"\:")
    parts.append(
        f"[vc]setpts=PTS/{SPEED},fps=30,scale=1080:1920:flags=lanczos,setsar=1,"
        f"subtitles='{ass}':fontsdir='{fonts}'[vout]"
    )
    parts.append(
        f"[ac]atempo={SPEED},loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000[aout]"
    )
    cmd = [
        imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-v", "error",
        "-i", str(SOURCE),
        "-filter_complex", ";".join(parts),
        "-map", "[vout]", "-map", "[aout]",
        "-c:v", "libx264", "-preset", "slow", "-crf", "19",
        "-profile:v", "high", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k",
        "-movflags", "+faststart",
        str(OUT),
    ]
    subprocess.run(cmd, check=True)
    print(OUT)


if __name__ == "__main__":
    build()
