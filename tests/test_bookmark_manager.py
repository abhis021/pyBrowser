"""Tests for bookmark_manager.py"""
from __future__ import annotations

import json

import pytest
from browser.bookmark_manager import BookmarkManager


class TestBookmarkManagerBasics:
    """Test basic BookmarkManager operations."""

    def test_add_bookmark(self, bookmark_manager: BookmarkManager) -> None:
        """Test adding a single bookmark."""
        bookmark_manager.add_bookmark("Google", "https://google.com")
        bookmarks = bookmark_manager.get_all()
        assert len(bookmarks) == 1
        assert bookmarks[0]["url"] == "https://google.com"
        assert bookmarks[0]["title"] == "Google"

    def test_add_duplicate_bookmark_ignored(self, bookmark_manager: BookmarkManager) -> None:
        """Test that duplicate URLs are not added."""
        bookmark_manager.add_bookmark("Google", "https://google.com")
        bookmark_manager.add_bookmark("Google Again", "https://google.com")
        bookmarks = bookmark_manager.get_all()
        assert len(bookmarks) == 1

    def test_remove_bookmark(self, bookmark_manager: BookmarkManager) -> None:
        """Test removing a bookmark."""
        bookmark_manager.add_bookmark("Example", "https://example.com")
        bookmarks = bookmark_manager.get_all()
        assert len(bookmarks) == 1

        bookmark_manager.remove_bookmark("https://example.com")
        bookmarks = bookmark_manager.get_all()
        assert len(bookmarks) == 0

    def test_remove_nonexistent_bookmark(self, bookmark_manager: BookmarkManager) -> None:
        """Test removing a bookmark that doesn't exist."""
        bookmark_manager.add_bookmark("Example", "https://example.com")
        bookmark_manager.remove_bookmark("https://nonexistent.com")
        bookmarks = bookmark_manager.get_all()
        assert len(bookmarks) == 1

    def test_get_all_returns_copy(self, bookmark_manager: BookmarkManager) -> None:
        """Test that get_all returns a copy, not a reference."""
        bookmark_manager.add_bookmark("Example", "https://example.com")
        bookmarks1 = bookmark_manager.get_all()
        bookmarks2 = bookmark_manager.get_all()
        assert bookmarks1 == bookmarks2
        assert bookmarks1 is not bookmarks2


class TestBookmarkManagerPersistence:
    """Test BookmarkManager JSON persistence."""

    def test_bookmarks_persist_to_disk(self, bookmark_manager: BookmarkManager) -> None:
        """Test that bookmarks are written to disk."""
        bookmark_manager.add_bookmark("Example", "https://example.com")
        assert bookmark_manager.bookmark_file.exists()

        with open(bookmark_manager.bookmark_file, "r") as f:
            data = json.load(f)
        assert len(data) == 1
        assert data[0]["url"] == "https://example.com"

    def test_bookmarks_load_from_disk(self, bookmark_manager: BookmarkManager) -> None:
        """Test that bookmarks are loaded from disk on init."""
        bookmark_manager.add_bookmark("Example1", "https://example1.com")
        bookmark_manager.add_bookmark("Example2", "https://example2.com")

        bookmark_manager2 = BookmarkManager()
        bookmarks = bookmark_manager2.get_all()
        assert len(bookmarks) == 2
        assert any(b["url"] == "https://example1.com" for b in bookmarks)

    def test_empty_bookmarks_on_load(self, bookmark_manager: BookmarkManager) -> None:
        """Test loading when no bookmarks file exists."""
        bookmark_manager2 = BookmarkManager()
        bookmarks = bookmark_manager2.get_all()
        assert len(bookmarks) == 0


class TestBookmarkManagerValidation:
    """Test URL validation in BookmarkManager."""

    def test_add_invalid_url(self, bookmark_manager: BookmarkManager) -> None:
        """Test that invalid URLs are rejected."""
        bookmark_manager.add_bookmark("Bad", "not a url")
        bookmarks = bookmark_manager.get_all()
        assert len(bookmarks) == 0

    def test_add_javascript_url_rejected(self, bookmark_manager: BookmarkManager) -> None:
        """Test that javascript: URLs are rejected."""
        bookmark_manager.add_bookmark("JS", "javascript:void(0)")
        bookmarks = bookmark_manager.get_all()
        assert len(bookmarks) == 0

    def test_add_empty_url_rejected(self, bookmark_manager: BookmarkManager) -> None:
        """Test that empty URLs are rejected."""
        bookmark_manager.add_bookmark("Empty", "")
        bookmarks = bookmark_manager.get_all()
        assert len(bookmarks) == 0

    def test_add_file_url(self, bookmark_manager: BookmarkManager) -> None:
        """Test adding file:// URLs."""
        bookmark_manager.add_bookmark("Local", "file:///home/user/document.html")
        bookmarks = bookmark_manager.get_all()
        assert len(bookmarks) == 1
        assert bookmarks[0]["url"] == "file:///home/user/document.html"

    def test_add_http_url(self, bookmark_manager: BookmarkManager) -> None:
        """Test adding http:// URLs."""
        bookmark_manager.add_bookmark("HTTP", "http://example.com")
        bookmarks = bookmark_manager.get_all()
        assert len(bookmarks) == 1

    def test_add_https_url(self, bookmark_manager: BookmarkManager) -> None:
        """Test adding https:// URLs."""
        bookmark_manager.add_bookmark("HTTPS", "https://example.com")
        bookmarks = bookmark_manager.get_all()
        assert len(bookmarks) == 1

    def test_add_url_with_whitespace_stripped(self, bookmark_manager: BookmarkManager) -> None:
        """Test that URLs have whitespace stripped."""
        bookmark_manager.add_bookmark("Whitespace", "  https://example.com  ")
        bookmarks = bookmark_manager.get_all()
        assert len(bookmarks) == 1
        assert bookmarks[0]["url"] == "https://example.com"


class TestBookmarkManagerTitleHandling:
    """Test bookmark title handling."""

    def test_empty_title_uses_url(self, bookmark_manager: BookmarkManager) -> None:
        """Test that empty title falls back to URL."""
        bookmark_manager.add_bookmark("", "https://example.com")
        bookmarks = bookmark_manager.get_all()
        assert len(bookmarks) == 1
        assert bookmarks[0]["title"] == "https://example.com"


class TestBookmarkManagerDiskFailures:
    """Test resilience to disk I/O errors."""

    def test_corrupted_json_file_gracefully_handled(self, bookmark_manager: BookmarkManager) -> None:
        """Test that corrupted JSON files don't crash on load."""
        bookmark_manager.add_bookmark("Valid", "https://example.com")
        
        # Corrupt the file
        with open(bookmark_manager.bookmark_file, "w") as f:
            f.write("{ invalid json }")
        
        # Create a new instance; should handle gracefully
        bookmark_manager2 = BookmarkManager()
        assert bookmark_manager2.bookmarks == []

    def test_non_list_json_gracefully_handled(self, bookmark_manager: BookmarkManager) -> None:
        """Test that non-list JSON data is handled gracefully."""
        bookmark_manager.add_bookmark("Valid", "https://example.com")
        
        # Replace with a non-list structure
        with open(bookmark_manager.bookmark_file, "w") as f:
            json.dump({"not": "a list"}, f)
        
        # Create a new instance; should reset to empty
        bookmark_manager2 = BookmarkManager()
        assert bookmark_manager2.bookmarks == []
