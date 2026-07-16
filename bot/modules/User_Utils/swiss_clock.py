import io
import math
from datetime import datetime, timedelta
from itertools import pairwise

from PIL import Image, ImageDraw

"""
Renders an analogue clock face as a PNG.
"""

DAY_HAND_COLOUR = "#070707"
NIGHT_HAND_COLOUR = "#EBE9E2"
SECOND_HAND_COLOUR = "#BC0909"
SECONDARY_HAND_COLOUR = "#69A2CC"
SECONDARY_HAND_NAME = "Blue"


_HOUR_COLOURS: list[tuple[float, tuple[int, int, int]]] = [
    (0, (7, 12, 21)),  # rgb(7, 12, 21)
    (3, (19, 33, 55)),  # rgb(19, 33, 55)
    (5, (144, 121, 159)),  # rgb(144, 121, 159)
    (6, (207, 142, 134)),  # rgb(207, 142, 134)
    (7, (227, 177, 155)),  # rgb(227, 177, 155)
    (9, (153, 203, 235)),  # rgb(153, 203, 235)
    (10, (96, 163, 194)),  # rgb(96, 163, 194)
    (11, (144, 184, 191)),  # rgb(144, 184, 191)
    (12, (104, 165, 173)),  # rgb(104, 165, 173)
    (14, (185, 206, 176)),  # rgb(185, 206, 176)
    (15, (169, 165, 165)),  # rgb(169, 165, 165)
    (16, (178, 140, 121)),  # rgb(178, 140, 121)
    (17, (196, 132, 120)),  # rgb(196, 132, 120)
    (18, (104, 68, 111)),  # rgb(104, 68, 111)
    (19, (85, 54, 76)),  # rgb(85, 54, 76)
    (20, (56, 47, 77)),  # rgb(56, 47, 77)
    (21, (37, 42, 77)),  # rgb(37, 42, 77)
    (24, (7, 12, 21)),  # rgb(7, 12, 21)
]


def _relative_luminance(rgb: tuple[int, int, int]) -> float:
    """Use the ITU-R BT.709 formula to calculate relative luminance of an RGB colour"""
    r, g, b = rgb
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def _hand_colour_for(bg_rgb: tuple[int, int, int]) -> str:
    """Pick black or off-white hands, whichever reads against this background."""
    return DAY_HAND_COLOUR if _relative_luminance(bg_rgb) > 130 else NIGHT_HAND_COLOUR


def _hour_colour(dt: datetime) -> tuple[int, int, int]:
    """Interpolate a pastel "time of day" colour for dt's hour, for the background gradient."""
    t = dt.hour + dt.minute / 60 + dt.second / 3600
    for (h0, c0), (h1, c1) in pairwise(_HOUR_COLOURS):
        if h0 <= t <= h1:
            frac = (t - h0) / (h1 - h0)
            r0, g0, b0 = c0
            r1, g1, b1 = c1
            return (
                round(r0 + (r1 - r0) * frac),
                round(g0 + (g1 - g0) * frac),
                round(b0 + (b1 - b0) * frac),
            )
    return _HOUR_COLOURS[-1][1]


def _gradient_background(
    size: int,
    left_rgb: tuple[int, int, int],
    right_rgb: tuple[int, int, int],
) -> Image.Image:
    """A horizontal gradient from left_rgb (earlier) to right_rgb (later)."""
    mask = Image.linear_gradient("L").resize((size, size)).transpose(Image.Transpose.ROTATE_90)
    return Image.composite(
        Image.new("RGB", (size, size), right_rgb),
        Image.new("RGB", (size, size), left_rgb),
        mask,
    )


def _rotate(x: float, y: float, cx: float, cy: float, angle_deg: float) -> tuple[float, float]:
    """
    Rotate point (x, y) about (cx, cy) by angle_deg degrees, matching the
    SVG `rotate(angle, cx, cy)` transform matrix.
    """
    rad = math.radians(angle_deg)
    cos_a, sin_a = math.cos(rad), math.sin(rad)
    dx, dy = x - cx, y - cy
    return (
        cx + dx * cos_a - dy * sin_a,
        cy + dx * sin_a + dy * cos_a,
    )


def _hour_angle(dt: datetime) -> float:
    return ((dt.hour % 12) + dt.minute / 60) * 30


def _minute_angle(dt: datetime) -> float:
    return dt.minute * 6


