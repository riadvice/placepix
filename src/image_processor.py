from __future__ import annotations

import io
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps

try:
    import pillow_avif  # noqa: F401
    _AVIF_AVAILABLE = True
except Exception:
    _AVIF_AVAILABLE = False

try:
    import cv2
    _OPENCV_AVAILABLE = True
except Exception:
    _OPENCV_AVAILABLE = False


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
        image_path: Path | io.BytesIO,
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
        watermark: str = "",
        watermark_config: dict | None = None,
        invert: bool = False,
        posterize: int = 0,
        solarize: int = 0,
        duotone: str = "",
        sharpen: float = 0.0,
        emboss: bool = False,
        halftone: int = 0,
        edges: str = "",
        oil_painting: bool = False,
        pencil_sketch: bool = False,
        cartoon: bool = False,
        vignette: float = 0.0,
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

            # Color effects
            if invert:
                img = self._apply_invert(img)

            if posterize > 0:
                img = self._apply_posterize(img, posterize)

            if solarize > 0:
                img = self._apply_solarize(img, solarize)

            if duotone:
                # Parse duotone colors: "color1,color2"
                colors = duotone.split(",")
                if len(colors) == 2:
                    img = self._apply_duotone(img, colors[0], colors[1])

            # Texture effects
            if sharpen > 0:
                img = self._apply_sharpen(img, sharpen)

            if emboss:
                img = self._apply_emboss(img)

            if halftone > 0:
                img = self._apply_halftone(img, halftone)

            # Edge detection
            if edges:
                img = self._apply_edges(img, edges)

            # Artistic effects
            if oil_painting:
                img = self._apply_oil_painting(img)

            if pencil_sketch:
                img = self._apply_pencil_sketch(img)

            if cartoon:
                img = self._apply_cartoon(img)

            # Lighting effects
            if vignette > 0:
                img = self._apply_vignette(img, vignette)

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
            
            # Apply watermark
            if watermark and watermark_config:
                img = self._apply_watermark(img, watermark, watermark_config)

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
        
        if fit == "smart":
            return self._smart_crop(img, width, height)

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
    
    def _smart_crop(self, img: Image.Image, width: int, height: int) -> Image.Image:
        """Smart crop using OpenCV face detection, fallback to center crop."""
        if not _OPENCV_AVAILABLE:
            # Fallback to center crop if OpenCV not available
            return self._crop_center(img, width, height)
        
        # Convert PIL to OpenCV format
        img_array = np.array(img)
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        
        # Load Haar Cascade for face detection
        try:
            cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            face_cascade = cv2.CascadeClassifier(cascade_path)
            faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
        except Exception:
            # Fallback to center crop on error
            return self._crop_center(img, width, height)
        
        if len(faces) == 0:
            # No faces detected, use center crop
            return self._crop_center(img, width, height)
        
        # Calculate bounding box that includes all faces
        x_min = min(x for x, y, w, h in faces)
        y_min = min(y for x, y, w, h in faces)
        x_max = max(x + w for x, y, w, h in faces)
        y_max = max(y + h for x, y, w, h in faces)
        
        # Add padding around faces (20%)
        face_width = x_max - x_min
        face_height = y_max - y_min
        padding_x = int(face_width * 0.2)
        padding_y = int(face_height * 0.2)
        
        x_min = max(0, x_min - padding_x)
        y_min = max(0, y_min - padding_y)
        x_max = min(img.width, x_max + padding_x)
        y_max = min(img.height, y_max + padding_y)
        
        # Calculate crop region maintaining target aspect ratio
        target_ratio = width / height
        current_width = x_max - x_min
        current_height = y_max - y_min
        current_ratio = current_width / current_height
        
        if current_ratio > target_ratio:
            # Too wide, adjust width
            new_width = int(current_height * target_ratio)
            x_center = (x_min + x_max) // 2
            x_min = max(0, x_center - new_width // 2)
            x_max = min(img.width, x_min + new_width)
        else:
            # Too tall, adjust height
            new_height = int(current_width / target_ratio)
            y_center = (y_min + y_max) // 2
            y_min = max(0, y_center - new_height // 2)
            y_max = min(img.height, y_min + new_height)
        
        # Crop and resize
        cropped = img.crop((x_min, y_min, x_max, y_max))
        return cropped.resize((width, height), Image.Resampling.LANCZOS)
    
    def _apply_watermark(self, img: Image.Image, position: str, config: dict) -> Image.Image:
        """Apply watermark to image."""
        # Get watermark settings
        watermark_image = config.get("watermark_image", "")
        watermark_text = config.get("watermark_text", "")
        opacity = config.get("watermark_opacity", 0.5)
        
        # Use provided position or config position
        if not position or position == "true":
            position = config.get("watermark_position", "bottom-right")
        
        # Create watermark layer
        watermark = None
        
        if watermark_image and Path(watermark_image).exists():
            # Load image watermark
            try:
                with Image.open(watermark_image) as wm:
                    wm = wm.convert("RGBA")
                    # Scale watermark to 20% of image width
                    wm_width = int(img.width * 0.2)
                    wm_height = int(wm.height * (wm_width / wm.width))
                    watermark = wm.resize((wm_width, wm_height), Image.Resampling.LANCZOS)
            except Exception:
                watermark = None
        
        if watermark is None and watermark_text:
            # Create text watermark
            wm_img = Image.new("RGBA", img.size, (255, 255, 255, 0))
            draw = ImageDraw.Draw(wm_img)
            font_size = max(12, int(img.width * 0.03))
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
            except Exception:
                font = ImageFont.load_default()
            
            bbox = draw.textbbox((0, 0), watermark_text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            # Position text
            x, y = self._get_watermark_position(position, img.width, img.height, text_width, text_height)
            draw.text((x, y), watermark_text, fill=(255, 255, 255, int(255 * opacity)), font=font)
            watermark = wm_img
        
        if watermark is None:
            return img
        
        # Apply watermark with opacity
        if watermark.mode != "RGBA":
            watermark = watermark.convert("RGBA")
        
        # Adjust opacity
        alpha = watermark.split()[3]
        alpha = ImageEnhance.Brightness(alpha).enhance(opacity)
        watermark.putalpha(alpha)
        
        # Position watermark
        if watermark.size != img.size:
            wm_width, wm_height = watermark.size
            x, y = self._get_watermark_position(position, img.width, img.height, wm_width, wm_height)
        else:
            x, y = 0, 0
        
        # Composite
        img_rgba = img.convert("RGBA")
        img_rgba.paste(watermark, (x, y), watermark)
        return img_rgba.convert("RGB")
    
    def generate_gradient(
        self,
        width: int,
        height: int,
        from_hex: str,
        to_hex: str,
        angle: int = 0,
        gradient_type: str = "linear",
    ) -> bytes:
        """Generate a gradient placeholder image."""
        from_hex = from_hex.lstrip("#")
        to_hex = to_hex.lstrip("#")
        if len(from_hex) == 3:
            from_hex = "".join(c * 2 for c in from_hex)
        if len(to_hex) == 3:
            to_hex = "".join(c * 2 for c in to_hex)
        if len(from_hex) != 6 or len(to_hex) != 6:
            raise ValueError("invalid hex color")

        r1, g1, b1 = int(from_hex[0:2], 16), int(from_hex[2:4], 16), int(from_hex[4:6], 16)
        r2, g2, b2 = int(to_hex[0:2], 16), int(to_hex[2:4], 16), int(to_hex[4:6], 16)

        w, h = self.clamp_size(width, height)
        if w == 0 or h == 0:
            w, h = 500, 300

        if gradient_type == "radial":
            # Radial gradient from center - use numpy for speed
            import numpy as np
            y, x = np.ogrid[:h, :w]
            dx = x - w / 2
            dy = y - h / 2
            dist = np.sqrt(dx * dx + dy * dy)
            max_dist = np.sqrt((w / 2) ** 2 + (h / 2) ** 2)
            t = np.clip(dist / max_dist, 0, 1)
            
            r = (r1 + (r2 - r1) * t).astype(np.uint8)
            g = (g1 + (g2 - g1) * t).astype(np.uint8)
            b = (b1 + (b2 - b1) * t).astype(np.uint8)
            
            rgb = np.dstack((r, g, b))
            img = Image.fromarray(rgb, "RGB")
        else:
            # Linear gradient - use numpy for speed
            import numpy as np
            y, x = np.ogrid[:h, :w]
            
            angle_rad = angle * math.pi / 180
            ux = w * math.cos(angle_rad)
            uy = h * math.sin(angle_rad)
            max_proj = math.sqrt(ux * ux + uy * uy)
            if max_proj == 0:
                max_proj = 1
            
            proj = (x * ux + y * uy) / max_proj
            t = np.clip(proj / max_proj, 0, 1)
            
            r = (r1 + (r2 - r1) * t).astype(np.uint8)
            g = (g1 + (g2 - g1) * t).astype(np.uint8)
            b = (b1 + (b2 - b1) * t).astype(np.uint8)
            
            rgb = np.dstack((r, g, b))
            img = Image.fromarray(rgb, "RGB")

        buffer = io.BytesIO()
        img.save(buffer, format="PNG", optimize=True)
        return buffer.getvalue()

    def _get_watermark_position(self, position: str, img_width: int, img_height: int, wm_width: int, wm_height: int) -> tuple[int, int]:
        """Calculate watermark position."""
        padding = 20
        
        position = position.lower()
        if position == "top-left":
            return (padding, padding)
        elif position == "top-right":
            return (img_width - wm_width - padding, padding)
        elif position == "bottom-left":
            return (padding, img_height - wm_height - padding)
        elif position == "bottom-right":
            return (img_width - wm_width - padding, img_height - wm_height - padding)
        elif position == "center":
            return ((img_width - wm_width) // 2, (img_height - wm_height) // 2)
        else:
            # Default to bottom-right
            return (img_width - wm_width - padding, img_height - wm_height - padding)
    
    def _apply_invert(self, img: Image.Image) -> Image.Image:
        """Invert image colors."""
        return ImageOps.invert(img)
    
    def _apply_posterize(self, img: Image.Image, levels: int) -> Image.Image:
        """Reduce color palette to N levels (1-8 bits)."""
        if levels < 1 or levels > 8:
            levels = 4
        # Posterize takes bits to keep (inverse of levels)
        bits = 9 - levels  # levels=1 -> bits=8, levels=8 -> bits=1
        return ImageOps.posterize(img, bits)
    
    def _apply_solarize(self, img: Image.Image, threshold: int) -> Image.Image:
        """Solarize image (invert pixels above threshold)."""
        threshold = max(0, min(threshold, 255))
        return ImageOps.solarize(img, threshold)
    
    def _apply_duotone(self, img: Image.Image, color1_hex: str, color2_hex: str) -> Image.Image:
        """Map grayscale to two hex colors."""
        def parse_hex(h: str) -> tuple[int, int, int]:
            h = h.lstrip("#")
            if len(h) == 3:
                h = "".join(c * 2 for c in h)
            if len(h) != 6 or not all(c in "0123456789abcdefABCDEF" for c in h):
                return (0, 0, 0)
            return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))
        
        c1 = parse_hex(color1_hex)
        c2 = parse_hex(color2_hex)
        
        # Convert to grayscale
        gray = img.convert("L")
        
        # Create duotone image
        duotone = Image.new("RGB", img.size)
        pixels = duotone.load()
        gray_pixels = gray.load()
        
        for y in range(img.height):
            for x in range(img.width):
                g = gray_pixels[x, y]
                # Interpolate between color1 and color2 based on grayscale value
                ratio = g / 255.0
                r = int(c1[0] * (1 - ratio) + c2[0] * ratio)
                g_val = int(c1[1] * (1 - ratio) + c2[1] * ratio)
                b = int(c1[2] * (1 - ratio) + c2[2] * ratio)
                pixels[x, y] = (r, g_val, b)
        
        return duotone
    
    def _apply_sharpen(self, img: Image.Image, amount: float) -> Image.Image:
        """Sharpen image using unsharp mask."""
        if amount <= 0:
            return img
        # Clamp amount to reasonable range
        amount = min(amount, 3.0)
        return img.filter(ImageFilter.UnsharpMask(radius=2, percent=int(amount * 100), threshold=3))
    
    def _apply_emboss(self, img: Image.Image) -> Image.Image:
        """Apply emboss effect (3D relief)."""
        return img.filter(ImageFilter.EMBOSS)
    
    def _apply_halftone(self, img: Image.Image, dot_size: int) -> Image.Image:
        """Apply halftone dot pattern effect."""
        if dot_size < 2:
            dot_size = 4
        
        # Convert to grayscale
        gray = img.convert("L")
        
        # Create halftone image
        halftone = Image.new("RGB", img.size, (255, 255, 255))
        draw = ImageDraw.Draw(halftone)
        
        for y in range(0, img.height, dot_size):
            for x in range(0, img.width, dot_size):
                # Get average brightness in this block
                block = gray.crop((x, y, min(x + dot_size, img.width), min(y + dot_size, img.height)))
                brightness = sum(block.getdata()) / (block.width * block.height)
                
                # Calculate dot radius based on brightness
                radius = (dot_size / 2) * (1 - brightness / 255)
                if radius > 0:
                    center_x = x + dot_size / 2
                    center_y = y + dot_size / 2
                    draw.ellipse(
                        [center_x - radius, center_y - radius, center_x + radius, center_y + radius],
                        fill=(0, 0, 0)
                    )
        
        return halftone
    
    def _apply_edges(self, img: Image.Image, method: str) -> Image.Image:
        """Apply edge detection (sobel or canny)."""
        if not _OPENCV_AVAILABLE:
            return img
        
        img_array = np.array(img)
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        
        if method == "canny":
            edges = cv2.Canny(gray, 100, 200)
        else:  # sobel (default)
            sobelx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
            sobely = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
            edges = np.sqrt(sobelx**2 + sobely**2)
            edges = np.clip(edges, 0, 255).astype(np.uint8)
        
        # Convert back to RGB
        edges_rgb = cv2.cvtColor(edges, cv2.COLOR_GRAY2RGB)
        return Image.fromarray(edges_rgb)
    
    def _apply_oil_painting(self, img: Image.Image) -> Image.Image:
        """Apply oil painting effect using OpenCV stylization."""
        if not _OPENCV_AVAILABLE:
            return img
        
        img_array = np.array(img)
        # cv2.stylization is available in newer OpenCV versions
        try:
            stylized = cv2.stylization(img_array, sigma_s=60, sigma_r=0.45)
            return Image.fromarray(stylized)
        except Exception:
            # Fallback: bilateral filter for smoothing
            smoothed = cv2.bilateralFilter(img_array, 15, 80, 80)
            return Image.fromarray(smoothed)
    
    def _apply_pencil_sketch(self, img: Image.Image) -> Image.Image:
        """Apply pencil sketch effect using OpenCV."""
        if not _OPENCV_AVAILABLE:
            return img
        
        img_array = np.array(img)
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        
        try:
            # cv2.pencilSketch returns (gray_sketch, color_sketch)
            gray_sketch, _ = cv2.pencilSketch(gray, sigma_s=60, sigma_r=0.07, shade_factor=0.05)
            # Convert to RGB
            sketch_rgb = cv2.cvtColor(gray_sketch, cv2.COLOR_GRAY2RGB)
            return Image.fromarray(sketch_rgb)
        except Exception:
            # Fallback: edge detection + inversion
            edges = cv2.Canny(gray, 50, 150)
            edges_rgb = cv2.cvtColor(edges, cv2.COLOR_GRAY2RGB)
            return Image.fromarray(edges_rgb)
    
    def _apply_cartoon(self, img: Image.Image) -> Image.Image:
        """Apply cartoon effect using OpenCV."""
        if not _OPENCV_AVAILABLE:
            return img
        
        img_array = np.array(img)
        
        # Bilateral filter for color quantization
        color = cv2.bilateralFilter(img_array, 15, 250, 250)
        
        # Edge detection
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        edges = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 9, 9)
        edges = cv2.cvtColor(edges, cv2.COLOR_GRAY2RGB)
        
        # Combine color and edges
        cartoon = cv2.bitwise_and(color, edges)
        return Image.fromarray(cartoon)
    
    def _apply_vignette(self, img: Image.Image, intensity: float) -> Image.Image:
        """Apply vignette effect (darken edges)."""
        if intensity <= 0:
            return img
        
        intensity = min(intensity, 1.0)
        
        # Create radial gradient mask
        w, h = img.size
        y, x = np.ogrid[:h, :w]
        center_x, center_y = w / 2, h / 2
        
        # Calculate distance from center
        dx = x - center_x
        dy = y - center_y
        dist = np.sqrt(dx * dx + dy * dy)
        max_dist = np.sqrt(center_x**2 + center_y**2)
        
        # Create vignette mask (darken edges)
        mask = 1 - (dist / max_dist) * intensity
        mask = np.clip(mask, 0, 1)
        
        # Apply mask to each channel
        img_array = np.array(img).astype(np.float32)
        for i in range(3):
            img_array[:, :, i] *= mask
        
        return Image.fromarray(np.clip(img_array, 0, 255).astype(np.uint8))
