"""
Icons drawn with Pillow (no PNG assets needed).

Rendered at 8x and downsampled for smooth edges. Transparent background,
so they look right on any surface and in the frozen (PyInstaller) build.
"""

import math
from PIL import Image, ImageDraw, ImageColor

_SS = 8  # supersampling factor
_LANCZOS = getattr(Image, "Resampling", Image).LANCZOS


def _rline(d, p1, p2, c, w):
    """Line with round caps."""
    d.line([p1, p2], fill=c, width=int(w))
    r = w / 2
    for x, y in (p1, p2):
        d.ellipse((x - r, y - r, x + r, y + r), fill=c)


def _poly_outline(d, pts, c, w):
    closed = pts + [pts[0]]
    d.line(closed, fill=c, width=int(w), joint="curve")
    r = w / 2
    for x, y in pts:
        d.ellipse((x - r, y - r, x + r, y + r), fill=c)


def _book(d, s, c):
    w = s * 0.075
    left = [(0.50, 0.28), (0.30, 0.20), (0.08, 0.26),
            (0.08, 0.78), (0.30, 0.72), (0.50, 0.80)]
    right = [(1 - x, y) for x, y in left]
    for page in (left, right):
        _poly_outline(d, [(x * s, y * s) for x, y in page], c, w)


def _glossary(d, s, c):
    w = s * 0.075
    d.rounded_rectangle(
        (0.20 * s, 0.10 * s, 0.80 * s, 0.90 * s),
        radius=s * 0.10, outline=c, width=int(w),
    )
    for y in (0.34, 0.52, 0.70):
        _rline(d, (0.34 * s, y * s), (0.66 * s, y * s), c, w * 0.85)


def _settings(d, s, c):
    cx = cy = s / 2
    n = 8
    big_r, small_r = s * 0.46, s * 0.34
    step = 2 * math.pi / n
    pts = []
    for i in range(n):
        a = i * step - math.pi / 2
        for da, rad in ((-0.30, small_r), (-0.17, big_r), (0.17, big_r), (0.30, small_r)):
            ang = a + da * step
            pts.append((cx + rad * math.cos(ang), cy + rad * math.sin(ang)))
        mid = a + 0.5 * step
        pts.append((cx + small_r * math.cos(mid), cy + small_r * math.sin(mid)))
    d.polygon(pts, fill=c)
    d.ellipse((cx - small_r, cy - small_r, cx + small_r, cy + small_r), fill=c)
    hole = s * 0.15
    d.ellipse((cx - hole, cy - hole, cx + hole, cy + hole), fill=(0, 0, 0, 0))


_DRAWERS = {
    "book": _book,
    "glossary": _glossary,
    "settings": _settings,
}


def has_icon(name: str) -> bool:
    return name in _DRAWERS


def render_icon(name: str, color: str, px: int = 40):
    """Return a PIL RGBA image (px x px) or None if the icon is unknown."""
    drawer = _DRAWERS.get(name)
    if drawer is None:
        return None
    s = px * _SS
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    drawer(d, s, ImageColor.getrgb(color) + (255,))
    return img.resize((px, px), _LANCZOS)