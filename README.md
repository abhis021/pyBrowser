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