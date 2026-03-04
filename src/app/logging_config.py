"""Настройка логирования приложения.

Требование COMMIT 1: минимальное логирование в stdout.
"""

from __future__ import annotations

import logging
import sys


def setup_logging() -> None:
    """Настроить логирование в stdout.

    Returns:
        None
    """
    root = logging.getLogger()
    if root.handlers:
        # Если кто-то уже настроил логирование (например, тесты) — не дублируем.
        return

    handler = logging.StreamHandler(stream=sys.stdout)
    fmt = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(fmt)

    root.setLevel(logging.INFO)
    root.addHandler(handler)