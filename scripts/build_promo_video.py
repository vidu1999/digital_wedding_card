#!/usr/bin/env python3
"""Build the vertical promo reel for the Anjali & Kavindu invitation."""
from __future__ import annotations

import math
import subprocess
import tempfile
import wave
from pathlib import Path

import numpy as np
import qrcode
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont
from imageio_ffmpeg import get_ffmpeg_exe

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
OUTPUT = ASSETS / "wedding-invitation-promo.mp4"
POSTER = ASSETS / "wedding-invitation-promo-poster.jpg"
PORUWA = ASSETS / "poruwa-hero.png"
LAMP = ASSETS / "lotus-lamp.png"
QR_URL = "https://vidu1999.github.io/digital_wedding_card/"

WIDTH, HEIGHT = 1080, 1920
FPS = 24
SEGMENT = 4.6
TRANSITION = 0.45
SCENE_STEP = SEGMENT - TRANSITION
SCENE_COUNT = 5
DURATION = SCENE_COUNT * SEGMENT - (SCENE_COUNT - 1) * TRANSITION

PAPER = (248, 246, 239, 255)
PAPER_LIGHT = (255, 253, 247, 255)
FOREST = (23, 62, 50, 255)
FOREST_DEEP = (16, 46, 38, 255)
GOLD = (217, 189, 141, 255)
GOLD_DEEP = (183, 141, 85, 255)
MUTED = (115, 124, 112, 255)
SERIF_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"
SERIF_BOLD_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
SANS_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
SANS_BOLD_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

FONT_CACHE: dict[tuple[str, int], ImageFont.FreeTypeFont] = {}

def font(path: str, size: int) -> ImageFont.FreeTypeFont:
    key = (path, size)
    if key not in FONT_CACHE:
        FONT_CACHE[key] = ImageFont.truetype(path, size=size)
    return FONT_CACHE[key]


def text_width(draw: ImageDraw.ImageDraw, text: str, ft: ImageFont.FreeTypeFont, tracking: int = 0) -> float:
    if tracking <= 0 or len(text) < 2:
        return draw.textlength(text, font=ft)
    return sum(draw.textlength(char, font=ft) for char in text) + tracking * (len(text) - 1)


def draw_at_center(
    draw: ImageDraw.ImageDraw,
    text: str,
    center_x: int,
    y: int,
    ft: ImageFont.FreeTypeFont,
    color: tuple[int, int, int, int],
    tracking: int = 0,
    stroke_width: int = 0,
    stroke_fill: tuple[int, int, int, int] = (0, 0, 0, 0),
) -> int:
    width = text_width(draw, text, ft, tracking)
    x = center_x - width / 2
    if tracking <= 0:
        bbox = draw.textbbox((0, 0), text, font=ft, stroke_width=stroke_width)
        draw.text((x - bbox[0], y - bbox[1]), text, font=ft, fill=color,
                  stroke_width=stroke_width, stroke_fill=stroke_fill)
    else:
        for char in text:
            draw.text((x, y), char, font=ft, fill=color,
                      stroke_width=stroke_width, stroke_fill=stroke_fill)
            x += draw.textlength(char, font=ft) + tracking
    return y + ft.size


def draw_center(
    draw: ImageDraw.ImageDraw,
    text: str,
    y: int,
    ft: ImageFont.FreeTypeFont,
    color: tuple[int, int, int, int],
    tracking: int = 0,
    stroke_width: int = 0,
    stroke_fill: tuple[int, int, int, int] = (0, 0, 0, 0),
) -> int:
    return draw_at_center(draw, text, WIDTH // 2, y, ft, color, tracking,
                          stroke_width, stroke_fill)


def draw_left(draw: ImageDraw.ImageDraw, text: str, x: int, y: int,
              ft: ImageFont.FreeTypeFont, color: tuple[int, int, int, int]) -> None:
    bbox = draw.textbbox((0, 0), text, font=ft)
    draw.text((x, y - bbox[1]), text, font=ft, fill=color)


