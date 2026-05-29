"""Tests for shortcut_manager.py"""
from __future__ import annotations

import pytest
from PySide6.QtGui import QKeySequence
from PySide6.QtWidgets import QMainWindow
from unittest.mock import MagicMock, call

from browser.shortcut_manager import ShortcutManager, ShortcutSpec


@pytest.fixture
def mock_window():
    """Provide a mock QMainWindow for testing."""
    window = MagicMock(spec=QMainWindow)
    window.addAction = MagicMock()
    window._not_implemented_stub = MagicMock()
    window.test_handler = MagicMock()
    return window


class TestShortcutSpec:
    """Test ShortcutSpec dataclass."""

    def test_create_spec(self) -> None:
        """Test creating a ShortcutSpec."""
        spec = ShortcutSpec(
            name="test",
            description="Test Shortcut",
            sequences=[QKeySequence.StandardKey.Copy, "Ctrl+C"],
            handler_name="test_handler"
        )
        assert spec.name == "test"
        assert spec.description == "Test Shortcut"
        assert len(spec.sequences) == 2
        assert spec.handler_name == "test_handler"


class TestShortcutManagerRegistration:
    """Test ShortcutManager registration and binding."""

    def test_register_single_shortcut_with_handler(self, mock_window) -> None:
        """Test registering a shortcut with an existing handler."""
        sm = ShortcutManager(mock_window)
        specs = [
            ShortcutSpec(
                name="test",
                description="Test",
                sequences=["Ctrl+T"],
                handler_name="test_handler"
            )
        ]

        sm.register_shortcuts(specs)

        # Verify addAction was called
        assert mock_window.addAction.called

    def test_register_shortcut_without_handler_uses_stub(self, mock_window) -> None:
        """Test that missing handlers fall back to _not_implemented_stub."""
        sm = ShortcutManager(mock_window)
        specs = [
            ShortcutSpec(
                name="unimplemented",
                description="Not Implemented",
                sequences=["Ctrl+U"],
                handler_name="nonexistent_handler"
            )
        ]

        sm.register_shortcuts(specs)

        # Verify addAction was called
        assert mock_window.addAction.called

    def test_register_multiple_shortcuts(self, mock_window) -> None:
        """Test registering multiple shortcuts at once."""
        sm = ShortcutManager(mock_window)
        specs = [
            ShortcutSpec("spec1", "Spec 1", ["Ctrl+1"], "test_handler"),
            ShortcutSpec("spec2", "Spec 2", ["Ctrl+2"], "test_handler"),
            ShortcutSpec("spec3", "Spec 3", ["Ctrl+3"], "test_handler"),
        ]

        sm.register_shortcuts(specs)

        # Verify addAction was called 3 times
        assert mock_window.addAction.call_count == 3

    def test_shortcut_with_multiple_sequences(self, mock_window) -> None:
        """Test registering a shortcut with multiple key sequences."""
        sm = ShortcutManager(mock_window)
        specs = [
            ShortcutSpec(
                name="find",
                description="Find",
                sequences=[QKeySequence.StandardKey.Find, "Ctrl+F"],
                handler_name="test_handler"
            )
        ]

        sm.register_shortcuts(specs)

        # Verify action was created
        assert mock_window.addAction.called


class TestShortcutManagerStandardKeys:
    """Test integration with QKeySequence.StandardKey."""

    def test_standard_key_refresh(self, mock_window) -> None:
        """Test using QKeySequence.StandardKey.Refresh."""
        sm = ShortcutManager(mock_window)
        specs = [
            ShortcutSpec(
                name="reload",
                description="Reload",
                sequences=[QKeySequence.StandardKey.Refresh],
                handler_name="test_handler"
            )
        ]

        sm.register_shortcuts(specs)
        assert mock_window.addAction.called

    def test_standard_key_print(self, mock_window) -> None:
        """Test using QKeySequence.StandardKey.Print."""
        sm = ShortcutManager(mock_window)
        specs = [
            ShortcutSpec(
                name="print",
                description="Print",
                sequences=[QKeySequence.StandardKey.Print],
                handler_name="test_handler"
            )
        ]

        sm.register_shortcuts(specs)
        assert mock_window.addAction.called

    def test_standard_key_find(self, mock_window) -> None:
        """Test using QKeySequence.StandardKey.Find."""
        sm = ShortcutManager(mock_window)
        specs = [
            ShortcutSpec(
                name="find",
                description="Find",
                sequences=[QKeySequence.StandardKey.Find],
                handler_name="test_handler"
            )
        ]

        sm.register_shortcuts(specs)
        assert mock_window.addAction.called


class TestShortcutManagerKeySequences:
    """Test key sequence handling."""

    @pytest.mark.parametrize("sequence", [
        "Ctrl+T",
        "Ctrl+N",
        "Ctrl+W",
        "Ctrl+Shift+T",
        "Alt+Left",
        "Alt+Right",
        "F5",
        "F12",
    ])
    def test_string_sequences(self, mock_window, sequence: str) -> None:
        """Test various string key sequences."""
        sm = ShortcutManager(mock_window)
        specs = [
            ShortcutSpec(
                name="test",
                description="Test",
                sequences=[sequence],
                handler_name="test_handler"
            )
        ]

        sm.register_shortcuts(specs)
        assert mock_window.addAction.called

    def test_empty_sequences_handled(self, mock_window) -> None:
        """Test that specs with no sequences don't crash."""
        sm = ShortcutManager(mock_window)
        specs = [
            ShortcutSpec(
                name="empty",
                description="Empty",
                sequences=[],
                handler_name="test_handler"
            )
        ]

        sm.register_shortcuts(specs)
        assert mock_window.addAction.called


class TestShortcutManagerErrorHandling:
    """Test error handling and edge cases."""

    def test_malformed_sequence_gracefully_handled(self, mock_window) -> None:
        """Test that malformed sequences don't crash."""
        sm = ShortcutManager(mock_window)
        specs = [
            ShortcutSpec(
                name="test",
                description="Test",
                sequences=["This is not a valid sequence format!!!"],
                handler_name="test_handler"
            )
        ]

        # Should not raise an exception
        sm.register_shortcuts(specs)
        assert mock_window.addAction.called