def _second_angle(dt: datetime) -> float:
    elapsed_second = dt.second + dt.microsecond / 1_000_000
    return min(elapsed_second / 58, 1) * 360


def _draw_rotated_rect(
    draw: ImageDraw.ImageDraw,
    x: float,
    y: float,
    width: float,
    height: float,
    angle_deg: float,
    scale: float,
    colour: str,
) -> None:
    corners = [(x, y), (x + width, y), (x + width, y + height), (x, y + height)]
    rotated = [_rotate(cx, cy, 50, 50, angle_deg) for cx, cy in corners]
    draw.polygon([(px * scale, py * scale) for px, py in rotated], fill=colour)


def _draw_rotated_line(
    draw: ImageDraw.ImageDraw,
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    angle_deg: float,
    scale: float,
    width: float,
    colour: str,
) -> None:
    p1 = _rotate(x1, y1, 50, 50, angle_deg)
    p2 = _rotate(x2, y2, 50, 50, angle_deg)
    draw.line(
        [(p1[0] * scale, p1[1] * scale), (p2[0] * scale, p2[1] * scale)],
        fill=colour,
        width=max(1, round(width * scale)),
    )


def _draw_circle(
    draw: ImageDraw.ImageDraw,
    x: float,
    y: float,
    radius: float,
    scale: float,
    colour: str,
) -> None:
    cx, cy, r = x * scale, y * scale, radius * scale
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=colour)


def render_swiss_clock(dt: datetime, other_dt: datetime | None = None, size: int = 600) -> io.BytesIO:
    """
    Render a Swiss railway clock face showing the time `dt`.

    If `other_dt` is given, an additional thin hour hand is drawn in
    SECONDARY_HAND_COLOUR pointing at `other_dt`'s hour, for comparing two
    people's times on a single face. If `other_dt` also has a different
    minute to `dt` (as happens with half/quarter-hour-offset timezones, e.g.
    India or Nepal), a matching secondary minute hand is drawn too.

    Returns a BytesIO containing PNG data, seeked to position 0.
    """
    _SUPERSAMPLE = 2
    render_size = size * _SUPERSAMPLE
    scale = render_size / 100

    bg_rgb = _hour_colour(dt)
    hand_colour = _hand_colour_for(bg_rgb)

    left_rgb = _hour_colour(dt - timedelta(hours=1))
    right_rgb = _hour_colour(dt + timedelta(hours=1))
    image = _gradient_background(render_size, left_rgb, right_rgb)
    draw = ImageDraw.Draw(image)

    # Ticks
    for i in range(60):
        angle = i * 6
        if i % 5 == 0:
            _draw_rotated_rect(draw, 48.35, 5.8, 3.3, 10.8, angle, scale, hand_colour)
        else:
            _draw_rotated_rect(draw, 49.35, 5.9, 1.3, 3.8, angle, scale, hand_colour)

    # Secondary hour/minute hands (drawn first, so the primary hands sit on top when equal)
    if other_dt is not None:
        _draw_rotated_line(draw, 50, 61, 50, 22.5, _hour_angle(other_dt), scale, 3.5, SECONDARY_HAND_COLOUR)
        if other_dt.minute != dt.minute:
            _draw_rotated_line(draw, 50, 63, 50, 10.5, _minute_angle(other_dt), scale, 2.7, SECONDARY_HAND_COLOUR)

    # Primary hour and minute hands, and the hub
    _draw_rotated_line(draw, 50, 61, 50, 22.5, _hour_angle(dt), scale, 6.8, hand_colour)
    _draw_rotated_line(draw, 50, 63, 50, 10.5, _minute_angle(dt), scale, 5.2, hand_colour)
    _draw_circle(draw, 50, 50, 2.7, scale, hand_colour)

    # Second hand, drawn last (on top of everything)
    second_angle = _second_angle(dt)
    _draw_rotated_line(draw, 50, 62.5, 50, 18.5, second_angle, scale, 1.25, SECOND_HAND_COLOUR)
    tip = _rotate(50, 18.5, 50, 50, second_angle)
    _draw_circle(draw, tip[0], tip[1], 1.55, scale, SECOND_HAND_COLOUR)
    _draw_circle(draw, 50, 50, 1.55, scale, SECOND_HAND_COLOUR)

    image = image.resize((size, size), Image.LANCZOS)

    buf = io.BytesIO()
    image.save(buf, format="PNG")
    buf.seek(0)
    return buf
