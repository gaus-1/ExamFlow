from __future__ import annotations

try:
    from telegram_bot.bot_handlers import (
        create_standard_button as _create_standard_button,  # type: ignore
    )
except Exception:

    def _create_standard_button(text: str, callback_data: str):  # type: ignore
        return {"text": text, "callback_data": callback_data}


def create_standard_button(text: str, callback_data: str):
    return _create_standard_button(text, callback_data)
