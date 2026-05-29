import logging
from PySide6.QtWidgets import (
    QMainWindow, QTabWidget, QToolBar, QStatusBar, QMenu,
    QApplication, QMessageBox, QWidget, QVBoxLayout, QLabel
)
from PySide6.QtGui import QAction, QKeySequence, QIcon
from PySide6.QtCore import QUrl, Qt, QSettings
from collections import deque
from typing import Deque, Optional
import html as _html
from urllib.parse import quote as _quote

from .shortcut_manager import ShortcutManager, ShortcutSpec

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
        # Keep a small deque of recently closed tab URLs for "reopen closed tab"
        self.closed_tabs: Deque[str] = deque(maxlen=10)

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
        # Declarative shortcut specs follow Chrome-like conventions.
        sm = ShortcutManager(self)

        # Helper to create StandardKey or fallback strings
        S = QKeySequence.StandardKey

        specs = [
            # Tab & Window Management
            ShortcutSpec("new_tab", "New Tab", ["Ctrl+T"], "_action_new_tab"),
            ShortcutSpec("new_window", "New Window", [S.New], "_action_new_window"),
            ShortcutSpec("close_tab", "Close Tab", [S.Close, "Ctrl+W", "Ctrl+F4"], "_action_close_tab"),
            ShortcutSpec("reopen_tab", "Reopen Closed Tab", ["Ctrl+Shift+T"], "reopen_closed_tab"),
            ShortcutSpec("next_tab", "Next Tab", ["Ctrl+Tab"], "next_tab"),
            ShortcutSpec("prev_tab", "Previous Tab", ["Ctrl+Shift+Tab"], "prev_tab"),
            # Tab jump 1-9
            ShortcutSpec("tab_1", "Jump to Tab 1", ["Ctrl+1"], "_jump_to_1"),
            ShortcutSpec("tab_2", "Jump to Tab 2", ["Ctrl+2"], "_jump_to_2"),
            ShortcutSpec("tab_3", "Jump to Tab 3", ["Ctrl+3"], "_jump_to_3"),
            ShortcutSpec("tab_4", "Jump to Tab 4", ["Ctrl+4"], "_jump_to_4"),
            ShortcutSpec("tab_5", "Jump to Tab 5", ["Ctrl+5"], "_jump_to_5"),
            ShortcutSpec("tab_6", "Jump to Tab 6", ["Ctrl+6"], "_jump_to_6"),
            ShortcutSpec("tab_7", "Jump to Tab 7", ["Ctrl+7"], "_jump_to_7"),
            ShortcutSpec("tab_8", "Jump to Tab 8", ["Ctrl+8"], "_jump_to_8"),
            ShortcutSpec("tab_9", "Jump to Last Tab", ["Ctrl+9"], "_jump_to_last"),

            # Navigation
            ShortcutSpec("back", "Back", ["Alt+Left"], "_action_back"),
            ShortcutSpec("forward", "Forward", ["Alt+Right"], "_action_forward"),
            ShortcutSpec("reload", "Reload", [S.Refresh, "Ctrl+R"], "reload"),
            ShortcutSpec("hard_reload", "Hard Reload", ["Ctrl+Shift+R", "Shift+F5"], "hard_reload"),
            ShortcutSpec("stop", "Stop Loading", ["Esc"], "stop_loading"),
            ShortcutSpec("home", "Home", ["Alt+Home"], "go_home"),

            # Address bar
            ShortcutSpec("focus_url", "Focus URL", ["Ctrl+L", "Alt+D", "F6"], "focus_url_bar"),

            # Page actions
            ShortcutSpec("print", "Print", [S.Print, "Ctrl+P"], "print_page"),
            ShortcutSpec("save", "Save Page", ["Ctrl+S"], "save_page"),
            ShortcutSpec("find", "Find in Page", [S.Find, "Ctrl+F"], "find_in_page"),
            ShortcutSpec("find_next", "Find Next", ["Ctrl+G"], "find_next"),
            ShortcutSpec("zoom_in", "Zoom In", ["Ctrl++", "Ctrl+=", "Ctrl+Plus"], "zoom_in"),
            ShortcutSpec("zoom_out", "Zoom Out", ["Ctrl+-", "Ctrl+Minus"], "zoom_out"),
            ShortcutSpec("zoom_reset", "Reset Zoom", ["Ctrl+0"], "zoom_reset"),

            # Browser features
            ShortcutSpec("history", "History", ["Ctrl+H"], "_not_impl_history"),
            ShortcutSpec("downloads", "Downloads", ["Ctrl+J"], "_not_impl_downloads"),
            ShortcutSpec("bookmark", "Bookmark Page", ["Ctrl+D"], "_add_bookmark"),
            ShortcutSpec("devtools", "DevTools", ["F12", "Ctrl+Shift+I"], "_action_devtools"),
            ShortcutSpec("view_source", "View Source", ["Ctrl+U"], "view_source"),
        ]

        sm.register_shortcuts(specs)

    # --- Core Logic ---

    def _current_tab(self) -> TabWidget | None:
        return self.tab_widget.currentWidget()

    # --- Shortcut handlers & helpers ---

    def _not_implemented_stub(self, feature_name: str) -> None:
        logger.info("Shortcut invoked for unimplemented feature: %s", feature_name)
        self.status.showMessage(f"{feature_name} not implemented", 3000)

    def _action_new_tab(self) -> None:
        self.add_new_tab(QUrl(self.settings.value("homepage", "https://duckduckgo.com")), "New Tab")

    def _action_new_window(self) -> None:
        self._not_implemented_stub("New Window")

    def _action_close_tab(self) -> None:
        self.close_tab(self.tab_widget.currentIndex())

    def reopen_closed_tab(self) -> None:
        if not self.closed_tabs:
            self.status.showMessage("No recently closed tabs", 2000)
            return
        url = self.closed_tabs.pop()
        self.add_new_tab(QUrl(url), "Reopened Tab")

    def next_tab(self) -> None:
        count = self.tab_widget.count()
        if count < 2:
            return
        idx = (self.tab_widget.currentIndex() + 1) % count
        self.tab_widget.setCurrentIndex(idx)

    def prev_tab(self) -> None:
        count = self.tab_widget.count()
        if count < 2:
            return
        idx = (self.tab_widget.currentIndex() - 1) % count
        self.tab_widget.setCurrentIndex(idx)

    def _jump_to_index(self, index: int) -> None:
        if 0 <= index < self.tab_widget.count():
            self.tab_widget.setCurrentIndex(index)

    def _jump_to_last(self) -> None:
        cnt = self.tab_widget.count()
        if cnt:
            self.tab_widget.setCurrentIndex(cnt - 1)

    # Per-number entry wrappers
    def _jump_to_1(self) -> None: self._jump_to_index(0)
    def _jump_to_2(self) -> None: self._jump_to_index(1)
    def _jump_to_3(self) -> None: self._jump_to_index(2)
    def _jump_to_4(self) -> None: self._jump_to_index(3)
    def _jump_to_5(self) -> None: self._jump_to_index(4)
    def _jump_to_6(self) -> None: self._jump_to_index(5)
    def _jump_to_7(self) -> None: self._jump_to_index(6)
    def _jump_to_8(self) -> None: self._jump_to_index(7)

    # Navigation handlers
    def _action_back(self) -> None:
        if tab := self._current_tab():
            tab.browser.back()

    def _action_forward(self) -> None:
        if tab := self._current_tab():
            tab.browser.forward()

    def reload(self) -> None:
        if tab := self._current_tab():
            tab.browser.reload()

    def hard_reload(self) -> None:
        if tab := self._current_tab():
            try:
                tab.browser.reload()  # QtWebEngine doesn't expose cache-bypass easily
            except Exception:
                pass

    def stop_loading(self) -> None:
        if tab := self._current_tab():
            tab.browser.stop()

    def go_home(self) -> None:
        homepage = self.settings.value("homepage", "https://duckduckgo.com")
        if tab := self._current_tab():
            tab.load_url(homepage)

    def focus_url_bar(self) -> None:
        self.url_bar.setFocus()
        self.url_bar.selectAll()

    # Page & feature stubs
    def print_page(self) -> None:
        self._not_implemented_stub("Print")

    def save_page(self) -> None:
        self._not_implemented_stub("Save Page")

    def find_in_page(self) -> None:
        self._not_implemented_stub("Find in Page")

    def find_next(self) -> None:
        self._not_implemented_stub("Find Next")

    def zoom_in(self) -> None:
        if tab := self._current_tab():
            try:
                z = tab.browser.zoomFactor()
                tab.browser.setZoomFactor(min(5.0, z + 0.1))
            except Exception:
                pass

    def zoom_out(self) -> None:
        if tab := self._current_tab():
            try:
                z = tab.browser.zoomFactor()
                tab.browser.setZoomFactor(max(0.25, z - 0.1))
            except Exception:
                pass

    def zoom_reset(self) -> None:
        if tab := self._current_tab():
            try:
                tab.browser.setZoomFactor(1.0)
            except Exception:
                pass

    def _not_impl_history(self) -> None:
        self._not_implemented_stub("History")

    def _not_impl_downloads(self) -> None:
        self._not_implemented_stub("Downloads")

    def _action_devtools(self) -> None:
        if tab := self._current_tab():
            tab.show_devtools()

    def view_source(self) -> None:
        if not (tab := self._current_tab()):
            return

        page = tab.browser.page()

        def _got_html(html_text: str) -> None:
            # Display source in a new tab inside a preformatted block
            src = _html.escape(html_text)
            new = self.add_new_tab(QUrl("about:blank"), "View Source")
            new.browser.setHtml(f"<pre>{src}</pre>")

        try:
            page.toHtml(_got_html)
        except Exception:
            self._not_implemented_stub("View Source")

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
        # Record URL for "reopen closed tab" queue if available
        try:
            url = widget.browser.url().toString()
            if url:
                self.closed_tabs.append(url)
        except Exception:
            pass

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