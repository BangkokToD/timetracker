"""Главное окно приложения с табами."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QMainWindow, QTabWidget

from app.config import APP_NAME
from app.core.app_bus import AppBus
from app.core.timer_engine import TimerEngine
from app.ui.tray import TrayController
from app.ui.tabs.history_tab import HistoryTab
from app.ui.tabs.settings_tab import SettingsTab
from app.ui.tabs.timer_tab import TimerTab


class MainWindow(QMainWindow):
    """Главное окно с 3 вкладками: Таймер/История/Настройки."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(APP_NAME)

        # Единый движок на приложение (COMMIT 4).
        self._engine = TimerEngine()
        self._bus = AppBus()

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

        # COMMIT 8: трей + управление.
        self._tray = TrayController(window=self, engine=self._engine)

        # COMMIT 8: показываем уведомление "свернуто в трей" один раз за запуск.
        self._tray_hint_shown: bool = False

    def closeEvent(self, event) -> None:  # type: ignore[override]
        """Скрыть окно вместо выхода (сворачиваем в трей).

        Args:
            event: Qt event.

        Returns:
            None
        """
        # Если трей не доступен, ведём себя как обычное окно.
        if not self._tray.is_available:
            super().closeEvent(event)
            return

        self.hide()
        event.ignore()

        if not self._tray_hint_shown:
            self._tray_hint_shown = True
            self._tray.show_hidden_message_once()
