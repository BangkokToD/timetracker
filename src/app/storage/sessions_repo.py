"""Репозиторий сессий (data.json)."""

from __future__ import annotations

import logging
from json import JSONDecodeError
from typing import Any

from app.storage.models import Session
from app.storage.paths import ensure_data_dir_exists, get_data_path
from app.storage.utils import read_json, write_json_atomic

log = logging.getLogger(__name__)

DATA_VERSION: int = 1


def ensure_data_file() -> None:
    """Создать data.json, если файла нет.

    Returns:
        None
    """
    ensure_data_dir_exists()
    path = get_data_path()
    if path.exists():
        _ = load_sessions()
        return

    payload = {"version": DATA_VERSION, "sessions": []}
    write_json_atomic(path, payload)
    log.info("Created default data.json at %s", path)


def load_sessions() -> list[Session]:
    """Загрузить все сессии.

    Returns:
        list[Session].

    Raises:
        ValueError: если data.json повреждён/структура неверная.
    """
    path = get_data_path()
    try:
        obj = read_json(path)
    except FileNotFoundError:
        ensure_data_file()
        obj = read_json(path)
    except JSONDecodeError as e:
        raise ValueError(f"data.json повреждён: {e}") from e

    version = int(obj.get("version", 0))
    if version != DATA_VERSION:
        raise ValueError(f"Неподдерживаемая версия data.json: {version}")

    raw_sessions = obj.get("sessions", [])
    if not isinstance(raw_sessions, list):
        raise ValueError("data.json: поле 'sessions' должно быть списком")

    sessions: list[Session] = []
    for i, item in enumerate(raw_sessions):
        if not isinstance(item, dict):
            raise ValueError(f"data.json: sessions[{i}] должен быть объектом")
        sessions.append(Session.from_dict(item))
    return sessions


def append_session(session: Session) -> None:
    """Добавить сессию в data.json.

    Args:
        session: Session.

    Returns:
        None
    """
    ensure_data_file()
    path = get_data_path()
    obj = read_json(path)

    raw_sessions = obj.get("sessions", [])
    if not isinstance(raw_sessions, list):
        raise ValueError("data.json: поле 'sessions' должно быть списком")

    raw_sessions.append(session.to_dict())
    obj["sessions"] = raw_sessions
    obj["version"] = DATA_VERSION
    write_json_atomic(path, obj)


def reset_all() -> None:
    """Сбросить историю (только data.json).

    Вариант A: settings.json не трогаем.

    Returns:
        None
    """
    ensure_data_dir_exists()
    path = get_data_path()
    payload: dict[str, Any] = {"version": DATA_VERSION, "sessions": []}
    write_json_atomic(path, payload)
    log.info("History reset: data.json cleared at %s", path)
