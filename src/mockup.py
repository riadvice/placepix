from __future__ import annotations

from dataclasses import dataclass, field
import io

from PIL import Image, ImageDraw, ImageOps

from src.image_processor import _load_font


@dataclass(frozen=True)
class DeviceSpec:
    """Geometry of a device frame, expressed at its native screen resolution."""

    label: str
    screen: tuple[int, int]
    bezel: tuple[int, int, int, int]  # left, top, right, bottom
    body_radius: int
    screen_radius: int
    body_color: tuple[int, int, int]
    chrome: str = ""  # "" | "notch" | "punch-hole" | "browser" | "laptop"
    chrome_color: tuple[int, int, int] = (245, 245, 247)
    accent_color: tuple[int, int, int] = (200, 200, 205)
    extras: dict = field(default_factory=dict)

    @property
    def frame_size(self) -> tuple[int, int]:
        left, top, right, bottom = self.bezel
        base = self.extras.get("base_height", 0)
        return (
            self.screen[0] + left + right,
            self.screen[1] + top + bottom + base,
        )


DEVICES: dict[str, DeviceSpec] = {
    "iphone": DeviceSpec(
        label="iPhone",
        screen=(390, 844),
        bezel=(14, 14, 14, 14),
        body_radius=58,
        screen_radius=44,
        body_color=(28, 28, 30),
        chrome="notch",
    ),
    "android": DeviceSpec(
        label="Android phone",
        screen=(412, 915),
        bezel=(11, 11, 11, 11),
        body_radius=44,
        screen_radius=34,
        body_color=(24, 24, 27),
        chrome="punch-hole",
    ),
    "tablet": DeviceSpec(
        label="Tablet",
        screen=(834, 1112),
        bezel=(26, 26, 26, 26),
        body_radius=42,
        screen_radius=20,
        body_color=(32, 32, 35),
    ),
    "macbook": DeviceSpec(
        label="Laptop",
        screen=(1440, 900),
        bezel=(16, 16, 16, 16),
        body_radius=18,
        screen_radius=6,
        body_color=(38, 38, 42),
        chrome="laptop",
        extras={"base_height": 46},
    ),
    "browser": DeviceSpec(
        label="Browser (light)",
        screen=(1280, 800),
        bezel=(1, 38, 1, 1),
        body_radius=14,
        screen_radius=0,
        body_color=(226, 226, 230),
        chrome="browser",
        chrome_color=(240, 240, 244),
        accent_color=(255, 255, 255),
    ),
    "browser-dark": DeviceSpec(
        label="Browser (dark)",
        screen=(1280, 800),
        bezel=(1, 38, 1, 1),
        body_radius=14,
        screen_radius=0,
        body_color=(48, 48, 52),
        chrome="browser",
        chrome_color=(38, 38, 42),
        accent_color=(64, 64, 70),
    ),
}

# Traffic-light dot colours shared by the browser and laptop chrome.
_DOTS = ((255, 95, 86), (255, 189, 46), (39, 201, 63))


def list_devices() -> list[dict]:
    """Public metadata for every frame, for the URL builder and /api/mockups."""
    return [
        {
            "id": name,
            "label": spec.label,
            "screen": {"width": spec.screen[0], "height": spec.screen[1]},
            "frame": {"width": spec.frame_size[0], "height": spec.frame_size[1]},
            "aspect_ratio": round(spec.frame_size[0] / spec.frame_size[1], 3),
        }
        for name, spec in DEVICES.items()
    ]


def _rounded_mask(size: tuple[int, int], radius: int) -> Image.Image:
    mask = Image.new("L", size, 0)
    draw = ImageDraw.Draw(mask)
    if radius > 0:
        draw.rounded_rectangle([0, 0, size[0] - 1, size[1] - 1], radius=radius, fill=255)
    else:
        draw.rectangle([0, 0, size[0] - 1, size[1] - 1], fill=255)
    return mask


def _draw_notch(draw: ImageDraw.ImageDraw, spec: DeviceSpec) -> None:
    left, top, _right, _bottom = spec.bezel
    width = int(spec.screen[0] * 0.42)
    height = 26
    x0 = left + (spec.screen[0] - width) // 2
    draw.rounded_rectangle(
        [x0, top, x0 + width, top + height],
        radius=height // 2,
        fill=spec.body_color,
    )


