"""Движок таймера (без системных интеграций).

Требования COMMIT 3:
— состояния STOPPED/RUNNING/PAUSED;
— команды start/pause/resume/stop;
— тик 1 сек: обновление effective_seconds только в RUNNING;
— на stop(): закрыть сессию и записать в data.json через append_session().

Важно:
— причины пауз (manual/idle/workspace) пока не учитываем;
— движок не знает про UI и QTimer, ему просто дергают tick().
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable, Optional

from app.core.state import TimerState
from app.storage.models import Session, utc_now_iso
from app.storage.sessions_repo import append_session


def local_date_iso_now() -> str:
    """Локальная дата в формате YYYY-MM-DD.

    Returns:
        Строка даты.
    """
    return datetime.now().date().isoformat()


@dataclass(slots=True)
class _ActiveSession:
    """Внутреннее представление активной сессии."""

    id: str
    date: str
    started_at: str
    effective_seconds: int


class TimerEngine:
    """Движок таймера с state machine и записью завершённых сессий."""

    def __init__(
        self,
        *,
        monotonic_fn: Callable[[], float] = time.monotonic,
        now_utc_iso_fn: Callable[[], str] = utc_now_iso,
        local_date_iso_fn: Callable[[], str] = local_date_iso_now,
        session_writer: Callable[[Session], None] = append_session,
    ) -> None:
        """Инициализировать движок.

        Args:
            monotonic_fn: источник монотонного времени (для delta на tick()).
            now_utc_iso_fn: функция "сейчас" в UTC ISO.
            local_date_iso_fn: функция "локальная дата".
            session_writer: функция записи завершённой сессии.
        """
        self._monotonic_fn = monotonic_fn
        self._now_utc_iso_fn = now_utc_iso_fn
        self._local_date_iso_fn = local_date_iso_fn
        self._session_writer = session_writer

        self._state: TimerState = TimerState.STOPPED
        self._active: Optional[_ActiveSession] = None

        # Для корректного накопления секунд без потерь: храним остаток < 1.0 секунды.
        self._last_tick_monotonic: Optional[float] = None
        self._tick_remainder: float = 0.0

    @property
    def state(self) -> TimerState:
        """Текущее состояние таймера."""
        return self._state

    @property
    def effective_seconds(self) -> int:
        """Эффективные секунды активной сессии (0 если STOPPED)."""
        if not self._active:
            return 0
        return int(self._active.effective_seconds)

    @property
    def active_session_id(self) -> str:
        """ID активной сессии или пустая строка."""
        return self._active.id if self._active else ""

    def start(self) -> None:
        """START.

        Если STOPPED — создаём новую сессию и переходим в RUNNING.
        Если PAUSED — это resume().
        Если RUNNING — ничего не делаем (идемпотентность).
        """
        if self._state == TimerState.RUNNING:
            return
        if self._state == TimerState.PAUSED:
            self.resume()
            return

        # STOPPED -> RUNNING
        sid = str(uuid.uuid4())
        date = self._local_date_iso_fn()
        started_at = self._now_utc_iso_fn()
        self._active = _ActiveSession(
            id=sid,
            date=date,
            started_at=started_at,
            effective_seconds=0,
        )
        self._state = TimerState.RUNNING
        self._last_tick_monotonic = self._monotonic_fn()
        self._tick_remainder = 0.0

    def pause(self) -> None:
        """PAUSE.

        RUNNING -> PAUSED.
        Остальные состояния — без эффекта (идемпотентно).
        """
        if self._state != TimerState.RUNNING:
            return

        # Перед паузой "дособерём" секунды до текущего момента.
        self.tick()
        self._state = TimerState.PAUSED
        self._last_tick_monotonic = None
        self._tick_remainder = 0.0

    def resume(self) -> None:
        """RESUME.

        PAUSED -> RUNNING.
        Остальные состояния — без эффекта (идемпотентно).
        """
        if self._state != TimerState.PAUSED:
            return
        if not self._active:
            # Защитный сценарий: не должно происходить, но не падаем.
            self._state = TimerState.STOPPED
            return

        self._state = TimerState.RUNNING
        self._last_tick_monotonic = self._monotonic_fn()
        self._tick_remainder = 0.0

    def stop(self) -> Optional[Session]:
        """STOP.

        RUNNING/PAUSED -> STOPPED, записать Session в data.json.

        Returns:
            Session если была активная сессия, иначе None.
        """
        if self._state == TimerState.STOPPED or not self._active:
            self._state = TimerState.STOPPED
            self._active = None
            self._last_tick_monotonic = None
            self._tick_remainder = 0.0
            return None

        if self._state == TimerState.RUNNING:
            self.tick()

        ended_at = self._now_utc_iso_fn()
        duration_seconds = max(int(self._active.effective_seconds), 0)

        s = Session(
            id=self._active.id,
            date=self._active.date,
            started_at=self._active.started_at,
            ended_at=ended_at,
            duration_seconds=duration_seconds,
        )
        self._session_writer(s)

        self._state = TimerState.STOPPED
        self._active = None
        self._last_tick_monotonic = None
        self._tick_remainder = 0.0
        return s

    def tick(self) -> None:
        """Тик движка.

        Должен вызываться не чаще 1 раза в секунду (или примерно так).
        Увеличивает effective_seconds только в RUNNING.

        Returns:
            None
        """
        if self._state != TimerState.RUNNING or not self._active:
            return

        now_m = self._monotonic_fn()
        if self._last_tick_monotonic is None:
            self._last_tick_monotonic = now_m
            return

        delta = now_m - self._last_tick_monotonic
        if delta <= 0:
            self._last_tick_monotonic = now_m
            return

        # Накопление секунд: переносим дробную часть дальше, чтобы не терять время.
        total = self._tick_remainder + delta
        add_secs = int(total)
        self._tick_remainder = total - float(add_secs)

        if add_secs > 0:
            self._active.effective_seconds += add_secs

        self._last_tick_monotonic = now_m
