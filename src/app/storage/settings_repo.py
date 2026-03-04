"""Репозиторий настроек (settings.json)."""

from __future__ import annotations

import logging
from json import JSONDecodeError
from typing import Any

from app.storage.models import Settings
from app.storage.paths import ensure_data_dir_exists, get_settings_path
from app.storage.utils import read_json, write_json_atomic

log = logging.getLogger(__name__)

SETTINGS_VERSION: int = 1


def ensure_settings_file() -> None:
    """Создать settings.json с дефолтами, если файла нет.

    Returns:
        None
    """
    ensure_data_dir_exists()
    path = get_settings_path()
    if path.exists():
        # Проверим, что файл читается.
        _ = load_settings()
        return

    defaults = Settings.defaults()
    payload = {"version": SETTINGS_VERSION, "settings": defaults.to_dict()}
    write_json_atomic(path, payload)
    log.info("Created default settings.json at %s", path)


def load_settings() -> Settings:
    """Загрузить настройки.

    Returns:
        Settings.

    Raises:
        ValueError: если структура/версия/значения некорректны.
    """
    path = get_settings_path()
    try:
        obj = read_json(path)
    except FileNotFoundError:
        # Сценарий: кто-то удалил файл. Восстановим дефолты.
        ensure_settings_file()
        obj = read_json(path)
    except JSONDecodeError as e:
        raise ValueError(f"settings.json повреждён: {e}") from e

    version = int(obj.get("version", 0))
    if version != SETTINGS_VERSION:
        raise ValueError(f"Неподдерживаемая версия settings.json: {version}")

    raw_settings = obj.get("settings", {})
    if not isinstance(raw_settings, dict):
        raise ValueError("settings.json: поле 'settings' должно быть объектом")

    return Settings.from_dict(raw_settings)


def save_settings(settings: Settings) -> None:
    """Сохранить настройки.

    Args:
        settings: Settings.

    Returns:
        None
    """
    ensure_data_dir_exists()
    path = get_settings_path()
    payload: dict[str, Any] = {"version": SETTINGS_VERSION, "settings": settings.to_dict()}
    write_json_atomic(path, payload)
