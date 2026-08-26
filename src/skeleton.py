from __future__ import annotations

import io

from PIL import Image, ImageDraw

# Light and dark greys for the canvas, the blocks, and the one accent block
# (buttons, primary actions) that keeps a wireframe readable.
THEMES: dict[str, dict[str, tuple[int, int, int]]] = {
    "light": {
        "bg": (255, 255, 255),
        "surface": (244, 244, 246),
        "block": (226, 226, 231),
        "muted": (235, 235, 239),
        "accent": (198, 198, 206),
    },
    "dark": {
        "bg": (24, 24, 27),
        "surface": (34, 34, 38),
        "block": (52, 52, 58),
        "muted": (42, 42, 47),
        "accent": (78, 78, 86),
    },
}

PRESETS = ("card", "article", "profile", "list", "grid", "form", "dashboard")


class _Canvas:
    """Fraction-based drawing helper so every preset scales to any size."""

    def __init__(self, width: int, height: int, palette: dict, radius: int) -> None:
        self.w = width
        self.h = height
        self.palette = palette
        self.radius = radius
        self.img = Image.new("RGB", (width, height), palette["bg"])
        self.draw = ImageDraw.Draw(self.img)

    def block(
        self,
        x: float,
        y: float,
        w: float,
        h: float,
        color: str = "block",
        radius: int | None = None,
    ) -> None:
        x0, y0 = x * self.w, y * self.h
        x1, y1 = x0 + w * self.w, y0 + h * self.h
        r = self.radius if radius is None else radius
        r = max(0, min(int(r), int(min(x1 - x0, y1 - y0) / 2)))
        if r:
            self.draw.rounded_rectangle([x0, y0, x1, y1], radius=r, fill=self.palette[color])
        else:
            self.draw.rectangle([x0, y0, x1, y1], fill=self.palette[color])

    def circle(self, cx: float, cy: float, d: float, color: str = "block") -> None:
        """Diameter is a fraction of the shorter side so circles stay round."""
        px = d * min(self.w, self.h)
        x0, y0 = cx * self.w - px / 2, cy * self.h - px / 2
        self.draw.ellipse([x0, y0, x0 + px, y0 + px], fill=self.palette[color])

    def line(self, x: float, y: float, w: float, thickness: float = 0.028) -> None:
        self.block(x, y, w, thickness, color="muted", radius=int(thickness * self.h / 2))


def _card(c: _Canvas) -> None:
    c.block(0.04, 0.04, 0.92, 0.92, color="surface")
    c.block(0.08, 0.09, 0.84, 0.42)
    c.line(0.08, 0.58, 0.62, 0.055)
    c.line(0.08, 0.68, 0.84, 0.035)
    c.line(0.08, 0.755, 0.72, 0.035)
    c.block(0.08, 0.83, 0.28, 0.08, color="accent")


def _article(c: _Canvas) -> None:
    c.line(0.08, 0.06, 0.7, 0.07)
    c.line(0.08, 0.17, 0.32, 0.03)
    c.block(0.08, 0.24, 0.84, 0.34)
    for i, w in enumerate((0.84, 0.8, 0.86, 0.62)):
        c.line(0.08, 0.64 + i * 0.075, w, 0.032)


def _profile(c: _Canvas) -> None:
    c.block(0.0, 0.0, 1.0, 0.3, color="surface", radius=0)
    c.circle(0.5, 0.3, 0.26)
    c.line(0.33, 0.47, 0.34, 0.05)
    c.line(0.38, 0.56, 0.24, 0.032)
    for i in range(3):
        c.block(0.08 + i * 0.29, 0.66, 0.25, 0.2, color="surface")
        c.line(0.13 + i * 0.29, 0.71, 0.15, 0.045)
        c.line(0.12 + i * 0.29, 0.79, 0.17, 0.03)


