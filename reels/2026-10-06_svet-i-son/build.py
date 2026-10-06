"""Сборка Reels «Пульсация LED-света и ночной сон».

Исходник: Google Drive → Reels → IMG_4935.MOV (скачивается в reels/source/).
Запуск:  python3 reels/2026-10-06_svet-i-son/build.py
Результат: reels/2026-10-06_svet-i-son/reels.mp4
"""
from pathlib import Path
import subprocess

import imageio_ffmpeg

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SOURCE = ROOT / "source" / "IMG_4935.MOV"
FONTS = ROOT / "fonts"
ASS = HERE / "subtitles.ass"
OUT = HERE / "reels.mp4"

# Фрагменты исходника (секунды). Вырезаны паузы, дубли, слово «кобздец»,
# непроверенное утверждение про «космические технологии», сбивчивые повторы
# и финальные «подпишитесь… вашего интерьера» (второе лицо).
SEGMENTS = [
    (24.50, 31.45),   # «Миф, что современный светильник означает качественный свет…»
    (74.45, 81.05),   # «Захотел по нужде вечером пройтись в туалет. Включил весь свет…»
    (85.60, 88.90),   # пустой стул: включается свет (86.5 с)
    (94.75, 97.45),   # «И всё, приплыли. Сну конец»
    (138.25, 140.55), # «Яркий свет просто его убивает»
    (144.30, 154.55), # «Даже не сам свет, а пульсация… угнетают мелатонин»
    (205.15, 211.60), # «Эта проблема только у современных LED. У свечи её нет»
    (420.20, 423.05), # «Эту ситуацию можно немножко поменять»
    (433.30, 448.62), # «Использовать светильники, встроенные в стену… облачко по полу»
    (493.40, 497.50), # «Как правильно подобрать сам светильник, правильно расположить его»
    (500.30, 505.05), # «Здесь уже нужно подключать эксперта, архитектора, дизайнера»
    (505.05, 506.95), # «Контакт в описании…» (конец фразы неразборчив)
]

# Текст на экране: (начало, конец в исходнике, стиль, текст).
# Акцент — только на ключевых словах (регламент, п. 4 «Монтаж»).
ACC = r"{\c&H9CC8E0&\b1}"   # тёплый песочный акцент
END = r"{\r}"
CUES = [
    (28.90, 31.45, "Sub", "даже если за какие-то\\Nбезумные деньги"),
    (74.45, 77.40, "Sub", "Захотел по нужде вечером\\Nпройтись в туалет"),
    (77.40, 81.05, "Sub", f"{ACC}Включил{END} весь свет —\\Nхотя бы одну лампу"),
    (94.75, 97.45, "Sub", f"И всё, приплыли.\\N{ACC}Сну конец{END}"),
    (138.25, 140.55, "Sub", "Яркий свет просто\\Nего убивает"),
    (144.30, 147.40, "Sub", f"Даже не сам свет, а\\N{ACC}пульсация{END} этого света"),
    (147.40, 149.90, "Sub", "вот эти прерывистые\\Nпучки света,"),
    (149.90, 154.55, "Sub", f"которые угнетают\\Nнаш {ACC}мелатонин{END}"),
    (205.15, 208.95, "Sub", f"Эта проблема только\\Nу современных {ACC}LED{END}"),
    (208.95, 211.60, "Sub", f"У {ACC}свечи{END} этой\\Nпроблемы нет"),
    (420.20, 423.05, "Sub", "Эту ситуацию можно\\Nнемножко поменять"),
    (433.30, 436.10, "Sub", f"Светильники,\\N{ACC}встроенные в стену{END}"),
    (436.10, 444.60, "Sub", f"источник света\\N{ACC}заглублён{END} внутрь"),
    (444.60, 448.62, "Sub", f"и освещает только\\Nнебольшое облачко {ACC}по полу{END}"),
    (493.40, 495.60, "Sub", "Как правильно подобрать\\Nсам светильник,"),
    (495.60, 497.50, "Sub", "правильно\\Nрасположить его —"),
    (500.30, 505.05, "Sub", f"здесь уже нужно подключать\\N{ACC}архитектора{END}"),
    (505.05, 506.95, "Sub", "Контакт — в описании"),
]
# Надписи в координатах готового ролика.
HOOK = (0.0, 4.4, "Hook", f"{ACC}Миф:{END}\\Nсовременный светильник\\N= качественный свет")
BRAND = "DEEV architects"


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
    s, _ = out_span(500.3, 506.95)
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