def _draw_punch_hole(draw: ImageDraw.ImageDraw, spec: DeviceSpec) -> None:
    left, top, _right, _bottom = spec.bezel
    d = 14
    cx = left + spec.screen[0] // 2
    cy = top + 16
    draw.ellipse([cx - d // 2, cy - d // 2, cx + d // 2, cy + d // 2], fill=spec.body_color)


def _draw_browser_chrome(draw: ImageDraw.ImageDraw, spec: DeviceSpec, url: str) -> None:
    left, top, right, _bottom = spec.bezel
    frame_w = spec.screen[0] + left + right
    draw.rounded_rectangle(
        [0, 0, frame_w - 1, top + spec.body_radius],
        radius=spec.body_radius,
        fill=spec.chrome_color,
    )
    draw.rectangle([0, top - 1, frame_w - 1, top + spec.body_radius], fill=spec.chrome_color)

    cy = top // 2
    for i, color in enumerate(_DOTS):
        cx = 18 + i * 18
        draw.ellipse([cx - 5, cy - 5, cx + 5, cy + 5], fill=color)

    bar_x0 = 18 + 3 * 18 + 12
    bar_x1 = frame_w - 18
    draw.rounded_rectangle(
        [bar_x0, cy - 10, bar_x1, cy + 10],
        radius=10,
        fill=spec.accent_color,
    )
    if url:
        font = _load_font(13)
        text_color = (90, 90, 96) if spec.chrome_color[0] > 128 else (190, 190, 196)
        draw.text((bar_x0 + 12, cy), url[:80], font=font, fill=text_color, anchor="lm")


def _draw_laptop_base(draw: ImageDraw.ImageDraw, spec: DeviceSpec) -> None:
    left, top, right, bottom = spec.bezel
    frame_w = spec.screen[0] + left + right
    base_top = top + spec.screen[1] + bottom
    base_h = spec.extras.get("base_height", 0)
    # Deck, slightly wider-looking than the lid thanks to the flat bottom radius.
    draw.rounded_rectangle(
        [0, base_top, frame_w - 1, base_top + base_h - 1],
        radius=10,
        fill=(58, 58, 64),
    )
    draw.rectangle([0, base_top, frame_w - 1, base_top + base_h // 2], fill=(58, 58, 64))
    # Trackpad notch.
    notch_w = int(frame_w * 0.14)
    nx0 = (frame_w - notch_w) // 2
    draw.rounded_rectangle(
        [nx0, base_top, nx0 + notch_w, base_top + 8],
        radius=4,
        fill=(40, 40, 45),
    )
    # Camera dot on the lid.
    cx = frame_w // 2
    draw.ellipse([cx - 3, top // 2 - 3, cx + 3, top // 2 + 3], fill=(70, 70, 78))


def render(
    source: Image.Image,
    device: str,
    width: int = 0,
    url: str = "placepix.net",
    background: str = "",
) -> Image.Image:
    """Composite `source` into a device frame, scaled so the frame is `width` px wide."""
    spec = DEVICES.get(device)
    if spec is None:
        raise ValueError(f"unknown device '{device}'")

    frame_w, frame_h = spec.frame_size
    left, top, _right, _bottom = spec.bezel

    frame = Image.new("RGBA", (frame_w, frame_h), (0, 0, 0, 0))
    body = Image.new("RGBA", (frame_w, frame_h), (*spec.body_color, 255))
    frame.paste(body, (0, 0), _rounded_mask((frame_w, frame_h), spec.body_radius))

    screen = ImageOps.fit(source.convert("RGB"), spec.screen, method=Image.LANCZOS)
    frame.paste(screen, (left, top), _rounded_mask(spec.screen, spec.screen_radius))

    draw = ImageDraw.Draw(frame)
    if spec.chrome == "notch":
        _draw_notch(draw, spec)
    elif spec.chrome == "punch-hole":
        _draw_punch_hole(draw, spec)
    elif spec.chrome == "browser":
        _draw_browser_chrome(draw, spec, url)
    elif spec.chrome == "laptop":
        _draw_laptop_base(draw, spec)

    if width and width != frame_w:
        scale = width / frame_w
        frame = frame.resize((width, max(1, round(frame_h * scale))), Image.LANCZOS)

    if background:
        bg_color = _parse_color(background)
        flat = Image.new("RGBA", frame.size, (*bg_color, 255))
        flat.alpha_composite(frame)
        frame = flat

    return frame


def _parse_color(hex_str: str) -> tuple[int, int, int]:
    value = hex_str.lstrip("#")
    if len(value) == 3:
        value = "".join(c * 2 for c in value)
    if len(value) != 6:
        raise ValueError(f"invalid color '{hex_str}'")
    try:
        return (int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16))
    except ValueError:
        raise ValueError(f"invalid color '{hex_str}'")


def render_bytes(
    source: Image.Image,
    device: str,
    width: int = 0,
    url: str = "placepix.net",
    background: str = "",
    output_format: str = "png",
    quality: int = 90,
) -> bytes:
    """Render a framed mockup and encode it."""
    frame = render(source, device, width=width, url=url, background=background)
    fmt = output_format.lower()
    if fmt == "jpg":
        fmt = "jpeg"
    if fmt in ("jpeg", "avif") and frame.mode == "RGBA":
        flat = Image.new("RGBA", frame.size, (255, 255, 255, 255))
        flat.alpha_composite(frame)
        frame = flat.convert("RGB")

    buffer = io.BytesIO()
    if fmt == "png":
        frame.save(buffer, format="PNG", optimize=True)
    elif fmt == "webp":
        frame.save(buffer, format="WEBP", quality=quality, method=4)
    elif fmt == "avif":
        frame.save(buffer, format="AVIF", quality=quality)
    else:
        frame.save(buffer, format="JPEG", quality=quality, optimize=True)
    return buffer.getvalue()
