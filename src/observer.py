from __future__ import annotations

import time
from threading import Thread

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from src.config import settings
from src.image_manager import ImageManager


class _RescanHandler(FileSystemEventHandler):
    def __init__(self, manager: ImageManager) -> None:
        self.manager = manager
        self._last_rescan = 0.0
        self._debounce_seconds = 1.0

    def on_any_event(self, event) -> None:  # noqa: ANN401
        now = time.time()
        if now - self._last_rescan < self._debounce_seconds:
            return
        self._last_rescan = now
        # debounce: wait a moment for bulk file operations to finish
        time.sleep(0.3)
        self.manager.rescan()


def start_watching(manager: ImageManager) -> Observer:
    """Start a watchdog observer and return it for later stopping."""
    observer = Observer()
    handler = _RescanHandler(manager)
    observer.schedule(handler, str(settings.images_dir), recursive=True)
    observer.start()
    return observer
