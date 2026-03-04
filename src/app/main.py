"""Запуск GUI приложения timetracker."""

from __future__ import annotations

import logging

from PyQt6.QtWidgets import QApplication

from app.logging_config import setup_logging
from app.storage.bootstrap import ensure_storage_initialized
from app.ui.main_window import MainWindow

log = logging.getLogger(__name__)


def main() -> int:
    """Запустить приложение.

    Returns:
        Код завершения процесса (0 — успех).
    """
    setup_logging()
    log.info("Starting timetracker...")

    # COMMIT 2: гарантируем наличие JSON-хранилища с дефолтами на первом запуске.
    # Если файлы повреждены/невалидны — поднимем понятную ошибку в логах.
    ensure_storage_initialized()

    app = QApplication([])
    # COMMIT 8: приложение живёт в фоне, когда окно скрыто в трей.
    app.setQuitOnLastWindowClosed(False)
    w = MainWindow()
    w.show()

    rc = app.exec()
    log.info("Exiting timetracker with code=%s", rc)
    return int(rc)