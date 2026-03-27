"""Тесты JSON-хранилища до COMMIT 9."""

from __future__ import annotations

import os
import tempfile

from app.storage.bootstrap import ensure_storage_initialized
from app.storage.models import Session, Settings
from app.storage.paths import get_data_path, get_settings_path
from app.storage.sessions_repo import append_session, load_sessions, reset_all
from app.storage.settings_repo import load_settings, save_settings


def test_bootstrap_creates_settings_and_data_files() -> None:
    """Bootstrap должен создавать оба файла хранилища."""
    with tempfile.TemporaryDirectory() as tmp:
        os.environ["XDG_DATA_HOME"] = tmp

        ensure_storage_initialized()

        assert get_settings_path().exists() is True
        assert get_data_path().exists() is True


def test_load_settings_returns_defaults_after_bootstrap() -> None:
    """После bootstrap должны читаться дефолтные настройки."""
    with tempfile.TemporaryDirectory() as tmp:
        os.environ["XDG_DATA_HOME"] = tmp

        ensure_storage_initialized()
        settings = load_settings()

        assert settings.hourly_rate == 20.0
        assert settings.tracked_workspace == 1
        assert settings.idle_timeout_minutes == 15
        assert settings.pin_hash == ""
        assert settings.pin_salt == ""
        assert settings.screen_activity_enabled is False


def test_save_settings_persists_values() -> None:
    """Сохранённые настройки должны корректно перечитываться."""
    with tempfile.TemporaryDirectory() as tmp:
        os.environ["XDG_DATA_HOME"] = tmp

        ensure_storage_initialized()
        save_settings(
            Settings(
                hourly_rate=42.5,
                tracked_workspace=3,
                idle_timeout_minutes=7,
                pin_hash="hash",
                pin_salt="salt",
                screen_activity_enabled=True,
            )
        )

        settings = load_settings()

        assert settings.hourly_rate == 42.5
        assert settings.tracked_workspace == 3
        assert settings.idle_timeout_minutes == 7
        assert settings.pin_hash == "hash"
        assert settings.pin_salt == "salt"
        assert settings.screen_activity_enabled is True


def test_append_session_persists_session() -> None:
    """append_session() должен добавлять запись в data.json."""
    with tempfile.TemporaryDirectory() as tmp:
        os.environ["XDG_DATA_HOME"] = tmp

        ensure_storage_initialized()

        session = Session(
            id="s1",
            date="2026-03-04",
            started_at="2026-03-04T10:00:00+00:00",
            ended_at="2026-03-04T10:10:00+00:00",
            duration_seconds=600,
        )
        append_session(session)

        sessions = load_sessions()

        assert len(sessions) == 1
        assert sessions[0].id == "s1"
        assert sessions[0].duration_seconds == 600


def test_reset_all_clears_only_sessions() -> None:
    """reset_all() должен очищать только историю, не затрагивая settings."""
    with tempfile.TemporaryDirectory() as tmp:
        os.environ["XDG_DATA_HOME"] = tmp

        ensure_storage_initialized()
        save_settings(
            Settings(
                hourly_rate=77.0,
                tracked_workspace=2,
                idle_timeout_minutes=9,
                pin_hash="ph",
                pin_salt="ps",
                screen_activity_enabled=True,
            )
        )
        append_session(
            Session(
                id="s1",
                date="2026-03-04",
                started_at="2026-03-04T10:00:00+00:00",
                ended_at="2026-03-04T10:05:00+00:00",
                duration_seconds=300,
            )
        )

        reset_all()

        sessions = load_sessions()
        settings = load_settings()

        assert sessions == []
        assert settings.hourly_rate == 77.0
        assert settings.tracked_workspace == 2
        assert settings.idle_timeout_minutes == 9
        assert settings.pin_hash == "ph"
        assert settings.pin_salt == "ps"
        assert settings.screen_activity_enabled is True


def test_load_sessions_returns_empty_list_after_bootstrap() -> None:
    """Пустое data.json должно читаться как пустой список сессий."""
    with tempfile.TemporaryDirectory() as tmp:
        os.environ["XDG_DATA_HOME"] = tmp

        ensure_storage_initialized()

        sessions = load_sessions()

        assert sessions == []
