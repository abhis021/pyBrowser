"""Tests for history_manager.py"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import pytest
from browser.history_manager import HistoryManager


class TestHistoryManagerBasics:
    """Test basic HistoryManager operations."""

    def test_add_history_entry(self, history_manager: HistoryManager) -> None:
        """Test adding a single history entry."""
        history_manager.add("https://example.com", "Example Domain")
        recent = history_manager.get_recent_urls(limit=1)
        assert len(recent) == 1
        assert recent[0] == "https://example.com"

    def test_get_recent_urls_limited(self, history_manager: HistoryManager) -> None:
        """Test limiting the number of recent URLs returned."""
        urls = [f"https://example{i}.com" for i in range(10)]
        for url in urls:
            history_manager.add(url, f"Page {url}")

        recent = history_manager.get_recent_urls(limit=5)
        assert len(recent) == 5
        # Most recent should be first
        assert recent[0] == urls[-1]

    def test_add_empty_url_ignored(self, history_manager: HistoryManager) -> None:
        """Test that empty URLs are not added."""
        history_manager.add("", "Empty")
        recent = history_manager.get_recent_urls()
        assert len(recent) == 0

    def test_add_devtools_url_ignored(self, history_manager: HistoryManager) -> None:
        """Test that devtools:// URLs are ignored."""
        history_manager.add("devtools://inspect", "DevTools")
        recent = history_manager.get_recent_urls()
        assert len(recent) == 0

    def test_add_file_url(self, history_manager: HistoryManager) -> None:
        """Test adding file:// URLs."""
        history_manager.add("file:///home/user/document.html", "Local File")
        recent = history_manager.get_recent_urls()
        assert len(recent) == 1
        assert recent[0] == "file:///home/user/document.html"


class TestHistoryManagerPersistence:
    """Test HistoryManager JSON persistence."""

    def test_history_persists_to_disk(self, history_manager: HistoryManager) -> None:
        """Test that history is written to disk."""
        history_manager.add("https://example.com", "Example")
        assert history_manager.history_file.exists()

        # Read the file directly
        with open(history_manager.history_file, "r") as f:
            data = json.load(f)
        assert len(data) == 1
        assert data[0]["url"] == "https://example.com"

    def test_history_loads_from_disk(self, history_manager: HistoryManager) -> None:
        """Test that history is loaded from disk on init."""
        history_manager.add("https://example1.com", "Example 1")
        history_manager.add("https://example2.com", "Example 2")

        # Create a new instance and verify it loads the history
        history_manager2 = HistoryManager()
        recent = history_manager2.get_recent_urls(limit=2)
        assert len(recent) == 2
        assert recent[0] == "https://example2.com"

    def test_history_entries_include_timestamp(self, history_manager: HistoryManager) -> None:
        """Test that history entries include ISO-formatted timestamps."""
        history_manager.add("https://example.com", "Example")
        assert len(history_manager.history) == 1

        entry = history_manager.history[0]
        assert "timestamp" in entry
        # Should be a valid ISO format string
        try:
            datetime.fromisoformat(entry["timestamp"])
        except ValueError:
            pytest.fail("Timestamp is not in ISO format")

    def test_history_max_entries_enforced(self, history_manager: HistoryManager) -> None:
        """Test that MAX_ENTRIES limit is enforced."""
        for i in range(HistoryManager.MAX_ENTRIES + 50):
            history_manager.add(f"https://example{i}.com", f"Page {i}")

        assert len(history_manager.history) == HistoryManager.MAX_ENTRIES


class TestHistoryManagerValidation:
    """Test URL validation in HistoryManager."""

    @pytest.mark.parametrize("url,should_be_valid", [
        ("https://example.com", True),
        ("http://example.com", True),
        ("file:///home/file.html", True),
        ("ftp://example.com", False),
        ("javascript:void(0)", False),
        ("data:text/html,<html></html>", False),
        ("", False),
        ("not a url", False),
    ])
    def test_url_validation(self, history_manager: HistoryManager, url: str, should_be_valid: bool) -> None:
        """Test URL validation rules."""
        history_manager.add(url, "Test")
        recent = history_manager.get_recent_urls()
        
        if should_be_valid:
            assert url in recent, f"Valid URL {url} was rejected"
        else:
            assert url not in recent, f"Invalid URL {url} was accepted"


class TestHistoryManagerDiskFailures:
    """Test resilience to disk I/O errors."""

    def test_corrupted_json_file_gracefully_handled(self, history_manager: HistoryManager) -> None:
        """Test that corrupted JSON files don't crash on load."""
        history_manager.add("https://example.com", "Example")
        
        # Corrupt the file
        with open(history_manager.history_file, "w") as f:
            f.write("{ invalid json }")
        
        # Create a new instance; should handle gracefully
        history_manager2 = HistoryManager()
        assert history_manager2.history == []

    def test_non_list_json_gracefully_handled(self, history_manager: HistoryManager) -> None:
        """Test that non-list JSON data is handled gracefully."""
        history_manager.add("https://example.com", "Example")
        
        # Replace with a non-list structure
        with open(history_manager.history_file, "w") as f:
            json.dump({"not": "a list"}, f)
        
        # Create a new instance; should reset to empty
        history_manager2 = HistoryManager()
        assert history_manager2.history == []
