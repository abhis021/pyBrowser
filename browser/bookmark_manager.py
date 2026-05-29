import json
import logging
from pathlib import Path
from typing import List, Dict
from urllib.parse import urlparse

from .storage import get_config_dir, atomic_write_text

logger = logging.getLogger(__name__)


class BookmarkManager:
    """Manages bookmarks with JSON persistence.

    Persistence is written atomically to avoid corruption. Files are stored
    in a platform-appropriate config directory.
    """

    def __init__(self) -> None:
        cfg = get_config_dir("my_chromium_browser")
        self.bookmark_file: Path = cfg / "bookmarks.json"
        self.bookmarks: List[Dict[str, str]] = []
        self._load()

    def _load(self) -> None:
        if self.bookmark_file.exists():
            try:
                with open(self.bookmark_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        self.bookmarks = data
                    else:
                        logger.warning("Bookmarks data not a list, resetting")
                        self.bookmarks = []
            except (json.JSONDecodeError, IOError) as e:
                logger.error("Failed to load bookmarks: %s", e)
                self.bookmarks = []

    def _save(self) -> None:
        try:
            atomic_write_text(self.bookmark_file, json.dumps(self.bookmarks, ensure_ascii=False, indent=2))
        except Exception as e:
            logger.error("Failed to save bookmarks: %s", e)

    @staticmethod
    def _is_valid_url(url: str) -> bool:
        try:
            parsed = urlparse(url)
            return parsed.scheme in ("http", "https", "file") and bool(parsed.netloc or parsed.path)
        except Exception:
            return False

    def add_bookmark(self, title: str, url: str) -> None:
        """Add a bookmark if the URL is valid and not already present."""
        url = url.strip()
        if not self._is_valid_url(url):
            logger.warning("Attempted to bookmark invalid URL: %s", url)
            return

        if not any(b.get("url") == url for b in self.bookmarks):
            self.bookmarks.append({"title": title or url, "url": url})
            self._save()
            logger.info("Bookmarked: %s", url)

    def remove_bookmark(self, url: str) -> None:
        self.bookmarks = [b for b in self.bookmarks if b.get("url") != url]
        self._save()

    def get_all(self) -> List[Dict[str, str]]:
        return list(self.bookmarks)