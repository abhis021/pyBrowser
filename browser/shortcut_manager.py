"""ShortcutManager: declarative, scalable registration of app shortcuts.

Uses QKeySequence.StandardKey when available to respect platform-native
modifier mapping (Ctrl vs Cmd on macOS). Binds missing features to a
not-implemented stub on the owning window.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable, List, Optional

from PySide6.QtGui import QKeySequence, QAction


@dataclass(slots=True)
class ShortcutSpec:
    name: str
    description: str
    sequences: List[QKeySequence | str]
    handler_name: str  # attribute name on the owner window to call


class ShortcutManager:
    def __init__(self, owner_window) -> None:
        self.owner = owner_window

    def _make_key(self, key: QKeySequence.StandardKey | str) -> QKeySequence:
        # Delegate to QKeySequence which accepts either a StandardKey or a string
        return QKeySequence(key)

    def register_shortcuts(self, specs: Iterable[ShortcutSpec]) -> None:
        """Create QAction objects for each spec and attach them to the owner.

        If the owner's attribute named by `handler_name` exists and is
        callable, it will be connected; otherwise a generic stub is used.
        """
        for spec in specs:
            # Create the action and set a sensible text
            action = QAction(spec.description, self.owner)

            # Resolve QKeySequence objects
            keyseqs: List[QKeySequence] = []
            for s in spec.sequences:
                if isinstance(s, QKeySequence):
                    keyseqs.append(s)
                else:
                    # s can be a StandardKey enum or a string; allow both
                    try:
                        keyseqs.append(self._make_key(s))
                    except Exception:
                        keyseqs.append(QKeySequence(str(s)))

            # Set the first sequence as the primary shortcut, keep others as alternate
            if keyseqs:
                action.setShortcuts(keyseqs)

            # Bind handler if available
            handler = getattr(self.owner, spec.handler_name, None)
            if callable(handler):
                # Wrap so the QAction's `triggered(bool)` doesn't pass through
                action.triggered.connect(lambda checked=False, h=handler: h())
            else:
                # Wire to the not-implemented stub with the feature name
                action.triggered.connect(lambda checked=False, n=spec.name: self.owner._not_implemented_stub(n))

            # Ensure the action is in the window's context so global shortcuts work
            self.owner.addAction(action)
