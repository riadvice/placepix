from __future__ import annotations

import io
import math
from pathlib import Path
from typing import Tuple

from PIL import Image, ImageDraw, ImageFont

from src.config import settings

# Named color palettes (RGB tuples)
_PALETTES: dict[str, list[tuple[int, int, int]]] = {
    "flatui": [
        (26, 188, 156),   # turquoise
        (46, 204, 113),   # emerald
        (52, 152, 219),   # peter river
        (155, 89, 182),   # amethyst
        (52, 73, 94),     # wet asphalt
        (22, 160, 133),   # green sea
        (39, 174, 96),    # nephritis
        (41, 128, 185),   # belize hole
        (142, 68, 173),   # wisteria
        (44, 62, 80),     # midnight blue
        (241, 196, 15),   # sun flower
        (230, 126, 34),   # orange
        (231, 76, 60),    # alizarin
        (236, 240, 241),  # clouds
        (149, 165, 166),  # concrete
        (127, 140, 141),  # asbestos
        (243, 156, 18),   # carrot
        (211, 84, 0),     # pumpkin
        (192, 57, 43),    # pomegranate
        (189, 195, 199),  # silver
    ],
    "material": [
        (244, 67, 54),    # red 500
        (233, 30, 99),    # pink 500
        (156, 39, 176),   # purple 500
        (103, 58, 183),   # deep purple 500
        (63, 81, 181),    # indigo 500
        (33, 150, 243),   # blue 500
        (3, 169, 244),    # light blue 500
        (0, 188, 212),    # cyan 500
        (0, 150, 136),    # teal 500
        (76, 175, 80),    # green 500
        (139, 195, 74),   # light green 500
        (255, 235, 59),   # yellow 500
        (255, 193, 7),    # amber 500
        (255, 152, 0),    # orange 500
        (255, 87, 34),    # deep orange 500
        (121, 85, 72),    # brown 500
        (96, 125, 139),   # blue grey 500
        (158, 158, 158),  # grey 500
    ],
    "pastel": [
        (255, 179, 186),  # pastel red
        (255, 223, 186),  # pastel orange
        (255, 255, 186),  # pastel yellow
        (186, 255, 201),  # pastel green
        (186, 225, 255),  # pastel blue
        (223, 186, 255),  # pastel purple
        (255, 186, 255),  # pastel pink
        (186, 255, 255),  # pastel cyan
        (218, 165, 105),  # pastel brown
        (192, 192, 192),  # pastel grey
        (230, 230, 250),  # lavender
        (255, 228, 225),  # misty rose
        (240, 248, 255),  # alice blue
        (245, 255, 250),  # mint cream
        (255, 250, 240),  # floral white
        (248, 248, 255),  # ghost white
    ],
    "neon": [
        (57, 255, 20),    # neon green
        (255, 7, 58),     # neon red
        (255, 0, 255),    # neon magenta
        (0, 255, 255),    # neon cyan
        (255, 255, 0),    # neon yellow
        (255, 128, 0),    # neon orange
        (191, 0, 255),    # neon purple
        (0, 128, 255),    # neon blue
        (255, 0, 128),    # neon pink
        (128, 255, 0),    # neon lime
        (0, 255, 128),    # neon mint
        (255, 102, 178),  # neon rose
    ],
    "cool": [
        (41, 128, 185),   # belize hole
        (52, 152, 219),   # peter river
        (22, 160, 133),   # green sea
        (26, 188, 156),   # turquoise
        (44, 62, 80),     # midnight blue
        (52, 73, 94),     # wet asphalt
        (142, 68, 173),   # wisteria
        (155, 89, 182),   # amethyst
        (46, 204, 113),   # emerald
        (39, 174, 96),    # nephritis
        (127, 140, 141),  # asbestos
        (149, 165, 166),  # concrete
    ],
    "warm": [
        (231, 76, 60),    # alizarin
        (243, 156, 18),   # carrot
        (230, 126, 34),   # orange
        (241, 196, 15),   # sun flower
        (211, 84, 0),     # pumpkin
        (192, 57, 43),    # pomegranate
        (232, 126, 4),    # dark orange
        (245, 176, 65),   # golden rod
        (205, 92, 92),    # indian red
        (219, 112, 147),  # pale violet red
        (255, 160, 122),  # light salmon
        (255, 140, 0),    # dark orange
        (178, 34, 34),    # fire brick
        (139, 0, 0),      # dark red
    ],
}


