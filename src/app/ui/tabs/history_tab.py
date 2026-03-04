"""Вкладка История: группировка по дням (COMMIT 5)."""

from __future__ import annotations

import logging

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QHeaderView,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.core.history_aggregator import aggregate_days, format_hhmmss, format_money_usdt
from app.core.timer_engine import TimerEngine

log = logging.getLogger(__name__)


def round_to_step(value: float, step: int = 5) -> int:
    """Округлить значение до ближайшего шага step.

    Правило отображения:
    0–2.5   → 0
    2.5–7.5 → 5
    7.5–12.5 → 10

    Используется только в UI истории.
    """
    half = step / 2
    return int(((value + half) // step) * step)



class HistoryTab(QWidget):
    """Вкладка История по дням."""

    def __init__(self, *, engine: TimerEngine) -> None:
        super().__init__()
        self._engine = engine

        self._table = QTableWidget(0, 4)
        self._table.setHorizontalHeaderLabels(["Дата", "Сессий", "Время", "Деньги"])
        self._table.verticalHeader().setVisible(False)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self._table.setAlternatingRowColors(True)
        self._table.setSortingEnabled(False)
        self._table.setShowGrid(True)

        # Явно задаём цвета, чтобы на тёмной теме не получить "пустую" таблицу
        # из-за совпадения цветов текста/фона.
        self._table.setStyleSheet(
            """
            QTableWidget {
              color: #EDEDED;
              background-color: #3b3b3b;
              gridline-color: #5a5a5a;
              selection-background-color: #2d5f9a;
              selection-color: #ffffff;
            }
            QHeaderView::section {
              color: #EDEDED;
              background-color: #2f2f2f;
              padding: 6px 8px;
              border: 1px solid #4a4a4a;
            }
            """
        )

        header = self._table.horizontalHeader()

        # Все колонки одинаковые
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        # Заголовки по центру
        header.setDefaultAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        layout = QVBoxLayout()
        layout.addWidget(self._table)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.setLayout(layout)

        # COMMIT 5: обновляем историю по событию stop() (сессия записана).
        self._engine.subscribe_on_stop(self._on_engine_stop)

        # Первичная загрузка.
        self.refresh()

    def showEvent(self, event) -> None:  # type: ignore[override]
        """При показе вкладки перечитываем историю (простое обновление)."""
        super().showEvent(event)
        self.refresh()

    def _on_engine_stop(self, _session) -> None:
        """Обновить таблицу после stop()."""
        self.refresh()

    def refresh(self) -> None:
        """Перечитать sessions + settings и перерисовать таблицу."""
        days = aggregate_days()
        log.info("HistoryTab.refresh(): days=%s", len(days))

        self._table.setRowCount(len(days))
        for row, d in enumerate(days):
            item_date = QTableWidgetItem(d.date_display)
            item_date.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            item_cnt = QTableWidgetItem(str(d.sessions_count))
            item_cnt.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            item_time = QTableWidgetItem(format_hhmmss(d.sum_seconds))
            item_time.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            # COMMIT 6 — отображаем деньги шагом 5 USDT
            money_display = round_to_step(d.money_day, step=5)

            # UX: если значение 0 — показываем "—"
            if money_display == 0:
                money_text = "—"
            else:
                money_text = f"{money_display} USDT"

            item_money = QTableWidgetItem(money_text)

            item_money.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            self._table.setItem(row, 0, item_date)
            self._table.setItem(row, 1, item_cnt)
            self._table.setItem(row, 2, item_time)
            self._table.setItem(row, 3, item_money)

        self._table.resizeRowsToContents()


    def closeEvent(self, event) -> None:  # type: ignore[override]
        """Отписка от движка при закрытии виджета (best-effort)."""
        try:
            self._engine.unsubscribe_on_stop(self._on_engine_stop)
        except Exception:
            pass
        super().closeEvent(event)
