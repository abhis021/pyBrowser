import logging
from PySide6.QtWidgets import QWidget, QVBoxLayout
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import QWebEnginePage, QWebEngineSettings
from PySide6.QtCore import QUrl, Signal, QObject, Slot, QSettings
from PySide6.QtWebChannel import QWebChannel

logger = logging.getLogger(__name__)

class PythonJSBridge(QObject):
    """
    Exposed to the JavaScript context via QWebChannel.
    SECURITY WARNING: Only inject this on trusted origins.
    """
    def __init__(self, tab_widget: 'TabWidget'):
        super().__init__()
        self._tab = tab_widget

    @Slot(str, result=str)
    def execute_python_logic(self, data: str) -> str:
        logger.info(f"Received from JS: {data}")
        return f"Python acknowledged: {data.upper()}"


class TabWidget(QWidget):
    """Encapsulates a single browser tab, rendering engine, and IPC mechanisms."""
    
    # Propagate signals to the main window
    url_changed = Signal(QUrl)
    title_changed = Signal(str)
    load_progress = Signal(int)
    load_finished = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        self.browser = QWebEngineView()
        self.layout.addWidget(self.browser)
        
        # Apply settings
        settings = QSettings("MyBrowserProject", "ChromiumPy")
        js_enabled = str(settings.value("enable_javascript", True)).lower() == 'true'
        self.browser.settings().setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, js_enabled)

        # Connect internal signals to external propagation
        self.browser.urlChanged.connect(self.url_changed.emit)
        self.browser.titleChanged.connect(self.title_changed.emit)
        self.browser.loadProgress.connect(self.load_progress.emit)
        self.browser.loadFinished.connect(self._on_load_finished)

        # DevTools Window (lazy loaded)
        self.devtools_view = None
        self.channel = None

    def _on_load_finished(self, success: bool) -> None:
        self.load_finished.emit(success)
        if success:
            self._inject_webchannel()

    def _inject_webchannel(self) -> None:
        """
        Injects the QWebChannel JS API.
        SECURITY: We only do this for local/trusted pages to prevent RCE.
        """
        url = self.browser.url().toString()
        is_trusted = url.startswith("file://") or "localhost" in url
        
        if is_trusted:
            self.channel = QWebChannel()
            self.bridge = PythonJSBridge(self)
            self.channel.registerObject("pybridge", self.bridge)
            self.browser.page().setWebChannel(self.channel)
            
            # Inject standard qtwebchannel.js script into the DOM
            js_injection = """
            if (typeof QWebChannel === 'undefined') {
                var script = document.createElement('script');
                script.src = 'qrc:///qtwebchannel/qwebchannel.js';
                script.onload = function() {
                    new QWebChannel(qt.webChannelTransport, function(channel) {
                        window.pybridge = channel.objects.pybridge;
                        console.log("Python Bridge Initialized.");
                    });
                };
                document.head.appendChild(script);
            }
            """
            self.run_javascript(js_injection)

    def run_javascript(self, script: str) -> None:
        """Python -> JS execution."""
        self.browser.page().runJavaScript(script, self._js_callback)

    def _js_callback(self, result) -> None:
        if result:
            logger.debug(f"JS Execution Result: {result}")

    def load_url(self, url: str) -> None:
        if not url.startswith(('http://', 'https://', 'file://', 'chrome://')):
            # Simple heuristic for searches vs direct URLs
            if '.' in url and ' ' not in url:
                url = f"https://{url}"
            else:
                url = f"https://duckduckgo.com/?q={url}"
        self.browser.setUrl(QUrl(url))

    def show_devtools(self) -> None:
        """Opens Chromium DevTools in a separate view."""
        if not self.devtools_view:
            self.devtools_view = QWebEngineView()
            self.devtools_view.setWindowTitle("Developer Tools")
            
            # Create a dedicated page for inspection
            dev_page = QWebEnginePage(self.devtools_view)
            self.devtools_view.setPage(dev_page)
            self.browser.page().setDevToolsPage(dev_page)
            
        self.devtools_view.show()
        self.devtools_view.raise_()