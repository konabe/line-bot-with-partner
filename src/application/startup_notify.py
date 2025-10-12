"""Startup notification helper for sending admin push messages."""

from __future__ import annotations

import os
from typing import Callable, Optional

from linebot.v3.messaging.models import PushMessageRequest, TextMessage


class _LoggerProtocol:
    """Minimal logger protocol to satisfy type checkers at runtime."""

    def debug(self, message: str):  # pragma: no cover - protocol definition
        raise NotImplementedError

    def info(self, message: str):  # pragma: no cover - protocol definition
        raise NotImplementedError

    def error(self, message: str):  # pragma: no cover - protocol definition
        raise NotImplementedError


def notify_startup_if_configured(
    safe_push_message: Callable[[PushMessageRequest], None],
    logger: Optional[_LoggerProtocol] = None,
) -> bool:
    """Send a startup notification to the admin if ADMIN_USER_ID is set.

    Returns True if a notification was attempted and succeeded, False otherwise.
    """
    admin_id = os.environ.get("ADMIN_USER_ID")
    if not admin_id:
        if logger:
            logger.debug("ADMIN_USER_ID not set; skipping startup notification")
        return False

    message = os.environ.get("ADMIN_STARTUP_MESSAGE", "サーバーが起動しました。")
    push_message_request = PushMessageRequest(
        to=admin_id,
        messages=[TextMessage(text=message)],
    )

    try:
        safe_push_message(push_message_request)
        if logger:
            logger.info(f"startup notification sent to admin {admin_id}")
        return True
    except Exception as exc:  # pragma: no cover - exercised in tests
        if logger:
            logger.error(f"failed to send startup notification: {exc}")
        return False


__all__ = ["notify_startup_if_configured"]