def _list(c: _Canvas, rows: int = 5) -> None:
    gap = 1.0 / rows
    for i in range(rows):
        top = i * gap
        c.circle(0.11, top + gap * 0.5, 0.11)
        c.line(0.22, top + gap * 0.3, 0.5, gap * 0.16)
        c.line(0.22, top + gap * 0.56, 0.7, gap * 0.12)


def _grid(c: _Canvas, cols: int = 3, rows: int = 2) -> None:
    pad, gap = 0.04, 0.03
    cell_w = (1 - pad * 2 - gap * (cols - 1)) / cols
    cell_h = (1 - pad * 2 - gap * (rows - 1)) / rows
    for r in range(rows):
        for col in range(cols):
            c.block(
                pad + col * (cell_w + gap),
                pad + r * (cell_h + gap),
                cell_w,
                cell_h,
            )


def _form(c: _Canvas, fields: int = 3) -> None:
    c.line(0.08, 0.07, 0.44, 0.06)
    step = 0.62 / fields
    for i in range(fields):
        top = 0.22 + i * step
        c.line(0.08, top, 0.24, 0.035)
        c.block(0.08, top + 0.07, 0.84, step * 0.42, color="surface")
    c.block(0.08, 0.88, 0.32, 0.08, color="accent")


def _dashboard(c: _Canvas) -> None:
    c.block(0.0, 0.0, 0.2, 1.0, color="surface", radius=0)
    for i in range(5):
        c.line(0.04, 0.12 + i * 0.09, 0.12, 0.035)
    c.block(0.2, 0.0, 0.8, 0.1, color="surface", radius=0)
    c.line(0.23, 0.04, 0.18, 0.035)
    for i in range(3):
        c.block(0.23 + i * 0.26, 0.15, 0.22, 0.2, color="surface")
        c.line(0.25 + i * 0.26, 0.19, 0.1, 0.045)
        c.line(0.25 + i * 0.26, 0.27, 0.14, 0.03)
    c.block(0.23, 0.42, 0.74, 0.48, color="surface")


_RENDERERS = {
    "card": _card,
    "article": _article,
    "profile": _profile,
    "list": _list,
    "grid": _grid,
    "form": _form,
    "dashboard": _dashboard,
}


def list_presets() -> list[dict]:
    """Public metadata for the URL builder and /api/skeletons."""
    return [{"id": name, "label": name.capitalize()} for name in PRESETS]


def render(
    preset: str,
    width: int,
    height: int,
    theme: str = "light",
    radius: int = 8,
    rows: int = 0,
    cols: int = 0,
) -> Image.Image:
    """Draw a lo-fi wireframe/skeleton block layout."""
    renderer = _RENDERERS.get(preset)
    if renderer is None:
        raise ValueError(f"unknown skeleton preset '{preset}'")
    palette = THEMES.get(theme)
    if palette is None:
        raise ValueError(f"unknown theme '{theme}'")

    canvas = _Canvas(width, height, palette, radius)
    if preset == "grid":
        renderer(canvas, cols=cols or 3, rows=rows or 2)
    elif preset == "list":
        renderer(canvas, rows=rows or 5)
    elif preset == "form":
        renderer(canvas, fields=rows or 3)
    else:
        renderer(canvas)
    return canvas.img


def render_bytes(
    preset: str,
    width: int,
    height: int,
    theme: str = "light",
    radius: int = 8,
    rows: int = 0,
    cols: int = 0,
    output_format: str = "png",
    quality: int = 90,
) -> bytes:
    """Render a skeleton placeholder and encode it."""
    img = render(preset, width, height, theme=theme, radius=radius, rows=rows, cols=cols)
    fmt = output_format.lower()
    if fmt == "jpg":
        fmt = "jpeg"
    buffer = io.BytesIO()
    if fmt == "webp":
        img.save(buffer, format="WEBP", quality=quality, method=4)
    elif fmt == "avif":
        img.save(buffer, format="AVIF", quality=quality)
    elif fmt == "jpeg":
        img.save(buffer, format="JPEG", quality=quality, optimize=True)
    else:
        img.save(buffer, format="PNG", optimize=True)
    return buffer.getvalue()
