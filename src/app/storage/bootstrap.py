"""Bootstrap хранилища.

Задача COMMIT 2:
— на первом запуске создать settings.json и data.json с дефолтами;
— при последующих запусках читать и валидировать без падений UI на пустых файлах.
"""

from __future__ import annotations

import logging

from app.storage.settings_repo import ensure_settings_file
from app.storage.sessions_repo import ensure_data_file

log = logging.getLogger(__name__)


def ensure_storage_initialized() -> None:
    """Инициализировать хранилище приложения.

    Создаёт файлы, если их нет. Если файлы есть — проверяет, что они читаются.

    Returns:
        None
    """
    ensure_settings_file()
    ensure_data_file()
    log.info("Storage initialized")
