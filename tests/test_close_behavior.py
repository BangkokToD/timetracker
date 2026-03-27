from __future__ import annotations

import os
os.environ["QT_QPA_PLATFORM"] = "offscreen"

import tempfile
from datetime import datetime, timezone

from PyQt6.QtWidgets import QMessageBox

from app.core.timer_engine import TimerEngine
from app.core.state import TimerState
from app.ui.main_window import MainWindow

class FakeClock:
    def __init__(self) -> None:
        self._t = 0.0

    def now(self) -> float:
        return self._t

    def advance(self, seconds: float) -> None:
        self._t += seconds


class FakeEvent:
    def __init__(self):
        self.accepted = False
        self.ignored = False

    def accept(self):
        self.accepted = True

    def ignore(self):
        self.ignored = True


class DummyWindow:
    """Минимальная замена MainWindow без Qt."""

    def __init__(self, engine):
        self._engine = engine

    def _handle_close(self):
        from app.ui.main_window import MainWindow
        return MainWindow._handle_close(self)


def test_close_without_session():
    with tempfile.TemporaryDirectory() as tmp:
        os.environ["XDG_DATA_HOME"] = tmp

        engine = TimerEngine()
        window = DummyWindow(engine)

        result = window._handle_close()

        assert result is True
        assert engine.state == TimerState.STOPPED


def test_close_paused_requires_confirm(monkeypatch):
    with tempfile.TemporaryDirectory() as tmp:
        os.environ["XDG_DATA_HOME"] = tmp

        clock = FakeClock()
        saved = []

        engine = TimerEngine(
            monotonic_fn=clock.now,
            now_utc_iso_fn=lambda: datetime(2026, 1, 1, tzinfo=timezone.utc).isoformat(),
            local_date_iso_fn=lambda: "2026-01-01",
            session_writer=saved.append,
        )

        engine.start()
        clock.advance(5)
        engine.tick()
        engine.pause()

        window = DummyWindow(engine)

        # эмулируем "Отмена"
        monkeypatch.setattr(
            "app.ui.main_window.QMessageBox.question",
            lambda *args, **kwargs: QMessageBox.StandardButton.Cancel,
        )

        result = window._handle_close()

        assert result is False
        assert engine.state == TimerState.PAUSED
        assert saved == []