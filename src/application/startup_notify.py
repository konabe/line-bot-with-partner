"""管理者へのプッシュメッセージ送信のための起動通知ヘルパー。"""

from __future__ import annotations

import os
from typing import Callable, Optional

from linebot.v3.messaging.models import PushMessageRequest, TextMessage
from ..infrastructure.logger import Logger


def notify_startup_if_configured(
    safe_push_message: Callable[[PushMessageRequest], None],
    logger: Optional[Logger] = None,
) -> bool:
    """ADMIN_USER_ID が設定されている場合、管理者に起動通知を送信します。

    通知が試行され成功した場合は True、そうでない場合は False を返します。
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
