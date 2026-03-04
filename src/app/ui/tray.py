"""Системный трей приложения (COMMIT 8).

Требования:
— иконка секундомера (fromTheme + fallback);
— меню: Open, Start/Pause/Resume/Stop (динамически), Exit;
— закрытие окна сворачивает в трей (реализовано в MainWindow.closeEvent);
— Exit: если RUNNING/PAUSED → stop() (запись сессии) и выйти.
"""

from __future__ import annotations

from typing import Optional

from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtWidgets import QApplication, QMenu, QStyle, QSystemTrayIcon, QWidget

from app.config import APP_NAME
from app.core.state import TimerState
from app.core.timer_engine import TimerEngine


def _tray_icon() -> QIcon:
    """Получить иконку трея (fromTheme + fallback).

    Returns:
        QIcon.
    """
    for name in ("chronometer", "timer", "stopwatch"):
        ico = QIcon.fromTheme(name)
        if not ico.isNull():
            return ico

    app = QApplication.instance()
    if app is not None:
        style = app.style()
        if style is not None:
            # Fallback: стандартная иконка приложения/системы.
            return style.standardIcon(QStyle.StandardPixmap.SP_ComputerIcon)
    return QIcon()


class TrayController:
    """Контроллер системного трея."""

    def __init__(self, *, window: QWidget, engine: TimerEngine) -> None:
        """Инициализировать трей.

        Args:
            window: главное окно (для show/raise/activate).
            engine: единый TimerEngine.
        """
        self._window = window
        self._engine = engine

        self._tray = QSystemTrayIcon(_tray_icon(), self._window)
        self._tray.setToolTip(APP_NAME)

        self._menu = QMenu()
        self._act_open = QAction("Открыть", self._menu)

        # Динамика управления (вариант B): показываем только релевантные действия.
        self._act_start = QAction("Старт", self._menu)
        self._act_pause_resume = QAction("Пауза", self._menu)
        self._act_stop = QAction("Стоп", self._menu)

        self._act_exit = QAction("Выход", self._menu)

        self._menu.addAction(self._act_open)
        self._menu.addSeparator()
        self._menu.addAction(self._act_start)
        self._menu.addAction(self._act_pause_resume)
        self._menu.addAction(self._act_stop)
        self._menu.addSeparator()
        self._menu.addAction(self._act_exit)

        self._tray.setContextMenu(self._menu)

        self._act_open.triggered.connect(self._on_open)
        self._act_start.triggered.connect(self._on_start)
        self._act_pause_resume.triggered.connect(self._on_pause_resume)
        self._act_stop.triggered.connect(self._on_stop)
        self._act_exit.triggered.connect(self._on_exit)

        # Одиночный клик по иконке — открыть окно.
        self._tray.activated.connect(self._on_tray_activated)

        # Обновление меню: state может меняться из UI, поэтому периодически сверяем.
        self._refresh_timer = QTimer(self._window)
        self._refresh_timer.setInterval(400)
        self._refresh_timer.timeout.connect(self.refresh_menu)
        self._refresh_timer.start()

        # Также обновляем меню после stop() (когда сессия записана).
        self._engine.subscribe_on_stop(self._on_engine_stop)

        self._tray.show()
        self.refresh_menu()

        self._hidden_message_shown: bool = False

    @property
    def is_available(self) -> bool:
        """Доступен ли системный трей.

        Returns:
            True если системный трей поддерживается.
        """
        return QSystemTrayIcon.isSystemTrayAvailable()

    def show_hidden_message_once(self) -> None:
        """Показать уведомление о сворачивании в трей один раз за запуск."""
        if self._hidden_message_shown:
            return
        self._hidden_message_shown = True
        try:
            self._tray.showMessage(APP_NAME, "Свернуто в трей")
        except Exception:
            # Некоторые окружения/WM могут не поддерживать сообщения.
            pass

    def refresh_menu(self) -> None:
        """Обновить видимость пунктов меню по состоянию движка."""
        st = self._engine.state

        # Вариант B: показываем только релевантные.
        if st == TimerState.STOPPED:
            self._act_start.setVisible(True)
            self._act_pause_resume.setVisible(False)
            self._act_stop.setVisible(False)
        elif st == TimerState.RUNNING:
            self._act_start.setVisible(False)
            self._act_pause_resume.setVisible(True)
            self._act_pause_resume.setText("Пауза")
            self._act_stop.setVisible(True)
        else:  # PAUSED
            self._act_start.setVisible(False)
            self._act_pause_resume.setVisible(True)
            self._act_pause_resume.setText("Возобновить")
            self._act_stop.setVisible(True)

        # Подстраховка: если actions скрыты, их enabled не важен, но держим корректно.
        self._act_start.setEnabled(st == TimerState.STOPPED)
        self._act_stop.setEnabled(st in (TimerState.RUNNING, TimerState.PAUSED))
        self._act_pause_resume.setEnabled(st in (TimerState.RUNNING, TimerState.PAUSED))

    def _on_tray_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        """Открыть окно при одиночном клике по иконке."""
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self._on_open()

    def _on_open(self) -> None:
        """Показать окно и поднять наверх."""
        self._window.show()
        self._window.raise_()
        self._window.activateWindow()

    def _on_start(self) -> None:
        """Start из трея."""
        self._engine.start()
        self.refresh_menu()

    def _on_pause_resume(self) -> None:
        """Pause/Resume из трея."""
        if self._engine.state == TimerState.RUNNING:
            self._engine.pause()
        elif self._engine.state == TimerState.PAUSED:
            self._engine.resume()
        self.refresh_menu()

    def _on_stop(self) -> None:
        """Stop из трея."""
        self._engine.stop()
        self.refresh_menu()

    def _on_exit(self) -> None:
        """Exit из трея.

        Если RUNNING/PAUSED — делаем stop() (сохранение) и выходим.
        """
        if self._engine.state in (TimerState.RUNNING, TimerState.PAUSED):
            self._engine.stop()
        QApplication.quit()

    def _on_engine_stop(self, _session) -> None:
        """После stop() обновляем меню (на случай вызова из UI)."""
        self.refresh_menu()

    def __del__(self) -> None:
        """Best-effort: отписка от колбэков."""
        try:
            self._engine.unsubscribe_on_stop(self._on_engine_stop)
        except Exception:
            pass
