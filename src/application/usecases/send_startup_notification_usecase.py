"""起動通知送信のユースケース"""

import os

from linebot.v3.messaging.models import PushMessageRequest, TextMessage

from ...infrastructure.logger import Logger, create_logger
from .protocols import LineAdapterProtocol


class SendStartupNotificationUsecase:
    def __init__(self, line_adapter: LineAdapterProtocol, logger: Logger = None):
        self.line_adapter = line_adapter
        self.logger = logger or create_logger(__name__)

    def execute(self) -> bool:
        """起動通知を送信する

        ADMIN_USER_IDが設定されている場合、管理者に起動通知を送信します。

        Returns:
            bool: 通知が試行され成功した場合はTrue、そうでない場合はFalse
        """
        admin_id = os.environ.get("ADMIN_USER_ID")
        if not admin_id:
            self.logger.debug("ADMIN_USER_ID not set; skipping startup notification")
            return False

        message_text = os.environ.get("ADMIN_STARTUP_MESSAGE", "サーバーが起動しました。")

        try:
            # PushMessageRequestを作成
            push_message_request = PushMessageRequest(
                to=admin_id,
                messages=[
                    TextMessage(text=message_text, quickReply=None, quoteToken=None)
                ],
                notificationDisabled=False,
                customAggregationUnits=None,
            )

            # メッセージ送信
            success = self.line_adapter.push_message(push_message_request)

            # 結果処理（後方互換性のためNoneの場合はTrueとして扱う）
            if success is None:
                success = True

            if success:
                self.logger.info(f"startup notification sent to admin {admin_id}")
                return True
            else:
                self.logger.error(
                    f"failed to send startup notification to admin {admin_id}"
                )
                return False

        except Exception as exc:
            self.logger.error(f"startup notification failed with exception: {exc}")
            return False


__all__ = ["SendStartupNotificationUsecase"]
