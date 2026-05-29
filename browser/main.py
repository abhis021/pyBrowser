import sys
import logging
from pathlib import Path
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

# Allow running this file directly from the repository without a package import error
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from browser.browser_window import BrowserWindow

# Configure standard logging format for engineering observability
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s"
)

def main() -> None:
    # Essential for high-DPI scaling on modern monitors
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    
    app = QApplication(sys.argv)
    app.setApplicationName("ChromiumPy Browser")
    app.setOrganizationName("MyBrowserProject")
    app.setOrganizationDomain("local")
    
    window = BrowserWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == '__main__':
    main()