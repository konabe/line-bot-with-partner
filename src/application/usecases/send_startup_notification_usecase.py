import os
from typing import Optional

from linebot.v3.messaging.models import PushMessageRequest, TextMessage

from ...infrastructure.logger import Logger, create_logger
from .protocols import LineAdapterProtocol


class SendStartupNotificationUsecase:
    def __init__(
        self, line_adapter: LineAdapterProtocol, logger: Optional[Logger] = None
    ):
        self._line_adapter = line_adapter
        self._logger = logger or create_logger(__name__)

    def execute(self) -> bool:
        admin_id = self._get_admin_user_id()
        if not admin_id:
            self._logger.debug("ADMIN_USER_ID not set; skipping startup notification")
            return False

        message_text = self._get_startup_message()

        try:
            self._send_push_message(admin_id, message_text)
            self._logger.info(f"startup notification sent to admin {admin_id}")
            return True
        except Exception as exc:
            self._logger.error(f"startup notification failed with exception: {exc}")
            return False

    def _get_admin_user_id(self) -> Optional[str]:
        return os.environ.get("ADMIN_USER_ID")

    def _get_startup_message(self) -> str:
        return os.environ.get("ADMIN_STARTUP_MESSAGE", "サーバーが起動しました。")

    def _send_push_message(self, admin_id: str, message_text: str) -> None:
        push_message_request = PushMessageRequest(
            to=admin_id,
            messages=[TextMessage(text=message_text, quickReply=None, quoteToken=None)],
            notificationDisabled=False,
            customAggregationUnits=None,
        )

        result = self._line_adapter.push_message(push_message_request)

        if result is False:
            raise RuntimeError(
                f"failed to send startup notification to admin {admin_id}"
            )


__all__ = ["SendStartupNotificationUsecase"]
