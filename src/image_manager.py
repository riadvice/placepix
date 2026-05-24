from __future__ import annotations

import hashlib
import json
import os
import random
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from src.config import settings


@dataclass
class ImageEntry:
    path: Path
    filename: str
    category: str
    id: int = 0


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
        return settings.images_dir / ".placepix_manifest.json"

    def _load_manifest(self) -> dict[str, int]:
        """Load the persistent id -> filename mapping."""
        if self._manifest_path.exists():
            try:
                with open(self._manifest_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, dict):
                    return {k: int(v) for k, v in data.items()}
            except Exception:
                pass
        return {}

    def _save_manifest(self, mapping: dict[str, int]) -> None:
        """Save the persistent id -> filename mapping."""
        try:
            with open(self._manifest_path, "w", encoding="utf-8") as f:
                json.dump(mapping, f, indent=2, sort_keys=True)
        except Exception:
            pass

    def _rescan(self) -> None:
        images_dir = settings.images_dir
        if not images_dir.exists():
            images_dir.mkdir(parents=True)

        manifest = self._load_manifest()
        next_id = max(manifest.values(), default=0) + 1

        new_categories: dict[str, Category] = {}
        total = 0

        for item in images_dir.iterdir():
            if item.name.startswith(".") or item.name in self.IGNORE_FILES:
                continue

            if item.is_dir():
                entries, meta, next_id = self._scan_subdir(item, manifest, next_id)
                if entries:
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

        self._categories = new_categories
        self._total = total
        self._save_manifest(manifest)

    def _scan_subdir(self, subdir: Path, manifest: dict[str, int], next_id: int) -> tuple[list[ImageEntry], CategoryMeta, int]:
        entries: list[ImageEntry] = []
        for child in subdir.iterdir():
            if child.name.startswith(".") or child.name in self.IGNORE_FILES:
                continue
            if child.is_file() and child.suffix.lower() in self.VALID_EXTS:
                key = f"{subdir.name}/{child.name}"
                if key not in manifest:
                    manifest[key] = next_id
                    next_id += 1
                entries.append(ImageEntry(
                    path=child,
                    filename=child.name,
                    category=subdir.name,
                    id=manifest[key],
                ))

        meta = self._read_meta(subdir)
        return entries, meta, next_id


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
