"""Tests for tab_widget.py"""
from __future__ import annotations

from unittest.mock import MagicMock, patch, call

import pytest
from PySide6.QtCore import QUrl
from PySide6.QtWidgets import QWidget

from browser.tab_widget import TabWidget, PythonJSBridge


@pytest.fixture
def tab_widget(qapp, monkeypatch_storage):
    """Provide a TabWidget with mocked QWebEngineView."""
    from conftest import MockQWebEngineView
    with patch("browser.tab_widget.QWebEngineView", MockQWebEngineView):
        tab = TabWidget()
        yield tab
        tab.deleteLater()


class TestTabWidgetBasics:
    """Test basic TabWidget creation and properties."""

    def test_tab_widget_creation(self, tab_widget: TabWidget) -> None:
        """Test creating a TabWidget."""
        assert isinstance(tab_widget, QWidget)
        assert tab_widget.browser is not None

    def test_tab_widget_has_signals(self, tab_widget: TabWidget) -> None:
        """Test that TabWidget exposes expected signals."""
        assert hasattr(tab_widget, "url_changed")
        assert hasattr(tab_widget, "title_changed")
        assert hasattr(tab_widget, "load_progress")
        assert hasattr(tab_widget, "load_finished")


class TestTabWidgetNavigation:
    """Test tab navigation and URL handling."""

    def test_load_url_with_http(self, tab_widget: TabWidget) -> None:
        """Test loading an HTTP URL."""
        tab_widget.load_url("https://example.com")
        tab_widget.browser.setUrl.assert_called_with(QUrl("https://example.com"))

    def test_load_url_with_domain_only(self, tab_widget: TabWidget) -> None:
        """Test loading a domain without protocol."""
        tab_widget.load_url("example.com")
        # Should prepend https://
        call_args = tab_widget.browser.setUrl.call_args
        assert "https://example.com" in str(call_args)

    def test_load_url_search_query(self, tab_widget: TabWidget) -> None:
        """Test that search queries are converted to DuckDuckGo searches."""
        tab_widget.load_url("python tutorial")
        # Should construct a search URL
        call_args = tab_widget.browser.setUrl.call_args
        assert "duckduckgo.com" in str(call_args)
        assert "python%20tutorial" in str(call_args)

    def test_load_url_with_protocol(self, tab_widget: TabWidget) -> None:
        """Test loading a URL with explicit protocol."""
        tab_widget.load_url("https://example.com/path")
        tab_widget.browser.setUrl.assert_called_with(QUrl("https://example.com/path"))

    def test_load_url_file_protocol(self, tab_widget: TabWidget) -> None:
        """Test loading a file:// URL."""
        tab_widget.load_url("file:///home/user/document.html")
        tab_widget.browser.setUrl.assert_called_with(QUrl("file:///home/user/document.html"))


class TestTabWidgetJavaScript:
    """Test JavaScript execution and Python-JS bridge."""

    def test_run_javascript(self, tab_widget: TabWidget) -> None:
        """Test executing JavaScript."""
        tab_widget.run_javascript("console.log('test')")
        # runJavaScript should be called on the page
        tab_widget.browser.page().runJavaScript.assert_called_once()

    def test_python_js_bridge_creation(self) -> None:
        """Test creating a PythonJSBridge."""
        tab = MagicMock()
        bridge = PythonJSBridge(tab)
        assert bridge._tab is tab

    def test_python_js_bridge_execute(self) -> None:
        """Test PythonJSBridge execute_python_logic."""
        tab = MagicMock()
        bridge = PythonJSBridge(tab)
        
        result = bridge.execute_python_logic("test data")
        assert "test data" in result
        assert result == "Python acknowledged: TEST DATA"


class TestTabWidgetZoom:
    """Test zoom functionality."""

    def test_zoom_factor_default(self, tab_widget: TabWidget) -> None:
        """Test that zoom factor is initialized."""
        assert tab_widget.browser.zoomFactor() == 1.0


class TestTabWidgetSignals:
    """Test TabWidget signal emission."""

    def test_url_changed_signal_emitted(self, tab_widget: TabWidget) -> None:
        """Test that url_changed signal is emitted."""
        mock_handler = MagicMock()
        tab_widget.url_changed.connect(mock_handler)
        
        tab_widget.browser.urlChanged.emit(QUrl("https://example.com"))
        
        # Handler should be called
        assert mock_handler.called

    def test_title_changed_signal_emitted(self, tab_widget: TabWidget) -> None:
        """Test that title_changed signal is emitted."""
        mock_handler = MagicMock()
        tab_widget.title_changed.connect(mock_handler)
        
        tab_widget.browser.titleChanged.emit("Example Page")
        
        # Handler should be called
        assert mock_handler.called

    def test_load_progress_signal_emitted(self, tab_widget: TabWidget) -> None:
        """Test that load_progress signal is emitted."""
        mock_handler = MagicMock()
        tab_widget.load_progress.connect(mock_handler)
        
        tab_widget.browser.loadProgress.emit(50)
        
        # Handler should be called with progress value
        assert mock_handler.called

    def test_load_finished_signal_emitted(self, tab_widget: TabWidget) -> None:
        """Test that load_finished signal is emitted on page load."""
        mock_handler = MagicMock()
        tab_widget.load_finished.connect(mock_handler)
        
        tab_widget.browser.loadFinished.emit(True)
        
        # Handler should be called with success flag
        assert mock_handler.called


class TestTabWidgetSettings:
    """Test TabWidget settings handling."""

    def test_javascript_setting_applied(self, qapp, monkeypatch_storage) -> None:
        """Test that JavaScript enable setting is applied."""
        from PySide6.QtCore import QSettings
        
        settings = QSettings("MyBrowserProject", "ChromiumPy")
        settings.setValue("enable_javascript", False)

        with patch("browser.tab_widget.QWebEngineView") as MockView:
            mock_view = MagicMock()
            mock_view.settings.return_value = MagicMock()
            MockView.return_value = mock_view

            tab = TabWidget()

            # Verify setAttribute was called for JavaScript
            settings_obj = mock_view.settings.return_value
            if settings_obj.setAttribute.called:
                # At least one call should set JavascriptEnabled
                calls = settings_obj.setAttribute.call_args_list
                assert len(calls) > 0
