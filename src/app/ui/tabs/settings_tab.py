"""Вкладка Настройки: ставка / workspace / idle timeout (COMMIT 7)."""

from __future__ import annotations

import logging

from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtWidgets import (
    QCheckBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from app.core.app_bus import AppBus
from app.storage.models import Settings
from app.storage.settings_repo import load_settings, save_settings

log = logging.getLogger(__name__)


class SettingsTab(QWidget):
    """Вкладка Настройки.

    COMMIT 7:
    — ставка / workspace / idle timeout;
    — чекбокс screen_activity_enabled;
    — сохранение по кнопке "Сохранить";
    — валидация по варианту C: приводим к допустимым значениям.
    """

    def __init__(self, *, bus: AppBus) -> None:
        super().__init__()
        self._bus = bus
        self._status_clear_timer = QTimer(self)
        self._status_clear_timer.setSingleShot(True)

        self._inp_hourly_rate = QLineEdit()
        self._inp_hourly_rate.setPlaceholderText("Например: 20 или 20.5")
        self._inp_hourly_rate.setClearButtonEnabled(True)

        self._spin_tracked_workspace = QSpinBox()
        self._spin_tracked_workspace.setMinimum(1)
        self._spin_tracked_workspace.setMaximum(10_000)

        self._spin_idle_timeout = QSpinBox()
        self._spin_idle_timeout.setMinimum(1)
        self._spin_idle_timeout.setMaximum(10_000)

        self._chk_screen_activity = QCheckBox("Эксперимент: отслеживание активности экрана")

        self._btn_save = QPushButton("Сохранить")
        self._btn_save.clicked.connect(self._on_save_clicked)

        self._lbl_status = QLabel("")
        self._lbl_status.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self._lbl_status.setStyleSheet("opacity: 0.85;")
        self._status_clear_timer.timeout.connect(self._clear_status)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        form.setFormAlignment(Qt.AlignmentFlag.AlignTop)
        form.setHorizontalSpacing(16)
        form.setVerticalSpacing(10)

        form.addRow("Ставка (USDT/час)", self._inp_hourly_rate)
        form.addRow("Workspace (>= 1)", self._spin_tracked_workspace)
        form.addRow("Idle timeout (мин, >= 1)", self._spin_idle_timeout)
        form.addRow("", self._chk_screen_activity)

        actions = QHBoxLayout()
        actions.addWidget(self._btn_save, 0, Qt.AlignmentFlag.AlignLeft)
        actions.addStretch(1)
        actions.addWidget(self._lbl_status, 0, Qt.AlignmentFlag.AlignRight)

        root = QVBoxLayout()
        root.addLayout(form)
        root.addSpacing(12)
        root.addLayout(actions)
        root.addStretch(1)
        self.setLayout(root)

        self._load_into_ui()

    def _load_into_ui(self) -> None:
        """Загрузить текущие настройки из settings.json в поля."""
        try:
            s = load_settings()
        except Exception as e:
            log.exception("SettingsTab: failed to load settings: %s", e)
            s = Settings.defaults()

        self._inp_hourly_rate.setText(self._format_rate(s.hourly_rate))
        self._spin_tracked_workspace.setValue(int(s.tracked_workspace))
        self._spin_idle_timeout.setValue(int(s.idle_timeout_minutes))
        self._chk_screen_activity.setChecked(bool(s.screen_activity_enabled))

    @staticmethod
    def _format_rate(v: float) -> str:
        """Преобразовать ставку в строку для поля ввода."""
        try:
            return f"{float(v):.2f}".rstrip("0").rstrip(".")
        except Exception:
            return "20"

    @staticmethod
    def _parse_rate(text: str, fallback: float) -> float:
        """Распарсить ставку из строки (разрешаем '.' и ',').

        Валидация по варианту C: если не распарсилось/<=0 — приводим к минимуму.
        """
        raw = (text or "").strip().replace(",", ".")
        try:
            v = float(raw)
        except Exception:
            v = float(fallback)
        if v <= 0:
            v = 0.01
        return float(v)

    def _on_save_clicked(self) -> None:
        """Сохранить настройки с приведением к допустимым значениям."""
        try:
            current = load_settings()
        except Exception:
            current = Settings.defaults()

        hourly_rate = self._parse_rate(self._inp_hourly_rate.text(), fallback=float(current.hourly_rate))
        tracked_workspace = max(int(self._spin_tracked_workspace.value()), 1)
        idle_timeout_minutes = max(int(self._spin_idle_timeout.value()), 1)
        screen_activity_enabled = bool(self._chk_screen_activity.isChecked())

        new_settings = Settings(
            hourly_rate=float(hourly_rate),
            tracked_workspace=int(tracked_workspace),
            idle_timeout_minutes=int(idle_timeout_minutes),
            pin_hash=str(current.pin_hash),
            pin_salt=str(current.pin_salt),
            screen_activity_enabled=screen_activity_enabled,
        )

        save_settings(new_settings)

        # Приводим UI к сохранённым значениям (чтобы пользователь видел нормализацию).
        self._inp_hourly_rate.setText(self._format_rate(new_settings.hourly_rate))
        self._spin_tracked_workspace.setValue(new_settings.tracked_workspace)
        self._spin_idle_timeout.setValue(new_settings.idle_timeout_minutes)
        self._chk_screen_activity.setChecked(new_settings.screen_activity_enabled)

        self._lbl_status.setText("Сохранено")
        # UX: авто-сброс статуса через ~2.5 секунды (best-effort).
        self._status_clear_timer.start(2500)
        self._bus.emit_settings_changed(new_settings)

    def _clear_status(self) -> None:
        """Сбросить строку статуса."""
        self._lbl_status.setText("")

        layout = QVBoxLayout()
        layout.addWidget(QLabel("Настройки (заглушка)"))
        layout.addStretch(1)

        self.setLayout(layout)