"""Вкладка Настройки (пока заглушка)."""

from __future__ import annotations

from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget


class SettingsTab(QWidget):
    """Вкладка Настройки.

    В COMMIT 1 — только каркас.
    """

    def __init__(self) -> None:
        super().__init__()

        layout = QVBoxLayout()
        layout.addWidget(QLabel("Настройки (заглушка)"))
        layout.addStretch(1)

        self.setLayout(layout)