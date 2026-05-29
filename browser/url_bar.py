from PySide6.QtWidgets import QLineEdit, QCompleter
from PySide6.QtCore import QStringListModel, Qt
from typing import List

class UrlBar(QLineEdit):
    """Custom address bar with history-based autocompletion."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setPlaceholderText("Enter URL or search...")
        self.setClearButtonEnabled(True)
        
        # Setup Completer
        self.completer_model = QStringListModel()
        self.custom_completer = QCompleter(self.completer_model, self)
        self.custom_completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        self.custom_completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.setCompleter(self.custom_completer)

    def update_history_completions(self, urls: List[str]) -> None:
        """Updates the dropdown suggestions based on recent history."""
        # Deduplicate while preserving order
        seen = set()
        deduped = [x for x in urls if not (x in seen or seen.add(x))]
        self.completer_model.setStringList(deduped)

    def set_url(self, url: str) -> None:
        """Updates the text only if it's not currently focused, preventing UX jarring."""
        if not self.hasFocus():
            self.setText(url)
            self.setCursorPosition(0)