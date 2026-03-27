"""Тесты агрегации истории (COMMIT 5)."""

from __future__ import annotations

from app.core.history_aggregator import (
    aggregate_days_from_sessions,
    format_hhmmss,
    format_money_usdt,
    iso_to_display_date,
    money_from_seconds,
)
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


def test_iso_to_display_date_formats_valid_iso() -> None:
    """Корректная ISO-дата должна преобразовываться в UI-формат."""
    assert iso_to_display_date("2026-03-04") == "04.03.2026"


def test_iso_to_display_date_keeps_invalid_value() -> None:
    """Некорректная дата должна возвращаться как есть."""
    assert iso_to_display_date("20260304") == "20260304"


def test_money_from_seconds_handles_zero_and_rounding() -> None:
    """Деньги должны считаться с округлением до цента."""
    assert money_from_seconds(0, 20.0) == 0.0
    assert money_from_seconds(180, 20.0) == 1.0
    assert money_from_seconds(1, 3600.0) == 1.0


def test_money_from_seconds_returns_zero_for_non_positive_rate() -> None:
    """Нулевая и отрицательная ставка должны давать 0.0."""
    assert money_from_seconds(100, 0.0) == 0.0
    assert money_from_seconds(100, -5.0) == 0.0


def test_format_hhmmss_formats_expected_value() -> None:
    """Время должно форматироваться как HH:MM:SS."""
    assert format_hhmmss(3661) == "01:01:01"


def test_format_hhmmss_clamps_negative_value() -> None:
    """Отрицательное время должно зажиматься в 00:00:00."""
    assert format_hhmmss(-10) == "00:00:00"


def test_format_money_usdt_formats_two_digits() -> None:
    """Деньги должны отображаться с двумя знаками после точки."""
    assert format_money_usdt(12) == "12.00 USDT"