def draw_rule(draw: ImageDraw.ImageDraw, y: int, span: int = 280,
              color: tuple[int, int, int, int] = GOLD) -> None:
    cx = WIDTH // 2
    draw.line((cx - span // 2, y, cx - 14, y), fill=color, width=2)
    draw.line((cx + 14, y, cx + span // 2, y), fill=color, width=2)
    draw.polygon([(cx, y - 7), (cx + 7, y), (cx, y + 7), (cx - 7, y)], fill=color)


def draw_lotus(draw: ImageDraw.ImageDraw, cx: int, cy: int, size: int,
               color: tuple[int, int, int, int] = GOLD, width: int = 2) -> None:
    r = size / 2
    draw.ellipse((cx - r, cy - r, cx + r, cy + r), outline=color, width=width)
    # A small three-petal lotus mark, echoed from the invitation's emblem.
    draw.line([(cx, cy + r * .30), (cx - r * .20, cy - r * .20),
               (cx, cy - r * .68), (cx + r * .20, cy - r * .20),
               (cx, cy + r * .30)], fill=color, width=width, joint="curve")
    draw.line([(cx, cy + r * .20), (cx - r * .30, cy - r * .05),
               (cx - r * .69, cy - r * .04), (cx - r * .45, cy + r * .25),
               (cx, cy + r * .26)], fill=color, width=width, joint="curve")
    draw.line([(cx, cy + r * .20), (cx + r * .30, cy - r * .05),
               (cx + r * .69, cy - r * .04), (cx + r * .45, cy + r * .25),
               (cx, cy + r * .26)], fill=color, width=width, joint="curve")
    draw.line((cx - r * .50, cy + r * .48, cx + r * .50, cy + r * .48), fill=color, width=width)


def add_border(draw: ImageDraw.ImageDraw, inset: int = 38, radius: int = 20,
               color: tuple[int, int, int, int] = (217, 189, 141, 175)) -> None:
    draw.rounded_rectangle((inset, inset, WIDTH - inset, HEIGHT - inset),
                           radius=radius, outline=color, width=2)


def center_label(draw: ImageDraw.ImageDraw, text: str, y: int,
                  color: tuple[int, int, int, int] = GOLD, size: int = 21,
                  tracking: int = 4) -> None:
    draw_center(draw, text.upper(), y, font(SANS_BOLD_PATH, size), color, tracking=tracking)


def make_tint(alpha_top: int, alpha_mid: int, alpha_bottom: int,
              color: tuple[int, int, int] = (10, 29, 22)) -> Image.Image:
    stops = ((0.0, alpha_top), (0.48, alpha_mid), (1.0, alpha_bottom))
    column = Image.new("RGBA", (1, HEIGHT))
    pix = []
    for y in range(HEIGHT):
        p = y / max(1, HEIGHT - 1)
        for idx in range(len(stops) - 1):
            if stops[idx][0] <= p <= stops[idx + 1][0]:
                (p0, a0), (p1, a1) = stops[idx], stops[idx + 1]
                q = (p - p0) / (p1 - p0)
                alpha = round(a0 + (a1 - a0) * q)
                break
        else:
            alpha = stops[-1][1]
        pix.append((*color, alpha))
    column.putdata(pix)
    return column.resize((WIDTH, HEIGHT), Image.Resampling.BILINEAR)


def prepare_photo(path: Path) -> Image.Image:
    image = Image.open(path).convert("RGB")
    overscan_w, overscan_h = round(WIDTH * 1.16), round(HEIGHT * 1.16)
    scale = max(overscan_w / image.width, overscan_h / image.height)
    size = (round(image.width * scale), round(image.height * scale))
    return image.resize(size, Image.Resampling.LANCZOS)


def pan_crop(image: Image.Image, progress: float, focus_x: float = .5,
             focus_y: float = .5, direction: float = 1.0) -> Image.Image:
    zoom = 1.035 + .038 * progress
    crop_w, crop_h = round(WIDTH / zoom), round(HEIGHT / zoom)
    extra_x, extra_y = max(0, image.width - crop_w), max(0, image.height - crop_h)
    fx = min(1.0, max(0.0, focus_x + direction * .045 * (progress - .5)))
    fy = min(1.0, max(0.0, focus_y + .035 * (progress - .5)))
    left, top = round(extra_x * fx), round(extra_y * fy)
    return image.crop((left, top, left + crop_w, top + crop_h)).resize(
        (WIDTH, HEIGHT), Image.Resampling.LANCZOS)


def gradient_background(top: tuple[int, int, int], bottom: tuple[int, int, int],
                        accent: tuple[int, int, int] | None = None) -> Image.Image:
    rows = np.linspace(0.0, 1.0, HEIGHT, dtype=np.float32)[:, None, None]
    upper = np.array(top, dtype=np.float32)[None, None, :]
    lower = np.array(bottom, dtype=np.float32)[None, None, :]
    arr = upper * (1 - rows) + lower * rows
    arr = np.broadcast_to(arr, (HEIGHT, WIDTH, 3)).copy()
    if accent:
        # Very restrained radial glow behind the center of the layout.
        yy, xx = np.mgrid[0:HEIGHT:1, 0:WIDTH:1]
        glow = np.exp(-(((xx - WIDTH * .52) / (WIDTH * .78)) ** 2 +
                        ((yy - HEIGHT * .38) / (HEIGHT * .53)) ** 2) * 3.0)[..., None]
        arr = arr * (1 - glow * .09) + np.array(accent, dtype=np.float32) * glow * .09
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB")


def screen_shadow() -> Image.Image:
    shadow = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    d = ImageDraw.Draw(shadow)
    d.rounded_rectangle((190, 565, 890, 1680), radius=94, fill=(15, 35, 26, 95))
    return shadow.filter(ImageFilter.GaussianBlur(30))


def draw_scene_1() -> Image.Image:
    overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    add_border(d, inset=43, radius=24)
    draw_lotus(d, WIDTH // 2, 253, 110, width=2)
    center_label(d, "A Sri Lankan wedding invitation", 354, size=18, tracking=4)
    draw_center(d, "A little bit of", 640, font(SERIF_PATH, 88), PAPER_LIGHT, stroke_width=1,
                stroke_fill=(8, 23, 17, 110))
    draw_center(d, "home", 760, font(SERIF_PATH, 155), PAPER_LIGHT, stroke_width=1,
                stroke_fill=(8, 23, 17, 110))
    draw_center(d, "in every detail.", 936, font(SERIF_PATH, 80), GOLD, stroke_width=1,
                stroke_fill=(8, 23, 17, 110))
    draw_rule(d, 1080, 250)
    center_label(d, "Tradition, carried forward", 1127, color=PAPER_LIGHT, size=18, tracking=3)
    draw_center(d, "A DIGITAL INVITATION WITH AN ISLAND HEART", 1633,
                font(SANS_PATH, 20), PAPER_LIGHT, tracking=2)
    draw_center(d, "ANJALI & KAVINDU  ·  COLOMBO 2027", 1687,
                font(SANS_BOLD_PATH, 18), GOLD, tracking=2)
    return overlay


def draw_scene_2() -> Image.Image:
    overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    add_border(d, inset=43, radius=24)
    center_label(d, "Rooted in the island we call home", 265, size=18, tracking=4)
    draw_center(d, "From blessings", 388, font(SERIF_PATH, 82), PAPER_LIGHT)
    draw_center(d, "on the Poruwa", 496, font(SERIF_PATH, 94), PAPER_LIGHT)
    draw_center(d, "to a night beneath", 625, font(SERIF_PATH, 62), PAPER_LIGHT)
    draw_center(d, "an island sky.", 710, font(SERIF_PATH, 77), GOLD)
    draw_rule(d, 842, 230)
    draw_center(d, "The lotus. The jasmine. The oil-lamp glow.", 901,
                font(SANS_PATH, 26), PAPER_LIGHT)
    draw_center(d, "A celebration shaped by the traditions we love.", 949,
                font(SANS_PATH, 22), (242, 237, 220, 235))
    # Soft pill panel keeps the cultural cues legible without covering the still-life.
    d.rounded_rectangle((104, 1180, 976, 1333), radius=25,
                        fill=(13, 35, 26, 132), outline=(217, 189, 141, 125), width=2)
    labels = [(247, "PORUWA"), (540, "LOTUS & JASMINE"), (833, "LAMP-LIGHT BLESSINGS")]
    for x, label in labels:
        d.ellipse((x - 6, 1231, x + 6, 1243), fill=GOLD)
        draw_at_center(d, label, x, 1270, font(SANS_BOLD_PATH, 15), PAPER_LIGHT, tracking=1)
    draw_center(d, "Sri Lankan soul, beautifully woven in.", 1680,
                font(SERIF_PATH, 35), PAPER_LIGHT)
    return overlay


def draw_phone_scene() -> Image.Image:
    overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    add_border(d, inset=43, radius=24, color=(183, 141, 85, 95))
    center_label(d, "A thoughtful digital experience", 150, color=GOLD_DEEP, size=18, tracking=4)
    draw_center(d, "A BEAUTIFUL INVITATION.", 225, font(SANS_BOLD_PATH, 38), FOREST, tracking=2)
    draw_center(d, "Even more beautiful,", 300, font(SERIF_PATH, 65), FOREST)
    draw_center(d, "made digital.", 379, font(SERIF_PATH, 74), GOLD_DEEP)

    # Device shadow and frame.
    overlay.alpha_composite(screen_shadow())
    d = ImageDraw.Draw(overlay)
    d.rounded_rectangle((218, 535, 862, 1642), radius=77,
                        fill=(20, 50, 40, 255), outline=(183, 141, 85, 230), width=3)
    d.rounded_rectangle((239, 557, 841, 1620), radius=60,
                        fill=(251, 249, 243, 255), outline=(227, 216, 193, 255), width=2)
    d.rounded_rectangle((484, 575, 596, 590), radius=8, fill=(50, 71, 58, 255))
    # Screen content mirrors the actual invitation card.
    draw_lotus(d, WIDTH // 2, 671, 57, color=GOLD_DEEP, width=2)
    draw_center(d, "WITH THE BLESSINGS OF OUR FAMILIES", 719,
                font(SANS_BOLD_PATH, 13), MUTED, tracking=1)
    draw_center(d, "Anjali", 784, font(SERIF_PATH, 76), FOREST)
    draw_center(d, "&", 874, font(SERIF_PATH, 46), GOLD_DEEP)
    draw_center(d, "Kavindu", 926, font(SERIF_PATH, 76), FOREST)
    draw_rule(d, 1031, 230, color=(183, 141, 85, 180))
    draw_center(d, "SATURDAY  ·  6 MARCH 2027", 1075,
                font(SANS_BOLD_PATH, 17), FOREST, tracking=1)
    draw_center(d, "The Kingsbury, Colombo", 1121,
                font(SERIF_PATH, 31), FOREST)
    draw_center(d, "SIX O'CLOCK IN THE EVENING", 1171,
                font(SANS_PATH, 14), MUTED, tracking=1)
    d.rounded_rectangle((343, 1235, 737, 1305), radius=1, fill=FOREST)
    draw_center(d, "KINDLY REPLY   ↗", 1254, font(SANS_BOLD_PATH, 17), PAPER_LIGHT, tracking=1)
    draw_center(d, "SAVE THE DATE  ·  GET DIRECTIONS", 1350,
                font(SANS_BOLD_PATH, 13), GOLD_DEEP, tracking=1)
    d.line((333, 1410, 747, 1410), fill=(214, 203, 181, 220), width=2)
    draw_center(d, "Countdown  ·  RSVP  ·  Venue", 1444,
                font(SERIF_PATH, 22), (91, 105, 91, 255))
    draw_center(d, "One lovely link for every guest.", 1731,
                font(SERIF_PATH, 34), FOREST)
    draw_center(d, "DESIGNED TO FEEL PERSONAL", 1791,
                font(SANS_BOLD_PATH, 15), GOLD_DEEP, tracking=3)
    return overlay


def draw_feature_scene() -> Image.Image:
    overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    add_border(d, inset=43, radius=24)
    center_label(d, "Made for every guest", 226, color=GOLD, size=19, tracking=4)
    draw_center(d, "Everything they need,", 334, font(SERIF_PATH, 78), PAPER_LIGHT)
    draw_center(d, "all in one place.", 430, font(SERIF_PATH, 91), GOLD)
    draw_center(d, "A seamless little journey from invite to RSVP.", 560,
                font(SANS_PATH, 24), (220, 226, 215, 255))

    cards = [
        (720, "01", "RSVP with a tap", "A warm yes or a loving note."),
        (1000, "02", "Save the date", "Add the celebration to your calendar."),
        (1280, "03", "Find your way", "Venue details and Colombo directions."),
    ]
    for y, number, title, subtitle in cards:
        d.rounded_rectangle((95, y, 985, y + 230), radius=8,
                            fill=(250, 248, 240, 248), outline=(217, 189, 141, 190), width=2)
        d.ellipse((134, y + 73, 220, y + 159), outline=(183, 141, 85, 220), width=2)
        draw_at_center(d, number, 177, y + 99, font(SERIF_PATH, 31), GOLD_DEEP)
        d.line((258, y + 45, 258, y + 185), fill=(183, 141, 85, 155), width=2)
        draw_left(d, title, 299, y + 60, font(SERIF_PATH, 45), FOREST)
        draw_left(d, subtitle, 301, y + 127, font(SANS_PATH, 22), (103, 113, 101, 255))
        draw_left(d, "ONE THOUGHTFUL DETAIL", 301, y + 176,
                  font(SANS_BOLD_PATH, 13), GOLD_DEEP)
    draw_center(d, "Thoughtful details. Effortless for everyone.", 1639,
                font(SERIF_PATH, 34), PAPER_LIGHT)
    draw_center(d, "DRESSED FOR TRADITION  ·  DESIGNED FOR TODAY", 1704,
                font(SANS_BOLD_PATH, 15), GOLD, tracking=2)
    return overlay


def make_qr() -> Image.Image:
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_Q,
        box_size=10,
        border=2,
    )
    qr.add_data(QR_URL)
    qr.make(fit=True)
    return qr.make_image(fill_color="#173e32", back_color="#fffdf7").convert("RGBA").resize(
        (320, 320), Image.Resampling.NEAREST)


def draw_closing_scene() -> Image.Image:
    overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    add_border(d, inset=43, radius=24)
    draw_lotus(d, WIDTH // 2, 236, 104, width=2)
    center_label(d, "You are warmly invited", 316, color=GOLD, size=18, tracking=4)
    draw_center(d, "Anjali & Kavindu", 403, font(SERIF_PATH, 82), PAPER_LIGHT)
    draw_rule(d, 518, 220)
    draw_center(d, "SATURDAY  ·  6 MARCH 2027", 560,
                font(SANS_BOLD_PATH, 19), PAPER_LIGHT, tracking=2)
    draw_center(d, "The Kingsbury  ·  Colombo, Sri Lanka", 607,
                font(SERIF_PATH, 33), PAPER_LIGHT)

    # QR card is large enough to scan from a paused mobile video.
    d.rounded_rectangle((308, 724, 772, 1238), radius=12,
                        fill=(255, 253, 247, 255), outline=(217, 189, 141, 255), width=3)
    qr = make_qr()
    overlay.alpha_composite(qr, (WIDTH // 2 - 160, 758))
    d = ImageDraw.Draw(overlay)
    draw_center(d, "SCAN TO OPEN THE INVITATION", 1104,
                font(SANS_BOLD_PATH, 15), FOREST, tracking=2)
    draw_center(d, "vidu1999.github.io/digital_wedding_card", 1300,
                font(SANS_BOLD_PATH, 19), PAPER_LIGHT, tracking=1)
    draw_center(d, "RSVP  ·  SAVE THE DATE  ·  DIRECTIONS", 1361,
                font(SANS_PATH, 16), GOLD, tracking=2)
    d.rounded_rectangle((330, 1457, 750, 1527), radius=2, fill=(255, 253, 247, 255))
    draw_center(d, "OPEN THE INVITATION   ↗", 1479,
                font(SANS_BOLD_PATH, 17), FOREST, tracking=1)
    draw_center(d, "We can't wait to celebrate with you.", 1610,
                font(SERIF_PATH, 35), PAPER_LIGHT)
    draw_center(d, "MADE WITH LOVE IN SRI LANKA  ·  2027", 1738,
                font(SANS_BOLD_PATH, 15), GOLD, tracking=2)
    return overlay


def make_flat_bg(kind: str) -> Image.Image:
    if kind == "paper":
        image = gradient_background((255, 253, 247), (239, 234, 221), (255, 250, 236))
        d = ImageDraw.Draw(image, "RGBA")
        d.ellipse((140, 370, 940, 1170), outline=(183, 141, 85, 24), width=2)
        d.ellipse((178, 408, 902, 1132), outline=(183, 141, 85, 16), width=1)
        for y in range(135, HEIGHT, 130):
            d.line((60, y, 120, y), fill=(183, 141, 85, 35), width=1)
            d.line((WIDTH - 120, y, WIDTH - 60, y), fill=(183, 141, 85, 35), width=1)
        return image
    image = gradient_background((31, 73, 58), (13, 39, 31), (62, 94, 68))
    d = ImageDraw.Draw(image, "RGBA")
    # Fine, understated linework nods to carved timber and woven batik geometry.
    for offset in range(-900, 2000, 180):
        d.line((offset, 1920, offset + 980, 0), fill=(217, 189, 141, 15), width=2)
    for radius in (360, 560, 760):
        d.ellipse((WIDTH - radius, 300 - radius, WIDTH + radius, 300 + radius),
                  outline=(217, 189, 141, 13), width=2)
    return image


PHOTO_BGS = {
    0: (prepare_photo(PORUWA), make_tint(78, 118, 164)),
    1: (prepare_photo(LAMP), make_tint(57, 74, 128)),
    4: (prepare_photo(LAMP), make_tint(102, 140, 185)),
}
FLAT_BGS = {2: make_flat_bg("paper"), 3: make_flat_bg("forest")}
OVERLAYS = [draw_scene_1(), draw_scene_2(), draw_phone_scene(), draw_feature_scene(), draw_closing_scene()]


def render_scene(index: int, progress: float) -> Image.Image:
    if index in PHOTO_BGS:
        source, tint = PHOTO_BGS[index]
        focus_x = .55 if index == 0 else .52
        direction = -1.0 if index in (1, 4) else 1.0
        background = pan_crop(source, progress, focus_x=focus_x, focus_y=.48, direction=direction)
        background = Image.alpha_composite(background.convert("RGBA"), tint)
    else:
        background = FLAT_BGS[index].convert("RGBA")
    return Image.alpha_composite(background, OVERLAYS[index]).convert("RGB")


def ease(value: float) -> float:
    value = min(1.0, max(0.0, value))
    return value * value * (3 - 2 * value)


def render_frame(time_s: float) -> Image.Image:
    index = min(SCENE_COUNT - 1, int(time_s / SCENE_STEP))
    start = index * SCENE_STEP
    progress = min(1.0, max(0.0, (time_s - start) / SEGMENT))
    current = render_scene(index, progress)
    if index > 0 and progress < TRANSITION / SEGMENT:
        previous_progress = min(1.0, max(0.0, (time_s - (index - 1) * SCENE_STEP) / SEGMENT))
        previous = render_scene(index - 1, previous_progress)
        alpha = ease(progress / (TRANSITION / SEGMENT))
        current = Image.blend(previous, current, alpha)
    return current


def synthesize_score(path: Path) -> None:
    """Make an original, soft ambient bed with warm pads and bell-like plucks."""
    sample_rate = 44100
    count = round(DURATION * sample_rate)
    time = np.arange(count, dtype=np.float32) / sample_rate
    mix = np.zeros((count, 2), dtype=np.float32)
    chord_events = [
        (0.0, [146.83, 220.00, 329.63, 370.00]),
        (4.15, [123.47, 185.00, 246.94, 293.66]),
        (8.30, [196.00, 246.94, 293.66, 392.00]),
        (12.45, [110.00, 164.81, 220.00, 329.63]),
        (16.60, [146.83, 220.00, 293.66, 370.00]),
    ]
    for event_index, (start, notes) in enumerate(chord_events):
        end = DURATION if event_index == len(chord_events) - 1 else start + SEGMENT
        a = round(start * sample_rate)
        b = min(count, round(end * sample_rate))
        local = time[a:b] - start
        span = max(0.1, end - start)
        envelope = np.sin(np.pi * np.clip(local / span, 0, 1)) ** .48
        envelope *= (.92 + .08 * np.sin(2 * np.pi * .19 * local))
        for note_index, freq in enumerate(notes):
            fundamental = np.sin(2 * np.pi * freq * local + note_index * .21)
            warmth = .21 * np.sin(2 * np.pi * freq * 2.002 * local)
            warmth += .075 * np.sin(2 * np.pi * freq * 3.01 * local)
            voice = (fundamental + warmth) * envelope * .010
            pan = .25 + .5 * ((note_index + event_index) % 4) / 3
            mix[a:b, 0] += voice * math.sqrt(1 - pan)
            mix[a:b, 1] += voice * math.sqrt(pan)

    melody = [
        (0.45, 587.33), (1.60, 440.00), (2.75, 493.88), (3.70, 659.25),
        (4.55, 554.37), (5.75, 440.00), (7.00, 739.99), (7.80, 659.25),
        (8.70, 587.33), (9.85, 493.88), (11.0, 440.00), (11.8, 587.33),
        (12.85, 659.25), (14.0, 739.99), (15.1, 587.33), (16.0, 493.88),
        (17.0, 587.33), (18.15, 739.99), (19.3, 659.25), (20.2, 587.33),
    ]
    for i, (start, freq) in enumerate(melody):
        a = round(start * sample_rate)
        b = min(count, a + round(1.9 * sample_rate))
        local = np.arange(b - a, dtype=np.float32) / sample_rate
        envelope = (1 - np.exp(-local * 90)) * np.exp(-local * 2.45)
        bell = (np.sin(2 * np.pi * freq * local) +
                .36 * np.sin(2 * np.pi * freq * 2.76 * local + .2) +
                .12 * np.sin(2 * np.pi * freq * 4.1 * local + .5))
        bell *= envelope * .032
        pan = .2 + .6 * (i % 5) / 4
        mix[a:b, 0] += bell * math.sqrt(1 - pan)
        mix[a:b, 1] += bell * math.sqrt(pan)

    # Short, quiet stereo reflections soften the plucks.
    dry = mix.copy()
    for delay_s, gain, swap in ((.16, .18, False), (.31, .105, True), (.48, .055, False)):
        delay = round(delay_s * sample_rate)
        if swap:
            mix[delay:, 0] += dry[:-delay, 1] * gain
            mix[delay:, 1] += dry[:-delay, 0] * gain
        else:
            mix[delay:] += dry[:-delay] * gain

    fade_in = np.clip(time / .8, 0, 1)
    fade_out = np.clip((DURATION - time) / 1.45, 0, 1)
    mix *= np.minimum(fade_in, fade_out)[:, None]
    peak = float(np.max(np.abs(mix)))
    if peak:
        mix *= .74 / peak
    pcm = np.clip(mix * 32767, -32768, 32767).astype("<i2")
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(2)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        wav.writeframes(pcm.tobytes())


def main() -> None:
    ASSETS.mkdir(parents=True, exist_ok=True)
    # Save a clean poster from the final call-to-action screen.
    poster = render_scene(4, .82)
    poster.save(POSTER, quality=91, optimize=True, progressive=True)

    ffmpeg = get_ffmpeg_exe()
    frame_count = round(DURATION * FPS)
    with tempfile.TemporaryDirectory(prefix="wedding-promo-") as temp_dir:
        audio_path = Path(temp_dir) / "original-ambient-score.wav"
        synthesize_score(audio_path)
        command = [
            ffmpeg, "-y", "-hide_banner", "-loglevel", "error",
            "-f", "rawvideo", "-vcodec", "rawvideo", "-pix_fmt", "rgb24",
            "-s", f"{WIDTH}x{HEIGHT}", "-r", str(FPS), "-i", "pipe:0",
            "-i", str(audio_path),
            "-vf", f"fade=t=in:st=0:d=0.55,fade=t=out:st={DURATION - .75:.3f}:d=0.75",
            "-c:v", "libx264", "-preset", "medium", "-crf", "22",
            "-pix_fmt", "yuv420p", "-profile:v", "high", "-level", "4.1",
            "-c:a", "aac", "-b:a", "160k", "-shortest",
            "-movflags", "+faststart", "-metadata", "title=Anjali and Kavindu - Wedding Invitation",
            "-metadata", "comment=Sri Lankan wedding invitation promo reel",
            str(OUTPUT),
        ]
        process = subprocess.Popen(command, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
        assert process.stdin is not None
        for frame_number in range(frame_count):
            timestamp = frame_number / FPS
            frame = render_frame(timestamp)
            if frame_number == 0:
                print(f"Rendering {frame_count} frames at {WIDTH}x{HEIGHT} ({DURATION:.1f}s)…", flush=True)
            try:
                process.stdin.write(frame.tobytes())
            except BrokenPipeError:
                break
        process.stdin.close()
        error_text = process.stderr.read().decode("utf-8", "replace") if process.stderr else ""
        exit_code = process.wait()
        if exit_code:
            raise RuntimeError(f"ffmpeg exited with {exit_code}:\n{error_text}")
    print(f"Created {OUTPUT} ({OUTPUT.stat().st_size / 1_000_000:.2f} MB)")
    print(f"Created {POSTER} ({POSTER.stat().st_size / 1_000:.0f} KB)")


if __name__ == "__main__":
    main()
