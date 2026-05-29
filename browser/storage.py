"""Utilities for cross-platform configuration/storage paths and safe file operations.

Designed for small, well-tested helpers used by persistence managers.
"""
from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Iterator


def get_config_dir(app_name: str = "pyBrowser") -> Path:
    """Return a platform-appropriate directory for storing app state.

    Uses APPDATA on Windows, ~/Library/Application Support on macOS,
    and XDG config dir (~/.config) on Linux/other.
    """
    if os.name == "nt":
        base = os.getenv("APPDATA") or Path.home() / "AppData" / "Roaming"
        return Path(base) / app_name
    # macOS
    try:
        if os.uname().sysname == "Darwin":
            return Path.home() / "Library" / "Application Support" / app_name
    except Exception:
        pass
    # Fallback to XDG
    xdg = os.getenv("XDG_CONFIG_HOME")
    if xdg:
        return Path(xdg) / app_name
    return Path.home() / ".config" / app_name


def atomic_write_text(path: Path, data: str, encoding: str = "utf-8") -> None:
    """Write text to `path` atomically.

    Writes to a temporary file adjacent to `path` then replaces it.
    This avoids partial writes if the app crashes during IO.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=path.name, dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding=encoding) as f:
            f.write(data)
        os.replace(tmp, str(path))
    finally:
        # Ensure temp is removed if something failed before replace
        try:
            if Path(tmp).exists():
                Path(tmp).unlink()
        except Exception:
            pass
