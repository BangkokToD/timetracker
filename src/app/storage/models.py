"""Модели данных для JSON-хранилища.

Требования COMMIT 2:
— Settings и Session;
— устойчивое чтение/дефолты при отсутствии полей;
— версия формата хранится в JSON (version=1).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


def utc_now_iso() -> str:
    """Текущее время в UTC в ISO-формате.

    Returns:
        ISO datetime string (UTC).
    """
    return datetime.now(timezone.utc).isoformat()


def parse_iso_datetime(value: str) -> datetime:
    """Распарсить ISO-строку datetime.

    Args:
        value: ISO datetime string.

    Returns:
        datetime.

    Raises:
        ValueError: если формат некорректный.
    """
    # datetime.fromisoformat поддерживает offset, в т.ч. "+00:00".
    return datetime.fromisoformat(value)


def is_non_empty_str(v: Any) -> bool:
    """Проверка: непустая строка."""
    return isinstance(v, str) and v.strip() != ""


@dataclass(frozen=True, slots=True)
class Settings:
    """Настройки приложения."""

    hourly_rate: float
    tracked_workspace: int
    idle_timeout_minutes: int
    pin_hash: str
    pin_salt: str
    screen_activity_enabled: bool

    @staticmethod
    def defaults() -> "Settings":
        """Дефолтные настройки (зафиксированы пользователем в COMMIT 2).

        Returns:
            Settings with defaults.
        """
        return Settings(
            hourly_rate=20.0,
            tracked_workspace=1,
            idle_timeout_minutes=15,
            pin_hash="",
            pin_salt="",
            screen_activity_enabled=False,
        )

    @staticmethod
    def from_dict(raw: dict[str, Any]) -> "Settings":
        """Создать Settings из dict с валидацией и дефолтами.

        Args:
            raw: словарь настроек (без обёртки version/settings).

        Returns:
            Settings.

        Raises:
            ValueError: при критически некорректных значениях.
        """
        d = Settings.defaults()

        hourly_rate = float(raw.get("hourly_rate", d.hourly_rate))
        if hourly_rate <= 0:
            raise ValueError("hourly_rate должен быть > 0")

        tracked_workspace = int(raw.get("tracked_workspace", d.tracked_workspace))
        if tracked_workspace < 1:
            raise ValueError("tracked_workspace должен быть >= 1")

        idle_timeout_minutes = int(raw.get("idle_timeout_minutes", d.idle_timeout_minutes))
        if idle_timeout_minutes < 1:
            raise ValueError("idle_timeout_minutes должен быть >= 1")

        pin_hash = str(raw.get("pin_hash", d.pin_hash))
        pin_salt = str(raw.get("pin_salt", d.pin_salt))
        screen_activity_enabled = bool(raw.get("screen_activity_enabled", d.screen_activity_enabled))

        return Settings(
            hourly_rate=hourly_rate,
            tracked_workspace=tracked_workspace,
            idle_timeout_minutes=idle_timeout_minutes,
            pin_hash=pin_hash,
            pin_salt=pin_salt,
            screen_activity_enabled=screen_activity_enabled,
        )

    def to_dict(self) -> dict[str, Any]:
        """Преобразовать Settings в JSON-словарь.

        Returns:
            dict для записи в settings.json (без version-обёртки).
        """
        return {
            "hourly_rate": float(self.hourly_rate),
            "tracked_workspace": int(self.tracked_workspace),
            "idle_timeout_minutes": int(self.idle_timeout_minutes),
            "pin_hash": str(self.pin_hash),
            "pin_salt": str(self.pin_salt),
            "screen_activity_enabled": bool(self.screen_activity_enabled),
        }


@dataclass(frozen=True, slots=True)
class Session:
    """Сессия работы (итоговая запись)."""

    id: str
    date: str  # "YYYY-MM-DD" (локальная дата старта)
    started_at: str  # ISO datetime UTC
    ended_at: str  # ISO datetime UTC
    duration_seconds: int

    @staticmethod
    def from_dict(raw: dict[str, Any]) -> "Session":
        """Создать Session из dict с валидацией.

        Args:
            raw: словарь сессии.

        Returns:
            Session.

        Raises:
            ValueError: при некорректных значениях.
        """
        sid = str(raw.get("id", "")).strip()
        if not sid:
            raise ValueError("Session.id обязателен")

        date = str(raw.get("date", "")).strip()
        if not date:
            raise ValueError("Session.date обязателен")

        started_at = str(raw.get("started_at", "")).strip()
        ended_at = str(raw.get("ended_at", "")).strip()
        if not started_at or not ended_at:
            raise ValueError("Session.started_at и Session.ended_at обязательны")

        # Проверим, что ISO парсится. Формат UTC-строки тоже пройдёт.
        _ = parse_iso_datetime(started_at)
        _ = parse_iso_datetime(ended_at)

        duration_seconds = int(raw.get("duration_seconds", 0))
        if duration_seconds < 0:
            raise ValueError("Session.duration_seconds не может быть отрицательным")

        return Session(
            id=sid,
            date=date,
            started_at=started_at,
            ended_at=ended_at,
            duration_seconds=duration_seconds,
        )

    def to_dict(self) -> dict[str, Any]:
        """Преобразовать Session в JSON-словарь.

        Returns:
            dict для записи в data.json.
        """
        return {
            "id": str(self.id),
            "date": str(self.date),
            "started_at": str(self.started_at),
            "ended_at": str(self.ended_at),
            "duration_seconds": int(self.duration_seconds),
        }
