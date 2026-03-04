"""Вкладка Таймер (пока заглушка)."""

from __future__ import annotations

from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget


class TimerTab(QWidget):
    """Вкладка Таймер.

    В COMMIT 1 — только каркас.
    """

    def __init__(self) -> None:
        super().__init__()

        layout = QVBoxLayout()
        layout.addWidget(QLabel("Таймер (заглушка)"))
        layout.addStretch(1)

        self.setLayout(layout)