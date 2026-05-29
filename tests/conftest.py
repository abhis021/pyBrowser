"""Pytest configuration and shared fixtures for pyBrowser tests."""
from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Generator

import pytest
from PySide6.QtWidgets import QApplication, QWidget
from PySide6.QtCore import Qt, QUrl
from unittest.mock import MagicMock, patch


class MockQWebEngineView(QWidget):
    """Mock QWebEngineView that inherits from QWidget for layout compatibility."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.url = MagicMock(return_value=QUrl("about:blank"))
        self.title = MagicMock(return_value="Untitled")
        self.zoomFactor = MagicMock(return_value=1.0)
        self.setZoomFactor = MagicMock()
        self.page = MagicMock(return_value=MagicMock())
        self.settings = MagicMock(return_value=MagicMock())
        self.setUrl = MagicMock()
        self.reload = MagicMock()
        self.back = MagicMock()
        self.forward = MagicMock()
        self.stop = MagicMock()
        self.loadProgress = MagicMock()
        self.loadFinished = MagicMock()
        self.urlChanged = MagicMock()
        self.titleChanged = MagicMock()


@pytest.fixture(scope="session")
def qapp() -> QApplication:
    """Create a QApplication instance for the test session."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


@pytest.fixture
def tmp_config_dir() -> Generator[Path, None, None]:
    """Provide a temporary config directory for each test."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def monkeypatch_storage(monkeypatch, tmp_config_dir) -> None:
    """Monkeypatch get_config_dir to use a temporary directory."""
    from browser import storage
    # Ensure temp dir exists before patching
    tmp_config_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(storage, "get_config_dir", lambda app_name="pyBrowser": tmp_config_dir)


@pytest.fixture
def history_manager(monkeypatch_storage, tmp_config_dir):
    """Provide a HistoryManager with isolated storage."""
    from browser.history_manager import HistoryManager
    # Clean up any existing history file to ensure isolation
    history_file = tmp_config_dir / "history.json"
    if history_file.exists():
        history_file.unlink()
    manager = HistoryManager()
    yield manager
    # Cleanup after test
    if history_file.exists():
        history_file.unlink()


@pytest.fixture
def bookmark_manager(monkeypatch_storage, tmp_config_dir):
    """Provide a BookmarkManager with isolated storage."""
    from browser.bookmark_manager import BookmarkManager
    # Clean up any existing bookmarks file to ensure isolation
    bookmarks_file = tmp_config_dir / "bookmarks.json"
    if bookmarks_file.exists():
        bookmarks_file.unlink()
    manager = BookmarkManager()
    yield manager
    # Cleanup after test
    if bookmarks_file.exists():
        bookmarks_file.unlink()


@pytest.fixture
def browser_window_mock(qapp, monkeypatch_storage):
    """Provide a BrowserWindow instance with mocked QWebEngineView.
    
    We mock the QWebEngineView to avoid initializing the actual Chromium
    renderer process, which is both slow and unnecessary for unit tests.
    """
    from unittest.mock import MagicMock, patch
    from PySide6.QtCore import QUrl
    from browser.browser_window import BrowserWindow

    # Patch QWebEngineView at the module level where it's imported
    with patch("browser.tab_widget.QWebEngineView") as MockWebEngineView:
        mock_view = MagicMock()
        mock_view.url.return_value = QUrl("about:blank")
        mock_view.title.return_value = "Test Page"
        mock_view.zoomFactor.return_value = 1.0
        MockWebEngineView.return_value = mock_view

        window = BrowserWindow()
        yield window
        window.close()


@pytest.fixture
def mock_qwebengineview():
    """Provide a mock QWebEngineView for direct testing."""
    from PySide6.QtCore import QUrl
    from unittest.mock import MagicMock

    mock = MagicMock()
    mock.url.return_value = QUrl("https://example.com")
    mock.title.return_value = "Example Domain"
    mock.zoomFactor.return_value = 1.0
    mock.page.return_value = MagicMock()
    return mock
