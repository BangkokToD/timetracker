"""Тесты движка таймера (COMMIT 3)."""

from __future__ import annotations

import os
import tempfile
from datetime import datetime, timezone

from app.core.state import TimerState
from app.core.timer_engine import TimerEngine
from app.storage.sessions_repo import load_sessions, reset_all


class FakeClock:
    """Фейковый монотонный таймер для тестов."""

    def __init__(self) -> None:
        self._t = 0.0

    def now(self) -> float:
        return self._t

    def advance(self, seconds: float) -> None:
        self._t += float(seconds)


def fixed_utc_iso() -> str:
    """Фиксированное UTC-время для предсказуемых тестов."""
    return datetime(2026, 3, 4, 12, 0, 0, tzinfo=timezone.utc).isoformat()


def fixed_local_date() -> str:
    """Фиксированная локальная дата старта."""
    return "2026-03-04"


def test_engine_start_pause_resume_stop_writes_session() -> None:
    """Проверка: start/pause/resume/stop пишут сессию и считают duration_seconds."""
    with tempfile.TemporaryDirectory() as tmp:
        os.environ["XDG_DATA_HOME"] = tmp

        # Чистим историю на всякий случай.
        reset_all()

        clk = FakeClock()
        eng = TimerEngine(
            monotonic_fn=clk.now,
            now_utc_iso_fn=fixed_utc_iso,
            local_date_iso_fn=fixed_local_date,
        )

        assert eng.state == TimerState.STOPPED
        assert eng.effective_seconds == 0

        eng.start()
        assert eng.state == TimerState.RUNNING
        assert eng.active_session_id != ""

        # 5 секунд в RUNNING
        clk.advance(5.2)
        eng.tick()
        assert eng.effective_seconds == 5

        eng.pause()
        assert eng.state == TimerState.PAUSED
        before = eng.effective_seconds

        # В паузе время не растет
        clk.advance(10)
        eng.tick()
        assert eng.effective_seconds == before

        eng.resume()
        assert eng.state == TimerState.RUNNING

        clk.advance(3.9)
        eng.tick()
        assert eng.effective_seconds == before + 3

        s = eng.stop()
        assert s is not None
        assert eng.state == TimerState.STOPPED

        sessions = load_sessions()
        assert len(sessions) == 1
        assert sessions[0].id == s.id
        assert sessions[0].date == "2026-03-04"
        assert sessions[0].duration_seconds == s.duration_seconds
        assert sessions[0].duration_seconds == (before + 3)
