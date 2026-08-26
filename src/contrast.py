from __future__ import annotations

from PIL import Image

# WCAG 2.1 minimum contrast ratios.
AA_NORMAL = 4.5
AA_LARGE = 3.0
AAA_NORMAL = 7.0

# Named regions of a 3x3 grid, in the order they are scanned.
GRID_POSITIONS = (
    "top-left",
    "top-center",
    "top-right",
    "center-left",
    "center",
    "center-right",
    "bottom-left",
    "bottom-center",
    "bottom-right",
)


def _linearize(channel: float) -> float:
    c = channel / 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def relative_luminance(rgb: tuple[int, int, int]) -> float:
    """WCAG relative luminance of an sRGB colour."""
    r, g, b = (_linearize(c) for c in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast_ratio(a: tuple[int, int, int], b: tuple[int, int, int]) -> float:
    """WCAG contrast ratio between two colours, always >= 1."""
    la, lb = relative_luminance(a), relative_luminance(b)
    lighter, darker = max(la, lb), min(la, lb)
    return (lighter + 0.05) / (darker + 0.05)


def _rating(ratio: float) -> str:
    if ratio >= AAA_NORMAL:
        return "AAA"
    if ratio >= AA_NORMAL:
        return "AA"
    if ratio >= AA_LARGE:
        return "AA-large"
    return "fail"


def required_scrim(
    background: tuple[int, int, int],
    text: tuple[int, int, int],
    target: float = AA_NORMAL,
    step: float = 0.05,
) -> float:
    """Smallest scrim opacity (0..1) that lifts `text` on `background` to `target`.

    The scrim is black when the text is light and white when the text is dark, which
    is the pairing that actually moves the ratio in the right direction.
    """
    if contrast_ratio(background, text) >= target:
        return 0.0
    scrim = (0, 0, 0) if relative_luminance(text) > 0.5 else (255, 255, 255)
    alpha = step
    while alpha <= 1.0 + 1e-9:
        blended = tuple(
            round(bg * (1 - alpha) + sc * alpha) for bg, sc in zip(background, scrim, strict=True)
        )
        if contrast_ratio(blended, text) >= target:
            return round(min(alpha, 1.0), 2)
        alpha += step
    return 1.0


def _mean_color(img: Image.Image, box: tuple[int, int, int, int]) -> tuple[int, int, int]:
    region = img.crop(box)
    # A 1x1 resize is the cheapest exact mean Pillow offers.
    pixel = region.resize((1, 1), Image.BOX).getpixel((0, 0))
    return (int(pixel[0]), int(pixel[1]), int(pixel[2]))


def parse_color(hex_str: str) -> tuple[int, int, int]:
    """Parse a #rgb / #rrggbb colour into an RGB triple."""
    value = hex_str.lstrip("#").strip()
    if len(value) == 3:
        value = "".join(c * 2 for c in value)
    if len(value) != 6:
        raise ValueError(f"invalid color '{hex_str}'")
    try:
        return (int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16))
    except ValueError:
        raise ValueError(f"invalid color '{hex_str}'")


def analyze(
    image: Image.Image,
    grid: int = 3,
    target: float = AA_NORMAL,
    text_color: str = "#ffffff",
) -> dict:
    """Report where `text_color` stays legible when overlaid on the image.

    For every cell of a `grid` x `grid` split this returns the mean colour, the WCAG
    ratio against the chosen text colour (plus white and black for reference), and the
    scrim opacity that would lift the cell to `target`.

    Note that white and black between them always clear AA somewhere on the scale, so
    the interesting question is not "is any text readable" but "is *this* text readable",
    which is why the caller's own text colour drives `passes` and `required_scrim`.
    """
    if grid < 1:
        raise ValueError("grid must be at least 1")

    text_rgb = parse_color(text_color)
    img = image.convert("RGB")
    w, h = img.size
    white, black = (255, 255, 255), (0, 0, 0)

    regions = []
    for row in range(grid):
        for col in range(grid):
            box = (
                int(col * w / grid),
                int(row * h / grid),
                int((col + 1) * w / grid),
                int((row + 1) * h / grid),
            )
            mean = _mean_color(img, box)
            on_white = contrast_ratio(mean, white)
            on_black = contrast_ratio(mean, black)
            ratio = contrast_ratio(mean, text_rgb)
            name = GRID_POSITIONS[row * 3 + col] if grid == 3 else f"r{row + 1}c{col + 1}"
            regions.append(
                {
                    "region": name,
                    "box": {
                        "x": box[0],
                        "y": box[1],
                        "width": box[2] - box[0],
                        "height": box[3] - box[1],
                    },
                    "mean_color": "#%02x%02x%02x" % mean,
                    "luminance": round(relative_luminance(mean), 4),
                    "contrast": round(ratio, 2),
                    "contrast_on_white_text": round(on_white, 2),
                    "contrast_on_black_text": round(on_black, 2),
                    "recommended_text_color": "#ffffff" if on_white >= on_black else "#000000",
                    "rating": _rating(ratio),
                    "passes": ratio >= target,
                    "required_scrim": required_scrim(mean, text_rgb, target=target),
                }
            )

    overall = _mean_color(img, (0, 0, w, h))
    light_wins = contrast_ratio(overall, white) >= contrast_ratio(overall, black)
    worst = min(regions, key=lambda r: r["contrast"])

    return {
        "grid": grid,
        "target_ratio": target,
        "text_color": "#%02x%02x%02x" % text_rgb,
        "mean_color": "#%02x%02x%02x" % overall,
        "luminance": round(relative_luminance(overall), 4),
        "recommended_text_color": "#ffffff" if light_wins else "#000000",
        "safe_for_text": all(r["passes"] for r in regions),
        "worst_region": worst["region"],
        "suggested_scrim": max(r["required_scrim"] for r in regions),
        "regions": regions,
    }
