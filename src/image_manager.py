from __future__ import annotations

import atexit
import hashlib
import io
import json
import logging
import os
import random
import fcntl
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml
from PIL import Image

from src.config import settings

logger = logging.getLogger(__name__)

VALID_CATEGORIES = {"White", "Black", "Gray", "Brown", "Red", "Orange", "Yellow", "Green", "Cyan", "Blue", "Purple", "Pink", "Other"}

# Global flag to ensure S3 scan happens only once across all workers
_s3_scan_done = False

try:
    import boto3
    from botocore.config import Config
    _BOTO3_AVAILABLE = True
except Exception:
    _BOTO3_AVAILABLE = False


def _hex_to_rgb(hex_str: str) -> tuple[int, int, int] | None:
    h = hex_str.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    if len(h) != 6 or not all(c in "0123456789abcdefABCDEF" for c in h):
        return None
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def _color_distance(c1: tuple[int, int, int], c2: tuple[int, int, int]) -> float:
    return ((c1[0] - c2[0]) ** 2 + (c1[1] - c2[1]) ** 2 + (c1[2] - c2[2]) ** 2) ** 0.5


def _extract_dominant_colors_from_bytes(image_data: bytes, num_colors: int = 3) -> list[str]:
    """Extract dominant colors from image bytes."""
    try:
        with Image.open(io.BytesIO(image_data)) as img:
            img = img.convert("RGB")
            img.thumbnail((100, 100))
            quantized = img.quantize(colors=num_colors + 2)
            palette = quantized.getpalette()[: num_colors * 3]
            colors = []
            for i in range(0, len(palette), 3):
                r, g, b = palette[i], palette[i + 1], palette[i + 2]
                colors.append(f"#{r:02x}{g:02x}{b:02x}")
            return colors[:num_colors]
    except Exception:
        return []


def _extract_dominant_colors(image_path: Path, num_colors: int = 3) -> list[str]:
    try:
        with Image.open(image_path) as img:
            img = img.convert("RGB")
            img.thumbnail((100, 100))
            quantized = img.quantize(colors=num_colors + 2)
            palette = quantized.getpalette()[: num_colors * 3]
            colors = []
            for i in range(0, len(palette), 3):
                r, g, b = palette[i], palette[i + 1], palette[i + 2]
                colors.append(f"#{r:02x}{g:02x}{b:02x}")
            return colors[:num_colors]
    except Exception:
        return []


@dataclass
class ImageEntry:
    path: Path | None
    filename: str
    category: str
    id: int = 0
    s3_key: str = ""
    ai: bool = False


@dataclass
class CategoryMeta:
    name: str = ""
    description: str = ""
    author: str = ""
    tags: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CategoryMeta:
        return cls(
            name=data.get("name", ""),
            description=data.get("description", ""),
            author=data.get("author", ""),
            tags=data.get("tags", []),
        )


@dataclass
class Category:
    name: str  # directory name
    meta: CategoryMeta
    entries: list[ImageEntry]


