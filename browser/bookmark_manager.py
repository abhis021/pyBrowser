import json
import logging
from pathlib import Path
from typing import List, Dict

logger = logging.getLogger(__name__)

class BookmarkManager:
    """Manages bookmarks with JSON persistence."""
    
    def __init__(self) -> None:
        self.bookmark_file = Path.home() / ".config" / "my_chromium_browser" / "bookmarks.json"
        self.bookmarks: List[Dict[str, str]] = []
        self._load()

    def _load(self) -> None:
        if self.bookmark_file.exists():
            try:
                with open(self.bookmark_file, 'r', encoding='utf-8') as f:
                    self.bookmarks = json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                logger.error(f"Failed to load bookmarks: {e}")
                self.bookmarks = []

    def _save(self) -> None:
        self.bookmark_file.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(self.bookmark_file, 'w', encoding='utf-8') as f:
                json.dump(self.bookmarks, f)
        except IOError as e:
            logger.error(f"Failed to save bookmarks: {e}")

    def add_bookmark(self, title: str, url: str) -> None:
        if not any(b['url'] == url for b in self.bookmarks):
            self.bookmarks.append({"title": title, "url": url})
            self._save()
            logger.info(f"Bookmarked: {url}")

    def remove_bookmark(self, url: str) -> None:
        self.bookmarks = [b for b in self.bookmarks if b['url'] != url]
        self._save()

    def get_all(self) -> List[Dict[str, str]]:
        return self.bookmarks