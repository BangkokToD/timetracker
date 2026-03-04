"""Шина событий приложения (внутренние уведомления UI).

Нужно для COMMIT 7: после сохранения настроек пересчитать суммы на Таймере и в Истории
без перезапуска приложения.
"""

from __future__ import annotations

from typing import Callable, List

from app.storage.models import Settings


class AppBus:
    """Простейшая шина событий приложения."""

    def __init__(self) -> None:
        self._settings_changed_handlers: List[Callable[[Settings], None]] = []

    def subscribe_on_settings_changed(self, handler: Callable[[Settings], None]) -> None:
        """Подписаться на событие изменения настроек.

        Args:
            handler: коллбек, принимающий Settings.
        """
        if handler in self._settings_changed_handlers:
            return
        self._settings_changed_handlers.append(handler)

    def unsubscribe_on_settings_changed(self, handler: Callable[[Settings], None]) -> None:
        """Отписаться от события изменения настроек.

        Args:
            handler: ранее подписанный коллбек.
        """
        try:
            self._settings_changed_handlers.remove(handler)
        except ValueError:
            return

    def emit_settings_changed(self, settings: Settings) -> None:
        """Сообщить подписчикам, что настройки изменились.

        Args:
            settings: сохранённые настройки.
        """
        for h in list(self._settings_changed_handlers):
            try:
                h(settings)
            except Exception:
                # best-effort: не валим приложение из-за одного подписчика
                continue
