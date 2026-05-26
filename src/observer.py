from __future__ import annotations

import logging
import time
from threading import Thread

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from src.config import settings
from src.image_manager import ImageManager

logger = logging.getLogger(__name__)


class _RescanHandler(FileSystemEventHandler):
    def __init__(self, manager: ImageManager) -> None:
        self.manager = manager
        self._last_rescan = 0.0
        self._debounce_seconds = 1.0
        # Ignore metadata files (they change due to internal operations)
        self._ignore_patterns = [".placepix_manifest.json", ".placepix_colors.json", ".placepix_metrics.db"]

    def _should_ignore(self, path: str) -> bool:
        """Check if file should be ignored (metadata files)."""
        return any(pattern in path for pattern in self._ignore_patterns)

    def on_created(self, event) -> None:  # noqa: ANN401
        """Trigger rescan on file/directory creation."""
        if not event.is_directory and not self._should_ignore(event.src_path):
            self._trigger_rescan(f"File created: {event.src_path}")

    def on_deleted(self, event) -> None:  # noqa: ANN401
        """Trigger rescan on file/directory deletion."""
        if not event.is_directory and not self._should_ignore(event.src_path):
            self._trigger_rescan(f"File deleted: {event.src_path}")

    def on_modified(self, event) -> None:  # noqa: ANN401
        """Trigger rescan on file modification."""
        if not event.is_directory and not self._should_ignore(event.src_path):
            self._trigger_rescan(f"File modified: {event.src_path}")

    def on_moved(self, event) -> None:  # noqa: ANN401
        """Trigger rescan on file/directory move/rename."""
        if not self._should_ignore(event.src_path) and not self._should_ignore(event.dest_path):
            self._trigger_rescan(f"File moved: {event.src_path} -> {event.dest_path}")

    def _trigger_rescan(self, reason: str) -> None:
        """Debounced rescan trigger."""
        now = time.time()
        if now - self._last_rescan < self._debounce_seconds:
            return
        self._last_rescan = now
        logger.info(f"File system change: {reason} - triggering rescan")
        # debounce: wait a moment for bulk file operations to finish
        time.sleep(0.3)
        self.manager.rescan()


def start_watching(manager: ImageManager) -> Observer:
    """Start a watchdog observer and return it for later stopping."""
    observer = Observer()
    handler = _RescanHandler(manager)
    
    # Check if the directory exists before scheduling
    if not settings.images_dir.exists():
        logger.warning(f"Images directory does not exist: {settings.images_dir}, file watcher disabled")
        return observer
    
    try:
        observer.schedule(handler, str(settings.images_dir), recursive=True)
        observer.start()
        logger.info(f"File watcher active for: {settings.images_dir}")
    except Exception as e:
        logger.error(f"Failed to start file watcher for {settings.images_dir}: {e}")
    
    return observer