def _load_font(font_size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Load font with fallback: custom dir -> any system font -> default."""
    # Try custom font directory first
    if settings.font_dir_path:
        custom_dir = settings.font_dir_path
        if custom_dir.exists():
            # Look for any .ttf or .ttc font file
            for font_path in custom_dir.glob("*.ttf"):
                try:
                    return ImageFont.truetype(str(font_path), font_size)
                except Exception:
                    continue
            for font_path in custom_dir.glob("*.ttc"):
                try:
                    return ImageFont.truetype(str(font_path), font_size)
                except Exception:
                    continue

    # Try to find any available system font
    system_font_dirs = [
        "/usr/share/fonts/truetype",
        "/usr/share/fonts",
        "/System/Library/Fonts",
        "/Windows/Fonts",
    ]
    for font_dir in system_font_dirs:
        if Path(font_dir).exists():
            for font_path in Path(font_dir).rglob("*.ttf"):
                try:
                    return ImageFont.truetype(str(font_path), font_size)
                except Exception:
                    continue

    # Fallback to default
    return ImageFont.load_default()


class AvatarGenerator:
    """Generate letter-based avatar images (PNG and SVG)."""

    def __init__(
        self,
        palette: list[tuple[int, int, int]] | str | None = None,
    ) -> None:
        self.palette = self._resolve_palette(palette)

    @staticmethod
    def _resolve_palette(
        palette: list[tuple[int, int, int]] | str | None = None,
    ) -> list[tuple[int, int, int]]:
        """Resolve a palette from a name string, a raw list, or default to flatui."""
        if palette is None:
            return _PALETTES["flatui"]
        if isinstance(palette, str):
            name = palette.lower().strip()
            if name in _PALETTES:
                return _PALETTES[name]
            raise ValueError(
                f"Unknown palette '{palette}'. Available: {', '.join(sorted(_PALETTES.keys()))}"
            )
        return palette

    @staticmethod
    def extract_initials(name: str, max_letters: int = 2, single: bool = False, uppercase: bool = True) -> str:
        """Extract initials from a name.

        - Splits by whitespace.
        - Takes the first letter of each word, up to max_letters.
        - If single=True, returns only the very first letter.
        - Uppercases by default.
        """
        name = name.strip()
        if not name:
            return "?"

        if single:
            letter = name[0]
            return letter.upper() if uppercase else letter

        words = name.split()
        letters = ""
        for word in words:
            for char in word:
                if char.isalpha():
                    letters += char.upper() if uppercase else char
                    break
            if len(letters) >= max_letters:
                break

        if not letters:
            letters = name[0].upper() if uppercase else name[0]

        return letters[:max_letters]

    def pick_color(self, name: str) -> tuple[int, int, int]:
        """Pick a deterministic background color from the palette using a hash of the name.

        Uses the same prime-multiplier approach as LetterAvatarKit.
        """
        if not name:
            return self.palette[0]

        # Sum ASCII values of all characters
        ascii_sum = sum(ord(c) for c in name)
        # Prime multiplier matching LetterAvatarKit's algorithm
        index = (ascii_sum * 3557) % len(self.palette)
        return self.palette[index]

    @staticmethod
    def _parse_hex(color: str) -> tuple[int, int, int]:
        """Parse a hex color string to an RGB tuple."""
        h = color.lstrip("#")
        if len(h) == 3:
            h = "".join(c * 2 for c in h)
        if len(h) != 6 or not all(c in "0123456789abcdefABCDEF" for c in h):
            return (204, 204, 204)
        return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))

    @staticmethod
    def _parse_size(size_str: str) -> tuple[int, int]:
        """Parse a size string like '100' or '100x150' into (width, height)."""
        size_str = size_str.strip().lower()
        if "x" in size_str:
            parts = size_str.split("x", 1)
            try:
                w = int(parts[0])
                h = int(parts[1])
                return w, h
            except (ValueError, IndexError):
                pass
        try:
            s = int(size_str)
            return s, s
        except ValueError:
            return 80, 80

    def _pick_color(self, name: str, palette: list[tuple[int, int, int]]) -> tuple[int, int, int]:
        if not name:
            return palette[0]
        ascii_sum = sum(ord(c) for c in name)
        index = (ascii_sum * 3557) % len(palette)
        return palette[index]

    def _fit_font(
        self,
        draw: ImageDraw.ImageDraw,
        text: str,
        max_width: int,
        max_height: int,
    ) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
        """Find the largest font size that fits within the given bounds."""
        for size in range(max_width, 8, -2):
            font = _load_font(size)
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            if text_width <= max_width and text_height <= max_height:
                return font
        return _load_font(8)

    def generate_png(
        self,
        name: str,
        size_str: str = "80",
        circle: bool = False,
        border: int = 0,
        border_color: str = "ffffff",
        bg: str = "",
        fg: str = "ffffff",
        single: bool = False,
        uppercase: bool = True,
        max_letters: int = 2,
        palette: list[tuple[int, int, int]] | str | None = None,
    ) -> bytes:
        """Generate a PNG avatar image."""
        # Resolve palette override
        active_palette = self._resolve_palette(palette) if palette is not None else self.palette
        width, height = self._parse_size(size_str)
        width = max(8, min(width, 5000))
        height = max(8, min(height, 5000))

        # Determine colors
        if bg:
            bg_rgb = self._parse_hex(bg)
        else:
            bg_rgb = self._pick_color(name, active_palette)

        fg_rgb = self._parse_hex(fg)
        border_rgb = self._parse_hex(border_color)

        # Extract initials
        text = self.extract_initials(name, max_letters=max_letters, single=single, uppercase=uppercase)

        # Create image with transparency support for circle/border
        img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Draw background (square or circle)
        if circle:
            draw.ellipse((0, 0, width - 1, height - 1), fill=(*bg_rgb, 255))
        else:
            draw.rectangle((0, 0, width - 1, height - 1), fill=(*bg_rgb, 255))

        # Draw border
        if border > 0:
            inset = border // 2
            if circle:
                draw.ellipse(
                    (inset, inset, width - 1 - inset, height - 1 - inset),
                    outline=(*border_rgb, 255),
                    width=border,
                )
            else:
                draw.rectangle(
                    (inset, inset, width - 1 - inset, height - 1 - inset),
                    outline=(*border_rgb, 255),
                    width=border,
                )

        # Draw text
        padding = max(4, min(width, height) // 10)
        max_text_w = width - padding * 2
        max_text_h = height - padding * 2
        font = self._fit_font(draw, text, max_text_w, max_text_h)
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        x = (width - text_width) // 2
        y = (height - text_height) // 2
        draw.text((x, y), text, fill=(*fg_rgb, 255), font=font)

        # Convert to RGB for JPEG compatibility
        img_rgb = img.convert("RGB")
        buffer = io.BytesIO()
        img_rgb.save(buffer, format="PNG", optimize=True)
        return buffer.getvalue()

    def generate_svg(
        self,
        name: str,
        size_str: str = "80",
        circle: bool = False,
        border: int = 0,
        border_color: str = "ffffff",
        bg: str = "",
        fg: str = "ffffff",
        single: bool = False,
        uppercase: bool = True,
        max_letters: int = 2,
        palette: list[tuple[int, int, int]] | str | None = None,
    ) -> str:
        """Generate an SVG avatar string."""
        active_palette = self._resolve_palette(palette) if palette is not None else self.palette
        width, height = self._parse_size(size_str)
        width = max(8, min(width, 5000))
        height = max(8, min(height, 5000))

        if bg:
            bg_hex = f"#{bg.lstrip('#')}" if len(bg.lstrip("#")) == 6 else f"#{bg.lstrip('#')}"
            if len(bg.lstrip("#")) == 3:
                bg_hex = f"#{bg.lstrip('#')}{bg.lstrip('#')}"
        else:
            r, g, b = self._pick_color(name, active_palette)
            bg_hex = f"#{r:02x}{g:02x}{b:02x}"

        fg_hex = f"#{fg.lstrip('#')}" if fg.startswith("#") else f"#{fg}"
        border_hex = f"#{border_color.lstrip('#')}" if border_color.startswith("#") else f"#{border_color}"

        text = self.extract_initials(name, max_letters=max_letters, single=single, uppercase=uppercase)

        # Escape XML special chars
        text_escaped = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

        # Font size proportional to smaller dimension
        font_size = min(width, height) // 2
        font_size = max(10, min(font_size, 120))

        # Build SVG
        shape = ""
        if circle:
            cx = width // 2
            cy = height // 2
            r = min(cx, cy)
            shape += f'  <circle cx="{cx}" cy="{cy}" r="{r}" fill="{bg_hex}"/>\n'
            if border > 0:
                shape += f'  <circle cx="{cx}" cy="{cy}" r="{r - border / 2}" fill="none" stroke="{border_hex}" stroke-width="{border}"/>\n'
        else:
            shape += f'  <rect width="100%" height="100%" fill="{bg_hex}"/>\n'
            if border > 0:
                inset = border / 2
                shape += f'  <rect x="{inset}" y="{inset}" width="{width - border}" height="{height - border}" fill="none" stroke="{border_hex}" stroke-width="{border}"/>\n'

        shape += f'  <text x="50%" y="50%" dominant-baseline="middle" text-anchor="middle"\n'
        shape += f'        fill="{fg_hex}" font-family="system-ui, -apple-system, sans-serif"\n'
        shape += f'        font-size="{font_size}px" font-weight="600">{text_escaped}</text>\n'

        svg = (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">\n'
            f'{shape}'
            f'</svg>'
        )
        return svg
