"""Вкладка Таймер: UI + realtime расчёт денег (COMMIT 4)."""

from __future__ import annotations

from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.core.state import TimerState
from app.core.timer_engine import TimerEngine
from app.storage.settings_repo import load_settings
from app.storage.sessions_repo import load_sessions


class TimerTab(QWidget):
    """Вкладка Таймер: текущая сессия + итоги."""

    def __init__(self, *, engine: TimerEngine) -> None:
        super().__init__()
        self._engine = engine

        self._lbl_session_time = QLabel("00:00:00")
        self._lbl_session_money = QLabel("0.00 USDT")
        self._lbl_total_time = QLabel("00:00:00")
        self._lbl_total_money = QLabel("0.00 USDT")

        # Разрешаем лейблам растягиваться
        for w in (
            self._lbl_session_time,
            self._lbl_session_money,
            self._lbl_total_time,
            self._lbl_total_money,
        ):
            w.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self._btn_start = QPushButton("Старт")
        self._btn_pause_resume = QPushButton("Пауза")
        self._btn_stop = QPushButton("Стоп")

        self._btn_start.clicked.connect(self._on_start_clicked)
        self._btn_pause_resume.clicked.connect(self._on_pause_resume_clicked)
        self._btn_stop.clicked.connect(self._on_stop_clicked)

        root = QVBoxLayout()
        # Панель должна занимать верхнюю область и растягиваться.
        root.addWidget(self._build_main_panel(), 1)
        # Разделитель: панель занимает верх, кнопки прижаты к низу.
        root.addStretch(0)
        root.addLayout(self._build_controls_row())
        self.setLayout(root)

        # Таймер UI: раз в секунду обновляем экран и тикаем движок.
        self._timer = QTimer(self)
        self._timer.setInterval(1000)
        self._timer.timeout.connect(self._on_tick)
        self._timer.start()

        # Первичная отрисовка.
        self._apply_fonts()
        self._refresh_ui()

    def _build_main_panel(self) -> QWidget:
        """Главная панель: крупные значения сессии слева, итоги справа (вторым планом).

        Returns:
            QWidget.
        """
        container = QWidget()
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(24)

        # Левый блок (первый план): сессия (центруем "пару" время+деньги)
        left = QVBoxLayout()
        left.setContentsMargins(0, 0, 0, 0)
        left.addStretch(1)
        left.addWidget(self._lbl_session_time, alignment=Qt.AlignmentFlag.AlignHCenter)
        left.addWidget(self._lbl_session_money, alignment=Qt.AlignmentFlag.AlignHCenter)
        left.addStretch(2)

        # Разделитель между сессией и общим
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.VLine)
        sep.setFrameShadow(QFrame.Shadow.Sunken)
        sep.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)

        # Правый блок (второй план): общее (центруем "пару" время+деньги)
        right = QVBoxLayout()
        right.setContentsMargins(0, 0, 0, 0)
        right.addStretch(1)
        right.addWidget(self._lbl_total_time, alignment=Qt.AlignmentFlag.AlignHCenter)
        right.addWidget(self._lbl_total_money, alignment=Qt.AlignmentFlag.AlignHCenter)
        right.addStretch(2)

        row.addLayout(left, 3)
        row.addWidget(sep)
        row.addLayout(right, 2)
        container.setLayout(row)
        return container

    def _build_controls_row(self) -> QHBoxLayout:
        """Ряд кнопок управления без заголовков/групп-бокса.

        Returns:
            QHBoxLayout.
        """
        row = QHBoxLayout()
        row.addWidget(self._btn_start)
        row.addWidget(self._btn_pause_resume)
        row.addWidget(self._btn_stop)
        row.addStretch(1)
        return row

    def _apply_fonts(self) -> None:
        """Настроить визуальную иерархию (крупно/мелко)."""
        # Используем stylesheet — он надёжно перебивает тему Qt.
        self._lbl_session_time.setStyleSheet(
            "font-size: 96px; font-weight: 600; padding-top: 20px;"
        )

        self._lbl_session_money.setStyleSheet(
            "font-size: 42px; padding-bottom: 25px;"
        )

        # Итоги (второй план)
        self._lbl_total_time.setStyleSheet(
            "font-size: 36px; padding-top: 40px;"
        )

        self._lbl_total_money.setStyleSheet(
            "font-size: 36px;"
        )

        # Аккуратное выравнивание текста внутри лейблов (на всякий случай).
        self._lbl_session_time.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
        self._lbl_session_money.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
        self._lbl_total_time.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
        self._lbl_total_money.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)

    def _on_tick(self) -> None:
        """Тик UI (раз в 1 секунду)."""
        self._engine.tick()
        self._refresh_ui()

    def _on_start_clicked(self) -> None:
        """Обработчик кнопки Старт."""
        self._engine.start()
        self._refresh_ui()

    def _on_pause_resume_clicked(self) -> None:
        """Обработчик кнопки Пауза/Возобновить."""
        if self._engine.state == TimerState.RUNNING:
            self._engine.pause()
        elif self._engine.state == TimerState.PAUSED:
            self._engine.resume()
        self._refresh_ui()

    def _on_stop_clicked(self) -> None:
        """Обработчик кнопки Стоп."""
        self._engine.stop()
        self._refresh_ui()

    def _refresh_ui(self) -> None:
        """Обновить UI по текущему состоянию движка."""
        state = self._engine.state

        # Настройки читаем каждый раз: это даст hot-apply ставки уже сейчас.
        try:
            hourly_rate = float(load_settings().hourly_rate)
        except Exception:
            hourly_rate = 0.0

        session_seconds = int(self._engine.effective_seconds)
        total_seconds = self._calc_total_seconds() + session_seconds

        self._lbl_session_time.setText(_format_hhmmss(session_seconds))
        self._lbl_total_time.setText(_format_hhmmss(total_seconds))

        self._lbl_session_money.setText(f"{_money_from_seconds(session_seconds, hourly_rate):.2f} USDT")
        self._lbl_total_money.setText(f"{_money_from_seconds(total_seconds, hourly_rate):.2f} USDT")

        # Управление: только disabled (без скрытия).
        self._btn_start.setEnabled(state == TimerState.STOPPED)
        self._btn_stop.setEnabled(state in (TimerState.RUNNING, TimerState.PAUSED))

        if state == TimerState.RUNNING:
            self._btn_pause_resume.setEnabled(True)
            self._btn_pause_resume.setText("Пауза")
        elif state == TimerState.PAUSED:
            self._btn_pause_resume.setEnabled(True)
            self._btn_pause_resume.setText("Возобновить")
        else:
            self._btn_pause_resume.setEnabled(False)
            self._btn_pause_resume.setText("Пауза")

    def _calc_total_seconds(self) -> int:
        """Посчитать суммарное время из истории (data.json).

        Returns:
            Сумма duration_seconds всех сохранённых сессий.
        """
        try:
            sessions = load_sessions()
        except Exception:
            return 0

        total = 0
        for s in sessions:
            try:
                total += int(getattr(s, "duration_seconds", 0))
            except Exception:
                continue
        return max(int(total), 0)


def _format_hhmmss(seconds: int) -> str:
    """Форматировать секунды как HH:MM:SS.

    Args:
        seconds: количество секунд.

    Returns:
        Строка HH:MM:SS.
    """
    s = max(int(seconds), 0)
    h = s // 3600
    s -= h * 3600
    m = s // 60
    s -= m * 60
    return f"{h:02d}:{m:02d}:{s:02d}"


def _money_from_seconds(seconds: int, hourly_rate: float) -> float:
    """Рассчитать деньги по секундам и ставке (округление до цента).

    Args:
        seconds: время в секундах.
        hourly_rate: ставка в час.

    Returns:
        Деньги, округлённые до 2 знаков.
    """
    s = max(int(seconds), 0)
    rate = float(hourly_rate)
    if rate <= 0:
        return 0.0
    value = (s / 3600.0) * rate
    return round(float(value), 2)
