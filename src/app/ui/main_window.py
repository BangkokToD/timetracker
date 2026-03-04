"""Главное окно приложения с табами."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QMainWindow, QTabWidget

from app.config import APP_NAME
from app.ui.tabs.history_tab import HistoryTab
from app.ui.tabs.settings_tab import SettingsTab
from app.ui.tabs.timer_tab import TimerTab


class MainWindow(QMainWindow):
    """Главное окно с 3 вкладками: Таймер/История/Настройки."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(APP_NAME)

        self._tabs = QTabWidget()
        self._tabs.setTabPosition(QTabWidget.TabPosition.North)
        self._tabs.setMovable(False)

        self._tabs.addTab(TimerTab(), "Таймер")
        self._tabs.addTab(HistoryTab(), "История")
        self._tabs.addTab(SettingsTab(), "Настройки")

        self.setCentralWidget(self._tabs)

        # Минимально разумное поведение окна.
        self.setMinimumSize(720, 420)
        self.setWindowFlag(Qt.WindowType.Window, True)