"""Тесты агрегации истории (COMMIT 5)."""

from __future__ import annotations

from app.core.history_aggregator import aggregate_days_from_sessions
from app.storage.models import Session


def test_aggregate_days_desc_and_sums() -> None:
    sessions = [
        Session(id="1", date="2026-03-01", started_at="x", ended_at="y", duration_seconds=60),
        Session(id="2", date="2026-03-01", started_at="x", ended_at="y", duration_seconds=120),
        Session(id="3", date="2026-03-02", started_at="x", ended_at="y", duration_seconds=30),
    ]

    days = aggregate_days_from_sessions(sessions=sessions, hourly_rate=20.0)

    assert [d.date_iso for d in days] == ["2026-03-02", "2026-03-01"]
    assert days[0].sessions_count == 1
    assert days[0].sum_seconds == 30
    assert days[1].sessions_count == 2
    assert days[1].sum_seconds == 180
    # 180s = 0.05h, *20 = 1.0
    assert days[1].money_day == 1.00


def test_aggregate_days_ignores_negative_durations() -> None:
    sessions = [
        Session(id="1", date="2026-03-01", started_at="x", ended_at="y", duration_seconds=-10),
        Session(id="2", date="2026-03-01", started_at="x", ended_at="y", duration_seconds=10),
    ]

    days = aggregate_days_from_sessions(sessions=sessions, hourly_rate=10.0)
    assert len(days) == 1
    assert days[0].sum_seconds == 10