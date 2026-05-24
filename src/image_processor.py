from __future__ import annotations

import io
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps

try:
    import pillow_avif  # noqa: F401
    _AVIF_AVAILABLE = True
except Exception:
    _AVIF_AVAILABLE = False


class ImageProcessor:
    """Process images with resize, crop, grayscale, blur, text overlay, format."""

    def __init__(
        self,
        min_width: int = 8,
        max_width: int = 2000,
        min_height: int = 8,
        max_height: int = 2000,
    ) -> None:
        self.min_width = min_width
        self.max_width = max_width
        self.min_height = min_height
        self.max_height = max_height

    def clamp_size(self, width: int, height: int) -> tuple[int, int]:
        w = max(self.min_width, min(width, self.max_width)) if width else 0
        h = max(self.min_height, min(height, self.max_height)) if height else 0
        return w, h

    def process(
        self,
        image_path: Path,
        width: int = 0,
        height: int = 0,
        grayscale: bool = False,
        blur: int = 0,
        text: str = "",
        fit: str = "crop",
        output_format: str = "jpeg",
        tint: str = "",
        brightness: float = 1.0,
        contrast: float = 1.0,
        saturation: float = 1.0,
        sepia: bool = False,
        border: str = "",
        padding: int = 0,
        noise: int = 0,
        pixelate: int = 0,
        quality: int = 85,
        lqip: bool = False,
    ) -> bytes:
        with Image.open(image_path) as img:
            img = img.convert("RGB")

            if grayscale:
                img = img.convert("L").convert("RGB")

            if sepia:
                img = self._apply_sepia(img)

            if brightness != 1.0:
                img = ImageEnhance.Brightness(img).enhance(brightness)

            if contrast != 1.0:
                img = ImageEnhance.Contrast(img).enhance(contrast)

            if saturation != 1.0:
                img = ImageEnhance.Color(img).enhance(saturation)

            if tint:
                img = self._apply_tint(img, tint)

            if blur > 0:
                img = img.filter(ImageFilter.GaussianBlur(radius=blur))

            if width > 0 or height > 0:
                w, h = self.clamp_size(width, height)
                img = self._resize(img, w, h, fit)
            
            # Apply pixelate effect
            if pixelate > 1:
                img = self._apply_pixelate(img, pixelate)
            
            # Apply noise/grain effect
            if noise > 0:
                img = self._apply_noise(img, noise)
            
            # Apply padding
            if padding > 0:
                img = ImageOps.expand(img, border=padding, fill=(255, 255, 255))
            
            # Apply border
            if border:
                img = self._apply_border(img, border)
            
            # Generate LQIP if requested
            if lqip:
                img = self._generate_lqip(img)

            if text:
                img = self._add_text(img, text)

            buffer = io.BytesIO()
            fmt = self._normalize_format(output_format)
            # Clamp quality to valid range
            quality = max(1, min(quality, 100))
            if fmt == "jpeg":
                img.save(buffer, format="JPEG", quality=quality, optimize=True, progressive=True)
            elif fmt == "png":
                img.save(buffer, format="PNG", optimize=True)
            elif fmt == "webp":
                img.save(buffer, format="WEBP", quality=quality, method=6)
            elif fmt == "avif":
                img.save(buffer, format="AVIF", quality=quality)
            else:
                img.save(buffer, format="JPEG", quality=quality, progressive=True)

            return buffer.getvalue()

    def _resize(self, img: Image.Image, width: int, height: int, fit: str) -> Image.Image:
        if width == 0 and height == 0:
            return img

        if width == 0:
            width = int(img.width * (height / img.height))
        elif height == 0:
            height = int(img.height * (width / img.width))

        fit = fit.lower()

        if fit == "scale":
            return img.resize((width, height), Image.Resampling.LANCZOS)

        if fit == "crop":
            return self._crop_center(img, width, height)

        if fit == "contain":
            img.thumbnail((width, height), Image.Resampling.LANCZOS)
            return img

        if fit == "cover":
            ratio_w = width / img.width
            ratio_h = height / img.height
            ratio = max(ratio_w, ratio_h)
            new_w = int(img.width * ratio)
            new_h = int(img.height * ratio)
            img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
            return self._crop_center(img, width, height)

        # default: crop center (fills exactly)
        return self._crop_center(img, width, height)

    def _crop_center(self, img: Image.Image, width: int, height: int) -> Image.Image:
        img_ratio = img.width / img.height
        target_ratio = width / height

        if img_ratio > target_ratio:
            # image is wider, crop width
            new_width = int(img.height * target_ratio)
            left = (img.width - new_width) // 2
            img = img.crop((left, 0, left + new_width, img.height))
        else:
            # image is taller, crop height
            new_height = int(img.width / target_ratio)
            top = (img.height - new_height) // 2
            img = img.crop((0, top, img.width, top + new_height))

        return img.resize((width, height), Image.Resampling.LANCZOS)

    def _add_text(self, img: Image.Image, text: str) -> Image.Image:
        draw = ImageDraw.Draw(img)

        # Calculate font size based on image dimensions
        font_size = max(12, min(img.width, img.height) // 10)
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
        except Exception:
            font = ImageFont.load_default()

        # Get text bounding box
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        x = (img.width - text_width) // 2
        y = (img.height - text_height) // 2

        # Draw semi-transparent background
        pad_x = font_size // 2
        pad_y = font_size // 4
        overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        overlay_draw = ImageDraw.Draw(overlay)
        overlay_draw.rectangle(
            [x - pad_x, y - pad_y, x + text_width + pad_x, y + text_height + pad_y],
            fill=(0, 0, 0, 128),
        )
        img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")

        # Draw white text centered
        draw = ImageDraw.Draw(img)
        draw.text((x, y), text, fill=(255, 255, 255), font=font)

        return img

    def _apply_sepia(self, img: Image.Image) -> Image.Image:
        """Apply a sepia tone filter."""
        # Sepia matrix: R=(.393,.769,.189), G=(.349,.686,.168), B=(.272,.534,.131)
        matrix = (
            0.393, 0.769, 0.189, 0,
            0.349, 0.686, 0.168, 0,
            0.272, 0.534, 0.131, 0,
        )
        return img.convert("RGB", matrix)

    def _apply_tint(self, img: Image.Image, tint_hex: str) -> Image.Image:
        """Blend image with a hex color overlay at 50% opacity."""
        h = tint_hex.lstrip("#")
        if len(h) == 3:
            h = "".join(c * 2 for c in h)
        if len(h) != 6 or not all(c in "0123456789abcdefABCDEF" for c in h):
            return img
        r = int(h[0:2], 16)
        g = int(h[2:4], 16)
        b = int(h[4:6], 16)
        overlay = Image.new("RGB", img.size, (r, g, b))
        return Image.blend(img, overlay, alpha=0.5)

    def _normalize_format(self, fmt: str) -> str:
        fmt = fmt.lower().lstrip(".")
        if fmt in ("jpg", "jpeg"):
            return "jpeg"
        if fmt in ("png", "webp"):
            return fmt
        if fmt == "avif":
            return "avif"
        return "jpeg"
    
    def _apply_border(self, img: Image.Image, border_spec: str) -> Image.Image:
        """Apply border to image. Format: 'width' or 'width,color'."""
        parts = border_spec.split(",")
        try:
            width = int(parts[0])
        except (ValueError, IndexError):
            return img
        
        # Parse color if provided
        color = (0, 0, 0)  # Default black
        if len(parts) > 1:
            h = parts[1].lstrip("#")
            if len(h) == 3:
                h = "".join(c * 2 for c in h)
            if len(h) == 6 and all(c in "0123456789abcdefABCDEF" for c in h):
                color = (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))
        
        return ImageOps.expand(img, border=width, fill=color)
    
    def _apply_noise(self, img: Image.Image, amount: int) -> Image.Image:
        """Apply noise/grain effect to image."""
        # Clamp amount to 0-100
        amount = max(0, min(amount, 100))
        if amount == 0:
            return img
        
        # Convert to numpy array
        img_array = np.array(img)
        
        # Generate noise
        noise_strength = amount / 100.0 * 50  # Scale to reasonable range
        noise = np.random.normal(0, noise_strength, img_array.shape).astype(np.int16)
        
        # Add noise and clip to valid range
        noisy = np.clip(img_array.astype(np.int16) + noise, 0, 255).astype(np.uint8)
        
        return Image.fromarray(noisy)
    
    def _apply_pixelate(self, img: Image.Image, pixel_size: int) -> Image.Image:
        """Apply pixelate/mosaic effect."""
        if pixel_size <= 1:
            return img
        
        # Downscale
        small_width = max(1, img.width // pixel_size)
        small_height = max(1, img.height // pixel_size)
        small = img.resize((small_width, small_height), Image.Resampling.NEAREST)
        
        # Upscale back with nearest neighbor
        return small.resize((img.width, img.height), Image.Resampling.NEAREST)
    
    def _generate_lqip(self, img: Image.Image) -> Image.Image:
        """Generate Low Quality Image Placeholder."""
        # Resize to very small (10% of original or 20x20, whichever is larger)
        target_width = max(20, img.width // 10)
        target_height = max(20, img.height // 10)
        
        # Resize and apply heavy blur
        lqip = img.resize((target_width, target_height), Image.Resampling.LANCZOS)
        lqip = lqip.filter(ImageFilter.GaussianBlur(radius=10))
        
        return lqip