class ImageManager:
    ROOT_KEY = "__root"
    IGNORE_FILES = {".cache", ".DS_Store", "Thumbs.db"}
    VALID_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp", ".tiff"}

    def __init__(self) -> None:
        self._categories: dict[str, Category] = {}
        self._total = 0
        self._colors: dict[int, list[str]] = {}
        self._scanning_colors = False
        self._s3_scanned = False
        self._is_leader = self._acquire_leader_lock()
        self._rescan()

    @property
    def categories(self) -> dict[str, Category]:
        return self._categories

    @property
    def total(self) -> int:
        return self._total

    def pick(self, category: str | None = None, seed: str | None = None) -> ImageEntry | None:
        cats = list(self._categories.values())
        if not cats:
            return None

        if category is None or category == "":
            # pick random category, deterministically if seed given
            if seed is not None:
                rng = random.Random(hashlib.sha256(seed.encode()).hexdigest())
                cat = rng.choice(cats)
            else:
                cat = random.choice(cats)
        else:
            # 1. Check AI-generated pool first
            ai_cat = self._categories.get(f"ai-generated/{category}")
            if ai_cat is not None and ai_cat.entries:
                cat = ai_cat
            else:
                # 2. Fallback to regular category
                cat = self._categories.get(category)
                if cat is None:
                    return None

        if not cat.entries:
            return None

        if seed is not None:
            # deterministic per category+seed
            hash_input = f"{seed}:{cat.name}"
            idx = int(hashlib.sha256(hash_input.encode()).hexdigest(), 16) % len(cat.entries)
            return cat.entries[idx]

        return random.choice(cat.entries)

    def pick_ai(self, category: str | None = None, seed: str | None = None) -> ImageEntry | None:
        """Pick only from AI-generated pool for a category. Returns None if no AI images."""
        ai_cat_name = f"ai-generated/{category}" if category else "ai-generated"
        cat = self._categories.get(ai_cat_name)
        if cat is None or not cat.entries:
            return None

        if seed is not None:
            hash_input = f"{seed}:{cat.name}"
            idx = int(hashlib.sha256(hash_input.encode()).hexdigest(), 16) % len(cat.entries)
            return cat.entries[idx]

        return random.choice(cat.entries)

    def get_entry(self, category: str, filename: str) -> ImageEntry | None:
        cat = self._categories.get(category)
        if cat is None:
            return None
        for entry in cat.entries:
            if entry.filename == filename:
                return entry
        return None

    def get_by_filename(self, filename: str) -> ImageEntry | None:
        """Look up an image by filename across all categories."""
        for cat in self._categories.values():
            for entry in cat.entries:
                if entry.filename == filename:
                    return entry
        return None

    def get_by_id(self, image_id: int) -> ImageEntry | None:
        """Look up an image by its stable numeric ID."""
        for cat in self._categories.values():
            for entry in cat.entries:
                if entry.id == image_id:
                    return entry
        return None

    def list_entries(self, page: int = 1, per_page: int = 20) -> tuple[list[ImageEntry], int]:
        """Return a flat, paginated list of all entries and total count."""
        all_entries: list[ImageEntry] = []
        for cat in self._categories.values():
            all_entries.extend(cat.entries)
        all_entries.sort(key=lambda e: e.id)
        total = len(all_entries)
        start = (page - 1) * per_page
        end = start + per_page
        return all_entries[start:end], total

    def list_categories(self) -> list[dict[str, Any]]:
        result = []
        for name, cat in self._categories.items():
            result.append({
                "name": name,
                "count": len(cat.entries),
                "display_name": cat.meta.name or name,
                "description": cat.meta.description,
                "author": cat.meta.author,
                "tags": cat.meta.tags,
            })
        return result

    def rescan(self) -> None:
        self._rescan()

    @property
    def _manifest_path(self) -> Path:
        return settings.data_dir / ".placepix_manifest.json"

    def _load_manifest(self) -> dict[str, int]:
        """Load the persistent id -> filename mapping."""
        if self._manifest_path.exists():
            try:
                with open(self._manifest_path, "r", encoding="utf-8") as f:
                    # Acquire shared lock for reading
                    fcntl.flock(f.fileno(), fcntl.LOCK_SH)
                    data = json.load(f)
                    fcntl.flock(f.fileno(), fcntl.LOCK_UN)
                if isinstance(data, dict):
                    return {k: int(v) for k, v in data.items()}
            except Exception:
                pass
        return {}

    def _save_manifest(self, mapping: dict[str, int]) -> None:
        """Save the persistent id -> filename mapping."""
        try:
            with open(self._manifest_path, "w", encoding="utf-8") as f:
                # Acquire exclusive lock for writing
                fcntl.flock(f.fileno(), fcntl.LOCK_EX)
                json.dump(mapping, f, indent=2, sort_keys=True)
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)
        except Exception:
            pass

    @property
    def _colors_path(self) -> Path:
        return settings.data_dir / ".placepix_colors.json"

    def _acquire_leader_lock(self) -> bool:
        """Try to acquire leader lock. Returns True if this worker is the leader."""
        lock_file = settings.data_dir / ".placepix_leader.lock"
        try:
            lock_file.touch(exist_ok=True)
            f = open(lock_file, "w")
            try:
                fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                # Write our PID to the lock file
                f.write(str(os.getpid()))
                f.flush()
                self._leader_lock_file = f
                logger.info(f"Worker {os.getpid()} acquired leader lock")
                # Register cleanup on exit
                atexit.register(self._release_leader_lock)
                return True
            except (IOError, BlockingIOError):
                f.close()
                logger.debug(f"Worker {os.getpid()} did not acquire leader lock")
                return False
        except Exception as e:
            logger.warning(f"Failed to acquire leader lock: {e}")
            return False

    def _release_leader_lock(self) -> None:
        """Release the leader lock."""
        if hasattr(self, '_leader_lock_file') and self._leader_lock_file:
            try:
                fcntl.flock(self._leader_lock_file.fileno(), fcntl.LOCK_UN)
                self._leader_lock_file.close()
                logger.info(f"Worker {os.getpid()} released leader lock")
            except Exception as e:
                logger.warning(f"Failed to release leader lock: {e}")

    def _load_colors(self) -> dict[int, list[str]]:
        if self._colors_path.exists():
            try:
                with open(self._colors_path, "r", encoding="utf-8") as f:
                    # Acquire shared lock for reading
                    fcntl.flock(f.fileno(), fcntl.LOCK_SH)
                    data = json.load(f)
                    fcntl.flock(f.fileno(), fcntl.LOCK_UN)
                if isinstance(data, dict):
                    return {int(k): list(v) for k, v in data.items()}
            except Exception:
                pass
        return {}

    def _save_colors(self, colors: dict[int, list[str]]) -> None:
        try:
            with open(self._colors_path, "w", encoding="utf-8") as f:
                # Acquire exclusive lock for writing
                fcntl.flock(f.fileno(), fcntl.LOCK_EX)
                json.dump(colors, f, indent=2, sort_keys=True)
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)
        except Exception:
            pass

    def _rescan(self) -> None:
        images_dir = settings.images_dir
        data_dir = settings.data_dir
        
        if not images_dir.exists():
            images_dir.mkdir(parents=True)
        if not data_dir.exists():
            data_dir.mkdir(parents=True)

        logger.info(f"Scanning image directory: {images_dir}")
        manifest = self._load_manifest()
        next_id = max(manifest.values(), default=0) + 1

        new_categories: dict[str, Category] = {}
        total = 0

        # Scan images_dir for user images
        logger.debug(f"  Scanning: {images_dir}")
        for item in images_dir.iterdir():
            if item.name.startswith(".") or item.name in self.IGNORE_FILES:
                continue

            if item.is_dir():
                # Handle ai-generated directory specially
                if item.name == "ai-generated":
                    for sub_item in item.iterdir():
                        if sub_item.name.startswith(".") or sub_item.name in self.IGNORE_FILES:
                            continue
                        if sub_item.is_dir():
                            ai_entries, ai_meta, next_id = self._scan_subdir(sub_item, manifest, next_id, ai=True)
                            ai_cat_name = f"ai-generated/{sub_item.name}"
                            if ai_entries:
                                new_categories[ai_cat_name] = Category(
                                    name=ai_cat_name,
                                    meta=ai_meta,
                                    entries=ai_entries,
                                )
                                total += len(ai_entries)
                    continue

                entries, meta, next_id = self._scan_subdir(item, manifest, next_id)
                if entries:
                    if item.name in new_categories:
                        # Merge entries if category already exists
                        new_categories[item.name].entries.extend(entries)
                    else:
                        new_categories[item.name] = Category(
                            name=item.name,
                            meta=meta,
                            entries=entries,
                        )
                        total += len(entries)
                elif item.suffix.lower() in self.VALID_EXTS:
                    root = new_categories.get(self.ROOT_KEY)
                    if root is None:
                        meta = self._read_meta(images_dir)
                        new_categories[self.ROOT_KEY] = Category(
                            name=self.ROOT_KEY,
                            meta=meta,
                            entries=[],
                        )
                        root = new_categories[self.ROOT_KEY]
                    key = f"{self.ROOT_KEY}/{item.name}"
                    if key not in manifest:
                        manifest[key] = next_id
                        next_id += 1
                    root.entries.append(ImageEntry(
                        path=item,
                        filename=item.name,
                        category=self.ROOT_KEY,
                        id=manifest[key],
                    ))
                    total += 1

        # Only scan S3 on first rescan (startup) in each worker
        logger.debug(f"S3 scan check: enabled={settings.s3_enabled}, boto3={_BOTO3_AVAILABLE}, endpoint={bool(settings.s3_endpoint)}, bucket={bool(settings.s3_bucket)}, already_scanned={self._s3_scanned}")
        if settings.s3_enabled and _BOTO3_AVAILABLE and settings.s3_endpoint and settings.s3_bucket and not self._s3_scanned:
            logger.info(f"Scanning S3 bucket: {settings.s3_bucket}")
            s3_categories, next_id = self._scan_s3(manifest, next_id)
            for cat_name, category in s3_categories.items():
                if cat_name in new_categories:
                    new_categories[cat_name].entries.extend(category.entries)
                else:
                    new_categories[cat_name] = category
                total += len(category.entries)
            self._s3_scanned = True
            logger.info(f"S3 scan complete: found {len(s3_categories)} categories")
        else:
            logger.debug("S3 scan skipped (disabled, not configured, or already scanned)")

        colors = self._load_colors()

        self._categories = new_categories
        self._total = total
        self._colors = colors
        self._save_manifest(manifest)
        logger.info(f"Scan complete: {total} images in {len(new_categories)} categories")

    def scan_colors(self) -> None:
        """Extract dominant colors for images that don't have them yet."""
        if self._scanning_colors:
            return
        self._scanning_colors = True
        try:
            colors = self._load_colors()
            missing_entries: list[ImageEntry] = []
            for cat in self._categories.values():
                for entry in cat.entries:
                    if entry.id not in colors:
                        missing_entries.append(entry)

            if not missing_entries:
                logger.info("Color scan: all images already have colors")
                self._colors = colors
                return

            logger.info(f"Color scan: extracting colors for {len(missing_entries)} images")

            # Initialize S3 client if needed for S3 images
            s3_client = None
            has_s3_images = any(e.s3_key for e in missing_entries)
            if has_s3_images and _BOTO3_AVAILABLE and settings.s3_enabled:
                try:
                    s3_client = boto3.client(
                        "s3",
                        endpoint_url=settings.s3_endpoint,
                        aws_access_key_id=settings.s3_access_key,
                        aws_secret_access_key=settings.s3_secret_key,
                        region_name=settings.s3_region or "auto",
                        config=Config(signature_version="s3v4"),
                    )
                except Exception as e:
                    logger.warning(f"Failed to initialize S3 client for color scan: {e}")

            total = len(missing_entries)
            last_logged_percent = 0

            for i, entry in enumerate(missing_entries, 1):
                source = entry.path if entry.path else f"S3:{entry.s3_key}"
                logger.info(f"Color scan [{i}/{total}]: processing {entry.filename} from {source}")
                extracted: list[str] = []

                if entry.path is not None:
                    # Local file
                    extracted = _extract_dominant_colors(entry.path)
                elif entry.s3_key and s3_client:
                    # S3 image - download and extract
                    try:
                        response = s3_client.get_object(
                            Bucket=settings.s3_bucket, Key=entry.s3_key
                        )
                        image_data = response["Body"].read()
                        extracted = _extract_dominant_colors_from_bytes(image_data)
                    except Exception as e:
                        logger.warning(f"Failed to extract colors from S3 image {entry.s3_key}: {e}")

                if extracted:
                    colors[entry.id] = extracted
                    logger.info(f"Color scan [{i}/{total}]: {entry.filename} -> {extracted}")
                else:
                    logger.warning(f"Color scan [{i}/{total}]: {entry.filename} -> no colors extracted")

                # Log progress every 5%
                percent = int((i / total) * 100)
                if percent >= last_logged_percent + 5 or i == total:
                    logger.info(f"Color scan progress: {percent}% ({i}/{total} images)")
                    last_logged_percent = percent

                # Save colors periodically
                if i % 10 == 0 or i == total:
                    self._colors = colors
                    self._save_colors(colors)

            self._colors = colors
            self._save_colors(colors)
            logger.info(f"Color scan complete: {len(missing_entries)} images processed")
        finally:
            self._scanning_colors = False

    def _scan_s3(self, manifest: dict[str, int], next_id: int) -> tuple[dict[str, Category], int]:
        """Scan S3 bucket for images and return categories."""
        new_categories: dict[str, Category] = {}
        try:
            logger.info(f"Connecting to S3: endpoint={settings.s3_endpoint}, bucket={settings.s3_bucket}")
            client = boto3.client(
                "s3",
                endpoint_url=settings.s3_endpoint,
                aws_access_key_id=settings.s3_access_key,
                aws_secret_access_key=settings.s3_secret_key,
                region_name=settings.s3_region or "auto",
                config=Config(signature_version="s3v4"),
            )
            prefix = settings.s3_prefix
            if prefix and not prefix.endswith("/"):
                prefix += "/"

            logger.info(f"Listing S3 objects with prefix: '{prefix}'")
            paginator = client.get_paginator("list_objects_v2")
            pages = paginator.paginate(Bucket=settings.s3_bucket, Prefix=prefix)

            for page in pages:
                for obj in page.get("Contents", []):
                    key = obj["Key"]
                    if key.endswith("/"):
                        continue
                    basename = key.split("/")[-1]
                    if not basename or basename.startswith("."):
                        continue
                    ext = os.path.splitext(basename)[1].lower()
                    if ext not in self.VALID_EXTS:
                        continue

                    relative_key = key[len(prefix):] if prefix else key
                    parts = relative_key.split("/")
                    if len(parts) > 1 and parts[0]:
                        # Handle ai-generated/nature/... structure
                        if parts[0] == "ai-generated" and len(parts) > 2:
                            cat_name = f"ai-generated/{parts[1]}"
                        else:
                            cat_name = parts[0]
                        filename = parts[-1]
                    else:
                        cat_name = self.ROOT_KEY
                        filename = basename

                    manifest_key = f"s3://{settings.s3_bucket}/{key}"
                    if manifest_key not in manifest:
                        manifest[manifest_key] = next_id
                        next_id += 1

                    if cat_name not in new_categories:
                        new_categories[cat_name] = Category(
                            name=cat_name,
                            meta=CategoryMeta(),
                            entries=[],
                        )

                    new_categories[cat_name].entries.append(ImageEntry(
                        path=None,
                        filename=filename,
                        category=cat_name,
                        id=manifest[manifest_key],
                        s3_key=key,
                        ai=cat_name.startswith("ai-generated/"),
                    ))
        except Exception as e:
            logger.error(f"S3 scan failed: {e}")
            import traceback
            logger.error(traceback.format_exc())

        return new_categories, next_id

    def _scan_subdir(self, subdir: Path, manifest: dict[str, int], next_id: int, ai: bool = False) -> tuple[list[ImageEntry], CategoryMeta, int]:
        entries: list[ImageEntry] = []
        # For AI images, include the ai-generated prefix in the key to avoid collisions
        if ai:
            key_prefix = f"ai-generated/{subdir.name}"
            cat_name = f"ai-generated/{subdir.name}"
        else:
            key_prefix = subdir.name
            cat_name = subdir.name

        for child in subdir.iterdir():
            if child.name.startswith(".") or child.name in self.IGNORE_FILES:
                continue
            if child.is_file() and child.suffix.lower() in self.VALID_EXTS:
                key = f"{key_prefix}/{child.name}"
                if key not in manifest:
                    manifest[key] = next_id
                    next_id += 1
                entries.append(ImageEntry(
                    path=child,
                    filename=child.name,
                    category=cat_name,
                    id=manifest[key],
                    ai=ai,
                ))

        meta = self._read_meta(subdir)
        return entries, meta, next_id


    def get_colors(self, image_id: int) -> list[str]:
        return self._colors.get(image_id, [])

    def pick_by_color(self, hex_color: str, category: str | None = None) -> ImageEntry | None:
        target_rgb = _hex_to_rgb(hex_color)
        if target_rgb is None:
            return None

        candidates = []
        cats = [self._categories.get(category)] if category else list(self._categories.values())
        for cat in cats:
            if cat is None:
                continue
            for entry in cat.entries:
                for color_hex in self._colors.get(entry.id, []):
                    color_rgb = _hex_to_rgb(color_hex)
                    if color_rgb and _color_distance(target_rgb, color_rgb) < 100:
                        candidates.append(entry)
                        break

        if not candidates:
            return None
        return random.choice(candidates)

    def find_by_color(self, hex_color: str) -> list[ImageEntry]:
        target_rgb = _hex_to_rgb(hex_color)
        if target_rgb is None:
            return []

        matches = []
        for cat in self._categories.values():
            for entry in cat.entries:
                for color_hex in self._colors.get(entry.id, []):
                    color_rgb = _hex_to_rgb(color_hex)
                    if color_rgb and _color_distance(target_rgb, color_rgb) < 100:
                        matches.append(entry)
                        break
        return matches

    @staticmethod
    def _hex_to_hue_category(hex_color: str) -> str:
        rgb = _hex_to_rgb(hex_color)
        if rgb is None:
            return "Other"
        r, g, b = rgb
        total = r + g + b
        # Luminance-based: White and Black before hue
        if total > 720:
            return "White"
        if total < 90:
            return "Black"
        r, g, b = r / 255.0, g / 255.0, b / 255.0
        mx, mn = max(r, g, b), min(r, g, b)
        if mx == mn:
            return "Gray"
        d = mx - mn
        if mx == r:
            h = (g - b) / d + (6 if g < b else 0)
        elif mx == g:
            h = (b - r) / d + 2
        else:
            h = (r - g) / d + 4
        h *= 60
        # Brown: dark, earthy tones in orange/red range
        if total < 380 and (h < 45 or h >= 15):
            if h < 45 and h >= 15:
                return "Brown"
        if h < 15 or h >= 345:
            return "Red"
        if h < 45:
            return "Orange"
        if h < 75:
            return "Yellow"
        if h < 165:
            return "Green"
        if h < 195:
            return "Cyan"
        if h < 255:
            return "Blue"
        if h < 285:
            return "Purple"
        if h < 345:
            return "Pink"
        return "Other"

    def list_colors(self, category: str = "", search: str = "") -> list[dict[str, Any]]:
        """Return unique dominant colors across all images, sorted by image count."""
        if category and category not in VALID_CATEGORIES:
            raise ValueError(f"Invalid category: {category}. Valid categories are: {', '.join(sorted(VALID_CATEGORIES))}")
        
        color_counts: dict[str, int] = {}
        color_samples: dict[str, list[int]] = {}

        # Snapshot to avoid RuntimeError if background thread mutates dict
        for image_id, colors in list(self._colors.items()):
            for hex_color in colors:
                if category and self._hex_to_hue_category(hex_color) != category:
                    continue
                if search and search.lower() not in hex_color.lower():
                    continue
                color_counts[hex_color] = color_counts.get(hex_color, 0) + 1
                samples = color_samples.setdefault(hex_color, [])
                if len(samples) < 3:
                    samples.append(image_id)

        result = []
        for hex_color in sorted(color_counts.keys(), key=lambda h: -color_counts[h]):
            result.append({
                "hex": hex_color,
                "count": color_counts[hex_color],
                "sample_ids": color_samples[hex_color],
                "category": self._hex_to_hue_category(hex_color),
            })
        return result

    def _read_meta(self, directory: Path) -> CategoryMeta:
        json_file = directory / "category.json"
        yaml_file = directory / "category.yml"

        if json_file.exists():
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return CategoryMeta.from_dict(data)
            except Exception:
                pass

        if yaml_file.exists():
            try:
                with open(yaml_file, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                if isinstance(data, dict):
                    return CategoryMeta.from_dict(data)
            except Exception:
                pass

        return CategoryMeta()
