"""Пути файлов хранилища.

Требование: JSON лежит в `~/.local/share/<app_name>/`.
Также поддерживаем XDG_DATA_HOME, если задано.
"""

from __future__ import annotations

import os
from pathlib import Path

from app.config import APP_NAME


def get_data_dir() -> Path:
    """Получить директорию данных приложения.

    Returns:
        Path директории (создание директории не выполняется).
    """
    xdg_data_home = os.environ.get("XDG_DATA_HOME", "").strip()
    if xdg_data_home:
        return Path(xdg_data_home) / APP_NAME
    return Path.home() / ".local" / "share" / APP_NAME


def get_settings_path() -> Path:
    """Путь к settings.json.

    Returns:
        Path.
    """
    return get_data_dir() / "settings.json"


def get_data_path() -> Path:
    """Путь к data.json.

    Returns:
        Path.
    """
    return get_data_dir() / "data.json"


def ensure_data_dir_exists() -> None:
    """Гарантировать существование директории данных.

    Returns:
        None
    """
    get_data_dir().mkdir(parents=True, exist_ok=True)
