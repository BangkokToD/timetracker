"""Утилиты для безопасной работы с JSON-файлами."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def read_json(path: Path) -> dict[str, Any]:
    """Прочитать JSON из файла.

    Args:
        path: путь к файлу.

    Returns:
        dict (если файл пустой/не существует — исключение не гасим здесь).

    Raises:
        FileNotFoundError: если файла нет.
        json.JSONDecodeError: если JSON битый.
        ValueError: если корень не dict.
    """
    raw = path.read_text(encoding="utf-8")
    obj = json.loads(raw)
    if not isinstance(obj, dict):
        raise ValueError("Ожидается JSON-объект (dict) в корне файла")
    return obj


def write_json_atomic(path: Path, obj: dict[str, Any]) -> None:
    """Атомарно записать JSON (best-effort).

    Пишем во временный файл в той же директории и затем replace().

    Args:
        path: путь к целевому файлу.
        obj: JSON-словарь.

    Returns:
        None
    """
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    data = json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True)
    tmp_path.write_text(data + "\n", encoding="utf-8")
    tmp_path.replace(path)
