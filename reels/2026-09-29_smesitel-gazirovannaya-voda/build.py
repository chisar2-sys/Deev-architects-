"""Сборка Reels «Газированная вода из смесителя».

Исходник: Google Drive → iCloud → IMG_4533.MOV (скачивается в reels/source/).
Запуск:  python3 reels/2026-09-29_smesitel-gazirovannaya-voda/build.py
Результат: reels/2026-09-29_smesitel-gazirovannaya-voda/reels.mp4
"""
from pathlib import Path
import subprocess

import imageio_ffmpeg

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SOURCE = ROOT / "source" / "IMG_4533.MOV"
FONTS = ROOT / "fonts"
ASS = HERE / "subtitles.ass"
OUT = HERE / "reels.mp4"

# Фрагменты исходника (секунды). Вырезаны паузы, обращения к зрителю
# на «вы» («смотрите», «на ваше здоровье») и реплика консультанту.
SEGMENTS = [
    (0.70, 4.00),   # «Какая штука есть! Итальянцы сделали» — смеситель
    (6.75, 10.00),  # «Допустим, я пью газированную водичку»
    (11.80, 19.60), # кнопка, «простая газированная водичка» — налив
    (23.00, 28.20), # «Можно сделать обычную водичку, холодную»
    (28.80, 32.00), # налив холодной воды
    (34.00, 36.00), # налив, деталь
    (40.05, 47.90), # глоток → «где поставить — знает архитектор» → контакт
]

# Текст на экране: (начало, конец в исходнике, стиль, текст).
# Акцент — только на ключевых словах (регламент, п. 4 «Монтаж»).
ACC = r"{\c&H9CC8E0&\b1}"   # тёплый песочный акцент
END = r"{\r}"
CUES = [
    (0.70, 4.00, "Sub", "Какая штука есть!"),
    (1.40, 4.00, "SubSmall", "Итальянцы сделали"),
    (6.90, 10.00, "Sub", f"Допустим, я пью\\N{ACC}газированную{END} водичку"),
    (13.80, 16.10, "Sub", f"Это простая\\N{ACC}газированная{END} водичка, да?"),
    (16.10, 19.60, "Sub", "— Да, она порционно даёт"),
    (23.20, 28.20, "Sub", f"Можно сделать обычную водичку —\\N{ACC}холодную{END}"),
    (42.20, 45.80, "Sub", f"Где его можно поставить —\\Nзнает {ACC}архитектор{END}"),
    (45.80, 47.90, "Sub", "Контакт — в описании профиля"),
]
# Надписи в координатах готового ролика.
HOOK = (0.0, 3.4, "Hook", f"Газированная вода —\\N{ACC}прямо из смесителя{END}")
BRAND = "DEEV architects"


def out_time(t):
    """Время исходника → время в смонтированном ролике."""
    pos = 0.0
    for a, b in SEGMENTS:
        if a <= t <= b:
            return pos + (t - a)
        pos += b - a
    raise ValueError(t)


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
    return start, end


def ts(t):
    h, t = divmod(t, 3600)
    m, s = divmod(t, 60)
    return f"{int(h)}:{int(m):02d}:{s:05.2f}"


def write_ass():
    total = sum(b - a for a, b in SEGMENTS)
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
Style: Sub,Montserrat DEEV SemiBold,62,&H00FFFFFF,&H00FFFFFF,&H00000000,&H78000000,0,0,0,0,100,100,0,0,1,3,2,2,120,160,470,1
Style: SubSmall,Montserrat DEEV Regular,50,&H00FFFFFF,&H00FFFFFF,&H00000000,&H78000000,0,0,0,0,100,100,0,0,1,3,2,2,120,160,400,1
Style: Hook,Montserrat DEEV Bold,76,&H00FFFFFF,&H00FFFFFF,&H00000000,&H64000000,1,0,0,0,100,100,0,0,1,3,3,8,100,140,330,1
Style: Brand,Montserrat DEEV SemiBold,40,&H00FFFFFF,&H00FFFFFF,&H00000000,&H64000000,0,0,0,0,100,100,6,0,1,2,2,8,100,140,270,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    fade = r"{\fad(150,150)}"
    lines = []
    s, e, style, text = HOOK
    lines.append(f"Dialogue: 1,{ts(s)},{ts(e)},{style},,0,0,0,,{fade}{text}")
    for a, b, style, text in CUES:
        s, e = out_span(a, b)
        lines.append(f"Dialogue: 0,{ts(s)},{ts(e)},{style},,0,0,0,,{fade}{text}")
    s, _ = out_span(42.2, 47.9)
    lines.append(f"Dialogue: 1,{ts(s)},{ts(total)},Brand,,0,0,0,,{fade}{BRAND}")
    ASS.write_text(header + "\n".join(lines) + "\n", encoding="utf-8")


def build():
    write_ass()
    parts, labels = [], []
    for i, (a, b) in enumerate(SEGMENTS):
        d = b - a
        parts.append(f"[0:v]trim={a}:{b},setpts=PTS-STARTPTS,fps=30[v{i}]")
        # короткие фейды на стыках убирают щелчки звука
        parts.append(
            f"[0:a:0]atrim={a}:{b},asetpts=PTS-STARTPTS,"
            f"afade=t=in:d=0.04,afade=t=out:st={d - 0.06:.3f}:d=0.06[a{i}]"
        )
        labels.append(f"[v{i}][a{i}]")
    n = len(SEGMENTS)
    parts.append(f"{''.join(labels)}concat=n={n}:v=1:a=1[vc][ac]")
    ass = str(ASS).replace(":", r"\:")
    fonts = str(FONTS).replace(":", r"\:")
    parts.append(
        "[vc]scale=1080:1920:flags=lanczos,setsar=1,"
        f"subtitles='{ass}':fontsdir='{fonts}'[vout]"
    )
    parts.append("[ac]loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000[aout]")
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
