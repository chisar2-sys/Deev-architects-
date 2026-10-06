"""Сборка Reels «Пульсация LED-света и ночной сон».

Исходник: Google Drive → Reels → IMG_4935.MOV (скачивается в reels/source/).
Карточки: python3 reels/2026-10-06_svet-i-son/make_cards.py (из pulsation-diagram.png).
Запуск:  python3 reels/2026-10-06_svet-i-son/build.py
Результат: reels/2026-10-06_svet-i-son/reels.mp4
"""
from pathlib import Path
import re
import subprocess

import imageio_ffmpeg

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SOURCE = ROOT / "source" / "IMG_4935.MOV"
FONTS = ROOT / "fonts"
CARDS_DIR = HERE / "cards"
ASS = HERE / "subtitles.ass"
OUT = HERE / "reels.mp4"
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()

# Фрагменты исходника (секунды). Вырезаны паузы, дубли, слово «кобздец»,
# «космические технологии», сбивчивые повторы, «подпишитесь… вашего интерьера»
# (второе лицо) и слова-паразиты: «да», «просто», «вот», «причём», «ну»,
# «в принципе», «такой», «как говорится», «туда», «сам».
SEGMENTS = [
    (24.50, 31.45),   # «Миф, что современный светильник означает качественный свет…»
    (74.40, 78.72),   # «Захотел по нужде вечером пройтись в туалет. Включил весь свет»
    (85.85, 88.30),   # звук щелчка выключателя (86.5 с); видео — вставка LIGHT_VIDEO
    (94.75, 97.45),   # «И всё, приплыли. Сну конец»
    (138.25, 140.55), # «Яркий свет просто его убивает»
    (144.47, 145.84), # «(Да) даже не сам свет, (а просто)
    (146.04, 147.44), #   пульсация этого света, (вот эти)
    (147.96, 150.30), #   прерывистые пучки света, которые (просто)
    (151.10, 154.55), #   угнетают наш мелатонин»
    (205.55, 208.95), # «(Причём) эта проблема только у современных светильников LED»
    (209.97, 211.60), # «У свечи этой проблемы нет,
    (233.36, 239.50), #   потому что свеча излучает ровный спокойный источник света, (который в принципе)
    (240.18, 241.45), #   не напрягает наш глаз»
    (247.70, 252.66), # «Схожий эффект мы получаем от обычной лампочки накаливания»
    (268.00, 271.58), # «Чуть хуже качество света от металлогалогеновой лампы, (ну)
    (272.45, 275.50), #   и похожее качество у обычной галогеновой лампы»
    (287.10, 291.25), # «(Ну а) если мы используем обычный LED-светильник, то тут всё, тушите свет»
    (300.50, 305.50), # «Импульсы этого LED-светильника просто убивают наш сон на раз»
    (420.45, 423.05), # «(Вот) эту ситуацию можно немножко поменять»
    (433.30, 438.04), # «…использовать светильники, встроенные в стену, у которого (сам)
    (438.42, 442.62), #   источник света находится максимально заглублен (туда)
    (443.32, 443.80), #   внутрь (сам светильника).
    (444.02, 448.62), #   И он освещает только небольшое облачко по полу»
    (493.80, 497.50), # «(А вот) как правильно подобрать сам светильник, правильно расположить его»
    (500.30, 505.05), # «Здесь уже нужно подключать эксперта, архитектора, дизайнера»
    (505.05, 506.95), # «Контакт в описании…»
]
# Вставка «включил свет»: вместо пустого стула — кадр, где автор уже сидит
# (92.25 с), сначала затемнённый «ночной», затем вспышка и горящая лампочка.
# Звук остаётся свой, со щелчком выключателя.
LIGHT = (85.85, 88.30)
LIGHT_VIDEO = 92.25
FLASH = 0.65          # момент щелчка от начала вставки
BULB_X, BULB_Y = 240, 300
# Фрагмент без речи: паузы в нём не вырезаются.
NO_TRIM = {LIGHT}

# Паузы внутри фрагментов длиннее MAX_PAUSE вырезаются, по краям остаётся KEEP.
MAX_PAUSE = 0.45
KEEP = 0.15
SILENCE_DB = -38

# Шумоподавление: срез гула ниже 80 Гц, нейросеть RNNoise для речи,
# затем мягкое FFT-подавление остаточного шума.
RNN_MODEL = ROOT / "audio-models" / "cb.rnnn"
DENOISE = (
    "highpass=f=80,"
    f"arnndn=m='{str(RNN_MODEL).replace(':', chr(92) + ':')}':mix=0.9,"
    "afftdn=nf=-35"
)

