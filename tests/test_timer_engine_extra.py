"""Дополнительные тесты движка таймера до COMMIT 9."""

from __future__ import annotations

from datetime import datetime, timezone

from app.core.state import TimerState
from app.core.timer_engine import TimerEngine


class FakeClock:
    """Фейковые часы для предсказуемого tick()."""

    def __init__(self) -> None:
        self._t = 0.0

    def now(self) -> float:
        """Вернуть текущее время."""
        return self._t

    def advance(self, seconds: float) -> None:
        """Сдвинуть время вперёд.

        Args:
            seconds: Количество секунд.
        """
        self._t += float(seconds)


def _build_engine(*, saved: list) -> tuple[TimerEngine, FakeClock]:
    """Собрать движок с контролируемыми часами.

    Args:
        saved: Список завершённых сессий.

    Returns:
        Кортеж из движка и часов.
    """
    clock = FakeClock()
    engine = TimerEngine(
        monotonic_fn=clock.now,
        now_utc_iso_fn=lambda: datetime(2026, 3, 4, 12, 0, 0, tzinfo=timezone.utc).isoformat(),
        local_date_iso_fn=lambda: "2026-03-04",
        session_writer=saved.append,
    )
    return engine, clock


def test_start_is_idempotent_while_running() -> None:
    """Повторный start() в RUNNING не должен создавать новую сессию."""
    saved: list = []
    engine, _clock = _build_engine(saved=saved)

    engine.start()
    first_session_id = engine.active_session_id
    engine.start()

    assert engine.state == TimerState.RUNNING
    assert engine.active_session_id == first_session_id
    assert saved == []


def test_start_while_paused_behaves_like_resume() -> None:
    """start() в PAUSED должен вести себя как resume()."""
    saved: list = []
    engine, clock = _build_engine(saved=saved)

    engine.start()
    clock.advance(5)
    engine.tick()
    engine.pause()
    engine.start()
    clock.advance(2)
    engine.tick()

    assert engine.state == TimerState.RUNNING
    assert engine.effective_seconds == 7


def test_stop_when_already_stopped_returns_none() -> None:
    """stop() в STOPPED должен быть безопасным и возвращать None."""
    saved: list = []
    engine, _clock = _build_engine(saved=saved)

    result = engine.stop()

    assert result is None
    assert engine.state == TimerState.STOPPED
    assert saved == []


def test_tick_with_subsecond_remainder_accumulates_time() -> None:
    """Дробные delta должны накапливаться без потери времени."""
    saved: list = []
    engine, clock = _build_engine(saved=saved)

    engine.start()
    clock.advance(0.4)
    engine.tick()
    clock.advance(0.4)
    engine.tick()
    clock.advance(0.4)
    engine.tick()

    assert engine.effective_seconds == 1


def test_pause_is_idempotent_when_not_running() -> None:
    """pause() вне RUNNING не должен менять состояние."""
    saved: list = []
    engine, _clock = _build_engine(saved=saved)

    engine.pause()
    assert engine.state == TimerState.STOPPED

    engine.start()
    engine.pause()
    engine.pause()
    assert engine.state == TimerState.PAUSED


def test_resume_is_safe_without_active_session() -> None:
    """resume() без активной сессии должен переводить движок в STOPPED."""
    saved: list = []
    engine, _clock = _build_engine(saved=saved)

    engine._state = TimerState.PAUSED
    engine._active = None

    engine.resume()

    assert engine.state == TimerState.STOPPED


def test_stop_notifies_subscribers_once() -> None:
    """Подписчики stop() должны вызываться один раз на сохранённую сессию."""
    saved: list = []
    notified: list = []
    engine, clock = _build_engine(saved=saved)

    engine.subscribe_on_stop(notified.append)
    engine.start()
    clock.advance(3)
    engine.tick()
    engine.stop()

    assert len(saved) == 1
    assert len(notified) == 1
    assert notified[0].id == saved[0].id