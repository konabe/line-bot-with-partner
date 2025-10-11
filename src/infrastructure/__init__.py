"""Infrastructure layer package.

Adapters for external systems (LINE Messaging API, HTTP clients, etc.)
This module manages a pluggable messaging adapter implementing the MessagingPort.
"""

from typing import Optional
from ..ports.messaging import MessagingPort

_adapter: Optional[MessagingPort] = None


def register_adapter(adapter: MessagingPort):
    global _adapter
    _adapter = adapter


def init_messaging_api(access_token: str):
    if _adapter is None:
        # lazy import default adapter
        try:
            from .line_adapter import LineMessagingAdapter
            register_adapter(LineMessagingAdapter())
        except Exception:
            return
    try:
        _adapter.init(access_token)
    except Exception:
        pass


def safe_reply_message(reply_message_request):
    if _adapter is None:
        return
    try:
        _adapter.reply_message(reply_message_request)
    except Exception:
        return


def safe_push_message(push_message_request):
    if _adapter is None:
        return
    try:
        _adapter.push_message(push_message_request)
    except Exception:
        return


__all__ = [
    'register_adapter',
    'init_messaging_api',
    'safe_reply_message',
    'safe_push_message',
]

