"""Главное окно приложения с табами."""

from __future__ import annotations

import logging

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QMainWindow, QTabWidget, QMessageBox
from typing import Optional

from app.config import APP_NAME
from app.core.app_bus import AppBus
from app.core.state import TimerState
from app.core.timer_engine import TimerEngine
from app.ui.tabs.history_tab import HistoryTab
from app.ui.tabs.settings_tab import SettingsTab
from app.ui.tabs.timer_tab import TimerTab

log = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """Главное окно с 3 вкладками: Таймер/История/Настройки."""

    def __init__(
        self,
        *,
        engine: Optional[TimerEngine] = None,
        build_ui: bool = True,
    ) -> None:
        """Инициализировать главное окно.

        Args:
            engine: внешний движок таймера для тестов или DI. Если не передан,
                создаётся стандартный TimerEngine.
        """
        super().__init__()
        self.setWindowTitle(APP_NAME)

        # Единый движок на приложение (COMMIT 4).
        self._bus = AppBus()
        self._engine = engine if engine is not None else TimerEngine()

        if build_ui:
            self._tabs = QTabWidget()
            self._tabs.setTabPosition(QTabWidget.TabPosition.North)
            self._tabs.setMovable(False)

            self._tabs.addTab(TimerTab(engine=self._engine, bus=self._bus), "Таймер")
            self._tabs.addTab(HistoryTab(engine=self._engine, bus=self._bus), "История")
            self._tabs.addTab(SettingsTab(bus=self._bus), "Настройки")

            self.setCentralWidget(self._tabs)

        # Минимально разумное поведение окна.
        self.setMinimumSize(720, 420)
        self.setWindowFlag(Qt.WindowType.Window, True)

    def closeEvent(self, event) -> None:  # type: ignore[override]
        """Закрытие приложения с учётом состояния таймера.

        Args:
            event: Qt event.

        Returns:
            None
        """
        if not self._handle_close():
            event.ignore()
            return

        event.accept()

    def _handle_close(self) -> bool:
        """Обработать закрытие. Возвращает True если можно закрывать."""

        state = self._engine.state

        # STOPPED → просто закрываем
        if state == TimerState.STOPPED:
            return True

        # RUNNING / PAUSED → спрашиваем подтверждение
        answer = QMessageBox.question(
            self,
            "Закрыть приложение",
            (
                "Текущая сессия ещё не завершена.\n\n"
                "При закрытии она будет сохранена."
            ),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel,
        )

        if answer != QMessageBox.StandardButton.Yes:
            return False

        # Сохраняем сессию
        try:
            self._engine.stop()
        except Exception as exc:
            log.exception("Ошибка при завершении сессии: %s", exc)
            QMessageBox.critical(
                self,
                "Ошибка",
                "Не удалось сохранить сессию. Закрытие отменено.",
            )
            return False

        return True
