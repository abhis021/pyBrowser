from PySide6.QtWidgets import QDialog, QVBoxLayout, QLineEdit, QCheckBox, QPushButton, QLabel, QHBoxLayout
from PySide6.QtCore import QSettings

class SettingsDialog(QDialog):
    """Simple settings dialog utilizing QSettings for native OS registry/plist integration."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Browser Settings")
        self.settings = QSettings("MyBrowserProject", "ChromiumPy")
        
        layout = QVBoxLayout(self)
        
        # Homepage Setting
        hp_layout = QHBoxLayout()
        hp_layout.addWidget(QLabel("Homepage:"))
        self.homepage_input = QLineEdit()
        self.homepage_input.setText(self.settings.value("homepage", "https://duckduckgo.com"))
        hp_layout.addWidget(self.homepage_input)
        layout.addLayout(hp_layout)
        
        # JS Toggle
        self.js_checkbox = QCheckBox("Enable JavaScript (applies to new tabs)")
        # Qt settings stores booleans as strings sometimes depending on OS, parse safely
        js_enabled = str(self.settings.value("enable_javascript", True)).lower() == 'true'
        self.js_checkbox.setChecked(js_enabled)
        layout.addWidget(self.js_checkbox)
        
        # Buttons
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.save_and_close)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

    def save_and_close(self) -> None:
        self.settings.setValue("homepage", self.homepage_input.text())
        self.settings.setValue("enable_javascript", self.js_checkbox.isChecked())
        self.accept()