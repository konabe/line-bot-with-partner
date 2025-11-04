from typing import Optional

from linebot.v3.messaging.models import (
    ReplyMessageRequest,
    TemplateMessage,
    TextMessage,
)
from linebot.v3.webhooks.models.message_event import MessageEvent

from ...domain.models.digimon_info import DigimonInfo
from ...infrastructure.line_model.digimon_button_template import (
    create_digimon_zukan_button_template,
)
from ...infrastructure.logger import Logger, create_logger
from .protocols import DigimonAdapterProtocol, LineAdapterProtocol


class SendDigimonUsecase:
    def __init__(
        self,
        line_adapter: LineAdapterProtocol,
        digimon_adapter: DigimonAdapterProtocol,
        logger: Optional[Logger] = None,
    ):
        self.line_adapter = line_adapter
        self.digimon_adapter = digimon_adapter
        self._logger = logger or create_logger(__name__)

    def execute(self, event: MessageEvent) -> None:
        self._logger.info("デジモンリクエスト受信。図鑑風情報を返信")

        info = self.digimon_adapter.get_random_digimon_info()
        if not info:
            self._send_error_message(event)
            return

        self._send_digimon_zukan_message(event, info)

    def _send_digimon_zukan_message(
        self, event: MessageEvent, info: DigimonInfo
    ) -> None:
        try:
            candidate = create_digimon_zukan_button_template(info)
            self._send_line_message(event, candidate)

        except Exception as e:
            self._logger.error(f"デジモンメッセージ送信エラー: {e}")
            self._send_error_message(event)

    def _send_line_message(
        self, event: MessageEvent, candidate: TemplateMessage
    ) -> None:
        if not event.reply_token:
            self._logger.warning("reply_tokenが存在しないため、応答をスキップします")
            return

        try:
            reply_message_request = ReplyMessageRequest(
                replyToken=event.reply_token,
                messages=[candidate],
                notificationDisabled=False,
            )
            self.line_adapter.reply_message(reply_message_request)
        except Exception as e:
            self._logger.error(f"LINE メッセージ送信エラー: {e}")
            raise

    def _send_error_message(self, event: MessageEvent) -> None:
        if not event.reply_token:
            self._logger.warning("reply_tokenが存在しないため、応答をスキップします")
            return

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
