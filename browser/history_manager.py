import json
import logging
from pathlib import Path
from typing import List, Dict
from datetime import datetime

logger = logging.getLogger(__name__)

class HistoryManager:
    """Manages browsing history with basic file persistence."""
    
    def __init__(self) -> None:
        self.history_file = Path.home() / ".config" / "my_chromium_browser" / "history.json"
        self.history: List[Dict[str, str]] = []
        self._load()

    def _load(self) -> None:
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    self.history = json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                logger.error(f"Failed to load history: {e}")
                self.history = []

    def _save(self) -> None:
        self.history_file.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.history, f)
        except IOError as e:
            logger.error(f"Failed to save history: {e}")

    def add(self, url: str, title: str) -> None:
        if url.startswith("devtools://") or not url:
            return
            
        entry = {"url": url, "title": title, "timestamp": datetime.now().isoformat()}
        self.history.insert(0, entry)
        
        # Keep only the last 1000 items to prevent memory/disk bloat
        if len(self.history) > 1000:
            self.history = self.history[:1000]
            
        self._save()

    def get_recent_urls(self, limit: int = 50) -> List[str]:
        return [entry["url"] for entry in self.history[:limit]]