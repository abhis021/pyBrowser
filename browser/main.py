import sys
import logging
from PySide6.QtWidgets import QApplication
from .browser_window import BrowserWindow

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