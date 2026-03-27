from __future__ import annotations

import os

os.environ["QT_QPA_PLATFORM"] = "offscreen"

import tempfile
from datetime import datetime, timezone
from typing import Any

from PyQt6.QtWidgets import QMessageBox

from app.core.timer_engine import TimerEngine
from app.core.state import TimerState

class FakeClock:
    """Фейковые часы для детерминированных тестов."""

    def __init__(self) -> None:
        self._t = 0.0

    def now(self) -> float:
        return self._t

    def advance(self, seconds: float) -> None:
        self._t += seconds

class DummyWindow:
    """Минимальная замена MainWindow без создания Qt-окна."""

    def __init__(self, engine: TimerEngine) -> None:
        self._engine = engine
        self.critical_calls: list[tuple[tuple[Any, ...], dict[str, Any]]] = []

    def _handle_close(self) -> bool:
        """Проксировать вызов настоящей логики MainWindow."""
        from app.ui.main_window import MainWindow

        return MainWindow._handle_close(self)


    def _critical(self, *args: Any, **kwargs: Any) -> None:
        """Сохранить вызов критического сообщения.

        Args:
            *args: Позиционные аргументы.
            **kwargs: Именованные аргументы.
        """
        self.critical_calls.append((args, kwargs))


def _build_engine(*, saved: list[Any], clock: FakeClock | None = None) -> tuple[TimerEngine, FakeClock]:
    """Собрать движок с контролируемым временем и writer.

    Args:
        saved: Список, куда будут писаться завершённые сессии.
        clock: Внешний экземпляр часов или None.

    Returns:
        Кортеж из движка и часов.
    """
    real_clock = clock if clock is not None else FakeClock()
    engine = TimerEngine(
        monotonic_fn=real_clock.now,
        now_utc_iso_fn=lambda: datetime(2026, 1, 1, tzinfo=timezone.utc).isoformat(),
        local_date_iso_fn=lambda: "2026-01-01",
        session_writer=saved.append,
    )
    return engine, real_clock

def test_close_without_session() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        os.environ["XDG_DATA_HOME"] = tmp

        engine = TimerEngine()
        window = DummyWindow(engine)

        result = window._handle_close()

        assert result is True
        assert engine.state == TimerState.STOPPED

def test_close_paused_requires_confirm(monkeypatch) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        os.environ["XDG_DATA_HOME"] = tmp

        clock = FakeClock()
        saved = []

        engine, clock = _build_engine(saved=saved, clock=clock)

        engine.start()
        clock.advance(5)
        engine.tick()
        engine.pause()

        window = DummyWindow(engine)

        monkeypatch.setattr(
            "app.ui.main_window.QMessageBox.question",
            lambda *args, **kwargs: QMessageBox.StandardButton.Cancel,
        )

        result = window._handle_close()

        assert result is False
        assert engine.state == TimerState.PAUSED
        assert saved == []


def test_close_running_confirm_saves_session(monkeypatch) -> None:
    """RUNNING-сессия должна сохраниться после подтверждённого закрытия."""
    with tempfile.TemporaryDirectory() as tmp:
        os.environ["XDG_DATA_HOME"] = tmp

        saved: list[Any] = []
        engine, clock = _build_engine(saved=saved)

        engine.start()
        clock.advance(9)
        engine.tick()

        window = DummyWindow(engine)

        monkeypatch.setattr(
            "app.ui.main_window.QMessageBox.question",
            lambda *args, **kwargs: QMessageBox.StandardButton.Yes,
        )

        result = window._handle_close()

        assert result is True
        assert engine.state == TimerState.STOPPED
        assert len(saved) == 1
        assert saved[0].duration_seconds == 9


def test_close_paused_confirm_saves_session(monkeypatch) -> None:
    """PAUSED тоже считается незавершённой сессией и должна сохраняться."""
    with tempfile.TemporaryDirectory() as tmp:
        os.environ["XDG_DATA_HOME"] = tmp

        saved: list[Any] = []
        engine, clock = _build_engine(saved=saved)

        engine.start()
        clock.advance(6)
        engine.tick()
        engine.pause()

        window = DummyWindow(engine)

        monkeypatch.setattr(
            "app.ui.main_window.QMessageBox.question",
            lambda *args, **kwargs: QMessageBox.StandardButton.Yes,
        )

        result = window._handle_close()

        assert result is True
        assert engine.state == TimerState.STOPPED
        assert len(saved) == 1
        assert saved[0].duration_seconds == 6


def test_close_returns_false_when_stop_failed(monkeypatch) -> None:
    """Если stop() падает, закрытие должно отменяться."""
    with tempfile.TemporaryDirectory() as tmp:
        os.environ["XDG_DATA_HOME"] = tmp

        saved: list[Any] = []
        engine, clock = _build_engine(saved=saved)

        engine.start()
        clock.advance(4)
        engine.tick()

        window = DummyWindow(engine)

        monkeypatch.setattr(
            "app.ui.main_window.QMessageBox.question",
            lambda *args, **kwargs: QMessageBox.StandardButton.Yes,
        )
        monkeypatch.setattr(
            engine,
            "stop",
            lambda: (_ for _ in ()).throw(RuntimeError("boom")),
        )
        monkeypatch.setattr(
            "app.ui.main_window.QMessageBox.critical",
            window._critical,
        )

        result = window._handle_close()

        assert result is False
        assert engine.state == TimerState.RUNNING
        assert saved == []
        assert len(window.critical_calls) == 1
