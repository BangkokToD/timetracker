"""Состояния таймера (state machine)."""

from __future__ import annotations

from enum import Enum


class TimerState(str, Enum):
    """Состояние таймера."""

    STOPPED = "STOPPED"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
