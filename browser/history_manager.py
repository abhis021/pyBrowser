import json
import logging
from pathlib import Path
from typing import List, Dict
from datetime import datetime
from urllib.parse import urlparse

from .storage import get_config_dir, atomic_write_text

logger = logging.getLogger(__name__)


class HistoryManager:
    """Manages browsing history with file persistence and basic validation.

    Keeps the most recent N entries and writes atomically to disk.
    """

    MAX_ENTRIES = 1000

    def __init__(self) -> None:
        cfg = get_config_dir("my_chromium_browser")
        self.history_file: Path = cfg / "history.json"
        self.history: List[Dict[str, str]] = []
        self._load()

    def _load(self) -> None:
        if self.history_file.exists():
            try:
                with open(self.history_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        self.history = data
                    else:
                        logger.warning("History data not a list, resetting")
                        self.history = []
            except (json.JSONDecodeError, IOError) as e:
                logger.error("Failed to load history: %s", e)
                self.history = []

    def _save(self) -> None:
        try:
            atomic_write_text(self.history_file, json.dumps(self.history, ensure_ascii=False))
        except Exception as e:
            logger.error("Failed to save history: %s", e)

    @staticmethod
    def _is_valid_navigable_url(url: str) -> bool:
        if not url:
            return False
        try:
            parsed = urlparse(url)
            if parsed.scheme in ("http", "https", "file"):
                return bool(parsed.netloc or parsed.path)
            return False
        except Exception:
            return False

    def add(self, url: str, title: str) -> None:
        """Add a history entry if the URL is navigable and not an internal scheme."""
        if not url or url.startswith("devtools://"):
            return

        if not self._is_valid_navigable_url(url):
            logger.debug("Skipping non-navigable URL for history: %s", url)
            return

        entry = {"url": url, "title": title, "timestamp": datetime.now().isoformat()}
        self.history.insert(0, entry)

        # Trim to cap
        if len(self.history) > self.MAX_ENTRIES:
            self.history = self.history[: self.MAX_ENTRIES]

        self._save()

    def get_recent_urls(self, limit: int = 50) -> List[str]:
        return [entry["url"] for entry in self.history[:limit]]