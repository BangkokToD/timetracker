"""Агрегация истории по дням (COMMIT 5).

Требования:
- группировка по Session.date (локальная дата старта, "YYYY-MM-DD");
- сортировка дней: сначала новые (DESC);
- агрегаты: sessions_count, sum_seconds;
- money_day = sum_seconds/3600 * hourly_rate (ставка текущая из settings);
- деньги округляем round(..., 2);
- отображаем дату в UI как "DD.MM.YYYY".
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from app.storage.sessions_repo import load_sessions
from app.storage.settings_repo import load_settings


@dataclass(frozen=True, slots=True)
class DaySummary:
    """Сводка по одному дню."""

    date_iso: str
    date_display: str
    sessions_count: int
    sum_seconds: int
    money_day: float


def iso_to_display_date(date_iso: str) -> str:
    """Преобразовать YYYY-MM-DD -> DD.MM.YYYY (best-effort).

    Args:
        date_iso: дата в ISO виде.

    Returns:
        DD.MM.YYYY или исходная строка, если формат неожиданный.
    """
    parts = date_iso.split("-")
    if len(parts) != 3:
        return date_iso
    yyyy, mm, dd = parts
    if len(yyyy) == 4 and len(mm) == 2 and len(dd) == 2:
        return f"{dd}.{mm}.{yyyy}"
    return date_iso


def money_from_seconds(sum_seconds: int, hourly_rate: float) -> float:
    """Посчитать деньги по секундам и ставке.

    Args:
        sum_seconds: сумма секунд.
        hourly_rate: ставка/час.

    Returns:
        round(value, 2).
    """
    s = max(int(sum_seconds), 0)
    rate = float(hourly_rate)
    if rate <= 0:
        return 0.0
    return round((s / 3600.0) * rate, 2)


def format_hhmmss(seconds: int) -> str:
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


def format_money_usdt(value: float) -> str:
    """Формат денег в USDT.

    Args:
        value: сумма.

    Returns:
        Строка вида "12.34 USDT".
    """
    return f"{float(value):.2f} USDT"


def aggregate_days_from_sessions(
    *,
    sessions: Iterable,
    hourly_rate: float,
) -> list[DaySummary]:
    """Агрегировать произвольный список сессий по дням.

    Args:
        sessions: iterable с объектами, у которых есть date и duration_seconds.
        hourly_rate: ставка/час.

    Returns:
        Список DaySummary, отсортированный по date_iso DESC.
    """
    buckets: dict[str, list[int]] = {}

    for s in sessions:
        date_iso = str(getattr(s, "date", "")).strip()
        if not date_iso:
            continue
        try:
            dur = int(getattr(s, "duration_seconds", 0))
        except Exception:
            dur = 0
        dur = max(dur, 0)
        buckets.setdefault(date_iso, []).append(dur)

    days: list[DaySummary] = []
    for date_iso, durs in buckets.items():
        sum_seconds = int(sum(durs))
        sessions_count = int(len(durs))
        days.append(
            DaySummary(
                date_iso=date_iso,
                date_display=iso_to_display_date(date_iso),
                sessions_count=sessions_count,
                sum_seconds=sum_seconds,
                money_day=money_from_seconds(sum_seconds, hourly_rate),
            )
        )

    # date_iso у нас "YYYY-MM-DD" => лексикографическая сортировка совпадает с хронологией.
    days.sort(key=lambda x: x.date_iso, reverse=True)
    return days


def aggregate_days() -> list[DaySummary]:
    """Загрузить sessions/settings и вернуть сводку по дням.

    Returns:
        Список DaySummary (DESC).
    """
    try:
        hourly_rate = float(load_settings().hourly_rate)
    except Exception:
        hourly_rate = 0.0

    try:
        sessions = load_sessions()
    except Exception:
        sessions = []

    return aggregate_days_from_sessions(sessions=sessions, hourly_rate=hourly_rate)