from __future__ import annotations

from typing import Protocol, TypedDict, Optional


class NotifyMessage(TypedDict):
    text: str
    parse_mode: Optional[str]


class Notifier(Protocol):
    """Абстракция канала уведомлений."""

    def send(self, user_id: str | int, message: NotifyMessage) -> None:
        ...
