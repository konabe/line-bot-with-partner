from typing import Any

from ...infrastructure.line_model.digimon_button_template import (
    create_digimon_zukan_button_template,
)
from ...infrastructure.logger import create_logger
from .protocols import DigimonAdapterProtocol, LineAdapterProtocol

logger = create_logger(__name__)


class SendDigimonUsecase:
    def __init__(
        self, line_adapter: LineAdapterProtocol, digimon_adapter: DigimonAdapterProtocol
    ):
        self.line_adapter = line_adapter
        self.digimon_adapter = digimon_adapter

    def execute(self, event: Any) -> None:
        logger.info("デジモンリクエスト受信。図鑑風情報を返信")

        info = self.digimon_adapter.get_random_digimon_info()
        if not info:
            self._send_error_message(event)
            return

        self._send_digimon_zukan_message(event, info)

    def _send_digimon_zukan_message(self, event: Any, info: Any) -> None:
        try:
            candidate = create_digimon_zukan_button_template(info)
            self._send_line_message(event, candidate)

        except Exception as e:
            logger.error(f"デジモンメッセージ送信エラー: {e}")
            self._send_error_message(event)

    def _send_line_message(self, event: Any, candidate: Any) -> None:
        try:
            if hasattr(candidate, "dict") and candidate.__class__.__name__ in (
                "TextMessage",
                "TemplateMessage",
            ):
                from linebot.v3.messaging.models import ReplyMessageRequest

                reply_message_request = ReplyMessageRequest(
                    replyToken=event.reply_token,
                    messages=[candidate],
                    notificationDisabled=False,
                )
                self.line_adapter.reply_message(reply_message_request)
                return

            from linebot.v3.messaging import models

            sdk_req = models.ReplyMessageRequest.parse_obj(
                {"replyToken": event.reply_token, "messages": [candidate]}
            )
            self.line_adapter.reply_message(sdk_req)

        except Exception as e:
            logger.error(f"LINE メッセージ送信エラー: {e}")
            raise

    def _send_error_message(self, event: Any) -> None:
        from linebot.v3.messaging.models import ReplyMessageRequest, TextMessage

        reply_message_request = ReplyMessageRequest(
            replyToken=event.reply_token,
            messages=[
                TextMessage(
                    text="デジモン図鑑情報の取得に失敗しました。",
                    quickReply=None,
                    quoteToken=None,
                )
            ],
            notificationDisabled=False,
        )
        self.line_adapter.reply_message(reply_message_request)