# Карточки со схемой пульсаций: (файл, начало, конец в исходнике).
# Стоят сверху, над головой, ниже зоны интерфейса Instagram.
CARDS = [
    ("candle", 209.97, 241.45),
    ("incandescent", 247.70, 252.66),
    ("metal-halide", 268.00, 271.58),
    ("halogen", 272.45, 275.50),
    ("led", 287.10, 305.50),
]
CARD_X, CARD_Y = 40, 290

# Текст на экране: (начало, конец в исходнике, стиль, текст).
# Акцент — только на ключевых словах (регламент, п. 4 «Монтаж»).
ACC = r"{\c&H9CC8E0&\b1}"   # тёплый песочный акцент
END = r"{\r}"
CUES = [
    (28.90, 31.45, "Sub", "даже если за какие-то\\Nбезумные деньги"),
    (74.45, 77.40, "Sub", "Захотел по нужде вечером\\Nпройтись в туалет"),
    (77.40, 78.72, "Sub", f"{ACC}Включил{END} весь свет"),
    (94.75, 97.45, "Sub", f"И всё, приплыли.\\N{ACC}Сну конец{END}"),
    (138.25, 140.55, "Sub", "Яркий свет просто\\Nего убивает"),
    (144.47, 147.44, "Sub", f"Даже не сам свет —\\N{ACC}пульсация{END} этого света"),
    (147.96, 150.30, "Sub", "прерывистые\\Nпучки света,"),
    (151.10, 154.55, "Sub", f"которые угнетают\\Nнаш {ACC}мелатонин{END}"),
    (205.55, 208.95, "Sub", f"Эта проблема только\\Nу современных {ACC}LED{END}"),
    (209.97, 211.60, "Sub", f"У {ACC}свечи{END} этой\\Nпроблемы нет:"),
    (233.36, 239.50, "Sub", "она излучает ровный\\Nспокойный свет,"),
    (240.18, 241.45, "Sub", "который не напрягает\\Nглаз"),
    (247.70, 252.66, "Sub", f"Схожий эффект —\\Nот {ACC}лампы накаливания{END}"),
    (268.00, 271.58, "Sub", f"Чуть хуже —\\Nу {ACC}металлогалогенной{END}"),
    (272.45, 275.50, "Sub", f"похоже —\\Nу {ACC}галогенной{END} лампы"),
    (287.10, 291.25, "Sub", f"Если это обычный {ACC}LED{END} —\\Nвсё, тушите свет"),
    (300.50, 305.50, "Sub", f"Импульсы LED\\Nубивают {ACC}сон{END} на раз"),
    (420.45, 423.05, "Sub", "Эту ситуацию можно\\Nнемножко поменять"),
    (433.30, 436.10, "Sub", f"Светильники,\\N{ACC}встроенные в стену{END}"),
    (436.10, 443.80, "Sub", f"источник света\\N{ACC}заглублён{END} внутрь"),
    (444.02, 448.62, "Sub", f"и освещает только\\Nнебольшое облачко {ACC}по полу{END}"),
    (493.80, 495.60, "Sub", "Как правильно подобрать\\Nсам светильник,"),
    (495.60, 497.50, "Sub", "правильно\\Nрасположить его —"),
    (500.30, 505.05, "Sub", f"здесь уже нужно подключать\\N{ACC}архитектора{END}"),
    (505.05, 506.95, "Sub", "Контакт — в описании"),
]
# Хук сверху — пока звучит «Миф, что современный светильник…».
HOOK = (24.50, 28.90, "Hook", f"{ACC}Миф:{END}\\Nсовременный светильник\\N= качественный свет")
BRAND = f"{ACC}DEEV{END}\\Narchitects"
# Скорость готового ролика (атемпо сохраняет высоту голоса).
SPEED = 1.15


def detect_silences():
    """Паузы в речи исходника: список (начало, конец) в секундах."""
    cmd = [
        FFMPEG, "-hide_banner", "-i", str(SOURCE),
        "-map", "0:a:0", "-af", f"silencedetect=n={SILENCE_DB}dB:d={MAX_PAUSE}",
        "-f", "null", "-",
    ]
    log = subprocess.run(cmd, capture_output=True, text=True).stderr
    starts = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", log)]
    ends = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", log)]
    return list(zip(starts, ends))


def tighten(segments, silences):
    """Разрезает фрагменты по внутренним паузам, оставляя KEEP по краям."""
    cuts = []
    for a, b in segments:
        if (a, b) in NO_TRIM:
            cuts.append((a, b))
            continue
        pos = a
        for s, e in silences:
            lo, hi = max(s, a) + KEEP, min(e, b) - KEEP
            if s < a:
                lo = a          # фрагмент начинается в паузе
            if e > b:
                hi = b          # фрагмент заканчивается в паузе
            if hi - lo > 0.05 and lo >= pos:
                if lo - pos > 0.15:
                    cuts.append((pos, lo))
                pos = hi
        if b - pos > 0.15:
            cuts.append((pos, b))
    return [(round(a, 3), round(b, 3)) for a, b in cuts]


