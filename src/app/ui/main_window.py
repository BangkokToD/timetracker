"""Главное окно приложения с табами."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QMainWindow, QTabWidget

from app.config import APP_NAME
from app.core.timer_engine import TimerEngine
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

        self._tabs = QTabWidget()
        self._tabs.setTabPosition(QTabWidget.TabPosition.North)
        self._tabs.setMovable(False)

        self._tabs.addTab(TimerTab(engine=self._engine), "Таймер")
        self._tabs.addTab(HistoryTab(engine=self._engine), "История")
        self._tabs.addTab(SettingsTab(), "Настройки")

        self.setCentralWidget(self._tabs)

        # Минимально разумное поведение окна.
        self.setMinimumSize(720, 420)
        self.setWindowFlag(Qt.WindowType.Window, True)