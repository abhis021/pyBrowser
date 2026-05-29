import logging
from PySide6.QtWidgets import (
    QMainWindow, QTabWidget, QToolBar, QStatusBar, QMenu,
    QApplication, QMessageBox, QWidget, QVBoxLayout, QLabel
)
from PySide6.QtGui import QAction, QKeySequence, QIcon
from PySide6.QtCore import QUrl, Qt, QSettings

from .tab_widget import TabWidget
from .url_bar import UrlBar
from .bookmark_manager import BookmarkManager
from .history_manager import HistoryManager
from .settings_dialog import SettingsDialog

logger = logging.getLogger(__name__)

class BrowserWindow(QMainWindow):
    """Main Application Window managing tabs, navigation, and state injection."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("pyBrowser")
        self.resize(1200, 800)

        # Managers (State)
        self.history_manager = HistoryManager()
        self.bookmark_manager = BookmarkManager()
        self.settings = QSettings("MyBrowserProject", "pyBrowser")

        # UI Setup
        self._setup_tabs()
        self._setup_toolbar()
        self._setup_menu()
        self._setup_statusbar()
        self._setup_shortcuts()

        # Initial Tab
        homepage = self.settings.value("homepage", "https://duckduckgo.com")
        self.add_new_tab(QUrl(homepage), "New Tab")

    def _setup_tabs(self) -> None:
        self.tab_widget = QTabWidget()
        self.tab_widget.setDocumentMode(True)
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.tabCloseRequested.connect(self.close_tab)
        self.tab_widget.currentChanged.connect(self._on_tab_changed)
        self.setCentralWidget(self.tab_widget)

    def _setup_toolbar(self) -> None:
        toolbar = QToolBar("Navigation")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        # Actions (Using fallback text if system theme lacks icons)
        back_action = QAction(QIcon.fromTheme("go-previous"), "Back", self)
        back_action.triggered.connect(lambda: self._current_tab().browser.back() if self._current_tab() else None)
        toolbar.addAction(back_action)

        forward_action = QAction(QIcon.fromTheme("go-next"), "Forward", self)
        forward_action.triggered.connect(lambda: self._current_tab().browser.forward() if self._current_tab() else None)
        toolbar.addAction(forward_action)

        reload_action = QAction(QIcon.fromTheme("view-refresh"), "Reload", self)
        reload_action.triggered.connect(lambda: self._current_tab().browser.reload() if self._current_tab() else None)
        toolbar.addAction(reload_action)

        # Address Bar
        self.url_bar = UrlBar()
        self.url_bar.returnPressed.connect(self._navigate_from_url_bar)
        toolbar.addWidget(self.url_bar)

    def _setup_menu(self) -> None:
        menubar = self.menuBar()
        
        # File Menu
        file_menu = menubar.addMenu("&File")
        new_tab_action = QAction("New Tab", self)
        new_tab_action.triggered.connect(lambda: self.add_new_tab(QUrl("https://duckduckgo.com"), "New Tab"))
        file_menu.addAction(new_tab_action)
        
        settings_action = QAction("Settings", self)
        settings_action.triggered.connect(self._open_settings)
        file_menu.addAction(settings_action)

        # Bookmarks Menu
        self.bookmarks_menu = menubar.addMenu("&Bookmarks")
        add_bm_action = QAction("Bookmark Current Page", self)
        add_bm_action.triggered.connect(self._add_bookmark)
        self.bookmarks_menu.addAction(add_bm_action)
        self.bookmarks_menu.addSeparator()
        self.bookmarks_menu.aboutToShow.connect(self._populate_bookmarks_menu)

        # Developer Menu
        dev_menu = menubar.addMenu("&Developer")
        inspect_action = QAction("Inspect Element (DevTools)", self)
        inspect_action.triggered.connect(lambda: self._current_tab().show_devtools() if self._current_tab() else None)
        dev_menu.addAction(inspect_action)

    def _setup_statusbar(self) -> None:
        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self.security_label = QLabel()
        self.status.addPermanentWidget(self.security_label)

    def _setup_shortcuts(self) -> None:
        QAction("New Tab", self, shortcut=QKeySequence("Ctrl+T"), triggered=lambda: self.add_new_tab(QUrl("https://duckduckgo.com"), "New Tab"))
        QAction("Close Tab", self, shortcut=QKeySequence("Ctrl+W"), triggered=lambda: self.close_tab(self.tab_widget.currentIndex()))
        QAction("Focus URL", self, shortcut=QKeySequence("Ctrl+L"), triggered=self.url_bar.setFocus)
        QAction("Refresh", self, shortcut=QKeySequence("F5"), triggered=lambda: self._current_tab().browser.reload() if self._current_tab() else None)
        QAction("DevTools", self, shortcut=QKeySequence("F12"), triggered=lambda: self._current_tab().show_devtools() if self._current_tab() else None)

    # --- Core Logic ---

    def _current_tab(self) -> TabWidget | None:
        return self.tab_widget.currentWidget()

    def add_new_tab(self, qurl: QUrl, label: str) -> TabWidget:
        tab = TabWidget(self)
        i = self.tab_widget.addTab(tab, label)
        self.tab_widget.setCurrentIndex(i)
        
        # Connect tab signals
        tab.url_changed.connect(lambda url, t=tab: self._update_url_bar(url, t))
        tab.title_changed.connect(lambda title, t=tab: self._update_tab_title(title, t))
        tab.load_progress.connect(self._update_progress)
        tab.load_finished.connect(self._handle_load_finished)

        tab.browser.setUrl(qurl)
        return tab

    def close_tab(self, index: int) -> None:
        if self.tab_widget.count() < 2:
            self.close()
            return
        widget = self.tab_widget.widget(index)
        self.tab_widget.removeTab(index)
        widget.deleteLater()

    def _navigate_from_url_bar(self) -> None:
        text = self.url_bar.text()
        if tab := self._current_tab():
            tab.load_url(text)

    def _on_tab_changed(self, index: int) -> None:
        if tab := self._current_tab():
            self._update_url_bar(tab.browser.url(), tab)
            self._update_security_icon(tab.browser.url())

    def _update_url_bar(self, qurl: QUrl, source_tab: TabWidget) -> None:
        if source_tab != self._current_tab():
            return # Only update UI if the signal came from the active tab
        url_str = qurl.toString()
        self.url_bar.set_url(url_str)
        self.url_bar.update_history_completions(self.history_manager.get_recent_urls())

    def _update_tab_title(self, title: str, source_tab: TabWidget) -> None:
        index = self.tab_widget.indexOf(source_tab)
        if index != -1:
            display_title = title[:20] + "..." if len(title) > 20 else title
            self.tab_widget.setTabText(index, display_title)

    def _update_progress(self, progress: int) -> None:
        self.status.showMessage(f"Loading: {progress}%", 1000)

    def _handle_load_finished(self, success: bool) -> None:
        if not success:
            logger.warning("Failed to load page.")
        if tab := self._current_tab():
            url = tab.browser.url().toString()
            title = tab.browser.title()
            self.history_manager.add(url, title)
            self._update_security_icon(tab.browser.url())

    def _update_security_icon(self, url: QUrl) -> None:
        if url.scheme() == "https":
            self.security_label.setText("🔒 Secure")
            self.security_label.setStyleSheet("color: green;")
        else:
            self.security_label.setText("🔓 Insecure")
            self.security_label.setStyleSheet("color: red;")

    def _add_bookmark(self) -> None:
        if tab := self._current_tab():
            url = tab.browser.url().toString()
            title = tab.browser.title()
            self.bookmark_manager.add_bookmark(title, url)
            self.status.showMessage("Bookmark added!", 2000)

    def _populate_bookmarks_menu(self) -> None:
        self.bookmarks_menu.clear()
        add_bm_action = QAction("Bookmark Current Page", self)
        add_bm_action.triggered.connect(self._add_bookmark)
        self.bookmarks_menu.addAction(add_bm_action)
        self.bookmarks_menu.addSeparator()

        for bm in self.bookmark_manager.get_all():
            action = QAction(bm['title'], self)
            action.triggered.connect(lambda checked=False, u=bm['url']: self._current_tab().load_url(u))
            self.bookmarks_menu.addAction(action)

    def _open_settings(self) -> None:
        dlg = SettingsDialog(self)
        dlg.exec()