CUTS = []   # заполняется в build(): фрагменты без пауз


def out_span(a, b):
    """Пересечение интервала исходника с фрагментами → интервал в ролике."""
    pos, start, end = 0.0, None, None
    for sa, sb in CUTS:
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
    total = sum(b - a for a, b in CUTS)
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
Style: Brand,Montserrat DEEV Bold,92,&H00FFFFFF,&H00FFFFFF,&H00000000,&H50000000,1,0,0,0,100,100,3,0,1,4,4,8,60,60,290,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    fade = r"{\fad(150,150)}"
    lines = []
    a, b, style, text = HOOK
    s, e = out_span(a, b)
    lines.append(f"Dialogue: 1,{ts(s)},{ts(e)},{style},,0,0,0,,{fade}{text}")
    for a, b, style, text in CUES:
        s, e = out_span(a, b)
        lines.append(f"Dialogue: 0,{ts(s)},{ts(e)},{style},,0,0,0,,{fade}{text}")
    s, _ = out_span(500.3, 506.95)
    lines.append(f"Dialogue: 1,{ts(s)},{ts(total)},Brand,,0,0,0,,{fade}{BRAND}")
    ASS.write_text(header + "\n".join(lines) + "\n", encoding="utf-8")


def build():
    # Границы фрагментов подобраны проверкой расшифровки каждого куска.
    CUTS[:] = tighten(SEGMENTS, detect_silences())
    before = sum(b - a for a, b in SEGMENTS)
    after = sum(b - a for a, b in CUTS)
    print(f"паузы: {len(CUTS)} кусков, {before:.1f} → {after:.1f} с, "
          f"после ускорения {after / SPEED:.1f} с")
    write_ass()
    parts, labels = [], []
    for i, (a, b) in enumerate(CUTS):
        d = b - a
        if (a, b) == LIGHT:
            # ночь → щелчок → вспышка, затем обычная яркость
            parts.append(
                f"[0:v]trim={LIGHT_VIDEO}:{LIGHT_VIDEO + d},setpts=PTS-STARTPTS,fps=30,"
                f"eq=eval=frame:brightness='if(lt(t,{FLASH}),-0.32,"
                f"0.22*exp(-(t-{FLASH})*4))':saturation='if(lt(t,{FLASH}),0.6,1)'[v{i}]"
            )
        else:
            parts.append(f"[0:v]trim={a}:{b},setpts=PTS-STARTPTS,fps=30[v{i}]")
        # короткие фейды на стыках убирают щелчки звука
        parts.append(
            f"[0:a:0]atrim={a}:{b},asetpts=PTS-STARTPTS,"
            f"afade=t=in:d=0.03,afade=t=out:st={d - 0.04:.3f}:d=0.04[a{i}]"
        )
        labels.append(f"[v{i}][a{i}]")
    n = len(CUTS)
    parts.append(f"{''.join(labels)}concat=n={n}:v=1:a=1[vc][ac]")
    parts.append("[vc]scale=1080:1920:flags=lanczos,setsar=1[v0c]")
    inputs = ["-i", str(SOURCE)]
    prev = "v0c"
    for k, (name, a, b) in enumerate(CARDS, start=1):
        inputs += ["-i", str(CARDS_DIR / f"{name}.png")]
        s, e = out_span(a, b)
        parts.append(
            f"[{prev}][{k}:v]overlay=x={CARD_X}:y={CARD_Y}:"
            f"enable='between(t,{s:.3f},{e:.3f})'[vk{k}]"
        )
        prev = f"vk{k}"
    s, e = out_span(*LIGHT)
    k = len(CARDS) + 1
    inputs += ["-i", str(CARDS_DIR / "bulb-off.png"), "-i", str(CARDS_DIR / "bulb-on.png")]
    parts.append(
        f"[{prev}][{k}:v]overlay=x={BULB_X}:y={BULB_Y}:"
        f"enable='between(t,{s:.3f},{s + FLASH:.3f})'[vb0]"
    )
    parts.append(
        f"[vb0][{k + 1}:v]overlay=x={BULB_X}:y={BULB_Y}:"
        f"enable='between(t,{s + FLASH:.3f},{e:.3f})'[vb1]"
    )
    prev = "vb1"
    ass = str(ASS).replace(":", r"\:")
    fonts = str(FONTS).replace(":", r"\:")
    parts.append(
        f"[{prev}]subtitles='{ass}':fontsdir='{fonts}',"
        # ускорение после надписей: они ускоряются вместе с речью
        f"setpts=PTS/{SPEED},fps=30[vout]"
    )
    parts.append(
        f"[ac]{DENOISE},atempo={SPEED},"
        "loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000[aout]"
    )
    cmd = [
        FFMPEG, "-y", "-v", "error", *inputs,
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
