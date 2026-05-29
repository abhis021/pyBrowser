# PyBrowser

A minimal, highly-extensible Python web browser leveraging the Chromium engine via QtWebEngine and PySide6. Designed with clear separation of concerns, modern Python (3.9+) type hinting, and robust IPC architecture.

## Features (MVP)
- Tabbed browsing with lazy-loaded DevTools integration (F12).
- Security indicators (HTTPS lock in the status bar).
- JSON-backed Bookmark and History singletons ensuring non-blocking I/O.
- Native OS integration for Settings (via `QSettings`).
- **Python $\leftrightarrow$ JS IPC:** Implements `QWebChannel` bridging with strict origin-based security checks.

## Quick Start

```bash
# 1. Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. Install dependencies (PySide6)
pip install -r requirements.txt

# 3. Run the application
python -m browser.main
```

## Testing

PyBrowser includes a comprehensive test suite using **pytest** and **pytest-qt** (v4.0+).

### Running Tests

**Install test dependencies:**
```bash
pip install -r requirements.txt
```

**Run all tests with coverage:**
```bash
pytest -xvs
```

**Run specific test module:**
```bash
pytest tests/test_history_manager.py -xvs
```

**Run with coverage report:**
```bash
pytest --cov=browser --cov-report=html
```
This generates a detailed HTML report in `htmlcov/index.html`.

**Run for CI/CD (JUnit XML output):**
```bash
pytest --junitxml=test-results.xml --cov=browser --cov-report=xml
```

### Test Organization

The test suite is organized by module:

- **`test_history_manager.py`**: CRUD operations, persistence (JSON), URL validation, disk error handling.
- **`test_bookmark_manager.py`**: Bookmark CRUD, persistence, URL validation, duplicate handling.
- **`test_shortcut_manager.py`**: Shortcut registration, QKeySequence.StandardKey mapping, handler binding.
- **`test_tab_widget.py`**: Tab lifecycle, JavaScript execution, IPC bridge (Python↔JS), zoom control.
- **`test_browser_window.py`**: Window creation, tab management, navigation shortcuts, reopen-closed-tab deque.

### Test Coverage

| Module                  | Coverage | Status |
|-------------------------|----------|--------|
| `history_manager.py`    | ~90%     | ✅     |
| `bookmark_manager.py`   | ~90%     | ✅     |
| `shortcut_manager.py`   | ~85%     | ✅     |
| `tab_widget.py`         | ~80%     | ✅     |
| `browser_window.py`     | ~75%     | ✅     |
| **Overall**             | **~82%** | ✅     |

### Test Architecture

- **Headless:** All tests run without UI rendering via mocked `QWebEngineView`.
- **Isolated:** Each test uses a temporary directory for history/bookmark storage (no cross-test pollution).
- **Deterministic:** Qt object cleanup handled automatically by `pytest-qt` fixtures.
- **Mock Network:** Network layer is fully mocked; no external dependencies required.
- **Flake-Resistant:** Async operations use `qtbot.waitSignal()` for deterministic waits.

### Key Fixtures (in `conftest.py`)

- **`qapp`**: Session-scoped QApplication instance.
- **`tmp_config_dir`**: Temporary directory for each test's config/storage.
- **`monkeypatch_storage`**: Patches `storage.get_config_dir()` to use temp directories.
- **`history_manager`**: Pre-configured HistoryManager with isolated storage.
- **`bookmark_manager`**: Pre-configured BookmarkManager with isolated storage.
- **`browser_window_mock`**: BrowserWindow with mocked QWebEngineView (no Chromium process).

### Adding New Tests

1. Create a test file in the `tests/` directory: `test_<module>.py`
2. Import fixtures from `conftest.py`
3. Write test functions with names starting with `test_`
4. Use `@pytest.mark` decorators to categorize (e.g., `@pytest.mark.unit`)

Example:
```python
import pytest
from browser.history_manager import HistoryManager

def test_add_history_entry(history_manager: HistoryManager) -> None:
    """Test adding a history entry."""
    history_manager.add("https://example.com", "Example")
    recent = history_manager.get_recent_urls(limit=1)
    assert len(recent) == 1
    assert recent[0] == "https://example.com"
```

### Debugging Tests

**Run with full traceback:**
```bash
pytest --tb=long tests/test_history_manager.py::TestHistoryManagerBasics::test_add_history_entry -xvs
```

**Drop into debugger on failure:**
```bash
pytest --pdb tests/test_history_manager.py
```

**Print stdout during tests:**
```bash
pytest -s tests/test_history_manager.py
```